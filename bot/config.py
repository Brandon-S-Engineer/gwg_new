"""Configuración global del bot."""

from pathlib import Path


SCREEN_WIDTH = 3840
SCREEN_HEIGHT = 2160

# SCREEN_WIDTH = 1920
# SCREEN_HEIGHT = 1080

INVENTORY_ROWS = 5
INVENTORY_COLS = 8
BANK_ROWS = 8
BANK_COLS = 10

DEFAULT_WAIT_TIMEOUT = 9.0
POLL_INTERVAL = 0.25
DEFAULT_MATCH_THRESHOLD = 0.8

MAX_ITERATIONS = 50  # -1 = infinito

RES_KEY = f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}"

PROJECT_ROOT = Path(__file__).parent.parent
ASSETS_DIR = Path(__file__).parent / "assets"
COORDS_PATH = Path(__file__).parent / "coords" / f"{RES_KEY}.json"
ITEMS_DIR = ASSETS_DIR / "items" / RES_KEY
STATES_DIR = ASSETS_DIR / "states" / RES_KEY
UI_DIR = ASSETS_DIR / "ui" / RES_KEY
