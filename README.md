# Lifecycles-Processes

Process-mining analysis of software lifecycles on the **Commitizen** GitHub repository (OCEL2). The pipeline detects weekly anomaly states (rolling IQR + lexicon severity/component) and evaluates whether a vitalizing sublog improves discovery quality versus whole-log and random-control baselines.

Algorithms, thresholds, seeds, lexicons, and miner settings match the original notebooks; this repository only reorganizes code into a `functions/` package and portable paths.

## Layout

```text
Lifecycles-Processes/
  main.ipynb              # run top-to-bottom
  functions/              # analysis modules (no algorithm changes)
  data/raw/               # place DuckDB + OCEL2 SQLite here (gitignored)
  results/tables/         # CSV outputs
  results/figures/        # PNG figures
  docs/                   # reporting drafts, threats to validity
  notebooks/legacy/       # original notebooks (kept for history)
  process-complexity/     # vendored EPA complexity toolkit
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

The complexity metrics use the vendored [process-complexity](process-complexity/) toolkit (EPA / graph entropy style measures). Prefer citing the upstream project if you publish results that rely on those metrics.

## Legacy notebooks

Original notebooks remain under `notebooks/legacy/` for reference. Prefer `main.ipynb` for new runs.
