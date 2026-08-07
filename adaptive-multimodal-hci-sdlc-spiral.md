# Software Development Life Cycle (SDLC) Specification: Research-Oriented Spiral Model

## Project Title
# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction

---

### Executive Summary & Methodology Rationale

The development of this project integrates **software engineering rigor, artificial intelligence research, online mathematical optimization, and human-computer interaction (HCI) experimental validation**. 

Standard commercial SDLC paradigms are fundamentally ill-suited for this scope:
* **Rigid Waterfall Model** fails because research systems cannot assume static algorithm specifications; theoretical feedback models, noise covariances, and gatekeeper thresholds require empirical calibration and continuous refinement.
* **Pure Agile / Scrum** fails because the core architectural requirements are already theoretically defined (Six Principled Layers), and sprint-based feature churn risks architectural fragmentation and unprincipled ad-hoc heuristics.

Consequently, the project adopts **Boehm's Spiral Model (Research-Oriented Variant)**. The Spiral Model is inherently **risk-driven, iterative, and validation-centric**. Each spiral cycle systematically addresses critical research and engineering uncertainties through mathematical modeling, rapid prototyping, rigorous invariant unit testing, and empirical evaluation.

```
                                    THE RESEARCH-ORIENTED SPIRAL SDLC
                                                    
                                    QUADRANT I: OBJECTIVES & CONSTRAINTS
                                                    ▲
                                                    │
                             Spiral 1: Architecture │ Spiral 7: Evaluation
                             [DOC1, DOC2, DOC3,     │ [E2, E3, DOC5,
                              DOC4, Master Specs]   │  A/B Study, LME]
                                           ┌────────┴────────┐
                                           │                 │
                                  Spiral 2 │                 │ Spiral 6
                                Perception │                 │ Online Learning
                                [D1]       │                 │ [E1]
                                           │    (START)      │
               QUADRANT IV: ───────────────┼────────●────────┼───────────────► QUADRANT II:
               REVIEW & TRANSITION         │                 │                 RISK ANALYSIS &
                                  Spiral 3 │                 │ Spiral 5        PROTOTYPING
                                  Decision │                 │ Assessment (RAE)
                                  [D2, D3] │                 │ [D5]
                                           │                 │
                                           └────────┬────────┘
                                   Spiral 4: Feedback│
                                   [D4]             │
                                                    ▼
                                    QUADRANT III: DEVELOPMENT & VERIFICATION
```

---

## 1. Master Traceability Matrix: Deliverables to Spiral Lifecycle

