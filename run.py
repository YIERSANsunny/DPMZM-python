"""Single command entry for the DPMZM project."""

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from config import load_config


ROOT = Path(__file__).resolve().parent
COMMANDS = {
    "spectrum": "tia_full_spectrum.py",
    "findpoint": "run_chained_findpoint.py",
    "validate": "findpoint_validator.py",
    "recheck": "vpi_model_recheck.py",
    "tia": "tia_experimental_curves.py",
    "visibility": "tia_visibility_analyzer.py",
    "adc": "adc_chain_model.py",
}


def main():
    if len(sys.argv) > 1 and sys.argv[1] in COMMANDS:
        script = ROOT / "simulation_validation" / COMMANDS[sys.argv[1]]
        return subprocess.call([sys.executable, str(script), *sys.argv[2:]])
    parser = argparse.ArgumentParser(description="DPMZM unified entry: " + ", ".join(COMMANDS) + ", config")
    parser.add_argument("command", choices=[*COMMANDS, "config"])
    parser.add_argument("--config", type=Path, help="Preview the resolved JSON scenario without running a simulation")
    args = parser.parse_args()
    if args.command in COMMANDS:
        forwarded = ["--config", str(args.config)] if args.config else []
        return subprocess.call([sys.executable, str(ROOT / "simulation_validation" / COMMANDS[args.command]), *forwarded])
    try:
        cfg = load_config(args.config)
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(dict(config=asdict(cfg), derived=cfg.derived()), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
