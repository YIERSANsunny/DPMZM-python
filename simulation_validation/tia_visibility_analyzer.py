"""Estimate TIA output visibility for the selected Step 1-4 bias points.

This script consumes ``findpoint_summary.json`` from the offline validator,
loads the selected CSV rows, and estimates the output voltage/noise after the
current schematic TIA: Rf || Cf = 100 kOhm || 10 pF.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from config import HARDWARE_CONFIG, HARDWARE_TIA_ARGS, load_config, parse_config_args, save_config_snapshot

HARDWARE_DEFAULTS = load_config(HARDWARE_CONFIG)
DEFAULT_SUMMARY = PROJECT_ROOT / "simulation_validation" / "results" / "findpoint_summary.json"
DEFAULT_OUT_DIR = PROJECT_ROOT / "simulation_validation" / "results"

K_BOLTZMANN = 1.380649e-23
Q_ELECTRON = 1.602176634e-19


@dataclass(frozen=True)
class TIAParams:
    rf_ohm: float = HARDWARE_DEFAULTS.tia.rf_ohm
    cf_f: float = HARDWARE_DEFAULTS.tia.cf_f
    temp_k: float = HARDWARE_DEFAULTS.physical.temp_k
    responsivity_a_per_w: float = HARDWARE_DEFAULTS.physical.responsivity_a_per_w
    rin_db_hz: float = HARDWARE_DEFAULTS.physical.rin_db_hz
    opamp_en_v_per_sqrt_hz: float = HARDWARE_DEFAULTS.tia.opamp_en_v_per_sqrt_hz
    opamp_in_a_per_sqrt_hz: float = HARDWARE_DEFAULTS.tia.opamp_in_a_per_sqrt_hz
    high_freq_enbw_hz: float = HARDWARE_DEFAULTS.tia.high_freq_enbw_hz
    low_freq_enbw_hz: float = HARDWARE_DEFAULTS.tia.low_freq_enbw_hz
    passband_ratio: float = HARDWARE_DEFAULTS.tia.passband_ratio

    @property
    def fc_hz(self) -> float:
        return 1.0 / (2.0 * math.pi * self.rf_ohm * self.cf_f)


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


def _to_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _db(value: float) -> float:
    return 20.0 * math.log10(max(float(value), 1e-300))


def _read_selected_row(path: Path, index: int) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row_index, row in enumerate(reader):
            if row_index == index:
                return row
    raise IndexError(f"row index {index} not found in {path}")


def _first_numeric(row: dict[str, str], columns: tuple[str, ...]) -> tuple[str | None, float | None]:
    for column in columns:
        if column in row:
            value = _to_float(row.get(column))
            if value is not None:
                return column, value
    return None, None


def _pd_avg_w(row: dict[str, str]) -> float | None:
    pd_dbm = _to_float(row.get("P_pd_avg_dBm"))
    if pd_dbm is None:
        return None
    return 10.0 ** ((pd_dbm - 30.0) / 10.0)


def _default_enbw(freq_hz: float, params: TIAParams) -> float:
    return params.low_freq_enbw_hz if abs(freq_hz) < 1e6 else params.high_freq_enbw_hz


def _bandwidth_flag(freq_hz: float, params: TIAParams) -> str:
    f = abs(float(freq_hz))
    if f <= params.passband_ratio * params.fc_hz:
        return "TIA_PASSBAND"
    if f <= params.fc_hz:
        return "TIA_ROLL_OFF"
    return "TIA_OUT_OF_BAND"


def _estimate_tia(
    *,
    current_peak_a: float,
    freq_hz: float,
    pd_avg_w: float | None,
    enbw_hz: float,
    params: TIAParams,
) -> dict[str, float | str | None]:
    fc_hz = params.fc_hz
    z_ohm = params.rf_ohm / math.sqrt(1.0 + (float(freq_hz) / fc_hz) ** 2)
    attenuation_db = _db(z_ohm / params.rf_ohm)
    gain_vs_50_db = _db(z_ohm / 50.0)

    v_peak = abs(float(current_peak_a)) * z_ohm
    v_rms = v_peak / math.sqrt(2.0)

    i_pd_avg = None
    i_shot = 0.0
    i_rin = 0.0
    if pd_avg_w is not None:
        i_pd_avg = params.responsivity_a_per_w * pd_avg_w
        i_shot = math.sqrt(max(0.0, 2.0 * Q_ELECTRON * i_pd_avg))
        i_rin = i_pd_avg * math.sqrt(10.0 ** (params.rin_db_hz / 10.0))

    i_rf = math.sqrt(4.0 * K_BOLTZMANN * params.temp_k / params.rf_ohm)
    i_op = params.opamp_in_a_per_sqrt_hz
    e_op = params.opamp_en_v_per_sqrt_hz

    input_current_noise_density = math.sqrt(i_shot**2 + i_rin**2 + i_rf**2 + i_op**2)
    output_current_noise_density = z_ohm * input_current_noise_density
    output_noise_density = math.sqrt(output_current_noise_density**2 + e_op**2)
    v_noise_rms_bin = output_noise_density * math.sqrt(float(enbw_hz))
    snr_db = _db(v_rms / v_noise_rms_bin) if v_noise_rms_bin > 0 else None

    saturation_flag = "TIA_OUTPUT_LARGE" if v_peak > 8.0 else "OK"

    return {
        "freq_hz": freq_hz,
        "enbw_hz": enbw_hz,
        "fc_hz": fc_hz,
        "z_tia_ohm": z_ohm,
        "z_tia_db_ohm": _db(z_ohm),
        "gain_vs_50ohm_db": gain_vs_50_db,
        "attenuation_vs_low_freq_db": attenuation_db,
        "v_tone_peak_v": v_peak,
        "v_tone_rms_v": v_rms,
        "pd_avg_w": pd_avg_w,
        "i_pd_avg_a": i_pd_avg,
        "i_shot_a_per_sqrt_hz": i_shot,
        "i_rin_a_per_sqrt_hz": i_rin,
        "i_rf_a_per_sqrt_hz": i_rf,
        "i_opamp_a_per_sqrt_hz": i_op,
        "e_opamp_v_per_sqrt_hz": e_op,
        "e_noise_out_v_per_sqrt_hz": output_noise_density,
        "v_noise_rms_bin_v": v_noise_rms_bin,
        "snr_tia_db": snr_db,
        "bandwidth_flag": _bandwidth_flag(freq_hz, params),
        "saturation_flag": saturation_flag,
    }


def _round_value(value: Any, digits: int = 6) -> Any:
    if isinstance(value, float) and math.isfinite(value):
        if value == 0.0:
            return 0.0
        if abs(value) < 1e-3 or abs(value) >= 1e5:
            return float(f"{value:.6e}")
        return round(value, digits)
    return value


def _format_eng(value: Any, unit: str = "") -> str:
    if value is None:
        return "-"
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        return str(value)
    value_f = float(value)
    if value_f == 0:
        return f"0 {unit}".rstrip()
    abs_v = abs(value_f)
    prefixes = [
        (1e9, "G"),
        (1e6, "M"),
        (1e3, "k"),
        (1.0, ""),
        (1e-3, "m"),
        (1e-6, "u"),
        (1e-9, "n"),
        (1e-12, "p"),
        (1e-15, "f"),
    ]
    for scale, prefix in prefixes:
        if abs_v >= scale:
            return f"{value_f / scale:.3g} {prefix}{unit}".rstrip()
    return f"{value_f:.3e} {unit}".rstrip()


def run_analysis(
    *,
    summary_path: Path,
    out_dir: Path,
    params: TIAParams,
) -> dict[str, Any]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    steps = summary.get("steps", {})
    results: dict[str, Any] = {}

    for step_key, step in steps.items():
        if not isinstance(step, dict) or step.get("status") != "FOUND":
            continue
        csv_path = Path(str(step["csv_path"]))
        selected_index = int(step["selected_index"])
        row = _read_selected_row(csv_path, selected_index)
        current_col, current_peak = _first_numeric(row, CURRENT_PEAK_COLUMNS)
        freq_col, freq_hz = _first_numeric(row, TONE_FREQ_COLUMNS)
        if current_peak is None or freq_hz is None:
            results[step_key] = {
                "status": "SKIPPED",
                "label": step.get("label", step_key),
                "message": "selected row has no current peak or tone frequency column",
            }
            continue

        enbw_hz = _default_enbw(freq_hz, params)
        estimate = _estimate_tia(
            current_peak_a=current_peak,
            freq_hz=freq_hz,
            pd_avg_w=_pd_avg_w(row),
            enbw_hz=enbw_hz,
            params=params,
        )
        results[step_key] = {
            "status": "FOUND",
            "label": step.get("label", step_key),
            "output_name": step.get("output_name"),
            "output_value": step.get("output_value"),
            "csv_path": str(csv_path),
            "selected_index": selected_index,
            "current_peak_column": current_col,
            "tone_frequency_column": freq_col,
            "current_peak_a": current_peak,
            **estimate,
        }

    overall_flags = sorted(
        {
            str(result.get("bandwidth_flag"))
            for result in results.values()
            if isinstance(result, dict) and result.get("bandwidth_flag") not in {None, "TIA_PASSBAND"}
        }
    )
    overall_status = "COMPLETE_WITH_WARNINGS" if overall_flags else "COMPLETE"

    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_summary_path": str(summary_path),
        "overall_status": overall_status,
        "overall_flags": overall_flags,
        "tia_params": {
            "rf_ohm": params.rf_ohm,
            "cf_f": params.cf_f,
            "fc_hz": params.fc_hz,
            "temp_k": params.temp_k,
            "responsivity_a_per_w": params.responsivity_a_per_w,
            "rin_db_hz": params.rin_db_hz,
            "opamp_en_v_per_sqrt_hz": params.opamp_en_v_per_sqrt_hz,
            "opamp_in_a_per_sqrt_hz": params.opamp_in_a_per_sqrt_hz,
            "high_freq_enbw_hz": params.high_freq_enbw_hz,
            "low_freq_enbw_hz": params.low_freq_enbw_hz,
        },
        "steps": results,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "tia_visibility_summary.json"
    report_path = out_dir / "tia_visibility_report.md"
    json_path.write_text(json.dumps(output, ensure_ascii=False, indent=2, default=_round_value), encoding="utf-8")
    _write_report(output, report_path)
    output["summary_path"] = str(json_path)
    output["report_path"] = str(report_path)
    return output


def _write_report(summary: dict[str, Any], path: Path) -> None:
    params = summary["tia_params"]
    lines = [
        "# TIA 可见性验证报告",
        "",
        f"生成时间：{summary['generated_at']}",
        "",
        f"总状态：`{summary['overall_status']}`",
        "",
        "## 1. TIA 参数",
        "",
        "| 参数 | 数值 |",
        "|---|---:|",
        f"| R_f | {_format_eng(params['rf_ohm'], 'ohm')} |",
        f"| C_f | {_format_eng(params['cf_f'], 'F')} |",
        f"| f_c | {_format_eng(params['fc_hz'], 'Hz')} |",
        f"| 低频跨阻 | {20 * math.log10(params['rf_ohm']):.2f} dBΩ |",
        f"| 相对 50Ω 低频增益 | {20 * math.log10(params['rf_ohm'] / 50.0):.2f} dB |",
        f"| 高频默认 ENBW | {_format_eng(params['high_freq_enbw_hz'], 'Hz')} |",
        f"| 低频默认 ENBW | {_format_eng(params['low_freq_enbw_hz'], 'Hz')} |",
        "",
        "## 2. Step 可见性",
        "",
        "| Step | 频率 | 带宽标记 | 饱和标记 | |Z_TIA| | 相对低频衰减 | I_peak | V_peak | V_noise/bin | SNR_TIA |",
        "|---|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for step_key, result in summary["steps"].items():
        if result.get("status") != "FOUND":
            lines.append(f"| {result.get('label', step_key)} | - | SKIPPED | - | - | - | - | - | - | - |")
            continue
        snr = result.get("snr_tia_db")
        snr_text = "-" if snr is None else f"{snr:.2f} dB"
        lines.append(
            "| {label} | {freq} | {flag} | {sat} | {z} | {att:.2f} dB | {i} | {vp} | {vn} | {snr} |".format(
                label=result.get("label", step_key),
                freq=_format_eng(result.get("freq_hz"), "Hz"),
                flag=result.get("bandwidth_flag"),
                sat=result.get("saturation_flag"),
                z=_format_eng(result.get("z_tia_ohm"), "ohm"),
                att=float(result.get("attenuation_vs_low_freq_db", 0.0)),
                i=_format_eng(result.get("current_peak_a"), "A"),
                vp=_format_eng(result.get("v_tone_peak_v"), "V"),
                vn=_format_eng(result.get("v_noise_rms_bin_v"), "V"),
                snr=snr_text,
            )
        )

    lines.extend(
        [
            "",
            "## 3. 结论",
            "",
            "- `TIA_PASSBAND` 表示该频点在当前 TIA 低频有效带宽内。",
            "- `TIA_OUT_OF_BAND` 表示该频点经过当前配置的 Rf/Cf TIA 后会被严重衰减，不应直接作为该 TIA 输出端的控制观测量。",
            "- 当前报告只做一阶估算，暂未加入 PD 结电容、PCB 寄生电容、真实 ADC 输入噪声和输出摆幅实测限制。",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Estimate TIA output visibility for selected findpoint rows.")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
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
    args = parse_config_args(parser, {key: value for key, value in HARDWARE_TIA_ARGS.items()
                                    if key != "rng_seed"}, argv, default_config=HARDWARE_CONFIG)
    if args.project_config.tia.profile != "hardware":
        parser.error("This entry estimates the hardware Rf/Cf/opamp TIA; use spectrum for the VPI TIA")
    return args


def main() -> int:
    args = parse_args()
    save_config_snapshot(args.project_config, args.out_dir / "visibility_config", source=args.config)
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
    output = run_analysis(summary_path=args.summary.resolve(), out_dir=args.out_dir.resolve(), params=params)
    print(f"overall_status={output['overall_status']}")
    print(f"summary={output['summary_path']}")
    print(f"report={output['report_path']}")
    for step_key, result in output["steps"].items():
        if result.get("status") != "FOUND":
            print(f"{step_key}: SKIPPED")
            continue
        print(
            "{label}: {flag}, f={freq:.6g} Hz, Z={z:.6g} ohm, Vpeak={vp:.6g} V, SNR={snr:.3f} dB".format(
                label=result.get("label", step_key),
                flag=result.get("bandwidth_flag"),
                freq=result.get("freq_hz"),
                z=result.get("z_tia_ohm"),
                vp=result.get("v_tone_peak_v"),
                snr=result.get("snr_tia_db"),
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
