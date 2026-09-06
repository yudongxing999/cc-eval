# -*- coding: utf-8 -*-
"""对 llm_rubric 题用评委模型补评分"""
import os, sys, json, glob, re, time
from concurrent.futures import ThreadPoolExecutor
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_MODEL = sys.argv[1] if len(sys.argv) > 1 else 'k2d6-agent'
JUDGE = sys.argv[2] if len(sys.argv) > 2 else 'k3-agent'
base = os.environ['KIMI_BASE_URL'].rstrip('/'); key = os.environ['KIMI_API_KEY']

items = {i['item_id']: i for i in (json.loads(l) for l in open(os.path.join(ROOT, 'items/v1.0/items.jsonl'), encoding='utf-8'))}

def judge(it, answer):
    rub = '\n'.join(f"- {r['dim']}（满分{r['max']}）：{r['desc']}" for r in it['scoring']['rubric'])
    gold = json.dumps(it['reference'].get('gold_meta'), ensure_ascii=False)[:600]
    prompt = (f"你是评测评委。请根据量表给下面的模型回答打分。\n\n"
              f"【题目指令】{it['prompt']['instruction']}\n【题目输入】{it['prompt'].get('input','')[:400]}\n"
              f"【参考答案信息】{gold}\n\n【被评回答】{answer[:1500]}\n\n"
              f"【量表】\n{rub}\n\n只输出 JSON：{{\"分数\": {{\"维度名\": 得分, ...}}, \"总分\": 数字}}")
    body = {"model": JUDGE, "messages": [{"role": "user", "content": prompt}], "thinking": {"type": "disabled"}}
    for att in range(3):
        try:
            req = urllib.request.Request(base + '/v1/chat/completions', data=json.dumps(body).encode(),
                headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=90) as r:
                resp = json.load(r)
            out = resp['choices'][0]['message']['content']
            m = re.search(r'"总分"\s*[:：]\s*(\d+(?:\.\d+)?)', out)
            if m:
                total = float(m.group(1))
                mx = sum(r['max'] for r in it['scoring']['rubric'])
                return total / mx
        except Exception:
            time.sleep(2)
    return None

todo = []
for f in glob.glob(os.path.join(ROOT, 'results', EVAL_MODEL, '*.json')):
    d = json.load(open(f, encoding='utf-8'))
    it = items.get(d['item_id'])
    if it and it['scoring']['type'] == 'llm_rubric' and d.get('score') is None and not d.get('error'):
        todo.append((f, d, it))
print(f'judge={JUDGE} pending={len(todo)}')

def work(t):
    f, d, it = t
    s = judge(it, d.get('output', ''))
    if s is not None:
        d['score'] = s
        d['judge'] = JUDGE
        json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False)
    return s is not None

n = 0
with ThreadPoolExecutor(max_workers=8) as ex:
    for ok in ex.map(work, todo):
        n += ok
        if n % 30 == 0: print(f'  judged {n}/{len(todo)}', flush=True)
print('judged:', n)
