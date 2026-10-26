# VPI 与离线仿真口径对齐

## 0. 文档用途

本文用于固定 VPI 仿真结果与 Python 离线仿真结果的比较口径。当前目标不是修改 DPMZM 物理模型，而是先确认同一个信号在不同读数口径下如何换算。

## 1. TIA 差分输出口径

VPI TIA 模块给出的定义为：

```text
out+ =  Z_TIA * (i_pd + i_noise) / 2
out- = -Z_TIA * (i_pd + i_noise) / 2
```

因此差分输出为：

```text
Vdiff = out+ - out- = Z_TIA * (i_pd + i_noise)
```

离线仿真中的 `TIA_signal_V_peak`、`TIA_signal_V_rms` 保持为差分电压口径，即对应 `Vdiff`。

新增列：

```text
TIA_diff_signal_V_peak
TIA_diff_signal_V_rms
TIA_single_signal_V_peak
TIA_single_signal_V_rms
```

其中单端口径满足：

```text
Vsingle = Vdiff / 2
```

如果 VPI 的 2 Port Analyzer 测的是 `out+ - out-`，应比较 `TIA_diff_*`；如果测的是单端 `out+` 或 `out-`，应比较 `TIA_single_*`。

## 2. 1Ω 与 50Ω 等效功率口径

VPI 中如果后处理为：

```text
y = 10log10(x*x) + 30
```

且 `x` 是 RMS 电压，则它等效于：

```text
dBm_1ohm = 10log10(Vrms^2 / 1Ω) + 30
```

离线仿真原有的 `dBm_50ohm` 为：

```text
dBm_50ohm = 10log10(Vrms^2 / 50Ω) + 30
```

两者差值固定为：

```text
dBm_1ohm - dBm_50ohm = 10log10(50) = 16.9897 dB
```

新增列：

```text
TIA_signal_dBm_1ohm
TIA_signal_dBm_50ohm
TIA_vpi_diff_rms_xx_plus30_dB
TIA_vpi_single_rms_xx_plus30_dB

ADC_signal_dBm_1ohm
ADC_signal_dBm_50ohm
ADC_vpi_rms_xx_plus30_dB
```

## 3. 当前比较原则

1. 如果 VPI 图来自 TIA 后、ADC 前，则优先比较 `TIA_*` 列。
2. 如果 VPI 图包含 ADC 满量程削顶、输入 RC 和数字滤波，则比较 `ADC_*` 列。
3. 如果 VPI 的 `Mag(f)` 是 RMS 电压，则直接比较 `*_dBm_1ohm` 或 `*_vpi_*_xx_plus30_dB`。
4. 如果 VPI 的 `Mag(f)` 是 peak 电压，则需要在 RMS 口径基础上增加 `3.0103 dB`。
5. 如果 VPI analyzer 读取单端电压，则比差分口径低 `6.0206 dB`。

## 4. 当前仍需确认

需要通过一个 VPI 标定小实验确认：

```text
输入一个已知 1 Vrms 或 1 Vpeak 的正弦电压
经过 2 Port Analyzer 的 Mag(f)
再经过 x*x 和 10log(x)+30
观察输出值
```

该实验用于确认：

1. `Mag(f)` 输出是 RMS 还是 peak；
2. analyzer 测的是差分还是单端；
3. VPI 当前显示值是否为 `1Ω` 等效；
4. 离线仿真应使用 `TIA_*` 还是 `ADC_*` 与之对齐。

## 5. 当前结论

当前不能再把 VPI 的 `10.36` 与离线的 `13.21 dBm_50ohm` 直接视为只差约 `3 dB`。在阻抗口径未锁死前，两者可能对应不同的参考阻抗和不同的测量层级。

下一步应使用新增列重新对齐：

```text
VPI TIA 差分 RMS 口径 -> TIA_vpi_diff_rms_xx_plus30_dB
VPI TIA 单端 RMS 口径 -> TIA_vpi_single_rms_xx_plus30_dB
VPI ADC 后 RMS 口径 -> ADC_vpi_rms_xx_plus30_dB
50Ω 历史实验口径 -> *_dBm_50ohm
```

## 6. 当前 Step1-I 对齐观察

当前 `Step1-I` 选中点 `V_DCI = -8.6 V` 的离线读数为：

```text
TIA diff Vpeak                 = 2.209 V
TIA diff Vrms                  = 1.562 V
TIA diff 1Ω                    = 33.87 dB
TIA diff 50Ω                   = 16.88 dBm
TIA single 1Ω                  = 27.85 dB
TIA single 50Ω                 = 10.86 dBm
ADC clipped 50Ω                = 13.21 dBm
```

