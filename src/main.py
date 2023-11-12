import argparse
import logging
import os
from pathlib import Path

from config_parser import ConfigParser
from data_loader import DataLoader
from preprocessor import Preprocessor
from indexer import Indexer


def setup_logging():
    root_dir = Path(__file__).parent.parent
    log_file = root_dir / 'logs' / 'logs.log'
    os.makedirs(log_file.parent, exist_ok=True)

    logging.basicConfig(
        filename=log_file,
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config',
        default=Path(__file__).parent.parent / 'settings' / 'config.yaml',
        type=str,
        help='Path to configuration file'
    )
    return parser.parse_args()


def main():
    setup_logging()
    args = parse_args()
    cp = ConfigParser(args.config)
    dl = DataLoader(cp)
    datasets, gold_standards = dl.load_data()
    print(datasets)
    print(gold_standards)
    pp = Preprocessor(cp, datasets)
    cleaned_datasets = pp.clean_data()
    ix = Indexer(cp, cleaned_datasets)
    mis = ix.index_data()
    # todo: clean up in the end
    print(mis)
    # todo: unify data format for goldstandard?
    # todo: implement compare
    # todo: implement monge-elkan


if __name__ == "__main__":
    main()
