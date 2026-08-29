"""
Threaded Video Acquisition Engine.
Provides asynchronous, lock-free video capture with double buffering,
frame rate regulation, ambient illuminance estimation, and synthetic frame injection for CI testing.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional, Tuple
import cv2
import numpy as np

from src.capture.frame_types import CameraConfig, RawFrame

logger = logging.getLogger(__name__)


class VideoStream:
    """
    High-performance threaded camera stream.
    Decouples frame acquisition from downstream ML inference pipelines.
    """

    def __init__(self, config: Optional[CameraConfig] = None) -> None:
        self._config = config or CameraConfig()
        self._cap: Optional[cv2.VideoCapture] = None
        
        # Threading and synchronization primitives
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._frame_ready_event = threading.Event()
        self._lock = threading.Lock()
        
        # Buffer slots
        self._latest_raw_frame: Optional[RawFrame] = None
        self._frame_counter: int = 0
        self._dropped_frames: int = 0
        self._total_captured: int = 0
        
        # Performance metrics
        self._last_frame_timestamp: float = 0.0
        self._actual_fps: float = 0.0
        self._mean_capture_latency_ms: float = 0.0

    @property
    def is_running(self) -> bool:
        """Returns True if the background acquisition thread is active."""
        return self._thread is not None and self._thread.is_alive() and not self._stop_event.is_set()

    def start(self) -> bool:
        """
        Initializes hardware or synthetic video source and starts background capture thread.
        Returns True on successful startup.
        """
        if self.is_running:
            logger.warning("VideoStream is already active.")
            return True

        self._stop_event.clear()
        self._frame_ready_event.clear()

        if not self._config.use_synthetic_feeder:
            self._cap = cv2.VideoCapture(self._config.camera_id, cv2.CAP_DSHOW if cv2.os.name == 'nt' else cv2.CAP_ANY)
            if not self._cap.isOpened():
                # Fallback without CAP_DSHOW
                self._cap = cv2.VideoCapture(self._config.camera_id)

            if not self._cap.isOpened():
                logger.error(f"Failed to open video capture device ID: {self._config.camera_id}")
                return False

            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.frame_width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.frame_height)
            self._cap.set(cv2.CAP_PROP_FPS, self._config.target_fps)

        self._thread = threading.Thread(target=self._capture_worker, name="VideoStreamWorker", daemon=True)
        self._thread.start()
        logger.info(f"VideoStream worker thread started (Synthetic={self._config.use_synthetic_feeder}).")
        return True

    def stop(self, timeout_sec: float = 2.0) -> None:
        """Signals background thread to terminate and releases camera resources."""
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout_sec)
            self._thread = None

        if self._cap is not None:
            self._cap.release()
            self._cap = None

        self._frame_ready_event.clear()
        logger.info("VideoStream stopped and camera resources released.")

    def read_latest_frame(self, wait_timeout_sec: Optional[float] = None) -> Optional[RawFrame]:
        """
        Retrieves the newest captured frame.
        If wait_timeout_sec is provided, blocks until a new frame arrives or timeout expires.
        """
        if wait_timeout_sec is not None:
            self._frame_ready_event.wait(timeout=wait_timeout_sec)

        with self._lock:
            self._frame_ready_event.clear()
            return self._latest_raw_frame

    def feed_synthetic_frame(self, image: np.ndarray, timestamp: Optional[float] = None) -> RawFrame:
        """
        Directly injects a synthetic frame into the buffer.
        Useful for deterministic automated testing and benchmarking.
        """
        t_now = timestamp if timestamp is not None else time.time()
        self._frame_counter += 1
        
        h, w = image.shape[:2]
        ambient_lux = self._estimate_ambient_lux(image)
        
        raw_frame = RawFrame(
            frame_id=self._frame_counter,
            timestamp=t_now,
            width=w,
            height=h,
            ambient_lux=ambient_lux,
            capture_latency_ms=0.5,
            image=image.copy()
        )
        
        with self._lock:
            self._latest_raw_frame = raw_frame
            self._total_captured += 1
            self._frame_ready_event.set()
            
        return raw_frame

    def _capture_worker(self) -> None:
        """Internal daemon loop for continuous video acquisition."""
        target_period = 1.0 / max(1.0, float(self._config.target_fps))

        while not self._stop_event.is_set():
            t_start = time.perf_counter()

            if self._config.use_synthetic_feeder:
                time.sleep(target_period)
                continue

            if self._cap is None or not self._cap.isOpened():
                time.sleep(0.05)
                continue

            ret, frame = self._cap.read()
            t_acquired = time.time()
            capture_latency = (time.perf_counter() - t_start) * 1000.0

            if not ret or frame is None:
                time.sleep(0.005)
                continue

            self._frame_counter += 1
            h, w = frame.shape[:2]
            ambient_lux = self._estimate_ambient_lux(frame)

            raw_frame = RawFrame(
                frame_id=self._frame_counter,
                timestamp=t_acquired,
                width=w,
                height=h,
                ambient_lux=ambient_lux,
                capture_latency_ms=capture_latency,
                image=frame
            )

            with self._lock:
                self._latest_raw_frame = raw_frame
                self._total_captured += 1
                self._frame_ready_event.set()

            # Regulation loop to maintain target FPS without CPU spinning
            elapsed = time.perf_counter() - t_start
            sleep_time = target_period - elapsed
            if sleep_time > 0.001:
                time.sleep(sleep_time)

    @staticmethod
    def _estimate_ambient_lux(image: np.ndarray) -> float:
        """Estimates ambient illuminance lux from subsampled grayscale luminance."""
        try:
            # Subsample 1/8th for sub-millisecond execution
            sub = image[::8, ::8]
            if len(sub.shape) == 3 and sub.shape[2] == 3:
                # Fast integer perceptual luminance approximation: 0.299R + 0.587G + 0.114B (OpenCV is BGR)
                b = sub[:, :, 0].astype(np.float32)
                g = sub[:, :, 1].astype(np.float32)
                r = sub[:, :, 2].astype(np.float32)
                mean_luma = float(np.mean(0.299 * r + 0.587 * g + 0.114 * b))
            else:
                mean_luma = float(np.mean(sub))
            # Linear lux mapping: 0-255 luma -> approx 5-300 lux
            return float(np.clip(mean_luma * 1.15 + 5.0, 5.0, 500.0))
        except Exception:
            return 50.0

    def get_stats(self) -> dict:
        """Returns runtime performance statistics of the stream."""
        return {
            "is_running": self.is_running,
            "total_captured": self._total_captured,
            "frame_counter": self._frame_counter,
            "dropped_frames": self._dropped_frames,
            "width": self._config.frame_width,
            "height": self._config.frame_height,
            "target_fps": self._config.target_fps
        }

    def __enter__(self) -> VideoStream:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


__all__ = ["VideoStream"]
