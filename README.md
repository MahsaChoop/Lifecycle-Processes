# Lifecycles-Processes

Process-mining analysis of software lifecycles on the GitHub repositories.

## What is the layout of the repo

```text
Lifecycles-Processes/
  main.ipynb              # main Commitizen analysis pipeline (run top-to-bottom)
  functions/              # analysis modules and per-repo configs/
  data/                   # extraction notebook, raw DBs, token config
    data extraction.ipynb
    raw/                  # place DuckDB + OCEL2 SQLite here
    README.md             # how to extract raw data
  results/
    tables/               # CSV outputs
    figures/              # figures (PNG + PDF)
    figures_no_titles/    # untitled figure copies
  replication/            # per-repo notebooks (FinRL, OpenBB, …)
  docs/                   # motivation, threats to validity, future work
  requirements.txt
```

## How to extract data? (Is you want to replicate from scratch with your own target repository)

1. Install dependencies from the repository root: `pip install -r requirements.txt`. ATTENTION: Do not trust me and always read what you are installing.
2. Create a gitignored GitHub token file at `data/configToken.py`. ATTENTION: Do not commit your personal token in public.
3. Run `data/data extraction.ipynb` (working directory: `data/`) to build the DuckDB and OCEL2 SQLite files under `data/raw/`.

Full steps, code snippet, and expected outputs: see [data/README.md](data/README.md).

## How to run `main.ipynb`?

1. Use Python 3.10+ and install dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure these files exist under `data/raw/` (extract them first if needed):

- `commitizen.duckdb`
- `ocel2_commitizen.sqlite`

3. Open and run `main.ipynb` from the **repository root** so `import functions` resolves.

4. The notebook defaults to `load_dataset_config("commitizen")`. Outputs go to `results/tables/commitizen/` and `results/figures/commitizen/`.

## What are the analyses in `main.ipynb`?

1. **Load DuckDB + weekly issue counts** — Load OCED tables and build weekly open/closed issue activity series.
2. **Rolling IQR anomaly detection** — Flag anomalous weeks with rolling IQR (`is_anomaly`) and an `anomaly_score`.
3. **Export anomaly object/event IDs** — Save object and event IDs from closed-issue events in anomalous weeks for downstream subsetting.
4. **Anomaly figures** — Plot weekly activity, rolling IQR bands, flagged weeks, and anomaly scores.
5. **Commit context + Conventional Commit classification** — Link commits to issues that closed in anomalous weeks via a shared `event_id`, classify those messages, and map types to overlapping categories (feature, bug, tech debt, docs, other).
6. **Flatten OCEL2 issue log** — Convert the OCEL2 SQLite export into a flat issue-level event log.
7. **Vitalizing subset** — Restrict the flat log to issues linked to anomaly object IDs.
8. **Preprocess + random control** — Clean traces (valid ends, `MAX_REP=5`) and build a size-matched random control (`SEED=40`).
9. **Discovery F1 evaluation** — Discover process models (Alpha, Heuristics, Inductive, …) and score fitness, precision, and F1 on the clean logs.
10. **Utility figures** — Compare vitalizing, control, and whole logs with bar, slope, and sensitivity plots.
11. **Multi-seed reproducibility** — Re-run the random control over seeds 0–9 to check stability of utility results.
12. **Cross-repo F-score comparison** — Aggregate replication F1 tables across repositories and plot miner comparisons.

Each step calls into `functions/` and writes CSVs/figures under `results/`.



