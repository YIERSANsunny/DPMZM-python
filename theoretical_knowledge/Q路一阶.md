# Q 路一阶导频公式推导参考内容

## 1. 推导目标

本文整理 DPMZM 中 **Q 路导频一阶项** 的公式推导。

所谓 Q 路导频一阶项，是指在 Q 路直流偏置上叠加一个小幅低频导频后，PD 输出电流中出现在导频频率：

$$
f_Q
$$

处的分量。

其数学本质是光电流对 Q 路相位 $\varphi_Q$ 的一阶偏导：

$$
D_Q=
\left.
\frac{\partial I}{\partial \varphi_Q}
\right|_{\Phi_I,\Phi_Q,\Phi_P}
$$

最终目标是得到：

$$
I_{\omega_Q}(t)
=
m_QD_Q\sin(\omega_Q t)
$$

其中 $D_Q$ 就是 Q 路一阶导频误差信号的系数。

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

静态偏置点定义为：

$$
\Phi_I,\qquad \Phi_Q,\qquad \Phi_P
$$

并定义：

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

## 3. Q 路导频定义

在 Q 路直流偏置上叠加低频小幅导频：

$$
\varphi_Q(t)
=
\Phi_Q
+
m_Q\sin(\omega_Q t)
$$

其中：

| 符号 | 含义 |
|---|---|
| $\Phi_Q$ | Q 路当前静态偏置相位 |
| $m_Q$ | Q 路导频相位调制深度 |
| $\omega_Q$ | Q 路导频角频率 |

I 路和 P 路暂时固定：

$$
\varphi_I(t)=\Phi_I
$$

$$
\varphi_P(t)=\Phi_P
$$

---

## 4. 泰勒展开形式

光电流 $I$ 对 Q 路相位 $\varphi_Q$ 在静态偏置点附近作一阶泰勒展开：

$$
I(t)
\approx
I(\Phi_I,\Phi_Q,\Phi_P)
+
m_QD_Q\sin(\omega_Q t)
$$

其中：

$$
D_Q=
\left.
\frac{\partial I}{\partial \varphi_Q}
\right|_{\Phi_I,\Phi_Q,\Phi_P}
$$

因此 Q 路一阶导频分量为：

$$
\boxed{
I_{\omega_Q}(t)
=
m_QD_Q\sin(\omega_Q t)
}
$$

---

## 5. DPMZM 理想光电流模型

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

理想光电流为：

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

---

## 6. 理想项对 Q 路一阶导频的贡献

理想光电流为：

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

对 $\varphi_Q$ 求偏导。

常数项和 $\cos(\varphi_I)$ 与 $\varphi_Q$ 无关，所以导数为 0。

对 $\cos(\varphi_Q)$ 求导：

$$
\frac{\partial}{\partial \varphi_Q}
\cos(\varphi_Q)
=
-\sin(\varphi_Q)
$$

对干涉项求导：

$$
\frac{\partial}{\partial \varphi_Q}
\left[
4\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
\right]
$$

由于：

$$
\frac{\partial}{\partial \varphi_Q}
\cos\left(\frac{\varphi_Q}{2}\right)
=
-\frac{1}{2}
\sin\left(\frac{\varphi_Q}{2}\right)
$$

所以：

$$
\frac{\partial}{\partial \varphi_Q}
\left[
4\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
\right]
=
-2
\cos\left(\frac{\varphi_I}{2}\right)
\sin\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
$$

在静态偏置点处：

$$
\boxed{
D_Q^{id}
=
K
\left[
-\sin(\Phi_Q)
-
2A_0b_0c_P
\right]
}
$$

这就是理想情况下 Q 路一阶导频系数。

---

## 7. 一阶非理想光电流模型

考虑有限消光比和幅度不平衡后，一阶非理想光电流可写成：

$$
I_{DPMZM}
=
I_{id}+I_{syn}+I_{asym}+O(\delta_k^2)
$$

其中：

1. $I_{id}$ 为理想项；
2. $I_{syn}$ 为同步变化项；
3. $I_{asym}$ 为非对称扰动项；
4. $O(\delta_k^2)$ 为二阶及以上非理想小量。

下面分别求 $I_{syn}$ 和 $I_{asym}$ 对 Q 路一阶导频的贡献。

