# Test Bench Suite (TBS) Testing & Verification Plan: Automated & Manual Protocol

## Project Title
# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction
### Deliverables: TBS-D1 & TBS-D2

---

## 1. Scope & Objective

This document defines the formal, exhaustive **Testing & Verification Plan** for the **Test Bench Suite (TBS)**, encompassing both deliverables:
* **TBS-D1**: Interactive Multimodal Frontend & UI Testing Primitives
* **TBS-D2**: Bidirectional Streaming Bridge & Verification Engine

The purpose is to empirically validate that the multimodal architecture (Layers 1 through 5) reliably executes gaze-and-gesture interactions across eight core human-computer interaction (HCI) primitives within an isolated, controlled, and ergonomically sized web testbench before any full-scale operating system deployment.

---

## 2. Test Environment & Pre-requisites

1. **Hardware Configuration**:
   * Standard RGB webcam (30 FPS, $640 \times 480$ minimum resolution) positioned centered above or below the display.
   * Standard physical keyboard and mouse (for testing handoff and takeover).
   * Minimum screen resolution: $1280 \times 720$ (Recommended: $1920 \times 1080$).
2. **Software Runtime**:
   * Python 3.12.x on Windows.
   * Modern browser (Google Chrome, Microsoft Edge, or Firefox) with WebSocket and HTML5 Canvas support.
   * Local server host: `http://127.0.0.1:8080`.
3. **Environmental Conditions**:
   * Standard indoor ambient lighting ($50\text{ lux} - 500\text{ lux}$).
   * Participant seated at normal desktop distance ($50\text{ cm} - 75\text{ cm}$) from webcam.

---

## 3. Formal Invariants Verification Matrix

| Invariant ID | Target Component | Formal Acceptance Criterion | Verification Method |
|---|---|---|---|
| **INV-TBS.1** | `testbench.css` | All interactive hitboxes must have width $\ge 140\text{ px}$ and height $\ge 60\text{ px}$. | Automated Static Check |
| **INV-TBS.2** | All TBS Code & Docs | Strictly ZERO emojis present in HTML, CSS, JavaScript, Python, or logs. | Automated Linter |
| **INV-TBS.3** | `server.py` | Local WebSocket dispatch latency must be $< 10.0\text{ ms}$ over loopback. | Automated Benchmark |
| **INV-TBS.4** | `testbench.js` | Dwell accumulation: Hover active at $\ge 300\text{ ms}$; Tier-2 confirmation at $\ge 600\text{ ms}$. | Automated Unit Test |
| **INV-TBS.5** | `testbench.js` | Focused text input must completely suppress multimodal click injection while typing. | Automated Unit Test |
| **INV-TBS.6** | `server.py` / `arbiter` | Physical mouse movement must switch active mode to `MOUSE_PRIORITY` within $< 5.0\text{ ms}$. | Automated Integration |

---

## 4. Automated Verification Suite

### AUT-TBS-01: Hitbox Sizing & Ergonomic Inspection
* **Target**: `src/testbench/frontend/testbench.css`, `index.html`
* **Test Method**: Static DOM and stylesheet parser.
* **Assertion**: Verify that every `.target-button`, `.target-zone`, `.target-input`, and `.custom-dropdown` element has a computed width $\ge 140\text{ px}$ and height $\ge 60\text{ px}$.
* **Pass Criterion**: 100% of targets meet or exceed the generous Fitts' Law hitbox threshold.

### AUT-TBS-02: Zero Emoji Static Linter
* **Target**: Entire `src/testbench/` directory and test files.
* **Test Method**: Unicode code-point scanner checking ranges `0x1F300`–`0x1FAFF`, `0x2600`–`0x27BF`, and related emoji blocks.
* **Assertion**: 0 emoji occurrences across all `.html`, `.css`, `.js`, and `.py` files.
* **Pass Criterion**: Zero matches.

### AUT-TBS-03: WebSocket Streaming Bridge Latency Benchmark
* **File**: `tests/benchmarks/test_testbench_latency.py`
* **Test Method**: Spawns local testbench server and connects a high-frequency asynchronous test client. Transmits 1,000 JSON `PERCEPTION_UPDATE` packets.
* **Assertion**: Mean packet roundtrip latency is $< 10.0\text{ ms}$; 95th percentile latency is $< 15.0\text{ ms}$.
* **Pass Criterion**: Benchmark pass with zero packet drops.

### AUT-TBS-04: WebSocket Server Message Serialization Unit Test
* **File**: `tests/unit/test_testbench_server.py`
* **Test Method**: Tests JSON encoding and decoding of `PerceptionFrame`, `GestureClassification`, and `ComposedCommand` dataclasts.
* **Assertion**: All fields serialize and deserialize cleanly without schema degradation.
* **Pass Criterion**: Pytest unit test passes with zero warnings.

