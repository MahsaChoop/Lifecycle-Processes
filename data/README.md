# Data

Place raw databases here before running `main.ipynb`:

| File | Approx. role |
|------|----------------|
| `raw/commitizen.duckdb` | DuckDB export used by anomaly / state extraction |
| `raw/ocel2_commitizen.sqlite` | OCEL2 SQLite used by the utility experiment |

Large binaries (`*.duckdb`, `*.sqlite`, large JSON) are gitignored. Obtain or regenerate them with the legacy notebook `notebooks/legacy/software as an entity.ipynb` (pystackt extraction) if needed.

Expected layout after setup:

```text
data/
  raw/
    commitizen.duckdb
    ocel2_commitizen.sqlite
  README.md
```
