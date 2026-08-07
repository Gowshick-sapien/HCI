# Project Deliverables Specification

## Project Title
# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction

---

### Executive Overview
This document provides the exhaustive, publication-grade specification of all **engineering deliverables, advanced research enhancements, software modules, and academic artifacts** comprising the project. It defines the architectural boundaries, input/output data contracts, mathematical formulations, source code structures, acceptance criteria, and verification methods for every deliverable.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               MASTER DELIVERABLES TAXONOMY                                       │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [CORE ENGINEERING DELIVERABLES (MUST-HAVE)]                                                     │
│  • Deliverable D1: Multimodal Perception & Feature Extraction Pipeline                           │
│  • Deliverable D2: Weighted Confidence Fusion & Box-Constrained Simplex Projection Engine       │
│  • Deliverable D3: Interactive Calibration & User Profile Bootstrapping Wizard                   │
│  • Deliverable D4: Decoupled Safety Dispatcher & Asynchronous Implicit Feedback Observer         │
│  • Deliverable D5: Runtime Assessment Engine (RAE) & Automated Evaluation Suite                  │
│                                                                                                  │
│  [ADVANCED RESEARCH ENHANCEMENTS (RESEARCH GOALS)]                                               │
│  • Enhancement E1: Dual-Scale Online Adaptive Engine & Hierarchical Wald SPRT Drift Detector     │
│  • Enhancement E2: State-Aware Explainability HUD Overlay                                        │
│  • Enhancement E3: Interactive Empirical Research Dashboard & Latin Square Study Runner          │
│                                                                                                  │
│  [DOCUMENTATION & REPLICATION ARTIFACTS]                                                         │
│  • DOC1: Canonical Project Proposal & Academic Framing                                          │
│  • DOC2: ISO/IEC/IEEE 29148 Software Requirements Specification (SRS)                            │
│  • DOC3: System Architecture Specification                                                      │
│  • DOC4: Project Implementation Plan & 4-Week Engineering Roadmap                                │
│  • SDLC: Spiral SDLC Methodology Specification (adaptive-multimodal-hci-sdlc-spiral.md)          │
│  • DOC5: Academic Research Paper Preprint & Open-Science Benchmark Dataset                       │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Core Engineering Deliverables Specification

---

### 1.1 Deliverable D1: Multimodal Perception & Feature Extraction Pipeline

#### 1.1.1 Purpose & Scope
Deliverable **D1** implements the foundational computer vision and spatial-temporal signal processing layer (Layer 1). It captures raw RGB frames from a single consumer webcam at $30\text{ FPS}$, extracts 3D facial mesh landmarks, iris gaze offsets, 3D head pose Euler angles, and 3D hand gesture kinematics, and applies an adaptive velocity-scaled Holt-Winters filter to eliminate landmark jitter.

#### 1.1.2 Module Decomposition & Source Code Artifacts
```
src/
├── capture/
│   ├── __init__.py
│   └── video_stream.py              # Threaded camera capture with lock-free buffer
├── perception/
│   ├── __init__.py
│   ├── face_mesh_extractor.py       # 468-point FaceMesh & 10-point iris tracking
│   ├── head_pose_estimator.py       # Levenberg-Marquardt SolvePnP 3D pose solver
│   ├── hand_pose_extractor.py       # 21-point 3D hand tracking & gesture syntax
│   ├── holt_winters_filter.py       # Adaptive double exponential smoothing filter
│   └── feature_pipeline.py          # Multimodal feature assembler & covariance estimator
```

#### 1.1.3 Mathematical Formulations & Data Contracts
1. **Ocular Gaze Normalized Coordinate Offsets**:
   $$r_{\text{iris}, x} = \frac{x_{\text{iris}} - x_{\text{inner}}}{x_{\text{outer}} - x_{\text{inner}}}, \quad r_{\text{iris}, y} = \frac{y_{\text{iris}} - y_{\text{superior}}}{y_{\text{inferior}} - y_{\text{superior}}}$$
   $$s_{\text{gaze}} = \text{clip}\left(1.0 - \frac{\|\mathbf{p}_{\text{screen}} - \mathbf{p}_{\text{target}}\|}{R_{\text{target}}}, \ 0.0, \ 1.0\right) \cdot \mathbb{I}(\text{EAR} \ge 0.18)$$
2. **Head Pose Mahalanobis Confidence**:
   $$s_{\text{head}} = \exp\left(-\frac{1}{2}(\mathbf{p}_{\text{pose}} - \boldsymbol{\mu}_{\text{pose}})^T \boldsymbol{\Sigma}_{\text{pose}}^{-1} (\mathbf{p}_{\text{pose}} - \boldsymbol{\mu}_{\text{pose}})\right) \in [0.0, 1.0]$$
