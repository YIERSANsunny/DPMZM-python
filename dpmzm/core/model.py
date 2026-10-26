"""DPMZM output model with RF/dither inputs, spectra, and PD noise.

The ideal model follows the derivation in ``DPMZM_output_model_rederived.md``:

    E_out = E_in / 2 * [cos(phi_I/2) + cos(phi_Q/2) exp(j phi_P)]

with optional non-ideal terms for I/Q/P finite extinction ratio. VPI-style
per-block insertion loss is applied inside the I/Q child MZM blocks and inside
the POSITIVE parent phase block on the Q optical path. The implementation is
intentionally NumPy-only so the physical output model remains usable even when
PyTorch is not installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class NoiseResult:
    P_thermal_W: float
    P_shot_W: float
    P_rin_W: float
    P_noise_total_W: float
    P_noise_floor_dBm: float
    P_density_dBmHz: float


@dataclass
class SpectrumResult:
    f_opt: np.ndarray
    P_opt_spec_dBm: np.ndarray
    f_elec: np.ndarray
    P_elec_spec_dBm: np.ndarray
    val_1G_dBm: float
    val_2G_dBm: float
    val_rf_dBm: float
    val_2rf_dBm: float


@dataclass
class BiasScanResult:
    V_I_scan: np.ndarray
    P_I_scan_mW: np.ndarray
    V_Q_scan: np.ndarray
    P_Q_scan_mW: np.ndarray
    V_P_scan: np.ndarray
    P_P_scan_mW: np.ndarray
    V_DCI: float
    V_DCQ: float
    V_DCP: float
    curr_P_mW: float
    curr_P_dBm: float


@dataclass
class SimulationResult:
    t: np.ndarray
    RBW_Hz: float
    E_out: np.ndarray
    P_opt_inst_W: np.ndarray
    P_pd_avg_dBm: float
    I_pd: np.ndarray
    noise: NoiseResult
    spectrum: SpectrumResult
    bias_scan: BiasScanResult
    Pin_dBm: float
    pd_tap: float
    params: dict[str, Any]


def voltage_to_phase(V: np.ndarray | float, Vpi: float) -> np.ndarray:
    """Map push-pull equivalent voltage to DPMZM phase: phi = pi * V / Vpi."""

    if float(Vpi) <= 0:
        raise ValueError("Vpi must be > 0")
    return (float(np.pi) / float(Vpi)) * np.asarray(V, dtype=float)


def phase_to_voltage(phi: np.ndarray | float, Vpi: float) -> np.ndarray:
    """Inverse of voltage_to_phase."""

    if float(Vpi) <= 0:
        raise ValueError("Vpi must be > 0")
    return (float(Vpi) / float(np.pi)) * np.asarray(phi, dtype=float)


def delta_from_er_db(er_db: float | None) -> float:
    """Convert extinction ratio in dB to the finite-ER delta parameter.

    The derivation uses ER = ((1 + delta) / delta)^2, where ER is a power
    ratio. Therefore delta = 1 / (sqrt(ER) - 1).
    """

    if er_db is None:
        return 0.0
    if np.isinf(float(er_db)):
        return 0.0
    er_field_ratio = 10.0 ** (float(er_db) / 20.0)
    if er_field_ratio <= 1.0:
        raise ValueError("er_db must correspond to an extinction ratio > 1")
    return float(1.0 / (er_field_ratio - 1.0))


def gamma_from_er_db(er_db: float | None) -> float:
    """Convert extinction ratio in dB to an arm-amplitude imbalance gamma.

    This matches the MZM model convention:
        gamma = (sqrt(ER) - 1) / (sqrt(ER) + 1)

    When gamma=1, the parent/main combiner is ideal. Finite ER makes one parent
    arm slightly smaller, yielding a finite residual at destructive interference.
    """

    if er_db is None:
        return 1.0
    if np.isinf(float(er_db)):
        return 1.0
    er_field_ratio = 10.0 ** (float(er_db) / 20.0)
    if er_field_ratio <= 1.0:
        raise ValueError("er_db must correspond to an extinction ratio > 1")
    return float((er_field_ratio - 1.0) / (er_field_ratio + 1.0))


def _normalize_er_model(er_model: str) -> str:
    model = str(er_model).strip().lower().replace("-", "_")
    aliases = {
        "vpi": "vpi",
        "normalized": "vpi",
        "normalised": "vpi",
        "arm_imbalance": "vpi",
        "thesis": "thesis",
        "paper": "thesis",
        "residual": "thesis",
    }
    if model not in aliases:
        raise ValueError("er_model must be 'vpi' or 'thesis'")
    return aliases[model]


def mzm_block_output_field(
    E_in: np.ndarray | complex | float,
    phi: np.ndarray | float,
    *,
    lower_arm_phase_sense: str = "NEGATIVE",
    delta: float = 0.0,
    loss_factor: float = 1.0,
    er_model: str = "vpi",
) -> np.ndarray:
    """Return the optical field after one VPI-style DiffMZ_DSM block.

    ``phi`` is the effective phase used by the DPMZM model. For
    ``NEGATIVE`` lower-arm phase sense it is the differential phase, so the
    ideal transfer is ``cos(phi / 2)``. For ``POSITIVE`` sense the differential
    cosine term collapses to one and the block acts as a common phase shifter
    with ideal transfer ``exp(j phi)``.

    ``loss_factor`` is the device fiber-in to fiber-out power transmission.
    Thus a single block with 6 dB insertion loss has a maximum output power of
    ``Pin - 6 dB``.

    ``er_model='vpi'`` uses a normalized arm-imbalance model, preserving unity
    maximum transfer while giving a finite residual at the minimum point.
    ``er_model='thesis'`` keeps the earlier unnormalized residual-field form
    from the derivation notes.
    """

    if float(loss_factor) < 0:
        raise ValueError("loss_factor must be >= 0")

    sense = str(lower_arm_phase_sense).strip().upper()
    er_model_eff = _normalize_er_model(er_model)
    phi_arr = np.asarray(phi, dtype=float)
    E_arr = np.asarray(E_in, dtype=complex)
    amp = np.sqrt(float(loss_factor))

    if sense == "NEGATIVE":
        transfer = np.cos(phi_arr / 2.0) + float(delta) * np.exp(1j * phi_arr / 2.0)
        if er_model_eff == "vpi":
            transfer = transfer / (1.0 + float(delta))
    elif sense == "POSITIVE":
        transfer = np.exp(1j * phi_arr)
    else:
        raise ValueError("lower_arm_phase_sense must be 'NEGATIVE' or 'POSITIVE'")

    return E_arr * amp * transfer


def dpmzm_output_field(
    E_in: np.ndarray | complex | float,
    phi_I: np.ndarray | float,
    phi_Q: np.ndarray | float,
    phi_P: np.ndarray | float,
    *,
    delta_I: float = 0.0,
    delta_Q: float = 0.0,
    delta_P: float = 0.0,
    gamma_P: float = 1.0,
    loss_factor: float = 1.0,
    branch_I_loss_factor: float = 1.0,
    branch_Q_loss_factor: float = 1.0,
    parent_loss_factor: float = 1.0,
    er_model: str = "vpi",
) -> np.ndarray:
    """Return DPMZM output optical field envelope.

    ``delta_I`` and ``delta_Q`` model finite extinction ratio of the child MZMs.
    With ``er_model='vpi'``, they are normalized so finite ER does not increase
    the maximum transfer above the insertion-loss limit. With
    ``er_model='thesis'``, ``delta_P`` also models parent/main MZM finite ER
    using the thesis form E_out = E_I + E_Q exp(j phi_P) + delta_P E_I.
    ``gamma_P`` is kept as an optional compatibility multiplier on the Q branch;
    its default is 1 and it is not used for the parent ER by default.
    Branch and parent loss factors are optical power factors. I and Q branch
    losses are applied to their child MZM blocks. The parent/main POSITIVE block
    is applied to the Q branch before the final external 2x2 combiner, matching
    the VPI build where the phase block is in the Q optical path.
    """

    phi_I_arr = np.asarray(phi_I, dtype=float)
    phi_Q_arr = np.asarray(phi_Q, dtype=float)
    phi_P_arr = np.asarray(phi_P, dtype=float)
    E_arr = np.asarray(E_in, dtype=complex)

    if float(loss_factor) < 0 or float(branch_I_loss_factor) < 0:
        raise ValueError("loss factors must be >= 0")
    if float(branch_Q_loss_factor) < 0 or float(parent_loss_factor) < 0:
        raise ValueError("loss factors must be >= 0")
    er_model_eff = _normalize_er_model(er_model)

    H_I = mzm_block_output_field(
        1.0,
        phi_I_arr,
        lower_arm_phase_sense="NEGATIVE",
        delta=float(delta_I),
        loss_factor=float(branch_I_loss_factor),
        er_model=er_model_eff,
    )
    H_Q = mzm_block_output_field(
        1.0,
        phi_Q_arr,
        lower_arm_phase_sense="NEGATIVE",
        delta=float(delta_Q),
        loss_factor=float(branch_Q_loss_factor),
        er_model=er_model_eff,
    )
    H_P = mzm_block_output_field(
        1.0,
        phi_P_arr,
        lower_arm_phase_sense="POSITIVE",
        loss_factor=float(parent_loss_factor),
        er_model=er_model_eff,
    )
    amp_common = np.sqrt(float(loss_factor))
    parent_leakage = 1.0 + float(delta_P) if er_model_eff == "thesis" else 1.0

    field_sum = (
        parent_leakage * H_I
        + float(gamma_P) * H_Q * H_P
    )
    return E_arr * amp_common * 0.5 * field_sum


def dpmzm_transfer_power(
    phi_I: np.ndarray | float,
    phi_Q: np.ndarray | float,
    phi_P: np.ndarray | float,
    *,
    delta_I: float = 0.0,
    delta_Q: float = 0.0,
    delta_P: float = 0.0,
    gamma_P: float = 1.0,
    loss_factor: float = 1.0,
    branch_I_loss_factor: float = 1.0,
    branch_Q_loss_factor: float = 1.0,
    parent_loss_factor: float = 1.0,
    er_model: str = "vpi",
) -> np.ndarray:
    """Return normalized optical power transfer |E_out|^2 / |E_in|^2."""

    E_out = dpmzm_output_field(
        1.0,
        phi_I,
        phi_Q,
        phi_P,
        delta_I=float(delta_I),
        delta_Q=float(delta_Q),
        delta_P=float(delta_P),
        gamma_P=float(gamma_P),
        loss_factor=float(loss_factor),
        branch_I_loss_factor=float(branch_I_loss_factor),
        branch_Q_loss_factor=float(branch_Q_loss_factor),
        parent_loss_factor=float(parent_loss_factor),
        er_model=er_model,
    )
    return np.abs(E_out) ** 2


def _resolve(value: float | None, fallback: float) -> float:
    return float(fallback if value is None else value)


def _loss_factor_from_db(loss_db: float | None) -> float:
    return 1.0 if loss_db is None else float(10.0 ** (-float(loss_db) / 10.0))


def _coerce_waveform(
    name: str,
    value: np.ndarray | float | None,
    t: np.ndarray,
) -> np.ndarray:
    if value is None:
        return np.zeros_like(t, dtype=float)
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 0:
        return np.full_like(t, float(arr), dtype=float)
    if arr.size != t.size:
        raise ValueError(f"{name} must be scalar or have length {t.size}")
    return arr.reshape(t.shape).astype(float, copy=False)


def _sine_wave(amp: float, freq: float, phase: float, t: np.ndarray) -> np.ndarray:
    if float(amp) == 0.0 or float(freq) == 0.0:
        return np.zeros_like(t, dtype=float)
    return float(amp) * np.sin(2.0 * float(np.pi) * float(freq) * t + float(phase))


def _noise_result(
    *,
    I_pd: np.ndarray,
    RBW_Hz: float,
    Temp_K: float,
    RIN_dB_Hz: float,
    R_load: float,
    vpi_compatible_dbm: bool,
) -> NoiseResult:
    I_av = float(np.mean(I_pd))

    K_Boltzmann = 1.38e-23
    q_electron = 1.6e-19

    P_thermal_W = K_Boltzmann * float(Temp_K) * float(RBW_Hz)
    P_shot_W = 2.0 * q_electron * I_av * float(RBW_Hz) * float(R_load)
    P_rin_W = (
        (10.0 ** (float(RIN_dB_Hz) / 10.0))
        * (I_av ** 2)
        * float(R_load)
        * float(RBW_Hz)
    )
    P_noise_total_W = P_thermal_W + P_shot_W + P_rin_W

    scale_factor = 1.0 / float(R_load) if bool(vpi_compatible_dbm) else 1.0
    P_noise_total_W_scaled = P_noise_total_W * scale_factor
    P_noise_floor_dBm = 10.0 * np.log10(P_noise_total_W_scaled * 1000.0 + 1e-30)
    P_density_W_Hz_scaled = P_noise_total_W_scaled / float(RBW_Hz)
    P_density_dBmHz = 10.0 * np.log10(P_density_W_Hz_scaled * 1000.0 + 1e-30)

    return NoiseResult(
        P_thermal_W=float(P_thermal_W * scale_factor),
        P_shot_W=float(P_shot_W * scale_factor),
        P_rin_W=float(P_rin_W * scale_factor),
        P_noise_total_W=float(P_noise_total_W_scaled),
        P_noise_floor_dBm=float(P_noise_floor_dBm),
        P_density_dBmHz=float(P_density_dBmHz),
    )


def _spectrum_result(
    *,
    E_out: np.ndarray,
    I_pd: np.ndarray,
    Fs: float,
    R_load: float,
    noise: NoiseResult,
    f_rf: float,
    vpi_compatible_dbm: bool,
    rng: np.random.Generator,
) -> SpectrumResult:
    L = int(E_out.size)
    E_spec = np.fft.fftshift(np.fft.fft(E_out)) / L
    f_opt = (np.arange(-L / 2, L / 2) * (float(Fs) / L))
    P_opt_spec_W = np.abs(E_spec) ** 2 * 1000.0
    P_opt_spec_dBm = 10.0 * np.log10(P_opt_spec_W + 1e-20)

    Y_elec = np.fft.fft(I_pd)
    P2 = np.abs(Y_elec / L)
    half = L // 2
    P1 = P2[: half + 1].copy()
    if P1.size > 2:
        P1[1:-1] = 2.0 * P1[1:-1]
    f_elec = float(Fs) * np.arange(0, half + 1) / L

    if bool(vpi_compatible_dbm):
        P_sig_W = 0.5 * (P1 ** 2)
        if P1.size > 0:
            P_sig_W[0] = P1[0] ** 2
    else:
        P_sig_W = 0.5 * (P1 ** 2) * float(R_load)
        if P1.size > 0:
            P_sig_W[0] = (P1[0] ** 2) * float(R_load)

    noise_trace_W = noise.P_noise_total_W * (-np.log(rng.random(P_sig_W.shape)))
    P_total_W = P_sig_W + noise_trace_W
    P_elec_spec_dBm = 10.0 * np.log10(P_total_W * 1000.0 + 1e-20)

    def value_at(freq_hz: float) -> float:
        idx = int(np.argmin(np.abs(f_elec - float(freq_hz))))
        return float(P_elec_spec_dBm[idx])

    return SpectrumResult(
        f_opt=f_opt,
        P_opt_spec_dBm=P_opt_spec_dBm,
        f_elec=f_elec,
        P_elec_spec_dBm=P_elec_spec_dBm,
        val_1G_dBm=value_at(1e9),
        val_2G_dBm=value_at(2e9),
        val_rf_dBm=value_at(float(f_rf)),
        val_2rf_dBm=value_at(2.0 * float(f_rf)),
    )


def _bias_scan(
    *,
    E_in: float,
    V_DCI: float,
    V_DCQ: float,
    V_DCP: float,
    Vpi_I: float,
    Vpi_Q: float,
    Vpi_P: float,
    delta_I: float,
    delta_Q: float,
    delta_P: float,
    gamma_P: float,
    loss_factor: float,
    branch_I_loss_factor: float,
    branch_Q_loss_factor: float,
    parent_loss_factor: float,
    er_model: str,
) -> BiasScanResult:
    V_I_scan = np.linspace(-2.0 * float(Vpi_I), 2.0 * float(Vpi_I), 1000)
    V_Q_scan = np.linspace(-2.0 * float(Vpi_Q), 2.0 * float(Vpi_Q), 1000)
    V_P_scan = np.linspace(-2.0 * float(Vpi_P), 2.0 * float(Vpi_P), 1000)

    phi_I_dc = voltage_to_phase(float(V_DCI), float(Vpi_I))
    phi_Q_dc = voltage_to_phase(float(V_DCQ), float(Vpi_Q))
    phi_P_dc = voltage_to_phase(float(V_DCP), float(Vpi_P))

    def power_mw(phi_I, phi_Q, phi_P) -> np.ndarray:
        E = dpmzm_output_field(
            E_in,
            phi_I,
            phi_Q,
            phi_P,
            delta_I=float(delta_I),
            delta_Q=float(delta_Q),
            delta_P=float(delta_P),
            gamma_P=float(gamma_P),
            loss_factor=float(loss_factor),
            branch_I_loss_factor=float(branch_I_loss_factor),
            branch_Q_loss_factor=float(branch_Q_loss_factor),
            parent_loss_factor=float(parent_loss_factor),
            er_model=er_model,
        )
        return np.abs(E) ** 2 * 1000.0

    P_I_scan_mW = power_mw(voltage_to_phase(V_I_scan, Vpi_I), phi_Q_dc, phi_P_dc)
    P_Q_scan_mW = power_mw(phi_I_dc, voltage_to_phase(V_Q_scan, Vpi_Q), phi_P_dc)
    P_P_scan_mW = power_mw(phi_I_dc, phi_Q_dc, voltage_to_phase(V_P_scan, Vpi_P))
    curr_P_mW = float(np.asarray(power_mw(phi_I_dc, phi_Q_dc, phi_P_dc)).reshape(-1)[0])
    curr_P_dBm = float(10.0 * np.log10(curr_P_mW + 1e-20))

    return BiasScanResult(
        V_I_scan=V_I_scan,
        P_I_scan_mW=P_I_scan_mW,
        V_Q_scan=V_Q_scan,
        P_Q_scan_mW=P_Q_scan_mW,
        V_P_scan=V_P_scan,
        P_P_scan_mW=P_P_scan_mW,
        V_DCI=float(V_DCI),
        V_DCQ=float(V_DCQ),
        V_DCP=float(V_DCP),
        curr_P_mW=curr_P_mW,
        curr_P_dBm=curr_P_dBm,
    )


def simulate_dpmzm(
    SymbolRate: float = 10e9,
    Fs: float = 100e9,
    T_total: float = 10e-6,
    Vpi: float = 5.0,
    Vpi_I: float | None = None,
    Vpi_Q: float | None = None,
    Vpi_P: float | None = None,
    ER_dB: float | None = 30.0,
    ER_I_dB: float | None = None,
    ER_Q_dB: float | None = None,
    ER_P_dB: float | None = None,
    IL_dB: float = 0.0,
    IL_I_dB: float | None = 6.0,
    IL_Q_dB: float | None = 6.0,
    IL_P_dB: float | None = 6.0,
    Responsivity: float = 0.786,
    R_load: float = 50.0,
    Pin_dBm: float = 10.0,
    pd_tap: float = 1.0,
    Temp_K: float = 290.0,
    RIN_dB_Hz: float = -145.0,
    V_DCI: float | None = None,
    V_DCQ: float | None = None,
    V_DCP: float | None = None,
    f_rf: float = 1e9,
    V_RFI_amp: float = 0.0,
    V_RFQ_amp: float = 0.0,
    rf_phase_I: float = 0.0,
    rf_phase_Q: float = 0.0,
    V_RFI: np.ndarray | float | None = None,
    V_RFQ: np.ndarray | float | None = None,
    V_dither_I_amp: float = 0.0,
    V_dither_Q_amp: float = 0.0,
    V_dither_P_amp: float = 0.0,
    f_dither_I: float = 10e3,
    f_dither_Q: float = 11e3,
    f_dither_P: float = 12e3,
    dither_phase_I: float = 0.0,
    dither_phase_Q: float = 0.0,
    dither_phase_P: float = 0.0,
    V_dither_I: np.ndarray | float | None = None,
    V_dither_Q: np.ndarray | float | None = None,
    V_dither_P: np.ndarray | float | None = None,
    ideal: bool = False,
    delta_I: float | None = None,
    delta_Q: float | None = None,
    delta_P: float | None = None,
    gamma_P: float | None = None,
    er_model: str = "vpi",
    vpi_compatible_dbm: bool = False,
    rng_seed: int | None = None,
) -> SimulationResult:
    """Run DPMZM output simulation with optional RF and dither voltages.

    RF and dither inputs are generic additive voltages. Use explicit bias and
    waveform parameters to realize CS-SSB, OSSB, or other operating points.
    ``IL_I_dB``, ``IL_Q_dB``, and ``IL_P_dB`` are per-MZM block insertion
    losses; ``IL_dB`` is reserved for extra link/common loss. ``er_model='vpi'``
    matches VPI's normalized finite-extinction-ratio behavior. ``er_model`` can
    be set to ``'thesis'`` to reproduce the earlier residual-field derivation.
    ``SymbolRate`` is accepted for API symmetry with ``mzm.model.simulate_mzm``.
    """

    _ = SymbolRate
    if float(Fs) <= 0 or float(T_total) <= 0:
        raise ValueError("Fs and T_total must be > 0")
    if float(pd_tap) <= 0:
        raise ValueError("pd_tap must be > 0")
    er_model_eff = _normalize_er_model(er_model)

    Vpi_I_eff = _resolve(Vpi_I, Vpi)
    Vpi_Q_eff = _resolve(Vpi_Q, Vpi)
    Vpi_P_eff = _resolve(Vpi_P, Vpi)
    if min(Vpi_I_eff, Vpi_Q_eff, Vpi_P_eff) <= 0:
        raise ValueError("all Vpi values must be > 0")

    V_DCI_eff = _resolve(V_DCI, Vpi_I_eff)
    V_DCQ_eff = _resolve(V_DCQ, Vpi_Q_eff)
    V_DCP_eff = _resolve(V_DCP, Vpi_P_eff / 2.0)

    L = int(round(float(T_total) * float(Fs)))
    if L < 2:
        raise ValueError("simulation length too small; increase T_total or Fs")
    t = np.arange(L, dtype=float) / float(Fs)
    RBW_Hz = float(Fs) / float(L)

    Pin_W = 10.0 ** ((float(Pin_dBm) - 30.0) / 10.0)
    E_in = float(np.sqrt(Pin_W))

    loss_factor = _loss_factor_from_db(IL_dB)
    branch_I_loss_factor = _loss_factor_from_db(IL_I_dB)
    branch_Q_loss_factor = _loss_factor_from_db(IL_Q_dB)
    parent_loss_factor = _loss_factor_from_db(IL_P_dB)

    if bool(ideal):
        delta_I_eff = 0.0
        delta_Q_eff = 0.0
        delta_P_eff = 0.0
        gamma_P_eff = 1.0
    else:
        ER_I_eff = ER_dB if ER_I_dB is None else ER_I_dB
        ER_Q_eff = ER_dB if ER_Q_dB is None else ER_Q_dB
        ER_P_eff = ER_dB if ER_P_dB is None else ER_P_dB
        delta_I_eff = delta_from_er_db(ER_I_eff) if delta_I is None else float(delta_I)
        delta_Q_eff = delta_from_er_db(ER_Q_eff) if delta_Q is None else float(delta_Q)
        delta_P_eff = delta_from_er_db(ER_P_eff) if delta_P is None else float(delta_P)
        gamma_P_eff = 1.0 if gamma_P is None else float(gamma_P)

    rf_I = (
        _coerce_waveform("V_RFI", V_RFI, t)
        if V_RFI is not None
        else _sine_wave(V_RFI_amp, f_rf, rf_phase_I, t)
    )
    rf_Q = (
        _coerce_waveform("V_RFQ", V_RFQ, t)
        if V_RFQ is not None
        else _sine_wave(V_RFQ_amp, f_rf, rf_phase_Q, t)
    )
    dither_I = (
        _coerce_waveform("V_dither_I", V_dither_I, t)
        if V_dither_I is not None
        else _sine_wave(V_dither_I_amp, f_dither_I, dither_phase_I, t)
    )
    dither_Q = (
        _coerce_waveform("V_dither_Q", V_dither_Q, t)
        if V_dither_Q is not None
        else _sine_wave(V_dither_Q_amp, f_dither_Q, dither_phase_Q, t)
    )
    dither_P = (
        _coerce_waveform("V_dither_P", V_dither_P, t)
        if V_dither_P is not None
        else _sine_wave(V_dither_P_amp, f_dither_P, dither_phase_P, t)
    )

    V_I_t = float(V_DCI_eff) + rf_I + dither_I
    V_Q_t = float(V_DCQ_eff) + rf_Q + dither_Q
    V_P_t = float(V_DCP_eff) + dither_P

    phi_I = voltage_to_phase(V_I_t, Vpi_I_eff)
    phi_Q = voltage_to_phase(V_Q_t, Vpi_Q_eff)
    phi_P = voltage_to_phase(V_P_t, Vpi_P_eff)

    E_out = dpmzm_output_field(
        E_in,
        phi_I,
        phi_Q,
        phi_P,
        delta_I=delta_I_eff,
        delta_Q=delta_Q_eff,
        delta_P=delta_P_eff,
        gamma_P=gamma_P_eff,
        loss_factor=loss_factor,
        branch_I_loss_factor=branch_I_loss_factor,
        branch_Q_loss_factor=branch_Q_loss_factor,
        parent_loss_factor=parent_loss_factor,
        er_model=er_model_eff,
    )

    P_opt_inst_W = np.abs(E_out) ** 2
    P_pd_inst_W = P_opt_inst_W * float(pd_tap)
    P_pd_avg_W = float(np.mean(P_pd_inst_W))
    P_pd_avg_dBm = float(10.0 * np.log10(P_pd_avg_W * 1000.0 + 1e-30))
    I_pd = float(Responsivity) * P_pd_inst_W

    noise_res = _noise_result(
        I_pd=I_pd,
        RBW_Hz=RBW_Hz,
        Temp_K=Temp_K,
        RIN_dB_Hz=RIN_dB_Hz,
        R_load=R_load,
        vpi_compatible_dbm=bool(vpi_compatible_dbm),
    )
    rng = np.random.default_rng(rng_seed)
    spectrum_res = _spectrum_result(
        E_out=E_out,
        I_pd=I_pd,
        Fs=Fs,
        R_load=R_load,
        noise=noise_res,
        f_rf=f_rf,
        vpi_compatible_dbm=bool(vpi_compatible_dbm),
        rng=rng,
    )
    bias_res = _bias_scan(
        E_in=E_in,
        V_DCI=V_DCI_eff,
        V_DCQ=V_DCQ_eff,
        V_DCP=V_DCP_eff,
        Vpi_I=Vpi_I_eff,
        Vpi_Q=Vpi_Q_eff,
        Vpi_P=Vpi_P_eff,
        delta_I=delta_I_eff,
        delta_Q=delta_Q_eff,
        delta_P=delta_P_eff,
        gamma_P=gamma_P_eff,
        loss_factor=loss_factor,
        branch_I_loss_factor=branch_I_loss_factor,
        branch_Q_loss_factor=branch_Q_loss_factor,
        parent_loss_factor=parent_loss_factor,
        er_model=er_model_eff,
    )

    params = {
        "Fs": float(Fs),
        "T_total": float(T_total),
        "RBW_Hz": float(RBW_Hz),
        "Vpi_I": float(Vpi_I_eff),
        "Vpi_Q": float(Vpi_Q_eff),
        "Vpi_P": float(Vpi_P_eff),
        "ER_I_dB": None if ER_I_dB is None else float(ER_I_dB),
        "ER_Q_dB": None if ER_Q_dB is None else float(ER_Q_dB),
        "ER_P_dB": None if ER_P_dB is None else float(ER_P_dB),
        "ER_dB": None if ER_dB is None else float(ER_dB),
        "IL_dB": float(IL_dB),
        "IL_I_dB": None if IL_I_dB is None else float(IL_I_dB),
        "IL_Q_dB": None if IL_Q_dB is None else float(IL_Q_dB),
        "IL_P_dB": None if IL_P_dB is None else float(IL_P_dB),
        "delta_I": float(delta_I_eff),
        "delta_Q": float(delta_Q_eff),
        "delta_P": float(delta_P_eff),
        "gamma_P": float(gamma_P_eff),
        "er_model": er_model_eff,
        "V_DCI": float(V_DCI_eff),
        "V_DCQ": float(V_DCQ_eff),
        "V_DCP": float(V_DCP_eff),
        "f_rf": float(f_rf),
        "V_RFI_amp": float(V_RFI_amp),
        "V_RFQ_amp": float(V_RFQ_amp),
        "rf_phase_I": float(rf_phase_I),
        "rf_phase_Q": float(rf_phase_Q),
        "Pin_dBm": float(Pin_dBm),
        "Responsivity": float(Responsivity),
        "R_load": float(R_load),
        "Temp_K": float(Temp_K),
        "RIN_dB_Hz": float(RIN_dB_Hz),
        "pd_tap": float(pd_tap),
        "vpi_compatible_dbm": bool(vpi_compatible_dbm),
        "ideal": bool(ideal),
    }

    return SimulationResult(
        t=t,
        RBW_Hz=RBW_Hz,
        E_out=E_out,
        P_opt_inst_W=P_opt_inst_W,
        P_pd_avg_dBm=P_pd_avg_dBm,
        I_pd=I_pd,
        noise=noise_res,
        spectrum=spectrum_res,
        bias_scan=bias_res,
        Pin_dBm=float(Pin_dBm),
        pd_tap=float(pd_tap),
        params=params,
    )
