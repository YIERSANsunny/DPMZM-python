# I-P 交调项公式推导及其随 P 路偏压变化趋势

## 1. 问题目标

本文整理 DPMZM 中 **I 路导频** 与 **P 路导频** 共同作用时产生的 **I-P 交调项**，并分析该交调项随 P 路偏压变化的趋势。

目标是得到如下关系：

```text
I 路导频 + P 路导频
        ↓
PD 输出电流中出现 |fI - fP| 和 fI + fP 交调分量
        ↓
交调幅度随 P 路偏压 ΦP 呈周期性变化
```

---

## 2. 基础符号定义

DPMZM 三路相位定义为：

$$
\varphi_I=\frac{\pi(V_{RFI}+V_{DCI})}{V_\pi}
$$

$$
\varphi_Q=\frac{\pi(V_{RFQ}+V_{DCQ})}{V_\pi}
$$

$$
\varphi_P=\frac{\pi V_{DCP}}{V_\pi}
$$

其中：

| 符号 | 含义 |
|---|---|
| $\varphi_I$ | I 路子 MZM 相位 |
| $\varphi_Q$ | Q 路子 MZM 相位 |
| $\varphi_P$ | P 路父级相位 |
| $V_\pi$ | 半波电压 |

定义：

$$
A=\cos\left(\frac{\varphi_I}{2}\right)
$$

$$
B=\cos\left(\frac{\varphi_Q}{2}\right)
$$

静态偏置点处定义：

$$
A_0=\cos\left(\frac{\Phi_I}{2}\right)
$$

$$
B_0=\cos\left(\frac{\Phi_Q}{2}\right)
$$

$$
a_0=\sin\left(\frac{\Phi_I}{2}\right)
$$

$$
b_0=\sin\left(\frac{\Phi_Q}{2}\right)
$$

$$
c_P=\cos(\Phi_P)
$$

$$
s_P=\sin(\Phi_P)
$$

同时定义：

$$
K=\frac{\eta P_m}{8}
$$

$$
\Delta=\delta_I+\delta_Q+\delta_P
$$

其中：

| 符号 | 含义 |
|---|---|
| $\eta$ | 光电探测器响应系数 |
| $P_m$ | 输入光功率幅度因子 |
| $\delta_I$ | I 路有限消光比非理想因子 |
| $\delta_Q$ | Q 路有限消光比非理想因子 |
| $\delta_P$ | 父级幅度不平衡非理想因子 |
| $\Delta$ | 一阶非理想因子的总和 |

---

## 3. 理想 DPMZM 光电流模型

理想 DPMZM 输出光场为：

$$
E_{out}(t)
=
\frac{E_{in}(t)}{2}
\left[
\cos\left(\frac{\varphi_I}{2}\right)
+
\cos\left(\frac{\varphi_Q}{2}\right)
e^{j\varphi_P}
\right]
$$

令：

$$
A=\cos\left(\frac{\varphi_I}{2}\right)
$$

$$
B=\cos\left(\frac{\varphi_Q}{2}\right)
$$

则：

$$
E_{out}(t)
=
\frac{E_{in}(t)}{2}
\left[
A+Be^{j\varphi_P}
\right]
$$

PD 输出电流正比于输出光场模平方：

$$
I_{DPMZM}
=
\eta E_{out}E_{out}^{*}
$$

所以理想归一化光电流为：

$$
I_{id}
=
K
\left[
2+\cos(\varphi_I)+\cos(\varphi_Q)
+
4\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
\right]
$$

其中：

$$
K=\frac{\eta P_m}{8}
$$

需要注意，只有最后一项同时包含 $\varphi_I$ 和 $\varphi_P$：

$$
4K
\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
$$

因此，I-P 交调项主要来源于该干涉项。

---

## 4. I 路和 P 路小信号导频定义

为了分析 I-P 交调项，在 I 路和 P 路直流偏置上分别叠加低频小幅导频。

令：

