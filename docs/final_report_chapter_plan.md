# 最终实验报告重构施工图（Chapter Plan）

> 来源：ARS `academic-paper` plan 模式产出。
> 目标对象：`final_report.md`（当前为分点式实验记录，目标为 IMRaD 学术风格课程实验报告）。
> 性质：**课程实验报告**——学术形式，机制性验证，定性方向论证，不苛求严格定量证明。

---

## 0. 文档定位与成功标准

| 维度 | 设定 |
|---|---|
| 文档性质 | 课程实验报告（非严格学术论文） |
| 论证强度 | 机制性验证（mechanism verification），证明大方向，不需严苛定量证明 |
| 引用密度 | 自包含（option A）：物理机制用经典公式自述，不强制文献溯源 |
| 成功标准 | 读者读完后理解：研究背景、研究问题、研究方案、研究结论；整体研究逻辑与方案自洽 |

---

## 1. INSIGHT Collection（已与用户确认）

**[INSIGHT: thesis_statement]**
本报告在同一多尺度 Geant4 模型中验证两类放疗选择性机制的物理图像：
- **实验一（宏观区）**：伽马与质子的优劣差异源于质子 Bragg peak 带来的宏观空间选择性（能量匹配肿瘤深度）；伽马无此机制而弥散沉积。
- **实验二（细胞尺度 BNCT）**：热中子 BNCT 的细胞尺度选择性来自 $^{10}\mathrm{B}$ 富集 × $\alpha$/$^{7}\mathrm{Li}$ 短射程；亚细胞 $^{10}\mathrm{B}$ 分布（均匀 vs shell）通过"反应位点到核的距离 × 产物射程"的几何机制非单调调控核内剂量。

**[INSIGHT: contribution_claim]**（从论点反射，待用户最终确认措辞）
本报告的贡献在于：在一个统一可执行程序内，以机制层面（而非定量层面）对照验证"宏观空间选择性"（质子 Bragg peak）与"微观细胞尺度选择性"（BNCT 双靶）两条正交的剂量优化维度；并定量呈现亚细胞硼分布对核内剂量的几何调控图像，以及离散微米几何中方差缩减失效的诚实负结果。

**[DECISION A]** Introduction 纯物理动机，不提临床。
**[DECISION B]** Theory §2.5 写成"诚实方法学反思"。
**[DECISION C]** occurrence bias 保留"诚实披露为探索性 estimator"口径。

---

## 2. 论点压力测试（Step 3）

对核心论点做反论压力测试，确认其鲁棒性来源——**论点依赖定性机制图像，不依赖定量数值**：

| 反论攻击 | 鲁棒性来源（为何不倒） |
|---|---|
| "浓度非物理（30 万 ppm），选择性数值不可信" | RQ2 结论是**定性机制**（硼富集 × 短射程 → 细胞选择性；shell 几何 → 核剂量更低），机制不依赖绝对浓度；浓度仅放大信号 |
| "occurrence-bias estimator 未通过倍率独立性验证" | BNCT 细胞选择性结论由**条件俘获实验 D**（独立于 bias、3 seed 稳定）支撑；biased estimator 仅作探索性展示，不载结论 |
| "假设正常细胞零硼，高估选择性" | 报告已诚实声明为理想化设定；机制结论（"BNCT 区分肿瘤/正常"）在零硼极端下成立，真实本底只会降低数值、不改方向 |
| "纯水 phantom 不真实" | 不影响两类选择性机制的物理图像（Bragg peak 位置、α/Li 射程、中子输运衰减方向） |

> 结论：四个主要攻击都因"论点是机制图像而非数值"而化解。**Discussion §5.4 必须显式写出这一鲁棒性论证。**

---

## 3. 章节蓝图与字数预估

总目标：约 11000 字（现报告约 6500 字，新增 Theory + Discussion + Introduction 约 4500 字）。

### Ch.1 Introduction（新增，约 900 字）
- 1.1 放疗核心矛盾：杀肿瘤 vs 保护正常组织 = 剂量空间/细胞选择性问题
- 1.2 三类机制物理定位：伽马（电磁、弥散）、质子（Bragg peak、宏观可控）、BNCT（化学靶向 × 短射程、微观可控）
- 1.3 两个研究问题（RQ1 宏观 / RQ2 细胞）
- 1.4 工作概述：统一 Geant4 平台 + 五组 BNCT 实验
- 纯物理动机，**不提临床**（DECISION A）

### Ch.2 Theory / 物理机制（新增，约 1800 字，**核心改造**）
五子节，每节公式 + "解释报告中哪个现象"一句：

