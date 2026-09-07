# Test Bench Suite (TBS) Deliverables Specification

## Project Title
# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction

---

### Executive Overview

This document specifies the formal deliverables plan for the **Test Bench Suite (TBS)**. The Test Bench Suite provides a dedicated, isolated, professional desktop-and-web testing application designed to empirically validate hands-free gaze-and-gesture interaction across eight fundamental human-computer interaction (HCI) primitives.

The suite is decomposed into two distinct engineering deliverables:
* **TBS-D1**: Interactive Multimodal Frontend & UI Testing Primitives
* **TBS-D2**: Real-Time Bidirectional Streaming Bridge, Daemon & Verification Engine

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                            TEST BENCH SUITE (TBS) TAXONOMY                                       │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [TBS-D1: INTERACTIVE FRONTEND & UI TESTING PRIMITIVES]                                          │
│  • Minimalist, high-contrast dark-mode web application (HTML5, Vanilla CSS, JS).                │
│  • Generous ergonomic hitboxes (140px to 320px) optimized for ocular saccade tolerances.         │
│  • Standardized interaction targets: Primary Click, Hover Dwell, Secondary Context Menu,         │
│    Text Input & Keyboard Handoff, Dropdown Selector, Kinetic Scroll Container,                   │
│    Tier-2 Confirmation Gate, and Physical Mouse Takeover Zone.                                   │
│  • Live Telemetry Strip & State Display (Strictly ZERO emojis).                                  │
│                                                                                                  │
│  [TBS-D2: BIDIRECTIONAL STREAMING BRIDGE & VERIFICATION ENGINE]                                  │
│  • Asynchronous 60 FPS Python WebSocket & HTTP server (`src/testbench/server.py`).               │
│  • Real-time serialization of PerceptionFrame, GestureToken, and ComposedCommand.                │
│  • Ingestion of trial timestamps, movement times, and errors into Layer 4 & Layer 5.            │
│  • Standalone execution script (`scripts/run_testbench.py`).                                     │
│  • Automated unit and integration verification test suites.                                      │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Deliverable TBS-D1: Interactive Frontend & UI Testing Primitives

### 1.1 Scope & Purpose
Deliverable **TBS-D1** provides the user-facing testing surface. It exposes standardized interactive widgets designed to test the full range of multimodal actions without requiring raw operating system cursor hijacking.

### 1.2 Source Code Artifacts
* `src/testbench/frontend/index.html`: Semantic HTML5 layout containing the live telemetry banner and the 8-target interactive grid.
* `src/testbench/frontend/testbench.css`: Vanilla CSS stylesheet implementing dark-mode aesthetics, generous hitbox geometries, high-contrast focus rings, and zero decorative emojis.
* `src/testbench/frontend/testbench.js`: Client-side interaction engine managing WebSocket connection, gaze reticle positioning, bounding-box hit testing, dwell accumulation, and keyboard handoff.

### 1.3 Target Specifications & Geometry

| Target ID | Widget Type | Dimensions | Interaction Modality | Trigger Criteria | Visual / Operational Feedback |
|---|---|---|---|---|---|
| **TB-T01** | Primary Action Button | $200 \times 70\text{ px}$ | Gaze + `PINCH_INDEX` | Gaze within bounds + pinch gesture | State changes to "CLICKED", counter increments, timestamp logged. |
| **TB-T02** | Hover & Dwell Zone | $220 \times 80\text{ px}$ | Continuous Gaze Fixation | Gaze within bounds $\ge 300\text{ ms}$ | Linear progress bar fills ($0 \to 600\text{ ms}$), status: "HOVER ACTIVE". |
| **TB-T03** | Context Menu Target | $200 \times 70\text{ px}$ | Gaze + `PINCH_MIDDLE` | Gaze within bounds + middle pinch | High-contrast context popup opens with selectable actions. |
| **TB-T04** | Text Input & Handoff | $320 \times 60\text{ px}$ | Gaze Click $\to$ Keyboard | Primary click into input box | Displays "KEYBOARD ACTIVE (Typing Mode)", suppresses gesture clicks, resumes on exit or `THUMBS_UP`. |
| **TB-T05** | Option Dropdown | $240 \times 60\text{ px}$ | Gaze + Click $\to$ Select | Click expands list, gaze + pinch option | Updates selected option readout with verification pulse. |
| **TB-T06** | Scroll Viewport | $320 \times 220\text{ px}$ | Hand `SWIPE_UP` / `DOWN` | Swiping gesture in camera FOV | Container scrolls smoothly with velocity decay. |
| **TB-T07** | Tier-2 Reset Button | $220 \times 70\text{ px}$ | Gaze + 600ms Visual Dwell | Dwell confirmation must finish | Circular HUD ring completes $360^\circ$ sweep before execution. |
| **TB-T08** | Mouse Takeover Zone | Global Viewport | Physical Hardware Mouse | User moves hardware mouse | Multimodal steering yields immediately, logs negative feedback to SPRT. |

