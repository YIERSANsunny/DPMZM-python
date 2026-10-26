"""Preserve the two deterministic spectra manually checked against VPI."""

import math
import unittest
from types import SimpleNamespace

import numpy as np

from dpmzm import run_analytical_self_check, simulate_dpmzm
from simulation_validation.tia_full_spectrum import _marker_frequencies


class SpectrumBaselineTests(unittest.TestCase):
    def test_analytical_model(self):
        self.assertTrue(run_analytical_self_check()["passed"])

    def test_confirmed_working_points(self):
        frequencies = [200, 1000, 1200, 2000, 2200, 2400]
        cases = [
            (0.5, 0.7, 140.0, [-56.826, -19.572, -15.510, -59.879, -56.826, -75.202]),
            (1.4, 2.1, 37.0, [-41.778, 0.863, 2.442, -66.524, -41.778, -45.613]),
        ]
        for i_source, q_source, phase_deg, expected in cases:
            sim = simulate_dpmzm(
                Fs=1e6, T_total=0.1, Vpi=5.0,
                ER_dB=30.0, IL_dB=0.0, IL_I_dB=6.0, IL_Q_dB=6.0, IL_P_dB=0.0,
                Pin_dBm=10.0, Responsivity=0.8, pd_tap=1.0, R_load=1.0,
                V_DCI=2 * i_source, V_DCQ=2 * q_source, V_DCP=5 * phase_deg / 180,
                V_dither_I_amp=0.05, V_dither_Q_amp=0.05, V_dither_P_amp=0.0,
                f_dither_I=1000.0, f_dither_Q=1200.0, f_dither_P=1300.0,
                V_RFI_amp=0.0, V_RFQ_amp=0.0, er_model="vpi", rng_seed=0,
            )
            bins = np.fft.rfft(sim.I_pd) / sim.I_pd.size
            for frequency, expected_db in zip(frequencies, expected):
                with self.subTest(i=i_source, q=q_source, phase=phase_deg, frequency=frequency):
                    index = int(round(frequency / sim.RBW_Hz))
                    current_rms = math.sqrt(2) * abs(bins[index])
                    single_v_rms = 10000.0 * current_rms / 2.0
                    reading_db = 20 * math.log10(single_v_rms) + 30
                    self.assertAlmostEqual(reading_db, expected_db, delta=0.002)

    def test_disabled_parent_pilot_markers(self):
        params = SimpleNamespace(
            f_i_hz=1000.0, f_q_hz=1200.0, f_p_hz=1300.0,
            i_dither_source_amp_vpeak=0.025,
            q_dither_source_amp_vpeak=0.025, p_dither_source_amp_vpeak=0.0,
        )
        self.assertEqual(_marker_frequencies(params), [0, 200, 1000, 1200, 2000, 2200, 2400])


if __name__ == "__main__":
    unittest.main()