$$
\varphi_I(t)
=
\Phi_I
+
m_I\sin(\omega_I t)
$$

$$
\varphi_P(t)
=
\Phi_P
+
m_P\sin(\omega_P t)
$$

Q 路暂时固定：

$$
\varphi_Q(t)=\Phi_Q
$$

其中：

| 符号 | 含义 |
|---|---|
| $\Phi_I$ | I 路当前静态偏置相位 |
| $\Phi_Q$ | Q 路当前静态偏置相位 |
| $\Phi_P$ | P 路当前静态偏置相位 |
| $m_I$ | I 路导频相位调制深度 |
| $m_P$ | P 路导频相位调制深度 |
| $\omega_I$ | I 路导频角频率 |
| $\omega_P$ | P 路导频角频率 |

---

## 5. 泰勒展开形式

光电流可对 $\varphi_I$ 和 $\varphi_P$ 在静态偏置点附近作二阶泰勒展开：

$$
I(t)
\approx
I(\Phi_I,\Phi_Q,\Phi_P)
+
m_I D_I\sin(\omega_I t)
+
m_P D_P\sin(\omega_P t)
+
m_I m_P D_{IP}
\sin(\omega_I t)\sin(\omega_P t)
$$

其中：

$$
D_I=
\left.
\frac{\partial I}{\partial \varphi_I}
\right|_{\Phi_I,\Phi_Q,\Phi_P}
$$

$$
D_P=
\left.
\frac{\partial I}{\partial \varphi_P}
\right|_{\Phi_I,\Phi_Q,\Phi_P}
$$

$$
D_{IP}
=
\left.
\frac{\partial^2 I}{\partial \varphi_I\partial \varphi_P}
\right|_{\Phi_I,\Phi_Q,\Phi_P}
$$

其中 $D_{IP}$ 就是 I-P 交调项的系数。

因此：

$$
I_{IP}(t)
=
m_I m_P D_{IP}
\sin(\omega_I t)\sin(\omega_P t)
$$

---

## 6. 理想情况下的 I-P 交调项推导

理想光电流中与 I-P 交调有关的项为：

$$
I_{I,P}^{id}
=
4K
\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
$$

先对 $\varphi_I$ 求偏导：

$$
\frac{\partial I_{I,P}^{id}}{\partial \varphi_I}
=
4K
\left[
-\frac{1}{2}
\sin\left(\frac{\varphi_I}{2}\right)
\right]
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
$$

即：

$$
\frac{\partial I_{I,P}^{id}}{\partial \varphi_I}
=
-2K
\sin\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
$$

再对 $\varphi_P$ 求偏导：

$$
\frac{\partial^2 I_{I,P}^{id}}{\partial \varphi_I\partial \varphi_P}
=
-2K
\sin\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\left[
-\sin(\varphi_P)
\right]
$$

因此：

$$
D_{IP}^{id}
=
2K
\sin\left(\frac{\Phi_I}{2}\right)
\cos\left(\frac{\Phi_Q}{2}\right)
\sin(\Phi_P)
$$

使用前面定义：

$$
a_0=\sin\left(\frac{\Phi_I}{2}\right)
$$

$$
B_0=\cos\left(\frac{\Phi_Q}{2}\right)
$$

$$
s_P=\sin(\Phi_P)
$$

得到：

$$
\boxed{
D_{IP}^{id}
=
2K a_0B_0s_P
}
$$

所以理想 I-P 交调项为：

$$
\boxed{
I_{IP}^{id}(t)
=
2K m_I m_P a_0B_0s_P
\sin(\omega_I t)\sin(\omega_P t)
}
$$

---

## 7. 和频与差频形式

根据三角恒等式：

$$
\sin(\omega_I t)\sin(\omega_P t)
=
\frac{1}{2}
\left[
\cos((\omega_I-\omega_P)t)
-
\cos((\omega_I+\omega_P)t)
\right]
$$

所以：

