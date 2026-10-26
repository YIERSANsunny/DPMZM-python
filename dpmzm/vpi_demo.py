"""Compatibility wrapper for :mod:`dpmzm.experiments.vpi_demo`."""

from .experiments.vpi_demo import *  # noqa: F401,F403
from .experiments.vpi_demo import main


if __name__ == "__main__":
    raise SystemExit(main())
