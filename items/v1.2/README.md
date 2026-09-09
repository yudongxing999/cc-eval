# CC-Eval V1.2 题库（三 Bench 榜单增量）

生成时间：2026-09-07 ｜ 生成器：`../gen_bench_items.py`（随机种子 20260907，可复现）
定位：对接《国际中文教育大模型测评榜单建设规划》（梁远远）的 TeacherBench / LearnerBench /
ResearchBench 三专项模块，补齐 CC-Eval v1.1 未覆盖、本地数据资产可支撑的 8 个二级维度。
维度匹配全景见 `report/三Bench维度匹配矩阵.md`。

## 构成（186 题，ID 段 CCE-PED-8-0001~0186，level=8 为榜单专项专用段）

| 子任务 | 题量 | 评分器 | 覆盖榜单维度 | 数据锚点 |
|---|---:|---|---|---|
| tb.explain 知识讲解 | 60 | llm_rubric（准确性/等级适配/易懂性） | TeacherBench-T2 | GF0025 词汇 30 + 语法 30（每级各 10） |
| tb.objective 教学目标设计 | 20 | llm_rubric（合理性/层次性/可实现性） | TeacherBench-T3 | 职业中文标准 10 + 文化框架 10 |
| tb.activity 课堂活动设计 | 20 | llm_rubric（交际性/参与度/可操作性） | TeacherBench-T5 | GF0025 语法点 1-4 级 × 三学段 |
| tb.exercise 练习生成 | 20 | llm_rubric（有效性/等级适配/规范性） | TeacherBench-T10 + LearnerBench-L9 | GF0025 语法点 2-5 级 |
| rb.litsearch 文献检索 | 6 | set_overlap（`score_litsearch`，命中/min(3,金标数)） | ResearchBench-R3 | `report/lit/` 6 主题组真实检索记录 |
| rb.understand 文献理解 | 20 | llm_rubric（准确性/完整性/概括力） | ResearchBench-R4 | 38 条真实文献摘要 |
| rb.review 论文评审 | 20 | exact_match（6 类方法学缺陷判类） | ResearchBench-R11 | 真实摘要 + 注入缺陷 |
| rb.authenticity 学术真实性 | 20 | exact_match（1 真 3 假判真伪） | ResearchBench-R12 | 38 条真实文献记录 |

评分器分布：llm_rubric 140 / exact_match 40 / set_overlap（专用实现）6。
contamination_risk：gf0025 锚定题 mid，lit 锚定题与生成题 low。

## 设计要点

1. **rb.authenticity 是幻觉高区分度题**：3 篇编造文献由模板生成（标题模式化、作者/年份随机填），
   真实文献来自实际检索记录——模型只有真见过该文献才能答对，编造答案恰好暴露幻觉倾向；
   4 个选项位置已随机化（A/B/C/D 分布 4/6/7/3），无位置偏差。
2. **rb.review 的缺陷是出题方注入的**：题面描述缺陷情境，金标为 6 类缺陷之一
   （样本偏差/因果混淆/测量循环/基线缺失/泛化过度/统计不充分）。缺陷类别按随机指派，
   同一摘要可能配不同缺陷情境，考的是「方法学缺陷类型学」而非该论文真实存在的问题。
3. **tb.explain 按 GF0025 等级分层**：1-6 级每级 5 词 + 5 语法点，量表评「等级适配性」，
   与 GEN 限级改写形成「判别—生成」互补：GEN 测硬约束，tb.explain 测讲解的因材施教。
4. **ID 段位约定**：8 = 榜单专项（原等级保留在 `anchor.bench_level`），schema pattern 已放宽到 [1-9]；
   `meta.bench` 字段（如 TB-T2、RB-R12）供榜单按维度聚合，与子任务一一对应。
5. **与存量题的关系**：v1.2 全库 = v1.1（1735）+ bench（186）= 1921 题，合并文件 `items.jsonl`；
   存量题的 Bench 维度映射见匹配矩阵 §2–§4（按任务类型聚合，无需改动存量题面）。

## 施测

```bash
python runner/run_eval.py --items items/v1.2/items_bench.jsonl --name mymodel \
    --model <model> --base <...> --key <...> --workers 8
# llm_rubric 140 题随后评委补评
python runner/judge_rubric.py --items items/v1.2/items_bench.jsonl mymodel <judge-model>
# 汇总（--items 指向 v1.2 才会统计 bench 题）
python runner/summarize.py --items items/v1.2/items_bench.jsonl mymodel
```

## 已知残留风险（draft，待专业团队复核）

1. rb.review 的缺陷-摘要配对是程序指派，非真实审稿情境——复核时建议专家过一遍情境描述是否自洽；
2. rb.litsearch 金标 = 2026-09 检索快照，文献领域后续更新会使金标时效衰减（建议按年刷新）；
3. tb.exercise 的「等级适配性」由评委判断，未接 deterministic_rule 词表校验（题面要求 ±1 级，
   复核时可对产出补跑 check_vocab_level 抽检）；
4. tb.objective 的职业场景描述条目部分含 OCR 页码噪声（如 "3.2.2"），出题时已尽量过滤，需抽核。