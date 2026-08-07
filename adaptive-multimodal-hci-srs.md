# Software Requirements Specification (SRS)

## Project Title
# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction

---

### Standard Compliance
* **Standard**: ISO/IEC/IEEE 29148:2018 & IEEE 830-1998 Standards for Software Engineering — Software Requirements Specifications
* **Document Status**: Canonical Project Baseline Specification
* **Target Environment**: Windows 10/11, Linux, macOS (Python 3.11+, Standard RGB Webcam)

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) provides the complete, authoritative engineering requirements for the **Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction (HCI)**. It establishes the functional, mathematical, interface, performance, safety, privacy, and verification constraints governing the implementation of a real-time, touchless desktop interaction system that personalizes decision policies via continuous implicit behavioral feedback and autonomous runtime self-assessment.

### 1.2 Document Conventions & Mathematical Notation
* **Mandatory Requirement**: Denoted by the keyword `SHALL`.
* **Advisory / Recommended**: Denoted by the keyword `SHOULD`.
* **Optional / Future Enhancement**: Denoted by the keyword `MAY`.
* **Mathematical Notation**:
  * $\mathbf{x} = [s_{\text{gaze}}, s_{\text{head}}, s_{\text{hand}}]^T \in [0, 1]^3$: Normalized perceptual feature confidence vector.
  * $\mathbf{w}_a = [w_{a, \text{gaze}}, w_{a, \text{head}}, w_{a, \text{hand}}]^T \in \Delta^2$: Per-action modality weight vector on the unit 2-simplex ($\sum_{i=1}^3 w_{a, i} = 1.0, w_{a, i} \in [0.05, 0.85]$).
  * $S_a(\mathbf{x}) = \mathbf{w}_a^T \mathbf{x} = \sum_{i=1}^3 w_{a, i} s_i \in [0.0, 1.0]$: Fused multimodal confidence score for action candidate $a$.
  * $\theta_a \in [0.35, 0.85]$: Per-user, per-action activation threshold.
  * $\theta_{\text{tier2}, a} = \min(0.95, \max(\theta_a + 0.15, \mu_{S, a} + 1.5\sigma_{S, a}))$: User-relative destructive safety threshold.
  * $c_{fb}(\Delta t) = \exp(-(\Delta t - 0.20)/\tau_{\text{user}})$: Continuous supervisory feedback confidence.
  * $C_{\text{update}}$: Global learning confidence modulating SGD step size ($\eta_{\text{eff}} = \eta_0 \cdot C_{\text{update}}$).
  * $S_m$: Cumulative Wald Sequential Probability Ratio Test (SPRT) log-likelihood score.
  * $AG_t, LV_t, WSI_t, ACI_t, ECE_t, RR, DRT$: Core runtime assessment metrics.

### 1.3 Intended Audience
This specification is intended for software engineers, machine learning researchers, HCI practitioners, test engineers, and academic reviewers evaluating the theoretical correctness and engineering feasibility of the system.

### 1.4 Project Scope & Core Thesis
* **Core Research Thesis**: A generalizable, runtime self-evaluating adaptive decision architecture that continuously observes, validates, and personalizes decision policies in real time using asynchronous implicit behavioral feedback without explicit labeling or deep learning overhead.
* **Domain Vehicle**: Vision-based multimodal (ocular gaze, head pose, hand gesture) HCI executing at $\ge 30\text{ FPS}$ entirely on consumer CPU hardware.

### 1.5 Academic & Technical References
1. MediaPipe Holistic & Hands: Lugaresi et al., *MediaPipe: A Framework for Building Perception Pipelines*, arXiv:1906.08172, 2019.
2. Perspective-n-Point Head Pose: Lepetit et al., *EPnP: An Accurate O(n) Solution to the PnP Problem*, IJCV, 2009.
3. Box-Constrained Simplex Projection: Duchi et al., *Efficient Projections onto the L1-Ball for Learning in High Dimensions*, ICML, 2008.
4. Sequential Hypothesis Drift Testing: Wald, A., *Sequential Analysis*, John Wiley & Sons, 1947.
5. Standardized HCI Usability: Brooke, J., *SUS: A Quick and Dirty Usability Scale*, Usability Evaluation in Industry, 1996.
6. Cognitive Workload Assessment: Hart & Staveland, *Development of NASA-TLX (Task Load Index)*, Advances in Psychology, 1988.

---

## 2. Overall Description

### 2.1 Product Perspective & Context
The system operates as an autonomous background service interfacing between a standard consumer RGB webcam and the host operating system's desktop environment:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           CLOSED-LOOP ADAPTIVE FEEDBACK PIPELINE                                 │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│           ┌─────────────────────────────────────────────────────────────┐                        │
│           │                   LAYER 1: PERCEPTION                       │                        │
│           │    (Webcam 30 FPS → FaceMesh/Iris + Hands + SolvePnP)       │                        │
│           └──────────────────────────────┬──────────────────────────────┘                        │
│                                          │ Feature Vector x                                      │
│                                          ▼                                                       │
│  ┌────────────────────────┐      ┌──────────────────────────────┐                                │
│  │ VERSIONED PROFILE STORE│─────►│      LAYER 3: DECISION       │                                │
│  │ (Profile v_k, ACI_t)   │      │ (3A Fusion → 3B Safety Reason│                                │
│  └───────────▲────────────┘      │  → 3C OS Context Dispatch)   │                                │
│              │                   └──────────────┬───────────────┘                                │
│              │ Profile v_k+1                    │ Executed Action Context                        │
│              │                                  ▼                                                │
│  ┌───────────┴────────────┐      ┌──────────────────────────────┐                                │
│  │    LAYER 6: LEARNING   │      │     LAYER 4: OBSERVATION     │                                │
│  │ (Micro SGD + Macro     │      │ (Temporal Windowing State    │                                │
│  │  Epoch State Machine)  │      │  Machine + 5 Sub-Detectors)  │                                │
│  └───────────▲────────────┘      └──────────────┬───────────────┘                                │
│              │ Validated Signal                 │ Observed Feedback Event                        │
│              │ (APPROVE)                        ▼                                                │
│              │                   ┌──────────────────────────────┐                                │
│              └───────────────────│     LAYER 5: ASSESSMENT      │                                │
│                                  │ (5A Metrics Engine +         │                                │
│                                  │  5B Decision Validator)      │                                │
│                                  └──────────────────────────────┘                                │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Summary of the Six Principled Architectural Layers
* **Layer 1 (Perception)**: *Observes* raw physical cues from 30 FPS webcam stream.
* **Layer 2 (Calibration)**: *Personalizes* user anatomy, sensor noise variances, and tempo baselines (`Profile v1`).
* **Layer 3 (Decision)**: *Decides* intent (Fusion 3A), reasons about safety (Safety 3B), and dispatches actions (OS 3C).
* **Layer 4 (Observation)**: *Evaluates* post-action user behavior via a temporal state machine and 5 asynchronous sub-detectors.
* **Layer 5 (Assessment)**: *Validates* updates via continuous health metrics (5A) and an intelligent gatekeeper (5B).
* **Layer 6 (Learning)**: *Learns* parameters via micro-SGD with 1D box simplex projection and epoch-driven macro adaptation.

