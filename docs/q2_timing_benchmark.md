# Q2 BNCT 模拟时间预算与统计量需求

本文档记录 Q2 重设计实验的事例数、反应数、单跑次时间和并行预算的实测与外推数据，供 [G4sim_reporter.md](../G4sim_reporter.md) 第 4 节、第 5 节引用。

## 1. 测速基准（实测）

**测试机器**：AMD Ryzen 9 8945HS（16 核），15 GiB RAM，WSL2 Linux 6.6。

**测试运行**：[macros/smoke_bnct_shell.mac](../macros/smoke_bnct_shell.mac)，`boronMode=shell`、`boronPPM=500000`、`beamRadius=150 um`、热中子 `0.5 eV`、events = 50000，单线程。

**结果**：
```
real    2m26.948s
user    2m25.369s
sys     0m0.914s
```
→ **343 events/s**（单线程）。

> 基准物理列表 `QGSP_BIC_HP`，含 HP 中子段；同一基准下 uniform 模式与 shell 模式的事例时间差异 < 5%（中子输运几乎相同，BNCT 反应数本身只占总 step 数的 ~1%）。`gamma 1 MeV` 与 `proton 80 MeV` 在 mixed cell patch 内事例时间约为中子组的 0.6–1.2 倍，预算估算时取 1.0× 即可。

## 2. 反应率经验估算

来自现有 200k events 跑次的 α+Li7 计数（[output_problem2_bnct_uniform_fluence_200000events.root](../output_problem2_bnct_uniform_fluence_200000events.root) / [...shell.root](../output_problem2_bnct_shell_fluence_200000events.root)）：

| 模式 | ppm | events | α+Li7 数 | reactions/event |
|---|---:|---:|---:|---:|
| uniform | 500000 | 200k | 1495 | 7.5×10⁻³ |
| shell（等 ppm，旧实现）| 500000 | 200k | 829 | 4.1×10⁻³ |

旧 shell 反应数较少是因为"等 ppm"使 shell 总 B10 原子数仅为 uniform 的 ~49%；改为"等 B10 原子总数"（shell ppm = uniform ppm × 2.049）后两者反应率近似相等。

**外推**（线性 ∝ B10 总原子数 ∝ uniform 等效 ppm）：
```
reactions/event ≈ 1.5 × 10⁻⁸ × ppm_uniform_equiv
```

| ppm (uniform 等效) | reactions/200k | reactions/1M | 适用图 |
|---:|---:|---:|---|
| 100 | 0.3 | 1.5 | 不可用 |
| 1000 | 3 | 15 | 仅趋势 |
| 10000 | 30 | 150 | F5 边缘 |
| 100000 | 300 | 1500 | F5/F2 |
| 300000 | 900 | 4500 | F2/F3' 边缘 |
| 500000 | 1500 | 7500 | F2/F3' 主图 |

## 3. F3' 单细胞叠加图统计需求

H2 维度：50 (r) × 50 (z) = 2500 bins；shell 模式有效 bins 仅 r∈[4,5] μm × 全 z ≈ 250 bins。  
要求每有效 bin ≥ 10 次沉积事件 → 约 **2500 反应/跑次** → 对应 **1M events @ 500k ppm**。

## 4. 实施预算（方案 A，最终采纳）

主图取 500k ppm 是因为它是当前唯一能稳定填出 F3'（单细胞叠加 2D+1D）有效 bins 的浓度量级；F5 在 30k–500k ppm 区间扫描以展示"shell 优势随 ppm 单调"的趋势。

| 实验 | 配置 | 跑次数 | events/跑 | 总 events |
|---|---|---:|---:|---:|
| F2/F3' 主图 | 500k ppm × {uniform, shell, none} × 3 seeds | 9 | 1M | 9M |
| F5 ppm 扫描 | {30k, 100k, 300k, 500k} ppm × {uniform, shell} × 1 seed | 8 | 500k | 4M |
| F4 等剂量对照 | {γ 1MeV, p 80MeV, BNCT uniform 500k, BNCT shell 500k} | 4 | 200k探针 + 等剂量正式 | ~3M |
| F6 注量扫描 | 沿用现有产物（无新跑次） | 0 | — | 0 |
| **合计** | | **21** | | **~16M** |

### 时间外推

按 343 ev/s 单线程：
```
T_serial = 16M / 343 ≈ 13 h
```
现有调度脚本 [scripts/run_q2_workflow.sh](../scripts/run_q2_workflow.sh) 用 `xargs -P "$Q2_JOBS"` 串行各跑次的并行；本机 16 核可设 `Q2_JOBS=12`（留 4 核给 OS/绘图）：
```
T_parallel(12) ≈ 13 h / 12 ≈ 65 min
```
扣除 cmake 配置/重建与绘图开销（~10 min），**总挂钟时间预期 ~75 分钟**。

## 5. 记录到报告的关键数字

报告第 4/5 节引用本文件时使用的精炼版表述：

> 本次 Q2 重运行总事例数约 16M（主图 9M、ppm 扫描 4M、等剂量对照 3M）。在 16 核机器上以 12 路并行运行，单跑次速率 343 events/s（实测，热中子 + 500000 ppm shell 模式），整体挂钟时间约 75 分钟，包含约 65 分钟的 Geant4 模拟和约 10 分钟的 ROOT 后处理与绘图。

---
*Generated: 2026-06-12 — based on 50k-events shell smoke test (output_smoke_bnct_shell.root).*

## 6. 实施过程中遇到的两个事实修正

### 6.1 "等总硼"约束限制了 uniform_equiv 上限

理论：`shell_ppm = uniform_ppm × V_cell / V_shell ≈ 2.049 × uniform_ppm`。Geant4 `G4Material::AddElementByMassFraction` 要求质量分数 ≤ 1，因此 `shell_ppm ≤ 1e6 ppm` → `uniform_equiv ≤ 488000 ppm`。原计划 §1.2 的 `500000 ppm` 不可达。

**最终采用 uniform_equiv = 300000 ppm**（shell_ppm ≈ 614550, ~61% 质量分数），仍偏离临床真实低 ppm 但保留物理合法性，且反应率充足（reactions/event ≈ 4.5×10⁻³）。

### 6.2 `/random/setSeeds` 必须使用大种子

Geant4 默认 RNG 在小种子（如 `1, 101`）下产生的早期 sequence 段会让 BNCT 反应数明显偏低（实测：`(1,101)` 50k events → 0 cells；`(31415927, 27182818)` 50k events → 1 cell）。

**采用的种子集**：
| seed_idx | seed1 | seed2 |
|---|---:|---:|
| 1 | 11111111 | 98765431 |
| 2 | 22222223 | 87654319 |
| 3 | 33333335 | 76543207 |

宏中 `/random/setSeeds` 必须放在 `/run/initialize` 之前（参数才能被 RunManager 在 BeginRun 之前应用）。

### 6.3 Bash 脚本陷阱

- `GROUPS` 是 bash 内建只读数组（用户所属 GID 列表），不能用作普通变量。Q2B 脚本使用了 `GROUPS=(...)` → bash 静默忽略 → 后续循环看到的是用户的 GID 列表（12 个数字），导致每组 spec 解析失败。修复：改名为 `Q2B_GROUPS`。
- ROOT v6 在 cling pre-flight 时可能报告 "cannot extract standard library include paths" 并退出码 255；用 `set -euo pipefail` 时这会通过 pipe 杀掉脚本。修复：在调用 `root -l ... | tail -1` 的循环周围加 `set +e ... set -e`。


