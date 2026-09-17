# Comprehensive Architectural Analysis & Engineering Blueprint: Interactive Multimodal HCI Testbench & Desktop Verification Suite

## Executive Summary

The **Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction** requires a robust, transparent, and empirical mechanism to validate real-time gaze-and-gesture interactions in an actual operational environment.

Direct uncontrolled operating system injection (such as hijacking the global Windows shell cursor and injecting raw `SendInput` events across arbitrary desktop software) introduces unnecessary instability, safety risks, and variable target geometries during the research and validation phase. Conversely, operating solely within a theoretical telemetry table fails to test whether the multimodal system actually works for realistic interaction tasks.

The developed solution is a **Dual-Surface Interactive Multimodal Testbench Suite (TBS)**:
1. **Scenario Interaction Suite (`TBS-D1` / `index.html`)**: A clean, professional, dedicated interactive surface featuring 8 standardized HCI interaction scenarios (primary clicks, hover dwell, context menus, text input with keyboard handoff, dropdown selectors, kinetic scrolling, Tier-2 confirmation, and mouse arbitration).
2. **Gesture Vocabulary Verification Suite (`TBS-G1` / `gestures.html`)**: A dedicated isolated test matrix covering all 13 built-in hand and finger gesture primitives defined in the system vocabulary.
3. **Optimized Target Hitboxes**: Targets are sized generously ($140\text{ px}$ to $320\text{ px}$) to conform to Fitts' Law and accommodate natural ocular saccade tolerances, establishing a baseline before micro-target calibration.
4. **Minimalist & Professional Aesthetic**: Clean dark-mode engineering styling, high contrast, clear visual status readouts, and **strictly zero emojis across the entire scope**.

---

## 1. Context & Architectural Analysis

### 1.1 The Testing Gap: Laboratory Sandbox vs. Full Desktop Control
The architectural evolution of the project has arrived at a critical junction:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                ARCHITECTURAL TESTING PARADIGMS                                   │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [PARADIGM A: Research Dashboard Sandbox (Spirals 1–7)]                                          │
│  • Synthetic targets arranged in an ISO circle; clicks logged as telemetry records.              │
│  • Limitation: Does not test interactive UI primitives (inputs, dropdowns, hover, scroll).       │
│                                                                                                  │
│  [PARADIGM B: Unrestricted OS Desktop Takeover (Deferred / High Risk)]                           │
│  • Direct Windows Win32 SendInput across entire OS; tiny 16px desktop icons.                    │
│  • Limitation: Jittery calibration can trigger destructive OS actions; Midas Touch text clashes. │
│                                                                                                  │
│  [PARADIGM C: Dedicated Interactive HCI Testbench Suite (IMPLEMENTED & OPERATIONAL)]             │
│  • Clean, minimal, full-screen professional testbed web application.                             │
│  • Dual testing surfaces: Scenario Testbench (TBS-D1) + Gesture Vocabulary Suite (TBS-G1).       │
│  • Generous ergonomic hitboxes (140–320px) calibrated for gaze + gesture interaction.            │
│  • Direct bi-directional 60 FPS bridge to Python perception and adaptation engines.              │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Interactive HCI Testbench: Core Interaction Scenarios (TBS-D1)

