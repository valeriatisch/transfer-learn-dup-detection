import argparse
import logging
import os
from pathlib import Path

from config_parser import ConfigParser
from data_loader import DataLoader


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
    # todo: clean later
    for ds in datasets:
        for df in ds:
            print(df.head(3))
    for df in gold_standards:
        print(df.head(3))
    # todo: implement selection of key attributes (highest entropy)
    # todo: implement indexing -> toolkit
    # todo: unify data format for goldstandard?


if __name__ == "__main__":
    main()
