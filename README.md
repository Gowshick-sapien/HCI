# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction

> A real-time, non-intrusive Human-Computer Interaction (HCI) framework that personalizes multimodal decision policies (ocular gaze, head pose, hand gesture) via continuous implicit behavioral feedback and autonomous runtime self-evaluation.

---

## 1. Executive Summary

Traditional vision-based Multimodal Human-Computer Interaction (HCI) systems rely heavily on static, hand-tuned rules (e.g., fixed IF-THEN combinations of gaze and gesture). However, static thresholds fail to account for variance across users—such as differences in eye shape, corrective eyewear, gesture speed, seating posture, or ambient lighting.

This project introduces a **Self-Evaluating Adaptive Multimodal Decision Architecture**. Operating entirely on standard consumer CPU hardware via a single webcam, the system replaces static boolean rules with a **decoupled confidence fusion and safety reasoning engine** that personalizes decision boundaries and modality confidence weights per user through a fast initial calibration wizard (60–90 s) and continuous online learning from implicit interaction feedback (e.g., OS undos, directional reversals, and rapid retries), governed by a dedicated **Runtime Assessment Engine (RAE)**.

---

## 2. Complete Project Documentation Suite

```
                  ┌────────────────────────────────────────────────────────┐
                  │ Project Proposal                                       │
                  │ adaptive-multimodal-hci-proposal.md                    │
                  └───────────────────────────┬────────────────────────────┘
                                              │ Research Vision & Motivation
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │ Project Implementation Plan                            │
                  │ adaptive-multimodal-hci-implementation-plan.md         │
                  └───────────────────────────┬────────────────────────────┘
                                              │ Execution Roadmap & Verification
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │ System Architecture Specification                      │
                  │ adaptive-multimodal-hci-architecture.md                │
                  └───────────────────────────┬────────────────────────────┘
                                              │ Six-Layer Technical Design
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │ Codebase & Empirical Benchmarks                        │
                  │ src/, tests/, profiles/, logs/                         │
                  └────────────────────────────────────────────────────────┘
```

