"""Self-check the VPI/offline readout alignment columns.

The checker verifies invariant conversions introduced for VPI alignment:

* 1-ohm equivalent readings must exceed 50-ohm readings by 10log10(50).
* Differential TIA readings must exceed single-ended TIA readings by 20log10(2).
* VPI helper columns must equal their corresponding 1-ohm RMS readings.

This script validates the readout ruler; it does not rerun the DPMZM physical
simulation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = PROJECT_ROOT / "simulation_validation" / "results"
DEFAULT_TIA_DIR = DEFAULT_RESULTS / "tia_curves"
DEFAULT_ADC_DIR = DEFAULT_RESULTS / "adc_curves"
DEFAULT_BATCH_CONVENTIONS = DEFAULT_RESULTS / "vpi_alignment_batch" / "vpi_alignment_batch_conventions.json"
DEFAULT_OUT_DIR = DEFAULT_RESULTS / "vpi_alignment_selfcheck"

DB_1OHM_MINUS_50OHM = 10.0 * math.log10(50.0)
DB_DIFF_MINUS_SINGLE = 20.0 * math.log10(2.0)


@dataclass
class Check:
    name: str
    file: str
    row_index: int
    expected_db: float
    observed_db: float
    error_db: float
    status: str


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


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _add_delta_check(
    checks: list[Check],
    *,
    name: str,
    path: Path,
    row_index: int,
    row: dict[str, str],
    high_col: str,
    low_col: str,
    expected_db: float,
    tolerance_db: float,
) -> None:
    high = _to_float(row.get(high_col))
    low = _to_float(row.get(low_col))
    if high is None or low is None:
        checks.append(
            Check(
                name=name,
                file=str(path),
                row_index=row_index,
                expected_db=expected_db,
                observed_db=float("nan"),
                error_db=float("nan"),
                status="MISSING_COLUMN",
            )
        )
        return
    observed = high - low
    error = observed - expected_db
    status = "PASS" if abs(error) <= tolerance_db else "FAIL"
    checks.append(
        Check(
            name=name,
            file=str(path),
            row_index=row_index,
            expected_db=expected_db,
            observed_db=observed,
            error_db=error,
            status=status,
        )
    )


def _check_tia_file(path: Path, tolerance_db: float) -> list[Check]:
    checks: list[Check] = []
    for index, row in enumerate(_read_csv(path)):
        _add_delta_check(
            checks,
            name="TIA diff 1ohm minus diff 50ohm",
            path=path,
            row_index=index,
            row=row,
            high_col="TIA_signal_dBm_1ohm",
            low_col="TIA_signal_dBm_50ohm",
            expected_db=DB_1OHM_MINUS_50OHM,
            tolerance_db=tolerance_db,
        )
        _add_delta_check(
            checks,
            name="TIA single 1ohm minus single 50ohm",
            path=path,
            row_index=index,
            row=row,
            high_col="TIA_single_signal_dBm_1ohm",
            low_col="TIA_single_signal_dBm_50ohm",
            expected_db=DB_1OHM_MINUS_50OHM,
            tolerance_db=tolerance_db,
        )
        _add_delta_check(
            checks,
            name="TIA diff 1ohm minus single 1ohm",
            path=path,
            row_index=index,
            row=row,
            high_col="TIA_signal_dBm_1ohm",
            low_col="TIA_single_signal_dBm_1ohm",
            expected_db=DB_DIFF_MINUS_SINGLE,
            tolerance_db=tolerance_db,
        )
        _add_delta_check(
            checks,
            name="TIA VPI diff equals 1ohm",
            path=path,
            row_index=index,
            row=row,
            high_col="TIA_vpi_diff_rms_xx_plus30_dB",
            low_col="TIA_signal_dBm_1ohm",
            expected_db=0.0,
            tolerance_db=tolerance_db,
        )
    return checks


def _check_adc_file(path: Path, tolerance_db: float) -> list[Check]:
    checks: list[Check] = []
    for index, row in enumerate(_read_csv(path)):
        _add_delta_check(
            checks,
            name="ADC 1ohm minus 50ohm",
            path=path,
            row_index=index,
            row=row,
            high_col="ADC_signal_dBm_1ohm",
            low_col="ADC_signal_dBm_50ohm",
            expected_db=DB_1OHM_MINUS_50OHM,
            tolerance_db=tolerance_db,
        )
        _add_delta_check(
            checks,
            name="ADC VPI equals 1ohm",
            path=path,
            row_index=index,
            row=row,
            high_col="ADC_vpi_rms_xx_plus30_dB",
            low_col="ADC_signal_dBm_1ohm",
            expected_db=0.0,
            tolerance_db=tolerance_db,
        )
    return checks


def _summarize_checks(checks: list[Check]) -> dict[str, Any]:
    total = len(checks)
    failures = [check for check in checks if check.status != "PASS"]
    max_abs_error = 0.0
    finite_errors = [abs(check.error_db) for check in checks if math.isfinite(check.error_db)]
    if finite_errors:
        max_abs_error = max(finite_errors)
    return {
        "total_checks": total,
        "failed_checks": len(failures),
        "status": "PASS" if not failures and total > 0 else "FAIL",
        "max_abs_error_db": max_abs_error,
    }


def _load_convention_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "MISSING", "locked_or_leading_convention": ""}
    data = json.loads(path.read_text(encoding="utf-8"))
    decision = data.get("decision", {})
    return {
        "status": decision.get("status", "UNKNOWN"),
        "locked_or_leading_convention": decision.get("locked_or_leading_convention", ""),
        "point_count": decision.get("point_count"),
        "min_points_for_lock": decision.get("min_points_for_lock"),
        "lock_threshold_db": decision.get("lock_threshold_db"),
    }


def _write_csv(path: Path, checks: list[Check]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "status",
                "name",
                "file",
                "row_index",
                "expected_db",
                "observed_db",
                "error_db",
            ],
        )
        writer.writeheader()
        for check in checks:
            writer.writerow(
                {
                    "status": check.status,
                    "name": check.name,
                    "file": check.file,
                    "row_index": check.row_index,
                    "expected_db": check.expected_db,
                    "observed_db": check.observed_db,
                    "error_db": check.error_db,
                }
            )


def _write_report(path: Path, summary: dict[str, Any], convention: dict[str, Any], checks: list[Check]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    failing = [check for check in checks if check.status != "PASS"]
    lines = [
        "# VPI Alignment Self-check Report",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Summary",
        "",
        f"- Readout conversion status: `{summary['status']}`",
        f"- Total checks: `{summary['total_checks']}`",
        f"- Failed checks: `{summary['failed_checks']}`",
        f"- Max abs conversion error: `{summary['max_abs_error_db']:.6g} dB`",
        f"- Batch convention status: `{convention.get('status', '-')}`",
        f"- Leading convention: `{convention.get('locked_or_leading_convention', '-')}`",
        "",
        "## Expected Invariants",
        "",
        f"- `1ohm - 50ohm = {DB_1OHM_MINUS_50OHM:.9f} dB`",
        f"- `diff - single = {DB_DIFF_MINUS_SINGLE:.9f} dB`",
        "",
    ]
    if failing:
        lines.extend(["## Failing Checks", "", "| Status | Name | Row | Error | File |", "|---|---|---:|---:|---|"])
        for check in failing[:50]:
            lines.append(
                f"| {check.status} | {check.name} | {check.row_index} | {check.error_db} | {check.file} |"
            )
    else:
        lines.extend(["## Failing Checks", "", "No failing conversion checks."])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    checks: list[Check] = []
    for path in sorted(args.tia_dir.glob("*_tia_curve.csv")):
        checks.extend(_check_tia_file(path, args.tolerance_db))
    for path in sorted(args.adc_dir.glob("*_adc_curve.csv")):
        checks.extend(_check_adc_file(path, args.tolerance_db))

    summary = _summarize_checks(checks)
    convention = _load_convention_status(args.batch_conventions)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "vpi_alignment_selfcheck.csv"
    json_path = out_dir / "vpi_alignment_selfcheck.json"
    report_path = out_dir / "vpi_alignment_selfcheck_report.md"
    _write_csv(csv_path, checks)
    json_path.write_text(
        json.dumps(
            {
                "summary": summary,
                "batch_convention": convention,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_report(report_path, summary, convention, checks)
    return {
        "summary": summary,
        "csv_path": str(csv_path),
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Self-check VPI/offline alignment readout columns.")
    parser.add_argument("--tia-dir", type=Path, default=DEFAULT_TIA_DIR)
    parser.add_argument("--adc-dir", type=Path, default=DEFAULT_ADC_DIR)
    parser.add_argument("--batch-conventions", type=Path, default=DEFAULT_BATCH_CONVENTIONS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--tolerance-db", type=float, default=1e-6)
    return parser


def main() -> int:
    result = run(build_parser().parse_args())
    summary = result["summary"]
    print(f"status={summary['status']}")
    print(f"total_checks={summary['total_checks']}")
    print(f"failed_checks={summary['failed_checks']}")
    print(f"report={result['report_path']}")
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
