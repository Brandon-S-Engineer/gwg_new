"""Entry: `python -m bot` o `python -m bot phase1`."""

import sys

from . import config


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "info"

    if cmd == "info":
        print(f"resolution : {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
        print(f"coords     : {config.COORDS_PATH}")
        print(f"items dir  : {config.ITEMS_DIR}")
        print("comandos: info | loop | phase1 | phase2 | click_test [<point_name>]")
        return

    if cmd == "loop":
        from . import boot, schedule
        boot.focus_game()
        max_iters = schedule.MAX_ITERATIONS
        i = 1
        while max_iters == -1 or i <= max_iters:
            print(f"\n=== iter {i} ===")
            for every, task in schedule.TASKS:
                if i % every == 0:
                    print(f"[loop] run {task.__module__}.{task.__name__} (every {every})")
                    try:
                        task()
                    except Exception as e:
                        print(f"[loop] task {task.__name__} falló: {e}")
            i += 1
        return

    if cmd == "click_test":
        from . import input as inp
        from .coords_loader import get_point
        args = sys.argv[2:]
        if len(args) >= 2 and args[0].isdigit() and args[1].isdigit():
            pt = (int(args[0]), int(args[1]))
            label = f"({pt[0]}, {pt[1]})"
        else:
            name = args[0] if args else "full_screen"
            pt = get_point(name)
            label = f"{name} = {pt}"
        print(f"[test] click x2 en {label} en 3s...")
        inp.sleep(3, jitter=0)
        inp.click(pt)
        inp.sleep(0.4, jitter=0)
        inp.click(pt)
        print("[test] listo. ¿se registró?")
        return

    if cmd == "phase1":
        from . import boot
        from .routines import phase1_salvage_greens
        boot.focus_game()
        phase1_salvage_greens.run()
        return

    if cmd == "phase2":
        from . import boot
        from .routines import phase2_consume_luck
        boot.focus_game()
        phase2_consume_luck.run()
        return

    print(f"comando desconocido: {cmd}")


if __name__ == "__main__":
    main()
