# Data

This folder turns any public GitHub repository into an event log you can analyze.

```text
GitHub API  ->  DuckDB (object-centric event data)  ->  OCEL 2.0 SQLite
```

Extraction uses [pystackt](https://github.com/LienBosmans/pystackt) (via PyGitHub). It collects issues, commits, events, users, and labels.

## Extract your own repository

1. **Install dependencies** (from the repository root):

   ```bash
   pip install -r requirements.txt
   ```

2. **Create a GitHub token.** In GitHub, go to *Settings > Developer settings > Personal access tokens*. A token that can read public repositories is enough.

3. **Save the token** in `data/configToken.py`. This file is gitignored. Never commit it.

   ```python
   GITHUB_ACCESS_TOKEN = "YOUR_GITHUB_TOKEN"
   ```

Then open [`data extraction.ipynb`](data%20extraction.ipynb) with the working directory set to `data/` (the `raw/` paths are relative to it). It has ready-made cells for every repository in the study. Copy one and change the repository owner and name.

## What you get

| Output | Used for |
|--------|----------|
| `raw/<repo>.duckdb` | Weekly counts, anomalies, commits, and the `graph_data_prep.graph_base_table` table |
| `raw/<repo>.sqlite` | OCEL 2.0 log that the analysis notebooks flatten |

## Use it in the analysis

- File paths are set per repository in `functions/configs/` (for example `commitizen.py`).
- `commitizen.ipynb` (repository root) expects `raw/commitizen.duckdb` and `raw/ocel2_commitizen.sqlite`.
- To analyze your own repository, either save your files under those names or edit `DUCKDB_PATH` and `SQLITE_PATH` in the matching config.
- The notebooks in `replication/` use the other configs (for example `raw/Qlib.duckdb` and `raw/Qlib.sqlite`).

## Data already included

- `raw/` holds the databases for the study repositories.
- `event logs/` holds the cleaned whole log of each dataset as a zipped XES file (one `.xes` per zip): `commitizen`, `TradingAgents`, `Vibe-Trading`, `Qlib`, `yargs`, and `semantic-release`.

## Tips

- Extraction can take a long time because of GitHub API rate limits. Test with `max_issues=100` first.
- More tutorials: [pystackt docs](https://lienbosmans.github.io/pystackt/).
