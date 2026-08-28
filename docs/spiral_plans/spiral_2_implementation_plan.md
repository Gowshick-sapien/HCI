# Spiral 2 Implementation Plan: Multimodal Perception Pipeline & Input Arbitration

## Project Title
# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction

---

## 1. Scope & Objective

Spiral 2 executes the implementation of **Deliverable D1: Multimodal Perception Pipeline**, encompassing:
1. **Threaded Video Ingestion Layer** (`src/capture/`)
2. **Layer 1 Computer Vision Perception & Spatial Filtering** (`src/perception/`)
3. **Layer 1 Gaze Dwell Tracker Sub-Module** (`src/perception/gaze_dwell_tracker.py`)
4. **Layer 1B Gesture Vocabulary Engine & Kinematic Classifier** (`src/gesture/`)
5. **Active Modality Arbiter** (`src/gesture/modality_arbiter.py`)
6. **Automated Verification, Integration & Latency Benchmarking Suite** (`tests/`)

---

## 2. Deliverables Breakdown for Spiral 2

| Deliverable Component | Architectural Scope | Key Codebase Artifacts | Invariant Target |
|---|---|---|---|
| **Capture Subsystem** | Video Ingestion & Buffering | `video_stream.py`, `frame_types.py` | Threaded capture at 30 FPS, capture latency $\le 5\text{ ms}$, lock-free buffer |
| **Layer 1 Perception Core** | Ocular Gaze, Head Pose, Hand Kinematics | `face_mesh_extractor.py`, `head_pose_estimator.py`, `hand_pose_extractor.py`, `holt_winters_filter.py`, `feature_pipeline.py` | Total perception latency $\le 20.5\text{ ms}$ on 4-core CPU, coordinate jitter $\le 1.2\text{ px}$, blink EAR suppression $(< 0.18)$ |
| **Layer 1 Gaze Dwell Tracker** | Fixation & Anchor Determination | `gaze_dwell_tracker.py` | Fixation detection radius $R = 40\text{ px}$, stable dwell accumulation, `gaze_anchor` only declared when `dwell_ms >= tau_dwell` |
| **Layer 1B Gesture Engine** | Fixed 13-Token Vocabulary & Classifier | `gesture_vocabulary.py`, `gesture_classifier.py`, `configs/gesture_vocabulary.yaml` | Sigmoid confidence scoring $c_{\text{gesture}} \in [0, 1]$, FIST guard strictly produces `action_intent = NO_ACTION` with 100% precision |
| **Active Modality Arbiter** | Priority-Ordered Device Arbitration | `modality_arbiter.py` | 4 operational modes (`NO_ACTION`, `KEYBOARD`, `MOUSE_PRIORITY`, `GESTURE`), rolling window timeouts, latency $< 1.0\text{ ms}$ |
| **Verification & Latency Suite** | Testing & Benchmarking | 9 unit test modules, 1 integration test, 1 latency benchmark | 100% invariant verification passes in CI |

---

## 3. Features to Design & Engineering Specifications

### 3.1 Video Ingestion Subsystem (`src/capture/`)
* **Threaded Video Stream (`video_stream.py`)**:
  * Background acquisition thread decoupling OpenCV `cv2.VideoCapture` from downstream perception inference.
  * Lock-free ring buffer (capacity $N=5$) with latest-frame-priority semantics (drops stale frames under CPU pressure).
  * Synthetic video feeder / mock camera mode for deterministic headless CI testing.
* **Capture Data Types (`frame_types.py`)**:
  * Strongly-typed `RawFrame` wrapper storing NumPy BGR ndarray, sequence frame ID, UTC epoch timestamp, and estimated ambient lux from mean frame luminance $L = 0.299R + 0.587G + 0.114B$.

### 3.2 Layer 1 Computer Vision & Spatial Filtering (`src/perception/`)
* **FaceMesh & Refined Iris Extractor (`face_mesh_extractor.py`)**:
  * Ingests `RawFrame`, processes via MediaPipe FaceMesh (`static_image_mode=False`, `max_num_faces=1`, `refine_landmarks=True`).
  * Extracts 468 facial mesh landmarks plus 10 refined iris landmarks (indices 468–472 left iris, 473–477 right iris).
  * Computes Eye Aspect Ratio (EAR) for left/right eyes:
    $$\text{EAR} = \frac{\|\mathbf{p}_2 - \mathbf{p}_6\| + \|\mathbf{p}_3 - \mathbf{p}_5\|}{2 \|\mathbf{p}_1 - \mathbf{p}_4\|}$$
  * Enforces instant zero-confidence suppression when $\text{EAR} < 0.18$ (blink event).
  * Calculates normalized iris displacement ratios $r_{\text{iris}, x}, r_{\text{iris}, y}$ relative to eye corner bounding boxes.
