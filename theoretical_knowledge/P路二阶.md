# 导频 P 路二阶公式推导参考内容

## 1. 推导目标

本文整理 DPMZM 中 **P 路导频二阶项** 的公式推导。

所谓 P 路导频二阶项，是指在 P 路偏置上叠加低频小信号导频后，由光电流关于 P 路相位的二阶泰勒展开产生的分量。

它主要表现为：

```text
P 路导频频率：fP
        ↓
二阶非线性项：sin²(ωP t)
        ↓
产生 DC 偏移项 和 2fP 二次谐波项
```

因此，P 路导频二阶项的核心研究对象是：

$$
2f_P
$$

处的二次谐波分量。

---

## 2. DPMZM 基础模型

理想 DPMZM 输出光场为：

$$
E_{out}(t)
=
\frac{E_{in}(t)}{2}
\left[
\cos\left(\frac{\varphi_I}{2}\right)
+
\cos\left(\frac{\varphi_Q}{2}\right)e^{j\varphi_P}
\right]
$$

定义：

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

光电探测器输出电流满足：

$$
I_{DPMZM}
=
\eta E_{out}E_{out}^{*}
$$

令：

$$
K=\frac{\eta P_m}{8}
$$

其中：

$$
P_m=|E_m|^2
$$

理想光电流可写为：

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

其中与 P 路相位 $\varphi_P$ 直接相关的是干涉项：

$$
4K
\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
$$

---

## 3. 一阶非理想光电流中与 P 路有关的部分

考虑有限消光比和幅度不平衡后，一阶非理想光电流可写成：

$$
I_{DPMZM}
=
I_{id}+I_{syn}+I_{asym}+O(\delta_k^2)
$$

其中：

$$
\Delta=\delta_I+\delta_Q+\delta_P
$$

与 P 路相位 $\varphi_P$ 有关的部分可以整理为：

$$
I_P
=
4K(1+\Delta)
\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
$$

$$
+
4K\delta_I
\cos\left(\frac{\varphi_Q}{2}\right)
\sin\left(\frac{\varphi_I}{2}\right)
\sin(\varphi_P)
$$

$$
-
4K\delta_Q
\cos\left(\frac{\varphi_I}{2}\right)
\sin\left(\frac{\varphi_Q}{2}\right)
\sin(\varphi_P)
$$

为了简化书写，定义：

$$
A=\cos\left(\frac{\varphi_I}{2}\right)
$$

$$
B=\cos\left(\frac{\varphi_Q}{2}\right)
$$

$$
a=\sin\left(\frac{\varphi_I}{2}\right)
$$

$$
b=\sin\left(\frac{\varphi_Q}{2}\right)
$$

则：

$$
I_P
=
4K(1+\Delta)AB\cos(\varphi_P)
+
4K\delta_I Ba\sin(\varphi_P)
-
4K\delta_Q Ab\sin(\varphi_P)
$$

---

## 4. P 路导频定义

在 P 路偏置上叠加小幅低频导频：

$$
\varphi_P(t)
=
\Phi_P
+
m_P\sin(\omega_P t)
$$

其中：

| 符号 | 含义 |
|---|---|
| $\Phi_P$ | P 路静态偏置相位 |
| $m_P$ | P 路导频相位调制深度 |
| $\omega_P$ | P 路导频角频率 |

I 路和 Q 路暂时固定：

$$
\varphi_I(t)=\Phi_I
$$

$$
\varphi_Q(t)=\Phi_Q
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

---

## 5. 泰勒展开形式

对光电流关于 $\varphi_P$ 在 $\Phi_P$ 附近作二阶泰勒展开：

$$
I(t)
\approx
I_0
+
m_P D_P\sin(\omega_P t)
+
\frac{1}{2}m_P^2D_{PP}\sin^2(\omega_P t)
$$

其中：

$$
D_P
=
\left.
\frac{\partial I}{\partial \varphi_P}
\right|_{\Phi_I,\Phi_Q,\Phi_P}
$$

$$
D_{PP}
=
\left.
\frac{\partial^2 I}{\partial \varphi_P^2}
\right|_{\Phi_I,\Phi_Q,\Phi_P}
$$

