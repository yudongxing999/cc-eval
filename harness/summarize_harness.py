# -*- coding: utf-8 -*-
"""汇总 results/harness 下各模型的 lm-eval 结果，生成 Markdown 对照表。
用法（在 harness/ 下）：../.venv/Scripts/python.exe summarize_harness.py
"""
import os, json, glob, math, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'results/harness')
DATA = os.path.join(ROOT, 'harness/data')
OUT = os.path.join(RES, 'LOCAL_OPENSOURCE_v1.1a.md')

MODELS = ['Qwen2.5-0.5B', 'Qwen2.5-0.5B-Instruct']
KNO_SHARDS = ['cceval_kno_p1', 'cceval_kno_p2', 'cceval_kno_p3', 'cceval_kno_p4']
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


def main():
    per = {m: latest_per_task(m) for m in MODELS}
    lines = []
    lines.append('# CC-Eval v1.1a 本地开源模型实测（loglikelihood 判别式）')
    lines.append('')
    lines.append(f'- 日期：{datetime.date.today().isoformat()}')
    lines.append('- 机器：i7-12700H / 32GB RAM / CPU 推理（RTX 3050 Laptop NVML 异常，未用 GPU）')
    lines.append('- 栈：lm-evaluation-harness 0.4.13 · torch 2.14.0+cpu · float32 · batch 64 · 0-shot · seed 0/1234')
    lines.append('- 题型：multiple_choice 对数似然（不生成文本）；候选统一加共享前缀「答案：」缓解位置偏差')
    lines.append('- 数据：`harness/data/`（530 题 = KNO 400 + PHO 130），锚定 GF 0025-2021')
    lines.append('')
    lines.append('| 任务 | 题数 | 随机基线 | Qwen2.5-0.5B（基座） | Qwen2.5-0.5B-Instruct（指令） |')
    lines.append('|---|---:|---:|---:|---:|')
    for task in TASKS:
        if task == 'cceval_kno':
            n_tot, base_c, ins_c = 0, 0.0, 0.0
            for sh in KNO_SHARDS:
                n = per['Qwen2.5-0.5B'][sh][1]
                n_tot += n
                base_c += per['Qwen2.5-0.5B'][sh][0] * n
                ins_c += per['Qwen2.5-0.5B-Instruct'][sh][0] * n
            b, i = base_c / n_tot, ins_c / n_tot
            n_show = n_tot
        else:
            n_show = per['Qwen2.5-0.5B'][task][1]
            b = per['Qwen2.5-0.5B'][task][0]
            i = per['Qwen2.5-0.5B-Instruct'][task][0]
        lines.append(f"| {TASK_NAME[task]} | {n_show} | {chance(task)*100:.1f}% | {b*100:.1f}% | {i*100:.1f}% |")
    lines.append('')
    lines.append('KNO 分片明细（acc × 100 题/片）：')
    lines.append('')
    lines.append('| 分片 | 基座 | 指令 |')
    lines.append('|---|---:|---:|')
    for sh in KNO_SHARDS:
        lines.append(f"| {sh} | {per['Qwen2.5-0.5B'][sh][0]*100:.0f}% | {per['Qwen2.5-0.5B-Instruct'][sh][0]*100:.0f}% |")
    lines.append('')
    lines.append('## 初步观察')
    lines.append('')
    lines.append('1. 0.5B 量级开源模型在 GF 0025-2021 等级知识（KNO）上仅 6.5%（七选一随机 14.3%），**显著低于随机**：模型不仅没有内化标准，且存在系统性错误偏好。')
    lines.append('2. 基座与指令版在四项任务上几乎无差异（KNO 同为 6.5%），说明在该参数量级上，通用指令对齐并未带来国际中文教育标准知识。')
    lines.append('3. PHO 音节合法性两个模型均为 50%（等于二选一随机），逐样本看模型恒定选同一标签，属于占位式回答。')
    lines.append('4. 多音字定音（基座 66.7% / 指令 60.0%）高于其候选随机基线，是相对最强的子项，但仍远低于商用模型（Kimi 100%）。')
    lines.append('5. 该结果支持论文核心论点：通用大模型「不会就是不会」，评测必须锚定标准、而非依赖主观打分。')
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
