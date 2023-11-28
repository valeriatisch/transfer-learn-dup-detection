import logging
from configparser import ConfigParser
from typing import Dict

import pandas as pd
import recordlinkage as rl
from recordlinkage.index import Block, SortedNeighbourhood, Full, Random
from scipy.stats import entropy

import preprocessor


class Indexer:
    def __init__(self, configparser: ConfigParser, ds_dict: Dict[str, Dict]):
        self.configparser = configparser
        self.ds_dict = ds_dict

    def index_data(self) -> Dict[str, Dict]:
        for ds_id, ds in self.ds_dict.items():
            multi_index = self.process_dataset(ds_id, ds)
            self.ds_dict[ds_id]["multi_index"] = multi_index
        return self.ds_dict

    def process_dataset(self, ds_id: str, ds_dict: Dict) -> pd.MultiIndex:
        candidate_set = ds_dict.get("candidate_set")
        if candidate_set is not None:
            try:
                ltable, rtable = ds_dict.get("tables")
                # Store original indices
                ltable_original_index = ltable.reset_index().index.copy()
                rtable_original_index = rtable.reset_index().index.copy()
                # Set 'id' as index for lookup
                ltable_id_index = ltable.set_index("id")
                rtable_id_index = rtable.set_index("id")
                # Map IDs in candidate_set to original indices
                ltable_indices = [
                    ltable_original_index[ltable_id_index.index.get_loc(_id)]
                    for _id in candidate_set["ltable.id"]
                ]
                rtable_indices = [
                    rtable_original_index[rtable_id_index.index.get_loc(_id)]
                    for _id in candidate_set["rtable.id"]
                ]
                # Create MultiIndex using these original indices
                multi_index = pd.MultiIndex.from_arrays(
                    [ltable_indices, rtable_indices]
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

    # TODO: maybe for later: in case of two tables assume that they might be dirty by itself,
    #  then indexing and comparing should be performed not only between the two tables but also within each table
    #  Note: the two tables might have different schemas

    def index(
        self, df1: pd.DataFrame, df2: pd.DataFrame, key: str, method: str, ds_id: str
    ) -> pd.MultiIndex:
        logging.info(
            f"Indexing tables of {ds_id} dataset with method {method} and key {key}"
        )
        indexer = rl.Index()
        indexing_methods = {
            "block": Block(on=key),
            "sortedneighbourhood": SortedNeighbourhood(on=key),
            "full": Full(),
            "random": Random(42),
        }
        # TODO: implement multi key indexing properly (for-loop & unify), test and refactor
        multi_key_indexing = False
        if multi_key_indexing:
            combined_index = pd.MultiIndex(levels=[[], []], codes=[[], []])
            entropies = self.calculate_entropy(df1)
            keys = 3
            for key_col in sorted(entropies, key=entropies.get, reverse=True):
                if keys == 0:
                    break
                # We need to find a common column for indexing in case the two tables have different schemas
                if key_col in df2.columns:
                    indexing_methods = {
                        "block": Block(on=key_col),
                        "sortedneighbourhood": SortedNeighbourhood(on=key_col),
                        "full": Full(),
                        "random": Random(42),
                    }
                    indexer.add(
                        indexing_methods.get(
                            method, ValueError(f"Invalid pair method: {method}")
                        )
                    )
                    pairs = indexer.index(df1, df2)
                    combined_index = combined_index.union(pairs)
                    keys -= 1
            return indexer.index(df1, df2)
        else:
            indexer.add(
                indexing_methods.get(
                    method, ValueError(f"Invalid pair method: {method}")
                )
            )
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
            # We need to find a common column for indexing in case the two tables have different schemas
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
