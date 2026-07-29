# Lifecycles-Processes

Process-mining analysis of software lifecycles on the **Commitizen** GitHub repository.


## Layout

```text
Lifecycles-Processes/
  main.ipynb              # run top-to-bottom
  functions/              # analysis modules 
  data/raw/               # place DuckDB + OCEL2 SQLite here 
  results/tables/         # CSV outputs
  results/figures/        # Figures in v and PDF formats
  docs/                   # motivation, threats to validity and future works idea
  notebooks/legacy/       # retired projects
```

## Setup

1. Create a Python 3.10+ environment and install dependencies:

```bash
pip install -r requirements.txt
```

2. Place raw databases under `data/raw/` (see `data/README.md`):

- `commitizen.duckdb`
- `ocel2_commitizen.sqlite`

3. Open and run `main.ipynb` from the repository root (so `import functions` resolves).

## Analysis order (`main.ipynb`)

1. Load DuckDB tables and build weekly issue counts  
2. Rolling IQR anomaly detection + lexicon state extraction  
3. Export anomaly object/event IDs  
4. Anomaly figures  
5. Commit-message context and Conventional Commit classification  
6. Flatten OCEL2 issue log  
7. Vitalizing subset from anomaly object IDs  
8. Preprocess (two valid ends, `MAX_REP=5`) + random control (`SEED=40`)  
9. Discovery evaluation (Alpha / Heuristics / Inductive) → F1 table  
10. Utility figures  
11. Log complexity metrics via `process-complexity`  
12. Multi-seed reproducibility for the random control  

Outputs are written under `results/tables/` and `results/figures/`.

## Key constants (unchanged)

| Setting | Value |
|---------|-------|
| IQR window / min_periods / multiplier | 30 / 8 / 1.5 |
| Closure event type id | 105 |
| Commit event type id | 43 |
| Utility `SEED` | 40 |
| `MAX_REP` | 5 |
| Valid ends | `closed`, `head_ref_deleted` |
| Repro seeds | 0–9 |

## Citation



