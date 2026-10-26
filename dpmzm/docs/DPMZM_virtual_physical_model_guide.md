# DPMZM 虚拟物理模型指导文档

版本：2026-05-31

本文档用于指导 DPMZM 虚拟物理模型的实现、参数配置、VPI 对齐和后续扩展。它不是单纯公式推导，而是当前 `dpmzm/model.py` 的物理含义说明和接口规范。

---

## 1. 建模目标

本模型用于描述双平行 Mach-Zehnder 调制器（DPMZM）的输出光场、光功率、PD 电流、电谱、光谱和基础 bias scan。

第一版模型的目标是：

1. 对齐 VPI 中由三个 `DiffMZ_DSM` block 搭建的 DPMZM 链路；
2. 保持 RF 输入通用，不在模型内部固定 CS-SSB、OSSB 等调制格式；
3. 支持 I/Q/P 三路偏置、电压波形、插入损耗、消光比和 PD 参数；
4. 输出可直接用于后续控制算法、数据集生成、VPI/MATLAB 对比和可视化。

模型暂不包含：

1. 闭环控制器；
2. 电极频响、行波效应、色散、非线性光纤传输；
3. VPI 中所有模拟电路细节；
4. 自动参数拟合。

---

## 2. 链路结构

当前模型对应的 VPI 链路结构为：

```text
CW Laser
  |
Power N / optical split
  |
  +--> I child MZM, LowerArmPhaseSense = NEGATIVE
  |
  +--> Q child MZM, LowerArmPhaseSense = NEGATIVE
        |
        +--> P / parent phase MZM, LowerArmPhaseSense = POSITIVE
  |
Power N / optical combine
  |
Photodiode
  |
SignalAnalyzer
```

重要约定：

1. I/Q 子 MZM 是 `NEGATIVE` 模式，起调制幅度控制作用；
2. P / 主调制器是 `POSITIVE` 模式，在该 VPI 结构中位于 Q 光路，只提供 Q 路公共相位；
3. P block 的 `InsertionLoss` 只作用在 Q 路，不是 I/Q 两路共同的总输出损耗；
4. 最终光场合成保留 DPMZM 结构中的 `1/2` 系数。

---

## 3. 电压与相位定义

Python 模型内部使用有效相位电压：

$$
\phi_k(t)=\frac{\pi V_k(t)}{V_{\pi,k}},
\qquad k\in\{I,Q,P\}.
$$

代码接口：

```python
voltage_to_phase(V, Vpi)
phase_to_voltage(phi, Vpi)
```

三路电压由 DC、RF 和 dither 叠加得到：

$$
V_I(t)=V_{DCI}+V_{RFI}(t)+V_{dither,I}(t)
$$

$$
V_Q(t)=V_{DCQ}+V_{RFQ}(t)+V_{dither,Q}(t)
$$

$$
V_P(t)=V_{DCP}+V_{dither,P}(t)
$$

模型不规定 RF 调制格式。调用者可以通过 `V_DCI`、`V_DCQ`、`V_DCP`、`V_RFI_amp`、`V_RFQ_amp`、`rf_phase_I`、`rf_phase_Q` 或直接传入数组波形来实现目标调制。

### 3.1 VPI 电压源映射

VPI `DiffMZ_DSM` 的 `LowerArmPhaseSense` 影响电压源到模型有效相位电压的映射。

I/Q 子 MZM：

```text
LowerArmPhaseSense = NEGATIVE
```

上下臂相位方向相反，VPI 电压源等效为 Python 中两倍差分相位电压：

```python
V_DCI = 2 * VPI_I_DC_source
V_DCQ = 2 * VPI_Q_DC_source
V_RFI_amp = 2 * VPI_RF_source_peak
V_RFQ_amp = 2 * VPI_RF_source_peak
```

P / 主调制器：

```text
LowerArmPhaseSense = POSITIVE
```

上下臂相位方向相同，电压源作为公共相位驱动，不加倍：

```python
V_DCP = VPI_P_DC_source
```

---

## 4. 单个 MZM block 模型

### 4.1 插入损耗

VPI 对 `InsertionLoss` 的描述是 fiber-in to fiber-out attenuation。因此单个 MZM block 的最大传输功率必须满足：

$$
P_{out,max}=P_{in}10^{-IL_{dB}/10}.
$$

例如：

```text
Pin = 10 dBm
InsertionLoss = 6 dB
Pout,max = 4 dBm
```

