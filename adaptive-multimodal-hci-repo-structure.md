# Base Repository Structure & Codebase Architecture Specification

## Project Title
# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction

---

### Executive Overview
This document provides the definitive, publication-grade specification for the **codebase architecture, directory structure, module decomposition, and file-level design** of the project repository. It establishes strict software engineering boundaries aligned with the **Six Principled Architectural Layers**, ensuring modularity, type safety, testability, and deterministic real-time performance ($\le 29.5\text{ ms}$ total frame latency on CPU hardware).

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               MASTER REPOSITORY ARCHITECTURE                                     │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [LAYER 1: PERCEPTION]      ──► src/perception/   (FaceMesh, Iris, SolvePnP, Hands, Smoothing)   │
│  [LAYER 2: CALIBRATION]     ──► src/calibration/  (5-Phase Wizard, Pose Ellipsoid, Gaze Affine) │
│  [LAYER 3: DECISION]        ──► src/decision/     (3A Fusion, 3B Tier-2 Dwell Gate, 3C Dispatch) │
│  [LAYER 4: OBSERVATION]     ──► src/feedback/     (Temporal State Machine, 5 Negative Detectors) │
│  [LAYER 5: ASSESSMENT]      ──► src/assessment/   (5A Metrics Engine, 5B Intelligent Gatekeeper) │
│  [LAYER 6: LEARNING]        ──► src/learning/     (Micro SGD, Box Simplex Solver, Macro & SPRT)  │
│  [PERSISTENCE & SCHEMAS]    ──► src/storage/      (Immutable ProfileSnapshot Store & Telemetry)  │
│  [EXPLAINABILITY & UI]      ──► src/ui/           (PyQt6 Explainability HUD & Research Dashboard)│
│  [EMPIRICAL EVALUATION]     ──► src/evaluation/   (Latin Square A/B Runner & Statistical Models) │
│  [SYSTEM TEST SUITE]        ──► tests/            (Unit Invariant Tests, Integration & Latency)  │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Master Repository Directory Tree