The Interactive Scenario Testbench is structured into a clean multi-panel testing surface. Each interactive target is intentionally sized for empirical validation:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         INTERACTIVE MULTIMODAL TESTBENCH SURFACE (TBS-D1)                        │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  STATUS BAR: Modality: GESTURE | Gaze: (960, 540) | Token: PINCH_INDEX | Latency: 16.2ms        │
│  NAVIGATION: [SCENARIOS (TBS-D1)] | [GESTURE VOCABULARY (TBS-G1)]                                │
├───────────────────────────────────────┬──────────────────────────────────────────────────────────┤
│  [SCENARIO 1: PRIMARY CLICK]          │  [SCENARIO 2: HOVER & DWELL FIXATION]                    │
│  Target Size: 200 x 70 px             │  Target Size: 220 x 80 px                                │
│  Action: Eye gaze + PINCH_INDEX       │  Action: Continuous eye gaze fixation                     │
│  Feedback: State "CLICKED (Count: N)" │  Feedback: Visual dwell fill (0ms -> 600ms) + "HOVERING" │
├───────────────────────────────────────┼──────────────────────────────────────────────────────────┤
│  [SCENARIO 3: SECONDARY / CONTEXT]    │  [SCENARIO 4: TEXT INPUT & KEYBOARD HANDOFF]             │
│  Target Size: 200 x 70 px             │  Target Size: 320 x 60 px                                │
│  Action: Eye gaze + PINCH_MIDDLE      │  Action: Gaze click to focus; I-beam pointer active      │
│  Feedback: Professional context menu  │  Feedback: "KEYBOARD ACTIVE" (suppresses gesture clicks) │
├───────────────────────────────────────┼──────────────────────────────────────────────────────────┤
│  [SCENARIO 5: DROPDOWN SELECTION]     │  [SCENARIO 6: KINETIC SWIPE SCROLL]                      │
│  Target Size: 240 x 60 px             │  Viewport: 280 x 130 px scroll container                 │
│  Action: Pinch to expand, gaze item   │  Action: SWIPE_UP / SWIPE_DOWN gestures (3000ms grace)   │
│  Feedback: All 4 options selectable   │  Feedback: Smooth kinetic scrolling + pulse animations   │
├───────────────────────────────────────┼──────────────────────────────────────────────────────────┤
│  [SCENARIO 7: TIER-2 CONFIRMATION]    │  [SCENARIO 8: PHYSICAL MOUSE TAKEOVER]                   │
│  Target Size: 220 x 70 px (Red Alert) │  Target Zone: Global input capture                       │
│  Action: 600ms dwell + pinch to reset │  Action: Physically move hardware mouse                  │
│  Feedback: Radial HUD confirmation    │  Feedback: "MOUSE OVERRIDE DETECTED" -> Yield to Mouse   │
└───────────────────────────────────────┴──────────────────────────────────────────────────────────┘
```

### 2.1 Specification of Interaction Targets & Recent Enhancements

1. **Target 1: Primary Click Target**
   * **Dimensions**: $200\text{ px} \times 70\text{ px}$ (generous hitbox, centered label).
   * **Trigger**: Fixate gaze on button + execute `PINCH_INDEX` gesture. Strict rejection of middle, ring, or pinky pinches.
   * **Response**: Instant visual activation state, counter increment (`Clicks: N`), timestamp logged, pulse animation.

2. **Target 2: Gaze Hover & Dwell Fixation Zone**
   * **Dimensions**: $220\text{ px} \times 80\text{ px}$.
   * **Trigger**: Rest gaze within the zone without gesturing.
   * **Response**: Real-time dwell progress indicator ($0\text{ ms} \to 600\text{ ms}$) changing state to `HOVER ACTIVE` upon reaching $300\text{ ms}$.

3. **Target 3: Secondary Click / Context Menu Target**
   * **Dimensions**: $200\text{ px} \times 70\text{ px}$.
   * **Trigger**: Fixate gaze + execute `PINCH_MIDDLE`.
   * **Response**: Pops up a modal menu with selectable options.

4. **Target 4: Text Input Box & Keyboard Handoff (Enhanced)**
   * **Dimensions**: $320\text{ px} \times 60\text{ px}$, font size $14\text{ px}$.
   * **Trigger**: Fixate gaze into input field + execute `PINCH_INDEX` (Primary Click).
   * **Enhancements & Pointer Behavior**:
     * **I-Beam Text Pointer Reticle**: When gaze shifts into the text input box or when keyboard handoff is active, the circular gaze reticle automatically transforms into a high-contrast cyan I-beam text pointer.
     * **Active Caret & Focus**: `inputHandoff.focus()` acquires DOM focus, applies `.text-pointer-active`, displays a blinking caret (`caret-color: #00E5FF`), and sets `cursor: text`.
     * **Gesture Click Suppression**: While the input field is active, multimodal gesture clicks are paused to prevent spurious activations while typing.
     * **Release**: multimodality resumes upon pressing `THUMBS_UP`, clicking outside, or blurring the element.

