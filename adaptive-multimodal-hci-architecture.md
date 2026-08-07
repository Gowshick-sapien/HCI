# System Design: Adaptive Multimodal HCI Decision Engine (v2.3)

## 1. Requirements

### Functional
* Ingest webcam frames (30 FPS) and extract face mesh, hand landmarks, and head pose orientation per frame.
* Fuse per-modality confidence scores into a single action prediction using personal weights and thresholds.
* Maintain a per-user calibration profile (gaze offset, gesture speed baseline, tempo, per-modality weights, per-action thresholds, running activation stats).
* Run a short calibration wizard with tempo and undo latency profiling (~60–90 seconds).
* Capture implicit feedback (undo hotkey, rapid reversal, or positive stability expiration) with continuous confidence weighting $c_{fb}$.
* Execute online parameter updates via decoupled Stochastic Gradient Descent with exact Box-Constrained Simplex Projection.
* Monitor drift via Hierarchical Wald Sequential Probability Ratio Tests (SPRT) across per-action and global accumulators.
* Render an explainability HUD showing per-modality confidence bars and safety dwell timers.
* Execute desktop commands via a tiered safety dispatcher with demo sandbox capabilities.

### Non-Functional
* End-to-end decision latency: under ~100 ms per cycle.
* Must run smoothly on standard consumer CPU hardware (8 GB RAM, no GPU required).
* Online update execution: $< 1\text{ms}$ per event via exact 1D bisection dual projection.
* Local profile storage (JSON/SQLite), zero external cloud reliance.

---

## 2. High-Level Design

### Component Diagram
```
┌─────────────┐     ┌────────────────────┐     ┌───────────────────────┐
│   Webcam    │────►│  Capture Thread     │────►│ MediaPipe Feature      │
│  (OpenCV)   │     │  (30 FPS Grab Loop) │     │ Extractor (Face/Hand/  │
└─────────────┘     └────────────────────┘     │ Head Pose via SolvePnP)│
                                                 └──────────┬─────────────┘
                                                            ▼
                                                 ┌───────────────────────┐
                        ┌───────────────────────►│ Feature Vector Buffer │
                        │                        │ (Rolling Spatial Avg) │
                        │                        └──────────┬─────────────┘
                        │                                   ▼
              ┌─────────┴─────────┐              ┌───────────────────────┐
              │ Calibration Profile│◄────────────►│ Weighted Confidence   │
              │ Store (SQLite/JSON)│              │ Fusion + Decision     │
              │ (Weights, Stats)  │              │ Engine (Decoupled SGD)│
              └─────────┬─────────┘              └──────────┬─────────────┘
                        ▲                                   │
                        │                                   ▼
              ┌─────────┴─────────┐              ┌───────────────────────┐
              │ Implicit Feedback │◄─────────────│ Tiered Safety Executor│
              │ & SPRT Detector   │              │ (Safe vs User-Rel T2) │
              └────────────────────┘              └──────────┬─────────────┘
                                                            │
                                                            ▼
                                                 ┌───────────────────────┐
                                                 │ Explainability HUD    │
                                                 │ (Confidence + Dwell)  │
                                                 └───────────────────────┘
```

### Internal API Contracts
```python
FeatureExtractor.extract(frame) -> FeatureVector
    # FeatureVector: gaze_norm, head_pose(yaw, pitch, roll), gesture_label, gesture_conf

DecisionEngine.predict(feature_vector, profile) -> (action, confidence, per_modality_scores)

DecisionEngine.update(action, feedback_event, profile) -> updated_profile
    # feedback_event: {outcome: y in {+1, -1}, latency: delta_t, score: S_fused}

FeedbackDetector.observe(user_input_stream, last_action_context) -> Optional[FeedbackEvent]

DriftDetector.step(action, feedback_event) -> DriftStatus
    # Evaluates per-action S_{m,a} and global S_{m,global} SPRT accumulators

SafetyExecutor.dispatch(action, confidence, profile) -> ExecutionResult
    # Checks Tier 1 vs Tier 2 relative threshold, dwell lock, and emergency interlock
```

---

## 3. Mathematical & Algorithmic Specifications

### 3.1 Decision & Fusion Model
For action $a$, confidence vector $\mathbf{x} = [s_{\text{gaze}}, s_{\text{head}}, s_{\text{hand}}]^T \in [0, 1]^3$, weights $\mathbf{w}_a = [w_{\text{gaze}}, w_{\text{head}}, w_{\text{hand}}]^T$:
$$S_a(\mathbf{x}) = \mathbf{w}_a^T \mathbf{x} = \sum_{i} w_{a, i} s_i, \quad \text{s.t. } \sum_i w_{a, i} = 1, \ w_{a, i} \in [0.05, 0.85]$$

