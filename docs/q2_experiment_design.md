# Q2 BNCT 实验设计文档

> 本文档是 Q2（BNCT shell vs uniform B10 分布对比）的**完整实验设计**，整理自对话开始时的设计讨论。
> 实验执行进度见 [q2_handoff.md](q2_handoff.md)。
> 时间预算与陷阱见 [q2_timing_benchmark.md](q2_timing_benchmark.md)。

## 0. 上下文

项目已完成 Q1（gamma/proton 外照射对比），但 Q2 原始实现存在三个本质性问题，使得实验结果与作业核心命题方向相反或无法直接论证：

1. **结论方向相反**：旧 §4.4 在等 ppm 条件下报告 uniform 核剂量 = `2.06e-1 Gy` > shell `3.47e-2 Gy`，与作业字面预期相反。根因是"相同硼浓度"被实现为"相同 ppm"，而 shell 区体积仅占整细胞 ~49% → shell 模式总 B10 原子数只有 uniform 的一半，反应数被人为压低。
2. **杀伤效果未定义**：现有指标只到物理剂量，没有任何"细胞死了没"的口径，无法直接支撑"BNCT 对正常细胞损伤更低"对比性结论。
3. **缺少机制可视化**：现有图都是细胞群体的柱状/散点统计，没有"硼壳热源 → 向内沉积"的微观空间证据。

本实验设计解决这三件事：
- (a) 修正实验变量定义（相同 B10 **总量** 而非相同 ppm；引入存活率口径）
- (b) 重设对照实验结构以分别支撑 H1/H2/H3/H4
- (c) 新增一张关键图 —— 单细胞叠加剂量分布图（顶行 2D，底行 1D），把 4096 个细胞按类型叠加到同一局部坐标系，用空间集成换统计量，直观展示 shell 与 uniform 的微观沉积差异

---

## 1. 作业核心命题与假设

### 1.1 作业字面命题

> 在相同硼浓度和相同中子注量下，¹⁰B 集中分布在细胞外壳（1 μm 层）比均匀分布在整个细胞内，能产生更高的细胞核剂量和更低的细胞存活率，且 BNCT 对正常细胞的损伤低于伽马/质子放疗。

### 1.2 拆解为 4 个可验证假设

| 编号 | 假设 | 主证图 |
|---|---|---|
| H1 | 等 B10 总原子数 + 等中子注量下，shell → 肿瘤核剂量更高、存活率更低 | F2 + F3' |
| H2 | 等处方剂量下，BNCT 对正常细胞损伤 < gamma/proton | F4 |
| H3 | shell 优势随 B10 总量降低而相对放大（贴近临床低浓度）| F5 |
| H4 | 中子注量主要放大绝对剂量，选择性比例不变 | 图 13（沿用旧 §4.6）|

---

## 2. 变量与杀伤效果定义

### 2.1 自变量 / 协变量 / 因变量
| 类别 | 量 | 取值 |
|---|---|---|
| 自变量 | B10 分布模式 | {none, uniform, shell} |
| 自变量 | 疗法粒子 | {gamma 1 MeV, proton 80 MeV, neutron 0.5 eV} |
| **协变量（必须等化）**| 每细胞 B10 总原子数 N_B10 | uniform_ppm = X 时，shell_ppm = X × V_cell / V_shell ≈ 2.05·X |
| 协变量 | 中子注量代理 | events × beamRadius²（同一束斑下用 events 即可）|
| 协变量 | 微区几何、束流方向、能量沉积切片 | 全部锁定 |
| 因变量（物理）| 细胞核平均剂量 D_nuc、整细胞剂量 D_cell、α+Li7 击中核次数 N_hit | 直接读 CellTree |
| 因变量（生物代理）| 细胞存活率 S、杀伤率 K = 1 − S | 后处理 |
| 衍生量 | 选择性 SEL = D_nuc_tumor / D_nuc_normal、治疗指数 TI = K_tumor / K_normal | 后处理 |

### 2.2 "相同硼浓度"重定义

作业语境中的"相同硼浓度"实际指**每肿瘤细胞内 ¹⁰B 原子总数相同**。约束公式：