### 2.3 User Classes and Characteristics
1. **General Desktop Users**: Require zero-configuration, seamless touchless navigation (scrolling, tab navigation, media control).
2. **Assistive & Motor-Impaired Users**: Require flexible spatial thresholds, tremor-tolerant smoothing, and personalized tempo baselines.
3. **Sterile Environment Operators (Surgeons / Cleanroom Technicians)**: Require zero false activations on critical commands via strict Tier-2 safety confirmation gates.
4. **HCI Researchers & Evaluators**: Require detailed telemetry logs, real-time ACI health gauges, Latin Square task managers, and automated session analytics reports.

### 2.4 Operating Environment & Hardware Constraints
* **Webcam**: Standard USB or integrated 720p/1080p RGB sensor at $\ge 30\text{ FPS}$.
* **Host Processor**: Standard multi-core x86_64 / ARM64 CPU (Intel Core i5 / AMD Ryzen 5 or equivalent).
* **System Memory**: $\ge 8\text{ GB}$ RAM (system memory footprint $\le 350\text{ MB}$).
* **Operating Systems**: Windows 10/11 (64-bit), Ubuntu Linux 22.04+, macOS 13+.
* **Hardware Acceleration**: GPU is NOT required; all perception, optimization, and evaluation pipelines must execute on CPU.

### 2.5 Design & Implementation Constraints
1. **End-to-End Latency Budget**: Maximum allowable frame processing cycle $\le 29.5\text{ ms}$ ($\ge 30\text{ FPS}$ sustained).
2. **On-Device Privacy Guarantee**: Video frames SHALL be processed strictly in volatile memory and NEVER written to disk or transmitted over networks.
3. **Non-Intrusive Supervision**: The system SHALL NOT interrupt the user with manual confirmation dialogues during normal interaction.

---

## 3. Specific System Features & Functional Requirements

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         FUNCTIONAL REQUIREMENTS MAPPING MATRIX                                   │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Layer 1: Perception & Feature Extraction ────────► FR-1.1 to FR-1.6                             │
│  Layer 2: Calibration & Profile Bootstrapping ────► FR-2.1 to FR-2.6                             │
│  Layer 3: Decoupled Decision & Safety Engine ─────► FR-3.1 to FR-3.7                             │
│  Layer 4: Implicit Feedback Observer ─────────────► FR-4.1 to FR-4.7                             │
│  Layer 5: Runtime Assessment Engine (RAE) ────────► FR-5.1 to FR-5.8                             │
│  Layer 6: Online Learning & Macro Adaptation ─────► FR-6.1 to FR-6.8                             │
│  Cross-Cutting: Global Uncertainty Propagation ──► FR-7.1 to FR-7.4                             │
│  Cross-Cutting: Explainability HUD & UI ──────────► FR-8.1 to FR-8.5                             │
│  Cross-Cutting: Diagnostics & Failure Governance ─► FR-9.1 to FR-9.5                             │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.1 Layer 1: Perception & Multimodal Feature Extraction

#### FR-1.1: Threaded Video Frame Ingestion
* **Description**: The system SHALL ingest webcam frames at native $1080\text{p} / 720\text{p}$ resolution at $30\text{ FPS}$ using a dedicated daemon capture thread with a lock-free double-buffered queue.
* **Acceptance Criteria**: Frame drop rate $< 0.5\%$; ingestion latency $< 5.0\text{ ms}$.
* **Verification**: Benchmark test `test_latency_benchmark.py`.

#### FR-1.2: Facial Mesh & Ocular Iris Landmark Extraction
* **Description**: The system SHALL extract 468 facial mesh landmarks and 10 refined iris landmarks (468–477) per frame via MediaPipe FaceMesh.
* **Mathematical Specification**:
  $$r_{\text{iris}, x} = \frac{x_{\text{iris}} - x_{\text{inner}}}{x_{\text{outer}} - x_{\text{inner}}}, \quad r_{\text{iris}, y} = \frac{y_{\text{iris}} - y_{\text{superior}}}{y_{\text{inferior}} - y_{\text{superior}}}$$
  Gaze confidence $s_{\text{gaze}} \in [0.0, 1.0]$ SHALL be computed using the calibrated affine transformation matrix $\mathbf{M}_{\text{gaze}}$ and gated by Eye Aspect Ratio ($\text{EAR} \ge 0.18$).
* **Acceptance Criteria**: Extraction completed in $< 12.0\text{ ms}$; blink events correctly suppress gaze confidence to $0.0$.
* **Verification**: Unit test `test_perception_gaze.py`.

#### FR-1.3: 3D Head Pose Orientation Estimation
* **Description**: The system SHALL compute continuous 3D head pose Euler angles (Yaw $\psi$, Pitch $\theta$, Roll $\phi$) by solving the Perspective-n-Point (SolvePnP) system using 6 canonical 3D facial feature points and camera intrinsic matrix $\mathbf{K}$.
* **Mathematical Specification**:
  $$s_{\text{head}} = \exp\left(-\frac{1}{2}(\mathbf{p} - \boldsymbol{\mu}_{\text{pose}})^T \boldsymbol{\Sigma}_{\text{pose}}^{-1} (\mathbf{p} - \boldsymbol{\mu}_{\text{pose}})\right) \in [0.0, 1.0]$$
* **Acceptance Criteria**: Pose estimation latency $< 2.0\text{ ms}$; angular resolution $< 0.5^\circ$.
* **Verification**: Unit test `test_head_pose_estimator.py`.

#### FR-1.4: 3D Hand Kinematics & Gesture Syntax Extraction
* **Description**: The system SHALL extract 21 3D hand landmarks via MediaPipe Hands, deriving normalized pinch aperture $d_{\text{pinch}} = \|\mathbf{p}_{\text{thumb\_tip}} - \mathbf{p}_{\text{index\_tip}}\|$, palm normal vector $\mathbf{n}_{\text{palm}}$, and wrist velocity vector $\mathbf{v}_{\text{wrist}}(t)$.
* **Mathematical Specification**: Hand confidence $s_{\text{hand}} \in [0.0, 1.0]$ SHALL be derived via sigmoid activation on gesture syntax match.
* **Acceptance Criteria**: Hand tracking latency $< 6.0\text{ ms}$; gesture detection accuracy $> 98\%$ on unobstructed hands.
* **Verification**: Unit test `test_hand_pose_extractor.py`.

#### FR-1.5: Adaptive Holt-Winters Spatial-Temporal Filter
* **Description**: The system SHALL apply an adaptive Holt-Winters double exponential smoothing filter to all extracted coordinates to eliminate dwell jitter while eliminating motion lag.
* **Mathematical Specification**:
  $$\hat{x}_t = \alpha_t x_t + (1 - \alpha_t)(\hat{x}_{t-1} + b_{t-1}), \quad b_t = \beta (\hat{x}_t - \hat{x}_{t-1}) + (1 - \beta) b_{t-1}$$
  $$\alpha_t = \text{clip}(\alpha_0 + \gamma \|\mathbf{v}_{\text{wrist}}(t)\|, \ 0.20, \ 0.85), \quad \beta = 0.15$$
