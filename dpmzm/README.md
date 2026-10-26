# DPMZM Package Layout

这个目录按用途拆成几类：

```text
dpmzm/
  core/           DPMZM 物理模型核心，包含输出光场、噪声、频谱、bias scan
  visualization/  绘图函数，复用 MZM 光谱/电谱绘图逻辑
  checks/         轻量级解析自检
  experiments/    VPI 对齐 demo 和各类导频/交调扫参脚本
  docs/           理论推导、模型说明、VPI 对齐记录
```

常用入口仍然可以从 `dpmzm` 顶层导入：

```python
from dpmzm import simulate_dpmzm, dpmzm_output_field
```

旧命令也保留兼容：

```powershell
python -m dpmzm.i_pilot_first_sweep
python -m dpmzm.vpi_demo
```

新代码更推荐直接使用分类后的模块：

```powershell
python -m dpmzm.experiments.i_pilot_first_sweep
```
