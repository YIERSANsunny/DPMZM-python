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
tests/                  统一配置与已确认工作点的回归检查
config.py               统一参数定义、校验、派生与配置加载
configs/                工作点、找点和硬件前端场景
run.py                  统一命令入口
项目流程与进展.md        项目入口与阶段计划
```

## 环境与检查

Python 3.10 或以上，在仓库根目录执行：

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

依赖为 NumPy 和 Matplotlib；当前 DPMZM 路径不需要 PyTorch。

## 统一入口与配置

公共默认参数统一在 `config.py` 中维护，场景文件只写需要覆盖的字段。
优先级为：默认参数 < JSON 场景 < 显式命令行参数。

先检查生效参数，再运行电谱：

```powershell
python run.py config --config configs/vpi_i1p4_q2p1_p37.json
python run.py spectrum --config configs/vpi_i1p4_q2p1_p37.json
python run.py spectrum --config configs/vpi_i0p5_q0p7_p140.json
```

需要临时改工作点时：

```powershell
python run.py spectrum --config configs/vpi_i1p4_q2p1_p37.json --i-source-bias 1.5 --p-phase-deg 45
```

参数含义、硬件配置与完整命令表见 [配置说明](configs/README.md)。

## 固定工作点电谱

下面复现源端 I=1.4 V、Q=2.1 V、主调总静态相位 37 度的工作点：

```powershell
python run.py spectrum --config configs/vpi_i1p4_q2p1_p37.json
```

输出默认写入 `simulation_validation/results/tia_full_spectrum/<case_name>/`，包含完整频谱 CSV、
单端/差分 PNG、参数 JSON、Markdown 摘要以及 `resolved_config.json`。
后者保存完整生效配置与派生量，也可以作为 `--config` 的输入复现运行。

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
python run.py recheck
python run.py findpoint --config configs/findpoint.json
```

第二条命令依次执行 I/Q 高响应平台、P 极值点、I 最小点候选、Q 最大点候选，
并把每一步偏置传入下一步。具体入口和后处理见
[验证目录说明](simulation_validation/README.md)。
电谱与找点的仿真采样默认统一为 1 MHz / 0.1 s；ADC 采样仍独立为 32 kSPS。

## 文档与结果管理

- [项目流程与进展](项目流程与进展.md)
- [VPI 数据对齐操作规程](simulation_validation/VPI数据对齐操作规程.md)
- [DPMZM 模型目录说明](dpmzm/README.md)

历史 CSV、NPZ、生成图片、PPT、运行报告和 Python 缓存保留在本地，并由 `.gitignore` 排除。
仓库保存源码、理论/流程文档、依赖说明和可复现的电谱回归检查。