---

## 8. 同步变化项对 Q 路一阶导频的贡献

同步变化项为：

$$
I_{syn}
=
K
\left[
2\Delta
+
2(\delta_I+\delta_P)\cos(\varphi_I)
+
2\delta_Q\cos(\varphi_Q)
+
4\Delta
\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
\right]
$$

其中与 $\varphi_Q$ 有关的部分是：

$$
2\delta_Q\cos(\varphi_Q)
$$

以及：

$$
4\Delta
\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
$$

对第一项求导：

$$
\frac{\partial}{\partial\varphi_Q}
\left[
2\delta_Q\cos(\varphi_Q)
\right]
=
-2\delta_Q\sin(\varphi_Q)
$$

对第二项求导：

$$
\frac{\partial}{\partial\varphi_Q}
\left[
4\Delta
\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
\right]
$$

$$
=
-2\Delta
\cos\left(\frac{\varphi_I}{2}\right)
\sin\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
$$

在静态偏置点处：

$$
\boxed{
D_Q^{syn}
=
K
\left[
-2\delta_Q\sin(\Phi_Q)
-
2\Delta A_0b_0c_P
\right]
}
$$

---

## 9. 非对称扰动项对 Q 路一阶导频的贡献

非对称扰动项为：

$$
I_{asym}
=
K
\left[
4\delta_I
\cos\left(\frac{\varphi_Q}{2}\right)
\sin\left(\frac{\varphi_I}{2}\right)
\sin(\varphi_P)
-
4\delta_Q
\cos\left(\frac{\varphi_I}{2}\right)
\sin\left(\frac{\varphi_Q}{2}\right)
\sin(\varphi_P)
\right]
$$

先对第一项求导：

$$
\frac{\partial}{\partial\varphi_Q}
\left[
4\delta_I
\cos\left(\frac{\varphi_Q}{2}\right)
\sin\left(\frac{\varphi_I}{2}\right)
\sin(\varphi_P)
\right]
$$

由于：

$$
\frac{\partial}{\partial\varphi_Q}
\cos\left(\frac{\varphi_Q}{2}\right)
=
-\frac{1}{2}
\sin\left(\frac{\varphi_Q}{2}\right)
$$

所以：

$$
=
-2\delta_I
\sin\left(\frac{\varphi_I}{2}\right)
\sin\left(\frac{\varphi_Q}{2}\right)
\sin(\varphi_P)
$$

在静态偏置点处为：

$$
-2\delta_Ia_0b_0s_P
$$

再对第二项求导：

$$
\frac{\partial}{\partial\varphi_Q}
\left[
-4\delta_Q
\cos\left(\frac{\varphi_I}{2}\right)
\sin\left(\frac{\varphi_Q}{2}\right)
\sin(\varphi_P)
\right]
$$

由于：

$$
\frac{\partial}{\partial\varphi_Q}
\sin\left(\frac{\varphi_Q}{2}\right)
=
\frac{1}{2}
\cos\left(\frac{\varphi_Q}{2}\right)
$$

所以：

$$
=
-2\delta_Q
\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\sin(\varphi_P)
$$

在静态偏置点处为：

$$
-2\delta_QA_0B_0s_P
$$

因此：

$$
\boxed{
D_Q^{asym}
=
K
\left[
-2\delta_Ia_0b_0s_P
-
2\delta_QA_0B_0s_P
\right]
}
$$

---

## 10. Q 路一阶导频完整公式

将三部分相加：

$$
D_Q
=
D_Q^{id}
+
D_Q^{syn}
+
D_Q^{asym}
$$

其中：

$$
D_Q^{id}
=
K
\left[
-\sin(\Phi_Q)
-
2A_0b_0c_P
\right]
$$

$$
D_Q^{syn}
=
K
\left[
-2\delta_Q\sin(\Phi_Q)
-
2\Delta A_0b_0c_P
\right]
$$

$$
D_Q^{asym}
=
K
\left[
-2\delta_Ia_0b_0s_P
-
2\delta_QA_0B_0s_P
\right]
$$

因此：

$$
\boxed{
D_Q
=
K
\left[
-\sin(\Phi_Q)
-
2A_0b_0c_P
-
2\delta_Q\sin(\Phi_Q)
-
2\Delta A_0b_0c_P
-
2\delta_Ia_0b_0s_P
-
2\delta_QA_0B_0s_P
\right]
}
$$

