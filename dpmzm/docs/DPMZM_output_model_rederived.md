# DPMZM 输出模型与非理想模型重新推导

> 说明：本文档重新推导 DPMZM 理想输出模型、归一化传输函数、CS-SSB 调制过程、非理想输出模型以及导频误差信号关系。推导中统一采用复光场模型，并保留到非理想因子的一阶小量。

---

## 1. 符号定义

输入光场定义为：

$$
E_{in}(t)=E_m e^{j\omega_c t}
$$

其中，$E_m$ 为输入光场幅度，$\omega_c$ 为光载波角频率。

DPMZM 由 I 路子 MZM、Q 路子 MZM 和父级 MZM 构成。定义三个相位量为：

$$
\varphi_I=\frac{\pi\left(V_{RFI}+V_{DCI}\right)}{V_\pi}
$$

$$
\varphi_Q=\frac{\pi\left(V_{RFQ}+V_{DCQ}\right)}{V_\pi}
$$

$$
\varphi_P=\frac{\pi V_{DCP}}{V_\pi}
$$

其中，$V_\pi$ 为半波电压。$\varphi_I$ 和 $\varphi_Q$ 分别表示 I 路、Q 路子 MZM 引入的等效相位差，$\varphi_P$ 表示父级 MZM 引入的相对相位。

为简化后续表达，定义：

$$
A=\cos\left(\frac{\varphi_I}{2}\right),\qquad
B=\cos\left(\frac{\varphi_Q}{2}\right)
$$

---

## 2. 理想 DPMZM 输出模型

### 2.1 单个 MZM 的理想传输关系

对于理想推挽型 MZM，其上下两臂引入的相位分别为 $+\varphi/2$ 和 $-\varphi/2$。忽略器件损耗时，单个 MZM 的输出光场为：

$$
E_{MZM}=\frac{E_{in}}{2}\left[\exp\left(j\frac{\varphi}{2}\right)+\exp\left(-j\frac{\varphi}{2}\right)\right]
$$

由欧拉公式可得：

$$
E_{MZM}=E_{in}\cos\left(\frac{\varphi}{2}\right)
$$

因此，MZM 的输出光场幅度由 $\cos(\varphi/2)$ 控制。

---

### 2.2 DPMZM 理想输出光场

DPMZM 中，I 路和 Q 路子 MZM 的输出光场在父级 MZM 处合成。若父级 MZM 对 Q 路引入相对相位 $\varphi_P$，则 DPMZM 的理想输出光场可以写为：

$$
E_{out}(t)=\frac{E_{in}(t)}{2}
\left[
\cos\left(\frac{\varphi_I}{2}\right)
+
\cos\left(\frac{\varphi_Q}{2}\right)\exp(j\varphi_P)
\right]
$$

即：

$$
E_{out}(t)=\frac{E_{in}(t)}{2}\left[A+B\exp(j\varphi_P)\right]
$$

---

### 2.3 归一化传输函数

归一化传输函数定义为：

$$
T=\frac{E_{out}(t)E_{out}^{*}(t)}{E_{in}(t)E_{in}^{*}(t)}
$$

代入理想输出光场表达式：

$$
T=\frac{1}{4}\left[A+B\exp(j\varphi_P)\right]
\left[A+B\exp(-j\varphi_P)\right]
$$

展开得：

$$
T=\frac{1}{4}\left[A^2+B^2+2AB\cos(\varphi_P)\right]
$$

又因为：

$$
A^2=\cos^2\left(\frac{\varphi_I}{2}\right)=\frac{1+\cos(\varphi_I)}{2}
$$

$$
B^2=\cos^2\left(\frac{\varphi_Q}{2}\right)=\frac{1+\cos(\varphi_Q)}{2}
$$

所以：

$$
T=\frac{1}{8}\left[
2+
\cos(\varphi_I)+
\cos(\varphi_Q)+
4\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
\right]
$$

该式是 DPMZM 理想归一化传输函数。

