import logging
from typing import List, Tuple, Dict

import pandas as pd
from pandas.api.types import is_string_dtype, is_datetime64_any_dtype
from recordlinkage.preprocessing import clean, phonetic

from config_parser import ConfigParser


class Preprocessor:
    def __init__(self, configparser: ConfigParser, datasets: List[List[pd.DataFrame]]):
        self.datasets = datasets
        self.configparser = configparser

    def clean_data(self) -> List[List[pd.DataFrame]]:
        cleaned_datasets = []
        for ds_info, ds in zip(self.configparser.datasets, self.datasets):
            cleaned_dfs = []
            phonetic_method = self.configparser.default_phonetic_method
            if ds_info.get('phonetic_method') is not None:
                phonetic_method = ds_info.get('phonetic_method')
            for table, df in zip(ds_info.get('tables'), ds):
                df, changes_log = self.clean_df(df, phonetic_method)
                cleaned_dfs.append(df)
                if table.startswith('http'):
                    table = f'{ds_info.get("id")}_{table.split("/")[-1]}'
                    print(table)
                cleaned_file = self.configparser.data_dir / f'cleaned_{table}'
                print(cleaned_file)
                df.to_csv(cleaned_file, index=False)
                logging.info(f'Changes applied to {ds_info.get("id")}: {table}: {changes_log}')
                logging.info(f'Cleaned table saved to {cleaned_file}')
            cleaned_datasets.append(cleaned_dfs)
        return cleaned_datasets

    def clean_df(self, df: pd.DataFrame, phonetic_method: str) -> Tuple[pd.DataFrame, Dict]:
        changes_log = {}
        original_df = df.copy()
        for col in df.columns:
            try:
                if is_string_dtype(df[col]) and not self.is_column_id(df[col]):
                    cleaned_data = clean(df[col], lowercase=True, replace_by_whitespace='[\\-\\_]',
                                         strip_accents='unicode', remove_brackets=True)
                    if phonetic_method:
                        cleaned_data = phonetic(cleaned_data, method=phonetic_method)
                    df[col] = cleaned_data
                elif is_datetime64_any_dtype(df[col]):
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                changes = (original_df[col] != df[col])
                changes_log[col] = changes.sum() if isinstance(changes, pd.Series) else 'Error: Not a Series'
            except Exception as e:
                logging.error(f'Error processing column {col}: {str(e)}')
                changes_log[col] = 'Error'
        return df, changes_log

    @staticmethod
    def is_column_id(column: pd.Series) -> bool:
        non_null_column = column.dropna()
        is_id = False

        # Check the values have the same length +/-1 (except null values)
        lengths = non_null_column.astype(str).map(len)
        if lengths.nunique() <= 3:
            is_id = True

        # Check for high value uniqueness
        unique_ratio = len(non_null_column.unique()) / len(non_null_column)
        if unique_ratio > 0.9:
            is_id = is_id and True

        return is_id