3. **Adaptive Holt-Winters Dynamic Smoothing**:
   $$\hat{x}_t = \alpha_t x_t + (1 - \alpha_t)(\hat{x}_{t-1} + b_{t-1}), \quad b_t = \beta (\hat{x}_t - \hat{x}_{t-1}) + (1 - \beta) b_{t-1}$$
   $$\alpha_t = \text{clip}(\alpha_0 + \gamma \|\mathbf{v}_{\text{wrist}}(t)\|, \ 0.20, \ 0.85), \quad \beta = 0.15$$

```python
@dataclass(frozen=True)
class FeatureVector:
    timestamp_ms: float
    gaze_confidence: float              # s_gaze ∈ [0.0, 1.0]
    head_confidence: float              # s_head ∈ [0.0, 1.0]
    hand_confidence: float              # s_hand ∈ [0.0, 1.0]
    gaze_screen_xy: Tuple[float, float]
    head_euler_angles: Tuple[float, float, float] # (yaw, pitch, roll) in degrees
    pinch_distance: float
    wrist_velocity: float
    sensor_covariance_matrix: np.ndarray # 3x3 matrix Σ_sensor
    ambient_illuminance_lux: float
    eye_aspect_ratio: float
```

#### 1.1.4 Acceptance Criteria & Verification Invariants
* **Invariant D1.1**: End-to-end perception latency $\le 20.5\text{ ms}$ on standard 4-core CPU hardware.
* **Invariant D1.2**: Stationary coordinate jitter $\le 1.2\text{ px}$; dynamic tracking lag $\le 15\text{ ms}$.
* **Invariant D1.3**: Automatic zero-confidence suppression on eye blinks ($\text{EAR} < 0.18$) and hand tracking occlusions.

---

### 1.2 Deliverable D2: Weighted Confidence Fusion & Simplex Projection Engine

#### 1.2.1 Purpose & Scope
Deliverable **D2** implements the core mathematical decision engine (Layer 3A). It computes the linear dot-product confidence fusion $S_a(\mathbf{x}) = \mathbf{w}_a^T \mathbf{x}$, compares scores against personalized thresholds $\theta_a$, and embeds the exact 1D bisection box-constrained simplex projection solver ensuring weights strictly satisfy $\sum_{i=1}^3 w_{a, i} = 1.0$ and $w_{a, i} \in [0.05, 0.85]$. It also provides a static-rule baseline engine for counterbalanced A/B benchmarking.

#### 1.2.2 Module Decomposition & Source Code Artifacts
```
src/
├── decision/
│   ├── __init__.py
│   ├── confidence_fuser.py          # Vectorized dot-product fuser S_a(x) = w_a^T x
│   ├── static_baseline_engine.py    # Hardcoded boolean rule baseline for A/B trials
│   └── intent_evaluator.py          # Candidate threshold evaluation & lockout checks
├── learning/
│   ├── __init__.py
│   └── simplex_projector.py         # Exact 1D dual bisection box-constrained projection
```

#### 1.2.3 Mathematical Formulations & Exact Algorithms
1. **Multimodal Late Fusion Score**:
   $$S_a(\mathbf{x}) = \mathbf{w}_a^T \mathbf{x} = w_{a, \text{gaze}} s_{\text{gaze}} + w_{a, \text{head}} s_{\text{head}} + w_{a, \text{hand}} s_{\text{hand}}$$
2. **Exact 1D Dual Bisection Box-Constrained Simplex Projection**:
   $$\text{Minimize } \frac{1}{2} \|\mathbf{w} - \tilde{\mathbf{w}}\|_2^2 \quad \text{subject to } \sum_{i=1}^d w_i = 1.0, \quad l_i \le w_i \le u_i$$
   Solved via the 1D monotonic piecewise root function:
   $$f(\mu) = \sum_{i=1}^d \text{clip}(\tilde{w}_i - \mu, \ l_i, \ u_i) - 1.0 = 0$$

