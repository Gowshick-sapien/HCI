# Spiral 7 Implementation Plan: Interactive Empirical Research Dashboard & Diagnostics Suite (Deliverable E3)

## 1. Executive Overview
Spiral 7 delivers **Deliverable E3 (Interactive Empirical Research Dashboard & Diagnostics Suite)**. Building upon the entire multimodal architecture stack (Perception D1, Fusion D2, Calibration D3, Feedback D4, Adaptation D5, and Explainability HUD E2), Spiral 7 provides a dedicated multi-tab GUI control panel for empirical researchers and system evaluators to observe real-time system metrics, monitor live SPRT trajectories, inspect parameter evolution curves, execute counterbalanced Latin Square A/B user studies, and automatically synthesize publication-grade statistical analysis reports.

---

## 2. Architectural Structure & Module Decomposition

### 2.1 Multi-Tab Research Dashboard GUI (`src/ui/research_dashboard.py`)
* **Asynchronous Multi-Threaded Architecture**: Runs in an asynchronous GUI thread decoupled from the core 30 FPS perception and fusion pipelines, ensuring zero latency degradation on real-time multimodal control.
* **Unified Control Hub**:
  * **Tab 1: Live Telemetry Stream**: Real-time event monitor for actions, feedback, and arbitration states.
  * **Tab 2: Parameter Evolution**: Dynamic plotting of weight vectors and threshold trajectories.
  * **Tab 3: SPRT Drift & Gatekeeper**: Real-time log-likelihood trajectory and decision boundary gauges.
  * **Tab 4: Latin Square Study Runner**: Interactive protocol manager for isomorphic A/B evaluation trials.
  * **Tab 5: Statistical Analytics & Reports**: On-demand non-parametric significance testing and automated markdown report generation.

---

### 2.2 Telemetry Stream Viewer (`src/ui/telemetry_stream_viewer.py`)
* **Streaming Table Component**: Renders `ActionContext`, `FeedbackEvent`, and `GatekeeperVerdict` records in a scrolling data table with color-coded success/failure indicators.
* **Filtering & Export**: Supports filtering by modality, failure mode, and feedback polarity, with one-click JSON/CSV dataset export.

---

### 2.3 Parameter Evolution Visualizer (`src/ui/parameter_evolution_plot.py`)
* **Live Matplotlib / Qt Canvas**: Plots the time-series trajectory of modality weights $\mathbf{w}_t = [w_{\text{eye}}, w_{\text{head}}, w_{\text{hand}}]$ and activation thresholds $\theta_t$ over continuous interaction epochs.
* **Simplex Boundary Indicators**: Displays upper ($0.85$) and lower ($0.05$) simplex box constraints to visualize micro-adaptation bounds.

---

### 2.4 SPRT Trajectory Gauge (`src/ui/sprt_trajectory_gauge.py`)
* **Cumulative Log-Likelihood Ratio Monitor**: Plots the rolling SPRT score $\Lambda_n = \sum \ln \frac{P(x_i \mid H_1)}{P(x_i \mid H_0)}$ in real time.
* **Decision Threshold Visualizers**: Renders upper approval/drift boundary ($A = 2.89$) and lower reset boundary ($B = -2.25$) with alert states.

---

### 2.5 Latin Square Empirical Study Runner (`src/ui/latin_square_panel.py`, `src/evaluation/study_manager.py`)
* **Counterbalanced $4 \times 4$ Design**: Automates Latin Square condition ordering:
  * $C_1$: Static Fixed-Weight Fusion (Baseline)
  * $C_2$: Heuristic Rule-Based Switching
  * $C_3$: Micro-SGD Gradient Descent Only
  * $C_4$: Full Dual-Scale Adaptive Multimodal Architecture (Proposed)
* **Standardized Task Automation**: Manages ISO 9241-9 pointing and command trial blocks, automated target presentation, timing, and error recording.

---

### 2.6 Statistical Analyzer & Session Report Synthesizer (`src/evaluation/statistical_analyzer.py`, `src/assessment/session_report_generator.py`)
* **Inferential Statistics**: Computes Wilcoxon Signed-Rank Tests, Friedman ANOVA, effect sizes (Cohen's $d$), and throughput ($TP = \frac{ID}{MT}$).
* **Report Synthesizer**: Generates formatted Markdown summaries with embedded summary tables, convergence metrics, and hypothesis testing results.

---

## 3. Formal Invariant Specifications

| Invariant ID | Target Component | Formal Acceptance Criterion | Verification Method |
|---|---|---|---|
| **INV-E3.1** | `research_dashboard.py` | Dashboard telemetry updates execute in $< 100\text{ ms}$ without dropping perception pipeline frame rates below 30 FPS. | Automated Benchmark |
| **INV-E3.2** | `telemetry_stream_viewer.py` | Telemetry viewer correctly formats and displays all action and feedback fields with zero table truncation. | Automated Unit Test |
| **INV-E3.3** | `parameter_evolution_plot.py` | Trajectory plot tracks $\mathbf{w}_t \in \Delta^2$ with monotonic step recording and boundary enforcement. | Automated Unit Test |
| **INV-E3.4** | `sprt_trajectory_gauge.py` | SPRT gauge correctly tracks cumulative log-likelihood $\Lambda_n$ and visualizes boundaries ($A = 2.89, B = -2.25$). | Automated Unit Test |
| **INV-E3.5** | `study_manager.py` | Latin Square coordinator generates exact orthogonal counterbalanced condition sequences across participant IDs. | Automated Unit Test |
| **INV-E3.6** | `statistical_analyzer.py` | Statistical analyzer computes valid Wilcoxon $p$-values, effect sizes, and ISO throughput metrics without division-by-zero. | Automated Unit Test |
| **INV-E3.7** | `session_report_generator.py` | Synthesizes clean Markdown reports and CSV datasets within $< 500\text{ ms}$ at session close. | Automated Integration |

---

## 4. Implementation Phasing

### Phase 1: Evaluation Core & Statistical Analyzer
* Implement `StudyManager` with $4 \times 4$ Latin Square counterbalancing.
* Implement `StatisticalAnalyzer` (Wilcoxon Signed-Rank, Friedman, Cohen's $d$, ISO 9241-9 Throughput).
* Implement `SessionReportGenerator` for automated Markdown and CSV synthesis.
* Unit tests in `tests/unit/test_study_manager.py` and `tests/unit/test_statistical_analyzer.py`.

### Phase 2: Live Plotting & Telemetry UI Components
* Implement `TelemetryStreamViewer` with searchable table model.
* Implement `ParameterEvolutionPlot` with dynamic Matplotlib/Qt canvas.
* Implement `SPRTTrajectoryGauge` with interactive score boundaries.
* Unit tests in `tests/unit/test_telemetry_stream_viewer.py` and `tests/unit/test_sprt_trajectory_gauge.py`.

### Phase 3: Research Dashboard GUI & Study Control Panel
* Implement `LatinSquarePanel` for automated study block execution.
* Implement `ResearchDashboardWindow` combining all 5 tabs.
* Public exports in `src/ui/__init__.py`, `src/evaluation/__init__.py`, and `src/assessment/__init__.py`.

### Phase 4: Integration, Benchmarking & Standalone Runner
* Integration test `tests/integration/test_research_dashboard_pipeline.py`.
* Performance benchmark `tests/benchmarks/test_dashboard_latency.py`.
* Standalone executable script `scripts/launch_research_dashboard.py`.
