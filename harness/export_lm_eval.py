# -*- coding: utf-8 -*-
"""将 CC-Eval 判别式题目导出为 lm-evaluation-harness 的 multiple_choice 任务
覆盖：KNO 定级（400）、PHO 音节合法性（60）、PHO 音节定级（40）、PHO 多音字（30）
输出：harness/data/*.jsonl + harness/tasks/*.yaml
用法：python harness/export_lm_eval.py
"""
import os, json, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = os.path.join(ROOT, 'items/v1.1/items.jsonl')
OUT_D = os.path.join(ROOT, 'harness/data')
OUT_T = os.path.join(ROOT, 'harness/tasks')
os.makedirs(OUT_D, exist_ok=True)
os.makedirs(OUT_T, exist_ok=True)

LEVELS = ['1', '2', '3', '4', '5', '6', '7-9']
items = [json.loads(l) for l in open(ITEMS, encoding='utf-8')]

# 多音字读音全集（候选项来源）
chars = json.load(open(os.path.join(ROOT, 'standard/gf0025-2021/characters.json'), encoding='utf-8'))
readings = collections.defaultdict(set)
for c in chars:
    readings[c['char']].add(c['pinyin'].lower())

def dump(name, rows):
    path = os.path.join(OUT_D, name + '.jsonl')
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'{name}: {len(rows)} rows ->', path)

def write_yaml(task, datafile, desc):
    y = f'''# CC-Eval {task} —— lm-evaluation-harness multiple_choice 任务
# 生成：harness/export_lm_eval.py（勿手改）
task: {task}
dataset_path: json
dataset_kwargs:
  data_files:
    test: data/{datafile}.jsonl
test_split: test
output_type: multiple_choice
doc_to_text: "{{{{instruction}}}}"
doc_to_choice: "{{{{choices}}}}"
doc_to_target: gold
metric_list:
  - metric: acc
    aggregation: mean
    higher_is_better: true
metadata:
  version: 1.1.0
  description: "{desc}"
'''
    path = os.path.join(OUT_T, task + '.yaml')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(y)
    print('yaml ->', path)

# ---- cceval_kno：等级知识 400 题（七选一）----
rows = []
for it in items:
    if it['task_type'] != 'KNO':
        continue
    gold = str(it['reference']['answer'])
    if gold not in LEVELS:
        continue
    rows.append({'instruction': it['prompt']['instruction'],
                 'choices': LEVELS, 'gold': LEVELS.index(gold),
                 'item_id': it['item_id'], 'sub_type': it['sub_type'],
                 'anchor_level': it['anchor'].get('level')})
dump('cceval_kno', rows)
write_yaml('cceval_kno', 'cceval_kno',
           '国际中文教育等级知识（音节/汉字/词汇/语法点定级，锚定 GF 0025-2021）')

# ---- cceval_pho_legal：音节合法性 60 题（二选一）----
rows = []
for it in items:
    if it['sub_type'] != 'pho.syl_legal':
        continue
    gold = it['reference']['answer']
    rows.append({'instruction': it['prompt']['instruction'],
                 'choices': ['合法', '非法'], 'gold': 0 if gold == '合法' else 1,
                 'item_id': it['item_id'], 'sub_type': it['sub_type']})
dump('cceval_pho_legal', rows)
write_yaml('cceval_pho_legal', 'cceval_pho_legal',
           '普通话音节合法性判断（锚定 GF 0025-2021 音节表）')

# ---- cceval_pho_level：音节定级 40 题（七选一）----
rows = []
for it in items:
    if it['sub_type'] != 'pho.syl_level':
        continue
    gold = str(it['reference']['answer'])
    if gold not in LEVELS:
        continue
    rows.append({'instruction': it['prompt']['instruction'],
                 'choices': LEVELS, 'gold': LEVELS.index(gold),
                 'item_id': it['item_id'], 'sub_type': it['sub_type'],
                 'anchor_level': it['anchor'].get('level')})
dump('cceval_pho_level', rows)
write_yaml('cceval_pho_level', 'cceval_pho_level',
           '带调音节等级定位（锚定 GF 0025-2021 音节表）')

# ---- cceval_pho_poly：多音字语境定音 30 题（候选=该字全部标准读音）----
rows = []
skipped = 0
for it in items:
    if it['sub_type'] != 'pho.polyphonic':
        continue
    ch = it['anchor']['char']
    gold = str(it['reference']['answer']).lower()
    choices = sorted(readings.get(ch, set()))
    if gold not in choices or len(choices) < 2:
        skipped += 1
        continue
    rows.append({'instruction': it['prompt']['instruction'],
                 'choices': choices, 'gold': choices.index(gold),
                 'item_id': it['item_id'], 'sub_type': it['sub_type']})
dump('cceval_pho_poly', rows)
write_yaml('cceval_pho_poly', 'cceval_pho_poly',
           '多音字语境定音（候选为《等级标准》汉字表中该字的全部读音）')
if skipped:
    print(f'cceval_pho_poly skipped {skipped}（读音未匹配汉字表）')
print('done.')