```python
def box_constrained_simplex_projection(
    w_tilde: np.ndarray, 
    lower_bound: float = 0.05, 
    upper_bound: float = 0.85, 
    max_iter: int = 25, 
    tol: float = 1e-6
) -> np.ndarray:
    """Exact 1D bisection root-finding projection onto box-constrained simplex."""
    mu_min = np.min(w_tilde) - upper_bound
    mu_max = np.max(w_tilde) - lower_bound
    
    for _ in range(max_iter):
        mu_mid = (mu_min + mu_max) / 2.0
        w_projected = np.clip(w_tilde - mu_mid, lower_bound, upper_bound)
        f_val = np.sum(w_projected) - 1.0
        
        if abs(f_val) <= tol:
            return w_projected
        if f_val > 0:
            mu_min = mu_mid
        else:
            mu_max = mu_mid
            
    return np.clip(w_tilde - (mu_min + mu_max) / 2.0, lower_bound, upper_bound)
```

#### 1.2.4 Acceptance Criteria & Verification Invariants
* **Invariant D2.1**: Simplex projection equality holds: $\left|\sum_{i=1}^3 w_{a, i} - 1.0\right| \le 10^{-6}$ across all updates.
* **Invariant D2.2**: Strict box adherence: $0.05 \le w_{a, i} \le 0.85 \quad \forall i \in \{\text{gaze}, \text{head}, \text{hand}\}$.
* **Invariant D2.3**: Fusion and projection computation completes in $< 0.5\text{ ms}$.

---

### 1.3 Deliverable D3: Interactive Calibration & User Profile Bootstrapping Wizard

#### 1.3.1 Purpose & Scope
Deliverable **D3** implements the 5-phase interactive onboarding wizard (Layer 2) requiring only 60–90 seconds (~10–15 sample actions). It bootstraps the user's neutral head pose 95% confidence ellipsoid $\mathcal{E}_{\text{head}}$, 5-point gaze affine perspective transformation matrix $\mathbf{M}_{\text{gaze}}$, individual reaction tempo $\tau_{\text{user}}$, and initializes variance-informed starting weights $\mathbf{w}_a^{(0)}$ (`Profile v1`).

#### 1.3.2 Module Decomposition & Source Code Artifacts
```
src/
├── calibration/
│   ├── __init__.py
│   ├── wizard_controller.py         # 5-phase onboarding state coordinator
│   ├── geometry_profiler.py         # Head pose 3D ellipsoid & gaze affine solver
│   ├── tempo_estimator.py           # Reaction latency & tau_user baseline estimator
│   └── variance_weight_init.py      # Noise-variance inverse weighting synthesizer
├── storage/
│   ├── __init__.py
│   └── profile_store.py             # JSON/SQLite schema serializer & version manager
```

