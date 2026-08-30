# Spiral 4 Implementation Plan: Multimodal Feedback Observer, Conflict Detector & Telemetry Engine

## Project Title
# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction

---

## 1. Scope & Objectives

Spiral 4 executes the implementation of **Deliverable D4: Layer 4 Implicit & Explicit Feedback Observer and Conflict Detector**, providing the self-evaluating supervisory feedback channel essential for the 8-element closed-loop architecture.

The architectural scope encompasses:
1. **Implicit Feedback Detector (`src/feedback/implicit_detector.py`)**:
   * Hardware takeover & mouse displacement preemption monitoring ($\Delta t \le 1200\text{ ms}$).
   * Keystroke reversal & rapid undo tracking (`Ctrl+Z`, `Escape`, `Backspace` within $\Delta t \le 2000\text{ ms}$).
   * Saccadic gaze escape detection ($\Delta r \ge 120\text{ px}$ within $400\text{ ms}$ post-action).
   * Interaction hesitation & abort pause estimation.
2. **Explicit Feedback Classifier (`src/feedback/explicit_classifier.py`)**:
   * Oscillatory head shake rejection detector (horizontal yaw oscillation $\ge \pm 12^\circ$ at $1.5-3.0\text{ Hz}$).
   * Oscillatory head nod confirmation detector (vertical pitch oscillation $\ge \pm 8^\circ$ at $1.2-2.5\text{ Hz}$).
   * Explicit gesture cancellation tokens.
3. **Temporal Correlator & Conflict Resolver (`src/feedback/feedback_correlator.py`)**:
   * Multi-stage temporal windowing: `REFRACTORY` ($[0, 200\text{ ms}]$), `CORRECTION` ($[200, 2000\text{ ms}]$), `STABILITY_EXPIRATION` ($[2000, 3000\text{ ms}]$).
   * Correlation of feedback signals with active `ActionContext` records.
   * Mapping to the 7-element Failure Taxonomy and Severity Grading (`SEV_1` to `SEV_5`).
4. **Feedback Telemetry Logger (`src/feedback/telemetry_logger.py`)**:
   * Thread-safe, non-blocking atomic JSONL logging to `logs/feedback_events.jsonl`.
5. **Master Feedback Observer Coordinator (`src/feedback/observer.py`)**:
   * Unified Layer 4 subsystem entrypoint emitting immutable `FeedbackEvent` instances to Layer 5.
6. **Automated Verification & Latency Suite (`tests/`)**:
   * Complete invariant test harness (INV-D4.1 to INV-D4.6) and sub-millisecond execution benchmarks.

---

## 2. Deliverables Breakdown for Spiral 4

| Deliverable Component | Architectural Scope | Key Codebase Artifacts | Invariant Target |
|---|---|---|---|
| **Implicit Detector** | Physical Takeover & Keystroke Undo | `src/feedback/implicit_detector.py` | Mouse displacement $> 16\text{ px}$ within $1.2\text{s}$ triggers `IMPLICIT_NEG` ($c_{\text{fb}} \ge 0.85$) |
| **Explicit Classifier** | Head Shake/Nod Kinematics | `src/feedback/explicit_classifier.py` | Head yaw/pitch zero-crossing frequency analysis ($1.5-3.0\text{ Hz}$), zero false fires during still posture |
| **Temporal Correlator** | Time-Window Binding & Taxonomy | `src/feedback/feedback_correlator.py` | Correct temporal association ($\Delta t \in [0.2, 2.0]\text{s}$); refractory guard suppresses false alarms ($< 200\text{ ms}$) |
| **Telemetry Logger** | Structured Telemetry Persistence | `src/feedback/telemetry_logger.py` | Non-blocking ring buffer, atomic JSONL writes under $1.0\text{ ms}$ |
| **Observer Coordinator** | Layer 4 Unified Subsystem Facade | `src/feedback/observer.py`, `src/feedback/__init__.py` | End-to-end feedback evaluation latency $\le 1.5\text{ ms}$ on CPU |
| **Verification & Latency Suite** | Unit, Integration & Latency Benchmarks | `tests/unit/test_implicit_detector.py`, `tests/unit/test_explicit_classifier.py`, `tests/unit/test_feedback_correlator.py`, `tests/benchmarks/test_feedback_latency.py` | 100% invariant pass rate, total Layer 4 latency $\le 1.5\text{ ms}$ |

---

## 3. Features to Design & Engineering Specifications

### 3.1 Implicit Feedback Detection Engine (`src/feedback/implicit_detector.py`)
* **Physical Mouse Takeover Detector**:
  * Monitors mouse movement and hardware clicks following an executed multimodal action.
  * If physical mouse displacement exceeds $\Delta r_{\text{mouse}} \ge 16\text{ px}$ within $\Delta t_{\text{takeover}} \le 1200\text{ ms}$ of an action execution:
    * Incurs `FeedbackType.IMPLICIT_NEG` with failure mode `FailureMode.USER_OVERRIDE`.
    * Confidence: $c_{\text{fb}} = \text{clip}(1.0 - \Delta t / 1.2, \ 0.50, \ 0.95)$.
