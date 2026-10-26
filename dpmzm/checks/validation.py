"""Validation helpers for the DPMZM output model."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..core.model import (
    delta_from_er_db,
    dpmzm_output_field,
    dpmzm_transfer_power,
    mzm_block_output_field,
    phase_to_voltage,
    simulate_dpmzm,
    voltage_to_phase,
)


def run_analytical_self_check() -> dict[str, Any]:
    """Run lightweight analytical checks for the DPMZM model.

    This is intentionally small and dependency-free so it can be used before
    VPI/MATLAB reference data is available.
    """

    phi_i = np.linspace(-2.0 * np.pi, 2.0 * np.pi, 101)
    phi_q = np.linspace(-np.pi, np.pi, 101)
    phi_p = 0.37

    transfer = dpmzm_transfer_power(phi_i, phi_q, phi_p)
    a = np.cos(phi_i / 2.0)
    b = np.cos(phi_q / 2.0)
    expected = 0.25 * (a * a + b * b + 2.0 * a * b * np.cos(phi_p))
    half_angle_max_err = float(np.max(np.abs(transfer - expected)))

    e_ideal = dpmzm_output_field(1.0, phi_i, phi_q, phi_p)
    e_zero_delta = dpmzm_output_field(
        1.0,
        phi_i,
        phi_q,
        phi_p,
        delta_I=0.0,
        delta_Q=0.0,
        delta_P=0.0,
    )
    zero_delta_field_err = float(np.max(np.abs(e_ideal - e_zero_delta)))

    v = np.array([0.0, 2.5, 5.0])
    phase_roundtrip_err = float(
        np.max(np.abs(phase_to_voltage(voltage_to_phase(v, 5.0), 5.0) - v))
    )
    single_block_e = mzm_block_output_field(
        np.sqrt(0.010),
        0.0,
        lower_arm_phase_sense="NEGATIVE",
        loss_factor=10.0 ** (-6.0 / 10.0),
    )
    single_block_dbm = float(10.0 * np.log10((np.abs(single_block_e) ** 2) * 1000.0))
    single_block_vpi_err_db = abs(single_block_dbm - 4.0)
    finite_er_block_e = mzm_block_output_field(
        np.sqrt(0.010),
        0.0,
        lower_arm_phase_sense="NEGATIVE",
        delta=delta_from_er_db(30.0),
        loss_factor=10.0 ** (-6.0 / 10.0),
        er_model="vpi",
    )
    finite_er_block_dbm = float(
        10.0 * np.log10((np.abs(finite_er_block_e) ** 2) * 1000.0)
    )
    finite_er_normalized_err_db = abs(finite_er_block_dbm - 4.0)

    sim_suppressed = simulate_dpmzm(
        Fs=2e9,
        T_total=1e-7,
        ideal=True,
        V_RFI_amp=0.0,
        V_RFQ_amp=0.0,
        rng_seed=1,
    )
    sim_max = simulate_dpmzm(
        Fs=2e9,
        T_total=1e-7,
        ideal=True,
        V_DCI=0.0,
        V_DCQ=0.0,
        V_DCP=0.0,
        rng_seed=1,
    )
    suppressed_vs_max_ratio = float(
        np.mean(sim_suppressed.P_opt_inst_W) / np.mean(sim_max.P_opt_inst_W)
    )

    sim_er_none = simulate_dpmzm(Fs=2e9, T_total=1e-7, ER_dB=None, rng_seed=2)
    finite_spectra = bool(
        np.isfinite(sim_er_none.spectrum.P_elec_spec_dBm).all()
        and np.isfinite(sim_er_none.spectrum.P_opt_spec_dBm).all()
    )

    return {
        "half_angle_max_err": half_angle_max_err,
        "zero_delta_field_err": zero_delta_field_err,
        "phase_roundtrip_err": phase_roundtrip_err,
        "single_block_dbm": single_block_dbm,
        "single_block_vpi_err_db": single_block_vpi_err_db,
        "finite_er_block_dbm": finite_er_block_dbm,
        "finite_er_normalized_err_db": finite_er_normalized_err_db,
        "suppressed_vs_max_ratio": suppressed_vs_max_ratio,
        "delta_30db": delta_from_er_db(30.0),
        "er_none_delta_I": sim_er_none.params["delta_I"],
        "er_none_delta_Q": sim_er_none.params["delta_Q"],
        "finite_spectra": finite_spectra,
        "passed": bool(
            half_angle_max_err < 1e-12
            and zero_delta_field_err < 1e-12
            and phase_roundtrip_err < 1e-12
            and single_block_vpi_err_db < 1e-12
            and finite_er_normalized_err_db < 1e-12
            and suppressed_vs_max_ratio < 1e-20
            and finite_spectra
        ),
    }
