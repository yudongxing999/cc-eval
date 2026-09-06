# -*- coding: utf-8 -*-
"""汇总某模型的评测结果"""
import os, sys, json, glob
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model = sys.argv[1] if len(sys.argv) > 1 else 'k2d6-agent'
items = {i['item_id']: i for i in (json.loads(l) for l in open(os.path.join(ROOT, 'items/v1.0/items.jsonl'), encoding='utf-8'))}

by_task, by_sub, errs, judged = defaultdict(list), defaultdict(list), 0, 0
for f in glob.glob(os.path.join(ROOT, 'results', model, '*.json')):
    d = json.load(open(f, encoding='utf-8'))
    it = items.get(d['item_id'])
    if not it: continue
    if d.get('error'): errs += 1
    s = d.get('score')
    if s is None:
        judged += 1
        continue
    by_task[it['task_type']].append(s)
    by_sub[it['sub_type']].append(s)

print(f'===== 模型: {model} =====')
print(f'已评: {sum(len(v) for v in by_task.values())}  待评委(llm_rubric): {judged}  错误: {errs}')
tot_all = [s for v in by_task.values() for s in v]
print(f'可机判题总得分率: {sum(tot_all)/len(tot_all)*100:.1f}%  (n={len(tot_all)})')
print()
for t in ('KNO', 'ERR', 'SCO', 'GEN', 'CUL', 'PED'):
    v = by_task.get(t)
    if v: print(f'{t}: {sum(v)/len(v)*100:.1f}%  (n={len(v)})')
print()
for st, v in sorted(by_sub.items()):
    print(f'  {st}: {sum(v)/len(v)*100:.1f}%  (n={len(v)})')