代码中使用功率损耗因子：

$$
L=10^{-IL_{dB}/10}.
$$

光场中使用：

$$
\sqrt{L}.
$$

### 4.2 NEGATIVE 模式

`LowerArmPhaseSense=NEGATIVE` 时，上下臂相位相反，理想传输为：

$$
H_{neg,ideal}(\phi)=\cos\left(\frac{\phi}{2}\right).
$$

考虑有限消光比后，默认使用 VPI 对齐的归一化形式：

$$
H_{neg,vpi}(\phi)=
\frac{
\cos\left(\frac{\phi}{2}\right)
+
\delta\exp\left(j\frac{\phi}{2}\right)
}{1+\delta}.
$$

其中：

$$
\delta=\frac{1}{10^{ER_{dB}/20}-1}.
$$

这个形式满足两个物理约束：

$$
H_{neg,vpi}(0)=1
$$

最大传输点不因有限消光比而超过插入损耗定义。

$$
\left|H_{neg,vpi}(\pi)\right|
=
\frac{\delta}{1+\delta}
=
10^{-ER_{dB}/20}
$$

最小传输点残余符合给定消光比。

### 4.3 POSITIVE 模式

`LowerArmPhaseSense=POSITIVE` 时，上下臂相位同向，差分余弦项抵消，只保留公共相位：

$$
H_{pos,vpi}(\phi)=\exp(j\phi).
$$

带插损时：

$$
H_{pos,vpi}(\phi)=\sqrt{L}\exp(j\phi).
$$

这正是当前 P / 主调制器 block 的默认模型。

### 4.4 论文残余项兼容模式

早期论文推导中常见的有限消光比写法为：

$$
H_{thesis}(\phi)=
\cos\left(\frac{\phi}{2}\right)
+
\delta\exp\left(j\frac{\phi}{2}\right).
$$

这个形式没有归一化：

$$
H_{thesis}(0)=1+\delta.
$$

因此它会让最大传输点功率变大，不适合绝对功率仿真或 VPI 对齐。

代码保留该形式用于论文复现实验：

```python
simulate_dpmzm(..., er_model="thesis")
```

默认应使用：

```python
simulate_dpmzm(..., er_model="vpi")
```

---

## 5. DPMZM 输出光场模型

定义 I/Q 子 MZM 输出传输项：

$$
H_I(t)=
\sqrt{L_I}
\frac{
\cos\left(\frac{\phi_I(t)}{2}\right)
+
\delta_I\exp\left(j\frac{\phi_I(t)}{2}\right)
}{1+\delta_I}
$$

$$
H_Q(t)=
\sqrt{L_Q}
\frac{
\cos\left(\frac{\phi_Q(t)}{2}\right)
+
\delta_Q\exp\left(j\frac{\phi_Q(t)}{2}\right)
}{1+\delta_Q}
$$

P / 主调制器位于 Q 光路：

$$
H_P(t)=\sqrt{L_P}\exp(j\phi_P(t)).
$$

额外公共链路损耗为：

$$
L_{global}=10^{-IL_{dB}/10}.
$$

DPMZM 总输出场为：

$$
E_{out}(t)=
\frac{E_{in}\sqrt{L_{global}}}{2}
\left[
H_I(t)
+
\gamma_P H_Q(t)H_P(t)
\right].
$$

默认：

$$
\gamma_P=1.
$$

`gamma_P` 仅作为兼容或实验参数保留，不由 `ER_P_dB` 自动生成。

---

## 6. 功率、PD 和电谱

瞬时光功率：

$$
P_{opt}(t)=|E_{out}(t)|^2.
$$

PD 输入可通过 `pd_tap` 做比例抽取：

$$
P_{PD}(t)=pd\_tap\cdot P_{opt}(t).
$$

PD 电流：

$$
I_{PD}(t)=R_{PD}P_{PD}(t).
$$

其中 `Responsivity` 默认为：

```python
Responsivity = 0.786  # A/W
```

### 6.1 电谱 dBm 口径

模型提供 `vpi_compatible_dbm` 开关。与当前 VPI SignalAnalyzer 对齐时使用：

```python
vpi_compatible_dbm=True
R_load=1.0
```

此时电谱近似按 1 ohm 电流口径计算：

$$
P_{DC}=I_{DC}^2
$$

$$
P_{AC}=\frac{I_{AC,peak}^2}{2}
$$

然后转换为 dBm：

