# Project Implementation Plan & Engineering Roadmap

## Project Title
# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction

---

## 1. Project Overview & Formal Research Objectives

### Objective
To engineer, validate, and benchmark a real-time, non-intrusive Human-Computer Interaction (HCI) framework combining ocular gaze, head pose orientation, and hand gesture tracking. The system dynamically personalizes decision thresholds and modality confidence weights per user via online updates driven by implicit behavioral feedback, continuously monitored and validated by a dedicated **Runtime Assessment Engine (RAE)**.

### Research Questions (RQs)
* **RQ1 (Personalization Effectiveness)**: Does online personalization via implicit feedback significantly reduce interaction errors (False Activation Rate, False Rejection Rate) and Task Completion Time compared to static-rule multimodal fusion baselines?
* **RQ2 (Implicit Supervision Viability)**: Can continuous, decay-weighted implicit feedback provide sufficient supervision to steer parameter updates without requiring explicit user labeling?
* **RQ3 (Runtime Self-Assessment Accuracy)**: Can a dedicated runtime assessment engine reliably determine when an interaction signal is trustworthy, and quantify whether updates improve or degrade interaction quality in real time?
* **RQ4 (Longitudinal Retention & Robustness)**: Can learned user profiles maintain stability and reduce cold-start friction across multiple sessions, while robustly adapting to drift via sequential testing?

---

## 2. Architectural Deliverables Breakdown

| Deliverable ID | Component Name | Primary Scope & Architectural Responsibilities |
|---|---|---|
| **D1** | **Multimodal Perception Layer** | Threaded webcam ingestion (30 FPS), MediaPipe FaceMesh/Iris + Hands, SolvePnP head pose, and Holt-Winters adaptive smoothing filter. |
| **D2** | **Weighted Decision Engine & Projection** | Vectorized confidence fusion ($S_a(\mathbf{x}) = \mathbf{w}_a^T \mathbf{x}$), exact 1D bisection box-constrained simplex projection solver ($w_i \in [0.05, 0.85]$). |
| **D3** | **Interactive Calibration Wizard** | 60–90 second 5-phase onboarding capturing gaze affine mapping $\mathbf{M}_{\text{gaze}}$, 95% pose ellipsoid $\mathcal{E}_{\text{head}}$, tempo $\tau_{\text{user}}$, and variance-informed initial weights (`Profile v1`). |
| **D4** | **Safety Dispatcher & Feedback Observer** | Decoupled Layer 3B (Tier-2 User-Relative Safety Gate) and Layer 4 Temporal State Machine with 5 asynchronous negative sub-detectors and continuous decay confidence $c_{fb}(\Delta t)$. |
| **D5** | **Runtime Assessment Engine (RAE)** | Dual-engine RAE: 5A Metrics Engine ($AG_t, LV_t, WSI_t, ACI_t, ECE_t, RR, DRT$) + 5B Intelligent Multi-Criteria Decision Validator, plus automated Session Report Generator. |
| **E1** | **Dual-Scale Adaptive Engine** | Real-time micro-adaptation (per-interaction SGD) + macro-adaptation state machine (`MERGE`, `FREEZE`, `DISCARD`, `RECALIBRATE`) with Wald SPRT drift detection. |
| **E2** | **State-Aware Explainability HUD** | Low-overhead desktop overlay displaying live modality confidence bars, Tier-2 confirmation ring, and active health state badges (`LEARNING`, `IMPROVING`, `STABLE`, `DRIFTING`, `RECOVERING`). |
| **E3** | **Empirical Research Dashboard** | Interactive diagnostic dashboard rendering real-time ACI gauge, SPRT trajectory, parameter evolution curves, and automated Latin Square study manager. |

---

## 3. Four-Week Execution Roadmap Mapped to the Spiral SDLC

