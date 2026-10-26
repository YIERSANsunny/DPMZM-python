"""VPI-style DPMZM demo.

Run from the project root:

    python -m dpmzm.vpi_demo

The default case mirrors the screenshot-level parameters:
- CW laser average power: 0.010 W -> 10 dBm
- BitRateDefault: 10 GHz
- SampleRateDefault: 16 * BitRateDefault -> 160 GSa/s
- TimeWindow: 65536 / BitRateDefault -> 6.5536 us
- DiffMZ_DSM VpiDC/VpiRF: 5 V
- Insertion loss: 6 dB per DiffMZ_DSM block
- Extinction ratio: 30 dB
- PD/SignalAnalyzer electrical load convention: 1 ohm
- RF sine: 10 GHz, amplitude 1.0 at the VPI drive source
- I/Q DC sources: 2.5 V at the VPI drive source
- Parent DC source: 1.25 V at the VPI drive source

The I/Q child DiffMZ_DSM blocks use LowerArmPhaseSense=NEGATIVE, so their VPI
source values are treated as half of the effective differential phase-drive
voltage. The parent DiffMZ_DSM uses LowerArmPhaseSense=POSITIVE, so its source
value is treated as common phase drive and is not doubled by default. In this
VPI layout the parent/P block is in the Q optical path, so its insertion loss is
applied to the Q branch before the final optical combiner. Finite extinction
ratio uses the normalized VPI-style arm-imbalance model by default.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from ..core.model import SimulationResult, simulate_dpmzm
from ..visualization.plot import (
    plot_bias_scan,
    plot_electrical_spectrum,
    plot_optical_spectrum_osa,
)


VPI_REFERENCE_DBM: dict[str, float] = {
    # Fill these from VPI SignalAnalyzer/OSA markers when available, e.g.
    # "opt_carrier": -80.0,
    # "opt_lower_1": -10.5,
    # "opt_upper_1": -45.0,
    "elec_dc": -49.0,
    "elec_rf": -74.0,
    "elec_2rf": -53.0,
}


def _dbm(power_w: float) -> float:
    return float(10.0 * np.log10(float(power_w) * 1000.0 + 1e-30))


def _peak_near(freq_hz: np.ndarray, power_dbm: np.ndarray, center_hz: float, span_hz: float) -> tuple[float, float]:
    mask = (freq_hz >= center_hz - span_hz) & (freq_hz <= center_hz + span_hz)
    if not np.any(mask):
        return float("nan"), float("nan")
    local_f = freq_hz[mask]
    local_p = power_dbm[mask]
    idx = int(np.argmax(local_p))
    return float(local_f[idx]), float(local_p[idx])


def _optical_markers(sim: SimulationResult, f_rf: float) -> dict[str, float]:
    f = sim.spectrum.f_opt
    p = sim.spectrum.P_opt_spec_dBm
    span = max(float(f_rf) * 0.15, sim.RBW_Hz * 3.0)

    _, carrier = _peak_near(f, p, 0.0, span)
    _, lower_1 = _peak_near(f, p, -float(f_rf), span)
    _, upper_1 = _peak_near(f, p, float(f_rf), span)
    _, lower_2 = _peak_near(f, p, -2.0 * float(f_rf), span)
    _, upper_2 = _peak_near(f, p, 2.0 * float(f_rf), span)

    return {
        "opt_carrier": carrier,
        "opt_lower_1": lower_1,
        "opt_upper_1": upper_1,
        "opt_lower_2": lower_2,
        "opt_upper_2": upper_2,
        "ssb_suppression_1_db": lower_1 - upper_1,
        "carrier_suppression_vs_lower_1_db": lower_1 - carrier,
    }


def _electrical_markers(sim: SimulationResult, f_rf: float) -> dict[str, float]:
    f = sim.spectrum.f_elec
    p = sim.spectrum.P_elec_spec_dBm
    span = max(float(f_rf) * 0.05, sim.RBW_Hz * 3.0)

    _, dc = _peak_near(f, p, 0.0, sim.RBW_Hz * 1.5)
    _, rf = _peak_near(f, p, float(f_rf), span)
    _, rf2 = _peak_near(f, p, 2.0 * float(f_rf), span)

    return {
        "elec_dc": dc,
        "elec_rf": rf,
        "elec_2rf": rf2,
        "pd_avg_dBm": sim.P_pd_avg_dBm,
        "noise_floor_dBm": sim.noise.P_noise_floor_dBm,
        "noise_density_dBmHz": sim.noise.P_density_dBmHz,
    }


def _print_table(metrics: dict[str, float], reference_dbm: dict[str, float]) -> None:
    print("\n=== DPMZM VPI-style demo markers ===")
    print(f"{'metric':34s} {'python(dBm)':>14s} {'vpi(dBm)':>12s} {'diff(dB)':>10s}")
    print("-" * 76)
    for key, value in metrics.items():
        if not np.isfinite(value):
            value_text = "nan"
        else:
            value_text = f"{value: .3f}"

        if key in reference_dbm:
            ref = float(reference_dbm[key])
            diff = value - ref
            print(f"{key:34s} {value_text:>14s} {ref:12.3f} {diff:10.3f}")
        else:
            print(f"{key:34s} {value_text:>14s} {'':>12s} {'':>10s}")


def _print_params(sim: SimulationResult) -> None:
    keys = [
        "Pin_dBm",
        "Responsivity",
        "R_load",
        "Vpi_I",
        "Vpi_Q",
        "Vpi_P",
        "ER_I_dB",
        "ER_Q_dB",
        "ER_P_dB",
        "IL_dB",
        "IL_I_dB",
        "IL_Q_dB",
        "IL_P_dB",
        "V_DCI",
        "V_DCQ",
        "V_DCP",
        "f_rf",
        "V_RFI_amp",
        "V_RFQ_amp",
        "rf_phase_I",
        "rf_phase_Q",
        "er_model",
        "RBW_Hz",
        "vpi_compatible_dbm",
    ]
    print("\n=== Effective Python parameters ===")
    for key in keys:
        print(f"{key:22s}: {sim.params.get(key)}")


def run_demo(
    *,
    out_dir: str | Path = "artifacts/dpmzm_vpi_demo",
    child_drive_gain: float = 2.0,
    parent_drive_gain: float = 1.0,
    rf_drive_gain: float | None = None,
    bit_rate: float = 10e9,
    samples_per_bit: int = 16,
    time_window_bits: int = 65536,
    fs: float | None = None,
    t_total: float | None = None,
    f_rf: float = 10e9,
    vpi_source_child_dc: float = 2.5,
    vpi_source_parent_dc: float = 1.25,
    vpi_source_rf_amp: float = 1.0,
    rf_phase_q_deg: float = 90.0,
    pd_tap: float = 1.0,
    er_model: str = "vpi",
    vpi_compatible_dbm: bool = True,
) -> tuple[SimulationResult, dict[str, float]]:
    """Run the screenshot-style VPI comparison case and save plots."""

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    fs_eff = float(fs) if fs is not None else float(samples_per_bit) * float(bit_rate)
    t_total_eff = (
        float(t_total)
        if t_total is not None
        else float(time_window_bits) / float(bit_rate)
    )

    sim = simulate_dpmzm(
        Fs=float(fs_eff),
        T_total=float(t_total_eff),
        Vpi=5.0,
        ER_dB=30.0,
        ER_I_dB=30.0,
        ER_Q_dB=30.0,
        ER_P_dB=30.0,
        IL_dB=0.0,
        IL_I_dB=6.0,
        IL_Q_dB=6.0,
        IL_P_dB=6.0,
        Pin_dBm=_dbm(0.010),
        R_load=1.0,
        pd_tap=float(pd_tap),
        V_DCI=float(child_drive_gain) * float(vpi_source_child_dc),
        V_DCQ=float(child_drive_gain) * float(vpi_source_child_dc),
        V_DCP=float(parent_drive_gain) * float(vpi_source_parent_dc),
        f_rf=float(f_rf),
        V_RFI_amp=float(rf_drive_gain if rf_drive_gain is not None else child_drive_gain)
        * float(vpi_source_rf_amp),
        V_RFQ_amp=float(rf_drive_gain if rf_drive_gain is not None else child_drive_gain)
        * float(vpi_source_rf_amp),
        rf_phase_I=0.0,
        rf_phase_Q=float(np.deg2rad(float(rf_phase_q_deg))),
        er_model=er_model,
        vpi_compatible_dbm=bool(vpi_compatible_dbm),
        rng_seed=0,
    )

    metrics = {}
    metrics.update(_optical_markers(sim, f_rf=float(f_rf)))
    metrics.update(_electrical_markers(sim, f_rf=float(f_rf)))

    _print_params(sim)
    _print_table(metrics, VPI_REFERENCE_DBM)

    plot_optical_spectrum_osa(sim, f_rf_hz=float(f_rf), span_factor=2.5, max_order=2)
    plt.savefig(out_path / "optical_spectrum.png", dpi=160)
    plt.close()

    plot_electrical_spectrum(sim, f_rf_hz=float(f_rf), harmonic_orders=(0, 1, 2))
    plt.savefig(out_path / "electrical_spectrum.png", dpi=160)
    plt.close()

    plot_bias_scan(sim)
    plt.savefig(out_path / "bias_scan.png", dpi=160)
    plt.close()

    np.savez(
        out_path / "markers.npz",
        **{k: np.array(v, dtype=float) for k, v in metrics.items()},
    )
    print(f"\nSaved plots and markers to: {out_path.resolve()}")
    return sim, metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a VPI-style DPMZM demo case.")
    parser.add_argument("--out-dir", default="artifacts/dpmzm_vpi_demo")
    parser.add_argument("--child-drive-gain", type=float, default=2.0)
    parser.add_argument("--parent-drive-gain", type=float, default=1.0)
    parser.add_argument("--rf-drive-gain", type=float, default=None)
    parser.add_argument("--bit-rate", type=float, default=10e9)
    parser.add_argument("--samples-per-bit", type=int, default=16)
    parser.add_argument("--time-window-bits", type=int, default=65536)
    parser.add_argument("--fs", type=float, default=None)
    parser.add_argument("--t-total", type=float, default=None)
    parser.add_argument("--f-rf", type=float, default=10e9)
    parser.add_argument("--rf-phase-q-deg", type=float, default=90.0)
    parser.add_argument("--pd-tap", type=float, default=1.0)
    parser.add_argument("--er-model", choices=("vpi", "thesis"), default="vpi")
    parser.add_argument("--no-vpi-compatible-dbm", action="store_true")
    args = parser.parse_args()

    run_demo(
        out_dir=args.out_dir,
        child_drive_gain=args.child_drive_gain,
        parent_drive_gain=args.parent_drive_gain,
        rf_drive_gain=args.rf_drive_gain,
        bit_rate=args.bit_rate,
        samples_per_bit=args.samples_per_bit,
        time_window_bits=args.time_window_bits,
        fs=args.fs,
        t_total=args.t_total,
        f_rf=args.f_rf,
        rf_phase_q_deg=args.rf_phase_q_deg,
        pd_tap=args.pd_tap,
        er_model=args.er_model,
        vpi_compatible_dbm=not bool(args.no_vpi_compatible_dbm),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
