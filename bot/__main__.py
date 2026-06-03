"""Entry: `python -m bot` o `python -m bot phase1`."""

import sys

from . import config


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "info"

    if cmd == "info":
        print(f"resolution : {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
        print(f"coords     : {config.COORDS_PATH}")
        print(f"items dir  : {config.ITEMS_DIR}")
        print("comandos: info | phase1 | click_test [<point_name>]")
        return

    if cmd == "click_test":
        from . import boot, input as inp
        from .coords_loader import get_point
        name = sys.argv[2] if len(sys.argv) > 2 else "full_screen"
        pt = get_point(name)
        print(f"[test] click en {name} = {pt} en 3s...")
        inp.sleep(3, jitter=0)
        inp.click(pt)
        print("[test] listo. ¿se registró el click?")
        return

    if cmd == "phase1":
        from . import boot
        from .routines import phase1_salvage_greens
        boot.focus_game()
        phase1_salvage_greens.run()
        return

    print(f"comando desconocido: {cmd}")


if __name__ == "__main__":
    main()
