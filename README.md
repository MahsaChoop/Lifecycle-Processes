# Lifecycles-Processes

Modeling and Analyzing Software Development as a Lifecycle Process.

## What is the layout of the repo

```text
Lifecycles-Processes/
  commitizen.ipynb                    # Commitizen analysis pipeline (run top-to-bottom)
  evaluation-ablation study.ipynb     # cross-repo ablation comparison
  functions/                          # analysis modules and per-repo configs/
  data/                               # extraction notebook, raw DBs, token config
    data extraction.ipynb
    raw/                              # place DuckDB + OCEL2 SQLite here
    README.md                         # how to extract raw data
  results/
    tables/                           # CSV outputs
    figures/                          # figures (PNG + PDF)
    figures_no_titles/                # untitled figure copies
  replication/                        # same pipeline for other reposiories (yargs, semantic-release, TradingAgents, Vibe-Trading)
  docs/                               # motivation, threats to validity, future work
  requirements.txt
```

## How to extract data? (If you want to replicate from scratch with your own target repository)

1. Install dependencies from the repository root: `pip install -r requirements.txt`.
  ATTENTION: Do not trust me and always read what you are installing.
2. Create a gitignored GitHub token file at `data/configToken.py`.
   ATTENTION: Do not commit your personal token in public.
3. Run `data/data extraction.ipynb` (working directory: `data/`) to build the DuckDB and OCEL2 SQLite files under `data/raw/`.

Full steps, code snippet, and expected outputs: see [data/README.md](data/README.md).

## How to run `commitizen.ipynb`?

1. Use Python 3.10+ and install dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure these files exist under `data/raw/` (extract them first if needed):

- `commitizen.duckdb`
- `ocel2_commitizen.sqlite`

3. Open and run `commitizen.ipynb` from the **repository root** so `import functions` resolves.

4. The notebook uses `load_dataset_config("commitizen")`. Outputs go to `results/tables/commitizen/`, `results/figures/commitizen/`, and `results/figures_no_titles/commitizen/`.

5. Petri-net cells (steps 8–10) need Graphviz on `PATH` (the notebook includes a Windows cell for `C:\Program Files\Graphviz\bin`).

## What are the analyses in `commitizen.ipynb`?

1. **Load DuckDB + weekly issue counts** — Load OCED tables and build weekly open/closed issue activity series as vital sign.
2. **Rolling IQR anomaly detection** — Flag anomalous weeks with rolling IQR (`is_anomaly`) and an `anomaly_score`.
3. **Export anomaly object/event IDs** — Save object and event IDs from closed-issue events in anomalous weeks for downstream subsetting.
4. **Anomaly figures** — Plot weekly activity, rolling IQR bands, flagged weeks, and anomaly scores.
5. **Commit context + Conventional Commit classification** — Link commits to issues that closed in anomalous weeks via a shared `event_id`, classify those messages, and plot stacked weekly categories.
6. **Flatten OCEL2 issue log** — Convert the OCEL2 SQLite export into a flat issue-level event log.
7. **Discovery F1 on partitioned logs**
   - **Category-log preprocess** — Keep traces that contain `closed` or `head_ref_deleted`.
   - **Commit-category logs + discovery F1** — Isolate the effect of action categories. Split the cleaned log into disjoint category logs (plus whole) and score F1 with `DISCOVERY_MINERS` (inductive IMF 0.2, split miner, heuristics).
   - **Anomaly vs normal + discovery F1** — Isolate the effect of states. Split the cleaned log by anomaly object IDs; reuse whole-log F1 from the category step.
   - **Anomaly × category + discovery F1** — Examine the combination effect: Cross anomaly/normal with the category logs; write `consolidated_results_tables.xlsx`.
8. **Petri nets by commit category** — Discover nets per disjoint category with `inductive_IMf_noise_0.2`.
9. **Petri nets by anomaly, normal, and whole** — Same miner on the anomaly/normal/whole logs.
10. **Example Petri PDF** — Compose and render selected nets (`petri_nets_commit_categories.pdf`).

Each step calls into `functions/` and writes CSVs/figures under `results/`.

## What are the analyses in the ablation study?

[`evaluation-ablation study.ipynb`](evaluation-ablation%20study.ipynb) compares log partitioning across five repositories (Commitizen, yargs, semantic-release, TradingAgents, Vibe-Trading) using the same three miners as Commitizen.

1. **Whole-log descriptives** — Case/event counts, cycle time, and related stats per repo.
2. **F-score ablation** — Whole-log F1 (baseline) vs case-weighted F1 on anomaly/normal, commit-category, and anomaly×category partitions.
3. **Cycle-time comparison** — Commitizen plot of average cycle time by category (normal vs anomaly).

Outputs go to `results/tables/compare/` and the Commitizen figure dirs. Run `commitizen.ipynb` and the replication notebooks first so each repo has `consolidated_results_tables.xlsx`.
