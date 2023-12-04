import logging
from configparser import ConfigParser
from typing import Dict, Tuple, List, Set
import networkx as nx

import pandas as pd
from sklearn.model_selection import train_test_split


class Classifier:
    def __init__(self, configparser: ConfigParser, ds_dict: Dict[str, Dict]):
        self.configparser = configparser
        self.ds_dict = ds_dict

    def split(self):
        # TODO: rethink logic in general
        # TODO: split all datasets into train, test, val
        #   to get larger set of data for training:
        #       Use multiindex from compare
        # TODO: refactor & speed up
        for ds_id, ds in self.ds_dict.items():
            tables = ds.get("tables")
            df1 = tables[0]
            if len(tables) == 2:
                continue
                # TODO: implement for two tables

            pairs = list(ds.get("gold_standard").to_records(index=False))
            clusters = self.create_transitive_clusters(pairs)
            train_ids, val_ids, test_ids = self.split_clusters(clusters)
            # train_idx = self.map_ids_to_indices(df1, train_ids)

            # TODO: sets should also contain non-matches

            indices_to_retrieve = [
                (df1[df1["id"] == id1].index[0], df1[df1["id"] == id2].index[0])
                for id1, id2 in pairs
                if id1 in train_ids and id2 in train_ids
            ]

            selected_features_list = []

            # Extract the features for the specified pairs, handling missing indices
            for idx1, idx2 in indices_to_retrieve:
                try:
                    selected_features_list.append(
                        ds.get("similarity_scores").loc[(idx1, idx2)]
                    )
                except KeyError:
                    pass

            # Concatenate the selected features DataFrames horizontally
            selected_features = pd.concat(selected_features_list, axis=1).T
            print(selected_features.head(3))
            # mi = ds.get('compared_multi_index')  # for actual task of deduplication
            # gold_standard_df = ds.get('gold_standard')
            logging.info(f"Split dataset {ds_id}")

    @staticmethod
    def create_transitive_clusters(pairs: List[Tuple[int, int]]) -> List[Set[int]]:
        g = nx.Graph()
        g.add_edges_from(pairs)
        return list(nx.connected_components(g))

    @staticmethod
    def split_clusters(clusters: List[Set[int]]) -> Tuple[Set[int], Set[int], Set[int]]:
        # Split clusters into train (70%) and test+val (30%)
        train_clusters, test_val_clusters = train_test_split(clusters, test_size=0.3)
        # Split test+val into test (20% of total) and val (10% of total)
        test_clusters, val_clusters = train_test_split(
            test_val_clusters, test_size=1 / 3
        )
        # Fold out the clusters back into sets of ids
        return (
            set().union(*train_clusters),
            set().union(*test_clusters),
            set().union(*val_clusters),
        )

    @staticmethod
    def map_ids_to_indices(df: pd.DataFrame, ids: Set[int]) -> Set[int]:
        return set(df.index[df["id"].isin(ids)].tolist())
