# Adaptive Context-Aware Multimodal HCI System

> A real-time, personalized Human-Computer Interaction (HCI) framework combining eye focus, head pose orientation, and hand gesture tracking with lightweight online adaptation.

---

## 1. Executive Summary

Traditional vision-based Multimodal Human-Computer Interaction (HCI) systems rely heavily on static, hand-tuned rules (e.g., fixed IF-THEN combinations of gaze and gesture). However, static thresholds fail to account for variance across users—such as differences in eye shape, gesture speed, seating posture, or lighting.

This project introduces an **Adaptive Context-Aware Multimodal HCI System**. Operating entirely on standard consumer CPU hardware via a single webcam, the system replaces static boolean rules with a **weighted confidence fusion engine** that personalizes decision boundaries and confidence weightings per user through a fast initial calibration wizard (60--90 s) and continuous online learning from implicit interaction feedback (e.g., undo actions and rapid repeats).

---

## 2. Complete Project Documentation Suite

The repository features a complete, 4-tier engineering documentation package:

```
                  ┌────────────────────────────────────────────────────────┐
                  │ Project Proposal (v2)                                  │
                  │ adaptive-multimodal-hci-proposal.md                    │
                  └───────────────────────────┬────────────────────────────┘
                                              │ Motivation & Objectives
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │ Project Implementation Plan                            │
                  │ adaptive-multimodal-hci-implementation-plan.md         │
                  └───────────────────────────┬────────────────────────────┘
                                              │ Implementation & Roadmap
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │ System Architecture Specification                      │
                  │ adaptive-multimodal-hci-architecture.md                │
                  └───────────────────────────┬────────────────────────────┘
                                              │ Technical System Design
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │ Codebase & Evaluation Benchmarks                       │
                  │ src/, tests/, profiles/, logs/                         │
                  └────────────────────────────────────────────────────────┘
```

