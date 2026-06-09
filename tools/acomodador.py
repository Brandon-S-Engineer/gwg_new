"""Grabador/reproductor de macros para Windows (sobre Parsec, corre por dentro).

Sirve para grabar una secuencia tediosa (ej: partir stacks de 250 en stacks
de ~63 y acomodarlos en el banco) una sola vez, y repetirla con un comando.

    py -m pip install pynput
    py tools/acomodador.py g    # grabar
    py tools/acomodador.py c    # correr

Grabar: Ctrl+P para EMPEZAR, Ctrl+P de nuevo para PARAR y guardar (igual que
el gesto de region_picker). Graba todo: movimiento del mouse, clicks, scroll y
teclas, con sus tiempos.

Correr: cuenta regresiva y repite. Cada punto sale ligeramente impreciso
(~5px) y los tiempos varían un poco, así nunca es 100% idéntico. Ctrl+P aborta.

La grabación queda en tools/macros/macro.json.
"""

from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from pynput import keyboard, mouse
except ImportError:
    print("falta pynput. Instalalo con:  py -m pip install pynput")
    sys.exit(1)

MACRO_PATH = Path(__file__).resolve().parent / "macros" / "macro.json"

JITTER_PX = 5        # impresición espacial al repetir (±px)
TIME_JITTER = 0.10   # variación de tiempos al repetir (±10%)
MAX_GAP = 3.0        # pausa máxima entre eventos al repetir (s)
START_DELAY = 5      # cuenta regresiva antes de correr (s)

CTRL_KEYS = {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}


# --------------------------------------------------------------- serializar
def _key_to_dict(key) -> dict:
    if isinstance(key, keyboard.Key):
        return {"key": key.name}
    if key.char is not None:
        return {"char": key.char}
    return {"vk": key.vk}


def _dict_to_key(d: dict):
    if "key" in d:
        return getattr(keyboard.Key, d["key"])
    if "char" in d:
        return keyboard.KeyCode.from_char(d["char"])
    return keyboard.KeyCode.from_vk(d["vk"])


def _is_p(key) -> bool:
    # Ctrl+P puede llegar como '\x10' o sin char; chequear vk de la P (0x50).
    if isinstance(key, keyboard.KeyCode):
        return key.char in ("p", "P", "\x10") or key.vk == 0x50
    return False


# ------------------------------------------------------------------- grabar
def grabar() -> None:
    state = {"on": False, "stop": False, "ctrl": False, "events": [], "t0": 0.0}

    def stamp() -> float:
        return time.time() - state["t0"]

    def on_move(x, y):
        if state["on"]:
            state["events"].append({"t": stamp(), "kind": "move", "x": x, "y": y})

    def on_click(x, y, button, pressed):
        if state["on"]:
            state["events"].append({"t": stamp(), "kind": "click", "x": x, "y": y,
                                    "button": button.name, "pressed": pressed})

    def on_scroll(x, y, dx, dy):
        if state["on"]:
            state["events"].append({"t": stamp(), "kind": "scroll", "x": x, "y": y,
                                    "dx": dx, "dy": dy})

    def on_press(key):
        if key in CTRL_KEYS:
            state["ctrl"] = True
        if _is_p(key) and state["ctrl"]:
            if not state["on"]:                       # EMPEZAR
                state["on"] = True
                state["t0"] = time.time()
                print("grabando... (Ctrl+P para parar)")
                return
            # PARAR: no grabar este combo y sacar el Ctrl que lo precede.
            state["on"] = False
            state["stop"] = True
            if state["events"] and state["events"][-1].get("key") in \
                    ("ctrl", "ctrl_l", "ctrl_r"):
                state["events"].pop()
            return False
        if state["on"]:
            state["events"].append({"t": stamp(), "kind": "key",
                                    "action": "press", **_key_to_dict(key)})

    def on_release(key):
        if key in CTRL_KEYS:
            state["ctrl"] = False
        if state["on"]:
            state["events"].append({"t": stamp(), "kind": "key",
                                    "action": "release", **_key_to_dict(key)})

    print("Listo para grabar. Poné el foco en el juego y Ctrl+P para empezar.")
    ml = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    kl = keyboard.Listener(on_press=on_press, on_release=on_release)
    ml.start()
    kl.start()
    try:
        while not state["stop"]:
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\ncancelado, no se guardó.")
        return
    finally:
        ml.stop()
        kl.stop()

    if not state["events"]:
        print("no se grabó nada.")
        return

    MACRO_PATH.parent.mkdir(parents=True, exist_ok=True)
    MACRO_PATH.write_text(json.dumps({
        "created": datetime.now().isoformat(timespec="seconds"),
        "events": state["events"],
    }, indent=2), encoding="utf-8")
    print(f"guardado {MACRO_PATH}  ({len(state['events'])} eventos)")


# ------------------------------------------------------------------- correr
def _jit(v: int) -> int:
    return int(round(v + random.uniform(-JITTER_PX, JITTER_PX)))


def correr() -> None:
    if not MACRO_PATH.exists():
        print(f"no hay grabación ({MACRO_PATH}). Grabá con: py tools/acomodador.py g")
        return
    events = json.loads(MACRO_PATH.read_text(encoding="utf-8"))["events"]
    print(f"{len(events)} eventos. Empieza en {START_DELAY}s (Ctrl+P aborta)...")

    abort = {"stop": False, "ctrl": False}

    def on_press(key):
        if key in CTRL_KEYS:
            abort["ctrl"] = True
        if _is_p(key) and abort["ctrl"]:
            abort["stop"] = True
            return False

    def on_release(key):
        if key in CTRL_KEYS:
            abort["ctrl"] = False

    kl = keyboard.Listener(on_press=on_press, on_release=on_release)
    kl.start()

    for _ in range(START_DELAY, 0, -1):
        if abort["stop"]:
            print("\nabortado.")
            kl.stop()
            return
        time.sleep(1)

    m = mouse.Controller()
    k = keyboard.Controller()
    prev_t = 0.0
    for ev in events:
        if abort["stop"]:
            print("\nabortado.")
            break
        gap = min(max(ev["t"] - prev_t, 0.0), MAX_GAP)
        gap *= random.uniform(1 - TIME_JITTER, 1 + TIME_JITTER)
        time.sleep(gap)
        prev_t = ev["t"]

        kind = ev["kind"]
        if kind == "move":
            m.position = (_jit(ev["x"]), _jit(ev["y"]))
        elif kind == "click":
            m.position = (_jit(ev["x"]), _jit(ev["y"]))
            btn = getattr(mouse.Button, ev["button"])
            m.press(btn) if ev["pressed"] else m.release(btn)
        elif kind == "scroll":
            m.scroll(ev["dx"], ev["dy"])
        elif kind == "key":
            key = _dict_to_key(ev)
            k.press(key) if ev["action"] == "press" else k.release(key)

    kl.stop()
    if not abort["stop"]:
        print("listo.")


# --------------------------------------------------------------------- main
def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    if cmd == "g":
        return grabar()
    if cmd == "c":
        return correr()

    print("uso:")
    print("  py tools/acomodador.py g    # grabar")
    print("  py tools/acomodador.py c    # correr")


if __name__ == "__main__":
    main()
