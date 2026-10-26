# DPMZM Python 仿真与偏压找点

DPMZM 非理想光场模型、PD/TIA 电谱、Step 1-4 离线找点以及 ADC 链路估算。
物理模型与验证脚本在同一仓库内管理，默认运行不依赖桌面上的其他代码目录。

## 目录

```text
dpmzm/
  core/model.py          DPMZM 光场、PD、频谱和噪声预算
  experiments/           I/Q 一阶、P 二阶、交调扫描
  checks/                解析自检
  visualization/         绘图入口
  docs/                  模型说明和推导
mzm/plot.py              DPMZM 复用的绘图函数
simulation_validation/  电谱、链式找点、TIA/ADC 后处理和 VPI 对照
theoretical_knowledge/  公式依据与 Step 工作流
tests/                  已确认工作点的电谱回归检查
项目流程与进展.md        项目入口与阶段计划
```

## 环境与检查

Python 3.10 或以上，在仓库根目录执行：

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

依赖为 NumPy 和 Matplotlib；当前 DPMZM 路径不需要 PyTorch。

## 固定工作点电谱

下面复现源端 I=1.4 V、Q=2.1 V、主调总静态相位 37 度的工作点：

```powershell
python simulation_validation/tia_full_spectrum.py --case-name iq_i1p4_q2p1_p37deg --i-source-bias 1.4 --q-source-bias 2.1 --p-source-bias 1.0277777777777777 --i-dither-source-amp 0.025 --q-dither-source-amp 0.025 --p-dither-source-amp 0 --tia-input-equivalent-noise-rms 1.1e-6 --tia-noise-bandwidth 8e9 --rin-db-hz -145 --add-model-noise
```

输出默认写入 `simulation_validation/results/tia_full_spectrum/`，包含完整频谱 CSV、
单端/差分 PNG、参数 JSON 和 Markdown 摘要。

本例固定口径：

| 项目 | 数值 |
|---|---|
| I/Q 电压 | NEGATIVE 模式，有效差分电压 = 2 倍源端电压 |
| P 相位 | `phi_P = pi * V_DCP / Vpi`，P 源端映射为 1 倍 |
| 半波电压 | 5 V |
| 导频 | I=1 kHz、Q=1.2 kHz，每臂 0.025 Vpeak；P 导频关闭 |
| 光功率 / 响应度 | 10 dBm / 0.8 A/W |
| I/Q ER / 插损 | 各 30 dB / 各 6 dB；P 插损 0 dB |
| TIA | 10 kOhm，`Vsingle = Z_TIA * Ipd / 2` |
| 读数 | 单端 RMS，`10log10(Vrms^2)+30`，1 ohm 等效 |
| 采样 | 1 MHz、0.1 s、矩形窗，频率间隔 10 Hz |

50 ohm 等效 dBm 比 1 ohm 读数低 16.9897 dB。
带噪谱当前采用频点噪声功率叠加近似；硬件 TIA 和 ADC 仍是独立后处理路径。

## 扫描与找点

```powershell
python simulation_validation/vpi_model_recheck.py
python simulation_validation/run_chained_findpoint.py
```

第二条命令依次执行 I/Q 高响应平台、P 极值点、I 最小点候选、Q 最大点候选，
并把每一步偏置传入下一步。具体入口和后处理见
[验证目录说明](simulation_validation/README.md)。

## 文档与结果管理

- [项目流程与进展](项目流程与进展.md)
- [VPI 数据对齐操作规程](simulation_validation/VPI数据对齐操作规程.md)
- [DPMZM 模型目录说明](dpmzm/README.md)

历史 CSV、NPZ、生成图片、PPT、运行报告和 Python 缓存保留在本地，并由 `.gitignore` 排除。
仓库保存源码、理论/流程文档、依赖说明和可复现的电谱回归检查。
