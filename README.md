# transfer-learn-dup-detection
Project @HPI

## Instructions

### Config File 🗂️

**Location**: `settings` directory

To run the application you need to specify a YAML configuration file.
This file contains some settings and the datasets to be used.
It has the following structure:

1. **Global Settings:**

    | Name                      | Required | Description                                              | Accepted Values                                    |
    |:--------------------------|:---------|:---------------------------------------------------------|:---------------------------------------------------|
    | `directory`               | ✅        | Directory in repo root where data is or will be stored.  | File path string, e.g. `data`                      |
    | `default_phonetic_method` | ❌        | Default method for phonetic matching.                    | `soundex`, `nysiis`, `metaphone`, `match_rating`   |
    | `default_pair_method`     | ❌        | Default method for creating candidate matches.           | `full`, `block`, `sortedneighbourhood`, `random`   |

2. **Datasets:** An **array** of datasets, each including:

   | Name               | Required  | Description                                                                                                                |
   |--------------------|-----------|----------------------------------------------------------------------------------------------------------------------------|
   | `id`               | ✅         | Unique identifier for the dataset.                                                                                         |
   | `phonetic_method`  | ❌         | Method used for phonetic matching. If not specified, the default method from the global settings will be applied.          |
   | `pair_method`      | ❌         | Method used for creating candidate matches. If not specified, the default method from the global settings will be applied. |
   | `tables`           | ✅         | Array of paths or URLs to the dataset tables.                                                                              |
   | `gold_standard`    | ✅         | Path or URL to the gold standard for the dataset.                                                                          |
   | `candidate_set`    | ❌         | Path or URL to the candidate set for the dataset.                                                                          |

All values should be strings.

#### Example YAML Config
```yaml
global_settings:
  directory: 'data'
  default_phonetic_method: 'soundex'
  default_pair_method: 'sortedneighbourhood'

datasets:
  - id: 'freedb_cds'
    tables:
      - 'freedb_cds_freedb_cds.csv'
    phonetic_method: 'soundex'
    gold_standard: 'freedb_cds_freedb_cds_goldstandard.csv'

  - id: 'hpi_cora'
    tables:
      - 'hpi_cora_hpi_cora.csv'
    gold_standard: 'hpi_cora_hpi_cora_goldstandard.csv'
    pair_method: 'block'

  - id: 'bikes'
    tables:
      - 'http://pages.cs.wisc.edu/~anhai/data/784_data/bikes/csv_files/bikedekho.csv'
      - 'http://pages.cs.wisc.edu/~anhai/data/784_data/bikes/csv_files/bikewale.csv'
    gold_standard: 'http://pages.cs.wisc.edu/~anhai/data/784_data/bikes/csv_files/labeled_data.csv'

```

### Running the Application 🚀

   ```bash
   python src/main.py --config settings/config.yaml
   ```

If no path to a config file is specified, the application will look for a file named `config.yaml` in the `settings` directory by default.

The datasets specified in the config will be either downloaded and saved in the specified directory or loaded from this directory.

A `log/logs.log` file will be created in the repo root directory. It will save all logs from an application run.