$$
I_{IP}^{id}(t)
=
K m_I m_P a_0B_0s_P
\left[
\cos((\omega_I-\omega_P)t)
-
\cos((\omega_I+\omega_P)t)
\right]
$$

因此，PD 电谱中会出现两个 I-P 交调频率分量：

$$
f_{IP,-}=|f_I-f_P|
$$

$$
f_{IP,+}=f_I+f_P
$$

两个频点处的交调幅度均正比于：

$$
\left|K m_I m_P a_0B_0s_P\right|
$$

即：

$$
\boxed{
|I_{IP,\pm}^{id}|
\propto
|a_0B_0\sin(\Phi_P)|
}
$$

---

## 8. 一阶非理想模型下的 I-P 交调项

考虑有限消光比和幅度不平衡后，一阶非理想光电流可写成：

$$
I_{DPMZM}
=
I_{id}+I_{syn}+I_{asym}+O(\delta_k^2)
$$

其中，与 I-P 交调有关的项包括三部分。

第一部分来自理想项与同步变化项：

$$
4K(1+\Delta)
\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
$$

第二部分来自 I 路非理想非对称扰动项：

$$
4K\delta_I
\cos\left(\frac{\varphi_Q}{2}\right)
\sin\left(\frac{\varphi_I}{2}\right)
\sin(\varphi_P)
$$

第三部分来自 Q 路非理想非对称扰动项：

$$
-4K\delta_Q
\cos\left(\frac{\varphi_I}{2}\right)
\sin\left(\frac{\varphi_Q}{2}\right)
\sin(\varphi_P)
$$

因此，保留一阶非理想量时，与 I-P 交调相关的光电流项为：

$$
I_{I,P}
=
4K(1+\Delta)
\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
+
4K\delta_I
\cos\left(\frac{\varphi_Q}{2}\right)
\sin\left(\frac{\varphi_I}{2}\right)
\sin(\varphi_P)
-
4K\delta_Q
\cos\left(\frac{\varphi_I}{2}\right)
\sin\left(\frac{\varphi_Q}{2}\right)
\sin(\varphi_P)
$$

对 $\varphi_I$ 和 $\varphi_P$ 求二阶混合偏导，可得：

$$
\boxed{
D_{IP}
=
2K
\left[
(1+\Delta)a_0B_0s_P
+
\delta_I A_0B_0c_P
+
\delta_Q a_0b_0c_P
\right]
}
$$

其中：

$$
A_0=\cos\left(\frac{\Phi_I}{2}\right)
$$

$$
a_0=\sin\left(\frac{\Phi_I}{2}\right)
$$

$$
B_0=\cos\left(\frac{\Phi_Q}{2}\right)
$$

$$
b_0=\sin\left(\frac{\Phi_Q}{2}\right)
$$

$$
c_P=\cos(\Phi_P)
$$

$$
s_P=\sin(\Phi_P)
$$

---

## 9. I-P 交调项完整公式

因此，一阶非理想模型下，I-P 交调项为：

$$
\boxed{
I_{IP}(t)
=
m_I m_P D_{IP}
\sin(\omega_I t)\sin(\omega_P t)
}
$$

其中：

$$
\boxed{
D_{IP}
=
2K
\left[
(1+\Delta)a_0B_0s_P
+
\delta_I A_0B_0c_P
+
\delta_Q a_0b_0c_P
\right]
}
$$

代入后得到：

$$
\boxed{
I_{IP}(t)
=
2K m_I m_P
\left[
(1+\Delta)a_0B_0s_P
+
\delta_I A_0B_0c_P
+
\delta_Q a_0b_0c_P
\right]
\sin(\omega_I t)\sin(\omega_P t)
}
$$

展开为和频、差频形式：

$$
\boxed{
I_{IP}(t)
=
K m_I m_P
\left[
(1+\Delta)a_0B_0s_P
+
\delta_I A_0B_0c_P
+
\delta_Q a_0b_0c_P
\right]
\left[
\cos((\omega_I-\omega_P)t)
-
\cos((\omega_I+\omega_P)t)
\right]
}
$$