合并同类项：

$$
\boxed{
D_Q
=
K
\left[
-(1+2\delta_Q)\sin(\Phi_Q)
-
2(1+\Delta)A_0b_0c_P
-
2\delta_Ia_0b_0s_P
-
2\delta_QA_0B_0s_P
\right]
}
$$

所以 Q 路一阶导频分量为：

$$
\boxed{
I_{\omega_Q}(t)
=
m_QD_Q\sin(\omega_Q t)
}
$$

即：

$$
\boxed{
I_{\omega_Q}(t)
=
m_QK
\left[
-(1+2\delta_Q)\sin(\Phi_Q)
-
2(1+\Delta)A_0b_0c_P
-
2\delta_Ia_0b_0s_P
-
2\delta_QA_0B_0s_P
\right]
\sin(\omega_Q t)
}
$$

---

## 11. 理想情况下的 Q 路一阶公式

令：

$$
\delta_I=\delta_Q=\delta_P=0
$$

则：

$$
\Delta=0
$$

完整公式退化为：

$$
\boxed{
D_Q^{id}
=
K
\left[
-\sin(\Phi_Q)
-
2A_0b_0c_P
\right]
}
$$

即：

$$
\boxed{
D_Q^{id}
=
K
\left[
-\sin(\Phi_Q)
-
2\cos\left(\frac{\Phi_I}{2}\right)
\sin\left(\frac{\Phi_Q}{2}\right)
\cos(\Phi_P)
\right]
}
$$

Q 路一阶导频分量为：

$$
\boxed{
I_{\omega_Q}^{id}(t)
=
m_QK
\left[
-\sin(\Phi_Q)
-
2A_0b_0c_P
\right]
\sin(\omega_Q t)
}
$$

---

## 12. Q 路一阶项随 Q 路偏置的变化趋势

完整一阶非理想公式为：

$$
D_Q
=
K
\left[
-(1+2\delta_Q)\sin(\Phi_Q)
-
2(1+\Delta)A_0b_0c_P
-
2\delta_Ia_0b_0s_P
-
2\delta_QA_0B_0s_P
\right]
$$

其中：

$$
B_0=\cos\left(\frac{\Phi_Q}{2}\right)
$$

$$
b_0=\sin\left(\frac{\Phi_Q}{2}\right)
$$

将其完全写成关于 $\Phi_Q$ 的函数：

$$
\boxed{
D_Q(\Phi_Q)
=
K
\left[
-(1+2\delta_Q)\sin(\Phi_Q)
-
2(1+\Delta)A_0c_P\sin\left(\frac{\Phi_Q}{2}\right)
-
2\delta_Ia_0s_P\sin\left(\frac{\Phi_Q}{2}\right)
-
2\delta_QA_0s_P\cos\left(\frac{\Phi_Q}{2}\right)
\right]
}
$$

利用：

$$
\sin(\Phi_Q)
=
2\sin\left(\frac{\Phi_Q}{2}\right)
\cos\left(\frac{\Phi_Q}{2}\right)
$$

可以写成：

$$
D_Q(\Phi_Q)
=
-2K
\left[
\alpha
\sin\left(\frac{\Phi_Q}{2}\right)
\cos\left(\frac{\Phi_Q}{2}\right)
+
\beta
\sin\left(\frac{\Phi_Q}{2}\right)
+
\gamma
\cos\left(\frac{\Phi_Q}{2}\right)
\right]
$$

其中：

$$
\alpha=1+2\delta_Q
$$

$$
\beta=(1+\Delta)A_0c_P+\delta_Ia_0s_P
$$

$$
\gamma=\delta_QA_0s_P
$$

因此：

$$
\boxed{
D_Q(\Phi_Q)
=
-2K
\left[
\alpha
\sin\left(\frac{\Phi_Q}{2}\right)
\cos\left(\frac{\Phi_Q}{2}\right)
+
\beta
\sin\left(\frac{\Phi_Q}{2}\right)
+
\gamma
\cos\left(\frac{\Phi_Q}{2}\right)
\right]
}
$$

