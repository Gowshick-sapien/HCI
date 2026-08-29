# Spiral 3 Implementation Plan: Calibration Wizard, Personalization Engine, Multimodal Command Composer & Simplex Projection

## Project Title
# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction

---

## 1. Scope & Objectives

Spiral 3 executes the implementation of **Deliverable D2 (Calibration & Personalization Engine)** and **Deliverable D3 (Multimodal Command Composer & Simplex Projection Engine)**, bridging Layer 1 perception with Layer 2 user personalization, Stage 3A spatial-intent binding, and mathematically exact probability simplex projection.

The architectural scope encompasses:
1. **Layer 2 Calibration Engine (`src/calibration/`)**:
   * Interactive 9-Point Desktop Gaze Calibration Wizard (PySide6 UI).
   * Affine ($3 \times 3$) and Second-Order Polynomial ($2 \times 6$) Gaze Mapping Solvers.
   * 3D Neutral Head Pose Ellipsoid Extractor $\mathcal{E}_{\text{head}} = (\boldsymbol{\mu}_{\text{head}}, \boldsymbol{\Sigma}_{\text{head}}^{-1})$.
   * Personalized Kinematic Threshold Estimators (Pinch Distance $\theta_{\text{pinch}}$, Dwell Threshold $\tau_{\text{dwell}}$).
2. **Personalization Profile Management (`src/storage/profile_manager.py`)**:
   * Profile persistence, schema validation, and runtime hot-reloading for `ProfileSnapshot`.
3. **Stage 3A Multimodal Command Composer (`src/fusion/command_composer.py`)**:
   * Formal binding of Layer 1 spatial targets (**WHERE**: `gaze_anchor`) and Layer 1B intent (**WHAT**: `gesture_token`) into immutable `ComposedCommand` instances.
   * Hard enforcement of Gaze-Gesture Spatial Invariants (Midas Touch suppression for unanchored spatial clicks).
4. **Exact 1D Box-Constrained Simplex Projection Engine (`src/fusion/simplex_projection.py`)**:
   * Deterministic $O(N \log N)$ Michelot/Duchi Euclidean projection onto the probability simplex $\Delta^K$.
   * Strict adherence to probability axioms ($\sum_{i=1}^K w_i = 1.0, \ w_i \ge 0$) within floating-point precision ($10^{-9}$).
5. **Multimodal Confidence Fusion Subsystem (`src/fusion/confidence_fusion.py`)**:
   * Multi-source weighted fusion of ocular ($s_{\text{gaze}}$), head pose ($s_{\text{head}}$), and gesture ($s_{\text{gesture}}$) confidence metrics.
6. **Automated Verification, UI Testing & Micro-Benchmark Suite (`tests/`)**:
   * 100% test coverage across mathematical invariants (INV-D2.1 to INV-D3.5), composite pipeline integration, and sub-millisecond optimization benchmarks.

---

## 2. Deliverables Breakdown for Spiral 3

