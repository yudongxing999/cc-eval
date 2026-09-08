# -*- coding: utf-8 -*-
"""论文一注入实验：GF0025 标准知识后训练注入
设计：
  任务1 词定级（word → GF0025 等级）：训练 70% 词表 / 测试 held-out 30%——区分记忆与泛化
  任务2 语法定级（语法点 → 等级）：训练 70% / held-out 30%
  评测：与 v1.1 KNO 400 题完全同口径（lm-eval multiple_choice 对数似然，随机基线 14.3%）
对照：
  基线：Qwen2.5-0.5B 基座（v1.1a 实测 6.5%） / Qwen2.5-0.5B-Instruct（6.5%）
  注入后：同一基座 + GF0025 指令对 LoRA
训练：LoRA r=16, CPU float32, 0.5B 可承受
"""
import json, os, random, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- 构造训练/评测数据 ----------
vocab = json.load(open(os.path.join(ROOT, 'standard/gf0025-2021/vocabulary.json'), encoding='utf-8'))
grammar = json.load(open(os.path.join(ROOT, 'standard/gf0025-2021/grammar.json'), encoding='utf-8'))
print(f'词表 {len(vocab)} 条 | 语法 {len(grammar)} 条')

random.seed(2026)

def fmt_level(lv):
    return str(lv) if lv in (1,2,3,4,5,6) else '7-9'

# 词任务：与 KNO 题面完全同模板
def word_prompt(w):
    lv = fmt_level(w['level'])
    return {
        'instr': f"根据《国际中文教育中文水平等级标准》（GF 0025-2021）词汇表，词语「{w['word']}」（{w['pos']}）属于哪个等级？请只回答一个等级：1、2、3、4、5、6 或 7-9，不要解释。",
        'answer': lv,
    }

# 语法任务
def gram_prompt(g):
    lv = fmt_level(g['level'])
    return {
        'instr': f"根据《国际中文教育中文水平等级标准》（GF 0025-2021）语法等级大纲，语法点「{g['item']}」属于哪个等级？请只回答一个等级：1、2、3、4、5、6 或 7-9，不要解释。",
        'answer': lv,
    }

# 70/30 分割（按等级分层，保证 held-out 分布与训练一致）
def split(data, key='level'):
    by = {}
    for d in data:
        by.setdefault(d[key], []).append(d)
    train, test = [], []
    for lv, lst in by.items():
        random.shuffle(lst)
        h = int(len(lst) * 0.3)
        test += lst[:h]
        train += lst[h:]
    return train, test

w_train, w_test = split(vocab)
g_train, g_test = split(grammar)
print(f'词: 训练 {len(w_train)} / held-out {len(w_test)}')
print(f'语法: 训练 {len(g_train)} / held-out {len(g_test)}')

# ---------- 训练对（SFT 格式，chat 模板）----------
def sft(instr, answer):
    return {
        'messages': [
            {'role': 'user', 'content': instr},
            {'role': 'assistant', 'content': f'答案：{answer}'},
        ]
    }

train_pairs = [sft(word_prompt(w)['instr'], word_prompt(w)['answer']) for w in w_train]
train_pairs += [sft(gram_prompt(g)['instr'], gram_prompt(g)['answer']) for g in g_train]
random.shuffle(train_pairs)
print(f'训练对: {len(train_pairs)}')

os.makedirs(os.path.join(ROOT, 'injection/data'), exist_ok=True)
json.dump(train_pairs, open(os.path.join(ROOT, 'injection/data/sft_train.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# held-out 评测集（与 harness lm-eval 格式一致：choices + gold）
def lm_eval_fmt(pairs, name):
    recs = []
    for p in pairs:
        d = word_prompt(p) if 'word' in p else gram_prompt(p)
        recs.append({
            'instruction': d['instr'],
            'choices': ['答案：1','答案：2','答案：3','答案：4','答案：5','答案：6','答案：7-9'],
            'gold': int(d['answer'].replace('7-9', '6')) if False else (int(d['answer']) if d['answer'] != '7-9' else 6),
            'sub_type': 'inject_word_level' if 'word' in p else 'inject_gram_level',
        })
    json.dump(recs, open(os.path.join(ROOT, f'injection/data/{name}.jsonl'), 'w', encoding='utf-8'), ensure_ascii=False)
    return len(recs)

n1 = lm_eval_fmt(w_test, 'heldout_words')
n2 = lm_eval_fmt(g_test, 'heldout_grammar')
print(f'held-out 评测: 词 {n1} / 语法 {n2}')

# 训练条目评测集（同格式——测"记忆"）
n3 = lm_eval_fmt(w_train[:400], 'seen_words')
n4 = lm_eval_fmt(g_train[:200], 'seen_grammar')
print(f'seen 评测: 词 {n3} / 语法 {n4}')
print('\n数据就绪：injection/data/')