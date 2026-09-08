# -*- coding: utf-8 -*-
"""按等级分解的注入效果分析：重跑注入组 held-out 1000 + seen 400，保存逐题预测"""
import json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

torch.set_num_threads(20)

BASE = os.path.join(ROOT, 'models/Qwen2.5-0.5B')
LORA = os.path.join(ROOT, 'injection/qwen05b_gf0025_lora')
tok = AutoTokenizer.from_pretrained(BASE)

print('加载基座...')
model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32)
model.eval()
print('挂载 LoRA...')
model = PeftModel.from_pretrained(model, LORA)
model.eval()

CHOICES = ['答案：1', '答案：2', '答案：3', '答案：4', '答案：5', '答案：6', '答案：7-9']

def clean0(t):
    for ch in ['\u200b', '\u200c', '\u200d', '\ufeff', '\u2060']:
        t = (t or '').replace(ch, '')
    return t

def loglikelihood(model, context, continuation):
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

def eval_save(model, recs, name, outpath):
    preds = []
    t0 = time.time()
    for i, r in enumerate(recs):
        instr = clean0(r['instruction'])
        ctx = f"<|im_start|>user\n{instr}<|im_end|>\n<|im_start|>assistant\n"
        lps = [loglikelihood(model, ctx, c) for c in CHOICES]
        pred = max(range(7), key=lambda k: lps[k])
        preds.append({'gold': r['gold'], 'pred': pred, 'sub_type': r.get('sub_type', '')})
        if (i+1) % 200 == 0:
            print(f'  {name}: {i+1}/{len(recs)} ({(time.time()-t0)/60:.0f}min)', flush=True)
    json.dump(preds, open(outpath, 'w', encoding='utf-8'))
    acc = sum(1 for p in preds if p['gold'] == p['pred']) / len(preds) * 100
    print(f'{name}: {acc:.1f}%（n={len(recs)}）逐题已存 {outpath}')
    return acc

def load_recs(path):
    text = open(path, encoding='utf-8').read().strip()
    if text.startswith('['):
        return json.loads(text)
    return [json.loads(l) for l in text.splitlines() if l.strip()]

recs_w = load_recs(os.path.join(ROOT, 'injection/data/heldout_words_1000.jsonl'))
recs_s = load_recs(os.path.join(ROOT, 'injection/data/seen_words.jsonl'))
eval_save(model, recs_w, '注入/heldout_words', os.path.join(ROOT, 'injection/preds_heldout.json'))
eval_save(model, recs_s, '注入/seen', os.path.join(ROOT, 'injection/preds_seen.json'))
print('完成')