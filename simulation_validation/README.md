# 找点流程离线仿真验证

本目录用于把已经固定的 Step 1-4 找点理论流程转成可执行的离线验证流程。

当前验证器不修改 DPMZM 物理模型，只读取已有 CSV 曲线并输出找点结果。

物理模型现已纳入项目根目录的 `dpmzm/`，各仿真入口默认使用仓库内模型。
安装依赖、测试和固定工作点复现命令见 [根目录说明](../README.md)。

## 统一配置入口

推荐使用根目录 `run.py`；公共参数来自 `config.py`，场景放在 `configs/`：

```powershell
python run.py config --config configs/vpi_i1p4_q2p1_p37.json
python run.py spectrum --config configs/vpi_i1p4_q2p1_p37.json
python run.py findpoint --config configs/findpoint.json
```

上述仿真及 TIA/ADC 后处理脚本继续可用，并接受 `--config`。显式命令行参数覆盖场景值；每次运行保存
`resolved_config.json`。具体字段与硬件配置见 [配置说明](../configs/README.md)。
仿真采样默认统一为 `1 MHz / 0.1 s`；ADC 仍独立使用 `32 kSPS`。
硬件 TIA 后处理的 PD 响应度默认统一为 `0.8 A/W`，随机种子统一为 `0`。

## 数据对齐 SOP

VPI 与 Python 离线仿真对齐时，先按 [VPI数据对齐操作规程.md](./VPI数据对齐操作规程.md) 执行。

该 SOP 固定了以下口径：

- VPI `TwoPortAnalyzerEl` 输出 RMS 幅值；
- 当前 VPI TIA 使用 `10 kOhm`，真实硬件 TIA `100 kOhm` 不混用；
- VPI `10log10(x*x)+30` 是 `1 ohm` RMS 电压等效口径；
- 默认比较 `VPI_single_rms_1ohm_dB` 或 `VPI_diff_rms_1ohm_dB`。

### 同参数模型复核

```powershell
python simulation_validation/vpi_model_recheck.py --out-dir simulation_validation/results/vpi_recheck_20261026
```

该入口复用现有 I/Q 一阶和 P 二阶扫描，固定 `0.025 Vp` 源端导频、
`0.8 A/W` 响应度与 `10 kOhm` 单端 RMS 读数，保存参数、TIA 曲线、
VPI 光标读数表和内部一致性检查结果。
本轮结果见 [复核报告](./results/vpi_recheck_20261026/report.md)。
内部检查和历史约 `5 dB` 的峰值参考不能替代同参数 VPI 全曲线对照；噪底仍需单独验证。

## 链式找点仿真入口

当前推荐先运行链式入口：

```powershell
python simulation_validation/run_chained_findpoint.py
```

该脚本会按顺序执行：

```text
Step 1-I/Q -> Step 2 P 极值点 -> Step 3 I 最小点 -> Step 4 Q 最大点
```

并把每一步输出偏置写入下一步：

- Step 2 固定 `V_DCI_bridge`、`V_DCQ_bridge`；
- Step 3 固定 `V_DCQ_bridge`、`V_DCP_extreme`；
- Step 4 固定 `V_DCI_min`、`V_DCP_extreme`。

当前默认频点：

```text
f_I = 1.0 kHz
f_Q = 1.2 kHz
f_P = 1.3 kHz
f_I + f_P = 2.3 kHz
2f_P = 2.6 kHz
```

输出：

- `simulation_validation/results/chained_findpoint_data/current/manifest.json`
- `simulation_validation/results/chained_findpoint_data/current/step*/`
- `simulation_validation/results/findpoint_summary.json`
- `simulation_validation/results/findpoint_report.md`

`findpoint_validator.py` 会优先读取当前 `manifest.json`，避免旧的 `2.2 kHz / 2.4 kHz` CSV 被默认误选。

## 运行方式

在项目根目录执行：

```powershell
python simulation_validation/findpoint_validator.py
```

默认输出：

- `simulation_validation/results/findpoint_summary.json`
- `simulation_validation/results/findpoint_report.md`

## TIA 可见性验证

在已经生成找点结果后，执行：

```powershell
python simulation_validation/tia_visibility_analyzer.py
```

默认按当前 TIA 原理图估算：

- `R_f = 100 kΩ`
- `C_f = 10 pF`
- `f_c ≈ 159 kHz`
- OPA140 典型噪声参数

输出：

- `simulation_validation/results/tia_visibility_summary.json`
- `simulation_validation/results/tia_visibility_report.md`

## TIA 实验观测曲线

在找点结果和 TIA 可见性验证之后，生成更接近实验观测的带噪声电压曲线：

```powershell
python simulation_validation/tia_experimental_curves.py
```

输出：

- `simulation_validation/results/tia_curves_report.md`
- `simulation_validation/results/tia_curves/*_tia_curve.csv`
- `simulation_validation/results/tia_curves/*_tia_curve.png`

