# Q2 BNCT 重设计 — 接手文档

**最后更新**：2026-06-12 17:45 CST
**当前 agent 退出后接手用**

## 2026-06-12 两阶段 BNCT 更新

已新增 `/therapy/sourceMode b10Capture` 条件俘获模式。每个 event 在一个肿瘤细胞的 B10 区域内按体积采样一次反应，并输运两个真实分支的 alpha、Li7 和伴随 gamma。该模式只测量 `response/capture`，不能解释为入射中子或绝对注量。

新增产物：

- `output_q2D_capture_{uniform,shell}_seed{1..3}.root`：每组 `100000` 次条件俘获。
- `figures/Q2_forced_capture_main.png`：单位俘获主结论图。
- `figures/Q2_forced_capture_microdose.png`：高统计单细胞高 LET 响应图；二维图按圆柱环 bin 体积、径向谱按球壳体积归一化，并附区域能量积分。
- `figures/Q2_two_stage_b10_scan.png`：真实中子俘获率 × 条件俘获响应。

实测单位俘获结果：

| 指标 | uniform | shell |
|---|---:|---:|
| 核内 alpha+Li7 沉积 | `0.236 MeV/capture` | `0.0782 MeV/capture` |
| 核高 LET 命中概率 | `35.4%` | `17.5%` |
| 初始高 LET 能量进入核内比例 | `10.1%` | `3.34%` |

三个指标的 seed 间变异系数均 `<0.5%`。F5 的真实中子 Li7 统计仍低，联合后 uniform/shell 分别约 `51/52` 个俘获，因此 F5 仅作为线性趋势图。F4 暂缓，现有 q2B final 文件不可用于等剂量结论。

## 0. 任务背景速读（30 秒）

Geant4 肿瘤治疗模拟项目，Q1（gamma/proton 外照射）已完成；Q2（BNCT shell vs uniform B10 分布）此前实验设计与作业目标错位。已完成实验重设计 + 代码改动 + 大部分模拟运行 + 4 张主图中的 3 张。

**作业核心命题**：在相同硼浓度（重定义为"相同 B10 原子总数"）和相同中子注量下，¹⁰B 集中在细胞外壳（1 μm 层）比均匀分布在整细胞内产生更高细胞核剂量和更低存活率，且 BNCT 对正常细胞损伤低于 gamma/proton。

**重设计核心文档**：[/home/yoru/.claude/plans/2d-dose-vs-r-2d-mutable-matsumoto.md](/home/yoru/.claude/plans/2d-dose-vs-r-2d-mutable-matsumoto.md)（实验设计 + 4 张图 F2/F3'/F4/F5）

## 1. 当前进度速览

| 任务 | 状态 | 备注 |
|---|---|---|
| 1. 代码改动 (CellTree 新 6 列 + 2 H2 + 2 H1 + cell-local 坐标) | ✅ 完成 | 已构建并通过烟雾测试 |
| 2. 时间预算文档 [docs/q2_timing_benchmark.md](q2_timing_benchmark.md) | ✅ 完成 | 含 343 ev/s 测速 + 3 个 bash/G4 陷阱说明 |
| 3. 实验 A 跑次（q2A，1M events × 9）| ✅ 完成 | 输出 `output_q2A_<mode>_300000ppm_seed<1-3>.root` |
| 4. 实验 C 跑次（q2C，500k events × 8）| ✅ 完成 | 输出 `output_q2C_<mode>_<ppm>ppm.root` |
| 5. 实验 B 跑次（q2B，2M events × 4 final）| 🔄 **进行中** | 4 个 final ~80 分钟剩余；probe 完毕 |
| 6. F2 主结论图（shell vs uniform）| ✅ 完成 | [figures/Q2_shell_vs_uniform_main.png](../figures/Q2_shell_vs_uniform_main.png) |
| 7. F3' 单细胞叠加图（机制证据）| ✅ 完成 | [figures/Q2_singlecell_dose_distribution.png](../figures/Q2_singlecell_dose_distribution.png) |
| 8. F5 B10 总量扫描图 | ⚠️ 完成但数据稀疏 | [figures/Q2_b10_total_scan.png](../figures/Q2_b10_total_scan.png) — 多个 shell 点为 0 |
| 9. F4 跨疗法等剂量对照 | ⏳ 待 q2B 完成 | [scripts/run_q2B_equal_dose.sh](../scripts/run_q2B_equal_dose.sh) |
| 10. 报告 §4 重写 | ✅ 完成 | [G4sim_reporter.md](../G4sim_reporter.md) §4.1-§4.13 |
| 11. 报告数值最终化 | ⏳ 待 F4 完成后更新 | §4.11 中数值需用最终实测值 |