需要注意，最后一项必须是半角形式：

$$
4\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
$$

不能写成：

$$
4\cos(\varphi_I)\cos(\varphi_Q)\cos(\varphi_P)
$$

---

## 3. CS-SSB 调制推导

载波抑制单边带调制，即 CS-SSB，要求 I 路和 Q 路子 MZM 工作在最小传输点附近，父级 MZM 工作在正交点附近。

令 I 路和 Q 路子 MZM 的直流偏置均位于最小传输点：

$$
\varphi_{I0}=\pi,\qquad \varphi_{Q0}=\pi
$$

父级 MZM 位于正交点：

$$
\varphi_P=\frac{\pi}{2}
$$

在 I 路和 Q 路分别加载幅度相同、频率相同、相位相差 $\pi/2$ 的射频信号：

$$
\varphi_I(t)=\pi+m\sin(\omega_{RF}t)
$$

$$
\varphi_Q(t)=\pi+m\cos(\omega_{RF}t)
$$

其中，$m$ 为相位调制深度。在小信号条件下，有：

$$
\cos\left[\frac{\pi+m\sin(\omega_{RF}t)}{2}\right]
= -\sin\left[\frac{m\sin(\omega_{RF}t)}{2}\right]
\approx -\frac{m}{2}\sin(\omega_{RF}t)
$$

$$
\cos\left[\frac{\pi+m\cos(\omega_{RF}t)}{2}\right]
= -\sin\left[\frac{m\cos(\omega_{RF}t)}{2}\right]
\approx -\frac{m}{2}\cos(\omega_{RF}t)
$$

定义：

$$
\alpha=\frac{m}{2}
$$

则：

$$
\cos\left(\frac{\varphi_I(t)}{2}\right)\approx -\alpha\sin(\omega_{RF}t)
$$

$$
\cos\left(\frac{\varphi_Q(t)}{2}\right)\approx -\alpha\cos(\omega_{RF}t)
$$

代入 DPMZM 理想输出光场：

$$
E_{out}(t)
=\frac{E_m e^{j\omega_c t}}{2}
\left[-\alpha\sin(\omega_{RF}t)
-\alpha\cos(\omega_{RF}t)\exp\left(j\frac{\pi}{2}\right)
\right]
$$

因为 $\exp(j\pi/2)=j$，所以：

$$
E_{out}(t)
=-\frac{\alpha E_m e^{j\omega_c t}}{2}
\left[\sin(\omega_{RF}t)+j\cos(\omega_{RF}t)\right]
$$

又因为：

$$
\sin x+j\cos x=j\exp(-jx)
$$

所以：

$$
E_{out}(t)
=-\frac{j\alpha E_m}{2}
\exp\left[j(\omega_c-\omega_{RF})t\right]
$$

由此可知，在该相位定义下，输出光场只保留 $\omega_c-\omega_{RF}$ 处的一阶边带，载波项和另一侧边带被抑制，因此实现了载波抑制单边带调制。

如果父级相位取 $-\pi/2$，或者 I/Q 射频相位关系反向，则保留的边带会从 $\omega_c-\omega_{RF}$ 切换为 $\omega_c+\omega_{RF}$。

---

## 4. 非理想 DPMZM 输出模型

### 4.1 非理想因素说明

理想模型假设 DPMZM 内部完全对称，实际器件中通常存在以下非理想因素：

1. 有限消光比；
2. 分光比不均衡；
3. I/Q 两路损耗不一致；
4. 父级 MZM 合成相位存在偏差；
5. 光电探测器和后级采样电路存在噪声。

为了描述有限消光比和幅度不平衡的影响，引入非理想因子 $\delta_I$、$\delta_Q$ 和 $\delta_P$。

---

### 4.2 单个子 MZM 的有限消光比模型

对于 I 路或 Q 路子 MZM，可用如下形式描述有限消光比：

