# -*- coding: utf-8 -*-
"""汇总 results/harness 下各模型的 lm-eval 结果，生成 Markdown 对照表。
用法（在 harness/ 下）：../.venv/Scripts/python.exe summarize_harness.py
"""
import os, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'results/harness')
DATA = os.path.join(ROOT, 'harness/data')
OUT = os.path.join(RES, 'LOCAL_OPENSOURCE_v1.1a.md')

MODELS = ['Qwen2.5-0.5B', 'Qwen2.5-0.5B-Instruct', 'Qwen2.5-1.5B-Instruct',
          'Qwen2.5-3B-Instruct', 'Llama-3.2-1B-Instruct', 'Llama-3.2-3B-Instruct']
MODEL_LABEL = {
    'Qwen2.5-0.5B': 'Qwen 0.5B 基座',
    'Qwen2.5-0.5B-Instruct': 'Qwen 0.5B 指令',
    'Qwen2.5-1.5B-Instruct': 'Qwen 1.5B 指令',
    'Qwen2.5-3B-Instruct': 'Qwen 3B 指令',
    'Llama-3.2-1B-Instruct': 'Llama 1B 指令',
    'Llama-3.2-3B-Instruct': 'Llama 3B 指令',
}
# 各模型计分用的分片集合（题目覆盖完全一致，仅分批粒度不同）
PARTS = {
    'cceval_kno': {
        'Qwen2.5-0.5B': ['cceval_kno_p1', 'cceval_kno_p2', 'cceval_kno_p3', 'cceval_kno_p4'],
        'Qwen2.5-0.5B-Instruct': ['cceval_kno_p1', 'cceval_kno_p2', 'cceval_kno_p3', 'cceval_kno_p4'],
        'Qwen2.5-1.5B-Instruct': ['cceval_kno_p1', 'cceval_kno_p2',
                                  'cceval_kno_s5', 'cceval_kno_s6', 'cceval_kno_s7', 'cceval_kno_s8'],
        'Qwen2.5-3B-Instruct': [f'cceval_kno_u{i}' for i in range(1, 35)],
        'Llama-3.2-1B-Instruct': [f'cceval_kno_s{i}' for i in range(1, 9)],
        'Llama-3.2-3B-Instruct': [f'cceval_kno_u{i}' for i in range(1, 35)],
    },
    'cceval_pho_legal': {
        'Qwen2.5-3B-Instruct': ['cceval_pho_legal_a', 'cceval_pho_legal_b'],
        'Llama-3.2-3B-Instruct': ['cceval_pho_legal_a', 'cceval_pho_legal_b'],
    },
    'cceval_pho_level': {
        'Qwen2.5-3B-Instruct': ['cceval_pho_level_a', 'cceval_pho_level_b'],
        'Llama-3.2-3B-Instruct': ['cceval_pho_level_a', 'cceval_pho_level_b'],
    },
    'cceval_pho_poly': {},
}
# GGUF 路线模型（llama.cpp + gguf_score.py，结果文件名固定）
GGUF_MODELS = ['Qwen2.5-7B-q8_0', 'Llama-3.1-8B-q8_0']
GGUF_LABEL = {
    'Qwen2.5-7B-q8_0': 'Qwen 7B 指令 Q8',
    'Llama-3.1-8B-q8_0': 'Llama 8B 指令 Q8',
}
GGUF_FILE = {
    'cceval_kno': 'kno.json',
    'cceval_pho_legal': 'pho_legal.json',
    'cceval_pho_level': 'pho_level.json',
    'cceval_pho_poly': 'pho_poly.json',
}

TASKS = ['cceval_kno', 'cceval_pho_legal', 'cceval_pho_level', 'cceval_pho_poly']
TASK_NAME = {
    'cceval_kno': 'KNO 标准知识定级（400 题）',
    'cceval_pho_legal': 'PHO 音节合法性（60 题）',
    'cceval_pho_level': 'PHO 音节定级（40 题）',
    'cceval_pho_poly': 'PHO 多音字定音（30 题）',
}
TASK_N = {'cceval_kno': 400, 'cceval_pho_legal': 60, 'cceval_pho_level': 40, 'cceval_pho_poly': 30}


