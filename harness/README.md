# harness/ —— lm-evaluation-harness 接入（开源模型规模化评测）

将 CC-Eval 的判别式题目导出为 [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness)
的 `multiple_choice` 任务。**不生成文本，只比较候选答案的 log 概率**，纯前向计算、完全确定性，
适用于任何 HuggingFace 开源模型（包括无指令微调能力的基座模型）。

## 任务清单（v1.1a，共 530 题）

| 任务名 | 题量 | 内容 | 候选 |
|---|---|---|---|
| `cceval_kno` | 400 | 音节/汉字/词汇/语法点定级（GF 0025-2021） | 1–6、7-9 七选一 |
| `cceval_pho_legal` | 60 | 音节合法性判断（音节表） | 合法/非法 |
| `cceval_pho_level` | 40 | 带调音节定级（音节表） | 1–6、7-9 七选一 |
| `cceval_pho_poly` | 30 | 多音字语境定音（候选=该字全部标准读音） | 2–4 个读音 |

`pho.tone_actual`（实际读音 50 题）暂以生成式评测为主（runner 路线），其 loglikelihood 化
（实际读音 vs 本调读音二选一的干扰项构造）留待 v1.1b。

## 首批实测记录（2026-09-06，本机 CPU，完整报告见 ../results/harness/LOCAL_OPENSOURCE_v1.1a.md）

Qwen2.5-0.5B 基座 vs 指令版，0-shot loglikelihood，float32：

| 任务 | 随机基线 | 0.5B 基座 | 0.5B-Instruct |
|---|---:|---:|---:|
| KNO 定级（400） | 14.3% | 6.5% | 6.5% |
| PHO 音节合法性（60） | 50.0% | 50.0% | 50.0% |
| PHO 音节定级（40） | 14.3% | 32.5% | 30.0% |
| PHO 多音字定音（30） | 47.8% | 66.7% | 60.0% |

0.5B 量级开源模型的《等级标准》知识显著低于随机水平，且指令对齐未带来改善——
与商用模型（Kimi KNO 88.5%）形成鲜明对照，佐证"标准知识需要专门注入"的核心论点。
任何 HuggingFace 模型均可按下方命令复测，欢迎 PR 补充结果。

## 使用方法

```bash
pip install lm-eval
# 在本目录（harness/）下执行，--include_path 指向 tasks/
lm_eval --model hf \
  --model_args pretrained=Qwen/Qwen2.5-7B-Instruct \
  --tasks cceval_kno,cceval_pho_legal,cceval_pho_level,cceval_pho_poly \
  --include_path tasks/ \
  --batch_size auto
```

基座模型（base model）同样可测——loglikelihood 不依赖指令遵循能力，这正是该路线的意义：
把"模型内化了多少《等级标准》知识"与"模型会不会按格式答题"分离开。

## 重新生成

```bash
python harness/export_lm_eval.py   # 从 items/v1.1/items.jsonl 重新导出 data/ 与 tasks/
```

## 与 runner 路线的关系

- **harness 路线（本目录）**：判别式子集，loglikelihood，面向海量开源模型的广度普查；
- **runner 路线（../runner/）**：全部 1735 题，生成+确定性评分，面向有生成能力的模型
  （商业 API 或本地 vLLM/llama.cpp，`--base` 指向本地 OpenAI 兼容端点即可）。
