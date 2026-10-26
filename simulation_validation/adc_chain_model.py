"""Model ADS131M02 effects after the TIA-domain observation curves.

The input CSV files come from ``tia_experimental_curves.py``.  This script adds
the ADC-facing part of the chain:

    TIA output voltage -> ADC input RC -> ADS131M02 sinc3 response
    -> full-scale check -> ADC input-referred noise + quantization noise

The result is still a frequency-bin level model, not a full transient
delta-sigma modulator simulation.  It is intended to answer whether the control
tones are visible, clipped, aliased, or likely limited by ADC noise.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from tia_visibility_analyzer import _format_eng, _to_float


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = PROJECT_ROOT / "simulation_validation" / "results" / "findpoint_summary.json"
DEFAULT_TIA_DIR = PROJECT_ROOT / "simulation_validation" / "results" / "tia_curves"
DEFAULT_OUT_DIR = PROJECT_ROOT / "simulation_validation" / "results" / "adc_curves"
DEFAULT_REPORT = PROJECT_ROOT / "simulation_validation" / "results" / "adc_chain_report.md"
REFERENCE_LOAD_OHM = 50.0


@dataclass(frozen=True)
class ADCParams:
    sample_rate_sps: float = 32_000.0
    osr: int = 128
    power_mode: str = "HR"
    gain: float = 1.0
    vref_v: float = 1.2
    bits: int = 24
    goertzel_points: int = 640
    goertzel_blocks: int = 10
    window: str = "none"
    global_chop_enabled: bool = False
    dc_block_enabled: bool = False
    input_bias_mode: str = "not_configured"
    r_pos_ohm: float = 1_000.0
    r_neg_ohm: float = 1_000.0
    c_diff_f: float = 10e-9
    adc_noise_rms_v: float = 21.31e-6
    reference_load_ohm: float = REFERENCE_LOAD_OHM

    @property
    def fmod_hz(self) -> float:
        return float(self.sample_rate_sps) * float(self.osr)

    @property
    def fullscale_peak_v(self) -> float:
        return float(self.vref_v) / float(self.gain)

    @property
    def lsb_v(self) -> float:
        # Bipolar two's-complement code span, expressed as input volts per code.
        return (2.0 * self.fullscale_peak_v) / float(2**self.bits)

    @property
    def rc_fc_hz(self) -> float:
        r_total = float(self.r_pos_ohm) + float(self.r_neg_ohm)
        return 1.0 / (2.0 * math.pi * r_total * float(self.c_diff_f))

    @property
    def goertzel_bin_width_hz(self) -> float:
        return float(self.sample_rate_sps) / float(self.goertzel_points)

    @property
    def measurement_enbw_hz(self) -> float:
        # Rectangular/no-window Goertzel has ENBW equal to one DFT bin.
        window = str(self.window).strip().lower()
        factor = 1.0 if window in {"none", "rect", "rectangular"} else 1.0
        return self.goertzel_bin_width_hz * factor


@dataclass
class ADCProduct:
    step_key: str
    label: str
    csv_path: Path
    png_path: Path | None
    row_count: int
    selected_bias_v: float | None
    selected_signal_dbm_1ohm: float | None
    selected_signal_dbm_50ohm: float | None
    selected_measured_dbm_1ohm: float | None
    selected_measured_dbm_50ohm: float | None
    selected_snr_db: float | None
    selected_fs_margin_db: float | None
    min_fs_margin_db: float
    min_snr_db: float
    flags: list[str]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _dbv(value_v: float) -> float:
    return 20.0 * math.log10(max(abs(float(value_v)), 1e-300))


def _dbm_from_v_rms(value_v_rms: float, load_ohm: float) -> float:
    v = max(abs(float(value_v_rms)), 1e-300)
    return 10.0 * math.log10((v * v / float(load_ohm)) * 1000.0)


def _db(value: float) -> float:
    return 20.0 * math.log10(max(abs(float(value)), 1e-300))


def _round(value: Any, digits: int = 9) -> Any:
    if isinstance(value, float) and math.isfinite(value):
        return round(value, digits)
    return value


def _rc_gain(freq_hz: float, params: ADCParams) -> float:
    return 1.0 / math.sqrt(1.0 + (float(freq_hz) / params.rc_fc_hz) ** 2)


def _sinc3_gain(freq_hz: float, params: ADCParams) -> float:
    f = abs(float(freq_hz))
    if f == 0.0:
        return 1.0
    fmod = params.fmod_hz
    n = float(params.osr)
    denominator = n * math.sin(math.pi * f / fmod)
    if abs(denominator) < 1e-300:
        return 0.0
    numerator = math.sin(math.pi * n * f / fmod)
    return abs(numerator / denominator) ** 3


def _clipped_sine_fundamental_peak(input_peak_v: float, fullscale_peak_v: float) -> float:
    """Fundamental peak of a sine clipped symmetrically to +/- fullscale."""

    a = abs(float(input_peak_v))
    b = abs(float(fullscale_peak_v))
    if a <= b or a == 0.0:
        return a
    ratio = max(min(b / a, 1.0), 0.0)
    alpha = math.asin(ratio)
    return (2.0 * a / math.pi) * (alpha + ratio * math.sqrt(max(1.0 - ratio * ratio, 0.0)))


def _noise_bin_from_total_rms(total_noise_rms_v: float, sample_rate_sps: float, enbw_hz: float) -> float:
    # Approximate the data-sheet broadband RMS noise as white over Nyquist.
    nyquist_hz = max(float(sample_rate_sps) / 2.0, 1e-300)
    density_v_sqrt_hz = float(total_noise_rms_v) / math.sqrt(nyquist_hz)
    return density_v_sqrt_hz * math.sqrt(max(float(enbw_hz), 0.0))


def _nearest_goertzel_bin(freq_hz: float, params: ADCParams) -> tuple[int, float, float]:
    bin_width = params.goertzel_bin_width_hz
    index = int(round(float(freq_hz) / bin_width))
    bin_freq = index * bin_width
    return index, bin_freq, float(freq_hz) - bin_freq


def _load_summary(summary_path: Path) -> dict[str, dict[str, Any]]:
    if not summary_path.exists():
        return {}
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    steps = data.get("steps", {})
    return {str(k): v for k, v in steps.items() if isinstance(v, dict)}


def _plot_adc_curve(
    *,
    path: Path,
    label: str,
    x_values: list[float],
    signal_dbm: list[float],
    measured_dbm: list[float],
    noise_dbm: list[float],
    snr_db: list[float],
    fs_margin_db: list[float],
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

    ax1.plot(x_values, signal_dbm, linewidth=1.8, label="ADC signal eq. dBm")
    ax1.plot(x_values, measured_dbm, linewidth=1.0, alpha=0.72, label="ADC measured eq. dBm")
    ax1.plot(x_values, noise_dbm, linewidth=1.2, linestyle="--", label="ADC noise/bin eq. dBm")
    ax1.set_ylabel("Equivalent power (dBm, 50 ohm)")
    ax1.set_title(label)
    ax1.grid(True, alpha=0.25)
    ax1.legend(loc="best", fontsize=8)

    ax2.plot(x_values, snr_db, color="#2ca02c", linewidth=1.4, label="SNR")
    ax2.plot(x_values, fs_margin_db, color="#d62728", linewidth=1.1, linestyle="--", label="FS margin")
    ax2.axhline(0.0, color="#666666", linestyle="--", linewidth=0.8)
    ax2.set_xlabel(x_label)
    ax2.set_ylabel("dB")
    ax2.grid(True, alpha=0.25)
    ax2.legend(loc="best", fontsize=8)

    if selected_bias_v is not None:
        ax1.axvline(selected_bias_v, color="#d62728", linestyle=":", linewidth=1.2)
        ax2.axvline(selected_bias_v, color="#d62728", linestyle=":", linewidth=1.2)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def _process_file(
    *,
    tia_csv: Path,
    out_dir: Path,
    summary_steps: dict[str, dict[str, Any]],
    params: ADCParams,
    rng: random.Random,
) -> ADCProduct | None:
    source_rows = _read_csv(tia_csv)
    if not source_rows:
        return None

    step_key = tia_csv.name.removesuffix("_tia_curve.csv")
    step = summary_steps.get(step_key, {})
    label = str(step.get("label", step_key))
    selected_index = int(step.get("selected_index", 0))

    curve_rows: list[dict[str, Any]] = []
    x_values: list[float] = []
    signal_dbm: list[float] = []
    measured_dbm: list[float] = []
    noise_dbm: list[float] = []
    snr_db: list[float] = []
    fs_margin_db: list[float] = []

    quant_noise_total = params.lsb_v / math.sqrt(12.0)

    for idx, row in enumerate(source_rows):
        bias_v = _to_float(row.get("bias_source_V"))
        freq_hz = _to_float(row.get("tone_freq_Hz"))
        tia_signal_peak = _to_float(row.get("TIA_signal_V_peak"))
        tia_signal_rms = _to_float(row.get("TIA_signal_V_rms"))
        tia_noise_rms_bin = _to_float(row.get("TIA_noise_V_rms_bin"))
        source_enbw_hz = _to_float(row.get("ENBW_Hz")) or 1.0
        enbw_hz = params.measurement_enbw_hz
        if bias_v is None or freq_hz is None or tia_signal_peak is None or tia_signal_rms is None:
            continue
        if tia_noise_rms_bin is None:
            tia_noise_rms_bin = 0.0

        bin_index, bin_freq_hz, bin_error_hz = _nearest_goertzel_bin(freq_hz, params)
        rc = _rc_gain(freq_hz, params)
        sinc3 = _sinc3_gain(freq_hz, params)
        total_gain = rc * sinc3

        linear_peak = float(tia_signal_peak) * total_gain
        linear_rms = float(tia_signal_rms) * total_gain
        clipped_peak = _clipped_sine_fundamental_peak(linear_peak, params.fullscale_peak_v)
        clipped_rms = clipped_peak / math.sqrt(2.0)

        source_to_measurement_noise_scale = math.sqrt(enbw_hz / max(float(source_enbw_hz), 1e-300))
        tia_noise_after_adc = float(tia_noise_rms_bin) * source_to_measurement_noise_scale * total_gain
        adc_noise_bin = _noise_bin_from_total_rms(
            params.adc_noise_rms_v,
            params.sample_rate_sps,
            enbw_hz,
        )
        quant_noise_bin = _noise_bin_from_total_rms(quant_noise_total, params.sample_rate_sps, enbw_hz)
        total_noise_bin = math.sqrt(
            tia_noise_after_adc**2
            + adc_noise_bin**2
            + quant_noise_bin**2
        )
        block_count = max(int(params.goertzel_blocks), 1)
        # Averaging power over M independent blocks keeps the expected noise
        # floor unchanged and reduces only the random scatter.
        noise_power_sample = (total_noise_bin**2) * rng.gammavariate(block_count, 1.0 / block_count)
        measured_rms = math.sqrt(clipped_rms**2 + noise_power_sample)

        margin_db = _db(params.fullscale_peak_v / max(abs(linear_peak), 1e-300))
        clip_ratio = abs(linear_peak) / max(params.fullscale_peak_v, 1e-300)
        alias_flag = "ADC_FREQ_OK" if abs(freq_hz) < params.sample_rate_sps / 2.0 else "ADC_FREQ_ABOVE_NYQUIST"
        clip_flag = "ADC_LINEAR" if clip_ratio <= 1.0 else "ADC_CLIPPED"
        cm_flag = "ADC_INPUT_BIAS_NOT_CONFIGURED"
        coherence_flag = "ADC_COHERENT_BIN" if abs(bin_error_hz) < 1e-9 else "ADC_BIN_OFFSET"

        signal_dbv = _dbv(clipped_rms)
        measured_dbv = _dbv(measured_rms)
        noise_dbv_value = _dbv(total_noise_bin)
        signal_dbm_1ohm = _dbm_from_v_rms(clipped_rms, 1.0)
        measured_dbm_1ohm = _dbm_from_v_rms(measured_rms, 1.0)
        noise_dbm_1ohm = _dbm_from_v_rms(total_noise_bin, 1.0)
        signal_dbm_value = _dbm_from_v_rms(clipped_rms, params.reference_load_ohm)
        measured_dbm_value = _dbm_from_v_rms(measured_rms, params.reference_load_ohm)
        noise_dbm_value = _dbm_from_v_rms(total_noise_bin, params.reference_load_ohm)
        snr_value = 20.0 * math.log10(max(clipped_rms, 1e-300) / max(total_noise_bin, 1e-300))

        row_out = {
            "row_index": idx,
            "step_key": step_key,
            "bias_source_V": bias_v,
            "bias_effective_V": _to_float(row.get("bias_effective_V")),
            "tone_freq_Hz": freq_hz,
            "ADC_sample_rate_SPS": params.sample_rate_sps,
            "ADC_OSR": params.osr,
            "ADC_power_mode": params.power_mode,
            "ADC_fmod_Hz": params.fmod_hz,
            "ADC_gain": params.gain,
            "ADC_vref_V": params.vref_v,
            "ADC_global_chop_enabled": params.global_chop_enabled,
            "ADC_dc_block_enabled": params.dc_block_enabled,
            "ADC_input_bias_mode": params.input_bias_mode,
            "ADC_goertzel_points": params.goertzel_points,
            "ADC_goertzel_blocks": params.goertzel_blocks,
            "ADC_window": params.window,
            "ADC_goertzel_bin_width_Hz": params.goertzel_bin_width_hz,
            "ADC_goertzel_bin_index": bin_index,
            "ADC_goertzel_bin_freq_Hz": bin_freq_hz,
            "ADC_goertzel_bin_error_Hz": bin_error_hz,
            "ADC_measurement_ENBW_Hz": enbw_hz,
            "ADC_source_TIA_ENBW_Hz": source_enbw_hz,
            "ADC_fullscale_peak_V": params.fullscale_peak_v,
            "ADC_lsb_V": params.lsb_v,
            "ADC_input_rc_fc_Hz": params.rc_fc_hz,
            "ADC_input_rc_gain": rc,
            "ADC_input_rc_gain_dB": _db(rc),
            "ADC_sinc3_gain": sinc3,
            "ADC_sinc3_gain_dB": _db(sinc3),
            "ADC_total_gain_from_TIA": total_gain,
            "ADC_total_gain_from_TIA_dB": _db(total_gain),
            "ADC_linear_signal_V_peak": linear_peak,
            "ADC_linear_signal_V_rms": linear_rms,
            "ADC_signal_V_peak_after_clip_fundamental": clipped_peak,
            "ADC_signal_V_rms": clipped_rms,
            "ADC_noise_TIA_V_rms_bin": tia_noise_after_adc,
            "ADC_noise_input_referred_V_rms_bin": adc_noise_bin,
            "ADC_noise_quantization_V_rms_bin": quant_noise_bin,
            "ADC_noise_total_V_rms_bin": total_noise_bin,
            "ADC_measured_V_rms": measured_rms,
            "ADC_signal_dBV_rms": signal_dbv,
            "ADC_noise_dBV_rms": noise_dbv_value,
            "ADC_measured_dBV_rms": measured_dbv,
            "ADC_signal_dBm_1ohm": signal_dbm_1ohm,
            "ADC_noise_dBm_1ohm": noise_dbm_1ohm,
            "ADC_measured_dBm_1ohm": measured_dbm_1ohm,
            "ADC_signal_dBm_50ohm": signal_dbm_value,
            "ADC_noise_dBm_50ohm": noise_dbm_value,
            "ADC_measured_dBm_50ohm": measured_dbm_value,
            "ADC_vpi_rms_xx_plus30_dB": signal_dbm_1ohm,
            "ADC_SNR_dB": snr_value,
            "ADC_fullscale_margin_dB": margin_db,
            "ADC_clip_ratio": clip_ratio,
            "ADC_alias_flag": alias_flag,
            "ADC_clip_flag": clip_flag,
            "ADC_common_mode_flag": cm_flag,
            "ADC_coherence_flag": coherence_flag,
            "ENBW_Hz": enbw_hz,
        }
        rounded = {k: _round(v) for k, v in row_out.items()}
        curve_rows.append(rounded)

        x_values.append(float(bias_v))
        signal_dbm.append(signal_dbm_value)
        measured_dbm.append(measured_dbm_value)
        noise_dbm.append(noise_dbm_value)
        snr_db.append(snr_value)
        fs_margin_db.append(margin_db)

    if not curve_rows:
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    curve_csv = out_dir / f"{step_key}_adc_curve.csv"
    curve_png = out_dir / f"{step_key}_adc_curve.png"
    _write_csv(curve_csv, curve_rows)

    selected_bias_v = None
    if 0 <= selected_index < len(curve_rows):
        selected_bias_v = _to_float(curve_rows[selected_index].get("bias_source_V"))

    png_path = _plot_adc_curve(
        path=curve_png,
        label=f"{step_key} ADC observation",
        x_values=x_values,
        signal_dbm=signal_dbm,
        measured_dbm=measured_dbm,
        noise_dbm=noise_dbm,
        snr_db=snr_db,
        fs_margin_db=fs_margin_db,
        selected_bias_v=selected_bias_v,
        x_label="bias_source_V",
    )

    selected = curve_rows[selected_index] if 0 <= selected_index < len(curve_rows) else {}
    flags = sorted(
        {
            str(row["ADC_alias_flag"])
            for row in curve_rows
        }
        | {str(row["ADC_clip_flag"]) for row in curve_rows}
        | {str(row["ADC_common_mode_flag"]) for row in curve_rows}
        | {str(row["ADC_coherence_flag"]) for row in curve_rows}
    )
    return ADCProduct(
        step_key=step_key,
        label=label,
        csv_path=curve_csv,
        png_path=png_path,
        row_count=len(curve_rows),
        selected_bias_v=selected_bias_v,
        selected_signal_dbm_1ohm=_to_float(selected.get("ADC_signal_dBm_1ohm")),
        selected_signal_dbm_50ohm=_to_float(selected.get("ADC_signal_dBm_50ohm")),
        selected_measured_dbm_1ohm=_to_float(selected.get("ADC_measured_dBm_1ohm")),
        selected_measured_dbm_50ohm=_to_float(selected.get("ADC_measured_dBm_50ohm")),
        selected_snr_db=_to_float(selected.get("ADC_SNR_dB")),
        selected_fs_margin_db=_to_float(selected.get("ADC_fullscale_margin_dB")),
        min_fs_margin_db=min(float(row["ADC_fullscale_margin_dB"]) for row in curve_rows),
        min_snr_db=min(float(row["ADC_SNR_dB"]) for row in curve_rows),
        flags=flags,
    )


def _write_report(path: Path, products: list[ADCProduct], params: ADCParams) -> None:
    lines = [
        "# ADS131M02 ADC 链路建模报告",
        "",
        f"生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "",
        "## 1. 参数",
        "",
        f"- `fDATA = {_format_eng(params.sample_rate_sps, 'SPS')}`",
        f"- `OSR = {params.osr}`",
        f"- `power mode = {params.power_mode}`",
        f"- `fMOD = {_format_eng(params.fmod_hz, 'Hz')}`",
        f"- `PGA gain = {params.gain:g}`",
        f"- `global chop = {params.global_chop_enabled}`",
        f"- `DC block = {params.dc_block_enabled}`",
        f"- `input bias = {params.input_bias_mode}`",
        f"- `Goertzel = {params.goertzel_points} points, {params.goertzel_blocks} blocks, window = {params.window}`",
        f"- `Goertzel bin width / ENBW = {_format_eng(params.measurement_enbw_hz, 'Hz')}`",
        f"- `VREF = {params.vref_v:g} V`",
        f"- `ADC differential full-scale = +/-{params.fullscale_peak_v:g} Vpeak`",
        f"- `ADC input RC fc = {_format_eng(params.rc_fc_hz, 'Hz')}`",
        f"- `ADC input-referred noise = {_format_eng(params.adc_noise_rms_v, 'V')} rms`",
        f"- `LSB = {_format_eng(params.lsb_v, 'V')}`",
        "",
        "## 2. 曲线汇总",
        "",
        "| Step | 点数 | 选中偏置 | 选中信号 dBm_50ohm | 选中观测 dBm_50ohm | 选中 SNR | 选中满量程裕量 | 最小满量程裕量 | 最小 SNR | 标记 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for product in products:
        lines.append(
            "| {label} | {rows} | {bias} | {sig} | {meas} | {snr} | {margin} | {min_margin:.2f} dB | {min_snr:.2f} dB | {flags} |".format(
                label=product.label,
                rows=product.row_count,
                bias="-" if product.selected_bias_v is None else f"{product.selected_bias_v:g} V",
                sig="-" if product.selected_signal_dbm_50ohm is None else f"{product.selected_signal_dbm_50ohm:.2f} dBm",
                meas="-" if product.selected_measured_dbm_50ohm is None else f"{product.selected_measured_dbm_50ohm:.2f} dBm",
                snr="-" if product.selected_snr_db is None else f"{product.selected_snr_db:.2f} dB",
                margin="-" if product.selected_fs_margin_db is None else f"{product.selected_fs_margin_db:.2f} dB",
                min_margin=product.min_fs_margin_db,
                min_snr=product.min_snr_db,
                flags=", ".join(product.flags),
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
            "## 4. 模型说明",
            "",
            "- 本模型是频点/bin 级近似，用于评估导频和交调项经过 ADC 后的可见性，不是完整 delta-sigma 位流仿真。",
            "- `ADC input RC` 使用原理图中的 `1 kΩ + 1 kΩ` 和差分 `10 nF` 估算，一阶差分低通截止频率约为 `7.96 kHz`。",
            "- `ADC_sinc3_gain` 使用 ADS131M02 sinc3 数字滤波幅频响应估算。",
            "- 当前主线测量算法为 `32 kSPS + 640点 Goertzel + 无窗 + 10 blocks`，因此单 block 的矩形窗 ENBW 为 `50 Hz`。",
            "- `10 blocks` 在当前模型中按功率平均处理：噪声均值不变，随机起伏降低。",
            "- `ADC_fullscale_margin_dB < 0` 表示按当前 TIA 输出幅度会超过 `±VREF/Gain` 差分满量程，相关点会被标为 `ADC_CLIPPED`。",
            "- `ADC_INPUT_BIAS_NOT_CONFIGURED` 表示当前主线未显式配置输入偏置；如果 TIA 输出是以 0 V 为中心的双极性信号，而 ADC 采用单电源且 AINN 接地，需要进一步确认负半周输入是否合法。",
            "- `ADC_COHERENT_BIN` 表示当前导频频点正好落在 640 点 Goertzel 的整数 bin 上。",
            "- `dBm_50ohm` 仍然只是 50 ohm 等效读数，方便对比历史实验图；ADC 实际处理的是输入电压和数字码值。",
            "",
            "## 5. 仍需确认",
            "",
            "1. ADC 输入是否存在中点偏置或 AC 耦合后的共模恢复；",
            "2. TIA 输出到 ADC 输入之间是否还有额外衰减、限幅或保护网络；",
            "3. ADS131M02 噪声参数是否需要根据实测空输入噪底重新标定；",
            "4. Goertzel 输出是功率平均、幅度平均还是复数相干平均。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    *,
    summary_path: Path,
    tia_dir: Path,
    out_dir: Path,
    report_path: Path,
    params: ADCParams,
    rng_seed: int,
) -> list[ADCProduct]:
    summary_steps = _load_summary(summary_path)
    rng = random.Random(int(rng_seed))
    products: list[ADCProduct] = []
    for tia_csv in sorted(tia_dir.glob("*_tia_curve.csv")):
        product = _process_file(
            tia_csv=tia_csv,
            out_dir=out_dir,
            summary_steps=summary_steps,
            params=params,
            rng=rng,
        )
        if product is not None:
            products.append(product)
    _write_report(report_path, products, params)
    return products


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Model ADS131M02 effects after TIA curves.")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--tia-dir", type=Path, default=DEFAULT_TIA_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--rng-seed", type=int, default=20260709)
    parser.add_argument("--sample-rate", type=float, default=32_000.0)
    parser.add_argument("--osr", type=int, default=128)
    parser.add_argument("--power-mode", default="HR")
    parser.add_argument("--gain", type=float, default=1.0)
    parser.add_argument("--vref", type=float, default=1.2)
    parser.add_argument("--bits", type=int, default=24)
    parser.add_argument("--goertzel-points", type=int, default=640)
    parser.add_argument("--goertzel-blocks", type=int, default=10)
    parser.add_argument("--window", default="none")
    parser.add_argument("--global-chop", action="store_true")
    parser.add_argument("--dc-block", action="store_true")
    parser.add_argument("--input-bias-mode", default="not_configured")
    parser.add_argument("--r-pos", type=float, default=1_000.0)
    parser.add_argument("--r-neg", type=float, default=1_000.0)
    parser.add_argument("--c-diff", type=float, default=10e-9)
    parser.add_argument("--adc-noise-rms", type=float, default=21.31e-6)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    params = ADCParams(
        sample_rate_sps=args.sample_rate,
        osr=args.osr,
        power_mode=args.power_mode,
        gain=args.gain,
        vref_v=args.vref,
        bits=args.bits,
        goertzel_points=args.goertzel_points,
        goertzel_blocks=args.goertzel_blocks,
        window=args.window,
        global_chop_enabled=bool(args.global_chop),
        dc_block_enabled=bool(args.dc_block),
        input_bias_mode=args.input_bias_mode,
        r_pos_ohm=args.r_pos,
        r_neg_ohm=args.r_neg,
        c_diff_f=args.c_diff,
        adc_noise_rms_v=args.adc_noise_rms,
    )
    products = run(
        summary_path=args.summary.resolve(),
        tia_dir=args.tia_dir.resolve(),
        out_dir=args.out_dir.resolve(),
        report_path=args.report.resolve(),
        params=params,
        rng_seed=args.rng_seed,
    )
    print(f"generated_adc_curves={len(products)}")
    print(f"report={args.report.resolve()}")
    for product in products:
        print(
            "{label}: selected={sig}, SNR={snr}, FS_margin={margin}, flags={flags}".format(
                label=product.label,
                sig="-" if product.selected_signal_dbm_50ohm is None else f"{product.selected_signal_dbm_50ohm:.2f} dBm",
                snr="-" if product.selected_snr_db is None else f"{product.selected_snr_db:.2f} dB",
                margin="-" if product.selected_fs_margin_db is None else f"{product.selected_fs_margin_db:.2f} dB",
                flags=",".join(product.flags),
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
