import logging
from configparser import ConfigParser
from typing import Dict, List

import pandas as pd
import recordlinkage as rl
from recordlinkage.index import Block, SortedNeighbourhood, Full, Random
from scipy.stats import entropy

import preprocessor


class Indexer:
    def __init__(
        self, configparser: ConfigParser = None, ds_dict: Dict[str, Dict] = None
    ):
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
                # TODO: make it a function
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
            number_indexing_keys = (
                ds_dict.get("number_indexing_keys", None)
                if ds_dict.get("number_indexing_keys")
                else self.configparser.default_number_indexing_keys
            )
            tables = ds_dict.get("tables")
            df1 = tables[0]
            df2 = tables[1] if len(tables) == 2 else df1
            keys = self.get_highest_entropy_common_columns(
                df1, df2.columns, number_indexing_keys
            )
            multi_index = self.index(df1, df2, keys, method, ds_id, len(tables))
        return multi_index

    # TODO: maybe for later: in case of two tables assume that they might be dirty by itself,
    #  then indexing and comparing should be performed not only between the two tables but also within each table
    #  Note: the two tables might have different schemas

    @staticmethod
    def index(
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        keys: List[str],
        method: str,
        ds_id: str,
        number_tables: int,
    ) -> pd.MultiIndex:
        logging.info(
            f"Indexing tables of {ds_id} dataset with method {method} and keys {keys}"
        )
        combined_index = pd.MultiIndex(levels=[[], []], codes=[[], []])
        for key_col in keys:
            indexer = rl.Index()
            # We need to find a common column for indexing in case the two tables have different schemas
            indexing_methods = {
                "block": Block(on=key_col),
                "sortedneighbourhood": SortedNeighbourhood(on=key_col, window=3),
                "full": Full(),
                "random": Random(42),
            }
            indexer.add(
                indexing_methods.get(
                    method, ValueError(f"Invalid pair method: {method}")
                )
            )
            if number_tables == 1:
                pairs = indexer.index(df1)
            else:
                pairs = indexer.index(df1, df2)
            combined_index = combined_index.union(pairs)
        return combined_index

    def get_highest_entropy_common_columns(
        self, df1: pd.DataFrame, df2_columns: List[str], number_indexing_keys: int
    ) -> List[str]:
        entropies_df1 = self.calculate_entropy(df1)
        common_columns = []
        for col in sorted(entropies_df1, key=entropies_df1.get, reverse=True):
            if number_indexing_keys == 0:
                return common_columns
            # We need to find a common column for indexing in case the two tables have different schemas
            if col in df2_columns:
                common_columns.append(col)
            number_indexing_keys -= 1
        raise ValueError("No common entropy column found for indexing")

    @staticmethod
    def calculate_entropy(df: pd.DataFrame) -> Dict[str, float]:
        entropies = {}
        for col in df.columns:
            if preprocessor.is_column_id(df[col]) or col == "id":
                continue
            counts = df[col].value_counts(normalize=True)
            entropies[col] = entropy(counts)
        return entropies
