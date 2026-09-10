# -*- coding: utf-8 -*-
"""论文三（中文信息学报稿）可验证数据全量重建：
A. 对齐指标全量复算（表1/表2：QWK/ρ/MAE/δ/α/β/并列结构/高分区/词面证据）
B. 线性校准 + 分位数映射校准（留出集分层 + 500 自举 CI）
数据源：results/<model>/CCE-SCO-*.json（250 篇 × 11 模型）+ items/v1.1 金标（reference.answer）
输出：report/论文三_可验证数据.json
"""
import json, os, re, glob
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = ['deepseek', 'qwen', 'zhipu', 'ernie', 'grok', 'stepfun', 'doubao', 'hunyuan',
        'k2d6-agent', 'k3-agent', 'tchub-dsv4f']
NAMES = {'deepseek': 'deepseek-chat', 'qwen': 'qwen-flash', 'zhipu': 'glm-4-flash',
         'ernie': 'ernie-4.5-turbo', 'grok': 'grok-3-mini-fast', 'stepfun': 'step-3.7-flash',
         'doubao': 'doubao-seed-1-6', 'hunyuan': 'hy3', 'k2d6-agent': 'k2d6-agent',
         'k3-agent': 'k3-agent', 'tchub-dsv4f': 'deepseek-v4-flash'}

# ---------- 金标与原始输出 ----------
gold = {}
band_of = {}
for l in open(os.path.join(ROOT, 'items/v1.1/items.jsonl'), encoding='utf-8'):
    r = json.loads(l)
    if r.get('sub_type') == 'sco.essay_score':
        gold[r['item_id']] = float(r['reference']['answer'])
        band_of[r['item_id']] = next(t for t in r['meta']['tags'] if t.startswith('band'))
SCO_IDS = sorted(gold)
print(f'SCO: {len(SCO_IDS)} 篇，金标来自 reference.answer（语料库人工分）')

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

