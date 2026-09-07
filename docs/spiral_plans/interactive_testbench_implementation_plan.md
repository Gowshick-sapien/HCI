# Implementation Plan: Interactive Multimodal HCI Testbench & Desktop Verification Suite

## 1. Goal Description
Implement an **Interactive Multimodal HCI Testbench Suite**: a dedicated, minimal, professional web-and-backend testing environment specifically designed to empirically test and validate hands-free gaze-and-gesture interaction across realistic UI controls (buttons, hover zones, text input fields, dropdowns, scroll containers, Tier-2 confirmation targets, and physical mouse takeover).

---

## 2. Key Requirements & Design Constraints

1. **Controlled, Realistic Interaction Environment**:
   * Evaluates the full perception-to-action loop without the safety risks of raw operating system cursor hijacking.
2. **Generous, High-Visibility Hitboxes**:
   * Elements sized specifically for gaze and gesture testing ($140\text{ px}$ to $320\text{ px}$) to accommodate natural eye saccade distributions and provide high-confidence interaction targets before precision tuning.
3. **Comprehensive Scenario Coverage**:
   * **Target 1**: Primary Click (`PINCH_INDEX` over button $\to$ click counter, state transition).
   * **Target 2**: Gaze Hover & Dwell Fixation (Fixate gaze $\to$ continuous dwell time meter $0 \to 600\text{ ms}$, hover active).
   * **Target 3**: Secondary Click / Context Menu (`PINCH_MIDDLE` $\to$ context modal options).
   * **Target 4**: Text Input & Keyboard Handoff (Click to focus $\to$ auto `KEYBOARD_HANDOFF`, suppresses gesture clicks while typing, resumes on `THUMBS_UP`).
   * **Target 5**: Option Dropdown Selector (Click to open, gaze item, pinch to select).
   * **Target 6**: Continuous Kinetic Scroll Viewport (`SWIPE_UP` / `SWIPE_DOWN` gestures $\to$ smooth document scrolling).
   * **Target 7**: Tier-2 Destructive Action (Click requires $600\text{ ms}$ visual dwell confirmation before execution).
   * **Target 8**: Physical Mouse Takeover Zone (Touching hardware mouse immediately switches to `MOUSE_PRIORITY`).
4. **Minimalist, Clean & Professional Aesthetics**:
   * Deep slate background (`#0E121A`), elevated cards (`#161C26`), crisp borders (`#263042`), high-contrast typography (`Segoe UI` / `Inter`).
5. **Strict User Rules**:
   * **Zero emojis anywhere** in HTML, CSS, JS, Python, logs, or documentation.

---

## 3. Proposed Changes & Deliverable Mapping

### Deliverable TBS-D1: Interactive Frontend & UI Testing Primitives (`src/testbench/frontend/`)

#### [NEW] [index.html](file:///d:/HCI/src/testbench/frontend/index.html)
* Semantic HTML5 layout with live telemetry header bar and an 8-panel responsive grid of interaction targets.

#### [NEW] [testbench.css](file:///d:/HCI/src/testbench/frontend/testbench.css)
* Minimalist, dark-mode CSS with high-contrast active states, generous hitboxes ($140\text{ px} - 320\text{ px}$), and smooth micro-animations.

#### [NEW] [testbench.js](file:///d:/HCI/src/testbench/frontend/testbench.js)
* Connects to WebSocket bridge, draws live gaze cursor reticle, performs bounding-box hit detection, handles dwell accumulation, triggers click/hover states, and reports user feedback back to the server.

---

### Deliverable TBS-D2: Bidirectional Streaming Bridge & Verification Engine (`src/testbench/`)

#### [NEW] [server.py](file:///d:/HCI/src/testbench/server.py)
* Lightweight asynchronous WebSocket/HTTP server running on `localhost:8080`.
* Bridges `LiveDashboardWorker` / `PerceptionWorker` to the web testbench at 60 FPS.
* Pushes `PerceptionFrame` (gaze screen coordinates, head pose), `GestureClassification` tokens, and `ComposedCommand` dispatches.
* Receives target click confirmations, movement times, and error overrides from the frontend, routing them into Layer 4 (`FeedbackObserver`) and Layer 5 (`AdaptationCoordinator`).

#### [NEW] [__init__.py](file:///d:/HCI/src/testbench/__init__.py)
* Package exports for `TestbenchServer`.

---

### Component 3: Standalone Launcher (`scripts/`)

#### [NEW] [run_testbench.py](file:///d:/HCI/scripts/run_testbench.py)
* Starts camera stream, perception pipeline, fusion engine, and local testbench server.
* Automatically launches the default web browser to `http://localhost:8080`.
* Supports graceful SIGINT / Ctrl+C shutdown.

---

### Component 4: Automated Test Suite (`tests/`)

#### [NEW] [test_testbench_server.py](file:///d:/HCI/tests/unit/test_testbench_server.py)
* Verifies WebSocket serialization, message routing, and target hit validation.

#### [NEW] [test_testbench_pipeline.py](file:///d:/HCI/tests/integration/test_testbench_pipeline.py)
* Verifies end-to-end perception $\to$ WebSocket bridge $\to$ feedback observer loop.

---

## 4. Verification Plan

### Automated Unit & Integration Tests
* `pytest tests/unit/test_testbench_server.py`
* `pytest tests/integration/test_testbench_pipeline.py`
* Run full project test suite (`pytest -v`) to confirm 100% pass rate.

### Manual Verification Scenarios (`TC-TB-01` to `TC-TB-08`)
1. **`TC-TB-01` (Primary Click)**: Move gaze to Target 1, pinch index $\to$ button states "CLICKED", counter increments.
2. **`TC-TB-02` (Hover Dwell)**: Gaze fixated on Target 2 $\to$ visual dwell bar fills from $0 \to 600\text{ ms}$, status turns to "HOVERING ACTIVE".
3. **`TC-TB-03` (Context Menu)**: Gaze on Target 3 + `PINCH_MIDDLE` $\to$ context modal opens.
4. **`TC-TB-04` (Keyboard Handoff)**: Click Target 4 text input $\to$ badge displays "KEYBOARD ACTIVE (Typing Mode)", physical typing accepted without gesture clicks.
5. **`TC-TB-05` (Dropdown Selector)**: Click Target 5 dropdown $\to$ option list expands, gazing and pinching an option updates selection.
6. **`TC-TB-06` (Kinetic Scroll)**: Swipe hand up/down over Target 6 $\to$ container scrolls smoothly.
7. **`TC-TB-07` (Tier-2 Confirmation)**: Attempt click on Target 7 $\to$ triggers 600ms circular confirmation before action executes.
8. **`TC-TB-08` (Mouse Takeover)**: Move hardware mouse $\to$ status turns to "MOUSE PRIORITY", multimodal control pauses.