其中：

$$
m_P D_P\sin(\omega_P t)
$$

是一阶导频项，对应 $f_P$ 分量。

而：

$$
\frac{1}{2}m_P^2D_{PP}\sin^2(\omega_P t)
$$

是二阶导频项，会产生 DC 分量和 $2f_P$ 分量。

---

## 6. P 路一阶导数推导

由：

$$
I_P
=
4K(1+\Delta)AB\cos(\varphi_P)
+
4K\delta_I Ba\sin(\varphi_P)
-
4K\delta_Q Ab\sin(\varphi_P)
$$

对 $\varphi_P$ 求一阶导数：

$$
\frac{\partial I_P}{\partial \varphi_P}
=
-4K(1+\Delta)AB\sin(\varphi_P)
+
4K\delta_I Ba\cos(\varphi_P)
-
4K\delta_Q Ab\cos(\varphi_P)
$$

因此，在静态偏置点处：

$$
\boxed{
D_P
=
-4K(1+\Delta)A_0B_0s_P
+
4K\delta_I B_0a_0c_P
-
4K\delta_Q A_0b_0c_P
}
$$

该式就是 P 路一阶导频项的系数。

因此，P 路一阶导频分量为：

$$
I_{\omega_P}(t)
=
m_PD_P\sin(\omega_P t)
$$

---

## 7. P 路二阶导数推导

继续对 $\varphi_P$ 求导：

$$
D_{PP}
=
\frac{\partial^2 I_P}{\partial \varphi_P^2}
$$

由：

$$
\frac{\partial}{\partial \varphi_P}\sin(\varphi_P)=\cos(\varphi_P)
$$

$$
\frac{\partial}{\partial \varphi_P}\cos(\varphi_P)=-\sin(\varphi_P)
$$

可得：

$$
\frac{\partial^2 I_P}{\partial \varphi_P^2}
=
-4K(1+\Delta)AB\cos(\varphi_P)
-
4K\delta_I Ba\sin(\varphi_P)
+
4K\delta_Q Ab\sin(\varphi_P)
$$

在静态偏置点处：

$$
\boxed{
D_{PP}
=
-4K(1+\Delta)A_0B_0c_P
-
4K\delta_I B_0a_0s_P
+
4K\delta_Q A_0b_0s_P
}
$$

也可以合并写为：

$$
\boxed{
D_{PP}
=
-4K
\left[
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
\right]
}
$$

---

## 8. P 路二阶导频项完整公式

P 路导频二阶项为：

$$
I_{P,2}(t)
=
\frac{1}{2}m_P^2D_{PP}\sin^2(\omega_P t)
$$

代入 $D_{PP}$：

$$
I_{P,2}(t)
=
\frac{1}{2}m_P^2
\left\{
-4K
\left[
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
\right]
\right\}
\sin^2(\omega_P t)
$$

所以：

$$
\boxed{
I_{P,2}(t)
=
-2Km_P^2
\left[
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
\right]
\sin^2(\omega_P t)
}
$$

该式就是 P 路导频二阶项的完整一阶非理想表达式。

---

## 9. 展开为 DC 项和 $2f_P$ 项

利用三角恒等式：

$$
\sin^2(\omega_P t)
=
\frac{1}{2}
\left[
1-\cos(2\omega_P t)
\right]
$$

代入：

$$
I_{P,2}(t)
=
\frac{1}{2}m_P^2D_{PP}
\sin^2(\omega_P t)
$$

得到：

$$
I_{P,2}(t)
=
\frac{m_P^2D_{PP}}{4}
\left[
1-\cos(2\omega_P t)
\right]
$$

因此：

$$
I_{P,2}(t)
=
\frac{m_P^2D_{PP}}{4}
-
\frac{m_P^2D_{PP}}{4}\cos(2\omega_P t)
$$

所以 P 路二阶项包含两部分：

1. 二阶 DC 偏移项；
2. $2f_P$ 二次谐波项。

---

## 10. P 路二阶 DC 偏移项

二阶 DC 偏移项为：

$$
I_{P,2}^{DC}
=
\frac{m_P^2D_{PP}}{4}
$$

代入 $D_{PP}$：