| Deliverable Component | Architectural Scope | Key Codebase Artifacts | Invariant Target |
|---|---|---|---|
| **Layer 2 Gaze Calibrator** | 9-Point Affine & Polynomial Gaze Fitting | `src/calibration/gaze_calibrator.py`, `src/utils/geometry.py` | Calibration residual error $\le 35\text{ px}$ RMSE on 1080p, solver execution $\le 5.0\text{ ms}$ |
| **Layer 2 Head Pose Calibrator** | Neutral Head Ellipsoid Fitting | `src/calibration/head_pose_calibrator.py` | Inverts $3 \times 3$ covariance $\boldsymbol{\Sigma}$, validates positive-definiteness $\det(\boldsymbol{\Sigma}) > 0$ |
| **Interactive Calibration Wizard** | PySide6 Fullscreen Interactive GUI | `src/calibration/calibration_wizard.py` | 9-target visual countdown ($1.5\text{s}$ per point), outlier rejection ($2\sigma$ filter), interactive UX |
| **Profile Manager** | Profile Persistence & Loading | `src/storage/profile_manager.py` | JSON atomic writes, schema validation, zero-copy snapshot retrieval |
| **Stage 3A Command Composer** | Gaze-Gesture Intent-Spatial Binding | `src/fusion/command_composer.py` | Binds spatial `gaze_anchor` to spatial gestures iff $\text{dwell} \ge \tau_{\text{dwell}}$; execution latency $\le 0.5\text{ ms}$ |
| **Simplex Projection Engine** | Exact $O(N \log N)$ Probability Optimizer | `src/fusion/simplex_projection.py` | $\sum_{i=1}^K w_i = 1.0 \pm 10^{-9}$, $w_i \in [0, 1]$, execution time $\le 0.05\text{ ms}$ |
| **Multimodal Confidence Fusion** | Weighted Tri-Modal Confidence Fusion | `src/fusion/confidence_fusion.py` | $S_{\text{fused}} \in [0.0, 1.0]$, strictly monotonic w.r.t. component scores |
| **Verification & Latency Suite** | Unit, Integration & Latency Benchmarks | `tests/unit/test_gaze_calibrator.py`, `tests/unit/test_simplex_projection.py`, `tests/unit/test_command_composer.py`, `tests/benchmarks/test_fusion_latency.py` | 100% invariant pass rate, total Stage 3A latency $\le 1.0\text{ ms}$ |

---

## 3. Features to Design & Engineering Specifications

### 3.1 9-Point Desktop Gaze Calibration & Polynomial Solver (`src/calibration/gaze_calibrator.py`)
* **Interactive 9-Point Grid Topology**:
  * Displays 9 target points uniformly distributed across the screen:
    $$\mathbf{P}_{\text{targets}} = \left\{ (0.1W, 0.1H), (0.5W, 0.1H), (0.9W, 0.1H), (0.1W, 0.5H), (0.5W, 0.5H), (0.9W, 0.5H), (0.1W, 0.9H), (0.5W, 0.9H), (0.9W, 0.9H) \right\}$$
  * At each calibration point, collects $N=30$ frames ($1.0\text{s}$ acquisition at 30 FPS) of raw ocular feature vectors $\mathbf{f}_k = (r_{\text{iris}, x}, r_{\text{iris}, y}, \text{yaw}, \text{pitch})$.
  * Applies $2\sigma$ Mahalanobis outlier rejection to discard blink/saccade corrupted frames.
* **Dual Mapping Solvers**:
  1. **Affine Transformation Solver ($\mathbf{M}_{\text{gaze}} \in \mathbb{R}^{3 \times 3}$)**:
     $$\begin{bmatrix} u \\ v \\ 1 \end{bmatrix} = \mathbf{M}_{\text{gaze}} \begin{bmatrix} r_{\text{iris}, x} \\ r_{\text{iris}, y} \\ 1 \end{bmatrix}$$
     Solves via Ordinary Least Squares (OLS) with Singular Value Decomposition (SVD):
     $$\mathbf{M}_{\text{gaze}} = \mathbf{Y} \mathbf{X}^T (\mathbf{X} \mathbf{X}^T)^{-1}$$
  2. **Second-Order Polynomial Solver ($\mathbf{W}_{\text{gaze}} \in \mathbb{R}^{2 \times 6}$)**:
     $$\mathbf{\phi}(r_x, r_y) = \begin{bmatrix} 1 & r_x & r_y & r_x^2 & r_y^2 & r_x r_y \end{bmatrix}^T$$
     $$\begin{bmatrix} u \\ v \end{bmatrix} = \mathbf{W}_{\text{gaze}} \mathbf{\phi}(r_x, r_y)$$
     Accounts for non-linear ocular curvature and wide-angle webcam peripheral distortion.
