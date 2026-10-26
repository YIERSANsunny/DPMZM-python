# MZM/DPMZM 物理模型入门与虚拟仿真指南

版本：2026-05-31

本文档面向刚接触光通信、光调制器和虚拟物理模型的读者。目标不是把所有电光器件理论一次讲完，而是建立一条清晰路径：

```text
光场是什么
  -> 光功率和 PD 电流怎么来
  -> 单个 MZM 如何把电压变成强度/相位变化
  -> DPMZM 如何由多个 MZM 组合而成
  -> 插入损耗、消光比等非理想项如何进入仿真
  -> 这些物理量如何对应到 Python/VPI 参数
```

读完后，应能理解当前项目中 MZM/DPMZM 模型的核心公式、参数含义和常见验收点。

---

## 1. 从光通信的信号直觉开始

光通信里传输的不是普通低频电压，而是非常高频的光载波。以 1550 nm 光通信波段为例，光频约为：

```text
193.1 THz
```

这么高的载波本身通常不直接在仿真里逐点采样。我们更常使用“复光场包络”表示慢变化部分：

$$
E(t)=A(t)e^{j\theta(t)}
$$

这里：

| 符号 | 直觉含义 |
|---|---|
| $A(t)$ | 光场幅度 |
| $\theta(t)$ | 光场相位 |
| $E(t)$ | 复光场包络 |

光功率与光场幅度平方成正比。在当前模型的归一化口径下，直接写成：

$$
P_{opt}(t)=|E(t)|^2
$$

这句话非常重要：**光场是复数，光功率是实数；光功率来自光场模长平方。**

---

## 2. 光电探测器 PD 做了什么

光电探测器（Photodiode, PD）把光功率转换成电流：

$$
I_{PD}(t)=R_{PD}P_{opt}(t)
$$

其中：

| 符号 | 含义 |
|---|---|
| $I_{PD}(t)$ | PD 输出电流 |
| $R_{PD}$ | 响应度，单位 A/W |
| $P_{opt}(t)$ | 入射到 PD 的光功率 |

当前 VPI 对齐中常用：

```python
Responsivity = 0.786  # A/W
```

如果光场中有多个频率分量，它们在 PD 中会相互拍频。比如：

```text
光载波 fc
一阶边带 fc + fRF
```

PD 看到的是光功率：

$$
|E_c + E_1 e^{j2\pi f_{RF}t}|^2
$$

展开后会出现 $f_{RF}$ 的电信号，这就是“拍频”的基本来源。

所以：

```text
光谱里的边带间隔 -> PD 电谱里的 RF 频率
光场幅度变化     -> PD 电流变化
```

---

## 3. 相位调制和强度调制

光场有两个最基本的可调维度：

```text
幅度 A(t)
相位 theta(t)
```

如果只改变相位：

$$
E(t)=E_0e^{j\theta(t)}
$$

光功率仍是：

$$
|E(t)|^2=|E_0|^2
$$

这叫相位调制。相位变了，但单独看瞬时光功率不一定变。

如果改变幅度：

$$
E(t)=A(t)e^{j\theta_0}
$$

光功率随 $A(t)^2$ 变化，这就是强度调制。

MZM 的核心能力，就是利用两条光路的相位差，把电压引起的相位变化转换成输出光强变化。

---

## 4. 单个 MZM 的物理图像

Mach-Zehnder Modulator（MZM）可以理解为：

```text
输入光
  |
  +---- 上臂: 加相位 phi_upper ----+
  |                                |
  +---- 下臂: 加相位 phi_lower ----+
                                   |
                                合束输出
```

输入光先被分成上下两臂。两臂分别积累相位，最后重新合束。合束时会发生干涉：

```text
两臂同相   -> 相长干涉 -> 输出强
两臂反相   -> 相消干涉 -> 输出弱
相位差中间 -> 输出处于中间状态
```

忽略插损时，单个 MZM 的输出光场可写为：

