# Spiral 5 Implementation Plan: Runtime Assessment Engine & Dual-Scale Dynamic Adaptation (Deliverable D5)

## 1. Executive Overview
Spiral 5 delivers **Layer 5 of the Multimodal Architecture (Deliverable D5: Runtime Assessment Engine & Dual-Scale Dynamic Adaptation)**. Building on the supervisory feedback signals produced by Layer 4 (Deliverable D4), Layer 5 closes the adaptive feedback loop by continuously evaluating multimodal interaction performance, validating parameter updates through statistical hypothesis testing, and executing dual-scale (micro-SGD and macro-policy) profile adaptation without user interruption.

---

## 2. Architectural Structure & Mathematical Foundations

### 2.1 Engine 5A: Runtime Performance Assessment Engine (`src/adaptation/assessment_engine.py`)
Engine 5A continuously computes statistical health and stability metrics over a rolling interaction window $W$:
1. **Adaptation Gain EWMA ($\overline{G}_t$)**:
   $$\overline{G}_t = \alpha \cdot G_t + (1 - \alpha) \cdot \overline{G}_{t-1}, \quad \alpha = 0.15$$
   where $G_t = \frac{\Delta \text{Success Rate}}{\Delta t}$.
2. **Learning Velocity ($v_L$)**:
   $$v_L = \frac{\|\mathbf{w}_t - \mathbf{w}_{t-k}\|_2}{k \cdot \Delta t}$$
3. **Weight Stability Index ($\kappa_w$)**:
   $$\kappa_w = 1.0 - \min\left(1.0, \frac{\sum_{i=1}^3 \text{Var}(w_{i, \text{window}})}{\sigma^2_{\text{threshold}}}\right)$$
4. **Expected Calibration Error (ECE)**:
   $$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
5. **Drift Recovery Rate ($\rho_{\text{drift}}$)**:
   $$\rho_{\text{drift}} = \frac{1}{\tau_{\text{recovery}}} \sum_{k=1}^K \mathbb{I}(\Delta t_k \le \tau_{\text{nominal}})$$
6. **System Health State Classification**:
   * `BOOTSTRAPPING`: Sample count $N < 10$.
   * `LEARNING`: Velocity $v_L > v_{\text{threshold}}$, error decreasing.
   * `STABLE`: Stability index $\kappa_w \ge 0.85$, error rate $\le 0.05$.
   * `IMPROVING`: Adaptation gain $\overline{G}_t > 0$, post-update accuracy rising.
   * `DRIFTING`: Error rate rising, ECE $> 0.15$.
   * `RECOVERING`: Corrective updates active after detected drift.

---

### 2.2 Engine 5B: Micro-Adaptation Engine & Gatekeeper SPRT (`src/adaptation/gatekeeper.py`, `src/adaptation/micro_adaptation.py`)
Engine 5B performs online gradient updates on modality fusion weights $\mathbf{w} = [w_{\text{eye}}, w_{\text{head}}, w_{\text{hand}}]$:
1. **Gatekeeper Validation (`gatekeeper.py`)**:
   * Implements Sequential Probability Ratio Test (SPRT) on accumulated feedback stream:
     $$\Lambda_n = \sum_{i=1}^n \log \left( \frac{P(x_i \mid H_1: \text{Systematic Bias})}{P(x_i \mid H_0: \text{Random Noise})} \right)$$
   * Decision Boundaries:
     * $\Lambda_n \ge A = \log\left(\frac{1 - \beta}{\alpha_{\text{sig}}}\right) \implies \text{APPROVE}$ update.
     * $\Lambda_n \le B = \log\left(\frac{\beta}{1 - \alpha_{\text{sig}}}\right) \implies \text{REJECT}$ update (discard noise).
   * Verifies minimum sample threshold ($N \ge N_{\text{min}}$) and feedback confidence $c_{\text{fb}} \ge \theta_{\text{gate}}$.
