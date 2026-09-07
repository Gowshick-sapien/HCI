# Verification Protocol: Test Bench Suite (TBS-D1 & TBS-D2)

## 1. Scope & Objective
This document defines the formal verification protocol for **TBS-D1 (Interactive Frontend & UI Testing Primitives)** and **TBS-D2 (Bidirectional Streaming Bridge & Verification Engine)**.

---

## 2. Formal Invariants Verification Matrix

| Test Identifier | Invariant ID | Target Component | Acceptance Criterion | Verification Type |
|---|---|---|---|---|
| **AUT-TBS-01** | `INV-TBS.1` | `src/testbench/frontend/testbench.css` | All interactive hitboxes width $\ge 140\text{ px}$, height $\ge 60\text{ px}$. | Automated Static Check |
| **AUT-TBS-02** | `INV-TBS.2` | All TBS Files | Zero emoji unicode characters found across all files. | Automated Static Check |
| **AUT-TBS-03** | `INV-TBS.3` | `src/testbench/server.py` | Asynchronous WebSocket message encoding/decoding and dispatch latency $< 10.0\text{ ms}$. | Automated Unit Test |
| **AUT-TBS-04** | `INV-TBS.4` | `src/testbench/` | Multi-layer integration test from perception pipeline to WebSocket stream. | Automated Integration |

---

## 3. Manual Interactive Verification Procedures

### TC-TB-01: Primary Action Button Activation
* **Objective**: Verify that eye gaze fixation combined with an index pinch gesture triggers the primary action button.
* **Procedure**:
  1. Launch testbench: `python scripts/run_testbench.py`.
  2. Fixate gaze on **Target 1 (Primary Action Button)**.
  3. Perform `PINCH_INDEX` gesture.
* **Pass Criteria**: Button background pulses emerald, click counter increments (`Clicks: 1`), action is logged to telemetry strip.

### TC-TB-02: Gaze Hover & Dwell Fixation
* **Objective**: Verify that continuous gaze fixation smoothly increments the dwell meter and engages the hover state without requiring a gesture.
* **Procedure**:
  1. Fixate gaze on **Target 2 (Hover & Dwell Zone)**.
  2. Maintain fixation for $> 300\text{ ms}$.
* **Pass Criteria**: Linear dwell progress bar fills from $0 \to 600\text{ ms}$, status badge updates to `[HOVER ACTIVE]`.

### TC-TB-03: Secondary Click / Context Menu
* **Objective**: Verify that secondary gesture triggers a context menu modal.
* **Procedure**:
  1. Fixate gaze on **Target 3 (Context Menu Target)**.
  2. Execute `PINCH_MIDDLE` gesture.
* **Pass Criteria**: Context modal pops up displaying clean selectable options.

### TC-TB-04: Text Input & Keyboard Handoff
* **Objective**: Verify that focusing a text field suppresses gesture clicks and permits normal physical typing.
* **Procedure**:
  1. Gaze + pinch into **Target 4 (Text Input Field)**.
  2. Observe status indicator switching to `[KEYBOARD ACTIVE - TYPING MODE]`.
  3. Type characters on the physical keyboard while moving hands in camera view.
* **Pass Criteria**: Typed characters appear in the box, no accidental clicks are triggered by hand movement. Multimodal control resumes upon exiting or gesturing `THUMBS_UP`.

### TC-TB-05: Option Dropdown Selector
* **Objective**: Verify dropdown expansion and option selection.
* **Procedure**:
  1. Click to expand **Target 5 (Dropdown Selector)**.
  2. Look at an option ($180 \times 40\text{ px}$) and execute `PINCH_INDEX`.
* **Pass Criteria**: Dropdown collapses, selected item text updates with verification pulse.

### TC-TB-06: Continuous Kinetic Scroll Viewport
* **Objective**: Verify hands-free scrolling via directional swipe gestures.
* **Procedure**:
  1. Move hand into camera view over **Target 6 (Scroll Container)**.
  2. Perform `SWIPE_DOWN` and `SWIPE_UP` gestures.
* **Pass Criteria**: Content viewport scrolls smoothly in the direction of the swipe with velocity decay.

### TC-TB-07: Tier-2 High-Consequence Action Confirmation
* **Objective**: Verify that destructive actions require full 600ms visual dwell confirmation.
* **Procedure**:
  1. Focus gaze on **Target 7 (Tier-2 System Reset Target)**.
  2. Initiate pinch gesture.
* **Pass Criteria**: Circular dwell ring must complete full $360^\circ$ sweep before action executes. Releasing gaze early aborts the action without executing.

### TC-TB-08: Physical Mouse Takeover Override
* **Objective**: Verify seamless transition to physical mouse and negative feedback registration.
* **Procedure**:
  1. Move cursor with gaze.
  2. Physically move hardware mouse.
* **Pass Criteria**: System immediately yields to physical mouse, status indicator switches to `[MOUSE PRIORITY]`, and negative feedback is logged to the SPRT engine.

---

## 4. Pass/Fail Sign-Off Matrix

| Test Identifier | Description | Verification Type | Status | Operator Signature |
|---|---|---|---|---|
| **AUT-TBS-01** | Hitbox Geometry Inspection ($\ge 140\text{ px}$) | Automated Static | READY | Automated CI |
| **AUT-TBS-02** | Zero Emojis Validation | Automated Linter | READY | Automated CI |
| **AUT-TBS-03** | WebSocket Streaming Bridge Latency | Automated Unit | READY | Automated CI |
| **AUT-TBS-04** | End-to-End Perception Pipeline Bridge | Automated Integr | READY | Automated CI |
| **TC-TB-01** | Primary Action Button Activation | Manual Visual | READY | Operator Review |
| **TC-TB-02** | Gaze Hover & Dwell Fixation | Manual Visual | READY | Operator Review |
| **TC-TB-03** | Secondary Click / Context Menu | Manual Visual | READY | Operator Review |
| **TC-TB-04** | Text Input & Keyboard Handoff | Manual Visual | READY | Operator Review |
| **TC-TB-05** | Option Dropdown Selector | Manual Visual | READY | Operator Review |
| **TC-TB-06** | Continuous Kinetic Scroll Viewport | Manual Visual | READY | Operator Review |
| **TC-TB-07** | Tier-2 High-Consequence Action Confirmation | Manual Visual | READY | Operator Review |
| **TC-TB-08** | Physical Mouse Takeover Override | Manual Visual | READY | Operator Review |