### AUT-TBS-05: Multi-Layer Pipeline Integration Test
* **File**: `tests/integration/test_testbench_pipeline.py`
* **Test Method**: Connects live camera feed $\to$ perception pipeline $\to$ command composer $\to$ WebSocket server $\to$ mock client.
* **Assertion**: Client receives continuous 60 FPS updates containing normalized gaze coordinates $(x_g, y_g) \in [0, W] \times [0, H]$ and gesture tokens.
* **Pass Criterion**: End-to-end integration test passes.

---

## 5. Manual Interactive Verification Procedures

Manual testing is conducted using the dedicated testbench interface launched via:
```powershell
python scripts/run_testbench.py
```

---

### TC-TB-01: Primary Action Button Activation
* **Objective**: Verify intentional primary clicking via eye-gaze targeting and index pinch gesture.
* **Prerequisites**: Testbench running, webcam connected, gaze calibrated.
* **Action Steps**:
  1. Fixate eye gaze on **Scenario 01 (Primary Click Target)** ($200 \times 70\text{ px}$).
  2. Observe cyan focus outline indicating active gaze fixation.
  3. Perform a clear `PINCH_INDEX` gesture in front of the camera.
* **Expected Visual & Operational Behavior**:
  * The button pulses with an emerald background (`rgba(0, 230, 118, 0.2)`).
  * The click counter increments immediately: `Clicks: 1`.
  * The telemetry bar displays: `ACTION DISPATCH: PRIMARY_CLICK`.
  * Card feedback updates: `Status: PRIMARY_CLICK Triggered (Total: 1)`.
* **Pass Criteria**: Click is registered accurately without false double-triggers.

---

### TC-TB-02: Gaze Hover & Dwell Fixation Meter
* **Objective**: Verify that resting eye gaze in a designated zone accumulates dwell time and engages hover state without gesture motor action.
* **Prerequisites**: Normal gaze tracking active.
* **Action Steps**:
  1. Look directly into **Scenario 02 (Gaze Hover Zone)** ($220 \times 80\text{ px}$) without moving hands.
  2. Maintain fixation continuously for $> 300\text{ ms}$.
  3. Look away to the left or right after 1 second.
* **Expected Visual & Operational Behavior**:
  * The linear cyan progress bar fills continuously from $0\% \to 100\%$ ($0\text{ ms} \to 600\text{ ms}$).
  * At $300\text{ ms}$, the zone outline turns solid emerald and card feedback changes to: `Status: HOVER ACTIVE (Fixation Confirmed)`.
  * Upon looking away, the dwell meter instantly resets to $0\text{ ms}$ and returns to idle.
* **Pass Criteria**: Smooth dwell accumulation and instant release upon saccade exit.

---

### TC-TB-03: Secondary Click / Context Menu
* **Objective**: Verify that a distinct gesture token (`PINCH_MIDDLE`) triggers a secondary action and context menu.
* **Prerequisites**: Normal gaze tracking active.
* **Action Steps**:
  1. Look at **Scenario 03 (Secondary Click Target)** ($200 \times 70\text{ px}$).
  2. Perform a `PINCH_MIDDLE` gesture (thumb touching middle fingertip).
* **Expected Visual & Operational Behavior**:
  * A high-contrast context menu pops up beneath the button displaying options: `Select Option Alpha`, `Select Option Beta`, `Select Option Gamma`.
  * Card feedback updates to: `Status: Context menu displayed via PINCH_MIDDLE`.
* **Pass Criteria**: Context menu opens reliably on middle pinch and does not trigger on standard index pinch.

---

### TC-TB-04: Text Input & Keyboard Handoff
* **Objective**: Verify that focusing a text input field automatically suppresses gesture clicks and permits uninterrupted physical keyboard typing.
* **Prerequisites**: Physical keyboard connected.
* **Action Steps**:
  1. Fixate on **Scenario 04 (Text Input Field)** ($280 \times 60\text{ px}$) and execute `PINCH_INDEX` to focus.
  2. Verify that the yellow badge appears: `[KEYBOARD ACTIVE - TYPING MODE]`.
  3. Type `Multimodal HCI 2026` on the physical keyboard while waving hands in front of the camera.
  4. Perform `THUMBS_UP` gesture outside the box or click elsewhere to exit typing mode.
* **Expected Visual & Operational Behavior**:
  * The text input displays the typed string smoothly.
  * No accidental clicks, deletions, or erratic selections occur despite hand movement.
  * Multimodal control resumes cleanly upon defocusing.
* **Pass Criteria**: 100% suppression of gesture click injection while keyboard typing mode is engaged.

---

### TC-TB-05: Dropdown Option Selector
* **Objective**: Verify expansion of hierarchical menu and selection of an option using gaze targeting.
* **Prerequisites**: Testbench running.
* **Action Steps**:
  1. Fixate on **Scenario 05 (Dropdown Header)** and pinch index to expand.
  2. Shift eye gaze to the option: `Fatigue Adaptive Profile`.
  3. Perform `PINCH_INDEX` over the option.
* **Expected Visual & Operational Behavior**:
  * The dropdown list collapses.
  * The header updates to display: `Fatigue Adaptive Profile`.
  * Card feedback displays: `Status: Selected [Fatigue Adaptive Profile]`.