$$
P_{dBm}=10\log_{10}(1000P_W).
$$

注意：VPI PD 参数面板中的 `LoadResistance=50 Ohm` 未直接表现为当前 SignalAnalyzer marker 的 `I^2R` 信号功率口径，否则会出现约 `16.99 dB` 的差异。

---

## 7. 噪声模型

噪声逻辑沿用原 MZM 模型的口径，包括：

1. 热噪声；
2. 散粒噪声；
3. RIN 噪声；
4. RBW 对噪声功率的影响；
5. `vpi_compatible_dbm` 对功率口径的缩放。

噪声项主要影响频谱噪声底，不应改变 PowerMeter 读到的平均光功率。

RIN 参数含义：

```text
RIN_dB_Hz: 相对强度噪声谱密度
RIN_MeasPower: VPI 中 RIN 的测量参考功率
```

当前代码显式使用 `RIN_dB_Hz`，暂未单独建模 `RIN_MeasPower` 对 RIN 标定的二次换算。该项后续可在更精细的激光器噪声模型中扩展。

---

## 8. 默认参数

`simulate_dpmzm(...)` 的主要默认参数如下：

| 参数 | 默认值 | 含义 |
|---|---:|---|
| `Vpi` | `5.0` | 默认半波电压 |
| `Vpi_I/Q/P` | `None` | 单路覆盖；为空时使用 `Vpi` |
| `ER_dB` | `30.0` | 默认消光比 |
| `ER_I/Q/P_dB` | `None` | 单路覆盖；为空时使用 `ER_dB` |
| `IL_dB` | `0.0` | 额外公共链路损耗 |
| `IL_I_dB` | `6.0` | I 子 MZM 插入损耗 |
| `IL_Q_dB` | `6.0` | Q 子 MZM 插入损耗 |
| `IL_P_dB` | `6.0` | Q 光路上的 P block 插入损耗 |
| `Responsivity` | `0.786` | PD 响应度，A/W |
| `R_load` | `50.0` | 普通电谱负载口径；VPI 对齐时设为 `1.0` |
| `Pin_dBm` | `10.0` | 输入激光平均功率 |
| `pd_tap` | `1.0` | PD 前光功率比例 |
| `Temp_K` | `290.0` | 噪声温度 |
| `RIN_dB_Hz` | `-145.0` | 激光 RIN |
| `er_model` | `"vpi"` | 有限消光比实现 |
| `vpi_compatible_dbm` | `False` | VPI 电谱 dBm 口径开关 |

VPI 对齐 demo 使用：

```python
simulate_dpmzm(
    Fs=160e9,
    T_total=65536 / 10e9,
    Vpi=5.0,
    ER_dB=30.0,
    IL_dB=0.0,
    IL_I_dB=6.0,
    IL_Q_dB=6.0,
    IL_P_dB=6.0,
    Pin_dBm=10.0,
    Responsivity=0.786,
    R_load=1.0,
    vpi_compatible_dbm=True,
    er_model="vpi",
)
```

---

## 9. 输出结果对象

`simulate_dpmzm(...)` 返回 `SimulationResult`，主要字段包括：

| 字段 | 含义 |
|---|---|
| `t` | 时间轴 |
| `RBW_Hz` | 频谱分辨率 |
| `E_out` | 输出复光场包络 |
| `P_opt_inst_W` | 瞬时光功率 |
| `P_pd_avg_dBm` | PD 前平均光功率 dBm |
| `I_pd` | PD 电流时域波形 |
| `noise` | 噪声结果 |
| `spectrum` | 光谱和电谱结果 |
| `bias_scan` | I/Q/P 三路 bias scan |
| `Pin_dBm` | 输入功率快照 |
| `pd_tap` | PD tap 快照 |
| `params` | 参数快照 |

---

## 10. VPI 对齐验收点

### 10.1 单个 MZM 最大透射点

VPI 条件：

```text
Pin = 10 dBm
InsertionLoss = 6 dB
RF = 0
DC = 0
LowerArmPhaseSense = NEGATIVE
```

期望：

```text
Pout = 4 dBm
```

Python 自检：

```text
single_block_dbm = 4.000 dBm
finite_er_block_dbm = 4.000 dBm
```

### 10.2 I/Q/P 三路 DC = 1 V 测试点

VPI 电压源：

```text
I DC = 1 V
Q DC = 1 V
P DC = 1 V
RF peak = 1 V
```

Python 有效参数：

