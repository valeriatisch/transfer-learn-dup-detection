import logging
from configparser import ConfigParser
from typing import Dict, List

import concurrent.futures as cf
import numpy as np
import pandas as pd
import recordlinkage
from recordlinkage.index import Block, SortedNeighbourhood, Full, Random


class Indexer:
    def __init__(self, configparser: ConfigParser, datasets: List[List[pd.DataFrame]]):
        self.configparser = configparser
        self.datasets = datasets

    def index_data(self) -> List[pd.MultiIndex]:
        with cf.ThreadPoolExecutor() as executor:
            # Create a future for each dataset indexing task
            futures = [executor.submit(self.process_dataset, ds_info, ds) for ds_info, ds in
                       zip(self.configparser.datasets, self.datasets)]
            ds_multi_indices = []
            for future in cf.as_completed(futures):
                multi_index = future.result()
                ds_multi_indices.append(multi_index)

        return ds_multi_indices

    def process_dataset(self, ds_info, ds):
        method = ds_info.get('pair_method') if ds_info.get('pair_method') else self.configparser.default_pair_method
        logging.info(f'Indexing tables of {ds_info.get("id")} dataset with method {method}')
        return self.index_single_table(ds[0], method) if len(ds) == 1 else self.index_two_tables(ds[0], ds[1], method)

    def index_single_table(self, df: pd.DataFrame, method: str) -> pd.MultiIndex:
        key = min(self.calculate_entropy(df), key=self.calculate_entropy(df).get)
        return self.index(df, df, key, method)

    def index_two_tables(self, df1: pd.DataFrame, df2: pd.DataFrame, method: str) -> pd.MultiIndex:
        key = self.find_lowest_entropy_common_column(df1, df2)
        return self.index(df1, df2, key, method)

    def index(self, df1: pd.DataFrame, df2: pd.DataFrame, key: str, method: str) -> pd.MultiIndex:
        indexer = recordlinkage.Index()
        indexing_methods = {
            'block': Block(left_on=key, right_on=key),
            'sortedneighbourhood': SortedNeighbourhood(left_on=key, right_on=key),
            'full': Full(),
            'random': Random(42)
        }
        indexer.add(indexing_methods.get(method, ValueError(f'Invalid pair method: {method}')))
        return indexer.index(df1, df2)

    def find_lowest_entropy_common_column(self, df1: pd.DataFrame, df2: pd.DataFrame) -> str:
        entropies_df1 = self.calculate_entropy(df1)
        for col in sorted(entropies_df1, key=entropies_df1.get):
            if col in df2.columns:
                return col
        raise ValueError('No common column found for indexing')

    @staticmethod
    def calculate_entropy(df: pd.DataFrame) -> Dict[str, float]:
        entropies = {}
        for col in df.columns:
            counts = df[col].value_counts(normalize=True)
            entropy = -np.sum(counts * np.log2(counts + np.finfo(float).eps))
            entropies[col] = entropy

        return entropies
