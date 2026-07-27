# Project Proposal (v2)

## Project Title
### Adaptive Context-Aware Multimodal Human-Computer Interaction System

---

## 1. Introduction

Human-Computer Interaction (HCI) has moved from keyboard-and-mouse control toward natural interaction using speech, gesture, and gaze. Combining multiple cues (multimodal interaction) is well established as more robust than any single modality — but most implementations, including v1 of this proposal, stop at a **static rule-based fusion engine**: fixed IF-THEN combinations of eye focus, head pose, and hand gesture.

That design is the part that makes the project feel generic — the vision pipeline (OpenCV + MediaPipe) is a commodity; dozens of student projects wire it up the same way. The genuinely interesting problem is what happens *after* feature extraction: how the system decides what a specific person meant, given that no two people gaze, gesture, or move their head the same way.

This v2 proposal keeps the multimodal foundation but replaces the static rule engine with an **adaptive, per-user learning engine** that personalizes its thresholds and confidence weighting over time using implicit feedback — no explicit "training mode," no large dataset, no deep learning from scratch.

---

## 2. Problem Statement

Rule-based multimodal fusion improves on single-modality interfaces, but it inherits a hidden assumption: that one fixed set of thresholds works for every user. In practice:

* Gaze estimation accuracy varies with eye shape, glasses, screen distance, and camera angle — a threshold tuned for one user misfires for another.
* Gesture "pinch" or "swipe" detection depends on hand size, speed, and personal habit — what one user does crisply, another does ambiguously.
* Head-pose tolerance for "facing screen" differs by posture and seating distance.

A static engine has exactly two ways to fail: it's too strict (real intents get rejected) or too loose (accidental activations) — and it can't be both right for everyone at once. The result is the same false-activation problem multimodal fusion was supposed to solve, just pushed one level up.

**Reframed problem**: build a multimodal interaction system whose decision boundaries *adapt to the individual user* over the course of normal use, without requiring an explicit calibration burden or a large training dataset.

---

## 3. What Makes This Version Different

| Common capstone version (v1) | This version (v2) |
|---|---|
| Fixed IF-THEN rules per action | Weighted, confidence-scored fusion with per-user weights |
| Same thresholds for every user | Short calibration wizard + continuous personalization |
| No notion of "wrong prediction" | Implicit feedback loop (undo/repeat = negative signal) |
| Black-box or nothing | Lightweight explainability HUD showing per-modality confidence |
| Static forever | Drift detection — recalibrates when accuracy silently degrades (lighting change, fatigue, new glasses) |

---

## 4. Proposed Solution

The system keeps the three input modalities (eye focus, head orientation, hand gesture) but changes the decision layer:

1. **Weighted confidence fusion** replaces boolean AND logic. Each modality contributes a confidence score (0–1); the fused score must clear a per-user, per-action threshold.
2. **Calibration wizard** (60–90 seconds, ~10–15 sample interactions) bootstraps a per-user profile: gaze offset, typical gesture speed, head-pose tolerance.
3. **Implicit feedback loop**: if a predicted action is immediately reversed (Ctrl+Z, closing what just opened, repeating the same gesture within ~1.5s), that's treated as a negative label. If the action is left in place, that's a mild positive label. No explicit "correct me" UI needed.
4. **Online weight update**: a simple, interpretable update rule (not a black-box model) nudges per-modality weights and thresholds after each labeled event — cheap enough to run every frame on a laptop CPU.
5. **Explainability HUD**: a small on-screen bar shows which modality drove a prediction and its confidence, so the user understands *why* something fired — which also improves the quality of their corrective feedback.
6. **Drift detection**: if the correction rate rises over a rolling window, the system flags a recalibration prompt instead of silently degrading.

---

## 5. Objectives

* Design a multimodal HCI system with eye focus, head orientation, and hand gesture inputs.
* Replace static fusion rules with a weighted, confidence-scored decision engine.
* Implement a short calibration wizard for per-user bootstrapping.
* Implement an implicit feedback loop and lightweight online weight update.
* Add an explainability HUD and drift detection.
* Demonstrate, quantitatively, that personalization reduces false activations/rejections versus the static-rule baseline over a session.

---

## 6. Scope

