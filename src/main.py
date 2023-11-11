import argparse
from pathlib import Path

from config_parser import ConfigParser
from data_loader import DataLoader


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
    # todo: try out datasets from
    #   https://sites.google.com/site/anhaidgroup/useful-stuff/the-magellan-data-repository
    #   https://dbs.uni-leipzig.de/research/projects/benchmark-datasets-for-entity-resolution
    # todo: implement selection of key attributes (highest entropy)


if __name__ == "__main__":
    main()
