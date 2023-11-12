import concurrent.futures as cf
import logging
import os
from pathlib import Path

import pandas as pd
import requests

from config_parser import ConfigParser


class DataLoader:
    def __init__(self, configparser: ConfigParser):
        self.configParser = configparser
        os.makedirs(self.configParser.data_dir, exist_ok=True)

    def load_data(self) -> (list, list):
        datasets = []
        gold_standards = []
        with cf.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_ds = {executor.submit(self._load_tables, ds.get('tables'),
                                            ds.get('id')): ds for ds in self.configParser.datasets}
            future_to_gs = {executor.submit(self._load_single_table, ds['gold_standard'],
                                            ds.get('id')): ds for ds in self.configParser.datasets}
            for future in cf.as_completed(future_to_ds):
                datasets.append(future.result())
            for future in cf.as_completed(future_to_gs):
                gold_standards.append(future.result())
        return datasets, gold_standards

    def _load_tables(self, tables: list, ds_id: str) -> list:
        results = []
        with cf.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._load_single_table, table, ds_id) for table in tables]
            for future in futures:
                results.append(future.result())
        return results

    def _load_single_table(self, table: str, ds_id: str) -> pd.DataFrame:
        try:
            if table.startswith('http'):
                logging.info(f'Downloading table {table}')
                file = self.download_dataset(table, ds_id)
            else:
                logging.info(f'Loading table {table}')
                file = Path(self.configParser.data_dir) / table

            return self.load_dataset(file)
        except Exception as e:
            logging.error(f'Error in load_single_table: {e}')
            raise

    @staticmethod
    def load_dataset(filename: str) -> pd.DataFrame:
        try:
            if not Path(filename).exists():
                raise FileNotFoundError(f'{filename} does not exist')
            df = pd.read_csv(filename)
            return df
        except Exception as e:
            logging.error(f'Error in load_dataset: {e}')
            raise

    def download_dataset(self, url: str, ds_id: str) -> str:
        try:
            response = requests.get(url)
            response.raise_for_status()

            file_path = Path(self.configParser.data_dir) / f'{ds_id}_{url.split("/")[-1]}'
            content = response.content.decode('utf-8')

            lines = content.split('\n')
            if all(self._should_delete_line(lines[i]) for i in range(5)):
                content = '\n'.join(lines[5:])

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return str(file_path)
        except requests.RequestException as e:
            logging.error(f'Network error while downloading dataset: {e}')
            raise
        except Exception as e:
            logging.error(f'Error in download_dataset: {e}')
            raise

    @staticmethod
    def _should_delete_line(line: str) -> bool:
        markers = ['#key=', '#rtable=', '#foreign_key_ltable=', '#foreign_key_rtable=', '#ltable=']
        return any(line.startswith(marker) for marker in markers)