* **Acceptance Criteria**: Stationary jitter $< 1.2\text{ px}$; dynamic tracking lag $< 15\text{ ms}$.
* **Verification**: Unit test `test_holt_winters_filter.py`.

#### FR-1.6: Perceptual Feature Vector Assembly
* **Description**: The system SHALL assemble the smoothed features into a normalized vector $\mathbf{x} = [s_{\text{gaze}}, s_{\text{head}}, s_{\text{hand}}]^T \in [0.0, 1.0]^3$ accompanied by sensor covariance matrix $\boldsymbol{\Sigma}_{\text{sensor}}$.
* **Acceptance Criteria**: Output vector emitted every frame cycle within $\le 20.5\text{ ms}$ of capture.
* **Verification**: Integration test `test_perception_pipeline.py`.

---

### 3.2 Layer 2: Calibration & Profile Bootstrapping Wizard

#### FR-2.1: 5-Phase Interactive Calibration Protocol
* **Description**: The system SHALL provide a structured 60–90 second interactive calibration wizard capturing 10–15 sample actions across 5 sequential phases:
  * *Phase A (0–10s)*: Hardware & Lighting Readiness Verification.
  * *Phase B (10–25s)*: Neutral Head Pose & Motion Envelope (3 samples).
  * *Phase C (25–50s)*: 5-Point Ocular Gaze Calibration Grid (5 samples).
  * *Phase D (50–75s)*: Hand Gesture Kinematics & Reaction Tempo (4 samples).
  * *Phase E (75–90s)*: Profile Synthesis & Initial Weight Generation (`Profile v1`).
* **Acceptance Criteria**: Total wizard duration $\le 90\text{ s}$; automated profile synthesis $< 50\text{ ms}$.
* **Verification**: Interactive UI verification test `test_calibration_wizard.py`.

#### FR-2.2: 95% Confidence Neutral Posture Ellipsoid
* **Description**: The system SHALL compute the mean vector $\boldsymbol{\mu}_{\text{pose}} \in \mathbb{R}^3$ and covariance matrix $\boldsymbol{\Sigma}_{\text{pose}} \in \mathbb{R}^{3 \times 3}$ from Phase B samples, defining the neutral resting boundary:
  $$\mathcal{E}_{\text{head}} = \left\{ \mathbf{p} \in \mathbb{R}^3 \mid (\mathbf{p} - \boldsymbol{\mu}_{\text{pose}})^T \boldsymbol{\Sigma}_{\text{pose}}^{-1} (\mathbf{p} - \boldsymbol{\mu}_{\text{pose}}) \le \chi^2_3(0.95) \approx 7.815 \right\}$$
* **Acceptance Criteria**: Positive definite covariance matrix; invertible via Cholesky decomposition.
* **Verification**: Mathematical unit test `test_calibration_geometry.py`.

#### FR-2.3: 5-Point Ocular Gaze Affine Mapping
* **Description**: The system SHALL compute a $2 \times 3$ affine perspective transformation matrix $\mathbf{M}_{\text{gaze}}$ mapping pupil coordinate ratios $(r_x, r_y)$ to screen coordinates $(u, v)$ using Phase C grid samples.
* **Acceptance Criteria**: Calibration residual root-mean-square error $\text{RMSE} \le 45\text{ px}$ on standard $1080\text{p}$ display.
* **Verification**: Unit test `test_gaze_affine_fitting.py`.

#### FR-2.4: Personal Reaction Tempo Baseline
* **Description**: The system SHALL measure individual visual-motor reaction latency across Phase D gesture triggers, computing the user-specific exponential decay constant:
  $$\tau_{\text{user}} = \text{clip}\left(0.60 \cdot \frac{T_{\text{user\_tempo}}}{0.80\text{s}}, \ 0.35\text{s}, \ 0.95\text{s}\right)$$
* **Acceptance Criteria**: Calibrated $\tau_{\text{user}}$ stored in initial profile; falls strictly within $[0.35\text{s}, 0.95\text{s}]$.
* **Verification**: Unit test `test_tempo_calibration.py`.

#### FR-2.5: Variance-Informed Initial Weight Synthesis
* **Description**: The system SHALL initialize per-action modality weights inversely proportional to empirical landmark variances observed during calibration:
  $$\tilde{w}_i^{(0)} = \frac{1 / \sigma_i^2}{\sum_{j \in \{\text{gaze}, \text{head}, \text{hand}\}} 1 / \sigma_j^2} \implies \mathbf{w}_a^{(0)} = \text{BoxSimplexProjection}(\tilde{\mathbf{w}}^{(0)}, \mathbf{l}=0.05\cdot\mathbf{1}, \mathbf{u}=0.85\cdot\mathbf{1})$$
* **Acceptance Criteria**: Initial weights satisfy $\sum w_i = 1.0$ and $w_i \in [0.05, 0.85]$. Users with noisy gaze (e.g., glasses) receive lower initial gaze weight ($w_{\text{gaze}} \approx 0.20$) compensated by hand ($w_{\text{hand}} \approx 0.55$).
* **Verification**: Mathematical unit test `test_variance_weight_init.py`.

#### FR-2.6: Initial Profile Serialization (`Profile v1`)
* **Description**: The system SHALL compile all calibrated parameters into an immutable `ProfileSnapshot` record (version 1) and persist it to local JSON/SQLite storage.
* **Acceptance Criteria**: Profile schema validates against `ProfileSnapshot` dataclass; file write $< 20\text{ ms}$.
* **Verification**: Storage test `test_profile_snapshot_store.py`.

---

### 3.3 Layer 3: Decoupled Decision, Safety Reasoning & Execution

