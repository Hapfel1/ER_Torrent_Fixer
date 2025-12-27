# Development

## Requirements
- Python **3.13+** (see `.python-version` / `pyproject.toml`)
- [`uv`](https://github.com/astral-sh/uv)

## Setup

```bash
uv sync --locked --dev
```

## Run

```bash
# GUI (default)
uv run er-save-fixer
```

## CLI examples

```bash
uv run er-save-fixer list --save "C:\Path\To\ER0000.sl2"
uv run er-save-fixer fix --save "C:\Path\To\ER0000.sl2" --slot 1
uv run er-save-fixer fix --save "C:\Path\To\ER0000.sl2" --slot 1 --teleport limgrave
```

## Lint / format

```bash
uv run ruff check
uv run ruff format
```

## Build (Windows exe)

```bash
uv run pyinstaller "Elden Ring Save Fixer.spec"
```

## Legacy (without uv)

```bash
py elden_ring_save_fixer_gui.py
py -m PyInstaller "Elden Ring Save Fixer.spec"
```
