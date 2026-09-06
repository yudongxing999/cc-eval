# CC-Eval · 国际中文教育大模型评测基准

**CC-Eval**（Chinese Language Education Evaluation）是面向**国际中文教育**（Teaching Chinese to Speakers of Other Languages）垂直场景的大语言模型实用价值评测基准。它以权威标准文件为骨架、真实学习者语料为素材，回答一个朴素的问题：**通用大模型在国际中文教育的具体工作中，到底能不能用、哪里能用、哪里不能用？**

作者：于东兴（Dongxing Yu）· 首次跑量：2026-09 · 版本：v1.0

## 排行榜（v1.0，1,555 题，六类任务等权，百分制）

| 排名 | 模型 | 总分 | KNO 等级知识 | ERR 偏误识别 | SCO 作文评分 | GEN 教学生成 | CUL 文化国情 | PED 标准定位 |
|---|---|---|---|---|---|---|---|---|
| 1 | Kimi k3-agent | 46.7 | 29.0 | 33.3 | 78.6 | 48.7 | 94.9 | 45.0 |
| 2 | DeepSeek deepseek-chat | 44.2 | 35.2 | 31.4 | 75.8 | 36.6 | 84.7 | 41.7 |
| 3 | deepseek-v4-flash（TokenHub） | 42.9 | 22.5 | 30.5 | 70.8 | 50.8 | 88.9 | 42.5 |
| 4 | 腾讯混元 hy3（TokenHub） | 42.2 | 23.8 | 32.8 | 48.6 | 59.7 | 92.0 | 43.3 |
| 5 | Grok grok-3-mini-fast | 41.2 | 24.8 | 28.0 | 58.6 | 53.7 | 87.4 | 40.3 |
| 6 | Kimi k2d6-agent | 39.4 | 21.2 | 36.1 | 55.8 | 40.0 | 85.6 | 44.1 |
| 7 | 百度 ernie-4.5-turbo | 38.4 | 20.2 | 24.1 | 76.8 | 35.0 | 82.4 | 42.5 |
| 8 | 阿里 qwen-flash | 38.2 | 12.2 | 30.8 | 74.2 | 38.4 | 80.4 | 43.8 |
| 9 | 字节 doubao-seed-1-6 | 37.9 | 20.2 | 34.0 | 44.4 | 46.6 | 86.3 | 41.1 |
| 10 | 阶跃 step-3.7-flash | 37.0 | 15.8 | 32.0 | 63.3 | 37.4 | 77.5 | 40.8 |
| 11 | 智谱 glm-4-flash | 33.4 | 12.0 | 21.5 | 74.2 | 31.4 | 70.5 | 37.1 |

> 完整分析见 [results/REPORT_v1.0_multimodel.md](results/REPORT_v1.0_multimodel.md)；机读数据见 [results/multimodel_summary.json](results/multimodel_summary.json)；逐题原始输出打包于 `results/results_v1.0_raw.tar.gz`。

**核心结论**：作文辅助评分 / 文化国情问答 / 场景化教学设计——可直接用；偏误归因 / 等级判断——需外挂标准检索；限级生成（最高仅 15%）/ 标准条文合规定位（最高 8.9%）——暂不可用。

## 基准设计

六类任务（v1.0 共 1,555 题）：

| 代码 | 任务 | 题量 | 素材来源 |
|---|---|---|---|
| KNO | 等级知识（音节/汉字/词汇/语法点定级） | 400 | GF 0025-2021 四张等级表 |
| ERR | 学习者偏误识别与纠正 | 377 | HSK 动态作文语料库（偏误标注） |
| SCO | 作文评分对齐（以人工分数为锚） | 250 | HSK 动态作文语料库（分数） |
| GEN | 教学生成（限级改写/用词成段/语法造句） | 300 | 词表约束程序化构造 |
| CUL | 文化国情与语用推理 | 78 | 《文化和国情教学参考框架》 |
| PED | 标准条文定位与教学设计 | 150 | 教材评价标准/教师能力标准/职业中文标准 |

评分方式：exact_match / numeric_proximity / set_overlap / deterministic_rule 四类自动评分器（1,357 题）+ LLM 评委按量表评分（198 题）。任务与评分明细见 [schema/](schema/) 与 `items/`。

## 目录结构

```
standard/    四份权威标准的结构化数据与全书级校验记录（含 errata.json）
schema/      题目 JSON Schema、评分器定义、示例
items/       题库（公开版 items_public.jsonl 928 题 + 生成器 generate_items.py）
runner/      评测运行器 run_eval.py / 评委补评 judge_rubric.py / 汇总 summarize.py
results/     报告、机读汇总、逐题原始输出压缩包
corpus/      语料库清单与使用申请说明（不含语料原文）
```

## 快速开始

```bash
# 1. 安装依赖（仅需 Python 3.10+ 标准库）
# 2. 配置被测模型的 OpenAI 兼容接口（自行创建 runner/providers.json，格式见 runner/run_provider.py）
# 3. 跑测（断点续跑，按 results/<name>/<item_id>.json 跳过已完成项）
python runner/run_eval.py --name mymodel --model <model-name> \
    --base <https://.../v1> --key <API_KEY> --workers 10
# 4. LLM 评委补评主观题
python runner/judge_rubric.py mymodel <judge-model>
# 5. 汇总
python runner/summarize.py mymodel
```

## 数据合规说明

- **HSK 动态作文语料库**（北京语言大学）需官方申请授权后方可使用。本仓库**不发布**语料原文及由其衍生的 627 道题目（ERR/SCO）；公开版题库为 928 题。获得授权的用户可将语料放入 `corpus/` 后运行 `items/generate_items.py` 重建完整 1,555 题（种子 20260905，结果可复现）。申请函模板见 `corpus/`。
- `standard/` 下结构化数据整理自公开出版标准（GF 0025-2021 等），仅供研究使用，著作权归原发布机构。
- 评测所用 API 凭证不包含在本仓库中。

## 引用

```bibtex
@misc{yu2026cceval,
  author = {于东兴 (Dongxing Yu)},
  title  = {CC-Eval: 国际中文教育大模型评测基准},
  year   = {2026},
  howpublished = {\url{https://github.com/yudongxing999/cc-eval}}
}
```

## 许可

代码与原创题库：[MIT License](LICENSE)。第三方标准数据与语料的著作权归原权利方。
