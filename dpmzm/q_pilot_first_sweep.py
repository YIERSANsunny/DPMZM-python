"""Compatibility wrapper for :mod:`dpmzm.experiments.q_pilot_first_sweep`."""

from .experiments.q_pilot_first_sweep import *  # noqa: F401,F403
from .experiments.q_pilot_first_sweep import main


if __name__ == "__main__":
    raise SystemExit(main())
