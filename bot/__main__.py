"""Entry: `python -m bot` o `python -m bot phase1`."""

import sys

from . import config


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "info"

    # schedule define las constantes de timing y luego importa TODAS las
    # rutinas en orden. Importarlo primero deja cada rutina lista y evita el
    # import circular si un comando importa una rutina suelta (ver TIMING).
    from . import schedule  # noqa: F401

    if cmd == "info":
        print(f"resolution : {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
        print(f"coords     : {config.COORDS_PATH}")
        print(f"items dir  : {config.ITEMS_DIR}")
        print("comandos: info | loop [y<N>] [iteraciones] | phase1 | phase2 | phase3 | sell | ectos | sell_all_clean | deposit_metal_plates | craft_essence | exotics | extract_yellow | open_bags | setup | conn_test | debug_green | click_test [<point_name>]")
        print("  loop: siempre corre amarillos primero (si hay) y después verdes, automático.")
        print("        y<N> = usar el Upgrade Extractor con N de los 250 slots al procesar amarillos")
        print("        (N = slots a barrer, no cantidad de yellows). Sin y<N> = amarillos SIN extractor.")
        print("        <iteraciones> = tope para esta corrida (pisa MAX_ITERATIONS_GREEN/YELLOW sin tocar schedule.py).")
        print("        Ej: 'loop y100 90', 'loop 30' o simplemente 'loop'.")
        return

    if cmd == "loop":
        import time

        from . import boot, dialogs, schedule
        from .routines import setup as _setup
        from .routines.phase1_salvage_greens import recover as _recovery_salvage

        # Hasta 2 argumentos opcionales, en cualquier orden:
        #   y<N>       - usar el Upgrade Extractor con N de los 250 slots al
        #                procesar amarillos (separa el salvage caro del
        #                barato). Sin esto = sin extractor, salvage directo.
        #   <número>   - tope de iteraciones para ESTA corrida (pisa
        #                MAX_ITERATIONS_GREEN/YELLOW del schedule.py sin
        #                tener que tocar el archivo ni hacer git push/pull;
        #                a veces conviene cortar a los 60, a veces a 120).
        #   py -m bot loop           -> sin extractor, tope de siempre
        #   py -m bot loop y100      -> con extractor, 100 slots
        #   py -m bot loop 30        -> 30 iteraciones, sin extractor
        #   py -m bot loop y100 90   -> con extractor (100 slots), 90 iteraciones
        #
        # Siempre corre amarillos primero y después verdes — no hace falta
        # elegir: si no hay amarillos, ese segmento corta casi al instante
        # (identify_one no encuentra nada, config.NO_GREENS) y sigue de
        # largo con verdes. Así los 3 casos (solo amarillos, solo verdes,
        # los dos) quedan cubiertos sin pedirle nada más al usuario.
        n = 0
        iterations = None
        for tok in sys.argv[2:]:
            tok = tok.strip().lower()
            if tok.startswith("y") and (tok[1:] == "" or tok[1:].isdigit()):
                n = int(tok[1:]) if tok[1:].isdigit() else 0
            elif tok.isdigit():
                iterations = int(tok)
            else:
                print(f"[loop] argumento desconocido: '{tok}' (usar 'y<N>', un número de iteraciones, o nada)")
                return
        schedule.YELLOW_MAX_SLOTS = n
        green_max_iters = iterations if iterations is not None else schedule.MAX_ITERATIONS_GREEN
        yellow_max_iters = iterations if iterations is not None else schedule.MAX_ITERATIONS_YELLOW

        print(f"[loop] arranca en {schedule.STARTUP_DELAY}s (sacá el mouse de Parsec)...")
        time.sleep(schedule.STARTUP_DELAY)
        boot.focus_game()
        print("[loop] setup inicial...")
        _setup.run()

        def _run_tasks(tasks, label, max_iters):
            if not tasks:
                return  # nada periódico que correr en este segmento
            i = 1
            stop = False
            while (max_iters == -1 or i <= max_iters) and not stop:
                if dialogs.check_conn_error():
                    print("[loop] conn error dismisseado, salvage recovery...")
                    _recovery_salvage()
                    print("[loop] reiniciando iteración...")
                    continue
                print(f"\n=== {label} iter {i} ===")
                restart_iter = False
                for every, task in tasks:
                    if i % every == 0:
                        print(f"[loop] run {task.__module__}.{task.__name__} (every {every})")
                        try:
                            if task() == config.NO_GREENS:
                                print(f"[loop] no queda más {label}, fin de este segmento.")
                                stop = True
                                break
                        except dialogs.ConnErrorDetected:
                            print("[loop] conn error mid-task, salvage recovery...")
                            _recovery_salvage()
                            print("[loop] reiniciando iteración...")
                            restart_iter = True
                            break
                        except Exception as e:
                            print(f"[loop] task {task.__name__} falló: {e}")
                if not restart_iter:
                    i += 1

        def _run_final(final_tasks):
            for task in final_tasks:
                print(f"\n[loop] tarea final {task.__module__}.{task.__name__}")
                try:
                    task()
                except Exception as e:
                    print(f"[loop] tarea final {task.__name__} falló: {e}")

        modo = f"con extractor, max_slots={n}" if n > 0 else "SIN extractor"
        tope = f", tope {iterations} iteraciones" if iterations is not None else ""
        print(f"\n[loop] ══════ amarillos primero, si hay ({modo}{tope}) ══════")
        _run_tasks(schedule.TASKS_YELLOW, "yellow", yellow_max_iters)
        _run_final(schedule.FINAL_TASKS_YELLOW)

        print("\n[loop] ══════ verdes ══════")
        _run_tasks(schedule.TASKS_GREEN, "green", green_max_iters)
        _run_final(schedule.FINAL_TASKS_GREEN)
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

    if cmd == "deposit_metal_plates":
        from . import boot
        from .routines import deposit_metal_plates
        boot.focus_game()
        deposit_metal_plates.run()
        return

    if cmd == "exotics":
        from . import boot
        from .routines import exotics
        sub = sys.argv[2] if len(sys.argv) > 2 else "all"
        boot.focus_game()
        if sub == "all":
            exotics.run()
        elif sub == "view":
            exotics.test_reset_view()
        elif sub == "salvage":
            exotics.test_salvage_rest()
        elif sub == "dark_matter":
            exotics.test_deposit_dark_matter()
        elif sub == "destroy":
            exotics.test_destroy_inscriptions()
        return

    if cmd == "extract_yellow":
        from . import boot
        from .routines import extract_yellow
        sub = sys.argv[2] if len(sys.argv) > 2 else "all"
        boot.focus_game()
        if sub == "all":
            # extractor completo (250) por default acá — el default de
            # run() es 0 (sin extractor) para el uso desde `loop y`.
            extract_yellow.run(max_slots=extract_yellow.MAX_SLOTS)
        elif sub == "identify":
            extract_yellow.identify_one()
        elif sub == "extract":
            extract_yellow.extract_all()
        elif sub == "identify_extract":
            extract_yellow.identify_and_extract()
        elif sub == "salvage":
            extract_yellow.salvage_gear_then_upgrades()
        return

    if cmd == "open_bags":
        from . import boot
        from .routines import open_bags
        boot.focus_game()
        open_bags.run()
        return

    if cmd == "conn_test":
        from . import boot, dialogs
        from .routines.phase1_salvage_greens import recover
        boot.focus_game()
        print("[conn_test] buscando ícono de error de conexión...")
        found = dialogs.check_conn_error()
        if not found:
            print("[conn_test] no se detectó (o se detectó pero no se encontró el OK). "
                  "Mirá el max_val de arriba contra CONN_ERROR_THRESHOLD.")
            return
        print("[conn_test] OK clickeado, corriendo recovery (identificar + rune_crafter)...")
        recover()
        print("[conn_test] listo")
        return

    if cmd == "debug_green":
        from . import boot
        from .routines import debug_green
        boot.focus_game()
        debug_green.run()
        return

    if cmd == "craft_essence":
        from . import boot
        from .routines import craft_essence
        sub = sys.argv[2] if len(sys.argv) > 2 else "all"
        boot.focus_game()
        if sub == "all":
            craft_essence.run()
        elif sub == "quick":
            craft_essence.quick()
        elif sub == "ectos_luck":
            craft_essence.run_after_ectos()
        elif sub == "search":
            craft_essence.open_and_search_luck()
        elif sub == "find":
            craft_essence.test_find_recipes()
        return

    if cmd == "setup":
        from . import boot
        from .routines import setup
        sub = sys.argv[2] if len(sys.argv) > 2 else "all"
        boot.focus_game()
        if sub == "all":
            setup.run()
        elif sub == "force":
            setup.run(force=True)   # rearma todo aunque las ventanas ya estén
        elif sub == "check":
            setup.diagnose_windows()
            print("[setup] listo para arrancar" if setup.windows_ready()
                  else "[setup] falta abrir algo")
        elif sub == "tab":
            setup.ensure_bank_tab()
        elif sub == "artificing":
            setup.ensure_artificing_tab()
        elif sub == "drag":
            setup.drag_bank()
        elif sub == "windows":
            setup.open_windows()
        elif sub == "extractor":
            setup.open_extractor()
        elif sub == "inv":
            setup.filter_inventory()
        elif sub == "bank":
            setup.filter_bank()
        elif sub == "position":
            setup.position_bank_for_calibration()
        return

    print(f"comando desconocido: {cmd}")


if __name__ == "__main__":
    main()