这些曲线不是原始 PD 电流功率图，而是 TIA 输出电压口径：

- TIA 输出信号 RMS；
- TIA 输出噪声底；
- 带随机噪声 bin 的模拟观测曲线；
- TIA 输出 SNR。

## Step 映射

| Step | 输入数据 | 推荐频点 | 判据 | 输出 |
|---|---|---:|---|---|
| Step 1-I | I 路一阶 CSV | `f_I = 1.0 kHz` | 一阶功率主要局部最大值 | `V_DCI_bridge` |
| Step 1-Q | Q 路一阶 CSV | `f_Q = 1.2 kHz` | 一阶功率主要局部最大值 | `V_DCQ_bridge` |
| Step 2 | I-P 交调 CSV | `f_I + f_P = 2.3 kHz` | I-P 交调功率主要局部最小值 | `V_DCP_extreme` |
| Step 3 | P 路二阶 CSV | `2f_P = 2.6 kHz` | P 路二阶功率主要局部最小值 | `V_DCI_min` |
| Step 4 | Q 路一阶 CSV | `f_Q = 1.2 kHz` | Q 一阶功率局部最小值 + 较高 PD 直流功率 | `V_DCQ_max` |

如果尚无扫描 CSV，先运行 `run_chained_findpoint.py` 生成当前数据。
验证器保留仓库内 `artifacts/` 历史数据回退入口，并在报告中记录来源。

注意：当前 `results/` 中的报告已经按 TIA 低频控制口径重新生成。旧的 `12 GHz / 24 GHz` CSV 仍保留在原数据目录中，只作为早期公式验证和旁路频谱口径参考。
## ADS131M02 ADC 链路建模

在已经生成 TIA 实验观测曲线后，继续执行：

```powershell
python simulation_validation/adc_chain_model.py
```

默认参数：

- `fDATA = 32 kSPS`
- `OSR = 128`
- `power mode = HR`
- `PGA gain = 1`
- `VREF = 1.2 V`
- `640点 Goertzel + 无窗 + 10 blocks`
- ADC 输入 RC：`1 kΩ + 1 kΩ` 与差分 `10 nF`

输出：

- `simulation_validation/results/adc_chain_report.md`
- `simulation_validation/results/adc_curves/*_adc_curve.csv`
- `simulation_validation/results/adc_curves/*_adc_curve.png`

该模型用于检查 ADC 满量程、输入 RC 衰减、sinc3 数字滤波、ADC 输入噪声、量化噪声和 50 Ω 等效 dBm 读数。

## VPI 导频幅度口径

导频幅度必须按每个对齐案例记录，不再只依赖脚本默认值。当前 VPI 对齐案例常用源端 `0.025 Vpeak`，对应 I/Q 有效差分 `0.05 Vpeak`。

I/Q 子 MZM 为 `LowerArmPhaseSense = NEGATIVE`，上下臂相位变化相反，离线模型用 `child_source_gain = 2` 映射为有效差分驱动：

```text
V_child_effective_peak = 2 * V_child_source_peak
```

例如 VPI 源端 `0.025 Vpeak` 与离线 I/Q `source_amp = 0.025, child_source_gain = 2` 是同一口径；不要再把 I/Q 导频幅度额外除以 2。

## VPI TIA 对齐口径

真实硬件原理图中的 TIA 反馈电阻为 `100 kΩ`，用于后续真实实验链路建模。当前 VPI TIA 模块参数为：

```text
Transimpedance = 10 kΩ
```

因此和 VPI 曲线对齐时，不应使用默认 `100 kΩ` TIA 曲线，而应使用已生成的 VPI 专用曲线：

```text
simulation_validation/results/tia_curves_vpi_10kohm/
simulation_validation/results/tia_curves_vpi_10kohm_report.md
```

生成命令：

```powershell
python simulation_validation/tia_experimental_curves.py --rf-ohm 10000 --out-dir simulation_validation/results/tia_curves_vpi_10kohm --report simulation_validation/results/tia_curves_vpi_10kohm_report.md
```

`vpi_reference_points_template.csv` 中的旧 Step1-I 参考点已禁用并标记为 legacy。后续只启用按 RMS 口径重新读取的 VPI 光标点。
## 2026-07-15：VPI TwoPortAnalyzerEl RMS 口径

VPI `TwoPortAnalyzerEl` 文档说明单频检测结果是 `magnitude (rms)`，因此后续与 VPI 曲线对齐时，默认使用 RMS 电压口径，而不是 peak 口径。

- TIA 单端 RMS、1 ohm 口径：`VPI_single_rms_1ohm_dB`
- TIA 差分 RMS、1 ohm 口径：`VPI_diff_rms_1ohm_dB`
- 原 `single peak` 曲线需要整体减去 `3.0103 dB` 才能和 VPI analyzer 的 RMS 输出比较。

当前 I 路全域扫描在 RMS 口径下峰值为 `4.976670 dB`，与 VPI 图中约 `5 dB` 的峰值基本一致。
