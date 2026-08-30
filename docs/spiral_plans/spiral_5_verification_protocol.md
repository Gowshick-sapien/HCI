# Spiral 5 Verification Protocol: Runtime Assessment Engine & Dual-Scale Dynamic Adaptation (Deliverable D5)

## 1. Scope & Objective
This document outlines the formal test protocol for verifying **Deliverable D5 (Layer 5: Dual-Scale Dynamic Adaptation & Runtime Assessment Engine)**. It specifies automated unit tests, integration tests, latency benchmarks, and manual live verification procedures.

---

## 2. Formal Invariants Verification Matrix

| Test Identifier | Invariant ID | Target Component | Formal Acceptance Criterion | Verification Type |
|---|---|---|---|---|
| **AUT-D5-01** | `INV-D5.1` | `assessment_engine.py` | Computes EWMA adaptation gain, learning velocity, stability index, and health states across 50 interaction cycles. | Automated Unit |
| **AUT-D5-02** | `INV-D5.2` | `gatekeeper.py` | SPRT statistical decision boundary approves systematic biases ($c_{\text{fb}} \ge 0.70$) and rejects noisy random inputs ($c_{\text{fb}} < 0.60$). | Automated Unit |
| **AUT-D5-03** | `INV-D5.3` | `micro_adaptation.py` | Micro-SGD update strictly maintains probability simplex constraint $\sum w_i = 1.0, w_i \ge 0.05$ with $\|\Delta \mathbf{w}\|_\infty \le 0.08$. | Automated Unit |
| **AUT-D5-04** | `INV-D5.4` | `macro_adaptation.py` | Policy state machine executes transitions (`MERGE`, `FREEZE`, `DISCARD`, `RECALIBRATE`) with exact trigger conditions. | Automated Unit |
| **AUT-D5-05** | `INV-D5.5` | `coordinator.py` | Closed-loop feedback $\to$ SPRT $\to$ micro-SGD update cycle executes in $\le 2.0\text{ ms}$ on CPU. | Automated Benchmark |
| **AUT-D5-06** | `INV-D5.6` | `test_closed_loop_adaptation.py` | End-to-end simulation confirms weights shift toward reliable modality during sustained simulated noise. | Automated Integr |

---

## 3. Automated Test Descriptions

### AUT-D5-01: Runtime Assessment Metrics
* **File**: `tests/unit/test_assessment_engine.py`
* **Assertion**: Verify that `AssessmentEngine.update()` computes valid non-NaN metrics for EWMA gain, velocity, stability index, and maps state to `BOOTSTRAPPING`, `LEARNING`, `STABLE`, or `DRIFTING`.

### AUT-D5-02: SPRT Gatekeeper Decision Boundaries
* **File**: `tests/unit/test_gatekeeper.py`
* **Assertion**: Verify that single isolated false activations are rejected (`GatekeeperVerdict.REJECT`), while 3+ consecutive negative feedback events trigger `GatekeeperVerdict.APPROVE`.

### AUT-D5-03: Simplex Projection & Micro-SGD Bounds
* **File**: `tests/unit/test_micro_adaptation.py`
* **Assertion**: Verify that gradient descent with simplex projection guarantees $\sum w_i = 1.0$, $w_i \ge 0.05$, and step size is capped at $\delta_{\text{max}} = 0.08$.

### AUT-D5-04: Macro-Adaptation State Machine
* **File**: `tests/unit/test_macro_adaptation.py`
* **Assertion**: Verify that `MERGE` updates baseline weights, `FREEZE` locks adaptation, `DISCARD` restores prior baseline, and `RECALIBRATE` flags drift.

### AUT-D5-05: Closed-Loop Adaptation Latency Benchmark
* **File**: `tests/benchmarks/test_adaptation_latency.py`
* **Assertion**: Verify that mean evaluation latency for Gatekeeper + Micro-SGD + Profile update is $\le 2.0\text{ ms}$ over 1,000 iterations.

---

## 4. Manual / Live Interactive Verification Procedures

### TC-MAN-01: Live Micro-Adaptation Weight Shifting
* **Objective**: Verify that repeated mouse takeovers cause modality weights to shift away from inaccurate channels toward higher-confidence modalities.
* **Procedure**:
  1. Start live visualizer: `python scripts/verify_perception_live.py`.
  2. Perform an action and immediately take over with the physical mouse 3 times in succession.
  3. Inspect HUD line: `MODE: GESTURE [LEARNING]` and observe weight adjustment in profile snapshot.
* **Pass Criteria**: Modality weight updates reflect gradient step without violating simplex bounds.

### TC-MAN-02: Gatekeeper Noise Rejection
* **Objective**: Verify that an isolated accidental keystroke is filtered out by the Gatekeeper without modifying baseline weights.
* **Procedure**:
  1. Trigger a single action and press `'z'`.
  2. Verify that Gatekeeper status logs `REJECT` (insufficient evidence $\Lambda_n < A$).
* **Pass Criteria**: Modality weights remain unchanged after single isolated disturbance.

---

## 5. Pass/Fail Sign-Off Matrix

| Test Identifier | Description | Verification Type | Status | Operator Signature |
|---|---|---|---|---|
| **AUT-D5-01** | Assessment Metrics & Health Classifier | Automated Unit | READY | Automated CI |
| **AUT-D5-02** | SPRT Gatekeeper Decision Boundaries | Automated Unit | READY | Automated CI |
| **AUT-D5-03** | Micro-SGD Simplex Projection & Step Bounds | Automated Unit | READY | Automated CI |
| **AUT-D5-04** | Macro-Adaptation State Machine Policies | Automated Unit | READY | Automated CI |
| **AUT-D5-05** | Adaptation Pipeline Latency ($\le 2.0\text{ ms}$) | Automated Benchmark | READY | Automated CI |
| **AUT-D5-06** | Closed-Loop Multi-Layer Integration | Automated Integr | READY | Automated CI |
| **TC-MAN-01** | Live Micro-Adaptation Weight Shifting | Manual Visual | READY | Operator Review |
| **TC-MAN-02** | Gatekeeper Noise Rejection | Manual Visual | READY | Operator Review |
