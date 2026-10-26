# VPI 数据对齐操作规程

版本：2026-07-15

## 0. 文档用途

本文是 VPI 仿真曲线与 Python 离线仿真曲线的数据对齐 SOP。

目标不是重新推导模型，而是固定每次对齐时必须统一的参数、读数口径、换算列和记录方式，避免再次出现 peak/RMS、单端/差分、1 ohm/50 ohm、TIA 参数混用造成的歧义。

## 1. 固定结论

每次做 VPI 与 Python 对齐时，先默认采用以下结论：

| 项目 | 固定口径 |
|---|---|
| VPI 单频分析器 | `TwoPortAnalyzerEl` 输出 `magnitude (rms)` |
| VPI TIA 跨阻 | `Z_TIA = 10 kOhm` |
| 真实硬件 TIA | 原理图为 `100 kOhm`，只用于真实实验链路建模，不用于当前 VPI 对齐 |
| TIA 输出 | 差分输出，`Vdiff = Z_TIA * i_pd`，单端输出为 `Vsingle = Vdiff / 2` |
| VPI `10log10(x*x)+30` | 等效 `1 ohm` RMS 电压功率口径 |
| peak 到 RMS | `RMS = peak / sqrt(2)`，功率读数相差 `3.0103 dB` |
| 1 ohm 到 50 ohm | `dBm_50ohm = dB_1ohm - 16.9897 dB` |

后续默认比较 RMS，不再用 peak 作为主口径。

## 2. 仿真参数对齐

每次对齐前，先确认 VPI 和 Python 使用同一组物理参数：

| 参数 | 当前 VPI 对齐值 |
|---|---:|
| `Pin_dBm` | `10 dBm` |
| `Vpi` | `5 V` |
| `ER_dB` | `30 dB` |
| `IL_I_dB` | `6 dB` |
| `IL_Q_dB` | `6 dB` |
| `IL_P_dB` | `0 dB` |
| PD responsivity | `0.8 A/W` |
| VPI TIA | `10 kOhm` |

导频源端口径：

| 路径 | VPI 源端口径 | Python 映射 |
|---|---|---|
| I/Q 子 MZM | 上臂 `+Vpeak`，下臂 `-Vpeak`，`NEGATIVE` | `effective = 2 * source` |
| P 路相位块 | `POSITIVE` | `effective = 1 * source` |

当前低频设置：

| 频点 | 当前值 |
|---|---:|
| `f_I` | `1.0 kHz` |
| `f_Q` | `1.2 kHz` |
| `f_P` | `1.3 kHz` |
| Step 2 I-P 交调 | `f_I + f_P = 2.3 kHz` |
| Step 3 P 二阶 | `2 f_P = 2.6 kHz` |

## 3. 每次对齐前必须记录

从 VPI 图或 VPI 工程中记录以下信息：

| 记录项 | 说明 |
|---|---|
| `case_id` | 当前对齐点唯一名称，例如 `step1_i_peak_001` |
| `step` | 对应流程，例如 `step1_i_bridge`、`step1_q_bridge` |
| 扫描路 | I、Q 或 P |
| 固定偏置 | 未扫描的 I/Q/P 偏置 |
| 扫描范围和步长 | VPI 曲线横轴设置 |
| 导频幅度 | 源端 `Vpeak` 或 a.u. |
| 读取频点 | 例如 `1 kHz`、`1.2 kHz`、`2.3 kHz` |
| analyzer 接法 | 单端 `out+` / `out-`，或差分 `out+ - out-` |
| VPI 后处理公式 | 例如 `10log10(x*x)+30` |
| 光标读数 | VPI 图上的 Y 值 |

没有这些信息，不判断“是否对齐”，只标记为“信息不足”。

## 4. Python 输出列选择

优先按下表选择比较列：

| VPI 图来源 | 首选 Python 列 |
|---|---|
| TIA 后、单端 analyzer、`10log10(x*x)+30` | `VPI_single_rms_1ohm_dB` |
| TIA 后、差分 analyzer、`10log10(x*x)+30` | `VPI_diff_rms_1ohm_dB` |
| 历史实验图，标注 `Equivalent power (dBm, 50 Ohm)` | `TIA_single_signal_dBm_50ohm` 或 `TIA_diff_signal_dBm_50ohm` |
| ADC 后 RMS 等效读数 | `ADC_vpi_rms_xx_plus30_dB` |

禁止把以下列直接互相比：