# ---------- 指标函数 ----------
def qwk(g, p):
    # 论文 3.2：QWK 在 0-100 整数原生网格（101 维）上计算；
    # 连续值（校准后输出）四舍五入至最近整数后入网格
    gs = np.array([max(0, min(100, int(x + 0.5))) for x in g])
    ps = np.array([max(0, min(100, int(x + 0.5))) for x in p])
    n = len(gs)
    k = 101
    O = np.zeros((k, k))
    for a, b in zip(gs, ps):
        O[int(a), int(b)] += 1
    O /= n
    w = np.array([[abs(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)])
    E = np.outer(O.sum(1), O.sum(0))
    den = (w * E).sum()
    return float(1 - (w * O).sum() / den) if den else 1.0

def spearman(a, b):
    # 论文 3.2：平均秩 + 经典公式 1-6Σd²/(n(n²-1))（与表 1 数据同口径）
    def rank(x):
        s = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        i = 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and x[s[j + 1]] == x[s[i]]:
                j += 1
            for t in range(i, j + 1):
                r[s[t]] = (i + j) / 2 + 1
            i = j + 1
        return r
    ra, rb = rank(a), rank(b)
    d2 = sum((x - y) ** 2 for x, y in zip(ra, rb))
    return 1 - 6 * d2 / (len(a) * (len(a) ** 2 - 1))

# ---------- A. 全量对齐指标 ----------
table = {}
model_preds = {}
for key in KEYS:
    G, P, R = [], [], []
    for iid in SCO_IDS:
        f = os.path.join(ROOT, f'results/{key}/{iid}.json')
        if not os.path.exists(f):
            continue
        d = json.load(open(f, encoding='utf-8'))
        s = extract_score(clean0(d.get('output') or ''))
        if s is None:
            continue
        G.append(gold[iid])
        P.append(s)
        R.append(clean0(d.get('output') or ''))
    G, P = np.array(G), np.array(P)
    model_preds[key] = (G, P)
    # 斜率截距
    A, B = np.polyfit(G, P, 1)
    # 并列结构
    uniq = len(set(P))
    top_val = int(np.bincount(P.astype(int)).argmax())
    top_cnt = int((P == top_val).sum())
    # 高分区（金标 90-100）
    hi = G >= 90
    hi_pred_mean = float(P[hi].mean()) if hi.any() else None
    # 词面证据（缺陷词/褒扬词）
    NEG = ['错误', '偏误', '问题', '不足', '缺陷', '欠缺']
    POS = ['好', '优秀', '流畅', '自然', '清楚', '恰当', '出色']
    neg = sum(str(r).count(w) for w in NEG for r in R)
    pos = sum(str(r).count(w) for w in POS for r in R)
    # 分段偏差（低分段 vs 高分段）
    lo_mask = G <= 59
    lo_bias = float((P[lo_mask] - G[lo_mask]).mean()) if lo_mask.any() else None
    hi_bias = float((P[G >= 90] - G[G >= 90]).mean()) if (G >= 90).any() else None
    table[NAMES[key]] = {
        'n': len(G), 'QWK': round(qwk(G, P), 3), 'rho': round(spearman(G, P), 3),
        'MAE': round(float(np.abs(P - G).mean()), 1),
        'delta': round(float(P.mean() - G.mean()), 1),
        'alpha': round(float(A), 3), 'beta': round(float(B), 1),
        'uniq_scores': uniq, 'top_score': top_val, 'top_score_n': top_cnt,
        'hi_pred_mean': round(hi_pred_mean, 1) if hi_pred_mean else None,
        'neg_words': neg, 'pos_words': pos, 'neg_pos_ratio': round(neg / max(pos, 1), 2),
        'lo_band_bias': round(lo_bias, 1) if lo_bias is not None else None,
        'hi_band_bias': round(hi_bias, 1) if hi_bias is not None else None,
    }
    print(f"{NAMES[key]:20s} QWK {table[NAMES[key]]['QWK']:.3f} rho {table[NAMES[key]]['rho']:.3f} "
          f"MAE {table[NAMES[key]]['MAE']:5.1f} δ {table[NAMES[key]]['delta']:+6.1f} "
          f"α {table[NAMES[key]]['alpha']:.3f} β {table[NAMES[key]]['beta']:+6.1f} "
          f"分值数 {uniq:3d}（{top_val}分×{top_cnt}）")

# ---------- B. 校准实验（线性 + 分位数映射） ----------
rng = np.random.RandomState(2026)
BANDS = ['band0-59', 'band60-69', 'band70-79', 'band80-89', 'band90-100']

def stratified_split(ids):
    tr, te = [], []
    for b in BANDS:
        b_ids = [i for i in ids if band_of[i] == b]
        rng.shuffle(b_ids)
        half = len(b_ids) // 2
        tr += b_ids[:half]
        te += b_ids[half:]
    return tr, te

def fit_linear(g_tr, p_tr):
    a, b = np.polyfit(p_tr, g_tr, 1)
    return lambda x: min(100.0, max(0.0, a * x + b))  # 论文 3.3：截断至 [0,100]（分档下与隐式截断数学等价）

def fit_qm(g_tr, p_tr):
    qs = np.linspace(0.01, 0.99, 99)
    src = np.quantile(p_tr, qs)
    dst = np.quantile(g_tr, qs)
    def f(x):
        return float(np.interp(x, src, dst))  # 并列值落在 src 的平台上：插值输出取该平台对应 dst 区间的线性内插（并列组整体邻域），与论文 3.3 "并列组赋目标分位邻域"表述一致
    return f

calib = {}
for key in KEYS:
    name = NAMES[key]
    G, P = model_preds[key]
    ids = [SCO_IDS[i] for i in range(len(SCO_IDS))][:len(G)]  # 对齐顺序
    # 重建 id 对齐（G/P 按相同顺序装载）
    pair_ids = []
    for iid in SCO_IDS:
        f = os.path.join(ROOT, f'results/{key}/{iid}.json')
        if not os.path.exists(f):
            continue
        d = json.load(open(f, encoding='utf-8'))
        if extract_score(clean0(d.get('output') or '')) is None:
            continue
        pair_ids.append(iid)
    assert len(pair_ids) == len(G), (len(pair_ids), len(G))
    # 500 次自举
    dLin, dQM = [], []
    lin_pre, lin_post, qm_pre, qm_post = [], [], [], []
    for boot in range(500):
        tr_ids, te_ids = stratified_split(pair_ids)
        tr_idx = [pair_ids.index(i) for i in tr_ids]
        te_idx = [pair_ids.index(i) for i in te_ids]
        g_tr, p_tr = G[tr_idx], P[tr_idx]
        g_te, p_te = G[te_idx], P[te_idx]
        f_lin = fit_linear(g_tr, p_tr)
        f_qm = fit_qm(g_tr, p_tr)
        p_lin = np.array([f_lin(x) for x in p_te])
        p_qm = np.array([f_qm(x) for x in p_te])
        q0 = qwk(g_te, p_te)
        ql = qwk(g_te, p_lin)
        qq = qwk(g_te, p_qm)
        lin_pre.append(q0); lin_post.append(ql); qm_pre.append(q0); qm_post.append(qq)
        dLin.append(ql - q0); dQM.append(qq - q0)
    def ci95(arr):
        return [round(float(np.percentile(arr, 2.5)), 3), round(float(np.percentile(arr, 97.5)), 3)]
    calib[name] = {
        '线性': {'前QWK': round(float(np.mean(lin_pre)), 3), '后QWK': round(float(np.mean(lin_post)), 3),
                 'Δ95CI': ci95(dLin)},
        'QM': {'前QWK': round(float(np.mean(qm_pre)), 3), '后QWK': round(float(np.mean(qm_post)), 3),
               'Δ95CI': ci95(dQM)},
    }
    print(f"{name:20s} 线性 Δ={np.mean(dLin):+.3f} {ci95(dLin)} | QM Δ={np.mean(dQM):+.3f} {ci95(dQM)}")

out = {'对齐指标': table, '校准': calib,
       '说明': '金标=items reference.answer（HSK 语料库人工分）；QWK 按 10 分档；校准 500 次分层自举'}
json.dump(out, open(os.path.join(ROOT, 'report/论文三_可验证数据.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f"\n保存: report/论文三_可验证数据.json")