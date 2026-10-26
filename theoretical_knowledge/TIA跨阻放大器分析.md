# TIA 跨阻放大器分析

## 0. 文档用途

本文用于分析 PD 后级跨阻放大器对找点流程的影响。

本文只固定理论口径和参数定义，不直接修改仿真代码。后续只有在本文确认后，才把 TIA 模块加入离线仿真验证器或 DPMZM 仿真模型。

本文关注四件事：

1. TIA 把 PD 电流转换成输出电压的增益口径；
2. TIA 的带宽限制；
3. TIA 引入的额外噪声；
4. TIA 对 Step 1-4 找点信号可见性的影响。

## 1. 电路参数

根据当前原理图，PD 后级读出链路可整理为：

| 项目 | 原理图标号 | 数值 | 作用 |
|---|---|---:|---|
| 运放 | U4 | OPA140AIDBVR | JFET 输入精密运放 |
| 反馈电阻 | R10 | `100 kΩ` | 主要跨阻增益 |
| 反馈电容 | C21 | `10 pF` | 限制 TIA 带宽并保证稳定性 |
| 输入耦合电容 | C19 | `10 uF` | PD 信号 AC 耦合到 TIA 输入 |
| PD 偏置滤波电阻 | R4 | `100 Ω` | PD 偏置供电隔离 |
| PD 偏置滤波电容 | C20 | `10 uF` | PD 偏置去耦 |
| PD+ 分压/监测电阻 | R6, R9 | `5 kΩ`, `5 kΩ` | 形成中点监测或偏置参考 |
| 供电 | U4 | `±12 V` | 运放供电 |

OPA140 关键参数需要从 datasheet 固定。当前可先采用 TI 官方页面和 datasheet 中的典型值：

| 参数 | 符号 | 典型值 | 用途 |
|---|---|---:|---|
| 增益带宽积 | `GBW` | `11 MHz` | 判断 TIA 稳定性和高频噪声增益 |
| 转换速率 | `SR` | `20 V/us` | 判断大信号输出能力 |
| 输入电压噪声密度 | `e_n` | `5.1 nV/sqrt(Hz)` at 1 kHz | 运放电压噪声 |
| 输入电流噪声密度 | `i_n` | `0.8 fA/sqrt(Hz)` at 1 kHz | 运放输入电流噪声 |
| 输入偏置电流 | `I_B` | max `10 pA` at 25 C | DC 偏置误差和低频漂移 |

参考来源：