The 4-week engineering execution roadmap aligns directly with the **Seven Iterative Research Spirals** defined in the **[Spiral SDLC Methodology Specification (`adaptive-multimodal-hci-sdlc-spiral.md`)](file:///d:/HCI/adaptive-multimodal-hci-sdlc-spiral.md)**:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                   4-WEEK EXECUTION ROADMAP MAPPED TO THE 7 RESEARCH SPIRALS                            │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  WEEK 1: Perception Core & Mathematical Decision Engine (Spirals 1, 2, 3)                              │
│  • Spiral 1 (Completed): Research vision, SRS, Architecture, Deliverables, and Repo Structure.         │
│  • Spiral 2 (Days 1–3): Threaded webcam video pipeline, MediaPipe FaceMesh/Iris + Hands, Holt-Winters. │
│  • Spiral 3 (Days 4–7): Weighted fusion engine, exact 1D bisection simplex solver, baseline engine.   │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  WEEK 2: Calibration, Safety Dispatcher & Runtime Assessment Engine (Spirals 3, 4, 5)                  │
│  • Spiral 3 (Days 8–9): 5-Phase calibration wizard & variance-informed profile synthesis (`Profile v1`)│
│  • Spiral 4 (Days 10–12): Layer 3B Tier-2 safety gate & Layer 4 4-window feedback observer (5 detectors)│
│  • Spiral 5 (Days 13–14): Layer 5 dual engines (5A Metrics Engine + 5B 6-Rule Gatekeeper Firewall).    │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  WEEK 3: Dual-Scale Adaptive Engine & Empirical Pilot Benchmark (Spirals 6, 7)                         │
│  • Spiral 6 (Days 15–17): Micro SGD + Macro epoch state machine (`MERGE`/`FREEZE`) + Wald SPRT detector│
│  • Spiral 5 (Days 18–19): Automated Session Diagnostic Report generator & matplotlib convergence charts│
│  • Spiral 7 (Days 20–21): Within-subjects counterbalanced A/B pilot study execution (N=4–6).          │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  WEEK 4: Explainability HUD, Dashboard & Academic Dissemination (Spiral 7)                             │
│  • Spiral 7 (Days 22–24): Low-overhead Explainability HUD overlay (PyQt6) & Research Dashboard (E2, E3)│
│  • Spiral 7 (Days 25–26): Statistical modeling (Wilcoxon Signed-Rank + Linear Mixed-Effects Models).   │
│  • Spiral 7 (Days 27–28): Academic conference paper preprint compilation (`paper/main.pdf`), DOC5.    │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Automated Verification & Test Suite

| Test Module | Target Component | Validation Criteria & Invariants Tested |
|---|---|---|
| `test_simplex_projection.py` | Layer 6 Optimizer | Verifies $\sum_{i=1}^3 w_{a, i} = 1.0 \pm 10^{-6}$ and $w_{a, i} \in [0.05, 0.85]$ across 10,000 random perturbation vectors. |
| `test_layer3_decoupling.py` | Layer 3 Decision Sub-stages | Verifies independent execution of Fusion (3A), Safety Reasoning (3B), and Context Dispatcher (3C). |
| `test_feedback_state_machine.py` | Layer 4 Feedback Observer | Verifies 200ms refractory lockout, continuous exponential decay $c_{fb}(\Delta t)$, and stability expiration at $t > 1.8\text{s}$. |
| `test_negative_sub_detectors.py` | Layer 4 Sub-detectors | Verifies synthetic event attribution for OS Undo, Directional Reversals, Retries, Dismissals, and Overrides. |
| `test_runtime_metrics_engine.py` | Layer 5A Metrics Engine | Verifies mathematical correctness of $AG_t, LV_t, WSI_t, ACI_t, ECE_t, RR, DRT$ against analytical ground-truth data. |
| `test_learning_gatekeeper.py` | Layer 5B Gatekeeper | Validates all 6 rejection rules: sample floor, low confidence, neutral state, macro drift active, contradictions, and sensor noise. |
| `test_macro_adaptation.py` | Layer 6 Macro Pipeline | Validates macro policy state transitions: `MERGE`, `FREEZE`, `DISCARD`, and `RECALIBRATE`. |
| `test_uncertainty_propagation.py` | Global Uncertainty Model | Verifies calculation of $C_{\text{update}}$ and effective learning rate scaling $\eta_{\text{eff}} = \eta_0 \cdot C_{\text{update}}$. |
| `test_profile_snapshot_store.py` | Profile Store | Verifies JSON serialization, deserialization, and immutability across sequential profile versions ($v_k \to v_{k+1}$). |
| `test_latency_benchmark.py` | End-to-End Pipeline | Verifies end-to-end frame processing completes in $< 33\text{ms}$ on CPU. |

---

## 5. Empirical Pilot Study Protocol & Statistical Analysis

### 5.1 Within-Subjects Counterbalanced A/B Protocol ($N = 4\text{--}6$)
* **Design**: 2 Conditions (Condition A: Static Rule Baseline; Condition B: Self-Evaluating Adaptive Engine).
* **Counterbalancing**: Cohort 1 ($N/2$ participants) completes $A \to B$; Cohort 2 ($N/2$ participants) completes $B \to A$.
* **Washout Period**: 5-minute cognitive washout between conditions to eliminate residual motor bias.
* **Isomorphic Task Sets**: 3 standardized desktop interaction scripts (Document Navigation, Tab & Window Management, Media Control) with randomized target sequences.

### 5.2 Metrics & Statistical Modeling
1. **Primary Objective Metrics**:
   - False Activation Rate (FAR, errors/minute)
   - False Rejection Rate (FRR, missed triggers/opportunity)
   - Task Completion Time (TCT, seconds)
   - Correction Rate across 5 session epochs (Epoch 1 to Epoch 5)
2. **Subjective UX Instruments**:
   - System Usability Scale (SUS, 0–100)
   - Raw NASA-TLX (Mental, Physical, Temporal, Performance, Effort, Frustration)
   - 7-Item Adaptation Scale (Perceived adaptability, predictability, recovery fluency, visual clarity)
3. **Statistical Hypothesis Testing**:
   - Paired Wilcoxon Signed-Rank Test ($\alpha = 0.05$) comparing Condition A vs. Condition B.
   - Linear Mixed-Effects Model: $\text{Metric} \sim \text{Condition} + \text{Order} + \text{Condition} \times \text{Order} + (1|\text{Subject})$ to isolate genuine adaptation gains from ordering/practice effects.

---

## 6. Risk Mitigation & Fallback Matrix

| Technical Risk | Likelihood | Impact | Architectural Mitigation Strategy |
|---|---|---|---|
| **Early Overfitting on Noisy Initial Cues** | Moderate | High | Gatekeeper warmup floor ($k \ge 3$ per action), box simplex constraints ($w_i \in [0.05, 0.85]$), and variance-informed bootstrap initialization. |
| **Environmental Lighting & Pose Drift** | High | Moderate | Continuous Wald SPRT drift monitoring ($S_m \ge 2.89$), which locks micro-updates and triggers a 30s micro-recalibration. |
| **MediaPipe Landmark Jitter Under CPU Load** | Moderate | Moderate | Adaptive Holt-Winters exponential smoothing filter dynamically scaling $\alpha_t$ with motion velocity. |
| **OS Permission / Hooking Latency** | Low | Moderate | Dedicated daemon thread for OS hooks with lock-free ring buffer queueing. |
| **Participant Learning Confound (Practice Effect)** | High | High | Counterbalanced Latin Square order design ($A \to B$ vs. $B \to A$) and isomorphic task scripts. |
