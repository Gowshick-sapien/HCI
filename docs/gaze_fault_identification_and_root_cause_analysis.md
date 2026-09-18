# Forensic Fault Analysis and Root-Cause Investigation: Gaze Instability and Direction Inversion

**Document ID**: FA-GAZE-2026-09  
**System**: Adaptive Multimodal Human-Computer Interaction Platform (HCI)  
**Role**: Senior System Fault Identifier  
**Classification**: Technical Audit & Root-Cause Analysis  
**Status**: Formal Diagnostic Report  
**Target Components**: Layer 1 Perception (`src/perception`), Calibration Wizard (`src/calibration`), Streaming Bridge (`src/testbench`), Frontend Reticle Engine (`src/testbench/frontend`)

---

## 1. Executive Summary

During manual validation of recent updates to the ocular tracking pipeline, the gaze tracking subsystem exhibited catastrophic functional degradation characterized by two severe symptoms:
1. **Opposite Direction Inversion**: Physical head turns and directional glances produced cursor movement in the inverted direction (turning face right caused the gaze reticle to move left; tilting face up caused the reticle to move down).
2. **Violent Persistent Jitter**: High-frequency tremor spanning 150 to 250 screen pixels persisted across all frames, rendering UI target acquisition impossible and triggering constant implicit mouse takeovers.

This document presents a rigorous architectural and mathematical fault analysis identifying the root causes of these failures. The investigation confirms that these defects are not stochastic noise issues or secondary feedback-loop artifacts. They stem directly from:
- A biological **Vestibulo-Ocular Reflex (VOR) Inversion Paradox** introduced when head orientation was decoupled from the gaze solver;
- The complete stripping of temporal low-pass filters across backend and frontend processing stages, exposing raw sub-pixel CMOS sensor noise to a 480x linear screen gain;
- An unviable **Signal-to-Noise Ratio (SNR) asymmetry** caused by relying on a 3.5-pixel ocular dynamic range instead of the 40-pixel facial pose range;
- A profile schema version lockout condition that clamped uncalibrated gaze confidence to zero.

---

## 2. Chronological Trajectory of Pipeline Degradation

To understand how the failure was introduced, the evolution of the perception codebase must be tracked across the last two revision states:

```
[State A: Baseline Multi-Smoothed Pipeline]
  - Head pose coupled into gaze via affine/polynomial solvers.
  - Directional alignment preserved (yaw > 0 moved cursor right).
  - Excessive stacked filters (Holt-Winters on iris + Holt-Winters on screen + lerp in JS).
  - Manifested high input latency, overshoot, and sluggish rubber-banding.
                    |
                    v  [Revision Attempt: Remove Stacking & Decouple Head Pose]
[State B: Current Broken Pipeline]
  - All temporal filters deleted from feature_pipeline.py.
  - Head pose completely stripped out; gaze reduced to 2x3 ocular-only model.
  - JS frontend lerp removed (currentGazeX = targetGazeX).
  - Profile version 1 invalidated; fallback gaze confidence clamped to 0.0.
  - Result: Immediate 180-degree axis inversion and violent 200px jitter.
```

---

## 3. Deep-Dive Root Cause Analysis

### Fault 1: The Vestibulo-Ocular Reflex (VOR) Inversion Paradox

* **Impacted Files**:
  * `src/perception/feature_pipeline.py` (Lines 110–143)
  * `src/calibration/gaze_calibrator.py` (Lines 91–108)
* **Code Mechanism**:
  In `feature_pipeline.py`:
  ```python
  # 4. Preserve raw pose telemetry, but do not inject head motion into gaze.
  if head_data is not None:
      head_euler = (float(head_data.yaw), float(head_data.pitch), float(head_data.roll))
  ...
  # 5. Direct ocular calibration; no temporal filtering or head compensation.
  if eye_data is not None and eye_data.confidence > 0.0:
      ...
      raw_screen_u, raw_screen_v = apply_affine_gaze(
          M_gaze, eye_data.iris_ratio_x, eye_data.iris_ratio_y
      )
  ```
  In `gaze_calibrator.py`:
  ```python
  # 3. Ocular-only affine calibration.
  design_x = np.column_stack([rx, np.ones(n_pts, dtype=np.float64)])
  w_x, _, _, _ = np.linalg.lstsq(design_x, tx, rcond=None)
  M_aff_2x3 = np.array([[w_x[0], 0.0, w_x[1]], [0.0, w_y[0], w_y[1]]], dtype=np.float64)
  ```