```
adaptive-multimodal-hci/
├── .github/
│   └── workflows/
│       ├── test-suite.yml              # CI automated test runner & flake8/mypy linter
│       └── benchmark.yml               # Automated frame latency & memory regression check
├── configs/
│   ├── default_config.yaml             # System hyperparameters, thresholds & frame budgets
│   ├── actions_config.yaml             # Action taxonomy, Tier-1/Tier-2 classification
│   └── logging_config.yaml             # Telemetry log formatting & rotation rules
├── docs/
│   ├── adaptive-multimodal-hci-proposal.md            # Canonical Academic Proposal
│   ├── adaptive-multimodal-hci-srs.md                 # ISO/IEC/IEEE 29148 SRS Specification
│   ├── adaptive-multimodal-hci-deliverables.md        # Master Deliverables Specification
│   ├── adaptive-multimodal-hci-architecture.md        # Technical System Architecture
│   ├── adaptive-multimodal-hci-implementation-plan.md # 4-Week Engineering Roadmap
│   ├── adaptive-multimodal-hci-repo-structure.md      # Repository Architecture (This Doc)
│   └── Proposed_Innovations.md                        # Technical Innovations Deep-Dive
├── profiles/                                          # Local JSON/SQLite user profile store
│   └── default_user.json                              # Default bootstrap profile template
├── logs/                                              # Telemetry and session data store
│   └── telemetry/                                     # JSONL formatted session logs
├── reports/                                           # Auto-generated markdown session reports
│   └── figures/                                       # Convergence & ECE chart png/svg files
├── scripts/
│   ├── run_system.py                   # Production launcher (Perception + Decision + HUD)
│   ├── run_calibration.py              # Standalone interactive onboarding wizard
│   ├── run_dashboard.py                # Standalone research dashboard launcher
│   ├── run_benchmarks.py               # Frame cycle latency & CPU profiler script
│   └── run_ab_study.py                 # Counterbalanced Latin Square A/B study runner
├── src/
│   ├── __init__.py
│   ├── main.py                         # Central pipeline coordinator & lifecycle manager
│   ├── capture/                        # Video acquisition & hardware ingestion
│   │   ├── __init__.py
│   │   ├── video_stream.py             # Threaded camera capture worker with ring buffer
│   │   └── frame_types.py              # RawFrame dataclass & capture configuration
│   ├── perception/                     # Layer 1: Feature Extraction & Spatial Filtering
│   │   ├── __init__.py
│   │   ├── face_mesh_extractor.py      # MediaPipe FaceMesh & 10-point refined iris tracker
│   │   ├── head_pose_estimator.py      # Levenberg-Marquardt SolvePnP 3D pose solver
│   │   ├── hand_pose_extractor.py      # MediaPipe Hands 21-point 3D kinematic tracker
│   │   ├── holt_winters_filter.py      # Adaptive velocity-scaled double exponential filter
│   │   └── feature_pipeline.py         # Perception pipeline coordinator & covariance builder
│   ├── calibration/                    # Layer 2: Onboarding & Profile Bootstrapping
│   │   ├── __init__.py
│   │   ├── wizard_controller.py        # 5-phase onboarding state coordinator
│   │   ├── geometry_profiler.py        # Neutral pose 95% ellipsoid & gaze affine solver
│   │   ├── tempo_estimator.py          # Visual-motor reaction tempo tau_user estimator
│   │   └── variance_weight_init.py     # Noise-variance inverse weighting synthesizer
│   ├── decision/                       # Layer 3: Fusion, Safety Reasoning & OS Dispatch
│   │   ├── __init__.py
│   │   ├── confidence_fuser.py         # Stage 3A: Vectorized linear dot-product fuser
│   │   ├── static_baseline_engine.py   # Control baseline engine with static boolean rules
│   │   ├── intent_evaluator.py         # Candidate activation threshold & lockout evaluator
│   │   ├── safety_gatekeeper.py        # Stage 3B: User-relative Tier-2 dwell confirmation
│   │   └── action_dispatcher.py        # Stage 3C: Native OS keystroke & mouse executor
│   ├── feedback/                       # Layer 4: Asynchronous Implicit Feedback Observation
│   │   ├── __init__.py
│   │   ├── temporal_state_machine.py   # 4-window temporal coordinator & ring buffer
│   │   ├── undo_hook_detector.py       # Sub-detector 1: Low-level OS hook (Ctrl+Z / Alt+Left)
│   │   ├── reversal_detector.py        # Sub-detector 2: Directional oppositional command watcher
│   │   ├── retry_detector.py           # Sub-detector 3: Rapid duplicate gesture retry counter
│   │   ├── dismissal_detector.py       # Sub-detector 4: Immediate window/tab dismissal watcher
│   │   └── override_detector.py        # Sub-detector 5: Sudden mouse (>800px/s) / key override
│   ├── assessment/                     # Layer 5: Runtime Assessment Engine (RAE)
│   │   ├── __init__.py
│   │   ├── runtime_metrics_engine.py   # Engine 5A: EWMA AG, LV, WSI, ACI, ECE, RR, DRT
│   │   ├── learning_gatekeeper.py      # Engine 5B: 6-rule validation firewall (APPROVE/REJECT)
│   │   ├── session_report_generator.py # Markdown report & matplotlib figure synthesizer
│   │   └── failure_classifier.py       # 4-stage failure taxonomy & targeted governance
│   ├── learning/                       # Layer 6: Online SGD & Macro Adaptation State Machine
│   │   ├── __init__.py
│   │   ├── micro_sgd_optimizer.py      # Ambiguity-gated online SGD weight & threshold updater
│   │   ├── simplex_projector.py        # Exact 1D dual bisection box-constrained simplex solver
│   │   ├── macro_adaptation_engine.py  # Epoch state machine (MERGE/FREEZE/DISCARD/RECAL)
│   │   ├── wald_sprt_detector.py       # Cumulative sequential hypothesis drift detector
│   │   └── uncertainty_propagator.py   # Global C_update uncertainty & learning rate scaler
│   ├── storage/                        # Persistence, Data Models & Serialization
│   │   ├── __init__.py
│   │   ├── schemas.py                  # Immutable dataclasses: FeatureVector, ActionContext, etc.
│   │   ├── profile_store.py            # SQLite/JSON profile repository & version manager
│   │   └── telemetry_logger.py         # Asynchronous JSONL telemetry event streamer
│   ├── ui/                             # Explainability HUD & Diagnostic User Interfaces
│   │   ├── __init__.py
│   │   ├── explainability_hud.py       # Semi-transparent PyQt6 click-through HUD overlay
│   │   ├── confidence_bars.py          # Per-modality animated visual progress indicators
│   │   ├── dwell_confirmation_ring.py  # 600ms circular Tier-2 countdown renderer
│   │   ├── health_badge_renderer.py    # Active state badge renderer (LEARNING -> STABLE)
│   │   ├── wizard_view.py              # Fullscreen 5-phase onboarding UI view
│   │   └── research_dashboard.py       # Multi-tab research control panel & diagnostic GUI
│   ├── evaluation/                     # Experimental Benchmark & Statistical Suite
│   │   ├── __init__.py
│   │   ├── study_manager.py            # Latin Square counterbalanced A/B test coordinator
│   │   ├── task_scripts.py             # Standardized desktop interaction benchmark tasks
│   │   └── statistical_analyzer.py     # Wilcoxon Signed-Rank & Linear Mixed-Effects modeler
│   └── utils/                          # Common Mathematical, Geometry & System Utilities
│       ├── __init__.py
│       ├── geometry.py                 # Affine transforms, Euler angle conversions, 3D math
│       ├── math_utils.py               # EWMA filters, softmax, sigmoid, numeric clipping
│       └── system_info.py              # CPU/RAM profiler, OS active window detector
├── tests/                              # Comprehensive Automated Test Suite
│   ├── __init__.py
│   ├── conftest.py                     # Synthetic landmark fixtures & mock video streams
│   ├── unit/                           # Layer-by-layer isolated mathematical unit tests
│   │   ├── test_video_stream.py
│   │   ├── test_face_mesh_extractor.py
│   │   ├── test_head_pose_estimator.py
│   │   ├── test_hand_pose_extractor.py
│   │   ├── test_holt_winters_filter.py
│   │   ├── test_calibration_geometry.py
│   │   ├── test_variance_weight_init.py
│   │   ├── test_confidence_fuser.py
│   │   ├── test_simplex_projection.py
│   │   ├── test_safety_gatekeeper.py
│   │   ├── test_feedback_state_machine.py
│   │   ├── test_negative_sub_detectors.py
│   │   ├── test_runtime_metrics_engine.py
│   │   ├── test_learning_gatekeeper.py
│   │   ├── test_micro_sgd_optimizer.py
│   │   ├── test_macro_adaptation.py
│   │   ├── test_wald_sprt_detector.py
│   │   ├── test_uncertainty_propagation.py
│   │   └── test_profile_store.py
│   ├── integration/                    # Multi-layer integration & data pipeline tests
│   │   ├── test_perception_pipeline.py
│   │   ├── test_layer3_decoupling.py
│   │   ├── test_closed_loop_feedback.py
│   │   └── test_session_reporting.py
│   └── benchmarks/                     # Performance, latency & resource budget tests
│       ├── test_frame_latency.py
│       └── test_memory_footprint.py
├── .gitignore
├── Makefile                            # Convenience build, test, lint & format commands
├── README.md                           # Master project README & documentation portal
├── pyproject.toml                      # Modern PEP 517/518 build & dependency configuration
└── requirements.txt                    # Locked production & testing dependency list
```

