"""
Layer 2 Calibration and Personalization Subsystem.
Provides 9-point gaze calibration, 3D neutral head pose ellipsoid estimation,
and interactive desktop calibration wizard.
"""

from src.calibration.gaze_calibrator import (
    CalibrationPointSample,
    GazeCalibrationResult,
    GazeCalibrator,
)
from src.calibration.head_pose_calibrator import (
    HeadPoseCalibrationResult,
    HeadPoseCalibrator,
)

__all__ = [
    "GazeCalibrator",
    "CalibrationPointSample",
    "GazeCalibrationResult",
    "HeadPoseCalibrator",
    "HeadPoseCalibrationResult",
]
