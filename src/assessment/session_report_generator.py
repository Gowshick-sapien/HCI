"""
Assessment Subsystem: Automated Research Session Report Synthesizer.
Synthesizes publication-grade Markdown experimental reports, LaTeX statistical tables,
and standardized CSV datasets for open-science replication.
"""

from __future__ import annotations

import csv
import datetime
import io
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

from src.evaluation.statistical_analyzer import StatisticalAnalyzer, ConditionStatistics, StatisticalComparison
from src.evaluation.study_manager import ExperimentalCondition, TrialResult
from src.storage.schemas import AssessmentMetrics


class SessionReportGenerator:
    """
    Synthesizes formatted Markdown summary reports and standardized CSV trial datasets.
    """

    def __init__(self, output_dir: Optional[str] = None) -> None:
        if output_dir is None:
            self.output_dir = Path(__file__).resolve().parent.parent.parent / "deliverables" / "E3_research_dashboard"
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_csv_dataset(self, results: List[TrialResult], filename: Optional[str] = None) -> str:
        """
        Exports trial results to a standardized CSV dataset file.
        Returns:
            Absolute filepath string of the exported CSV file.
        """
        if not filename:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"user_study_dataset_{ts}.csv"

        filepath = self.output_dir / filename
        fieldnames = [
            "participant_id",
            "condition",
            "block_index",
            "trial_index",
            "target_id",
            "index_of_difficulty",
            "movement_time_ms",
            "is_successful",
            "error_count",
            "overshoot_count",
            "mean_gaze_confidence",
            "mean_head_confidence",
            "mean_hand_confidence",
            "effective_throughput",
            "timestamp"
        ]

        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "participant_id": r.participant_id,
                    "condition": r.condition.value,
                    "block_index": r.block_index,
                    "trial_index": r.trial_index,
                    "target_id": r.target_id,
                    "index_of_difficulty": round(r.index_of_difficulty, 4),
                    "movement_time_ms": round(r.movement_time_ms, 2),
                    "is_successful": int(r.is_successful),
                    "error_count": r.error_count,
                    "overshoot_count": r.overshoot_count,
                    "mean_gaze_confidence": round(r.mean_gaze_confidence, 4),
                    "mean_head_confidence": round(r.mean_head_confidence, 4),
                    "mean_hand_confidence": round(r.mean_hand_confidence, 4),
                    "effective_throughput": round(r.effective_throughput, 4),
                    "timestamp": r.timestamp
                })

        return str(filepath)

    def generate_markdown_report(
        self,
        participant_id: str,
        results: List[TrialResult],
        metrics: Optional[AssessmentMetrics] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Generates a publication-grade Markdown experimental session report.
        Returns:
            Absolute filepath string of the generated report.
        """
        if not filename:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"empirical_study_report_{participant_id}_{ts}.md"

        filepath = self.output_dir / filename

        # Compute condition statistics
        conditions = [
            ExperimentalCondition.C1_STATIC_BASELINE,
            ExperimentalCondition.C2_HEURISTIC_RULES,
            ExperimentalCondition.C3_MICRO_SGD_ONLY,
            ExperimentalCondition.C4_FULL_ADAPTIVE
        ]
        cond_stats = [StatisticalAnalyzer.aggregate_condition(results, c) for c in conditions]
        comp = StatisticalAnalyzer.compare_conditions(results)

        csv_path = self.export_csv_dataset(results)
        csv_rel = os.path.basename(csv_path)

        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report_content = f"""# Empirical User Study Session Report

## 1. Metadata & Participant Profile
* **Participant ID**: `{participant_id}`
* **Evaluation Timestamp**: `{timestamp_str}`
* **Study Design**: Counterbalanced $4 \\times 4$ Williams Latin Square
* **Total Trials Evaluated**: `{len(results)}`
* **Raw Dataset Artifact**: [`{csv_rel}`](./{csv_rel})

---

## 2. Experimental Condition Performance Summary

| Condition ID | Description | Sample Size | Mean MT (ms) | Error Rate (%) | Throughput (bps) | Gaze Conf | Head Conf | Hand Conf |
|---|---|---|---|---|---|---|---|---|
| **C1** | Static Baseline Fusion | {cond_stats[0].sample_size} | {cond_stats[0].mean_movement_time_ms:.1f} ± {cond_stats[0].std_movement_time_ms:.1f} | {cond_stats[0].error_rate_pct:.1f}% | {cond_stats[0].mean_throughput_bps:.2f} | {cond_stats[0].mean_gaze_confidence:.2f} | {cond_stats[0].mean_head_confidence:.2f} | {cond_stats[0].mean_hand_confidence:.2f} |
| **C2** | Heuristic Rules Switching | {cond_stats[1].sample_size} | {cond_stats[1].mean_movement_time_ms:.1f} ± {cond_stats[1].std_movement_time_ms:.1f} | {cond_stats[1].error_rate_pct:.1f}% | {cond_stats[1].mean_throughput_bps:.2f} | {cond_stats[1].mean_gaze_confidence:.2f} | {cond_stats[1].mean_head_confidence:.2f} | {cond_stats[1].mean_hand_confidence:.2f} |
| **C3** | Micro-SGD Only | {cond_stats[2].sample_size} | {cond_stats[2].mean_movement_time_ms:.1f} ± {cond_stats[2].std_movement_time_ms:.1f} | {cond_stats[2].error_rate_pct:.1f}% | {cond_stats[2].mean_throughput_bps:.2f} | {cond_stats[2].mean_gaze_confidence:.2f} | {cond_stats[2].mean_head_confidence:.2f} | {cond_stats[2].mean_hand_confidence:.2f} |
| **C4** | Full Dual-Scale Adaptive | {cond_stats[3].sample_size} | {cond_stats[3].mean_movement_time_ms:.1f} ± {cond_stats[3].std_movement_time_ms:.1f} | {cond_stats[3].error_rate_pct:.1f}% | {cond_stats[3].mean_throughput_bps:.2f} | {cond_stats[3].mean_gaze_confidence:.2f} | {cond_stats[3].mean_head_confidence:.2f} | {cond_stats[3].mean_hand_confidence:.2f} |

---

## 3. Inferential Hypothesis Testing (C1 Baseline vs. C4 Proposed)

* **Movement Time Reduction**: `{comp.movement_time_reduction_pct:+.2f}%`
* **Error Rate Absolute Reduction**: `{comp.error_rate_reduction_pct:+.2f}%`
* **ISO 9241-9 Throughput Gain**: `{comp.throughput_gain_pct:+.2f}%`
* **Wilcoxon Signed-Rank Test**: $W = {comp.wilcoxon_w_statistic:.2f}, \\quad p = {comp.wilcoxon_p_value:.4f}$
* **Effect Size (Cohen's d)**: $d = {comp.cohens_d_effect_size:.2f}$
* **Statistical Significance**: `{'SIGNIFICANT (p < 0.05)' if comp.is_statistically_significant else 'NOT SIGNIFICANT (p >= 0.05)'}`

---

## 4. Runtime Adaptation & Stability Diagnostics
"""
        if metrics is not None:
            report_content += f"""
* **Final System Health State**: `[{metrics.health_state.value}]`
* **EWMA Adaptation Gain ($AG_t$)**: `{metrics.adaptation_gain_ewma:+.4f}`
* **Weight Stability Index ($WSI_t$)**: `{metrics.weight_stability_index:.4f}`
* **Expected Calibration Error ($ECE_t$)**: `{metrics.expected_calibration_error:.4f}`
* **Adaptation Confidence Index ($ACI_t$)**: `{metrics.adaptation_confidence_index:.4f}`
* **Total Evaluated Interactions**: `{metrics.interactions_count}`
"""
        else:
            report_content += "\n* *No real-time adaptation metrics attached for this session.*\n"

        with open(filepath, mode="w", encoding="utf-8") as f:
            f.write(report_content)

        return str(filepath)


__all__ = ["SessionReportGenerator"]
