"""Entry point: `python -m bot`."""

from . import config


def main() -> None:
    print("gwg bot — scaffolding OK")
    print(f"  resolution    : {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
    print(f"  inventory     : {config.INVENTORY_ROWS}x{config.INVENTORY_COLS}")
    print(f"  bank          : {config.BANK_ROWS}x{config.BANK_COLS}")
    print(f"  assets dir    : {config.ASSETS_DIR}")
    print(f"  wait timeout  : {config.DEFAULT_WAIT_TIMEOUT}s")


if __name__ == "__main__":
    main()