* **Calibration Quality Metrics**:
  * Evaluates Root Mean Squared Error (RMSE) across all 9 validation points:
    $$\text{RMSE}_{\text{gaze}} = \sqrt{\frac{1}{N}\sum_{i=1}^N \left( (u_i - \hat{u}_i)^2 + (v_i - \hat{v}_i)^2 \right)}$$
  * Invariant Target: $\text{RMSE}_{\text{gaze}} \le 35.0\text{ px}$ on standard 1080p desktop monitors.

### 3.2 3D Head Pose Neutral Calibration Engine (`src/calibration/head_pose_calibrator.py`)
* Collects $K=60$ frames of comfortable neutral sitting posture Euler angles $(\text{yaw}_k, \text{pitch}_k, \text{roll}_k)$.
* Computes sample mean vector $\boldsymbol{\mu}_{\text{head}} \in \mathbb{R}^3$ and sample covariance matrix $\boldsymbol{\Sigma}_{\text{head}} \in \mathbb{R}^{3 \times 3}$:
  $$\boldsymbol{\mu}_{\text{head}} = \frac{1}{K}\sum_{k=1}^K \mathbf{y}_k, \quad \boldsymbol{\Sigma}_{\text{head}} = \frac{1}{K-1}\sum_{k=1}^K (\mathbf{y}_k - \boldsymbol{\mu}_{\text{head}})(\mathbf{y}_k - \boldsymbol{\mu}_{\text{head}})^T + \epsilon \mathbf{I}_3$$
* Regularizes $\boldsymbol{\Sigma}_{\text{head}}$ with Tikhonov diagonal ridge ($\epsilon = 10^{-4}$) ensuring positive-definiteness.
* Computes precision matrix $\boldsymbol{\Sigma}_{\text{head}}^{-1}$ via Cholesky decomposition.

### 3.3 Interactive PySide6 Calibration Wizard (`src/calibration/calibration_wizard.py`)
* Fullscreen, frameless, transparent-overlay PySide6 Qt GUI.
* Visual presentation:
  * Sleek dark mode backdrop with animated glowing calibration rings.
  * 9 sequential target locations with smooth animated transitions.
  * Real-time gaze fixation countdown ring ($1.5\text{ seconds}$ hold per target).
  * Audio/visual confirmation feedback on point acquisition.
  * Summary review screen displaying calibration accuracy grade, RMSE error, and visual accuracy heatmap.

### 3.4 Personalization Profile Manager (`src/storage/profile_manager.py`)
* Manages user profiles saved under `data/profiles/{user_id}.json`.
* Schema validation: verifies all matrix dimensions, non-negative threshold values, and timestamp bounds.
* Atomic file writes using temporary file swap to eliminate profile corruption during crashes.
* Emits immutable `ProfileSnapshot` instances consumed downstream by Layer 1, Layer 2, and Layer 3.

### 3.5 Stage 3A Multimodal Command Composer (`src/fusion/command_composer.py`)
* Merges spatial target data from Layer 1 `PerceptionFrame` and action semantics from Layer 1B `GestureClassification`.
* **Binding Logic & Modality Disambiguation**:
  * **Spatial Action Tokens (`PINCH_INDEX`, `PINCH_MIDDLE`, `PINCH_RING`, `PINCH_HOLD`)**:
    * If `gesture.requires_gaze_target == True`:
      * Checks if `perception.gaze_anchor` is locked ($\text{dwell} \ge \tau_{\text{dwell}}$).
      * If locked: binds command to spatial anchor: $\mathbf{P}_{\text{target}} = \text{gaze\_anchor}$, `is_gaze_anchored = True`.
      * If NOT locked: marks as `UNBOUND_SPATIAL_INTENT` or suppresses execution (prevents accidental clicks during saccades).
  * **Global Non-Spatial Tokens (`OPEN_PALM`, `THUMBS_UP`, `SWIPE_LEFT`, `SWIPE_RIGHT`, `SWIPE_UP`, `SWIPE_DOWN`)**:
    * `requires_gaze_target == False`: directly emits command with `target_screen_xy = None`, `is_gaze_anchored = False`.
  * **Rest State (`FIST`, `NONE`)**:
    * Emits `action_type = ActionType.NO_ACTION`, `target_screen_xy = None`.