所以 $f_I+f_P$ 和 $|f_I-f_P|$ 处的交调分量幅度均正比于：

$$
\boxed{
\left|
K m_I m_P
\left[
(1+\Delta)a_0B_0s_P
+
\delta_I A_0B_0c_P
+
\delta_Q a_0b_0c_P
\right]
\right|
}
$$

---

## 10. I-P 交调项随 P 路偏压的变化趋势

为了单独分析 I-P 交调项随 P 路偏压 $\Phi_P$ 的变化，将 $D_{IP}$ 中与 $\Phi_P$ 有关的项提取出来。

原式为：

$$
D_{IP}
=
2K
\left[
(1+\Delta)a_0B_0\sin(\Phi_P)
+
\delta_I A_0B_0\cos(\Phi_P)
+
\delta_Q a_0b_0\cos(\Phi_P)
\right]
$$

合并 $\cos(\Phi_P)$ 项：

$$
D_{IP}
=
2K
\left[
(1+\Delta)a_0B_0\sin(\Phi_P)
+
(\delta_I A_0B_0+\delta_Q a_0b_0)\cos(\Phi_P)
\right]
$$

定义：

$$
S=(1+\Delta)a_0B_0
$$

$$
C=\delta_I A_0B_0+\delta_Q a_0b_0
$$

则：

$$
\boxed{
D_{IP}(\Phi_P)
=
2K
\left[
S\sin(\Phi_P)+C\cos(\Phi_P)
\right]
}
$$

因此，I-P 交调幅度随 P 路偏压的变化趋势为：

$$
\boxed{
|I_{IP,\pm}|
\propto
\left|
S\sin(\Phi_P)+C\cos(\Phi_P)
\right|
}
$$

I-P 交调功率随 P 路偏压的变化趋势为：

$$
\boxed{
P_{IP}
\propto
\left[
S\sin(\Phi_P)+C\cos(\Phi_P)
\right]^2
}
$$

---

## 11. 写成带相位偏移的正弦平方形式

由于：

$$
S\sin(\Phi_P)+C\cos(\Phi_P)
$$

可以合成为一个带相位偏移的正弦函数：

$$
S\sin(\Phi_P)+C\cos(\Phi_P)
=
R\sin(\Phi_P+\theta)
$$

其中：

$$
R=\sqrt{S^2+C^2}
$$

$$
\theta=\arctan\left(\frac{C}{S}\right)
$$

更严谨地，为了确定象限，应写成：

$$
\theta=\operatorname{atan2}(C,S)
$$

因此：

$$
D_{IP}(\Phi_P)
=
2KR\sin(\Phi_P+\theta)
$$

交调功率为：

$$
\boxed{
P_{IP}
\propto
R^2\sin^2(\Phi_P+\theta)
}
$$

这说明：

$$
\boxed{
I-P 交调功率随 P 路偏压总体呈带相位偏移的正弦平方型变化。
}
$$

---

## 12. 理想情况下的 P 路变化趋势

理想情况下：

$$
\delta_I=\delta_Q=\delta_P=0
$$

因此：

$$
\Delta=0
$$

$$
C=0
$$

$$
S=a_0B_0
$$

所以：

$$
D_{IP}^{id}(\Phi_P)
=
2K a_0B_0\sin(\Phi_P)
$$

I-P 交调幅度为：

$$
\boxed{
|I_{IP,\pm}^{id}|
\propto
|a_0B_0\sin(\Phi_P)|
}
$$

I-P 交调功率为：

$$
\boxed{
P_{IP}^{id}
\propto
a_0^2B_0^2\sin^2(\Phi_P)
}
$$

因此，理想情况下，I-P 交调功率随 P 路偏压呈：

$$
\boxed{
\sin^2(\Phi_P)
}
$$

变化。

对应关系如下：