$$
\boxed{
I_{P,2}^{DC}
=
-Km_P^2
\left[
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
\right]
}
$$

这个项表示 P 路导频的二阶效应会改变 PD 输出电流的平均值。

---

## 11. P 路 $2f_P$ 二次谐波项

$2f_P$ 项为：

$$
I_{2\omega_P}(t)
=
-\frac{m_P^2D_{PP}}{4}\cos(2\omega_P t)
$$

代入 $D_{PP}$：

$$
\boxed{
I_{2\omega_P}(t)
=
Km_P^2
\left[
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
\right]
\cos(2\omega_P t)
}
$$

所以，$2f_P$ 处的电流幅度正比于：

$$
\boxed{
\left|
Km_P^2
\left[
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
\right]
\right|
}
$$

对应的功率趋势为：

$$
\boxed{
P_{2f_P}
\propto
\left[
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
\right]^2
}
$$

---

## 12. 定义简化函数 $G_{PP}$

为了便于分析 P 路二阶项随偏置变化的趋势，定义：

$$
G_{PP}
=
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
$$

则：

$$
\boxed{
D_{PP}
=
-4KG_{PP}
}
$$

$$
\boxed{
I_{P,2}(t)
=
-2Km_P^2G_{PP}\sin^2(\omega_P t)
}
$$

$$
\boxed{
I_{P,2}^{DC}
=
-Km_P^2G_{PP}
}
$$

$$
\boxed{
I_{2\omega_P}(t)
=
Km_P^2G_{PP}\cos(2\omega_P t)
}
$$

$$
\boxed{
P_{2f_P}
\propto
G_{PP}^2
}
$$

---

## 13. 理想情况下的 P 路二阶公式

理想情况下：

$$
\delta_I=\delta_Q=\delta_P=0
$$

因此：

$$
\Delta=0
$$

于是：

$$
G_{PP}^{id}
=
A_0B_0c_P
$$

所以：

$$
D_{PP}^{id}
=
-4KA_0B_0c_P
$$

P 路二阶项为：

$$
\boxed{
I_{P,2}^{id}(t)
=
-2Km_P^2A_0B_0c_P\sin^2(\omega_P t)
}
$$

展开为：

$$
I_{P,2}^{id}(t)
=
-Km_P^2A_0B_0c_P
+
Km_P^2A_0B_0c_P\cos(2\omega_P t)
$$

因此：

$$
\boxed{
I_{P,2}^{DC,id}
=
-Km_P^2A_0B_0\cos(\Phi_P)
}
$$

$$
\boxed{
I_{2\omega_P}^{id}(t)
=
Km_P^2A_0B_0\cos(\Phi_P)\cos(2\omega_P t)
}
$$

$2f_P$ 幅度趋势为：

$$
\boxed{
|I_{2\omega_P}^{id}|
\propto
|A_0B_0\cos(\Phi_P)|
}
$$

$2f_P$ 功率趋势为：

$$
\boxed{
P_{2f_P}^{id}
\propto
A_0^2B_0^2\cos^2(\Phi_P)
}
$$

---

## 14. P 路二阶项随 P 路偏压的变化趋势

完整一阶非理想情况下：

$$
G_{PP}
=
(1+\Delta)A_0B_0\cos(\Phi_P)
+
\delta_I B_0a_0\sin(\Phi_P)
-
\delta_Q A_0b_0\sin(\Phi_P)
$$

合并 $\sin(\Phi_P)$ 项：

$$
G_{PP}
=
(1+\Delta)A_0B_0\cos(\Phi_P)
+
\left[
\delta_I B_0a_0
-
\delta_Q A_0b_0
\right]\sin(\Phi_P)
$$

定义：

$$
M=(1+\Delta)A_0B_0
$$

$$
N=\delta_I B_0a_0-\delta_Q A_0b_0
$$

则：

$$
\boxed{
G_{PP}(\Phi_P)
=
M\cos(\Phi_P)+N\sin(\Phi_P)
}
$$

因此，$2f_P$ 幅度趋势为：

$$
\boxed{
|I_{2\omega_P}|
\propto
|M\cos(\Phi_P)+N\sin(\Phi_P)|
}
$$