#### 1.3.3 Calibration Protocol & Mathematical Baselines
```
┌────────────────────────────────────────────────────────────────────────┐
│               5-PHASE INTERACTIVE CALIBRATION TIMELINE                 │
├────────────────────────────────────────────────────────────────────────┤
│  Phase A: System & Lighting Readiness (0–10s, 1 sample)                │
│  Phase B: Neutral Head Pose & Motion Range (10–25s, 3 samples)         │
│  Phase C: 5-Point Ocular Gaze Mapping (25–50s, 5 samples)              │
│  Phase D: Gesture Kinematics & Tempo Baseline (50–75s, 4 samples)      │
│  Phase E: Profile Synthesis & Initial Weighting (75–90s, automated)   │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Neutral Posture 95% Confidence Ellipsoid**:
   $$\mathcal{E}_{\text{head}} = \left\{ \mathbf{p} \in \mathbb{R}^3 \mid (\mathbf{p} - \boldsymbol{\mu}_{\text{pose}})^T \boldsymbol{\Sigma}_{\text{pose}}^{-1} (\mathbf{p} - \boldsymbol{\mu}_{\text{pose}}) \le \chi^2_3(0.95) \approx 7.815 \right\}$$
2. **Gaze 2D Affine Transformation Matrix**:
   $$\begin{bmatrix} u_{\text{screen}} \\ v_{\text{screen}} \end{bmatrix} = \begin{bmatrix} m_{11} & m_{12} & t_x \\ m_{21} & m_{22} & t_y \end{bmatrix} \begin{bmatrix} r_{\text{iris}, x} \\ r_{\text{iris}, y} \\ 1 \end{bmatrix}$$
3. **Variance-Informed Weight Initialization**:
   $$\tilde{w}_i^{(0)} = \frac{1 / \sigma_i^2}{\sum_{j \in \{\text{gaze}, \text{head}, \text{hand}\}} 1 / \sigma_j^2} \implies \mathbf{w}_a^{(0)} = \text{BoxSimplexProjection}(\tilde{\mathbf{w}}^{(0)})$$

#### 1.3.4 Acceptance Criteria & Verification Invariants
* **Invariant D3.1**: Onboarding wizard completes within $\le 90\text{ seconds}$ without dropped frames.
* **Invariant D3.2**: Gaze calibration residual $\text{RMSE} \le 45\text{ px}$ on $1080\text{p}$ reference screen.
* **Invariant D3.3**: Calibrated $\tau_{\text{user}}$ bounded strictly within $[0.35\text{s}, 0.95\text{s}]$.
* **Invariant D3.4**: Initial profile serialized as `Profile v1` to disk in $< 20\text{ ms}$.

---

### 1.4 Deliverable D4: Decoupled Safety Dispatcher & Feedback Observer

#### 1.4.1 Purpose & Scope
Deliverable **D4** implements the decoupled safety execution pipeline (Layer 3B/3C) and the 4-window implicit feedback observation state machine (Layer 4). It enforces user-relative Tier-2 safety gating with 600ms visual dwell confirmation and 3.0s grace-period undo hooking, while asynchronously monitoring five negative sub-detectors to infer supervisory labels without intrusive dialogues.

#### 1.4.2 Module Decomposition & Source Code Artifacts
```
src/
├── decision/
│   ├── safety_gatekeeper.py         # Tier-1 instant / Tier-2 user-relative dwell gate
│   └── action_dispatcher.py         # OS command execution & ActionContext dispatch
├── feedback/
│   ├── __init__.py
│   ├── temporal_state_machine.py    # 4-window temporal coordinator & ring buffer
│   ├── undo_hook_detector.py        # Low-level OS hook interceptor (Ctrl+Z, Alt+Left)
│   ├── reversal_detector.py         # Directional oppositional continuous command tracker
│   ├── retry_detector.py            # Rapid duplicate gesture retry counter
│   ├── dismissal_detector.py        # Immediate window/tab dismissal watcher
│   └── override_detector.py         # Physical mouse (>800px/s) / keyboard override sensor
```

#### 1.4.3 Mathematical Formulations & State Machine Logic
```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         IMPLICIT FEEDBACK TEMPORAL STATE MACHINE                                 │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  [t0: Action Executed & Logged to ActionContextQueue]                                            │
│  ├── Window 1: REFRACTORY WINDOW [t0, t0 + 200ms]             ──► Inputs Ignored (Motor Delay)   │
│  ├── Window 2: CORRECTION WINDOW [t0 + 200ms, t0 + 1.8s]      ──► 5 Negative Sub-Detectors Active│
│  │                                                                c_fb = exp(-(Δt - 0.2)/τ_user) │
│  └── Window 3: STABILITY EXPIRATION [t > t0 + 1.8s]           ──► Implicit Positive (c_fb = 1.0) │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **User-Relative Tier-2 Destructive Action Gate**:
   $$\theta_{\text{tier2}, a} = \min\left(0.95, \ \max(\theta_a + 0.15, \ \mu_{S, a} + 1.5\sigma_{S, a})\right)$$
2. **Continuous Exponential Confidence Decay**:
   $$c_{fb}(\Delta t) = \exp\left(-\frac{\Delta t - 0.20}{\tau_{\text{user}}}\right) \in [0.05, 1.0]$$

```python
@dataclass(frozen=True)
class FeedbackEvent:
    action_id: str
    action_type: str
    feedback_outcome: int               # +1 (Accepted), -1 (Corrected / Rejected)
    supervisory_confidence: float       # c_fb ∈ [0.05, 1.0]
    reaction_time_ms: float             # Δt
    failure_taxonomy: str               # "NONE", "FALSE_ACTIVATION", "WRONG_TARGET", etc.
    detection_channel: str              # "UNDO_HOOK", "OPPOSITIONAL_REVERSAL", "STABILITY_EXPIRY"
    timestamp_ms: float
```

#### 1.4.4 Acceptance Criteria & Verification Invariants
* **Invariant D4.1**: Zero false feedback triggers during Window 1 ($[t_0, t_0 + 200\text{ms}]$).
* **Invariant D4.2**: Destructive Tier-2 commands NEVER execute without uninterrupted $600\text{ ms}$ visual dwell.
* **Invariant D4.3**: Active undo hook stack captures `Ctrl+Z` reversals within $< 5\text{ ms}$ of occurrence.

---

### 1.5 Deliverable D5: Runtime Assessment Engine (RAE) & Automated Evaluation Suite

#### 1.5.1 Purpose & Scope
Deliverable **D5** delivers the self-evaluating intelligence core (Layer 5) split into two decoupled internal engines: **Engine 5A (Runtime Metrics Engine)** tracking seven continuous health metrics and **Engine 5B (Decision & Learning Validator / Gatekeeper)** enforcing six strict rejection rules before allowing parameter updates. It also includes the automated Session Report Generator and the standardized Latin Square A/B evaluation suite.