## 2. 关键发现（已记入报告）

**主结论与作业字面预期相反**：在等 B10 原子总数 + cellRadius=5μm + shellThickness=1μm 几何下：
- uniform 模式肿瘤核剂量 = 3.2×10⁻³ Gy
- shell 模式肿瘤核剂量 = 6.9×10⁻⁴ Gy（**仅为 uniform 的 ~22%**）
- 核内 α+Li7 击中：uniform 6.7 vs shell 2.0

**物理解释**：alpha/Li7 为短射程带电粒子，能损通常在射程末端增强，而不是固定发生在路径起始的前 `1–2 um`。shell 模式下反应产物必须穿越约 `1.5 um` 细胞质才能进入核；体积归一化 F3' 显示 shell 在 `r≈4 um` 出现峰，区域积分同时确认细胞质获得约 `0.300 MeV/capture`，但最终进入核的能量仍受方向和射程限制。

详细物理解释见 [G4sim_reporter.md §4.11](../G4sim_reporter.md)。

## 3. 待完成工作

### 3.1 当前正在运行（不要 kill）

```
pid 445208: bash scripts/run_q2B_equal_dose.sh
4 个 ./build/tumor_therapy q2B_*_final.mac 进程 @ 92% CPU
预期完成时间：~18:30 CST（再 45 分钟）
日志：/tmp/q2B.log
```

q2B 完成判定：
```bash
grep -q "experiment B] done" /tmp/q2B.log && echo "DONE"
```

输出文件：
- `output_q2B_gamma_final.root`（2M events @ 1 MeV gamma）
- `output_q2B_proton_final.root`（2M events @ 80 MeV proton）
- `output_q2B_neutron_uniform_final.root`（2M events @ 0.5 eV neutron + 300k ppm uniform）
- `output_q2B_neutron_shell_final.root`（2M events @ 0.5 eV neutron + 614754 ppm shell）

### 3.2 q2B 完成后立即做

```bash
cd /home/yoru/learning/ucas_course/detector_sim/7th/Geant4TumorTherapySim
source /home/yoru/packages/geant4-11.4.0/bin/geant4.sh >/dev/null 2>&1
export ROOTSYS=/home/yoru/packages/root
export PATH=$ROOTSYS/bin:$PATH
export LD_LIBRARY_PATH=$ROOTSYS/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$ROOTSYS/lib
# 生成 F4
/home/yoru/miniconda3/envs/iris/bin/python -c "
import sys
sys.path.insert(0, 'scripts')
from plot_assignment_results import plot_q2_therapy_equal_dose
plot_q2_therapy_equal_dose()
"
ls -la figures/Q2_therapy_equal_dose.png
```

预期：F4 显示在等肿瘤细胞剂量 (~2 Gy) 下，BNCT uniform/shell 的 normal 细胞存活率 S 应明显高于 gamma/proton（因 normal 细胞不含 B10）→ 支持 H2。

### 3.3 报告数值更新

读 q2B 最终 4 个 ROOT 文件的实际数据，更新 [G4sim_reporter.md §4.11](../G4sim_reporter.md) 中的具体数字（目前 §4.11 的表格用了实测值，但 §4.8 F4 一节为预期描述，需要填实测）。

### 3.4 F5 数据稀疏问题（可选改进）

F5 当前用 q2C 的 500k events × 4 ppm 点 × 2 mode = 8 跑次。结果：
- shell 模式在 30k/100k/200k/300k ppm 中 3 个点核内剂量为 0
- F5 (b) shell/uniform 优势比图大部分为 0，只 200k 点 ~2.0

**修复选项 A**：每点提高到 1M events，重跑 q2C：
```bash
nohup bash -c 'EVENTS_SCAN=1000000 JOBS=12 bash scripts/run_q2C_ppm_scan.sh' > /tmp/q2C_v2.log 2>&1 < /dev/null &
disown
# 预计 ~50 分钟
```