---

## 2. Detailed Package & Subpackage Specification

---

### 2.1 Package: `src/capture/`
* **Purpose**: Hardware video capture management operating in an isolated high-priority thread to prevent frame dropping.
* **Key Files**:
  * `video_stream.py`:
    * Class `VideoStreamReader(threading.Thread)`: Ingests frames at native $30\text{ FPS}$ from OpenCV `cv2.VideoCapture` into a lock-free double-buffered queue.
    * Method `get_latest_frame() -> Optional[RawFrame]`: Returns the most recent frame with zero-copy reference.
  * `frame_types.py`:
    * Dataclass `RawFrame`: Encapsulates `image_rgb: np.ndarray`, `timestamp_ms: float`, `frame_index: int`, and `camera_lux_est: float`.

---

### 2.2 Package: `src/perception/` (Layer 1: Perception)
* **Purpose**: Computer vision extraction and spatial-temporal coordinate filtering.
* **Key Files**:
  * `face_mesh_extractor.py`:
    * Class `FaceMeshExtractor`: Manages MediaPipe FaceMesh model. Computes normalized iris offsets $(r_x, r_y)$ and Eye Aspect Ratio ($\text{EAR}$).
    * Method `process(frame: np.ndarray) -> GazeLandmarkResult`.
  * `head_pose_estimator.py`:
    * Class `HeadPoseEstimator`: Solves Levenberg-Marquardt Perspective-n-Point (SolvePnP) using 6 canonical 3D facial landmarks and camera matrix $\mathbf{K}$.
    * Method `estimate_pose(landmarks: np.ndarray) -> Tuple[float, float, float]`: Returns continuous `(yaw, pitch, roll)` in degrees.
  * `hand_pose_extractor.py`:
    * Class `HandPoseExtractor`: Manages MediaPipe Hands model. Extracts 21 3D landmarks, calculates pinch distance $d_{\text{pinch}}$, palm normal $\mathbf{n}_{\text{palm}}$, and wrist velocity $\mathbf{v}_{\text{wrist}}$.
    * Method `process(frame: np.ndarray) -> HandLandmarkResult`.
  * `holt_winters_filter.py`:
    * Class `AdaptiveHoltWintersFilter`: Implements double exponential smoothing dynamically scaled by velocity $\alpha_t = \text{clip}(\alpha_0 + \gamma \|\mathbf{v}\|, 0.20, 0.85)$.
    * Method `filter(coord: np.ndarray, velocity: float) -> np.ndarray`.
  * `feature_pipeline.py`:
    * Class `PerceptionPipeline`: Coordinates all extractors, applies smoothing, estimates sensor covariance $\boldsymbol{\Sigma}_{\text{sensor}}$, and emits the consolidated `FeatureVector`.

