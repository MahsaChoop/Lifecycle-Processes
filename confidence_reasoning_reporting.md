# Reporting confidence and reasoning (article draft)

Copy-ready text for the Methods, Results, and Discussion sections. Statistics and examples are taken from `anomaly_states.csv` (Commitizen case study, 25 rolling-IQR anomaly weeks).

---

## Methods — textual state extraction

### Reasoning

For each flagged week, a single reasoning sentence is generated from a fixed template. It states (i) the direction and magnitude of the closure anomaly relative to the rolling IQR band, (ii) the number of supporting issue titles and events, (iii) the dominant component area(s) from the component lexicon, (iv) up to four frequent content terms after stop-word removal, and (v) severity signal words when present. The sentence is rule-composed for traceability; it is not produced by a language model.

### Confidence

Label confidence is computed separately from label selection. For the chosen severity and component, we measure **lexicon dominance**: the share of severity-keyword hits attributed to the winning severity class, and analogously for the top component class. When both lexicons match, dominance is `0.7 × severity_share + 0.3 × component_share`; otherwise the available share is used. The score `γ = 0.30 + 0.65 × dominance` is increased by 0.05 when at least one unique title is present and decreased by 0.10 when severity was inferred from the numeric anomaly detector rather than from text keywords. Values are clipped to [0.30, 0.95]. Higher scores indicate clearer, less ambiguous keyword evidence; lower scores indicate mixed lexicon signals or fallback labelling.

**Terminology:** report `confidence` as a **lexicon-support score** or **evidence score**, not as a calibrated probability.

---

## Results — summary

Each anomalous week is accompanied by a one-sentence reasoning field that summarizes the closure deviation, the supporting issue titles, the dominant component area, recurring terms, and any severity keywords detected in the text. Confidence scores range from 0.30 to 0.95 and reflect how strongly the issue-title lexicon supports the assigned severity and component, with lower values indicating mixed keyword evidence or numeric fallback labelling.

### Table 1 — Summary of extracted anomaly states (Commitizen)

| Statistic | Value |
|-----------|-------|
| Anomalous weeks | 25 |
| Confidence (min / median / max) | 0.55 / 0.68 / 0.88 |
| Confidence (mean ± SD) | 0.68 ± 0.07 |
| Severity: P4 / P3 / P2 / P1 | 16 / 7 / 1 / 1 |
| Top components | documentation (8), version & bump (7), build & ci (5), dependencies (2), testing (2) |

### Table 2 — Illustrative anomaly states

| week_start | value | direction | severity | component | confidence | reasoning (verbatim) |
|------------|------:|-----------|----------|-----------|----------:|----------------------|
| 2019-11-25 | 4 | high | P4 | documentation | 0.88 | Weekly closures show a slightly beyond-typical spike (4 vs upper bound 4), covering 4 unique titles across 4 events, focused on documentation, version & bump, with recurring terms like check, different, docs, documentation, flagged by P4 signal words. |
| 2023-04-17 | 21 | high | P4 | dependencies | 0.68 | Weekly closures show a well beyond-typical spike (21 vs upper bound 8), covering 21 unique titles across 21 events, focused on dependencies, build & ci, with recurring terms like bump, build, poetry, deps, flagged by P2/P3 signal words. |
| 2019-11-11 | 4 | high | P2 | build & ci | 0.55 | Weekly closures show a near-typical spike (4 vs upper bound 1), covering 4 unique titles across 4 events, focused on build & ci, dependencies, with recurring terms like exception, occurs, subject, not, flagged by P2/P3 signal words. |

The first row illustrates **high lexicon-support** (unambiguous P4/documentation signals). The third row illustrates **lower support** (mixed P2/P3 severity keywords and competing component areas). The middle row is near the cohort median.

### Optional figure caption

*Lexicon-support scores for detected anomaly weeks (Commitizen), ranked by confidence and coloured by severity. Scores reflect keyword dominance in issue titles, not calibrated probabilities.*

---

## Discussion — limitations

Confidence and reasoning are heuristic outputs of the lexicon classifier; they have not been validated against expert annotations and should be read as transparent summaries of the evidence used, not as posterior probabilities.

### What to claim

- Confidence reflects **ambiguity vs. clarity of lexicon matches**.
- Reasoning links **quantitative anomaly** (IQR band, direction) with **qualitative text cues** (components, terms, severity keywords).
- Both fields support **interpretability and traceability** of automated state labels.

### What to avoid

- Do not interpret confidence as “probability the label is correct.”
- Do not describe reasoning as LLM-generated (it is template-based).
- Do not rank weeks by “true severity” from confidence alone without manual review.