* **Pass Criteria**: Option is selected accurately without mis-selecting adjacent items.

---

### TC-TB-06: Kinetic Scroll Viewport
* **Objective**: Verify directional hands-free page and viewport scrolling via swipe gestures.
* **Prerequisites**: Hand tracking active.
* **Action Steps**:
  1. Fixate on **Scenario 06 (Scroll Viewport)** ($280 \times 130\text{ px}$).
  2. Perform a downward hand swipe gesture (`SWIPE_DOWN`).
  3. Perform an upward hand swipe gesture (`SWIPE_UP`).
* **Expected Visual & Operational Behavior**:
  * The telemetry bar displays `GESTURE TOKEN: SWIPE_DOWN` / `SWIPE_UP`.
  * The scroll container scrolls downward by 60 pixels per swipe, revealing lower telemetry items.
  * Card feedback updates: `Status: Scrolled DOWN (Pos: N px)`.
* **Pass Criteria**: Smooth, predictable scrolling matching gesture direction.

---

### TC-TB-07: Tier-2 High-Consequence Action Confirmation
* **Objective**: Verify that high-consequence / destructive actions require full visual dwell confirmation to prevent accidental activation.
* **Prerequisites**: Normal gaze tracking active.
* **Action Steps**:
  1. Look at **Scenario 07 (System Recalibrate / Reset Button)**.
  2. Maintain continuous eye gaze.
  3. Test 1 (Early Abort): Look away after $300\text{ ms}$ (halfway through sweep).
  4. Test 2 (Full Confirmation): Look continuously for full $600\text{ ms}$.
* **Expected Visual & Operational Behavior**:
  * The circular radial stroke sweeps clockwise from $0^\circ$ to $360^\circ$ over 600 ms.
  * In Test 1, the sweep immediately aborts and resets to 0; no action executes.
  * In Test 2, upon reaching 600 ms, the button flashes red, and card feedback confirms: `Status: TIER-2 ACTION EXECUTED (Reset Confirmed)`.
* **Pass Criteria**: Accidental or partial fixations cannot trigger execution; 600 ms dwell strictly required.

---

### TC-TB-08: Physical Hardware Mouse Takeover Override
* **Objective**: Verify that user movement of the physical hardware mouse immediately preempts multimodal control and registers negative supervisory feedback.
* **Prerequisites**: Physical mouse connected.
* **Action Steps**:
  1. Move the gaze reticle over the testbench.
  2. Physically grasp and move the hardware mouse.
* **Expected Visual & Operational Behavior**:
  * The hardware mouse pointer takes immediate precedence without stutter.
  * The telemetry bar switches `ACTIVE MODALITY` to `MOUSE_PRIORITY`.
  * Scenario 08 displays: `PHYSICAL MOUSE TAKEOVER ACTIVE`.
  * Feedback logs an implicit override event to the Python backend (`IMPLICIT_MOUSE_TAKEOVER`).
* **Pass Criteria**: Instantaneous ($< 16\text{ ms}$) handoff to physical mouse with zero cursor fighting.

---

## 6. Pass/Fail Sign-Off Matrix

| Test Identifier | Description | Verification Type | Status | Operator Signature |
|---|---|---|---|---|
| **AUT-TBS-01** | Hitbox Sizing ($\ge 140\text{ px} \times 60\text{ px}$) | Automated Static | PASS | Automated CI |
| **AUT-TBS-02** | Zero Emojis Validation | Automated Static | PASS | Automated CI |
| **AUT-TBS-03** | WebSocket Bridge Latency ($< 10\text{ ms}$) | Automated Benchmark | READY | Automated CI |
| **AUT-TBS-04** | Message Serialization Unit Test | Automated Unit | READY | Automated CI |
| **AUT-TBS-05** | Perception Pipeline Integration Test | Automated Integr | READY | Automated CI |
| **TC-TB-01** | Primary Action Button Activation | Manual Interactive | READY | Operator Review |
| **TC-TB-02** | Gaze Hover & Dwell Fixation Meter | Manual Interactive | READY | Operator Review |
| **TC-TB-03** | Secondary Click / Context Menu | Manual Interactive | READY | Operator Review |
| **TC-TB-04** | Text Input & Keyboard Handoff | Manual Interactive | READY | Operator Review |
| **TC-TB-05** | Dropdown Option Selector | Manual Interactive | READY | Operator Review |
| **TC-TB-06** | Kinetic Scroll Viewport | Manual Interactive | READY | Operator Review |
| **TC-TB-07** | Tier-2 High-Consequence Confirmation | Manual Interactive | READY | Operator Review |
| **TC-TB-08** | Physical Mouse Takeover Override | Manual Interactive | READY | Operator Review |

---

## 7. Sign-Off Authorization

Upon successful execution of all automated test suites and interactive manual test scenarios, the operator and lead engineer authorize acceptance:

* **Operator Name**: ___________________________
* **Date**: _______________
* **Final Verdict**: [  ] ACCEPTED    [  ] REJECTED