```
┌────────────────────────────────────────────────────────────────────────┐
│                        LAYER 3 INTERNAL SUB-STAGES                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  [Feature Vector x]                                                    │
│        │                                                               │
│        ▼                                                               │
│  ┌──────────────────────────────────────────────┐                      │
│  │ Stage 3A: Confidence Fusion & Intent Evaluator│                      │
│  │ • S_a(x) = w_gaze·s_gaze + w_head·s_head +   │                      │
│  │            w_hand·s_hand                     │                      │
│  │ • Evaluates base condition: S_a(x) ≥ θ_a     │                      │
│  └──────────────────────┬───────────────────────┘                      │
│                         │ (Intent Candidate)                           │
│                         ▼                                              │
│  ┌──────────────────────────────────────────────┐                      │
│  │ Stage 3B: Post-Decision Safety Reasoning     │                      │
│  │ • Determines Action Tier (Tier 1 vs Tier 2)  │                      │
│  │ • Tier 2 Gate: S_a ≥ min(0.95, max(θ_a+0.15, │                      │
│  │                           μ_S + 1.5σ_S))     │                      │
│  │ • Manages 600ms HUD visual dwell confirmation│                      │
│  │ • Arms 3.0s Grace-Period Undo Hook Stack     │                      │
│  └──────────────────────┬───────────────────────┘                      │
│                         │ (Approved for Execution)                     │
│                         ▼                                              │
│  ┌──────────────────────────────────────────────┐                      │
│  │ Stage 3C: OS Execution & Context Dispatch    │                      │
│  │ • Executes native OS API (pyautogui / win32) │                      │
│  │ • Pushes immutable ActionContext to Layer 4  │                      │
│  └──────────────────────────────────────────────┘                      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### FR-3.1: Stage 3A Weighted Confidence Late Fusion
* **Description**: The system SHALL compute the scalar fused confidence score $S_a(\mathbf{x}) = \mathbf{w}_a^T \mathbf{x} = \sum_{i=1}^3 w_{a, i} s_i$ for each action candidate $a \in \mathcal{A}$.
* **Acceptance Criteria**: Mathematical evaluation latency $< 0.1\text{ ms}$; fused score bounded strictly in $[0.0, 1.0]$.
* **Verification**: Unit test `test_confidence_fuser.py`.

#### FR-3.2: Stage 3A Intent Candidate Trigger
* **Description**: The system SHALL emit an `IntentCandidate(action_id, a, S_a, \theta_a)` if and only if $S_a(\mathbf{x}) \ge \theta_a$ and no refractory lockout is active.
* **Acceptance Criteria**: Intent candidate passed directly to Stage 3B within the same frame cycle.
* **Verification**: Unit test `test_confidence_fuser.py`.

#### FR-3.3: Stage 3B Action Tier Classification
* **Description**: The system SHALL classify every action into one of two safety tiers:
  * *Tier 1 (Safe / Reversible / Continuous)*: Scrolling, tab switching, media playback, cursor motion.
  * *Tier 2 (Destructive / State-Altering)*: Window closure, application launch, system sleep, file deletion.
* **Acceptance Criteria**: Tier classification lookup latency $< 0.05\text{ ms}$.
* **Verification**: Unit test `test_safety_gatekeeper.py`.

#### FR-3.4: Stage 3B Tier-1 Instant Execution Path
* **Description**: For Tier-1 actions, Stage 3B SHALL forward the intent candidate immediately to Stage 3C without delay.
* **Acceptance Criteria**: Forwarding latency $< 0.1\text{ ms}$.
* **Verification**: Integration test `test_layer3_decoupling.py`.

#### FR-3.5: Stage 3B User-Relative Tier-2 Safety Dwell Gate
* **Description**: For Tier-2 actions, Stage 3B SHALL enforce a dynamic safety threshold:
  $$\theta_{\text{tier2}, a} = \min\left(0.95, \ \max(\theta_a + 0.15, \ \mu_{S, a} + 1.5\sigma_{S, a})\right)$$
  and mandate a $600\text{ ms}$ visual dwell confirmation on the HUD overlay before releasing the command.
* **Acceptance Criteria**: If confidence drops below $\theta_{\text{tier2}, a}$ before $600\text{ ms}$, the action is aborted without OS execution.
* **Verification**: Unit test `test_safety_gatekeeper.py`.

#### FR-3.6: Stage 3B Grace-Period Undo Hook Arming
* **Description**: Upon approving any Tier-2 action, Stage 3B SHALL arm a $3.0\text{ s}$ OS-level undo interceptor enabling instantaneous reversal via keyboard or gesture.
* **Acceptance Criteria**: Undo interceptor active for exactly $3.0\text{ s}$ post-dispatch.
* **Verification**: Unit test `test_safety_gatekeeper.py`.

#### FR-3.7: Stage 3C Native OS Action Execution & Context Dispatch
* **Description**: Stage 3C SHALL execute the command via native OS API (`PyAutoGUI` / `win32api`) and simultaneously push an immutable `ActionContext` record to the Layer 4 observation queue.
* **Acceptance Criteria**: OS execution latency $< 2.0\text{ ms}$; `ActionContext` successfully enqueued.
* **Verification**: Integration test `test_action_dispatcher.py`.

---

### 3.4 Layer 4: Implicit Feedback Observer & Temporal State Machine

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         IMPLICIT FEEDBACK TEMPORAL STATE MACHINE                                 │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [t0: Action Executed & Logged to ActionContextQueue]                                            │
│         │                                                                                        │
│         ▼                                                                                        │
│  ┌──────────────────────────────────────────────────────────┐                                    │
│  │ Window 1: REFRACTORY WINDOW [t0, t0 + 200ms]             │ ──► Events Ignored (Motor Delay)   │
│  └──────────────────────────┬───────────────────────────────┘                                    │
│                             ▼                                                                    │
│  ┌──────────────────────────────────────────────────────────┐                                    │
│  │ Window 2: CORRECTION WINDOW [t0 + 200ms, t0 + 1.8s]      │                                    │
│  │                                                          │                                    │
│  │  • Sub-Detector 1: Global OS Undo (Ctrl+Z, Alt+Left)     │ ──► Emits IMPLICIT_NEG             │
│  │  • Sub-Detector 2: Directional Oppositional Reversal     │     with Continuous Confidence:    │
│  │  • Sub-Detector 3: Rapid Duplicate Gesture Retries       │     c_fb = exp(-(Δt - 0.2)/τ_user) │
│  │  • Sub-Detector 4: Immediate App/Tab Dismissal           │                                    │
│  │  • Sub-Detector 5: Manual Physical Mouse/Key Override    │                                    │
│  └──────────────────────────┬───────────────────────────────┘                                    │
│                             ▼ (No Negative Event Detected)                                       │
│  ┌──────────────────────────────────────────────────────────┐                                    │
│  │ Window 3: STABILITY EXPIRATION [t > t0 + 1.8s]           │ ──► Emits IMPLICIT_POS             │
│  │           (Action Persisted Without Reversal)            │     with Confidence c_fb = 1.0     │
│  └──────────────────────────┬───────────────────────────────┘                                    │
│                             ▼                                                                    │
│  [Action Context Resolved & Pruned from Queue]                                                   │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### FR-4.1: Asynchronous Action Context Ring Buffer
* **Description**: Layer 4 SHALL maintain a thread-safe, lock-free ring buffer holding up to 50 active `ActionContext` records awaiting temporal resolution.
* **Acceptance Criteria**: Thread-safe push and pop operations with zero lock contention overhead ($< 0.1\text{ ms}$).
* **Verification**: Unit test `test_feedback_state_machine.py`.

#### FR-4.2: Window 1 Refractory Lockout Enforcement
* **Description**: The system SHALL ignore all user inputs and potential feedback events occurring within $\Delta t \in [0.0\text{s}, 0.2\text{s}]$ post-action ($t_0$) to account for human neuromuscular visual-motor reaction time limits.
* **Acceptance Criteria**: Zero feedback events emitted during $[t_0, t_0 + 200\text{ms}]$.
* **Verification**: Unit test `test_feedback_state_machine.py`.

#### FR-4.3: Window 2 Negative Sub-Detector 1 (Global OS Undo Hook)
* **Description**: The system SHALL intercept `Ctrl+Z`, `Alt+Left`, and `Ctrl+Shift+T` keystrokes targeted at the active window process ID within $\Delta t \in [0.2\text{s}, 1.8\text{s}]$, emitting `FeedbackEvent(outcome = -1, failure = FALSE_ACTIVATION)`.
* **Acceptance Criteria**: Key combination detected with attribution to correct action within $< 5\text{ ms}$.
* **Verification**: Unit test `test_negative_sub_detectors.py`.

#### FR-4.4: Window 2 Negative Sub-Detector 2 (Directional Oppositional Reversal)
* **Description**: The system SHALL detect immediate inverse continuous actions (e.g. Scroll Down followed by Scroll Up within $1.0\text{ s}$), emitting `FeedbackEvent(outcome = -1, failure = WRONG_TARGET)`.
* **Acceptance Criteria**: Directional reversal identified with $100\%$ precision on continuous commands.
* **Verification**: Unit test `test_negative_sub_detectors.py`.

#### FR-4.5: Window 2 Negative Sub-Detector 3 (Rapid Duplicate Retries)
* **Description**: The system SHALL detect repeated gesture attempts ($\ge 2$ triggers within $1.2\text{ s}$ without system action dispatch), emitting `FeedbackEvent(outcome = -1, failure = FALSE_REJECTION)`.
* **Acceptance Criteria**: Rapid retries trigger negative feedback indicating false rejection.
* **Verification**: Unit test `test_negative_sub_detectors.py`.

#### FR-4.6: Window 2 Negative Sub-Detectors 4 & 5 (Dismissals & Overrides)
* **Description**: The system SHALL detect immediate window/tab dismissals within $1.5\text{ s}$ (`Alt+F4`/`Ctrl+W`) and sudden physical mouse/keyboard interventions ($>800\text{ px/s}$), emitting corresponding negative feedback events.
* **Acceptance Criteria**: Physical mouse override interrupts gesture control within $< 10\text{ ms}$.
* **Verification**: Unit test `test_negative_sub_detectors.py`.

#### FR-4.7: Window 3 Stability Expiration & Continuous Confidence Decay
* **Description**: If no negative feedback is detected within $1.8\text{ s}$ post-dispatch, Layer 4 SHALL emit `FeedbackEvent(outcome = +1, c_fb = 1.0, failure = NONE)`. For negative feedback during Window 2, continuous confidence SHALL decay exponentially:
  $$c_{fb}(\Delta t) = \exp\left(-\frac{\Delta t - 0.20}{\tau_{\text{user}}}\right) \in [0.05, 1.0]$$
* **Acceptance Criteria**: Feedback event emitted to Layer 5 immediately upon resolution.
* **Verification**: Unit test `test_feedback_state_machine.py`.

---

### 3.5 Layer 5: Runtime Assessment Engine (RAE)

```
┌────────────────────────────────────────────────────────────────────────┐
│               LAYER 5: RUNTIME ASSESSMENT ENGINE (RAE)                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ ENGINE 5A: RUNTIME METRICS ENGINE                                │  │
│  │ • Computes EWMA Adaptation Gain (AG_t, α=0.10)                   │  │
│  │ • Computes Sliding Learning Velocity (LV_t, W=20)                │  │
│  │ • Computes Weight Stability Index (WSI_t)                        │  │
│  │ • Computes Adaptation Confidence Index (ACI_t)                   │  │
│  │ • Computes Expected Calibration Error (ECE_t)                    │  │
│  │ • Computes Recovery Rate (RR) & Drift Recovery Time (DRT)        │  │
│  └──────────────────────────────────┬───────────────────────────────┘  │
│                                     │ Live Health Metrics Snapshot      │
│                                     ▼                                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ ENGINE 5B: DECISION & LEARNING VALIDATOR (GATEKEEPER)            │  │
│  │ • Validates Sample Count Floor (k ≥ 3)                           │  │
│  │ • Validates Continuous Feedback Confidence (c_fb ≥ 0.40)         │  │
│  │ • Enforces Macro Drift Lockout (Blocks updates if S_m ≥ 2.89)    │  │
│  │ • Resolves Sub-Detector Contradictions                           │  │
│  │ • Evaluates Environmental Sensor SNR (Lux > 20, GazeVar < 0.25)  │  │
│  │ • Emits: APPROVE vs REJECT Verdict + Validated Signal            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### FR-5.1: Engine 5A Continuous Metric Formulations
* **Description**: Engine 5A SHALL compute the full suite of categorized health metrics continuously:
  1. **EWMA Adaptation Gain**: $AG_t = \alpha (\text{Acc}_t - \text{Base}) + (1-\alpha) AG_{t-1}, \quad \alpha = 0.10$
  2. **Sliding Learning Velocity**: $LV_t = \frac{\text{Error}(t-W) - \text{Error}(t)}{W}, \quad W = 20$
  3. **Weight Stability Index**: $WSI_t = \frac{1}{d} \sum_{i=1}^d \sqrt{\frac{1}{K}\sum_{k=0}^{K-1} (w_{i, t-k} - \bar{w}_i)^2}, \quad K = 30, d = 3$
  4. **Adaptation Confidence Index**: $ACI_t = \text{clip}\left(0.30 \frac{\min(N_a, 20)}{20} + 0.30 (1 - \frac{WSI_t}{0.10}) + 0.25 \frac{AG_t}{0.20} - 0.15 ECE_t, \ 0, \ 1\right)$
  5. **Expected Calibration Error**: $ECE_t = \sum_{b=1}^{10} \frac{|B_b|}{N} \left| \text{Acc}(B_b) - \text{Conf}(B_b) \right|$
  6. **Recovery Rate**: $RR = \frac{\sum \mathbb{I}(\text{Outcome}_{t+1} = \text{Success} \mid \text{Outcome}_t = \text{Error})}{\sum \mathbb{I}(\text{Outcome}_t = \text{Error})}$
  7. **Drift Recovery Time**: $DRT = t_{\text{stabilized}} - t_{\text{alarm}}$ (Time from Wald SPRT $S_m \ge 2.89$ to reset $S_m \le -2.25$).