**修复选项 B**：在报告中标注"F5 仅作为 ppm 趋势示意，shell 模式在低 ppm 区因 α/Li7 短射程几乎无核内沉积，与图 F2 一致"。

### 3.5 用户提出的 forceReaction 方案（可选大改进）

用户考虑在 B10 分布点直接强制产生 (n,α)Li7 反应，绕过中子统计稀疏。详见对话最后一轮分析：

- **适用**：F3' 单细胞机制图（强制反应不破坏径向形状判断，提供 1000× 统计量）
- **不适用**：F2 主图（绝对数值会失真）、F4 跨疗法（剂量来源不可比）、F5 ppm 扫描（ppm 是自变量）

代码改动（~50 行）：
- 新增 `/therapy/forceReaction true` 开关
- [src/PrimaryGeneratorAction.cc](../src/PrimaryGeneratorAction.cc) 中：按 boronMode 在 cell 的 B10 几何内随机采样发射点，发射 α (1.47 MeV) + Li7 (0.84 MeV) 背对背对，跳过中子输运
- 时间成本：~1.5 小时（写 + 验证 + 重画 F3'）

如果用户决定做，建议**只为 F3' 升级版**做，保留现有真实中子的 F3' 作为对照。

## 4. 已完成的代码改动（其它 agent 不要再改）

### 4.1 文件清单

修改的文件：
- [include/TherapyAnalysisManager.hh](../include/TherapyAnalysisManager.hh)：CellAccumulator/EventAccumulator 新增按粒子分桶的 nucleus edep + nucleus hit 计数；AddEnergyDeposit 新签名（多 2 参数：cellLocalPosition, hasCellLocal）；GetCellCenter API
- [src/TherapyAnalysisManager.cc](../src/TherapyAnalysisManager.cc)：CellTree 新增 6 列（edepNucleusGamma/Proton/Alpha/Li7_MeV + alphaNucleusHits + liNucleusHits）；CreateObjects 新增 H2 索引 0/1（hCellLocalNormal/Tumor）+ H1 索引 10/11（hCellRadialNormal/Tumor）；EventAccumulator::Reset 重写
- [include/SteppingAction.hh](../include/SteppingAction.hh)：新增 FindCellDepth 声明（未使用，可保留）
- [src/SteppingAction.cc](../src/SteppingAction.cc)：cellLocalPos = prePoint position − cell center（用 TherapyAnalysisManager::GetCellCenter）

### 4.2 关键 bug fix（不要回退）

1. **cell-local 坐标用 `prePoint - cell.info.position`** 而非 `GetTransform(depth).TransformPoint`（后者在 Geant4 11.4 的 NavigationHistory 返回 identity，无效；前者依赖所有 cell placement rotation = nullptr，已验证）
2. **shell ppm 必须 ≤ 1e6**（mass fraction ≤ 1 物理约束）→ uniform_equiv ≤ 488k；当前用 300k
3. **`/random/setSeeds 1 101` 等小种子产生统计偏差** → 改用 8 位质数对（11111111, 98765431 等）
4. **bash `GROUPS=` 是 readonly 内建数组**（用户 GID 列表）→ 改名 `Q2B_GROUPS`
5. **ROOT cling 退出码 255 + `set -euo pipefail`** → 在调用 root 的循环周围 `set +e ... set -e`

### 4.3 文件目录

```
scripts/
├── run_q2A_main.sh        # 实验 A: 1M events × 3 seeds × 3 modes = 9 runs (DONE)
├── run_q2B_equal_dose.sh  # 实验 B: probe + 等剂量正式 (RUNNING, ETA 18:30)
├── run_q2C_ppm_scan.sh    # 实验 C: 500k events × 4 ppm × 2 modes = 8 runs (DONE)
└── plot_assignment_results.py  # 含新函数 plot_q2_shell_vs_uniform_main / plot_q2_singlecell_dose_distribution / plot_q2_therapy_equal_dose / plot_q2_b10_total_scan

macros/
├── problem2_bnct_uniform.mac / shell.mac  # 旧版（500k ppm，不用）
└── smoke_bnct_shell.mac                    # 调试用

results/generated_macros/
└── q2[ABC]_*.mac  # 自动生成

output_q2A_*.root  # 9 files, 53MB each (实验 A 输出)
output_q2C_*.root  # 8 files, 29MB each (实验 C 输出)
output_q2B_*_probe.root  # 4 files (实验 B 探针)
output_q2B_*_final.root  # 4 files (实验 B 等剂量，生成中)

figures/
├── Q2_shell_vs_uniform_main.png       # F2 ✅
├── Q2_singlecell_dose_distribution.png # F3' ✅
├── Q2_b10_total_scan.png              # F5 ⚠️ 数据稀疏
└── Q2_therapy_equal_dose.png          # F4 待生成
```