#### 1.5.2 Module Decomposition & Source Code Artifacts
```
src/
├── assessment/
│   ├── __init__.py
│   ├── runtime_metrics_engine.py    # Engine 5A: EWMA AG, LV, WSI, ACI, ECE, RR, DRT
│   ├── learning_gatekeeper.py       # Engine 5B: 6-rule validation firewall
│   ├── session_report_generator.py  # Automated markdown report & plot synthesizer
│   └── failure_classifier.py        # 4-stage failure taxonomy & governance
├── evaluation/
│   ├── __init__.py
│   ├── study_manager.py             # Latin Square counterbalanced A/B test coordinator
│   ├── task_scripts.py              # Isomorphic desktop task automation routines
│   └── statistical_analyzer.py      # Wilcoxon Signed-Rank & Linear Mixed-Effects modeler
```

#### 1.5.3 Categorized Runtime Metrics & Gatekeeper Rules
1. **Runtime Metrics (Engine 5A)**:
   * *EWMA Adaptation Gain*: $AG_t = \alpha (\text{Acc}_t - \text{Base}) + (1-\alpha) AG_{t-1} \quad (\alpha = 0.10)$
   * *Sliding Learning Velocity*: $LV_t = \frac{\text{Error}(t-W) - \text{Error}(t)}{W} \quad (W = 20)$
   * *Weight Stability Index*: $WSI_t = \frac{1}{d} \sum_{i=1}^d \sqrt{\frac{1}{K}\sum_{k=0}^{K-1} (w_{i, t-k} - \bar{w}_i)^2} \quad (K = 30, d = 3)$
   * *Adaptation Confidence Index*: $ACI_t = \text{clip}\left(0.30 \frac{\min(N_a, 20)}{20} + 0.30 (1 - \frac{WSI_t}{0.10}) + 0.25 \frac{AG_t}{0.20} - 0.15 ECE_t, \ 0, \ 1\right)$
   * *Expected Calibration Error*: $ECE_t = \sum_{b=1}^{10} \frac{|B_b|}{N} \left| \text{Acc}(B_b) - \text{Conf}(B_b) \right|$
   * *Recovery Rate*: $RR = \frac{\sum \mathbb{I}(\text{Outcome}_{t+1} = \text{Success} \mid \text{Outcome}_t = \text{Error})}{\sum \mathbb{I}(\text{Outcome}_t = \text{Error})}$
   * *Drift Recovery Time*: $DRT = t_{\text{stabilized}} - t_{\text{alarm}}$ (Time from Wald SPRT $S_m \ge 2.89$ to reset $S_m \le -2.25$).
2. **Gatekeeper Validation Rules (Engine 5B)**:
   * `Rule 1 (Sample Floor)`: $k_a \ge 3$ required per action.
   * `Rule 2 (Confidence Floor)`: $c_{fb} \ge 0.40$ required.
   * `Rule 3 (Neutral Suppression)`: Uninformative $y=0$ discarded.
   * `Rule 4 (Drift Lockout)`: Micro-updates blocked if Wald SPRT $S_m \ge 2.89$.
   * `Rule 5 (Contradiction Check)`: Drops conflicting sub-detector signals.
   * `Rule 6 (Sensor SNR)`: Requires Lux $> 20$ and GazeVar $< 0.25$.

```python
@dataclass(frozen=True)
class GatekeeperVerdict:
    status: str                         # "APPROVE" | "REJECT"
    rejection_reason: str               # "NONE" | "SAMPLE_COUNT_BELOW_WARMUP_FLOOR" | ...
    validated_error_residual: float     # e_a = y_target - S_a(x)
    effective_learning_rate: float      # η_eff = η_0 * C_update
    ambiguity_weight: float             # g_weight(Δ_decision)
    current_health_snapshot: dict
```

#### 1.5.4 Acceptance Criteria & Verification Invariants
* **Invariant D5.1**: Gatekeeper firewalls all corrupt/noisy updates, achieving $100\%$ precision on synthetic outlier tests.
* **Invariant D5.2**: RAE metrics calculation completed in $< 1.5\text{ ms}$.
* **Invariant D5.3**: Automated session markdown report and 5 convergence charts generated within $< 500\text{ ms}$ at session close.

---

## 2. Advanced Research Enhancements Specification

---

### 2.1 Enhancement E1: Dual-Scale Online Adaptive Engine & Wald SPRT Drift Detector