---

### 2.3 Package: `src/calibration/` (Layer 2: Calibration)
* **Purpose**: 60–90 second interactive onboarding wizard and user profile bootstrapping.
* **Key Files**:
  * `wizard_controller.py`:
    * Class `CalibrationWizardController`: State machine managing transitions across Phases A through E.
    * Method `advance_phase() -> CalibrationPhaseState`.
  * `geometry_profiler.py`:
    * Class `GeometryProfiler`: Computes the 95% neutral pose ellipsoid $\mathcal{E}_{\text{head}} = (\boldsymbol{\mu}_{\text{pose}}, \boldsymbol{\Sigma}_{\text{pose}}^{-1})$ and fits the 5-point gaze 2D affine matrix $\mathbf{M}_{\text{gaze}}$.
  * `tempo_estimator.py`:
    * Class `TempoEstimator`: Computes user visual-motor reaction tempo $\tau_{\text{user}} \in [0.35\text{s}, 0.95\text{s}]$.
  * `variance_weight_init.py`:
    * Class `VarianceWeightInitializer`: Generates initial weights inversely proportional to sensor noise $\tilde{w}_i \propto 1/\sigma_i^2$ and projects onto the box simplex (`Profile v1`).

---

### 2.4 Package: `src/decision/` (Layer 3: Decision & Safety Engine)
* **Purpose**: Decoupled confidence fusion, safety reasoning, and native OS command dispatching.
* **Key Files**:
  * `confidence_fuser.py`:
    * Class `ConfidenceFuser`: Vectorized dot product $S_a(\mathbf{x}) = \mathbf{w}_a^T \mathbf{x} = \sum w_i s_i$.
  * `static_baseline_engine.py`:
    * Class `StaticBaselineEngine`: Hardcoded boolean IF-THEN rule engine used as the control condition in A/B experiments.
  * `intent_evaluator.py`:
    * Class `IntentEvaluator`: Evaluates $S_a(\mathbf{x}) \ge \theta_a$ and refractory lockouts, generating `IntentCandidate`.
  * `safety_gatekeeper.py`:
    * Class `SafetyGatekeeper`: Evaluates User-Relative Tier-2 Gate $\theta_{\text{tier2}, a} = \min(0.95, \max(\theta_a + 0.15, \mu_S + 1.5\sigma_S))$, manages $600\text{ ms}$ visual dwell progress, and arms $3.0\text{ s}$ undo hook.
  * `action_dispatcher.py`:
    * Class `ActionDispatcher`: Executes native OS events via `pyautogui` / `win32api` and dispatches `ActionContext` to Layer 4.

