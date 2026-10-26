"""Sweep I bias and measure the P-pilot second harmonic in DPMZM PD current.

Default case:

    python -m dpmzm.p_pilot_second_sweep

This keeps the Q child MZM near a source bias of 1.527 V, keeps the parent
P-path phase block at -0.1 V, adds a 100 mV peak pilot on P at 12 GHz, sweeps
the I child MZM source bias from -10 V to 10 V, and measures the PD tone at
24 GHz.

The default source-to-model mapping follows the VPI DiffMZ_DSM setup used in
this project:

    NEGATIVE child MZM source voltage -> 2x push-pull equivalent phase voltage
    POSITIVE P block source voltage   -> 1x common-phase voltage
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from ..core.model import _noise_result, delta_from_er_db, mzm_block_output_field, voltage_to_phase


def _dbm(power_w: np.ndarray | float) -> np.ndarray | float:
    return 10.0 * np.log10(np.asarray(power_w, dtype=float) * 1000.0 + 1e-30)


def _loss_factor(loss_db: float | None) -> float:
    return 1.0 if loss_db is None else float(10.0 ** (-float(loss_db) / 10.0))


def _format_freq_label(freq_hz: float) -> str:
    freq = float(freq_hz)
    for scale, suffix in ((1e9, "GHz"), (1e6, "MHz"), (1e3, "kHz")):
        if abs(freq) >= scale:
            return f"{freq / scale:g} {suffix}"
    return f"{freq:g} Hz"


def _format_freq_tag(freq_hz: float) -> str:
    return _format_freq_label(freq_hz).replace(" ", "").replace(".", "p").lower()


def run_p_pilot_second_sweep(
    *,
    out_dir: str | Path = "artifacts/dpmzm_p_pilot_second_sweep",
    V_DCI_source_start: float = -10.0,
    V_DCI_source_stop: float = 10.0,
    V_DCI_source_step: float = 0.05,
    V_DCQ_source: float = 1.527,
    V_DCP_source: float = -0.1,
    child_source_gain: float = 2.0,
    parent_source_gain: float = 1.0,
    Vpi: float = 5.0,
    ER_dB: float | None = 30.0,
    IL_dB: float = 0.0,
    IL_I_dB: float = 6.0,
    IL_Q_dB: float = 6.0,
    IL_P_dB: float = 6.0,
    Pin_dBm: float = 10.0,
    Responsivity: float = 0.786,
    pd_tap: float = 1.0,
    R_load: float = 1.0,
    Fs: float = 128e9,
    T_total: float = 8.192e-6,
    V_dither_P_source_amp: float = 0.1,
    f_dither_P: float = 12e9,
    dither_phase_P: float = 0.0,
    er_model: str = "vpi",
    vpi_compatible_dbm: bool = True,
    Temp_K: float = 290.0,
    RIN_dB_Hz: float = -145.0,
) -> dict[str, np.ndarray | float | str]:
    """Run the sweep and save CSV/NPZ/PNG outputs."""

    if float(Fs) <= 0 or float(T_total) <= 0:
        raise ValueError("Fs and T_total must be > 0")
    if float(V_DCI_source_step) <= 0:
        raise ValueError("V_DCI_source_step must be > 0")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    n = int(round(float(Fs) * float(T_total)))
    if n < 2:
        raise ValueError("simulation length too small")
    t = np.arange(n, dtype=float) / float(Fs)
    rbw_hz = float(Fs) / n

    target_freq_hz = 2.0 * float(f_dither_P)
    target_bin = target_freq_hz / rbw_hz
    if abs(target_bin - round(target_bin)) > 1e-6:
        raise ValueError(
            f"target frequency is not coherent with the FFT bin: "
            f"target/RBW={target_bin:.12g}"
        )

    V_DCI_source_values = np.round(
        np.arange(
            float(V_DCI_source_start),
            float(V_DCI_source_stop) + 0.5 * float(V_DCI_source_step),
            float(V_DCI_source_step),
        ),
        12,
    )
    V_DCI_eff_values = float(child_source_gain) * V_DCI_source_values
    V_DCQ_eff = float(child_source_gain) * float(V_DCQ_source)
    V_DCP_eff = float(parent_source_gain) * float(V_DCP_source)
    V_dither_P_eff_amp = float(parent_source_gain) * float(V_dither_P_source_amp)

    Pin_W = 10.0 ** ((float(Pin_dBm) - 30.0) / 10.0)
    E_in = float(np.sqrt(Pin_W))
    delta = delta_from_er_db(ER_dB)

    global_loss_factor = _loss_factor(IL_dB)
    branch_I_loss_factor = _loss_factor(IL_I_dB)
    branch_Q_loss_factor = _loss_factor(IL_Q_dB)
    parent_loss_factor = _loss_factor(IL_P_dB)

    phi_Q = voltage_to_phase(V_DCQ_eff, Vpi)
    V_P_t = (
        V_DCP_eff
        + V_dither_P_eff_amp
        * np.sin(2.0 * np.pi * float(f_dither_P) * t + float(dither_phase_P))
    )
    phi_P = voltage_to_phase(V_P_t, Vpi)

    H_Q = complex(
        mzm_block_output_field(
            1.0,
            phi_Q,
            lower_arm_phase_sense="NEGATIVE",
            delta=delta,
            loss_factor=branch_Q_loss_factor,
            er_model=er_model,
        )
    )
    H_P = mzm_block_output_field(
        1.0,
        phi_P,
        lower_arm_phase_sense="POSITIVE",
        loss_factor=parent_loss_factor,
        er_model=er_model,
    )
    target_idx = int(round(target_bin))
    hp_spec = np.fft.fft(H_P) / n
    hp_conj_spec = np.fft.fft(np.conj(H_P)) / n
    hp_coeff = complex(hp_spec[target_idx])
    hp_conj_coeff = complex(hp_conj_spec[target_idx])
    hp_dc = complex(hp_spec[0])
    hp_conj_dc = complex(hp_conj_spec[0])
    hp_power_mean = float(np.mean(np.abs(H_P) ** 2))

    parent_leakage = 1.0 + float(delta) if str(er_model).strip().lower() == "thesis" else 1.0
    pd_current_scale = (
        float(Responsivity)
        * float(pd_tap)
        * Pin_W
        * global_loss_factor
        * 0.25
    )
    pd_power_scale = float(pd_tap) * Pin_W * global_loss_factor * 0.25

    current_peak_A = np.empty_like(V_DCI_source_values, dtype=float)
    signal_power_W = np.empty_like(V_DCI_source_values, dtype=float)
    signal_power_dBm = np.empty_like(V_DCI_source_values, dtype=float)
    noise_floor_dBm = np.empty_like(V_DCI_source_values, dtype=float)
    pd_avg_dBm = np.empty_like(V_DCI_source_values, dtype=float)
    bin_freq_Hz = np.empty_like(V_DCI_source_values, dtype=float)

    for idx, V_DCI_eff in enumerate(V_DCI_eff_values):
        phi_I = voltage_to_phase(float(V_DCI_eff), Vpi)
        H_I = complex(
            mzm_block_output_field(
                1.0,
                phi_I,
                lower_arm_phase_sense="NEGATIVE",
                delta=delta,
                loss_factor=branch_I_loss_factor,
                er_model=er_model,
            )
        )
        H_I_eff = parent_leakage * H_I

        current_coeff = pd_current_scale * (
            H_I_eff * np.conj(H_Q) * hp_conj_coeff
            + np.conj(H_I_eff) * H_Q * hp_coeff
        )
        peak_amp = 2.0 * abs(current_coeff)
        if bool(vpi_compatible_dbm):
            power_w = 0.5 * peak_amp**2
        else:
            power_w = 0.5 * peak_amp**2 * float(R_load)

        pd_power_avg = pd_power_scale * (
            abs(H_I_eff) ** 2
            + abs(H_Q) ** 2 * hp_power_mean
            + H_I_eff * np.conj(H_Q) * hp_conj_dc
            + np.conj(H_I_eff) * H_Q * hp_dc
        )
        pd_power_avg = float(np.real(pd_power_avg))
        pd_current_avg = float(Responsivity) * pd_power_avg
        noise = _noise_result(
            I_pd=np.asarray([pd_current_avg], dtype=float),
            RBW_Hz=rbw_hz,
            Temp_K=float(Temp_K),
            RIN_dB_Hz=float(RIN_dB_Hz),
            R_load=float(R_load),
            vpi_compatible_dbm=bool(vpi_compatible_dbm),
        )

        current_peak_A[idx] = peak_amp
        signal_power_W[idx] = power_w
        signal_power_dBm[idx] = float(_dbm(power_w))
        noise_floor_dBm[idx] = float(_dbm(noise.P_noise_total_W))
        pd_avg_dBm[idx] = float(_dbm(pd_power_avg))
        bin_freq_Hz[idx] = float(target_idx * float(Fs) / n)

    freq_label = _format_freq_label(target_freq_hz)
    freq_tag = _format_freq_tag(target_freq_hz)

    csv_path = out_path / f"i_bias_p_pilot_2nd_{freq_tag}_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "V_DCI_source_V",
                "V_DCI_effective_V",
                "V_DCQ_source_V",
                "V_DCQ_effective_V",
                "V_DCP_source_V",
                "V_DCP_effective_V",
                "tone_bin_Hz",
                "I_tone_peak_A",
                "P_tone_signal_W",
                "P_tone_signal_dBm",
                "P_noise_floor_dBm",
                "P_pd_avg_dBm",
            ]
        )
        writer.writerows(
            zip(
                V_DCI_source_values,
                V_DCI_eff_values,
                np.full_like(V_DCI_source_values, float(V_DCQ_source), dtype=float),
                np.full_like(V_DCI_source_values, V_DCQ_eff, dtype=float),
                np.full_like(V_DCI_source_values, float(V_DCP_source), dtype=float),
                np.full_like(V_DCI_source_values, V_DCP_eff, dtype=float),
                bin_freq_Hz,
                current_peak_A,
                signal_power_W,
                signal_power_dBm,
                noise_floor_dBm,
                pd_avg_dBm,
            )
        )

    npz_path = out_path / f"i_bias_p_pilot_2nd_{freq_tag}_sweep.npz"
    np.savez(
        npz_path,
        V_DCI_source_values=V_DCI_source_values,
        V_DCI_eff_values=V_DCI_eff_values,
        V_DCQ_source=float(V_DCQ_source),
        V_DCQ_eff=V_DCQ_eff,
        V_DCP_source=float(V_DCP_source),
        V_DCP_eff=V_DCP_eff,
        bin_freq_Hz=bin_freq_Hz,
        current_peak_A=current_peak_A,
        signal_power_W=signal_power_W,
        signal_power_dBm=signal_power_dBm,
        noise_floor_dBm=noise_floor_dBm,
        pd_avg_dBm=pd_avg_dBm,
        rbw_hz=rbw_hz,
        fs=float(Fs),
        t_total=float(T_total),
        f_dither_P=float(f_dither_P),
        target_freq_hz=target_freq_hz,
        V_dither_P_source_amp=float(V_dither_P_source_amp),
        V_dither_P_eff_amp=V_dither_P_eff_amp,
        child_source_gain=float(child_source_gain),
        parent_source_gain=float(parent_source_gain),
    )

    png_path = out_path / f"i_bias_p_pilot_2nd_{freq_tag}_sweep.png"
    fig, ax1 = plt.subplots(figsize=(9.5, 5.2), dpi=150)
    ax1.plot(V_DCI_source_values, signal_power_dBm, color="#1f77b4", linewidth=1.8)
    ax1.set_xlabel("I child source bias V_DCI (V)")
    ax1.set_ylabel(f"PD {freq_label} tone power (dBm)")
    ax1.grid(True, alpha=0.28)
    ax1.set_title(
        f"P-pilot second harmonic vs I bias, "
        f"Q={V_DCQ_source:g} V source, P={V_DCP_source:g} V source"
    )

    ax2 = ax1.twinx()
    ax2.plot(V_DCI_source_values, current_peak_A, color="#ff7f0e", linewidth=1.2, alpha=0.7)
    ax2.set_ylabel(f"PD {freq_label} current peak (A)")

    info = (
        f"fP={_format_freq_label(f_dither_P)}, RBW={_format_freq_label(rbw_hz)}, "
        f"Fs={_format_freq_label(Fs)}, N={n}"
    )
    fig.text(0.5, 0.01, info, ha="center", va="bottom", fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(png_path)
    plt.close(fig)

    return {
        "csv_path": str(csv_path),
        "npz_path": str(npz_path),
        "png_path": str(png_path),
        "rbw_hz": rbw_hz,
        "target_freq_hz": target_freq_hz,
        "min_power_dBm": float(np.min(signal_power_dBm)),
        "max_power_dBm": float(np.max(signal_power_dBm)),
        "min_at_V_DCI_source": float(V_DCI_source_values[int(np.argmin(signal_power_dBm))]),
        "max_at_V_DCI_source": float(V_DCI_source_values[int(np.argmax(signal_power_dBm))]),
    }


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="artifacts/dpmzm_p_pilot_second_sweep")
    parser.add_argument("--i-start", type=float, default=-10.0)
    parser.add_argument("--i-stop", type=float, default=10.0)
    parser.add_argument("--i-step", type=float, default=0.05)
    parser.add_argument("--q-bias", type=float, default=1.527)
    parser.add_argument("--p-bias", type=float, default=-0.1)
    parser.add_argument("--child-source-gain", type=float, default=2.0)
    parser.add_argument("--parent-source-gain", type=float, default=1.0)
    parser.add_argument("--vpi", type=float, default=5.0)
    parser.add_argument("--er-db", type=float, default=30.0)
    parser.add_argument("--il-db", type=float, default=0.0)
    parser.add_argument("--il-i-db", type=float, default=6.0)
    parser.add_argument("--il-q-db", type=float, default=6.0)
    parser.add_argument("--il-p-db", type=float, default=6.0)
    parser.add_argument("--pin-dbm", type=float, default=10.0)
    parser.add_argument("--responsivity", type=float, default=0.786)
    parser.add_argument("--pd-tap", type=float, default=1.0)
    parser.add_argument("--r-load", type=float, default=1.0)
    parser.add_argument("--fs", type=float, default=128e9)
    parser.add_argument("--t-total", type=float, default=8.192e-6)
    parser.add_argument("--p-dither-amp", type=float, default=0.1)
    parser.add_argument("--p-dither-freq", type=float, default=12e9)
    parser.add_argument("--p-dither-phase", type=float, default=0.0)
    parser.add_argument("--er-model", choices=["vpi", "thesis"], default="vpi")
    parser.add_argument("--no-vpi-compatible-dbm", action="store_true")
    parser.add_argument("--temp-k", type=float, default=290.0)
    parser.add_argument("--rin-db-hz", type=float, default=-145.0)
    return parser


def main() -> None:
    args = build_argparser().parse_args()
    result = run_p_pilot_second_sweep(
        out_dir=args.out_dir,
        V_DCI_source_start=args.i_start,
        V_DCI_source_stop=args.i_stop,
        V_DCI_source_step=args.i_step,
        V_DCQ_source=args.q_bias,
        V_DCP_source=args.p_bias,
        child_source_gain=args.child_source_gain,
        parent_source_gain=args.parent_source_gain,
        Vpi=args.vpi,
        ER_dB=args.er_db,
        IL_dB=args.il_db,
        IL_I_dB=args.il_i_db,
        IL_Q_dB=args.il_q_db,
        IL_P_dB=args.il_p_db,
        Pin_dBm=args.pin_dbm,
        Responsivity=args.responsivity,
        pd_tap=args.pd_tap,
        R_load=args.r_load,
        Fs=args.fs,
        T_total=args.t_total,
        V_dither_P_source_amp=args.p_dither_amp,
        f_dither_P=args.p_dither_freq,
        dither_phase_P=args.p_dither_phase,
        er_model=args.er_model,
        vpi_compatible_dbm=not args.no_vpi_compatible_dbm,
        Temp_K=args.temp_k,
        RIN_dB_Hz=args.rin_db_hz,
    )
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
