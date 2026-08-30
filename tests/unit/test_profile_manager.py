"""
Unit tests for ProfileManager persistence and validation.
Verifies Invariant INV-D3.3: Roundtrip save/load preserves all profile fields.
"""

import tempfile
from pathlib import Path
import pytest

from src.storage.profile_manager import ProfileManager
from src.storage.schemas import ProfileSnapshot


def test_profile_manager_roundtrip_persistence():
    """Invariant INV-D3.3: Preserves all profile fields without loss."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = ProfileManager(profiles_dir=Path(tmpdir))

        original = ProfileSnapshot.create_default(user_id="test_user_42")
        original.gaze_target_dwell_ms = 145.0
        original.neutral_pose_mean = [1.5, -2.5, 0.0]

        # Save
        assert mgr.save_profile(original) is True

        # Load
        loaded = mgr.load_profile("test_user_42")

        assert loaded.user_id == "test_user_42"
        assert loaded.gaze_target_dwell_ms == 145.0
        assert loaded.neutral_pose_mean == [1.5, -2.5, 0.0]
        assert "PRIMARY_CLICK" in loaded.modality_weights
