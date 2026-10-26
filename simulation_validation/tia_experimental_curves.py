"""Generate TIA-domain noisy observation curves for Step 1-4 sweeps.

The raw sweep PNG/CSV files are PD-current spectrum results. This script
post-processes the selected low-frequency sweep CSV files into a more
experiment-like TIA output view:

    PD current tone -> Z_TIA(f) -> output voltage + TIA noise

It writes one curve CSV/PNG per Step and a short Markdown summary.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import HARDWARE_CONFIG, HARDWARE_TIA_ARGS, parse_config_args, save_config_snapshot
from simulation_validation.tia_visibility_analyzer import (
    TIAParams,
    _bandwidth_flag,
    _default_enbw,
    _estimate_tia,
    _first_numeric,
    _format_eng,
    _pd_avg_w,
    _to_float,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = PROJECT_ROOT / "simulation_validation" / "results" / "findpoint_summary.json"
DEFAULT_OUT_DIR = PROJECT_ROOT / "simulation_validation" / "results" / "tia_curves"
DEFAULT_REPORT = PROJECT_ROOT / "simulation_validation" / "results" / "tia_curves_report.md"
REFERENCE_LOAD_OHM = 50.0

CURRENT_PEAK_COLUMNS = (
    "I_tone_peak_A",
    "I_2p2k_peak_A",
    "I_beat_peak_A",
)

TONE_FREQ_COLUMNS = (
    "tone_bin_Hz",
    "target_freq_Hz",
    "target_freq_hz",
)


@dataclass
class CurveProduct:
    step_key: str
    label: str
    csv_path: Path
    png_path: Path | None
    row_count: int
    selected_bias_v: float | None
    selected_snr_db: float | None
    selected_signal_v_peak: float | None
    selected_noise_v_rms: float | None
    selected_signal_dbm_1ohm: float | None
    selected_signal_dbm_50ohm: float | None
    selected_measured_dbm_1ohm: float | None
    selected_measured_dbm_50ohm: float | None
    max_signal_v_peak: float
    min_snr_db: float
    max_snr_db: float
    bandwidth_flags: list[str]
    saturation_flags: list[str]


def _dbv(value_v: float) -> float:
    return 20.0 * math.log10(max(abs(float(value_v)), 1e-300))


def _dbm_50ohm_from_v_rms(value_v_rms: float) -> float:
    """Return 50-ohm equivalent dBm for an RMS voltage.

    This is an equivalent readout metric for comparison with instruments that
    label FFT bins as "Equivalent power, 50 Ohm"; it is not TIA delivered load
    power unless the output is actually terminated by 50 ohm.
    """

    v = max(abs(float(value_v_rms)), 1e-300)
    return 10.0 * math.log10((v * v / REFERENCE_LOAD_OHM) * 1000.0)


def _dbm_1ohm_from_v_rms(value_v_rms: float) -> float:
    """Return the VPI-style 1-ohm equivalent reading for an RMS voltage.

    A VPI post-processing chain of ``x*x`` followed by ``10log(x)+30`` is
    equivalent to this expression when ``x`` is an RMS voltage amplitude and
    no explicit load impedance is applied.
    """

    v = max(abs(float(value_v_rms)), 1e-300)
    return 10.0 * math.log10((v * v / 1.0) * 1000.0)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_curve_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _plot_curve(
    *,
    path: Path,
    label: str,
    x_values: list[float],
    signal_dbv: list[float],
    measured_dbv: list[float],
    noise_dbv: list[float],
    snr_db: list[float],
    selected_bias_v: float | None,
    x_label: str,
) -> Path | None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None

    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(8.8, 6.0),
        dpi=160,
        sharex=True,
        gridspec_kw={"height_ratios": [2.0, 1.0]},
    )

    ax1.plot(x_values, signal_dbv, linewidth=1.8, label="TIA signal Vrms")
    ax1.plot(x_values, measured_dbv, linewidth=1.0, alpha=0.72, label="Noisy measured Vrms")
    ax1.plot(x_values, noise_dbv, linewidth=1.2, linestyle="--", label="TIA noise/bin")
    ax1.set_ylabel("Voltage (dBV rms)")
    ax1.set_title(label)
    ax1.grid(True, alpha=0.25)
    ax1.legend(loc="best", fontsize=8)

    ax2.plot(x_values, snr_db, color="#2ca02c", linewidth=1.4)
    ax2.axhline(0.0, color="#666666", linestyle="--", linewidth=0.8)
    ax2.set_xlabel(x_label)
    ax2.set_ylabel("SNR (dB)")
    ax2.grid(True, alpha=0.25)

    if selected_bias_v is not None:
        ax1.axvline(selected_bias_v, color="#d62728", linestyle=":", linewidth=1.2)
        ax2.axvline(selected_bias_v, color="#d62728", linestyle=":", linewidth=1.2)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def _round(value: Any, digits: int = 9) -> Any:
    if isinstance(value, float) and math.isfinite(value):
        return round(value, digits)
    return value


def _process_step(
    *,
    step_key: str,
    step: dict[str, Any],
    out_dir: Path,
    params: TIAParams,
    rng: random.Random,
) -> CurveProduct | None:
    source_csv = Path(str(step["csv_path"]))
    source_rows = _read_rows(source_csv)
    x_column = str(step["x_column"])
    effective_column = step.get("effective_column")
    label = str(step.get("label", step_key))
    selected_index = int(step["selected_index"])

    curve_rows: list[dict[str, Any]] = []
    x_values: list[float] = []
    signal_dbv: list[float] = []
    measured_dbv: list[float] = []
    noise_dbv: list[float] = []
    snr_db: list[float] = []

    for idx, row in enumerate(source_rows):
        bias_v = _to_float(row.get(x_column))
        if bias_v is None:
            continue
        effective_v = _to_float(row.get(str(effective_column))) if effective_column else None
        current_col, current_peak = _first_numeric(row, CURRENT_PEAK_COLUMNS)
        freq_col, freq_hz = _first_numeric(row, TONE_FREQ_COLUMNS)
        if current_peak is None or freq_hz is None:
            continue

        enbw_hz = _default_enbw(freq_hz, params)
        estimate = _estimate_tia(
            current_peak_a=current_peak,
            freq_hz=freq_hz,
            pd_avg_w=_pd_avg_w(row),
            enbw_hz=enbw_hz,
            params=params,
        )

        # The VPI TIA block is differential:
        #   out+ =  Z_TIA * i_pd / 2
        #   out- = -Z_TIA * i_pd / 2
        # Therefore out+ - out- equals Z_TIA * i_pd.  The legacy
        # TIA_signal_* columns below keep this differential voltage.
        v_signal_peak_diff = float(estimate["v_tone_peak_v"])
        v_signal_rms = float(estimate["v_tone_rms_v"])
        v_noise_rms = float(estimate["v_noise_rms_bin_v"])
        noise_power_sample = (v_noise_rms**2) * rng.expovariate(1.0)
        v_measured_rms = math.sqrt(v_signal_rms**2 + noise_power_sample)

        v_signal_peak_single = v_signal_peak_diff / 2.0
        v_signal_rms_single = v_signal_rms / 2.0
        v_noise_rms_single = v_noise_rms / 2.0
        v_measured_rms_single = v_measured_rms / 2.0

        row_out = {
            "row_index": idx,
            "step_key": step_key,
            "bias_source_V": bias_v,
            "bias_effective_V": effective_v,
            "tone_freq_Hz": freq_hz,
            "current_peak_column": current_col,
            "current_peak_A": current_peak,
            "TIA_Z_ohm": estimate["z_tia_ohm"],
            "TIA_gain_vs_50ohm_dB": estimate["gain_vs_50ohm_db"],
            "TIA_attenuation_vs_low_freq_dB": estimate["attenuation_vs_low_freq_db"],
            "TIA_signal_V_peak": v_signal_peak_diff,
            "TIA_signal_V_rms": v_signal_rms,
            "TIA_noise_V_rms_bin": v_noise_rms,
            "TIA_measured_V_rms": v_measured_rms,
            "TIA_diff_signal_V_peak": v_signal_peak_diff,
            "TIA_diff_signal_V_rms": v_signal_rms,
            "TIA_diff_noise_V_rms_bin": v_noise_rms,
            "TIA_diff_measured_V_rms": v_measured_rms,
            "TIA_single_signal_V_peak": v_signal_peak_single,
            "TIA_single_signal_V_rms": v_signal_rms_single,
            "TIA_single_noise_V_rms_bin": v_noise_rms_single,
            "TIA_single_measured_V_rms": v_measured_rms_single,
            "TIA_signal_dBV_rms": _dbv(v_signal_rms),
            "TIA_noise_dBV_rms": _dbv(v_noise_rms),
            "TIA_measured_dBV_rms": _dbv(v_measured_rms),
            "TIA_diff_signal_dBV_rms": _dbv(v_signal_rms),
            "TIA_diff_noise_dBV_rms": _dbv(v_noise_rms),
            "TIA_diff_measured_dBV_rms": _dbv(v_measured_rms),
            "TIA_single_signal_dBV_rms": _dbv(v_signal_rms_single),
            "TIA_single_noise_dBV_rms": _dbv(v_noise_rms_single),
            "TIA_single_measured_dBV_rms": _dbv(v_measured_rms_single),
            "TIA_signal_dBm_1ohm": _dbm_1ohm_from_v_rms(v_signal_rms),
            "TIA_signal_dBm_50ohm": _dbm_50ohm_from_v_rms(v_signal_rms),
            "TIA_measured_dBm_1ohm": _dbm_1ohm_from_v_rms(v_measured_rms),
            "TIA_measured_dBm_50ohm": _dbm_50ohm_from_v_rms(v_measured_rms),
            "TIA_diff_signal_dBm_1ohm": _dbm_1ohm_from_v_rms(v_signal_rms),
            "TIA_diff_signal_dBm_50ohm": _dbm_50ohm_from_v_rms(v_signal_rms),
            "TIA_diff_measured_dBm_1ohm": _dbm_1ohm_from_v_rms(v_measured_rms),
            "TIA_diff_measured_dBm_50ohm": _dbm_50ohm_from_v_rms(v_measured_rms),
            "TIA_single_signal_dBm_1ohm": _dbm_1ohm_from_v_rms(v_signal_rms_single),
            "TIA_single_signal_dBm_50ohm": _dbm_50ohm_from_v_rms(v_signal_rms_single),
            "TIA_single_measured_dBm_1ohm": _dbm_1ohm_from_v_rms(v_measured_rms_single),
            "TIA_single_measured_dBm_50ohm": _dbm_50ohm_from_v_rms(v_measured_rms_single),
            "TIA_vpi_diff_rms_xx_plus30_dB": _dbm_1ohm_from_v_rms(v_signal_rms),
            "TIA_vpi_single_rms_xx_plus30_dB": _dbm_1ohm_from_v_rms(v_signal_rms_single),
            "TIA_SNR_dB": estimate["snr_tia_db"],
            "TIA_bandwidth_flag": estimate["bandwidth_flag"],
            "TIA_saturation_flag": estimate["saturation_flag"],
            "ENBW_Hz": enbw_hz,
        }
        curve_rows.append({k: _round(v) for k, v in row_out.items()})

        x_values.append(bias_v)
        signal_dbv.append(float(row_out["TIA_signal_dBV_rms"]))
        measured_dbv.append(float(row_out["TIA_measured_dBV_rms"]))
        noise_dbv.append(float(row_out["TIA_noise_dBV_rms"]))
        snr_db.append(float(row_out["TIA_SNR_dB"]))

    if not curve_rows:
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    curve_csv = out_dir / f"{step_key}_tia_curve.csv"
    curve_png = out_dir / f"{step_key}_tia_curve.png"
    _write_curve_csv(curve_csv, curve_rows)

    selected_bias_v = _to_float(source_rows[selected_index].get(x_column)) if selected_index < len(source_rows) else None
    png_result = _plot_curve(
        path=curve_png,
        label=f"{step_key} TIA observation",
        x_values=x_values,
        signal_dbv=signal_dbv,
        measured_dbv=measured_dbv,
        noise_dbv=noise_dbv,
        snr_db=snr_db,
        selected_bias_v=selected_bias_v,
        x_label=x_column,
    )

    selected_curve = curve_rows[selected_index] if selected_index < len(curve_rows) else {}
    return CurveProduct(
        step_key=step_key,
        label=label,
        csv_path=curve_csv,
        png_path=png_result,
        row_count=len(curve_rows),
        selected_bias_v=selected_bias_v,
        selected_snr_db=_to_float(selected_curve.get("TIA_SNR_dB")),
        selected_signal_v_peak=_to_float(selected_curve.get("TIA_signal_V_peak")),
        selected_noise_v_rms=_to_float(selected_curve.get("TIA_noise_V_rms_bin")),
        selected_signal_dbm_1ohm=_to_float(selected_curve.get("TIA_signal_dBm_1ohm")),
        selected_signal_dbm_50ohm=_to_float(selected_curve.get("TIA_signal_dBm_50ohm")),
        selected_measured_dbm_1ohm=_to_float(selected_curve.get("TIA_measured_dBm_1ohm")),
        selected_measured_dbm_50ohm=_to_float(selected_curve.get("TIA_measured_dBm_50ohm")),
        max_signal_v_peak=max(float(r["TIA_signal_V_peak"]) for r in curve_rows),
        min_snr_db=min(float(r["TIA_SNR_dB"]) for r in curve_rows),
        max_snr_db=max(float(r["TIA_SNR_dB"]) for r in curve_rows),
        bandwidth_flags=sorted({str(r["TIA_bandwidth_flag"]) for r in curve_rows}),
        saturation_flags=sorted({str(r["TIA_saturation_flag"]) for r in curve_rows}),
    )


def _write_report(path: Path, products: list[CurveProduct], params: TIAParams) -> None:
    lines = [
        "# TIA 实验观测口径曲线报告",
        "",
        f"生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "",
        "## 1. 参数",
        "",
        f"- `R_f = {_format_eng(params.rf_ohm, 'ohm')}`",
        f"- `C_f = {_format_eng(params.cf_f, 'F')}`",
        f"- `f_c = {_format_eng(params.fc_hz, 'Hz')}`",
        f"- 默认低频 ENBW：`{_format_eng(params.low_freq_enbw_hz, 'Hz')}`",
        "",
        "## 2. 曲线汇总",
        "",
        "| Step | 点数 | 选中偏置 | 选中 V_peak | 选中信号 dBm_50ohm | 选中观测 dBm_50ohm | 选中噪声/bin | 选中 SNR | 最大 V_peak | 最小 SNR | 标记 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for product in products:
        lines.append(
            "| {label} | {rows} | {bias} | {vp} | {sig_dbm} | {meas_dbm} | {vn} | {snr} | {max_vp} | {min_snr:.2f} dB | {flags} |".format(
                label=product.label,
                rows=product.row_count,
                bias="-" if product.selected_bias_v is None else f"{product.selected_bias_v:g} V",
                vp=_format_eng(product.selected_signal_v_peak, "V"),
                sig_dbm=(
                    "-"
                    if product.selected_signal_dbm_50ohm is None
                    else f"{product.selected_signal_dbm_50ohm:.2f} dBm"
                ),
                meas_dbm=(
                    "-"
                    if product.selected_measured_dbm_50ohm is None
                    else f"{product.selected_measured_dbm_50ohm:.2f} dBm"
                ),
                vn=_format_eng(product.selected_noise_v_rms, "V"),
                snr="-" if product.selected_snr_db is None else f"{product.selected_snr_db:.2f} dB",
                max_vp=_format_eng(product.max_signal_v_peak, "V"),
                min_snr=product.min_snr_db,
                flags=", ".join(product.bandwidth_flags + product.saturation_flags),
            )
        )

    lines.extend(["", "## 3. 输出文件", ""])
    for product in products:
        lines.append(f"- {product.label}")
        lines.append(f"  - CSV：`{product.csv_path}`")
        if product.png_path is not None:
            lines.append(f"  - PNG：`{product.png_path}`")

    lines.extend(
        [
            "",
            "## 4. 说明",
            "",
            "- `TIA signal Vrms` 是由原始 PD 电流导频峰值乘以 `Z_TIA(f)` 得到的确定性信号。",
            "- `Noisy measured Vrms` 是在信号功率上加入一个随机噪声 bin 后的模拟观测曲线。",
            "- `TIA noise/bin` 是当前 ENBW 下的 TIA 输出噪声 RMS。",
            "- `TIA_signal_dBV_rms` 和 `TIA_measured_dBV_rms` 使用 dBV，是因为 TIA 输出端首先是电压观测量，采集卡/示波器/ADC 看到的是 `V_rms`，而不是已经定义好负载的真实功率。",
            "- `TIA_signal_dBm_50ohm` 和 `TIA_measured_dBm_50ohm` 是为了和历史实验图中的 `Equivalent power (dBm, 50 Ohm)` 对齐而新增的等效功率口径，换算公式为 `dBm_50ohm = dBV_rms + 30 - 10log10(50)`。",
            "- 这两个 dBm_50ohm 字段只表示 50 ohm 等效读数；除非 TIA 输出真实接入 50 ohm 终端，否则它不等同于 TIA 实际向负载交付的功率。",
            "- 当前噪声为一阶近似，尚未包含真实 ADC 量化噪声、后级电压噪声、PCB 寄生和实测工频干扰。",
        ]
    )

    lines.extend(
        [
            "",
            "## VPI readout alignment",
            "",
            "The VPI TIA block is differential: `out+ = Z_TIA*i/2`, `out- = -Z_TIA*i/2`, so `Vdiff = out+ - out- = Z_TIA*i`.",
            "`VPI diff 1ohm` matches `10log10(Vdiff_rms^2)+30` if the VPI analyzer `Mag(f)` is RMS differential voltage.",
            "`VPI single 1ohm` is 6.0206 dB lower and matches a single-ended `out+` or `out-` RMS voltage.",
            "`diff dBm_50ohm = VPI diff 1ohm - 10log10(50)`.",
            "",
            "| Step | selected bias | Vdiff_peak | VPI diff 1ohm | diff dBm_50ohm | VPI single 1ohm |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for product in products:
        single_1ohm = (
            None
            if product.selected_signal_dbm_1ohm is None
            else product.selected_signal_dbm_1ohm - 6.020599913
        )
        lines.append(
            "| {label} | {bias} | {vp} | {diff_1ohm} | {diff_50ohm} | {single_1ohm} |".format(
                label=product.label,
                bias="-" if product.selected_bias_v is None else f"{product.selected_bias_v:g} V",
                vp=_format_eng(product.selected_signal_v_peak, "V"),
                diff_1ohm=(
                    "-"
                    if product.selected_signal_dbm_1ohm is None
                    else f"{product.selected_signal_dbm_1ohm:.2f} dB"
                ),
                diff_50ohm=(
                    "-"
                    if product.selected_signal_dbm_50ohm is None
                    else f"{product.selected_signal_dbm_50ohm:.2f} dBm"
                ),
                single_1ohm="-" if single_1ohm is None else f"{single_1ohm:.2f} dB",
            )
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    *,
    summary_path: Path,
    out_dir: Path,
    report_path: Path,
    params: TIAParams,
    rng_seed: int,
) -> list[CurveProduct]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    steps = summary.get("steps", {})
    rng = random.Random(int(rng_seed))

    products: list[CurveProduct] = []
    for step_key, step in steps.items():
        if not isinstance(step, dict) or step.get("status") != "FOUND":
            continue
        product = _process_step(
            step_key=step_key,
            step=step,
            out_dir=out_dir,
            params=params,
            rng=rng,
        )
        if product is not None:
            products.append(product)

    _write_report(report_path, products, params)
    return products


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate TIA-domain noisy observation curves.")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--rng-seed", type=int)
    parser.add_argument("--rf-ohm", type=float)
    parser.add_argument("--cf-f", type=float)
    parser.add_argument("--temp-k", type=float)
    parser.add_argument("--responsivity", type=float)
    parser.add_argument("--rin-db-hz", type=float)
    parser.add_argument("--opamp-en", type=float)
    parser.add_argument("--opamp-in", type=float)
    parser.add_argument("--high-freq-enbw", type=float)
    parser.add_argument("--low-freq-enbw", type=float)
    return parser


def parse_args(argv=None):
    parser = build_parser()
    args = parse_config_args(parser, HARDWARE_TIA_ARGS, argv, default_config=HARDWARE_CONFIG)
    if args.project_config.tia.profile != "hardware":
        parser.error("This entry estimates hardware TIA curves; use spectrum for the VPI TIA")
    return args


def main() -> int:
    args = parse_args()
    save_config_snapshot(args.project_config, args.out_dir, source=args.config)
    params = TIAParams(
        rf_ohm=args.rf_ohm,
        cf_f=args.cf_f,
        temp_k=args.temp_k,
        responsivity_a_per_w=args.responsivity,
        rin_db_hz=args.rin_db_hz,
        opamp_en_v_per_sqrt_hz=args.opamp_en,
        opamp_in_a_per_sqrt_hz=args.opamp_in,
        high_freq_enbw_hz=args.high_freq_enbw,
        low_freq_enbw_hz=args.low_freq_enbw,
        passband_ratio=args.project_config.tia.passband_ratio,
    )
    products = run(
        summary_path=args.summary.resolve(),
        out_dir=args.out_dir.resolve(),
        report_path=args.report.resolve(),
        params=params,
        rng_seed=args.rng_seed,
    )
    print(f"generated_curves={len(products)}")
    print(f"report={args.report.resolve()}")
    for product in products:
        print(
            "{label}: selected SNR={snr:.2f} dB, selected Vpeak={vp}, png={png}".format(
                label=product.label,
                snr=product.selected_snr_db if product.selected_snr_db is not None else float("nan"),
                vp=_format_eng(product.selected_signal_v_peak, "V"),
                png=product.png_path,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