* **Acceptance Criteria**: Metrics snapshot computed in $< 1.5\text{ ms}$.
* **Verification**: Unit test `test_runtime_metrics_engine.py`.

#### FR-5.2: Engine 5B Gatekeeper Rule 1 (Sample Count Floor)
* **Description**: Engine 5B SHALL reject any update if the total historical sample count for that action $k < 3$, preventing single-trial overreactions during warmup.
* **Acceptance Criteria**: Emits `GatekeeperVerdict(status="REJECT", reason="SAMPLE_COUNT_BELOW_WARMUP_FLOOR")`.
* **Verification**: Unit test `test_learning_gatekeeper.py`.

#### FR-5.3: Engine 5B Gatekeeper Rule 2 (Feedback Confidence Floor)
* **Description**: Engine 5B SHALL reject any update where continuous feedback confidence $c_{fb} < 0.40$ (sluggish or ambiguous corrections).
* **Acceptance Criteria**: Emits `GatekeeperVerdict(status="REJECT", reason="FEEDBACK_CONFIDENCE_BELOW_THRESHOLD")`.
* **Verification**: Unit test `test_learning_gatekeeper.py`.

#### FR-5.4: Engine 5B Gatekeeper Rule 3 (Neutral State Suppression)
* **Description**: Engine 5B SHALL reject uninformative or ambiguous interaction states ($y = 0.0$).
* **Acceptance Criteria**: Emits `GatekeeperVerdict(status="REJECT", reason="NEUTRAL_OR_AMBIGUOUS_EVENT")`.
* **Verification**: Unit test `test_learning_gatekeeper.py`.

