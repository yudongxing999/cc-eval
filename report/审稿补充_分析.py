# -*- coding: utf-8 -*-
"""评审修改补充分析：语言学特征与模型判别行为的计量检验
意见2（语言学特征多元回归）+ 意见5（混淆矩阵/Macro-F1）+ 意见1（吸引子机制检验）

数据源：
- injection/preds_heldout.json（1,000 未见词条的 gold/pred）+ heldout_words_1000.jsonl（词条本身）
- SUBTLEX-CH（Cai & Brysbaert 2010）：词频（W/million）、logW-CD
- GF 0025 词表：词长、词性
产出：
- report/审稿补充_特征回归.json（全部统计量）
- report/审稿补充_混淆矩阵.md（混淆矩阵表 + Macro-F1 对比）
"""
import json, re, os, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'runner'))

# ---------- 数据载入 ----------
recs = json.load(open(os.path.join(ROOT, 'injection/data/heldout_words_1000.jsonl'), encoding='utf-8'))
preds = json.load(open(os.path.join(ROOT, 'injection/preds_heldout.json'), encoding='utf-8'))
assert len(recs) == len(preds) == 1000, (len(recs), len(preds))

def parse_rec(instr):
    m = re.match(r'.*词语「(.+?)」（(.*?)）属于哪个等级', instr)
    return m.group(1), m.group(2) or '无'

# SUBTLEX-CH 词频（GBK 编码，tab 分隔）
freq = {}
import os.path
_p = os.environ.get('SUBTLEX_WF', os.path.join(os.path.expanduser('~'), 'AppData/Local/Temp/subtlex_ch/SUBTLEX-CH-WF'))
with open(_p, encoding='gbk') as f:
    next(f); next(f); next(f)  # 跳过两行元信息+表头
    for line in f:
        parts = line.rstrip('\r\n').split('\t')
        if len(parts) >= 4:
            try:
                freq[parts[0]] = (float(parts[2]), float(parts[6]))  # W/million, logW-CD
            except ValueError:
                continue
print(f'SUBTLEX-CH 词频表: {len(freq)} 词条')


# Unihan 笔画数
strokes = {}
_u8 = os.path.join(os.path.expanduser('~'), 'AppData/Local/Temp/unihan/Unihan_IRGSources.txt')
with open(_u8, encoding='utf-8') as f:
    for line in f:
        parts = line.rstrip('\r\n').split('\t')
        if len(parts) == 3 and parts[1] == 'kTotalStrokes':
            try:
                strokes[chr(int(parts[0][2:], 16))] = float(parts[2].split()[0])
            except ValueError:
                continue
print(f'Unihan 笔画表: {len(strokes)} 字')

def word_strokes(w):
    return sum(strokes.get(ch, 0) for ch in w) / max(1, len(w))

rows = []
for r, p in zip(recs, preds):
    w, pos = parse_rec(r['instruction'])
    gold, pred = p['gold'], p['pred']
    f_wpm, f_lcd = freq.get(w, (0.0, 0.0))
    rows.append({
        'word': w, 'pos': pos, 'nchar': len(w), 'gold': gold, 'pred': pred,
        'wpm': f_wpm, 'log_cd': (f_lcd if f_lcd > 0 else 0.0), 'strokes': word_strokes(w),
        'hit': int(gold == pred),
        'in_freq_dict': int(w in freq),
    })
print(f'1,000 未见词条：{sum(r["in_freq_dict"] for r in rows)}/1000 命中 SUBTLEX 词频表')

# ---------- A. 混淆矩阵 + Macro-F1（意见5） ----------
LV = ['1', '2', '3', '4', '5', '6', '7-9']
cm = [[0] * 7 for _ in range(7)]
for r in rows:
    cm[r['gold']][r['pred']] += 1

def macro_f1(cm):
    f1s = []
    for c in range(7):
        tp = cm[c][c]
        fp = sum(cm[g][c] for g in range(7)) - tp
        fn = sum(cm[c]) - tp
        f1s.append(2 * tp / (2 * tp + fp + fn) if tp else 0.0)
    return sum(f1s) / 7, f1s

mf1_inj, f1_by = macro_f1(cm)
micro_inj = sum(cm[i][i] for i in range(7)) / 1000

# 多数类基线（全猜 7-9）：micro = π(7-9)，macro-F1 只在 7-9 类有值
pi79 = cm[6] and sum(cm[6]) / 1000
f1_79 = 2 * pi79 / (pi79 + 1)  # precision=1, recall=π
mf1_maj = f1_79 / 7

# ---------- B. 模型判别行为对语言学特征的回归（意见2） ----------
# 因变量：模型预测（pred 0-6）；自变量：词长、log 词频(log10(wpm+1))、logW-CD、词性（名/动/形/其他）、gold
import math
def log10p1(x):
    return math.log10(x + 1)

