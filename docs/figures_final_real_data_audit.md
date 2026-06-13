# `figures_final/` 真实数据审计

## 审计目的

本文件用于区分报告图中的三类内容：

1. 可由当前 ROOT 文件重现的真实模拟结果；
2. 旧版真实模拟结果，但原始 ROOT 已丢失，无法重现；
3. 几何示意图，不应被描述为模拟数据。

报告中不得使用绘图脚本在缺失 ROOT 数据时生成的 reference fallback 数据点。

## 如何判断是否生成了 fallback 数据

旧版和当前版 `scripts/plot_assignment_results.py` 都包含 fallback 公式。触发 fallback 时，图标题会自动附加：

```text
(reference fallback)
```

对 B10 浓度扫描和中子通量扫描，脚本仅在所有扫描数据均缺失时生成整组 fallback 点；单个点缺失时只会跳过该点，不会自动补点。中子通量二维投影图同样仅在所有面板均无数据时生成 fallback。

现有三张旧版扫描图均没有 `(reference fallback)` 标记，因此没有触发这些自动造点分支。旧版 ROOT 文件已丢失，故无法进一步复核每个点或重新生成图。

## 可用性结论

| 图 | 类型与来源 | 是否含自动生成模拟点 | 报告建议 |
|---|---|---:|---|
| `Q1_depth_dose.png` | 当前 Q1 ROOT | 否；已由当前 ROOT 原样重现 | 可用于定量结论 |
| `Q1_dose_heatmap.png` | 当前 Q1 ROOT | 否；已由当前 ROOT 原样重现 | 可用于定量/空间分布结论 |
| `Q1_gamma_energy_heatmap_grid.png` | 当前 Q1 能量扫描 ROOT | 否；9 个能量点均存在且非空 | 可用 |
| `Q1_gamma_energy_scan.png` | 当前 Q1 能量扫描 ROOT | 否；已原样重现 | 可用 |
| `Q1_proton_energy_heatmap_grid.png` | 当前 Q1 能量扫描 ROOT | 否；9 个能量点均存在且非空 | 可用 |
| `Q1_proton_energy_scan.png` | 当前 Q1 能量扫描 ROOT | 否；已原样重现 | 可用 |
| `Q1_region_dose_comparison.png` | 当前 Q1 ROOT | 否；已原样重现 | 可用 |
| `Q1_let_spectra.png` | 当前 Q1 ROOT | 否；LET 直方图非空 | 可用 |
| `F2_forced_capture_quantitative.png` | 当前 q2D 条件俘获 ROOT，3 seeds × 100k captures | 否；已原样重现 | 可用；必须表述为每次强制俘获响应 |
| `F3_forced_capture_singlecell_distribution.png` | 当前 q2D 条件俘获 ROOT | 否；已原样重现 | 可用；不得解释为每个入射中子的绝对剂量 |
| `F4_therapy_comparison_projected_maps.png` | 当前 q2B 真实束流；BNCT 使用单 seed、100× occurrence bias | 否；剂量由 Geant4 权重还原 | 可用；图注必须说明截面偏置与权重修正 |
| `Q2_b10_concentration_scan.png` | 旧版扫描结果 | 否；现图未触发 fallback | 可作为历史真实结果使用，但需注明原始 ROOT 已丢失、不可复现 |
| `Q2_neutron_fluence_scan.png` | 旧版扫描结果 | 否；现图未触发 fallback | 可作为历史真实结果使用，但需注明原始 ROOT 已丢失、不可复现 |
| `Q2_neutron_fluence_projected_maps.png` | 旧版扫描结果 | 否；现图未触发 fallback | 可作历史定性图；不可从当前数据重新生成 |
| `F1_b10_distribution_geometry.png` | 人工绘制的模型示意图 | 不适用 | 可用，图注必须写“几何/采样示意图” |
| `Q1_body_tumor_xz_section.png` | 人工绘制的几何示意图 | 不适用 | 可用，不能称为剂量结果 |
| `Q2_geometry_mixed_cell_layout.png` | 当前 CellTree 几何布局 | 否；已由当前 ROOT 原样重现 | 可用作模型布局图 |

## 重要统计限制

当前 F4 的 gamma/proton 组各运行 2,000,000 个真实束流 histories。BNCT 组各运行一个
200,000 histories seed，并在 B10 材料内对 `neutronInelastic` 使用 100× occurrence bias：

- uniform B10：16 次 raw Li7，权重等效 Li7 为 0.925；
- shell B10：12 次 raw Li7，权重等效 Li7 为 0.432。

F4 中的能量沉积、剂量和选择性均按 Geant4 track weight 还原，raw Li7 仅表示采样统计量。
100× 截面偏置在当前短 B10 体积路径下实际带来约 10× 的 raw Li7 统计增益，并非 100×。
BNCT 热点可用于展示选择性，但 uniform/shell 的细微差异仍应谨慎解释。

当前目录下可重现的新版浓度扫描和通量扫描统计量更低：

- B10 浓度扫描：每点 0–4 次 Li7 俘获；
- 中子通量扫描：每点 0–4 次 Li7 俘获。

这些新版数据不能替代旧版扫描图来支持平滑趋势结论。

## 报告使用规则

1. 主报告优先使用可由当前 ROOT 重现的 Q1、F2、F3、F4。
2. 旧版 B10 浓度和中子通量图可以使用，但图注应明确写为“旧版真实模拟结果，原始 ROOT 未保留”。
3. 不重新运行旧版绘图脚本来生成报告图；该脚本在数据缺失时会自动生成 reference fallback。
4. 任意新生成图若标题出现 `(reference fallback)`，立即判定为不可用于报告。
5. F2/F3 是条件俘获微剂量结果；F4 是真实束流结果，两者不得混合解释为同一种剂量归一化。