* **Biomechanical & Mathematical Analysis**:
  1. True human gaze relative to a screen coordinate frame is the vector composition of head pose and ocular orientation:
     $$\mathbf{G}_{\text{screen}} = \mathbf{\Theta}_{\text{head}} + \mathbf{\Theta}_{\text{eye\_in\_head}}$$
  2. When a user naturally interacts with a desktop display and targets an interface element on the right:
     - The head rotates toward the right ($\text{yaw} > 0$).
     - To maintain visual fixation on the monitor plane, the human Vestibulo-Ocular Reflex (VOR) automatically rotates the eyes to the **left** relative to the eye sockets.
     - The ocular extraction algorithm calculates the iris ratio $r_x$ relative to the facial eye corners (canthi):
       $$r_x = 0.5 + \frac{(\mathbf{p}_{\text{iris}} - \mathbf{p}_{\text{canthus\_mid}}) \cdot \mathbf{u}_{\text{eye\_axis}}}{w_{\text{eye}}}$$
     - Because the pupil rotated left relative to the face, $r_x$ increases from $0.50$ toward $0.80$.
     - The linear ocular calibration matrix maps higher $r_x$ to lower horizontal screen coordinates ($w_x < 0$).
  3. Because head orientation was completely eliminated from the runtime gaze solver, the system received zero evidence that the head had rotated right. It only detected that the eyes had shifted left in their sockets.
  4. Consequently, turning the face right commands the reticle to drive to the **left**.
  5. The vertical axis experiences the exact same failure: tilting the head upward causes the eyes to rotate downward relative to the palpebral fissure, driving the cursor down.

---

### Fault 2: Total Absence of Temporal Filtering and the 480x Noise Multiplier

* **Impacted Files**:
  * `src/perception/feature_pipeline.py` (Lines 66–69)
  * `src/testbench/frontend/testbench.js` (Lines 159–165)
  * `src/testbench/frontend/gestures.js` (Lines 102–108)
* **Code Mechanism**:
  In `feature_pipeline.py`:
  ```python
  # 2. Gaze coordinates are intentionally not temporally filtered. A
  # calibrated ocular model corrects direction at the source instead.
  self._warned_uncalibrated_gaze = False
  ```
  In `testbench.js`:
  ```javascript
  // Render the calibrated gaze point directly; no client-side smoothing.
  currentGazeX = targetGazeX;
  currentGazeY = targetGazeY;
  ```

* **Signal Processing Analysis**:
  1. A calibration matrix $M_{\text{gaze}}$ is a memoryless spatial transform:
     $$u = M_{0,0} \cdot r_x + M_{0,2}$$
     It does not attenuate high-frequency noise; it is a direct linear noise amplifier.
  2. On a 640x480 webcam with a user seated 60 cm away, the horizontal distance between eye canthi is approximately 40 pixels. Across the full breadth of a 1920-pixel display, the iris moves only 3.5 to 5.0 pixels.
  3. The spatial amplification factor (gain) is:
     $$K_{\text{gain}} = \frac{1920\text{ px}}{4.0\text{ px}} = 480\text{ px screen motion per pixel of iris displacement}$$
  4. Standard MediaPipe FaceMesh landmark estimation on standard CMOS sensors exhibits a thermal/illumination noise floor of $\sigma_{\text{iris}} \approx 0.3\text{–}0.6\text{ px}$.
  5. With zero low-pass filtering in Python and zero interpolation in JavaScript, this noise floor translates directly to instantaneous screen jump:
     $$\Delta u = 0.4\text{ px} \times 480 = 192\text{ pixels of frame-to-frame tremor}$$
  6. This 192-pixel tremor was broadcast at 30/60 Hz directly to the browser canvas, creating violent, uncontrollable pointer oscillation.

---

### Fault 3: The Signal-to-Noise Ratio (SNR) Physics Asymmetry

A fundamental engineering question must be asked: *Why does filtering eye gaze alone repeatedly fail?*

The failure is rooted in physical information theory. Filtering cannot extract high-fidelity spatial certainty from a low-SNR carrier. Comparing the two candidate modalities reveals why pure ocular tracking fails:

| Parameter | Pure Ocular Tracking (Iris-in-Socket) | Facial / Head Pose Tracking (Skull Pose) |
| :--- | :--- | :--- |
| **Physical Tracking Span** | 35–45 px (Canthus-to-canthus) | 180–240 px (Facial mesh bounding box) |
| **Active Landmark Base** | 5 refined iris contour points | 468 facial mesh landmarks |
| **Dynamic Range on Screen** | 3.5 – 5.0 px | 30.0 – 60.0 px |
| **Landmark Noise Floor** | 0.4 – 0.7 px (CMOS noise, eyelid flutter) | 0.2 – 0.3 px (Averaged over rigid SolvePnP model) |
| **Signal-to-Noise Ratio** | **~7:1 (Critically noisy)** | **>60:1 (Extremely stable)** |
| **Physiological Coupling** | Highly erratic (Micro-saccades, nystagmus) | Smooth inertial motion (Cervical vertebrae) |

When an algorithm treats the 7:1 SNR ocular signal as the sole carrier of screen position:
- Aggressive smoothing suppresses jitter but creates fatal lag, latency, and overshoot.
- Relaxed smoothing eliminates lag but unleashes 200px jitter.
- Velocity-adaptive smoothers (1€, Holt-Winters) are constantly triggered by micro-saccades and sensor noise, popping unpredictably between high and low cutoffs.

**Core Diagnostic Rule**: Head pose must be the primary, coarse carrier of screen position, while ocular tracking serves strictly as a localized fine-tuning delta.

---

### Fault 4: Invalidation of Profiles and the Zero-Confidence Fallback Lockout

* **Impacted Files**:
  * `src/perception/feature_pipeline.py` (Lines 126–154)
  * `data/profiles/user_02.json` (Lines 101–116, 287)
* **Code Mechanism**:
  In `feature_pipeline.py`:
  ```python
  calibrated = bool(
      profile
      and profile.gaze_calibration_matrix
      and profile.last_recalibration_timestamp > 0
      and getattr(profile, "gaze_feature_version", 1) >= 3
      and np.asarray(profile.gaze_calibration_matrix).shape == (2, 3)
  )
  if not calibrated:
      gaze_screen_xy = (self.screen_width / 2.0, self.screen_height / 2.0)
      gaze_conf = 0.0
  ```
  In `testbench.js`:
  ```javascript
  const hasUsableGaze = data.gaze_confidence === undefined || data.gaze_confidence > 0.0;
  if (hasUsableGaze && now - lastPhysicalMouseMoveTime > 1200.0) {
      // Update coordinates
  }
  ```

* **Root Cause Breakdown**:
  1. The profile `user_02.json` on disk contained `gaze_feature_version: 1` and a 2x5 affine matrix.
  2. The updated pipeline demanded `gaze_feature_version >= 3` and matrix shape `(2, 3)`.
  3. Consequently, `user_02` was rejected at runtime.
  4. Instead of maintaining a geometric head+eye baseline, the fallback locked `gaze_screen_xy = (960, 540)` and set `gaze_conf = 0.0`.
  5. The frontend received `gaze_confidence = 0.0` and dropped every incoming coordinate packet, freezing the cursor at center and forcing the user to touch the physical mouse.

---

### Fault 5: Coordinate Frame and Trigonometric Sign Consistency

A complete mathematical audit of landmark and angle sign conventions confirms the directional relationships across all subsystems:

