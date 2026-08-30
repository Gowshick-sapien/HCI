"""
Personalization Profile Storage Manager.
Handles JSON serialization, schema validation, and atomic disk persistence for ProfileSnapshot.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from src.storage.schemas import ProfileSnapshot

logger = logging.getLogger(__name__)


class ProfileManager:
    """
    User Profile storage coordinator.
    Persists and loads validated ProfileSnapshot instances from the data/profiles directory.
    """

    DEFAULT_PROFILES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "profiles"

    def __init__(self, profiles_dir: Optional[Path] = None) -> None:
        self.profiles_dir = Path(profiles_dir) if profiles_dir else self.DEFAULT_PROFILES_DIR
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def get_profile_path(self, user_id: str) -> Path:
        """Returns the absolute file path for a user profile JSON."""
        clean_id = "".join(c for c in user_id if c.isalnum() or c in ("-", "_")).strip()
        if not clean_id:
            clean_id = "default_user"
        return self.profiles_dir / f"{clean_id}.json"

    def save_profile(self, profile: ProfileSnapshot) -> bool:
        """
        Saves a ProfileSnapshot to disk using atomic temporary file swap.

        Args:
            profile: ProfileSnapshot instance to serialize.

        Returns:
            True if write succeeded, False otherwise.
        """
        target_path = self.get_profile_path(profile.user_id)
        temp_path = target_path.with_suffix(".json.tmp")

        try:
            data_dict = profile.to_dict()
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data_dict, f, indent=2)

            # Atomic swap
            os.replace(temp_path, target_path)
            logger.info(f"Successfully saved profile for user '{profile.user_id}' to {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save profile for user '{profile.user_id}': {e}")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return False

    def load_profile(self, user_id: str) -> ProfileSnapshot:
        """
        Loads a ProfileSnapshot from disk. If not found or corrupt, returns default profile.

        Args:
            user_id: Unique user identifier.

        Returns:
            ProfileSnapshot instance.
        """
        target_path = self.get_profile_path(user_id)

        if not target_path.exists():
            logger.info(f"No profile found for user '{user_id}'. Generating default profile snapshot.")
            default_prof = ProfileSnapshot.create_default(user_id=user_id)
            self.save_profile(default_prof)
            return default_prof

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                raw_dict = json.load(f)

            profile = ProfileSnapshot.from_dict(raw_dict)
            logger.info(f"Successfully loaded profile for user '{user_id}' from {target_path}")
            return profile
        except Exception as e:
            logger.warning(f"Error reading profile file {target_path}: {e}. Returning default profile.")
            return ProfileSnapshot.create_default(user_id=user_id)


__all__ = ["ProfileManager"]
