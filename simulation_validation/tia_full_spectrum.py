"""Generate VPI-style TIA-domain full electrical spectra.

This script runs one DPMZM low-frequency pilot case, converts the simulated
PD current spectrum to the VPI TIA voltage readout convention, and writes CSV,
PNG, JSON, and Markdown outputs.

Default convention:

    I/Q source voltages -> effective voltage = 2 * source
    P source voltage    -> effective voltage = 1 * source
    VPI TIA             -> differential output Vdiff = Z_TIA * i_pd
    single-ended output -> Vsingle = Vdiff / 2
    TwoPortAnalyzerEl   -> RMS magnitude
    VPI expression      -> 10log10(x*x) + 30
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DPMZM_ROOT = PROJECT_ROOT
DEFAULT_OUT_DIR = PROJECT_ROOT / "simulation_validation" / "results" / "tia_full_spectrum"


def _db_1ohm_from_v_rms(v_rms: np.ndarray | float) -> np.ndarray:
    v = np.maximum(np.asarray(v_rms, dtype=float), 1e-150)
    return 10.0 * np.log10(v * v * 1000.0)


def _dbm_50ohm_from_v_rms(v_rms: np.ndarray | float) -> np.ndarray:
    v = np.maximum(np.asarray(v_rms, dtype=float), 1e-150)
    return 10.0 * np.log10((v * v / 50.0) * 1000.0)


def _format_float(value: float | None, digits: int = 6) -> str:
    if value is None:
        return "-"
    if not math.isfinite(float(value)):
        return "nan"
    return f"{float(value):.{digits}g}"


def _marker_frequencies(params: SpectrumParams) -> list[float]:
    tones = [frequency for frequency, amplitude in (
        (params.f_i_hz, params.i_dither_source_amp_vpeak),
        (params.f_q_hz, params.q_dither_source_amp_vpeak),
        (params.f_p_hz, params.p_dither_source_amp_vpeak),
    ) if amplitude != 0.0]
    markers = {0.0, *tones, *(2.0 * frequency for frequency in tones)}
    for index, first in enumerate(tones):
        for second in tones[index + 1:]:
            markers.update((abs(first - second), first + second))
    return sorted(markers)


@dataclass(frozen=True)
class SpectrumParams:
    case_name: str
    i_source_bias_v: float
    q_source_bias_v: float
    p_source_bias_v: float
    child_source_gain: float
    parent_source_gain: float
    i_dither_source_amp_vpeak: float
    q_dither_source_amp_vpeak: float
    p_dither_source_amp_vpeak: float
    f_i_hz: float
    f_q_hz: float
    f_p_hz: float
    fs_hz: float
    t_total_s: float
    vpi_v: float
    er_db: float
    il_db: float
    il_i_db: float
    il_q_db: float
    il_p_db: float
    pin_dbm: float
    responsivity_a_per_w: float
    pd_tap: float
    tia_ohm: float
    tia_input_equivalent_noise_rms_a: float
    tia_noise_bandwidth_hz: float
    er_model: str
    rin_db_hz: float
    temp_k: float
    rng_seed: int
    add_model_noise: bool


def run_case(params: SpectrumParams, *, out_dir: Path, dpmzm_root: Path) -> dict[str, Any]:
    if str(dpmzm_root) not in sys.path:
        sys.path.insert(0, str(dpmzm_root))

    from dpmzm.core.model import simulate_dpmzm

    out_dir.mkdir(parents=True, exist_ok=True)

    i_eff = params.child_source_gain * params.i_source_bias_v
    q_eff = params.child_source_gain * params.q_source_bias_v
    p_eff = params.parent_source_gain * params.p_source_bias_v
    i_dither_eff = params.child_source_gain * params.i_dither_source_amp_vpeak
    q_dither_eff = params.child_source_gain * params.q_dither_source_amp_vpeak
    p_dither_eff = params.parent_source_gain * params.p_dither_source_amp_vpeak

    sim = simulate_dpmzm(
        Fs=params.fs_hz,
        T_total=params.t_total_s,
        Vpi=params.vpi_v,
        ER_dB=params.er_db,
        ER_I_dB=params.er_db,
        ER_Q_dB=params.er_db,
        ER_P_dB=params.er_db,
        IL_dB=params.il_db,
        IL_I_dB=params.il_i_db,
        IL_Q_dB=params.il_q_db,
        IL_P_dB=params.il_p_db,
        Pin_dBm=params.pin_dbm,
        Responsivity=params.responsivity_a_per_w,
        pd_tap=params.pd_tap,
        R_load=1.0,
        V_DCI=i_eff,
        V_DCQ=q_eff,
        V_DCP=p_eff,
        V_dither_I_amp=i_dither_eff,
        V_dither_Q_amp=q_dither_eff,
        V_dither_P_amp=p_dither_eff,
        f_dither_I=params.f_i_hz,
        f_dither_Q=params.f_q_hz,
        f_dither_P=params.f_p_hz,
        V_RFI_amp=0.0,
        V_RFQ_amp=0.0,
        vpi_compatible_dbm=True,
        er_model=params.er_model,
        RIN_dB_Hz=params.rin_db_hz,
        Temp_K=params.temp_k,
        rng_seed=params.rng_seed,
    )

    current = np.asarray(sim.I_pd, dtype=float)
    n = int(current.size)
    spectrum = np.fft.rfft(current) / n
    freq = np.fft.rfftfreq(n, d=1.0 / params.fs_hz)
    current_peak = np.abs(spectrum)
    if current_peak.size > 2:
        current_peak[1:-1] *= 2.0

    ac = np.ones_like(current_peak, dtype=bool)
    ac[0] = False
    current_rms = current_peak.copy()
    current_rms[ac] = current_rms[ac] / math.sqrt(2.0)

    vdiff_signal_rms = params.tia_ohm * current_rms
    vsingle_signal_rms = 0.5 * vdiff_signal_rms

    diff_signal_db = _db_1ohm_from_v_rms(vdiff_signal_rms)
    single_signal_db = _db_1ohm_from_v_rms(vsingle_signal_rms)
    diff_signal_dbm50 = _dbm_50ohm_from_v_rms(vdiff_signal_rms)
    single_signal_dbm50 = _dbm_50ohm_from_v_rms(vsingle_signal_rms)

    rng = np.random.default_rng(params.rng_seed)
    model_input_noise_rms = math.sqrt(max(float(sim.noise.P_noise_total_W), 0.0))
    rbw_hz = float(sim.RBW_Hz)
    if params.tia_input_equivalent_noise_rms_a > 0.0 and params.tia_noise_bandwidth_hz > 0.0:
        tia_input_noise_rms = params.tia_input_equivalent_noise_rms_a * math.sqrt(
            rbw_hz / params.tia_noise_bandwidth_hz
        )
    else:
        tia_input_noise_rms = 0.0
    input_noise_rms = math.sqrt(model_input_noise_rms**2 + tia_input_noise_rms**2)
    noise_scale = rng.exponential(scale=1.0, size=current_rms.shape) if params.add_model_noise else 0.0
    noise_current_rms = input_noise_rms * np.sqrt(noise_scale)
    diff_noise_rms = params.tia_ohm * noise_current_rms
    single_noise_rms = 0.5 * diff_noise_rms
    vdiff_measured_rms = np.sqrt(vdiff_signal_rms**2 + diff_noise_rms**2)
    vsingle_measured_rms = np.sqrt(vsingle_signal_rms**2 + single_noise_rms**2)

    diff_measured_db = _db_1ohm_from_v_rms(vdiff_measured_rms)
    single_measured_db = _db_1ohm_from_v_rms(vsingle_measured_rms)
    diff_measured_dbm50 = _dbm_50ohm_from_v_rms(vdiff_measured_rms)
    single_measured_dbm50 = _dbm_50ohm_from_v_rms(vsingle_measured_rms)

    csv_path = out_dir / f"{params.case_name}_tia_full_spectrum.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "freq_Hz",
                "I_pd_peak_A",
                "I_pd_rms_A",
                "TIA_diff_signal_V_rms",
                "TIA_single_signal_V_rms",
                "TIA_diff_signal_1ohm_dB",
                "TIA_single_signal_1ohm_dB",
                "TIA_diff_signal_dBm_50ohm",
                "TIA_single_signal_dBm_50ohm",
                "TIA_diff_measured_1ohm_dB",
                "TIA_single_measured_1ohm_dB",
                "TIA_diff_measured_dBm_50ohm",
                "TIA_single_measured_dBm_50ohm",
            ]
        )
        writer.writerows(
            zip(
                freq,
                current_peak,
                current_rms,
                vdiff_signal_rms,
                vsingle_signal_rms,
                diff_signal_db,
                single_signal_db,
                diff_signal_dbm50,
                single_signal_dbm50,
                diff_measured_db,
                single_measured_db,
                diff_measured_dbm50,
                single_measured_dbm50,
            )
        )

    markers_hz = _marker_frequencies(params)
    markers = []
    for target in markers_hz:
        if target > freq[-1]:
            continue
        index = int(np.argmin(np.abs(freq - target)))
        markers.append({
            "target_Hz": target,
            "freq_Hz": float(freq[index]),
            "value_dB": float(single_signal_db[index]),
            "TIA_diff_signal_1ohm_dB": float(diff_signal_db[index]),
            "TIA_single_measured_1ohm_dB": float(single_measured_db[index]),
            "TIA_diff_measured_1ohm_dB": float(diff_measured_db[index]),
        })

    png_single = out_dir / f"{params.case_name}_tia_single_rms_1ohm.png"
    png_diff = out_dir / f"{params.case_name}_tia_diff_rms_1ohm.png"
    _plot_spectrum(
        path=png_single,
        freq=freq,
        signal_db=single_signal_db,
        measured_db=single_measured_db,
        markers=markers_hz,
        title=f"{params.case_name}: TIA single-ended RMS, 1 ohm",
        ylabel="10log10(Vsingle_rms^2)+30 (dB)",
    )
    _plot_spectrum(
        path=png_diff,
        freq=freq,
        signal_db=diff_signal_db,
        measured_db=diff_measured_db,
        markers=markers_hz,
        title=f"{params.case_name}: TIA differential RMS, 1 ohm",
        ylabel="10log10(Vdiff_rms^2)+30 (dB)",
    )

    summary = {
        "case_name": params.case_name,
        "params": asdict(params),
        "effective_voltages": {
            "V_DCI_effective_V": i_eff,
            "V_DCQ_effective_V": q_eff,
            "V_DCP_effective_V": p_eff,
            "V_dither_I_effective_Vpeak": i_dither_eff,
            "V_dither_Q_effective_Vpeak": q_dither_eff,
            "V_dither_P_effective_Vpeak": p_dither_eff,
        },
        "pd_avg_dBm": float(sim.P_pd_avg_dBm),
        "p_static_phase_deg": 180.0 * p_eff / params.vpi_v,
        "model_input_noise_rms_A_per_bin": model_input_noise_rms,
        "tia_input_noise_rms_A_per_bin": tia_input_noise_rms,
        "total_input_noise_rms_A_per_bin": input_noise_rms,
        "single_noise_mean_1ohm_dB": float(_db_1ohm_from_v_rms(0.5 * params.tia_ohm * input_noise_rms))
        if params.add_model_noise else None,
        "noise_readout_method": "Independent exponential bin powers added to signal power; no coherent cross term",
        "rbw_Hz": float(sim.RBW_Hz),
        "markers": markers,
        "csv_path": str(csv_path),
        "single_png": str(png_single),
        "diff_png": str(png_diff),
    }
    json_path = out_dir / f"{params.case_name}_tia_full_spectrum_summary.json"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path = out_dir / f"{params.case_name}_tia_full_spectrum_summary.md"
    md_path.write_text(_render_markdown(summary), encoding="utf-8")

    return summary


def _plot_spectrum(
    *,
    path: Path,
    freq: np.ndarray,
    signal_db: np.ndarray,
    measured_db: np.ndarray,
    markers: list[float],
    title: str,
    ylabel: str,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(freq, signal_db, linewidth=1.0, label="deterministic signal")
    if not np.allclose(signal_db, measured_db):
        ax.plot(freq, measured_db, linewidth=0.7, alpha=0.65, label="signal + noise (power sum)")
    for tone in sorted(set(float(x) for x in markers)):
        if tone <= freq[-1]:
            ax.axvline(tone, color="tab:red" if tone > 0 else "tab:gray", alpha=0.32, linewidth=0.8, linestyle="--")
    ax.set_xlim(0, min(5000.0, float(freq[-1])))
    finite = signal_db[np.isfinite(signal_db)]
    if finite.size:
        y_max = float(np.max(finite)) + 10.0
        y_min = y_max - 220.0
        ax.set_ylim(y_min, y_max)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _render_markdown(summary: dict[str, Any]) -> str:
    params = summary["params"]
    eff = summary["effective_voltages"]
    lines = [
        f"# TIA Full Spectrum: {summary['case_name']}",
        "",
        "## VPI Readout Convention",
        "",
        "- TIA: `Vdiff = Z_TIA * Ipd`, `Vsingle = Vdiff / 2`",
        "- Analyzer: `TwoPortAnalyzerEl` RMS magnitude",
        "- Expression: `10log10(x*x)+30`, equivalent to RMS voltage in `1 ohm`",
        "- Default comparison column: `TIA_single_signal_1ohm_dB` unless VPI analyzer is explicitly differential",
        "",
        "## Parameters",
        "",
        f"- `Z_TIA = {_format_float(params['tia_ohm'])} ohm`",
        f"- `TIA InputEquivalentNoise = {_format_float(params['tia_input_equivalent_noise_rms_a'])} A rms over {_format_float(params['tia_noise_bandwidth_hz'])} Hz`",
        f"- Noise per FFT bin: model `{_format_float(summary['model_input_noise_rms_A_per_bin'])} A rms`, TIA `{_format_float(summary['tia_input_noise_rms_A_per_bin'])} A rms`, total `{_format_float(summary['total_input_noise_rms_A_per_bin'])} A rms`",
        f"- Source biases: `I={_format_float(params['i_source_bias_v'])} V`, `Q={_format_float(params['q_source_bias_v'])} V`, `P={_format_float(params['p_source_bias_v'])} V`",
        f"- Effective biases: `I={_format_float(eff['V_DCI_effective_V'])} V`, `Q={_format_float(eff['V_DCQ_effective_V'])} V`, `P={_format_float(eff['V_DCP_effective_V'])} V`",
        f"- P total static phase: `{_format_float(summary['p_static_phase_deg'])} deg`",
        f"- Source pilot amplitudes: `I={_format_float(params['i_dither_source_amp_vpeak'])} Vpeak`, `Q={_format_float(params['q_dither_source_amp_vpeak'])} Vpeak`, `P={_format_float(params['p_dither_source_amp_vpeak'])} Vpeak`",
        f"- Effective pilot amplitudes: `I={_format_float(eff['V_dither_I_effective_Vpeak'])} Vpeak`, `Q={_format_float(eff['V_dither_Q_effective_Vpeak'])} Vpeak`, `P={_format_float(eff['V_dither_P_effective_Vpeak'])} Vpeak`",
        f"- Frequencies: `f_I={_format_float(params['f_i_hz'])} Hz`, `f_Q={_format_float(params['f_q_hz'])} Hz`, `f_P={_format_float(params['f_p_hz'])} Hz`",
        f"- `ER={_format_float(params['er_db'])} dB`, `IL_I={_format_float(params['il_i_db'])} dB`, `IL_Q={_format_float(params['il_q_db'])} dB`, `IL_P={_format_float(params['il_p_db'])} dB`",
        f"- `Pin={_format_float(params['pin_dbm'])} dBm`, `Responsivity={_format_float(params['responsivity_a_per_w'])} A/W`, `pd_tap={_format_float(params['pd_tap'])}`",
        f"- `Fs={_format_float(params['fs_hz'])} Hz`, `T_total={_format_float(params['t_total_s'])} s`, `RBW={_format_float(summary['rbw_Hz'])} Hz`",
        f"- `add_model_noise={params['add_model_noise']}`",
        f"- `RIN={_format_float(params['rin_db_hz'])} dB/Hz`, `Temp={_format_float(params['temp_k'])} K`",
        f"- Mean noise power per bin, single-ended 1 ohm: `{_format_float(summary['single_noise_mean_1ohm_dB'])} dB`",
        f"- Noise method: {summary['noise_readout_method']}",
        "",
        "## Markers",
        "",
        "| Target Hz | Bin Hz | Single signal dB | Diff signal dB | Single measured dB | Diff measured dB |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for marker in summary["markers"]:
        lines.append(
            "| {target} | {freq} | {single} | {diff} | {single_m} | {diff_m} |".format(
                target=_format_float(marker["target_Hz"], 3),
                freq=_format_float(marker["freq_Hz"], 3),
                single=_format_float(marker["value_dB"], 4),
                diff=_format_float(marker["TIA_diff_signal_1ohm_dB"], 4),
                single_m=_format_float(marker["TIA_single_measured_1ohm_dB"], 4),
                diff_m=_format_float(marker["TIA_diff_measured_1ohm_dB"], 4),
            )
        )
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- CSV: `{summary['csv_path']}`",
            f"- Single-ended plot: `{summary['single_png']}`",
            f"- Differential plot: `{summary['diff_png']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a VPI-style TIA full electrical spectrum.")
    parser.add_argument("--dpmzm-root", type=Path, default=DEFAULT_DPMZM_ROOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--case-name", default="tia_full_spectrum")
    parser.add_argument("--i-source-bias", type=float, default=-7.5)
    parser.add_argument("--q-source-bias", type=float, default=-1.55)
    parser.add_argument("--p-source-bias", type=float, default=0.1)
    parser.add_argument("--child-source-gain", type=float, default=2.0)
    parser.add_argument("--parent-source-gain", type=float, default=1.0)
    parser.add_argument("--i-dither-source-amp", type=float, default=0.025)
    parser.add_argument("--q-dither-source-amp", type=float, default=0.0)
    parser.add_argument("--p-dither-source-amp", type=float, default=0.025)
    parser.add_argument("--f-i", type=float, default=1000.0)
    parser.add_argument("--f-q", type=float, default=1200.0)
    parser.add_argument("--f-p", type=float, default=1300.0)
    parser.add_argument("--fs", type=float, default=1_000_000.0)
    parser.add_argument("--t-total", type=float, default=0.1)
    parser.add_argument("--vpi", type=float, default=5.0)
    parser.add_argument("--er-db", type=float, default=30.0)
    parser.add_argument("--il-db", type=float, default=0.0)
    parser.add_argument("--il-i-db", type=float, default=6.0)
    parser.add_argument("--il-q-db", type=float, default=6.0)
    parser.add_argument("--il-p-db", type=float, default=0.0)
    parser.add_argument("--pin-dbm", type=float, default=10.0)
    parser.add_argument("--responsivity", type=float, default=0.8)
    parser.add_argument("--pd-tap", type=float, default=1.0)
    parser.add_argument("--tia-ohm", type=float, default=10_000.0)
    parser.add_argument(
        "--tia-input-equivalent-noise-rms",
        type=float,
        default=0.0,
        help="VPI TIA InputEquivalentNoise in A rms over --tia-noise-bandwidth.",
    )
    parser.add_argument(
        "--tia-noise-bandwidth",
        type=float,
        default=1.0,
        help="NoiseBandwidth used to interpret --tia-input-equivalent-noise-rms.",
    )
    parser.add_argument("--er-model", choices=("vpi", "thesis"), default="vpi")
    parser.add_argument("--rin-db-hz", type=float, default=-145.0)
    parser.add_argument("--temp-k", type=float, default=290.0)
    parser.add_argument("--rng-seed", type=int, default=0)
    parser.add_argument("--add-model-noise", action="store_true")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    params = SpectrumParams(
        case_name=args.case_name,
        i_source_bias_v=args.i_source_bias,
        q_source_bias_v=args.q_source_bias,
        p_source_bias_v=args.p_source_bias,
        child_source_gain=args.child_source_gain,
        parent_source_gain=args.parent_source_gain,
        i_dither_source_amp_vpeak=args.i_dither_source_amp,
        q_dither_source_amp_vpeak=args.q_dither_source_amp,
        p_dither_source_amp_vpeak=args.p_dither_source_amp,
        f_i_hz=args.f_i,
        f_q_hz=args.f_q,
        f_p_hz=args.f_p,
        fs_hz=args.fs,
        t_total_s=args.t_total,
        vpi_v=args.vpi,
        er_db=args.er_db,
        il_db=args.il_db,
        il_i_db=args.il_i_db,
        il_q_db=args.il_q_db,
        il_p_db=args.il_p_db,
        pin_dbm=args.pin_dbm,
        responsivity_a_per_w=args.responsivity,
        pd_tap=args.pd_tap,
        tia_ohm=args.tia_ohm,
        tia_input_equivalent_noise_rms_a=args.tia_input_equivalent_noise_rms,
        tia_noise_bandwidth_hz=args.tia_noise_bandwidth,
        er_model=args.er_model,
        rin_db_hz=args.rin_db_hz,
        temp_k=args.temp_k,
        rng_seed=args.rng_seed,
        add_model_noise=args.add_model_noise,
    )
    summary = run_case(params, out_dir=args.out_dir, dpmzm_root=args.dpmzm_root)
    print(f"Saved CSV: {Path(summary['csv_path']).resolve()}")
    print(f"Saved single-ended plot: {Path(summary['single_png']).resolve()}")
    print(f"Saved differential plot: {Path(summary['diff_png']).resolve()}")
    print("Markers:")
    for marker in summary["markers"]:
        print(
            "  {target:8.3f} Hz -> single {single: .3f} dB, diff {diff: .3f} dB".format(
                target=marker["target_Hz"],
                single=marker["value_dB"],
                diff=marker["TIA_diff_signal_1ohm_dB"],
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