$$
E_{out}(t)=
\frac{E_{in}(t)}{2}
\exp\left(j\pi\frac{V_{upper}(t)}{V_\pi}\right)
+
\frac{E_{in}(t)}{2}
\exp\left(j\pi\frac{V_{lower}(t)}{V_\pi}\right)
$$

整理后：

$$
E_{out}(t)
=
E_{in}(t)
\cos\left(
\frac{\pi[V_{upper}(t)-V_{lower}(t)]}{2V_\pi}
\right)
\exp\left(
j\frac{\pi[V_{upper}(t)+V_{lower}(t)]}{2V_\pi}
\right)
$$

这个公式可以读成两部分：

| 项 | 物理意义 |
|---|---|
| $\cos(\cdots)$ | 由上下臂相位差决定的强度调制 |
| $\exp(j\cdots)$ | 由上下臂共同相位决定的相位调制 |

---

## 5. Vpi 是什么

$V_\pi$ 称为半波电压。直觉上，它表示让 MZM 两臂产生 $\pi$ 相位差所需的等效电压尺度。

在当前模型里，经常使用：

```python
Vpi = 5.0  # V
```

如果有效电压为 $V$，则模型内部常用相位：

$$
\phi(t)=\frac{\pi V(t)}{V_\pi}
$$

代码接口：

```python
voltage_to_phase(V, Vpi)
phase_to_voltage(phi, Vpi)
```

理解 $V_\pi$ 的关键：

```text
电压越大 -> 相位变化越大
Vpi 越大 -> 同样电压引起的相位变化越小
```

---

## 6. MZM 的三个典型工作点

对于理想 push-pull MZM：

$$
E_{out}=E_{in}\cos\left(\frac{\phi}{2}\right)
$$

输出功率：

$$
P_{out}=P_{in}\cos^2\left(\frac{\phi}{2}\right)
$$

常见工作点：

| 工作点 | 相位 | 光场 | 功率 | 直觉 |
|---|---:|---:|---:|---|
| 最大传输点 | $\phi=0$ | $E_{in}$ | $P_{in}$ | 最亮 |
| 最小传输点 | $\phi=\pi$ | 0 | 0 | 最暗 |
| 正交点 | $\phi=\pi/2$ | $E_{in}/\sqrt{2}$ | $P_{in}/2$ | 斜率最大 |

正交点常用于线性强度调制，因为在这个点附近，小电压变化能比较线性地转换成光强变化。

最小传输点常用于载波抑制类调制，因为它能压低原始光载波。

---

## 7. VPI 的 LowerArmPhaseSense

VPI `DiffMZ_DSM` 里有一个关键参数：

```text
LowerArmPhaseSense = NEGATIVE / POSITIVE
```

它决定下臂相位随电压变化的方向。

### 7.1 NEGATIVE：push-pull 强度调制

`NEGATIVE` 表示上下臂相位方向相反：

```text
上臂: +phase
下臂: -phase
```

这时共同相位抵消，主要留下余弦强度调制项：

$$
E_{out}=E_{in}\cos\left(\frac{\phi}{2}\right)
$$

在当前项目中，I/Q 子 MZM 使用 `NEGATIVE`。

VPI 电压源到 Python 有效电压的映射为：

```python
V_DCI = 2 * VPI_I_DC_source
V_DCQ = 2 * VPI_Q_DC_source
V_RFI_amp = 2 * VPI_RF_source_peak
V_RFQ_amp = 2 * VPI_RF_source_peak
```

### 7.2 POSITIVE：common phase 相位调制

`POSITIVE` 表示上下臂相位方向相同：

```text
上臂: +phase
下臂: +phase
```

这时两臂没有相位差，余弦强度项等于 1，输出主要是公共相位：

$$
E_{out}=E_{in}\exp(j\phi)
$$

在当前 DPMZM VPI 链路中，P / 主调制器使用 `POSITIVE`，位于 Q 光路上。