这说明 Q 路一阶导频项通常不是单纯的 $-\sin(\Phi_Q)$，而是会受到 I 路偏置、P 路偏置和非理想项共同影响。

---

## 13. 理想情况下的变化趋势

理想情况下：

$$
\delta_I=\delta_Q=\delta_P=0
$$

所以：

$$
\Delta=0
$$

此时：

$$
D_Q^{id}
=
K
\left[
-\sin(\Phi_Q)
-
2A_0c_P\sin\left(\frac{\Phi_Q}{2}\right)
\right]
$$

利用：

$$
\sin(\Phi_Q)
=
2\sin\left(\frac{\Phi_Q}{2}\right)
\cos\left(\frac{\Phi_Q}{2}\right)
$$

可得：

$$
D_Q^{id}
=
-2K
\sin\left(\frac{\Phi_Q}{2}\right)
\left[
\cos\left(\frac{\Phi_Q}{2}\right)
+
A_0c_P
\right]
$$

即：

$$
\boxed{
D_Q^{id}(\Phi_Q)
=
-2K
\sin\left(\frac{\Phi_Q}{2}\right)
\left[
\cos\left(\frac{\Phi_Q}{2}\right)
+
A_0\cos(\Phi_P)
\right]
}
$$

这表明，理想情况下 Q 路一阶导频趋势由两部分决定：

1. Q 路自身的 MZM 传输斜率；
2. I/Q 两路经 P 路相位合成后的相干干涉项。

---

## 14. 最常用近似：I 路在最小传输点附近

如果 I 路在最小传输点附近：

$$
\Phi_I\approx\pi
$$

则：

$$
A_0=\cos\left(\frac{\Phi_I}{2}\right)\approx0
$$

$$
a_0=\sin\left(\frac{\Phi_I}{2}\right)\approx1
$$

如果进一步忽略非理想项：

$$
\delta_I,\delta_Q,\delta_P\approx0
$$

则：

$$
D_Q^{id}
=
K
\left[
-\sin(\Phi_Q)
-
2A_0b_0c_P
\right]
\approx
-K\sin(\Phi_Q)
$$

所以：

$$
\boxed{
D_Q^{id}(\Phi_Q)
\approx
-K\sin(\Phi_Q)
}
$$

Q 路一阶导频幅度趋势为：

$$
\boxed{
|I_{\omega_Q}|
\propto
|\sin(\Phi_Q)|
}
$$

Q 路一阶导频功率趋势为：

$$
\boxed{
P_{f_Q}
\propto
\sin^2(\Phi_Q)
}
$$

---

## 15. Q 路一阶导频的典型趋势

在常用近似：

$$
D_Q\approx-K\sin(\Phi_Q)
$$

下，有：

| Q 路相位 $\Phi_Q$ | $\sin(\Phi_Q)$ | $D_Q$ | 一阶导频幅度 | 一阶导频功率 |
|---|---:|---:|---:|---:|
| $0^\circ$ | 0 | 0 | 最小 | 最小 |
| $90^\circ$ | 1 | $-K$ | 最大 | 最大 |
| $180^\circ$ | 0 | 0 | 最小 | 最小 |
| $270^\circ$ | -1 | $+K$ | 最大 | 最大 |
| $360^\circ$ | 0 | 0 | 最小 | 最小 |

因此：

$$
\boxed{
Q 路一阶导频在最大传输点和最小传输点处都会为零。
}
$$

也就是说：

$$
\Phi_Q=0^\circ
$$

和：

$$
\Phi_Q=180^\circ
$$

处都可能出现一阶导频零点。

---

## 16. 为什么一阶导频无法区分最大点和最小点

单个理想 MZM 的功率传输函数为：

$$
P_Q
\propto
\cos^2\left(\frac{\Phi_Q}{2}\right)
$$

它对 $\Phi_Q$ 的导数为：

$$
\frac{dP_Q}{d\Phi_Q}
\propto
-\sin(\Phi_Q)
$$

Q 路一阶导频本质上就是在测量当前偏置点附近的传输曲线斜率。

因此：

- 最大传输点处，曲线斜率为 0；
- 最小传输点处，曲线斜率也为 0。

所以仅靠一阶导频零点无法区分：

$$
\Phi_Q=0
$$

和：

