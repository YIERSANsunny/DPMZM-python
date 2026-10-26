"""Check configuration precedence, unit conversion, and entry-point agreement."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from config import DEFAULT_CONFIG, ROOT, load_config, save_config_snapshot
from simulation_validation.adc_chain_model import parse_args as adc_args
from simulation_validation.findpoint_validator import parse_args as validate_args
from simulation_validation.run_chained_findpoint import parse_args as findpoint_args
from simulation_validation.tia_experimental_curves import parse_args as tia_args
from simulation_validation.tia_full_spectrum import parse_args as spectrum_args
from simulation_validation.tia_visibility_analyzer import parse_args as visibility_args


class ConfigurationTests(unittest.TestCase):
    def test_confirmed_scenarios_and_units(self):
        for filename, i_effective, q_effective, phase in (
            ("vpi_i0p5_q0p7_p140.json", 1.0, 1.4, 140.0),
            ("vpi_i1p4_q2p1_p37.json", 2.8, 4.2, 37.0),
        ):
            with self.subTest(scenario=filename):
                cfg = load_config(ROOT / "configs" / filename)
                actual = cfg.derived()
                self.assertEqual(actual["i_effective_bias_v"], i_effective)
                self.assertEqual(actual["q_effective_bias_v"], q_effective)
                self.assertAlmostEqual(actual["p_source_bias_v"], phase * 5 / 180)
                self.assertEqual(actual["p_effective_pilot_vpeak"], 0)
                self.assertEqual(actual["fft_bin_width_hz"], 10)
                self.assertEqual(actual["adc_bin_width_hz"], 50)

    def test_cli_overrides_scenario_and_updates_snapshot_values(self):
        args = spectrum_args(["--config", str(ROOT / "configs/vpi_i0p5_q0p7_p140.json"),
                              "--i-source-bias", "1.2", "--p-phase-deg", "37", "--vpi", "6",
                              "--no-add-model-noise"])
        self.assertEqual(args.project_config.drive.i_source_bias_v, 1.2)
        self.assertEqual(args.project_config.drive.q_source_bias_v, 0.7)
        self.assertAlmostEqual(args.p_source_bias, 37 * 6 / 180)
        self.assertEqual(args.project_config.drive.p_phase_deg, 37)
        self.assertFalse(args.project_config.sampling.add_model_noise)

    def test_legacy_parent_voltage_is_converted_once(self):
        args = spectrum_args(["--p-source-bias", "0.1", "--parent-source-gain", "2"])
        self.assertAlmostEqual(args.p_phase_deg, 7.2)
        self.assertAlmostEqual(args.project_config.derived()["p_effective_bias_v"], 0.2)

    def test_entries_share_defaults_and_keep_sampling_domains_separate(self):
        spectrum, findpoint = spectrum_args([]), findpoint_args([])
        self.assertEqual((spectrum.fs, spectrum.t_total), (findpoint.fs, findpoint.t_total))
        self.assertEqual(spectrum.responsivity, tia_args([]).responsivity)
        self.assertEqual(spectrum.rin_db_hz, visibility_args([]).rin_db_hz)
        self.assertEqual(findpoint.scan_step, 0.05)
        self.assertEqual(findpoint.edge_points, validate_args([]).edge_points)
        self.assertEqual(validate_args(["--edge-points", "2"]).project_config.findpoint.edge_points, 2)
        self.assertEqual(findpoint.p_dither_amp, 0.025)
        self.assertEqual(spectrum.p_dither_source_amp, 0.0)
        self.assertEqual(adc_args(["--sample-rate", "16000"]).sample_rate, 16000)
        self.assertEqual(adc_args([]).project_config.sampling.fs_hz, spectrum.fs)
        self.assertEqual(visibility_args([]).rf_ohm, 100000)
        self.assertEqual(spectrum.tia_ohm, 10000)

    def test_resolved_snapshot_can_be_loaded(self):
        cfg = spectrum_args(["--p-phase-deg", "73", "--rng-seed", "5"]).project_config
        with tempfile.TemporaryDirectory() as folder:
            snapshot = save_config_snapshot(cfg, Path(folder))
            self.assertEqual(load_config(snapshot), cfg)
            saved = json.loads(snapshot.read_text(encoding="utf-8"))
            self.assertEqual(saved["config"]["drive"]["p_phase_deg"], 73)

    def test_bad_configs_are_rejected(self):
        invalid = [
            {"drive": {"i_effective_bias_v": 1}},
            {"physical": {"vpi_v": 0}},
            {"sampling": {"fs_hz": "1 MHz"}},
            {"sampling": {"add_model_noise": "false"}},
            {"sampling": {"t_total_s": 0.0123}},
            {"findpoint": {"scan_step_source_v": 0}},
            {"adc": {"window": "hann"}},
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            for values in invalid:
                with self.subTest(config=values):
                    path.write_text(json.dumps(values), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_config(path)

    def test_conflicting_phase_flags_and_wrong_tia_profile_fail(self):
        for flags in (["--p-phase-deg", "37", "--p-source-bias", "1"],
                      ["--config", str(ROOT / "configs/hardware.json")],
                      ["--vpi", "0"], ["--p-phase-deg", "nan"]):
            with self.subTest(flags=flags), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    spectrum_args(flags)
                self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