```python
V_DCI = 2.0
V_DCQ = 2.0
V_DCP = 1.0
V_RFI_amp = 2.0
V_RFQ_amp = 2.0
```

RF 关闭光功率：

| 项目 | 功率 |
|---|---:|
| Python | -0.716 dBm |
| VPI | -0.717 dBm |

RF 打开电谱：

| 分量 | Python | VPI |
|---|---:|---:|
| DC | -34.683 dBm | -34.690 dBm |
| 1f | -41.313 dBm | -41.320 dBm |
| 2f | -62.827 dBm | -62.830 dBm |

### 10.3 原始截图参数点

VPI 电压源：

```text
I DC = 2.5 V
Q DC = 2.5 V
P DC = 1.25 V
RF peak = 1 V
```

Python 有效参数：

```python
V_DCI = 5.0
V_DCQ = 5.0
V_DCP = 1.25
V_RFI_amp = 2.0
V_RFQ_amp = 2.0
```

当前模型结果：

| 分量 | Python | VPI 参考 |
|---|---:|---:|
| DC | -49.080 dBm | -49 dBm |
| 1f | -74.031 dBm | -74 dBm |
| 2f | -53.851 dBm | -53 dBm |

该点的 VPI marker 读数精度和 SignalAnalyzer peak/bin 选择方式会影响约 `0.x dB` 的最后差异。若需要严格验收，应导出 VPI 数组数据，而不是只读图上 marker。

---

## 11. 绘图工具

DPMZM 复用 MZM 的光谱和电谱绘图逻辑：

```python
from dpmzm.plot import (
    plot_optical_spectrum_osa,
    plot_electrical_spectrum,
    plot_bias_scan,
)
```

其中：

1. 光谱图复用 `mzm.plot.plot_optical_spectrum_osa`；
2. 电谱图复用 `mzm.plot.plot_electrical_spectrum`；
3. `plot_bias_scan` 是 DPMZM 专用，显示 I/Q/P 三路 bias scan。

---

## 12. 实现约束与扩展原则

后续修改模型时，应保持以下原则：

1. 有限消光比只能抬高最小传输点残余，不能让最大传输点超过插损定义；
2. 插入损耗是功率损耗，进入光场时必须取平方根；
3. P block 位于 Q 光路时，`IL_P_dB` 只作用于 Q 路；
4. `NEGATIVE` 和 `POSITIVE` 的 VPI 电压源映射不能混用；
5. 光功率对齐优先用 PowerMeter 验证，电谱对齐再考虑 PD 和 SignalAnalyzer 口径；
6. 任何 VPI/MATLAB 对齐都应记录采样率、时间窗、RBW、负载口径、PD 响应度和 marker 读取方式；
7. 若新增非理想效应，应先给出单 block 验收点，再并入 DPMZM 总链路。

---

## 13. 最小使用示例

```python
import numpy as np
from dpmzm import simulate_dpmzm
from dpmzm.vpi_demo import _dbm

sim = simulate_dpmzm(
    Fs=160e9,
    T_total=65536 / 10e9,
    Vpi=5.0,
    ER_dB=30.0,
    IL_dB=0.0,
    IL_I_dB=6.0,
    IL_Q_dB=6.0,
    IL_P_dB=6.0,
    Pin_dBm=_dbm(0.010),
    Responsivity=0.786,
    R_load=1.0,
    V_DCI=2.0,
    V_DCQ=2.0,
    V_DCP=1.0,
    f_rf=10e9,
    V_RFI_amp=2.0,
    V_RFQ_amp=2.0,
    rf_phase_Q=np.deg2rad(90.0),
    er_model="vpi",
    vpi_compatible_dbm=True,
    rng_seed=0,
)

print(sim.P_pd_avg_dBm)
print(sim.spectrum.val_rf_dBm)
```

---

## 14. 相关文件

| 文件 | 用途 |
|---|---|
| `dpmzm/model.py` | DPMZM 核心物理模型 |
| `dpmzm/plot.py` | 光谱、电谱、bias scan 绘图 |
| `dpmzm/validation.py` | 分析自检 |
| `dpmzm/vpi_demo.py` | VPI 参数对齐 demo |
| `dpmzm/dpmzm_python_model_notes.md` | Python 模型公式笔记 |
| `dpmzm/vpi_finite_er_correction.md` | 有限消光比错误定位记录 |
| `dpmzm/DPMZM_output_model_rederived.md` | 早期推导文档 |