$$
\Phi_Q=\pi
$$

即无法区分：

```text
最大传输点 MATP
最小传输点 MITP
```

因此需要结合：

1. PD 直流光功率；
2. Q 路二阶导频；
3. 扫描过程中的功率谷值；
4. 其他辅助判据。

---

## 17. I/P 偏置对 Q 路一阶零点的影响

理想情况下：

$$
D_Q^{id}(\Phi_Q)
=
-2K
\sin\left(\frac{\Phi_Q}{2}\right)
\left[
\cos\left(\frac{\Phi_Q}{2}\right)
+
A_0c_P
\right]
$$

令：

$$
D_Q^{id}=0
$$

得到两个条件：

### 17.1 第一类零点

$$
\sin\left(\frac{\Phi_Q}{2}\right)=0
$$

所以：

$$
\frac{\Phi_Q}{2}=n\pi
$$

即：

$$
\boxed{
\Phi_Q=2n\pi
}
$$

这对应 Q 路最大传输点。

### 17.2 第二类零点

$$
\cos\left(\frac{\Phi_Q}{2}\right)+A_0c_P=0
$$

即：

$$
\boxed{
\cos\left(\frac{\Phi_Q}{2}\right)
=
-A_0\cos(\Phi_P)
}
$$

如果：

$$
A_0c_P=0
$$

则：

$$
\cos\left(\frac{\Phi_Q}{2}\right)=0
$$

得到：

$$
\Phi_Q=\pi
$$

即 Q 路最小传输点。

但如果：

$$
A_0c_P\neq0
$$

则零点会偏离：

$$
\Phi_Q=\pi
$$

也就是说：

$$
\boxed{
Q 路一阶导频零点会被 I 路偏置和 P 路偏置牵引。
}
$$

---

## 18. P 路正交点附近的简化

如果 P 路位于正交点附近：

$$
\Phi_P\approx\frac{\pi}{2}
$$

则：

$$
c_P=\cos(\Phi_P)\approx0
$$

$$
s_P=\sin(\Phi_P)\approx1
$$

完整公式：

$$
D_Q
=
K
\left[
-(1+2\delta_Q)\sin(\Phi_Q)
-
2(1+\Delta)A_0b_0c_P
-
2\delta_Ia_0b_0s_P
-
2\delta_QA_0B_0s_P
\right]
$$

近似为：

$$
D_Q
\approx
K
\left[
-(1+2\delta_Q)\sin(\Phi_Q)
-
2\delta_Ia_0b_0
-
2\delta_QA_0B_0
\right]
$$

若非理想项很小，则：

$$
\boxed{
D_Q\approx-K\sin(\Phi_Q)
}
$$

因此在 P 正交点附近，Q 路一阶导频主要恢复为 Q 路自身的斜率信号。

---

## 19. I 路最小点附近的简化

如果 I 路位于最小点附近：

$$
\Phi_I\approx\pi
$$

则：

$$
A_0\approx0
$$

$$
a_0\approx1
$$

完整公式：

$$
D_Q
=
K
\left[
-(1+2\delta_Q)\sin(\Phi_Q)
-
2(1+\Delta)A_0b_0c_P
-
2\delta_Ia_0b_0s_P
-
2\delta_QA_0B_0s_P
\right]
$$

近似为：

$$
\boxed{
D_Q
\approx
K
\left[
-(1+2\delta_Q)\sin(\Phi_Q)
-
2\delta_Ib_0s_P
\right]
}
$$

如果进一步忽略 I 路非理想项 $\delta_I$，则：

$$
\boxed{
D_Q
\approx
-K\sin(\Phi_Q)
}
$$

---

## 20. Q 路最小点附近的局部近似

令 Q 路接近最小传输点：

$$
\Phi_Q=\pi+\epsilon_Q
$$

其中 $\epsilon_Q$ 为小偏移量。

有：

$$
\sin(\Phi_Q)
=
\sin(\pi+\epsilon_Q)
\approx
-\epsilon_Q
$$

$$
b_0=
\sin\left(\frac{\Phi_Q}{2}\right)
=
\sin\left(\frac{\pi+\epsilon_Q}{2}\right)
=
\sin\left(\frac{\pi}{2}+\frac{\epsilon_Q}{2}\right)
\approx
1
$$

