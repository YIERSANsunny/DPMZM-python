# DPMZM Python 模型公式说明

本文档记录当前 `dpmzm/model.py` 中实际使用的 DPMZM 输出模型，便于和 VPI / MATLAB 仿真逐项核对。

---

## 1. 电压到相位的映射

当前模型采用等效差分驱动电压：

$$
\phi_I(t)=\frac{\pi V_I(t)}{V_{\pi,I}},
\qquad
\phi_Q(t)=\frac{\pi V_Q(t)}{V_{\pi,Q}},
\qquad
\phi_P(t)=\frac{\pi V_P(t)}{V_{\pi,P}}.
$$

其中三路电压为：

$$
V_I(t)=V_{DCI}+V_{RFI}(t)+V_{\mathrm{dither},I}(t),
$$

$$
V_Q(t)=V_{DCQ}+V_{RFQ}(t)+V_{\mathrm{dither},Q}(t),
$$

$$
V_P(t)=V_{DCP}+V_{\mathrm{dither},P}(t).
$$

若使用内置 RF 正弦源：

$$
V_{RFI}(t)=A_I\sin(2\pi f_{RF}t+\theta_I),
$$

$$
V_{RFQ}(t)=A_Q\sin(2\pi f_{RF}t+\theta_Q).
$$

注意：`V_RFI_amp` 和 `V_RFQ_amp` 是正弦**峰值幅度**，不是峰峰值。

---

## 2. I/Q 子 MZM 模型

理想子 MZM 的输出场包络为：

$$
H_I^{ideal}(t)=\cos\left(\frac{\phi_I(t)}{2}\right),
$$

$$
H_Q^{ideal}(t)=\cos\left(\frac{\phi_Q(t)}{2}\right).
$$

考虑有限消光比后，默认 `er_model="vpi"` 使用归一化臂不平衡形式：

$$
H_I^{vpi}(t)=
\frac{
\cos\left(\frac{\phi_I(t)}{2}\right)
+
\delta_I \exp\left(j\frac{\phi_I(t)}{2}\right)
}{1+\delta_I},
$$

$$
H_Q^{vpi}(t)=
\frac{
\cos\left(\frac{\phi_Q(t)}{2}\right)
+
\delta_Q \exp\left(j\frac{\phi_Q(t)}{2}\right)
}{1+\delta_Q}.
$$

这个归一化保证最大透射点仍为 1，不会因为有限消光比项而超过 `InsertionLoss` 定义的最大输出。若需要复现早期论文残余项，可显式设置 `er_model="thesis"`，此时分母 `1+\delta_k` 不使用。

消光比到 `delta` 的换算为：

$$
\delta_k=
\frac{1}{\sqrt{ER_k}-1}
=
\frac{1}{10^{ER_{k,dB}/20}-1},
\qquad k\in\{I,Q\}.
$$

当：

$$
ER_{I,dB}=ER_{Q,dB}=30\ \mathrm{dB},
$$

有：

$$
\delta_I=\delta_Q\approx 0.032655.
$$

---

## 3. 父级 / 主调制器合成模型

当前 Python 默认模型按 VPI 搭建方式加入各级插损：

$$
E_{out}(t)
=
\frac{E_{in}\sqrt{L_{global}}}{2}
\left[
\sqrt{L_I}\,H_I^{vpi}(t)
+
\gamma_P\sqrt{L_Q L_P}\,H_Q^{vpi}(t)\exp(j\phi_P(t))
\right].
$$

这里 `L_P` 只进入 Q 路，因为 VPI 结构里的父级 / 主调制器 `POSITIVE` block 是 Q 光路中的相位块；额外公共链路损耗才由 `L_global` 表示。

当前模型把插损放在各个 MZM block 内部：

$$
L_I=10^{-IL_{I,dB}/10},
\qquad
L_Q=10^{-IL_{Q,dB}/10},
\qquad
L_P=10^{-IL_{P,dB}/10}.
$$

`L_I` / `L_Q` 对应 I/Q 子调制器内部插损，`L_P` 对应父级 / 主调制器内部插损。`L_global` 对应额外公共链路损耗：

$$
L_{global}=10^{-IL_{dB}/10}.
$$

VPI demo 默认使用：

```python
IL_dB = 0.0
IL_I_dB = 6.0
IL_Q_dB = 6.0
IL_P_dB = 6.0
```