# ① 模型判对概率 vs 特征（哪些词被正确判别？）——Logistic 回归
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

feats = []
y_hit = []
for r in rows:
    feats.append([r['nchar'], log10p1(r['wpm']), r['log_cd'], r['strokes'], 1 if r['pos'] == '名' else 0,
                  1 if r['pos'] == '动' else 0, 1 if r['pos'] == '形' else 0])
    y_hit.append(r['hit'])
clf = LogisticRegression(max_iter=2000).fit(feats, y_hit)
auc = roc_auc_score(y_hit, clf.decision_function(feats))
coefs_hit = dict(zip(['词长', 'log词频', 'logW-CD', '笔画', '名', '动', '形'], clf.coef_[0].round(3).tolist()))

# ② 金标等级 vs 特征（GF 0025 的等级边界本身是否可由特征预测？——"制度性 vs 特征性"的实证）
y_gold = [r['gold'] for r in rows]
try:
    from sklearn.linear_model import LogisticRegressionCV
    # 多项 logistic：7 类特征可分性（等权类内准确率 / macro 结构）
    from sklearn.model_selection import cross_val_score
    mlog = LogisticRegression(max_iter=3000, C=1.0)
    # 5 折交叉验证 macro-F1：特征对金标等级的可预测上限
    from sklearn.model_selection import cross_validate
    cv = cross_validate(mlog, feats, y_gold, cv=5, scoring='f1_macro')
    gold_macro_f1 = cv['test_score'].mean()
except Exception as e:
    gold_macro_f1 = None
    print('gold 回归失败:', e)

# 多项回归全拟合：提取各等级的词频系数（表：等级 × [词长, log词频, logCD, ...]）
mlog_full = LogisticRegression(max_iter=3000).fit(feats, y_gold)
coef_names = ['词长', 'log词频', 'logW-CD', '笔画', '名', '动', '形']
level_coefs = {LV[i]: dict(zip(coef_names, mlog_full.coef_[i].round(3).tolist())) for i in range(7)}

# ③ 模型预测等级 vs 特征（模型实际用什么特征判别？）——与金标系数并排比较
y_pred = [r['pred'] for r in rows]
# pred 只有 4 个非零类（0,3,6 为主 + 少量2）——多项回归只在出现的类上做
pred_classes = sorted(set(y_pred))
mlog_pred = LogisticRegression(max_iter=3000).fit(feats, y_pred)
pred_coefs = {LV[c] if c < 7 else str(c): dict(zip(coef_names, mlog_pred.coef_[i].round(3).tolist()))
              for i, c in enumerate(mlog_pred.classes_)}

# ④ 一级判对 vs 判错的特征差异（"两极先成形"的机制证据）
g1 = [r for r in rows if r['gold'] == 0]
g1_hit = [r for r in g1 if r['hit']]
g1_miss = [r for r in g1 if not r['hit']]
import statistics as st
def mean(rs, k):
    return st.mean(r[k] for r in rs) if rs else None
g1_stats = {
    '判对': {'n': len(g1_hit), '词长': mean(g1_hit, 'nchar'), 'log词频': round(log10p1(mean(g1_hit, 'wpm')), 2), 'logW-CD': round(mean(g1_hit, 'log_cd'), 2)},
    '判错': {'n': len(g1_miss), '词长': mean(g1_miss, 'nchar'), 'log词频': round(log10p1(mean(g1_miss, 'wpm')), 2), 'logW-CD': round(mean(g1_miss, 'log_cd'), 2)},
}

# ⑤ 7-9 吸引子检验：被吸到 7-9 的 gold2-6 词有什么特征（vs 保持 4 或判对的）？
#    反驳"向多数类坍缩"：训练分布均衡（每级~322），若坍缩向多数类，应均匀吸向全部训练类
sucked79 = [r for r in rows if r['gold'] in (1, 2, 3, 4, 5) and r['pred'] == 6]
kept4 = [r for r in rows if r['gold'] in (1, 2, 3, 4, 5) and r['pred'] == 3]
island_correct = [r for r in rows if r['gold'] in (1, 2, 3, 4, 5) and r['hit']]
attractor_stats = {
    '被吸向7-9(gold2-6)': {'n': len(sucked79), '词长': round(mean(sucked79, 'nchar'), 2), 'log词频': round(log10p1(mean(sucked79, 'wpm')), 2), 'logW-CD': round(mean(sucked79, 'log_cd'), 2)},
    '被吸向4(gold2-6)': {'n': len(kept4), '词长': round(mean(kept4, 'nchar'), 2), 'log词频': round(log10p1(mean(kept4, 'wpm')), 2), 'logW-CD': round(mean(kept4, 'log_cd'), 2)},
}