$$
B_0=
\cos\left(\frac{\Phi_Q}{2}\right)
=
\cos\left(\frac{\pi}{2}+\frac{\epsilon_Q}{2}\right)
\approx
-\frac{\epsilon_Q}{2}
$$

代入完整公式：

$$
D_Q
=
K
\left[
-(1+2\delta_Q)\sin(\Phi_Q)
-
2(1+\Delta)A_0b_0c_P
-
2\delta_Ia_0b_0s_P
-
2\delta_QA_0B_0s_P
\right]
$$

得到近似：

$$
D_Q
\approx
K
\left[
(1+2\delta_Q)\epsilon_Q
-
2(1+\Delta)A_0c_P
-
2\delta_Ia_0s_P
+
\delta_QA_0\epsilon_Qs_P
\right]
$$

如果 I 路在最小点且非理想很小，则：

$$
A_0\approx0,\qquad a_0\approx1,\qquad \delta_I\approx0
$$

于是：

$$
\boxed{
D_Q
\approx
K\epsilon_Q
}
$$

这说明在 Q 路最小点附近，一阶导频系数近似与偏离量 $\epsilon_Q$ 成正比。

---

## 21. Q 路最大点附近的局部近似

令 Q 路接近最大传输点：

$$
\Phi_Q=0+\epsilon_Q
$$

其中 $\epsilon_Q$ 为小偏移量。

有：

$$
\sin(\Phi_Q)\approx\epsilon_Q
$$

$$
b_0=
\sin\left(\frac{\Phi_Q}{2}\right)
\approx
\frac{\epsilon_Q}{2}
$$

$$
B_0=
\cos\left(\frac{\Phi_Q}{2}\right)
\approx
1
$$

代入完整公式：

$$
D_Q
\approx
K
\left[
-(1+2\delta_Q)\epsilon_Q
-
(1+\Delta)A_0c_P\epsilon_Q
-
\delta_Ia_0s_P\epsilon_Q
-
2\delta_QA_0s_P
\right]
$$

如果非理想项很小，则：

$$
\boxed{
D_Q\approx-K\epsilon_Q
}
$$

这说明在 Q 路最大点附近，一阶导频系数也与偏离量成正比，但斜率方向与最小点附近相反。

---

## 22. Q 路一阶导频的物理直觉

Q 路一阶导频本质上是在测量 Q 路偏置点附近的传输曲线斜率：

```text
Q 路导频
  -> Q 路相位产生小幅摆动
  -> Q 路输出光场幅度发生小幅变化
  -> I/Q 两路相干合束后的总光功率发生变化
  -> PD 输出中出现 fQ 分量
```

如果 Q 路处在最大点或最小点：

```text
传输曲线局部斜率为 0
  -> 小幅导频引起的一阶变化接近 0
  -> fQ 分量接近 0
```

如果 Q 路处在正交点附近：

```text
传输曲线局部斜率最大
  -> 小幅导频引起的一阶变化最大
  -> fQ 分量最大
```

因此：

$$
\boxed{
Q 路一阶导频信号更像是“斜率信号”，而不是直接的“功率大小信号”。
}
$$

---

## 23. Q 路一阶导频用于偏置控制时的注意事项

### 23.1 一阶零点不等于最小点

因为：

$$
D_Q\approx-K\sin(\Phi_Q)
$$

所以：

$$
D_Q=0
$$

时有：

$$
\Phi_Q=0,\pi,2\pi,\cdots
$$

既包括最大传输点，也包括最小传输点。

因此：

$$
\boxed{
不能只靠 Q 路一阶导频零点判断 Q 路已经到达最小传输点。
}
$$

---

### 23.2 需要结合 PD 直流功率

最大传输点和最小传输点的区别是：

| 工作点 | 相位 | 光功率 |
|---|---:|---:|
| 最大传输点 | $\Phi_Q=0$ | 高 |
| 最小传输点 | $\Phi_Q=\pi$ | 低 |

因此实际控制中可以结合 PD 直流光功率判断：

```text
一阶导频接近零 + PD 光功率较高
        -> 可能是最大传输点

一阶导频接近零 + PD 光功率较低
        -> 可能是最小传输点
```

---

### 23.3 可结合 Q 路二阶导频