def latest_per_task(model):
    """返回 {task: (acc, n)}，每个任务取时间戳最新的结果文件。"""
    d = os.path.join(RES, model)
    out = {}
    for root, _dirs, files in os.walk(d):  # 目录名以 ".." 开头，glob 不可靠，用 os.walk
        for fn in files:
            if not (fn.startswith('results_') and fn.endswith('.json')):
                continue
            ts = fn.replace('results_', '').replace('.json', '')
            with open(os.path.join(root, fn), encoding='utf-8') as f:
                r = json.load(f)
            for task, v in r.get('results', {}).items():
                if task not in out or ts > out[task][0]:
                    out[task] = (ts, v['acc,none'], v['sample_len'])
    return {t: (acc, n) for t, (ts, acc, n) in out.items()}


def chance(task):
    with open(os.path.join(DATA, task + '.jsonl'), encoding='utf-8') as f:
        rows = [json.loads(l) for l in f]
    return sum(1.0 / len(r['choices']) for r in rows) / len(rows)


def majority_chance(task):
    """众数猜测基线：始终预测 gold 频率最高的选项位置所能得到的 ACC。"""
    from collections import Counter
    with open(os.path.join(DATA, task + '.jsonl'), encoding='utf-8') as f:
        rows = [json.loads(l) for l in f]
    return Counter(r['gold'] for r in rows).most_common(1)[0][1] / len(rows)


def task_acc(per_model, task, model):
    parts = PARTS[task].get(model, [task])
    n_tot, c = 0, 0.0
    for sh in parts:
        acc, n = per_model[sh]
        n_tot += n
        c += acc * n
    assert n_tot == TASK_N[task], f'{model} {task} 题数不符: {n_tot}'
    return c / n_tot


def gguf_acc(model):
    """读取 gguf_score.py 结果，返回 {task: (acc, n, complete)}。"""
    d = os.path.join(RES, model)
    out = {}
    for task, fn in GGUF_FILE.items():
        p = os.path.join(d, fn)
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                r = json.load(f)
            out[task] = (r['acc'], r['n'], r.get('complete', False))
    return out