* **Composed Command Output Schema (`ComposedCommand`)**:
  * Generates a frozen, immutable `ComposedCommand` dataclass containing: `command_id`, `timestamp_ms`, `gesture_token`, `action_type`, `target_screen_xy`, `is_gaze_anchored`, `c_gesture`, `c_gaze`, `fused_confidence`.

### 3.6 Exact 1D Box-Constrained Simplex Projection Optimizer (`src/fusion/simplex_projection.py`)
* Implements Michelot's exact algorithm for projecting arbitrary weight vectors $\mathbf{y} \in \mathbb{R}^K$ onto the probability simplex:
  $$\Delta^K = \left\{ \mathbf{w} \in \mathbb{R}^K : \sum_{i=1}^K w_i = 1, \ w_i \ge 0 \quad \forall i \right\}$$
* **Algorithm Steps**:
  1. Sort vector $\mathbf{y}$ in descending order: $u_1 \ge u_2 \ge \dots \ge u_K$.
  2. Compute cumulative sum array: $s_j = \sum_{i=1}^j u_i$.
  3. Find maximum index $\rho = \max \left\{ j \in \{1, \dots, K\} : u_j + \frac{1 - s_j}{j} > 0 \right\}$.
  4. Compute exact Lagrange multiplier $\lambda^* = \frac{1 - s_\rho}{\rho}$.
  5. Compute projected weights: $w_i = \max(0, y_i + \lambda^*)$ for all $i \in \{1, \dots, K\}$.
* Guarantees:
  * Exact convergence in $O(K \log K)$ operations.
  * Zero numerical divergence or negative weights ($w_i \ge 0$).
  * Execution latency $\le 0.05\text{ ms}$ for $K \le 10$.

### 3.7 Multimodal Confidence Fusion Subsystem (`src/fusion/confidence_fusion.py`)
* Ingests tri-modal confidence vector $\mathbf{s} = \begin{bmatrix} s_{\text{gaze}} & s_{\text{head}} & s_{\text{gesture}} \end{bmatrix}^T \in [0, 1]^3$.
* Ingests personalized/adaptive weight vector $\mathbf{w} \in \Delta^3$.
* Enforces simplex constraint via `SimplexProjectionEngine`.
* Computes weighted fused confidence:
  $$S_{\text{fused}} = \mathbf{w}^T \mathbf{s} = w_{\text{gaze}} s_{\text{gaze}} + w_{\text{head}} s_{\text{head}} + w_{\text{gesture}} s_{\text{gesture}}$$
* Computes confidence variance and bounds checking.

---

## 4. Codebase Architecture & File Modifications

