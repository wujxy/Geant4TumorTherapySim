# Q2 最终结论图实验计划与接手文档

**最后更新：2026-06-12**

本文档记录 Q2 当前进度，以及已经与用户确认的最终实验方案。后续 agent 应以本文档为准；旧的
[q2_experiment_design.md](q2_experiment_design.md) 和 [q2_handoff.md](q2_handoff.md)
仅作为历史背景与已有运行记录参考。

## 0. 最新执行状态

F1–F4 聚焦绘图流程已经实现并通过首轮数值与目视检查：

```text
scripts/plot_q2_final_results.py
tests/test_q2_final_figures.py
figures2/F1_b10_distribution_geometry.png
figures2/F2_forced_capture_quantitative.png
figures2/F3_forced_capture_singlecell_distribution.png
figures2/F4_therapy_comparison_projected_maps.png
```

运行命令：

```bash
python scripts/plot_q2_final_results.py --section all
```

F2 当前三 seed 均值：

| 模式 | Tumor cell (MeV/capture) | Normal cell | Tumor nucleus | Normal nucleus | Tumor nucleus hit | Normal nucleus hit | Selectivity |
|---|---:|---:|---:|---:|---:|---:|---:|
| uniform | `1.4624` | `0.03342` | `0.23679` | `0.001481` | `0.3568` | `0.01257` | `0.9777` |
| cytoplasm-only | `1.3991` | `0.03631` | `0.13465` | `0.001552` | `0.2626` | `0.01347` | `0.9747` |
| shell | `1.1952` | `0.04661` | `0.07778` | `0.002331` | `0.1781` | `0.01701` | `0.9625` |

F4 将每组平均肿瘤细胞剂量归一化为 `1 Gy` 后：

| 疗法 | Normal cell dose (Gy) | Dtumor/(Dtumor+Dnormal) |
|---|---:|---:|
| gamma 1 MeV | `0.9265` | `0.5191` |
| proton 80 MeV | `1.0129` | `0.4968` |
| BNCT uniform, biased | `0.0764` | `0.9290` |
| BNCT shell, biased | `0.0776` | `0.9280` |

F4 热点图使用对数色标。零剂量投影列必须显示为黑色；不能使用 matplotlib
对屏蔽值的默认透明色，否则会透出白色背景并被误认为最高剂量。图中的单个投影点
是同一 `(x,z,cell type)` 列沿 `y` 方向的剂量和，因此少数被粒子命中的 normal
投影列可以形成真实亮点，但不代表 normal 平均剂量与 tumor 相同。

当前图形结论：

- F2/F3 显示核响应依次为 `uniform > cytoplasm-only > shell`，说明是否允许
  B10 进入细胞核会显著改变单位俘获核响应。
- 反应位置越靠近细胞外侧，对正常细胞与正常细胞核的沉积越高。
- F3 展示三种 tumor 响应和一张 cytoplasm-only normal 对照，使用共享对数色标和共享径向坐标。
- F4 显示在等平均肿瘤细胞剂量下，BNCT uniform/shell 的正常细胞剂量显著低于 gamma/proton；当前单 seed 加权结果中两种 B10 分布的选择性接近。

### F3 边界采样修正

初版 F3 在核/细胞质界面和细胞外表面出现锐利亮线，normal 图内部还出现明显无沉积矩形区域。检查确认这不是材料效应：

- uniform 肿瘤细胞的核与外层均为同一种 borated water，却在 `r=2.5 um` 出现峰；
- normal 细胞各区域均为 water，却同时在 `r=2.5 um` 和 `r=5 um` 出现峰。

根因是旧计分把整个 Geant4 step 的能量全部填在 pre-step 点。逻辑体边界会强制切断 step，下一步从边界开始，因此能量被系统性堆积到边界 bin；长 step 还会使内部部分 bin 没有采样。

当前实现只对 cell-local H1/H2 做路径分段计分：每条 step 按不超过 `0.1 um` 的间距拆分，并将该 step 的能量守恒地均分到各子段中点。EventTree/CellTree 总能量仍只累计一次。