映射为：

```python
V_DCP = VPI_P_DC_source
```

这里不再乘 2。

---

## 8. 插入损耗：最大功率约束

插入损耗（Insertion Loss, IL）描述器件从输入光纤到输出光纤的功率衰减。

如果：

```text
Pin = 10 dBm
InsertionLoss = 6 dB
```

那么最大透射点输出应为：

```text
Pout,max = 4 dBm
```

用线性功率因子表示：

$$
L=10^{-IL_{dB}/10}
$$

进入光场公式时用平方根：

$$
E_{out}\propto \sqrt{L}
$$

这是因为：

$$
P=|E|^2
$$

所以功率乘 $L$，光场幅度乘 $\sqrt{L}$。

当前 DPMZM 模型里有四类插损：

| 参数 | 含义 |
|---|---|
| `IL_I_dB` | I 子 MZM 插损 |
| `IL_Q_dB` | Q 子 MZM 插损 |
| `IL_P_dB` | P block 插损，只作用在 Q 光路 |
| `IL_dB` | 额外公共光路损耗 |

---

## 9. 消光比：最小点残余

消光比（Extinction Ratio, ER）描述最大输出功率和最小输出功率的比值：

$$
ER=\frac{P_{max}}{P_{min}}
$$

以 dB 表示：

$$
ER_{dB}=10\log_{10}(ER)
$$

一个物理上合理的有限消光比模型应该满足：

```text
最大点: 由输入功率和插入损耗决定
最小点: 由消光比决定残余功率
```

也就是：

$$
P_{max}=P_{in}10^{-IL_{dB}/10}
$$

$$
P_{min}=\frac{P_{max}}{ER}
$$

注意：**有限消光比不应该让最大点功率凭空变大。**

当前模型默认使用 VPI 对齐的归一化形式：

$$
H_{vpi}(\phi)=
\frac{
\cos\left(\frac{\phi}{2}\right)
+
\delta\exp\left(j\frac{\phi}{2}\right)
}{1+\delta}
$$

其中：

$$
\delta=\frac{1}{10^{ER_{dB}/20}-1}
$$

这个形式保证：

$$
H_{vpi}(0)=1
$$

最大点不变。

同时：

$$
\left|H_{vpi}(\pi)\right|=10^{-ER_{dB}/20}
$$

最小点残余符合消光比。

代码中默认：

```python
er_model = "vpi"
```

如果需要复现早期论文中未归一化的残余场形式，可以使用：

```python
er_model = "thesis"
```

但该模式不适合绝对功率对齐，因为它会让最大点功率被消光比项额外抬高。

---

## 10. 从 MZM 到 DPMZM

DPMZM 可以理解为两个子 MZM 并联，再通过一个父级/主调制器控制相对相位。

当前 VPI 对齐结构可画成：

```text
                     +--> I child MZM (NEGATIVE) ------------------+
                     |                                              |
Input optical field -+                                              +--> combiner --> E_out
                     |                                              |
                     +--> Q child MZM (NEGATIVE) --> P block (POSITIVE)
```

I/Q 两路子 MZM 负责产生两个可控光场分量。P block 位于 Q 光路，负责给 Q 路增加相对相位。

---

## 11. DPMZM 输出光场

I 路传输项：

$$
H_I(t)=
\sqrt{L_I}
\frac{
\cos\left(\frac{\phi_I(t)}{2}\right)
+
\delta_I\exp\left(j\frac{\phi_I(t)}{2}\right)
}{1+\delta_I}
$$

Q 路传输项：

$$
H_Q(t)=
\sqrt{L_Q}
\frac{
\cos\left(\frac{\phi_Q(t)}{2}\right)
+
\delta_Q\exp\left(j\frac{\phi_Q(t)}{2}\right)
}{1+\delta_Q}
$$

P block 位于 Q 光路：

$$
H_P(t)=\sqrt{L_P}\exp(j\phi_P(t))
$$