**In scope:**
* Real-time webcam-based interaction
* Vision-based feature extraction (MediaPipe)
* Weighted confidence fusion with per-user adaptive weights
* Lightweight online learning (linear/perceptron-style updates — not deep learning)
* Calibration wizard and drift detection
* Explainability HUD

**Out of scope (unchanged from v1, plus one addition):**
* Full eye-tracking hardware
* Deep learning model training from scratch
* Speech recognition
* Large-scale, cross-user intent prediction / cloud sync
* AR/VR interfaces
* Multi-user simultaneous profiles (noted as a future extension, not v1)

---

## 7. Methodology (Updated Workflow)

```
Webcam
   │
   ▼
Video Capture (OpenCV)
   │
   ▼
MediaPipe Processing (Face Mesh / Hand Tracking / Head Pose)
   │
   ▼
Feature Extraction  ──────────────►  Calibration Profile (per user)
   │                                          ▲
   ▼                                          │
Weighted Confidence Fusion  ◄─────────────────┘
   │
   ▼
Adaptive Decision Engine ──► Action Prediction + Confidence
   │
   ▼
Computer Action Execution
   │
   ▼
Implicit Feedback Detector (undo / repeat / accept)
   │
   ▼
Online Weight Update ──► back into Calibration Profile
```

---

## 8. System Features

* Real-time webcam input, hand gesture detection, face landmark detection, gaze/head-pose estimation
* Weighted multimodal confidence fusion (replacing boolean rules)
* Calibration wizard for new users
* Implicit feedback detection and online weight adaptation
* Drift detection with recalibration prompts
* Explainability HUD (per-modality confidence bars)
* Live visualization of landmarks and predicted actions

---

## 9. Technologies

| Category | Technology |
|---|---|
| Programming Language | Python |
| Computer Vision | OpenCV |
| Landmark Detection | MediaPipe |
| Numerical Processing | NumPy |
| Lightweight Online Learning | scikit-learn (`partial_fit`) or River (streaming ML) |
| Automation | PyAutoGUI |
| Local Profile Storage | SQLite / JSON |
| GUI / HUD | Tkinter or PyQt5 |
| Development Environment | VS Code |
| Version Control | Git & GitHub |

---

## 10. Hardware & Software Requirements

Unchanged from v1: standard webcam, 8 GB RAM, Windows/Linux/macOS, Python 3.11+, no specialized sensors.

---

## 11. Expected Outcomes

* A multimodal interaction system whose false-activation/false-rejection rate measurably decreases over a session as the engine personalizes.
* A working calibration + feedback loop, not just a fusion demo.
* A quantitative comparison (adaptive vs. static-rule baseline) on the same task set.
* An explainability HUD that makes the personalization visible and debuggable.

---

## 12. Applications

Touchless computer interaction, smart workstations, assistive technology (personalization matters most here — users with atypical gesture/gaze patterns are exactly who static thresholds fail), public kiosks, interactive presentations, industrial human-machine interfaces.

---

## 13. Evaluation Plan (New)

* Baseline run: static-rule engine (v1 logic) on a fixed task script (open app, scroll, play/pause, switch window) — log false positives/negatives.
* Adaptive run: same task script and same users, adaptive engine active — log the same metrics over the session and plot correction rate over time.
* Success criterion: correction rate trends downward within a session and is lower than the static baseline by a defined margin.

---

## 14. Future Enhancements

* Multi-user profile switching on shared devices
* Context-mode profiles (e.g., "coding" vs. "media" thresholds) learned automatically from active application
* Swap the linear/perceptron fusion for a small neural fusion model once enough session data exists
* Voice command as a fourth modality
* On-device acceleration (e.g., a small edge accelerator) if moved to embedded hardware

---

## 15. Deliverables

* Functional adaptive multimodal HCI prototype
* Source code repository
* System architecture documentation (see companion architecture doc)
* Baseline-vs-adaptive evaluation results
* Demonstration video
* Final project report and presentation slides

---

## 16. Conclusion

Combining eye focus, head pose, and hand gesture is no longer a novel idea on its own — the fusion logic is. Making that fusion **adapt to the individual user through implicit feedback**, rather than relying on fixed thresholds, is what turns this from "another MediaPipe demo" into a system that gets measurably better the more a specific person uses it, while staying small enough to build and evaluate in a single semester.