```text
ppm_shell · V_shell · ρ_shell = ppm_uniform · V_cell · ρ_cell
≈ ppm_uniform · V_cell / V_shell   (密度同为 1 g/cm³)
```

对 cellRadius=5 μm、shellThickness=1 μm：
- V_shell/V_cell = 1 − (4/5)³ = 0.488
- **ppm_shell ≈ 2.049 · ppm_uniform**

**物理上限**：Geant4 `G4Material::AddElementByMassFraction` 要求质量分数 ≤ 1，故 `shell_ppm ≤ 1×10⁶ ppm → uniform_equiv ≤ 488000 ppm`。**本次重运行采用 uniform_equiv = 300000 ppm**（shell 实际 ≈ 614550 ppm，约 61% 质量分数，仍偏离临床但保持合法且反应率充足）。

### 2.3 杀伤效果（双口径）

**口径 A：LQ 存活模型（主口径）** — 按粒子拆分细胞核剂量后用 RBE 加权，代入线性二次模型：

```text
D_eff_nuc = Σ_p RBE_p · D_nuc,p
S = exp(-α · D_eff − β · D_eff²)
```

参数：

| 量 | 取值 |
|---|---:|
| RBE gamma/electron | 1.0 |
| RBE proton | 1.1 |
| RBE alpha+Li7（tumor）| 1.3 |
| RBE alpha+Li7（normal）| 3.0 |
| α/β tumor | 10 Gy（α=0.3, β=0.03）|
| α/β normal | 3 Gy（α=0.1, β=0.033）|

参数为文献保守值；用于本节内的相对比较，不代表临床绝对值。RBE 在 normal 细胞上更高反映了高 LET 粒子在敏感组织上的等效生物效应放大。**报告中需明示参数取值并标注敏感性。**

**口径 B：核击中阈值（机制直观口径）** — 单细胞核被 α 或 Li7 击中 ≥ 1 次 → 标记为 lethal hit。Lethal fraction `f_LH = N_LH / N_cells` 作为存活的几何代理，不依赖 RBE/αβ 参数。

> 报告中两套口径都报出，**结论一致才采信**；不一致则讨论参数不确定性。

### 2.4 代码改动需求（最小集）

**改动 1**：CellTree 新增按粒子拆分的核内剂量列（支撑 LQ 口径）
- 修改：[include/TherapyAnalysisManager.hh](../include/TherapyAnalysisManager.hh) 的 `CellAccumulator` 增加 `edepNucleusByGamma/Proton/Alpha/Li7`、`alphaNucleusHits/liNucleusHits`
- 修改：[src/TherapyAnalysisManager.cc](../src/TherapyAnalysisManager.cc) `AddEnergyDeposit` 按 `particleName` 分桶累加
- CellTree 新增 6 列

**改动 2**：新增 H2 直方图 —— 单细胞叠加 (r, z_local) 2D 沉积谱
- 修改：[src/TherapyAnalysisManager.cc](../src/TherapyAnalysisManager.cc) `CreateObjects` 新增：
  - 2 个 H2（`hCellLocalNormal`、`hCellLocalTumor`），50 bins r ∈ [0,5] μm × 50 bins z ∈ [−5,5] μm
  - 2 个 H1（`hCellRadialNormal`、`hCellRadialTumor`），50 bins r ∈ [0,5] μm

**改动 3**：SteppingAction 计算局部坐标
- 修改：[src/SteppingAction.cc](../src/SteppingAction.cc) `UserSteppingAction`
- 新增：在 `cellID > 0` 时计算 `cellLocalPos = prePoint global pos − cell center`（依赖所有 cell placement rotation = nullptr，已验证）
- 在已有 `inTumorCell` / `cellID > 0` 分支里 fill H2/H1

> 上述改动均不依赖 StepTree（不增加 ROOT 写入开销）。

---

## 3. 对照实验设计

统一基准：mixed patch 200³ μm³、pitch 12 μm、4096 细胞（2048 tumor + 2048 normal）、中子束斑 150 μm、**每点 3 个独立随机种子**用于误差条。

