# -*- coding: utf-8 -*-
"""论文二全量审计：11 模型 × 120 道限级改写题 = 1,320 篇输出
与官方判分口径严格一致（复用 runner/run_eval.py 的 check_vocab_level）
输出：report/论文二_全量审计.json
"""
import json, glob, re, sys, collections

sys.path.insert(0, 'runner')
from run_eval import check_vocab_level, clean_output

REPO = '.'
MODELS = ['deepseek', 'qwen', 'zhipu', 'ernie', 'grok', 'stepfun', 'doubao', 'hunyuan',
          'k2d6-agent', 'k3-agent', 'tchub-dsv4f']
NAMES = {'deepseek': 'deepseek-chat', 'qwen': 'qwen-flash', 'zhipu': 'glm-4-flash',
         'ernie': 'ernie-4.5-turbo', 'grok': 'grok-3-mini-fast', 'stepfun': 'step-3.7-flash',
         'doubao': 'doubao-seed-1-6', 'hunyuan': 'hy3', 'k2d6-agent': 'k2d6-agent',
         'k3-agent': 'k3-agent', 'tchub-dsv4f': 'deepseek-v4-flash'}

items = {json.loads(l)['item_id']: json.loads(l) for l in open('items/v1.1/items.jsonl', encoding='utf-8')}
lvl_ids = [i for i in items if i.startswith('CCE-GEN') and '改写' in (items[i]['meta'].get('tags') or [])]
assert len(lvl_ids) == 120

# 官方词表（级差与密度分析用）
import run_eval
lx = run_eval.load_lexicon()
WL, CL = lx['word_lvl'], lx['char_lvl']

def lvl_of_word(w):
    return WL.get(w)

def target_level(iid):
    m = re.search(r'(\d)\s*级', items[iid]['prompt']['instruction'])
    return int(m.group(1))

def hanzi_count(s):
    return sum(1 for c in s if '一' <= c <= '鿿')

def char_bigram_overlap(a, b):
    """粗糙内容保真代理：原文与改写的汉字 bigram Jaccard"""
    def bg(s):
        s = re.sub(r'[^\u4e00-\u9fff]', '', s)
        return {s[i:i+2] for i in range(len(s)-1)}
    A, B = bg(a), bg(b)
    return len(A & B) / max(len(A | B), 1)

audit = {}
for m in MODELS:
    per_item = []
    for iid in lvl_ids:
        f = f'results/{m}/{iid}.json'
        try:
            d = json.load(open(f, encoding='utf-8'))
        except FileNotFoundError:
            continue
        cap = target_level(iid)
        out = clean_output(d['output'] or '')
        orig = items[iid]['prompt'].get('input') or ''
        ok, viol = check_vocab_level(out, cap)
        # 违规详情：词 + 级差
        vdetail = []
        for v in viol:
            wlvl = lvl_of_word(v)
            if wlvl is None:
                wlvl = CL.get(v[0] if v in CL else v, 7) if len(v) == 1 else 7
                # 单字兜底：char_lvl 查首字
                wlvl = CL.get(v, 7)
            gap = (9 if wlvl not in (1,2,3,4,5,6) else wlvl) - cap
            vdetail.append({'w': v, 'lvl': wlvl, 'gap': gap})
        per_item.append({
            'item_id': iid, 'target': cap, 'pass': ok, 'score': d['score'],
            'n_viol': len(viol),
            'viol_density': len(viol) / max(hanzi_count(out) / 100, 0.01),
            'gaps': [v['gap'] for v in vdetail],
            'viol_words': [v['w'] for v in vdetail],
            'out_len': len(out), 'orig_len': len(orig),
            'len_ratio': len(out) / max(len(orig), 1),
            'overlap': char_bigram_overlap(orig, out),
            'hnz': hanzi_count(out),
        })
    audit[m] = per_item

json.dump(audit, open('report/论文二_全量审计.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('写入 report/论文二_全量审计.json')

# ===== 汇总表 =====
print(f"\n{'模型':>20} | {'通过率':>6} | {'违规/百字':>8} | {'均值Δ(级差)':>10} | {'长比':>5} | {'保真':>5}")
for m in MODELS:
    P = audit[m]
    pr = sum(1 for p in P if p['pass']) / len(P) * 100
    dens = sum(p['viol_density'] for p in P) / len(P)
    allg = [g for p in P for g in p['gaps']]
    mg = sum(allg) / max(len(allg), 1)
    lr = sum(p['len_ratio'] for p in P) / len(P)
    ov = sum(p['overlap'] for p in P) / len(P)
    print(f"{NAMES[m]:>20} | {pr:5.1f}% | {dens:8.1f} | {mg:10.1f} | {lr:5.2f} | {ov:5.3f}")

# 全局违规词 Top（跨模型共性——"标准 vs 自然语言"错配证据）
top = collections.Counter()
for m in MODELS:
    for p in audit[m]:
        for w in set(p['viol_words']):
            top[w] += 1
print('\n违规词 Top 20（出现于多少题×模型组合）:')
for w, n in top.most_common(20):
    print(f'  {w}: {n} | GF0025 级: {WL.get(w, CL.get(w, "?"))}')