2. **Online Gradient Descent & Simplex Projection (`micro_adaptation.py`)**:
   * Loss Function with Respect to Failure Mode:
     $$\mathcal{L}(\mathbf{w}) = \frac{1}{2} (y_{\text{target}} - \mathbf{w}^T \mathbf{s})^2 + \lambda \|\mathbf{w} - \mathbf{w}_{\text{baseline}}\|_2^2$$
   * Gradient Update:
     $$\mathbf{w}^{(t+1)} = \Pi_{\Delta} \left( \mathbf{w}^{(t)} - \eta \cdot \nabla_{\mathbf{w}} \mathcal{L} \right)$$
   * Simplex Projection $\Pi_{\Delta}$:
     $$\sum_{i=1}^3 w_i = 1.0, \quad w_i \ge w_{\text{min}} > 0, \quad \forall i$$
   * Max Step Limiter:
     $$\|\mathbf{w}^{(t+1)} - \mathbf{w}^{(t)}\|_\infty \le \delta_{\text{max}} = 0.08$$

---

### 2.3 Engine 5C: Macro-Adaptation Policy State Machine (`src/adaptation/macro_adaptation.py`)
Engine 5C coordinates long-term profile lifecycle transitions:
1. **`MERGE` Policy**: Blends verified micro-adapted weights into baseline profile after sustained stability ($T \ge 120\text{ s}, \kappa_w \ge 0.85$).
2. **`FREEZE` Policy**: Halts online learning when environmental noise or ambient lux shifts exceed thresholds.
3. **`DISCARD` Policy**: Rolls back active session weights to baseline profile if post-update error rate spikes $> 20\%$.
4. **`RECALIBRATE` Policy**: Flags persistent drift ($> 150\text{ px}$ systematic gaze bias) to recommend calibration wizard execution.

---

### 2.4 Master Adaptation Coordinator (`src/adaptation/coordinator.py`, `src/adaptation/__init__.py`)
Acts as the unified facade orchestrating:
* Receiving `FeedbackEvent` records from Layer 4 `FeedbackObserver`.
* Querying `Engine 5A` for health metrics.
* Routing candidates through `Gatekeeper` and `Engine 5B` for gradient descent.
* Applying `Engine 5C` lifecycle state transitions.
* Persisting updated `ProfileSnapshot` states through `ProfileManager`.

---

## 3. Formal Invariant Specifications

| Invariant ID | Target Component | Formal Acceptance Criterion | Verification Method |
|---|---|---|---|
| **INV-D5.1** | `assessment_engine.py` | Computes EWMA gain, velocity, stability index, and health state accurately without NaN/inf. | Automated Unit Test |
| **INV-D5.2** | `gatekeeper.py` | SPRT rejects updates with $c_{\text{fb}} < 0.65$ or insufficient samples ($N < N_{\text{min}}$) and approves sustained error trends. | Automated Unit Test |
| **INV-D5.3** | `micro_adaptation.py` | Updated weights strictly satisfy simplex constraints $\sum w_i = 1.0, w_i \ge 0.05$ with max step $\|\Delta \mathbf{w}\|_\infty \le 0.08$. | Automated Unit Test |
| **INV-D5.4** | `macro_adaptation.py` | Correctly executes `MERGE`, `FREEZE`, `DISCARD`, and `RECALIBRATE` state transitions based on session metrics. | Automated Unit Test |
| **INV-D5.5** | `coordinator.py` | Full closed-loop feedback $\to$ SPRT $\to$ micro-SGD $\to$ profile save pipeline executes in $\le 2.0\text{ ms}$. | Automated Benchmark |

---

## 4. Implementation Phasing

### Phase 1: Engine 5A Performance Assessment
* Implement `AssessmentEngine` with rolling metric buffers.
* Implement ECE calculation, stability variance, and health state classifier.
* Unit tests in `tests/unit/test_assessment_engine.py`.

### Phase 2: Engine 5B Gatekeeper & Micro-Adaptation
* Implement `Gatekeeper` with SPRT statistical decision boundaries.
* Implement `MicroAdaptationEngine` with gradient descent and simplex projection.
* Unit tests in `tests/unit/test_gatekeeper.py` and `tests/unit/test_micro_adaptation.py`.

### Phase 3: Engine 5C Macro-Adaptation State Machine
* Implement `MacroAdaptationEngine` with 4-state lifecycle transitions.
* Unit tests in `tests/unit/test_macro_adaptation.py`.

### Phase 4: Master Adaptation Coordinator & Closed-Loop Integration
* Implement `AdaptationCoordinator` integrating FeedbackObserver, Engine 5A, 5B, 5C, and ProfileManager.
* Multi-layer integration test in `tests/integration/test_closed_loop_adaptation.py`.
* Performance micro-benchmark in `tests/benchmarks/test_adaptation_latency.py`.