| P 路相位 $\Phi_P$ | $\sin(\Phi_P)$ | I-P 交调幅度 | I-P 交调功率 |
|---|---:|---:|---:|
| $0$ | 0 | 最小 | 最小 |
| $\frac{\pi}{2}$ | 1 | 最大 | 最大 |
| $\pi$ | 0 | 最小 | 最小 |
| $\frac{3\pi}{2}$ | -1 | 最大 | 最大 |
| $2\pi$ | 0 | 最小 | 最小 |

所以理想情况下：

$$
\boxed{
\Phi_P=0,\pi,2\pi,\cdots
\quad \Rightarrow \quad
I\text{-}P 交调最小
}
$$

$$
\boxed{
\Phi_P=\frac{\pi}{2},\frac{3\pi}{2},\cdots
\quad \Rightarrow \quad
I\text{-}P 交调最大
}
$$

---

## 13. Q 路偏置对 I-P 交调项的影响

理想 I-P 交调项为：

$$
D_{IP}^{id}
=
2K a_0B_0s_P
$$

其中最关键的因子是：

$$
B_0=\cos\left(\frac{\Phi_Q}{2}\right)
$$

当 Q 路位于最小传输点时：

$$
\Phi_Q=\pi
$$

因此：

$$
B_0=\cos\left(\frac{\pi}{2}\right)=0
$$

于是：

$$
D_{IP}^{id}=0
$$

也就是说：

$$
\boxed{
当 Q 路严格处于最小传输点时，理想 I-P 交调项会被压低到零。
}
$$

这说明 I-P 交调项不是一个单纯由 P 路决定的量，它强烈依赖 Q 路偏置状态。

特别地：

```text
Q 路偏离最小点越明显
        ↓
B0 = cos(ΦQ/2) 越不为零
        ↓
I-P 交调项越明显
```

反过来：

```text
Q 路越接近最小点
        ↓
B0 越接近零
        ↓
理想 I-P 交调项越弱
```

---

## 14. I/Q 均接近最小点时的近似

在 CS-SSB 偏置附近，通常有：

$$
\Phi_I\approx\pi
$$

$$
\Phi_Q\approx\pi
$$

于是：

$$
A_0=\cos\left(\frac{\Phi_I}{2}\right)\approx 0
$$

$$
B_0=\cos\left(\frac{\Phi_Q}{2}\right)\approx 0
$$

$$
a_0=\sin\left(\frac{\Phi_I}{2}\right)\approx 1
$$

$$
b_0=\sin\left(\frac{\Phi_Q}{2}\right)\approx 1
$$

代入完整公式：

$$
D_{IP}
=
2K
\left[
(1+\Delta)a_0B_0s_P
+
\delta_I A_0B_0c_P
+
\delta_Q a_0b_0c_P
\right]
$$

得到近似：

$$
\boxed{
D_{IP}
\approx
2K
\left[
(1+\Delta)B_0\sin(\Phi_P)
+
\delta_Q\cos(\Phi_P)
\right]
}
$$

这说明在 I/Q 均靠近最小点时，I-P 交调项主要由两部分组成：

第一部分：

$$
(1+\Delta)B_0\sin(\Phi_P)
$$

它来自理想干涉项，但需要 Q 路偏离最小点，即 $B_0\neq0$。

第二部分：

$$
\delta_Q\cos(\Phi_P)
$$

它来自 Q 路有限消光比等非理想残余。

---

## 15. 几种典型情况分析

### 15.1 情况一：Q 路没有锁在最小点

如果：

$$
B_0\neq0
$$

且非理想项较小：

$$
\delta_I,\delta_Q,\delta_P\approx0
$$

则：

$$
D_{IP}
\approx
2K a_0B_0\sin(\Phi_P)
$$

交调功率：

$$
P_{IP}
\propto
a_0^2B_0^2\sin^2(\Phi_P)
$$

此时扫 P 路偏压，会看到明显的 $\sin^2(\Phi_P)$ 趋势：