如果 VPI 图中读到的 `10.36` 来自 TIA 后输出，那么它目前最接近：

```text
TIA_single_signal_dBm_50ohm = 10.86 dBm
```

两者差约 `0.5 dB`，明显比与 `ADC_signal_dBm_50ohm = 13.21 dBm` 或 `TIA_diff_signal_dBm_50ohm = 16.88 dBm` 更接近。

因此一个新的待验证假设是：

```text
VPI analyzer 当前可能等效读取了单端 TIA 输出，并且内部或显示链路已采用 50Ω 等效口径。
```

这个假设需要通过 `1 Vrms / 1 Vpeak` 标定小实验确认。

## 7. 自动匹配工具

已新增自动匹配脚本：

```text
simulation_validation/vpi_alignment_checker.py
```

默认用当前 VPI 截图读数：

```text
VPI observed value = 10.36660078773
step = step1_i_bridge
bias = -8.6 V
```

运行方式：

```powershell
python simulation_validation\vpi_alignment_checker.py --vpi-value 10.36660078773 --bias -8.6 --step step1_i_bridge
```

输出：

```text
simulation_validation/results/vpi_alignment/step1_i_bridge_vpi_alignment_report.md
simulation_validation/results/vpi_alignment/step1_i_bridge_vpi_alignment_candidates.csv
simulation_validation/results/vpi_alignment/step1_i_bridge_vpi_alignment_candidates.json
```

当前自动匹配结果：

```text
best = TIA | single RMS direct 50ohm
offline value = 10.8637 dB
VPI value = 10.3666 dB
error = +0.4971 dB
```

候选排序前几项为：

```text
1. TIA single RMS 50Ω      error = 0.497 dB
2. ADC clipped RMS 50Ω     error = 2.842 dB
3. TIA single peak 50Ω     error = 3.507 dB
4. TIA diff RMS 50Ω        error = 6.518 dB
5. TIA single RMS 1Ω       error = 17.487 dB
```

因此当前最强证据指向：

```text
该 VPI 图更像是 TIA 单端 RMS 电压的 50Ω 等效显示。
```

后续每拿到一个 VPI 曲线读数，都应先用该脚本匹配一次，再决定和离线结果中的哪一列比较。

## 8. 多点批量对齐入口

已新增批量模板：

```text
simulation_validation/vpi_reference_points_template.csv
```

字段含义：

```text
enabled      是否参与批量匹配
case_id      当前 VPI 点的唯一名称
step         对应离线 step，例如 step1_i_bridge
vpi_value    VPI 图上的光标读数
bias         对应扫描偏置；为空时默认取 CSV 第一行
row_index    可选，直接指定离线 CSV 行号
tia_csv      可选，手动指定 TIA 曲线 CSV
adc_csv      可选，手动指定 ADC 曲线 CSV
note         备注
```

当前模板已经包含一个已启用参考点和四个待采集占位点：

```text
enabled=1  step1_i_1khz_peak       Step1-I 一阶峰值，已填入当前 VPI 截图读数
enabled=0  step1_q_1p2khz_peak     Step1-Q 一阶峰值，待填 VPI 光标读数
enabled=0  step2_ip_2p3khz_valley  Step2 I-P 交调读数，待填 VPI 光标读数
enabled=0  step3_p2_2p6khz_i_min   Step3 P 二阶读数，待填 VPI 光标读数
enabled=0  step4_q_1p2khz_final    Step4 Q 一阶最终点读数，待填 VPI 光标读数
```

填表规则：

```text
1. 从 VPI 曲线窗口读取对应光标 Y 值；
2. 填入 vpi_value；
3. 确认 bias 是离线同一步选中的 source bias；
4. 将 enabled 从 0 改为 1；
5. 重新运行 vpi_alignment_batch.py。
```

批量运行：

```powershell
python simulation_validation\vpi_alignment_batch.py
```

当前输出：

```text
simulation_validation/results/vpi_alignment_batch/vpi_alignment_batch_report.md
simulation_validation/results/vpi_alignment_batch/vpi_alignment_batch_summary.csv
simulation_validation/results/vpi_alignment_batch/vpi_alignment_batch_summary.json
```

当前模板中只有 Step1-I 一个 VPI 点，批量结果为：

```text
case_id        = step1_i_1khz_peak
best           = TIA | single RMS direct 50ohm
offline value  = 10.8637 dB
VPI value      = 10.3666 dB
error          = +0.4971 dB
```

