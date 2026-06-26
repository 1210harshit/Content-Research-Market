#!/usr/bin/env python3
"""One-command installer that wires course-market-intelligence-mcp into Claude Desktop.

Run this ON YOUR LOCAL MACHINE (where Claude Desktop is installed):

    python3 setup_claude_desktop.py

It will:
  1. create a virtualenv (.venv) in this repo and install the server into it;
  2. locate your OS's Claude Desktop config file;
  3. back up the existing config (if any);
  4. add/merge a "course-market-intelligence" MCP server entry with the correct
     absolute path to the installed entry point.

Then quit and reopen Claude Desktop. No manual JSON editing required.

Flags:
  --print            Show the config + target path, but don't write anything.
  --config-path PATH Override the Claude Desktop config location (for testing).
  --python PATH      Use a specific Python interpreter to build the venv.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SERVER_KEY = "course-market-intelligence"
ENTRY_POINT = "course-market-intelligence"


def log(msg: str) -> None:
    print(f"  {msg}")


def default_config_path() -> Path:
    system = platform.system()
    home = Path.home()
    if system == "Darwin":
        return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if system == "Windows":
        import os
        appdata = os.environ.get("APPDATA", str(home / "AppData" / "Roaming"))
        return Path(appdata) / "Claude" / "claude_desktop_config.json"
    # Linux / other
    return home / ".config" / "Claude" / "claude_desktop_config.json"


def venv_paths(venv_dir: Path) -> tuple[Path, Path]:
    """Return (python_executable, entry_point_binary) inside the venv."""
    if platform.system() == "Windows":
        return (venv_dir / "Scripts" / "python.exe",
                venv_dir / "Scripts" / f"{ENTRY_POINT}.exe")
    return (venv_dir / "bin" / "python", venv_dir / "bin" / ENTRY_POINT)


def ensure_venv(python_exe: str) -> Path:
    venv_dir = REPO_ROOT / ".venv"
    py, entry = venv_paths(venv_dir)
    if not py.exists():
        log(f"Creating virtualenv at {venv_dir} ...")
        subprocess.run([python_exe, "-m", "venv", str(venv_dir)], check=True)
    else:
        log(f"Reusing existing virtualenv at {venv_dir}")

    log("Installing course-market-intelligence-mcp into the virtualenv ...")
    subprocess.run([str(py), "-m", "pip", "install", "--quiet", "--upgrade", "pip"],
                   check=True)
    subprocess.run([str(py), "-m", "pip", "install", "--quiet", "-e", str(REPO_ROOT)],
                   check=True)

    if not entry.exists():
        raise SystemExit(
            f"ERROR: entry point not found at {entry} after install. "
            "Check the install output above."
        )
    return entry


def build_entry(entry_binary: Path) -> dict:
    return {
        "command": str(entry_binary),
        "args": [],
        # Secrets live in the repo's .env (loaded automatically). Add keys here
        # only if you prefer to keep them in the Claude Desktop config instead.
        "env": {},
    }


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"ERROR: existing config at {path} is not valid JSON ({exc}). "
            "Fix or remove it, then re-run."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--print", action="store_true", dest="print_only")
    parser.add_argument("--config-path")
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()

    print("course-market-intelligence-mcp -> Claude Desktop setup")
    print("=" * 56)

    entry_binary = ensure_venv(args.python)
    log(f"Entry point: {entry_binary}")

    config_path = Path(args.config_path) if args.config_path else default_config_path()
    server_entry = build_entry(entry_binary)

    if args.print_only:
        print("\nWould write this entry to:", config_path)
        print(json.dumps({"mcpServers": {SERVER_KEY: server_entry}}, indent=2))
        return 0

    config = load_config(config_path)
    config.setdefault("mcpServers", {})

    if SERVER_KEY in config["mcpServers"]:
        log(f"Updating existing '{SERVER_KEY}' entry.")
    else:
        log(f"Adding new '{SERVER_KEY}' entry.")
    config["mcpServers"][SERVER_KEY] = server_entry

    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        backup = config_path.with_suffix(config_path.suffix + ".bak")
        shutil.copy2(config_path, backup)
        log(f"Backed up existing config to {backup}")

    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    log(f"Wrote config to {config_path}")

    print("\nDone. Next steps:")
    print("  1. (optional) put API keys in", REPO_ROOT / ".env",
          "(copy from .env.example)")
    print("  2. Fully QUIT and reopen Claude Desktop.")
    print("  3. The 'course-market-intelligence' tools will appear in the tools menu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
