# Base Repository Structure & Codebase Architecture Specification

## Project Title
# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction

---

### Executive Overview
This document provides the definitive, publication-grade specification for the **complete repository ecosystem**, encompassing:
1. **The Revised Core Codebase (`src/`)** aligned with the 8-element principled architectural layers (Layer 1, Layer 1B, Modality Arbiter, Layers 2–6).
2. **The Comprehensive Documentation Suite (`docs/`)** containing academic, technical, user, and API manuals.
3. **The Academic Publication & LaTeX Preprint Package (`paper/`)** for peer-reviewed conference dissemination.
4. **The Empirical Evaluation, Instruments & Replication Dataset Package (`evaluation/`, `data/`, `notebooks/`)**.
5. **The Formal Deliverable Verification & Release Packaging (`deliverables/`)** mapping all Core Deliverables (D1–D5), Research Enhancements (E1–E3), and Documentation Artifacts (DOC1–DOC5).
6. **The Automated Test Suite & Latency Benchmarks (`tests/`)**.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               MASTER REPOSITORY ECOSYSTEM                                        │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [CORE CODEBASE]            ──► src/             (6 Principled Layers, UI, Storage, Utilities)   │
│  [DOCUMENTATION SUITE]      ──► docs/            (Proposals, SRS, Architecture, Manuals, APIs)   │
│  [ACADEMIC PREPRINT & TEX]  ──► paper/           (LaTeX Manuscript, Figures, BibTeX References)  │
│  [EVALUATION & DATASETS]    ──► evaluation/,     (Protocols, Questionnaires, Task Scripts,       │
│                                 data/, notebooks/(Benchmark Datasets & Jupyter Analysis)         │
│  [DELIVERABLES PACKAGING]   ──► deliverables/    (D1–D5 & E1–E3 Sign-Offs & Release Bundles)     │
│  [AUTOMATED TEST SUITE]     ──► tests/           (Unit Invariants, Multi-Layer Integration, Perf)│
│  [REPORTS & TELEMETRY]      ──► reports/, logs/  (Auto-Generated Markdown Reports & JSONL Logs)  │
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
│       ├── benchmark.yml               # Automated frame latency & memory regression check
│       └── paper-build.yml             # Automated LaTeX compilation to PDF preprint
├── configs/
│   ├── default_config.yaml             # System hyperparameters, thresholds & frame budgets
│   ├── gesture_vocabulary.yaml         # [NEW] Fixed gesture token dictionary & default thresholds
│   ├── actions_config.yaml             # Action taxonomy, Tier-1/Tier-2 classification
│   └── logging_config.yaml             # Telemetry log formatting & rotation rules
├── data/                               # Open-Science Datasets & Synthetic Benchmarks
│   ├── benchmark_traces/               # Pre-recorded landmark sequences for deterministic testing
│   │   ├── subject_normal_posture.npz
│   │   ├── subject_glasses_glare.npz
│   │   ├── subject_rapid_fatigue.npz
│   │   └── synthetic_drift_noise.npz
│   └── synthetic_outliers/             # Controlled stress-test failure vectors
├── deliverables/                       # Formal Release Packages & Sign-Off Artifacts
│   ├── D1_perception_pipeline/         # Deliverable D1 release bundle, latency proof & sign-off
│   │   ├── README.md
│   │   └── verification_report.pdf
│   ├── D2_fusion_engine/               # Deliverable D2 release bundle, Command Composer proof & sign-off
│   ├── D3_calibration_wizard/          # Deliverable D3 release bundle & 5-phase validation log
│   ├── D4_feedback_observer/           # Deliverable D4 release bundle & detector precision matrix
│   ├── D5_runtime_assessment/          # Deliverable D5 release bundle & sample session reports
│   ├── E1_dual_scale_engine/           # Enhancement E1 release bundle & macro state test logs
│   ├── E2_explainability_hud/          # Enhancement E2 release bundle & HUD render benchmarks
│   └── E3_research_dashboard/          # Enhancement E3 release bundle & UI sync benchmarks
├── docs/                               # Comprehensive Technical & Academic Documentation
│   ├── adaptive-multimodal-hci-proposal.md            # Canonical Academic Proposal (DOC1)
│   ├── adaptive-multimodal-hci-srs.md                 # ISO/IEC/IEEE 29148 SRS (DOC2)
│   ├── adaptive-multimodal-hci-deliverables.md        # Master Deliverables Specification
│   ├── adaptive-multimodal-hci-architecture.md        # Technical System Architecture (DOC3)
│   ├── adaptive-multimodal-hci-repo-structure.md      # Repository Architecture (This Document)
│   ├── adaptive-multimodal-hci-sdlc-spiral.md         # Spiral SDLC Methodology Specification
│   ├── adaptive-multimodal-hci-implementation-plan.md # High-Level Engineering Overview (DOC4)
│   ├── Proposed_Innovations.md                        # Technical Innovations Deep-Dive
│   ├── Project_Applications.md                        # Application Domains & Use Cases
│   ├── literature-review-and-methodology.md           # Theoretical Foundations & Comparative SOTA
│   ├── literature-review-summary.md                   # Executive Literature Synthesis
│   ├── Detailed Literature Review.md                  # Exhaustive Academic Literature Corpus
│   ├── api/                                           # Subsystem API Reference Manuals
│   │   ├── perception_api.md
│   │   ├── gesture_api.md                             # [NEW] Gesture Vocabulary & Classifier API
│   │   ├── arbiter_api.md                             # [NEW] Modality Arbiter API
│   │   ├── calibration_api.md
│   │   ├── decision_api.md
│   │   ├── feedback_api.md
│   │   ├── assessment_api.md
│   │   └── learning_api.md
│   ├── guides/                                        # User, Operator & Developer Guides
│   │   ├── user_manual.md                             # End-user setup & interaction guide
│   │   ├── calibration_guide.md                       # 5-phase onboarding walkthrough
│   │   ├── developer_guide.md                         # Codebase contribution & architecture guide
│   │   └── deployment_guide.md                        # Packaging, installer & OS permissions
│   └── math/                                          # Theoretical Formulations & Proofs
│       ├── simplex_projection_proof.md                # 1D dual bisection convergence proof
│       ├── wald_sprt_derivation.md                    # Sequential log-likelihood boundary derivation
│       └── uncertainty_propagation_model.md           # End-to-end C_update formulation
├── evaluation/                         # Empirical Evaluation, Protocols & Instruments
│   ├── protocols/                      # Human-subject study protocols & IRB materials
│   │   ├── study_protocol.md                          # Counterbalanced A/B experimental design
│   │   ├── participant_briefing.md                    # Scripted verbal onboarding & consent form
│   │   └── latin_square_order.json                    # Cohort counterbalance order assignments
│   ├── instruments/                    # Standardized UX & Psychometric Survey Questionnaires
│   │   ├── sus_questionnaire.md                       # System Usability Scale (10 items, 0-100)
│   │   ├── nasa_tlx_survey.md                         # Raw NASA-TLX 6-dimensional workload form
│   │   └── adaptation_experience_scale.md             # 7-item custom adaptation rating scale
│   ├── tasks/                          # Isomorphic task automation scripts & target sequences
│   │   ├── task1_document_navigation.py
│   │   ├── task2_window_management.py
│   │   └── task3_media_player_control.py
│   └── analysis/                       # Statistical analysis scripts
│       ├── run_wilcoxon_tests.py                      # Paired non-parametric hypothesis tests
│       └── run_linear_mixed_effects.py                # LME model (Condition * Order + (1|Subject))
├── logs/                               # Session Telemetry & Runtime Logs
│   ├── telemetry/                                     # JSONL formatted interaction records
│   └── system/                                        # Execution trace and debug logs
├── media/                              # Media, Diagrams & Walkthrough Assets
│   ├── diagrams/                                      # Vector architecture & sequence diagrams (.svg)
│   ├── ui_mockups/                                    # HUD overlay and dashboard UI mockups
│   └── demo_recordings/                               # System demo walkthrough video (.mp4)
├── notebooks/                          # Interactive Jupyter Research & Analysis Notebooks
│   ├── 01_latency_and_framerate_profiling.ipynb       # Frame cycle & jitter distribution plots
│   ├── 02_calibration_geometry_analysis.ipynb         # 3D pose ellipsoid & gaze affine residuals
│   ├── 03_adaptation_convergence_curves.ipynb         # Weight trajectories & EWMA AG curves
│   ├── 04_sprt_drift_detection_and_recovery.ipynb     # Sequential hypothesis likelihood traces
│   └── 05_empirical_user_study_statistical_lme.ipynb  # Primary benchmark paper figures & tables
├── paper/                              # Academic Conference Publication Package (DOC5)
│   ├── main.tex                                       # LaTeX manuscript entry point (IEEE/ACM format)
│   ├── references.bib                                 # Complete BibTeX bibliography
│   ├── ieee_conference.cls                            # Style template class file
│   ├── sections/                                      # Modular manuscript sections
│   │   ├── 01_abstract.tex
│   │   ├── 02_introduction.tex
│   │   ├── 03_related_work.tex
│   │   ├── 04_system_architecture.tex
│   │   ├── 05_online_adaptation_engine.tex
│   │   ├── 06_runtime_assessment_engine.tex
│   │   ├── 07_empirical_evaluation.tex
│   │   ├── 08_results_and_analysis.tex
│   │   ├── 09_discussion_and_limitations.tex
│   │   └── 10_conclusion.tex
│   ├── figures/                                       # Publication-ready vector PDF figures
│   │   ├── fig1_system_architecture.pdf
│   │   ├── fig2_decision_sequence.pdf
│   │   ├── fig3_convergence_curves.pdf
│   │   ├── fig4_error_rate_comparison.pdf
│   │   └── fig5_sprt_trajectory.pdf
│   └── tables/                                        # LaTeX formatted benchmark tables
│       ├── tab1_latency_breakdown.tex
│       ├── tab2_quantitative_results.tex
│       └── tab3_subjective_scores.tex
├── profiles/                           # Local User Profile Storage Repository
│   └── default_user.json                              # Default bootstrap profile template
├── reports/                            # Automated Post-Session Diagnostic Markdown Reports
│   ├── figures/                                       # Generated Matplotlib figures per session
│   └── session_sample_report.md                       # Sample auto-generated executive report
├── scripts/                            # Operational & Diagnostic CLI Scripts
│   ├── run_system.py                   # Production launcher (Perception + Decision + HUD)
│   ├── run_calibration.py              # Standalone interactive onboarding wizard
│   ├── run_dashboard.py                # Standalone research dashboard launcher
│   ├── run_benchmarks.py               # Frame cycle latency & CPU profiler script
│   ├── run_ab_study.py                 # Counterbalanced Latin Square A/B study runner
│   └── generate_paper_figures.py       # Generates publication PDF charts from session logs
├── src/                                # Core 6-Layer Python Package Source Code
│   ├── __init__.py
│   ├── main.py                         # Central pipeline coordinator & lifecycle manager
│   ├── capture/                        # Video acquisition & threading
│   │   ├── __init__.py
│   │   ├── video_stream.py             # Threaded camera capture worker with ring buffer
│   │   └── frame_types.py              # RawFrame dataclass & capture configuration
│   ├── perception/                     # Layer 1: Feature Extraction, Spatial Filtering & Gaze Dwell
│   │   ├── __init__.py
│   │   ├── face_mesh_extractor.py      # MediaPipe FaceMesh & 10-point refined iris tracker
│   │   ├── head_pose_estimator.py      # Levenberg-Marquardt SolvePnP 3D pose solver
│   │   ├── hand_pose_extractor.py      # MediaPipe Hands 21-point 3D kinematic tracker
│   │   ├── gaze_dwell_tracker.py       # [NEW] Temporal gaze fixation tracker (dwell_ms, stability, anchor)
│   │   ├── holt_winters_filter.py      # Adaptive velocity-scaled double exponential filter
│   │   └── feature_pipeline.py         # Perception pipeline coordinator & PerceptionFrame assembler
│   ├── gesture/                        # [NEW] Layer 1B: Gesture Vocabulary Engine & Modality Arbiter
│   │   ├── __init__.py
│   │   ├── gesture_vocabulary.py       # [NEW] Fixed token dict loader from gesture_vocabulary.yaml
│   │   ├── gesture_classifier.py       # [NEW] Kinematic-to-token classifier with sigmoid confidence
│   │   └── modality_arbiter.py         # [NEW] Rolling device activity monitor & arbitration logic
│   ├── calibration/                    # Layer 2: Onboarding & Profile Bootstrapping
│   │   ├── __init__.py
│   │   ├── wizard_controller.py        # 5-phase onboarding state coordinator
│   │   ├── geometry_profiler.py        # Neutral pose 95% ellipsoid & gaze affine solver
│   │   ├── tempo_estimator.py          # Visual-motor reaction tempo tau_user estimator
│   │   └── variance_weight_init.py     # Noise-variance inverse weighting synthesizer
│   ├── decision/                       # Layer 3: Command Composer, Safety Reasoning & OS Dispatch
│   │   ├── __init__.py
│   │   ├── command_composer.py         # [NEW] Stage 3A: Two-stage asymmetric command composer
│   │   ├── static_baseline_engine.py   # Control baseline engine with static boolean rules
│   │   ├── intent_evaluator.py         # Candidate activation threshold & lockout evaluator
│   │   ├── safety_gatekeeper.py        # Stage 3B: Tier 0/1/2 safety gates & dwell confirmation
│   │   └── action_dispatcher.py        # Stage 3C: Native OS keystroke & mouse executor + KB handoff
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
│       └── system_info.py              # CPU/RAM profiler, OS active window & UIAutomation focus detector
├── tests/                              # Comprehensive Automated Test Suite
│   ├── __init__.py
│   ├── conftest.py                     # Synthetic landmark fixtures & mock video streams
│   ├── unit/                           # Isolated unit tests for mathematical correctness
│   │   ├── test_video_stream.py
│   │   ├── test_face_mesh_extractor.py
│   │   ├── test_head_pose_estimator.py
│   │   ├── test_hand_pose_extractor.py
│   │   ├── test_gaze_dwell_tracker.py
│   │   ├── test_gesture_vocabulary.py
│   │   ├── test_modality_arbiter.py
│   │   ├── test_holt_winters_filter.py
│   │   ├── test_calibration_geometry.py
│   │   ├── test_variance_weight_init.py
│   │   ├── test_confidence_fuser.py
│   │   ├── test_gesture_classifier.py
│   │   ├── test_command_composer.py
│   │   ├── test_tier0_intentionality_gate.py
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
│   ├── integration/                    # Multi-layer pipeline verification
│   │   ├── test_perception_pipeline.py
│   │   ├── test_layer3_decoupling.py
│   │   ├── test_keyboard_handoff.py
│   │   ├── test_closed_loop_feedback.py
│   │   └── test_session_reporting.py
│   └── benchmarks/                     # Performance, latency & resource budget tests
│       ├── test_frame_latency.py
│       └── test_memory_footprint.py
├── .gitignore
├── Makefile                            # Convenience build, test, lint, paper & benchmark targets
├── README.md                           # Master project README & documentation portal
├── pyproject.toml                      # Modern PEP 517/518 build & dependency configuration
└── requirements.txt                    # Locked production, test & publication dependencies
```

---

## 2. Detailed Documentation Architecture (`docs/`)

The documentation suite is structured into four specialized tiers covering academic theory, engineering specifications, user manuals, and mathematical proofs:

```
┌────────────────────────────────────────────────────────────────────────┐
│                     DOCUMENTATION TIERS BREAKDOWN                      │
├────────────────────────────────────────────────────────────────────────┤
│  Tier 1: Canonical Academic & Engineering Specifications (Root)       │
│  Tier 2: Subsystem API Reference Manuals (`docs/api/`)                 │
│  Tier 3: User, Operator & Developer Onboarding Guides (`docs/guides/`) │
│  Tier 4: Mathematical Formulations & Rigorous Proofs (`docs/math/`)    │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Tier 1: Canonical Project Specifications
* **`adaptive-multimodal-hci-proposal.md` (DOC1)**: Formal research proposal, scientific thesis, Research Questions (RQ1–RQ4), application domains, and 5-stage validation methodology.
* **`adaptive-multimodal-hci-srs.md` (DOC2)**: ISO/IEC/IEEE 29148 compliant Software Requirements Specification detailing functional requirements (`FR-1.1` to `FR-9.5`, `FR-1B.x`, `FR-ARB.x`), non-functional budgets, and traceability matrices.
* **`adaptive-multimodal-hci-deliverables.md`**: Master breakdown of all Core Deliverables (D1–D5), Research Enhancements (E1–E3), and academic replication artifacts.
* **`adaptive-multimodal-hci-architecture.md` (DOC3)**: Deep technical specification of the 8-element principled layers, sequence diagrams, global uncertainty models, and data schemas.
* **`adaptive-multimodal-hci-repo-structure.md`**: Repository Architecture and codebase layout specification.
* **`adaptive-multimodal-hci-sdlc-spiral.md`**: Risk-driven 7-spiral development lifecycle mapping Boehm's 4-quadrant framework to the revised architecture and milestone acceptance gates.
* **`adaptive-multimodal-hci-implementation-plan.md` (DOC4)**: High-level engineering roadmap, deliverable matrix, and test verification suite.
* **`Proposed_Innovations.md`**: Deep dive into scientific contributions, comparison tables, and state-of-the-art positioning.
* **`literature-review-and-methodology.md`**: Exhaustive literature synthesis and theoretical foundations.

### 2.2 Tier 2: Subsystem API Reference Manuals (`docs/api/`)
* `perception_api.md`: Function signatures, parameters, and return types for FaceMesh, SolvePnP, Hands, Holt-Winters filter, and Gaze Dwell Tracker.
* `gesture_api.md`: Token dictionary definitions, feature classification schemas, and confidence scoring.
* `arbiter_api.md`: Rolling device activity monitoring flags and priority arbitration logic contracts.
* `calibration_api.md`: API contracts for wizard state transitions, geometry fitting, and profile synthesis (incl. Phase D REST pose).
* `decision_api.md`: Interfaces for Stage 3A Command Composer, Stage 3B safety gatekeeper, and Stage 3C action dispatcher with keyboard handoff.
* `feedback_api.md`: Contracts for temporal state machine, ring buffer management, and 5 negative sub-detectors.
* `assessment_api.md`: Interfaces for Engine 5A metrics engine, Engine 5B learning gatekeeper, and report generator.
* `learning_api.md`: Parameters for micro-SGD updater, simplex bisection solver, macro state machine, and Wald SPRT.

### 2.3 Tier 3: User & Developer Guides (`docs/guides/`)
* `user_manual.md`: Installation steps, webcam positioning, desktop gesture dictionary, and HUD explanation.
* `calibration_guide.md`: Step-by-step walkthrough of the 5-phase onboarding wizard (gaze target fixation, neutral pose hold, gesture sample).
* `developer_guide.md`: Development setup, coding standards, branch conventions, running unit tests, and adding custom gestures.
* `deployment_guide.md`: Packaging scripts, Windows/Linux OS permission setup (accessibility/keystroke hooking), and installer creation.

### 2.4 Tier 4: Mathematical Formulations & Proofs (`docs/math/`)
* `simplex_projection_proof.md`: Formal derivation and proof of convergence for the 1D dual bisection box-constrained simplex root-finding algorithm.
* `wald_sprt_derivation.md`: Mathematical derivation of sequential log-likelihood decision boundaries ($A = 2.89, B = -2.25$) under Type I/II error tolerances ($\alpha = \beta = 0.05$).
* `uncertainty_propagation_model.md`: Complete derivation of the unified global update confidence $C_{\text{update}}$ from sensor covariance to learning rate scaling.

---

## 3. Academic Publication & Preprint Package (`paper/`)

The repository includes a complete, self-contained academic manuscript package formatted in standard double-column IEEE/ACM conference style (DOC5):

```
paper/
├── main.tex                            # Root LaTeX document compiling to full paper PDF
├── references.bib                      # Complete BibTeX bibliography (HCI & ML citations)
├── ieee_conference.cls                 # Standard conference LaTeX document class
├── sections/                           # Modular section source files
│   ├── 01_abstract.tex                 # 250-word structured abstract & keywords
│   ├── 02_introduction.tex             # Problem statement, motivation, and contributions
│   ├── 03_related_work.tex             # Literature review (Multimodal HCI, Online Adaptation)
│   ├── 04_system_architecture.tex      # Six-Layer decomposition & pipeline design
│   ├── 05_online_adaptation_engine.tex # Micro SGD & box simplex projection algorithms
│   ├── 06_runtime_assessment_engine.tex# Dual-engine RAE, health metrics & gatekeeper rules
│   ├── 07_empirical_evaluation.tex     # Latin Square within-subjects user study methodology
│   ├── 08_results_and_analysis.tex     # Quantitative KPIs, NASA-TLX, and LME models
│   ├── 09_discussion_and_limitations.tex# Real-world viability, failure modes & edge cases
│   └── 10_conclusion.tex               # Summary of findings & future research directions
├── figures/                            # Publication-grade vector PDF figures (300+ DPI)
│   ├── fig1_system_architecture.pdf    # Master closed-loop 6-layer architecture diagram
│   ├── fig2_decision_sequence.pdf      # End-to-end interaction lifecycle sequence chart
│   ├── fig3_convergence_curves.pdf    # Parameter weight trajectories across 50 interactions
│   ├── fig4_error_rate_comparison.pdf  # False Activation / Rejection Rate boxplots (A vs B)
│   └── fig5_sprt_trajectory.pdf        # Wald SPRT sequential log-likelihood drift traces
└── tables/                             # LaTeX formatted tables
    ├── tab1_latency_breakdown.tex      # Component latency budgets vs empirical measurements
    ├── tab2_quantitative_results.tex   # FAR, FRR, TCT, and Correction Rate benchmarks
    └── tab3_subjective_scores.tex      # SUS (0-100) and Raw NASA-TLX workload dimensions
```

---

## 4. Empirical Evaluation, Instruments & Replication Package (`evaluation/`)

To support open-science replication and rigorous peer review, the repository contains all experimental protocols, psychometric instruments, and analysis notebooks:

```
┌────────────────────────────────────────────────────────────────────────┐
│               EMPIRICAL EVALUATION & REPLICATION SUITE                 │
├────────────────────────────────────────────────────────────────────────┤
│  • Human-Subject Protocols (`evaluation/protocols/`)                   │
│  • Standardized Survey Instruments (`evaluation/instruments/`)         │
│  • Automated Task Sequences (`evaluation/tasks/`)                      │
│  • Pre-Recorded Benchmark Traces (`data/benchmark_traces/`)           │
│  • Statistical Analysis & Figures Notebooks (`notebooks/`)             │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Human-Subject Study Protocols (`evaluation/protocols/`)**:
   - `study_protocol.md`: Complete within-subjects counterbalanced ($A \to B$ vs. $B \to A$) experimental procedure ($N = 4\text{--}6$), 5-minute washout period, and environment setup.
   - `participant_briefing.md`: Standardized verbal onboarding script and informed consent template.
   - `latin_square_order.json`: Randomized counterbalance order assignment table.
2. **Psychometric Instruments (`evaluation/instruments/`)**:
   - `sus_questionnaire.md`: 10-item System Usability Scale instrument with standard 1–5 Likert scoring.
   - `nasa_tlx_survey.md`: Raw NASA-TLX instrument evaluating 6 workload subscales (Mental, Physical, Temporal, Performance, Effort, Frustration).
   - `adaptation_experience_scale.md`: Custom 7-item 7-point Likert scale evaluating perceived adaptation smoothness, predictability, and recovery fluency.
3. **Isomorphic Task Automation (`evaluation/tasks/`)**:
   - `task1_document_navigation.py`: Multi-page PDF/document scrolling and targeted paragraph dwell tasks.
   - `task2_window_management.py`: Browser tab switching, window resizing, and application switching.
   - `task3_media_player_control.py`: Media play/pause, scrub, volume adjustment, and Tier-2 application close.
4. **Interactive Jupyter Analysis Notebooks (`notebooks/`)**:
   - `01_latency_and_framerate_profiling.ipynb`: Generates frame cycle latency histograms, CDF plots, and CPU/memory profiling charts.
   - `02_calibration_geometry_analysis.ipynb`: Evaluates 95% posture ellipsoid fit quality and 5-point gaze affine RMSE residuals.
   - `03_adaptation_convergence_curves.ipynb`: Visualizes per-action weight evolution $\mathbf{w}_a(t)$, threshold adaptation $\theta_a(t)$, and EWMA $AG_t$.
   - `04_sprt_drift_detection_and_recovery.ipynb`: Plots Wald SPRT log-likelihood trajectories $S_m$ under simulated lighting and posture drift.
   - `05_empirical_user_study_statistical_lme.ipynb`: Performs Wilcoxon Signed-Rank tests, computes Cohen's $d$, and fits Linear Mixed-Effects models.

---

## 5. Deliverable Packaging & Release Manifest (`deliverables/`)

Every Core Deliverable (D1–D5) and Research Enhancement (E1–E3) has a dedicated release bundle directory containing package metadata, invariant sign-off sheets, and verification test logs:

| Deliverable ID | Release Bundle Path | Scope & Verification Invariant Summary | Release Artifacts |
|---|---|---|---|
| **D1** | `deliverables/D1_perception_pipeline/` | Layer 1 perception pipeline; latency $\le 20.5\text{ms}$, jitter $\le 1.2\text{px}$. | Invariant test log, latency benchmark report. |
| **D2** | `deliverables/D2_fusion_engine/` | Layer 3A fuser & exact simplex solver ($\sum w_i = 1.0, w_i \in [0.05, 0.85]$). | Simplex mathematical proof, unit test logs. |
| **D3** | `deliverables/D3_calibration_wizard/` | Layer 2 onboarding wizard ($\le 90\text{s}$ duration, gaze $\text{RMSE} \le 45\text{px}$). | 5-phase validation log, sample `Profile v1`. |
| **D4** | `deliverables/D4_feedback_observer/` | Layer 3B safety gate (600ms dwell) & Layer 4 5-detector observer. | Sub-detector precision matrix, undo hook test log. |
| **D5** | `deliverables/D5_runtime_assessment/` | Layer 5 dual RAE ($AG, LV, WSI, ACI, ECE, RR, DRT$ & 6 gatekeeper rules).| Gatekeeper outlier rejection logs, sample session report.|
| **E1** | `deliverables/E1_dual_scale_engine/` | Layer 6 micro SGD, macro epoch state machine, and Wald SPRT ($S_m \ge 2.89$).| Macro state transition logs, SPRT drift recovery trace.|
| **E2** | `deliverables/E2_explainability_hud/` | PyQt6 semi-transparent HUD overlay; render overhead $\le 1.0\text{ms}$ ($\le 2\%$ CPU).| HUD render latency benchmarks, video demo clip. |
| **E3** | `deliverables/E3_research_dashboard/` | Multi-tab PyQt6 GUI with live telemetry, SPRT gauge, and study runner.| Dashboard sync logs, GUI walkthrough recording. |
| **DOC1–5**| `docs/` & `paper/` | Proposal, SRS, Architecture, Plan, and LaTeX Conference Preprint. | Canonical Markdown documents & compiled `paper.pdf`.|

---

## 6. Convenience Build & Automation Tooling (`Makefile`)

The repository provides automated targets for developer workflow, testing, paper compilation, and benchmarking:

```makefile
.PHONY: help install test unit-test integration-test benchmark lint format paper clean

help:
	@echo "Adaptive Multimodal HCI - Master Development Commands:"
	@echo "  make install          - Install production and development dependencies"
	@echo "  make test             - Run complete automated test suite (Unit + Integration)"
	@echo "  make benchmark        - Run frame cycle latency & resource profiler"
	@echo "  make lint             - Run flake8 and mypy type checking"
	@echo "  make format           - Format codebase using black and isort"
	@echo "  make paper            - Compile LaTeX conference paper preprint to PDF"
	@echo "  make run              - Launch production application with Explainability HUD"
	@echo "  make dashboard        - Launch empirical research dashboard"

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

unit-test:
	pytest tests/unit/ -v

integration-test:
	pytest tests/integration/ -v

benchmark:
	python scripts/run_benchmarks.py

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/ scripts/
	isort src/ tests/ scripts/

paper:
	cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/
	cd paper && rm -f *.aux *.bbl *.blg *.log *.out *.toc *.synctex.gz
```

---

## 7. Master Traceability Matrix: Deliverables to Repository Assets

| Master Deliverable ID | Deliverable Category | Primary Codebase Assets | Documentation & Paper Assets | Test & Verification Modules |
|---|---|---|---|---|
| **D1** | Perception Pipeline | `src/capture/`, `src/perception/`, `src/gesture/` | `docs/api/perception_api.md`, `docs/api/gesture_api.md`, `docs/api/arbiter_api.md`, `paper/sections/04_system_architecture.tex` | `tests/unit/test_face_mesh_extractor.py`, `tests/unit/test_gesture_classifier.py`, `tests/unit/test_modality_arbiter.py`, `tests/benchmarks/test_frame_latency.py` |
| **D2** | Decision & Projection | `src/decision/command_composer.py`, `src/learning/simplex_projector.py` | `docs/math/simplex_projection_proof.md`, `paper/sections/05_online_adaptation_engine.tex` | `tests/unit/test_command_composer.py`, `tests/unit/test_tier0_intentionality_gate.py`, `tests/unit/test_simplex_projection.py` |
| **D3** | Calibration Wizard | `src/calibration/`, `src/storage/profile_store.py` | `docs/guides/calibration_guide.md`, `docs/api/calibration_api.md` | `tests/unit/test_calibration_geometry.py`, `tests/unit/test_variance_weight_init.py` |
| **D4** | Safety & Observation | `src/decision/safety_gatekeeper.py`, `src/decision/action_dispatcher.py`, `src/feedback/` | `docs/api/feedback_api.md`, `paper/sections/04_system_architecture.tex` | `tests/unit/test_feedback_state_machine.py`, `tests/unit/test_negative_sub_detectors.py`, `tests/integration/test_keyboard_handoff.py` |
| **D5** | Runtime Assessment | `src/assessment/`, `src/evaluation/` | `docs/api/assessment_api.md`, `paper/sections/06_runtime_assessment_engine.tex` | `tests/unit/test_runtime_metrics_engine.py`, `tests/unit/test_learning_gatekeeper.py` |
| **E1** | Dual-Scale Adaptation | `src/learning/` | `docs/math/wald_sprt_derivation.md`, `paper/sections/05_online_adaptation_engine.tex` | `tests/unit/test_macro_adaptation.py`, `tests/unit/test_wald_sprt_detector.py` |
| **E2** | Explainability HUD | `src/ui/explainability_hud.py` | `docs/guides/user_manual.md`, `paper/figures/fig1_system_architecture.pdf` | `tests/unit/test_explainability_hud.py`, `media/ui_mockups/` |
| **E3** | Research Dashboard | `src/ui/research_dashboard.py` | `docs/guides/developer_guide.md`, `notebooks/` | `tests/unit/test_research_dashboard.py`, `evaluation/` |
| **DOC1–5** | Master Documentation | `docs/`, `paper/` | `docs/adaptive-multimodal-hci-proposal.md`, `docs/adaptive-multimodal-hci-srs.md`, `paper/main.tex` | CI workflow `.github/workflows/paper-build.yml` |

---

## 8. Conclusion
This Base Repository Structure specification provides the complete, unambiguous architectural blueprint for the entire project ecosystem. By embedding first-class directories for academic publication (`paper/`), empirical user study protocols (`evaluation/`), reproducible research notebooks (`notebooks/`), formal deliverable sign-offs (`deliverables/`), and multi-tiered documentation (`docs/`), it ensures that every engineering, research, and documentation requirement is fully realized.