#### 2.1.1 Purpose & Scope
Enhancement **E1** implements the full closed-loop learning engine (Layer 6). It integrates real-time micro-adaptation (per-interaction SGD with box-constrained simplex projection) and periodic macro-adaptation (epoch state machine executing `MERGE`, `FREEZE`, `DISCARD`, and `RECALIBRATE` policies), coupled with a cumulative Wald Sequential Probability Ratio Test (SPRT) drift detector.

#### 2.1.2 Module Decomposition & Source Code Artifacts
```
src/
├── learning/
│   ├── micro_sgd_optimizer.py       # Micro-adaptation SGD parameter updater
│   ├── macro_adaptation_engine.py   # Epoch state machine (MERGE/FREEZE/DISCARD/RECAL)
│   ├── wald_sprt_detector.py        # Sequential log-likelihood drift hypothesis tester
│   └── uncertainty_propagator.py    # End-to-end C_update confidence pipeline
```

#### 2.1.3 Mathematical Formulations & Macro Policies
1. **Global Propagated Update Confidence**:
   $$C_{\text{update}} = \left(\frac{1}{1 + \sigma_{\text{perceptual}}}\right) \cdot g_{\text{weight}}(\Delta_{\text{decision}}) \cdot c_{fb}(\Delta t) \cdot (1 - \text{ECE}_t) \cdot ACI_t$$
   $$\eta_{\text{eff}}(t) = \eta_0 \cdot C_{\text{update}}$$
2. **Micro-Adaptation Parameter Updates**:
   $$\tilde{\mathbf{w}}_a^{(t+1)} = \mathbf{w}_a^{(t)} + \eta_w(t) \cdot g_{\text{weight}}(S_a, \theta_a) \cdot c_{fb} \cdot e_a \cdot \mathbf{x}$$
   $$\mathbf{w}_a^{(t+1)} = \text{BoxSimplexProjection}(\tilde{\mathbf{w}}_a^{(t+1)}, \ \mathbf{l}=0.05\cdot\mathbf{1}, \ \mathbf{u}=0.85\cdot\mathbf{1})$$
   $$\theta_a^{(t+1)} = \text{clip}\left(\theta_a^{(t)} - \eta_\theta(t) \cdot c_{fb} \cdot e_a, \ 0.35, \ 0.85\right)$$
3. **Cumulative Wald SPRT Drift Detector**:
   $$S_m = S_{m-1} + \ln \frac{P(e_m \mid H_1: p_1 = 0.20)}{P(e_m \mid H_0: p_0 = 0.05)}$$
   $$\text{Decision Boundaries: } A = \ln\frac{1 - \beta}{\alpha} \approx 2.89, \quad B = \ln\frac{\beta}{1 - \alpha} \approx -2.89 \quad (\alpha=\beta=0.05)$$
   * If $S_m \ge 2.89$: Reject $H_0 \implies$ Trigger `MACRO_DRIFT_ALARM` $\implies$ Prompt 30s Recalibration.
   * If $S_m \le -2.25$: Accept $H_0 \implies$ Reset $S_m \leftarrow 0.0$.

#### 2.1.4 Acceptance Criteria & Verification Invariants
* **Invariant E1.1**: Micro SGD and simplex projection completes in $< 1.0\text{ ms}$ per approved interaction.
* **Invariant E1.2**: Macro policies execute deterministically: `MERGE` on steady improvement, `FREEZE` on convergence, `DISCARD` on ECE spikes ($>0.15$), and `RECALIBRATE` on Wald alarm ($S_m \ge 2.89$).
* **Invariant E1.3**: Monotonic version increment ($v_k \to v_{k+1}$) stored in persistent snapshot store.

---

### 2.2 Enhancement E2: State-Aware Explainability HUD Overlay

#### 2.2.1 Purpose & Scope
Enhancement **E2** provides a lightweight, GPU-less, semi-transparent desktop overlay rendering live confidence breakdowns, Tier-2 dwell progress rings, and active system health badges to maximize interaction transparency and user trust.

#### 2.2.2 Module Decomposition & Source Code Artifacts
```
src/
├── ui/
│   ├── __init__.py
│   ├── explainability_hud.py        # Semi-transparent PyQt6 click-through HUD
│   ├── confidence_bars.py           # Animated per-modality confidence visualizers
│   ├── dwell_confirmation_ring.py   # 600ms circular Tier-2 countdown renderer
│   └── health_badge_renderer.py     # State badge visualizer (LEARNING -> STABLE)
```