$$
H_k(\varphi_k)=\cos\left(\frac{\varphi_k}{2}\right)+\delta_k\exp\left(j\frac{\varphi_k}{2}\right),\qquad k\in\{I,Q\}
$$

其中，$\delta_k$ 为小量。当 $\delta_k=0$ 时，退化为理想 MZM。

当 $\varphi_k=0$ 时，MZM 位于最大传输点：

$$
|H_k(0)|^2=(1+\delta_k)^2
$$

当 $\varphi_k=\pi$ 时，MZM 位于最小传输点：

$$
|H_k(\pi)|^2=\delta_k^2
$$

因此，消光比可写为：

$$
ER_k=\frac{|H_k(0)|^2}{|H_k(\pi)|^2}
=\left(\frac{1+\delta_k}{\delta_k}\right)^2
$$

若 $ER_k$ 使用线性值表示，则：

$$
\delta_k=\frac{1}{\sqrt{ER_k}-1}
$$

当 $ER_k$ 越大时，$\delta_k$ 越小，器件越接近理想状态。

---

### 4.3 DPMZM 非理想输出光场

令：

$$
H_I=\cos\left(\frac{\varphi_I}{2}\right)+\delta_I\exp\left(j\frac{\varphi_I}{2}\right)
$$

$$
H_Q=\cos\left(\frac{\varphi_Q}{2}\right)+\delta_Q\exp\left(j\frac{\varphi_Q}{2}\right)
$$

为了描述父级合成结构中的幅度不平衡，对 I 路引入一阶幅度因子 $1+\delta_P$。此时 DPMZM 的非理想输出光场写为：

$$
E_{out}(t)=\frac{E_m(t)}{2}
\left\{
(1+\delta_P)
\left[
\cos\left(\frac{\varphi_I}{2}\right)
+\delta_I\exp\left(j\frac{\varphi_I}{2}\right)
\right]
+
\left[
\cos\left(\frac{\varphi_Q}{2}\right)
+\delta_Q\exp\left(j\frac{\varphi_Q}{2}\right)
\right]
\exp(j\varphi_P)
\right\}
$$

注意，Q 路括号外必须保留 $\exp(j\varphi_P)$，否则后续输出光功率中不会出现与父级相位 $\varphi_P$ 相关的干涉项，模型将不完整。

---

## 5. 非理想模型的一阶展开

### 5.1 光电流表达式

光电探测器输出电流为：

$$
I_{DPMZM}=\eta E_{out}(t)E_{out}^{*}(t)
$$

令：

$$
P_m=|E_m|^2
$$

则：

$$
I_{DPMZM}=\frac{\eta P_m}{4}|F|^2
$$

其中：

$$
F=(1+\delta_P)
\left[A+\delta_I\exp\left(j\frac{\varphi_I}{2}\right)\right]
+
\left[B+\delta_Q\exp\left(j\frac{\varphi_Q}{2}\right)\right]
\exp(j\varphi_P)
$$

由于 $\delta_I$、$\delta_Q$、$\delta_P$ 均为小量，忽略二阶及以上小量，可写为：

$$
F=F_0+F_1+O(\delta_k^2)
$$

其中：

$$
F_0=A+B\exp(j\varphi_P)
$$

$$
F_1=\delta_P A+
\delta_I\exp\left(j\frac{\varphi_I}{2}\right)+
\delta_Q\exp\left(j\frac{\varphi_Q}{2}+j\varphi_P\right)
$$

因此：

$$
|F|^2=|F_0|^2+2\operatorname{Re}\left(F_0^{*}F_1\right)+O(\delta_k^2)
$$

于是，光电流可分解为：

$$
I_{DPMZM}=I_{id}+I_{syn}+I_{asym}+O(\delta_k^2)
$$

其中，$I_{id}$ 为理想项，$I_{syn}$ 为与理想输出趋势相同的同步变化项，$I_{asym}$ 为由 I/Q 非对称性引入的非对称扰动项。

这里不建议再额外写 $I_{o2}+O(\delta_k^2)$，因为 $I_{o2}$ 本身就是二阶及以上小量。若使用 $I_{o2}$，应写为：

