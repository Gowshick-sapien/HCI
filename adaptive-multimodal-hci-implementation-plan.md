# Project Implementation Plan (v2.3)

## Adaptive Context-Aware Multimodal Human-Computer Interaction System

---

## Document Metadata
* **Project Title**: Adaptive Context-Aware Multimodal Human-Computer Interaction System
* **Document Type**: Project Implementation Plan & Engineering Roadmap
* **Status**: Active / Definitive Baseline Specification (v2.3)
* **Target Environment**: Windows / macOS / Linux (Python 3.11+, Standard Webcam)

---

## 1. Project Overview

### Objective
The objective of this project is to build, validate, and benchmark a real-time, non-intrusive Human-Computer Interaction (HCI) system that combines vision-based eye focus, head pose orientation, and hand gesture tracking. The system personalizes decision thresholds and modality confidence weightings per user via online updates driven by implicit interaction feedback, operating efficiently on consumer CPU hardware without offline retraining.

### Key Architectural Pillars (v2.3)
1. **Decoupled Online SGD**: Online parameter adaptation that decouples weight updates (suppressed near decision boundaries to avoid jitter) from threshold updates (active across boundary events).
2. **Exact Box-Constrained Simplex Projection**: 1D bisection dual projection ensuring weights satisfy $\sum w_i = 1$ and $w_i \in [0.05, 0.85]$.
3. **Hierarchical Wald SPRT Drift Detection**: Per-action and global sequential probability ratio testing preventing spurious recalibrations while capturing genuine performance degradation.
4. **User-Relative Adaptive Safety Gating**: Tier-2 state-altering actions dynamically gated relative to the user's observed confidence distribution with minimum sample floors.
5. **Tiered Evaluation Strategy**: Feasibility-aligned $N=4\text{--}6$ within-subjects counterbalanced pilot for Core Deliverable (D5), with full Latin-Square $N=12\text{--}16$ LME study reserved for Stretch (E3).

---

## 2. Deliverables & Capabilities Breakdown

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CORE DELIVERABLES (MUST HAVE)                   │
├────────────────────────────────────────────────────────────────────────┤
│ • D1: Multimodal Perception Layer (MediaPipe FaceMesh, Hands, SolvePnP)│
│ • D2: Weighted Confidence Decision Engine + Box Simplex Projection    │
│ • D3: Calibration Wizard with Tempo Profiling & Local Profile Store    │
│ • D4: Tiered Safety Action Executor (Safe vs Relative Tier 2 + Undo)   │
│ • D5: Evaluation Pilot (N=4–6 Counterbalanced A/B + Wilcoxon Tests)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      STRETCH ENHANCEMENTS (OPTIONAL)                   │
├────────────────────────────────────────────────────────────────────────┤
│ • E1: Adaptive Online Engine (Decoupled SGD + Hierarchical SPRT)       │
│ • E2: Real-Time Explainability HUD Overlay (Confidence + Dwell Timers) │
│ • E3: Extended Statistical Study (N=12–16 Latin Square + LME Model)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Four-Week Execution Schedule

### Week 1: Core Perception & Mathematical Foundations (D1, D2)
* **Perception Pipeline (D1)**: Threaded video frame capture (30 FPS) with MediaPipe FaceMesh, Hand Tracking, and SolvePnP Head Pose.
* **Feature Vector Construction**: Normalized coordinates with rolling spatial-temporal smoothing filter.
* **Decision & Projection Layer (D2)**: Weighted confidence sum intent evaluator with exact 1D bisection box-constrained simplex projection.
* **Automated Unit Tests**: Validate projection invariants ($\sum w_i = 1, w_i \in [0.05, 0.85]$) and latency budgets ($<33\text{ms}/\text{frame}$).

### Week 2: Calibration, Safety Dispatcher & Feedback Capture (D3, D4)
* **Calibration Wizard (D3)**: 60–90 second interactive setup capturing gaze offsets, neutral posture, and natural tempo baseline.
* **Safety Dispatcher (D4)**: Tier 1 (safe/continuous) direct dispatch; Tier 2 (destructive) user-relative gating ($\mu_S + 1.5\sigma_S$, floor $\theta_a + 0.15$), 600ms visual dwell, and 3s grace-period undo stack.
* **Feedback Detector (D4)**: Explicit undo hotkey tracking, rapid directional reversal detection, and stability window ($T_{\text{stability}} = 1.8\text{s}$) watcher.

### Week 3: Adaptive Online Learning & Core Pilot Evaluation (E1, D5)
* **Adaptive Online Engine (E1)**: Decoupled SGD parameter updater ($g_{\text{weight}}$ ambiguity suppression, $g_{\text{thresh}}$ active boundary adaptation) and Hierarchical Wald SPRT drift detector.
* **Core Benchmark Pilot (D5)**: Within-subjects counterbalanced A/B evaluation ($N=4\text{--}6$) across isomorphic task scripts.
* **Statistical Analysis**: Compute FAR, FRR, TCT, and epoch correction rates with paired Wilcoxon signed-rank testing.

### Week 4: Explainability HUD, Documentation & Stretch Goals (E2, E3)
* **Explainability HUD (E2)**: Semi-transparent overlay displaying per-modality confidence bars, active drift status, and dwell timer circles.
* **Stretch Evaluation (E3)**: Optional expanded $N=12\text{--}16$ Latin Square study with NASA-TLX, SUS, and Linear Mixed-Effects analysis.
* **Deliverables Packaging**: Final project report, demo video, verified literature review, and code repository release.