进一步检查发现，仅做路径分段后，normal 核边界仍存在约 `2.3–2.5` 倍的阶梯跳变。原因是核逻辑体边界会改变 Geant4 凝聚历史输运 step 的划分，而 `G4UserLimits` 在未注册 `G4StepLimiterPhysics` 时不会生效。

最终修正为：

- problem2 的 detailed outer cell、cytoplasm 和 nucleus 统一设置 `0.05 um` 最大 step；
- 参考物理列表额外注册 `G4StepLimiterPhysics`，使最大 step 限制真正作用于带电粒子；
- 保留 `0.1 um` cell-local 路径分段计分，确保空间直方图能量守恒。

正式 `3 seeds x 100000 captures` 重跑后，normal 核边界相邻径向 bin
`density(r=2.55 um) / density(r=2.45 um)` 为：

- uniform capture：`1.060`
- shell capture：`1.044`

原先的阶梯跳变已经消失，剩余变化为平滑的外源短射程粒子径向衰减。

修正后：

- 核边界和细胞表面的锐利亮线消失；
- normal 图中的矩形空区消失；
- F2 总能量、核响应和选择性保持不变；
- normal 外层沉积仍高于内部，这是因为反应发生在邻近肿瘤细胞，进入 normal 的短射程粒子多数只穿过或擦过外层，属于真实几何输运效应。

## 1. 核心研究目标

Q2 最终只回答两个问题：

1. B10 在肿瘤细胞内采用 uniform、cytoplasm-only 或 shell 分布时，俘获反应产物在肿瘤细胞、细胞核和邻近正常细胞中的沉积有何差异？
2. 在相同平均肿瘤细胞剂量下，真实束流 BNCT 相比 gamma/proton 是否具有更高的肿瘤选择性？

最终仅保留 F1、F2、F3、F4。暂不考虑 B10 浓度扫描、中子注量扫描、独立 F7、LQ 存活率和两阶段 ppm 合成图。

### 模拟方式选择原则

- **直接 B10 反应模式**：用于 F2、F3。研究问题只关心俘获发生后，反应位置如何影响局部高 LET 沉积，不需要模拟低概率中子俘获过程。
- **真实粒子束流模式**：用于 F4。跨疗法对比依赖 gamma、proton 和 neutron 的完整输运过程，必须保留真实束流直接入射。

直接反应模式解决真实中子 B10 俘获截面小、局部图统计量不足的问题，但每个 event 代表一次 B10 俘获，不能解释为一个入射中子或绝对临床剂量。

## 2. 当前已完成进度

### 2.1 条件俘获模拟

程序已实现 `/therapy/sourceMode b10Capture`：

- 仅用于 `problem2` 的 `uniform`、`cytoplasm` 或 `shell` 模式。
- 为保持旧 ROOT 文件兼容，`boronMode` 编码保留 `uniform=1`、`shell=2`，
  新增 `cytoplasm=3`。
- 每个 event 在一个含 B10 肿瘤细胞内直接生成一次真实 B10 俘获反应。
- uniform 在整个细胞体积内均匀采样；cytoplasm 在 `r=2.5–5 um` 内按体积
  均匀采样并排除细胞核；shell 在 `r=4–5 um` 内按体积均匀采样。
- alpha 与 Li7 背对背各向同性发射，并包含两个真实反应分支及伴随 gamma。
- 条件俘获模式下，cell-local H1/H2 只记录 alpha/Li7 高 LET 沉积。

已有数据：

```text
output_q2D_capture_uniform_seed{1..3}.root
output_q2D_capture_cytoplasm_seed{1..3}.root
output_q2D_capture_shell_seed{1..3}.root
```

每个文件含 `100000` 次条件俘获，总计：

- uniform：`300000 captures`
- cytoplasm：`300000 captures`
- shell：`300000 captures`

正式文件已验证：每个 EventTree 均为 `100000` 行；cytoplasm 三个 seed 的反应
半径均位于 `2.5–5 um`，shell 均位于 `4–5 um`。

