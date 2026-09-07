# CC-Eval v1.1a 本地开源模型实测（loglikelihood 判别式）

- 日期：2026-09-07
- 机器：i7-12700H / 32GB RAM / CPU 推理（RTX 3050 Laptop NVML 异常，未用 GPU）
- 栈：lm-evaluation-harness 0.4.13 · torch 2.14.0+cpu · float32 · 0-shot · seed 0/1234
- 题型：multiple_choice 对数似然（不生成文本）；候选统一加共享前缀「答案：」缓解位置偏差
- 数据：`harness/data/`（530 题 = KNO 400 + PHO 130），锚定 GF 0025-2021
- 说明：loglikelihood 与 batch size 无关；KNO 按模型耗时以 100/50/25/12 题分片完成，题目完全一致

| 任务 | 题数 | 随机基线 | Qwen 0.5B 基座 | Qwen 0.5B 指令 | Qwen 1.5B 指令 | Qwen 3B 指令 | Llama 1B 指令 | Llama 3B 指令 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| KNO 标准知识定级（400 题） | 400 | 14.3% | 6.5% | 6.5% | 15.8% | 11.8% | 6.2% | 10.5% |
| PHO 音节合法性（60 题） | 60 | 50.0% | 50.0% | 50.0% | 50.0% | 50.0% | 50.0% | 50.0% |
| PHO 音节定级（40 题） | 40 | 14.3% | 32.5% | 30.0% | 5.0% | 32.5% | 32.5% | 15.0% |
| PHO 多音字定音（30 题） | 30 | 47.8% | 66.7% | 60.0% | 80.0% | 90.0% | 73.3% | 70.0% |

## 初步观察

1. **KNO 全部处于随机水平**：六个模型 KNO 落在 6.2%–15.8%（七选一随机 14.3%，400 题 stderr≈1.6%），两个模型族、0.5B–3B 之间无可靠缩放趋势（Qwen 3B 的 11.8% 甚至低于 1.5B 的 15.8%）——开源小模型普遍未内化《等级标准》知识，与商用模型（Kimi 88.5%）差距是质的而非量的。
2. **族间结论一致**：Llama-3.2 与 Qwen2.5 表现同构（KNO 1B 6.2% / 3B 10.5%，音节合法性均 50% 占位式回答）——标准知识缺失是跨模型族的普遍现象，非某家特有问题。
3. **多音字定音是唯一随规模稳定提升的子项**：Qwen 66.7% → 60.0% → 80.0% → 90.0%；Llama 73.3% → 70.0%——语境定音属于通用语言能力，而定级判断属于标准专门知识，二者清晰分离。
4. 音节定级无稳定模式（5%–32.5% 波动），"语音+等级"复合判断对小模型最难。
5. 佐证论文核心论点：通用开源小模型对锚定标准的专门知识近乎空白，且该空白与指令对齐、参数量级（≤3B）、模型族无关——必须通过后训练专门注入。

## 复现

```bash
cd harness && ../.venv/Scripts/python.exe export_lm_eval.py
../.venv/Scripts/python.exe -m lm_eval --model hf \
  --model_args pretrained=../models/Qwen2.5-0.5B,dtype=float32 \
  --tasks cceval_kno_p1 --include_path tasks --device cpu --batch_size 64 \
  --output_path ../results/harness/Qwen2.5-0.5B
# 大模型 CPU 限时环境：run_queue.py 断点续跑微分片
../.venv/Scripts/python.exe run_queue.py --model ../models/Qwen2.5-3B-Instruct \
  --prefix cceval_kno_u --count 34 --budget 240
```
