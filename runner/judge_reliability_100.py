# -*- coding: utf-8 -*-
"""评委信度扩样：120 对（seed 2026 独立抽样），第二评委 deepseek-chat 复评
区别于原 judge_reliability.py（30 对，seed 42）：更大样本 + 独立抽样 + 结果存 judge_reliability_120.json
"""
import os, sys, json, glob, re, time, random
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
print(f'llm_rubric pool: {len(pool)}')

random.seed(2026)  # 独立于原 30 对的 seed 42
sample = random.sample(pool, min(120, len(pool)))

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
        except Exception:
            time.sleep(2)
    return None

def work(s):
    it = items[s['item_id']]
    j2 = judge(it, s['output'])
    return {**s, 'j2': j2}

pairs = []
done = 0
with ThreadPoolExecutor(max_workers=4) as ex:
    for r in ex.map(work, sample):
        done += 1
        if r['j2'] is not None:
            pairs.append({'model': r['model'], 'item_id': r['item_id'], 'k3': r['k3_score'], 'j2': r['j2']})
        if done % 20 == 0:
            print(f'{done}/{len(sample)} 完成', flush=True)
print(f'共完成 {len(pairs)} 有效对')

def pearson(a, b):
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    num = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    den = (sum((x-ma)**2 for x in a) * sum((y-mb)**2 for y in b)) ** 0.5
    return num/den if den else 0.0

def spearman(a, b):
    def rank(x):
        s = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0]*len(x); i = 0
        while i < len(s):
            j = i
            while j+1 < len(s) and x[s[j+1]] == x[s[i]]: j += 1
            for k in range(i, j+1): r[s[k]] = (i+j)/2+1
            i = j+1
        return r
    ra, rb = rank(a), rank(b)
    d2 = sum((x-y)**2 for x, y in zip(ra, rb))
    return 1 - 6*d2/(len(a)*(len(a)**2-1))

k3s = [p['k3'] for p in pairs]
j2s = [p['j2'] for p in pairs]
out = {
    'n': len(pairs),
    'judge1': 'k3-agent', 'judge2': f'deepseek-chat({JUDGE2})',
    'pearson_r': pearson(k3s, j2s), 'spearman_rho': spearman(k3s, j2s),
    'agreement_within_0.15': sum(1 for k, j in zip(k3s, j2s) if abs(k-j) <= 0.15)/len(pairs),
    'mean_abs_diff': sum(abs(k-j) for k, j in zip(k3s, j2s))/len(pairs),
    'k3_mean': sum(k3s)/len(k3s), 'judge2_mean': sum(j2s)/len(j2s),
    'pairs': pairs,
}
json.dump(out, open(os.path.join(ROOT, 'results/judge_reliability_120.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'pairs'}, ensure_ascii=False, indent=1))