# -*- coding: utf-8 -*-
"""均衡化重测对照：原版 vs 均衡版 ACC + 选项偏好分解（非偏好题命中率）。
用法（在 harness/ 下）：../.venv/Scripts/python.exe bal_report.py
"""
import json, os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results/harness")
DATA = os.path.join(ROOT, "harness/data")

MODELS = ['Qwen2.5-7B-q8_0', 'Llama-3.1-8B-q8_0']
TASKS = [('kno', 'kno_bal', 'KNO 标准定级'), ('pho_level', 'pho_level_bal', '音节定级'),
         ('pho_poly', 'pho_poly_bal', '多音字定音')]


def load(model, stem):
    p = os.path.join(RES, model, stem + '.json')
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding='utf-8'))


def bias_decomp(d, data_file):
    """按选项文本内容分解（位置可被均衡化打乱，内容先验才是真金）。
    返回 (acc, 主导文本集中度, 选非主导文本题的命中率)。"""
    rows = {}
    for l in open(os.path.join(DATA, data_file), encoding='utf-8'):
        r = json.loads(l)
        rows[r['item_id']] = r
    preds = [p for p in d['preds'] if not p.get('error')]
    n = len(preds)
    acc = sum(bool(p['correct']) for p in preds) / n
    tc = Counter(rows[p['item_id']]['choices'][p['pred']] for p in preds)
    top_txt, topn = tc.most_common(1)[0]
    rest = [p for p in preds if rows[p['item_id']]['choices'][p['pred']] != top_txt]
    rest_acc = sum(bool(p['correct']) for p in rest) / len(rest) if rest else float('nan')
    return acc, top_txt, topn / n, rest_acc, len(rest)


print('| 模型 | 任务 | 原版 ACC | 均衡版 ACC | 主导选项文本集中度 | 选其他文本时命中 | 判读 |')
print('|---|---|---:|---:|---:|---:|---|')
for m in MODELS:
    for orig, bal, name in TASKS:
        do, db = load(m, orig), load(m, bal)
        if db is None:
            print(f'| {m} | {name} | {"%.1f%%" % (do["acc"]*100) if do else "—"} | 未完成 | | | |')
            continue
        acc, top_txt, conc, rest_acc, nrest = bias_decomp(db, 'cceval_' + bal + '.jsonl')
        if conc < 0.15 and acc > 0.55:
            verdict = '真实信号（无内容先验）'
        elif rest_acc > 0.30 and nrest >= 30:
            verdict = '真实信号'
        elif abs(acc - 1 / 7) < 0.06 or (rest_acc < 0.20 and nrest >= 30):
            verdict = '占位/随机'
        else:
            verdict = '弱信号待复核'
        print(f'| {m} | {name} | {"%.1f%%" % (do["acc"]*100) if do else "—"} | {acc*100:.1f}% '
              f'| {top_txt}×{conc*100:.0f}% | {rest_acc*100:.1f}%(n={nrest}) | {verdict} |')