- [TI OPA140 product page](https://www.ti.com/product/OPA140)
- [TI OPAx140 datasheet PDF](https://www.ti.com/lit/ds/symlink/opa140.pdf)

## 2. 增益口径

跨阻放大器的本体增益不是普通电压增益，而是电流到电压的跨阻：

```text
V_out = -Z_TIA(f) · I_PD
```

反馈网络为 `R_f` 与 `C_f` 并联时：

```text
Z_TIA(f) = R_f / (1 + j 2π f R_f C_f)
```

幅值为：

```text
|Z_TIA(f)| = R_f / sqrt(1 + (f / f_c)^2)
```

其中：

```text
f_c = 1 / (2π R_f C_f)
```

代入 `R_f = 100 kΩ`、`C_f = 10 pF`：

```text
f_c ≈ 159 kHz
```

因此低频跨阻约为：

```text
|Z_TIA(低频)| ≈ 100 kΩ
```

跨阻本体用 `dBΩ` 表示：

```text
Z_TIA,dBΩ = 20log10(|Z_TIA| / 1Ω)
```

低频时：

```text
20log10(100 kΩ / 1Ω) = 100 dBΩ
```

如果把 TIA 输出与“PD 电流直接流过 50Ω 负载”相比，则电压提升为：

```text
Gain_vs_50Ω = 20log10(|Z_TIA| / 50Ω)
```

低频时：

```text
20log10(100 kΩ / 50Ω) = 66.02 dB
```

因此：

> `66.02 dB` 是相对于 50Ω 直接读出的电压/功率提升口径，不是跨阻本体的 `dBΩ` 口径。跨阻本体应写为 `100 kΩ = 100 dBΩ`。

## 3. 带宽影响

由 `R_f = 100 kΩ` 和 `C_f = 10 pF` 得到：

```text
f_c ≈ 159 kHz
```

典型频点下的跨阻幅值约为：

| 频率 | `|Z_TIA(f)|` | 相对低频衰减 | 相对 50Ω 增益 |
|---:|---:|---:|---:|
| `2.3 kHz` | `≈ 99.99 kΩ` | `≈ 0 dB` | `≈ 66.02 dB` |
| `159 kHz` | `≈ 70.7 kΩ` | `-3 dB` | `≈ 63.01 dB` |
| `1 MHz` | `≈ 15.7 kΩ` | `≈ -16.1 dB` | `≈ 49.9 dB` |
| `12 GHz` | `≈ 1.33 Ω` | `≈ -97.5 dB` | `≈ -31.5 dB` |
| `24 GHz` | `≈ 0.66 Ω` | `≈ -103.6 dB` | `≈ -37.6 dB` |

结论：

1. 该 TIA 适合低频导频、低频拍频、包络或控制通道读出；
2. 该 TIA 不适合直接读出 `12 GHz` 或 `24 GHz` 电谱导频；
3. 如果后续真实系统经过该 TIA，则导频频率需要落在 TIA 有效带宽内，或高频频谱需要通过另一条旁路读出。

这对当前仿真非常重要：当前 CSV 中的 `12 GHz`、`24 GHz` 导频结果，不能简单乘上 `66.02 dB` 后当作 TIA 输出。对于 TIA 通道，应重新定义低频导频或低频拍频读出口径。

## 4. AC 耦合影响

原理图中 PD+ 到 TIA 输入之间存在 `C19 = 10 uF` 串联电容，因此该通道更接近 AC 耦合读出。

这意味着：

1. PD 直流平均光功率不能直接从 TIA 输出获得；
2. `P_pd_avg_dBm` 仍然需要通过独立 DC 监测路径或仿真中的光功率平均值得到；
3. TIA 输出主要用于观察导频、交调、拍频等交流分量；
4. 低频端还会受到 `C19` 与前级等效阻抗形成的高通影响。

若近似用 `R6 || R9 = 2.5 kΩ` 估计输入 AC 耦合高通：

```text
f_HP ≈ 1 / (2π · 2.5 kΩ · 10 uF) ≈ 6.4 Hz
```

该估算只用于量级判断，真实高通还与 PD 等效阻抗、偏置网络、连接方式和运放虚地有关。

## 5. 信号换算

对于某个导频或交调电流峰值 `I_tone_peak`，TIA 输出电压峰值为：

```text
V_tone_peak(f) = |Z_TIA(f)| · I_tone_peak
```

若按正弦信号 RMS 计算：

```text
V_tone_rms(f) = V_tone_peak(f) / sqrt(2)
```

如果后级使用 `R_meas` 作为电压功率换算阻抗，则：

```text
P_tone_out = V_tone_rms^2 / R_meas
```

```text
P_tone_out,dBm = 10log10(P_tone_out / 1mW)
```

如果后级是 ADC 高阻输入，则不应优先使用 dBm，而应使用：

```text
V_tone_peak
V_tone_rms
V_noise_rms
SNR_dB
```

作为主判据。

## 6. 噪声模型

TIA 输出噪声不能只沿用当前仿真中的 PD 电流噪声。至少需要考虑以下噪声项。

### 6.1 PD shot noise

PD 平均电流为：

```text
I_PD,avg = Responsivity · P_PD,avg
```

shot noise 电流密度：

```text
i_shot = sqrt(2 q I_PD,avg)
```

单位为 `A/sqrt(Hz)`。

对应 TIA 输出电压噪声密度：

```text
e_shot,out(f) = |Z_TIA(f)| · i_shot
```

### 6.2 RIN noise

若激光相对强度噪声为 `RIN_dB/Hz`：

```text
i_RIN = I_PD,avg · sqrt(10^(RIN_dB/10))
```

对应输出：

```text
e_RIN,out(f) = |Z_TIA(f)| · i_RIN
```

### 6.3 反馈电阻热噪声

反馈电阻的等效输入电流噪声密度：

```text
i_Rf = sqrt(4 k T / R_f)
```

代入 `R_f = 100 kΩ`、`T = 290 K`：

```text
i_Rf ≈ 0.40 pA/sqrt(Hz)
```

对应低频输出电压噪声密度：

```text
e_Rf,out ≈ sqrt(4 k T R_f)
```

代入后：

```text
e_Rf,out ≈ 40 nV/sqrt(Hz)
```

该项通常是低电流读出时的重要噪声来源。

### 6.4 运放输入电流噪声

OPA140 输入电流噪声密度约为：

```text
i_n,op ≈ 0.8 fA/sqrt(Hz)
```

低频输出贡献：

```text
e_in,out(f) = |Z_TIA(f)| · i_n,op
```

代入 `100 kΩ` 时约为：

```text
0.08 nV/sqrt(Hz)
```

该项远小于反馈电阻热噪声，通常不是主导项。

### 6.5 运放输入电压噪声

OPA140 输入电压噪声密度约为：

```text
e_n,op ≈ 5.1 nV/sqrt(Hz) at 1 kHz
```

在 TIA 中，运放电压噪声通过 noise gain 放大：

```text
e_en,out(f) = |NG(f)| · e_n,op
```

其中 `NG(f)` 与反馈网络、PD 电容、运放输入电容、PCB 寄生电容有关。当前原理图没有给出 PD 电容和输入总电容，因此这一项需要后续补参。

低频且忽略输入电容时，可先近似：

```text
NG(f) ≈ 1
```

但在高频端，输入电容会抬高 noise gain，可能导致噪声上升或稳定性变差。

### 6.6 总输出噪声

一阶近似可写为：

```text
e_n,out^2(f)
≈ |Z_TIA(f)|^2 · (i_shot^2 + i_RIN^2 + i_Rf^2 + i_n,op^2)
  + |NG(f)|^2 · e_n,op^2
  + e_n,ADC^2
  + e_n,inst^2
```

其中 `e_n,ADC` 和 `e_n,inst` 分别表示 ADC 或后级仪器噪声。

对频谱 bin：

```text
V_noise_rms,bin = e_n,out · sqrt(ENBW)
```

如果要换算成 dBm：

```text
P_noise_bin,dBm = 10log10((V_noise_rms,bin^2 / R_meas) / 1mW)
```

如果后级不是 50Ω 频谱仪，而是 ADC 高阻输入，则建议保留 `V/sqrt(Hz)`、`V_rms` 和 `SNR_dB`，不要强行写 dBm。

## 7. 与当前仿真的关系

当前 `python-mzm-main/dpmzm` 模型输出的是：

```text
P_PD(t) -> I_PD(t) -> 电谱功率
```

其中：

```text
I_PD(t) = Responsivity · P_PD(t)
```

当前模型没有包含：

1. TIA 跨阻；
2. TIA 带宽；
3. TIA 反馈电阻热噪声；
4. 运放输入电压/电流噪声；
5. ADC 或后级仪器噪声；
6. 输出摆幅和饱和限制。

因此，当前报告中的 `P_noise_floor_dBm` 只能表示“PD 电流直接进入电谱计算口径”的噪底，不能代表真实 TIA 后输出噪底。

后续加入 TIA 后，仿真结果至少应增加以下字段：

| 字段 | 含义 |
|---|---|
| `R_f_ohm` | 反馈电阻 |
| `C_f_F` | 反馈电容 |
| `f_TIA_Hz` | 当前观测频率 |
| `Z_TIA_ohm` | 当前频率跨阻幅值 |
| `V_tone_peak_V` | TIA 输出导频峰值 |
| `V_tone_rms_V` | TIA 输出导频 RMS |
| `e_noise_out_V_per_sqrtHz` | 输出噪声密度 |
| `V_noise_rms_bin_V` | 当前 ENBW 下的输出噪声 |
| `SNR_TIA_dB` | TIA 输出端信噪比 |
| `TIA_saturation_flag` | 是否可能饱和 |
| `TIA_bandwidth_flag` | 观测频点是否超出有效带宽 |

## 8. 对 Step 1-4 的影响

### 8.1 TIA 控制频率规划

当前建议将真实控制导频设置为：

| 频率项 | 推荐值 | 用途 | TIA 适配性 |
|---|---:|---|---|
| `f_I` | `1.0 kHz` | Step 1-I 的 I 路一阶；Step 2 的 I-P 交调 | 在通带内 |
| `f_P` | `1.3 kHz` | Step 2 的 P 路导频；Step 3 的 P 路二阶 | 在通带内 |
| `f_Q` | `1.2 kHz` | Step 1-Q 和 Step 4 的 Q 路一阶 | 在通带内 |
| `f_I + f_P` | `2.3 kHz` | Step 2 推荐读取的 I-P 交调频点 | 在通带内 |
| `|f_I - f_P|` | `0.2 kHz` | Step 2 可选交调频点 | 在通带内，但更靠近低频漂移 |
| `2f_P` | `2.6 kHz` | Step 3 的 P 路二阶频点 | 在通带内 |

其中 `f_I = 1.0 kHz` 是当前 Step 1-I 的推荐值，`f_P = 1.3 kHz` 用于避免 P 路与 Q 路同频，同时保留 Step 2 中 `f_I + f_P = 2.3 kHz` 的交调观测口径。

### 8.2 Step 影响

| Step | 当前观测量 | 加入 TIA 后的影响 |
|---|---|---|
| Step 1：I/Q bridge | I/Q 一阶导频功率 | 若仍使用 12 GHz 导频，TIA 无法直接读出；需要低频导频或旁路频谱读出 |
| Step 2：P 极值点 | I-P 交调功率谷值 | 若交调为 kHz 级，TIA 适合读出，并且会显著提高电压信号 |
| Step 3：I 最小点 | P 路二阶功率谷值 | 若二阶频点为 24 GHz，TIA 无法直接读出；需要改成低频 P 导频二阶或使用旁路读出 |
| Step 4：Q 最大点 | Q 一阶谷值 + PD 直流 | TIA 可读交流谷值，但 PD 直流需要独立 DC 监测路径 |

关键结论：

> 如果真实控制链路只经过该 TIA，那么控制导频频率应设计在 TIA 带宽内。当前用于公式验证的 `12 GHz` 和 `24 GHz` 电谱频点更适合看作 VPI/频谱分析口径，不适合直接作为该 TIA 输出口径。

## 9. 后续需要补齐的实测或器件参数

在写代码前，需要确认：

1. PD 型号和响应度 `Responsivity`；
2. PD 结电容 `C_PD`；
3. OPA140 实际封装和供电；
4. ADC 或频谱仪输入阻抗；
5. ADC 采样率、满量程、量化位数；
6. 实际控制导频频率；
7. 实际 ENBW 或数字滤波带宽；
8. TIA 输出是否进入 ADC 高阻输入，还是 50Ω 频谱仪；
9. 是否存在额外后级电压增益或滤波；
10. 输出摆幅限制和饱和恢复策略。

## 10. 建模建议

后续代码中不要把 TIA 简化为固定 `+66.02 dB`。

建议建模顺序为：

```text
PD current tone
    -> AC coupling high-pass
    -> Z_TIA(f)
    -> TIA noise model
    -> output voltage
    -> ADC / spectrum analyzer口径
    -> SNR and quality flags
```

第一版代码可以先实现简化模型：

```text
Z_TIA(f) = R_f / (1 + j2πfR_fC_f)
e_noise_out^2 = |Z_TIA|^2 · (i_shot^2 + i_RIN^2 + i_Rf^2 + i_n,op^2) + e_n,op^2
```

并先输出电压域指标：

```text
V_tone_rms
V_noise_rms
SNR_TIA_dB
```

等真实后级输入阻抗和 ADC 口径确定后，再统一换算 dBm。

## 11. 离线可见性验证入口

当前已建立第一版 TIA 可见性验证脚本：

```text
simulation_validation/tia_visibility_analyzer.py
```

运行方式：

```powershell
python simulation_validation/tia_visibility_analyzer.py
```

该脚本读取：

```text
simulation_validation/results/findpoint_summary.json
```

并输出：

```text
simulation_validation/results/tia_visibility_summary.json
simulation_validation/results/tia_visibility_report.md
```

当前脚本只做一阶估算：

1. 使用 `R_f // C_f` 计算 `Z_TIA(f)`；
2. 使用选中行的 `I_tone_peak_A` 或 `I_2p2k_peak_A` 计算 TIA 输出电压；
3. 使用 PD shot noise、RIN、反馈电阻热噪声、OPA140 电压/电流噪声估算输出噪声；
4. 给出 `TIA_PASSBAND`、`TIA_ROLL_OFF`、`TIA_OUT_OF_BAND` 标记。

该脚本不替代完整电路仿真，只用于判断当前找点观测频点是否适合经过该 TIA 通道。
