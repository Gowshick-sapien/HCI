# Spiral 7 Verification Protocol: Interactive Empirical Research Dashboard & Diagnostics Suite (Deliverable E3)

## 1. Scope & Objective
This document defines the formal verification protocol for **Deliverable E3 (Interactive Empirical Research Dashboard & Diagnostics Suite)**. It specifies automated unit tests, integration tests, latency benchmarks, and manual interactive trial verification procedures.

---

## 2. Formal Invariants Verification Matrix

| Test Identifier | Invariant ID | Target Component | Formal Acceptance Criterion | Verification Type |
|---|---|---|---|---|
| **AUT-E3-01** | `INV-E3.1` | `research_dashboard.py` | Dashboard async telemetry event push executes in $< 100\text{ ms}$ without UI blocking. | Automated Benchmark |
| **AUT-E3-02** | `INV-E3.2` | `telemetry_stream_viewer.py` | Telemetry table formats and inserts records correctly with dynamic row filtering. | Automated Unit |
| **AUT-E3-03** | `INV-E3.3` | `parameter_evolution_plot.py` | Parameter plot maintains bounded history buffers and renders simplex limit guidelines. | Automated Unit |
| **AUT-E3-04** | `INV-E3.4` | `sprt_trajectory_gauge.py` | SPRT gauge plots cumulative score $\Lambda_n$ and flags alarms at $A = 2.89$. | Automated Unit |
| **AUT-E3-05** | `INV-E3.5` | `study_manager.py` | Latin Square generator generates balanced $4 \times 4$ sequences with orthogonal condition assignments. | Automated Unit |
| **AUT-E3-06** | `INV-E3.6` | `statistical_analyzer.py` | Computes exact Wilcoxon test, Friedman statistic, effect sizes, and ISO 9241-9 throughput. | Automated Unit |
| **AUT-E3-07** | `INV-E3.7` | `session_report_generator.py` | Synthesizes formatted Markdown summary report and CSV dataset in $< 500\text{ ms}$. | Automated Integr |

---

## 3. Automated Test Descriptions

### AUT-E3-01: Dashboard Event Dispatch Latency Benchmark
* **File**: `tests/benchmarks/test_dashboard_latency.py`
* **Assertion**: Verify that mean telemetry ingestion and dispatch latency is $< 100\text{ ms}$ over 1,000 asynchronous events.

### AUT-E3-02: Telemetry Viewer Table Model & Filtering
* **File**: `tests/unit/test_telemetry_stream_viewer.py`
* **Assertion**: Verify table model row insertion, data column formatting, and filter criteria.

### AUT-E3-03: Parameter Evolution History & Bounds
* **File**: `tests/unit/test_parameter_evolution_plot.py`
* **Assertion**: Verify history buffer trimming, array normalization, and simplex limit visualization.

### AUT-E3-04: SPRT Trajectory Gauge & Decision Boundary Tracking
* **File**: `tests/unit/test_sprt_trajectory_gauge.py`
* **Assertion**: Verify cumulative log-likelihood calculation, boundary alerts ($A = 2.89, B = -2.25$), and gauge reset behavior.

### AUT-E3-05: Latin Square Counterbalanced Condition Generator
* **File**: `tests/unit/test_study_manager.py`
* **Assertion**: Verify that all 4 conditions ($C_1$ to $C_4$) appear exactly once per participant row in orthogonal Latin Square ordering.

### AUT-E3-06: Statistical Analyzer & Inferential Testing
* **File**: `tests/unit/test_statistical_analyzer.py`
* **Assertion**: Verify non-parametric Wilcoxon Signed-Rank Test, Cohen's $d$, and ISO 9241-9 Throughput calculation.

### AUT-E3-07: Automated Markdown Report Synthesizer
* **File**: `tests/integration/test_research_dashboard_pipeline.py`
* **Assertion**: Verify complete end-to-end trial session execution, data logging, and markdown report synthesis.

---

## 4. Manual / Live Interactive Verification Procedures

### TC-MAN-01: Research Dashboard GUI & Telemetry Streaming
* **Objective**: Verify that the multi-tab research dashboard GUI launches cleanly and renders real-time telemetry streaming and parameter evolution plots.
* **Procedure**:
  1. Launch dashboard: `python scripts/launch_research_dashboard.py`.
  2. Inspect the 5 tabs (**Telemetry Stream**, **Parameter Evolution**, **SPRT Monitor**, **Study Runner**, **Analytics**).
  3. Confirm telemetry entries populate and plots update continuously.
* **Pass Criteria**: Dashboard operates smoothly at 60 FPS without UI freezes.

### TC-MAN-02: Automated Latin Square Study Session Execution
* **Objective**: Verify that the Latin Square study panel executes automated experimental trial blocks and exports session reports.
* **Procedure**:
  1. Navigate to **Study Runner** tab in the dashboard.
  2. Click **Start Study Session (Participant P01)**.
  3. Complete simulated trial sequence across conditions $C_1 \to C_4$.
  4. Click **Generate Session Report & Export CSV**.
* **Pass Criteria**: Markdown report generated with statistical tables and trial CSV saved to deliverables directory.

---

## 5. Pass/Fail Sign-Off Matrix

| Test Identifier | Description | Verification Type | Status | Operator Signature |
|---|---|---|---|---|
| **AUT-E3-01** | Dashboard Event Dispatch Latency ($< 100\text{ ms}$) | Automated Benchmark | READY | Automated CI |
| **AUT-E3-02** | Telemetry Stream Table Model & Filtering | Automated Unit | READY | Automated CI |
| **AUT-E3-03** | Parameter Evolution Plot & History Bounds | Automated Unit | READY | Automated CI |
| **AUT-E3-04** | SPRT Trajectory Gauge & Decision Bounds | Automated Unit | READY | Automated CI |
| **AUT-E3-05** | Latin Square Counterbalancing Generator | Automated Unit | READY | Automated CI |
| **AUT-E3-06** | Statistical Analyzer & Inferential Testing | Automated Unit | READY | Automated CI |
| **AUT-E3-07** | End-to-End Pipeline & Report Generation | Automated Integr | READY | Automated CI |
| **TC-MAN-01** | Research Dashboard GUI & Live Telemetry | Manual Visual | READY | Operator Review |
| **TC-MAN-02** | Latin Square Study Session Execution | Manual Visual | READY | Operator Review |
