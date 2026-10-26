"""DPMZM reusable physical output model."""

from .core.model import (
    BiasScanResult,
    NoiseResult,
    SimulationResult,
    SpectrumResult,
    delta_from_er_db,
    dpmzm_output_field,
    dpmzm_transfer_power,
    gamma_from_er_db,
    mzm_block_output_field,
    phase_to_voltage,
    simulate_dpmzm,
    voltage_to_phase,
)
from .checks.validation import run_analytical_self_check
from .visualization.plot import (
    plot_bias_scan,
    plot_electrical_spectrum,
    plot_optical_spectrum_osa,
)

__all__ = [
    "BiasScanResult",
    "NoiseResult",
    "SimulationResult",
    "SpectrumResult",
    "delta_from_er_db",
    "dpmzm_output_field",
    "dpmzm_transfer_power",
    "gamma_from_er_db",
    "mzm_block_output_field",
    "phase_to_voltage",
    "simulate_dpmzm",
    "voltage_to_phase",
    "run_analytical_self_check",
    "plot_bias_scan",
    "plot_electrical_spectrum",
    "plot_optical_spectrum_osa",
]