$$
I_{DPMZM}=I_{id}+I_{syn}+I_{asym}+I_{o2},\qquad I_{o2}=O(\delta_k^2)
$$

---

### 5.2 理想项

由 $|F_0|^2$ 可得：

$$
I_{id}=\frac{\eta P_m}{8}
\left[
2+
\cos(\varphi_I)+
\cos(\varphi_Q)+
4\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
\right]
$$

---

### 5.3 同步变化项

保留与理想传输函数形式相同的非理想一阶项，可得：

$$
I_{syn}=\frac{\eta P_m}{8}
\left[
2(\delta_I+\delta_Q+\delta_P)
+2(\delta_I+\delta_P)\cos(\varphi_I)
+2\delta_Q\cos(\varphi_Q)
+4(\delta_I+\delta_Q+\delta_P)
\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
\right]
$$

---

### 5.4 非对称扰动项

非对称扰动项为：

$$
I_{asym}=\frac{\eta P_m}{8}
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

该项说明：当 I/Q 两个子 MZM 的非理想程度不一致时，父级相位 $\varphi_P$ 会通过 $\sin(\varphi_P)$ 项影响输出光电流，使实际误差信号出现偏移。

---

## 6. 导频误差信号推导

### 6.1 小信号导频相位定义

在自动偏压控制中，可以在 I、Q 或 P 的直流偏置上叠加低频小幅导频。定义：

$$
\varphi_I(t)=\Phi_I+m_I\sin(\omega_I t)
$$

$$
\varphi_Q(t)=\Phi_Q+m_Q\sin(\omega_Q t)
$$

$$
\varphi_P(t)=\Phi_P+m_P\sin(\omega_P t)
$$

其中，$\Phi_I$、$\Phi_Q$、$\Phi_P$ 为当前直流偏置对应的静态相位；$m_I$、$m_Q$、$m_P$ 为导频相位调制深度。

当导频幅度较小时，光电流可以对相位作泰勒展开：

$$
I(t)\approx I(\Phi_I,\Phi_Q,\Phi_P)
+m_I D_I\sin(\omega_I t)
+m_Q D_Q\sin(\omega_Q t)
+m_P D_P\sin(\omega_P t)
+m_I m_Q D_{IQ}\sin(\omega_I t)\sin(\omega_Q t)
$$

其中：

$$
D_I=\left.\frac{\partial I}{\partial \varphi_I}\right|_{\Phi_I,\Phi_Q,\Phi_P}
$$

$$
D_Q=\left.\frac{\partial I}{\partial \varphi_Q}\right|_{\Phi_I,\Phi_Q,\Phi_P}
$$

$$
D_P=\left.\frac{\partial I}{\partial \varphi_P}\right|_{\Phi_I,\Phi_Q,\Phi_P}
$$

$$
D_{IQ}=\left.\frac{\partial^2 I}{\partial \varphi_I\partial \varphi_Q}\right|_{\Phi_I,\Phi_Q,\Phi_P}
$$

---

### 6.2 一阶导频分量

定义：

$$
A_0=\cos\left(\frac{\Phi_I}{2}\right),\qquad
B_0=\cos\left(\frac{\Phi_Q}{2}\right)
$$

$$
a_0=\sin\left(\frac{\Phi_I}{2}\right),\qquad
b_0=\sin\left(\frac{\Phi_Q}{2}\right)
$$

$$
c_P=\cos(\Phi_P),\qquad s_P=\sin(\Phi_P)
$$

$$
\Delta=\delta_I+\delta_Q+\delta_P
$$

并令：

$$
K=\frac{\eta P_m}{8}
$$

则 I 路导频分量的系数为：

$$
D_I=K\left[
-\sin(\Phi_I)
-2a_0B_0c_P
-2(\delta_I+\delta_P)\sin(\Phi_I)
-2\Delta a_0B_0c_P
+2\delta_I A_0B_0s_P
+2\delta_Q a_0b_0s_P
\right]
$$

