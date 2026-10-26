"""Compatibility wrapper for :mod:`dpmzm.experiments.p_pilot_second_sweep`."""

from .experiments.p_pilot_second_sweep import *  # noqa: F401,F403
from .experiments.p_pilot_second_sweep import main


if __name__ == "__main__":
    raise SystemExit(main())