后续应把 Q 一阶、I-P 交调、P 二阶等 VPI 曲线读数继续追加到模板或复制出的正式参考 CSV 中。如果多个点稳定指向同一个 `best_candidate`，即可认为 VPI 与离线仿真的读数口径基本锁定。

## 9. 读数口径锁定判据

批量脚本现在会输出 convention 汇总：

```text
simulation_validation/results/vpi_alignment_batch/vpi_alignment_batch_conventions.csv
simulation_validation/results/vpi_alignment_batch/vpi_alignment_batch_conventions.json
```

默认锁定规则：

```text
min_points_for_lock = 3
lock_threshold_db = 1.0 dB
```

即至少需要 3 个 VPI 参考点，并且这些点全部指向同一个归一化读数口径，同时该口径的最大绝对误差不超过 `1.0 dB`，才会给出：

```text
Convention status = LOCKED
```

当前只有一个 VPI 点，因此输出为：

```text
Convention status = INSUFFICIENT_POINTS
Leading convention = TIA | single RMS 50ohm
```

这表示当前证据支持 `TIA | single RMS 50ohm`，但还不能最终宣布 VPI 与离线读数口径已经完全锁定。

## 10. 对齐口径自检

已新增自检脚本：

```text
simulation_validation/vpi_alignment_selfcheck.py
```

运行方式：

```powershell
python simulation_validation\vpi_alignment_selfcheck.py
```

自检内容：

```text
1Ω - 50Ω = 10log10(50) = 16.989700043 dB
差分 - 单端 = 20log10(2) = 6.020599913 dB
VPI helper column = 对应 1Ω RMS 读数
```

当前自检结果：

```text
Readout conversion status = PASS
Total checks = 12030
Failed checks = 0
Max abs conversion error = 7.20378e-10 dB
Batch convention status = INSUFFICIENT_POINTS
Leading convention = TIA | single RMS 50ohm
```

输出：

```text
simulation_validation/results/vpi_alignment_selfcheck/vpi_alignment_selfcheck_report.md
simulation_validation/results/vpi_alignment_selfcheck/vpi_alignment_selfcheck.csv
simulation_validation/results/vpi_alignment_selfcheck/vpi_alignment_selfcheck.json
```

这说明离线侧的读数换算列已经自洽；当前未锁定的原因不是换算公式不稳定，而是 VPI 参考点数量还不够。

## 11. 2026-07-10 负载口径修正

用户已确认：当前 VPI 截图中的 `10.36660078773` 是在 `1 ohm` 负载口径下由 `10log10(x*x)+30` 得到的数值。

因此，之前不限制负载时得到的：

```text
best = TIA | single RMS direct 50ohm
offline value = 10.8637 dB
error = +0.4971 dB
```

只能说明“如果把 VPI 当成 50 ohm 等效显示，则数值接近”，不能作为当前 VPI 链路已经对齐的证据。

现在模板和匹配工具已经增加：

```text
expected_load_ohm = 1
```

在该约束下，当前 Step1-I 点的匹配结果为：

```text
VPI observed value              = 10.36660078773 dB, 1 ohm
best constrained candidate      = TIA | single RMS direct 1ohm
offline value                   = 27.853400854 dB
error                           = +17.486800066 dB
```

结论：

```text
当前不能认为 VPI 与离线仿真已经数值对齐。
在 1 ohm 口径下，离线仿真幅度仍然明显偏高。
```

下一步排查重点不再是 `1 ohm` 与 `50 ohm` 的显示换算，而是链路幅度来源：

```text
1. VPI 中 0.05 a.u. 导频幅度是否等价于离线模型的 0.05 Vpeak；
2. 离线模型中的 child_source_gain / RF drive 是否比 VPI 实际更大；
3. VPI 光功率分束、PD 电流、TIA 单端/差分读点是否和离线链路一致；
4. VPI analyzer 读点是否确实在 TIA 输出后、ADC 输入前；
5. 是否存在 VPI 模块内部额外比例系数或端口归一化。
```

## 12. 2026-07-10 VPI 导频幅度口径修正

用户已确认：VPI 中 `FuncSineEI Amplitude = 0.05 a.u.` 是峰值幅度，并且 I/Q 子 MZM 的 `LowerArmPhaseSense = NEGATIVE`。

其物理含义为：

```text
upper arm drive = +0.05 * sin(wt)
lower arm drive = -0.05 * sin(wt)
```

因此上下臂相位变化相反，子 MZM 的等效差分驱动峰值为：

```text
V_effective_peak = V_upper - V_lower = 0.05 - (-0.05) = 0.10
```

