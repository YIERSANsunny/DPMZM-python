"""Match a VPI readout against offline TIA/ADC readout candidates.

This script compares one VPI scalar value, for example a curve cursor value
after ``x*x`` and ``10log(x)+30``, against the equivalent offline columns.  It
does not change the physical simulation.  It only ranks possible readout
interpretations: differential/single-ended, RMS/peak, 1-ohm/50-ohm, TIA/ADC.
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
DEFAULT_OUT = DEFAULT_RESULTS / "vpi_alignment"
REFERENCE_LOAD_OHM = 50.0


@dataclass(frozen=True)
class Candidate:
    source: str
    name: str
    value_db: float
    note: str
    load_ohm: float | None = None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


def _db_from_v(value_v: float, load_ohm: float) -> float:
    v = max(abs(float(value_v)), 1e-300)
    return 10.0 * math.log10((v * v / float(load_ohm)) * 1000.0)


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _select_row(rows: list[dict[str, str]], bias: float | None, row_index: int | None) -> dict[str, str]:
    if not rows:
        raise ValueError("no rows available")
    if row_index is not None:
        if row_index < 0 or row_index >= len(rows):
            raise ValueError(f"row index {row_index} outside 0..{len(rows) - 1}")
        return rows[row_index]
    if bias is None:
        return rows[0]
    best = min(
        rows,
        key=lambda row: abs((_to_float(row.get("bias_source_V")) or float("inf")) - float(bias)),
    )
    if _to_float(best.get("bias_source_V")) is None:
        raise ValueError("bias_source_V column is missing or not numeric")
    return best


def _voltage_candidates(source: str, row: dict[str, str], names: list[tuple[str, str]]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for column, label in names:
        value = _to_float(row.get(column))
        if value is None:
            continue
        candidates.append(
            Candidate(
                source=source,
                name=f"{label} 1ohm",
                value_db=_db_from_v(value, 1.0),
                note=f"10log10({column}^2/1ohm)+30",
                load_ohm=1.0,
            )
        )
        candidates.append(
            Candidate(
                source=source,
                name=f"{label} 50ohm",
                value_db=_db_from_v(value, REFERENCE_LOAD_OHM),
                note=f"10log10({column}^2/50ohm)+30",
                load_ohm=REFERENCE_LOAD_OHM,
            )
        )
    return candidates


def _direct_candidates(source: str, row: dict[str, str], names: list[tuple[str, str, float | None]]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for column, label, load_ohm in names:
        value = _to_float(row.get(column))
        if value is None:
            continue
        candidates.append(Candidate(source=source, name=label, value_db=value, note=column, load_ohm=load_ohm))
    return candidates


def _tia_candidates(row: dict[str, str]) -> list[Candidate]:
    direct = _direct_candidates(
        "TIA",
        row,
        [
            ("TIA_signal_dBm_1ohm", "diff RMS direct 1ohm", 1.0),
            ("TIA_signal_dBm_50ohm", "diff RMS direct 50ohm", REFERENCE_LOAD_OHM),
            ("TIA_single_signal_dBm_1ohm", "single RMS direct 1ohm", 1.0),
            ("TIA_single_signal_dBm_50ohm", "single RMS direct 50ohm", REFERENCE_LOAD_OHM),
            ("TIA_vpi_diff_rms_xx_plus30_dB", "VPI diff RMS x*x +30 1ohm", 1.0),
            ("TIA_vpi_single_rms_xx_plus30_dB", "VPI single RMS x*x +30 1ohm", 1.0),
        ],
    )
    derived = _voltage_candidates(
        "TIA",
        row,
        [
            ("TIA_diff_signal_V_rms", "diff RMS derived"),
            ("TIA_diff_signal_V_peak", "diff peak derived"),
            ("TIA_single_signal_V_rms", "single RMS derived"),
            ("TIA_single_signal_V_peak", "single peak derived"),
        ],
    )
    return direct + derived


def _adc_candidates(row: dict[str, str]) -> list[Candidate]:
    direct = _direct_candidates(
        "ADC",
        row,
        [
            ("ADC_signal_dBm_1ohm", "clipped RMS direct 1ohm", 1.0),
            ("ADC_signal_dBm_50ohm", "clipped RMS direct 50ohm", REFERENCE_LOAD_OHM),
            ("ADC_vpi_rms_xx_plus30_dB", "VPI clipped RMS x*x +30 1ohm", 1.0),
        ],
    )
    derived = _voltage_candidates(
        "ADC",
        row,
        [
            ("ADC_linear_signal_V_rms", "preclip RMS derived"),
            ("ADC_linear_signal_V_peak", "preclip peak derived"),
            ("ADC_signal_V_rms", "clipped RMS derived"),
            ("ADC_signal_V_peak_after_clip_fundamental", "clipped peak derived"),
        ],
    )
    return direct + derived


def _rank(candidates: list[Candidate], observed: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        error = candidate.value_db - float(observed)
        rows.append(
            {
                "source": candidate.source,
                "candidate": candidate.name,
                "load_ohm": "" if candidate.load_ohm is None else candidate.load_ohm,
                "candidate_value_dB": round(candidate.value_db, 9),
                "observed_vpi_dB": round(float(observed), 9),
                "error_dB": round(error, 9),
                "abs_error_dB": round(abs(error), 9),
                "note": candidate.note,
            }
        )
    return sorted(rows, key=lambda row: float(row["abs_error_dB"]))


def _filter_by_expected_load(candidates: list[Candidate], expected_load_ohm: float | None) -> list[Candidate]:
    if expected_load_ohm is None:
        return candidates
    expected = float(expected_load_ohm)
    return [
        candidate
        for candidate in candidates
        if candidate.load_ohm is not None and math.isclose(float(candidate.load_ohm), expected, rel_tol=1e-9, abs_tol=1e-9)
    ]


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_report(
    path: Path,
    *,
    case_id: str | None,
    step: str,
    vpi_value: float,
    expected_load_ohm: float | None,
    bias: float | None,
    tia_row: dict[str, str] | None,
    adc_row: dict[str, str] | None,
    ranked: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# VPI Alignment Match Report",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"- Step: `{step}`",
        f"- Case ID: `{'-' if case_id is None else case_id}`",
        f"- VPI observed value: `{vpi_value:.9f}`",
        f"- Expected VPI load: `{'unconstrained' if expected_load_ohm is None else f'{expected_load_ohm:g} ohm'}`",
        f"- Requested bias: `{'-' if bias is None else bias}`",
    ]
    if tia_row is not None:
        lines.append(f"- TIA matched bias: `{tia_row.get('bias_source_V', '-')}`")
    if adc_row is not None:
        lines.append(f"- ADC matched bias: `{adc_row.get('bias_source_V', '-')}`")
    lines.extend(
        [
            "",
            "## Best Matches",
            "",
            "| Rank | Source | Candidate | Load | Candidate value | Error | Abs error |",
            "|---:|---|---|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(ranked[:12], start=1):
        lines.append(
            "| {rank} | {source} | {candidate} | {load} | {value:.3f} dB | {error:+.3f} dB | {abs_error:.3f} dB |".format(
                rank=index,
                source=row["source"],
                candidate=row["candidate"],
                load="-" if row.get("load_ohm", "") == "" else f"{float(row['load_ohm']):g} ohm",
                value=float(row["candidate_value_dB"]),
                error=float(row["error_dB"]),
                abs_error=float(row["abs_error_dB"]),
            )
        )
    if not ranked:
        lines.append("| - | - | no candidates after load filtering | - | - | - | - |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- If `Expected VPI load` is set, candidates using a different load are intentionally excluded.",
            "- A `single RMS 50ohm` match suggests the VPI plot is effectively reading one TIA output pin and using a 50-ohm equivalent display.",
            "- A `diff RMS 1ohm` match suggests the VPI plot is reading differential voltage and using the raw `x*x` plus 30 formula without a 50-ohm divisor.",
            "- VPI `TwoPortAnalyzerEl` reports single-frequency magnitude as RMS; `peak derived` candidates are kept only as diagnostics for legacy plots or nonstandard post-processing.",
            "- If an ADC candidate wins, the VPI comparison point likely includes ADC clipping/filtering. Otherwise compare against TIA candidates.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    step = args.step
    tia_path = args.tia_csv or (DEFAULT_RESULTS / "tia_curves" / f"{step}_tia_curve.csv")
    adc_path = args.adc_csv or (DEFAULT_RESULTS / "adc_curves" / f"{step}_adc_curve.csv")

    tia_rows = _read_rows(tia_path)
    adc_rows = _read_rows(adc_path)
    tia_row = _select_row(tia_rows, args.bias, args.row_index) if tia_rows else None
    adc_row = _select_row(adc_rows, args.bias, args.row_index) if adc_rows else None

    candidates: list[Candidate] = []
    if tia_row is not None:
        candidates.extend(_tia_candidates(tia_row))
    if adc_row is not None:
        candidates.extend(_adc_candidates(adc_row))
    candidates = _filter_by_expected_load(candidates, args.expected_load_ohm)
    ranked = _rank(candidates, args.vpi_value)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    case_id = getattr(args, "case_id", None)
    stem_parts = [str(case_id).strip(), step] if case_id else [step]
    stem = "_".join(part for part in stem_parts if part).replace(" ", "_")
    csv_path = out_dir / f"{stem}_vpi_alignment_candidates.csv"
    json_path = out_dir / f"{stem}_vpi_alignment_candidates.json"
    report_path = out_dir / f"{stem}_vpi_alignment_report.md"

    _write_csv(csv_path, ranked)
    json_path.write_text(json.dumps(ranked, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(
        report_path,
        case_id=case_id,
        step=step,
        vpi_value=args.vpi_value,
        expected_load_ohm=args.expected_load_ohm,
        bias=args.bias,
        tia_row=tia_row,
        adc_row=adc_row,
        ranked=ranked,
    )
    return {
        "csv_path": str(csv_path),
        "json_path": str(json_path),
        "report_path": str(report_path),
        "best": ranked[0] if ranked else None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Match a VPI readout against offline readout candidates.")
    parser.add_argument("--case-id", default=None)
    parser.add_argument("--step", default="step1_i_bridge")
    parser.add_argument("--vpi-value", type=float, default=10.36660078773)
    parser.add_argument("--expected-load-ohm", type=float, default=None)
    parser.add_argument("--bias", type=float, default=-8.6)
    parser.add_argument("--row-index", type=int, default=None)
    parser.add_argument("--tia-csv", type=Path, default=None)
    parser.add_argument("--adc-csv", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    return parser


def main() -> int:
    result = run(build_parser().parse_args())
    print(f"report={result['report_path']}")
    print(f"csv={result['csv_path']}")
    best = result.get("best")
    if best:
        print(
            "best={source} | {candidate} | value={value:.6f} dB | error={error:+.6f} dB".format(
                source=best["source"],
                candidate=best["candidate"],
                value=float(best["candidate_value_dB"]),
                error=float(best["error_dB"]),
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
