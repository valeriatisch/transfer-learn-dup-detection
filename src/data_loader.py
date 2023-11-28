import concurrent.futures as cf
import logging
from pathlib import Path
from typing import List, Dict, Tuple

import pandas as pd
import requests

from config_parser import ConfigParser


class DataLoader:
    def __init__(self, configparser: ConfigParser):
        self.configparser = configparser
        # os.makedirs(self.configparser.data_dir, exist_ok=True)
        self.ds_dict = {}

    def load_data(self) -> Dict[str, Dict]:
        datasets = []
        gold_standards = []
        with cf.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_ds = {
                executor.submit(self._load_tables, ds.get("tables"), ds.get("id")): ds
                for ds in self.configparser.datasets
            }
            future_to_gs = {
                executor.submit(
                    self._load_single_table, ds["gold_standard"], ds.get("id")
                ): ds
                for ds in self.configparser.datasets
            }
            for future in cf.as_completed(future_to_ds):
                datasets.append(future.result())
            for future in cf.as_completed(future_to_gs):
                gold_standards.append(future.result())
        for ds_info, ds, gs in zip(
            self.configparser.datasets, datasets, gold_standards
        ):
            self.ds_dict[ds_info.get("id")] = {
                "table_names": ds_info.get("tables"),
                "tables": ds,
                "gold_standard": gs,
                "pair_method": ds_info.get("pair_method"),
                "phonetic_method": ds_info.get("phonetic_method"),
                "similarity_measures": ds_info.get("similarity_measures"),
            }
        self.load_candidate_sets()
        return self.ds_dict

    def load_candidate_sets(self):
        for ds in self.configparser.datasets:
            if ds.get("candidate_set"):
                self.ds_dict[ds.get("id")]["candidate_set"] = self._load_single_table(
                    ds["candidate_set"], ds.get("id")
                )

    def _load_tables(self, tables: List[str], ds_id: str) -> List[pd.DataFrame]:
        results = []
        with cf.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(self._load_single_table, table, ds_id)
                for table in tables
            ]
            for future in futures:
                results.append(future.result())
        return results

    def _load_single_table(self, table: str, ds_id: str) -> pd.DataFrame:
        try:
            if table.startswith("http"):
                logging.info(f"Downloading table {table} for dataset {ds_id}")
                file, foreign_keys = self.download_dataset(table, ds_id)
                if len(foreign_keys) == 2:
                    # Candidate set
                    desirable_key_names = ["ltable.id", "rtable.id"]
                    if not any(key in desirable_key_names for key in foreign_keys):
                        logging.error(
                            f"Candidate/label set of dataset {ds_id} has foreign keys: {foreign_keys}. Please, rename "
                            f"the foreign keys in the candidate/label set to ltable._id and rtable._id"
                        )
                        raise ValueError(
                            f"Foreign keys {foreign_keys} do not contain the desirable key names {desirable_key_names}."
                            " Please, rename the foreign keys in the candidate/label set to ltable._id and rtable._id"
                        )
                    else:
                        logging.info(
                            f"Foreign keys for candidate/label set of dataset {ds_id} are {foreign_keys}"
                        )
            else:
                logging.info(f"Loading table {table} for dataset {ds_id}")
                file = Path(self.configparser.data_dir) / table

            return self.load_dataset(file)
        except Exception as e:
            logging.error(f"Error in load_single_table: {e}")
            raise

    @staticmethod
    def load_dataset(filename: str) -> pd.DataFrame:
        try:
            if not Path(filename).exists():
                raise FileNotFoundError(f"{filename} does not exist")
            df = pd.read_csv(filename)
            return df
        except Exception as e:
            logging.error(f"Error in load_dataset: {e}")
            raise

    def download_dataset(self, url: str, ds_id: str) -> Tuple[str, List[str]]:
        try:
            response = requests.get(url)
            response.raise_for_status()

            file_path = (
                Path(self.configparser.data_dir) / f'{ds_id}_{url.split("/")[-1]}'
            )
            content = response.content.decode("utf-8")

            lines = content.split("\n")

            foreign_keys = []
            for i in range(5):
                should_delete, value = self._should_delete_line(lines[i])
                if should_delete:
                    if value is not None:
                        foreign_keys.append(value)
                    if i == 4:
                        content = "\n".join(lines[5:])
                    continue

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return str(file_path), foreign_keys
        except requests.RequestException as e:
            logging.error(f"Network error while downloading dataset: {e}")
            raise
        except Exception as e:
            logging.error(f"Error in download_dataset: {e}")
            raise

    @staticmethod
    def _should_delete_line(line: str):
        markers = [
            "#key=",
            "#rtable=",
            "#foreign_key_ltable=",
            "#foreign_key_rtable=",
            "#ltable=",
        ]
        for marker in markers:
            if line.startswith(marker):
                if marker in ["#foreign_key_ltable=", "#foreign_key_rtable="]:
                    value = line.split(marker)[1].strip()
                    return True, value
                return True, None
        return False, None
