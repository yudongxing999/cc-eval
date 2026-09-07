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
    # 候选统一加“答案：”共享前缀，缓解基座模型的“复述最近选项”位置偏差
    # 注意：必须复制行再改写，避免 rows 被二次 dump（如 KNO 主文件+分片）时前缀叠加
    path = os.path.join(OUT_D, name + '.jsonl')
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows:
            r2 = dict(r)
            r2['choices'] = ['答案：' + c for c in r['choices']]
            f.write(json.dumps(r2, ensure_ascii=False) + '\n')
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
# KNO 分片（供 CPU/限时环境分段跑：4 片 × 100 题）
CH = 100
for ci in range(0, len(rows), CH):
    part = rows[ci:ci + CH]
    name = f'cceval_kno_p{ci // CH + 1}'
    dump(name, part)
    write_yaml(name, name, f'CC-Eval KNO 分片 {ci // CH + 1}（合并 acc 按题数加权）')
# KNO 细分片（大模型 CPU 推理更慢时改用：8 片 × 50 题；s5-s8 = p3-p4 的拆分）
CH2 = 50
for ci in range(0, len(rows), CH2):
    part = rows[ci:ci + CH2]
    name = f'cceval_kno_s{ci // CH2 + 1}'
    dump(name, part)
    write_yaml(name, name, f'CC-Eval KNO 细分片 {ci // CH2 + 1}（合并 acc 按题数加权）')
# KNO 微分片（3B+ 模型 CPU 限时环境用：16 片 × 25 题）
CH3 = 25
for ci in range(0, len(rows), CH3):
    part = rows[ci:ci + CH3]
    name = f'cceval_kno_t{ci // CH3 + 1}'
    dump(name, part)
    write_yaml(name, name, f'CC-Eval KNO 微分片 {ci // CH3 + 1}（合并 acc 按题数加权）')
# KNO 超微分片（系统负载高、单片超时时的兜底：约 34 片 × 12 题）
CH4 = 12
for ci in range(0, len(rows), CH4):
    part = rows[ci:ci + CH4]
    name = f'cceval_kno_u{ci // CH4 + 1}'
    dump(name, part)
    write_yaml(name, name, f'CC-Eval KNO 超微分片 {ci // CH4 + 1}（合并 acc 按题数加权）')

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
# 大模型 CPU 限时环境用：legal 2 片 × 30 题
for ci in range(0, len(rows), 30):
    part = rows[ci:ci + 30]
    name = f'cceval_pho_legal_{chr(97 + ci // 30)}'
    dump(name, part)
    write_yaml(name, name, f'CC-Eval PHO legal 分片 {chr(97 + ci // 30)}（合并 acc 按题数加权）')

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
# 大模型 CPU 限时环境用：level 2 片 × 20 题
for ci in range(0, len(rows), 20):
    part = rows[ci:ci + 20]
    name = f'cceval_pho_level_{chr(97 + ci // 20)}'
    dump(name, part)
    write_yaml(name, name, f'CC-Eval PHO level 分片 {chr(97 + ci // 20)}（合并 acc 按题数加权）')

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
