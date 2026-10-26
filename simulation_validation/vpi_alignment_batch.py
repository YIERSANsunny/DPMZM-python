"""Batch-match VPI cursor readings against offline simulation outputs.

Input is a CSV table with one VPI point per row.  The script calls
``vpi_alignment_checker.py`` for each enabled row and writes a compact summary
CSV/JSON/Markdown report.  This is the intended workflow once we have multiple
VPI screenshots or exported cursor values to compare.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from typing import Any

import vpi_alignment_checker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "simulation_validation" / "vpi_reference_points_template.csv"
DEFAULT_OUT = PROJECT_ROOT / "simulation_validation" / "results" / "vpi_alignment_batch"


def _to_float(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


def _to_int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_path(value: Any) -> Path | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return Path(text)


def _enabled(value: Any) -> bool:
    text = str(value).strip().lower()
    return text not in {"0", "false", "no", "n", "off", "skip"}


def _read_points(path: Path) -> list[dict[str, str]]:
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


def _candidate_convention(source: Any, candidate: Any) -> str:
    text = str(candidate or "").strip()
    for token in (" direct ", " derived "):
        text = text.replace(token, " ")
    text = " ".join(text.split())
    return f"{source or '-'} | {text or '-'}"


def _summarize_conventions(
    rows: list[dict[str, Any]],
    *,
    lock_threshold_db: float,
    min_points_for_lock: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[float]] = {}
    examples: dict[str, str] = {}
    for row in rows:
        error = _to_float(row.get("best_abs_error_dB"))
        if error is None:
            continue
        key = _candidate_convention(row.get("best_source"), row.get("best_candidate"))
        grouped.setdefault(key, []).append(error)
        examples.setdefault(key, str(row.get("best_candidate", "")))

    stats: list[dict[str, Any]] = []
    for key, values in grouped.items():
        stats.append(
            {
                "convention": key,
                "example_candidate": examples.get(key, ""),
                "count": len(values),
                "mean_abs_error_dB": round(sum(values) / len(values), 9),
                "max_abs_error_dB": round(max(values), 9),
            }
        )
    stats.sort(key=lambda item: (-int(item["count"]), float(item["mean_abs_error_dB"])))

    total = sum(int(item["count"]) for item in stats)
    if total == 0:
        status = "NO_POINTS"
        locked = ""
    elif total < int(min_points_for_lock):
        status = "INSUFFICIENT_POINTS"
        locked = str(stats[0]["convention"]) if stats else ""
    elif len(stats) == 1 and float(stats[0]["max_abs_error_dB"]) <= float(lock_threshold_db):
        status = "LOCKED"
        locked = str(stats[0]["convention"])
    elif len(stats) == 1:
        status = "CONSISTENT_BUT_HIGH_ERROR"
        locked = str(stats[0]["convention"])
    else:
        status = "MIXED_CONVENTIONS"
        locked = str(stats[0]["convention"]) if stats else ""

    decision = {
        "status": status,
        "locked_or_leading_convention": locked,
        "point_count": total,
        "min_points_for_lock": int(min_points_for_lock),
        "lock_threshold_db": float(lock_threshold_db),
    }
    return stats, decision


def _write_report(
    path: Path,
    rows: list[dict[str, Any]],
    input_path: Path,
    convention_stats: list[dict[str, Any]],
    convention_decision: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# VPI Alignment Batch Report",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"Input: `{input_path}`",
        f"Convention status: `{convention_decision.get('status', '-')}`",
        f"Leading convention: `{convention_decision.get('locked_or_leading_convention', '-')}`",
        f"Lock rule: `{convention_decision.get('min_points_for_lock', '-')} points minimum, max abs error <= {convention_decision.get('lock_threshold_db', '-')} dB`",
        "",
        "| Case | Step | Bias | VPI value | Expected load | VPI formula | Expected column | Best source | Best candidate | Best load | Offline value | Error | Abs error |",
        "|---|---|---:|---:|---:|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {case_id} | {step} | {bias} | {vpi} | {expected_load} | {vpi_formula} | {expected_column} | {source} | {candidate} | {best_load} | {value} | {error} | {abs_error} |".format(
                case_id=row.get("case_id", "-"),
                step=row.get("step", "-"),
                bias=row.get("bias", "-"),
                vpi=row.get("vpi_value", "-"),
                expected_load=row.get("expected_load_ohm", "-"),
                vpi_formula=row.get("vpi_formula", "-"),
                expected_column=row.get("expected_python_column", "-"),
                source=row.get("best_source", "-"),
                candidate=row.get("best_candidate", "-"),
                best_load=row.get("best_load_ohm", "-"),
                value=row.get("best_value_dB", "-"),
                error=row.get("best_error_dB", "-"),
                abs_error=row.get("best_abs_error_dB", "-"),
            )
        )
    lines.extend(
        [
            "",
            "## Convention Summary",
            "",
            "| Convention | Count | Mean abs error | Max abs error | Example candidate |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for item in convention_stats:
        lines.append(
            "| {convention} | {count} | {mean:.3f} dB | {maxerr:.3f} dB | {example} |".format(
                convention=item.get("convention", "-"),
                count=item.get("count", "-"),
                mean=float(item.get("mean_abs_error_dB", 0.0)),
                maxerr=float(item.get("max_abs_error_dB", 0.0)),
                example=item.get("example_candidate", "-"),
            )
        )
    lines.extend(
        [
            "",
            "## Reading Rules",
            "",
            "- When `expected_load_ohm` is filled, the matching result excludes candidates using other loads.",
            "- `TIA single RMS direct 50ohm` currently means the VPI value is closest to a single-ended TIA output interpreted as 50-ohm equivalent RMS power.",
            "- `TIA diff RMS direct 1ohm` means the VPI value is closest to a differential TIA RMS voltage processed as `10log10(V^2)+30`.",
            "- `ADC clipped RMS direct 50ohm` means the VPI value is closest to the ADC-facing clipped fundamental.",
            "- Use consistent winning candidates across multiple VPI points before declaring the readout convention locked.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_path = args.input.resolve()
    out_dir = args.out_dir.resolve()
    case_out_dir = out_dir / "cases"
    rows = _read_points(input_path)

    summary_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not _enabled(row.get("enabled", "1")):
            continue
        step = (row.get("step") or "").strip()
        vpi_value = _to_float(row.get("vpi_value"))
        if not step or vpi_value is None:
            continue
        case_id = (row.get("case_id") or f"case_{index:03d}").strip()
        bias = _to_float(row.get("bias"))
        row_index = _to_int(row.get("row_index"))
        expected_load_ohm = _to_float(row.get("expected_load_ohm"))

        result = vpi_alignment_checker.run(
            Namespace(
                case_id=case_id,
                step=step,
                vpi_value=vpi_value,
                expected_load_ohm=expected_load_ohm,
                bias=bias,
                row_index=row_index,
                tia_csv=_to_path(row.get("tia_csv")),
                adc_csv=_to_path(row.get("adc_csv")),
                out_dir=case_out_dir,
            )
        )
        best = result.get("best") or {}
        summary_rows.append(
            {
                "case_id": case_id,
                "step": step,
                "bias": "" if bias is None else bias,
                "row_index": "" if row_index is None else row_index,
                "vpi_value": vpi_value,
                "expected_load_ohm": "" if expected_load_ohm is None else expected_load_ohm,
                "analyzer_connection": row.get("analyzer_connection", ""),
                "vpi_formula": row.get("vpi_formula", ""),
                "expected_python_column": row.get("expected_python_column", ""),
                "best_source": best.get("source", ""),
                "best_candidate": best.get("candidate", ""),
                "best_load_ohm": best.get("load_ohm", ""),
                "best_value_dB": best.get("candidate_value_dB", ""),
                "best_error_dB": best.get("error_dB", ""),
                "best_abs_error_dB": best.get("abs_error_dB", ""),
                "case_report": result.get("report_path", ""),
                "case_csv": result.get("csv_path", ""),
                "note": row.get("note", ""),
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = out_dir / "vpi_alignment_batch_summary.csv"
    summary_json = out_dir / "vpi_alignment_batch_summary.json"
    summary_report = out_dir / "vpi_alignment_batch_report.md"
    convention_csv = out_dir / "vpi_alignment_batch_conventions.csv"
    convention_json = out_dir / "vpi_alignment_batch_conventions.json"
    convention_stats, convention_decision = _summarize_conventions(
        summary_rows,
        lock_threshold_db=args.lock_threshold_db,
        min_points_for_lock=args.min_points_for_lock,
    )
    _write_csv(summary_csv, summary_rows)
    _write_csv(convention_csv, convention_stats)
    summary_json.write_text(json.dumps(summary_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    convention_json.write_text(
        json.dumps(
            {
                "decision": convention_decision,
                "conventions": convention_stats,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_report(summary_report, summary_rows, input_path, convention_stats, convention_decision)
    return {
        "count": len(summary_rows),
        "summary_csv": str(summary_csv),
        "summary_json": str(summary_json),
        "summary_report": str(summary_report),
        "convention_csv": str(convention_csv),
        "convention_json": str(convention_json),
        "convention_status": convention_decision.get("status"),
        "leading_convention": convention_decision.get("locked_or_leading_convention"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch-match VPI readings against offline outputs.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--lock-threshold-db", type=float, default=1.0)
    parser.add_argument("--min-points-for-lock", type=int, default=3)
    return parser


def main() -> int:
    result = run(build_parser().parse_args())
    print(f"matched_points={result['count']}")
    print(f"convention_status={result['convention_status']}")
    print(f"leading_convention={result['leading_convention']}")
    print(f"summary_report={result['summary_report']}")
    print(f"summary_csv={result['summary_csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
