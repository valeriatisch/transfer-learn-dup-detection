import concurrent.futures as cf
import logging
from configparser import ConfigParser
from typing import Dict

import pandas as pd
import recordlinkage
from recordlinkage.index import Block, SortedNeighbourhood, Full, Random
from scipy.stats import entropy

import preprocessor


class Indexer:
    def __init__(self, configparser: ConfigParser, ds_dict: Dict[str, Dict]):
        self.configparser = configparser
        self.ds_dict = ds_dict

    def index_data(self) -> Dict[str, Dict]:
        with cf.ThreadPoolExecutor() as executor:
            # Create a future for each dataset indexing task
            futures = [
                executor.submit(self.process_dataset, ds_id, ds)
                for ds_id, ds in self.ds_dict.items()
            ]
            ds_multi_indices = []
            for future in cf.as_completed(futures):
                multi_index = future.result()
                ds_multi_indices.append(multi_index)
        # todo
        for mi, ds_id in zip(ds_multi_indices, self.ds_dict.keys()):
            self.ds_dict[ds_id]["multi_index"] = mi
        return self.ds_dict

    def process_dataset(self, ds_id: str, ds_dict: Dict) -> pd.MultiIndex:
        candidate_set = ds_dict.get("candidate_set")
        if candidate_set is not None:
            try:
                multi_index = pd.MultiIndex.from_arrays(
                    [candidate_set["ltable.id"], candidate_set["rtable.id"]]
                )
            except KeyError:
                logging.error(
                    f"Candidate set of dataset {ds_id} has wrong foreign keys. "
                    f"Please, rename the foreign keys in the candidate set to ltable._id and rtable._id"
                )
                raise ValueError(
                    f"Foreign keys for Candidate set of dataset {ds_id} do not contain the desirable key names. "
                    f"Please, rename the foreign keys in the candidate set to ltable._id and rtable._id"
                )
        else:
            method = (
                ds_dict.get("pair_method")
                if ds_dict.get("pair_method")
                else self.configparser.default_pair_method
            )
            tables = ds_dict.get("tables")
            multi_index = (
                self.index_single_table(tables[0], method, ds_id)
                if len(tables) == 1
                else self.index_two_tables(tables[0], tables[1], method, ds_id)
            )
        return multi_index

    def index_single_table(
        self, df: pd.DataFrame, method: str, ds_id: str
    ) -> pd.MultiIndex:
        key = max(self.calculate_entropy(df), key=self.calculate_entropy(df).get)
        return self.index(df, df, key, method, ds_id)

    def index_two_tables(
        self, df1: pd.DataFrame, df2: pd.DataFrame, method: str, ds_id: str
    ) -> pd.MultiIndex:
        key = self.find_highest_entropy_common_column(df1, df2)
        return self.index(df1, df2, key, method, ds_id)

    # todo: maybe later assume in two tables, one might be dirty & the two have different schemas, do do duplicate
    #  detection on singles to be

    @staticmethod
    def index(
        df1: pd.DataFrame, df2: pd.DataFrame, key: str, method: str, ds_id: str
    ) -> pd.MultiIndex:
        logging.info(
            f"Indexing tables of {ds_id} dataset with method {method} and key {key}"
        )
        indexer = recordlinkage.Index()
        indexing_methods = {
            "block": Block(left_on=key, right_on=key),
            "sortedneighbourhood": SortedNeighbourhood(left_on=key, right_on=key),
            "full": Full(),
            "random": Random(42),
        }
        indexer.add(
            indexing_methods.get(method, ValueError(f"Invalid pair method: {method}"))
        )
        # todo: multi key sorted neightbourhood, for & unify in the end
        return indexer.index(df1, df2)

    def find_lowest_entropy_common_column(
        self, df1: pd.DataFrame, df2: pd.DataFrame
    ) -> str:
        entropies_df1 = self.calculate_entropy(df1)
        for col in sorted(entropies_df1, key=entropies_df1.get):
            if col in df2.columns:
                return col
        raise ValueError("No common column found for indexing")

    def find_highest_entropy_common_column(
        self, df1: pd.DataFrame, df2: pd.DataFrame
    ) -> str:
        entropies_df1 = self.calculate_entropy(df1)
        for col in sorted(entropies_df1, key=entropies_df1.get, reverse=True):
            if col in df2.columns:
                return col
        raise ValueError("No common entropy column found for indexing")

    @staticmethod
    def calculate_entropy(df: pd.DataFrame) -> Dict[str, float]:
        entropies = {}
        for col in df.columns:
            if preprocessor.is_column_id(df[col]):
                continue
            counts = df[col].value_counts(normalize=True)
            entropies[col] = entropy(counts)
        return entropies