```
d:\HCI\
+-- configs/
¦   +-- default_profile.yaml                    # Base profile defaults
+-- src/
¦   +-- calibration/                            # [NEW] Layer 2 Calibration Subsystem
¦   ¦   +-- __init__.py                         # Module exports
¦   ¦   +-- gaze_calibrator.py                  # 9-point affine & polynomial OLS solver
¦   ¦   +-- head_pose_calibrator.py             # Neutral head ellipsoid solver
¦   ¦   +-- calibration_wizard.py               # Interactive PySide6 calibration GUI
¦   +-- fusion/                                 # [EXPAND] Layer 3 & Stage 3A Subsystem
¦   ¦   +-- __init__.py                         # Module exports
¦   ¦   +-- simplex_projection.py               # Exact 1D Box-Constrained Simplex Engine
¦   ¦   +-- confidence_fusion.py                # Tri-modal weighted confidence fusion
¦   ¦   +-- command_composer.py                 # Stage 3A Gaze-Gesture Command Composer
¦   +-- storage/
¦       +-- profile_manager.py                  # [NEW] ProfileSnapshot JSON serializer/loader
+-- tests/
¦   +-- unit/
¦   ¦   +-- test_gaze_calibrator.py             # Unit tests for affine/polynomial OLS
¦   ¦   +-- test_head_pose_calibrator.py        # Unit tests for ellipsoid estimation
¦   ¦   +-- test_profile_manager.py             # Unit tests for profile JSON lifecycle
¦   ¦   +-- test_simplex_projection.py          # Unit tests for exact simplex invariants
¦   ¦   +-- test_confidence_fusion.py           # Unit tests for confidence aggregation
¦   ¦   +-- test_command_composer.py            # Unit tests for Stage 3A binding
¦   +-- integration/
¦   ¦   +-- test_calibration_fusion_flow.py     # End-to-end Calibration -> Profile -> Composer
¦   +-- benchmarks/
¦       +-- test_fusion_latency.py              # Micro-benchmarks for Composer & Simplex (< 1.0 ms)
+-- docs/
    +-- spiral_plans/
        +-- spiral_3_implementation_plan.md     # This publication document
```

---

## 5. Traceability Matrix & Formal Verification Invariants

| Invariant ID | Target Component | Acceptance Specification | Formal Verification Method |
|---|---|---|---|
| **INV-D2.1** | `gaze_calibrator.py` | 9-point polynomial solver produces RMSE $\le 35.0\text{ px}$ on synthetic/simulated ground truth. | Automated Unit Test with synthetic 9-point data + Gaussian noise ($\sigma = 2.0\text{ px}$). |
| **INV-D2.2** | `head_pose_calibrator.py` | Covariance matrix is positive definite: $\det(\boldsymbol{\Sigma}_{\text{head}}) > 0$ and all eigenvalues $\lambda_i > 0$. | Cholesky factorization and eigenvalue checks on sample traces. |
| **INV-D2.3** | `profile_manager.py` | Profile save/load roundtrip preserves all 7 personalization fields without precision loss ($10^{-6}$). | Unit test saving synthetic `ProfileSnapshot` to disk and asserting equality after reload. |
| **INV-D3.1** | `command_composer.py` | Spatial gestures (`PINCH_INDEX`, `PINCH_MIDDLE`) MUST NOT emit active screen clicks without `gaze_anchor`. | Assert `ComposedCommand.is_gaze_anchored == False` and click suppressed when `dwell_ms < tau_dwell`. |
| **INV-D3.2** | `command_composer.py` | Non-spatial gestures (`OPEN_PALM`, `THUMBS_UP`, `SWIPE`) emit valid commands regardless of gaze state. | Assert immediate command composition without requiring gaze anchor. |
| **INV-D3.3** | `simplex_projection.py` | Exact sum-to-one invariant: $|\sum_{i=1}^K w_i - 1.0| \le 10^{-9}$ for any random input vector $\mathbf{y} \in \mathbb{R}^K$. | 1,000 Monte Carlo random vector projections with arbitrary magnitudes $\in [-1000, 1000]$. |
| **INV-D3.4** | `simplex_projection.py` | Non-negativity invariant: $w_i \ge 0.0 \ \forall i$ for all projected weights. | Assertion check across all Monte Carlo test vectors. |
| **INV-D3.5** | `fusion_latency.py` | Combined Stage 3A Command Composer + Simplex Projection execution time $\le 1.0\text{ ms}$ on CPU. | High-resolution performance benchmark across 1,000 iterations. |

---

## 6. Architectural Decisions for Spiral 3

### Decision 1: Fallback Mapping Hierarchy for Gaze Projection
* **Decision**: If no personalized calibration matrix is present, the pipeline uses the dynamic baseline gaze mapping with Eye-Head coordination. When a valid calibration profile is loaded, `FeaturePipeline` seamlessly switches to the high-precision 2nd-order polynomial mapping $\mathbf{W}_{\text{gaze}}$.
* **Rationale**: Ensures the system remains fully operational out of the box before calibration, while offering pixel-level precision once calibrated.

