# -*- coding: utf-8 -*-
"""意见4 口径防御：deepseek-chat KNO 词定级 30 题重复施测（稳定性验证）
原测 vs 复测的一致率——生成式作答在提供商默认参数下的可复现性。
"""
import json, os, time, urllib.request, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prov = json.load(open(os.path.join(ROOT, 'runner/providers.json'), encoding='utf-8'))
cfg = prov['deepseek']
base, key = cfg['base'], cfg['key']
model = cfg['models'][0] if isinstance(cfg.get('models'), list) else 'deepseek-chat'

items = json.load(open('C:/Users/Donal/AppData/Local/Temp/kno_stab_items.json', encoding='utf-8'))

# 原测答案（results/deepseek）
orig = {}
for it in items:
    p = os.path.join(ROOT, f"results/deepseek/{it['item_id']}.json")
    if os.path.exists(p):
        orig[it['item_id']] = json.load(open(p, encoding='utf-8'))['output']

def chat(messages):
    body = json.dumps({'model': model, 'messages': messages}).encode()
    req = urllib.request.Request(
        base.rstrip('/') + '/chat/completions',
        data=body,
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'})
    for _ in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())['choices'][0]['message']['content']
        except Exception as e:
            time.sleep(3)
    return None

out = []
same_ans = same_score = n = 0
t0 = time.time()
for it in items:
    ans = chat([{'role': 'user', 'content': it['instruction']}])
    o = orig.get(it['item_id'])
    if ans:
        a = ans.strip()
        out.append({'item_id': it['item_id'], 'orig': o, 'retest': a, 'gold': it['gold']})
        n += 1
        if a == o:
            same_ans += 1
        import re
        m = re.search(r'([1-6]|7-9)', a)
        pred = 6 if (m and m.group(1) == '7-9') else (int(m.group(1)) - 1 if m else -1)
        if pred == it['gold']:
            same_score += 1
    print(f"{n}/{len(items)} 一致率(逐字)={same_ans/max(1,n)*100:.0f}% ({(time.time()-t0)/60:.0f}min)", flush=True)

res = {
    'n': n,
    '逐字一致率': same_ans / n,
    '复测正确率': same_score / n,
    '明细': out,
}
# 原测正确率
import re
orig_correct = 0
for r in out:
    m = re.search(r'([1-6]|7-9)', r['orig'] or '')
    pred = 6 if (m and m.group(1) == '7-9') else (int(m.group(1)) - 1 if m else -1)
    if pred == r['gold']:
        orig_correct += 1
res['原测正确率'] = orig_correct / n
json.dump(res, open(os.path.join(ROOT, 'injection/results_retest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f"\n逐字一致率 {same_ans/n*100:.1f}%  原测正确率 {orig_correct/n*100:.1f}%  复测正确率 {same_score/n*100:.1f}%")
print('保存: injection/results_retest.json')