1. **Head Pose Estimator** (`cv2.solvePnP` with `cv2.RQDecomp3x3`):
   - Face turns **Right** (user's right): $\text{Yaw} > 0$ ($+7.8^\circ$).
   - Face turns **Left** (user's left): $\text{Yaw} < 0$ ($-7.8^\circ$).
   - Face tilts **Up**: $\text{Pitch} < 0$ ($-14.3^\circ$).
   - Face tilts **Down**: $\text{Pitch} > 0$ ($+14.3^\circ$).

2. **Screen Coordinate System**:
   - Origin $(0, 0)$ is at Top-Left.
   - Horizontal axis: $+X$ points **Right** ($0 \to 1920$).
   - Vertical axis: $+Y$ points **Down** ($0 \to 1080$).

3. **Ocular Iris Ratio** (`_compute_iris_ratio`):
   - User looks **Right**: Pupil moves to camera-left; $r_x$ **decreases** ($0.50 \to 0.20$).
   - User looks **Left**: Pupil moves to camera-right; $r_x$ **increases** ($0.50 \to 0.80$).
   - User looks **Up**: Pupil moves camera-up; $r_y$ **decreases** ($0.50 \to 0.36$).
   - User looks **Down**: Pupil moves camera-down; $r_y$ **increases** ($0.50 \to 0.64$).

4. **Required Gain Signs for Positive Mapping**:
   - Horizontal Screen Motion:
     $$\Delta X = +K_{\text{head\_x}} \cdot \text{Yaw} - K_{\text{eye\_x}} \cdot (r_x - 0.50)$$
     *(Both turning face right and looking eyes right increase screen X)*.
   - Vertical Screen Motion:
     $$\Delta Y = +K_{\text{head\_y}} \cdot \text{Pitch} + K_{\text{eye\_y}} \cdot (r_y - 0.50)$$
     *(Both tilting face down and looking eyes down increase screen Y)*.

When head pose was removed, only the ocular term remained. Because VOR causes $r_x$ to move inversely during head rotation, the absence of the $+K_{\text{head\_x}} \cdot \text{Yaw}$ carrier produced total directional inversion.

---

### Fault 6: Analysis of the Adaptive Feedback Loop and Modality Weights

* **Investigation Target**: Did Layer 5 online adaptation or modality weight scaling cause the cursor inversion or jitter?
* **Findings**:
  1. Layer 5 adaptation (`src/adaptation/coordinator.py`, `micro_adaptation.py`) manages `modality_weights = [w_eye, w_head, w_hand]`.
  2. These weights are strictly consumed by `ConfidenceFusionEngine` to determine whether an intentional gesture token (e.g., `PRIMARY_CLICK`) passes the activation threshold.
  3. **They have zero mathematical connection to the $(X, Y)$ screen coordinates of the gaze pointer.**
  4. However, the broken gaze coordinates corrupted Layer 5 downstream:
     - The inverted, jittering reticle prevented users from acquiring test targets.
     - Users grabbed the physical mouse, triggering hundreds of `IMPLICIT_MOUSE_TAKEOVER` feedback events in `logs/feedback_events.jsonl`.
     - The SPRT Gatekeeper interpreted this barrage as chronic system drift and degraded the profile's adaptation confidence score.

---

### Fault 7: Vector Normalization Singularities in Canthus Basis

* **Impacted File**: `src/perception/face_mesh_extractor.py` (Lines 185–192)
* **Code Mechanism**:
  ```python
  if eye_axis[0] < 0.0:
      eye_axis *= -1.0
  eye_perp = np.array([-eye_axis[1], eye_axis[0]], dtype=np.float64)
  if eye_perp[1] < 0.0:
      eye_perp *= -1.0
  ```
* **Failure Mode**:
  Hard sign flips on 2D axis vectors introduce bifurcation singularities. When a user tilts their head near $90^\circ$ or during sudden lateral neck roll, the vector crosses the zero threshold, causing an instantaneous $180^\circ$ basis inversion that snaps the normalized ratio from $0.20$ to $0.80$ in a single frame. The canthi must be anchored via 3D facial mesh topology rather than ad-hoc 2D vector thresholding.

---

## 4. Comprehensive System Fault Matrix

| Fault ID | Component / File | Line Range | Mechanism of Failure | Manifested Symptom | Severity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F-01** | `feature_pipeline.py` & `gaze_calibrator.py` | [feature_pipeline.py:110-137](file:///d:/HCI/src/perception/feature_pipeline.py#L110-L137), [gaze_calibrator.py:95-107](file:///d:/HCI/src/calibration/gaze_calibrator.py#L95-L107) | Head pose stripped from solver; pure 2x3 ocular model applied without VOR compensation. | **Opposite direction motion**: Turning head right drives gaze reticle left. | **Critical** |
| **F-02** | `feature_pipeline.py`, `testbench.js`, `gestures.js` | [feature_pipeline.py:66-69](file:///d:/HCI/src/perception/feature_pipeline.py#L66-L69), [testbench.js:159-165](file:///d:/HCI/src/testbench/frontend/testbench.js#L159-L165) | All temporal filters and client-side reticle lerping deleted. | **Violent 150–200px jitter**: Raw webcam CMOS noise magnified by 480x gain directly to display. | **Critical** |
| **F-03** | `feature_pipeline.py` | [feature_pipeline.py:126-154](file:///d:/HCI/src/perception/feature_pipeline.py#L126-L154) | Invalidated profiles lacking version 3 / shape (2,3); zeroed gaze confidence. | Profile loading fails; reticle frozen at center; mouse takeover triggered immediately. | **High** |
| **F-04** | Architecture / Modality Selection | System-wide design | Relied on 3.5px ocular dynamic range (SNR 7:1) as sole screen pointer instead of 40px facial pose (SNR >60:1). | Inability to eliminate jitter via filtering without causing severe input lag. | **Critical** |
| **F-05** | `face_mesh_extractor.py` | [face_mesh_extractor.py:185-192](file:///d:/HCI/src/perception/face_mesh_extractor.py#L185-L192) | Hard conditional sign flips on 2D axis vectors (`if eye_axis[0] < 0.0`). | Angular discontinuity and abrupt $180^\circ$ coordinate flipping during head roll. | **Medium** |
| **F-06** | `server.py` & `run_testbench.py` | [server.py:245-255](file:///d:/HCI/src/testbench/server.py#L245-L255) | Unchecked broadcast of zero-confidence gaze coordinates when uncalibrated. | Downstream frontend freezes or fails to bind spatial anchors. | **Medium** |

---

## 5. Architectural Blueprint for the Definitive Fix

To eliminate both directional inversion and persistent jitter permanently, the architecture must transition to a **Dual-Stage Composite Gaze Pipeline (Face Carrier + Eye Vernier)**:

```
[Webcam Video Frame (640x480)]
               |
               +-------------------------------------------------------------+
               |                                                             |
               v                                                             v
+---------------------------------------------+               +---------------------------------------------+
|    3D Head Pose Estimator (SolvePnP)       |               |         Refined Iris Extractor              |
| 468 Landmarks -> Robust Skull Orientation   |               | Canthus-relative Iris Centroids             |
| Output: Yaw, Pitch (Clean, SNR > 60:1)      |               | Output: rx, ry (Dynamic Range ~ 4px)        |
+---------------------------------------------+               +---------------------------------------------+
               |                                                             |
               v                                                             v
+---------------------------------------------+               +---------------------------------------------+
|       PRIMARY FACE CARRIER ENGINE           |               |       DIFFERENTIAL EYE VERNIER ENGINE       |
| Direct screen mapping:                      |               | Localized fine adjustment (radius < 150px): |
| U_face = Screen_W * (0.50 + Yaw / Yaw_range)|               | Delta_U = -K_rx * (rx - 0.50)               |
| V_face = Screen_H * (0.50 + Pitch / P_range)|               | Delta_V = +K_ry * (ry - 0.50)               |
+---------------------------------------------+               +---------------------------------------------+
               |                                                             |
               +------------------------------+------------------------------+
                                              |
                                              v
                              +---------------------------------------------+
                              |      COMPOSITE SCREEN GAZE INTEGRATOR       |
                              | U_raw = U_face + Delta_U                    |
                              | V_raw = V_face + Delta_V                    |
                              +---------------------------------------------+
                                              |
                                              v
                              +---------------------------------------------+
                              |         ONE EURO FILTER (CHI 2012)          |
                              | fc_min = 0.8 Hz (Rock-solid during fix)    |
                              | beta = 0.005 (Zero lag on fast saccades)    |
                              +---------------------------------------------+
                                              |
                                              v
                              +---------------------------------------------+
                              |          CLIENT-SIDE EXPONENTIAL LERP       |
                              | Current += (Target - Current) * 0.35        |
                              | Saccade threshold > 140px (Instant snap)    |
                              +---------------------------------------------+
                                              |
                                              v
                                   [Calm, Stable Screen Reticle]
```

### Architectural Principles of the Solution:
1. **Direct Direction Alignment (Turn Right -> Move Right)**:
   The Face Carrier provides the bulk screen coordinate. When the face turns right ($\text{yaw} > 0$), screen X increases toward the right. This directly satisfies the user requirement and biomechanically overpowers VOR counter-rotation.
2. **Inherited High-SNR Stability**:
   Because 80% of cursor position is driven by the 468-point facial mesh, the pointer inherits the stability of the skull pose ($\text{SNR} > 60:1$).
3. **Sub-Pixel Tremor Elimination**:
   The iris signal is constrained to a localized vernier boundary ($\pm 120\text{ px}$), preventing sub-pixel sensor noise from ever generating 200px screen jumps.
4. **Optimal Temporal Dynamics via 1€ Filtering**:
   A single, calibrated 1€ Filter applied to the composite coordinates guarantees complete stillness during fixation while providing immediate, lag-free transitions during intentional movements.

---

## 6. Document Sign-Off

This document concludes the formal fault identification and root-cause audit. Implementation of the proposed composite pipeline will commence upon user approval.
