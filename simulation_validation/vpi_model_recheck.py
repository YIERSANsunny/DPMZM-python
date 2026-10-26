"""Regenerate explicit-parameter TIA curves for comparison with VPI exports.

Internal consistency checks and approximate historical VPI peaks are reported
separately. A Python self-check cannot certify agreement with VPI measurements.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SIM_ROOT = ROOT
COMMON = dict(
    child_source_gain=2.0, parent_source_gain=1.0, Vpi=5.0,
    ER_dB=30.0, IL_dB=0.0, IL_I_dB=6.0, IL_Q_dB=6.0,
    IL_P_dB=0.0, Pin_dBm=10.0, Responsivity=0.8, pd_tap=1.0,
    R_load=1.0, Fs=1e6, T_total=0.1, er_model="vpi",
    vpi_compatible_dbm=True, Temp_K=290.0, RIN_dB_Hz=-145.0,
)
TIA_OHM = 10000.0


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def db_readout(v_rms):
    return 20.0 * np.log10(np.maximum(v_rms, 1e-150)) + 30.0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dpmzm-root", type=Path, default=DEFAULT_SIM_ROOT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "simulation_validation/results/vpi_model_recheck")
    args = parser.parse_args()
    sys.path.insert(0, str(args.dpmzm_root))
    from dpmzm.core import model
    from dpmzm.experiments.i_pilot_first_sweep import run_i_pilot_first_sweep
    from dpmzm.experiments.q_pilot_first_sweep import run_q_pilot_first_sweep
    from dpmzm.experiments.p_pilot_second_sweep import run_p_pilot_second_sweep
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = [
        dict(name="i_first", function=run_i_pilot_first_sweep, axis="I", target=1000.0,
             biases=[0.0, 1.367, 0.0], amps=[0.025, 0.0, 0.0],
             sweep=dict(V_DCI_source_start=-10.0, V_DCI_source_stop=10.0,
                        V_DCI_source_step=0.05, V_DCQ_source=1.367, V_DCP_source=0.0,
                        V_dither_I_source_amp=0.025, f_dither_I=1000.0)),
        dict(name="q_first", function=run_q_pilot_first_sweep, axis="Q", target=1200.0,
             biases=[1.367, 0.0, 0.0], amps=[0.0, 0.025, 0.0],
             sweep=dict(V_DCQ_source_start=-10.0, V_DCQ_source_stop=10.0,
                        V_DCQ_source_step=0.05, V_DCI_source=1.367, V_DCP_source=0.0,
                        V_dither_Q_source_amp=0.025, f_dither_Q=1200.0)),
        dict(name="p_second", function=run_p_pilot_second_sweep, axis="I", target=2600.0,
             biases=[0.0, -1.55, 0.1], amps=[0.0, 0.0, 0.025],
             sweep=dict(V_DCI_source_start=-10.0, V_DCI_source_stop=10.0,
                        V_DCI_source_step=0.05, V_DCQ_source=-1.55, V_DCP_source=0.1,
                        V_dither_P_source_amp=0.025, f_dither_P=1300.0)),
    ]
    manifest = dict(
        common=COMMON, tia_ohm=TIA_OHM, readout="single-ended RMS, 1 ohm equivalent",
        noise_scope="Deterministic signals; noise estimates are not used as measured curves.",
        sampling="1 MSa/s, 0.1 s, rectangular window; 10 Hz coherent bins",
        scan="source -10..10 V, step 0.05 V; child effective step 0.1 V",
        model_path=str(Path(model.__file__).resolve()),
        model_sha256=hashlib.sha256(Path(model.__file__).read_bytes()).hexdigest(),
        vpi_validation="PENDING_POINTWISE_VPI_DATA",
        cases=[], checks=[],
    )
    figure, axes = plt.subplots(3, 1, figsize=(10, 11), constrained_layout=True)
    marker_rows = []
    peak_rows = []
    curves = []
    for case, ax in zip(cases, axes):
        folder = out_dir / case["name"]
        result = case["function"](out_dir=folder, **COMMON, **case["sweep"])
        with Path(result["csv_path"]).open(encoding="utf-8", newline="") as stream:
            raw = list(csv.DictReader(stream))
        bias = np.array([float(row[f"V_DC{case['axis']}_source_V"]) for row in raw])
        peak = np.array([float(row["I_tone_peak_A"]) for row in raw])
        v_rms = peak / math.sqrt(2.0) * TIA_OHM / 2.0
        reading = db_readout(v_rms)
        curves.append(peak)
        rows = []
        for index, row in enumerate(raw):
            rows.append(dict(
                case_id=case["name"], bias_source_V=bias[index],
                bias_effective_V=2.0 * bias[index], target_Hz=case["target"],
                I_source_V=float(row["V_DCI_source_V"]),
                Q_source_V=float(row["V_DCQ_source_V"]),
                P_source_V=float(row["V_DCP_source_V"]),
                PD_tone_peak_A=peak[index], PD_tone_rms_A=peak[index] / math.sqrt(2.0),
                PD_mean_optical_dBm=float(row["P_pd_avg_dBm"]),
                TIA_single_V_rms=v_rms[index],
                TIA_single_rms_1ohm_dB=reading[index],
                TIA_single_rms_dBm_50ohm=reading[index] - 10.0 * math.log10(50.0),
            ))
        write_csv(folder / "tia_readout.csv", rows)
        peak_index = int(np.argmax(reading))
        peak_rows.append(dict(case_id=case["name"], python_peak_dB=float(reading[peak_index]),
                              source_V=float(bias[peak_index]),
                              historical_vpi_approx_dB=5.0 if case["name"] != "p_second" else None))
        # Compare the optimized sweeps with direct time-domain simulation at weak and strong points.
        indices = sorted({0, len(raw) // 2, peak_index, int(np.argmin(peak)),
                          int(np.argmin(abs(bias + 7.5)))})
        errors = []
        for index in indices:
            volts = [float(raw[index][f"V_DC{axis}_source_V"]) for axis in "IQP"]
            sim = model.simulate_dpmzm(
                Fs=COMMON["Fs"], T_total=COMMON["T_total"], Vpi=5.0,
                ER_dB=30.0, ER_I_dB=30.0, ER_Q_dB=30.0, ER_P_dB=30.0,
                IL_dB=0.0, IL_I_dB=6.0, IL_Q_dB=6.0, IL_P_dB=0.0,
                Pin_dBm=10.0, Responsivity=0.8, R_load=1.0, pd_tap=1.0,
                V_DCI=2 * volts[0], V_DCQ=2 * volts[1], V_DCP=volts[2],
                V_dither_I_amp=2 * case["amps"][0], V_dither_Q_amp=2 * case["amps"][1],
                V_dither_P_amp=case["amps"][2],
                f_dither_I=1000.0, f_dither_Q=1200.0, f_dither_P=1300.0,
                V_RFI_amp=0.0, V_RFQ_amp=0.0, er_model="vpi", rng_seed=0,
            )
            time = np.arange(sim.I_pd.size) / COMMON["Fs"]
            direct_peak = 2 * abs(np.mean(sim.I_pd * np.exp(-2j * np.pi * case["target"] * time)))
            errors.append(abs(float(direct_peak) - peak[index]))
        check = dict(name=case["name"] + "_sweep_vs_time_domain",
                     max_abs_error_A=max(errors),
                     status="PASS" if max(errors) < 1e-15 else "FAIL")
        manifest["checks"].append(check)
        for voltage in [-7.5, -5.0, -3.6, -1.55, 0.0, 1.55, 2.5, 5.0, 7.5]:
            index = int(np.argmin(abs(bias - voltage)))
            marker_rows.append(dict(
                case_id=case["name"], **{key: rows[index][key] for key in
                    ["I_source_V", "Q_source_V", "P_source_V", "target_Hz"]},
                python_single_rms_1ohm_dB=reading[index], vpi_single_rms_1ohm_dB="",
            ))
        ax.plot(bias, reading, color="#177d91", linewidth=1.4)
        if case["name"] != "p_second":
            ax.axhline(5.0, color="#a33d36", linestyle="--", linewidth=1,
                       label="Historical VPI peak about 5 dB (not a VPI trace)")
            ax.legend(fontsize=8)
        else:
            ax.axvline(-7.5, color="#777777", linestyle=":", linewidth=1)
        fixed = ", ".join(f"{axis}={value:g} V" for axis, value in zip("IQP", case["biases"])
                          if axis != case["axis"])
        ax.set(xlabel=f"{case['axis']} source bias (V)", ylabel="Single RMS, 1 ohm equivalent (dB)",
               title=f"{case['name']} at {case['target']:g} Hz; fixed {fixed}\n"
                     f"Source pilots I/Q/P={case['amps']} Vp")
        ax.grid(alpha=0.25)
        manifest["cases"].append(dict(
            name=case["name"], target_hz=case["target"], biases_source_V=case["biases"],
            pilots_source_Vpeak=case["amps"], sweep=case["sweep"],
            readout_csv=str(folder / "tia_readout.csv"),
            raw_csv=str(result["csv_path"]),
        ))
        print(json.dumps(peak_rows[-1]), flush=True)

    symmetry_error = float(np.max(abs(curves[0] - curves[1])))
    manifest["checks"].append(dict(name="I_Q_swapped_source_symmetry_at_P0",
        max_abs_error_A=symmetry_error, status="PASS" if symmetry_error < 1e-15 else "FAIL"))
    if not (out_dir / "vpi_cursor_points.csv").exists():
        write_csv(out_dir / "vpi_cursor_points.csv", marker_rows)
    manifest["peaks"] = peak_rows
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    figure.savefig(out_dir / "tia_comparison.png", dpi=160)
    plt.close(figure)
    lines = [
        "# VPI / Python 模型复核", "",
        "当前结论：I/Q 一阶的历史峰值量级可复核；尚无逐点 VPI 导出数据，不能认定两个模型全面一致。", "",
        "## 固定参数", "",
        "- Pin=10 dBm；Vpi=5 V；I/Q ER=30 dB；I/Q IL=6 dB；P IL=0 dB；PD=0.8 A/W。",
        "- I/Q 源端 NEGATIVE 映射为两倍有效电压；P 源端按 1:1 映射。",
        "- 扫描源端 -10..10 V、步进 0.05 V，即 I/Q 有效步进 0.1 V。",
        "- Fs=1 MHz；TimeWindow=0.1 s；矩形窗；RBW=10 Hz。",
        "- TIA=10 kOhm，单端 RMS，10log10(Vrms^2)+30；50 ohm 列在此基础上减 16.9897 dB。",
        "- 本轮曲线为确定性信号；模型噪声预算仍为 RIN=-145 dB/Hz、290 K，未叠加成观测曲线。", "",
        "## 对照结果", "",
        "| 案例 | 固定源端偏置 | 开启的源端导频 | Python 峰值 | 历史 VPI 参考 |",
        "|---|---|---|---:|---|",
    ]
    descriptions = [
        ("Q=1.367 V, P=0 V", "I=0.025 Vp @ 1 kHz"),
        ("I=1.367 V, P=0 V", "Q=0.025 Vp @ 1.2 kHz"),
        ("Q=-1.55 V, P=0.1 V", "P=0.025 Vp @ 1.3 kHz; 读 2.6 kHz"),
    ]
    for peak, (biases, pilots) in zip(peak_rows, descriptions):
        reference = "约 5 dB，仅截图量级" if peak["historical_vpi_approx_dB"] is not None else "缺同参数逐点数据"
        lines.append(f"| {peak['case_id']} | {biases} | {pilots} | {peak['python_peak_dB']:.6f} dB | {reference} |")
    lines.extend(["", "## Python 内部检查", ""])
    for check in manifest["checks"]:
        lines.append(f"- {check['name']}: {check['status']}, 最大电流幅度差 {check['max_abs_error_A']:.3g} A。")
    lines.extend([
        "", "## 尚未完成的模型对齐", "",
        "- vpi 模式下 ER_P 虽被读取，delta_P 未进入场传输；P 块为 Q 光路相位调节，主合束默认等权。",
        "- I/Q 一阶的约 5 dB 截图只证明峰值量级接近，不能替代全曲线、谷值位置及 DC 功率的对照。",
        "- 历史 Q 路峰值为 4.823321 dB；统一响应度到 0.8 A/W 后，应与 I 路重算结果一起比较。",
        "- 历史 VPI RIN=-175 dB/Hz，与当前 Python -145 dB/Hz 不同；噪底暂不判定一致。",
        "- TIA 截止频率和 Bessel 阶数未接入当前电压换算；当前频谱脚本按功率叠加噪声，没有相干交叉项。",
        "- 历史部分频谱将三路导频均设为 0.05 Vp，不能与本轮单路 0.025 Vp 直接作峰值对照。", "",
        "## 下一次 VPI 采集", "",
        "1. 按上表分别运行 I 一阶、Q 一阶和 P 二阶；未列出的导频关闭。",
        "2. 扫描源端步进 0.05 V；若 VPI 横轴为上下臂差分，则使用 0.1 V，并换回源端电压比较。",
        "3. 将 vpi_cursor_points.csv 的空白 VPI 读数列补齐，或提供同参数全扫描导出。谷值附近优先比较线性电压和位置。",
        "4. 两路子 MZM 均置于最大传输状态后单独扫 P，再改变 P 块 ER，可检查 ER_P 在 VPI POSITIVE 模式下是否实际改变输出。", "",
        "内部检查通过不代表 VPI 模型对齐通过。manifest.json 保存实际运行参数与模型源码 SHA256。", "",
    ])
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {out_dir / 'report.md'}", flush=True)
    return 1 if any(check["status"] != "PASS" for check in manifest["checks"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
