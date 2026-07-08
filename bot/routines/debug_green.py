"""Debug: capturar inventario y banco + loggear TODOS los matches de
green.png con su score real (no solo pass/fail contra un threshold), para
diagnosticar a ciegas por qué el banco falla con los últimos items.

Corre una vez, guarda todo en tools/debug_output/ (git-tracked: se
commitea y pushea como cualquier archivo, así llega a la otra PC/sesión
para revisarlo con datos reales en vez de adivinar).

    py -m bot debug_green

Genera:
    tools/debug_output/report.txt          - scores de cada candidato
    tools/debug_output/inventory_color.png - screenshot completo (color)
    tools/debug_output/bank_color.png      - screenshot completo (color)
    tools/debug_output/{name}_crop_{score}.png - recorte 60x60 de cada
        candidato, para comparar visualmente cómo se ve el ícono en cada
        score (ideal ~0.99, falso ~0.62, y lo que sea que esté en el medio)
"""

import cv2

from .. import config
from .. import vision
from ..config import ITEMS_DIR
from ..coords_loader import get_region

GREEN = ITEMS_DIR / "green.png"
OUT_DIR = config.PROJECT_ROOT / "tools" / "debug_output"

# Piso bajo a propósito: acá queremos ver TODO lo que exista arriba del
# ruido, no solo lo que ya pasaría el threshold real (0.85 o 0.75).
REPORT_FLOOR = 0.40
MAX_MATCHES = 25
CROP_HALF = 30  # recorte de 60x60 centrado en cada match


def _find_all_matches(screen_gray, tpl):
    th, tw = tpl.shape[:2]
    result = cv2.matchTemplate(screen_gray, tpl, cv2.TM_CCOEFF_NORMED)
    matches = []
    for _ in range(MAX_MATCHES):
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < REPORT_FLOOR:
            break
        matches.append((max_val, max_loc[0] + tw // 2, max_loc[1] + th // 2))
        x0 = max(0, max_loc[0] - tw // 2)
        y0 = max(0, max_loc[1] - th // 2)
        x1 = min(result.shape[1], max_loc[0] + tw // 2 + 1)
        y1 = min(result.shape[0], max_loc[1] + th // 2 + 1)
        result[y0:y1, x0:x1] = 0
    return matches


def _dump_region(name, region, tpl):
    gray = vision.capture_screen(region, color=False)
    color = vision.capture_screen(region, color=True)
    cv2.imwrite(str(OUT_DIR / f"{name}_gray.png"), gray)
    cv2.imwrite(str(OUT_DIR / f"{name}_color.png"), color)

    matches = _find_all_matches(gray, tpl)

    lines = [f"{name}: {len(matches)} candidatos (piso {REPORT_FLOOR})"]
    h, w = gray.shape[:2]
    for score, x, y in matches:
        abs_x, abs_y = region.x + x, region.y + y
        lines.append(f"  score={score:.3f}  pos_relativa=({x},{y})  pos_absoluta=({abs_x},{abs_y})")
        x0, y0 = max(0, x - CROP_HALF), max(0, y - CROP_HALF)
        x1, y1 = min(w, x + CROP_HALF), min(h, y + CROP_HALF)
        crop = color[y0:y1, x0:x1]
        cv2.imwrite(str(OUT_DIR / f"{name}_crop_{score:.3f}_{x}_{y}.png"), crop)
    return lines


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tpl = cv2.imread(str(GREEN), 0)
    if tpl is None:
        raise FileNotFoundError(GREEN)

    report = []
    report += _dump_region("inventory", get_region("INVENTORY_AREA"), tpl)
    report += _dump_region("bank", get_region("BANK_AREA"), tpl)

    (OUT_DIR / "report.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print(f"\n[debug_green] guardado en {OUT_DIR}")
