# transfer-learn-dup-detection
Project @HPI

## Instructions

### Config File 🗂️

**Location**: `settings` directory

To run the application you need to specify a YAML configuration file.
This file contains some settings and the datasets to be used.
It has the following structure:

1. **Global Settings:**

    | Name                  | Required | Description                                    |
    |:----------------------|:---------|:-----------------------------------------------|
    | `directory`           | ✅        | Directory where data is or will be stored.     |
    | `default_pair_method` | ❌        | Default method for creating candidate matches. |

2. **Datasets:** An **array** of datasets, each including:

    | Name             | Required  | Description                                                                                                                |
    |------------------|-----------|----------------------------------------------------------------------------------------------------------------------------|
    | `id`             | ✅         | Unique identifier for the dataset.                                                                                         |
    | `pair_method`    | ❌         | Method used for creating candidate matches. If not specified, the default method from the global settings will be applied. |
    | `tables`         | ✅         | Array of paths or URLs to the dataset tables.                                                                              |
    | `gold_standard`  | ✅         | Path or URL to the gold standard for the dataset.                                                                          |

All values should be strings.

#### Example YAML Config
```yaml
global_settings:
  directory: 'data'
  default_pair_method: 'SortedNeighbourhood'

datasets:
  - id: 'dataset1'
    pair_method: 'Block'
    tables:
      - 'path/to/table1.csv'
    gold_standard: 'path/to/gold_standard.csv'

  - id: 'dataset2'
    tables:
      - 'https://example.com/table2.csv'
    gold_standard: 'https://example.com/gold_standard2.csv'
```

### Running the Application 🚀

   ```bash
   python src/main.py --config /settings/config.yml
   ```

The specified datasets in `/settings/config.yml` will be either downloaded and saved in the specified directory or loaded from this directory.
