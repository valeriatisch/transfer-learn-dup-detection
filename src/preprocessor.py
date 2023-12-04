import logging
from typing import Tuple, Dict

import pandas as pd
from pandas.api.types import is_string_dtype, is_datetime64_any_dtype
from recordlinkage.preprocessing import clean, phonetic

from config_parser import ConfigParser


def is_column_id(column: pd.Series) -> bool:
    non_null_column = column.dropna()
    is_id = False

    # Check the values have the same length +/-1 (except null values)
    lengths = non_null_column.astype(str).map(len)
    print(lengths)
    if lengths.nunique() <= 3:
        is_id = True

    # Check for high value uniqueness
    unique_ratio = len(non_null_column.unique()) / len(non_null_column)
    print(unique_ratio)
    if unique_ratio > 0.9:
        return is_id and True
    else:
        return False


class Preprocessor:
    def __init__(self, configparser: ConfigParser, ds_dict: Dict[str, Dict]):
        self.ds_dict = ds_dict
        self.configparser = configparser

    def clean_data(self) -> Dict[str, Dict]:
        # loop through dictionary
        for ds_id, ds in self.ds_dict.items():
            cleaned_dfs = []
            phonetic_method = self.configparser.default_phonetic_method
            if ds.get("phonetic_method") is not None:
                phonetic_method = ds.get("phonetic_method")
            for table_name, df in zip(ds.get("table_names"), ds.get("tables")):
                df, changes_log = self.clean_df(df, phonetic_method)
                cleaned_dfs.append(df)
                if table_name.startswith("http"):
                    table_name = f'{ds_id}_{table_name.split("/")[-1]}'
                cleaned_file = self.configparser.data_dir / f"cleaned_{table_name}"
                df.to_csv(cleaned_file, index=False)
                logging.info(
                    f'Changes applied to {ds.get("id")}: {table_name}: {changes_log}'
                )
                logging.info(f"Cleaned table saved to {cleaned_file}")
            self.ds_dict[ds_id]["cleaned_tables"] = cleaned_dfs
        return self.ds_dict

    @staticmethod
    def clean_df(df: pd.DataFrame, phonetic_method: str) -> Tuple[pd.DataFrame, Dict]:
        changes_log = {}
        original_df = df.copy()
        for col in df.columns:
            try:
                if is_string_dtype(df[col]) and not is_column_id(df[col]):
                    cleaned_data = clean(
                        df[col],
                        lowercase=True,
                        replace_by_whitespace="[\\-\\_]",
                        strip_accents="unicode",
                        remove_brackets=True,
                    )
                    if phonetic_method:
                        cleaned_data = phonetic(cleaned_data, method=phonetic_method)
                    df[col] = cleaned_data
                elif is_datetime64_any_dtype(df[col]):
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                changes = original_df[col] != df[col]
                changes_log[col] = (
                    changes.sum()
                    if isinstance(changes, pd.Series)
                    else "Error: Not a Series"
                )
            except Exception as e:
                logging.error(f"Error processing column {col}: {str(e)}")
                changes_log[col] = "Error"
        return df, changes_log