```text
P 路 0 点附近：交调小
P 路 π/2 附近：交调大
P 路 π 附近：交调小
P 路 3π/2 附近：交调大
```

---

### 15.2 情况二：Q 路严格锁在最小点，且器件理想

如果：

$$
\Phi_Q=\pi
$$

则：

$$
B_0=0
$$

如果同时：

$$
\delta_I=\delta_Q=\delta_P=0
$$

则：

$$
D_{IP}=0
$$

因此：

$$
\boxed{
I_{IP}(t)\approx0
}
$$

此时无论怎么扫 P 路偏压，I-P 交调项都很弱，几乎看不到明显变化。

---

### 15.3 情况三：Q 路严格锁在最小点，但存在有限消光比

如果：

$$
B_0\approx0
$$

但：

$$
\delta_Q\neq0
$$

则：

$$
D_{IP}
\approx
2K\delta_Q\cos(\Phi_P)
$$

交调功率：

$$
P_{IP}
\propto
\delta_Q^2\cos^2(\Phi_P)
$$

此时扫 P 路偏压，会看到近似 $\cos^2(\Phi_P)$ 趋势：

```text
P 路 0 点附近：交调较大
P 路 π/2 附近：交调较小
P 路 π 附近：交调较大
P 路 3π/2 附近：交调较小
```

但是这个交调项来自非理想残余，通常强度较弱。

---

## 16. 换成 P 路电压形式

由于：

$$
\Phi_P=\frac{\pi V_{DCP}}{V_\pi}
$$

所以 I-P 交调功率随 P 路电压的变化可以写成：

$$
\boxed{
P_{IP}(V_{DCP})
\propto
\left[
S\sin\left(\frac{\pi V_{DCP}}{V_\pi}\right)
+
C\cos\left(\frac{\pi V_{DCP}}{V_\pi}\right)
\right]^2
}
$$

其中：

$$
S=(1+\Delta)a_0B_0
$$

$$
C=\delta_I A_0B_0+\delta_Q a_0b_0
$$

由于 $\sin^2(\cdot)$ 或 $\cos^2(\cdot)$ 的周期是 $\pi$，而：

$$
\Phi_P=\frac{\pi V_{DCP}}{V_\pi}
$$

所以交调功率关于 P 路电压的周期为：

$$
\boxed{
V_\pi
}
$$

如果观察交调电流的带符号系数 $D_{IP}$，其周期为：

$$
\boxed{
2V_\pi
}
$$

需要区分：

| 观察量 | 关于 $\Phi_P$ 的周期 | 关于 $V_{DCP}$ 的周期 |
|---|---:|---:|
| 交调电流系数 $D_{IP}$ | $2\pi$ | $2V_\pi$ |
| 交调幅度 $|D_{IP}|$ | $\pi$ | $V_\pi$ |
| 交调功率 $D_{IP}^2$ | $\pi$ | $V_\pi$ |

---

## 17. 与 I-Q 交调项的区别

I-Q 交调项在 I/Q 均靠近最小点时，近似满足：

$$
D_{IQ}
\approx
K(1+\Delta)\cos(\Phi_P)
$$

所以：

$$
P_{IQ}
\propto
\cos^2(\Phi_P)
$$

因此 I-Q 交调功率在：

$$
\Phi_P=\frac{\pi}{2},\frac{3\pi}{2}
$$

附近最小，适合用于搜索 P 路正交点。

但是 I-P 交调项理想情况下为：

$$
D_{IP}^{id}
=
2K a_0B_0\sin(\Phi_P)
$$

它包含：

$$
B_0=\cos\left(\frac{\Phi_Q}{2}\right)
$$

因此 I-P 交调项强烈依赖 Q 路是否偏离最小点。

所以：

$$
\boxed{
I-Q 交调项更适合作为 P 路正交点搜索指标。
}
$$

而：

$$
\boxed{
I-P 交调项更适合作为 I/Q/P 偏置耦合关系和非理想残余的辅助诊断指标。
}
$$