### 实验 A — Shell vs Uniform（核心，H1）

| 组 | boronMode | uniform 等效 ppm | 实际 ppm | events |
|---|---|---|---|---|
| A1 | uniform | 300000 | 300000 | 1M × 3 seeds |
| A2 | shell | 300000 | 614550（=300k × 2.049）| 1M × 3 seeds |
| A0 | none | 0 | 0 | 1M × 3 seeds |

**为何不取 100/1000 ppm 双量级**：原计划在 100 ppm + 1000 ppm 两个量级各跑一遍。但 §2.2 物理上限限制 uniform_equiv ≤ 488000，且低 ppm 反应率不足（100 ppm × 200k events ≈ 0.3 反应）。最终采用单个高浓度（300k ppm）+ 3 seeds 误差条。

### 实验 B — 跨疗法等剂量对照（H2）

统一肿瘤细胞平均剂量到 ~2 Gy 后比较 normal 细胞副损伤：

| 组 | 粒子 | 能量 | 备注 |
|---|---|---|---|
| B1 | gamma | 1 MeV | events 调到 D_tumor_cell ≈ 2 Gy |
| B2 | proton | 80 MeV | 同上 |
| B3 | neutron + uniform 300k ppm | 0.5 eV | 同上 |
| B4 | neutron + shell（等效 300k ppm）| 0.5 eV | 同上 |

**处方剂量归一化**：第一轮跑 200k events 探针，从 CellTree 读 D_tumor 平均值，按 D_target / D_tumor 线性外推所需 events，cap 在 2M events 上限内（避免单跑次过长）。同时输出未归一化原始结果作为附录。

### 实验 C — B10 总量扫描（H3）

扫描 uniform 等效 ppm ∈ {30000, 100000, 200000, 300000}，每点同时跑 uniform 与 shell（shell 用 2.049×），events 固定 500k。关注 shell/uniform 优势比随 ppm 的趋势。

### 实验 D — 中子注量扫描（H4，复用）

保留现有 [scripts/run_q2_neutron_fluence_scan.sh](../scripts/run_q2_neutron_fluence_scan.sh) 产出的 `output_problem2_bnct_<mode>_fluence_<n>events.root` 系列（旧版 500k ppm × 7 个注量点），只需在绘图阶段叠加 S(events) 曲线。不重跑模拟。

---

## 4. 需要画的图

| ID | 图 | 假设 | 布局 |
|---|---|---|---|
| F1 | B10 分布几何示意（保留旧图）| 几何理解 | `Q2_boron_distribution_cell_model.png` 不变 |
| **F2** | **Shell vs Uniform 主结论图** | **H1** | (a) tumor/normal 核剂量分组柱状 + 误差条；(b) LQ 存活率柱状（4 组）；(c) lethal-hit fraction 柱状；(d) α+Li7 核击中数柱状 |
| **F3'** | **单细胞叠加剂量分布图（本计划新增）** | **H1 机制** | **顶行：3 张 (r_xy, z_local) 2D 热图**（normal / tumor uniform / tumor shell），共享色标；**底行：3 张 1D 径向 dose vs r 曲线**，每张对应顶行同列细胞类型，纵轴 dose density [Gy/μm³]，横轴 r ∈ [0,5] μm；shell 列预期在 r∈[4,5] μm 出现峰 |
| **F4** | **跨疗法等剂量对照图** | **H2** | (a) 4 疗法 normal vs tumor 核剂量分组柱状；(b) **normal cell S 值柱状（重点）**；(c) 治疗指数 TI = K_tumor/K_normal；(d) tumor 核剂量 CDF |
| F5 | B10 总量扫描 | H3 | (a) 肿瘤核剂量 vs ppm（uniform/shell 双线，log-log）；(b) shell/uniform 优势比 vs ppm；(c) 存活率 vs ppm 分 tumor/normal |
| F6 | 中子注量扫描（复用旧 §4.6 图 13）| H4 | 不变 |
| F7 | 微区 (x,z) 剂量热图（复用旧 §4.4 图 11）| 空间选择性 | 不变 |

