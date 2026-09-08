# -*- coding: utf-8 -*-
"""论文三实验3：SCO 多采样稳定性验证
对 3 个代表模型（hunyuan=均匀压分 / deepseek=强压缩 / k3-agent=高基准）
各以 250 题中分层抽 50 题，重采 3 次，验证 δ（均值偏差）与 α（斜率）的采样稳定性
"""
import os, sys, json, re, time, random, glob
from concurrent.futures import ThreadPoolExecutor
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
prov = json.load(open(os.path.join(ROOT, 'runner/providers.json'), encoding='utf-8'))

items = {json.loads(l)['item_id']: json.loads(l) for l in open(os.path.join(ROOT, 'items/v1.1/items.jsonl'), encoding='utf-8')}
sco_ids = [i for i in items if i.startswith('CCE-SCO')]

# 分层抽 50：按五个分数段（0-59/60-69/70-79/80-89/90-100）各 10
random.seed(2026)
def band(g):
    if g < 60: return 0
    if g < 70: return 1
    if g < 80: return 2
    if g < 90: return 3
    return 4
by_band = {}
for iid in sco_ids:
    g = items[iid]['reference']['answer']
    by_band.setdefault(band(g), []).append(iid)
sample50 = []
for b, lst in sorted(by_band.items()):
    random.shuffle(lst)
    sample50 += lst[:10]
print('各段规模:', {b: len(l) for b, l in by_band.items()}, '| 抽样:', len(sample50))
assert len(sample50) >= 45, f'仅抽到 {len(sample50)}'

MODELS = {
    'hunyuan': prov['hunyuan'],
    'deepseek': prov['deepseek'],
    # k3-agent 首轮经 Kimi 网关，本轮用 deepseek-v4-flash（tchub）作第三对照点
    'tchub-dsv4f': prov['tchub-dsv4f'],
}

def call_api(pr, prompt):
    base = pr['base'].rstrip('/')
    key = pr.get('key') or pr.get('api_key')
    model = pr.get('model') or pr.get('chosen')
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": None}
    # 温度不传 = API 默认（与 v1.0 首轮一致）
    body.pop('temperature')
    for att in range(3):
        try:
            req = urllib.request.Request(base + '/chat/completions', data=json.dumps(body).encode(),
                headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.load(r)
            return resp['choices'][0]['message']['content']
        except Exception as e:
            time.sleep(3 * (att + 1))
    return None

def one_item(args):
    mname, pr, iid = args
    it = items[iid]
    prompt = (it['prompt'].get('system') or '') + '\n' + it['prompt']['instruction'] + '\n' + (it['prompt'].get('input') or '')
    out = call_api(pr, prompt)
    if not out:
        return (mname, iid, None)
    m = re.search(r'"score"\s*:\s*(\d+)', out)
    return (mname, iid, int(m.group(1)) if m else None)

tasks = []
for mname, pr in MODELS.items():
    if pr is None:
        print(f'!! {mname} 不在 providers，跳过')
        continue
    for iid in sample50:
        tasks.append((mname, pr, iid))

print(f'任务: {len(tasks)} 次调用（{len(MODELS)} 模型 × 50 题）')
results = []
with ThreadPoolExecutor(max_workers=3) as ex:
    for i, r in enumerate(ex.map(one_item, tasks)):
        results.append(r)
        if (i+1) % 30 == 0:
            print(f'{i+1}/{len(tasks)}', flush=True)

# 分析
def slope_intercept(golds, preds):
    mx, my = sum(golds)/len(golds), sum(preds)/len(preds)
    a = sum((x-mx)*(y-my) for x, y in zip(golds, preds)) / sum((x-mx)**2 for x in golds)
    return a, my - a*mx

print('\n===== 多采样结果（50 题/模型，对比 v1.0 首轮同题值）=====')
out = {}
for mname in MODELS:
    new = {iid: p for m, iid, p in results if m == mname and p is not None}
    golds = [items[iid]['reference']['answer'] for iid in sample50 if iid in new]
    preds = [new[iid] for iid in sample50 if iid in new]
    if len(preds) < 40:
        print(f'{mname}: 有效 {len(preds)}/50，不足')
        continue
    # v1.0 首轮同题
    old = {}
    for f in glob.glob(os.path.join(ROOT, f'results/{mname}/CCE-SCO-*.json')):
        d = json.load(open(f, encoding='utf-8'))
        m2 = re.search(r'"score"\s*:\s*(\d+)', d['output'] or '')
        if m2:
            old[d['item_id']] = int(m2.group(1))
    og = [items[iid]['reference']['answer'] for iid in sample50 if iid in old and iid in new]
    op = [old[iid] for iid in sample50 if iid in old and iid in new]
    np_ = [new[iid] for iid in sample50 if iid in old and iid in new]
    a_new, b_new = slope_intercept(golds, preds)
    a_old, b_old = slope_intercept(og, op)
    d_new = sum(preds)/len(preds) - sum(golds)/len(golds)
    d_old = sum(op)/len(op) - sum(og)/len(og)
    print(f'{mname:>10}: n={len(np_)} | δ 首轮 {d_old:+.1f} → 重采 {d_new:+.1f} | α 首轮 {a_old:.3f} → 重采 {a_new:.3f}')
    out[mname] = {'n': len(np_), 'delta_old': d_old, 'delta_new': d_new, 'alpha_old': a_old, 'alpha_new': a_new,
                  'pairs': {iid: {'gold': items[iid]['reference']['answer'], 'old': old.get(iid), 'new': new.get(iid)} for iid in sample50 if iid in new}}

json.dump(out, open(os.path.join(ROOT, 'results/sco_resample_50.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n写入 results/sco_resample_50.json')