也就是把截图中每个 `DiffMZ_DSM` block 的 `InsertionLoss=6 dB` 放到对应 MZM 内部，而不是在 DPMZM 总输出外只乘一次。

代码对应为：

```python
field_sum = (
    H_I
    + gamma_P * H_Q * H_P
)

E_out = E_in * sqrt(L_global) * 0.5 * field_sum
```

其中 `H_I`、`H_Q` 已经分别包含 I/Q 子 MZM 的 `IL_I_dB`、`IL_Q_dB` 和 VPI 风格有限消光比归一化；`H_P=sqrt(L_P) exp(j phi_P)` 对应 Q 路上的 `POSITIVE` 父级相位 block。

在默认模型中：

$$
\gamma_P=1.
$$

`gamma_P` 仅作为兼容/实验参数保留，不再由 `ER_P_dB` 自动生成。

### 3.1 父级有限消光比

父级 / 主调制器消光比在 VPI 默认模式下不再引入 `delta_P E_{I,out}` 项。原因是 `LowerArmPhaseSense=POSITIVE` 时上下臂同相，有限臂不平衡归一化后只剩公共相位：

$$
H_P^{vpi}(t)=\sqrt{L_P}\exp(j\phi_P(t)).
$$

若显式设置 `er_model="thesis"`，父级 / 主调制器消光比才使用论文中的 `delta_P E_{I,out}` 项：

$$
\delta_P=
\frac{1}{\sqrt{ER_P}-1}
=
\frac{1}{10^{ER_{P,dB}/20}-1}.
$$

当：

$$
ER_{P,dB}=30\ \mathrm{dB},
$$

有：

$$
\delta_P\approx 0.032655.
$$

因此 `er_model="thesis"` 下父级合成等价于：

$$
E_{out}(t)
=
(1+\delta_P)E_{I,out}(t)
+
E_{Q,out}(t)\exp(j\phi_P(t)).
$$

---

## 4. 理想情况下的归一化传输函数

当：

$$
\delta_I=\delta_Q=\delta_P=0,\qquad
\gamma_P=1,\qquad
L_{global}=L_I=L_Q=L_P=1,
$$

有：

$$
E_{out}(t)=
\frac{E_{in}}{2}
\left[
\cos\left(\frac{\phi_I(t)}{2}\right)
+
\cos\left(\frac{\phi_Q(t)}{2}\right)
\exp(j\phi_P(t))
\right].
$$

归一化光功率传输为：

$$
T(t)
=
\frac{|E_{out}(t)|^2}{|E_{in}|^2}
$$

$$
=
\frac{1}{4}
\left[
A^2+B^2+2AB\cos(\phi_P)
\right],
$$

其中：

$$
A=\cos\left(\frac{\phi_I}{2}\right),
\qquad
B=\cos\left(\frac{\phi_Q}{2}\right).
$$

展开后：

$$
T(t)
=
\frac{1}{8}
\left[
2
+
\cos(\phi_I)
+
\cos(\phi_Q)
+
4
\cos\left(\frac{\phi_I}{2}\right)
\cos\left(\frac{\phi_Q}{2}\right)
\cos(\phi_P)
\right].
$$

注意最后一项必须是半角项：

$$
4
\cos\left(\frac{\phi_I}{2}\right)
\cos\left(\frac{\phi_Q}{2}\right)
\cos(\phi_P),
$$

不是：

$$
4\cos(\phi_I)\cos(\phi_Q)\cos(\phi_P).
$$

---

## 5. 光功率、PD 电流和电谱口径

输出光功率为：

$$
P_{opt}(t)=|E_{out}(t)|^2.
$$

进入 PD 的光功率为：

$$
P_{PD}(t)=\mathrm{pd\_tap}\cdot P_{opt}(t).
$$

PD 电流为：

$$
I_{PD}(t)=R\cdot P_{PD}(t),
$$

其中 `R = Responsivity`，默认：

$$
R=0.786\ \mathrm{A/W}.
$$

电谱中，若：

```python
vpi_compatible_dbm = True
```

则按 VPI 常见的 1 Ω 显示口径：

$$
P_{elec}\propto I^2.
$$

若：

```python
vpi_compatible_dbm = False
```

则按物理负载：

$$
P_{elec}\propto I^2R_{load}.
$$

---

## 6. 当前 VPI demo 参数映射

`dpmzm/vpi_demo.py` 当前默认匹配 VPI 全局设置：

$$
BitRateDefault=10\ \mathrm{GHz},
$$