* **Rapid Keystroke Undo / Cancellation Detector**:
  * Ingests hardware keyboard hooks (`Ctrl+Z`, `Escape`, `Backspace`, `Ctrl+Y`).
  * `Ctrl+Z` within $\Delta t \le 2000\text{ ms} \implies$ `FeedbackType.IMPLICIT_NEG`, `FailureMode.FALSE_ACTIVATION`, severity `SEV_3_MODERATE`.
  * `Escape` within $\Delta t \le 1500\text{ ms} \implies$ `FeedbackType.IMPLICIT_NEG`, `FailureMode.WRONG_TARGET`, severity `SEV_2_MINOR`.
* **Saccadic Gaze Escape Detector**:
  * Evaluates post-click gaze deviation: if user gaze moves $\Delta r_{\text{gaze}} > 150\text{ px}$ away from the target within $400\text{ ms}$, signals target mismatch (`FailureMode.WRONG_TARGET`).
* **Positive Implicit Confirmation (Stability Expiration)**:
  * If no correction, takeover, or undo occurs within $\Delta t_{\text{stable}} = 2000\text{ ms}$, emits `FeedbackType.IMPLICIT_POS` with confidence $c_{\text{fb}} = 0.80$ (`FailureMode.NONE`).

### 3.2 Explicit Head Gesture Feedback Classifier (`src/feedback/explicit_classifier.py`)
* **Head Shake Rejection Detector (`EXPLICIT_NEG`)**:
  * Tracks rolling buffer of head yaw Euler angles over the last $1200\text{ ms}$.
  * Detects sinusoidal zero-crossing oscillations:
    * Peak-to-peak amplitude $A_{\text{yaw}} \ge 24.0^\circ$ ($\pm 12^\circ$).
    * Zero-crossing count $\ge 3$ within $1.0\text{ s}$ ($f \approx 1.5 - 3.0\text{ Hz}$).
  * Emits `FeedbackType.IMPLICIT_NEG` (or `EXPLICIT_NEG`), confidence $c_{\text{fb}} = 0.95$, `FailureMode.USER_OVERRIDE`.
* **Head Nod Confirmation Detector (`EXPLICIT_POS`)**:
  * Tracks rolling buffer of head pitch Euler angles.
  * Detects vertical sinusoidal zero-crossing oscillations ($A_{\text{pitch}} \ge 16.0^\circ$, zero-crossings $\ge 3$ within $1.0\text{ s}$).
  * Emits `FeedbackType.IMPLICIT_POS`, confidence $c_{\text{fb}} = 0.90$.

### 3.3 Temporal Feedback Correlator (`src/feedback/feedback_correlator.py`)
* **Temporal Windowing Architecture**:
  * Ingests executed `ActionContext` records into a thread-safe sliding history buffer (capacity $N=20$).
  * Enforces the 3 temporal stages:
    1. **Refractory Window ($0 \le \Delta t < 200\text{ ms}$)**: Discards spurious micro-events to prevent false alarms during mechanical motor follow-through.
    2. **Correction Window ($200\text{ ms} \le \Delta t \le 2000\text{ ms}$)**: Active evaluation window for physical takeovers, undos, and head gestures.
    3. **Stability Expiration Window ($2000\text{ ms} < \Delta t \le 3000\text{ ms}$)**: Marks uncontested actions as successful (`IMPLICIT_POS`).
* Generates immutable `FeedbackEvent` records.

### 3.4 Feedback Telemetry Logger (`src/feedback/telemetry_logger.py`)
* Asynchronous JSONL event logger writing to `logs/feedback_events.jsonl`.
* Thread-safe double buffering with automatic rotation if file size exceeds $50\text{ MB}$.

---

## 4. Codebase Architecture & File Modifications

