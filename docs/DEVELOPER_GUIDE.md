# P4wnP1 ALOA Menu Forever - Developer Guide

This document explains the code structure and provides tips for extending the menu.

## Repository layout

```
P4wnp1-ALOA-Menu-Forever/
├── library/         # core modules for display, system helpers and UI
├── new.py           # main menu application
├── old.py           # previous version kept for reference
├── install.sh       # dependency installer
├── update.sh        # script to update menu code
└── docs/            # documentation
```

The `library` package contains:

- `display.py` – OLED/terminal display handling and key mappings
- `system.py` – wrappers around shell commands and menu utilities
- `ui.py` – common user‑interface routines
- `ups.py` – helper functions for the optional UPS hat

## Coding conventions

- The project targets Python 3.7 and runs on Raspberry Pi hardware.
- Hardware buttons use BCM GPIO numbering (see `display.py`).
- OLED drawing uses the `luma.oled` library and fonts in `fonts/`.

## Adding new menu items

The menu logic lives in `new.py`. To add new options:

1. In `switch_menu(argument)` add entries for your new menu or submenu identifiers.
2. In `main()` handle the new page value and call your function when selected.
3. Implement the function that runs your command. Use helper functions from `MANUAL.md` such as:
   - `execcmd(cmd)` – run a shell command and capture output
   - `autoKillCommand(cmd, t)` – run a command for a fixed time and kill it automatically
   - `checklist(list)` – display a selection list on the screen

Refer to `MANUAL.md` for more utilities and examples.

## Testing

Use Python's bytecode compilation to quickly check for syntax errors:

```bash
python -m py_compile new.py old.py library/*.py
```

Run your new code on a Raspberry Pi with P4wnP1 to verify interaction with hardware and network tools.

## Contribution guidelines

- Keep commits focused and documented.
- Ensure scripts remain compatible with Python 3.7.
- Test hardware interactions where possible; many features rely on physical buttons and network interfaces.

