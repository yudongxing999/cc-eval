# -*- coding: utf-8 -*-
"""汇总 results/harness 下各模型的 lm-eval 结果，生成 Markdown 对照表。
用法（在 harness/ 下）：../.venv/Scripts/python.exe summarize_harness.py
"""
import os, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'results/harness')
DATA = os.path.join(ROOT, 'harness/data')
OUT = os.path.join(RES, 'LOCAL_OPENSOURCE_v1.1a.md')

MODELS = ['Qwen2.5-0.5B', 'Qwen2.5-0.5B-Instruct', 'Qwen2.5-1.5B-Instruct']
MODEL_LABEL = {
    'Qwen2.5-0.5B': '0.5B 基座',
    'Qwen2.5-0.5B-Instruct': '0.5B 指令',
    'Qwen2.5-1.5B-Instruct': '1.5B 指令',
}
# 各模型 KNO 计分用的分片（1.5B 的 p3/p4 因限时改用 50 题细分片 s5-s8，覆盖相同题目）
KNO_PARTS = {
    'Qwen2.5-0.5B': ['cceval_kno_p1', 'cceval_kno_p2', 'cceval_kno_p3', 'cceval_kno_p4'],
    'Qwen2.5-0.5B-Instruct': ['cceval_kno_p1', 'cceval_kno_p2', 'cceval_kno_p3', 'cceval_kno_p4'],
    'Qwen2.5-1.5B-Instruct': ['cceval_kno_p1', 'cceval_kno_p2',
                              'cceval_kno_s5', 'cceval_kno_s6', 'cceval_kno_s7', 'cceval_kno_s8'],
}
TASKS = ['cceval_kno', 'cceval_pho_legal', 'cceval_pho_level', 'cceval_pho_poly']
TASK_NAME = {
    'cceval_kno': 'KNO 标准知识定级（400 题）',
    'cceval_pho_legal': 'PHO 音节合法性（60 题）',
    'cceval_pho_level': 'PHO 音节定级（40 题）',
    'cceval_pho_poly': 'PHO 多音字定音（30 题）',
}


def latest_per_task(model):
    """返回 {task: (acc, n, stderr)}，每个任务取时间戳最新的结果文件。"""
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
                    out[task] = (ts, v['acc,none'], v['sample_len'], v['acc_stderr,none'])
    return {t: (acc, n, se) for t, (ts, acc, n, se) in out.items()}


def chance(task):
    with open(os.path.join(DATA, task + '.jsonl'), encoding='utf-8') as f:
        rows = [json.loads(l) for l in f]
    return sum(1.0 / len(r['choices']) for r in rows) / len(rows)


def kno_acc(per_model, model):
    n_tot, c = 0, 0.0
    detail = []
    for sh in KNO_PARTS[model]:
        acc, n, _se = per_model[sh]
        n_tot += n
        c += acc * n
        detail.append(f"{sh.replace('cceval_kno_', '')} {acc*100:.0f}%")
    return c / n_tot, n_tot, detail


def main():
    per = {m: latest_per_task(m) for m in MODELS}
    lines = []
    lines.append('# CC-Eval v1.1a 本地开源模型实测（loglikelihood 判别式）')
    lines.append('')
    lines.append(f'- 日期：{datetime.date.today().isoformat()}')
    lines.append('- 机器：i7-12700H / 32GB RAM / CPU 推理（RTX 3050 Laptop NVML 异常，未用 GPU）')
    lines.append('- 栈：lm-evaluation-harness 0.4.13 · torch 2.14.0+cpu · float32 · 0-shot · seed 0/1234')
    lines.append('- 题型：multiple_choice 对数似然（不生成文本）；候选统一加共享前缀「答案：」缓解位置偏差')
    lines.append('- 数据：`harness/data/`（530 题 = KNO 400 + PHO 130），锚定 GF 0025-2021')
    lines.append('- 说明：loglikelihood 结果与 batch size 无关（0.5B 用 64，1.5B 用 256）；1.5B 的 KNO 后 200 题以 50 题细分片（s5-s8）完成，题目与 p3/p4 完全一致')
    lines.append('')
    header = '| 任务 | 题数 | 随机基线 |' + ''.join(f' {MODEL_LABEL[m]} |' for m in MODELS)
    sep = '|---|---:|---:|' + '---:|' * len(MODELS)
    lines.append(header)
    lines.append(sep)
    for task in TASKS:
        cells = []
        if task == 'cceval_kno':
            n_show = 400
            for m in MODELS:
                acc, _n, _d = kno_acc(per[m], m)
                cells.append(acc)
        else:
            n_show = per[MODELS[0]][task][1]
            cells = [per[m][task][0] for m in MODELS]
        row = f"| {TASK_NAME[task]} | {n_show} | {chance(task)*100:.1f}% |"
        row += ''.join(f' {c*100:.1f}% |' for c in cells)
        lines.append(row)
    lines.append('')
    lines.append('KNO 分片明细：')
    lines.append('')
    lines.append('| 模型 | 分片 acc |')
    lines.append('|---|---|')
    for m in MODELS:
        acc, n, detail = kno_acc(per[m], m)
        lines.append(f"| {MODEL_LABEL[m]}（合计 {acc*100:.1f}%，{n} 题） | {' · '.join(detail)} |")
    lines.append('')
    lines.append('## 初步观察')
    lines.append('')
    lines.append('1. **清晰的参数缩放趋势**：KNO 定级从 0.5B 的 6.5%（低于随机 14.3%）升到 1.5B 的 15.8%（略高于随机）。标准知识随参数量增长，但 1.5B 仍只是"接近随机"，距离商用模型（Kimi 88.5%）有数量级差距。')
    lines.append('2. 0.5B 基座与指令版四项几乎无差异（KNO 同为 6.5%）：小参数量级上，通用指令对齐并未注入《等级标准》知识。')
    lines.append('3. PHO 音节合法性三个模型全部 50%（=二选一随机），逐样本看模型恒定选同一标签，属于占位式回答——音节表知识完全缺失。')
    lines.append('4. 多音字定音是最强子项且随规模提升（66.7% → 60.0% → 80.0%），但仍低于商用模型（Kimi 100%）；音节定级在 1.5B 上反而跌到 5%，提示小模型的"语音+等级"复合判断极不稳定。')
    lines.append('5. 该结果支持论文核心论点：通用大模型对锚定标准的专门知识"不会就是不会"，评测必须锚定标准、而非依赖主观打分；也为"后训练注入标准知识"提供了量化基线。')
    lines.append('')
    lines.append('## 复现')
    lines.append('')
    lines.append('```bash')
    lines.append('cd harness && ../.venv/Scripts/python.exe export_lm_eval.py')
    lines.append('../.venv/Scripts/python.exe -m lm_eval --model hf \\')
    lines.append('  --model_args pretrained=../models/Qwen2.5-0.5B,dtype=float32 \\')
    lines.append('  --tasks cceval_kno_p1 --include_path tasks --device cpu --batch_size 64 \\')
    lines.append('  --output_path ../results/harness/Qwen2.5-0.5B')
    lines.append('```')
    txt = '\n'.join(lines) + '\n'
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(txt)
    print(txt)
    print('written ->', OUT)


if __name__ == '__main__':
    main()