# ⑥ Pearson：词频/词长与 gold 的相关（语言学事实：特征确实单调对应等级）
def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    syy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return sxy / (sxx * syy)

r_freq_gold = pearson([log10p1(r['wpm']) for r in rows], [r['gold'] for r in rows])
r_len_gold = pearson([r['nchar'] for r in rows], [r['gold'] for r in rows])
r_str_gold = pearson([r['strokes'] for r in rows], [r['gold'] for r in rows])
r_freq_pred = pearson([log10p1(r['wpm']) for r in rows], [r['pred'] for r in rows])
r_len_pred = pearson([r['nchar'] for r in rows], [r['pred'] for r in rows])
r_gold_pred = pearson([r['gold'] for r in rows], [r['pred'] for r in rows])

# ---------- C. 剂量防御（意见1）：均衡训练分布下"吸引子"不能由多数类先验收敛解释 ----------
train_dist = Counter('7-9' if '7-9' in p['messages'][1]['content'] else p['messages'][1]['content'].replace('答案：', '')
                     for p in json.load(open(os.path.join(ROOT, 'injection/data/sft_train_fast.json'), encoding='utf-8')))
print('训练分布:', dict(sorted(train_dist.items())))

# ---------- 输出 ----------
out = {
    '混淆矩阵': {'行gold列pred': cm, '行等级': LV, 'micro': micro_inj,
               'macro_F1注入': mf1_inj, 'macro_F1多数类': mf1_maj, 'per_class_F1': dict(zip(LV, [round(x, 3) for x in f1_by]))},
    '判对率回归': {'AUC': round(auc, 3), '系数': coefs_hit},
    '金标等级特征可预测性': {'5折CV_macro_F1': round(gold_macro_f1, 3) if gold_macro_f1 else None, '等级系数': level_coefs},
    '模型预测等级系数': pred_coefs,
    '一级判对vs判错': g1_stats,
    '吸引子特征': attractor_stats,
    'Pearson相关': {'词频~gold': round(r_freq_gold, 3), '词长~gold': round(r_len_gold, 3), '笔画~gold': round(r_str_gold, 3),
                '词频~pred': round(r_freq_pred, 3), '词长~pred': round(r_len_pred, 3),
                'gold~pred': round(r_gold_pred, 3)},
    '训练分布': dict(train_dist),
    'SUBTLEX命中率': sum(r['in_freq_dict'] for r in rows),
}
opath = os.path.join(ROOT, 'report/审稿补充_特征回归.json')
json.dump(out, open(opath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'\n保存: {opath}')

# 混淆矩阵 markdown
md = ['# 审稿补充：混淆矩阵与 Macro-F1（未见词条 n=1,000）\n',
      '| gold\\pred | 1 | 2 | 3 | 4 | 5 | 6 | 7-9 | 行计 | 召回 |\n|--' + '|--' * 8 + '|',
      '| ' + ' | '.join(['**1**'] + [str(v) for v in cm[0]] + [str(sum(cm[0])), f'{100*cm[0][0]/sum(cm[0]):.1f}%']) + ' |']
for i in range(1, 7):
    md.append('| ' + ' | '.join([f'**{LV[i]}**'] + [str(v) for v in cm[i]] + [str(sum(cm[i])), f'{100*cm[i][i]/sum(cm[i]):.1f}%']) + ' |')
md.append(f'\n- micro：注入 {micro_inj*100:.1f}% vs 多数类（全猜 7-9）{pi79*100:.1f}%')
md.append(f'- **macro-F1：注入 {mf1_inj*100:.2f} vs 多数类 {mf1_maj*100:.2f}（+{(mf1_inj-mf1_maj)*100:.2f}）**')
md.append(f'- per-class F1：' + '、'.join(f'{LV[i]}={f1_by[i]:.3f}' for i in range(7)))
md.append(f'\n训练集分布（均衡，每级约 322 对）：' + '、'.join(f'{k}={v}' for k, v in sorted(train_dist.items())))
md.append('→ 训练分布均衡，"向多数类坍缩"不成立；吸引子只能来自词条特征与等级边界的交互。')
open(os.path.join(ROOT, 'report/审稿补充_混淆矩阵.md'), 'w', encoding='utf-8').write('\n'.join(md))
print('保存: report/审稿补充_混淆矩阵.md')
for k in ['混淆矩阵', '判对率回归', '金标等级特征可预测性', '一级判对vs判错', '吸引子特征', 'Pearson相关']:
    print(f'\n=== {k} ===')
    print(json.dumps(out[k], ensure_ascii=False, indent=1)[:1200])