#### FR-5.5: Engine 5B Gatekeeper Rule 4 (Macro Drift Lockout)
* **Description**: When Wald SPRT indicates active drift ($S_m \ge 2.89$), Engine 5B SHALL lock out all micro-updates to prevent fitting parameters on corrupted drift states until recalibration completes.
* **Acceptance Criteria**: Emits `GatekeeperVerdict(status="REJECT", reason="MACRO_DRIFT_ACTIVE_AWAITING_RECALIBRATION")`.
* **Verification**: Unit test `test_learning_gatekeeper.py`.

#### FR-5.6: Engine 5B Gatekeeper Rule 5 (Sub-Detector Contradiction Resolution)
* **Description**: Engine 5B SHALL reject updates if multiple sub-detectors report conflicting failure modes for the same interaction.
* **Acceptance Criteria**: Emits `GatekeeperVerdict(status="REJECT", reason="CONTRADICTORY_SUB_DETECTOR_SIGNALS")`.
* **Verification**: Unit test `test_learning_gatekeeper.py`.

#### FR-5.7: Engine 5B Gatekeeper Rule 6 (Environmental Noise Check)
* **Description**: Engine 5B SHALL reject updates if ambient lighting $< 20\text{ lux}$ or gaze landmark tracking variance $> 0.25$.
* **Acceptance Criteria**: Emits `GatekeeperVerdict(status="REJECT", reason="ENVIRONMENTAL_NOISE_EXCEEDS_TOLERANCE")`.
* **Verification**: Unit test `test_learning_gatekeeper.py`.

#### FR-5.8: Automated Session Report Generator
* **Description**: Layer 5 SHALL generate an automated markdown session report at session conclusion containing executive summary KPIs, Significant Interaction Events table, and 5 matplotlib convergence plots.
* **Acceptance Criteria**: Report generated and saved to `reports/session_<id>.md` in $< 500\text{ ms}$.
* **Verification**: Integration test `test_session_report_generator.py`.

---

### 3.6 Layer 6: Online Learning & Dual-Scale Optimization

#### FR-6.1: Micro-Adaptation Ambiguity-Gated SGD
* **Description**: Upon receiving an `APPROVE` verdict, Layer 6 SHALL execute decoupled parameter updates:
  $$\tilde{\mathbf{w}}_a^{(t+1)} = \mathbf{w}_a^{(t)} + \eta_w(t) \cdot g_{\text{weight}}(S_a, \theta_a) \cdot c_{fb} \cdot e_a \cdot \mathbf{x}$$
  $$\theta_a^{(t+1)} = \text{clip}\left(\theta_a^{(t)} - \eta_\theta(t) \cdot c_{fb} \cdot e_a, \ 0.35, \ 0.85\right)$$
  where error residual $e_a = y_{\text{target}} - S_a(\mathbf{x})$ and ambiguity gate:
  $$g_{\text{weight}}(S_a, \theta_a) = \frac{1}{1 + \exp(-40 (|S_a - \theta_a| - 0.05))}$$
* **Acceptance Criteria**: Update execution completed in $< 0.2\text{ ms}$.
* **Verification**: Unit test `test_micro_sgd_optimizer.py`.

#### FR-6.2: Exact 1D Bisection Box-Constrained Simplex Projection
* **Description**: Layer 6 SHALL project the updated weights onto the box-constrained unit simplex ($\sum_{i=1}^3 w_{a, i} = 1.0, w_{a, i} \in [0.05, 0.85]$) by solving the 1D dual root equation:
  $$f(\mu) = \sum_{i=1}^3 \text{clip}(\tilde{w}_{a, i} - \mu, \ 0.05, \ 0.85) - 1.0 = 0$$
  using bisection root-finding with initial bracket $\mu \in [\min(\tilde{\mathbf{w}}) - 0.85, \max(\tilde{\mathbf{w}}) - 0.05]$.
* **Acceptance Criteria**: Solves to tolerance $|f(\mu^*)| \le 10^{-6}$ within $\le 15$ bisection iterations ($< 0.3\text{ ms}$).
* **Verification**: Unit test `test_simplex_projection.py`.

#### FR-6.3: Macro-Adaptation Epoch Trigger
* **Description**: Layer 6 SHALL trigger macro-adaptation evaluation every $N = 30\text{--}50$ interactions or upon session termination.
* **Acceptance Criteria**: Evaluates running Gaussian score distributions ($\mu_S, \sigma_S$), ECE across 10 bins, and Wald SPRT score.
* **Verification**: Unit test `test_macro_adaptation.py`.

#### FR-6.4: Macro Policy `MERGE` Execution
* **Description**: If $AG_t > 0.05 \land WSI_t < 0.02 \land ECE_t < 0.10$, the system SHALL execute `MERGE`, permanently committing micro-weight updates into the baseline profile.
* **Acceptance Criteria**: Commits weights; updates baseline distributions.
* **Verification**: Unit test `test_macro_adaptation.py`.

#### FR-6.5: Macro Policy `FREEZE` Execution
* **Description**: If $ACI_t \ge 0.80 \land WSI_t < 0.01$, the system SHALL execute `FREEZE`, locking weights into a stable baseline and reducing base learning rate $\eta \to \eta_{\min}$.
* **Acceptance Criteria**: Learning rate dampened; HUD displays `STABLE` state badge.
* **Verification**: Unit test `test_macro_adaptation.py`.

#### FR-6.6: Macro Policy `DISCARD` Execution
* **Description**: If $ECE_t$ spikes by $> 0.15$ or $AG_t < -0.05$, the system SHALL execute `DISCARD`, rolling back corrupt parameter drift to the previous snapshot.
* **Acceptance Criteria**: Restores parameters from previous versioned snapshot within $< 5\text{ ms}$.
* **Verification**: Unit test `test_macro_adaptation.py`.

#### FR-6.7: Macro Policy `RECALIBRATE` & Hierarchical Wald SPRT
* **Description**: The system SHALL maintain a cumulative Wald SPRT log-likelihood score:
  $$S_m = \sum_{i=1}^m \ln \frac{P(e_i \mid H_1: \text{error\_rate} = 0.20)}{P(e_i \mid H_0: \text{error\_rate} = 0.05)}$$
  If $S_m \ge 2.89$ ($\alpha=\beta=0.05$), the system SHALL lock micro-updates and prompt the user for a $30\text{ s}$ micro-recalibration.
* **Acceptance Criteria**: Wald SPRT triggers alarm at $S_m \ge 2.89$; resets to $0.0$ on recalibration completion.
* **Verification**: Unit test `test_wald_sprt_detector.py`.

#### FR-6.8: Profile Snapshot Serialization
* **Description**: Upon completing a macro adaptation cycle, Layer 6 SHALL persist an immutable `ProfileSnapshot` record (version $k+1$) to local storage.
* **Acceptance Criteria**: JSON/SQLite record written and verified with monotonic version increment ($v_k \to v_{k+1}$).
* **Verification**: Storage test `test_profile_snapshot_store.py`.

