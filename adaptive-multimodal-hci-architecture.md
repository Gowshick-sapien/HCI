# System Design: Adaptive Multimodal HCI Decision Engine

## 1. Requirements

### Functional
* Ingest webcam frames and extract face mesh, hand landmarks, and head pose per frame.
* Fuse per-modality confidence scores into a single action prediction with an overall confidence.
* Maintain a per-user calibration profile (gaze offset, gesture speed baseline, per-modality weights, per-action thresholds).
* Run a short calibration wizard for new users (~10–15 samples).
* Detect implicit feedback (undo/repeat = negative signal, action left in place = positive) and update weights online.
* Detect accuracy drift and prompt recalibration.
* Render an explainability HUD showing per-modality confidence for the last prediction.
* Execute predicted actions via OS automation.

### Non-Functional
* End-to-end decision latency: under ~100 ms per cycle (must feel real-time, not batchy).
* Must run on a standard laptop CPU, 8 GB RAM, no GPU assumed.
* Online weight update must not introduce visible lag (target: <5 ms per update).
* No cloud dependency; all learning and storage local.

### Constraints
* Single-semester timeline — favors interpretable, cheap-to-implement online learning over training a model from scratch.
* Python stack (OpenCV, MediaPipe, NumPy, PyAutoGUI).
* No large labeled dataset available or expected.

---

## 2. High-Level Design

### Component Diagram
```
┌─────────────┐     ┌────────────────────┐     ┌───────────────────────┐
│   Webcam    │────►│  Capture Thread     │────►│ MediaPipe Feature      │
│  (OpenCV)   │     │  (frame grab loop)  │     │ Extractor (Face/Hand/  │
└─────────────┘     └────────────────────┘     │ Head Pose)             │
                                                 └──────────┬─────────────┘
                                                            ▼
                                                 ┌───────────────────────┐
                        ┌───────────────────────►│ Feature Vector Buffer │
                        │                        │ (rolling smoothing)   │
                        │                        └──────────┬─────────────┘
                        │                                   ▼
              ┌─────────┴─────────┐              ┌───────────────────────┐
              │ Calibration Profile│◄────────────►│ Weighted Confidence   │
              │ Store (SQLite/JSON)│              │ Fusion + Decision     │
              └─────────┬─────────┘              │ Engine (online update)│
                        ▲                         └──────────┬─────────────┘
                        │                                    ▼
              ┌─────────┴─────────┐              ┌───────────────────────┐
              │ Feedback Detector  │◄─────────────│ Action Executor       │
              │ (undo/repeat watch)│              │ (PyAutoGUI)           │
              └────────────────────┘              └──────────┬─────────────┘
                                                              ▼
                                                    ┌───────────────────────┐
                                                    │ Explainability HUD    │
                                                    │ (Tkinter/PyQt overlay)│
                                                    └───────────────────────┘
```

### Data Flow
Frame → feature extraction → smoothing buffer → fusion/decision (reads + writes calibration profile) → action execution → feedback detector observes the outcome → writes an implicit label back into the decision engine's online updater → calibration profile updated.

### Internal API Contracts
```python
FeatureExtractor.extract(frame) -> FeatureVector
    # FeatureVector: gaze_target, head_pose(yaw,pitch,roll), gesture_label, gesture_confidence

DecisionEngine.predict(feature_vector, profile) -> (action, confidence, per_modality_scores)

DecisionEngine.update(action, feedback_signal, profile) -> updated_profile
    # feedback_signal: {POSITIVE, NEGATIVE, NEUTRAL}

ProfileStore.load(user_id) -> CalibrationProfile
ProfileStore.save(user_id, profile) -> None
```

### Storage Choice
A local SQLite file (or flat JSON for a single-user prototype) holding one row/document per user profile. No need for a full database server — profile size is a handful of floats plus timestamps.

---

## 3. Deep Dive

