# Project Implementation Plan: High-Level Engineering Overview

## Project Title
# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction

---

## 1. Project Objective & Formal Research Questions

### Objective
To engineer, validate, and benchmark a real-time, non-intrusive Human-Computer Interaction (HCI) framework combining ocular gaze, head pose orientation, and hand gesture tracking. The system uses gaze to resolve **where** to act and gesture to resolve **what** action to perform. Decision policies are continuously personalized via online updates driven by implicit behavioral feedback, autonomously monitored and validated by a dedicated **Runtime Assessment Engine (RAE)**.

### Research Questions (RQs)
* **RQ1 (Personalization Effectiveness)**: Does online personalization via implicit feedback significantly reduce interaction errors (FAR, FRR) and Task Completion Time compared to static-rule multimodal fusion baselines?
* **RQ2 (Implicit Supervision Viability)**: Can continuous, decay-weighted implicit feedback provide sufficient supervision to steer parameter updates without requiring explicit user labeling?
* **RQ3 (Runtime Self-Assessment Accuracy)**: Can a dedicated RAE reliably determine when an interaction signal is trustworthy and quantify whether updates improve or degrade interaction quality in real time?
* **RQ4 (Longitudinal Retention & Robustness)**: Can learned user profiles maintain stability and reduce cold-start friction across multiple sessions while robustly adapting to drift?

---

## 2. Architectural Deliverables Breakdown

| Deliverable ID | Component Name | Primary Scope & Architectural Responsibilities |
|---|---|---|
| **D1** | **Multimodal Perception Pipeline** | Threaded webcam ingestion (30 FPS), FaceMesh/Iris + Hands, SolvePnP head pose, Holt-Winters smoothing, Gaze Dwell Tracker (dwell_ms, stability, anchor), Gesture Vocabulary Engine (13 fixed tokens, sigmoid confidence, FIST guard), Active Modality Arbiter (rolling device flags, arbitration logic). |
| **D2** | **Command Composer & Simplex Engine** | Two-stage asymmetric Command Composer (Stage A1: spatial target, Stage A2: Tier 0 intent gate, Stage A3: composition), exact 1D bisection box-constrained simplex projector ($w_i \in [0.05, 0.85]$). |
| **D3** | **Interactive Calibration Wizard** | 60--90s 5-phase onboarding capturing gaze affine map, pose ellipsoid, REST pose (FIST landmark geometry), per-token gesture thresholds, tempo $\tau_\text{user}$, and `Profile v1` with all 7 new ProfileSnapshot fields. |
| **D4** | **Safety Dispatcher & Feedback Observer** | Stage 3B Tier-1/Tier-2 safety gates (600ms dwell, 3.0s undo hook), Stage 3C UIAutomation keyboard handoff (KEYBOARD_HANDOFF mode), Layer 4 4-window temporal state machine + 5 asynchronous sub-detectors. |
| **D5** | **Runtime Assessment Engine (RAE)** | Engine 5A: 7 health metrics ($AG_t, LV_t, WSI_t, ACI_t, ECE_t, RR, DRT$) + Engine 5B: 6-rule gatekeeper firewall + automated session report generator. |
| **E1** | **Dual-Scale Adaptive Engine** | Micro-SGD on expanded parameter set ($\mathbf{w}_\text{spatial}, \theta_a, \alpha, \tau_\text{dwell}, \tau_\text{intent}$, per-gesture thresholds) + macro epoch state machine + Wald SPRT drift detector. |
| **E2** | **Explainability HUD** | Low-overhead PyQt6 overlay: modality confidence bars, Tier-2 dwell ring, health badges, keyboard handoff indicator. |
| **E3** | **Research Dashboard** | Live ACI gauge, SPRT trajectory, parameter evolution curves, Latin Square study manager. |

---

## 3. Phased Engineering Roadmap