因此，频率 $\omega_I$ 处的光电流分量为：

$$
I_{\omega_I}(t)=m_I D_I\sin(\omega_I t)
$$

Q 路导频分量的系数为：

$$
D_Q=K\left[
-\sin(\Phi_Q)
-2A_0b_0c_P
-2\delta_Q\sin(\Phi_Q)
-2\Delta A_0b_0c_P
-2\delta_I a_0b_0s_P
-2\delta_Q A_0B_0s_P
\right]
$$

因此，频率 $\omega_Q$ 处的光电流分量为：

$$
I_{\omega_Q}(t)=m_Q D_Q\sin(\omega_Q t)
$$

若 P 路也叠加导频，则 P 路导频分量的系数为：

$$
D_P=K\left[
-4(1+\Delta)A_0B_0s_P
+4\delta_I B_0a_0c_P
-4\delta_Q A_0b_0c_P
\right]
$$

因此：

$$
I_{\omega_P}(t)=m_P D_P\sin(\omega_P t)
$$

---

### 6.3 I/Q 导频交调分量

I 路和 Q 路导频共同作用时，会产生和频与差频交调分量。其系数为：

$$
D_{IQ}=K\left[
(1+\Delta)a_0b_0c_P
-\delta_I A_0b_0s_P
+\delta_Q a_0B_0s_P
\right]
$$

因此：

$$
I_{IQ}(t)=m_I m_QD_{IQ}\sin(\omega_I t)\sin(\omega_Q t)
$$

由三角恒等式：

$$
\sin(\omega_I t)\sin(\omega_Q t)
=\frac{1}{2}
\left[
\cos((\omega_I-\omega_Q)t)-\cos((\omega_I+\omega_Q)t)
\right]
$$

所以，$\omega_I+\omega_Q$ 和 $|\omega_I-\omega_Q|$ 处都会出现交调分量，其幅度均与 $D_{IQ}$ 成正比。

当 I 路和 Q 路均位于最小传输点附近时：

$$
\Phi_I\approx \pi,\qquad \Phi_Q\approx \pi
$$

此时：

$$
A_0\approx 0,\qquad B_0\approx 0,\qquad a_0\approx 1,\qquad b_0\approx 1
$$

于是：

$$
D_{IQ}\approx K(1+\Delta)\cos(\Phi_P)
$$

因此，I/Q 导频交调分量与父级相位 $\Phi_P$ 的余弦函数近似成正比。交调分量在：

$$
\Phi_P=\frac{\pi}{2}\quad \text{或}\quad \Phi_P=\frac{3\pi}{2}
$$

附近达到最小值。因此，可以利用 $f_I+f_Q$ 或 $|f_I-f_Q|$ 处的交调功率作为 P 路正交偏置点的误差信号。

---

## 7. 偏置点判断关系

根据上述推导，可以得到以下结论。

### 7.1 I 路和 Q 路最小传输点

在理想条件下，当 Q 路和 P 路固定时，I 路导频一阶分量与 $D_I$ 成正比。若 Q 路位于最小传输点，且非理想扰动较小，则：

$$
D_I\approx -K\sin(\Phi_I)
$$

因此，I 路一阶导频分量在：

$$
\Phi_I=0,\pi,2\pi,\cdots
$$

处为零。这里既包括最大传输点，也包括最小传输点，因此仅靠一阶导频零点无法区分 MATP 和 MITP，需要结合直流光功率或二阶导频分量判断。

对于最小传输点，应满足：

$$
\Phi_I\approx \pi \pmod {2\pi}
$$

同理，Q 路最小传输点满足：

$$
\Phi_Q\approx \pi \pmod {2\pi}
$$

实际控制中，可以将 I 路导频频率处的功率最小作为 I-MITP 的候选指标，将 Q 路导频频率处的功率最小作为 Q-MITP 的候选指标，同时使用 PD DC 平均光功率辅助排除最大传输点和伪谷底。