由于一阶导频在最大点和最小点都为零，可以引入二阶导频辅助判断。

一般来说，二阶项反映曲率信息：

```text
最大点附近：曲率为负
最小点附近：曲率为正
```

因此二阶导频可以帮助区分最大传输点和最小传输点。

---

### 23.4 I/P 偏置不准会牵引 Q 路零点

理想情况下：

$$
D_Q^{id}
=
-2K
\sin\left(\frac{\Phi_Q}{2}\right)
\left[
\cos\left(\frac{\Phi_Q}{2}\right)
+
A_0c_P
\right]
$$

如果：

$$
A_0c_P\neq0
$$

则 Q 路最小点附近的一阶零点会偏移，满足：

$$
\cos\left(\frac{\Phi_Q}{2}\right)
=
-A_0c_P
$$

因此：

$$
\boxed{
当 I 路不在最小点，或者 P 路不在正交点时，Q 路一阶导频零点可能不再准确对应 Q 路最小传输点。
}
$$

---

## 24. 最终核心公式汇总

### 24.1 Q 路一阶导频项

$$
\boxed{
I_{\omega_Q}(t)
=
m_QD_Q\sin(\omega_Q t)
}
$$

### 24.2 Q 路一阶导频完整系数

$$
\boxed{
D_Q
=
K
\left[
-\sin(\Phi_Q)
-
2A_0b_0c_P
-
2\delta_Q\sin(\Phi_Q)
-
2\Delta A_0b_0c_P
-
2\delta_Ia_0b_0s_P
-
2\delta_QA_0B_0s_P
\right]
}
$$

### 24.3 合并后的 Q 路一阶导频系数

$$
\boxed{
D_Q
=
K
\left[
-(1+2\delta_Q)\sin(\Phi_Q)
-
2(1+\Delta)A_0b_0c_P
-
2\delta_Ia_0b_0s_P
-
2\delta_QA_0B_0s_P
\right]
}
$$

### 24.4 理想情况下的 Q 路一阶系数

$$
\boxed{
D_Q^{id}
=
K
\left[
-\sin(\Phi_Q)
-
2A_0b_0\cos(\Phi_P)
\right]
}
$$

### 24.5 理想情况下写成半角形式

$$
\boxed{
D_Q^{id}(\Phi_Q)
=
-2K
\sin\left(\frac{\Phi_Q}{2}\right)
\left[
\cos\left(\frac{\Phi_Q}{2}\right)
+
A_0\cos(\Phi_P)
\right]
}
$$

### 24.6 I 路在最小点附近的近似

若：

$$
\Phi_I\approx\pi
$$

则：

$$
A_0\approx0
$$

忽略非理想项后：

$$
\boxed{
D_Q\approx-K\sin(\Phi_Q)
}
$$

### 24.7 Q 路一阶导频功率趋势

在常用近似下：

$$
\boxed{
P_{f_Q}
\propto
\sin^2(\Phi_Q)
}
$$

---

## 25. 结论

Q 路一阶导频项来自光电流对 Q 路相位的一阶偏导，其完整一阶非理想表达式为：

$$
D_Q
=
K
\left[
-(1+2\delta_Q)\sin(\Phi_Q)
-
2(1+\Delta)A_0b_0c_P
-
2\delta_Ia_0b_0s_P
-
2\delta_QA_0B_0s_P
\right]
$$

对应的导频分量为：

$$
I_{\omega_Q}(t)=m_QD_Q\sin(\omega_Q t)
$$

理想情况下：

$$
D_Q^{id}
=
K
\left[
-\sin(\Phi_Q)
-
2A_0b_0\cos(\Phi_P)
\right]
$$

如果 I 路位于最小传输点附近，且非理想项较小，则进一步退化为：

$$
D_Q\approx-K\sin(\Phi_Q)
$$

因此 Q 路一阶导频功率随 Q 路偏置的趋势为：

$$
P_{f_Q}\propto \sin^2(\Phi_Q)
$$

这意味着 Q 路一阶导频在最大传输点和最小传输点都会出现零点，不能单独用于区分最大点和最小点。实际偏置控制中，需要结合 PD 直流功率、二阶导频项或其他辅助判据共同判断 Q 路是否真正到达最小传输点。