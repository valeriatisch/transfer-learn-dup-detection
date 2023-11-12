import logging
from pathlib import Path

import jsonschema
import yaml


class ConfigParser:

    def __init__(self, config_path=None):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        self.validate_schema()
        root_dir = Path(__file__).parent.parent
        self.data_dir = root_dir / self.config['global_settings']['directory']
        self.global_settings = self.config['global_settings']
        self.default_pair_method = self.global_settings.get('default_pair_method', None)
        if self.default_pair_method is None:
            self.default_pair_method = 'sortedneighbourhood'
        self.default_phonetic_method = self.global_settings.get('default_phonetic_method', None)
        self.datasets = self.config['datasets']
        self.check_values()

    def validate_schema(self):
        schema = {
            'type': 'object',
            'properties': {
                'global_settings': {
                    'type': 'object',
                    'properties': {
                        'directory': {'type': 'string'},
                        'default_file_type': {'type': 'string'},
                        'default_phonetic_method': {'type': 'string'},
                        'default_pair_method': {'type': 'string'},
                    },
                    'required': ['directory', 'default_pair_method'],
                },
                'datasets': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'},
                            'file_type': {'type': 'string'},
                            'phonetic_method': {'type': 'string'},
                            'pair_method': {'type': 'string'},
                            'tables': {
                                'type': 'array',
                                'items': {'type': 'string'}
                            },
                            'key_column': {'type': 'string'},
                            'gold_standard': {'type': 'string'}
                        },
                        'required': ['id', 'tables', 'gold_standard'],
                    }
                }
            }
        }
        try:
            jsonschema.validate(instance=self.config, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            logging.error(f'Configuration validation error: {e}')
            raise

    def check_values(self):
        values_to_check = []  # ['pair_method' , 'phonetic_method']
        for value in values_to_check:
            if not self.global_settings.get(f'default_{value}'):
                for ds in self.datasets:
                    if not ds.get(f'{value}'):
                        logging.error(f'No default_{value} set and no {value} set for dataset {ds.get("id")}')
                        raise ValueError(f'No default_{value} set and no {value} set for dataset {ds.get("id")}')
        for ds in self.datasets:
            if len(ds.get('tables')) < 0 or len(ds.get('tables')) > 2:
                logging.error(f'Invalid number of tables for dataset {ds.get("id")}')
                raise ValueError('Only one or two tables allowed in a dataset')

    def get(self, section, key=None) -> dict:
        if key:
            return self.config[section].get(key, None)
        return self.config.get(section, None)
