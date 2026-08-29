# Deliverable D3 Release Package: Layer 2 Calibration Wizard & Personalization Engine

## 1. Executive Summary
Deliverable **D3** implements **Layer 2 of the Multimodal Architecture**, encompassing:
* **9-Point Desktop Gaze Calibration Solvers (`src/calibration/gaze_calibrator.py`)**: Computes affine ($3 \times 3$) and 2nd-order polynomial ($2 \times 6$) projection matrices via Least Squares SVD.
* **3D Neutral Head Pose Calibrator (`src/calibration/head_pose_calibrator.py`)**: Fits neutral sitting ellipsoid $\mathcal{E}_{\text{head}} = (\boldsymbol{\mu}_{\text{head}}, \boldsymbol{\Sigma}_{\text{head}}^{-1})$ with positive-definite covariance regularization.
* **Interactive Fullscreen PySide6 Calibration Wizard (`src/calibration/calibration_wizard.py`)**: Frameless desktop Qt GUI with animated 9-point targets and live fixation countdown rings.
* **Personalization Profile Manager (`src/storage/profile_manager.py`)**: Manages atomic JSON persistence, schema validation, and loading for `ProfileSnapshot`.

---

## 2. Included Source Code Artifacts
* `src/calibration/gaze_calibrator.py`: 9-point OLS SVD affine and polynomial gaze mapping solver.
* `src/calibration/head_pose_calibrator.py`: Sample covariance and Cholesky inversion solver.
* `src/calibration/calibration_wizard.py`: Interactive PySide6 fullscreen 9-point wizard.
* `src/calibration/__init__.py`: Public API exports.
* `src/storage/profile_manager.py`: Atomic JSON persistence and loader.

---

## 3. Formal Acceptance Invariants

| Invariant ID | Target Component | Formal Specification | Pass Criterion |
|---|---|---|---|
| **INV-D3.1** | `gaze_calibrator.py` | Calibration residual error $\text{RMSE}_{\text{gaze}} \le 35.0\text{ px}$ on 1080p display. | Verified against synthetic/simulated ground truth. |
| **INV-D3.2** | `head_pose_calibrator.py` | Head covariance matrix $\boldsymbol{\Sigma}_{\text{head}}$ is strictly positive-definite ($\det > 0, \lambda_i > 0$). | Successful Cholesky decomposition $\boldsymbol{\Sigma} = \mathbf{L}\mathbf{L}^T$. |
| **INV-D3.3** | `profile_manager.py` | Complete roundtrip profile save and load preserves all 7 personalization fields. | Equality assertions verified within float tolerance ($10^{-6}$). |
| **INV-D3.4** | `calibration_wizard.py` | Non-blocking asynchronous acquisition thread with animated countdowns. | Zero GUI freezing, responsive 60 FPS Qt render loop. |

---

## 4. Test & Integration Verification
* Automated Unit Tests: `tests/unit/test_gaze_calibrator.py`, `tests/unit/test_head_pose_calibrator.py`, `tests/unit/test_profile_manager.py`
* Multi-Layer Integration: `tests/integration/test_calibration_fusion_flow.py`