### 1.4 Acceptance Criteria
* **AC-TBS-D1.1**: All target bounding boxes must be $\ge 140\text{ px}$ in width and $\ge 60\text{ px}$ in height.
* **AC-TBS-D1.2**: Zero emojis, pictographs, or non-technical unicode glyphs in any UI element or text string.
* **AC-TBS-D1.3**: Frontend operates at 60 FPS with DOM latency $< 16.6\text{ ms}$.

---

## 2. Deliverable TBS-D2: Bidirectional Streaming Bridge & Verification Engine

### 2.1 Scope & Purpose
Deliverable **TBS-D2** implements the backend communication and execution bridge connecting the Python multimodal perception pipeline (Layers 1–5) to the interactive frontend at low latency, along with the automated testing framework.

### 2.2 Source Code Artifacts
* `src/testbench/server.py`: Asynchronous WebSocket server operating on `http://127.0.0.1:8080`.
* `src/testbench/__init__.py`: Public package exports.
* `scripts/run_testbench.py`: Master single-command launcher script.
* `tests/unit/test_testbench_server.py`: Unit test verifying server startup, serialization, and connection handling.
* `tests/integration/test_testbench_pipeline.py`: Integration test verifying perception-to-frontend event propagation.

### 2.3 Mathematical Data Contracts

1. **Server-to-Client Frame Packet (60 Hz JSON)**:
```json
{
  "type": "PERCEPTION_UPDATE",
  "timestamp_ms": 128456.2,
  "gaze_x": 960.0,
  "gaze_y": 540.0,
  "head_yaw": 1.2,
  "head_pitch": -0.8,
  "active_mode": "GESTURE",
  "gesture_token": "PINCH_INDEX",
  "gesture_confidence": 0.88,
  "command": "PRIMARY_CLICK",
  "dwell_ms": 450.0,
  "health_state": "STABLE"
}
```

2. **Client-to-Server Event Packet**:
```json
{
  "type": "INTERACTION_EVENT",
  "target_id": "TB-T01",
  "action_type": "PRIMARY_CLICK",
  "movement_time_ms": 520.4,
  "is_successful": true,
  "gaze_error_px": 12.4,
  "timestamp": 1788756000.12
}
```

### 2.4 Acceptance Criteria
* **AC-TBS-D2.1**: Streaming bridge network dispatch latency must be $< 10.0\text{ ms}$ over loopback.
* **AC-TBS-D2.2**: Graceful fallback: If camera is unavailable, supports `--simulated` mode for synthetic demonstration.
* **AC-TBS-D2.3**: 100% test pass rate across unit, integration, and latency test suites.

---

## 3. Traceability & Verification Protocol

| Deliverable | Test Identifier | Verification Method | Target | Pass Gate |
|---|---|---|---|---|
| **TBS-D1** | `AUT-TBS-01` | Automated Static Validation | Frontend Source Code | Zero emojis confirmed across all files. |
| **TBS-D1** | `AUT-TBS-02` | Hitbox Geometry Inspection | CSS / HTML Bounds | All interactive targets $\ge 140\text{ px}$. |
| **TBS-D2** | `AUT-TBS-03` | Automated Unit Test | `test_testbench_server.py` | WebSocket message encode/decode verified. |
| **TBS-D2** | `AUT-TBS-04` | Integration Test | `test_testbench_pipeline.py` | End-to-end event dispatch verified. |
| **TBS-D1/D2** | `TC-TB-01 to 08`| Live Interactive User Verification | `run_testbench.py` | All 8 interaction scenarios verified by operator. |

---

## 4. Conclusion
The TBS-D1 and TBS-D2 deliverables establish a rigorous, realistic, and safe testing bridge, enabling comprehensive validation of the multimodal HCI architecture prior to any operating system-wide deployment.
