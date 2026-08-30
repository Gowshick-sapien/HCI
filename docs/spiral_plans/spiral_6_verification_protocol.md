# Spiral 6 Verification Protocol: State-Aware Explainability HUD & Adaptive Overlay Suite (Deliverable E2)

## 1. Scope & Objective
This document outlines the formal test protocol for verifying **Deliverable E2 (State-Aware Explainability HUD & Adaptive Overlay Suite)**. It specifies automated unit tests, integration tests, latency benchmarks, and manual live verification procedures.

---

## 2. Formal Invariants Verification Matrix

| Test Identifier | Invariant ID | Target Component | Formal Acceptance Criterion | Verification Type |
|---|---|---|---|---|
| **AUT-E2-01** | `INV-E2.1` | `explainability_hud.py` | HUD paint event executes in $\le 1.0\text{ ms}$ over 1,000 continuous frames. | Automated Benchmark |
| **AUT-E2-02** | `INV-E2.2` | `explainability_hud.py` | Window flags enforce `FramelessWindowHint`, `WindowStaysOnTopHint`, and `WindowTransparentForInput`. | Automated Unit |
| **AUT-E2-03** | `INV-E2.3` | `confidence_bars.py` | Confidence bars correctly compute geometry, fill percentages, and labels without visual clipping. | Automated Unit |
| **AUT-E2-04** | `INV-E2.4` | `dwell_confirmation_ring.py` | Dwell ring calculates angular sweep $\theta(t) = 360^\circ \cdot \min(1.0, t / 600\text{ ms})$ centered on anchor. | Automated Unit |
| **AUT-E2-05** | `INV-E2.5` | `health_badge_renderer.py` | Health badge correctly maps states (`BOOTSTRAPPING` to `RECOVERING`) to distinct color palettes. | Automated Unit |
| **AUT-E2-06** | `INV-E2.6` | `hud_manager.py` | Full multi-threaded HUD manager updates telemetry buffers safely without mutex deadlocks. | Automated Integr |

---

## 3. Automated Test Descriptions

### AUT-E2-01: HUD Render Latency Benchmark
* **File**: `tests/benchmarks/test_hud_latency.py`
* **Assertion**: Verify that mean paint event latency is $\le 1.0\text{ ms}$ on CPU across 1,000 iterations.

### AUT-E2-02: Window Transparency & Flags Verification
* **File**: `tests/unit/test_explainability_hud.py`
* **Assertion**: Verify that the HUD window initializes with `Qt.WindowType.WindowTransparentForInput` and `Qt.WidgetAttribute.WA_TranslucentBackground`.

### AUT-E2-03: Modality Confidence Bars Geometry & Math
* **File**: `tests/unit/test_confidence_bars.py`
* **Assertion**: Verify that per-modality bars accurately represent raw confidence, weights, and fused score without layout overflow.

### AUT-E2-04: Dwell Progress Ring Angular Calculation
* **File**: `tests/unit/test_dwell_confirmation_ring.py`
* **Assertion**: Verify that ring progress scales linearly from $0^\circ$ to $360^\circ$ at $600\text{ ms}$ and clamps at $360^\circ$.

### AUT-E2-05: Health & Modality Badge Rendering
* **File**: `tests/unit/test_health_badge_renderer.py`
* **Assertion**: Verify that all 6 health states and 4 device modes produce valid color palettes and readable label strings.

### AUT-E2-06: End-to-End HUD Pipeline Integration
* **File**: `tests/integration/test_explainability_hud_pipeline.py`
* **Assertion**: Verify that simulated perception frames and feedback events propagate to the HUD visual components in real time.

---

## 4. Manual / Live Interactive Verification Procedures

### TC-MAN-01: Live Transparent HUD Overlay
* **Objective**: Verify that the HUD renders on top of the desktop as a translucent, click-through overlay.
* **Procedure**:
  1. Start live HUD overlay demo: `python scripts/verify_hud_overlay.py`.
  2. Click on a browser or background desktop window through the transparent area of the HUD.
* **Pass Criteria**: Mouse clicks pass through cleanly to underlying applications without being intercepted.

### TC-MAN-02: Live Dwell Confirmation Ring & Health Badge
* **Objective**: Verify that fixation on a screen location renders the circular dwell progress ring and active health state badge.
* **Procedure**:
  1. Fixate gaze on a target for $\ge 600\text{ ms}$.
  2. Observe the circular progress ring animating smoothly to $100\%$ confirmation.
* **Pass Criteria**: Progress ring follows gaze anchor smoothly and health state badge reflects current adaptation state.

---

## 5. Pass/Fail Sign-Off Matrix

| Test Identifier | Description | Verification Type | Status | Operator Signature |
|---|---|---|---|---|
| **AUT-E2-01** | HUD Render Latency ($\le 1.0\text{ ms}$) | Automated Benchmark | READY | Automated CI |
| **AUT-E2-02** | Click-Through Window Transparency Flags | Automated Unit | READY | Automated CI |
| **AUT-E2-03** | Confidence Bars Geometry & Normalization | Automated Unit | READY | Automated CI |
| **AUT-E2-04** | Dwell Progress Ring Sweep Calculation | Automated Unit | READY | Automated CI |
| **AUT-E2-05** | Health & Modality Badge Visual Mapping | Automated Unit | READY | Automated CI |
| **AUT-E2-06** | End-to-End HUD Pipeline Integration | Automated Integr | READY | Automated CI |
| **TC-MAN-01** | Live Transparent HUD Overlay & Click-Through | Manual Visual | READY | Operator Review |
| **TC-MAN-02** | Live Dwell Confirmation Ring & Health Badge | Manual Visual | READY | Operator Review |