| 子节 | 核心公式/数值 | 解释的现象 |
|---|---|---|
| 2.1 带电粒子能量损失与 Bragg peak | Bethe-Bloch $-\frac{dE}{dx}\propto\frac{z^2}{\beta^2}\ln(\dots)$；β→0 发散成峰；CSDA 射程 | §4 质子深度剂量、$f_{\text{tumor}}$ 单峰、峰后急速截止 |
| 2.2 光子相互作用 | 注量指数衰减 $I=I_0 e^{-\mu x}$；次级电子级联；无射程 | §4 伽马弥散无峰、$f_{\text{tumor}}\approx5\%$–$9\%$ 平台 |
| 2.3 $^{10}\mathrm{B}(n,\alpha)^{7}\mathrm{Li}$ 与产物射程 | Q 值 + 分支比；**CSDA（水中）：α(1.47MeV)≈8μm，α(1.78MeV)≈10μm，$^{7}\mathrm{Li}$(0.84MeV)≈4μm，$^{7}\mathrm{Li}$(1.01MeV)≈4.5μm**；两产物背对背合计可达~12μm | 全文"单细胞杀伤"物理基础（最关键的一个数） |
| 2.4 BNCT 双靶选择性 + 几何模型 | 化学靶向 × 物理靶向；各向同性发射 + 立体角 + 穿越胞质损耗 | §5.7 shell/uniform 核剂量 ≈ 0.33 |
| 2.5 中子输运 + 方差缩减 | 散射平均自由程 λ=1/Σ；氢慢化；$w\to w/f$ 无偏条件 | §5.8 到达率随深度衰减；§5.6 estimator 失效（**诚实反思**，DECISION B） |

**Theory 章应写公式清单**（落笔时直接用）：
1. Bethe-Bloch 完整形式（含对数项）
2. 光子注量衰减 $I(x)=I_0 e^{-\mu x}$
3. $^{10}\mathrm{B}+n\to\alpha+^{7}\mathrm{Li}$（94%/6% 两分支能量）
4. α 与 $^{7}\mathrm{Li}$ 在水中 CSDA 射程（**已复核**：α(1.47MeV)≈8μm / α(1.78MeV)≈10μm 来自 NIST ASTAR；$^{7}\mathrm{Li}$(0.84MeV)≈4μm / $^{7}\mathrm{Li}$(1.01MeV)≈4.5μm 来自 SRIM/ICRU 73 + Dartz et al. 2024；Gschwind APL 2024 印证）
5. 剂量选择性 $S_{\text{cell}},S_{\text{nucleus}},S_{\text{therapy}}$（已在 §3.4）
6. 单位俘获响应 $R_{\text{high-LET}},P_{\text{hit,nuc}}$（已在 §3.4）
7. 加权重建 $E_{\text{dep,w}}=\sum w_i E_i$，$N_{^{7}\mathrm{Li},w}=\sum w_i$（已在 §3.5）
8. 中子平均自由程 $\lambda=1/\Sigma_t$，到达概率近似 $P\sim e^{-\Sigma_t d}$
9. occurrence bias 权重补偿关系 $w\to w/\text{factor}$

### Ch.3 Methods（重组现有，约 1500 字）
- 3.1 几何与材料（phantom + 细胞 patch，合并现 §4.2 + §5.2）
- 3.2 物理列表 `QGSP_BIC_HP` 与截面
- 3.3 源、束流、**Notation**（现 §3"变量约定"章降级并入）
- 3.4 计分口径（剂量、LET、选择性、单位俘获响应）
- 3.5 方差缩减实现（occurrence bias + 条件俘获两种工程手段）
- 3.6 实验设计（实验 A–E 设计动机）

### Ch.4 Results（保留数值 + 追加机制解释段，约 4500 字）
**关键改造**：每张图后由"数值是多少"升级为"数值是多少 + 物理上为何是这个值"。机制解释段映射见 §4 证据映射表。

### Ch.5 Discussion（新增，约 1800 字，**核心改造**）
- 5.1 两条正交选择性维度（质子=宏观可控；BNCT=微观选择性；伽马皆弱）
- 5.2 单位俘获响应如何机制性连接细胞剂量（$R_{\text{high-LET}}\times$束流俘获数，D↔B）
- 5.3 shell 为何弱于 uniform（几何参数 × 产物射程，非"shell 更差"）
- 5.4 局限性与机制鲁棒性（§2 压力测试表，说明为何局限不推翻机制结论）