def main():
    per = {m: latest_per_task(m) for m in MODELS}
    accs = {m: {t: task_acc(per[m], t, m) for t in TASKS} for m in MODELS}
    gaccs = {m: gguf_acc(m) for m in GGUF_MODELS}
    gaccs = {m: a for m, a in gaccs.items() if a}  # 只保留已有结果的模型

    lines = []
    lines.append('# CC-Eval v1.1a 本地开源模型实测（loglikelihood 判别式）')
    lines.append('')
    lines.append(f'- 日期：{datetime.date.today().isoformat()}')
    lines.append('- 机器：i7-12700H / 32GB RAM / CPU 推理（RTX 3050 Laptop NVML 异常，未用 GPU）')
    lines.append('- 栈：lm-evaluation-harness 0.4.13 · torch 2.14.0+cpu · float32 · 0-shot · seed 0/1234')
    lines.append('- 题型：multiple_choice 对数似然（不生成文本）；候选统一加共享前缀「答案：」缓解位置偏差')
    lines.append('- 数据：`harness/data/`（530 题 = KNO 400 + PHO 130），锚定 GF 0025-2021')
    lines.append('- 说明：loglikelihood 与 batch size 无关；KNO 按模型耗时以 100/50/25/12 题分片完成，题目完全一致')
    lines.append('- 基线：随机基线 = 均匀猜测期望；众数基线 = 始终预测 gold 频率最高的选项位置（占位/退化行为的有效上限），模型 ACC 须同时越过两条基线才可解读为真实掌握')
    lines.append('')
    lines.append('| 任务 | 题数 | 随机基线 | 众数基线 |' + ''.join(f' {MODEL_LABEL[m]} |' for m in MODELS))
    lines.append('|---|---:|---:|---:|' + '---:|' * len(MODELS))
    for task in TASKS:
        row = f"| {TASK_NAME[task]} | {TASK_N[task]} | {chance(task)*100:.1f}% | {majority_chance(task)*100:.1f}% |"
        row += ''.join(f' {accs[m][task]*100:.1f}% |' for m in MODELS)
        lines.append(row)
    lines.append('')

    if gaccs:
        glabels = [GGUF_LABEL[m] for m in gaccs]
        lines.append('## 7B/8B 量级（GGUF Q8_0 · llama.cpp · 同口径 loglikelihood 判别式）')
        lines.append('')
        lines.append('- 路线：llama-server + `gguf_score.py`（trie 共享候选前缀 + 全词表 logprobs 逐 token 取值），'
                     '与 lm-eval 同口径公式，0.5B 抽样一致性核验差异 ≤1 题')
        lines.append('- 量化：Q8_0（引入少量数值噪声，解释跨表对比时需注意）')
        lines.append('')
        lines.append('| 任务 | 题数 | 随机基线 | 众数基线 |' + ''.join(f' {l} |' for l in glabels))
        lines.append('|---|---:|---:|---:|' + '---:|' * len(glabels))
        for task in TASKS:
            row = f"| {TASK_NAME[task]} | {TASK_N[task]} | {chance(task)*100:.1f}% | {majority_chance(task)*100:.1f}% |"
            for m in gaccs:
                if task in gaccs[m]:
                    acc, n, comp = gaccs[m][task]
                    row += f' {acc*100:.1f}%{"" if comp else f"({n}/{TASK_N[task]} 部分)"} |'
                else:
                    row += ' — |'
            lines.append(row)
        lines.append('')
    lines.append('## 初步观察')
    lines.append('')
    q, l1, l3 = (accs[m] for m in ('Qwen2.5-3B-Instruct', 'Llama-3.2-1B-Instruct', 'Llama-3.2-3B-Instruct'))
    lines.append(f"1. **KNO（标准定级知识）八个开源模型全部无真实掌握**：0.5B–3B 六模型落在 6.2%–15.8%（均匀随机 14.3%，stderr≈1.6%）；Qwen 7B 为 14.0% 恰在随机带内（主导文本「答案：3」集中度 56%，选其他文本时命中 14.0%）；Llama 8B 原始值 33.5% 经均衡化重测证伪——见下方「均衡化重测」节，其全部得分来自对「7-9 级」文本的内容先验剥削——标准定级知识在 0.5B–8B 两个模型族上均未随规模涌现，与商用模型（Kimi 88.5%）的差距是质的。")
    lines.append('2. **音节合法性涌现是族特异的**：Qwen 7B 达 85.0%（0.5B–3B 各模型均为 50% 占位式退化），Llama 8B 仍为 50.0% 占位（合法半边 0/30、非法半边全对）——同为 7–8B 指令模型，语音知识涌现与否取决于训练数据/模型族而非参数量，能力结论不能跨族外推。')
    lines.append(f"3. **多音字定音是唯一随规模稳定提升的子项**：Qwen 66.7% → 60.0% → 80.0% → 90.0% → 83.3%（7B）；Llama {l1['cceval_pho_poly']*100:.1f}% → {l3['cceval_pho_poly']*100:.1f}% → 72.4%（8B）——语境定音属于通用语言能力，与标准专门知识清晰分离。")
    lines.append('4. **音节定级两族全败**：Qwen 7B 25.0%、Llama 8B 10.0%（低于随机 14.3%），"语音+等级"复合判断在通用模型上普遍缺失。')
    lines.append('5. **方法论警示**：本批次同时给出正反两例——Qwen 7B 的 85% 经逐题核验为真实作答，Llama 8B KNO 的 33.5% 经两轮检验（位置分布 → 内容先验）证伪。任何基准的原始 ACC 都必须配套占位检验、众数基线与**按选项文本的偏好分解**（位置均衡化不能消除内容先验），否则会把退化行为误读为能力涌现。')
    lines.append('6. 佐证论文核心论点：通用开源模型对锚定标准的专门知识近乎空白，该空白与指令对齐、参数量级（≤8B）、模型族无关；通用语言能力（音节表、语境定音）的涌现则是族特异、规模相关的——必须通过后训练专门注入标准知识，并以锚定基准客观验证。')
    lines.append('')
    lines.append('## 均衡化重测（v1.1b · 2026-10-02）')
    lines.append('')
    lines.append('对 KNO / 音节定级 / 多音字三个任务做 gold 位置均衡化（种子 42 轮转洗牌，仅对换选项、内容零改动，等价性已校验），7B/8B 两模型全量重测。**六个任务的均衡版 ACC 与原版完全一致**——模型预测由选项文本内容驱动而非位置，位置均衡化不改变结果；据此把偏好分解从"位置"升级为"内容先验"口径：')
    lines.append('')
    lines.append('| 模型 | 任务 | 原版 | 均衡版 | 主导选项文本集中度 | 选其他文本时命中 | 判读 |')
    lines.append('|---|---|---:|---:|---:|---:|---|')
    lines.append('| Qwen 7B | KNO 定级 | 14.0% | 14.0% | 「3 级」56% | 14.0%（n=178） | 随机 |')
    lines.append('| Llama 8B | KNO 定级 | 33.5% | 33.5% | 「7-9 级」77% | **12.9%（n=93，低于随机）** | **内容先验剥削，无真实知识** |')
    lines.append('| Qwen 7B | 音节定级 | 25.0% | 25.0% | 「3 级」75% | 60.0%（n=10，样本小） | 弱信号待复核 |')
    lines.append('| Llama 8B | 音节定级 | 10.0% | 10.0% | 「7-9 级」92% | 0.0%（n=3） | 占位 |')
    lines.append('| Qwen 7B | 多音字 | 83.3% | 83.3% | 7%（无先验） | 82.1%（n=28） | 真实能力 |')
    lines.append('| Llama 8B | 多音字 | 72.4% | 72.4% | 7%（无先验） | 70.4%（n=27） | 真实能力 |')
    lines.append('')
    lines.append('要点：Llama 8B KNO 的 33.5% 全部来自"猜 7-9 级"策略——该标签覆盖词表 51% 词条（本题库 gold 占 39%），选它时命中 39.7%（恰等于该标签先验），不选时 12.9% 反低于随机。**内容先验剥削比位置偏误更隐蔽**：模型位置分布可以相当分散（均衡版位置 6 集中度降至 47%），但文本先验纹丝不动。KNO 题库的「7-9 级」是合并标签（覆盖三个等级、51% 词条），既是标准的本体特征也是评测的结构性弱点——v1.3 应将 7-9 拆分为独立等级或按词条频率加权报告。')
    lines.append('')
    lines.append('## 数据质量备注')
    lines.append('')
    lines.append('- KNO 金标选项位置不均衡：7 个选项的 gold 分布为 {0:25, 1:45, 2:42, 3:39, 4:43, 5:50, 6:156}（第 7 项占 39.0%）。均匀猜测基线仍为 14.3%，但众数猜测基线高达 39.0%——v1.3 题库应做 gold 位置均衡化。')
    lines.append('- PHO 音节合法性题组按"合法/非法"顺序排列（前 30 合法、后 30 非法），便于占位行为识别；随机化后结论不变。')
    lines.append('- 7B/8B 为 Q8_0 量化，与 fp32 的 lm-eval 结果跨表对比时存在少量量化噪声（0.5B 抽样核验 ≤1 题差异）。')
    lines.append('')
    lines.append('## 复现')
    lines.append('')
    lines.append('```bash')
    lines.append('cd harness && ../.venv/Scripts/python.exe export_lm_eval.py')
    lines.append('../.venv/Scripts/python.exe -m lm_eval --model hf \\')
    lines.append('  --model_args pretrained=../models/Qwen2.5-0.5B,dtype=float32 \\')
    lines.append('  --tasks cceval_kno_p1 --include_path tasks --device cpu --batch_size 64 \\')
    lines.append('  --output_path ../results/harness/Qwen2.5-0.5B')
    lines.append('# 大模型 CPU 限时环境：run_queue.py 断点续跑微分片')
    lines.append('../.venv/Scripts/python.exe run_queue.py --model ../models/Qwen2.5-3B-Instruct \\')
    lines.append('  --prefix cceval_kno_u --count 34 --budget 240')
    lines.append('```')
    txt = '\n'.join(lines) + '\n'
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(txt)
    print(txt)
    print('written ->', OUT)


if __name__ == '__main__':
    main()
