# Lifecycles-Processes

Modeling and Analyzing Software Development as a Lifecycle Process.

## What is the layout of the repo

```text
Lifecycles-Processes/
  commitizen.ipynb                    # main study; run top to bottom
  evaluation-ablation study.ipynb     # compare partitions across five repositories
  functions/                          # analysis modules and per-repo configs
  data/                               # extraction notebook, raw databases, token file
    data extraction.ipynb
    raw/                              # DuckDB and OCEL2 SQLite files
    README.md                         # how to extract raw data
  results/
    tables/                           # CSV and Excel outputs
    figures/                          # figures (PNG and PDF)
    figures_no_titles/                # the same figures without titles
  replication/                        # same pipeline for yargs, semantic-release, TradingAgents, Vibe-Trading, and Qlib
  docs/                               # motivation notes (motivation and curiosity.ipynb)
  requirements.txt
```

## How to extract data? (If you want to replicate from scratch with your own target repository)

1. Install dependencies from the repository root: `pip install -r requirements.txt`.
  (ATTENTION: Do not trust me and always read what you are installing.)
2. Create a gitignored GitHub token file at `data/configToken.py`.
   (ATTENTION: Do not commit your personal token in public.)
3. Run `data/data extraction.ipynb` (working directory: `data/`) to build the DuckDB and OCEL2 SQLite files under `data/raw/`.

Full steps, code snippet, and expected outputs: see [data/README.md](data/README.md).

Thanks to Lien Bosmans for developing [pystackt](https://github.com/LienBosmans/pystackt).

## How to run `commitizen.ipynb`?

1. Use Python 3.10+ and install dependencies from the repository root:

```bash
pip install -r requirements.txt
```

2. Place these files in `data/raw/` (extract them first if they are not there yet):

   - `commitizen.duckdb`
   - `ocel2_commitizen.sqlite`

3. Open and run `commitizen.ipynb` from the repository root so `import functions` resolves.

4. The notebook calls `load_dataset_config("commitizen")`. Tables go to `results/tables/commitizen/`. Figures go to `results/figures/commitizen/` and `results/figures_no_titles/commitizen/`.

5. Petri-net cells (steps 8, 9, and 9b) need Graphviz on `PATH`. The notebook includes a Windows cell that adds `C:\Program Files\Graphviz\bin`.

## What are the analyses in `commitizen.ipynb`?

Each step calls into `functions/` and writes CSVs and figures under `results/`. Labels below are the notebook section ids.

- **1. Load DuckDB and weekly issue counts.** Load the OCED tables and build the weekly open and closed issue series.
- **2. Rolling IQR anomaly detection.** Flag anomalous weeks with a rolling interquartile range (`is_anomaly`) and an `anomaly_score`.
- **3. Export anomaly object and event IDs.** Save object and event IDs from closed-issue events in anomalous weeks so later steps can subset the log.
- **4. Anomaly figures.** Plot weekly activity, rolling IQR bands, flagged weeks, and anomaly scores.
- **5. Commit context and Conventional Commit classification.** Link commits to issues that closed in anomalous weeks through a shared `event_id`, classify the messages, and plot stacked weekly categories.
- **6. Flatten the OCEL2 issue log.** Convert the OCEL2 SQLite export into a flat issue-level event log.
- **7a. Category-log preprocess.** Keep traces that contain `closed` or `head_ref_deleted`, then drop traces where any activity repeats more than `CATEGORY_MAX_REP` times.
- **7b. Commit-category logs and discovery F1.** Split the cleaned log into disjoint commit-category logs, plus the whole log, and score F1 with `DISCOVERY_MINERS` (inductive IMF 0.2, split miner, heuristics).
- **7c. Anomaly vs normal and discovery F1.** Split the cleaned log by anomaly object IDs. The whole-log F1 is the one already computed in 7b.
- **7d. Anomaly × category and discovery F1.** Cross anomaly and normal with the category logs, then write `consolidated_results_tables.xlsx`.
- **7e. Random 10-bucket partition.** Shuffle the cleaned log into 10 nearly equal buckets, repeat for seeds 42–51, and score discovery F1. Results go to `random partitioning 10 buckets.xlsx`.
- **7f. Trace clustering.** Cluster the cleaned log into 10 trace clusters and score discovery F1. Results go to `trace clustering 10 clusters.xlsx`.
- **8. Petri nets by commit category.** Discover one net per disjoint category with `inductive_IMf_noise_0.2`.
- **9. Petri nets by anomaly, normal, and whole.** Run the same miner on the anomaly, normal, and whole logs.
- **9b. Petri net of the whole log.** Discover one net for the preprocessed whole log and save it as a PDF without a log-name title.
- **11a. Prepare process-complexity.** Clone [process-complexity](https://github.com/MaxVidgof/process-complexity) if it is not already present, then load its EPA metrics (entropy, magnitude, variety, and affinity).
- **11b. EPA for commit-category logs.** Compute those metrics on the category partitions.
- **11c. EPA for anomaly vs normal.** Compute those metrics on the anomaly and normal logs.
- **11d. EPA for anomaly × category.** Compute those metrics on the crossed partitions.
- **11e. Combine EPA tables.** Write the three EPA tables into `epa_complexity_tables.xlsx`.
- **11f. EPA for random 10-bucket partitions.** Repeat the 7e split and record affinity and normalized sequence entropy in `random partitioning 10 buckets epa.xlsx`.
- **11g. EPA for trace clustering.** Recluster the cleaned log into 5 trace clusters and record affinity and normalized sequence entropy in `trace clustering 5 clusters epa.xlsx`.

## What are the analyses in the ablation study?

[`evaluation-ablation study.ipynb`](evaluation-ablation%20study.ipynb) compares log partitioning across five repositories (Commitizen, yargs, semantic-release, TradingAgents, and Vibe-Trading) using the same three miners as Commitizen.

Run `commitizen.ipynb` and the replication notebooks for yargs, semantic-release, TradingAgents, and Vibe-Trading through step 11e first. Each of those repositories needs `consolidated_results_tables.xlsx` and `epa_complexity_tables.xlsx`.

1. **Whole-log descriptives.** Case and event counts, cycle time, and related stats per repository.
2. **F-score ablation.** Whole-log F1 against case-weighted F1 on the anomaly/normal, commit-category, and anomaly×category partitions.
3. **Model complexity ablation.** The same partitions, scored on size, CFC, and simplicity.
4. **EPA complexity ablation.** The same partitions, scored on affinity and normalized variant and sequence entropy.
5. **Cycle-time comparison.** Commitizen plot of average cycle time by category, for normal and anomaly weeks.

Outputs go to `results/tables/compare/` and the Commitizen figure folders.
