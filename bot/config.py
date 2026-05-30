"""
Configuración global del bot.

Todo lo que pueda cambiar entre setups (resolución, tamaños de inventario,
timeouts, paths de assets) vive aquí. Ningún otro módulo debería tener
constantes mágicas.
"""

from pathlib import Path


# --- Resolución de pantalla -------------------------------------------------
# El bot asume una sola pantalla a esta resolución. Si cambias de monitor
# o de resolución, este es el único lugar donde se toca.
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080


# --- Tamaño de inventario y banco -------------------------------------------
# Cada personaje puede tener bolsas/banco distintos. El bot descubre los
# slots usando estas dimensiones — NO asume posiciones hardcoded.
INVENTORY_ROWS = 5          # filas visibles del inventario
INVENTORY_COLS = 8          # columnas del inventario (estándar GW2)
BANK_ROWS = 8               # filas visibles del banco (configurable)
BANK_COLS = 10              # columnas del banco


# --- Timeouts ---------------------------------------------------------------
DEFAULT_WAIT_TIMEOUT = 9.0      # segundos para wait_for por defecto
POLL_INTERVAL = 0.25            # cada cuánto re-checar durante un wait
DEFAULT_MATCH_THRESHOLD = 0.8   # confianza mínima para template matching


# --- Paths ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
ASSETS_DIR = Path(__file__).parent / "assets"
ITEMS_DIR = ASSETS_DIR / "items"
STATES_DIR = ASSETS_DIR / "states"    # pantallas: login, char select, errores
UI_DIR = ASSETS_DIR / "ui"            # botones, opciones de menú contextual