---

### 2.5 Package: `src/feedback/` (Layer 4: Implicit Feedback Observer)
* **Purpose**: Temporal state machine and asynchronous sub-detectors monitoring user behavior.
* **Key Files**:
  * `temporal_state_machine.py`:
    * Class `TemporalFeedbackStateMachine`: Manages active `ActionContextQueue` ring buffer, enforcing 200ms Refractory Window, 1.8s Correction Window, and Stability Expiration.
  * `undo_hook_detector.py`:
    * Class `UndoHookDetector`: Low-level hook intercepting `Ctrl+Z`, `Alt+Left`, `Ctrl+Shift+T` on target process ID.
  * `reversal_detector.py`:
    * Class `ReversalDetector`: Intercepts directional oppositional continuous commands (Scroll Down $\to$ Scroll Up).
  * `retry_detector.py`:
    * Class `RetryDetector`: Identifies rapid duplicate gesture retries ($\ge 2$ within $1.2\text{ s}$).
  * `dismissal_detector.py`:
    * Class `DismissalDetector`: Tracks immediate window/tab closures within $1.5\text{ s}$.
  * `override_detector.py`:
    * Class `OverrideDetector`: Captures sudden physical mouse ($>800\text{ px/s}$) or keyboard intervention.

---

### 2.6 Package: `src/assessment/` (Layer 5: Runtime Assessment Engine - RAE)
* **Purpose**: Continuous health metrics calculation, update gatekeeping, and session reporting.
* **Key Files**:
  * `runtime_metrics_engine.py` (Engine 5A):
    * Class `RuntimeMetricsEngine`: Computes EWMA Adaptation Gain ($AG_t$), Sliding Learning Velocity ($LV_t$), Weight Stability Index ($WSI_t$), Adaptation Confidence Index ($ACI_t$), Expected Calibration Error ($ECE_t$), Recovery Rate ($RR$), and Drift Recovery Time ($DRT$).
  * `learning_gatekeeper.py` (Engine 5B):
    * Class `LearningGatekeeper`: Validates 6 rejection rules (Sample floor $k \ge 3$, Confidence floor $c_{fb} \ge 0.40$, Neutral suppression, Macro drift lockout $S_m \ge 2.89$, Contradiction resolution, Sensor SNR check) and emits `GatekeeperVerdict(APPROVE/REJECT)`.
  * `session_report_generator.py`:
    * Class `SessionReportGenerator`: Compiles session KPIs, significant event logs, and 5 matplotlib convergence plots into a clean markdown document.
  * `failure_classifier.py`:
    * Class `FailureClassifier`: Enforces the 4-Stage Failure Governance Subsystem (Detection $\to$ Classification $\to$ Severity $\to$ Corrective Policy).

---

### 2.7 Package: `src/learning/` (Layer 6: Online Learning & Optimization)
* **Purpose**: Real-time micro-adaptation, exact simplex projection, and epoch macro-adaptation.
* **Key Files**:
  * `micro_sgd_optimizer.py`:
    * Class `MicroSGDOptimizer`: Ambiguity-gated per-interaction parameter updater for $\mathbf{w}_a$ and $\theta_a$.
  * `simplex_projector.py`:
    * Class `BoxSimplexProjector`: Exact 1D dual bisection root solver enforcing $\sum w_i = 1.0$ and $w_i \in [0.05, 0.85]$.
  * `macro_adaptation_engine.py`:
    * Class `MacroAdaptationEngine`: Evaluates periodic epochs ($N=30\text{--}50$ interactions) and triggers `MERGE`, `FREEZE`, `DISCARD`, or `RECALIBRATE` policies.
  * `wald_sprt_detector.py`:
    * Class `WaldSPRTDetector`: Cumulative log-likelihood sequential hypothesis tester detecting environmental calibration drift ($S_m \ge 2.89$).
  * `uncertainty_propagator.py`:
    * Class `UncertaintyPropagator`: Computes global $C_{\text{update}}$ and modulates effective learning rate $\eta_{\text{eff}} = \eta_0 \cdot C_{\text{update}}$.