1. **[Project Proposal (v2)](file:///d:/HCI/adaptive-multimodal-hci-proposal.md)**  
   Explains the project vision, problem statement, research scope, baseline comparison methodology, and overall target outcomes.
2. **[Project Implementation Plan](file:///d:/HCI/adaptive-multimodal-hci-implementation-plan.md)**  
   Execution-focused engineering plan covering deliverables (D1–D5), stretch enhancements (E1–E3), deliverable traceability matrix, milestone completion criteria, and verification strategy.
3. **[System Architecture Specification](file:///d:/HCI/adaptive-multimodal-hci-architecture.md)**  
   Deep technical specification detailing component diagrams, frame data flow, API contracts, CalibrationProfile data schema, threading models, and trade-off analyses.

---

## 3. Core Subsystems

* **Multimodal Perception Layer**: Ingests video at 30+ FPS, extracting 3D head pose angles (solvePnP), eye gaze offsets, and hand gestures (MediaPipe Face Mesh & Hand Tracking) with temporal smoothing filters.
* **Weighted Confidence Decision Engine**: Converts modality features into normalized confidence scores (0.0--1.0) and fuses them using dynamic per-user weights. Includes a static rule-based baseline engine for control comparisons.
* **Calibration & User Profile Layer**: Provides a 60–90 second calibration wizard to bootstrap initial per-user gaze, posture, and gesture baselines, persisting parameters to disk (JSON/SQLite).
* **Adaptive Online Learning Engine (Stretch Goal)**: Nudges per-modality weights and activation thresholds in real time using a lightweight perceptron update rule driven by implicit user feedback.
* **System Interaction & Explainability Layer**: Dispatches OS desktop commands (PyAutoGUI), monitors implicit correction feedback (Ctrl+Z undo & rapid gesture repeats), and renders a live explainability HUD overlay.
* **Evaluation & Benchmarking Layer**: Logs interaction telemetry, runs standardized task scripts, and generates statistical graphs comparing baseline static rules vs. adaptive personalization.

---

## 4. Implementation Roadmap (Deliverables & Enhancements)

Development is structured into five Core Deliverables (Must Have) and three Stretch Enhancements (Optional Research Goals):

### Core Deliverables (Must Have)
* **[D1] Multimodal Perception Layer**: Real-time webcam frame acquisition, MediaPipe landmark extraction, and temporal feature buffer smoothing.
* **[D2] Weighted Confidence Decision Engine**: Multimodal confidence calculation, weighted score fusion, and single-modality dropout recovery.
* **[D3] Calibration & User Profile Layer**: Interactive setup wizard (60–90s) generating persistent user calibration profiles.
* **[D4] System Interaction Layer**: PyAutoGUI OS action execution and implicit feedback detection (undo / repeat watcher).
* **[D5] System Evaluation & Benchmarking Layer**: Automated telemetry logging, task script benchmarking, and final documentation packaging.

### Stretch Enhancements (Optional Research Goals)
* **[E1] Adaptive Online Learning Engine**: Real-time perceptron weight updates and continuous accuracy drift detection.
* **[E2] Explainability HUD Overlay**: Visual overlay rendering live per-modality confidence bars over desktop applications.
* **[E3] Advanced Statistical Benchmarking Suite**: Automated parsing of session logs and comparative error-curve plotting.

---

## 5. Repository Layout

```
adaptive-multimodal-hci/
├── docs/
│   ├── adaptive-multimodal-hci-proposal.md            # Project Proposal (v2)
│   ├── adaptive-multimodal-hci-architecture.md        # System Architecture Specification
│   └── adaptive-multimodal-hci-implementation-plan.md # Project Implementation Plan
├── src/
│   ├── __init__.py
│   ├── main.py                          # Application entry point & main loop
│   ├── capture/                         # Frame acquisition & worker thread
│   │   ├── __init__.py
│   │   └── capture_thread.py
│   ├── perception/                      # Landmark extraction & feature buffer
│   │   ├── __init__.py
│   │   ├── face_tracker.py
│   │   ├── hand_tracker.py
│   │   ├── head_pose.py
│   │   └── feature_buffer.py
│   ├── decision/                        # Fusion engine & confidence scoring
│   │   ├── __init__.py
│   │   ├── static_baseline.py
│   │   ├── confidence_calculators.py
│   │   └── fusion_engine.py
│   ├── adaptation/                      # Calibration & user profiles
│   │   ├── __init__.py
│   │   ├── calibration_wizard.py
│   │   ├── profile_store.py
│   │   ├── online_updater.py            # (Stretch Goal E1)
│   │   └── drift_detector.py            # (Stretch Goal E1)
│   ├── interaction/                     # Desktop actions & feedback
│   │   ├── __init__.py
│   │   ├── action_executor.py
│   │   ├── feedback_detector.py
│   │   └── explainability_hud.py        # (Stretch Goal E2)
│   └── evaluation/                      # Telemetry logging & benchmarking
│       ├── __init__.py
│       ├── logger.py
│       ├── benchmark_runner.py
│       └── eval_metrics.py              # (Stretch Goal E3)
├── tests/                               # Automated unit & integration tests
│   ├── test_perception.py
│   ├── test_decision.py
│   ├── test_adaptation.py
│   └── test_interaction.py
├── profiles/                            # Local storage for user calibration profiles
│   └── default_user.json
├── logs/                                # Telemetry logs from evaluation runs
├── requirements.txt                     # Dependencies (OpenCV, MediaPipe, NumPy, etc.)
└── README.md                            # Repository index & setup guide
```

---

## 6. System Requirements & Dependencies

### Hardware Requirements
* **Standard Webcam**: 720p or 1080p resolution operating at 30+ FPS.
* **Host Processor**: Standard Intel/AMD x86-64 or Apple Silicon ARM CPU (8 GB RAM minimum).
* **GPU**: None required—all perception and online learning run efficiently on CPU.

### Software Prerequisites
* **Operating System**: Windows 10/11, macOS 12+, or Linux (Ubuntu 20.04+).
* **Python**: Version 3.11 or higher.

### Installation & Dependencies
```bash
# Clone repository
git clone https://github.com/user/adaptive-multimodal-hci.git
cd adaptive-multimodal-hci

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

---

## 7. Quickstart Guide

1. **Launch Calibration Wizard**:
   ```bash
   python -m src.adaptation.calibration_wizard
   ```
2. **Run System (Core Interaction Mode)**:
   ```bash
   python src/main.py --profile default_user.json
   ```
3. **Run System (Baseline Evaluation Mode)**:
   ```bash
   python src/main.py --mode baseline
   ```

---

## 8. License & Citation

This project is developed as an advanced Human-Computer Interaction (HCI) capstone repository. All documentation and source code are open for academic and research reference.