### Ch.6 Conclusion（精简现 §6，约 600 字）
一句话论点 + 两个机制结论 + 后续方向。

---

## 4. 证据 → 论点映射表（Results 章构造核心）

### RQ1（实验一，宏观区）

| 图 / 结果 | 支撑论点 | 机制解释段（Theory 引用） |
|---|---|---|
| Q1_body_tumor_xz_section | 几何定义 | — |
| Q1_depth_dose | 质子有 Bragg peak 落于肿瘤；伽马弥散 | §2.1, §2.2 |
| Q1_dose_heatmap | 质子高沉积区贴肿瘤；伽马长柱弥散 | §2.1, §2.2 |
| Q1_gamma_energy_scan + heatmap | 伽马能量扫描只改穿透深度，无局部最优 | §2.2（指数衰减，无射程） |
| Q1_proton_energy_scan + heatmap | 质子扫描移动 Bragg peak；$f_{\text{tumor}}$ 单峰 85 MeV | §2.1（射程-能量） |
| Q1_let_spectra | 质子 LET 尾部更长 | §2.1（低能高 $dE/dx$） |
| Q1_region_dose_comparison | 宏观剂量量级（质量归一，辅助） | §2.1/§2.2 |

### RQ2（实验二，细胞尺度）

| 图 / 结果 | 支撑论点 | 机制解释段（Theory 引用） |
|---|---|---|
| F1_b10_distribution_geometry | 分布模式定义 | §2.4 |
| Q2_geometry_mixed_cell_layout | 细胞 patch 布局 | §2.4 |
| F2_forced_capture_quantitative（实验 D） | 单位俘获响应；shell/uniform 核剂量 ≈ 0.33 | §2.3（CSDA）, §2.4（几何） |
| F3_forced_capture_singlecell_distribution（实验 D） | 径向谱；shell 峰 r≈4μm 但核内低 | §2.3, §2.4 |
| F4_therapy_comparison_projected_maps（实验 B） | BNCT $S_{\text{therapy}}\approx0.93$ vs 伽马/质子 ≈ 0.5 | §2.4（双靶选择性）；伽马/质子无细胞区分 |
| Q2_biased_ppm_scan + projected_maps（实验 C） | estimator 不独立（负结果） | §2.5（方差缩减失效） |
| Q2_tumor_depth_scan + projected_maps（实验 E） | 到达率随深度衰减 | §2.5（中子输运，λ） |
| 实验 A（无图） | 无偏基准，支撑 §2.5 验证 | §2.5 |

---

## 5. 重写施工序列（final_report.md 改造步骤）

> 建议按此顺序逐节改造，每步完成后该节即"论文级"。

1. **建新骨架**：`final_report.md` 顶部重排为 Ch.1–6 六章标题。
2. **迁移 Methods**：现 §3"变量约定" → Ch.3 §3.3 Notation；现 §4.3 + §5.2 + §5.3 合并 → Ch.3。
3. **迁移 Results**：现 §4 → Ch.4 §4.1（实验一）；现 §5.4–5.8 → Ch.4 §4.2（实验二，保留实验 A–E 子节）。
4. **追加机制解释段**：按 §4 证据映射表，给每张图后补 1 段"物理上为何如此"（引用对应 Theory 子节）。
5. **写 Introduction**（Ch.1，新）。
6. **写 Theory**（Ch.2，新）——直接用 §3 的公式清单。
7. **写 Discussion**（Ch.5，新）——含 §2 压力测试表作为 §5.4。
8. **精简 Conclusion**（Ch.6）。
9. **全文审计**：删除所有"仅描述数值趋势"的孤立句；确认每个数值结论都有机制段支撑。

---

## 6. 待用户最终确认的开放项

- **[INSIGHT: contribution_claim]** 措辞（§1 已给出反射版本，用户可在落笔时定稿）。
- ~~Theory §2.3 的 CSDA 射程数值复核~~ ✅ 已完成（见 §2.3）：α(1.47MeV)≈8μm、$^{7}\mathrm{Li}$(0.84MeV)≈4μm。来源 NIST ASTAR + SRIM/ICRU 73 + Dartz et al. 2024（PMID 38964312）+ Gschwind APL 2024。

---

## 7. 下一步

施工图即施工依据。可：
- **直接施工**：按 §5 序列重写 `final_report.md`（建议分 2–3 轮交付：Ch.1+2 → Ch.3+4 → Ch.5+6）；
- 或先用 `ars-outline` 产出更细的逐段 outline 再施工；
- 或用 `ars-reviewer` 对本施工图做一次模拟评审后再施工。