---

### 2.8 Package: `src/storage/`
* **Purpose**: Immutable schema definitions, SQLite/JSON persistence, and telemetry event streaming.
* **Key Files**:
  * `schemas.py`: Core dataclasses (`FeatureVector`, `IntentCandidate`, `ActionContext`, `FeedbackEvent`, `GatekeeperVerdict`, `ProfileSnapshot`).
  * `profile_store.py`:
    * Class `ProfileStore`: Thread-safe persistence engine managing versioned user profiles (`Profile v_k`).
  * `telemetry_logger.py`:
    * Class `TelemetryLogger`: Asynchronous non-blocking JSONL event logger writing detailed interaction logs.

---

### 2.9 Package: `src/ui/`
* **Purpose**: Visual explainability overlay, onboarding views, and interactive research dashboard.
* **Key Files**:
  * `explainability_hud.py`: Semi-transparent PyQt6 click-through overlay showing confidence bars, dwell ring, and health state badges.
  * `wizard_view.py`: Fullscreen 5-phase interactive calibration wizard interface.
  * `research_dashboard.py`: Multi-tab PyQt6 GUI with live ACI gauges, SPRT trajectory graphs, parameter evolution curves, and study manager.

---

### 2.10 Package: `src/evaluation/`
* **Purpose**: Standardized experimental protocol execution and statistical analysis.
* **Key Files**:
  * `study_manager.py`: Coordinates counterbalanced Latin Square A/B user studies ($A \to B$ vs. $B \to A$) with 5-minute washout intervals.
  * `task_scripts.py`: Standardized isomorphic task automation routines (Document Navigation, Tab Management, Media Control).
  * `statistical_analyzer.py`: Performs Wilcoxon Signed-Rank tests and Linear Mixed-Effects (LME) modeling.

---

## 3. Automated Test Suite & Benchmark Architecture (`tests/`)

Development enforces strict test-driven invariant verification across three testing tiers:

```
tests/
├── conftest.py                         # Reusable synthetic fixtures, landmark mocks & video feeds
├── unit/                               # Isolated unit tests for mathematical correctness
│   ├── test_video_stream.py            # Validates zero-copy buffer & frame acquisition
│   ├── test_face_mesh_extractor.py     # Validates blink suppression & normalized coordinates
│   ├── test_head_pose_estimator.py     # Validates SolvePnP Euler angles & Mahalanobis confidence
│   ├── test_hand_pose_extractor.py     # Validates pinch distance & wrist velocity derivation
│   ├── test_holt_winters_filter.py     # Validates dynamic alpha scaling & jitter elimination
│   ├── test_calibration_geometry.py    # Validates 95% ellipsoid & gaze affine perspective map
│   ├── test_variance_weight_init.py    # Validates noise-variance inverse weighting
│   ├── test_confidence_fuser.py        # Validates dot-product fusion score bounds [0.0, 1.0]
│   ├── test_simplex_projection.py      # Validates sum(w_i)=1.0 and box constraints [0.05, 0.85]
│   ├── test_safety_gatekeeper.py       # Validates Tier-2 dwell gating & 3.0s undo hook arming
│   ├── test_feedback_state_machine.py  # Validates 200ms refractory lockout & 1.8s stability expiry
│   ├── test_negative_sub_detectors.py  # Validates all 5 negative sub-detector event triggers
│   ├── test_runtime_metrics_engine.py  # Validates mathematical derivations of AG, LV, WSI, ACI, ECE
│   ├── test_learning_gatekeeper.py     # Validates all 6 gatekeeper rejection rules
│   ├── test_micro_sgd_optimizer.py     # Validates ambiguity-gated SGD updates
│   ├── test_macro_adaptation.py        # Validates MERGE, FREEZE, DISCARD, RECALIBRATE state logic
│   ├── test_wald_sprt_detector.py      # Validates cumulative SPRT log-likelihood & alarm threshold
│   ├── test_uncertainty_propagation.py # Validates C_update calculation & eta_eff scaling
│   └── test_profile_store.py           # Validates ProfileSnapshot serialization & immutability
├── integration/                        # Multi-layer pipeline verification
│   ├── test_perception_pipeline.py     # End-to-end landmark to FeatureVector assembly
│   ├── test_layer3_decoupling.py       # Validates independent execution of 3A, 3B, and 3C
│   ├── test_closed_loop_feedback.py    # Traces full loop from gesture to parameter adaptation
│   └── test_session_reporting.py       # Validates automated markdown report generation
└── benchmarks/                         # Performance & resource budget verifications
    ├── test_frame_latency.py           # Asserts total frame cycle <= 29.5ms on CPU hardware
    └── test_memory_footprint.py        # Asserts total resident memory <= 350MB
```

