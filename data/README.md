# Data

Raw inputs for the analyses are extracted from the GitHub REST API with [pystackt](https://github.com/LienBosmans/pystackt) (via PyGitHub). Issues, commits, events, users, and labels are stored in DuckDB as Object-Centric Event Data (OCED), then optionally exported to OCEL 2.0 SQLite.

## Prerequisites

From the repository root:

```bash
pip install -r requirements.txt
```

You also need a GitHub personal access token that can read the target public repository.

## Token file

Create `data/configToken.py` (this path is gitignored; do not commit it):

```python
GITHUB_ACCESS_TOKEN = "YOUR_GITHUB_PAT"
```

## Extract Commitizen (main study)

Open [`data extraction.ipynb`](data%20extraction.ipynb) with the working directory set to `data/` (paths such as `raw/...` are relative).

Run the Commitizen cells, then add `prepare_graph_data` if it is not already in that block (analysis loading expects `graph_data_prep.graph_base_table`):

```python
from pystackt import (
    get_github_log,
    export_to_ocel2,
    create_statistics_views,
    prepare_graph_data,
)
from configToken import GITHUB_ACCESS_TOKEN

DUCKDB_PATH = "raw/commitizen.duckdb"
SQLITE_PATH = "raw/ocel2_commitizen.sqlite"

get_github_log(
    GITHUB_ACCESS_TOKEN=GITHUB_ACCESS_TOKEN,
    repo_owner="commitizen-tools",
    repo_name="commitizen",
    max_issues=None,
    quack_db=str(DUCKDB_PATH),
    schema="main",
)

export_to_ocel2(
    quack_db=DUCKDB_PATH,
    schema_in="main",
    schema_out="ocel2",
    sqlite_db=SQLITE_PATH,
)

create_statistics_views(
    quack_db=DUCKDB_PATH,
    schema_in="main",
    schema_out="statistics",
)

prepare_graph_data(
    quack_db=DUCKDB_PATH,
    schema_in="main",
    schema_out="graph_data_prep",
)
```

Pipeline order:

1. `get_github_log` → writes `raw/commitizen.duckdb`
2. `export_to_ocel2` → writes `raw/ocel2_commitizen.sqlite`
3. `create_statistics_views` → optional statistics schema
4. `prepare_graph_data` → creates `graph_data_prep.graph_base_table` required by `main.ipynb`

## Expected outputs

| File | Role |
|------|------|
| `data/raw/commitizen.duckdb` | OCED DuckDB for weekly counts, anomalies, and commits |
| `data/raw/ocel2_commitizen.sqlite` | OCEL2 export flattened in `main.ipynb` |

## Other repositories

The same notebook has cells for TradingAgents, FinGPT, FinRL, OpenBB, Qlib, Vibe-Trading, Nautilus Trader, and related projects. They write matching `raw/*.duckdb` and `raw/*.sqlite` files used by notebooks under `replication/`.

## Tips

- Extraction can take a long time because of GitHub API rate limits.
- More tutorials: [pystackt docs](https://lienbosmans.github.io/pystackt/) and [LienBosmans/pystackt](https://github.com/LienBosmans/pystackt).
