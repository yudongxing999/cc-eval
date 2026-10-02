# -*- coding: utf-8 -*-
"""gold 选项位置均衡化：对 multiple_choice jsonl，重排每题选项顺序，
使 gold 位置在全体题目上尽量均匀（轮转 + 种子洗牌），消除众数猜测先验。
用法: ../.venv/Scripts/python.exe balance_gold.py <in.jsonl> <out.jsonl> [--seed 42]
"""
import json, random, sys, os


def balance(inp, outp, seed=42):
    rows = [json.loads(l) for l in open(inp, encoding='utf-8')]
    rng = random.Random(seed)
    # 按选项数分组，组内轮转均匀分配 gold 位置
    groups = {}
    for idx, r in enumerate(rows):
        groups.setdefault(len(r['choices']), []).append(idx)
    for k, idxs in sorted(groups.items()):
        targets = [(i % k) for i in range(len(idxs))]
        rng.shuffle(targets)
        for i, tgt in zip(idxs, targets):
            r = rows[i]
            ch = list(r['choices'])
            g = r['gold']
            if g != tgt:
                ch[g], ch[tgt] = ch[tgt], ch[g]
                r['choices'] = ch
                r['gold'] = tgt
    with open(outp, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    from collections import Counter
    print(os.path.basename(outp), 'gold 分布:', dict(sorted(Counter(r['gold'] for r in rows).items())))


if __name__ == '__main__':
    seed = 42
    if '--seed' in sys.argv:
        i = sys.argv.index('--seed')
        seed = int(sys.argv[i + 1])
        sys.argv = sys.argv[:i] + sys.argv[i + 2:]
    balance(sys.argv[1], sys.argv[2], seed)
