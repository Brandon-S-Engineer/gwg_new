"""Entry: `python -m bot` o `python -m bot phase1`."""

import sys

from . import config


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "info"

    if cmd == "info":
        print(f"resolution : {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
        print(f"coords     : {config.COORDS_PATH}")
        print(f"items dir  : {config.ITEMS_DIR}")
        print("comandos: info | loop | phase1 | phase2 | phase3 | sell | ectos | sell_all_clean | click_test [<point_name>]")
        return

    if cmd == "loop":
        import time

        from . import boot, schedule
        print(f"[loop] arranca en {schedule.STARTUP_DELAY}s (sacá el mouse de Parsec)...")
        time.sleep(schedule.STARTUP_DELAY)
        boot.focus_game()
        max_iters = schedule.MAX_ITERATIONS
        i = 1
        stop = False
        import time as _t
        from . import dialogs
        from .routines.phase1_salvage_greens import (
            salvage_with_rune_crafter as _recovery_salvage,
            SLEEP_AFTER_SALVAGE as _RECOVERY_SLEEP,
        )
        while (max_iters == -1 or i <= max_iters) and not stop:
            if dialogs.check_conn_error():
                print("[loop] conn error dismisseado, salvage recovery...")
                _recovery_salvage()
                _t.sleep(_RECOVERY_SLEEP)
                print("[loop] reiniciando iteración...")
                continue
            print(f"\n=== iter {i} ===")
            restart_iter = False
            for every, task in schedule.TASKS:
                if i % every == 0:
                    print(f"[loop] run {task.__module__}.{task.__name__} (every {every})")
                    try:
                        if task() == config.NO_GREENS:
                            print("[loop] no quedan greens, fin.")
                            stop = True
                            break
                    except dialogs.ConnErrorDetected:
                        print("[loop] conn error mid-task, salvage recovery...")
                        _recovery_salvage()
                        _t.sleep(_RECOVERY_SLEEP)
                        print("[loop] reiniciando iteración...")
                        restart_iter = True
                        break
                    except Exception as e:
                        print(f"[loop] task {task.__name__} falló: {e}")
            if not restart_iter:
                i += 1

        # Al terminar el loop: tareas finales (1 vez). Ej: salvage ectos + dust.
        for task in schedule.FINAL_TASKS:
            print(f"\n[loop] tarea final {task.__module__}.{task.__name__}")
            try:
                task()
            except Exception as e:
                print(f"[loop] tarea final {task.__name__} falló: {e}")
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

    if cmd == "phase3":
        from . import boot
        from .routines import phase3_salvage_rares
        boot.focus_game()
        phase3_salvage_rares.run()
        return

    if cmd == "sell":
        from . import boot
        from .routines import sell_materials
        boot.focus_game()
        sell_materials.run()
        return

    if cmd == "ectos":
        from . import boot
        from .routines import ectos
        boot.focus_game()
        ectos.run()
        return

    if cmd == "sell_all_clean":
        from . import boot
        from .routines import sell_all_clean
        boot.focus_game()
        sell_all_clean.run()
        return

    if cmd == "setup":
        from . import boot
        from .routines import setup
        sub = sys.argv[2] if len(sys.argv) > 2 else "all"
        boot.focus_game()
        if sub in ("drag", "all"):
            print("[setup] arrastrando banco...")
            setup.drag_bank()
        if sub in ("inv", "all"):
            print("[setup] filtrando inventario → luck...")
            setup.filter_inventory()
        if sub in ("bank", "all"):
            print("[setup] filtrando banco → unidentified...")
            setup.filter_bank()
        return

    print(f"comando desconocido: {cmd}")


if __name__ == "__main__":
    main()