1. **[Project Proposal](file:///d:/HCI/adaptive-multimodal-hci-proposal.md)**: Research thesis, formal research questions (RQ1–RQ4), theoretical motivation, real-world application domains, and 5-stage empirical validation protocol.
2. **[Software Requirements Specification (SRS)](file:///d:/HCI/adaptive-multimodal-hci-srs.md)**: ISO/IEC/IEEE 29148 compliant specification detailing functional requirements (FR-1.1 to FR-9.5), performance budgets ($<29.5\text{ms}$), safety/privacy constraints, and verification traceability matrices.
3. **[Project Deliverables Specification](file:///d:/HCI/adaptive-multimodal-hci-deliverables.md)**: Exhaustive breakdown of Core Deliverables (D1–D5), Advanced Enhancements (E1–E3), data contracts, mathematical formulations, and acceptance criteria.
4. **[System Architecture Specification](file:///d:/HCI/adaptive-multimodal-hci-architecture.md)**: Exhaustive 6-layer design, decision lifecycle sequence diagram, decoupled Layer 3 sub-stages, global uncertainty propagation model, dual-engine Runtime Assessment Engine, dual-scale micro/macro adaptation, and profile schemas.
5. **[Project Implementation Plan](file:///d:/HCI/adaptive-multimodal-hci-implementation-plan.md)**: 4-week execution roadmap, D1–D5 and E1–E3 deliverables, automated test suite, counterbalanced A/B pilot study protocol, and risk mitigation strategies.
6. **[Proposed Technical Innovations](file:///d:/HCI/Proposed_Innovations.md)**: Deep dive into the core scientific contributions, comparison tables, and mathematical foundations.

---

## 3. The Six Principled Architectural Layers

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           THE SIX PRINCIPLED ARCHITECTURAL LAYERS                                │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [LAYER 1: PERCEPTION]      ──► Observes:     Extracts raw physical cues from webcam stream      │
│  [LAYER 2: CALIBRATION]     ──► Personalizes: Bootstraps user anatomy, noise variances & tempo   │
│  [LAYER 3: DECISION]        ──► Decides:      Fuses confidence, verifies safety & dispatches     │
│  [LAYER 4: OBSERVATION]     ──► Evaluates:    Monitors post-action user behavior via implicit cues│
│  [LAYER 5: ASSESSMENT]      ──► Validates:    Computes health metrics & gatekeeps updates        │
│  [LAYER 6: LEARNING]        ──► Learns:       Executes micro/macro SGD, simplex & profile store  │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Key Technical Capabilities

* **Variance-Informed Calibration Wizard (Layer 2)**: 60–90 second 5-phase onboarding protocol mapping 3D neutral posture ellipsoids $\mathcal{E}_{\text{head}}$, 5-point gaze affine transforms $\mathbf{M}_{\text{gaze}}$, personal reaction tempos $\tau_{\text{user}}$, and initializing noise-variance-weighted parameters (`Profile v1`).
* **Decoupled Decision & Safety Engine (Layer 3)**: Decoupled Stage 3A (Confidence Fusion), Stage 3B (Post-Decision Safety Reasoning with user-relative Tier-2 gates and 600ms visual dwell confirmation), and Stage 3C (OS Execution & Context Dispatch).
* **Asynchronous Implicit Feedback Observer (Layer 4)**: 4-window temporal state machine monitoring 5 negative sub-detectors (OS Undo, Directional Reversal, Rapid Retries, Window Dismissal, Physical Overrides) with continuous confidence decay $c_{fb}(\Delta t)$.
* **Dual-Engine Runtime Assessment (Layer 5)**:
  * *Engine 5A (Runtime Metrics)*: EWMA Adaptation Gain ($AG_t$), Learning Velocity ($LV_t$), Weight Stability Index ($WSI_t$), Adaptation Confidence Index ($ACI_t$), Expected Calibration Error ($ECE_t$), Recovery Rate ($RR$), and Drift Recovery Time ($DRT$).
  * *Engine 5B (Intelligent Gatekeeper)*: Multi-criteria validation engine enforcing sample floors, confidence floors, macro drift lockouts, contradiction resolution, and sensor noise checks.
* **Dual-Scale Online Adaptation (Layer 6)**: Micro-adaptation ($<1\text{ms}$ online SGD with 1D bisection box-constrained simplex projection) and macro-adaptation (periodic epoch re-estimation with `MERGE`, `FREEZE`, `DISCARD`, and `RECALIBRATE` policies, plus hierarchical Wald SPRT drift detection).
* **State-Aware Explainability HUD & Dashboard**: Live desktop overlay displaying real-time confidence breakdowns, dwell confirmation rings, and active system health state badges (`LEARNING`, `IMPROVING`, `STABLE`, `DRIFTING`, `RECOVERING`).

---

## 5. Repository Directory Layout

```
adaptive-multimodal-hci/
├── docs/
│   ├── adaptive-multimodal-hci-proposal.md            # Canonical Project Proposal
│   ├── adaptive-multimodal-hci-architecture.md        # Technical System Architecture
│   ├── adaptive-multimodal-hci-implementation-plan.md # Engineering Roadmap & Verification
│   └── Proposed_Innovations.md                        # Technical Innovations Deep-Dive
├── src/
│   ├── __init__.py
│   ├── main.py                          # Application entry point & pipeline coordinator
│   ├── capture/                         # Threaded frame acquisition
│   │   ├── __init__.py
│   │   └── video_stream.py
│   ├── perception/                      # Layer 1: Landmark extraction & smoothing
│   │   ├── __init__.py
│   │   ├── face_mesh_extractor.py
│   │   ├── hand_pose_extractor.py
│   │   ├── head_pose_estimator.py
│   │   └── holt_winters_filter.py
│   ├── calibration/                     # Layer 2: Calibration wizard & profile bootstrap
│   │   ├── __init__.py
│   │   ├── wizard_controller.py
│   │   └── profile_generator.py
│   ├── decision/                        # Layer 3: Fusion, safety reasoning & dispatch
│   │   ├── __init__.py
│   │   ├── confidence_fuser.py
│   │   ├── safety_gatekeeper.py
│   │   └── action_dispatcher.py
│   ├── feedback/                        # Layer 4: Implicit feedback observation
│   │   ├── __init__.py
│   │   ├── temporal_state_machine.py
│   │   └── sub_detectors.py
│   ├── assessment/                      # Layer 5: Runtime Assessment Engine (RAE)
│   │   ├── __init__.py
│   │   ├── runtime_metrics_engine.py
│   │   ├── learning_gatekeeper.py
│   │   └── session_report_generator.py
│   ├── learning/                        # Layer 6: Online SGD & macro adaptation
│   │   ├── __init__.py
│   │   ├── micro_sgd_optimizer.py
│   │   ├── simplex_projector.py
│   │   ├── macro_adaptation_engine.py
│   │   └── wald_sprt_detector.py
│   ├── storage/                         # Versioned ProfileSnapshot persistence
│   │   ├── __init__.py
│   │   └── profile_store.py
│   └── ui/                              # State-aware HUD & research dashboard
│       ├── __init__.py
│       ├── explainability_hud.py
│       └── research_dashboard.py
├── tests/                               # Comprehensive automated test suite
│   ├── test_simplex_projection.py
│   ├── test_layer3_decoupling.py
│   ├── test_feedback_state_machine.py
│   ├── test_runtime_metrics_engine.py
│   ├── test_learning_gatekeeper.py
│   └── test_macro_adaptation.py
└── profiles/                            # Local JSON/SQLite user profile repository
```

---

## 6. Verification & System Constraints

* **Platform Compatibility**: Windows 10/11, Linux, macOS
* **Python Runtime**: Python 3.11+
* **Dependencies**: OpenCV, MediaPipe, NumPy, SciPy, PyAutoGUI, PyQt6
* **Hardware Targets**: Standard consumer CPU, $\ge 8\text{ GB}$ RAM, standard 720p/1080p USB webcam. No dedicated GPU required.
* **Latency Guarantee**: Total end-to-end pipeline latency $< 30\text{ ms}$ ($\ge 30\text{ FPS}$ sustained throughput).