5. **Target 5: Dropdown Option Selector (Enhanced)**
   * **Dimensions**: $240\text{ px} \times 60\text{ px}$ header with expandable menu.
   * **Trigger**: Fixate gaze on `#dropdown-header` + execute `PINCH_INDEX` to toggle open/closed hands-free.
   * **Enhancements & Multi-Option Hit-Testing**:
     * **Hitbox Hierarchy Resolution**: Hit-testing logic evaluates child `.dropdown-option` elements first when the menu is open, resolving the container occlusion issue.
     * **All Options Selectable**: All four operational profiles (Standard, High Sensitivity, Tremor Damped, and Fatigue Adaptive) can be independently fixated and selected via primary pinch.
     * **Direct Click Binding**: Wired native click event listeners to each option for manual fallback testing.

6. **Target 6: Continuous Kinetic Scroll Viewport (Enhanced)**
   * **Dimensions**: $280\text{ px} \times 130\text{ px}$ scrollable container with 12 telemetry records.
   * **Trigger**: Hand translation in field of view performing `SWIPE_UP` or `SWIPE_DOWN`.
   * **Enhancements & Velocity Handling**:
     * **Extended Fixation Grace Window**: Expanded sticky gaze tolerance to $3000\text{ ms}$ to accommodate natural eye shifts during hand translation, matching vocabulary configuration (`requires_gaze_target: false`).
     * **Smooth Scrolling Execution**: Applied `scrollContainer.scrollBy({ top: delta, behavior: "smooth" })` with a $180\text{ ms}$ debounce filter to prevent multi-frame overshoot.
     * **Visual Pulse & Controls**: Added directional border pulse animations (`.scroll-pulse-up`, `.scroll-pulse-down`) and explicit manual `SCROLL UP` and `SCROLL DOWN` buttons.

7. **Target 7: Tier-2 High-Consequence Action Target (Reset System)**
   * **Dimensions**: $220\text{ px} \times 70\text{ px}$, bordered in warning red.
   * **Trigger**: 600ms visual dwell confirmation sweep must complete before the reset action executes, protecting against accidental activation.

8. **Target 8: Physical Hardware Mouse Takeover Zone**
   * **Trigger**: Moving the physical hardware mouse at any point.
   * **Response**: Instantly yields multimodal control, switches modality badge to `MOUSE_PRIORITY`, and notifies the supervisory arbiter.

---

## 3. Dedicated Gesture Vocabulary Suite (TBS-G1 / `gestures.html`)

To provide isolated, empirical validation for every individual gesture primitive built into the architecture, a dedicated Gesture Vocabulary Testing Suite has been integrated into the testbench:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                     MULTIMODAL GESTURE VOCABULARY VERIFICATION SUITE (TBS-G1)                    │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  STATUS: CONNECTED (60 FPS) | GESTURE: PINCH_INDEX (0.94) | LATENCY: 15.8ms                      │
│  CONTROLS: [RESET ALL METRICS] | TABS: [SCENARIOS (TBS-D1)] | [GESTURE VOCABULARY (TBS-G1)]       │
├──────────────────────────┬──────────────────────────┬──────────────────────────┬─────────────────┤
│  [01: PINCH_INDEX]       │  [02: PINCH_MIDDLE]      │  [03: PINCH_RING]        │  [04: PINCH_PIN]│
│  Action: PRIMARY_CLICK   │  Action: RIGHT_CLICK     │  Action: DOUBLE_CLICK    │  Action: MIDDLE │
│  Target: Click Button    │  Target: Popup Context   │  Target: 2-Hit Verifier  │  Target: Aux Clk│
├──────────────────────────┼──────────────────────────┼──────────────────────────┼─────────────────┤
│  [05: PINCH_HOLD]        │  [06: PINCH_RELEASE]     │  [07: SWIPE_LEFT]        │  [08: SWIPE_RIG]│
│  Action: DRAG_START      │  Action: DRAG_DROP       │  Action: NAV_PREVIOUS    │  Action: NAV_NXT│
│  Target: Dock Hold Pulse │  Target: Drop Catch Zone │  Target: Deck Carousel   │  Target: Deck Ca│
├──────────────────────────┼──────────────────────────┼──────────────────────────┼─────────────────┤
│  [09: SWIPE_UP]          │  [10: SWIPE_DOWN]        │  [11: OPEN_PALM]         │  [12: FIST]     │
│  Action: SCROLL_UP       │  Action: SCROLL_DOWN     │  Action: HOVER           │  Action: REST   │
│  Target: Ascend Viewport │  Target: Descend Viewport│  Target: Dwell Bar       │  Target: Shield │
├──────────────────────────┴──────────────────────────┴──────────────────────────┴─────────────────┤
│  [13: THUMBS_UP] - Action: CONFIRM_SUBMIT | Target: High-Tier Confirmation Gate Stamp            │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Gesture Primitives Matrix

