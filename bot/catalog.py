"""Manifiesto de templates: path + threshold + región."""

from dataclasses import dataclass
from pathlib import Path

from .config import DEFAULT_MATCH_THRESHOLD, ITEMS_DIR, STATES_DIR, UI_DIR
from .regions import (
    INVENTORY_AREA,
    BANK_AREA,
    CONFIRM_DIALOG_AREA,
    ERROR_DIALOG_AREA,
    Region,
)


@dataclass(frozen=True)
class Template:
    path: Path
    threshold: float = DEFAULT_MATCH_THRESHOLD
    default_region: Region | None = None


# Items
# LUCENT_MOTES = Template(ITEMS_DIR / "lucent_motes.png", 0.85, INVENTORY_AREA)

# Estados
# ERROR_FATAL = Template(STATES_DIR / "err_fatal.png", 0.8, ERROR_DIALOG_AREA)
# CHARACTER_SELECT = Template(STATES_DIR / "select_character.png", 0.8)
# PLAYING_MODE = Template(STATES_DIR / "playing_mode.png", 0.8)

# UI
# MENU_SELL = Template(UI_DIR / "menu_sell.png", 0.9)
# MENU_SALVAGE = Template(UI_DIR / "menu_salvage.png", 0.9)
# MENU_USE_ALL = Template(UI_DIR / "menu_use_all.png", 0.9)
# CONFIRM_OK = Template(UI_DIR / "confirm_ok.png", 0.9, CONFIRM_DIALOG_AREA)
