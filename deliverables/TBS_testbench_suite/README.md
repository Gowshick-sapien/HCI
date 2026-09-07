# Deliverable Release Package: Test Bench Suite (TBS)
## Deliverables: TBS-D1 & TBS-D2

---

## 1. Executive Summary
The **Test Bench Suite (TBS)** provides a dedicated, isolated, professional testing environment specifically designed to validate hands-free gaze-and-gesture interaction across eight fundamental human-computer interaction (HCI) primitives.

* **TBS-D1**: Interactive Multimodal Frontend & UI Testing Primitives (HTML5, Vanilla CSS, JS).
* **TBS-D2**: Real-Time Bidirectional Streaming Bridge, Daemon & Verification Engine.

---

## 2. Included Source Code Artifacts

### TBS-D1 (Frontend & Interaction Primitives)
* `src/testbench/frontend/index.html`: Semantic HTML5 layout with live telemetry header and 8-target grid.
* `src/testbench/frontend/testbench.css`: Dark-mode stylesheet with generous hitboxes ($140\text{ px} - 320\text{ px}$) and zero emojis.
* `src/testbench/frontend/testbench.js`: Client-side interaction engine, hit testing, and WebSocket telemetry sync.

### TBS-D2 (Backend Bridge & Engine)
* `src/testbench/server.py`: Asynchronous Python WebSocket and HTTP server streaming at 60 FPS.
* `src/testbench/__init__.py`: Package exports for `TestbenchServer`.
* `scripts/run_testbench.py`: Master single-command launcher script.
* `tests/unit/test_testbench_server.py`: Unit test verifying server startup and serialization.
* `tests/integration/test_testbench_pipeline.py`: Multi-layer integration test.

---

## 3. Formal Acceptance Invariants

| Invariant ID | Target Component | Acceptance Criterion | Verification Method |
|---|---|---|---|
| **INV-TBS.1** | `testbench.css` | All 8 target hitboxes have minimum width $\ge 140\text{ px}$ and height $\ge 60\text{ px}$. | Automated Static Check |
| **INV-TBS.2** | All TBS Files | Strictly ZERO emojis present in HTML, CSS, JS, Python, or logs. | Automated Linter |
| **INV-TBS.3** | `server.py` | Local WebSocket dispatch latency $< 10.0\text{ ms}$ over loopback. | Automated Benchmark |
| **INV-TBS.4** | `testbench.js` | Gaze hover accumulation triggers active state at $300\text{ ms}$ and dwell at $600\text{ ms}$. | Automated Unit Test |
| **INV-TBS.5** | `testbench.js` | Text input focus engages `KEYBOARD_HANDOFF` and suppresses gesture clicks. | Automated Unit Test |

---

## 4. Verification Protocol
* Automated Unit Tests: `tests/unit/test_testbench_server.py`
* Integration Test: `tests/integration/test_testbench_pipeline.py`
* Interactive Manual Suite: Scenarios `TC-TB-01` through `TC-TB-08` in `docs/spiral_plans/tbs_verification_protocol.md`.
