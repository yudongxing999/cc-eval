# -*- coding: utf-8 -*-
"""A2：GF0025 语法大纲同名跨级条目对齐标注（机械化，对齐标准原文，不作教学论判断）
输出：
  standard/gf0025-2021/grammar_ambiguity.jsonl  —— 逐条目标注（572 条全覆盖）
  report/语法点歧义标注_A2.md                    —— 汇总报告
标注逻辑（仅依据标准自身的字段）：
  - 同名单条：名称全表唯一 → unique，可直接用于"条目→等级"判断
  - 同名多条：比较各级的 category/subcategory/content
      content 完全一致 → duplicate（同内容跨级复现）
      content 不同     → spiral（螺旋递进：同名但各级内容范围不同）
      部分相同         → mixed
用法：../.venv/Scripts/python.exe anno_grammar_ambiguity.py
"""
import json, os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'standard/gf0025-2021/grammar.json')
OUT = os.path.join(ROOT, 'standard/gf0025-2021/grammar_ambiguity.jsonl')
RPT = os.path.join(ROOT, 'report/语法点歧义标注_A2.md')


def norm(s):
    return ''.join((s or '').split())


def main():
    rows = json.load(open(G, encoding='utf-8'))
    unnamed = [r for r in rows if not str(r.get('item') or '').strip()]
    named = [r for r in rows if str(r.get('item') or '').strip()]
    by_name = defaultdict(list)
    for r in named:
        by_name[r['item']].append(r)

    annotated = []
    for name, occ in by_name.items():
        occ = sorted(occ, key=lambda x: str(x['level']))
        levels = [str(x['level']) for x in occ]
        if len(occ) == 1:
            kind = 'unique'
        else:
            contents = {norm(x.get('content')) for x in occ}
            cats = {(x.get('category'), x.get('subcategory')) for x in occ}
            if len(contents) == 1:
                kind = 'duplicate'
            elif len(contents) == len(occ) and len(cats) == 1:
                kind = 'spiral'          # 同范畴、内容逐级不同
            elif len(contents) == len(occ):
                kind = 'spiral-crosscat'  # 连范畴都不同
            else:
                kind = 'mixed'
        # 可否用于等级判断：unique 可以；duplicate 不可以（同内容多等级）；
        # spiral 需"名称+内容"联合定位才可以
        for x in occ:
            annotated.append({
                'no': x['no'], 'item': name, 'level': str(x['level']),
                'category': x.get('category'), 'subcategory': x.get('subcategory'),
                'content': x.get('content'),
                'name_occurrences': len(occ), 'name_levels': levels,
                'ambiguity': kind,
                'level_judgeable_by_name_only': kind == 'unique',
                'level_judgeable_by_name_and_content': kind in ('unique', 'spiral', 'spiral-crosscat'),
            })

    with open(OUT, 'w', encoding='utf-8') as f:
        for a in annotated:
            f.write(json.dumps(a, ensure_ascii=False) + '\n')

    # 空名称条目（数字化合并单元格残留）：单独归类，不参与同名歧义统计
    for x in unnamed:
        annotated.append({
            'no': x['no'], 'item': '', 'level': str(x['level']),
            'category': x.get('category'), 'subcategory': x.get('subcategory'),
            'content': x.get('content'),
            'name_occurrences': 0, 'name_levels': [],
            'ambiguity': 'unnamed',
            'level_judgeable_by_name_only': False,
            'level_judgeable_by_name_and_content': True,  # 等级字段本身在，可用内容定位
        })

    n_names = len(by_name)
    multi = {k: v for k, v in by_name.items() if len(v) > 1}
    kind_of = {}
    for a in annotated:
        if a['ambiguity'] != 'unnamed':
            kind_of.setdefault(a['item'], a['ambiguity'])
    kc = Counter(kind_of[n] for n in multi)
    span = Counter(tuple(a['name_levels']) for a in annotated if a['name_occurrences'] > 1)

    lines = ['# GF0025 语法大纲同名跨级条目标注（A2）', '',
             f'- 条目总数：{len(rows)}；其中**空名称条目 {len(unnamed)} 条**（数字化合并单元格残留，主要分布在口语格式/固定格式等范畴，等级字段完整，可用"范畴+内容"定位）',
             f'- 有效名称数：{n_names}；单一名称条目：{sum(1 for v in by_name.values() if len(v)==1)} 条；同名跨级名称：**{len(multi)} 个**，覆盖条目 {sum(len(v) for v in multi.values())} 条',
             '', '## 同名条目的歧义类型（对齐标准 content 字段判定）', '',
             '| 类型 | 名称数 | 含义 | 可否用于"名称→等级"判断 |',
             '|---|---:|---|---|',
             f"| duplicate | {kc.get('duplicate',0)} | 各级内容完全相同（纯复现） | 不可 |",
             f"| spiral | {kc.get('spiral',0)} | 同范畴、内容逐级扩展（螺旋递进） | 不可；名称+内容可 |",
             f"| spiral-crosscat | {kc.get('spiral-crosscat',0)} | 连范畴归属都不同 | 不可；名称+内容可 |",
             f"| mixed | {kc.get('mixed',0)} | 部分级别内容相同 | 不可 |",
             '', '## 等级跨度分布（同名条目的等级组合 TOP15）', '',
             '| 等级组合 | 名称数 |', '|---|---:|']
    for combo, c in span.most_common(15):
        lines.append(f"| {'、'.join(combo)} | {c} |")
    lines += ['', '## 示例（每类前 3 个）', '']
    shown = Counter()
    for name, occ in sorted(multi.items()):
        kind = kind_of[name]
        if shown[kind] >= 3:
            continue
        shown[kind] += 1
        occ = sorted(occ, key=lambda x: str(x['level']))
        lines.append(f"**{name}**（{kind}）：" + '；'.join(
            f"{x['level']}级[{x.get('category')}/{x.get('subcategory')}] {norm(x.get('content'))[:40]}…" for x in occ))
        lines.append('')
    lines += ['---', f'逐条目标注：standard/gf0025-2021/grammar_ambiguity.jsonl（{len(annotated)} 条）']
    open(RPT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('\n'.join(lines[:14]))
    print('written ->', RPT)


if __name__ == '__main__':
    main()