$$
SampleRateDefault=16\times BitRateDefault=160\ \mathrm{GSa/s},
$$

$$
TimeWindow=\frac{65536}{BitRateDefault}=6.5536\ \mu s.
$$

因此：

$$
N=1048576,
\qquad
RBW=\frac{1}{TimeWindow}=152587.890625\ \mathrm{Hz}.
$$

截图中的 VPI 电压源按 `LowerArmPhaseSense` 分别映射。

MZM 标准输出可写为：

$$
E_{out}
=
E_{in}
\cos\left[
\frac{\pi(V_{upper}-V_{lower})}{2V_\pi}
\right]
\exp\left[
j\frac{\pi(V_{upper}+V_{lower})}{2V_\pi}
\right].
$$

若 `LowerArmPhaseSense = NEGATIVE`，同一电压使上下臂相位反向：

$$
V_{upper}=V,\qquad V_{lower}=-V.
$$

因此：

$$
E_{out}=E_{in}\cos\left(\frac{\pi V}{V_\pi}\right),
$$

公共指数相位抵消。这适用于 I/Q 子调制器。

若 `LowerArmPhaseSense = POSITIVE`，同一电压使上下臂相位同向：

$$
V_{upper}=V,\qquad V_{lower}=V.
$$

因此：

$$
E_{out}=E_{in}\exp\left(j\frac{\pi V}{V_\pi}\right),
$$

cos 幅度项为 1，仅留下公共相位。这适用于当前 VPI 截图里的父级 / 主调制器。

因此 demo 中使用：

```python
child_drive_gain = 2.0
parent_drive_gain = 1.0
rf_drive_gain = 2.0
```

映射到 Python 模型的等效电压：

| VPI 参数 | Python 等效参数 |
|---|---|
| I 子 MZM DC = 2.5 V | `V_DCI = 5.0 V` |
| Q 子 MZM DC = 2.5 V | `V_DCQ = 5.0 V` |
| P 父级 DC = 1.25 V | `V_DCP = 1.25 V` |
| RF peak = 1.0 V | `V_RFI_amp = V_RFQ_amp = 2.0 V` |

此时：

$$
\phi_I=\phi_Q=\pi,
\qquad
\phi_P=\frac{\pi}{4},
$$

对应 I/Q 子 MZM 最小传输点，以及父级 POSITIVE 模式下的公共相位移。

---

## 7. 当前和 VPI marker 的差异

用户给出的 VPI PD 电谱 marker 为：

| 分量 | VPI |
|---|---:|
| DC | -49 dBm |
| 1f | -74 dBm |
| 2f | -53 dBm |

当前 Python 默认 `er_model="vpi"`、`rf_phase_Q = 90°`，并按 VPI 三个 `DiffMZ_DSM` block 分别施加 `IL_I/Q/P=6 dB` 时。这里 P block 的 `InsertionLoss=6 dB` 只作用在 Q 光路：

| 分量 | Python | VPI | 差值 |
|---|---:|---:|---:|
| DC | -49.08 dBm | -49.00 dBm | -0.08 dB |
| 1f | -74.03 dBm | -74.00 dBm | -0.03 dB |
| 2f | -53.85 dBm | -53.00 dBm | -0.85 dB |

这个结果说明：

1. VPI 的时间窗 / RBW、1 ohm 电谱口径、PD 响应度、RF/DC 电压幅度保持不变即可基本对齐；
2. 关键修正是父级 `POSITIVE` block 的插损位置：它在 Q 光路上，而不是 DPMZM 总输出的公共损耗；
3. 第二个关键修正是有限消光比归一化：`ER=30 dB` 不应提高最大透射点；
4. 单个 `DiffMZ_DSM` 自检中，`Pin=10 dBm`、`InsertionLoss=6 dB`、最大传输点输出为 `4 dBm`，因此模型中的单个 MZM block 不再引入额外 3 dB / 6 dB 归一化损耗。

---

## 8. 当前重点待核对项

1. VPI `Power N` 模块是否还有额外光功率比例或归一化；
2. SignalAnalyzer 对 DC/1f/2f marker 的功率定义是 peak、RMS、单边谱还是双边谱；
3. VPI `DiffMZ_DSM` 的 RF 端口输入电压是单臂电压、差分电压，还是内部再做 push-pull 映射；
4. 外部 `PhaseShift = 90 deg` 进入 Q 路后，是否还叠加了端口符号或内部上下臂符号。