* **Head Pose 3D Estimator (`head_pose_estimator.py`)**:
  * Selects 6 canonical 3D anthropometric facial feature points (Nose tip [1], Chin [199], Left eye outer corner [33], Right eye outer corner [263], Left mouth corner [61], Right mouth corner [291]).
  * Maps 2D landmark projections against standard 3D facial model coordinates using Levenberg-Marquardt `cv2.solvePnP`.
  * Computes rotation vector $\mathbf{r}$ (converted to Euler angles: yaw, pitch, roll) and translation vector $\mathbf{t}$.
  * Calculates head pose Mahalanobis confidence $s_{\text{head}} \in [0, 1]$ relative to calibrated neutral ellipsoid $\mathcal{E}_{\text{head}}$.
* **Hand Pose Kinematics Extractor (`hand_pose_extractor.py`)**:
  * Ingests `RawFrame`, processes via MediaPipe Hands (`max_num_hands=2`, `min_detection_confidence=0.7`).
  * Extracts 21 3D landmarks $(\mathbf{p}_0, \dots, \mathbf{p}_{20})$ per detected hand in normalized camera space.
  * Computes wrist velocity $\mathbf{v}_{\text{wrist}}(t) = \frac{\|\mathbf{p}_0(t) - \mathbf{p}_0(t-1)\|}{\Delta t}$, palm normal vector $\mathbf{n}_{\text{palm}}$, and Euclidean inter-finger tip distances (thumb-to-index, thumb-to-middle, thumb-to-ring, thumb-to-pinky).
  * Outputs raw kinematic metrics without assigning high-level command intent (strict separation of perception vs. gesture classification).
* **Adaptive Holt-Winters Dynamic Smoothing Filter (`holt_winters_filter.py`)**:
  * Applies velocity-scaled double exponential smoothing to continuous landmark coordinates:
    $$\hat{\mathbf{x}}_t = \alpha_t \mathbf{x}_t + (1 - \alpha_t)(\hat{\mathbf{x}}_{t-1} + \mathbf{b}_{t-1}), \quad \mathbf{b}_t = \beta (\hat{\mathbf{x}}_t - \hat{\mathbf{x}}_{t-1}) + (1 - \beta) \mathbf{b}_{t-1}$$
    $$\alpha_t = \text{clip}(\alpha_0 + \gamma \|\mathbf{v}_{\text{wrist}}(t)\|, \ 0.20, \ 0.85), \quad \beta = 0.15$$
  * Maintains stationary jitter $\le 1.2\text{ px}$ while preserving dynamic responsiveness during rapid saccades/swipes.
* **Gaze Dwell Tracker Sub-Module (`gaze_dwell_tracker.py`)**:
  * Maintains temporal sliding window of smoothed gaze coordinates $(u_t, v_t)$ over the last $150\text{ ms}$.
  * Calculates gaze spatial variance $\sigma^2_{\text{dwell}, t} = \frac{1}{K}\sum_{k=0}^{K-1} \|\mathbf{p}_{t-k} - \bar{\mathbf{p}}\|^2$.
  * Computes continuous stability score $\text{gaze\_stability}_t = \exp(-\sigma^2_{\text{dwell}, t} / R^2)$ with reference radius $R = 40\text{ px}$.
  * Accumulates `gaze_dwell_ms` as long as $\|\mathbf{p}_t - \mathbf{p}_{\text{anchor}}\| \le R$; resets dwell timer on saccades $(> R)$.
  * Emits `gaze_anchor = (u, v)` only when `gaze_dwell_ms >= tau_dwell`; emits `gaze_anchor = None` otherwise.
* **Feature Pipeline Coordinator (`feature_pipeline.py`)**:
  * Executes FaceMesh, HeadPose, HandPose, Holt-Winters, and Dwell Tracker within a unified execution harness.
  * Estimates $2 \times 2$ spatial covariance matrix $\boldsymbol{\Sigma}_{\text{sensor}}$.
  * Packages outputs into the immutable `PerceptionFrame` dataclass.

