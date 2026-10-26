# ADS131M02 ADC 链路建模

## 0. 文档用途

本文用于固定 TIA 后级 ADS131M02 ADC 在找点离线仿真中的建模口径。

本文不替代 ADS131M02 datasheet，也不把 ADC 当作完整 delta-sigma 位流仿真；当前目标是回答工程问题：

1. TIA 输出导频/交调项进入 ADC 后是否会削顶；
2. `1.0 kHz`、`1.2 kHz`、`1.3 kHz`、`2.3 kHz`、`2.6 kHz` 是否会被 ADC 采样率和数字滤波影响；
3. ADC 输入噪声和量化噪声是否会影响找点；
4. 离线仿真曲线如何换算成历史实验图中的 `Equivalent power (dBm, 50 Ohm)` 口径。

对应脚本：

- `simulation_validation/adc_chain_model.py`
- `simulation_validation/results/adc_chain_report.md`
- `simulation_validation/results/adc_curves/*_adc_curve.csv`
- `simulation_validation/results/adc_curves/*_adc_curve.png`

## 1. 当前硬件入口

根据原理图，ADC 采用 `ADS131M02`，差分输入前端近似为：

```text
TIA/模拟输入 -> 1 kΩ -> AINxP
GND/参考端   -> 1 kΩ -> AINxN
AINxP 与 AINxN 之间并联 10 nF
```

因此一阶差分抗混叠低通可近似为：

```text
R_diff = R_P + R_N = 2 kΩ
C_diff = 10 nF
f_RC = 1 / (2π R_diff C_diff) ≈ 7.96 kHz
```

在当前控制频点下，RC 衰减大约为：

| 频率 | RC 衰减 |
|---:|---:|
| `1.0 kHz` | `-0.07 dB` |
| `1.2 kHz` | `-0.10 dB` |
| `1.3 kHz` | `-0.11 dB` |
| `2.3 kHz` | `-0.35 dB` |
| `2.6 kHz` | `-0.44 dB` |

结论：RC 前端不会破坏当前低频导频，但需要纳入幅度标定。

## 2. ADS131M02 默认参数

当前已知实际参数：

```text
fDATA = 32 kSPS
PGA gain = 1
OSR = 128
power mode = HR
global chop = 未显式开启
DC block = 未显式开启
输入偏置 = 未显式配置
测量算法 = 640点 Goertzel + 无窗 + 默认10 blocks
```

当前模型将这组参数作为 DPMZM 主线配置。`VREF` 仍按 ADS131M02 典型内部参考 `1.2 V` 建模，`bits = 24`。

由此得到：

```text
fMOD = fDATA * OSR = 4.096 MHz
ADC differential full-scale = ±VREF / Gain = ±1.2 Vpeak
LSB ≈ 143 nV
```

`±1.2 Vpeak` 是当前模型中最重要的限制：任何进入 ADC 的差分信号峰值超过这个值，都标记为 `ADC_CLIPPED`。

640 点 Goertzel 在 `32 kSPS` 下的 bin 间隔为：

```text
Δf = 32000 / 640 = 50 Hz
```

无窗矩形 Goertzel 的 ENBW 等于一个 bin：

```text
ENBW = 50 Hz
```

当前 `1.0 kHz`、`1.2 kHz`、`1.3 kHz`、`2.3 kHz`、`2.6 kHz` 都是 `50 Hz` 的整数倍，因此模型标记为 `ADC_COHERENT_BIN`。

## 3. 数字滤波模型

ADS131M02 是 delta-sigma ADC，调制器之后有 sinc 型数字滤波。当前 `OSR = 128` 时使用 sinc3 近似：

```text
|H_sinc3(f)| =
| sin(π N f / fMOD) / [N sin(π f / fMOD)] |^3
```

其中：

```text
N = OSR
fMOD = fDATA * OSR
```

当前低频下 sinc3 衰减大约为：