---

### 3.7 Cross-Cutting: Global Uncertainty Propagation Pipeline

#### FR-7.1: Perceptual Sensor Covariance Propagation
* **Description**: The system SHALL compute propagated perceptual variance $\sigma_{\text{perceptual}}^2 = \mathbf{w}_a^T \boldsymbol{\Sigma}_{\text{sensor}} \mathbf{w}_a$ from raw landmark noise.
* **Acceptance Criteria**: Bounded non-negative scalar computed per frame in $< 0.05\text{ ms}$.
* **Verification**: Unit test `test_uncertainty_propagation.py`.

#### FR-7.2: Decision Margin Ambiguity Weighting
* **Description**: The system SHALL compute the epistemic distance $\Delta_{\text{decision}} = |S_a(\mathbf{x}) - \theta_a|$ and evaluate the sigmoid ambiguity weight $g_{\text{weight}}(\Delta_{\text{decision}})$.
* **Acceptance Criteria**: Suppresses updates near the decision boundary ($\Delta_{\text{decision}} < 0.05$).
* **Verification**: Unit test `test_uncertainty_propagation.py`.

#### FR-7.3: Global Update Confidence Synthesis
* **Description**: The system SHALL compute unified update confidence:
  $$C_{\text{update}} = \left(\frac{1}{1 + \sigma_{\text{perceptual}}}\right) \cdot g_{\text{weight}}(\Delta_{\text{decision}}) \cdot c_{fb}(\Delta t) \cdot (1 - \text{ECE}_t) \cdot ACI_t \in [0.0, 1.0]$$
* **Acceptance Criteria**: Synthesis completed in $< 0.1\text{ ms}$.
* **Verification**: Unit test `test_uncertainty_propagation.py`.

#### FR-7.4: Dynamic Effective Learning Rate Modulation
* **Description**: The system SHALL dynamically modulate the effective SGD step size:
  $$\eta_{\text{eff}}(t) = \eta_0 \cdot C_{\text{update}}$$
* **Acceptance Criteria**: Step size scales continuously with global confidence; drops to $\approx 0$ on high uncertainty.
* **Verification**: Unit test `test_uncertainty_propagation.py`.

---

### 3.8 Cross-Cutting: User Interface & Explainability Subsystems

#### FR-8.1: State-Aware Semi-Transparent HUD Overlay
* **Description**: The system SHALL render a low-overhead ($< 5\text{ MB}$ RAM, $< 1\text{ ms}$ render time) semi-transparent overlay in the screen corner showing real-time per-modality confidence bars ($s_{\text{gaze}}, s_{\text{head}}, s_{\text{hand}}$) and fused score $S_a$.
* **Acceptance Criteria**: HUD render overhead $< 2\%$ CPU; click-through transparent.
* **Verification**: UI test `test_explainability_hud.py`.

#### FR-8.2: Dynamic Health State Badge Rendering
* **Description**: The HUD SHALL display the active system health state badge:
  * `LEARNING`: Baseline initialization ($AG_t \le 0.05$).
  * `IMPROVING`: Active adaptation gain ($AG_t > 0.05 \land WSI_t \ge 0.02$).
  * `STABLE`: Converged weights ($ACI_t \ge 0.75 \land WSI_t < 0.02$).
  * `DRIFTING`: Macro drift warning ($S_m \ge 2.0$).
  * `RECOVERING`: Post-recalibration stabilization ($S_m \ge 2.89 \to \text{reset}$).
* **Acceptance Criteria**: Badge updates instantaneously upon metric transition.
* **Verification**: UI test `test_explainability_hud.py`.

#### FR-8.3: Tier-2 Visual Dwell Confirmation Ring
* **Description**: For Tier-2 destructive actions, the HUD SHALL render a circular $600\text{ ms}$ animated progress ring confirming intentional trigger before execution.
* **Acceptance Criteria**: Smooth $60\text{ FPS}$ circular dwell animation.
* **Verification**: UI test `test_explainability_hud.py`.

#### FR-8.4: Research Dashboard GUI
* **Description**: The system SHALL provide an interactive research dashboard rendering live ACI gauge, SPRT trajectory plot, weight evolution curves, and Latin Square study configuration panel.
* **Acceptance Criteria**: Dashboard launches in separate thread without dropping perception pipeline frames.
* **Verification**: UI test `test_research_dashboard.py`.

---

### 3.9 Cross-Cutting: Diagnostics, Failure Governance & Schemas

#### FR-9.1: Enriched `ActionContext` Schema
* **Description**: Every executed action SHALL be logged with the comprehensive `ActionContext` schema:
```python
@dataclass
class ActionContext:
    action_id: str
    action_type: str
    dispatched_at_ms: float
    feature_vector: np.ndarray
    modality_weights: np.ndarray
    activation_threshold: float
    fused_score: float
    decision_path: str                  # "TIER1_DIRECT" | "TIER2_DWELL_CONFIRMED"
    target_process_id: int
    target_executable_name: str         # "chrome.exe", "code.exe"
    target_window_title: str
    target_app_category: str            # "EDITOR", "BROWSER", "MEDIA_PLAYER", "SYSTEM"
    cursor_position_xy: tuple
    ambient_illuminance_lux: float
    user_distance_est_mm: float
    tracking_snr_gaze: float
    tracking_snr_hands: float
    profile_version_id: int
    active_aci_score: float
    evaluation_status: str              # "PENDING" | "RESOLVED_POS" | "RESOLVED_NEG"
```
* **Acceptance Criteria**: Full schema serialized without missing fields.
* **Verification**: Schema test `test_enriched_action_context.py`.

#### FR-9.2: Four-Stage Failure Governance Subsystem
* **Description**: Diagnosed failures SHALL be processed through the 4-stage governance pipeline:
  1. *Detection*: Intercepted via 5 negative sub-detectors.
  2. *Classification*: Mapped to 7 canonical failure modes (`FALSE_ACTIVATION`, `FALSE_REJECTION`, `WRONG_TARGET`, `LOW_CONFIDENCE`, `DELAYED_RESPONSE`, `USER_OVERRIDE`, `ENVIRONMENTAL_DRIFT`).
  3. *Severity Scoring*: Rated Level 1 (Benign scroll over-reach) to Level 5 (Critical destructive misfire).
  4. *Corrective Policy*:
     - `FALSE_ACTIVATION`: $\theta_a \leftarrow \theta_a + 0.03$, penalize dominant modality weight.
     - `FALSE_REJECTION`: $\theta_a \leftarrow \theta_a - 0.03$, boost responsive modality weight.
     - `WRONG_TARGET`: Increase directional disambiguation dwell timer by $150\text{ ms}$.
     - `ENVIRONMENTAL_DRIFT`: Lock micro-updates; trigger Wald SPRT recalibration.
* **Acceptance Criteria**: Policy applied within $< 1.0\text{ ms}$ of diagnosis.
* **Verification**: Unit test `test_failure_governance.py`.

---

## 4. External Interface Requirements

