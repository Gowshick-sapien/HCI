# Empirical User Study Session Report

## 1. Metadata & Participant Profile
* **Participant ID**: `P01`
* **Evaluation Timestamp**: `2026-09-07 09:48:46`
* **Study Design**: Counterbalanced $4 \times 4$ Williams Latin Square
* **Total Trials Evaluated**: `64`
* **Raw Dataset Artifact**: [`user_study_dataset_20260907_094846.csv`](./user_study_dataset_20260907_094846.csv)

---

## 2. Experimental Condition Performance Summary

| Condition ID | Description | Sample Size | Mean MT (ms) | Error Rate (%) | Throughput (bps) | Gaze Conf | Head Conf | Hand Conf |
|---|---|---|---|---|---|---|---|---|
| **C1** | Static Baseline Fusion | 16 | 849.6 ± 84.3 | 18.8% | 4.39 | 0.82 | 0.85 | 0.80 |
| **C2** | Heuristic Rules Switching | 16 | 726.7 ± 63.0 | 18.8% | 5.18 | 0.85 | 0.88 | 0.82 |
| **C3** | Micro-SGD Only | 16 | 608.8 ± 65.0 | 0.0% | 6.11 | 0.90 | 0.90 | 0.89 |
| **C4** | Full Dual-Scale Adaptive | 16 | 491.9 ± 58.9 | 0.0% | 7.59 | 0.94 | 0.94 | 0.92 |

---

## 3. Inferential Hypothesis Testing (C1 Baseline vs. C4 Proposed)

* **Movement Time Reduction**: `+42.10%`
* **Error Rate Absolute Reduction**: `+18.75%`
* **ISO 9241-9 Throughput Gain**: `+72.79%`
* **Wilcoxon Signed-Rank Test**: $W = 0.00, \quad p = 0.0004$
* **Effect Size (Cohen's d)**: $d = 3.40$
* **Statistical Significance**: `SIGNIFICANT (p < 0.05)`

---

## 4. Runtime Adaptation & Stability Diagnostics

* *No real-time adaptation metrics attached for this session.*
