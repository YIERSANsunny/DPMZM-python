"""Offline validator for the DPMZM Step 1-4 bias finding workflow.

The script reads existing sweep CSV files, applies the workflow criteria, and
writes a JSON summary plus a Markdown report. It intentionally stays small and
stdlib-only so it can run before the control codebase is built.
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
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from config import ROOT, parse_config_args, save_config_snapshot

DEFAULT_CHAIN_MANIFEST = (
    PROJECT_ROOT
    / "simulation_validation"
    / "results"
    / "chained_findpoint_data"
    / "current"
    / "manifest.json"
)

EXTERNAL_I_FIRST_CANDIDATES = [
    PROJECT_ROOT / "artifacts" / "dpmzm_i_pilot_first_q1527_pminus01_12g"
    / "i_bias_i_pilot_1st_12ghz_sweep.csv"
]


@dataclass(frozen=True)
class StepSpec:
    key: str
    label: str
    output_name: str
    x_candidates: tuple[str, ...]
    effective_candidates: tuple[str, ...]
    signal_candidates: tuple[str, ...]
    noise_candidates: tuple[str, ...]
    pd_candidates: tuple[str, ...]
    kind: str
    selection: str = "best"


STEP_SPECS = {
    "step1_i_bridge": StepSpec(
        key="step1_i_bridge",
        label="Step 1-I：I 路 bridge",
        output_name="V_DCI_bridge",
        x_candidates=("V_DCI_source_V", "V_DCI_V", "V_DCI"),
        effective_candidates=("V_DCI_effective_V",),
        signal_candidates=("P_tone_signal_dBm", "P_1f_signal_dBm"),
        noise_candidates=("P_noise_floor_dBm",),
        pd_candidates=("P_pd_avg_dBm",),
        kind="max",
    ),
    "step1_q_bridge": StepSpec(
        key="step1_q_bridge",
        label="Step 1-Q：Q 路 bridge",
        output_name="V_DCQ_bridge",
        x_candidates=("V_DCQ_source_V", "V_DCQ_V", "V_DCQ"),
        effective_candidates=("V_DCQ_effective_V",),
        signal_candidates=("P_tone_signal_dBm", "P_1f_signal_dBm"),
        noise_candidates=("P_noise_floor_dBm",),
        pd_candidates=("P_pd_avg_dBm",),
        kind="max",
    ),
    "step2_p_extreme": StepSpec(
        key="step2_p_extreme",
        label="Step 2：P 路极值点",
        output_name="V_DCP_extreme",
        x_candidates=("V_DCP_V", "V_DCP_source_V", "V_DCP"),
        effective_candidates=("V_DCP_effective_V",),
        signal_candidates=(
            "P_tone_signal_dBm",
            "P_2p2k_signal_dBm",
            "P_tone_measured_dBm",
            "P_2p2k_measured_dBm",
        ),
        noise_candidates=("P_noise_floor_dBm",),
        pd_candidates=("P_pd_avg_dBm",),
        kind="min",
    ),
    "step3_i_min": StepSpec(
        key="step3_i_min",
        label="Step 3：I 路最小点",
        output_name="V_DCI_min",
        x_candidates=("V_DCI_source_V", "V_DCI_V", "V_DCI"),
        effective_candidates=("V_DCI_effective_V",),
        signal_candidates=("P_tone_signal_dBm", "P_2f_signal_dBm"),
        noise_candidates=("P_noise_floor_dBm",),
        pd_candidates=("P_pd_avg_dBm",),
        kind="min",
    ),
    "step4_q_max": StepSpec(
        key="step4_q_max",
        label="Step 4：Q 路最大点",
        output_name="V_DCQ_max",
        x_candidates=("V_DCQ_source_V", "V_DCQ_V", "V_DCQ"),
        effective_candidates=("V_DCQ_effective_V",),
        signal_candidates=("P_tone_signal_dBm", "P_1f_signal_dBm"),
        noise_candidates=("P_noise_floor_dBm",),
        pd_candidates=("P_pd_avg_dBm",),
        kind="min",
        selection="min_then_high_pd",
    ),
}


def _is_finite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _read_numeric_csv(path: Path) -> dict[str, list[float]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        columns: dict[str, list[float]] = {name: [] for name in reader.fieldnames}
        for row in reader:
            for name in columns:
                columns[name].append(_to_float(row.get(name, "")))
    return columns


def _pick_column(columns: dict[str, list[float]], candidates: Iterable[str]) -> str | None:
    for name in candidates:
        if name in columns:
            return name
    return None


def _glob_first(root: Path, patterns: Iterable[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(root.glob(pattern))
        if matches:
            return matches[0]
    return None


def _manifest_paths(project_root: Path) -> dict[str, Path]:
    manifest_path = project_root / DEFAULT_CHAIN_MANIFEST.relative_to(PROJECT_ROOT)
    if not manifest_path.exists():
        return {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    steps = manifest.get("steps", {})
    if not isinstance(steps, dict):
        return {}

    paths: dict[str, Path] = {}
    for key, payload in steps.items():
        if not isinstance(payload, dict):
            continue
        csv_path = payload.get("csv_path")
        if not isinstance(csv_path, str) or not csv_path:
            continue
        path = Path(csv_path)
        if path.exists():
            paths[str(key)] = path
    return paths


def _default_paths(project_root: Path) -> dict[str, Path | None]:
    paths: dict[str, Path | None] = {
        "step1_i_bridge": _glob_first(
            project_root,
            (
                "I路一阶/*khz*.csv",
                "I路一阶/*i_pilot_1st*.csv",
                "I路一阶/*pilot_1st*.csv",
                "I路一阶/*.csv",
            ),
        ),
        "step1_q_bridge": _glob_first(
            project_root,
            (
                "Q路一阶/*khz*.csv",
                "Q路一阶/*q_pilot_1st*.csv",
                "Q路一阶/*pilot_1st*.csv",
                "Q路一阶/*.csv",
            ),
        ),
        "step2_p_extreme": _glob_first(
            project_root,
            (
                "I_P交调/TIA低频/*beat_sweep.csv",
                "I_P交调/*beat_sweep.csv",
                "I_P交调/*.csv",
            ),
        ),
        "step3_i_min": _glob_first(
            project_root,
            (
                "P路二阶/*khz*.csv",
                "P路二阶/*p_pilot_2nd*.csv",
                "P路二阶/*.csv",
            ),
        ),
        "step4_q_max": _glob_first(
            project_root,
            (
                "Q路一阶/*khz*.csv",
                "Q路一阶/*q_pilot_1st*.csv",
                "Q路一阶/*pilot_1st*.csv",
                "Q路一阶/*.csv",
            ),
        ),
    }

    if paths["step1_i_bridge"] is None:
        for candidate in EXTERNAL_I_FIRST_CANDIDATES:
            if candidate.exists():
                paths["step1_i_bridge"] = candidate
                break

    for key, path in _manifest_paths(project_root).items():
        paths[key] = path

    return paths


def _valid_indices(n: int, edge_points: int) -> list[int]:
    if n <= 0:
        return []
    start = max(0, int(edge_points))
    stop = max(start, n - max(0, int(edge_points)))
    if start >= stop:
        return list(range(n))
    return list(range(start, stop))


def _local_extrema(values: list[float], *, kind: str, edge_points: int) -> list[int]:
    n = len(values)
    if n < 3:
        return _valid_indices(n, edge_points)

    valid = set(_valid_indices(n, edge_points))
    indices: list[int] = []
    for i in range(1, n - 1):
        if i not in valid:
            continue
        y0, y1, y2 = values[i - 1], values[i], values[i + 1]
        if not (_is_finite(y0) and _is_finite(y1) and _is_finite(y2)):
            continue
        if kind == "max" and ((y1 > y0 and y1 >= y2) or (y1 >= y0 and y1 > y2)):
            indices.append(i)
        elif kind == "min" and ((y1 < y0 and y1 <= y2) or (y1 <= y0 and y1 < y2)):
            indices.append(i)
    return indices


def _best_index(values: list[float], indices: list[int], *, kind: str) -> int | None:
    finite_indices = [i for i in indices if _is_finite(values[i])]
    if not finite_indices:
        return None
    if kind == "max":
        return max(finite_indices, key=lambda i: values[i])
    if kind == "min":
        return min(finite_indices, key=lambda i: values[i])
    raise ValueError(f"Unknown extrema kind: {kind}")


def _major_indices(
    values: list[float],
    indices: list[int],
    *,
    kind: str,
    window_db: float,
) -> list[int]:
    best = _best_index(values, indices, kind=kind)
    if best is None:
        return []
    best_value = values[best]
    if kind == "max":
        return [i for i in indices if _is_finite(values[i]) and values[i] >= best_value - window_db]
    return [i for i in indices if _is_finite(values[i]) and values[i] <= best_value + window_db]


def _value_at(columns: dict[str, list[float]], name: str | None, idx: int) -> float | None:
    if name is None:
        return None
    values = columns.get(name)
    if values is None or idx >= len(values):
        return None
    value = values[idx]
    return float(value) if _is_finite(value) else None


def _round_or_none(value: float | None, digits: int = 6) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(float(value), digits)


def _path_source(path: Path, project_root: Path) -> str:
    try:
        path.resolve().relative_to(project_root.resolve())
        return "project"
    except ValueError:
        return "external"


def _summarize_step(
    *,
    spec: StepSpec,
    csv_path: Path | None,
    project_root: Path,
    edge_points: int,
    major_window_db: float,
) -> dict[str, object]:
    if csv_path is None:
        return {
            "status": "MISSING",
            "label": spec.label,
            "output_name": spec.output_name,
            "message": "未找到输入 CSV",
        }
    if not csv_path.exists():
        return {
            "status": "MISSING",
            "label": spec.label,
            "output_name": spec.output_name,
            "csv_path": str(csv_path),
            "message": "输入 CSV 路径不存在",
        }

    columns = _read_numeric_csv(csv_path)
    x_col = _pick_column(columns, spec.x_candidates)
    signal_col = _pick_column(columns, spec.signal_candidates)
    noise_col = _pick_column(columns, spec.noise_candidates)
    pd_col = _pick_column(columns, spec.pd_candidates)
    effective_col = _pick_column(columns, spec.effective_candidates)

    if x_col is None or signal_col is None:
        return {
            "status": "INVALID",
            "label": spec.label,
            "output_name": spec.output_name,
            "csv_path": str(csv_path),
            "available_columns": list(columns.keys()),
            "message": "缺少偏置列或信号功率列",
        }

    x_values = columns[x_col]
    y_values = columns[signal_col]
    n = min(len(x_values), len(y_values))
    candidate_indices = _local_extrema(y_values[:n], kind=spec.kind, edge_points=edge_points)

    selection_note = "local_extrema"
    if not candidate_indices:
        candidate_indices = _valid_indices(n, edge_points)
        selection_note = "fallback_global_after_edge_exclusion"

    major = _major_indices(
        y_values[:n],
        candidate_indices,
        kind=spec.kind,
        window_db=float(major_window_db),
    )
    if not major:
        major = candidate_indices

    if spec.selection == "min_then_high_pd" and pd_col is not None:
        finite_pd_major = [i for i in major if _is_finite(_value_at(columns, pd_col, i))]
        if finite_pd_major:
            selected = max(finite_pd_major, key=lambda i: columns[pd_col][i])
            selection_note = "major_minimum_then_highest_pd_dc"
        else:
            selected = _best_index(y_values[:n], major, kind=spec.kind)
            selection_note = "major_minimum_pd_missing_fallback"
    else:
        selected = _best_index(y_values[:n], major, kind=spec.kind)

    if selected is None:
        return {
            "status": "INVALID",
            "label": spec.label,
            "output_name": spec.output_name,
            "csv_path": str(csv_path),
            "message": "没有可用的有限数值候选点",
        }

    x_value = _value_at(columns, x_col, selected)
    effective_value = _value_at(columns, effective_col, selected)
    signal_value = _value_at(columns, signal_col, selected)
    noise_value = _value_at(columns, noise_col, selected)
    pd_value = _value_at(columns, pd_col, selected)
    margin = signal_value - noise_value if signal_value is not None and noise_value is not None else None
    csv_source = _path_source(csv_path, project_root)

    quality_flags: list[str] = []
    if csv_source == "external":
        quality_flags.append("EXTERNAL_CSV")
    if margin is not None:
        if margin < 0.0:
            quality_flags.append("SIGNAL_BELOW_NOISE_FLOOR")
        elif margin < 3.0:
            quality_flags.append("LOW_MARGIN_LT_3DB")
    if selection_note.startswith("fallback"):
        quality_flags.append("FALLBACK_SELECTION")

    sorted_candidates = sorted(
        major,
        key=lambda i: (
            columns[pd_col][i] if spec.selection == "min_then_high_pd" and pd_col is not None else y_values[i]
        ),
        reverse=spec.kind == "max" or spec.selection == "min_then_high_pd",
    )
    if spec.kind == "min" and spec.selection != "min_then_high_pd":
        sorted_candidates = sorted(major, key=lambda i: y_values[i])

    candidate_preview = []
    for i in sorted_candidates[:8]:
        candidate_preview.append(
            {
                "index": int(i),
                x_col: _round_or_none(_value_at(columns, x_col, i)),
                "effective_V": _round_or_none(_value_at(columns, effective_col, i)),
                "signal_dBm": _round_or_none(_value_at(columns, signal_col, i)),
                "noise_floor_dBm": _round_or_none(_value_at(columns, noise_col, i)),
                "margin_dB": _round_or_none(
                    (
                        _value_at(columns, signal_col, i) - _value_at(columns, noise_col, i)
                        if _value_at(columns, signal_col, i) is not None
                        and _value_at(columns, noise_col, i) is not None
                        else None
                    )
                ),
                "pd_avg_dBm": _round_or_none(_value_at(columns, pd_col, i)),
            }
        )

    return {
        "status": "FOUND",
        "label": spec.label,
        "output_name": spec.output_name,
        "output_value": _round_or_none(x_value),
        "output_effective_value": _round_or_none(effective_value),
        "csv_path": str(csv_path),
        "csv_source": csv_source,
        "row_count": int(n),
        "x_column": x_col,
        "effective_column": effective_col,
        "signal_column": signal_col,
        "noise_column": noise_col,
        "pd_column": pd_col,
        "selected_index": int(selected),
        "selected_signal_dBm": _round_or_none(signal_value),
        "selected_noise_floor_dBm": _round_or_none(noise_value),
        "selected_margin_dB": _round_or_none(margin),
        "selected_pd_avg_dBm": _round_or_none(pd_value),
        "local_candidate_count": int(len(candidate_indices)),
        "major_candidate_count": int(len(major)),
        "selection_note": selection_note,
        "quality_flags": quality_flags,
        "candidate_preview": candidate_preview,
    }


def _markdown_value(value: object) -> str:
    if value is None:
        return "-"
    return str(value)


def _write_report(summary: dict[str, object], path: Path) -> None:
    steps = summary["steps"]
    assert isinstance(steps, dict)

    lines = [
        "# 找点流程离线仿真验证报告",
        "",
        f"生成时间：{summary['generated_at']}",
        "",
        f"总状态：`{summary['overall_status']}`",
        "",
        "## 1. 输出状态变量",
        "",
        "| 变量 | 数值 source V | effective V | 来源 Step |",
        "|---|---:|---:|---|",
    ]

    final_state = summary["final_state"]
    assert isinstance(final_state, dict)
    for name, payload in final_state.items():
        assert isinstance(payload, dict)
        lines.append(
            "| {name} | {source} | {effective} | {step} |".format(
                name=name,
                source=_markdown_value(payload.get("source_V")),
                effective=_markdown_value(payload.get("effective_V")),
                step=_markdown_value(payload.get("step")),
            )
        )

    lines.extend(
        [
            "",
            "## 2. Step 结果",
            "",
            "| Step | 状态 | 输出 | source V | effective V | 信号 dBm | 噪声底 dBm | 裕量 dB | PD 直流 dBm | 数据来源 | 质量标记 |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for key, payload_obj in steps.items():
        payload = payload_obj
        assert isinstance(payload, dict)
        lines.append(
            "| {label} | {status} | {out} | {source_v} | {eff_v} | {sig} | {noise} | {margin} | {pd} | {source} | {flags} |".format(
                label=payload.get("label", key),
                status=payload.get("status", "-"),
                out=payload.get("output_name", "-"),
                source_v=_markdown_value(payload.get("output_value")),
                eff_v=_markdown_value(payload.get("output_effective_value")),
                sig=_markdown_value(payload.get("selected_signal_dBm")),
                noise=_markdown_value(payload.get("selected_noise_floor_dBm")),
                margin=_markdown_value(payload.get("selected_margin_dB")),
                pd=_markdown_value(payload.get("selected_pd_avg_dBm")),
                source=payload.get("csv_source", "-"),
                flags=", ".join(payload.get("quality_flags", [])) or "-",
            )
        )

    lines.extend(["", "## 3. 输入 CSV", ""])
    for key, payload_obj in steps.items():
        payload = payload_obj
        assert isinstance(payload, dict)
        lines.append(f"- {payload.get('label', key)}：`{payload.get('csv_path', payload.get('message', '-'))}`")

    external_steps = [
        str(payload.get("label"))
        for payload in steps.values()
        if isinstance(payload, dict) and payload.get("csv_source") == "external"
    ]
    if external_steps:
        lines.extend(
            [
                "",
                "## 4. 注意事项",
                "",
                "- 以下步骤使用了项目目录外部的历史仿真 CSV：" + "、".join(external_steps),
                "- 后续建议把对应 CSV 复制或重新生成到本项目的数据目录中，使仿真验证完全自洽。",
            ]
        )

    flagged_steps = [
        f"{payload.get('label')}：{', '.join(payload.get('quality_flags', []))}"
        for payload in steps.values()
        if isinstance(payload, dict) and payload.get("quality_flags")
    ]
    if flagged_steps:
        lines.extend(["", "质量提示："])
        for item in flagged_steps:
            lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## 5. 判据说明",
            "",
            "- Step 1：在一阶导频功率局部最大值中选择主峰。",
            "- Step 2：在 I-P 交调功率局部最小值中选择主谷。",
            "- Step 3：在 P 路二阶功率局部最小值中选择主谷。",
            "- Step 4：先取 Q 路一阶功率主谷候选，再选择 PD 直流功率较高的候选点。",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_validation(
    *,
    project_root: Path,
    out_dir: Path,
    edge_points: int,
    major_window_db: float,
    overrides: dict[str, Path | None],
) -> dict[str, object]:
    paths = _default_paths(project_root)
    for key, value in overrides.items():
        if value is not None:
            paths[key] = value

    steps: dict[str, object] = {}
    for key, spec in STEP_SPECS.items():
        steps[key] = _summarize_step(
            spec=spec,
            csv_path=paths.get(key),
            project_root=project_root,
            edge_points=edge_points,
            major_window_db=major_window_db,
        )

    final_state: dict[str, dict[str, object]] = {}
    for key, payload_obj in steps.items():
        if not isinstance(payload_obj, dict) or payload_obj.get("status") != "FOUND":
            continue
        output_name = str(payload_obj["output_name"])
        final_state[output_name] = {
            "source_V": payload_obj.get("output_value"),
            "effective_V": payload_obj.get("output_effective_value"),
            "step": payload_obj.get("label"),
        }

    missing_or_invalid = [
        key
        for key, payload_obj in steps.items()
        if not isinstance(payload_obj, dict) or payload_obj.get("status") != "FOUND"
    ]
    quality_flags = {
        key: payload_obj.get("quality_flags", [])
        for key, payload_obj in steps.items()
        if isinstance(payload_obj, dict) and payload_obj.get("quality_flags")
    }
    if missing_or_invalid:
        overall_status = "PARTIAL"
    elif quality_flags:
        overall_status = "COMPLETE_WITH_WARNINGS"
    else:
        overall_status = "COMPLETE"

    summary: dict[str, object] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(project_root),
        "overall_status": overall_status,
        "missing_or_invalid_steps": missing_or_invalid,
        "quality_flags": quality_flags,
        "parameters": {
            "edge_points": int(edge_points),
            "major_window_db": float(major_window_db),
        },
        "steps": steps,
        "final_state": final_state,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "findpoint_summary.json"
    report_path = out_dir / "findpoint_report.md"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(summary, report_path)

    summary["summary_path"] = str(summary_path)
    summary["report_path"] = str(report_path)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate DPMZM Step 1-4 bias finding from CSV sweeps.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "simulation_validation" / "results")
    parser.add_argument("--edge-points", type=int)
    parser.add_argument("--major-window-db", type=float)
    parser.add_argument("--i-first-csv", type=Path, default=None)
    parser.add_argument("--q-first-csv", type=Path, default=None)
    parser.add_argument("--ip-csv", type=Path, default=None)
    parser.add_argument("--p-second-csv", type=Path, default=None)
    parser.add_argument("--q-max-csv", type=Path, default=None)
    return parser


def parse_args(argv=None):
    return parse_config_args(build_parser(), dict(edge_points="findpoint.edge_points",
        major_window_db="findpoint.major_window_db"), argv,
        default_config=ROOT / "configs" / "findpoint.json")


def main() -> int:
    args = parse_args()
    save_config_snapshot(args.project_config, args.out_dir / "findpoint_config", source=args.config)
    overrides = {
        "step1_i_bridge": args.i_first_csv,
        "step1_q_bridge": args.q_first_csv,
        "step2_p_extreme": args.ip_csv,
        "step3_i_min": args.p_second_csv,
        "step4_q_max": args.q_max_csv if args.q_max_csv is not None else args.q_first_csv,
    }
    summary = run_validation(
        project_root=args.project_root.resolve(),
        out_dir=args.out_dir.resolve(),
        edge_points=args.edge_points,
        major_window_db=args.major_window_db,
        overrides=overrides,
    )

    print(f"overall_status={summary['overall_status']}")
    print(f"summary={summary['summary_path']}")
    print(f"report={summary['report_path']}")
    final_state = summary["final_state"]
    assert isinstance(final_state, dict)
    for name, payload in final_state.items():
        assert isinstance(payload, dict)
        print(f"{name}={payload.get('source_V')} source V, effective={payload.get('effective_V')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