### 4.1 User Interfaces
* **Semi-Transparent HUD Overlay**: Corner-anchored, click-through, 60 FPS PyQt6/OpenGL window showing modality confidence, fused score, active health badge, and Tier-2 dwell confirmation rings.
* **Interactive Calibration Wizard**: Fullscreen 5-phase onboarding UI guiding the user through gaze target fixation, neutral posture holds, and sample gesture pinches.
* **Research Dashboard**: Multi-tab Qt application displaying real-time metrics, telemetry event logs, SPRT graphs, and Latin Square pilot study controls.

### 4.2 Hardware Interfaces
* **Webcam Video Stream**: Standard USB 2.0/3.0 or integrated CMOS sensor capturing 8-bit RGB frames ($1280 \times 720$ or $1920 \times 1080$ @ $30\text{ FPS}$).

### 4.3 Software Interfaces
* **OS Keystroke & Mouse Event Injection**: `PyAutoGUI` / `win32api` / `Xlib` for native OS event generation.
* **OS Keystroke & Input Hooking**: Low-level Windows Hook API (`SetWindowsHookEx` / `pynput`) for asynchronous undo (`Ctrl+Z`) and physical override detection.
* **Computer Vision Framework**: MediaPipe Python SDK (v0.10+) and OpenCV (v4.8+).
* **Storage Engine**: SQLite 3 database and JSON flat-file storage for versioned `ProfileSnapshot` records.

### 4.4 Communications Interfaces
* **Inter-Thread Message Queues**: Lock-free double-buffered queues and Python standard library `queue.Queue` with timeout bounds ($\le 2\text{ ms}$) for zero-overhead inter-thread communication.

---

## 5. Non-Functional Requirements & Quality Attributes

### 5.1 Performance Requirements
* **NFR-PERF-1 (Frame Cycle Budget)**: Total end-to-end perception, decision, observation, and optimization latency SHALL NOT exceed $29.5\text{ ms}$ per frame, sustaining $\ge 30\text{ FPS}$ on standard CPU hardware.
* **NFR-PERF-2 (Memory Footprint)**: Total resident set memory consumption SHALL NOT exceed $350\text{ MB}$ under steady-state operation.
* **NFR-PERF-3 (CPU Utilization)**: Average CPU utilization SHALL NOT exceed $35\%$ across a standard 4-core processor (Intel Core i5 / AMD Ryzen 5).
* **NFR-PERF-4 (Storage Footprint)**: Each serialized `ProfileSnapshot` SHALL NOT exceed $15\text{ KB}$; total session telemetry SHALL NOT exceed $5\text{ MB/hour}$.

### 5.2 Safety & Reliability Requirements
* **NFR-SAFE-1 (Fail-Safe Defaults)**: In the event of sensor occlusion or landmark tracking loss ($\text{SNR} < 0.10$), the system SHALL gracefully degrade to zero-confidence state without emitting spurious actions.
* **NFR-SAFE-2 (Tier-2 Destructive Isolation)**: Destructive OS actions SHALL NEVER execute without completing the $600\text{ ms}$ visual dwell confirmation gate.
* **NFR-SAFE-3 (Undo Recovery Stack)**: All executed actions SHALL remain interceptable and reversible via the $3.0\text{ s}$ grace-period undo stack.

### 5.3 Security & Privacy Requirements
* **NFR-PRIV-1 (Zero Frame Persistence)**: Video stream frames SHALL exist exclusively in volatile RAM and SHALL NEVER be saved to persistent storage or transmitted over network sockets.
* **NFR-PRIV-2 (Local On-Device Execution)**: All feature extraction, decision fusion, assessment, and optimization algorithms SHALL execute $100\%$ locally on-device with zero cloud dependencies.
* **NFR-PRIV-3 (Anonymized Telemetry)**: Telemetry logs and profile records SHALL use anonymized UUIDs without recording identifiable biometric imagery.

### 5.4 Maintainability & Modularity
* **NFR-MAINT-1 (Six-Layer Separation)**: Each layer SHALL communicate strictly through standardized dataclass contracts (`FeatureVector`, `IntentCandidate`, `ActionContext`, `FeedbackEvent`, `GatekeeperVerdict`, `ProfileSnapshot`).
* **NFR-MAINT-2 (Test Coverage)**: Automated unit and integration test coverage SHALL exceed $90\%$ of non-UI logic.

---

## 6. Comprehensive Verification, Validation & Traceability Matrix

| Requirement ID | Module / Layer | Verification Method | Associated Test Module | Research Question (RQ) |
|---|---|---|---|---|
| **FR-1.1 to FR-1.6** | Layer 1: Perception | Automated Unit & Benchmark Tests | `test_perception_pipeline.py`, `test_latency_benchmark.py` | Baseline Ingestion |
| **FR-2.1 to FR-2.6** | Layer 2: Calibration | Unit & UI Wizard Integration Tests | `test_calibration_geometry.py`, `test_variance_weight_init.py` | RQ1, RQ4 |
| **FR-3.1 to FR-3.7** | Layer 3: Decision & Safety | Unit & Decoupled Integration Tests | `test_confidence_fuser.py`, `test_safety_gatekeeper.py`, `test_layer3_decoupling.py` | RQ1, RQ3 |
| **FR-4.1 to FR-4.7** | Layer 4: Observation | Unit State Machine & Timing Tests | `test_feedback_state_machine.py`, `test_negative_sub_detectors.py` | RQ2 |
| **FR-5.1 to FR-5.8** | Layer 5: Assessment (RAE)| Unit Mathematical & Gate Tests | `test_runtime_metrics_engine.py`, `test_learning_gatekeeper.py` | RQ3 |
| **FR-6.1 to FR-6.8** | Layer 6: Learning | Mathematical & Invariant Tests | `test_simplex_projection.py`, `test_micro_sgd_optimizer.py`, `test_macro_adaptation.py` | RQ1, RQ2, RQ4 |
| **FR-7.1 to FR-7.4** | Global Uncertainty | Unit Formulation Tests | `test_uncertainty_propagation.py` | RQ2, RQ3 |
| **FR-8.1 to FR-8.5** | UI & Explainability | UI & Render Latency Tests | `test_explainability_hud.py`, `test_research_dashboard.py` | RQ3 |
| **FR-9.1 to FR-9.5** | Diagnostics & Failure | Schema & Policy Tests | `test_enriched_action_context.py`, `test_failure_governance.py` | RQ1, RQ3 |
| **NFR-PERF-1 to 4** | Performance & Resource | Continuous Benchmark Profiler | `test_latency_benchmark.py`, Memory/CPU Profiler | All RQs |
| **NFR-PRIV-1 to 3** | Privacy & Security | Static Code & Network Inspection | `test_privacy_compliance.py` | Ethics & Standards |

---

## 7. Conclusion

This Software Requirements Specification provides the complete, unambiguous, and mathematically formalized engineering blueprint for the Self-Evaluating Adaptive Multimodal Decision Architecture. By specifying all six architectural layers, global uncertainty propagation pipelines, dual-engine runtime assessment engines, and rigorous verification matrices, this document serves as the authoritative baseline for implementation and empirical validation.