Every deliverable specified in [Project Deliverables Specification (`adaptive-multimodal-hci-deliverables.md`)](file:///d:/HCI/adaptive-multimodal-hci-deliverables.md) maps bijectively to a dedicated Spiral iteration, architectural layer, and automated verification suite:

| Deliverable ID | Deliverable Name & Scope | Architectural Layer | Target Spiral Cycle | Primary Codebase Modules | Verification Invariant & Suite | Release Bundle Artifact |
|---|---|---|---|---|---|---|
| **DOC1–4** | Master Specifications (Proposal, SRS, Architecture, Implementation Plan) | Cross-Cutting | **Spiral 1** | `docs/`, `configs/` | Documentation sign-off & peer review | `docs/` |
| **D1** | Multimodal Perception & Feature Extraction Pipeline | **Layer 1** | **Spiral 2** | `src/capture/`, `src/perception/` | $\le 20.5\text{ms}$ latency, $\le 1.2\text{px}$ jitter; `test_perception_pipeline.py` | `deliverables/D1_perception_pipeline/` |
| **D3** | Interactive Calibration & Profile Bootstrapping Wizard | **Layer 2** | **Spiral 3** | `src/calibration/`, `src/storage/` | $\le 90\text{s}$ duration, $\text{RMSE} \le 45\text{px}$; `test_calibration_geometry.py` | `deliverables/D3_calibration_wizard/` |
| **D2** | Weighted Confidence Fusion & Simplex Projection Engine | **Layer 3A** & **Layer 6** | **Spiral 3** | `src/decision/`, `src/learning/` | Simplex $\sum w_i = 1.0, w_i \in [0.05, 0.85]$; `test_simplex_projection.py` | `deliverables/D2_fusion_engine/` |
| **D4** | Decoupled Safety Dispatcher & Implicit Feedback Observer | **Layer 3B/3C** & **Layer 4** | **Spiral 4** | `src/decision/`, `src/feedback/` | $600\text{ms}$ dwell, $200\text{ms}$ refractory, 5 detectors; `test_feedback_state_machine.py` | `deliverables/D4_feedback_observer/` |
| **D5** | Runtime Assessment Engine (RAE) & Evaluation Suite | **Layer 5** | **Spiral 5** | `src/assessment/`, `src/evaluation/` | 7 metrics, 6 gatekeeper rules ($100\%$ outlier rejection); `test_learning_gatekeeper.py` | `deliverables/D5_runtime_assessment/` |
| **E1** | Dual-Scale Online Adaptive Engine & Wald SPRT Detector | **Layer 6** | **Spiral 6** | `src/learning/`, `src/storage/` | Ambiguity SGD, macro epoch policies, Wald $S_m \ge 2.89$; `test_macro_adaptation.py` | `deliverables/E1_dual_scale_engine/` |
| **E2** | State-Aware Explainability HUD Overlay | UI / Presentation | **Spiral 7** | `src/ui/explainability_hud.py` | $\le 1.0\text{ms}$ render overhead ($\le 2\%$ CPU); `test_explainability_hud.py` | `deliverables/E2_explainability_hud/` |
| **E3** | Interactive Empirical Research Dashboard & Diagnostics | UI / Presentation | **Spiral 7** | `src/ui/research_dashboard.py` | Live telemetry sync, zero frame drops; `test_research_dashboard.py` | `deliverables/E3_research_dashboard/` |
| **DOC5** | Academic Conference Manuscript & Replication Package | Publication & Study | **Spiral 7** | `paper/`, `evaluation/`, `notebooks/` | LaTeX compilation, Latin Square LME analysis | `paper/main.pdf` |

---

## 2. The Four Quadrants of Each Research Spiral

Every spiral cycle progresses clockwise through four formal quadrants, ensuring that technical and scientific risks are resolved before subsequent architectural layers depend on them:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             THE 4 FORMAL SPIRAL QUADRANTS                                        │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [QUADRANT I: DETERMINE OBJECTIVES, ALTERNATIVES & CONSTRAINTS]                                  │
│  • Define layer-specific functional requirements (FRs) and performance budgets ($<29.5\text{ms}$).│
│  • Identify theoretical alternatives and mathematical constraints (e.g., box-simplex bounds).   │
│                                                                                                  │
│  [QUADRANT II: IDENTIFY & RESOLVE RISKS (RISK ANALYSIS & PROTOTYPING)]                          │
│  • Enumerate algorithmic, numerical, latency, and human-behavioral risks.                        │
│  • Construct targeted proof-of-concept prototypes and run synthetic stress benchmarks.         │
│                                                                                                  │
│  [QUADRANT III: DEVELOP & VERIFY NEXT-LEVEL PRODUCT]                                             │
│  • Implement production-grade modules in `src/` adhering to strict type schemas.                 │
│  • Execute automated unit invariant tests, multi-layer integration suites, and latency checks.   │
│                                                                                                  │
│  [QUADRANT IV: REVIEW, ASSESS & PLAN NEXT SPIRAL]                                                │
│  • Evaluate empirical exit criteria against quantitative acceptance gates.                       │
│  • Freeze verified component baseline and transition to the next outer spiral.                   │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Breakdown of the Seven Research Spirals

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               MASTER SPIRAL LIFECYCLE ROADMAP                                    │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  • SPIRAL 1: Research Vision, Theoretical Formulations & Canonical Architecture [COMPLETED]      │
│  • SPIRAL 2: Core Multimodal Perception & Spatial-Temporal Filtering Prototype (Layer 1, D1)    │
│  • SPIRAL 3: Calibration Wizard & Mathematical Decision Engine (Layer 2 & 3, D2, D3)             │
│  • SPIRAL 4: Asynchronous Implicit Feedback Observation Pipeline (Layer 4, D4)                  │
│  • SPIRAL 5: Dual-Engine Runtime Assessment Engine (RAE) (Layer 5, D5)                           │
│  • SPIRAL 6: Dual-Scale Online Adaptive Learning & Drift Recovery Engine (Layer 6, E1)           │
│  • SPIRAL 7: Empirical User Study, Research Dashboard & Academic Dissemination (E2, E3, DOC5)    │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.1 Spiral 1: Research Vision, Theoretical Formulations & Canonical Architecture
* **Status**: **COMPLETED (BASELINE FROZEN)**
* **Primary Objective**: Establish the foundational scientific thesis, formalize research questions (**RQ1–RQ4**), draft complete mathematical models, specify system requirements (IEEE 29148 SRS), and design the master repository architecture.
* **Mapped Deliverables**: `DOC1`, `DOC2`, `DOC3`, `DOC4`, `adaptive-multimodal-hci-deliverables.md`, `adaptive-multimodal-hci-repo-structure.md`, `Proposed_Innovations.md`.
* **Quadrant Breakdown**:
  * *Quadrant I (Objectives)*: Unify the 6 principled layers into an unambiguous specification; eliminate vague heuristics.
  * *Quadrant II (Risk Analysis)*: Addressed the fundamental risk of scope ambiguity, unverified mathematical claims, and architectural coupling between assessment and adaptation.
  * *Quadrant III (Outputs Generated)*: Complete suite of canonical specifications under `docs/` and root configuration schemas under `configs/`.
  * *Quadrant IV (Exit Gate)*: Complete formal sign-off on the documentation suite without version-number clutter.

---

### 3.2 Spiral 2: Core Multimodal Perception & Feature Extraction Prototype (Layer 1, Deliverable D1)
* **Status**: **NEXT EXECUTION TARGET**
* **Primary Objective**: Ingest raw RGB video at native $30\text{ FPS}$, extract 3D facial landmarks, normalized iris gaze offsets, SolvePnP head pose Euler angles, and 3D hand gestures, applying velocity-scaled Holt-Winters smoothing.
* **Mapped Deliverable**: **`D1` (Multimodal Perception & Feature Extraction Pipeline)**.
* **Input Dependencies**: `Spiral 1` (`configs/default_config.yaml`, `src/storage/schemas.py`).
* **Key Research & Engineering Risks**:
  * *Risk R2.1*: Computer vision inference latency exceeds $20.5\text{ ms}$, causing frame drops and jitter on standard CPU hardware.
  * *Risk R2.2*: Coordinate jitter under static gaze/hand positions degrades confidence scores.
* **Risk Resolution & Prototyping Strategy**:
  * Isolate video capture in a dedicated `threading.Thread` with lock-free double buffering.
  * Benchmark MediaPipe FaceMesh (refine_landmarks=True) and Hands under 640x480 resolution.
  * Tune Holt-Winters dynamic alpha scaling $\alpha_t = \text{clip}(\alpha_0 + \gamma \|\mathbf{v}\|, 0.20, 0.85)$.
* **Codebase Implementation Modules**:
  * `src/capture/video_stream.py`, `src/capture/frame_types.py`
  * `src/perception/face_mesh_extractor.py`, `src/perception/head_pose_estimator.py`
  * `src/perception/hand_pose_extractor.py`, `src/perception/holt_winters_filter.py`
  * `src/perception/feature_pipeline.py`
* **Verification Invariants & Acceptance Gate**:
  * `Invariant D1.1`: Total perception cycle $\le 20.5\text{ ms}$ on 4-core CPU.
  * `Invariant D1.2`: Stationary jitter $\le 1.2\text{ px}$; dynamic tracking lag $\le 15\text{ ms}$.
  * `Invariant D1.3`: Zero-confidence suppression on eye blinks ($\text{EAR} < 0.18$).
* **Release Artifact**: `deliverables/D1_perception_pipeline/` (verification log + latency benchmark report).

---

### 3.3 Spiral 3: Calibration Wizard & Mathematical Decision Engine (Layer 2 & 3, Deliverables D2, D3)
* **Primary Objective**: Implement the 5-phase onboarding wizard (60–90s) bootstrapping user geometry, compute dot-product late fusion $S_a(\mathbf{x}) = \mathbf{w}_a^T \mathbf{x}$, enforce user-relative Tier-2 safety gating with 600ms visual dwell, and integrate the exact 1D bisection box simplex solver.
* **Mapped Deliverables**: **`D3` (Interactive Calibration Wizard)**, **`D2` (Weighted Confidence Fusion & Simplex Projection Engine)**.
* **Input Dependencies**: `Spiral 2` (Layer 1 `FeatureVector` output).
* **Key Research & Engineering Risks**:
  * *Risk R3.1*: User calibration drift or high residual error ($\text{RMSE} > 50\text{px}$) produces distorted initial weights.
  * *Risk R3.2*: Destructive Tier-2 actions trigger accidentally without explicit user confirmation.
* **Risk Resolution & Prototyping Strategy**:
  * Implement 5-point gaze affine transformation with RANSAC outlier rejection.
  * Decouple Layer 3 into Stage 3A (Fusion), Stage 3B (Safety Gatekeeper), and Stage 3C (Dispatcher).
  * Validate exact 1D bisection solver over $10^6$ synthetic weight vectors.
* **Codebase Implementation Modules**:
  * `src/calibration/wizard_controller.py`, `src/calibration/geometry_profiler.py`, `src/calibration/tempo_estimator.py`, `src/calibration/variance_weight_init.py`
  * `src/decision/confidence_fuser.py`, `src/decision/static_baseline_engine.py`, `src/decision/intent_evaluator.py`, `src/decision/safety_gatekeeper.py`, `src/decision/action_dispatcher.py`
  * `src/learning/simplex_projector.py`
* **Verification Invariants & Acceptance Gate**:
  * `Invariant D2.1`: $\left|\sum w_i - 1.0\right| \le 10^{-6}$ and $w_i \in [0.05, 0.85]$.
  * `Invariant D3.2`: Gaze calibration residual $\text{RMSE} \le 45\text{ px}$.
  * `Invariant D4.2`: Tier-2 commands blocked without uninterrupted $600\text{ ms}$ visual dwell.
* **Release Artifacts**: `deliverables/D2_fusion_engine/` and `deliverables/D3_calibration_wizard/`.

---

### 3.4 Spiral 4: Asynchronous Implicit Feedback Observation Pipeline (Layer 4, Deliverable D4)
* **Primary Objective**: Build the 4-window temporal state machine and 5 asynchronous negative sub-detectors to infer supervisory labels without intrusive user prompts.
* **Mapped Deliverable**: **`D4` (Decoupled Safety Dispatcher & Asynchronous Implicit Feedback Observer)**.
* **Input Dependencies**: `Spiral 3` (Layer 3 `ActionContext` dispatch events).
* **Key Research & Engineering Risks**:
  * *Risk R4.1*: Normal motor delay ($<200\text{ms}$) misclassified as intentional user correction.
  * *Risk R4.2*: Complex OS interactions (e.g., background window clicks) create false negative attributions.
* **Risk Resolution & Prototyping Strategy**:
  * Enforce strict 200ms Refractory Window ($[t_0, t_0 + 200\text{ms}]$) ignoring all input.
  * Implement 5 dedicated sub-detectors (`UndoHook`, `Reversal`, `Retry`, `Dismissal`, `Override`).
  * Apply continuous exponential confidence decay $c_{fb}(\Delta t) = \exp(-(\Delta t - 0.20)/\tau_{\text{user}})$.
* **Codebase Implementation Modules**:
  * `src/feedback/temporal_state_machine.py`, `src/feedback/undo_hook_detector.py`
  * `src/feedback/reversal_detector.py`, `src/feedback/retry_detector.py`
  * `src/feedback/dismissal_detector.py`, `src/feedback/override_detector.py`
* **Verification Invariants & Acceptance Gate**:
  * `Invariant D4.1`: Zero false triggers during Refractory Window.
  * `Invariant D4.3`: Undo hook captures `Ctrl+Z` reversals within $< 5\text{ ms}$.
  * `Invariant D4.4`: Sub-detector precision $\ge 90\%$ on synthetic interaction traces.
* **Release Artifact**: `deliverables/D4_feedback_observer/` (detector precision matrix + test log).

---

### 3.5 Spiral 5: Dual-Engine Runtime Assessment Engine (RAE) (Layer 5, Deliverable D5)
* **Primary Objective**: Implement Engine 5A (Runtime Metrics Engine) tracking seven continuous health metrics and Engine 5B (Learning Gatekeeper) enforcing six rejection rules before parameter updates.
* **Mapped Deliverable**: **`D5` (Runtime Assessment Engine & Automated Evaluation Suite)**.
* **Input Dependencies**: `Spiral 4` (Layer 4 `ObservedFeedback` signals).
* **Key Research & Engineering Risks**:
  * *Risk R5.1*: System learns from noisy or accidental interactions, leading to performance degradation.
  * *Risk R5.2*: Metric computation introduces frame latency overhead ($> 5\text{ ms}$).
* **Risk Resolution & Prototyping Strategy**:
  * Decouple metrics computation ($AG_t, LV_t, WSI_t, ACI_t, ECE_t, RR, DRT$) into an asynchronous evaluation cycle.
  * Enforce 6-rule validation firewall emitting explicit `GatekeeperVerdict(APPROVE/REJECT)`.
  * Auto-generate post-session markdown diagnostic reports with matplotlib convergence plots.
* **Codebase Implementation Modules**:
  * `src/assessment/runtime_metrics_engine.py`, `src/assessment/learning_gatekeeper.py`
  * `src/assessment/session_report_generator.py`, `src/assessment/failure_classifier.py`
* **Verification Invariants & Acceptance Gate**:
  * `Invariant D5.1`: $100\%$ precision in rejecting synthetic outlier/noisy feedback.
  * `Invariant D5.2`: Metrics calculation completed in $< 1.5\text{ ms}$.
  * `Invariant D5.3`: Automated session markdown report generated in $< 500\text{ ms}$.
* **Release Artifact**: `deliverables/D5_runtime_assessment/` (RAE test report + sample session report).

---

### 3.6 Spiral 6: Dual-Scale Online Adaptive Learning & Drift Recovery (Layer 6, Enhancement E1)
* **Primary Objective**: Integrate micro-adaptation (per-interaction SGD with box simplex projection), macro-adaptation epoch state machine (`MERGE`, `FREEZE`, `DISCARD`, `RECALIBRATE`), and cumulative Wald SPRT sequential drift detection.
* **Mapped Deliverable**: **`E1` (Dual-Scale Online Adaptive Engine & Hierarchical Wald SPRT Drift Detector)**.
* **Input Dependencies**: `Spiral 5` (Layer 5 approved `GatekeeperVerdict(APPROVE)` events).
* **Key Research & Engineering Risks**:
  * *Risk R6.1*: Parameter drift occurs under gradual ambient lighting or user posture shifts.
  * *Risk R6.2*: Over-adaptation on atypical gestures degrades general interaction accuracy.
* **Risk Resolution & Prototyping Strategy**:
  * Gate SGD updates by decision ambiguity $g_{\text{weight}}(\Delta_{\text{decision}})$ and global $C_{\text{update}}$.
  * Implement Wald SPRT log-likelihood ratio with decision boundaries $A = 2.89$ and $B = -2.25$.
  * Snapshot immutable profiles (`Profile v_k`) to SQLite/JSON store.
* **Codebase Implementation Modules**:
  * `src/learning/micro_sgd_optimizer.py`, `src/learning/macro_adaptation_engine.py`
  * `src/learning/wald_sprt_detector.py`, `src/learning/uncertainty_propagator.py`
  * `src/storage/profile_store.py`, `src/storage/telemetry_logger.py`
* **Verification Invariants & Acceptance Gate**:
  * `Invariant E1.1`: Micro SGD update and simplex projection completes in $< 1.0\text{ ms}$.
  * `Invariant E1.2`: Macro policies execute deterministically across all epoch boundaries.
  * `Invariant E1.3`: Wald SPRT triggers `MACRO_DRIFT_ALARM` within $\le 5$ error interactions under synthetic drift.
* **Release Artifact**: `deliverables/E1_dual_scale_engine/` (macro state validation log + drift trace).

---

### 3.7 Spiral 7: Empirical User Study, Research Dashboard & Paper Dissemination (Enhancements E2, E3, DOC5)
* **Primary Objective**: Deploy the semi-transparent PyQt6 Explainability HUD, execute counterbalanced Latin Square A/B user studies, conduct statistical analysis (Wilcoxon Signed-Rank, Linear Mixed-Effects), and compile the LaTeX conference paper preprint.
* **Mapped Deliverables**: **`E2` (Explainability HUD Overlay)**, **`E3` (Interactive Research Dashboard)**, **`DOC5` (Academic Publication & LaTeX Preprint Package)**.
* **Input Dependencies**: `Spiral 2` through `Spiral 6` (Full 6-Layer Integrated Closed-Loop System).
* **Key Research & Engineering Risks**:
  * *Risk R7.1*: HUD overlay interferes with desktop clicks or degrades CPU performance.
  * *Risk R7.2*: Order effects confound comparative A/B evaluation results.
* **Risk Resolution & Prototyping Strategy**:
  * Implement click-through window flags (`Qt.WindowTransparentForInput`) for HUD overlay.
  * Enforce strict counterbalanced Latin Square ordering ($A \to B$ vs. $B \to A$) with 5-minute washout.
  * Automate data extraction from JSONL telemetry into statistical analysis notebooks.
* **Codebase & Artifact Modules**:
  * `src/ui/explainability_hud.py`, `src/ui/research_dashboard.py`
  * `evaluation/study_manager.py`, `evaluation/analysis/run_linear_mixed_effects.py`
  * `notebooks/01_latency_and_framerate_profiling.ipynb` to `05_empirical_user_study_statistical_lme.ipynb`
  * `paper/main.tex`, `paper/sections/`, `paper/figures/`, `paper/tables/`
* **Verification Invariants & Acceptance Gate**:
  * `Invariant E2.1`: HUD render overhead $\le 1.0\text{ ms}$ ($\le 2\%$ CPU).
  * `Invariant E3.1`: Telemetry logging occurs asynchronously with zero dropped frames.
  * `Invariant DOC5.1`: LaTeX preprint compiles cleanly with verified statistical tables.
* **Release Artifacts**: `deliverables/E2_explainability_hud/`, `deliverables/E3_research_dashboard/`, and `paper/main.pdf`.

---

## 4. Cross-Spiral Deliverable Integration & Cumulative Value Stream

The deliverables integrate cumulatively across the 7 Spirals, ensuring continuous, regression-free system maturation:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              CUMULATIVE DELIVERABLE VALUE STREAM                                       │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                        │
│  [SPIRAL 1] ──► DOC1–4 & Architectural Blueprints                                                      │
│                   │                                                                                    │
│                   ▼                                                                                    │
│  [SPIRAL 2] ──► D1 (Perception Pipeline: FaceMesh, Pose, Hands, Holt-Winters Filter)                   │
│                   │                                                                                    │
│                   ▼                                                                                    │
│  [SPIRAL 3] ──► D3 (Calibration Wizard) + D2 (Stage 3A Fusion & Box Simplex Projector)                 │
│                   │                                                                                    │
│                   ▼                                                                                    │
│  [SPIRAL 4] ──► D4 (Stage 3B Safety Dwell Gate + Layer 4 Asynchronous Implicit Feedback Observer)      │
│                   │                                                                                    │
│                   ▼                                                                                    │
│  [SPIRAL 5] ──► D5 (Layer 5 Dual Runtime Assessment Engine: 7 Metrics + 6-Rule Gatekeeper Firewall)    │
│                   │                                                                                    │
│                   ▼                                                                                    │
│  [SPIRAL 6] ──► E1 (Layer 6 Dual-Scale Online Learning: Ambiguity SGD + Macro Epochs + Wald SPRT)     │
│                   │                                                                                    │
│                   ▼                                                                                    │
│  [SPIRAL 7] ──► E2 (Explainability HUD) + E3 (Research Dashboard) + DOC5 (LaTeX Conference Preprint)   │
│                                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Comprehensive Risk Management & Mitigation Matrix

| Spiral Cycle | Deliverable ID | Key Identified Risk | Risk Category | Severity | Automated Mitigation / Verification Method |
|---|---|---|---|---|---|
| **Spiral 2** | **D1** | Perception pipeline latency exceeds 20.5ms on CPU hardware. | Technical / Performance | **HIGH** | Dedicated capture thread + double buffer + Holt-Winters velocity scaling; verified via `test_frame_latency.py`. |
| **Spiral 2** | **D1** | Eye blinks cause false gaze saccades. | Algorithmic | **MEDIUM** | Instant confidence suppression when $\text{EAR} < 0.18$; verified via `test_face_mesh_extractor.py`. |
| **Spiral 3** | **D3** | User calibration residual $\text{RMSE} > 45\text{px}$. | Human Factors / Geometry | **MEDIUM** | Gaze affine solver with RANSAC outlier filtering; verified via `test_calibration_geometry.py`. |
| **Spiral 3** | **D2** | Destructive Tier-2 action executed accidentally. | Safety / System | **CRITICAL** | User-relative gate $\theta_{\text{tier2}, a}$ + 600ms visual dwell + 3.0s undo hook; verified via `test_safety_gatekeeper.py`. |
| **Spiral 4** | **D4** | Normal user motor latency misidentified as negative correction. | Behavioral / Temporal | **HIGH** | Strict 200ms Refractory Window lockout; verified via `test_feedback_state_machine.py`. |
| **Spiral 4** | **D4** | Sub-detectors emit contradictory feedback signals. | Algorithmic | **MEDIUM** | Gatekeeper Rule 5 contradiction check drops conflicting signals; verified via `test_learning_gatekeeper.py`. |
| **Spiral 5** | **D5** | System overfits to noisy / accidental interaction labels. | Learning / Stability | **CRITICAL** | Engine 5B 6-rule validation firewall ($k \ge 3, c_{fb} \ge 0.40$, SNR check); verified via `test_learning_gatekeeper.py`. |
| **Spiral 6** | **E1** | Uncontrolled parameter drift under ambient lighting changes. | Convergence / Drift | **HIGH** | Wald SPRT sequential drift detector ($S_m \ge 2.89$) prompting recalibration; verified via `test_wald_sprt_detector.py`. |
| **Spiral 6** | **E1** | Weight projection violates boundary constraints. | Numerical / Math | **CRITICAL** | Exact 1D dual bisection box-constrained simplex solver; verified via `test_simplex_projection.py`. |
| **Spiral 7** | **DOC5** | Carryover / fatigue order effects confound A/B user study. | Experimental / HCI | **HIGH** | Counterbalanced Latin Square design + 5-min washout; modeled via Linear Mixed-Effects (`Subject` random effect). |
| **Spiral 7** | **E2** | Visual HUD overlay blocks user desktop interaction. | Usability / OS | **MEDIUM** | Non-modal click-through window flags (`Qt.WindowTransparentForInput`); verified via `test_explainability_hud.py`. |

---

## 6. Master Spiral Lifecycle & Milestone Acceptance Matrix

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               MASTER MILESTONE EXIT CRITERIA                                     │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [SPIRAL 1 GATE]: All 7 canonical documents drafted, formatted, and verified.     ──► [PASS]     │
│  [SPIRAL 2 GATE]: Video capture, MediaPipe extractors, Holt-Winters <= 20.5ms.    ──► [PENDING]  │
│  [SPIRAL 3 GATE]: Calibration wizard RMSE <= 45px, Tier-2 600ms dwell enforced.   ──► [PENDING]  │
│  [SPIRAL 4 GATE]: Feedback state machine zero false refractory triggers.         ──► [PENDING]  │
│  [SPIRAL 5 GATE]: RAE Engine 5A metrics & Engine 5B 100% outlier rejection.       ──► [PENDING]  │
│  [SPIRAL 6 GATE]: Micro SGD + Simplex Projector + Wald SPRT drift detection.      ──► [PENDING]  │
│  [SPIRAL 7 GATE]: A/B study completed, LME model fitted, LaTeX preprint compiled.──► [PENDING]  │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Conclusion & Operational Guidelines

Adopting the **Research-Oriented Spiral SDLC** guarantees that every software component is built upon empirically verified, mathematically sound lower layers. 

### Development Rules for Every Spiral:
1. **Never skip Quadrant II Risk Prototyping**: Build targeted micro-tests before implementing production classes.
2. **Strict Invariant Verification**: All code written in Quadrant III must have corresponding unit tests in `tests/unit/` verifying mathematical invariants.
3. **Formal Quadrant IV Exit Gate**: A spiral is only marked complete when all performance budgets and invariant tests pass.

With **Spiral 1 (Research & Architecture)** complete, the project transitions immediately into **Spiral 2 (Core Multimodal Perception & Feature Extraction Prototype - Deliverable D1)**.