---

## 4. Configuration & Dependency Management

### 4.1 Production & Testing Dependencies (`requirements.txt`)
```txt
# Computer Vision & Machine Learning
opencv-python>=4.8.0
mediapipe>=0.10.9
numpy>=1.24.0
scipy>=1.11.0

# Desktop GUI & Visual Explainability
PyQt6>=6.5.0
matplotlib>=3.7.0

# OS Automation & Low-Level Hooking
pyautogui>=0.9.54
pynput>=1.7.6
pywin32>=306; sys_platform == 'win32'

# Utilities & Serialization
pyyaml>=6.0.1
dataclasses-json>=0.6.0

# Testing & Quality Assurance
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-benchmark>=4.0.0
flake8>=6.1.0
mypy>=1.5.0
```

### 4.2 Modern Build Configuration (`pyproject.toml`)
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "adaptive-multimodal-hci"
version = "1.0.0"
description = "Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction"
readme = "README.md"
requires-python = ">=3.11"
authors = [
    { name = "Gowshick", email = "gowshick@example.com" }
]
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Topic :: Scientific/Engineering :: Human Machine Interfaces",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --cov=src --cov-report=term-missing"
testpaths = ["tests"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## 5. Master Traceability & Verification Mapping

| Package / Module | Layer Responsibility | Key Deliverable | Primary Test Module | Performance Budget |
|---|---|---|---|---|
| `src/capture/` | Video Acquisition | D1 | `test_video_stream.py` | $< 5.0\text{ ms}$ |
| `src/perception/` | Layer 1: Perception | D1 | `test_perception_pipeline.py` | $< 18.0\text{ ms}$ |
| `src/calibration/` | Layer 2: Calibration | D3 | `test_calibration_geometry.py` | $\le 90\text{ s}$ total |
| `src/decision/` | Layer 3: Decision & Safety | D2, D4 | `test_layer3_decoupling.py` | $< 2.5\text{ ms}$ |
| `src/feedback/` | Layer 4: Observation | D4 | `test_feedback_state_machine.py`| $< 1.0\text{ ms}$ |
| `src/assessment/` | Layer 5: Assessment (RAE) | D5 | `test_runtime_metrics_engine.py`| $< 1.5\text{ ms}$ |
| `src/learning/` | Layer 6: Online Learning | E1 | `test_simplex_projection.py` | $< 1.0\text{ ms}$ |
| `src/storage/` | Persistence & Telemetry | D3, D5 | `test_profile_store.py` | $< 20\text{ ms}$ IO |
| `src/ui/` | Explainability HUD & Dash | E2, E3 | `test_explainability_hud.py` | $< 1.0\text{ ms}$ render |
| `src/evaluation/` | Empirical A/B Study | D5 | `test_session_reporting.py` | Standalone |

---

## 6. Conclusion
This Base Repository Structure specification establishes the definitive architectural hierarchy for the codebase. With clean module boundaries, strict typing contracts, and comprehensive unit/integration test coverage, it guarantees a robust, maintainable, and high-performance implementation.