An action intent is triggered when $S_a(\mathbf{x}) \ge \theta_a$.

### 3.2 Implicit Feedback Confidence
* Negative Feedback ($y = -1$, correction within $\Delta t \in [0.2\text{s}, 1.8\text{s}]$):
  $$c_{fb} = \exp\left(-\frac{\Delta t - 0.2}{0.6}\right)$$
* Positive Feedback ($y = +1$, action uncorrected after $T_{\text{stability}} = 1.8\text{s}$):
  $$c_{fb} = 1.0$$
* Prediction Error:
  $$e_a = y_{\text{target}} - S_a(\mathbf{x}), \quad y_{\text{target}} = \begin{cases} 1.0 & \text{if } y = +1 \\ 0.0 & \text{if } y = -1 \end{cases}$$

### 3.3 Decoupled Online Parameter Updates
1. **Weight Ambiguity Gate**: $g_{\text{weight}}(S_a, \theta_a) = \frac{1}{1 + \exp(-40 (|S_a - \theta_a| - 0.05))}$ (suppresses weight thrashing on borderline scores).
2. **Threshold Gate**: $g_{\text{thresh}}(S_a, \theta_a) = 1.0$ (maintains active boundary adaptation).
3. **Weight Update**: $\tilde{\mathbf{w}}_a^{(t+1)} = \mathbf{w}_a^{(t)} + \eta_w(t) \cdot g_{\text{weight}} \cdot c_{fb} \cdot e_a \cdot \mathbf{x}$.
4. **Box-Constrained Simplex Projection**: Projects $\tilde{\mathbf{w}}_a^{(t+1)}$ to satisfy $\sum w_i = 1, w_i \in [0.05, 0.85]$ via 1D bisection root finding on dual variable $\mu$.
5. **Threshold Update**: $\theta_a^{(t+1)} = \text{clip}\left(\theta_a^{(t)} - \eta_\theta(t) \cdot c_{fb} \cdot e_a, \ 0.35, \ 0.85\right)$.
6. **Learning Rate Decay**: $\eta_w(t) = \frac{0.05}{1 + 0.015 t_a}, \eta_\theta(t) = \frac{0.03}{1 + 0.015 t_a}$ with sample-count gating $k \ge 3$.

### 3.4 Hierarchical Wald SPRT Drift Detection
* Discretization: $X_i = 1$ if $y=-1$ and $c_{fb} \ge 0.50$; $X_i = 0$ if $y=+1$.
* Parameters: Nominal $p_0 = 0.05$, Drift $p_1 = 0.25$, $\alpha = 0.05 \implies A \approx 2.89$, $\beta = 0.10 \implies B \approx -2.25$.
* Accumulator: $S_m = k_m \ln (p_1/p_0) + (m - k_m) \ln ((1-p_1)/(1-p_0))$.
* Renewal Reset: On $S_m \ge A$ (drift alert) or $S_m \le B$ (stability confirmed), reset $(S_m, m, k_m \leftarrow 0)$.

### 3.5 User-Relative Tier-2 Safety Gating
$$\theta_{\text{tier2}, a} = \begin{cases} \theta_a + 0.15 & \text{if } N_{\text{accepted}, a} < 5 \\ \min(0.95, \max(\theta_a + 0.15, \mu_{S, a} + 1.5\sigma_{S, a})) & \text{if } N_{\text{accepted}, a} \ge 5 \end{cases}$$
Coupled with a 600ms visual dwell confirmation on the HUD, reversible 3-second grace period, and global `Esc` interlock hotkey.

---

## 4. Trade-off Analysis

| Architectural Decision | Chosen Strategy | Primary Rationale & Trade-off |
|---|---|---|
| **Learning Paradigm** | Projected Online SGD with Decoupled Gating | Interpretable, O(1) CPU updates, separates weight stability from threshold adaptation. |
| **Simplex Projection** | 1D Bisection Dual Solver | Exact mathematical guarantees for box constraints without heuristic clipping artifacts. |
| **Drift Detection** | Hierarchical Wald SPRT | Prevents noisy false recalibration prompts via formal hypothesis bounds; separates local gesture issues from global shifts. |
| **Safety Gating** | User-Relative Adaptive Floor | Avoids penalizing users with lower baseline confidence distributions while maintaining strict safety margins. |
| **Evaluation Scope** | Tiered D5 Pilot vs E3 LME Study | Fits single-semester part-time 4-week timeline while maintaining scientific rigor. |