### 3.3 Layer 1B Gesture Vocabulary Engine & Classifier (`src/gesture/`)
* **Vocabulary Loader (`gesture_vocabulary.py`)**:
  * Parses `configs/gesture_vocabulary.yaml` into immutable `GestureTokenDefinition` records.
  * Validates all 13 fixed tokens at startup:
    * `PINCH_INDEX` $\to$ `PRIMARY_CLICK` (`requires_gaze_target=True`, $\theta=0.70$)
    * `PINCH_MIDDLE` $\to$ `RIGHT_CLICK` (`requires_gaze_target=True`, $\theta=0.70$)
    * `PINCH_RING` $\to$ `DOUBLE_CLICK` (`requires_gaze_target=True`, $\theta=0.75$)
    * `PINCH_PINKY` $\to$ `MIDDLE_CLICK` (`requires_gaze_target=True`, $\theta=0.75$)
    * `PINCH_HOLD` $\to$ `DRAG_START` (`requires_gaze_target=True`, $\theta=0.70$)
    * `PINCH_RELEASE` $\to$ `DRAG_DROP` (`requires_gaze_target=True`, $\theta=0.70$)
    * `SWIPE_LEFT` $\to$ `NAVIGATE_PREVIOUS` (`requires_gaze_target=False`, $\theta=0.65$)
    * `SWIPE_RIGHT` $\to$ `NAVIGATE_NEXT` (`requires_gaze_target=False`, $\theta=0.65$)
    * `SWIPE_UP` $\to$ `SCROLL_UP` (`requires_gaze_target=False`, $\theta=0.60$)
    * `SWIPE_DOWN` $\to$ `SCROLL_DOWN` (`requires_gaze_target=False`, $\theta=0.60$)
    * `OPEN_PALM` $\to$ `HOVER` (`requires_gaze_target=True`, $\theta=0.65$)
    * `FIST` $\to$ `NO_ACTION` (`requires_gaze_target=False`, `is_rest_state=True`, $\theta=0.80$)
    * `THUMBS_UP` $\to$ `CONFIRM_SUBMIT` (`requires_gaze_target=False`, $\theta=0.75$)
* **Kinematic Gesture Classifier (`gesture_classifier.py`)**:
  * Evaluates finger curl ratios $C_i = 1.0 - \frac{\|\mathbf{p}_{\text{tip}, i} - \mathbf{p}_{\text{mcp}, i}\|}{\|\mathbf{p}_{\text{pip}, i} - \mathbf{p}_{\text{mcp}, i}\| + \|\mathbf{p}_{\text{dip}, i} - \mathbf{p}_{\text{pip}, i}\| + \|\mathbf{p}_{\text{tip}, i} - \mathbf{p}_{\text{dip}, i}\|}$.
  * **FIST REST Guard Rule**: If $C_{\text{index}}, C_{\text{middle}}, C_{\text{ring}}, C_{\text{pinky}} \ge 0.75$, force classify as `FIST` token with `action_intent = NO_ACTION`.
  * For pinch gestures, computes normalized Euclidean gap $d_{\text{pinch}}$ and maps to sigmoid confidence:
    $$c_{\text{gesture}} = \frac{1}{1 + \exp\left(-k_s \cdot (d_{\text{threshold}} - d_{\text{pinch}})\right)}, \quad k_s = 20.0$$
  * For swipe gestures, evaluates directional velocity vector and palm translation magnitude.
  * Tracks continuous `stable_duration_ms` the current token has been maintained.
  * Emits `GestureClassification` dataclass.

### 3.4 Active Modality Arbiter (`src/gesture/modality_arbiter.py`)
* **Rolling Device Activity Listener**:
  * Background low-level input listener (via `pynput.keyboard` and `pynput.mouse`) updating timestamps $t_{\text{last\_key}}$ and $t_{\text{last\_mouse\_move}}$.
* **Priority Arbitration Decision Function**:
  $$\text{DeviceMode} = \begin{cases} \text{NO\_ACTION} & \text{if } \text{gesture} == \text{FIST} \lor \text{hard\_lockout} \\ \text{KEYBOARD} & \text{else if } (t - t_{\text{last\_key}}) \le 1500\text{ ms} \\ \text{MOUSE\_PRIORITY} & \text{else if } (t - t_{\text{last\_mouse}}) \le 800\text{ ms} \\ \text{GESTURE} & \text{otherwise} \end{cases}$$
* **Arbitration Signal Transformation**:
  * In `KEYBOARD` mode: Suppresses gesture confidence to $0.0$ (`action_intent = NO_ACTION`).
  * In `MOUSE_PRIORITY` mode: Soft-reduces gesture confidence $c_{\text{gesture}} \leftarrow 0.50 \cdot c_{\text{gesture}}$.
  * In `GESTURE` mode: Passes `GestureClassification` uninhibited.

---

## 4. Architectural Decisions in Spiral 2 Scope