---

### 7.2 P 路正交点

当 I 路和 Q 路均靠近最小传输点时，I/Q 导频交调分量满足：

$$
D_{IQ}\approx K(1+\Delta)\cos(\Phi_P)
$$

因此，交调功率满足：

$$
P_{IQ}\propto |D_{IQ}|^2\propto \cos^2(\Phi_P)
$$

所以交调功率在父级正交点附近达到最小：

$$
\Phi_P=\frac{\pi}{2}\quad \text{或}\quad \Phi_P=\frac{3\pi}{2}
$$

因此，可以将 $f_I+f_Q$ 或 $|f_I-f_Q|$ 处的交调功率最小作为 P-QTP 的搜索指标。

---

## 8. 核对后的修改结论

### 8.1 归一化传输函数必须使用半角项

正确形式为：

$$
T=\frac{1}{8}\left[
2+
\cos(\varphi_I)+
\cos(\varphi_Q)+
4\cos\left(\frac{\varphi_I}{2}\right)
\cos\left(\frac{\varphi_Q}{2}\right)
\cos(\varphi_P)
\right]
$$

最后一项不能写成 $4\cos(\varphi_I)\cos(\varphi_Q)\cos(\varphi_P)$。

---

### 8.2 非理想输出模型必须保留父级相位项

正确形式为：

$$
E_{out}(t)=\frac{E_m(t)}{2}
\left\{
(1+\delta_P)
\left[
\cos\left(\frac{\varphi_I}{2}\right)
+\delta_I\exp\left(j\frac{\varphi_I}{2}\right)
\right]
+
\left[
\cos\left(\frac{\varphi_Q}{2}\right)
+\delta_Q\exp\left(j\frac{\varphi_Q}{2}\right)
\right]
\exp(j\varphi_P)
\right\}
$$

若缺少 $\exp(j\varphi_P)$，后续无法推出 P 路正交点与 I/Q 导频交调分量之间的关系。

---

### 8.3 二阶小量表达应避免重复

推荐写法为：

$$
I_{DPMZM}=I_{id}+I_{syn}+I_{asym}+O(\delta_k^2)
$$

或者：

$$
I_{DPMZM}=I_{id}+I_{syn}+I_{asym}+I_{o2},\qquad I_{o2}=O(\delta_k^2)
$$

不要同时写成：

$$
I_{DPMZM}=I_{id}+I_{syn}+I_{asym}+I_{o2}+O(\delta_k^2)
$$

否则表达上会重复。

---

### 8.4 图编号建议

若前一张 DPMZM 系统结构图编号为“图 2-1”，则 CS-SSB 调制原理图应编号为：

**图 2-2 CS-SSB 调制原理图**

不建议写成“图 2- CS-SSB 调制的原理图”。

---

## 9. 可用于论文中的总结段落

由上述推导可知，DPMZM 的输出光功率由 I 路子 MZM、Q 路子 MZM 和父级 MZM 三个偏置相位共同决定。在理想条件下，I/Q 子 MZM 的最小传输点对应 $\Phi_I\approx\pi$ 和 $\Phi_Q\approx\pi$，父级 MZM 的正交点对应 $\Phi_P\approx\pi/2$ 或 $3\pi/2$。当在 I/Q 偏置端叠加不同频率的低频导频时，PD 输出中会出现与 I/Q 偏置相关的一阶导频分量，以及与父级偏置相关的 I/Q 交调分量。特别地，当 I/Q 子 MZM 均位于最小传输点附近时，I/Q 导频交调分量近似与 $\cos(\Phi_P)$ 成正比，因此可以利用交调功率最小来搜索父级 MZM 的正交偏置点。考虑有限消光比和幅度不平衡后，导频误差信号会出现一定偏移，因此实际控制中应结合导频功率、PD 直流光功率和局部复查机制共同判断偏置点，避免选到最大传输点、边界点或伪谷底。

