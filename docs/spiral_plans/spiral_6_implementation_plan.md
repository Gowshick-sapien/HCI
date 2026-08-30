# Spiral 6 Implementation Plan: State-Aware Explainability HUD & Adaptive Overlay Suite (Deliverable E2)

## 1. Executive Overview
Spiral 6 delivers **Deliverable E2 (State-Aware Explainability HUD & Adaptive Overlay Suite)**. Building upon the core perception (D1), fusion (D2), calibration (D3), feedback observation (D4), and adaptation (D5) layers, Spiral 6 provides a lightweight, GPU-less, semi-transparent desktop overlay rendering live confidence breakdowns, Tier-2 visual dwell countdown rings, active system health status badges, and device modality indicators without interfering with standard desktop window interaction.

---

## 2. Architectural Structure & Module Decomposition

### 2.1 Explainability HUD Overlay (`src/ui/explainability_hud.py`)
* **Frameless Transparent Window**: Built with PySide6 using `Qt.WindowType.FramelessWindowHint`, `Qt.WindowType.WindowStaysOnTopHint`, `Qt.WindowType.WindowTransparentForInput`, and `Qt.WindowType.SubWindow` with `WA_TranslucentBackground`.
* **Zero Input Interception**: Click-through transparency ensuring standard mouse clicks and keyboard events pass through unimpeded to underlying desktop applications.
* **Low-Overhead 60 FPS Render Loop**: Decoupled QTimer paint loop maintaining $\le 1.0\text{ ms}$ render overhead per frame.

---

### 2.2 Animated Modality Confidence Visualizer (`src/ui/confidence_bars.py`)
* **Live Contribution Bars**: Renders real-time weighted confidence meters for each active modality channel:
  * Gaze ($w_{\text{eye}} \cdot s_{\text{gaze}}$)
  * Head Pose ($w_{\text{head}} \cdot s_{\text{head}}$)
  * Hand Gesture ($w_{\text{hand}} \cdot s_{\text{hand}}$)
* **Smooth Interpolation**: Dual exponential smoothing on bar transitions to prevent visual flickering during high-frequency sensor updates.

---

### 2.3 Visual Dwell Confirmation Ring (`src/ui/dwell_confirmation_ring.py`)
* **Spatial Tracking**: Positions a circular progress countdown ring centered directly over the active gaze fixation anchor $(x_{\text{anchor}}, y_{\text{anchor}})$.
* **Tier-2 Safety Confirmation**: Animates visual progress over the $600\text{ ms}$ dwell period for high-consequence / destructive commands before execution.
* **Color Transitions**: Interpolates ring color from searching cyan to locked green upon intentionality confirmation.

---

### 2.4 System Health & Modality State Badges (`src/ui/health_badge_renderer.py`, `src/ui/keyboard_handoff_indicator.py`)
* **Health Badge**: Displays current Layer 5 System Health State (`BOOTSTRAPPING`, `LEARNING`, `IMPROVING`, `STABLE`, `DRIFTING`, `RECOVERING`) with color-coded typography.
* **Modality & Handoff Indicator**: Displays active `DeviceMode` (`GESTURE`, `MOUSE_OVERRIDE`, `KEYBOARD_HANDOFF`, `COOLDOWN`) providing immediate transparency into why multimodal signals may be throttled or suppressed.

---

### 2.5 Master HUD Coordinator (`src/ui/hud_manager.py`, `src/ui/__init__.py`)
* Connects the pipeline streams (`PerceptionFrame`, `ComposedCommand`, `FeedbackEvent`, `AssessmentMetrics`) to the HUD overlay components via thread-safe double-buffering.

---

## 3. Formal Invariant Specifications

| Invariant ID | Target Component | Formal Acceptance Criterion | Verification Method |
|---|---|---|---|
| **INV-E2.1** | `explainability_hud.py` | HUD rendering loop consumes $\le 1.0\text{ ms}$ per frame on CPU without dropping below 30 FPS. | Automated Benchmark |
| **INV-E2.2** | `explainability_hud.py` | Window flags enforce full click-through transparency (`WindowTransparentForInput`). | Automated Unit Test |
| **INV-E2.3** | `confidence_bars.py` | Modality confidence bars accurately map $s_i \in [0.0, 1.0]$ and modality weights $w_i \in [0.05, 0.85]$. | Automated Unit Test |
| **INV-E2.4** | `dwell_confirmation_ring.py` | Progress ring calculates exact angular sweep $\theta(t) = 360^\circ \cdot \min(1.0, t / 600\text{ ms})$ centered on anchor. | Automated Unit Test |
| **INV-E2.5** | `health_badge_renderer.py` | Color palettes and status strings correctly map all 6 health states and 4 macro policies. | Automated Unit Test |
| **INV-E2.6** | `hud_manager.py` | Multi-threaded pipeline update rate remains continuous with zero frame stutter or deadlocks. | Automated Integration |

---

## 4. Implementation Phasing

### Phase 1: Core HUD Window & Click-Through Transparency
* Implement `ExplainabilityHUDWindow` with frameless translucent PySide6 architecture.
* Implement window attribute flags and native desktop click-through behavior.
* Unit tests in `tests/unit/test_explainability_hud.py`.

### Phase 2: Confidence Bars & Health State Badges
* Implement `ConfidenceBarsRenderer` with smoothing interpolation.
* Implement `HealthBadgeRenderer` and `KeyboardHandoffIndicator`.
* Unit tests in `tests/unit/test_confidence_bars.py` and `tests/unit/test_health_badge_renderer.py`.

### Phase 3: Spatial Dwell Progress Ring & HUD Manager
* Implement `DwellConfirmationRing` with geometric angular interpolation.
* Implement `HUDManager` facade coordinating all visualizer components.
* Unit tests in `tests/unit/test_dwell_confirmation_ring.py`.

### Phase 4: Integration, Benchmarking & Public Exports
* Integration test `tests/integration/test_explainability_hud_pipeline.py`.
* Render latency benchmark `tests/benchmarks/test_hud_latency.py`.
* Public module exports in `src/ui/__init__.py`.