| 频率 | sinc3 衰减 |
|---:|---:|
| `1.0 kHz` | `-0.04 dB` |
| `1.2 kHz` | `-0.06 dB` |
| `1.3 kHz` | `-0.07 dB` |
| `2.3 kHz` | `-0.22 dB` |
| `2.6 kHz` | `-0.28 dB` |

结论：ADC 数字滤波对当前找点频点影响较小，但会带来可标定的幅度下降。

## 4. 噪声模型

当前模型包含三类进入 ADC 观测口径的噪声：

1. TIA 输出噪声；
2. ADS131M02 输入参考噪声；
3. ADC 量化噪声。

ADS131M02 datasheet 中 `OSR = 128`、`gain = 1` 的典型输入参考噪声为：

```text
V_ADC_noise,rms ≈ 21.31 uV rms
```

当前脚本把该宽带 RMS 噪声近似摊到 Nyquist 带宽内，再换算到当前 Goertzel bin：

```text
e_ADC,bin ≈ V_ADC_noise,rms / sqrt(fDATA / 2) * sqrt(ENBW)
```

其中当前主线：

```text
ENBW = 50 Hz
```

`10 blocks` 当前按功率平均处理：噪声均值不变，随机起伏降低。若实际算法做的是复数相干平均或幅度平均，需要再调整噪声统计模型。

这是工程近似，不是完整 sigma-delta 噪声整形仿真。真实实验中的空输入噪底仍需要后续校准。

## 5. 输出口径

ADC 实际处理的是电压和数字码值，因此模型保留：

```text
ADC_signal_V_rms
ADC_noise_total_V_rms_bin
ADC_measured_V_rms
ADC_SNR_dB
ADC_fullscale_margin_dB
```

为了和历史实验曲线对齐，同时输出 50 Ω 等效读数：

```text
ADC_signal_dBm_50ohm
ADC_noise_dBm_50ohm
ADC_measured_dBm_50ohm
```

换算公式：

```text
dBm_50ohm = 20log10(V_rms) + 30 - 10log10(50)
           = dBV_rms + 13.0103
```

注意：`dBm_50ohm` 是历史频谱图对比口径，不表示 ADC 内部真的向 50 Ω 负载交付功率。

## 6. 当前建模结果

按当前 TIA 输出和默认 ADC 参数，初步结论为：

| Step | 主要结论 |
|---|---|
| Step 1-I | 选中点超过 ADC 满量程，`ADC_fullscale_margin_dB ≈ -11.2 dB`，会削顶 |
| Step 1-Q | 选中点未削顶，满量程裕量约 `3.9 dB`，SNR 约 `102 dB` |
| Step 2 | I-P 交调谷值可见，选中点 SNR 约 `13 dB` |
| Step 3 | I 路最小点可见，选中点 SNR 约 `15 dB` |
| Step 4 | Q 路最大点可见，选中点 SNR 约 `50 dB` |

这说明当前有两个重点：

1. Step 1-I 幅度过大，会触发 ADC 削顶；
2. Step 2 和 Step 3 在 50 Hz ENBW 下只剩约 `13-15 dB` SNR，后续需要通过实测噪底确认鲁棒性。

## 7. 当前必须确认的问题

下面几个参数会显著改变 ADC 模型结果：

1. ADC 输入是否有中点共模偏置；
2. 如果 TIA 输出是以 `0 V` 为中心的双极性信号，AINN 又接地，则负半周是否会违反 ADS131M02 输入范围；
3. 前端是否还有额外衰减、电阻分压、保护电路或采集前数字缩放；
4. Goertzel 的 10 blocks 是功率平均、幅度平均还是复数相干平均；
5. ADS131M02 空输入实测噪底是多少。

其中第 1、2 项非常重要：如果 ADC 是单电源、AINN 接地，并且没有把 TIA 输出偏置到合法共模范围，那么即使差分幅度不超过 `±1.2 V`，输入绝对电压也可能不合法。当前报告用 `ADC_INPUT_BIAS_NOT_CONFIGURED` 标记这一风险。

## 8. 参考资料

- TI ADS131M02 datasheet: https://www.ti.com/lit/ds/symlink/ads131m02.pdf
