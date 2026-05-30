"""
Regiones nombradas de la pantalla.

Una Region es un rectángulo (x, y, w, h) con un nombre. El resto del bot
NUNCA usa coordenadas sueltas: pide "encuéntrame el ícono X en la región
INVENTORY_AREA" y vision.py se encarga del resto.

Las coordenadas se medirán sobre una screenshot de referencia a 1080p
en la fase 3. Por ahora solo está la forma de Region y los nombres.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    w: int
    h: int

    def contains(self, point: tuple[int, int]) -> bool:
        px, py = point
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def as_pyautogui_region(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.w, self.h)


# --- Áreas principales ------------------------------------------------------
# Valores placeholder — se rellenan en la fase 3 con la screenshot de ref.
INVENTORY_AREA = Region(0, 0, 0, 0)
BANK_AREA = Region(0, 0, 0, 0)
TP_SELL_PANEL = Region(0, 0, 0, 0)
TP_BUY_PANEL = Region(0, 0, 0, 0)

# Zona donde viven los kits de salvage en la barra de utilidad
KIT_SLOT_AREA = Region(0, 0, 0, 0)

# Diálogos: en vez de probar 6 confirm_button_N, buscamos el botón aquí
CONFIRM_DIALOG_AREA = Region(0, 0, 0, 0)
ERROR_DIALOG_AREA = Region(0, 0, 0, 0)

# Menú contextual del click derecho — se busca relativo al punto del click
CONTEXT_MENU_OFFSET = Region(0, 0, 0, 0)  # offset desde el click derecho


def slot_grid(area: Region, rows: int, cols: int) -> list[tuple[int, int]]:
    """
    Calcula el centro de cada slot de una grilla uniforme dentro de un área.
    Reemplaza las listas hardcoded tipo salvage_exotics_coords_list de v2.
    Devuelve [(x, y), ...] en orden fila-mayor.
    """
    raise NotImplementedError("Pendiente fase 3")
