# -*- coding: utf-8 -*-
"""审稿修改实验：A. 打分分布信息熵；B. 两两 LLM 在 250 篇作文上的一致性"""
import json, os, re, glob
import numpy as np

ROOT = '.'
KEYS = ['deepseek', 'qwen', 'zhipu', 'ernie', 'grok', 'stepfun', 'doubao', 'hunyuan',
        'k2d6-agent', 'k3-agent', 'tchub-dsv4f']
NAMES = {'deepseek': 'deepseek-chat', 'qwen': 'qwen-flash', 'zhipu': 'glm-4-flash',
         'ernie': 'ernie-4.5-turbo', 'grok': 'grok-3-mini-fast', 'stepfun': 'step-3.7-flash',
         'doubao': 'doubao-seed-1-6', 'hunyuan': 'hy3', 'k2d6-agent': 'k2d6-agent',
         'k3-agent': 'k3-agent', 'tchub-dsv4f': 'deepseek-v4-flash'}

gold, band_of = {}, {}
for l in open('items/v1.1/items.jsonl', encoding='utf-8'):
    r = json.loads(l)
    if r.get('sub_type') == 'sco.essay_score':
        gold[r['item_id']] = float(r['reference']['answer'])
        band_of[r['item_id']] = next(t for t in r['meta']['tags'] if t.startswith('band'))
SCO_IDS = sorted(gold)

def extract_score(output):
    if not output:
        return None
    m = re.search(r'"score"\s*[:：]\s*"?(\d+)', str(output))
    if not m:
        m = re.search(r'(\d+)\s*分', str(output))
    if m:
        s = int(m.group(1))
        return float(s) if 0 <= s <= 100 else None
    return None

def clean0(t):
    for ch in ['\u200b', '\u200c', '\u200d', '\ufeff', '\u2060']:
        t = t.replace(ch, '')
    return t

# ===== A. 信息熵 =====
print('===== 打分分布信息熵 =====')
H = {}
for key in KEYS:
    P = []
    for iid in SCO_IDS:
        f = f'results/{key}/{iid}.json'
        if not os.path.exists(f):
            continue
        d = json.load(open(f, encoding='utf-8'))
        s = extract_score(clean0(d.get('output') or ''))
        if s is None:
            continue
        P.append(s)
    P = np.array(P)
    vals, cnts = np.unique(P, return_counts=True)
    p = cnts / cnts.sum()
    h = float(-(p * np.log2(p)).sum())
    H[key] = round(h, 2)
    print(f'{NAMES[key]:20s} 唯一分值 {len(vals):3d}  熵 H={h:.2f} bit  最大点 {int(vals[cnts.argmax()])}分×{int(cnts.max())}')

# ===== B. 两两 LLM 一致性 =====
print()
print('===== 两两模型作文评分一致性 =====')
preds = {}
for key in KEYS:
    P, ids = [], []
    for iid in SCO_IDS:
        f = f'results/{key}/{iid}.json'
        if not os.path.exists(f):
            continue
        d = json.load(open(f, encoding='utf-8'))
        s = extract_score(clean0(d.get('output') or ''))
        if s is None:
            continue
        P.append(s)
        ids.append(iid)
    preds[key] = dict(zip(ids, P))

pairs_data = []
keys = list(preds)
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        a, b = keys[i], keys[j]
        common = sorted(set(preds[a]) & set(preds[b]))
        A = np.array([preds[a][k] for k in common])
        B = np.array([preds[b][k] for k in common])
        r = float(np.corrcoef(A, B)[0, 1])
        ra = np.argsort(np.argsort(A))
        rb = np.argsort(np.argsort(B))
        rho = float(np.corrcoef(ra, rb)[0, 1])
        pairs_data.append({'a': NAMES[a], 'b': NAMES[b], 'n': len(common),
                           'pearson': round(r, 3), 'spearman': round(rho, 3),
                           'MAD': round(float(np.abs(A - B).mean()), 1),
                           'bias': round(float((B - A).mean()), 1)})
pairs_data.sort(key=lambda x: -x['spearman'])
for p in pairs_data[:6]:
    print(f"{p['a']:18s} vs {p['b']:18s} n={p['n']} r={p['pearson']:.3f} rho={p['spearman']:.3f} MAD={p['MAD']:.1f} bias={p['bias']:+.1f}")
rhos = [p['spearman'] for p in pairs_data]
mads = [p['MAD'] for p in pairs_data]
print(f'共 {len(pairs_data)} 对；Spearman 范围 {min(rhos):.3f}–{max(rhos):.3f}；MAD 范围 {min(mads):.1f}–{max(mads):.1f}')

# 熵与并列的关系：熵 vs uniq
print()
print('熵排序:', {NAMES[k]: H[k] for k in sorted(H, key=lambda x: -H[x])})

out = {'熵': {NAMES[k]: H[k] for k in H}, '两两一致性': pairs_data,
       '熵说明': 'H=-p(s)log2p(s) 求和；理论最大 log2(250)≈7.97 bit'}
json.dump(out, open('report/论文三_熵与两两一致性.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('保存: report/论文三_熵与两两一致性.json')