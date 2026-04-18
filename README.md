# Mystia Rhythm

A 4-key rhythm game prototype built with Python + Kivy.
It currently includes a playable flow, chart parsing, judgment logic, and a mod API skeleton.

## Project State (After Initial Cleanup)

- App entry and module boundaries are now documented.
- Runtime data is separated from source code (`data/`).
- A prioritized cleanup backlog now lives in `TODO.md`.

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the app:

```bash
python main.py
```

## Directory Overview

- `main.py`: app entry, screen wiring, main update loop.
- `config.py`: config loading/saving and runtime path setup.
- `core/`: core gameplay systems (audio, chart, timing, judgment, engine).
- `ui/`: menu, song select, play, pause, result, settings screens.
- `mod_system/`: mod manager, permission layer, exposed APIs.
- `assets/`: fonts and UI assets.
- `data/`: runtime data (ignored by default).
- `logs/`: runtime logs (ignored by default).

## Development Rules

- Do not commit runtime artifacts (`__pycache__`, logs, local data).
- Update `TODO.md` before/while touching major areas.
- Prefer small, verifiable changes over large one-shot rewrites.

## Known Hotspots

See `TODO.md` for full details. Current top issues:

- Duplicate `_check_note_hit` definitions in `core/game_engine.py`.
- Historical text encoding issues in comments/log messages.