---

## 18. 物理直觉总结

I-P 交调项的产生依赖两个条件：

1. I 路导频改变 I 路输出光场幅度；
2. P 路导频改变 Q 路相对于 I 路的光场相位；
3. I/Q 两路在合束处发生相干干涉；
4. PD 对合成光场取模平方后，产生交调频率分量。

可以理解为：

```text
I 路导频：让 I 路光场强弱摆动
P 路导频：让 Q 路相对相位摆动
二者在相干合束后相互耦合
PD 平方律探测后出现 fI ± fP 交调
```

但是，如果 Q 路在最小点：

```text
Q 路光场幅度接近 0
        ↓
P 路即使改变 Q 路相位，也没有足够强的 Q 光场参与干涉
        ↓
理想 I-P 交调项被压低
```

因此，I-P 交调项强不强，不只取决于 P 路，也取决于 Q 路是否还有残余光场。

---

## 19. 最终核心公式汇总

### 19.1 I-P 交调系数

$$
\boxed{
D_{IP}
=
2K
\left[
(1+\Delta)a_0B_0s_P
+
\delta_I A_0B_0c_P
+
\delta_Q a_0b_0c_P
\right]
}
$$

### 19.2 I-P 交调时域项

$$
\boxed{
I_{IP}(t)
=
m_I m_P D_{IP}
\sin(\omega_I t)\sin(\omega_P t)
}
$$

### 19.3 I-P 交调和频、差频形式

$$
\boxed{
I_{IP}(t)
=
\frac{m_I m_P D_{IP}}{2}
\left[
\cos((\omega_I-\omega_P)t)
-
\cos((\omega_I+\omega_P)t)
\right]
}
$$

### 19.4 I-P 交调出现的频率

$$
\boxed{
f_{IP,-}=|f_I-f_P|
}
$$

$$
\boxed{
f_{IP,+}=f_I+f_P
}
$$

### 19.5 随 P 路偏压的变化趋势

$$
\boxed{
P_{IP}
\propto
\left[
S\sin(\Phi_P)+C\cos(\Phi_P)
\right]^2
}
$$

其中：

$$
S=(1+\Delta)a_0B_0
$$

$$
C=\delta_I A_0B_0+\delta_Q a_0b_0
$$

### 19.6 理想情况下的变化趋势

$$
\boxed{
P_{IP}^{id}
\propto
a_0^2B_0^2\sin^2(\Phi_P)
}
$$

### 19.7 I/Q 均接近最小点时的近似

$$
\boxed{
D_{IP}
\approx
2K
\left[
(1+\Delta)B_0\sin(\Phi_P)
+
\delta_Q\cos(\Phi_P)
\right]
}
$$

---

## 20. 结论

I-P 交调项的完整一阶表达式为：

$$
D_{IP}
=
2K
\left[
(1+\Delta)a_0B_0\sin(\Phi_P)
+
\delta_I A_0B_0\cos(\Phi_P)
+
\delta_Q a_0b_0\cos(\Phi_P)
\right]
$$

它随 P 路偏压的变化趋势可以概括为：

$$
P_{IP}
\propto
\left[
S\sin(\Phi_P)+C\cos(\Phi_P)
\right]^2
$$

因此，I-P 交调功率整体上是一个带相位偏移的正弦平方型曲线。

在理想情况下：

$$
P_{IP}^{id}
\propto
\sin^2(\Phi_P)
$$

但这个趋势是否明显，取决于：

$$
B_0=\cos\left(\frac{\Phi_Q}{2}\right)
$$

当 Q 路严格位于最小传输点时：

$$
B_0=0
$$

理想 I-P 交调项会消失。

因此，I-P 交调项不如 I-Q 交调项适合作为 P 路正交点的主误差信号。它更适合作为观察 Q 路残余、有限消光比、I/Q/P 耦合关系和非理想扰动的辅助指标。