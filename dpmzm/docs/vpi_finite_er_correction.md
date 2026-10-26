# VPI 有限消光比对齐错误总结

## 背景

在 DPMZM 与 VPI `DiffMZ_DSM` 链路对齐时，前期模型已经修正了三个关键口径：

1. I/Q 子调制器 `LowerArmPhaseSense=NEGATIVE`，VPI 电压源需要映射为 Python 中的两倍有效差分相位电压；
2. P / 主调制器 `LowerArmPhaseSense=POSITIVE`，电压源不再加倍，只作为公共相位驱动；
3. P block 位于 Q 光路，因此 `IL_P_dB` 只作用在 Q 路，不是 I/Q 两路共同的输出损耗。

完成这些修正后，模型与 VPI 仍存在约 `0.95 dB` 的电谱公共偏差。

## 现象

在 VPI 电压源设置为：

```text
I DC = 1 V
Q DC = 1 V
P DC = 1 V
RF peak = 1 V
```

对应 Python 有效参数为：

```python
V_DCI = 2.0
V_DCQ = 2.0
V_DCP = 1.0
V_RFI_amp = 2.0
V_RFQ_amp = 2.0
```

旧模型得到：

| 分量 | Python 旧模型 | VPI | 差值 |
|---|---:|---:|---:|
| DC | -33.738 dBm | -34.690 dBm | +0.952 dB |
| 1f | -40.337 dBm | -41.320 dBm | +0.983 dB |
| 2f | -61.813 dBm | -62.830 dBm | +1.017 dB |

三个频点几乎是同一个平移量，因此一开始看起来像 PD 前存在约 `0.47 dB` 的公共光功率损耗。

进一步关闭 RF 后，VPI PowerMeter 读数为：

```text
VPI RF off optical power = -0.717 dBm
Python old RF off optical power = -0.246 dBm
```

光功率差为：

```text
0.471 dB
```

电谱功率近似正比于 PD 电流平方，而 PD 电流正比于光功率，所以 `0.471 dB` 光功率差会变成约 `0.942 dB` 电谱差。这解释了 RF 打开时的三个 marker 偏差。

## 错误原因

旧模型将有限消光比写成论文残余场形式：

$$
H_{old}(\phi)
=
\cos\left(\frac{\phi}{2}\right)
+
\delta \exp\left(j\frac{\phi}{2}\right)
$$

其中：

$$
\delta = \frac{1}{10^{ER_{dB}/20}-1}
$$

这个形式可以给出正确的最小点残余，但它没有归一化最大透射点。最大透射点附近：

$$
H_{old}(0)=1+\delta
$$

当 `ER=30 dB` 时：

```text
delta = 0.032655
20log10(1 + delta) = 0.279 dB
```

因此每个有限消光比 block 都会在最大透射附近引入一个并不存在的幅度提升。多个 block 叠加后，就表现为约 `0.47 dB` 的“公共光功率偏高”。

这不是 VPI 的行为。VPI 的 `InsertionLoss` 描述为 fiber-in to fiber-out attenuation，因此在最大透射点：

```text
Pin = 10 dBm
InsertionLoss = 6 dB
Pout = 4 dBm
```

有限消光比只应该决定最小点残余，不应该改变最大点由插损定义的输出功率。

## 修正方式

默认模型改为 VPI 风格的归一化臂不平衡形式：

$$
H_{vpi}(\phi)
=
\frac{
\cos\left(\frac{\phi}{2}\right)
+
\delta \exp\left(j\frac{\phi}{2}\right)
}{1+\delta}
$$

这个形式满足：

$$
H_{vpi}(0)=1
$$

并且在最小点：

$$
\left|H_{vpi}(\pi)\right|
=
\frac{\delta}{1+\delta}
=
10^{-ER_{dB}/20}
$$

因此它同时满足：

1. 最大透射点不超过 `InsertionLoss` 定义；
2. 最小透射点仍符合给定消光比。

对于 `LowerArmPhaseSense=POSITIVE` 的 P block，上下臂同相，归一化臂不平衡后只保留公共相位：

$$
H_P^{vpi}(t)=\sqrt{L_P}\exp(j\phi_P(t))
$$

因此默认 VPI 对齐模型不再使用 `delta_P E_I` 作为父级泄漏项。

## 代码变更

新增参数：

```python
er_model="vpi"
```

默认值 `"vpi"` 使用上述归一化有限消光比模型。

如果需要复现早期论文推导中的非归一化残余项，可以显式设置：

```python
er_model="thesis"
```

对应代码位置：

```text
dpmzm/model.py
  mzm_block_output_field(...)
  dpmzm_output_field(...)
  simulate_dpmzm(..., er_model="vpi")
```

## 修正后验证

在 `I=1 V, Q=1 V, P=1 V, RF peak=1 V` 的 VPI 测试点：

| 分量 | Python 新模型 | VPI | 差值 |
|---|---:|---:|---:|
| DC | -34.683 dBm | -34.690 dBm | +0.007 dB |
| 1f | -41.313 dBm | -41.320 dBm | +0.007 dB |
| 2f | -62.827 dBm | -62.830 dBm | +0.003 dB |

RF 关闭纯 DC 光功率：

| 项目 | 功率 |
|---|---:|
| Python 新模型 | -0.716 dBm |
| VPI PowerMeter | -0.717 dBm |

这说明前面的 `0.47 dB` 并不是额外真实光路损耗，而是有限消光比残余项未归一化导致的模型错误。