离线模型中 I/Q 子调制器的映射规则是：

```text
V_child_effective = child_source_gain * V_child_source
child_source_gain = 2
```

所以当离线链式仿真使用：

```text
V_dither_I_source_amp = 0.05
V_dither_Q_source_amp = 0.05
```

时，对应的 I/Q 有效差分导频峰值正是：

```text
V_dither_I_effective_amp = 0.10
V_dither_Q_effective_amp = 0.10
```

结论：

```text
当前不应把 I/Q 导频源幅度再除以 2。
若 VPI 源端为 0.05 peak，离线模型保留 source_amp=0.05 且 child_source_gain=2 是正确映射。
```

当前 `run_chained_findpoint.py` 的默认导频幅度已固定为：

```text
i_dither_amp = 0.05
q_dither_amp = 0.05
p_dither_amp = 0.05
```

因此，1 ohm 口径下仍然存在的约 `17.49 dB` 幅度差，不应优先归因于 I/Q `NEGATIVE` 导频映射，而应继续排查光功率、PD 分支、TIA 读点、VPI Analyzer 幅值定义或模块内部归一化。

## 13. 2026-07-10 VPI TIA 跨阻参数修正

用户已确认：当前 VPI TIA 模块参数为：

```text
Transimpedance = 10000 ohm
```

VPI 文档说明：

```text
The output voltage swing measured between the differential outputs is the input current multiplied by the transimpedance.
```

因此 VPI TIA 的差分输出满足：

```text
Vdiff_peak = I_peak * 10 kOhm
```

而此前离线 TIA 曲线默认使用真实硬件原理图参数：

```text
R_f = 100 kOhm
```

两者相差：

```text
20log10(100 kOhm / 10 kOhm) = 20 dB
```

这解释了此前 `1 ohm` 口径下约 `17.49 dB` 的主要偏差。当前已生成专门用于 VPI 对齐的 TIA 曲线：

```text
simulation_validation/results/tia_curves_vpi_10kohm/
simulation_validation/results/tia_curves_vpi_10kohm_report.md
```

当前 Step1-I 点在 VPI `10 kOhm` TIA 口径下的结果：

```text
VPI observed value             = 10.36660078773 dB
VPI load                       = 1 ohm
VPI TIA transimpedance         = 10 kOhm
Offline best candidate         = TIA | single peak derived 1ohm  (legacy interpretation before RMS confirmation)
Offline value                  = 10.863870535 dB
Error                          = +0.497269747 dB
```

结论：

```text
当前 Step1-I 单点已经基本对齐。
该判断已被后续 VPI `TwoPortAnalyzerEl` 技术文档修正：analyzer 输出为 RMS 幅值，peak 口径只保留为历史排查记录。
```

注意：

```text
1. 真实硬件 TIA 仍按 100 kOhm 原理图建模；
2. VPI 数值对齐时应使用 10 kOhm TIA 曲线；
3. 后续需要用 Step1-Q、Step2 I-P、Step3 P二阶等更多 VPI 点验证 `single RMS 1ohm` 或 `diff RMS 1ohm` 口径是否稳定。
```
## 2026-07-15 更新：TwoPortAnalyzerEl 使用 RMS 幅值

根据 VPI `TwoPortAnalyzerEl.vtmg` 技术文档，模块说明为：

```text
detects an electrical signal to isolate the magnitude (rms) and phase
of a single frequency component
```

因此后续与 VPI 曲线对齐时，默认不再使用峰值口径，而使用 RMS 口径：

```text
VPI 单端 RMS, 1 ohm  -> VPI_single_rms_1ohm_dB
VPI 差分 RMS, 1 ohm  -> VPI_diff_rms_1ohm_dB
```

若离线结果中已有 `I_tone_peak_A`，则换算关系为：

```text
Vdiff_peak   = I_tone_peak_A * Z_TIA
Vsingle_peak = Vdiff_peak / 2
Vsingle_rms  = Vsingle_peak / sqrt(2)
VPI_single_rms_1ohm_dB = 10log10(Vsingle_rms^2) + 30
```

所以原来按 `single peak` 绘制的曲线需要整体减去：

```text
20log10(sqrt(2)) = 3.0103 dB
```

当前 I 路全域扫描在该口径下的峰值从 `7.986969 dB` 修正为 `4.976670 dB`，与 VPI 图中的约 `5 dB` 峰值一致。这说明本次约 `3 dB` 的差异主要来自 peak/RMS 读数口径，而不是 DPMZM 或 TIA 增益模型错误。
