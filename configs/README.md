# 配置与统一入口

在仓库根目录使用 `python run.py <命令> --config <场景.json>`。
公共默认值只在根目录 `config.py` 定义；场景使用标准 JSON，不增加第三方依赖。

## 常用命令

| 命令 | 用途 | 默认配置 |
|---|---|---|
| `config` | 预览完整配置和派生量，不进行仿真 | `config.py` 默认值 |
| `spectrum` | 固定工作点的 VPI TIA 电谱 | 默认 1.4 V / 2.1 V / 37 度 |
| `findpoint` | Step 1-4 串联扫描找点 | `configs/findpoint.json` |
| `validate` | 使用已有 CSV 重新选点与生成报告 | `configs/findpoint.json` |
| `recheck` | 固定扫描夹具与完整时域模型交叉检查 | `config.py` 默认公共参数 |
| `visibility` | 选点的硬件 TIA 可见性估算 | `configs/hardware.json` |
| `tia` | 从扫描 CSV 生成硬件 TIA 观测曲线 | `configs/hardware.json` |
| `adc` | 对已有 TIA 曲线进行 ADC 后处理 | `configs/hardware.json` |

上述仿真与后处理脚本入口保留，并接受同样的 `--config` 参数。
例如 `python simulation_validation/tia_full_spectrum.py --config configs/vpi_i1p4_q2p1_p37.json`。

## 参数分组

| 分组 | 内容 |
|---|---|
| `physical` | 半波电压、ER、插损、光功率、PD 响应度、RIN、温度、源端映射系数 |
| `drive` | 固定工作点源端偏置、P 总相位、I/Q/P 导频幅度与频率 |
| `sampling` | 仿真采样率、时间窗口、随机种子、电谱噪声叠加开关 |
| `tia` | VPI/硬件类型、跨阻、输入等效噪声；硬件反馈电容和运放噪声 |
| `adc` | 32 kSPS、PGA、OSR、Goertzel、输入 RC 和 ADC 噪声 |
| `findpoint` | Step 1 固定偏置、全流程扫描范围/步进、候选点判据和 P 导频幅度 |

输入字段名中的 `_v`、`_vpeak`、`_hz`、`_s`、`_ohm`、`_f` 和 `_a` 分别表示对应 SI 单位。
I/Q 偏置与导频幅度始终填写源端值，模型内有效差分值自动乘 `child_source_gain`。
P 使用 `drive.p_phase_deg`，表示 Q 相对 I 的总静态相位；P 源端电压由程序换算。
有效差分值属于只读派生量，不接受作为场景输入。

## 场景示例

```json
{
  "case_name": "my_working_point",
  "drive": {
    "i_source_bias_v": 1.4,
    "q_source_bias_v": 2.1,
    "p_phase_deg": 37.0,
    "p_dither_source_amp_vpeak": 0.0
  }
}
```

```powershell
python run.py config --config configs/vpi_i1p4_q2p1_p37.json
python run.py spectrum --config configs/vpi_i1p4_q2p1_p37.json --p-phase-deg 45 --no-add-model-noise
python run.py findpoint --config configs/findpoint.json --scan-step 0.1
python run.py tia --config configs/hardware.json
python run.py adc --config configs/hardware.json
```

显式命令行参数优先级最高，覆盖值同样保存进最终配置。
原有 `--p-source-bias` 电压入口保留，与 `--p-phase-deg` 互斥。

## 执行与记录规则

- 每次运行生成 `resolved_config.json`，保存完整生效参数、源端/差分换算、FFT 与 ADC 频点宽度。
- `spectrum` 按 `case_name` 分目录输出；其他命令可用原有输出目录参数指定独立运行目录。
- 默认仿真采样为 `sampling.fs_hz=1000000`、`t_total_s=0.1`，对应 10 Hz 频点间隔。
- 找点与单独 CSV 验证默认都排除边缘 5 个点；可以通过 `findpoint.edge_points` 或 `--edge-points` 覆盖。
- ADC 独立使用 `adc.sample_rate_sps=32000`、`goertzel_points=640`，对应 50 Hz 频点间隔。
- VPI TIA 为 10 kOhm 平坦跨阻电谱模型；硬件 TIA 为 100 kOhm 的 Rf/Cf/运放估算。入口会拒绝混用两种类型。
- 找点采用 `findpoint.step1_*` 初始设置并传递后续偏置，不使用固定电谱场景的 I/Q/P 静态偏置。
- 找点共享 I/Q 导频幅度和频率；流程的 P 导频使用 `findpoint.p_dither_source_amp_vpeak`，不受固定电谱 P 导频关闭状态影响。
- `recheck` 保留固定扫描夹具的偏置和范围，读取统一公共器件、导频和采样参数。
- `sampling.add_model_noise` 控制固定电谱的频点噪声功率叠加；硬件 TIA/ADC 仍按原后处理模型估算噪声。
- 配置统一不改变现有找点观测路径：选点仍读取 PD 扫描信号，TIA/ADC 的影响继续在后处理阶段评估。

程序会检查未知字段、数值类型、非正采样率/步进、相位输入冲突与非相干采样频点。