DPMZM 输出：

$$
E_{out}(t)=
\frac{E_{in}(t)\sqrt{L_{global}}}{2}
\left[
H_I(t)+\gamma_P H_Q(t)H_P(t)
\right]
$$

默认：

$$
\gamma_P=1
$$

在理想、无插损、无有限 ER 的情况下，上式退化为：

$$
E_{out}(t)=
\frac{E_{in}(t)}{2}
\left[
\cos\left(\frac{\phi_I(t)}{2}\right)
+
\cos\left(\frac{\phi_Q(t)}{2}\right)
\exp(j\phi_P(t))
\right]
$$

这就是 DPMZM 最常用的理想输出模型。

---

## 12. DPMZM 中 I/Q/P 三路分别做什么

可以用一句话理解：

```text
I/Q 子 MZM 控制两路光场幅度，P 路控制两路光场相对相位。
```

更具体地说：

| 路径 | 作用 | 常见偏置 |
|---|---|---|
| I 子 MZM | 生成 I 路调制光场 | 最小点、正交点或其他工作点 |
| Q 子 MZM | 生成 Q 路调制光场 | 通常与 I 路配合 |
| P block | 设置 I/Q 两路相对相位 | 常用正交相位，如 $\pi/2$ |

对于 CS-SSB 一类调制，常见思路是：

```text
I/Q 子 MZM 在最小传输点附近工作
I/Q RF 相位相差 90 度
P 路提供 I/Q 光场的 90 度相对相位
```

但当前 Python 模型并不硬编码任何调制方式。它只提供物理输出模型，调制方式由调用者通过参数决定。

---

## 13. Python 仿真参数如何对应物理量

核心入口：

```python
from dpmzm import simulate_dpmzm
```

常用参数：

| 参数 | 物理含义 |
|---|---|
| `Pin_dBm` | 输入激光平均功率 |
| `Vpi` | 默认半波电压 |
| `Vpi_I`, `Vpi_Q`, `Vpi_P` | I/Q/P 单路半波电压覆盖 |
| `ER_dB` | 默认消光比 |
| `ER_I_dB`, `ER_Q_dB`, `ER_P_dB` | I/Q/P 单路消光比覆盖 |
| `IL_dB` | 额外公共光路损耗 |
| `IL_I_dB`, `IL_Q_dB`, `IL_P_dB` | I/Q/P block 插入损耗 |
| `V_DCI`, `V_DCQ`, `V_DCP` | I/Q/P DC 偏置 |
| `V_RFI_amp`, `V_RFQ_amp` | I/Q RF 电压峰值 |
| `rf_phase_I`, `rf_phase_Q` | I/Q RF 相位 |
| `Responsivity` | PD 响应度 |
| `R_load` | 电谱负载口径 |
| `vpi_compatible_dbm` | 是否使用 VPI 对齐电谱 dBm 口径 |
| `er_model` | 有限消光比模型，默认 `"vpi"` |

---

## 14. VPI 参数映射示例

若 VPI 中：

```text
I DC source = 1 V
Q DC source = 1 V
P DC source = 1 V
RF source peak = 1 V
```

且：

```text
I/Q child MZM: LowerArmPhaseSense = NEGATIVE
P block:       LowerArmPhaseSense = POSITIVE
```

则 Python 中应设置：

```python
V_DCI = 2.0
V_DCQ = 2.0
V_DCP = 1.0
V_RFI_amp = 2.0
V_RFQ_amp = 2.0
```

一个最小示例：

```python
import numpy as np
from dpmzm import simulate_dpmzm

sim = simulate_dpmzm(
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
```

---

## 15. RBW、采样率和时间窗

频谱分辨率 RBW 与采样率和采样点数有关：

$$
RBW=\frac{F_s}{N}
$$

其中：

| 符号 | 含义 |
|---|---|
| $F_s$ | 采样率 |
| $N$ | 总采样点数 |

VPI 常见设置：