| 不可直接比较 | 原因 |
|---|---|
| `VPI_single_peak_1ohm_dB` vs VPI `TwoPortAnalyzerEl` | VPI analyzer 是 RMS，不是 peak |
| `dBm_50ohm` vs `10log10(x*x)+30` | 前者除以 `50 ohm`，后者等效 `1 ohm` |
| `100 kOhm` TIA 曲线 vs 当前 VPI TIA 图 | 当前 VPI TIA 是 `10 kOhm` |
| 原始 PD 电流功率 vs TIA 输出电压图 | 物理观测层级不同 |

## 5. 推荐操作流程

### 5.1 生成或更新离线曲线

先保证离线仿真使用 VPI 对齐参数，尤其是：

```text
IL_P_dB = 0
Responsivity = 0.8 A/W
Z_TIA = 10 kOhm
TwoPortAnalyzerEl = RMS
```

若只需要重新生成 TIA 对齐曲线，使用：

```powershell
python simulation_validation/tia_experimental_curves.py --rf-ohm 10000 --out-dir simulation_validation/results/tia_curves_vpi_10kohm --report simulation_validation/results/tia_curves_vpi_10kohm_report.md
```

### 5.2 填写 VPI 参考点

将 VPI 光标读数填入：

```text
simulation_validation/vpi_reference_points_template.csv
```

必填字段：

```text
enabled
case_id
step
vpi_value
expected_load_ohm
bias
tia_csv
analyzer_connection
vpi_formula
expected_python_column
note
```

当前 `expected_load_ohm` 对 VPI `10log10(x*x)+30` 图应填：

```text
1
```

### 5.3 运行自动匹配

```powershell
python simulation_validation/vpi_alignment_batch.py
```

输出位置：

```text
simulation_validation/results/vpi_alignment_batch/vpi_alignment_batch_report.md
simulation_validation/results/vpi_alignment_batch/vpi_alignment_batch_summary.csv
simulation_validation/results/vpi_alignment_batch/vpi_alignment_batch_conventions.csv
```

### 5.4 判断是否对齐

单点判断：

```text
abs(error_dB) <= 1.0 dB
```

多点锁定：

```text
至少 3 个 VPI 点
全部指向同一读数口径
最大 abs(error_dB) <= 1.0 dB
```

若误差接近 `3.0103 dB`，优先检查 peak/RMS 是否混用。

若误差接近 `6.0206 dB`，优先检查单端/差分是否混用。

若误差接近 `16.9897 dB`，优先检查 1 ohm/50 ohm 是否混用。

若误差接近 `20 dB`，优先检查 VPI TIA 是否把 `10 kOhm` 和真实硬件 `100 kOhm` 混用。

## 6. 结果归档规则

每次完成一次 VPI 对齐后，至少归档以下内容：

| 文件 | 内容 |
|---|---|
| VPI 截图或导出数据 | 原始 VPI 曲线证据 |
| 对应 Python CSV | 离线仿真输出 |
| 对应 Python PNG | 离线曲线图 |
| `vpi_alignment_batch_summary.csv` | 自动匹配摘要 |
| `vpi_alignment_batch_report.md` | 人可读报告 |
| 结论备注 | 使用的读数口径、误差、是否通过 |

推荐结论格式：

```text
case_id:
VPI value:
Python column:
Python value:
error:
judgement:
notes:
```

## 7. 当前已确认案例

当前 I 路全域扫描案例：

```text
条件：Q = 1.367 V, P = 0 V, I pilot source = 0.025 Vpeak
Python peak 口径：7.986969 dB
Python RMS 口径：4.976670 dB
VPI 图读数：约 5 dB
结论：3 dB 差异来自 peak/RMS 口径；RMS 口径对齐
```

当前 Q 路全域扫描案例：

```text
条件：I = 1.367 V, P = 0 V, Q pilot source = 0.025 Vpeak
Python RMS 口径：4.823321 dB
VPI 图读数：约 5 dB 量级
结论：I/Q 一阶曲线在 RMS 口径下量级一致
```

## 8. 后续更新规则

1. 新发现的口径差异先写入本文，再改脚本默认行为；
2. 历史判断如果被新证据推翻，要保留但标注为 legacy；
3. 所有新曲线默认输出 RMS 主图，peak 只作为参考列或诊断列；
4. 与真实实验对齐时，另建实验口径小节，不覆盖 VPI 对齐口径。
