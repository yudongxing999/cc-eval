# CC-Eval v1.1a 本地开源模型实测（loglikelihood 判别式）

- 日期：2026-09-06
- 机器：i7-12700H / 32GB RAM / CPU 推理（RTX 3050 Laptop NVML 异常，未用 GPU）
- 栈：lm-evaluation-harness 0.4.13 · torch 2.14.0+cpu · float32 · batch 64 · 0-shot · seed 0/1234
- 题型：multiple_choice 对数似然（不生成文本）；候选统一加共享前缀「答案：」缓解位置偏差
- 数据：`harness/data/`（530 题 = KNO 400 + PHO 130），锚定 GF 0025-2021

| 任务 | 题数 | 随机基线 | Qwen2.5-0.5B（基座） | Qwen2.5-0.5B-Instruct（指令） |
|---|---:|---:|---:|---:|
| KNO 标准知识定级（400 题） | 400 | 14.3% | 6.5% | 6.5% |
| PHO 音节合法性（60 题） | 60 | 50.0% | 50.0% | 50.0% |
| PHO 音节定级（40 题） | 40 | 14.3% | 32.5% | 30.0% |
| PHO 多音字定音（30 题） | 30 | 47.8% | 66.7% | 60.0% |

KNO 分片明细（acc × 100 题/片）：

| 分片 | 基座 | 指令 |
|---|---:|---:|
| cceval_kno_p1 | 13% | 12% |
| cceval_kno_p2 | 8% | 8% |
| cceval_kno_p3 | 2% | 2% |
| cceval_kno_p4 | 3% | 4% |

## 初步观察

1. 0.5B 量级开源模型在 GF 0025-2021 等级知识（KNO）上仅 6.5%（七选一随机 14.3%），**显著低于随机**：模型不仅没有内化标准，且存在系统性错误偏好。
2. 基座与指令版在四项任务上几乎无差异（KNO 同为 6.5%），说明在该参数量级上，通用指令对齐并未带来国际中文教育标准知识。
3. PHO 音节合法性两个模型均为 50%（等于二选一随机），逐样本看模型恒定选同一标签，属于占位式回答。
4. 多音字定音（基座 66.7% / 指令 60.0%）高于其候选随机基线，是相对最强的子项，但仍远低于商用模型（Kimi 100%）。
5. 该结果支持论文核心论点：通用大模型「不会就是不会」，评测必须锚定标准、而非依赖主观打分。

## 复现

```bash
cd harness && ../.venv/Scripts/python.exe export_lm_eval.py
../.venv/Scripts/python.exe -m lm_eval --model hf \
  --model_args pretrained=../models/Qwen2.5-0.5B,dtype=float32 \
  --tasks cceval_kno_p1 --include_path tasks --device cpu --batch_size 64 \
  --output_path ../results/harness/Qwen2.5-0.5B
```