RunTree、EventTree、CellTree、`hCellLocalTumor/Normal` 和
`hCellRadialTumor/Normal` 均已输出。正常细胞 H1/H2 已有非零沉积，不需要新增反应模式。

条件俘获数据中的 H2 总 alpha/Li7 沉积：

| 模式 | Tumor cells | Normal cells |
|---|---:|---:|
| uniform | `438726.6 MeV` | `10025.5 MeV` |
| cytoplasm-only | `419724.4 MeV` | `10893.7 MeV` |
| shell | `358553.3 MeV` | `13983.5 MeV` |

这说明 shell 反应产物更容易向细胞外传播，并对邻近正常细胞产生更高沉积；该差异应在 F2、F3 中保留，不应把两种模式的 normal 响应合并。

### 2.2 当前条件俘获结果

已生成的高统计结果表明：

| 指标 | uniform | cytoplasm-only | shell |
|---|---:|---:|---:|
| 核内 alpha+Li7 沉积 | `0.2368 MeV/capture` | `0.1346 MeV/capture` | `0.0778 MeV/capture` |
| 核高 LET 命中概率 | `35.68%` | `26.26%` | `17.81%` |

当前几何为：

- 细胞半径：`5 um`
- 细胞核半径：`2.5 um`
- cytoplasm-only：`r=2.5–5 um`
- shell：`r=4–5 um`

在该几何下，uniform 允许反应直接发生于细胞核内；cytoplasm-only 排除核内
反应但仍允许反应紧邻核表面；shell 反应产物需要先穿过约 `1.5 um` 细胞质。
因此三者单位俘获核响应呈 `uniform > cytoplasm-only > shell`。

### 2.3 真实束流跨疗法数据

以下 F4 输入文件均完整可读，CellTree 各含 `4096` 行：

```text
output_q2B_gamma_final.root
output_q2B_proton_final.root
output_q2B_neutron_uniform_biased_seed1.root
output_q2B_neutron_shell_biased_seed1.root
```

gamma、proton 各运行 `2000000` 个真实入射粒子；两个 BNCT 文件各运行单 seed、
`200000` 个真实入射中子，并在 B10 材料体内施加 `100x` occurrence bias。当前原始
平均整细胞剂量为：

| 疗法 | Dtumor (Gy) | Dnormal (Gy) | Dtumor/(Dtumor+Dnormal) |
|---|---:|---:|---:|
| gamma 1 MeV | `0.002029` | `0.001880` | `0.5191` |
| proton 80 MeV | `0.095375` | `0.096604` | `0.4968` |
| BNCT uniform, biased | `0.000173` | `0.0000132` | `0.9290` |
| BNCT shell, biased | `0.0000755` | `0.00000586` | `0.9280` |

四组原始肿瘤剂量差异较大。因此 F4 不直接比较原始剂量大小，而是在后处理中将每组平均肿瘤细胞剂量线性归一化到 `1 Gy`，再比较正常细胞剂量和肿瘤选择性。

两个 BNCT 文件的 raw Li7 分别为 `16` 和 `12`，加权等效 Li7 分别为 `0.925`
和 `0.432`。偏置后 raw Li7 统计量约相当于旧版 `2M` 未偏置运行，但只需要十分之一
histories；不能将 raw Li7 或 `100x` 偏置倍率直接解释为真实俘获产额。

## 3. 最终图组

所有新图保存到仓库根目录的 `figures2/`，不得覆盖 `figures/` 中的历史图。

### F1：B10 分布几何示意

输出：

```text
figures2/F1_b10_distribution_geometry.png
```

内容：

- 展示 uniform、cytoplasm-only 与 shell 三种 B10 分布。
- 标注细胞半径 `5 um`、核半径 `2.5 um`、shell 区域 `4–5 um`。
- 只负责定义几何，不承载剂量结论。

### F2：单位俘获定量比较

输出：

```text
figures2/F2_forced_capture_quantitative.png
```

