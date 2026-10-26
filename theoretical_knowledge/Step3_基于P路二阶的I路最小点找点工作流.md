# Step 3：基于 P 路二阶的 I 路最小点找点工作流

版本：2026-07-06

## 0. 文档用途

本文是 Step 3 工作流文档，用于指导程序和实验在已经完成 I/Q 高响应平台找点和 P 路极值点找点之后，利用 P 路导频二阶分量寻找 I 路最小传输点。

本文不展开长篇公式推导。详细公式见：[找点流程公式依据.md](./找点流程公式依据.md) 和 [P路二阶.md](./P路二阶.md)。

---

## 1. Step 3 目标

Step 3 的输入来自 Step 1 和 Step 2：

1. `V_DCQ_bridge`
2. `V_DCP_extreme`

Step 3 的输出为：

1. `V_DCI_min`

其中：

```text
V_DCI_min = I 路最小传输点对应的 I 路偏置
```

Step 3 的核心目标是：

> 固定 Q 路和 P 路，扫描 I 路偏置，观测 P 路导频二阶功率 `P_2fP`，用 `P_2fP` 的主要局部最小值寻找 I 路最小传输点。

---

## 2. 理论依据简述

固定 Q 路和 P 路后，P 路二阶项随 I 路偏置的变化可写为：

$$
P_{2f_P}(\Phi_I)
\propto
\left[
U\cos\left(\frac{\Phi_I}{2}\right)
+
V\sin\left(\frac{\Phi_I}{2}\right)
\right]^2
$$

其中：

$$
U=(1+\Delta)B_0c_P-\delta_Qb_0s_P
$$

$$
V=\delta_IB_0s_P
$$

在 Step 2 中，P 路已经被放到传输极值点附近，因此：

$$
s_P\approx0,
\qquad
c_P\approx\pm1
$$

于是常用近似为：

$$
P_{2f_P}(\Phi_I)
\propto
B_0^2
\cos^2\left(\frac{\Phi_I}{2}\right)
$$

所以当：

$$
\Phi_I\approx\pi
$$

时：

$$
\cos\left(\frac{\Phi_I}{2}\right)\approx0
$$

P 路二阶功率出现谷值，对应 I 路最小传输点。

---

## 3. 输入条件

执行 Step 3 前，需要满足：

1. Q 路已固定在 `V_DCQ_bridge`；
2. P 路已固定在 `V_DCP_extreme`；
3. P 路导频已开启；
4. 已确定 I 路扫描范围和步长；
5. 已确定 P 路二阶频点读取方式；
6. 已确定扫描结果保存路径。

P 路二阶频点为：

$$
2f_P
$$

如果 P 路导频频率为 $f_P$，则程序应读取 PD 频谱中 $2f_P$ 处的功率。

当前 TIA 控制口径下，推荐：

```text
f_P = 1.3 kHz
2f_P = 2.6 kHz
```

因此 Step 3 读取 `2.6 kHz` 处的 P 路二阶功率。该频点位于当前 `100 kΩ // 10 pF` TIA 的有效通带内，并且在 `32 kSPS / 640点 Goertzel` 下正好落在整数 bin 上。

---

## 4. 执行步骤

### 4.1 固定 Q/P

将 Q/P 设置为前序步骤输出：

```text
V_DCQ = V_DCQ_bridge
V_DCP = V_DCP_extreme
```

保持 Q 路和 P 路不再扫描。

### 4.2 扫描 I 路

扫描 I 路直流偏置：

```text
V_DCI = V_DCI_start → V_DCI_stop
```

每个 I 路偏置点记录：

1. `V_DCI`
2. P 路二阶功率 `P_2fP`
3. P 路二阶噪声底 `noise_floor_at_2fP`
4. PD 直流功率 `P_DC`
5. 二阶频点信息

### 4.3 提取 P 路二阶曲线

得到：

$$
P_{2f_P}(V_{DCI})
$$

该曲线用于寻找 I 路最小传输点。

### 4.4 寻找主要局部最小值

在 $P_{2f_P}(V_{DCI})$ 曲线中寻找主要局部最小值点。

写入：

```text
V_DCI_min = arg local min P_2fP(V_DCI)
```

如果存在多个可接受谷值，优先选择曲线形态更清晰、远离扫描边界、重复性更好的谷值。

---

## 5. 选点判据

`V_DCI_min` 优先满足：

1. P 路二阶功率接近主谷值；
2. 谷值不贴近扫描边界；
3. 谷值两侧趋势清晰；
4. 谷值与噪声底关系可解释；
5. 多周期扫描时同类谷值可重复出现；
6. 选点后再次小范围扫描仍能复现该局部最小值。

PD 直流功率可以作为辅助记录量，用于后续诊断 I 路是否确实接近低传输状态，但当前 Step 3 的主判据是 P 路二阶功率谷值。

---

## 6. 输出

Step 3 完成后，需要输出：

1. `V_DCI_min`
2. `P_2fP_min`
3. `P_DC_at_I_min`
4. `noise_floor_at_2fP`
5. `SNR_or_margin`
6. I 路扫描 CSV
7. I 路扫描下的 P 路二阶曲线图

建议同时记录：

```text
step = 3
state = I_MIN_FOUND
next = Q_MAX_SEARCH
```

---

## 7. 下一步入口

当 `V_DCI_min` 写入完成后，流程进入：

```text
Step 4:
基于 Q 路一阶寻找 Q 路最大传输点
```

Step 4 需要基于当前 I 路最小点和 P 路极值点，扫描 Q 路并观测 Q 路一阶功率谷值，再结合 PD 直流功率选择 Q 路最大传输点。对应工作流见：[Step4_基于Q路一阶的Q路最大点找点工作流.md](./Step4_基于Q路一阶的Q路最大点找点工作流.md)。
