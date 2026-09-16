# -*- coding: utf-8 -*-
"""Full second-judge pass on ALL scored llm_rubric (model,item) pairs.
Judge1 = existing k3 scores in results/<model>/*.json
Judge2 = deepseek-chat from providers.json
Checkpointed: results/judge_reliability_full.checkpoint.jsonl
Final: results/judge_reliability_full.json
"""
import os, sys, json, re, time, statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prov = json.load(open(os.path.join(ROOT, 'runner/providers.json'), encoding='utf-8'))
DP = prov['deepseek']
BASE = DP['base'].rstrip('/')
KEY = DP.get('key') or DP.get('api_key')
JUDGE2 = DP['chosen']
WORKERS = int(os.environ.get('JUDGE2_WORKERS', '4'))
OUT_JSON = os.path.join(ROOT, 'results', 'judge_reliability_full.json')
CKPT = os.path.join(ROOT, 'results', 'judge_reliability_full.checkpoint.jsonl')
FAIL_LOG = os.path.join(ROOT, 'results', 'judge_reliability_full.failures.jsonl')

items = {i['item_id']: i for i in (json.loads(l) for l in open(os.path.join(ROOT, 'items/v1.0/items.jsonl'), encoding='utf-8'))}
rubric_ids = {iid for iid, it in items.items() if it['scoring']['type'] == 'llm_rubric'}

