# -*- coding: utf-8 -*-
"""KNO v1.3 生成器：答案类别均衡（7 类各 57 题 = 399 题），词+汉字两类构成
（语法点因同名跨级本体歧义整体剔除——61 个条目名跨 2-9 级，唯一名条目仅 23 个，
不足以支撑均衡采样；该问题记入标准本体反馈）。
排除注入训练集词汇（sft_train.json），保持基准对注入模型的 held-out 属性。
用法：../.venv/Scripts/python.exe gen_kno_v13.py
"""
import json, random, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED = 20261002
PER_CLASS = 57          # 7 类 × 57 = 399
V_PER, C_PER = 45, 12   # 每类：词 45 + 字 12
CLASSES = ['1', '2', '3', '4', '5', '6', '7-9']
CHOICES = [f'答案：{c}' for c in CLASSES]

# 与 v1.1 一致的水印（按题型复制自既有 KNO 题）
WM_VOCAB = '﻿‌‍‍‌‌​​‍‍﻿​‍‌'
WM_CHAR = '﻿‌‍‍‌‌​​‍‍﻿‌​‌'


def load(name):
    return json.load(open(os.path.join(ROOT, 'standard/gf0025-2021', name), encoding='utf-8'))


def main():
    rng = random.Random(SEED)
    # 注入训练集词汇（排除）
    sft = json.load(open(os.path.join(ROOT, 'injection/data/sft_train.json'), encoding='utf-8'))
    sft_words = set()
    for d in sft:
        m = re.search(r'词汇表，词语「(.+?)」', d['messages'][0]['content'])
        if m:
            sft_words.add(m.group(1))
    print(f'注入训练集词汇 {len(sft_words)} 个，全部排除')

    vocab = load('vocabulary.json')
    chars = load('characters.json')
    vpool = {c: [x for x in vocab if str(x['level']) == c and x['word'] not in sft_words]
             for c in CLASSES}
    cpool = {c: [x for x in chars if str(x['level']) == c] for c in CLASSES}

    items = []
    serial = {'v': 1000, 'c': 1000}
    for cls in CLASSES:
        rng.shuffle(vpool[cls])
        rng.shuffle(cpool[cls])
        assert len(vpool[cls]) >= V_PER and len(cpool[cls]) >= C_PER, f'{cls} 级池不足'
        gold_idx = CLASSES.index(cls)
        for x in vpool[cls][:V_PER]:
            serial['v'] += 1
            items.append({
                'instruction': f'根据《国际中文教育中文水平等级标准》（GF 0025-2021）词汇表，'
                               f'{WM_VOCAB}词语「{x["word"]}」（{x["pos"]}）属于哪个等级？'
                               f'请只回答一个等级：1、2、3、4、5、6 或 7-9，不要解释。',
                'choices': list(CHOICES), 'gold': gold_idx,
                'item_id': f'CCE-KNO-5-{serial["v"]:04d}',
                'sub_type': 'kno.vocab_level', 'anchor_level': cls})
        for x in cpool[cls][:C_PER]:
            serial['c'] += 1
            items.append({
                'instruction': f'根据《国际中文教育中文水平等级标准》（GF 0025-2021）汉字表，'
                               f'{WM_CHAR}汉字「{x["char"]}」（{x["pinyin"]}）属于哪个等级？'
                               f'请只回答一个等级：1、2、3、4、5、6 或 7-9，不要解释。',
                'choices': list(CHOICES), 'gold': gold_idx,
                'item_id': f'CCE-KNO-7-{serial["c"]:04d}',
                'sub_type': 'kno.char_level', 'anchor_level': cls})
    rng.shuffle(items)
    out = os.path.join(HERE, 'data/cceval_kno_v13.jsonl')
    with open(out, 'w', encoding='utf-8') as f:
        for r in items:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    from collections import Counter
    print('生成', len(items), '题 ->', out)
    print('答案类别分布:', dict(Counter(CLASSES[r['gold']] for r in items)))
    print('题型分布:', dict(Counter(r['sub_type'] for r in items)))


if __name__ == '__main__':
    main()