```
d:\HCI\
+-- logs/
¦   +-- feedback_events.jsonl                   # Auto-generated runtime telemetry stream
+-- src/
¦   +-- feedback/                               # [EXPAND] Layer 4 Subsystem
¦       +-- __init__.py                         # Module exports
¦       +-- implicit_detector.py                # Hardware takeover & keystroke undo detector
¦       +-- explicit_classifier.py              # Head shake/nod kinematic classifier
¦       +-- feedback_correlator.py              # Temporal windowing & action correlation
¦       +-- telemetry_logger.py                 # Non-blocking JSONL telemetry writer
¦       +-- observer.py                         # Unified Layer 4 Feedback Observer facade
+-- tests/
¦   +-- unit/
¦   ¦   +-- test_implicit_detector.py           # Unit tests for takeover & undo detection
¦   ¦   +-- test_explicit_classifier.py         # Unit tests for head shake/nod oscillation
¦   ¦   +-- test_feedback_correlator.py         # Unit tests for temporal windowing
¦   ¦   +-- test_telemetry_logger.py            # Unit tests for JSONL persistence
¦   +-- integration/
¦   ¦   +-- test_feedback_observer_pipeline.py  # End-to-end Action -> Observer -> FeedbackEvent
¦   +-- benchmarks/
¦       +-- test_feedback_latency.py            # Latency benchmark (<= 1.5 ms)
+-- docs/
    +-- spiral_plans/
        +-- spiral_4_implementation_plan.md     # This publication document
```

---

## 5. Traceability Matrix & Formal Verification Invariants

| Invariant ID | Target Component | Acceptance Specification | Formal Verification Method |
|---|---|---|---|
| **INV-D4.1** | `implicit_detector.py` | Physical mouse movement $\ge 16\text{ px}$ within $1.2\text{s}$ triggers `IMPLICIT_NEG` ($c_{\text{fb}} \ge 0.80$). | Unit test injecting hardware mouse displacement post-action. |
| **INV-D4.2** | `implicit_detector.py` | Keystroke `Ctrl+Z` within $2.0\text{s}$ triggers `IMPLICIT_NEG` with `FALSE_ACTIVATION`. | Unit test simulating key event sequence. |
| **INV-D4.3** | `explicit_classifier.py` | Head yaw oscillation $\ge \pm 12^\circ$ ($1.5-3.0\text{ Hz}$) reliably classifies head shake (`c_fb >= 0.90`). | Synthetic sinusoidal Euler angle trace evaluation. |
| **INV-D4.4** | `feedback_correlator.py` | Refractory period ($< 200\text{ ms}$) strictly suppresses false correction events. | Unit test verifying event discard within refractory window. |
| **INV-D4.5** | `feedback_correlator.py` | Uncontested actions past $2000\text{ ms}$ automatically resolve to `IMPLICIT_POS`. | Timer expiration test verifying positive feedback emission. |
| **INV-D4.6** | `feedback_latency.py` | Layer 4 total evaluation cycle latency $\le 1.5\text{ ms}$ on CPU. | Micro-benchmark across 1,000 evaluation cycles. |

---

## 6. Step-by-Step Implementation Sequence

```
+--------------------------------------------------------------------------------------------------+
¦                                SPIRAL 4 IMPLEMENTATION WORKFLOW                                  ¦
+--------------------------------------------------------------------------------------------------¦
¦                                                                                                  ¦
¦  [PHASE 1: Core Detection Engines]                                                               ¦
¦   +-- Step 1.1: Implicit Feedback Detector (`src/feedback/implicit_detector.py`)                 ¦
¦   +-- Step 1.2: Explicit Head Gesture Classifier (`src/feedback/explicit_classifier.py`)         ¦
¦                                                                                                  ¦
¦  [PHASE 2: Temporal Correlation & Windowing]                                                     ¦
¦   +-- Step 2.1: Temporal Correlator & Failure Mapper (`src/feedback/feedback_correlator.py`)     ¦
¦   +-- Step 2.2: JSONL Telemetry Logger (`src/feedback/telemetry_logger.py`)                      ¦
¦                                                                                                  ¦
¦  [PHASE 3: Unified Layer 4 Observer Facade]                                                      ¦
¦   +-- Step 3.1: Feedback Observer Coordinator (`src/feedback/observer.py`)                       ¦
¦   +-- Step 3.2: Export public APIs in `src/feedback/__init__.py`                                 ¦
¦                                                                                                  ¦
¦  [PHASE 4: Automated Verification & Latency Benchmarks]                                          ¦
¦   +-- Step 4.1: Unit test suites for all detection engines (`tests/unit/`)                       ¦
¦   +-- Step 4.2: End-to-end integration test (`test_feedback_observer_pipeline.py`)               ¦
¦   +-- Step 4.3: Micro-benchmark execution (INV-D4.6 <= 1.5 ms)                                   ¦
¦   +-- Step 4.4: Deliverable D4 Packaging & README Sign-Off                                       ¦
¦                                                                                                  ¦
+--------------------------------------------------------------------------------------------------+
```

---

## 7. Verification Strategy & Acceptance Sign-Off

Upon completion of Phases 1–4, the entire test suite will be executed:
```powershell
pytest tests/ -v
pytest -s tests/benchmarks/test_feedback_latency.py
```
* **Acceptance Criterion**: 100% test pass rate across all unit and integration tests, verified refractory suppression ($< 200\text{ ms}$), and latency budget $\le 1.5\text{ ms}$.