```text
BitRateDefault = 10e9
SampleRateDefault = 16 * BitRateDefault = 160e9
TimeWindow = 65536 / BitRateDefault
```

对应：

```python
Fs = 160e9
T_total = 65536 / 10e9
RBW = 152587.890625 Hz
```

如果 Python 和 VPI 的采样率、时间窗、RBW 不一致，频谱 marker 可能会有差异。

---

## 16. 常见验收点

### 16.1 单个 MZM 最大传输点

条件：

```text
Pin = 10 dBm
InsertionLoss = 6 dB
DC = 0
RF = 0
LowerArmPhaseSense = NEGATIVE
```

期望：

```text
Pout = 4 dBm
```

这个验收点用于确认：插入损耗没有被错误地叠加额外 3 dB 或 6 dB。

### 16.2 有限消光比不抬高最大点

条件：

```text
ER = 30 dB
最大传输点
```

期望：

```text
Pout 仍由 Pin - IL 决定
```

有限消光比只影响最小点残余，不应让最大点功率增加。

### 16.3 DPMZM 1V 测试点

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

当前对齐结果：

| 项目 | Python | VPI |
|---|---:|---:|
| RF off 光功率 | -0.716 dBm | -0.717 dBm |
| RF on DC | -34.683 dBm | -34.690 dBm |
| RF on 1f | -41.313 dBm | -41.320 dBm |
| RF on 2f | -62.827 dBm | -62.830 dBm |

### 16.4 原始 VPI 截图参数点

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

---

## 17. 初学者常见误区

### 17.1 把光场和光功率混在一起

光场是复数，可以相干叠加；光功率是实数，来自光场模长平方。

```text
先加光场，再取模平方
```

不能直接把两路光功率相加来代替相干合束。

### 17.2 插损进入光场时忘记开方

插损是功率损耗。若功率乘 $L$，光场应乘 $\sqrt{L}$。

### 17.3 有限消光比让最大点变亮

这是错误的绝对功率模型。消光比只应描述暗态残余，不应改变亮态由插损定义的功率。

### 17.4 忘记 VPI 的 `NEGATIVE` / `POSITIVE` 映射差异

I/Q 子 MZM 和 P block 的电压映射不同：

```text
NEGATIVE -> 有效差分相位电压，VPI source 通常乘 2
POSITIVE -> 公共相位电压，不乘 2
```

### 17.5 只看电谱，不先看光功率

排查 VPI/Python 差异时，建议顺序是：

```text
单 block PowerMeter
  -> DPMZM RF off PowerMeter
  -> PD 平均电流
  -> 电谱 DC/1f/2f marker
```

先确认光功率，再确认电谱口径。

---

## 18. 推荐阅读顺序

建议按下面顺序阅读项目文档：

1. `docs/mzm_dpmzm_physical_model_intro.md`  
   入门理解 MZM/DPMZM 物理模型。

2. `dpmzm/DPMZM_virtual_physical_model_guide.md`  
   查看当前 DPMZM 虚拟模型的实现指导、参数和验收点。

3. `dpmzm/vpi_finite_er_correction.md`  
   理解有限消光比归一化错误是如何定位和修正的。

4. `dpmzm/dpmzm_python_model_notes.md`  
   查看与当前 Python 模型更贴近的公式笔记。

5. `dpmzm/DPMZM_output_model_rederived.md`  
   查看早期较完整的理论推导过程。

---

## 19. 一句话总结

MZM 的本质是：**用两臂相位差控制干涉强弱**。

DPMZM 的本质是：**用两个子 MZM 产生 I/Q 两路光场，再用父级相位控制两路光场如何相干合成**。

虚拟物理模型最重要的约束是：

```text
光场先相干相加
光功率等于 |E|^2
插损约束最大输出
消光比约束最小残余
PD 电流正比于光功率
```

只要这几个关系不乱，MZM/DPMZM 的仿真模型就有了正确的物理骨架。
