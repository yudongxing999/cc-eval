# -*- coding: utf-8 -*-
"""审稿加固分析：
1) SCO：各模型作文分与人工分的 Pearson r / Spearman rho / QWK（10分档离散）
2) GEN：各模型限级改写的平均超限词率 OOV%（FMM 切分，逐题重算）
"""
import os, sys, json, glob, re, math, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_eval import check_vocab_level, load_lexicon, clean_output

def default_items_path():
    """v1.1 是 v1.0 超集（含 PHO）；优先用 v1.1，避免分析时静默丢题。"""
    v11 = os.path.join(ROOT, 'items/v1.1/items.jsonl')
    v10 = os.path.join(ROOT, 'items/v1.0/items.jsonl')
    return v11 if os.path.isfile(v11) else v10

_items_path = os.environ.get('CCEVAL_ITEMS') or default_items_path()
items = {i['item_id']: i for i in (json.loads(l) for l in open(_items_path, encoding='utf-8'))}
print(f'items={_items_path}  n={len(items)}')
MODELS = ['k3-agent','deepseek','tchub-dsv4f','hunyuan','grok','k2d6-agent','ernie','qwen','doubao','stepfun','zhipu']

def extract_score(out):
    m = re.search(r'"score"\s*[:：]\s*(\d+)', out)
    if not m: m = re.search(r'(\d{1,3})\s*分', out)
    if not m: m = re.search(r'\b(\d{1,3})\b', clean_output(out))
    return float(m.group(1)) if m else None

def pearson(x, y):
    n=len(x); mx=statistics.mean(x); my=statistics.mean(y)
    cov=sum((a-mx)*(b-my) for a,b in zip(x,y))
    sx=sum((a-mx)**2 for a in x)**.5; sy=sum((b-my)**2 for b in y)**.5
    return cov/(sx*sy) if sx*sy else None

def spearman(x, y):
    n=len(x)
    def ranks(v):
        order=sorted(range(n), key=lambda i: v[i]); r=[0]*n; i=0
        while i<n:
            j=i
            while j+1<n and v[order[j+1]]==v[order[i]]: j+=1
            for k in range(i,j+1): r[order[k]]=(i+j)/2+1
            i=j+1
        return r
    return pearson(ranks(x), ranks(y))

def qwk(x, y, bands=10):
    """二次加权卡帕，按 bands 分一档离散（0-100 -> 11 档 when bands=10）"""
    def band(v): return min(int(v//bands), int(100//bands))
    cats = int(100//bands)+1
    O=[[0]*cats for _ in range(cats)]
    for a,b in zip(x,y): O[band(a)][band(b)]+=1
    n=len(x)
    hx=[sum(r) for r in O]; hy=[sum(O[i][j] for i in range(cats)) for j in range(cats)]
    num=den=0.0
    for i in range(cats):
        for j in range(cats):
            w=(i-j)**2/((cats-1)**2)
            E=hx[i]*hy[j]/n if n else 0
            num+=w*O[i][j]; den+=w*E
    return 1-num/den if den else None

# ---------- FMM 切词计数版（用于 OOV 率） ----------
def segment_count(text, max_lvl):
    lx = load_lexicon()
    wl, cl, mx = lx['word_lvl'], lx['char_lvl'], lx['maxlen']
    n_tok, n_oov, i = 0, 0, 0
    text = re.sub(r'[a-zA-Z0-9]+', '', text)
    while i < len(text):
        ch = text[i]
        if not '一' <= ch <= '鿿': i += 1; continue
        hit = None
        for L in range(min(mx, len(text)-i), 1, -1):
            w = text[i:i+L]
            if w in wl: hit = w; break
        if hit:
            n_tok += 1
            if wl[hit] > max_lvl: n_oov += 1
            i += len(hit)
        else:
            n_tok += 1
            if cl.get(ch, 7) > max_lvl: n_oov += 1
            i += 1
    return n_tok, n_oov

sco_out, gen_out = {}, {}
for name in MODELS:
    d = os.path.join(ROOT, 'results', name)
    if not os.path.isdir(d): continue
    # SCO
    preds, golds = [], []
    for f in glob.glob(os.path.join(d, 'CCE-SCO-*.json')):
        r = json.load(open(f, encoding='utf-8'))
        it = items.get(r['item_id'])
        if not it or r.get('error'): continue
        p = extract_score(r.get('output',''))
        if p is None: continue
        preds.append(p); golds.append(float(it['reference']['answer']))
    if preds:
        sco_out[name] = {
            'n': len(preds),
            'pearson_r': round(pearson(preds, golds), 4),
            'spearman_rho': round(spearman(preds, golds), 4),
            'qwk_10pt': round(qwk(preds, golds, 10), 4),
            'pred_mean': round(statistics.mean(preds), 1),
            'gold_mean': round(statistics.mean(golds), 1),
            'pred_sd': round(statistics.pstdev(preds), 1),
        }
    # GEN 限级改写（deterministic_rule）
    rates = []
    for f in glob.glob(os.path.join(d, 'CCE-GEN-*.json')):
        r = json.load(open(f, encoding='utf-8'))
        it = items.get(r['item_id'])
        if not it or it['scoring']['type'] != 'deterministic_rule' or r.get('error'): continue
        out = clean_output(r.get('output',''))
        if not out: continue
        max_lvl = it['scoring']['params'].get('max_vocab_level', 9)
        n_tok, n_oov = segment_count(out, max_lvl)
        if n_tok: rates.append(n_oov / n_tok)
    if rates:
        gen_out[name] = {'n': len(rates), 'oov_rate_mean_pct': round(100*statistics.mean(rates), 2),
                         'oov_rate_median_pct': round(100*statistics.median(rates), 2)}

res = {'SCO_correlations': sco_out, 'GEN_oov': gen_out}
out_path = os.path.join(ROOT, 'results', 'review_metrics.json')
json.dump(res, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps(res, ensure_ascii=False, indent=2))
print('saved:', out_path)