#### 2.2.3 Visual States & Health Badges
* `LEARNING`: System initializing; accumulating baseline interactions ($AG_t \le 0.05$).
* `IMPROVING`: Active adaptation gain observed ($AG_t > 0.05 \land WSI_t \ge 0.02$).
* `STABLE`: Weights converged ($ACI_t \ge 0.75 \land WSI_t < 0.02$).
* `DRIFTING`: Wald SPRT score rising ($S_m \ge 2.0$).
* `RECOVERING`: Post-recalibration stabilization ($S_m \ge 2.89 \to \text{reset}$).

#### 2.2.4 Acceptance Criteria & Verification Invariants
* **Invariant E2.1**: HUD render cycle overhead $\le 1.0\text{ ms}$ ($\le 2\%$ CPU utilization).
* **Invariant E2.2**: Zero click interception; completely transparent to mouse clicks outside HUD widgets.
* **Invariant E2.3**: Dwell ring animates smoothly at $60\text{ FPS}$ during Tier-2 confirmation.

---

### 2.3 Enhancement E3: Interactive Empirical Research Dashboard & Diagnostics Suite

#### 2.3.1 Purpose & Scope
Enhancement **E3** provides a dedicated multi-tab GUI for researchers and evaluators to observe real-time system metrics, monitor live SPRT trajectories, inspect parameter evolution curves, and conduct counterbalanced Latin Square A/B user studies.

#### 2.3.2 Module Decomposition & Source Code Artifacts
```
src/
├── ui/
│   ├── research_dashboard.py        # Multi-tab PyQt6 research control panel
│   ├── telemetry_stream_viewer.py   # Live scrolling table of ActionContext records
│   ├── parameter_evolution_plot.py  # Real-time Matplotlib weight trajectory curves
│   ├── sprt_trajectory_gauge.py     # Live Wald SPRT log-likelihood monitor
│   └── latin_square_panel.py        # Automated study protocol runner & task timer
```

#### 2.3.3 Acceptance Criteria & Verification Invariants
* **Invariant E3.1**: Dashboard operates in an asynchronous thread without reducing perception pipeline frame rates.
* **Invariant E3.2**: Live telemetry view updates within $< 100\text{ ms}$ of action dispatch.
* **Invariant E3.3**: Automated Latin Square runner coordinates task transitions and logs clean isomorphic datasets.

---

## 3. Documentation & Academic Replication Package

```
┌────────────────────────────────────────────────────────────────────────┐
│               DOCUMENTATION & REPLICATION DELIVERABLES                 │
├────────────────────────────────────────────────────────────────────────┤
│  DOC1: Canonical Project Proposal (adaptive-multimodal-hci-proposal.md)│
│  DOC2: IEEE 29148 SRS (adaptive-multimodal-hci-srs.md)                 │
│  DOC3: System Architecture (adaptive-multimodal-hci-architecture.md)   │
│  DOC4: Implementation Plan (adaptive-multimodal-hci-implementation.md) │
│  SDLC: Spiral SDLC Methodology (adaptive-multimodal-hci-sdlc-spiral.md)│
│  DOC5: Academic Research Paper Preprint & Open-Science Dataset Package │
└────────────────────────────────────────────────────────────────────────┘
```

1. **DOC1: Project Proposal**: Formalizes research thesis, theoretical motivation, formal Research Questions (**RQ1–RQ4**), real-world impact domains, and 5-stage validation methodology.
2. **DOC2: Software Requirements Specification (SRS)**: ISO/IEC/IEEE 29148 compliant document specifying functional requirements (`FR-1.1` to `FR-9.5`), non-functional constraints, and verification matrices.
3. **DOC3: System Architecture Specification**: Complete technical design detailing the 6 principled layers, closed-loop feedback pipeline, decoupled Layer 3 sub-stages, global uncertainty propagation model, dual-engine RAE, and schema definitions.
4. **DOC4: Project Implementation Plan**: 4-week engineering roadmap, milestone tracking, automated test suite invariants, and risk mitigation strategies.
5. **SDLC: Spiral SDLC Methodology Specification**: Risk-driven 7-spiral development lifecycle mapping Boehm's 4-quadrant framework to the 6-layer architecture, risk analysis, and milestone acceptance gates.
6. **DOC5: Academic Preprint & Replication Package**: Publication-ready LaTeX manuscript and anonymized benchmark evaluation datasets formatted for open-science dissemination.

---

