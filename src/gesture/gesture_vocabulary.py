"""
Gesture Vocabulary Definition and Dictionary Loader.
Parses configs/gesture_vocabulary.yaml and exposes immutable token metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from src.storage.schemas import ActionType, GestureToken


@dataclass(frozen=True)
class GestureTokenDefinition:
    """Immutable definition of a single vocabulary gesture token."""
    token: GestureToken
    mapped_action: ActionType
    requires_gaze_target: bool
    default_threshold: float
    is_rest_state: bool = False
    description: str = ""


class GestureVocabulary:
    """
    Registry of all 13 supported multimodal gesture tokens.
    Loads definitions from YAML with hardcoded safe defaults.
    """

    def __init__(self, config_path: Optional[Path | str] = None) -> None:
        self._tokens: Dict[GestureToken, GestureTokenDefinition] = {}
        if config_path is not None:
            self.load_from_yaml(config_path)
        else:
            default_path = Path("configs/gesture_vocabulary.yaml")
            if default_path.exists():
                self.load_from_yaml(default_path)
            else:
                self._load_fallback_defaults()

    def load_from_yaml(self, config_path: Path | str) -> None:
        """Loads and validates token definitions from a YAML configuration file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Gesture vocabulary config file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        vocab_data = data.get("gesture_vocabulary", {}).get("tokens", {})
        self._tokens.clear()

        for token_name, item in vocab_data.items():
            token_enum = GestureToken(token_name)
            action_enum = ActionType(item["mapped_action"])
            req_gaze = bool(item.get("requires_gaze_target", True))
            thresh = float(item.get("default_threshold", 0.70))
            is_rest = bool(item.get("is_rest_state", False))
            desc = str(item.get("description", ""))

            self._tokens[token_enum] = GestureTokenDefinition(
                token=token_enum,
                mapped_action=action_enum,
                requires_gaze_target=req_gaze,
                default_threshold=thresh,
                is_rest_state=is_rest,
                description=desc
            )

    def _load_fallback_defaults(self) -> None:
        """Initializes default 13-token vocabulary if config file is missing."""
        defaults = [
            (GestureToken.PINCH_INDEX, ActionType.PRIMARY_CLICK, True, 0.70, False, "Index pinch"),
            (GestureToken.PINCH_MIDDLE, ActionType.RIGHT_CLICK, True, 0.70, False, "Middle pinch"),
            (GestureToken.PINCH_RING, ActionType.DOUBLE_CLICK, True, 0.75, False, "Ring pinch"),
            (GestureToken.PINCH_PINKY, ActionType.MIDDLE_CLICK, True, 0.75, False, "Pinky pinch"),
            (GestureToken.PINCH_HOLD, ActionType.DRAG_START, True, 0.70, False, "Pinch hold"),
            (GestureToken.PINCH_RELEASE, ActionType.DRAG_DROP, True, 0.70, False, "Pinch release"),
            (GestureToken.SWIPE_LEFT, ActionType.NAVIGATE_PREVIOUS, False, 0.65, False, "Swipe left"),
            (GestureToken.SWIPE_RIGHT, ActionType.NAVIGATE_NEXT, False, 0.65, False, "Swipe right"),
            (GestureToken.SWIPE_UP, ActionType.SCROLL_UP, False, 0.60, False, "Swipe up"),
            (GestureToken.SWIPE_DOWN, ActionType.SCROLL_DOWN, False, 0.60, False, "Swipe down"),
            (GestureToken.OPEN_PALM, ActionType.HOVER, True, 0.65, False, "Open palm"),
            (GestureToken.FIST, ActionType.NO_ACTION, False, 0.80, True, "Rest state fist"),
            (GestureToken.THUMBS_UP, ActionType.CONFIRM_SUBMIT, False, 0.75, False, "Thumbs up confirm"),
        ]
        self._tokens = {
            t[0]: GestureTokenDefinition(t[0], t[1], t[2], t[3], t[4], t[5]) for t in defaults
        }

    def get_definition(self, token: GestureToken) -> GestureTokenDefinition:
        """Retrieves metadata definition for a specific gesture token."""
        if token not in self._tokens:
            raise KeyError(f"Unknown gesture token: {token}")
        return self._tokens[token]

    def all_tokens(self) -> List[GestureToken]:
        """Returns list of all registered vocabulary tokens."""
        return list(self._tokens.keys())

    def __contains__(self, token: GestureToken) -> bool:
        return token in self._tokens

    def __len__(self) -> int:
        return len(self._tokens)


__all__ = ["GestureVocabulary", "GestureTokenDefinition"]