### Data Model: CalibrationProfile
```
user_id
gaze_offset_x, gaze_offset_y
gesture_speed_baseline
head_pose_tolerance (yaw_range, pitch_range)
modality_weights: {gaze: w1, head: w2, hand: w3}   # per action, or global
action_thresholds: {open_app: t1, scroll: t2, ...}
correction_rate_window: rolling list of recent feedback outcomes
last_calibrated_at
```

### Decision Engine Design
* Fusion score = `w_gaze * conf_gaze + w_head * conf_head + w_hand * conf_hand`, weights sum to 1, initialized from the calibration wizard.
* Action fires only if fusion score clears `action_thresholds[action]`.
* Online update: a perceptron-style nudge — on NEGATIVE feedback, decrease the threshold's associated weights (or raise the threshold) slightly; on POSITIVE feedback, reinforce slightly. Kept linear and bounded (clip weights to a sane range) so behavior stays interpretable and stable — deliberately not a full gradient-descent classifier, to keep it auditable and cheap.

### Feedback Signal Design
* NEGATIVE: action undone/reversed or the same gesture repeated within ~1.5s (implies the first attempt didn't register as intended).
* POSITIVE: action persists with no immediate reversal or repeat.
* NEUTRAL: ambiguous cases (e.g., user idle) — no update.

### Buffering / Smoothing
A rolling buffer of ~10–15 frames per modality reduces jitter in gaze and gesture detection before fusion — avoids reacting to single noisy frames.

### Error Handling
* Low fused confidence → no-op plus a subtle HUD nudge, rather than a forced guess.
* Missing/occluded landmarks (hand out of frame, face turned away) → that modality's confidence drops to 0 and fusion relies on the remaining modalities.
* Capture thread crash or webcam disconnect → watchdog restarts capture without killing the whole process.

---

## 4. Real-Time Budget & Reliability

Single-device, real-time system — "scale" here means per-frame budget, not distributed load:

* Target 30 fps → ~33 ms/frame budget.
* MediaPipe face+hand+pose inference is the dominant cost; run capture and inference on separate threads/processes to avoid blocking the UI loop (mind Python's GIL — prefer multiprocessing for the CPU-bound MediaPipe calls, threading for I/O-bound capture).
* Online weight update is O(1) per feedback event — negligible cost.
* Reliability: watchdog on the capture thread; graceful degradation when a modality drops out; correction-rate logging doubles as both a drift signal and an evaluation metric.

---

## 5. Trade-off Analysis

| Decision | Chose | Trade-off |
|---|---|---|
| Learning approach | Lightweight linear/perceptron-style online update | Simple, fast, interpretable, easy to debug — vs. a full ML model, which would generalize better but is harder to train from sparse implicit feedback in one semester and harder to explain in the HUD |
| Fusion logic | Weighted confidence sum with per-user thresholds | Keeps the rule *skeleton* (so behavior stays predictable/explainable) while adapting weights — vs. a black-box classifier, which could fit better but loses explainability and cold-start behavior |
| Storage | Local file/SQLite | Simple, private, zero infra — vs. cloud sync, which would enable cross-device profiles but adds infra and privacy surface for no v1 benefit |
| Feedback source | Implicit (undo/repeat detection) | No extra UI burden on the user — vs. explicit "correct me" prompts, which are more reliable signals but interrupt the interaction being tested |
| Concurrency | Multiprocessing for MediaPipe, threading for capture | Avoids GIL contention on the CPU-bound part — vs. a single-threaded pipeline, which is simpler but risks missing the frame budget |

---

## 6. What I'd Revisit as This Grows

* Multi-user profile switching (face-ID-based profile selection) if deployed on a shared device.
* Swapping the linear fusion for a small neural fusion model once there's enough logged session data to justify it.
* If ever moved off a laptop CPU onto embedded/edge hardware (e.g., a Jetson or Coral-class accelerator), the feature-extraction stage is the part to offload first — it's the dominant per-frame cost.
* Federated/aggregate learning across devices if this ever needs to generalize faster for new users than per-user cold start allows.
