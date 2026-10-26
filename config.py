"""Shared experiment settings: defaults < JSON scenario < explicit CLI flags."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass, field, fields, is_dataclass, replace
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HARDWARE_CONFIG = ROOT / "configs" / "hardware.json"


@dataclass(frozen=True)
class PhysicalConfig:
    vpi_v: float = 5.0
    er_db: float = 30.0
    il_db: float = 0.0
    il_i_db: float = 6.0
    il_q_db: float = 6.0
    il_p_db: float = 0.0
    pin_dbm: float = 10.0
    responsivity_a_per_w: float = 0.8
    pd_tap: float = 1.0
    child_source_gain: float = 2.0
    parent_source_gain: float = 1.0
    er_model: str = "vpi"
    rin_db_hz: float = -145.0
    temp_k: float = 290.0


@dataclass(frozen=True)
class DriveConfig:
    i_source_bias_v: float = 1.4
    q_source_bias_v: float = 2.1
    p_phase_deg: float = 37.0
    i_dither_source_amp_vpeak: float = 0.025
    q_dither_source_amp_vpeak: float = 0.025
    p_dither_source_amp_vpeak: float = 0.0
    f_i_hz: float = 1000.0
    f_q_hz: float = 1200.0
    f_p_hz: float = 1300.0


@dataclass(frozen=True)
class SamplingConfig:
    fs_hz: float = 1_000_000.0
    t_total_s: float = 0.1
    rng_seed: int = 0
    add_model_noise: bool = True


@dataclass(frozen=True)
class TIAConfig:
    profile: str = "vpi"
    rf_ohm: float = 10_000.0
    cf_f: float = 10e-12
    input_equivalent_noise_rms_a: float = 1.1e-6
    noise_bandwidth_hz: float = 8e9
    opamp_en_v_per_sqrt_hz: float = 5.1e-9
    opamp_in_a_per_sqrt_hz: float = 0.8e-15
    high_freq_enbw_hz: float = 122070.3125
    low_freq_enbw_hz: float = 1.0
    passband_ratio: float = 0.1


@dataclass(frozen=True)
class ADCConfig:
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
    r_pos_ohm: float = 1000.0
    r_neg_ohm: float = 1000.0
    c_diff_f: float = 10e-9
    adc_noise_rms_v: float = 21.31e-6
    reference_load_ohm: float = 50.0

    @property
    def fmod_hz(self):
        return self.sample_rate_sps * self.osr

    @property
    def fullscale_peak_v(self):
        return self.vref_v / self.gain

    @property
    def lsb_v(self):
        return 2.0 * self.fullscale_peak_v / 2**self.bits

    @property
    def rc_fc_hz(self):
        return 1.0 / (2.0 * math.pi * (self.r_pos_ohm + self.r_neg_ohm) * self.c_diff_f)

    @property
    def goertzel_bin_width_hz(self):
        return self.sample_rate_sps / self.goertzel_points

    @property
    def measurement_enbw_hz(self):
        return self.goertzel_bin_width_hz


@dataclass(frozen=True)
class FindpointConfig:
    step1_i_fixed_q_bias: float = 1.367
    step1_i_fixed_p_phase_deg: float = 0.0
    step1_q_fixed_i_bias: float = 1.367
    step1_q_fixed_p_phase_deg: float = 0.0
    p_dither_source_amp_vpeak: float = 0.025
    scan_start_source_v: float = -10.0
    scan_stop_source_v: float = 10.0
    scan_step_source_v: float = 0.05
    edge_points: int = 5
    major_window_db: float = 3.0


@dataclass(frozen=True)
class ProjectConfig:
    case_name: str = "iq_i1p4_q2p1_p37deg"
    physical: PhysicalConfig = field(default_factory=PhysicalConfig)
    drive: DriveConfig = field(default_factory=DriveConfig)
    sampling: SamplingConfig = field(default_factory=SamplingConfig)
    tia: TIAConfig = field(default_factory=TIAConfig)
    adc: ADCConfig = field(default_factory=ADCConfig)
    findpoint: FindpointConfig = field(default_factory=FindpointConfig)

    def p_source_voltage(self, phase_deg):
        return phase_deg * self.physical.vpi_v / (180.0 * self.physical.parent_source_gain)

    def derived(self):
        p, d, s = self.physical, self.drive, self.sampling
        count = round(s.fs_hz * s.t_total_s)
        return dict(
            i_effective_bias_v=p.child_source_gain * d.i_source_bias_v,
            q_effective_bias_v=p.child_source_gain * d.q_source_bias_v,
            p_source_bias_v=self.p_source_voltage(d.p_phase_deg),
            p_effective_bias_v=d.p_phase_deg * p.vpi_v / 180.0,
            i_effective_pilot_vpeak=p.child_source_gain * d.i_dither_source_amp_vpeak,
            q_effective_pilot_vpeak=p.child_source_gain * d.q_dither_source_amp_vpeak,
            p_effective_pilot_vpeak=p.parent_source_gain * d.p_dither_source_amp_vpeak,
            simulation_points=count, fft_bin_width_hz=s.fs_hz / count,
            adc_bin_width_hz=self.adc.goertzel_bin_width_hz,
            tia_diff_to_single_db=20.0 * math.log10(2.0),
            one_ohm_to_50ohm_db=-10.0 * math.log10(50.0),
        )


DEFAULT_CONFIG = ProjectConfig()


def _update(instance, values, location="config"):
    if not isinstance(values, dict):
        raise ValueError(f"{location} must be a JSON object")
    known = {item.name for item in fields(instance)}
    unknown = set(values) - known
    if unknown:
        raise ValueError(f"Unknown {location} fields: {', '.join(sorted(unknown))}")
    changes = {}
    for name, value in values.items():
        previous = getattr(instance, name)
        label = f"{location}.{name}"
        if is_dataclass(previous):
            value = _update(previous, value, label)
        elif isinstance(previous, bool):
            if not isinstance(value, bool):
                raise ValueError(f"{label} must be boolean")
        elif isinstance(previous, (float, int)):
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
                raise ValueError(f"{label} must be a finite number")
            if isinstance(previous, int) and not isinstance(value, int):
                raise ValueError(f"{label} must be an integer")
        elif not isinstance(value, str):
            raise ValueError(f"{label} must be a string")
        changes[name] = value
    return replace(instance, **changes)


def validate_config(cfg):
    _update(DEFAULT_CONFIG, asdict(cfg))
    p, d, s, t, a, f = cfg.physical, cfg.drive, cfg.sampling, cfg.tia, cfg.adc, cfg.findpoint
    positive = dict(vpi_v=p.vpi_v, er_db=p.er_db, responsivity=p.responsivity_a_per_w,
        pd_tap=p.pd_tap, child_source_gain=p.child_source_gain, parent_source_gain=p.parent_source_gain,
        temp_k=p.temp_k, fs_hz=s.fs_hz, t_total_s=s.t_total_s, tia_rf_ohm=t.rf_ohm,
        tia_cf_f=t.cf_f, noise_bandwidth_hz=t.noise_bandwidth_hz, passband_ratio=t.passband_ratio,
        high_freq_enbw_hz=t.high_freq_enbw_hz, low_freq_enbw_hz=t.low_freq_enbw_hz,
        adc_sample_rate_sps=a.sample_rate_sps, osr=a.osr, gain=a.gain, vref_v=a.vref_v,
        bits=a.bits, goertzel_points=a.goertzel_points, goertzel_blocks=a.goertzel_blocks,
        r_pos_ohm=a.r_pos_ohm, r_neg_ohm=a.r_neg_ohm, c_diff_f=a.c_diff_f,
        reference_load_ohm=a.reference_load_ohm, scan_step_source_v=f.scan_step_source_v)
    for name, value in positive.items():
        if value <= 0:
            raise ValueError(f"{name} must be > 0")
    nonnegative = dict(il_db=p.il_db, il_i_db=p.il_i_db, il_q_db=p.il_q_db, il_p_db=p.il_p_db,
        tia_noise=t.input_equivalent_noise_rms_a, opamp_en=t.opamp_en_v_per_sqrt_hz,
        opamp_in=t.opamp_in_a_per_sqrt_hz, adc_noise=a.adc_noise_rms_v,
        edge_points=f.edge_points, major_window_db=f.major_window_db, rng_seed=s.rng_seed)
    for name, value in nonnegative.items():
        if value < 0:
            raise ValueError(f"{name} must be >= 0")
    if p.er_model not in {"vpi", "thesis"} or t.profile not in {"vpi", "hardware"}:
        raise ValueError("er_model must be vpi/thesis; tia.profile must be vpi/hardware")
    if a.window not in {"none", "rect", "rectangular"}:
        raise ValueError("Only rectangular/no-window ADC measurement is currently modeled")
    if a.reference_load_ohm != 50.0:
        raise ValueError("ADC *_50ohm output columns require adc.reference_load_ohm = 50")
    if not cfg.case_name or cfg.case_name in {".", ".."} or Path(cfg.case_name).name != cfg.case_name or any(c in cfg.case_name for c in "/\\"):
        raise ValueError("case_name must be a filename without directory separators")
    if f.scan_stop_source_v < f.scan_start_source_v:
        raise ValueError("scan_stop_source_v must be >= scan_start_source_v")
    count = round(s.fs_hz * s.t_total_s)
    if count < 2 or not math.isclose(count, s.fs_hz * s.t_total_s, abs_tol=1e-6, rel_tol=0):
        raise ValueError("fs_hz * t_total_s must be an integer >= 2")
    for name in ("f_i_hz", "f_q_hz", "f_p_hz"):
        frequency = getattr(d, name)
        if not 0 < frequency < s.fs_hz / 2:
            raise ValueError(f"{name} must lie between DC and the simulation Nyquist frequency")
        cycles = frequency * count / s.fs_hz
        if not math.isclose(cycles, round(cycles), abs_tol=1e-8, rel_tol=0):
            raise ValueError(f"{name} is not coherent with the simulation time window")
    return cfg


def load_config(path=None):
    cfg = DEFAULT_CONFIG
    if path is not None:
        with Path(path).open(encoding="utf-8-sig") as stream:
            values = json.load(stream)
        if isinstance(values, dict) and "config" in values:
            if set(values) - {"config", "derived", "config_source", "precedence"}:
                raise ValueError("Unknown resolved-config metadata")
            values = values["config"]
        cfg = _update(cfg, values)
    return validate_config(cfg)


PHYSICAL_ARGS = dict(vpi="physical.vpi_v", er_db="physical.er_db", il_db="physical.il_db",
    il_i_db="physical.il_i_db", il_q_db="physical.il_q_db", il_p_db="physical.il_p_db",
    pin_dbm="physical.pin_dbm", responsivity="physical.responsivity_a_per_w", pd_tap="physical.pd_tap",
    child_source_gain="physical.child_source_gain", parent_source_gain="physical.parent_source_gain",
    er_model="physical.er_model", rin_db_hz="physical.rin_db_hz", temp_k="physical.temp_k")
SAMPLING_ARGS = dict(fs="sampling.fs_hz", t_total="sampling.t_total_s", rng_seed="sampling.rng_seed")
PILOT_ARGS = dict(f_i="drive.f_i_hz", f_q="drive.f_q_hz", f_p="drive.f_p_hz",
    i_dither_source_amp="drive.i_dither_source_amp_vpeak",
    q_dither_source_amp="drive.q_dither_source_amp_vpeak",
    p_dither_source_amp="drive.p_dither_source_amp_vpeak")
HARDWARE_TIA_ARGS = dict(rf_ohm="tia.rf_ohm", cf_f="tia.cf_f", temp_k="physical.temp_k",
    responsivity="physical.responsivity_a_per_w", rin_db_hz="physical.rin_db_hz",
    opamp_en="tia.opamp_en_v_per_sqrt_hz", opamp_in="tia.opamp_in_a_per_sqrt_hz",
    high_freq_enbw="tia.high_freq_enbw_hz", low_freq_enbw="tia.low_freq_enbw_hz",
    rng_seed="sampling.rng_seed")


def parse_config_args(parser, bindings, argv=None, *, default_config=None, spectrum=False):
    """Resolve config first, then let argparse apply explicitly supplied flags."""
    parser.add_argument("--config", type=Path, default=default_config, help="JSON scenario; explicit flags take precedence")
    probe = argparse.ArgumentParser(add_help=False)
    probe.add_argument("--config", type=Path, default=default_config)
    selection, _ = probe.parse_known_args(argv)
    try:
        cfg = load_config(selection.config)
        defaults = {}
        for argument, dotted in bindings.items():
            value = cfg
            for part in dotted.split("."):
                value = getattr(value, part)
            defaults[argument] = value
        parser.set_defaults(**defaults)
        args = parser.parse_args(argv)
        patch = {}
        for argument, dotted in bindings.items():
            destination = patch
            parts = dotted.split(".")
            for part in parts[:-1]:
                destination = destination.setdefault(part, {})
            destination[parts[-1]] = getattr(args, argument)
        cfg = validate_config(_update(cfg, patch))
        if spectrum:
            if args.p_source_bias is not None:
                phase = 180.0 * cfg.physical.parent_source_gain * args.p_source_bias / cfg.physical.vpi_v
                cfg = replace(cfg, drive=replace(cfg.drive, p_phase_deg=phase))
            elif args.p_phase_deg is not None:
                cfg = replace(cfg, drive=replace(cfg.drive, p_phase_deg=args.p_phase_deg))
            args.p_source_bias = cfg.p_source_voltage(cfg.drive.p_phase_deg)
            args.p_phase_deg = cfg.drive.p_phase_deg
            if cfg.tia.profile != "vpi":
                raise ValueError("The full-spectrum entry models the VPI TIA; use tia/visibility for the hardware profile")
        args.project_config = validate_config(cfg)
        return args
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))


def save_config_snapshot(cfg, out_dir, *, source=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(config=asdict(cfg), derived=cfg.derived(),
                   config_source=str(Path(source).resolve()) if source else "config.py defaults",
                   precedence="config.py defaults < JSON scenario < explicit CLI flags")
    path = out_dir / "resolved_config.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
