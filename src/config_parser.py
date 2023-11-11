from pathlib import Path

import jsonschema
import yaml


class ConfigParser:

    def __init__(self, config_path=None):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        self.validate_schema()
        self.directory = Path(__file__).parent.parent / self.config['global_settings']['directory']
        self.global_settings = self.config['global_settings']
        self.datasets = self.config['datasets']

    def validate_schema(self):
        schema = {
            'type': 'object',
            'properties': {
                'global_settings': {
                    'type': 'object',
                    'properties': {
                        'directory': {'type': 'string'},
                        'default_file_type': {'type': 'string'},
                        'default_pair_method': {'type': 'string'},
                    },
                    'required': ['directory'],
                },
                'datasets': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'},
                            'file_type': {'type': 'string'},
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
        jsonschema.validate(instance=self.config, schema=schema)

    def get(self, section, key=None) -> dict:
        if key:
            return self.config[section].get(key, None)
        return self.config.get(section, None)
