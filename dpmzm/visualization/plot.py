"""Plot helpers for DPMZM simulation.

Optical and electrical spectrum plots reuse the MZM plotting helpers because
the DPMZM SimulationResult exposes the same fields they need. Bias scan is
DPMZM-specific because it has I/Q/P slices instead of one bias axis.
"""

from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

if TYPE_CHECKING:
    from ..core.model import SimulationResult


@lru_cache(maxsize=1)
def _shared_mzm_plot_module():
    """Load mzm/plot.py without importing the full torch-dependent mzm package."""

    plot_path = Path(__file__).resolve().parents[2] / "mzm" / "plot.py"
    spec = importlib.util.spec_from_file_location("_dpmzm_shared_mzm_plot", plot_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load shared MZM plot helpers from {plot_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plot_optical_spectrum_osa(
    sim: "SimulationResult",
    f_rf_hz: float = 1e9,
    span_factor: float = 2.5,
    max_order: int = 2,
) -> None:
    """Plot DPMZM optical spectrum using the shared MZM OSA-style helper."""

    _shared_mzm_plot_module().plot_optical_spectrum_osa(
        sim,
        f_rf_hz=float(f_rf_hz),
        span_factor=float(span_factor),
        max_order=int(max_order),
    )


def plot_electrical_spectrum(
    sim: "SimulationResult",
    f_rf_hz: float = 1e9,
    harmonic_orders=(0, 1, 2),
) -> None:
    """Plot DPMZM PD electrical spectrum using the shared MZM helper."""

    _shared_mzm_plot_module().plot_electrical_spectrum(
        sim,
        f_rf_hz=float(f_rf_hz),
        harmonic_orders=harmonic_orders,
    )


def plot_bias_scan(sim: "SimulationResult") -> None:
    """Plot I/Q/P DPMZM bias-scan slices and mark the current bias point."""

    bs = sim.bias_scan
    fig, axes = plt.subplots(3, 1, figsize=(7, 8), sharey=True)
    curves = [
        ("I child MZM", bs.V_I_scan, bs.P_I_scan_mW, bs.V_DCI),
        ("Q child MZM", bs.V_Q_scan, bs.P_Q_scan_mW, bs.V_DCQ),
        ("Parent MZM", bs.V_P_scan, bs.P_P_scan_mW, bs.V_DCP),
    ]

    for ax, (title, v_scan, p_scan, v_bias) in zip(axes, curves):
        p_at_bias = float(np.interp(float(v_bias), v_scan, p_scan))
        ax.plot(v_scan, p_scan, "k", linewidth=1.5)
        ax.scatter([v_bias], [p_at_bias], color="r", zorder=3)
        ax.axvline(v_bias, color="r", linestyle="--", linewidth=1)
        ax.set_title(title)
        ax.set_xlabel("Bias Voltage (V)")
        ax.set_ylabel("Optical Power (mW)")
        ax.grid(True, linestyle="--", alpha=0.5)

    fig.suptitle(
        f"DPMZM Bias Scan (current output {bs.curr_P_dBm:.2f} dBm)",
        y=0.99,
    )
    fig.tight_layout()
