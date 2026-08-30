"""
Interactive Live Perception & Modality Arbitration Diagnostic Visualizer.
Runs the live webcam perception pipeline with real-time OpenCV HUD overlays,
allowing manual verification of Gaze Dwell, Gesture Classification, Modality Arbitration,
and Personalized Gaze Calibration.

Usage:
    python scripts/verify_perception_live.py
Controls:
    [q] / [ESC] : Exit visualizer
    [a]         : Toggle physical device arbitration hooks (pynput)
    [r]         : Reset tracking & reload calibration profile
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np

from src.capture.frame_types import CameraConfig
from src.capture.video_stream import VideoStream
from src.gesture.gesture_classifier import GestureClassifier
from src.gesture.modality_arbiter import ModalityArbiter
from src.perception.feature_pipeline import FeaturePipeline
from src.storage.profile_manager import ProfileManager
from src.storage.schemas import DeviceMode, GestureToken, ProfileSnapshot

# Hand landmark skeletal connections
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17)                                # Palm base
]


def draw_hud(
    frame: np.ndarray,
    perc_frame,
    gesture_out,
    arb_gesture,
    active_mode: DeviceMode,
    fps: float,
    latency_ms: float,
    arbitration_enabled: bool,
    is_calibrated: bool
) -> np.ndarray:
    """Renders comprehensive HUD telemetry on top of the live video frame."""
    canvas = frame.copy()
    h, w = canvas.shape[:2]

    # 1. Draw Top Telemetry Bar
    overlay = canvas.copy()
    cv2.rectangle(overlay, (0, 0), (w, 100), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.85, canvas, 0.15, 0, canvas)

    # Telemetry line 1: Mode & Active Gesture
    mode_colors = {
        DeviceMode.GESTURE: (0, 255, 0),       # Green
        DeviceMode.MOUSE_PRIORITY: (0, 215, 255),# Yellow/Gold
        DeviceMode.KEYBOARD: (255, 140, 0),    # Cyan/Blue
        DeviceMode.NO_ACTION: (0, 0, 255)      # Red
    }
    mode_color = mode_colors.get(active_mode, (200, 200, 200))

    arb_status = "[ARB: ON]" if arbitration_enabled else "[ARB: OFF]"
    calib_status = "[CALIBRATED]" if is_calibrated else "[UNCALIBRATED]"
    cv2.putText(canvas, f"MODE: {active_mode.value} {arb_status} {calib_status}", (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.52, mode_color, 2)
    cv2.putText(canvas, f"TOKEN: {arb_gesture.gesture_token.value}", (380, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (255, 255, 255), 2)

    # Telemetry line 2: Intent, Confidence, FPS
    conf_pct = int(arb_gesture.c_gesture * 100)
    cv2.putText(canvas, f"INTENT: {arb_gesture.action_intent}", (12, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 255, 200), 1)
    cv2.putText(canvas, f"CONF: {conf_pct}%", (230, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)
    cv2.putText(canvas, f"FPS: {fps:.0f} ({latency_ms:.1f}ms)", (380, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)

    # Telemetry line 3: Gaze & Anchor Coordinates
    gaze_u, gaze_v = perc_frame.gaze_screen_xy
    dwell_ms = int(perc_frame.gaze_dwell_ms)
    anchor_str = f"({int(perc_frame.gaze_anchor[0])}, {int(perc_frame.gaze_anchor[1])}) [LOCKED]" if perc_frame.gaze_anchor else "[SEARCHING...]"
    cv2.putText(canvas, f"GAZE: ({int(gaze_u)}, {int(gaze_v)}) | DWELL: {dwell_ms}ms | ANCHOR: {anchor_str}", (12, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 220, 120), 1)

    # Controls hint banner
    cv2.putText(canvas, "[Keys: 'q'=Quit | 'a'=Toggle Arbiter | 'r'=Reload Profile/Reset]", (12, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (160, 160, 160), 1)

    # 2. Draw Eye Landmarks on Face
    if perc_frame.eye.confidence > 0.0:
        lx, ly = int(perc_frame.eye.left_iris_center[0]), int(perc_frame.eye.left_iris_center[1])
        rx, ry = int(perc_frame.eye.right_iris_center[0]), int(perc_frame.eye.right_iris_center[1])
        cv2.circle(canvas, (lx, ly), 3, (0, 255, 255), -1)
        cv2.circle(canvas, (rx, ry), 3, (0, 255, 255), -1)
    else:
        cv2.putText(canvas, "[EYE BLINK / GAZE REST]", (w // 2 - 120, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # 3. Draw Head Pose Euler Angles
    head = perc_frame.head
    cv2.putText(
        canvas,
        f"HEAD: Y:{head.yaw:+.1f} P:{head.pitch:+.1f} R:{head.roll:+.1f}",
        (12, h - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (200, 200, 200),
        1
    )

    # 4. Draw Hand Skeleton & Keypoints
    if perc_frame.hand.is_detected and perc_frame.hand.raw_landmarks_21:
        pts = perc_frame.hand.raw_landmarks_21
        pixel_pts = [(int(lm[0] * w), int(lm[1] * h)) for lm in pts]

        # Draw bones
        for p1_idx, p2_idx in HAND_CONNECTIONS:
            cv2.line(canvas, pixel_pts[p1_idx], pixel_pts[p2_idx], (0, 180, 0), 2)

        # Draw joints
        for i, (px, py) in enumerate(pixel_pts):
            joint_color = (0, 255, 255) if i in [4, 8, 12, 16, 20] else (0, 255, 0)
            cv2.circle(canvas, (px, py), 4, joint_color, -1)

        # Highlight pinch point if pinch gesture active
        if "PINCH" in arb_gesture.gesture_token.value:
            thumb_px, thumb_py = pixel_pts[4]
            cv2.circle(canvas, (thumb_px, thumb_py), 16, (0, 255, 255), 2)

    # 5. Draw Dynamic Gaze Pointer and Gaze Anchor
    view_gx = int(np.clip((gaze_u / 1920.0) * w, 20, w - 20))
    view_gy = int(np.clip((gaze_v / 1080.0) * h, 110, h - 20))

    if perc_frame.gaze_confidence > 0.0:
        # 5A. Live Instantaneous Gaze Pointer (Green Circle & Cross)
        cv2.circle(canvas, (view_gx, view_gy), 6, (0, 255, 0), -1)
        cv2.drawMarker(canvas, (view_gx, view_gy), (0, 255, 0), cv2.MARKER_CROSS, 14, 1)

        # 5B. Dwell Countdown Ring at current fixation
        if dwell_ms > 0:
            dwell_progress = min(1.0, dwell_ms / 120.0)
            radius = int(10 + dwell_progress * 16)
            ring_color = (0, 255, 255) if dwell_progress < 1.0 else (0, 255, 0)
            cv2.circle(canvas, (view_gx, view_gy), radius, ring_color, 2)

        # 5C. Gaze Anchor (Locked Target)
        if perc_frame.gaze_anchor is not None:
            ax = int(np.clip((perc_frame.gaze_anchor[0] / 1920.0) * w, 20, w - 20))
            ay = int(np.clip((perc_frame.gaze_anchor[1] / 1080.0) * h, 110, h - 20))
            cv2.circle(canvas, (ax, ay), 16, (255, 255, 0), 2)
            cv2.drawMarker(canvas, (ax, ay), (255, 255, 0), cv2.MARKER_CROSS, 26, 2)
            cv2.putText(canvas, "GAZE_ANCHOR", (ax + 14, ay - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)

    return canvas


def main():
    print("================================================================================")
    print("  LIVE PERCEPTION & MODALITY ARBITRATION DIAGNOSTIC VISUALIZER")
    print("  Deliverable D1 & D2 Verification Tool")
    print("================================================================================")
    print("Initializing webcam video capture (640x480 @ 30 FPS)...")

    config = CameraConfig(camera_id=0, frame_width=640, frame_height=480, target_fps=30)
    stream = VideoStream(config)

    if not stream.start():
        print("ERROR: Could not open hardware camera. Ensure webcam is connected and accessible.")
        return

    pipeline = FeaturePipeline(camera_fov_degrees=60.0, screen_width=1920, screen_height=1080)
    classifier = GestureClassifier()
    arbiter = ModalityArbiter(enable_pynput_hooks=True)
    arbiter.start_listeners()

    profile_mgr = ProfileManager()
    profile = profile_mgr.load_profile("default_user")
    is_calibrated = profile.last_recalibration_timestamp > 0.0

    print(f"Loaded Profile for '{profile.user_id}': {'CALIBRATED' if is_calibrated else 'UNCALIBRATED DEFAULT'}")

    arbitration_enabled = True
    print("\nVisualizer active. Press 'q' or ESC in the window to quit.")
    print("Press 'a' to toggle physical input arbitration ON/OFF.")
    print("Press 'r' to reload calibration profile and reset tracking.\n")

    fps = 30.0
    frame_count = 0
    t_prev = time.perf_counter()

    try:
        while True:
            raw_frame = stream.read_latest_frame(wait_timeout_sec=0.1)

            if raw_frame is None or raw_frame.image is None:
                time.sleep(0.005)
                continue

            # 1. Layer 1 Perception
            t0 = time.perf_counter()
            perc_frame = pipeline.process_frame(raw_frame, profile=profile)

            # 2. Layer 1B Gesture Classification
            gesture_out = classifier.classify(perc_frame.hand, timestamp_ms=perc_frame.timestamp_ms)

            # 3. Active Modality Arbiter
            if arbitration_enabled:
                arb_gesture, active_mode = arbiter.arbitrate(gesture_out, timestamp_ms=perc_frame.timestamp_ms)
            else:
                arb_gesture = gesture_out
                active_mode = DeviceMode.GESTURE if gesture_out.gesture_token != GestureToken.FIST else DeviceMode.NO_ACTION

            latency_ms = (time.perf_counter() - t0) * 1000.0

            # FPS calculation
            frame_count += 1
            if frame_count % 15 == 0:
                now = time.perf_counter()
                fps = 15.0 / max(1e-4, now - t_prev)
                t_prev = now

            # Render HUD overlay
            hud_frame = draw_hud(
                raw_frame.image,
                perc_frame,
                gesture_out,
                arb_gesture,
                active_mode,
                fps,
                latency_ms,
                arbitration_enabled,
                is_calibrated
            )

            cv2.imshow("Adaptive Multimodal HCI - Deliverable D1 Verification HUD", hud_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('a'):
                arbitration_enabled = not arbitration_enabled
                print(f"Physical Device Arbitration toggled: {'ENABLED' if arbitration_enabled else 'DISABLED (BYPASS)'}")
            elif key == ord('r'):
                classifier.reset()
                pipeline.gaze_dwell_tracker.reset()
                profile = profile_mgr.load_profile("default_user")
                is_calibrated = profile.last_recalibration_timestamp > 0.0
                print(f"Profile reloaded: {'CALIBRATED' if is_calibrated else 'UNCALIBRATED DEFAULT'}. Tracking reset.")

    finally:
        print("\nShutting down stream and ML pipeline...")
        stream.stop()
        arbiter.stop_listeners()
        pipeline.close()
        cv2.destroyAllWindows()
        print("Visualizer exited cleanly.")


if __name__ == "__main__":
    main()
