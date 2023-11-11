import concurrent.futures as cf
import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

from config_parser import ConfigParser


def load_dataset(filename: str) -> pd.DataFrame:
    if not os.path.exists(filename):
        raise Exception(f'{filename} does not exist')
    df = pd.read_csv(filename)
    return df


class DataLoader:
    def __init__(self, configparser: ConfigParser):
        self.configParser = configparser
        if not os.path.exists(self.configParser.data_dir):
            os.makedirs(self.configParser.data_dir)

    def load_data(self) -> (list, list):
        datasets = []
        goldstandards = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_ds = {executor.submit(self.load_tables, ds.get('tables', [])): ds for ds in
                            self.configParser.datasets}
            future_to_gs = {executor.submit(self.load_single_table, ds['gold_standard']): ds for ds in
                            self.configParser.datasets}

            for future in cf.as_completed(future_to_ds):
                datasets.append(future.result())

            for future in cf.as_completed(future_to_gs):
                goldstandards.append(future.result())

        return datasets, goldstandards

    def load_tables(self, tables):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.load_single_table, table) for table in tables]
            return [future.result() for future in cf.as_completed(futures)]

    def load_single_table(self, table):
        if table.startswith('http'):
            print(f'Downloading table {table}')
            file = self.download_dataset(table)
        else:
            print(f'Loading table {table}')
            file = self.configParser.data_dir / table

        return load_dataset(file)

    def download_dataset(self, url: str) -> str:
        response = requests.get(url)
        if response.status_code == 200:
            file = self.configParser.data_dir / url.split('/')[-1]
            with open(file, 'wb') as f:
                f.write(response.content)
        else:
            raise Exception('Error while downloading dataset, got: '
                            f'{str(response.status_code)}, {response.reason}')
        return file
