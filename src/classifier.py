from configparser import ConfigParser
from typing import Dict, Tuple, List, Set
import networkx as nx
import pandas as pd
from sklearn.model_selection import train_test_split
import recordlinkage as rl
import joblib


class Classifier:
    def __init__(self, configparser: ConfigParser, ds_dict: Dict[str, Dict]):
        self.configparser = configparser
        self.ds_dict = ds_dict

    def split(self):
        for ds_id, ds in self.ds_dict.items():
            tables = ds.get("tables")
            df1 = tables[0]
            gold_standard = ds.get("gold_standard")

            if len(tables) == 2:
                # TODO: implement for two tables
                continue

            pairs = list(gold_standard.to_records(index=False))
            clusters = self.create_transitive_clusters(pairs)
            train_ids, val_ids, test_ids = self.split_clusters(clusters)

            similarity_scores = ds.get("similarity_scores")
            similarity_scores = self.sort_similarity_scores(similarity_scores)
            (
                train_similarity_matrix,
                common_indices,
            ) = self.create_train_similarity_matrix(
                df1, train_ids, pairs, similarity_scores
            )
            self.train_and_save_model(train_similarity_matrix, common_indices)

    @staticmethod
    def create_transitive_clusters(pairs: List[Tuple[int, int]]) -> List[Set[int]]:
        graph = nx.Graph()
        graph.add_edges_from(pairs)
        return list(nx.connected_components(graph))

    @staticmethod
    def split_clusters(clusters: List[Set[int]]) -> Tuple[Set[int], Set[int], Set[int]]:
        train_clusters, test_val_clusters = train_test_split(clusters, test_size=0.3)
        test_clusters, val_clusters = train_test_split(
            test_val_clusters, test_size=1 / 3
        )
        return (
            set().union(*train_clusters),
            set().union(*test_clusters),
            set().union(*val_clusters),
        )

    @staticmethod
    def sort_similarity_scores(similarity_scores: pd.DataFrame) -> pd.DataFrame:
        def sort_index_pairs(index):
            return pd.MultiIndex.from_tuples([tuple(sorted(pair)) for pair in index])

        sorted_index = sort_index_pairs(similarity_scores.index)
        sorted_similarity_scores = pd.DataFrame(
            index=sorted_index, columns=similarity_scores.columns
        )

        # Populate the new DataFrame with data from the original DataFrame
        for idx in sorted_similarity_scores.index:
            if idx in similarity_scores.index:
                sorted_similarity_scores.loc[idx] = similarity_scores.loc[idx]
            elif idx[::-1] in similarity_scores.index:
                sorted_similarity_scores.loc[idx] = similarity_scores.loc[idx[::-1]]
        return sorted_similarity_scores

    @staticmethod
    def create_train_similarity_matrix(
        df: pd.DataFrame,
        train_ids: Set[int],
        pairs: List[Tuple[int, int]],
        similarity_scores: pd.DataFrame,
    ) -> tuple:
        indices_to_retrieve = [
            (df[df["id"] == id1].index[0], df[df["id"] == id2].index[0])
            for id1, id2 in pairs
            if id1 in train_ids and id2 in train_ids
        ]
        multi_index = pd.MultiIndex.from_tuples(indices_to_retrieve)
        multi_index = pd.MultiIndex.from_tuples(
            [tuple(sorted(pair)) for pair in multi_index]
        )

        common_indices = similarity_scores.index.intersection(multi_index)
        # Filter the DataFrame to keep only rows with indices in the intersection
        similarity_scores_train_true_matches = similarity_scores.loc[common_indices]

        mask = similarity_scores.index.map(lambda x: (x[0], x[1]) not in multi_index)

        # Apply the mask to the DataFrame
        similarity_scores_filtered = similarity_scores[
            mask
        ]  # that are not true matches

        train_idx_non_matches, test_val_non_matches = train_test_split(
            similarity_scores_filtered.index, test_size=0.3
        )

        train_non_matches = similarity_scores_filtered.loc[train_idx_non_matches]

        train_similarity_matrix = pd.concat(
            [similarity_scores_train_true_matches, train_non_matches]
        ).sample(frac=1)

        return train_similarity_matrix, common_indices

    @staticmethod
    def train_and_save_model(train_similarity_matrix: pd.DataFrame, common_indices):
        classifier = rl.SVMClassifier()
        classifier.fit(train_similarity_matrix, common_indices)
        joblib.dump(classifier, "svm_record_linkage_model.pkl")