This overview maps to the **Seven Research Spirals** detailed in the **[Spiral SDLC Methodology Specification](file:///d:/HCI/adaptive-multimodal-hci-sdlc-spiral.md)**, which carries all per-cycle tasks, risk prototyping strategies, acceptance gates, and codebase module listings.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                    HIGH-LEVEL PHASED ENGINEERING ROADMAP                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  PHASE 1 — PERCEPTION & VOCABULARY (Spirals 2-3, Deliverable D1)                      │
│  • Threaded capture + FaceMesh/Iris + SolvePnP + Holt-Winters filter                  │
│  • Gaze Dwell Tracker (dwell_ms, gaze_stability, gaze_anchor)                          │
│  • Gesture Vocabulary Engine (13 fixed tokens, FIST guard)                             │
│  • Active Modality Arbiter (4 device modes, proactive Midas Touch prevention)         │
│  • Schema bootstrap: PerceptionFrame, GestureClassification, gesture_vocabulary.yaml   │
│                                                                                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 2 — CALIBRATION & DECISION ENGINE (Spiral 3, Deliverables D2, D3)              │
│  • 5-phase calibration wizard (Phase D: REST pose + gesture thresholds)                │
│  • Two-stage Command Composer (A1 spatial / A2 Tier 0 / A3 asymmetric composition)    │
│  • Stage 3B Tier-1/Tier-2 safety + Stage 3C UIAutomation keyboard handoff             │
│  • 1D bisection simplex projector + Profile v1 with all 7 new ProfileSnapshot fields  │
│                                                                                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 3 — FEEDBACK & ASSESSMENT (Spirals 4-5, Deliverables D4, D5)                   │
│  • Layer 4: 4-window state machine + 5 sub-detectors (Arbiter complements SD-5)       │
│  • Layer 5: 7 health metrics + 6-rule gatekeeper + session report generator           │
│                                                                                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 4 — ONLINE LEARNING & DRIFT DETECTION (Spiral 6, Enhancement E1)              │
│  • Micro-SGD on expanded parameter set + box-simplex projection                        │
│  • Macro epoch state machine + Wald SPRT drift detector                                │
│  • Versioned ProfileSnapshot (all 7 new fields persisted)                              │
│                                                                                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  PHASE 5 — HUD, DASHBOARD & DISSEMINATION (Spiral 7, E2, E3, DOC5)                   │
│  • PyQt6 Explainability HUD + Research Dashboard                                       │
│  • Counterbalanced A/B user study execution (N=4-6, Latin Square)                     │
│  • Wilcoxon + LME statistical analysis + LaTeX conference paper preprint              │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Automated Verification & Test Suite

| Test Module | Target Component | Validation Criteria & Invariants Tested |
|---|---|---|
| `test_gaze_dwell_tracker.py` | Layer 1 Dwell Tracker | `gaze_anchor` only declared at `dwell_ms >= tau_dwell`; overhead `< 0.3 ms`. |
| `test_gesture_vocabulary.py` | Layer 1B Token Dict | All 13 tokens loadable from YAML; unknown tokens rejected at parse time. |
| `test_gesture_classifier.py` | Layer 1B Classifier | FIST always `NO_ACTION`; confidence in `[0,1]`; latency `< 0.5 ms`. |
| `test_modality_arbiter.py` | Modality Arbiter | Correct DEVICE_MODE for all 4 states on synthetic device traces. |
| `test_command_composer.py` | Layer 3A Composer | Asymmetric $S_a$ correct; self-contained gestures bypass gaze gate entirely. |
| `test_tier0_intentionality_gate.py` | Layer 3A Tier 0 Gate | Gestures held `< tau_intent` never dispatch any OS action. |
| `test_simplex_projection.py` | Layer 6 Optimizer | $\sum w_i = 1.0 \pm 10^{-6}$; $w_i \in [0.05, 0.85]$ across 10,000 random vectors. |
| `test_layer3_decoupling.py` | Layer 3 Sub-stages | Independent execution of Composer (3A), Safety (3B), Dispatcher (3C). |
| `test_keyboard_handoff.py` | Layer 3C KB Handoff | KEYBOARD_HANDOFF within `< 1 ms` of focus change; zero gestures during text input. |
| `test_feedback_state_machine.py` | Layer 4 State Machine | 200ms refractory lockout; correct $c_{fb}(t)$ exponential decay. |
| `test_negative_sub_detectors.py` | Layer 4 Sub-detectors | Attribution correctness for all 5 negative signal types. |
| `test_runtime_metrics_engine.py` | Layer 5A Metrics | All 7 metrics correct vs. analytical ground truth. |
| `test_learning_gatekeeper.py` | Layer 5B Gatekeeper | 100% precision rejection on all 6 outlier rule cases. |
| `test_macro_adaptation.py` | Layer 6 Macro Engine | Deterministic state transitions across all epoch boundaries. |
| `test_uncertainty_propagation.py` | Global $C_\text{update}$ | $\eta_\text{eff} = \eta_0 \cdot C_\text{update}$ scaling correctness. |
| `test_profile_snapshot_store.py` | Profile Store | All 7 new fields present; JSON round-trip immutability. |
| `test_latency_benchmark.py` | End-to-End Pipeline | Full frame cycle `< 33 ms` sustained on CPU. |

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