$2f_P$ 功率趋势为：

$$
\boxed{
P_{2f_P}
\propto
\left[
M\cos(\Phi_P)+N\sin(\Phi_P)
\right]^2
}
$$

---

## 15. 带相位偏移的余弦平方形式

由于：

$$
M\cos(\Phi_P)+N\sin(\Phi_P)
$$

可以合成为：

$$
M\cos(\Phi_P)+N\sin(\Phi_P)
=
R\cos(\Phi_P-\theta)
$$

其中：

$$
R=\sqrt{M^2+N^2}
$$

$$
\theta=\operatorname{atan2}(N,M)
$$

因此：

$$
G_{PP}(\Phi_P)
=
R\cos(\Phi_P-\theta)
$$

所以：

$$
\boxed{
P_{2f_P}
\propto
R^2\cos^2(\Phi_P-\theta)
}
$$

这说明：

$$
\boxed{
P 路导频二阶功率随 P 路偏压总体呈带相位偏移的余弦平方型变化。
}
$$

理想情况下，$N=0$，所以：

$$
\theta=0
$$

于是退化为：

$$
\boxed{
P_{2f_P}^{id}
\propto
\cos^2(\Phi_P)
}
$$

---

## 16. P 路偏压特殊点分析

### 16.1 P 路最大点

若认为 P 路最大点对应：

$$
\Phi_P=0 \pmod{2\pi}
$$

则：

$$
c_P=1
$$

$$
s_P=0
$$

代入：

$$
G_{PP}
=
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
$$

得到：

$$
\boxed{
G_{PP}
=
(1+\Delta)A_0B_0
}
$$

因此：

$$
\boxed{
I_{2\omega_P}(t)
=
Km_P^2(1+\Delta)A_0B_0\cos(2\omega_P t)
}
$$

在 P 路最大点时，P 路二阶项主要由：

$$
A_0B_0
=
\cos\left(\frac{\Phi_I}{2}\right)
\cos\left(\frac{\Phi_Q}{2}\right)
$$

决定。

也就是说：

```text
P 路最大点时：
P 路二阶导频强弱主要取决于 I/Q 两路子 MZM 是否有足够的输出光场参与干涉。
```

---

### 16.2 P 路正交点

若：

$$
\Phi_P=\frac{\pi}{2}
$$

则：

$$
c_P=0
$$

$$
s_P=1
$$

代入：

$$
G_{PP}
=
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
$$

得到：

$$
\boxed{
G_{PP}
=
\delta_I B_0a_0
-
\delta_Q A_0b_0
}
$$

理想情况下：

$$
\delta_I=\delta_Q=0
$$

所以：

$$
G_{PP}^{id}=0
$$

因此：

$$
\boxed{
理想情况下，P 路位于正交点时，P 路二阶导频项最小。
}
$$

若实际系统中在 P 正交点附近仍然存在明显 $2f_P$ 分量，则可能来自：

1. I/Q 子 MZM 的有限消光比；
2. I/Q 两路不对称；
3. P 路偏置没有准确位于正交点；
4. I/Q 路偏置不在预期位置；
5. 模型中被忽略的二阶非理想项。

---

### 16.3 P 路反向最大点

若：

$$
\Phi_P=\pi
$$

则：

$$
c_P=-1
$$

$$
s_P=0
$$

代入：

$$
G_{PP}
=
-(1+\Delta)A_0B_0
$$

所以：

$$
\boxed{
I_{2\omega_P}(t)
=
-Km_P^2(1+\Delta)A_0B_0\cos(2\omega_P t)
}
$$

与 $\Phi_P=0$ 相比，$2f_P$ 分量的符号相反，但幅度相同。

如果只看频谱功率，则两者相同：

$$
P_{2f_P}(\Phi_P=0)
=
P_{2f_P}(\Phi_P=\pi)
$$

---

## 17. I/Q 偏置对 P 路二阶项的影响

P 路二阶项不仅取决于 P 路偏压，也取决于 I/Q 两路偏置。

完整趋势为：

$$
G_{PP}
=
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
$$

其中：

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

理想情况下：

$$
G_{PP}^{id}
=
A_0B_0c_P
$$