| Decision Item | Options Considered | Selected Decision | Technical Rationale |
|---|---|---|---|
| **D2.1: Default Camera Resolution** | (A) 1280x720 (HD)<br>(B) 640x480 (VGA) | **Option B: 640x480 default** (1280x720 configurable) | MediaPipe FaceMesh & Hands achieve identical landmark accuracy on 640x480 while reducing CPU frame cycle time by $\sim 42\%$, guaranteeing $\le 20.5\text{ ms}$ latency budget on standard CPUs. |
| **D2.2: Double Buffering Mechanism** | (A) `queue.Queue(maxsize=1)`<br>(B) Atomic lock-free pointer swap | **Option B: Atomic pointer swap with `threading.Event`** | Eliminates thread lock contention; reading the latest frame never blocks the perception worker thread. |
| **D2.3: SolvePnP Flag / Method** | (A) `cv2.SOLVEPNP_ITERATIVE`<br>(B) `cv2.SOLVEPNP_EPNP`<br>(C) `cv2.SOLVEPNP_IPPE` | **Option A: `cv2.SOLVEPNP_ITERATIVE` with Levenberg-Marquardt** | Provides highest numerical stability across the 6 canonical facial points with $< 0.4\text{ ms}$ compute overhead. |
| **D2.4: FIST Detection Metric** | (A) MCP-to-Tip Euclidean distance<br>(B) Multi-joint angle curvature | **Option A: Normalized MCP-to-Tip distance curl ratio** | Bounded in $[0, 1]$, highly robust across different hand shapes and depths from camera. |
| **D2.5: Physical Device Listener Mode** | (A) Polling `GetCursorPos` & `GetAsyncKeyState`<br>(B) `pynput` non-blocking daemon listeners | **Option B: `pynput` daemon thread listeners** | Event-driven architecture with zero polling CPU overhead; captures exact timestamp on key/mouse events. |

---

## 5. File Creation & Modification Matrix

