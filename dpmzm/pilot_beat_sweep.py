"""Compatibility wrapper for :mod:`dpmzm.experiments.pilot_beat_sweep`."""

from .experiments.pilot_beat_sweep import *  # noqa: F401,F403
from .experiments.pilot_beat_sweep import main


if __name__ == "__main__":
    raise SystemExit(main())