所以，理想 P 路二阶项需要 I/Q 两路都有非零输出光场：

$$
A_0B_0\neq0
$$

如果 I 路或 Q 路任意一路严格位于最小传输点：

$$
A_0=0
$$

或：

$$
B_0=0
$$

则理想 P 路二阶项会被压低。

---

## 18. I/Q 均位于最小传输点时

当：

$$
\Phi_I=\pi
$$

$$
\Phi_Q=\pi
$$

有：

$$
A_0=\cos\left(\frac{\pi}{2}\right)=0
$$

$$
B_0=\cos\left(\frac{\pi}{2}\right)=0
$$

$$
a_0=\sin\left(\frac{\pi}{2}\right)=1
$$

$$
b_0=\sin\left(\frac{\pi}{2}\right)=1
$$

代入完整公式：

$$
G_{PP}
=
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
$$

可得：

$$
G_{PP}=0
$$

因此：

$$
\boxed{
当 I/Q 两路均严格位于最小传输点时，在当前一阶非理想模型下，P 路二阶导频项趋近于零。
}
$$

物理原因是：

```text
P 路只改变 Q 路相对于 I 路的相位；
如果 I/Q 两路输出光场都接近零，
则 P 路相位扰动很难通过相干合束转化为明显的光功率变化。
```

需要注意：

```text
如果继续保留 δIδQ 等二阶非理想小量，
I/Q 残余光场之间仍可能产生很弱的 P 相关二阶项；
但这部分属于 O(δk²)，在当前一阶非理想模型中被忽略。
```

---

## 19. I 路扫描时的趋势

如果固定 Q 路和 P 路，观察 P 路二阶项随 I 路偏置 $\Phi_I$ 的变化，可以从：

$$
G_{PP}
=
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
$$

中提取关于 $\Phi_I$ 的部分。

代入：

$$
A_0=\cos\left(\frac{\Phi_I}{2}\right)
$$

$$
a_0=\sin\left(\frac{\Phi_I}{2}\right)
$$

得到：

$$
G_{PP}(\Phi_I)
=
\left[
(1+\Delta)B_0c_P
-
\delta_Q b_0s_P
\right]
\cos\left(\frac{\Phi_I}{2}\right)
+
\delta_I B_0s_P
\sin\left(\frac{\Phi_I}{2}\right)
$$

定义：

$$
U=(1+\Delta)B_0c_P-\delta_Q b_0s_P
$$

$$
V=\delta_I B_0s_P
$$

则：

$$
\boxed{
G_{PP}(\Phi_I)
=
U\cos\left(\frac{\Phi_I}{2}\right)
+
V\sin\left(\frac{\Phi_I}{2}\right)
}
$$

因此：

$$
\boxed{
P_{2f_P}(\Phi_I)
\propto
\left[
U\cos\left(\frac{\Phi_I}{2}\right)
+
V\sin\left(\frac{\Phi_I}{2}\right)
\right]^2
}
$$

理想情况下：

$$
\delta_I=\delta_Q=\delta_P=0
$$

所以：

$$
U=B_0c_P
$$

$$
V=0
$$

得到：

$$
\boxed{
P_{2f_P}^{id}(\Phi_I)
\propto
B_0^2c_P^2
\cos^2\left(\frac{\Phi_I}{2}\right)
}
$$

---

## 20. 特例：P 路最大点，Q 路相位为 $110^\circ$

若 P 路位于最大点：

$$
\Phi_P=0
$$

则：

$$
c_P=1
$$

$$
s_P=0
$$

所以：

$$
G_{PP}
=
(1+\Delta)A_0B_0
$$

若 Q 路相位为：

$$
\Phi_Q=110^\circ
$$

则：

$$
B_0
=
\cos\left(\frac{110^\circ}{2}\right)
=
\cos(55^\circ)
$$

数值为：

$$
B_0\approx0.5736
$$

因此：

$$
G_{PP}(\Phi_I)
\approx
0.5736(1+\Delta)
\cos\left(\frac{\Phi_I}{2}\right)
$$

于是：

$$
\boxed{
I_{2\omega_P}(t)
\approx
0.5736K m_P^2(1+\Delta)
\cos\left(\frac{\Phi_I}{2}\right)
\cos(2\omega_P t)
}
$$