数据源：现有 q2D 条件俘获三 seed ROOT 文件。

每个指标展示三 seed 均值和标准差，四个面板为：

1. Tumor/normal 整细胞 alpha+Li7 沉积能量 `/ capture`。
2. Tumor/normal 细胞核 alpha+Li7 沉积能量 `/ capture`。
3. 一次俘获使任意 tumor/normal 细胞核获得 alpha/Li7 沉积的概率。
4. 整细胞高 LET 选择性：

```text
S_capture = E_tumor / (E_tumor + E_normal)
```

F2 用于定量回答：

- 三种分布对肿瘤细胞和细胞核的单位俘获响应有何差异；
- 三种反应位置对邻近正常细胞的沉积有何差异；
- 哪种模式具有更高的单位俘获局部选择性。

F2 不解释真实中子俘获率或绝对临床剂量。

### F3：四列单细胞局部响应图

输出：

```text
figures2/F3_forced_capture_singlecell_distribution.png
```

四列依次为：

1. tumor response from uniform capture
2. tumor response from cytoplasm-only capture
3. tumor response from shell capture
4. normal control from cytoplasm-only capture

布局：

- 顶行：`(r_xy, z_local)` 二维 alpha+Li7 沉积密度。
- 底行：对应的径向 alpha+Li7 沉积密度。
- 二维图除以精确圆柱环体积：

```text
DeltaV = pi * (r_out^2 - r_in^2) * Delta z
```

- 径向图除以精确球壳体积：

```text
DeltaV = 4*pi/3 * (r_out^3 - r_in^3)
```

- 所有结果再除以强制俘获数，单位为 `MeV / capture / um^3`。
- 四张二维图共享对数色标，四张径向图共享坐标范围。
- 标出核边界 `r=2.5 um` 与 shell 起点 `r=4 um`。

正常细胞列表示所有正常细胞的叠加响应，来源是肿瘤细胞内反应产物的跨细胞输运；正常细胞本身不含 B10，也没有在其内部强制产生反应。

F3 用于解释 F2 的空间机制：

- B10 能否进入细胞核为何会显著影响核响应；
- cytoplasm-only 为什么位于 uniform 与 shell 之间；
- shell 是否在 `r=4–5 um` 形成外壳热源；
- 肿瘤细胞内反应产物如何传播至邻近正常细胞。

### F4：真实束流跨疗法对比

输出：

```text
figures2/F4_therapy_comparison_projected_maps.png
```

数据源：gamma/proton q2B final ROOT 文件，以及 BNCT biased single-seed ROOT 文件。
四组均使用真实束流直接入射结果；BNCT 剂量由 Geant4 track weight 还原。

归一化：

```text
scale_i = 1 Gy / mean_tumor_cell_dose_i
scaled_cell_dose = raw_cell_dose * scale_i
```

布局：

- 顶行：四种疗法的微区二维投影细胞剂量图。
- 四个热点图使用共享绝对色标，不进行单面板归一化。
- 中间：四种疗法归一化后的 tumor/normal 平均整细胞剂量柱状图。
- 底部：肿瘤选择性：

```text
S_therapy = D_tumor / (D_tumor + D_normal)
```

- 图中注明每组原始平均肿瘤剂量和归一化倍数。

F4 用于回答：

> 在达到相同平均肿瘤细胞剂量时，哪种疗法对正常细胞的剂量更低、肿瘤选择性更高？

F4 不使用条件俘获数据，不使用 LQ 存活率或治疗指数。

## 4. 实施计划

### 4.1 新绘图入口

新增：

```text
scripts/plot_q2_final_results.py
```

命令行接口：

```text
python scripts/plot_q2_final_results.py --section all
python scripts/plot_q2_final_results.py --section f1
python scripts/plot_q2_final_results.py --section f2
python scripts/plot_q2_final_results.py --section f3
python scripts/plot_q2_final_results.py --section f4
```

