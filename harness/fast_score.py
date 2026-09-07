# -*- coding: utf-8 -*-
"""fast_score.py —— CC-Eval multiple_choice 高速打分器（前缀 KV 缓存）

与 lm-evaluation-harness 的 loglikelihood multiple_choice 等价的评分逻辑：
  context = instruction + " "（target_delimiter），continuation = 候选答案；
  context 只前向一次并用 KV cache 复用，各候选只算自己的 token ——
  比 lm-eval 逐候选重复计算整个 context 快约 5 倍，3B/7B 模型 CPU 评测可行。

用法（harness/ 下）：
  ../.venv/Scripts/python.exe fast_score.py --model ../models/Qwen2.5-3B-Instruct \
      --data data/cceval_kno.jsonl --out ../results/harness/Qwen2.5-3B-Instruct/kno.json \
      --start 0 --end 100
"""
import argparse, json, os, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def score(model, tok, instruction, choices, device):
    ctx = tok(instruction + ' ', add_special_tokens=True, return_tensors='pt').input_ids.to(device)
    with torch.no_grad():
        out = model(ctx, use_cache=True)
        past0, logits0 = out.past_key_values, out.logits[:, -1, :]
        scores = []
        for ch in choices:
            ids = tok(ch, add_special_tokens=False, return_tensors='pt').input_ids.to(device)
            past, logits, total = past0, logits0, 0.0
            for i in range(ids.shape[1]):
                token = ids[0, i]
                total += torch.log_softmax(logits[0].float(), -1)[token].item()
                if i + 1 < ids.shape[1]:
                    out2 = model(token.view(1, 1), past_key_values=past, use_cache=True)
                    past, logits = out2.past_key_values, out2.logits[:, -1, :]
            scores.append(total)
    return scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--end', type=int, default=10 ** 9)
    ap.add_argument('--dtype', default='float32')
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.data, encoding='utf-8')][args.start:args.end]
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=getattr(torch, args.dtype))
    model.eval()
    device = 'cpu'

    preds, t0 = [], time.time()
    for k, r in enumerate(rows):
        s = score(model, tok, r['instruction'], r['choices'], device)
        pred = max(range(len(s)), key=lambda i: s[i])
        preds.append({'item_id': r.get('item_id'), 'gold': r['gold'], 'pred': pred,
                      'correct': pred == r['gold']})
        if (k + 1) % 10 == 0:
            el = time.time() - t0
            print(f'{k + 1}/{len(rows)}  {el:.0f}s  eta {el / (k + 1) * (len(rows) - k - 1):.0f}s',
                  flush=True)
    acc = sum(p['correct'] for p in preds) / len(preds)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump({'model': args.model, 'data': args.data,
                   'start': args.start, 'n': len(preds), 'acc': acc,
                   'seconds': time.time() - t0, 'preds': preds}, f, ensure_ascii=False, indent=1)
    print(f'ACC {acc:.4f}  ({sum(p["correct"] for p in preds)}/{len(preds)})  -> {args.out}')


if __name__ == '__main__':
    main()