所以 $2f_P$ 幅度随 I 路偏置的变化趋势为：

$$
\boxed{
|I_{2\omega_P}|
\propto
\left|
\cos\left(\frac{\Phi_I}{2}\right)
\right|
}
$$

对应功率趋势为：

$$
\boxed{
P_{2f_P}
\propto
\cos^2\left(\frac{\Phi_I}{2}\right)
}
$$

对应关系如下：

| I 路相位 $\Phi_I$ | $\cos(\Phi_I/2)$ | $2f_P$ 幅度 | $2f_P$ 功率 |
|---|---:|---:|---:|
| $0^\circ$ | $1$ | 最大 | 最大 |
| $90^\circ$ | $0.707$ | 中等 | $1/2$ |
| $180^\circ$ | $0$ | 最小 | 最小 |
| $270^\circ$ | $-0.707$ | 中等，符号反向 | $1/2$ |
| $360^\circ$ | $-1$ | 最大，符号反向 | 最大 |

因此：

$$
\boxed{
当 P 路在最大点、Q 路相位固定为 110^\circ 时，P 路导频二阶项随 I 路偏置呈 \cos(\Phi_I/2) 型变化；若看功率，则呈 \cos^2(\Phi_I/2) 型变化。
}
$$

---

## 21. P 路电压形式

P 路相位与偏置电压的关系为：

$$
\Phi_P=\frac{\pi V_{DCP}}{V_\pi}
$$

所以：

$$
G_{PP}(V_{DCP})
=
M\cos\left(\frac{\pi V_{DCP}}{V_\pi}\right)
+
N\sin\left(\frac{\pi V_{DCP}}{V_\pi}\right)
$$

其中：

$$
M=(1+\Delta)A_0B_0
$$

$$
N=\delta_I B_0a_0-\delta_Q A_0b_0
$$

因此：

$$
\boxed{
P_{2f_P}(V_{DCP})
\propto
\left[
M\cos\left(\frac{\pi V_{DCP}}{V_\pi}\right)
+
N\sin\left(\frac{\pi V_{DCP}}{V_\pi}\right)
\right]^2
}
$$

需要注意周期：

| 观察量 | 关于 $\Phi_P$ 的周期 | 关于 $V_{DCP}$ 的周期 |
|---|---:|---:|
| 带符号系数 $G_{PP}$ | $2\pi$ | $2V_\pi$ |
| 幅度 $|G_{PP}|$ | $\pi$ | $V_\pi$ |
| 功率 $G_{PP}^2$ | $\pi$ | $V_\pi$ |

---

## 22. 与 I-P 交调项的关系

I-P 交调项的核心系数为：

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

理想情况下：

$$
D_{IP}^{id}
=
2Ka_0B_0s_P
$$

因此：

$$
P_{IP}^{id}
\propto
a_0^2B_0^2\sin^2(\Phi_P)
$$

而 P 路二阶项理想情况下：

$$
P_{2f_P}^{id}
\propto
A_0^2B_0^2\cos^2(\Phi_P)
$$

二者对比如下：

| 项目 | 理想系数 | 随 P 路偏压趋势 |
|---|---|---|
| I-P 交调项 | $a_0B_0\sin(\Phi_P)$ | $\sin^2(\Phi_P)$ |
| P 路二阶项 | $A_0B_0\cos(\Phi_P)$ | $\cos^2(\Phi_P)$ |

所以：

$$
\boxed{
理想情况下，I-P 交调项和 P 路二阶项随 P 路偏压的变化趋势相差约 90^\circ。
}
$$

当 P 路位于正交点：

$$
\Phi_P=\frac{\pi}{2}
$$

理想情况下：

$$
I\text{-}P \text{ 交调项较强}
$$

而：

$$
P \text{ 路二阶项较弱}
$$

当 P 路位于最大点：

$$
\Phi_P=0
$$

理想情况下：

$$
I\text{-}P \text{ 交调项较弱}
$$

而：

$$
P \text{ 路二阶项较强}
$$

---

## 23. 物理直觉总结

P 路导频的本质作用是改变 Q 路相对于 I 路的相位：