### Decision 2: GUI Technology for Interactive Calibration Wizard
* **Decision**: Implement the Calibration Wizard using PySide6 (Qt6) in frameless fullscreen mode (`Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint`).
* **Rationale**: PySide6 is already installed in the environment, provides hardware-accelerated 60 FPS rendering of animated calibration rings, and integrates directly with Python asynchronous worker threads.

### Decision 3: Exact Michelot Simplex Projection Algorithm vs. Softmax
* **Decision**: Use Michelot's exact Euclidean projection algorithm rather than Softmax.
* **Rationale**: Softmax cannot produce exact zero weights (it always assigns non-zero probabilities to inactive or noisy modalities). Michelot's projection allows noisy modalities (e.g. eye blink $s_{\text{gaze}} = 0$) to receive exact $0.0$ weight while preserving mathematically exact probability geometry.

---

## 7. Step-by-Step Implementation Sequence

```
+--------------------------------------------------------------------------------------------------+
¦                                SPIRAL 3 IMPLEMENTATION WORKFLOW                                  ¦
+--------------------------------------------------------------------------------------------------¦
¦                                                                                                  ¦
¦  [PHASE 1: Core Mathematical Optimizers]                                                         ¦
¦   +-- Step 1.1: Exact Simplex Projection Engine (`src/fusion/simplex_projection.py`)             ¦
¦   +-- Step 1.2: Tri-Modal Weighted Confidence Fusion (`src/fusion/confidence_fusion.py`)         ¦
¦                                                                                                  ¦
¦  [PHASE 2: Calibration Solvers & Algorithms]                                                     ¦
¦   +-- Step 2.1: 9-Point Affine & Polynomial Gaze Solver (`src/calibration/gaze_calibrator.py`)   ¦
¦   +-- Step 2.2: Neutral Head Pose Ellipsoid Solver (`src/calibration/head_pose_calibrator.py`)  ¦
¦                                                                                                  ¦
¦  [PHASE 3: Personalization Profile Manager]                                                      ¦
¦   +-- Step 3.1: Profile Persistence & Validation (`src/storage/profile_manager.py`)              ¦
¦   +-- Step 3.2: Integration into `ProfileSnapshot` contracts                                     ¦
¦                                                                                                  ¦
¦  [PHASE 4: Stage 3A Multimodal Command Composer]                                                 ¦
¦   +-- Step 4.1: Spatial-Intent Binding Logic (`src/fusion/command_composer.py`)                  ¦
¦                                                                                                  ¦
¦  [PHASE 5: Interactive Calibration Wizard GUI]                                                   ¦
¦   +-- Step 5.1: Fullscreen PySide6 Calibration Wizard (`src/calibration/calibration_wizard.py`)  ¦
¦                                                                                                  ¦
¦  [PHASE 6: Verification, Integration & Benchmarks]                                               ¦
¦   +-- Step 6.1: Unit test suites for all 6 new modules (`tests/unit/`)                           ¦
¦   +-- Step 6.2: End-to-end integration test (`test_calibration_fusion_flow.py`)                  ¦
¦   +-- Step 6.3: Micro-benchmark execution (INV-D3.5 <= 1.0 ms)                                   ¦
¦   +-- Step 6.4: Deliverables D2 and D3 Packaging Manifest                                        ¦
¦                                                                                                  ¦
+--------------------------------------------------------------------------------------------------+
```

---

## 8. Verification Strategy & Acceptance Sign-Off

Upon completion of Phases 1–6, the entire test suite will be executed:
```powershell
pytest tests/ -v
pytest -s tests/benchmarks/test_fusion_latency.py
```
* **Acceptance Criterion**: 100% test pass rate across all unit and integration tests, verified Simplex invariants ($|\sum w_i - 1| \le 10^{-9}$), and latency budget $\le 1.0\text{ ms}$.