# load checkpoint done keys
done = {}
if os.path.isfile(CKPT):
    with open(CKPT, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get('j2') is not None:
                done[(o['model'], o['item_id'])] = o

pool = []
for m in sorted(os.listdir(os.path.join(ROOT, 'results'))):
    d = os.path.join(ROOT, 'results', m)
    if not os.path.isdir(d) or m in ('harness',):
        continue
    files = set(os.listdir(d))
    for iid in rubric_ids:
        fn = iid + '.json'
        if fn not in files:
            continue
        try:
            obj = json.load(open(os.path.join(d, fn), encoding='utf-8'))
        except Exception:
            continue
        if obj.get('score') is None or obj.get('error'):
            continue
        key = (m, iid)
        if key in done:
            continue
        pool.append({
            'model': m,
            'item_id': iid,
            'k3': float(obj['score']),
            'output': obj.get('output', '') or '',
        })

print(f'rubric items={len(rubric_ids)} already_done={len(done)} todo={len(pool)} workers={WORKERS} judge2={JUDGE2}', flush=True)

_lock = threading.Lock()
_ok = 0
_fail = 0

def judge(it, answer):
    rub = '\n'.join(f"- {r['dim']}（满分{r['max']}）：{r['desc']}" for r in it['scoring']['rubric'])
    gold = json.dumps(it['reference'].get('gold_meta'), ensure_ascii=False)[:600]
    prompt = (f"你是评测评委。请根据量表给下面的模型回答打分。\n\n"
              f"【题目指令】{it['prompt']['instruction']}\n【题目输入】{it['prompt'].get('input','')[:400]}\n"
              f"【参考答案信息】{gold}\n\n【被评回答】{answer[:1500]}\n\n"
              f"【量表】\n{rub}\n\n只输出 JSON：{{\"分数\": {{\"维度名\": 得分, ...}}, \"总分\": 数字}}")
    body = {"model": JUDGE2, "messages": [{"role": "user", "content": prompt}]}
    last = 'parse_fail'
    for att in range(4):
        try:
            req = urllib.request.Request(
                BASE + '/chat/completions',
                data=json.dumps(body).encode(),
                headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'},
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.load(r)
            out = resp['choices'][0]['message']['content']
            m = re.search(r'"总分"\s*[:：]\s*(\d+(?:\.\d+)?)', out)
            if m:
                total = float(m.group(1))
                mx = sum(r['max'] for r in it['scoring']['rubric'])
                return min(total / mx, 1.0), out
            m2 = re.search(r'"total"\s*:\s*(\d+(?:\.\d+)?)', out, re.I)
            if m2:
                total = float(m2.group(1))
                mx = sum(r['max'] for r in it['scoring']['rubric'])
                return min(total / mx, 1.0), out
        except Exception as e:
            time.sleep(1.5 * (att + 1))
            last = str(e)
    return None, last

def work(s):
    it = items[s['item_id']]
    j2, raw = judge(it, s['output'])
    return {**s, 'j2': j2, 'raw_err': None if j2 is not None else (raw[:200] if isinstance(raw, str) else str(raw))}

def append_ckpt(rec):
    with _lock:
        with open(CKPT, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')

if pool:
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(work, s) for s in pool]
        for fut in as_completed(futs):
            r = fut.result()
            if r['j2'] is not None:
                rec = {'model': r['model'], 'item_id': r['item_id'], 'k3': r['k3'], 'j2': r['j2']}
                append_ckpt(rec)
                done[(r['model'], r['item_id'])] = rec
                _ok += 1
            else:
                with _lock:
                    with open(FAIL_LOG, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({'model': r['model'], 'item_id': r['item_id'], 'err': r.get('raw_err')}, ensure_ascii=False) + '\n')
                _fail += 1
            total_prog = _ok + _fail
            if total_prog % 50 == 0 or total_prog == len(pool):
                print(f'progress {_ok} ok / {_fail} fail / {total_prog}/{len(pool)} this_run; cumulative_done={len(done)}', flush=True)

pairs = []
seen = set()
if os.path.isfile(CKPT):
    with open(CKPT, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            if o.get('j2') is None:
                continue
            key = (o['model'], o['item_id'])
            if key in seen:
                continue
            seen.add(key)
            pairs.append({'model': o['model'], 'item_id': o['item_id'], 'k3': float(o['k3']), 'j2': float(o['j2'])})

print(f'pairs for metrics: {len(pairs)}', flush=True)

def pearson(a, b):
    if len(a) < 2:
        return None
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else None

def spearman(a, b):
    n = len(a)
    if n < 2:
        return None
    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    return pearson(ranks(a), ranks(b))

item_cov = len({p['item_id'] for p in pairs})
model_cov = sorted({p['model'] for p in pairs})
by_task = {}
for p in pairs:
    task = p['item_id'].split('-')[1] if '-' in p['item_id'] else '?'
    by_task.setdefault(task, {'n': 0, 'k3': [], 'j2': []})
    by_task[task]['n'] += 1
    by_task[task]['k3'].append(p['k3'])
    by_task[task]['j2'].append(p['j2'])

k3s = [p['k3'] for p in pairs]
j2s = [p['j2'] for p in pairs]
task_stats = {}
for t, v in by_task.items():
    task_stats[t] = {
        'n': v['n'],
        'pearson_r': round(pearson(v['k3'], v['j2']), 4) if len(v['k3']) >= 2 else None,
        'spearman_rho': round(spearman(v['k3'], v['j2']), 4) if len(v['k3']) >= 2 else None,
        'agreement_within_0.15': round(sum(1 for a, b in zip(v['k3'], v['j2']) if abs(a - b) <= 0.15) / v['n'], 4),
        'mean_abs_diff': round(sum(abs(a - b) for a, b in zip(v['k3'], v['j2'])) / v['n'], 4),
        'k3_mean': round(statistics.mean(v['k3']), 4),
        'judge2_mean': round(statistics.mean(v['j2']), 4),
    }

out = {
    'n': len(pairs),
    'unique_items': item_cov,
    'unique_items_target': len(rubric_ids),
    'models': model_cov,
    'judge1': 'k3-agent',
    'judge2': f'{JUDGE2}',
    'pearson_r': round(pearson(k3s, j2s), 4) if pairs else None,
    'spearman_rho': round(spearman(k3s, j2s), 4) if pairs else None,
    'agreement_within_0.15': round(sum(1 for a, b in zip(k3s, j2s) if abs(a - b) <= 0.15) / len(pairs), 4) if pairs else None,
    'mean_abs_diff': round(sum(abs(a - b) for a, b in zip(k3s, j2s)) / len(pairs), 4) if pairs else None,
    'k3_mean': round(statistics.mean(k3s), 4) if pairs else None,
    'judge2_mean': round(statistics.mean(j2s), 4) if pairs else None,
    'by_task': task_stats,
    'this_run_ok': _ok,
    'this_run_fail': _fail,
    'pairs': pairs,
}
json.dump(out, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
summary = {k: v for k, v in out.items() if k != 'pairs'}
print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
print('saved', OUT_JSON, flush=True)
