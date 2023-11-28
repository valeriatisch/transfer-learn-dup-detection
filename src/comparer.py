import logging
from configparser import ConfigParser
from typing import Dict

import recordlinkage as rl
import pandas as pd


class Comparer:
    def __init__(self, configparser: ConfigParser, ds_dict: Dict[str, Dict]):
        self.configparser = configparser
        self.ds_dict = ds_dict

    # TODO: implement monge-elkan similarity measure

    def compare(self) -> Dict[str, Dict]:
        for ds_id, ds in self.ds_dict.items():
            compare_obj = rl.Compare()
            similarity_string_measure = self.set_similarity_measure(
                self.configparser.default_similarity_string_measure,
                ds.get("similarity_measures"),
                "string",
            )
            similarity_numeric_measure = self.set_similarity_measure(
                self.configparser.default_similarity_numeric_measure,
                ds.get("similarity_measures"),
                "numeric",
            )
            logging.info(
                f"Comparing candidate pairs for dataset {ds_id} with similarity measures: "
                f"{similarity_string_measure} for strings, {similarity_numeric_measure} for numbers"
            )
            tables = ds.get("tables")
            df1 = tables[0]
            if len(tables) == 2:
                df2 = tables[1]
                threshold = int(min(len(df1.columns), len(df2.columns)) * 0.5)
                for col in df1.columns.intersection(
                    df2.columns
                ):  # Only compare columns that are in both tables
                    self.compare_columns(
                        compare_obj,
                        df1,
                        col,
                        similarity_string_measure
                        if pd.api.types.is_string_dtype(df1[col])
                        else similarity_numeric_measure,
                    )
                features = compare_obj.compute(ds.get("multi_index"), df1, df2)
            else:
                threshold = int(len(df1.columns) * 0.5)
                for col in df1.columns:
                    self.compare_columns(
                        compare_obj,
                        df1,
                        col,
                        similarity_string_measure
                        if pd.api.types.is_string_dtype(df1[col])
                        else similarity_numeric_measure,
                    )
                features = compare_obj.compute(ds.get("multi_index"), df1)
            logging.info(
                f"Chosen threshold for summed features: {threshold} out of {len(features.columns)}"
            )
            matches = features[features.sum(axis=1) > threshold]
            self.ds_dict[ds_id]["compared_multi_index"] = matches
            # TODO: might delete this later or refactor in case no id colum is there,
            #  then multi index is enough bc it's gonna be the same
            self.ds_dict[ds_id]["matched_ids"] = matches.index.map(
                lambda idx: (
                    df1["id"].iloc[idx[0]],
                    df2["id"].iloc[idx[1]]
                    if len(tables) == 2
                    else df1["id"].iloc[idx[1]],
                )
            )

        return self.ds_dict

    @staticmethod
    def set_similarity_measure(
        default_measure: str, custom_measures: Dict[str, str], measure_type: str
    ) -> str:
        return (
            custom_measures.get(measure_type, default_measure)
            if custom_measures
            else default_measure
        )

    @staticmethod
    def compare_columns(
        compare_obj: rl.Compare, df: pd.DataFrame, col: str, similarity_measure: str
    ):
        if pd.api.types.is_string_dtype(df[col]):
            if similarity_measure == "exact":  # String / Text
                compare_obj.exact(col, col, label=col)
            else:
                compare_obj.string(
                    col, col, method=similarity_measure, threshold=0.85, label=col
                )
        elif pd.api.types.is_numeric_dtype(df[col]):  # Numeric
            if similarity_measure == "exact":
                compare_obj.exact(col, col, label=col)
            else:
                compare_obj.numeric(col, col, method=similarity_measure, label=col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):  # Date
            compare_obj.date(col, col, label=col)
        else:  # Unknown
            compare_obj.exact(col, col, label=col)