## 5. 接手 agent 的下一步任务清单

按优先级排序：

### 必做

1. **等 q2B 完成**（自动检测）：
   ```bash
   until grep -q "experiment B] done" /tmp/q2B.log; do sleep 30; done
   ```

2. **生成 F4**（命令见 §3.2）

3. **更新报告**：读 q2B 实测值，把 [G4sim_reporter.md §4.8](../G4sim_reporter.md) 中"F4 预期支持 H2"段落改为实测描述。具体读法：
   ```python
   import sys; sys.path.insert(0, 'scripts')
   from plot_assignment_results import cell_summary, read_cell_rows
   for name in ['gamma', 'proton', 'neutron_uniform', 'neutron_shell']:
       rows = read_cell_rows(f'output_q2B_{name}_final.root')
       s = cell_summary(rows)
       print(name, 'D_tumor_cell=', s['tumor']['mean_dose_cell'],
             'D_normal_cell=', s['normal']['mean_dose_cell'],
             'S_normal=', s['normal']['mean_S'])
   ```

4. **生成全套图**（最后一次性运行）：
   ```bash
   /home/yoru/miniconda3/envs/iris/bin/python scripts/plot_assignment_results.py --section q2new
   ```

### 可选

5. **F5 补统计**（§3.4 选项 A）：q2C 重跑 1M events × 4 ppm × 2 mode，~50 分钟
6. **forceReaction for F3'**（§3.5）：需用户确认；~1.5 小时

### 提交

7. **Git commit 前 read [G4sim_reporter.md](../G4sim_reporter.md) §4 全文并校对**：确保 §4.6/§4.7/§4.8 描述与 F2/F3'/F4 实际图内容一致。

8. **Git commit** 用户没要求时不要 commit；要求时按现有 commit 风格（git log）写信息。

## 6. 已知陷阱（别再踩）

1. `pgrep -f "tumor_therapy.*q2X"` 会 match 自己 → chain 脚本永远不退出。用 `pgrep -f '\./build/tumor_therapy.*q2X'` 配 `ps -ef | grep '\./build/tumor_therapy'` 替代
2. PyROOT 在 9 × 4096 cell × 21 cols 遍历约 90 秒；plotting 函数已优化但仍较慢，**别频繁重跑**
3. PyROOT `import ROOT` 第一次会输出 `ERROR in cling::CIFactory::createCI`，**正常**，可忽略
4. `set -euo pipefail` 下任何 root 命令在 pipe 里都可能因 cling exit 255 杀死 shell；用 `set +e ... set -e` 包围
5. 当前所有 macros 里的 `/random/setSeeds` 必须放在 `/run/initialize` 之前

## 7. 联系信息 + 状态文件

- 计划文件：[/home/yoru/.claude/plans/2d-dose-vs-r-2d-mutable-matsumoto.md](/home/yoru/.claude/plans/2d-dose-vs-r-2d-mutable-matsumoto.md)
- 时间预算 + bug 记录：[docs/q2_timing_benchmark.md](q2_timing_benchmark.md)
- 报告（最终交付）：[G4sim_reporter.md](../G4sim_reporter.md)
- q2B 实时日志：`/tmp/q2B.log`（监控 q2B 进度用）
- 旧版报告（参考用）：git log → `e8a9c3d` 是上一版 commit

## 8. 用户偏好（从对话观察）

- 中文报告、中文沟通
- 不要在没要求时改 PROJECT.md/README.md/CLAUDE.md
- 严谨学术风格，**实测结果与字面预期不符时如实写出 + 给物理解释**，不要为了符合作业表面预期硬凑
- 报告数据要标注**实测值**而非"预期"或"应该"
- 接受"机制成立但临床预期不符合直觉"的结论
- 时间紧张，每步给"是否继续/选哪个方案"以便快速决策
