# transfer-learn-dup-detection
Project @HPI

## Instructions

### Config File 🗂️

**Location**: `settings` directory

To run the application you need to specify a YAML configuration file.
This file contains some settings and the datasets to be used.
It has the following structure:

1. **Global Settings:**

    | Name                                   | Required  | Description                                                                                                                             | Accepted Values                                                                                         | Default               |
    |:---------------------------------------|:---------:|:----------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------|:----------------------|
    | `directory`                            |     ✅     | Directory in repo root where data is or will be stored.                                                                                 | File path string, e.g. `data`                                                                           |                       |
    | `default_phonetic_method`              |     ❌     | Default method for phonetic matching.                                                                                                   | `soundex`, `nysiis`, `metaphone`, `match_rating`                                                        |                       |
    | `default_pair_method`                  |     ❌     | Default method for creating candidate matches.                                                                                          | `full`, `block`, `sortedneighbourhood`, `random`                                                        | `sortedneighbourhood` |
    | `number_indexing_keys`                 |     ❌     | Number of key columns to be used for indexing in case multi-key-indexing is needed. The ones with the highest entropies will be chosen. | Integer, e.g. `2`                                                                                       | `1`                   |
    | `default_similarity_measures: string`  |     ❌     | Default similarity measure for string candidate matches.                                                                                | `jaro`, `jarowinkler`, `levenshtein`, `damerau_levenshtein`, `qgram`, `cosine`, `smith_waterman`, `lcs` | `levenshtein`         |
    | `default_similarity_measures: numeric` |     ❌     | Default similarity threshold for numeric candidate matches.                                                                             | `step`, `linear`, `exp`, `gauss`, `squared`                                                             | `linear`              |

2. **Datasets:** An **array** of datasets, each including:

   | Name                           | Required | Description                                                                                                                                            | Accepted Values                                                                                                                   | Default               |
   |:-------------------------------|:--------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------|:----------------------|
   | `id`                           |    ✅     | Unique identifier for the dataset.                                                                                                                     | E.g. *'freedb_cds'*, *'hpi_cora'*, *'bikes'*                                                                                      |                       |
   | `phonetic_method`              |    ❌     | Method used for phonetic matching. If not specified, the default method from the global settings will be applied.                                      | `soundex`, `nysiis`, `metaphone`, `match_rating`                                                                                  |                       |                                              
   | `pair_method`                  |    ❌     | Method used for creating candidate matches. If not specified, the default method from the global settings will be applied.                             | `full`, `block`, `sortedneighbourhood`, `random`                                                                                  | `sortedneighbourhood` |
   | `number_indexing_keys`         |    ❌     | Number of key columns to be used for indexing in case multi-key-indexing is needed. The ones with the highest entropies will be chosen.                | Integer, e.g. `2`                                                                                                                 | `1`                   |
   | `tables`                       |    ✅     | URL(s) or filename(s) of the dataset tables in csv format lying in the `directory` specified in the global settings. Max number of tables: 2; min: 1   | E.g. *'freedb_cds.csv'* or *'http://pages.cs.wisc.edu/~anhai/data/784_data/bikes/csv_files/bikedekho.csv'*                        |                       |
   | `gold_standard`                |    ✅     | URL or filename of the gold standard for the dataset in csv format lying in the `directory` specified in the global settings.                          | E.g. *'hpi_cora_hpi_cora_goldstandard.csv'* or *'http://pages.cs.wisc.edu/~anhai/data/784_data/bikes/csv_files/labeled_data.csv'* |                       |
   | `candidate_set`                |    ❌     | URL or filename to the candidate set for the dataset in csv format lying in the `directory` specified in the global settings .                         | E.g. *'bikes_candset.csv'* or *'http://pages.cs.wisc.edu/~anhai/data/784_data/bikes/csv_files/candset.csv'*                       |                       |
   | `similarity_measures: string`  |    ❌     | Similarity measure for string candidate matches. If not specified, the default string similarity measure from the global settings will be applied.     | `jaro`, `jarowinkler`, `levenshtein`, `damerau_levenshtein`, `qgram`, `cosine`, `smith_waterman`, `lcs`                           | `levenshtein`         |
   | `similarity_measures: numeric` |    ❌     | Similarity threshold for numeric candidate matches. If not specified, the default numeric similarity measure from the global settings will be applied. | `step`, `linear`, `exp`, `gauss`, `squared`                                                                                       | `linear`              |


All values should be strings.

#### Example YAML Config
```yaml
global_settings:
  directory: 'data'
  default_phonetic_method: 'soundex'
  default_pair_method: 'sortedneighbourhood'
  default_similarity_measures:
    string: 'jaro'
    numeric: 'exp'

datasets:
  - id: 'freedb_cds'
    tables:
      - 'freedb_cds_freedb_cds.csv'
    phonetic_method: 'soundex'
    gold_standard: 'freedb_cds_freedb_cds_goldstandard.csv'
    similarity_measures:
      numeric: 'gauss'

  - id: 'hpi_cora'
    tables:
      - 'hpi_cora_hpi_cora.csv'
    gold_standard: 'hpi_cora_hpi_cora_goldstandard.csv'
    pair_method: 'block'
    similarity_measures:
      string: 'jarowinkler'

  - id: 'bikes'
    tables:
      - 'http://pages.cs.wisc.edu/~anhai/data/784_data/bikes/csv_files/bikedekho.csv'
      - 'http://pages.cs.wisc.edu/~anhai/data/784_data/bikes/csv_files/bikewale.csv'
    gold_standard: 'http://pages.cs.wisc.edu/~anhai/data/784_data/bikes/csv_files/labeled_data.csv'
    candidate_set: 'http://pages.cs.wisc.edu/~anhai/data/784_data/bikes/csv_files/candset.csv'
```

### Running the Application 🚀

   ```bash
   python src/main.py --config settings/config.yaml
   ```

If no path to a config file is specified, the application will look for a file named `config.yaml` in the `settings` directory by default.

The datasets specified in the config will be either downloaded and saved in the specified directory or loaded from this directory.

A `log/logs.log` file will be created in the repo root directory. It will save all logs from an application run.
