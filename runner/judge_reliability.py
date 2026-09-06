# -*- coding: utf-8 -*-
"""评委信度抽检：抽样 llm_rubric 已评分题，用第二评委(deepseek-chat)复评，与 k3 评委分比较"""
import os, sys, json, glob, re, time, random, statistics
from concurrent.futures import ThreadPoolExecutor
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
prov = json.load(open(os.path.join(ROOT, 'runner/providers.json'), encoding='utf-8'))
DP = prov['deepseek']
BASE = DP['base'].rstrip('/')
KEY = DP.get('key') or DP.get('api_key')
JUDGE2 = DP['chosen']

items = {i['item_id']: i for i in (json.loads(l) for l in open(os.path.join(ROOT, 'items/v1.0/items.jsonl'), encoding='utf-8'))}

# 收集所有已有 k3 评委分的 llm_rubric 结果
pool = []
for model_dir in glob.glob(os.path.join(ROOT, 'results', '*')):
    mname = os.path.basename(model_dir)
    if not os.path.isdir(model_dir):
        continue
    for f in glob.glob(os.path.join(model_dir, '*.json')):
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        it = items.get(d.get('item_id'))
        if it and it['scoring']['type'] == 'llm_rubric' and d.get('score') is not None and not d.get('error'):
            pool.append({'model': mname, 'file': f, 'item_id': d['item_id'], 'k3_score': d['score'], 'output': d.get('output', '')})
print('llm_rubric scored pool:', len(pool))

random.seed(42)
sample = random.sample(pool, min(30, len(pool)))

def judge(it, answer):
    rub = '\n'.join(f"- {r['dim']}（满分{r['max']}）：{r['desc']}" for r in it['scoring']['rubric'])
    gold = json.dumps(it['reference'].get('gold_meta'), ensure_ascii=False)[:600]
    prompt = (f"你是评测评委。请根据量表给下面的模型回答打分。\n\n"
              f"【题目指令】{it['prompt']['instruction']}\n【题目输入】{it['prompt'].get('input','')[:400]}\n"
              f"【参考答案信息】{gold}\n\n【被评回答】{answer[:1500]}\n\n"
              f"【量表】\n{rub}\n\n只输出 JSON：{{\"分数\": {{\"维度名\": 得分, ...}}, \"总分\": 数字}}")
    body = {"model": JUDGE2, "messages": [{"role": "user", "content": prompt}]}
    for att in range(3):
        try:
            req = urllib.request.Request(BASE + '/chat/completions', data=json.dumps(body).encode(),
                headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=90) as r:
                resp = json.load(r)
            out = resp['choices'][0]['message']['content']
            m = re.search(r'"总分"\s*[:：]\s*(\d+(?:\.\d+)?)', out)
            if m:
                total = float(m.group(1))
                mx = sum(r['max'] for r in it['scoring']['rubric'])
                return min(total / mx, 1.0)
        except Exception as e:
            time.sleep(2)
    return None

def work(s):
    it = items[s['item_id']]
    s['judge2_score'] = judge(it, s['output'])
    return s

with ThreadPoolExecutor(max_workers=4) as ex:
    sample = list(ex.map(work, sample))

ok = [s for s in sample if s.get('judge2_score') is not None]
print(f're-judged: {len(ok)}/{len(sample)} by {JUDGE2}')

def spearman(x, y):
    n = len(x)
    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0]*n
        i = 0
        while i < n:
            j = i
            while j+1 < n and v[order[j+1]] == v[order[i]]:
                j += 1
            for k in range(i, j+1):
                r[order[k]] = (i+j)/2 + 1
            i = j+1
        return r
    rx, ry = ranks(x), ranks(y)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    cov = sum((a-mx)*(b-my) for a, b in zip(rx, ry))
    sx = sum((a-mx)**2 for a in rx)**.5
    sy = sum((b-my)**2 for b in ry)**.5
    return cov/(sx*sy) if sx*sy else None

if ok:
    k3 = [s['k3_score'] for s in ok]
    j2 = [s['judge2_score'] for s in ok]
    n = len(ok)
    pearson_num = sum((a-statistics.mean(k3))*(b-statistics.mean(j2)) for a, b in zip(k3, j2))
    pearson_den = (sum((a-statistics.mean(k3))**2 for a in k3)*sum((b-statistics.mean(j2))**2 for b in j2))**.5
    pearson = pearson_num/pearson_den if pearson_den else None
    spe = spearman(k3, j2)
    mad = statistics.mean(abs(a-b) for a, b in zip(k3, j2))
    agree15 = sum(1 for a, b in zip(k3, j2) if abs(a-b) <= 0.15)/n
    result = {
        'n': n, 'judge1': 'k3-agent', 'judge2': JUDGE2,
        'pearson_r': round(pearson, 4) if pearson else None,
        'spearman_rho': round(spe, 4) if spe else None,
        'mean_abs_diff': round(mad, 4),
        'agreement_within_0.15': round(agree15, 4),
        'k3_mean': round(statistics.mean(k3), 4),
        'judge2_mean': round(statistics.mean(j2), 4),
        'pairs': [{'model': s['model'], 'item_id': s['item_id'], 'k3': round(s['k3_score'],3), 'j2': round(s['judge2_score'],3)} for s in ok],
    }
    out = os.path.join(ROOT, 'results', 'judge_reliability.json')
    json.dump(result, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != 'pairs'}, ensure_ascii=False, indent=2))
    print('saved:', out)