### 4.1 F3' 实现细节

**数据源**：H2 `hCellLocal_*` 与 H1 `hCellRadial_*` 直接从 ROOT 读出；按 `boronMode` 文件名区分 uniform / shell 跑次。

**归一化**：
- 2D 热图：每 bin 的 edep / (该类细胞数 × bin 体积 2πr·Δr·Δz) → dose density
- 1D 径向：每 r-bin edep / (该类细胞数 × 4πr²·Δr) → dose density，**必须做 4πr² 反卷**，否则会看到伪上升

**三列对齐**：normal/tumor-uniform/tumor-shell 三列共享色标和 r 轴范围；shell 列预期峰位 r ∈ [4, 4.95] μm，uniform 列预期平台 + r→0 缓慢下降。

**叠加合法性**：[src/CellModel.cc:120,177](../src/CellModel.cc) 所有 PVPlacement rotation=nullptr，所有细胞同向 → 局部坐标叠加合法；若以后引入旋转，叠加会破坏各向异性，但径向 1D 仍合法。

### 4.2 Geant4 端输出压力评估

- H2：50×50×2 类 ≈ 5000 doubles ≈ 40 KB，无显著开销
- H1：50×2 类 ≈ 100 doubles，可忽略
- 每 step 新增工作：1 次 `prePoint - cellCenter`（GetCellCenter 是 map 查找）+ 2 次 FillH → 远小于现有 5 次 `TouchableContains` 字符串搜索的开销
- 不开 StepTree，每 step 工作仍是 O(1)；**输出压力可控**

---

## 5. 实施顺序

1. **代码改动**（按 §2.4）→ 重新构建 → 烟雾测试 ROOT 文件结构
2. **写新宏与扫描脚本**：
   - 新建 `scripts/run_q2A_main.sh`（实验 A，9 跑次）
   - 新建 `scripts/run_q2C_ppm_scan.sh`（实验 C，8 跑次）
   - 新建 `scripts/run_q2B_equal_dose.sh`（实验 B 探针 + 等剂量正式）
   - 输出新文件名 `output_q2[ABC]_*.root` 区分新旧数据
3. **改写 [scripts/plot_assignment_results.py](../scripts/plot_assignment_results.py) 的 Q2 段**：
   - 扩展 `read_cell_rows` 解析新增 6 列
   - 新增 `read_h2` 辅助
   - 实现 LQ 存活计算与 lethal-hit 后处理函数（`equiv_dose_gy`, `survival_lq`, `lethal_hit`, `cell_summary`）
   - 实现 F2、F3'、F4、F5 四张新图
4. **更新报告** [G4sim_reporter.md](../G4sim_reporter.md) 第 4 节：按 H1–H4 重写，删除/修正"shell 不如 uniform"结论

---

## 6. 验证方法

**代码改动验证**：
- 跑 [macros/problem2_bnct_uniform.mac](../macros/problem2_bnct_uniform.mac)（events=2000 探针）→ 检查 ROOT 文件含 H2 `hCellLocal_normal`/`hCellLocal_tumor`、CellTree 多出 6 列、值非负且总和 ≈ 原 `edepNucleus_MeV`
- 在 ROOT TBrowser 中目视 H2：normal 细胞应是 r→0 单调下降、tumor uniform 类似但更高、tumor shell 在外环亮

**实验设计验证**：
- 实验 A：A2（shell 614k ppm）α+Li7 数应 ≈ A1（uniform 300k ppm）（同总原子数 → 同反应数）；预期 A2 肿瘤核剂量 > A1（但实测发现相反，详见 §8 实测结果）
- 实验 B：四组 D_tumor_cell 在归一化后差异 < 10%（说明探针外推成功）；B3/B4 的 D_normal_cell 应 ≪ B1/B2
- F3'：shell 列 1D 谱在 r∈[4,5] μm 应出现局部峰；uniform 列在 r ∈ [0,5] 应近似平台（叠加 ~2048 个细胞统计应足够）

