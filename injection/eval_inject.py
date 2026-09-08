# -*- coding: utf-8 -*-
"""注入效果评测：与 v1.1a harness 完全同口径
multiple_choice 对数似然（共享前缀「答案：」缓解位置偏差），0-shot
四组评测：
  1. heldout_words（3,325）——泛化
  2. heldout_grammar（169）——泛化
  3. seen_words（400）/ seen_grammar（200）——记忆
  4. KNO 400（原题库）——与基线可比的绝对数
模型：
  A. Qwen2.5-0.5B 基座（基线，v1.1a 实测 6.5%）
  B. 基座 + GF0025 LoRA（注入后）
"""
import json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

torch.set_num_threads(8)

BASE = os.path.join(ROOT, 'models/Qwen2.5-0.5B')
LORA = os.path.join(ROOT, 'injection/qwen05b_gf0025_lora')
tok = AutoTokenizer.from_pretrained(BASE)

print('加载基座...')
model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32)
model.eval()

CHOICES = ['答案：1', '答案：2', '答案：3', '答案：4', '答案：5', '答案：6', '答案：7-9']

def loglikelihood(model, context, continuation):
    """P(continuation|context) 对数似然（与 lm-eval 口径一致）"""
    ids_ctx = tok(context, add_special_tokens=False)['input_ids']
    ids_cont = tok(continuation, add_special_tokens=False)['input_ids']
    ids = ids_ctx + ids_cont
    with torch.no_grad():
        out = model(torch.tensor([ids]))
        logits = out.logits[0]
    lp = 0.0
    for i, cid in enumerate(ids_cont):
        pos = len(ids_ctx) + i - 1
        lp += torch.log_softmax(logits[pos], dim=-1)[cid].item()
    return lp

def clean0(t):
    if not t:
        return t
    for ch in ['\u200b', '\u200c', '\u200d', '\ufeff', '\u2060']:
        t = t.replace(ch, '')
    return t

def eval_mc(model, recs, name, chat_fmt=True):
    correct, n = 0, 0
    t0 = time.time()
    for i, r in enumerate(recs):
        instr = clean0(r['instruction'])
        if chat_fmt:
            ctx = f"<|im_start|>user\n{instr}<|im_end|>\n<|im_start|>assistant\n"
        else:
            ctx = instr + '\n'
        lps = [loglikelihood(model, ctx, c) for c in CHOICES]
        pred = max(range(len(lps)), key=lambda k: lps[k])
        if pred == r['gold']:
            correct += 1
        n += 1
        if (i+1) % 200 == 0:
            print(f'  {name}: {i+1}/{len(recs)} acc={correct/n*100:.1f}% ({(time.time()-t0)/60:.0f}min)', flush=True)
    acc = correct / n * 100
    print(f'{name}: {acc:.1f}%（n={n}, {(time.time()-t0)/60:.1f} 分钟）')
    return acc

def load_recs(path, limit=None):
    text = open(path, encoding='utf-8').read().strip()
    if text.startswith('['):
        recs = json.loads(text)          # JSON 数组格式
    else:
        recs = [json.loads(l) for l in text.splitlines() if l.strip()]  # 逐行 JSONL
    return recs[:limit] if limit else recs

RESULT_PATH = os.path.join(ROOT, 'injection/results_inject.json')
results = {}
if os.path.exists(RESULT_PATH):
    try:
        results = json.load(open(RESULT_PATH, encoding='utf-8'))
        print(f'断点续跑: 已有 {sum(len(v) for v in results.values())} 组结果')
    except Exception:
        results = {}

def eval_mc_cached(model, recs, name, chat_fmt=True, group=None, section=None):
    key = section
    if key in results.get(group, {}):
        print(f'[跳过] {name}（已完成: {results[group][key]}%）')
        return results[group][key]
    acc = eval_mc(model, recs, name, chat_fmt)
    results.setdefault(group, {})[key] = acc
    json.dump(results, open(RESULT_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return acc

# ===== A. 基座 =====
print('\n===== A. Qwen2.5-0.5B 基座 =====')
recs_w = load_recs(os.path.join(ROOT, 'injection/data/heldout_words_1000.jsonl'))
recs_g = load_recs(os.path.join(ROOT, 'injection/data/heldout_grammar.jsonl'))
results.setdefault('base', {})
eval_mc_cached(model, recs_w, '基座/heldout_words', chat_fmt=False, group='base', section='heldout_words_raw')
eval_mc_cached(model, recs_w, '基座/heldout_words', group='base', section='heldout_words_chat')
eval_mc_cached(model, recs_g, '基座/heldout_grammar', chat_fmt=False, group='base', section='heldout_grammar_raw')

# KNO 400（raw = lm-eval 口径，与 v1.1a 的 6.5% 可比；chat = 训练一致口径）
kno_recs = load_recs(os.path.join(ROOT, 'harness/data/cceval_kno.jsonl'))
eval_mc_cached(model, kno_recs, '基座/kno400', chat_fmt=False, group='base', section='kno400_raw')
eval_mc_cached(model, kno_recs, '基座/kno400', group='base', section='kno400_chat')

# ===== B. 注入后 =====
print('\n===== B. 基座 + GF0025 LoRA =====')
model = PeftModel.from_pretrained(model, LORA)
model.eval()
results.setdefault('injected', {})
eval_mc_cached(model, recs_w, '注入/heldout_words', group='injected', section='heldout_words_chat')
eval_mc_cached(model, recs_g, '注入/heldout_grammar', group='injected', section='heldout_grammar_chat')
eval_mc_cached(model, load_recs(os.path.join(ROOT, 'injection/data/seen_words.jsonl')), '注入/seen', group='injected', section='seen_chat')
eval_mc_cached(model, kno_recs, '注入/kno400', group='injected', section='kno400_chat')
eval_mc_cached(model, kno_recs, '注入/kno400', chat_fmt=False, group='injected', section='kno400_raw')

json.dump(results, open(os.path.join(ROOT, 'injection/results_inject.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n===== 结果汇总 =====')
for m, r in results.items():
    print(m, json.dumps(r, ensure_ascii=False))