### 5.1 Source Code Files (`src/`)
* [`src/utils/geometry.py`](file:///d:/HCI/src/utils/geometry.py): 3D math, Euler conversions, landmark affine mapping.
* [`src/utils/math_utils.py`](file:///d:/HCI/src/utils/math_utils.py): Sigmoid, EWMA smoothing, bounding box helpers.
* [`src/capture/frame_types.py`](file:///d:/HCI/src/capture/frame_types.py): `RawFrame` dataclass and camera acquisition configuration.
* [`src/capture/video_stream.py`](file:///d:/HCI/src/capture/video_stream.py): Threaded capture worker with lock-free buffer and mock video feeder.
* [`src/perception/face_mesh_extractor.py`](file:///d:/HCI/src/perception/face_mesh_extractor.py): MediaPipe FaceMesh & 10-point iris tracker with blink EAR guard.
* [`src/perception/head_pose_estimator.py`](file:///d:/HCI/src/perception/head_pose_estimator.py): SolvePnP 3D pose estimator and Mahalanobis confidence evaluator.
* [`src/perception/hand_pose_extractor.py`](file:///d:/HCI/src/perception/hand_pose_extractor.py): 21-point kinematic tracker without domain interpretation.
* [`src/perception/holt_winters_filter.py`](file:///d:/HCI/src/perception/holt_winters_filter.py): Velocity-scaled double exponential smoothing filter.
* [`src/perception/gaze_dwell_tracker.py`](file:///d:/HCI/src/perception/gaze_dwell_tracker.py): Fixation tracker, continuous dwell timer, and anchor detector.
* [`src/perception/feature_pipeline.py`](file:///d:/HCI/src/perception/feature_pipeline.py): Pipeline coordinator assembling `PerceptionFrame`.
* [`src/gesture/gesture_vocabulary.py`](file:///d:/HCI/src/gesture/gesture_vocabulary.py): Token dictionary loader from YAML.
* [`src/gesture/gesture_classifier.py`](file:///d:/HCI/src/gesture/gesture_classifier.py): Kinematic classifier with FIST guard and sigmoid confidence.
* [`src/gesture/modality_arbiter.py`](file:///d:/HCI/src/gesture/modality_arbiter.py): Device activity listener and priority arbitration logic.

### 5.2 Automated Test Files (`tests/`)
* [`tests/conftest.py`](file:///d:/HCI/tests/conftest.py): Synthetic landmark fixtures and mock video stream feeds.
* [`tests/unit/test_video_stream.py`](file:///d:/HCI/tests/unit/test_video_stream.py): Lifecycle, buffer overflow, and mock feeding tests.
* [`tests/unit/test_face_mesh_extractor.py`](file:///d:/HCI/tests/unit/test_face_mesh_extractor.py): Iris offset math, EAR blink zeroing.
* [`tests/unit/test_head_pose_estimator.py`](file:///d:/HCI/tests/unit/test_head_pose_estimator.py): SolvePnP Euler angles, extreme rotation bounds.
* [`tests/unit/test_hand_pose_extractor.py`](file:///d:/HCI/tests/unit/test_hand_pose_extractor.py): 21-landmark parsing, wrist velocity math.
* [`tests/unit/test_holt_winters_filter.py`](file:///d:/HCI/tests/unit/test_holt_winters_filter.py): Dynamic alpha scaling, step response & lag.
* [`tests/unit/test_gaze_dwell_tracker.py`](file:///d:/HCI/tests/unit/test_gaze_dwell_tracker.py): Dwell accumulation, anchor determination, saccade reset.
* [`tests/unit/test_gesture_vocabulary.py`](file:///d:/HCI/tests/unit/test_gesture_vocabulary.py): YAML loading, 13 token validation, unknown token error.
* [`tests/unit/test_gesture_classifier.py`](file:///d:/HCI/tests/unit/test_gesture_classifier.py): FIST NO_ACTION invariant, pinch sigmoid confidence.
* [`tests/unit/test_modality_arbiter.py`](file:///d:/HCI/tests/unit/test_modality_arbiter.py): 4-mode transition verification on synthetic traces.
* [`tests/integration/test_perception_pipeline.py`](file:///d:/HCI/tests/integration/test_perception_pipeline.py): End-to-end RawFrame -> PerceptionFrame -> GestureClassification.
* [`tests/benchmarks/test_frame_latency.py`](file:///d:/HCI/tests/benchmarks/test_frame_latency.py): CPU latency benchmark verifying $\le 20.5\text{ ms}$ per frame.

---

## 6. Acceptance Invariants & Verification Matrix

| Invariant ID | Target Component | Acceptance Criteria | Automated Test Method |
|---|---|---|---|
| **INV-D1.1** | `feature_pipeline.py` | Total perception cycle $\le 20.5\text{ ms}$ on 4-core CPU hardware. | `tests/benchmarks/test_frame_latency.py` (1,000 frames) |
| **INV-D1.2** | `holt_winters_filter.py` | Stationary coordinate jitter $\le 1.2\text{ px}$; dynamic tracking lag $\le 15\text{ ms}$. | `tests/unit/test_holt_winters_filter.py` |
| **INV-D1.3** | `face_mesh_extractor.py` | Eye blink ($\text{EAR} < 0.18$) forces $s_{\text{gaze}} = 0.0$ immediately. | `tests/unit/test_face_mesh_extractor.py` |
| **INV-D1.4** | `gaze_dwell_tracker.py` | `gaze_anchor` is `None` when `gaze_dwell_ms < tau_dwell`; declared when $\ge \tau_{\text{dwell}}$. | `tests/unit/test_gaze_dwell_tracker.py` |
| **INV-D1.5** | `gesture_classifier.py` | `FIST` token always emits `action_intent = "NO_ACTION"`; 100% precision on curled-finger traces. | `tests/unit/test_gesture_classifier.py` (50 synthetic traces) |
| **INV-D1.6** | `modality_arbiter.py` | Emits correct `DeviceMode` across all 4 states on synthetic physical input event streams. | `tests/unit/test_modality_arbiter.py` |
| **INV-D1.7** | `video_stream.py` | Capture thread never blocks reader thread; buffer overflow drops oldest frame. | `tests/unit/test_video_stream.py` |

---

## 7. Step-by-Step Execution Sequence

```
+------------------------------------------------------------------------+
¦                   SPIRAL 2 STEP-BY-STEP EXECUTION                      ¦
+------------------------------------------------------------------------¦
¦  STEP 1: Utilities & Geometry Primitives (`src/utils/`)               ¦
¦  STEP 2: Video Stream & Buffer Threading (`src/capture/`)              ¦
¦  STEP 3: Spatial Filtering & Gaze Dwell Tracker (`src/perception/`)    ¦
¦  STEP 4: Computer Vision Extractors (FaceMesh, HeadPose, Hands)        ¦
¦  STEP 5: Perception Pipeline Assembler (`feature_pipeline.py`)         ¦
¦  STEP 6: Gesture Vocabulary Engine & FIST Guard (`src/gesture/`)       ¦
¦  STEP 7: Active Modality Arbiter (`src/gesture/modality_arbiter.py`)   ¦
¦  STEP 8: Unit & Integration Test Suite Execution (`pytest tests/`)     ¦
¦  STEP 9: CPU Latency & Resource Benchmarking (`test_frame_latency.py`) ¦
¦  STEP 10: Deliverable D1 Release Package Compilation (`deliverables/`) ¦
+------------------------------------------------------------------------+
```