```text
P 路导频
  -> Q 路光场相对相位发生周期摆动
  -> I/Q 两路相干合束状态发生变化
  -> PD 输出光电流发生变化
```

由于 PD 是平方律探测器，P 路导频引起的光电流变化不仅包含一阶项：

$$
f_P
$$

还包含二阶项：

$$
2f_P
$$

二阶项来自：

$$
\sin^2(\omega_P t)
=
\frac{1}{2}
\left[
1-\cos(2\omega_P t)
\right]
$$

所以 P 路二阶导频一定同时带来：

```text
DC 偏移项 + 2fP 二次谐波项
```

理想情况下，P 路二阶项需要 I/Q 两路都有非零光场参与干涉：

$$
A_0B_0\neq0
$$

如果 I/Q 两路都在最小传输点，输出光场接近零，那么 P 路相位扰动很难转化为明显的光功率变化，因此 P 路二阶项会很弱。

---

## 24. 最终核心公式汇总

### 24.1 P 路二阶导数

$$
\boxed{
D_{PP}
=
-4K
\left[
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
\right]
}
$$

### 24.2 P 路二阶时域项

$$
\boxed{
I_{P,2}(t)
=
\frac{1}{2}m_P^2D_{PP}\sin^2(\omega_P t)
}
$$

也可写成：

$$
\boxed{
I_{P,2}(t)
=
-2Km_P^2
\left[
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
\right]
\sin^2(\omega_P t)
}
$$

### 24.3 P 路二阶 DC 项

$$
\boxed{
I_{P,2}^{DC}
=
-Km_P^2
\left[
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
\right]
}
$$

### 24.4 P 路 $2f_P$ 项

$$
\boxed{
I_{2\omega_P}(t)
=
Km_P^2
\left[
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
\right]
\cos(2\omega_P t)
}
$$

### 24.5 P 路 $2f_P$ 功率趋势

$$
\boxed{
P_{2f_P}
\propto
\left[
(1+\Delta)A_0B_0\cos(\Phi_P)
+
(\delta_I B_0a_0-\delta_Q A_0b_0)\sin(\Phi_P)
\right]^2
}
$$

### 24.6 理想情况下的趋势

$$
\boxed{
P_{2f_P}^{id}
\propto
A_0^2B_0^2\cos^2(\Phi_P)
}
$$

### 24.7 固定 P/Q 后随 I 路变化趋势

$$
\boxed{
P_{2f_P}(\Phi_I)
\propto
\left[
U\cos\left(\frac{\Phi_I}{2}\right)
+
V\sin\left(\frac{\Phi_I}{2}\right)
\right]^2
}
$$

其中：

$$
U=(1+\Delta)B_0c_P-\delta_Q b_0s_P
$$

$$
V=\delta_I B_0s_P
$$

### 24.8 P 最大点、Q 为 $110^\circ$ 时随 I 路变化

$$
\boxed{
P_{2f_P}
\propto
\cos^2\left(\frac{\Phi_I}{2}\right)
}
$$

---

## 25. 结论

P 路导频二阶项来自光电流对 P 路相位的二阶泰勒展开，其核心系数为：

$$
D_{PP}
=
-4K
\left[
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
\right]
$$

P 路二阶项会产生：

1. DC 偏移项；
2. $2f_P$ 二次谐波项。

其中 $2f_P$ 分量为：

$$
I_{2\omega_P}(t)
=
Km_P^2
\left[
(1+\Delta)A_0B_0c_P
+
\delta_I B_0a_0s_P
-
\delta_Q A_0b_0s_P
\right]
\cos(2\omega_P t)
$$

理想情况下，其功率趋势为：

$$
P_{2f_P}^{id}
\propto
A_0^2B_0^2\cos^2(\Phi_P)
$$

因此，P 路导频二阶项随 P 路偏压整体呈余弦平方型变化；考虑有限消光比和 I/Q 非对称性后，会变成带相位偏移的余弦平方型曲线。

该项适合用于辅助观察 P 路偏置状态、I/Q 光场残余和器件非理想耦合，但它本身也强烈依赖 I/Q 两路偏置状态，不能脱离 I/Q 偏置单独解释。