默认输出目录固定为 `figures2/`。复用 `scripts/plot_assignment_results.py` 中现有 ROOT 读取、cell 投影和体积计算逻辑，但不得让新流程重绘或覆盖旧图。

### 4.2 输入校验

绘图前必须验证：

- F2/F3 输入 `RunTree.sourceMode == b10Capture`。
- F4 输入 `RunTree.sourceMode == beam`。
- 每个文件 EventTree 行数等于 RunTree 的事件数。
- F2/F3 三个 seed 均存在且可读。
- F3 的 tumor/normal H1/H2 沉积均非零。
- F4 四个文件均存在、可读，且 CellTree 含 `4096` 行。
- 所有选择性值有限并位于 `[0,1]`。

### 4.3 文档更新

实现完成后更新报告 Q2 部分：

- 只使用 F1–F4 组织结论。
- 明确区分“直接反应微剂量实验”和“真实束流跨疗法实验”。
- 删除或移至附录的 ppm 扫描、中子注量扫描、两阶段合成剂量和独立 F7。
- 不把条件俘获结果解释为入射中子剂量或临床绝对剂量。

## 5. 测试与验收

### 单元测试

- 精确圆柱环与球壳体积计算正确。
- F2/F4 选择性严格使用：

```text
Dtumor / (Dtumor + Dnormal)
```

- F4 归一化后四组平均肿瘤细胞剂量均为 `1 Gy`，误差小于 `1e-6`。
- F2/F3 输入拒绝 beam 文件；F4 输入拒绝 b10Capture 文件。

### 图形验收

- `figures2/` 生成且仅生成 F1–F4 新图。
- F3 四列均非空；normal 响应明显低于对应 tumor 响应。
- F3 shell tumor 列在 `r=4–5 um` 显示明显外壳响应。
- F4 四张热点图共享同一绝对色标。
- F4 柱状图中的平均肿瘤细胞剂量均为 `1 Gy`。
- F4 选择性数值与当前数据预期一致：
  gamma/proton 约 `0.5`，BNCT uniform/shell 明显更高。
- 现有 `figures/` 文件不得被新绘图流程修改。

### 完整验证命令

```bash
cmake --build build -j
python scripts/plot_q2_final_results.py --section all
python -m py_compile scripts/plot_q2_final_results.py
git diff --check
```

同时运行仓库现有 Python 测试和新增 Q2 最终图测试。

## 6. 明确不做

本轮不执行以下工作：

- 不重跑 B10 浓度扫描。
- 不重跑中子注量扫描。
- 不生成两阶段 ppm 合成剂量图。
- 不保留独立 F7 微区图。
- 不使用 LQ 存活率、lethal-hit fraction 或治疗指数作为最终结论。
- 不修改或删除现有历史 ROOT 数据与 `figures/` 图。

## 7. 接手优先级

1. 编写 `scripts/plot_q2_final_results.py` 和测试。
2. 生成并检查 `figures2/F1`–`F4`。
3. 核对 F2/F3 数值与空间分布是否一致。
4. 核对 F4 的等肿瘤剂量归一化和选择性公式。
5. 按四图逻辑重写报告 Q2 部分。
# B10 俘获截面偏置说明

F4 的 BNCT 真实中子束流使用 Geant4 occurrence bias 提高中子俘获采样效率。当前默认在
`B10_Borated_Water` 逻辑体内，将 QGSP_BIC_HP 的 neutron `neutronInelastic` 过程截面偏置为模拟截面的
100 倍。Geant4 HP 将目标 `B10(n,alpha)Li7` 通道归入该过程；偏置算子仅附着于含 B10 的材料体积。
这是一种方差缩减技术，并不代表物理 B10 浓度或真实反应截面提高。

程序使用 Geant4 传播的统计权重修正所有能量沉积、剂量和俘获产额。F4 图中的剂量均为
权重还原后的物理估计值，同时标注 raw Li7 captures、weighted-equivalent Li7 captures
和偏置倍率。报告方法部分必须注明该偏置方法；不得将 raw captures 直接解释为真实俘获数。
