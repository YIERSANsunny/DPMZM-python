"""Sweep DPMZM P-bias and measure the PD pilot beat term.

Default case:

    python -m dpmzm.pilot_beat_sweep

This sweeps V_DCP from -10 V to 10 V, with I/Q DC voltages at 1.527 V,
an I-path 100 mV peak dither at 1 kHz, and a P-path 100 mV peak dither
at 1.2 kHz. It measures the PD current tone at 2.2 kHz and, by default,
adds the model noise floor to emulate a measured spectrum bin.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from ..core.model import _noise_result, delta_from_er_db, dpmzm_output_field, voltage_to_phase


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
    label = _format_freq_label(freq_hz)
    return label.replace(" ", "").replace(".", "p").lower()


def _single_sided_tone(
    signal: np.ndarray,
    *,
    fs: float,
    freq_hz: float,
    r_load: float,
    vpi_compatible_dbm: bool,
) -> dict[str, float]:
    n = int(signal.size)
    spectrum = np.fft.rfft(signal) / n
    freqs = np.fft.rfftfreq(n, d=1.0 / float(fs))
    idx = int(np.argmin(np.abs(freqs - float(freq_hz))))

    peak_amp = float(np.abs(spectrum[idx]))
    if 0 < idx < freqs.size - 1:
        peak_amp *= 2.0

    if bool(vpi_compatible_dbm):
        power_w = peak_amp**2 if idx == 0 else 0.5 * peak_amp**2
    else:
        power_w = (peak_amp**2) * float(r_load) if idx == 0 else 0.5 * peak_amp**2 * float(r_load)

    return {
        "bin_index": float(idx),
        "bin_freq_Hz": float(freqs[idx]),
        "current_peak_A": float(peak_amp),
        "power_W": float(power_w),
        "power_dBm": float(_dbm(power_w)),
    }


def run_pilot_beat_sweep(
    *,
    out_dir: str | Path = "artifacts/dpmzm_pilot_beat_sweep",
    V_DCI: float = 1.527,
    V_DCQ: float = 1.527,
    V_DCP_start: float = -10.0,
    V_DCP_stop: float = 10.0,
    V_DCP_step: float = 0.05,
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
    Fs: float = 100e3,
    T_total: float = 1.0,
    V_dither_I_amp: float = 0.1,
    f_dither_I: float = 1e3,
    V_dither_P_amp: float = 0.1,
    f_dither_P: float = 1.2e3,
    dither_phase_I: float = 0.0,
    dither_phase_P: float = 0.0,
    er_model: str = "vpi",
    vpi_compatible_dbm: bool = True,
    noise_mode: str = "spectrum",
    Temp_K: float = 290.0,
    RIN_dB_Hz: float = -145.0,
    rng_seed: int = 0,
) -> dict[str, np.ndarray | float | str]:
    """Run the P-bias sweep and save CSV/NPZ/PNG outputs."""

    if float(Fs) <= 0 or float(T_total) <= 0:
        raise ValueError("Fs and T_total must be > 0")
    if float(V_DCP_step) <= 0:
        raise ValueError("V_DCP_step must be > 0")
    noise_mode_eff = str(noise_mode).strip().lower()
    if noise_mode_eff not in {"none", "spectrum"}:
        raise ValueError("noise_mode must be 'none' or 'spectrum'")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(int(rng_seed))

    n = int(round(float(Fs) * float(T_total)))
    if n < 2:
        raise ValueError("simulation length too small")
    t = np.arange(n, dtype=float) / float(Fs)
    rbw_hz = float(Fs) / n

    target_freq_hz = float(f_dither_I) + float(f_dither_P)
    V_DCP_values = np.round(
        np.arange(float(V_DCP_start), float(V_DCP_stop) + 0.5 * float(V_DCP_step), float(V_DCP_step)),
        12,
    )

    Pin_W = 10.0 ** ((float(Pin_dBm) - 30.0) / 10.0)
    E_in = float(np.sqrt(Pin_W))
    delta = delta_from_er_db(ER_dB)

    V_I_t = (
        float(V_DCI)
        + float(V_dither_I_amp)
        * np.sin(2.0 * np.pi * float(f_dither_I) * t + float(dither_phase_I))
    )
    V_Q_t = np.full_like(t, float(V_DCQ), dtype=float)
    phi_I = voltage_to_phase(V_I_t, Vpi)
    phi_Q = voltage_to_phase(V_Q_t, Vpi)

    current_peak_A = np.empty_like(V_DCP_values, dtype=float)
    signal_power_W = np.empty_like(V_DCP_values, dtype=float)
    signal_power_dBm = np.empty_like(V_DCP_values, dtype=float)
    noise_power_W = np.empty_like(V_DCP_values, dtype=float)
    noise_floor_dBm = np.empty_like(V_DCP_values, dtype=float)
    measured_power_W = np.empty_like(V_DCP_values, dtype=float)
    measured_power_dBm = np.empty_like(V_DCP_values, dtype=float)
    pd_avg_dBm = np.empty_like(V_DCP_values, dtype=float)
    bin_freq_Hz = np.empty_like(V_DCP_values, dtype=float)

    for idx, V_DCP in enumerate(V_DCP_values):
        V_P_t = (
            float(V_DCP)
            + float(V_dither_P_amp)
            * np.sin(2.0 * np.pi * float(f_dither_P) * t + float(dither_phase_P))
        )
        phi_P = voltage_to_phase(V_P_t, Vpi)

        E_out = dpmzm_output_field(
            E_in,
            phi_I,
            phi_Q,
            phi_P,
            delta_I=delta,
            delta_Q=delta,
            delta_P=delta,
            gamma_P=1.0,
            loss_factor=_loss_factor(IL_dB),
            branch_I_loss_factor=_loss_factor(IL_I_dB),
            branch_Q_loss_factor=_loss_factor(IL_Q_dB),
            parent_loss_factor=_loss_factor(IL_P_dB),
            er_model=er_model,
        )
        P_pd_t = np.abs(E_out) ** 2 * float(pd_tap)
        I_pd = float(Responsivity) * P_pd_t
        tone = _single_sided_tone(
            I_pd,
            fs=float(Fs),
            freq_hz=target_freq_hz,
            r_load=float(R_load),
            vpi_compatible_dbm=bool(vpi_compatible_dbm),
        )
        noise = _noise_result(
            I_pd=I_pd,
            RBW_Hz=rbw_hz,
            Temp_K=float(Temp_K),
            RIN_dB_Hz=float(RIN_dB_Hz),
            R_load=float(R_load),
            vpi_compatible_dbm=bool(vpi_compatible_dbm),
        )
        bin_noise_W = (
            float(noise.P_noise_total_W) * float(-np.log(rng.random()))
            if noise_mode_eff == "spectrum"
            else 0.0
        )

        current_peak_A[idx] = tone["current_peak_A"]
        signal_power_W[idx] = tone["power_W"]
        signal_power_dBm[idx] = tone["power_dBm"]
        noise_power_W[idx] = bin_noise_W
        noise_floor_dBm[idx] = float(_dbm(noise.P_noise_total_W))
        measured_power_W[idx] = signal_power_W[idx] + noise_power_W[idx]
        measured_power_dBm[idx] = float(_dbm(measured_power_W[idx]))
        pd_avg_dBm[idx] = float(_dbm(np.mean(P_pd_t)))
        bin_freq_Hz[idx] = tone["bin_freq_Hz"]

    freq_label = _format_freq_label(target_freq_hz)
    freq_tag = _format_freq_tag(target_freq_hz)

    csv_path = out_path / f"p_bias_{freq_tag}_beat_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "V_DCP_V",
                "tone_bin_Hz",
                "I_tone_peak_A",
                "P_tone_signal_W",
                "P_tone_signal_dBm",
                "P_noise_bin_W",
                "P_noise_floor_dBm",
                "P_tone_measured_W",
                "P_tone_measured_dBm",
                "P_pd_avg_dBm",
            ]
        )
        writer.writerows(
            zip(
                V_DCP_values,
                bin_freq_Hz,
                current_peak_A,
                signal_power_W,
                signal_power_dBm,
                noise_power_W,
                noise_floor_dBm,
                measured_power_W,
                measured_power_dBm,
                pd_avg_dBm,
            )
        )

    npz_path = out_path / f"p_bias_{freq_tag}_beat_sweep.npz"
    np.savez(
        npz_path,
        V_DCP_values=V_DCP_values,
        bin_freq_Hz=bin_freq_Hz,
        current_peak_A=current_peak_A,
        signal_power_W=signal_power_W,
        signal_power_dBm=signal_power_dBm,
        noise_power_W=noise_power_W,
        noise_floor_dBm=noise_floor_dBm,
        measured_power_W=measured_power_W,
        measured_power_dBm=measured_power_dBm,
        pd_avg_dBm=pd_avg_dBm,
        Fs=float(Fs),
        T_total=float(T_total),
        RBW_Hz=float(rbw_hz),
        target_freq_Hz=float(target_freq_hz),
        V_DCI=float(V_DCI),
        V_DCQ=float(V_DCQ),
        V_dither_I_amp=float(V_dither_I_amp),
        f_dither_I=float(f_dither_I),
        V_dither_P_amp=float(V_dither_P_amp),
        f_dither_P=float(f_dither_P),
        er_model=str(er_model),
        vpi_compatible_dbm=bool(vpi_compatible_dbm),
        noise_mode=noise_mode_eff,
        Temp_K=float(Temp_K),
        RIN_dB_Hz=float(RIN_dB_Hz),
        rng_seed=int(rng_seed),
    )

    plot_path = out_path / f"p_bias_{freq_tag}_beat_sweep.png"
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.plot(V_DCP_values, measured_power_dBm, linewidth=1.6, label="measured with noise")
    ax.plot(V_DCP_values, signal_power_dBm, linewidth=1.1, linestyle="--", label="deterministic signal")
    ax.set_xlabel("P bias V_DCP (V)")
    ax.set_ylabel(f"{freq_label} PD beat power (dBm)")
    ax.set_title(f"DPMZM P-bias sweep: {freq_label} pilot beat")
    ax.grid(True, alpha=0.28)
    ax.legend()
    fig.tight_layout()
    fig.savefig(plot_path, dpi=160)
    plt.close(fig)

    max_idx = int(np.argmax(measured_power_dBm))
    min_idx = int(np.argmin(measured_power_dBm))
    signal_max_idx = int(np.argmax(signal_power_dBm))
    signal_min_idx = int(np.argmin(signal_power_dBm))
    print("=== DPMZM P-bias pilot beat sweep ===")
    print(f"P bias range: {V_DCP_values[0]:.3f} to {V_DCP_values[-1]:.3f} V, step {float(V_DCP_step):.3f} V")
    print(f"I/Q DC: {float(V_DCI):.6g} V / {float(V_DCQ):.6g} V")
    print(f"I dither: {float(V_dither_I_amp):.6g} V peak @ {float(f_dither_I):.6g} Hz")
    print(f"P dither: {float(V_dither_P_amp):.6g} V peak @ {float(f_dither_P):.6g} Hz")
    print(f"Measured tone: target {target_freq_hz:.6g} Hz, FFT bin {bin_freq_Hz[0]:.6g} Hz, RBW {rbw_hz:.6g} Hz")
    print(f"Noise mode: {noise_mode_eff}, Temp={float(Temp_K):.3g} K, RIN={float(RIN_dB_Hz):.3g} dB/Hz")
    print(f"Measured max: V_DCP={V_DCP_values[max_idx]:.3f} V, P_tone={measured_power_dBm[max_idx]:.3f} dBm")
    print(f"Measured min: V_DCP={V_DCP_values[min_idx]:.3f} V, P_tone={measured_power_dBm[min_idx]:.3f} dBm")
    print(f"Signal max: V_DCP={V_DCP_values[signal_max_idx]:.3f} V, P_tone={signal_power_dBm[signal_max_idx]:.3f} dBm")
    print(f"Signal min: V_DCP={V_DCP_values[signal_min_idx]:.3f} V, P_tone={signal_power_dBm[signal_min_idx]:.3f} dBm")
    print(f"Saved CSV: {csv_path.resolve()}")
    print(f"Saved NPZ: {npz_path.resolve()}")
    print(f"Saved plot: {plot_path.resolve()}")

    return {
        "V_DCP_values": V_DCP_values,
        "beat_power_dBm": measured_power_dBm,
        "signal_power_dBm": signal_power_dBm,
        "noise_floor_dBm": noise_floor_dBm,
        "current_peak_A": current_peak_A,
        "pd_avg_dBm": pd_avg_dBm,
        "csv_path": str(csv_path.resolve()),
        "npz_path": str(npz_path.resolve()),
        "plot_path": str(plot_path.resolve()),
        "RBW_Hz": float(rbw_hz),
        "target_freq_Hz": float(target_freq_hz),
        "noise_mode": noise_mode_eff,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sweep DPMZM P bias and measure the 2.2 kHz PD pilot beat.")
    parser.add_argument("--out-dir", default="artifacts/dpmzm_pilot_beat_sweep")
    parser.add_argument("--v-dci", type=float, default=1.527)
    parser.add_argument("--v-dcq", type=float, default=1.527)
    parser.add_argument("--p-start", type=float, default=-10.0)
    parser.add_argument("--p-stop", type=float, default=10.0)
    parser.add_argument("--p-step", type=float, default=0.05)
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
    parser.add_argument("--fs", type=float, default=100e3)
    parser.add_argument("--t-total", type=float, default=1.0)
    parser.add_argument("--i-dither-amp", type=float, default=0.1)
    parser.add_argument("--i-dither-freq", type=float, default=1e3)
    parser.add_argument("--p-dither-amp", type=float, default=0.1)
    parser.add_argument("--p-dither-freq", type=float, default=1.2e3)
    parser.add_argument("--i-dither-phase", type=float, default=0.0)
    parser.add_argument("--p-dither-phase", type=float, default=0.0)
    parser.add_argument("--er-model", choices=("vpi", "thesis"), default="vpi")
    parser.add_argument("--noise-mode", choices=("spectrum", "none"), default="spectrum")
    parser.add_argument("--temp-k", type=float, default=290.0)
    parser.add_argument("--rin-db-hz", type=float, default=-145.0)
    parser.add_argument("--rng-seed", type=int, default=0)
    parser.add_argument("--no-vpi-compatible-dbm", action="store_true")
    args = parser.parse_args()

    run_pilot_beat_sweep(
        out_dir=args.out_dir,
        V_DCI=args.v_dci,
        V_DCQ=args.v_dcq,
        V_DCP_start=args.p_start,
        V_DCP_stop=args.p_stop,
        V_DCP_step=args.p_step,
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
        V_dither_I_amp=args.i_dither_amp,
        f_dither_I=args.i_dither_freq,
        V_dither_P_amp=args.p_dither_amp,
        f_dither_P=args.p_dither_freq,
        dither_phase_I=args.i_dither_phase,
        dither_phase_P=args.p_dither_phase,
        er_model=args.er_model,
        noise_mode=args.noise_mode,
        Temp_K=args.temp_k,
        RIN_dB_Hz=args.rin_db_hz,
        rng_seed=args.rng_seed,
        vpi_compatible_dbm=not bool(args.no_vpi_compatible_dbm),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
