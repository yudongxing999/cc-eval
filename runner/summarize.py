# -*- coding: utf-8 -*-
"""汇总某模型的评测结果"""
import os, sys, json, glob, argparse
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_items_path():
    """v1.1 是 v1.0 超集（含 PHO）；优先用 v1.1，避免汇总时静默丢题。"""
    v11 = os.path.join(ROOT, 'items/v1.1/items.jsonl')
    v10 = os.path.join(ROOT, 'items/v1.0/items.jsonl')
    return v11 if os.path.isfile(v11) else v10


def load_items(path):
    return {i['item_id']: i for i in (json.loads(l) for l in open(path, encoding='utf-8'))}


def main():
    ap = argparse.ArgumentParser(description='汇总某模型的评测结果')
    ap.add_argument('model', nargs='?', default='k2d6-agent')
    ap.add_argument('--items', default=None, help='题库路径；默认优先 items/v1.1，否则 v1.0')
    args = ap.parse_args()

    items_path = args.items or default_items_path()
    items = load_items(items_path)
    print(f'items={items_path}  n={len(items)}')

    by_task, by_sub, errs, judged = defaultdict(list), defaultdict(list), 0, 0
    for f in glob.glob(os.path.join(ROOT, 'results', args.model, '*.json')):
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

    print(f'===== 模型: {args.model} =====')
    print(f'已评: {sum(len(v) for v in by_task.values())}  待评委(llm_rubric): {judged}  错误: {errs}')
    tot_all = [s for v in by_task.values() for s in v]
    if tot_all:
        print(f'可机判题总得分率: {sum(tot_all)/len(tot_all)*100:.1f}%  (n={len(tot_all)})')
    else:
        print('可机判题总得分率: n/a  (n=0)')
    print()
    for t in ('KNO', 'ERR', 'SCO', 'GEN', 'CUL', 'PED', 'PHO'):
        v = by_task.get(t)
        if v: print(f'{t}: {sum(v)/len(v)*100:.1f}%  (n={len(v)})')
    print()
    for st, v in sorted(by_sub.items()):
        print(f'  {st}: {sum(v)/len(v)*100:.1f}%  (n={len(v)})')


if __name__ == '__main__':
    main()