## 4. Cross-Deliverable Inter-Module Threading & Data Flow

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM THREADING & INTER-MODULE COMMUNICATION                            │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [THREAD 1: Video Ingestion Daemon]                                                              │
│       │ (Raw Frame Buffer)                                                                       │
│       ▼                                                                                          │
│  [THREAD 2: Multimodal Perception & Smoothing (D1)]                                              │
│       │                                                                                          │
│       ├─► [Layer 2 Calibration Wizard (D3)] (During Onboarding)                                  │
│       │                                                                                          │
│       ▼ (FeatureVector x, Σ_sensor)                                                              │
│  [THREAD 3: Decision & Safety Execution Engine (D2, D4)]                                         │
│       │                                                                                          │
│       ├─► [Stage 3A Fusion & Intent Evaluator]                                                   │
│       ├─► [Stage 3B Safety Reasoner & Dwell Gate] ──► [UI Thread: Explainability HUD (E2)]       │
│       └─► [Stage 3C OS Context Dispatcher]                                                       │
│                │                                                                                 │
│                ▼ (ActionContext Record)                                                          │
│  [THREAD 4: Asynchronous Implicit Feedback Observer (D4)]                                        │
│       │ (Refractory Lockout & 5 Sub-Detectors)                                                   │
│       ▼ (FeedbackEvent)                                                                          │
│  [THREAD 5: Runtime Assessment Engine (RAE) (D5)]                                                │
│       │                                                                                          │
│       ├─► [Engine 5A: Runtime Metrics Engine] ──────► [UI Thread: Research Dashboard (E3)]       │
│       └─► [Engine 5B: Learning Gatekeeper]                                                       │
│                │                                                                                 │
│                ▼ (Validated Learning Signal / APPROVE)                                           │
│  [THREAD 6: Dual-Scale Adaptive Engine (E1)]                                                     │
│       │                                                                                          │
│       ├─► [Micro-Adaptation SGD & Box Simplex Projection]                                        │
│       ├─► [Macro-Adaptation Epoch State Machine & Wald SPRT]                                     │
│       └─► [Persistent Profile Store (Profile v_k+1)]                                             │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Deliverable Traceability & Verification Acceptance Matrix

| Deliverable ID | Component / Subsystem | Primary Verification Method | Test Module Artifact | Acceptance Gate |
|---|---|---|---|---|
| **D1** | Perception Pipeline & Smoothing | Automated Unit & Latency Benchmark | `tests/test_perception_pipeline.py`, `tests/test_latency_benchmark.py` | Latency $\le 20.5\text{ms}$, Jitter $\le 1.2\text{px}$ |
| **D2** | Fuser & Simplex Projection | Mathematical Invariant Unit Tests | `tests/test_simplex_projection.py`, `tests/test_confidence_fuser.py` | $\sum w_i = 1.0 \pm 10^{-6}, w_i \in [0.05, 0.85]$ |
| **D3** | Calibration Wizard & Profile | Geometry Unit & Wizard UI Test | `tests/test_calibration_geometry.py`, `tests/test_profile_snapshot_store.py` | Wizard $\le 90\text{s}$, $\text{RMSE} \le 45\text{px}$ |
| **D4** | Safety Gate & Feedback Observer | State Machine & Hook Unit Tests | `tests/test_safety_gatekeeper.py`, `tests/test_feedback_state_machine.py` | Tier-2 600ms dwell strictly enforced |
| **D5** | Runtime Assessment Engine (RAE)| Formulation Unit & Gate Tests | `tests/test_runtime_metrics_engine.py`, `tests/test_learning_gatekeeper.py` | $100\%$ precision on noise rejection |
| **E1** | Dual-Scale Adaptive Engine | Micro SGD & Epoch State Tests | `tests/test_micro_sgd_optimizer.py`, `tests/test_macro_adaptation.py` | Deterministic macro state transitions |
| **E2** | Explainability HUD Overlay | Qt Render & UI Benchmark Tests | `tests/test_explainability_hud.py` | Render overhead $\le 1.0\text{ms}$ ($\le 2\%$ CPU) |
| **E3** | Research Dashboard & Study UI | GUI Integration & Study Tests | `tests/test_research_dashboard.py`, `tests/test_study_manager.py` | Zero frame drops during telemetry sync |
| **DOC1–DOC5**| Documentation & Paper | Editorial & Peer-Review Checks | Canonical Markdown & LaTeX Suite | Complete compliance with IEEE standards |

---

## 6. Conclusion
This Project Deliverables Specification establishes the authoritative blueprint for all engineering, research, and documentation deliverables. By coupling rigorous mathematical invariants with decoupled architectural boundaries and automated verification suites, it guarantees seamless transition into codebase execution and empirical validation.