The suite covers all 13 vocabulary gesture tokens defined in [gesture_vocabulary.yaml](file:///d:/HCI/configs/gesture_vocabulary.yaml):

| Token | Mapped Action | Gaze Requirement | Default Threshold | Verification Widget |
| :--- | :--- | :--- | :--- | :--- |
| `PINCH_INDEX` | `PRIMARY_CLICK` | Required | $0.70$ | Primary Click Target with trigger counter and active pulse |
| `PINCH_MIDDLE` | `RIGHT_CLICK` | Required | $0.70$ | Context Menu Target with pop-up action confirmation |
| `PINCH_RING` | `DOUBLE_CLICK` | Required | $0.75$ | Double Click Verification widget with rapid-fire tracking |
| `PINCH_PINKY` | `MIDDLE_CLICK` | Required | $0.75$ | Auxiliary Middle Click Target |
| `PINCH_HOLD` | `DRAG_START` | Required | $0.70$ | Drag Initiation Dock with dynamic hold-state indicator |
| `PINCH_RELEASE` | `DRAG_DROP` | Required | $0.70$ | Drop Reception Zone confirming drag sequence completion |
| `SWIPE_LEFT` | `NAVIGATE_PREVIOUS` | Global | $0.65$ | Interactive 3-pane carousel stepping leftward |
| `SWIPE_RIGHT` | `NAVIGATE_NEXT` | Global | $0.65$ | Interactive 3-pane carousel stepping rightward |
| `SWIPE_UP` | `SCROLL_UP` | Global | $0.60$ | Mini scroll viewport with ascending displacement |
| `SWIPE_DOWN` | `SCROLL_DOWN` | Global | $0.60$ | Mini scroll viewport with descending displacement |
| `OPEN_PALM` | `HOVER` | Required | $0.65$ | Dwell progress indicator confirming sustained open palm |
| `FIST` | `NO_ACTION` | Global | $0.80$ | Rest Guard Shield confirming Midas Touch suppression |
| `THUMBS_UP` | `CONFIRM_SUBMIT` | Global | $0.75$ | Explicit Confirmation Gate stamping submit approval |

### 3.2 Key Features of the Gesture Suite
1. **Per-Token Trigger Counters**: Independent counters record every confirmed gesture activation.
2. **Dynamic Confidence Meters**: Real-time confidence percentage bar ($0\% \to 100\%$) indicating classifier certainty.
3. **Interactive Widget Feedback**: Each card contains visual animations tailored to its action intent.
4. **Reset Controls**: Individual card reset buttons and a global "Reset All Metrics" toolbar action.
5. **Bidirectional Navigation**: Header tabs allow switching between Scenario testing and Gesture vocabulary testing without session restarts.

---

## 4. Technical Architecture: WebSocket & Dispatch Pipeline

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               TESTBENCH SYSTEM ARCHITECTURE                                      │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│   [Python Multimodal Perception & Fusion Backend]                                                │
│   • VideoStream (Webcam Capture)                                                                 │
│   • FeaturePipeline (FaceMesh, Irises, Head Pose, Hand Skeleton)                                 │
│   • GestureClassifier (13-Token Kinematic Engine)                                                │
│   • ModalityArbiter & CommandComposer                                                           │
│   • ProfileManager (User-specific Calibration Curves)                                            │
│          │                                                                                       │
│          ▼                                                                                       │
│   [WebSocket / HTTP Bridge Server] (`src/testbench/server.py`)                                   │
│   • Port: 8080 (Localhost)                                                                       │
│   • Routes:                                                                                      │
│       - GET /             -> index.html (Scenario Suite TBS-D1)                                  │
│       - GET /gestures     -> gestures.html (Gesture Suite TBS-G1)                                │
│       - GET /gestures.html-> gestures.html                                                       │
│       - GET /ws           -> Bidirectional WebSocket Streaming Bridge                           │
│   • Broadcasts 60 FPS perception telemetry (gaze_x, gaze_y, token, confidence, command)          │
│   • Receives client-side verification events (`INTERACTION_EVENT`)                               │
│          ▲                                                                                       │
│          │ (Bidirectional JSON WebSocket)                                                         │
│          ▼                                                                                       │
│   [Frontend Verification Clients] (`src/testbench/frontend/`)                                    │
│   ├── index.html & testbench.js (Scenario Suite)                                                 │
│   ├── gestures.html & gestures.js (Gesture Vocabulary Suite)                                     │
│   └── testbench.css & gestures.css (Zero-Emoji Minimal Dark Styling)                             │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Live Execution Guide

### 5.1 Launching Live Multimodal Testing
To launch the full interactive testbench with live camera perception and user profile calibration:
```powershell
python scripts/run_testbench.py --user user_02
```

### 5.2 Launching Synthetic Simulation Mode
To test interaction widgets and hit-testing logic without physical camera hardware:
```powershell
python scripts/run_testbench.py --simulated
```

### 5.3 Operational Verification Checklist
- **Scenario 4**: Fixate gaze on the text field and execute `PINCH_INDEX`. Verify the gaze reticle morphs to an I-beam text pointer, the text box gains active focus, the typing handoff badge appears, and gesture clicks pause during typing. Exit with `THUMBS_UP` or click outside.
- **Scenario 5**: Fixate on the dropdown header and execute `PINCH_INDEX` to open. Gaze at any option (1, 2, 3, or 4) and execute `PINCH_INDEX` to verify selection and automatic closure.
- **Scenario 6**: Perform `SWIPE_DOWN` or `SWIPE_UP` gestures in front of the camera. Verify the viewport scrolls smoothly with directional green pulse feedback.
- **Gesture Suite**: Click `GESTURE VOCABULARY (TBS-G1)` in the top header. Perform any of the 13 gestures to observe token-specific counters, confidence meters, and interactive widget actuation.

---

## 6. Gaze Calibration and Coordinate Mapping Architecture

### 6.1 Decoupled Orthogonal Regression
Previously, unconstrained 5D regression fitted both horizontal and vertical screen targets simultaneously against coupled ocular and head features `[rx, ry, yaw, pitch, 1.0]`. Due to natural sample correlation between eye axes during multi-target calibration, the solver produced severe cross-axis weights (for example, horizontal iris changes altering vertical screen coordinates by over 2400 pixels). 

The calibration solver (`src/calibration/gaze_calibrator.py`) now enforces strictly decoupled orthogonal ridge regression:
- **Horizontal Screen Coordinate (X)**: Fitted exclusively against `[rx, yaw, 1.0]`. Cross-axis terms for vertical iris displacement (`ry`) and head pitch are locked to `0.0`.
- **Vertical Screen Coordinate (Y)**: Fitted exclusively against `[ry, pitch, 1.0]`. Cross-axis terms for horizontal iris displacement (`rx`) and head yaw are locked to `0.0`.

This architecture guarantees that horizontal glances move the pointer purely along the X axis, and vertical glances move the pointer purely along the Y axis, eliminating diagonal cross-talk.

### 6.2 Intrinsic Gaze Velocity Saccadic Snapping
In `src/perception/feature_pipeline.py`, the Holt-Winters exponential smoothing filter was previously updated with hand wrist velocity. During eye fixations where the hand remained stationary, the filter was locked at minimum alpha (0.20), creating sluggish tracking and 15-20 frame lag during eye saccades.

The filter now computes velocity from intrinsic gaze displacement (`np.linalg.norm(x_meas - x_prev)`):
- **During Saccades**: Displacement velocity rises sharply, driving alpha to `alpha_max = 0.85` for instantaneous pointer snapping without lag.
- **During Fixations**: Velocity drops to near-zero, lowering alpha to `alpha_min = 0.20` for stable jitter attenuation on UI hitboxes.

### 6.3 Display DPI and Viewport Resolution Alignment
On Windows displays running DPI scaling (such as 125% scaling on 1080p panels), logical screen dimensions are 1536x864 while physical panel metrics are 1920x1080. Hardcoding 1920x1080 in the live pipeline compressed normalized coordinates to 80% of the browser width, preventing the gaze pointer from reaching the right and bottom screen boundaries.

The pipeline (`scripts/run_testbench.py`) now dynamically resolves display metrics using `GetSystemMetrics`, matching the browser viewport logical resolution and ensuring true full-screen reach across all display scales.

---

## 7. Gesture Vocabulary Execution Guide and Testbench Enhancements

### 7.1 Physical Execution Guidelines for Gestures
To perform gestures reliably in front of the camera:
1. **THUMBS_UP**:
   - Form a relaxed fist with all four fingers (index, middle, ring, pinky) curled in against your palm.
   - Extend your thumb vertically upward towards the ceiling.
   - Keep your thumb upright and straight (`thumb_curl < 0.38`). The thumb tip must be higher than the other four knuckles and fingertips.
   - Hold the posture steady for 100-200 ms to trigger confirmation.
2. **SWIPE_LEFT**:
   - Open or relaxed hand with palm facing the camera.
   - Sweep your hand quickly from your right to your left across your field of view (towards camera right, $dx > 0$).
   - A moderate sweep velocity ($\ge 0.22$) triggers the transition immediately.
3. **SWIPE_RIGHT**:
   - Sweep your hand quickly from your left to your right across your field of view (towards camera left, $dx < 0$).
4. **SWIPE_UP**:
   - Sweep your hand rapidly upward towards the ceiling ($dy < 0$).
5. **SWIPE_DOWN**:
   - Sweep your hand rapidly downward towards the desk ($dy > 0$).

### 7.2 Kinematic Classifier Optimizations (`src/gesture/gesture_classifier.py`)
- **Swipe Velocity Threshold**: Relaxed from $1.2$ down to $0.22$, and minimum frame displacement from $0.020$ to $0.005$. This accommodates natural arm movements at 30 FPS and 60 FPS without requiring unnatural arm whipping.
- **Webcam Mirror Mapping**: Correctly handles un-mirrored webcam frame translation so moving your hand right produces `SWIPE_RIGHT` and moving left produces `SWIPE_LEFT`.
- **Thumbs Up Posture Model**: Decoupled from strict 4-finger curl requirements. It evaluates thumb verticality (`thumb_tip` above `index_mcp` and `thumb_mcp`), straightness (`thumb_curl < 0.38`), and checks that all four other fingertips remain below the thumb tip.

### 7.3 Interactive Testbench Scenario Refinements (`src/testbench/frontend/testbench.js`)
- **Scenario 4 (Text Input & Keyboard Handoff)**: Point gaze at the Scenario 4 section and execute `PINCH_INDEX` (Primary Click). The text field gains focus, the blinking text cursor appears, and the gaze reticle morphs into a high-contrast cyan I-beam text pointer. Gesture clicks pause during typing. To exit typing mode, perform `THUMBS_UP` or click outside.
- **Scenario 5 (Dropdown Option Selector)**: Point gaze at the Scenario 5 section and execute `PINCH_INDEX`. The dropdown menu opens and lists all four options. Gaze at any desired option and execute `PINCH_INDEX` to select that option. The selection algorithm uses exact vertical center distance, eliminating false hits on adjacent options.
- **Scenario 6 (Kinetic Scroll Viewport)**: Point gaze at Scenario 6 and perform `SWIPE_UP`, `SWIPE_DOWN`, `SWIPE_LEFT`, or `SWIPE_RIGHT`. The viewport scrolls smoothly with emerald directional pulse animations and accurate position feedback.