**端到端运行**：
```bash
cd /home/yoru/learning/ucas_course/detector_sim/7th/Geant4TumorTherapySim
cmake --build build -j
EVENTS_MAIN=1000000 JOBS=12 bash scripts/run_q2A_main.sh         # 实验 A，~50 min
EVENTS_SCAN=500000 JOBS=12 bash scripts/run_q2C_ppm_scan.sh      # 实验 C，~25 min
JOBS=12 PROBE_EVENTS=200000 bash scripts/run_q2B_equal_dose.sh   # 实验 B，~2 h（包括探针）
python scripts/plot_assignment_results.py --section q2new
```

预期产物：
- `figures/Q2_shell_vs_uniform_main.png`（F2）
- `figures/Q2_singlecell_dose_distribution.png`（F3'）
- `figures/Q2_therapy_equal_dose.png`（F4）
- `figures/Q2_b10_total_scan.png`（F5）

---

## 7. 时间预算

详见 [q2_timing_benchmark.md](q2_timing_benchmark.md)。简要：

- 实测速率：**343 events/s** 单线程（neutron 0.5 eV + 500k ppm shell mode）
- 总事件数：~16M（A 9M + B 3M + C 4M）
- 16 核机器 12 路并行：~75 分钟模拟 + ~10 分钟绘图 = **~75 分钟总挂钟时间**

---

## 8. 实测结果与设计假设的偏差（执行阶段发现）

**主要发现：在当前 cellRadius=5 μm + shellThickness=1 μm 几何下，shell 模式的核内剂量反而低于 uniform**（与作业字面命题 H1 方向相反）：

| 指标（300k ppm × 1M events × 3 seeds 平均）| uniform | shell（等 B10 总量）|
|---|---:|---:|
| 肿瘤细胞核平均剂量 D_nuc | 3.2×10⁻³ Gy | 6.9×10⁻⁴ Gy |
| 核内 alpha+Li7 击中总数 | 6.7 | 2.0 |
| Lethal-hit fraction | 0.0018 | 0.00065 |

**物理解释**：α/Li7 在水中平均射程 ≈ 5-10 μm，但 Bragg 峰能量损失发生在前 1-2 μm。具体：
- **uniform 模式**：B10 均匀填充包括细胞核 → 反应直接在核内发生 → 立即沉积，几乎无衰减进入核
- **shell 模式**：B10 仅在 r ∈ [4, 5] μm 壳层 → 反应产物必须穿越 r ∈ [2.5, 4] μm（约 1.5 μm 厚）的细胞质才能进入核 → 大量能量已沉积在细胞质中（Bragg 峰位于壳层附近）

**F3' 验证机制成立**：shell 列径向 1D 谱在 r ≈ 4 μm 出现明显径向峰（"硼壳热源"），uniform 列径向上单调衰减；shell 的硼分布机制本身是对的，但 α/Li7 短射程让能量无法有效抵达核。

**结论修正**：
- H1 部分成立（径向"硼壳热源"机制 → ✅）部分不成立（核内剂量更高 → ❌）。
- 作业命题成立需要一个隐含条件：α/Li7 路径完全到达细胞核 —— 这对当前 5 μm 细胞 + 1 μm 壳层不成立。
- 若 shell 更接近核（如 shellThickness=2 μm + 核更大），或反应 Q 值更高（产物射程更长），结论可能反转。

这是一个**真实的物理学发现**，依赖具体几何参数选择。报告中需如实给出，并提供物理解释。

---

## 9. 与原始计划文件的对应关系

本文档整理自 [/home/yoru/.claude/plans/2d-dose-vs-r-2d-mutable-matsumoto.md](/home/yoru/.claude/plans/2d-dose-vs-r-2d-mutable-matsumoto.md)，是该计划的精炼/中文版本。原计划中包含 plan-mode 的对话上下文（如 ExitPlanMode 注释），本文件去掉这些只保留实验设计核心。

实施过程中的具体进度与陷阱：
- 当前进度与下一步：[q2_handoff.md](q2_handoff.md)
- 速率/时间/3 个 bash+G4 陷阱：[q2_timing_benchmark.md](q2_timing_benchmark.md)
