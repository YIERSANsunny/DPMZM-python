"""Run the low-frequency DPMZM find-point workflow as a chained offline flow.

This script generates fresh sweep CSV files with the current control-tone
settings and feeds each Step result into the next Step:

    Step 1-I/Q -> Step 2 P extreme -> Step 3 I minimum -> Step 4 Q maximum

It writes a manifest that ``findpoint_validator.py`` uses by default, so stale
2.2 kHz / 2.4 kHz files no longer get picked accidentally after changing the
P-pilot frequency.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DEFAULT_CONFIG, PHYSICAL_ARGS, ROOT, parse_config_args, save_config_snapshot, validate_config
from simulation_validation.findpoint_validator import (
    PROJECT_ROOT,
    STEP_SPECS,
    _summarize_step,
    run_validation,
)


DEFAULT_SIM_ROOT = PROJECT_ROOT
DEFAULT_CHAIN_ROOT = (
    PROJECT_ROOT / "simulation_validation" / "results" / "chained_findpoint_data" / "current"
)


def _format_freq_tag(freq_hz: float) -> str:
    freq = float(freq_hz)
    for scale, suffix in ((1e9, "ghz"), (1e6, "mhz"), (1e3, "khz")):
        if abs(freq) >= scale:
            return f"{freq / scale:g}{suffix}".replace(".", "p")
    return f"{freq:g}hz".replace(".", "p")


def _run_module(sim_root: Path, module: str, args: list[str]) -> None:
    cmd = [sys.executable, "-m", module, *args]
    subprocess.run(cmd, cwd=sim_root, check=True)


def _require_csv(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Expected sweep CSV was not generated: {path}")
    return path


def _summarize_required(
    *,
    step_key: str,
    csv_path: Path,
    edge_points: int,
    major_window_db: float,
) -> dict[str, Any]:
    summary = _summarize_step(
        spec=STEP_SPECS[step_key],
        csv_path=csv_path,
        project_root=PROJECT_ROOT,
        edge_points=edge_points,
        major_window_db=major_window_db,
    )
    if summary.get("status") != "FOUND":
        raise RuntimeError(f"{step_key} failed: {summary}")
    return summary


def _number(summary: dict[str, Any], key: str) -> float:
    value = summary.get(key)
    if value is None:
        raise RuntimeError(f"Missing {key} in step summary: {summary}")
    return float(value)


def _step_payload(csv_path: Path, summary: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "csv_path": str(csv_path),
        "selected_source_V": summary.get("output_value"),
        "selected_effective_V": summary.get("output_effective_value"),
        "selected_index": summary.get("selected_index"),
        "selected_signal_dBm": summary.get("selected_signal_dBm"),
        "selected_noise_floor_dBm": summary.get("selected_noise_floor_dBm"),
        "selected_margin_dB": summary.get("selected_margin_dB"),
    }
    if extra:
        payload.update(extra)
    return payload


def run_chained_findpoint(
    *,
    sim_root: Path,
    chain_root: Path,
    fs: float,
    t_total: float,
    f_i: float,
    f_q: float,
    f_p: float,
    vpi: float,
    er_db: float,
    il_db: float,
    il_i_db: float,
    il_q_db: float,
    il_p_db: float,
    pin_dbm: float,
    responsivity: float,
    pd_tap: float,
    child_source_gain: float,
    parent_source_gain: float,
    step1_i_fixed_q_bias: float,
    step1_i_fixed_p_bias: float,
    step1_q_fixed_i_bias: float,
    step1_q_fixed_p_bias: float,
    i_dither_amp: float,
    q_dither_amp: float,
    p_dither_amp: float,
    edge_points: int,
    major_window_db: float,
    scan_start: float = DEFAULT_CONFIG.findpoint.scan_start_source_v,
    scan_stop: float = DEFAULT_CONFIG.findpoint.scan_stop_source_v,
    scan_step: float = DEFAULT_CONFIG.findpoint.scan_step_source_v,
    er_model: str = DEFAULT_CONFIG.physical.er_model,
    temp_k: float = DEFAULT_CONFIG.physical.temp_k,
    rin_db_hz: float = DEFAULT_CONFIG.physical.rin_db_hz,
    report_dir: Path | None = None,
) -> dict[str, Any]:
    if not sim_root.exists():
        raise FileNotFoundError(f"Simulation repository not found: {sim_root}")

    chain_root.mkdir(parents=True, exist_ok=True)
    step_dirs = {
        "step1_i_bridge": chain_root / "step1_i_bridge",
        "step1_q_bridge": chain_root / "step1_q_bridge",
        "step2_p_extreme": chain_root / "step2_p_extreme",
        "step3_i_min": chain_root / "step3_i_min",
        "step4_q_max": chain_root / "step4_q_max",
    }
    for path in step_dirs.values():
        path.mkdir(parents=True, exist_ok=True)

    i_tag = _format_freq_tag(f_i)
    q_tag = _format_freq_tag(f_q)
    p2_tag = _format_freq_tag(2.0 * f_p)
    beat_tag = _format_freq_tag(f_i + f_p)

    def run_scan(module, arguments):
        axis = {
            "dpmzm.i_pilot_first_sweep": "i", "dpmzm.q_pilot_first_sweep": "q",
            "dpmzm.pilot_beat_sweep": "p", "dpmzm.p_pilot_second_sweep": "i",
        }[module]
        _run_module(sim_root, module, [*arguments,
            f"--{axis}-start", str(scan_start), f"--{axis}-stop", str(scan_stop),
            f"--{axis}-step", str(scan_step), "--er-model", er_model,
            "--temp-k", str(temp_k), "--rin-db-hz", str(rin_db_hz)])

    run_scan(
        "dpmzm.i_pilot_first_sweep",
        [
            "--out-dir",
            str(step_dirs["step1_i_bridge"]),
            "--i-dither-freq",
            str(f_i),
            "--i-dither-amp",
            str(i_dither_amp),
            "--q-bias",
            str(step1_i_fixed_q_bias),
            "--p-bias",
            str(step1_i_fixed_p_bias),
            "--fs",
            str(fs),
            "--t-total",
            str(t_total),
            "--vpi",
            str(vpi),
            "--er-db",
            str(er_db),
            "--il-db",
            str(il_db),
            "--il-i-db",
            str(il_i_db),
            "--il-q-db",
            str(il_q_db),
            "--il-p-db",
            str(il_p_db),
            "--pin-dbm",
            str(pin_dbm),
            "--responsivity",
            str(responsivity),
            "--pd-tap",
            str(pd_tap),
            "--child-source-gain",
            str(child_source_gain),
            "--parent-source-gain",
            str(parent_source_gain),
        ],
    )
    step1_i_csv = _require_csv(
        step_dirs["step1_i_bridge"] / f"i_bias_i_pilot_1st_{i_tag}_sweep.csv"
    )
    step1_i = _summarize_required(
        step_key="step1_i_bridge",
        csv_path=step1_i_csv,
        edge_points=edge_points,
        major_window_db=major_window_db,
    )

    run_scan(
        "dpmzm.q_pilot_first_sweep",
        [
            "--out-dir",
            str(step_dirs["step1_q_bridge"]),
            "--q-dither-freq",
            str(f_q),
            "--q-dither-amp",
            str(q_dither_amp),
            "--i-bias",
            str(step1_q_fixed_i_bias),
            "--p-bias",
            str(step1_q_fixed_p_bias),
            "--fs",
            str(fs),
            "--t-total",
            str(t_total),
            "--vpi",
            str(vpi),
            "--er-db",
            str(er_db),
            "--il-db",
            str(il_db),
            "--il-i-db",
            str(il_i_db),
            "--il-q-db",
            str(il_q_db),
            "--il-p-db",
            str(il_p_db),
            "--pin-dbm",
            str(pin_dbm),
            "--responsivity",
            str(responsivity),
            "--pd-tap",
            str(pd_tap),
            "--child-source-gain",
            str(child_source_gain),
            "--parent-source-gain",
            str(parent_source_gain),
        ],
    )
    step1_q_csv = _require_csv(
        step_dirs["step1_q_bridge"] / f"q_bias_q_pilot_1st_{q_tag}_sweep.csv"
    )
    step1_q = _summarize_required(
        step_key="step1_q_bridge",
        csv_path=step1_q_csv,
        edge_points=edge_points,
        major_window_db=major_window_db,
    )

    v_dci_bridge_source = _number(step1_i, "output_value")
    v_dcq_bridge_source = _number(step1_q, "output_value")
    v_dci_bridge_effective = _number(step1_i, "output_effective_value")
    v_dcq_bridge_effective = _number(step1_q, "output_effective_value")

    # pilot_beat_sweep accepts direct model phase-drive voltages for I/Q, so
    # bridge effective voltages are used here. P is a parent/common-phase source
    # voltage and therefore source == effective in the current model.
    run_scan(
        "dpmzm.pilot_beat_sweep",
        [
            "--out-dir",
            str(step_dirs["step2_p_extreme"]),
            "--v-dci",
            str(v_dci_bridge_effective),
            "--v-dcq",
            str(v_dcq_bridge_effective),
            "--i-dither-freq",
            str(f_i),
            "--i-dither-amp",
            str(i_dither_amp),
            "--p-dither-freq",
            str(f_p),
            "--p-dither-amp",
            str(p_dither_amp),
            "--fs",
            str(fs),
            "--t-total",
            str(t_total),
            "--vpi",
            str(vpi),
            "--er-db",
            str(er_db),
            "--il-db",
            str(il_db),
            "--il-i-db",
            str(il_i_db),
            "--il-q-db",
            str(il_q_db),
            "--il-p-db",
            str(il_p_db),
            "--pin-dbm",
            str(pin_dbm),
            "--responsivity",
            str(responsivity),
            "--pd-tap",
            str(pd_tap),
        ],
    )
    step2_csv = _require_csv(
        step_dirs["step2_p_extreme"] / f"p_bias_{beat_tag}_beat_sweep.csv"
    )
    step2 = _summarize_required(
        step_key="step2_p_extreme",
        csv_path=step2_csv,
        edge_points=edge_points,
        major_window_db=major_window_db,
    )
    v_dcp_extreme = _number(step2, "output_value")

    run_scan(
        "dpmzm.p_pilot_second_sweep",
        [
            "--out-dir",
            str(step_dirs["step3_i_min"]),
            "--q-bias",
            str(v_dcq_bridge_source),
            "--p-bias",
            str(v_dcp_extreme),
            "--p-dither-freq",
            str(f_p),
            "--p-dither-amp",
            str(p_dither_amp),
            "--fs",
            str(fs),
            "--t-total",
            str(t_total),
            "--vpi",
            str(vpi),
            "--er-db",
            str(er_db),
            "--il-db",
            str(il_db),
            "--il-i-db",
            str(il_i_db),
            "--il-q-db",
            str(il_q_db),
            "--il-p-db",
            str(il_p_db),
            "--pin-dbm",
            str(pin_dbm),
            "--responsivity",
            str(responsivity),
            "--pd-tap",
            str(pd_tap),
            "--child-source-gain",
            str(child_source_gain),
            "--parent-source-gain",
            str(parent_source_gain),
        ],
    )
    step3_csv = _require_csv(
        step_dirs["step3_i_min"] / f"i_bias_p_pilot_2nd_{p2_tag}_sweep.csv"
    )
    step3 = _summarize_required(
        step_key="step3_i_min",
        csv_path=step3_csv,
        edge_points=edge_points,
        major_window_db=major_window_db,
    )
    v_dci_min = _number(step3, "output_value")

    run_scan(
        "dpmzm.q_pilot_first_sweep",
        [
            "--out-dir",
            str(step_dirs["step4_q_max"]),
            "--i-bias",
            str(v_dci_min),
            "--p-bias",
            str(v_dcp_extreme),
            "--q-dither-freq",
            str(f_q),
            "--q-dither-amp",
            str(q_dither_amp),
            "--fs",
            str(fs),
            "--t-total",
            str(t_total),
            "--vpi",
            str(vpi),
            "--er-db",
            str(er_db),
            "--il-db",
            str(il_db),
            "--il-i-db",
            str(il_i_db),
            "--il-q-db",
            str(il_q_db),
            "--il-p-db",
            str(il_p_db),
            "--pin-dbm",
            str(pin_dbm),
            "--responsivity",
            str(responsivity),
            "--pd-tap",
            str(pd_tap),
            "--child-source-gain",
            str(child_source_gain),
            "--parent-source-gain",
            str(parent_source_gain),
        ],
    )
    step4_csv = _require_csv(step_dirs["step4_q_max"] / f"q_bias_q_pilot_1st_{q_tag}_sweep.csv")
    step4 = _summarize_required(
        step_key="step4_q_max",
        csv_path=step4_csv,
        edge_points=edge_points,
        major_window_db=major_window_db,
    )

    steps = {
        "step1_i_bridge": _step_payload(step1_i_csv, step1_i),
        "step1_q_bridge": _step_payload(step1_q_csv, step1_q),
        "step2_p_extreme": _step_payload(
            step2_csv,
            step2,
            {
                "fixed_V_DCI_effective": v_dci_bridge_effective,
                "fixed_V_DCQ_effective": v_dcq_bridge_effective,
            },
        ),
        "step3_i_min": _step_payload(
            step3_csv,
            step3,
            {
                "fixed_V_DCQ_source": v_dcq_bridge_source,
                "fixed_V_DCP_source": v_dcp_extreme,
            },
        ),
        "step4_q_max": _step_payload(
            step4_csv,
            step4,
            {
                "fixed_V_DCI_source": v_dci_min,
                "fixed_V_DCP_source": v_dcp_extreme,
            },
        ),
    }

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sim_root": str(sim_root),
        "chain_root": str(chain_root),
        "parameters": {
            "fs": fs,
            "t_total": t_total,
            "f_i": f_i,
            "f_q": f_q,
            "f_p": f_p,
            "f_ip_sum": f_i + f_p,
            "f_p_second": 2.0 * f_p,
            "vpi": vpi,
            "er_db": er_db,
            "il_db": il_db,
            "il_i_db": il_i_db,
            "il_q_db": il_q_db,
            "il_p_db": il_p_db,
            "pin_dbm": pin_dbm,
            "responsivity": responsivity,
            "pd_tap": pd_tap,
            "child_source_gain": child_source_gain,
            "parent_source_gain": parent_source_gain,
            "step1_i_fixed_q_bias": step1_i_fixed_q_bias,
            "step1_i_fixed_p_bias": step1_i_fixed_p_bias,
            "step1_q_fixed_i_bias": step1_q_fixed_i_bias,
            "step1_q_fixed_p_bias": step1_q_fixed_p_bias,
            "i_dither_amp_source_vpeak": i_dither_amp,
            "q_dither_amp_source_vpeak": q_dither_amp,
            "p_dither_amp_source_vpeak": p_dither_amp,
            "edge_points": edge_points,
            "major_window_db": major_window_db,
            "scan_start_source_v": scan_start,
            "scan_stop_source_v": scan_stop,
            "scan_step_source_v": scan_step,
            "er_model": er_model,
            "temp_k": temp_k,
            "rin_db_hz": rin_db_hz,
        },
        "steps": steps,
    }
    manifest_path = chain_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    validation = run_validation(
        project_root=PROJECT_ROOT,
        out_dir=report_dir or PROJECT_ROOT / "simulation_validation" / "results",
        edge_points=edge_points,
        major_window_db=major_window_db,
        overrides={
            "step1_i_bridge": step1_i_csv,
            "step1_q_bridge": step1_q_csv,
            "step2_p_extreme": step2_csv,
            "step3_i_min": step3_csv,
            "step4_q_max": step4_csv,
        },
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["validation_summary_path"] = validation.get("summary_path")
    manifest["validation_report_path"] = validation.get("report_path")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run chained DPMZM low-frequency find-point sweeps.")
    parser.add_argument("--sim-root", type=Path, default=DEFAULT_SIM_ROOT)
    parser.add_argument("--chain-root", type=Path, default=DEFAULT_CHAIN_ROOT)
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--fs", type=float)
    parser.add_argument("--t-total", type=float)
    parser.add_argument("--f-i", type=float)
    parser.add_argument("--f-q", type=float)
    parser.add_argument("--f-p", type=float)
    parser.add_argument("--vpi", type=float)
    parser.add_argument("--er-db", type=float)
    parser.add_argument("--il-db", type=float)
    parser.add_argument("--il-i-db", type=float)
    parser.add_argument("--il-q-db", type=float)
    parser.add_argument("--il-p-db", type=float)
    parser.add_argument("--pin-dbm", type=float)
    parser.add_argument("--responsivity", type=float)
    parser.add_argument("--pd-tap", type=float)
    parser.add_argument("--child-source-gain", type=float)
    parser.add_argument("--parent-source-gain", type=float)
    parser.add_argument("--er-model", choices=("vpi", "thesis"))
    parser.add_argument("--rin-db-hz", type=float)
    parser.add_argument("--temp-k", type=float)
    parser.add_argument("--step1-i-fixed-q-bias", type=float)
    parser.add_argument("--step1-i-fixed-p-bias", type=float)
    parser.add_argument("--step1-q-fixed-i-bias", type=float)
    parser.add_argument("--step1-q-fixed-p-bias", type=float)
    parser.add_argument("--i-dither-amp", type=float)
    parser.add_argument("--q-dither-amp", type=float)
    parser.add_argument("--p-dither-amp", type=float)
    parser.add_argument("--scan-start", type=float)
    parser.add_argument("--scan-stop", type=float)
    parser.add_argument("--scan-step", type=float)
    parser.add_argument("--edge-points", type=int)
    parser.add_argument("--major-window-db", type=float)
    return parser


def parse_args(argv=None):
    parser = build_parser()
    args = parse_config_args(parser, {
        **PHYSICAL_ARGS, "fs": "sampling.fs_hz", "t_total": "sampling.t_total_s",
        "f_i": "drive.f_i_hz", "f_q": "drive.f_q_hz", "f_p": "drive.f_p_hz",
        "i_dither_amp": "drive.i_dither_source_amp_vpeak",
        "q_dither_amp": "drive.q_dither_source_amp_vpeak",
        "p_dither_amp": "findpoint.p_dither_source_amp_vpeak",
        "step1_i_fixed_q_bias": "findpoint.step1_i_fixed_q_bias",
        "step1_q_fixed_i_bias": "findpoint.step1_q_fixed_i_bias",
        "scan_start": "findpoint.scan_start_source_v", "scan_stop": "findpoint.scan_stop_source_v",
        "scan_step": "findpoint.scan_step_source_v", "edge_points": "findpoint.edge_points",
        "major_window_db": "findpoint.major_window_db",
    }, argv, default_config=ROOT / "configs" / "findpoint.json")
    cfg = args.project_config
    for source_field, phase_field in (
        ("step1_i_fixed_p_bias", "step1_i_fixed_p_phase_deg"),
        ("step1_q_fixed_p_bias", "step1_q_fixed_p_phase_deg"),
    ):
        voltage = getattr(args, source_field)
        if voltage is None:
            setattr(args, source_field, cfg.p_source_voltage(getattr(cfg.findpoint, phase_field)))
        else:
            phase = 180.0 * cfg.physical.parent_source_gain * voltage / cfg.physical.vpi_v
            cfg = replace(cfg, findpoint=replace(cfg.findpoint, **{phase_field: phase}))
    try:
        args.project_config = validate_config(cfg)
    except ValueError as exc:
        parser.error(str(exc))
    return args


def main() -> int:
    args = parse_args()
    save_config_snapshot(args.project_config, args.chain_root, source=args.config)
    manifest = run_chained_findpoint(
        sim_root=args.sim_root.resolve(),
        chain_root=args.chain_root.resolve(),
        fs=args.fs,
        t_total=args.t_total,
        f_i=args.f_i,
        f_q=args.f_q,
        f_p=args.f_p,
        vpi=args.vpi,
        er_db=args.er_db,
        il_db=args.il_db,
        il_i_db=args.il_i_db,
        il_q_db=args.il_q_db,
        il_p_db=args.il_p_db,
        pin_dbm=args.pin_dbm,
        responsivity=args.responsivity,
        pd_tap=args.pd_tap,
        child_source_gain=args.child_source_gain,
        parent_source_gain=args.parent_source_gain,
        step1_i_fixed_q_bias=args.step1_i_fixed_q_bias,
        step1_i_fixed_p_bias=args.step1_i_fixed_p_bias,
        step1_q_fixed_i_bias=args.step1_q_fixed_i_bias,
        step1_q_fixed_p_bias=args.step1_q_fixed_p_bias,
        i_dither_amp=args.i_dither_amp,
        q_dither_amp=args.q_dither_amp,
        p_dither_amp=args.p_dither_amp,
        edge_points=args.edge_points,
        major_window_db=args.major_window_db,
        scan_start=args.scan_start, scan_stop=args.scan_stop, scan_step=args.scan_step,
        er_model=args.er_model, temp_k=args.temp_k, rin_db_hz=args.rin_db_hz,
        report_dir=args.report_dir,
    )
    print(f"manifest={manifest['manifest_path']}")
    print(f"validation_summary={manifest['validation_summary_path']}")
    for key, payload in manifest["steps"].items():
        print(
            "{key}: source={source}, effective={effective}, csv={csv}".format(
                key=key,
                source=payload.get("selected_source_V"),
                effective=payload.get("selected_effective_V"),
                csv=payload.get("csv_path"),
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
