# -*- coding: utf-8 -*-
"""评审意见1（剂量防御）：3 epoch 重训 + heldout 复测
原 dose_and_calib.py 的 A 部分（B 部分口径校准已完成，结果在 results_dose.json）
"""
import json, os, sys, time, math
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'injection'))
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from peft import PeftModel, LoraConfig, get_peft_model
from collections import Counter

torch.set_num_threads(10)

BASE = os.path.join(ROOT, 'models/Qwen2.5-0.5B')
DATA = os.path.join(ROOT, 'injection/data/sft_train_fast.json')
OUT = os.path.join(ROOT, 'injection/qwen05b_gf0025_lora_3ep')
RESULT = os.path.join(ROOT, 'injection/results_dose.json')

tok = AutoTokenizer.from_pretrained(BASE)

CHOICES = ['答案：1', '答案：2', '答案：3', '答案：4', '答案：5', '答案：6', '答案：7-9']
LEVELS = ['1', '2', '3', '4', '5', '6', '7-9']

def clean0(t):
    for ch in ['\u200b', '\u200c', '\u200d', '\ufeff', '\u2060']:
        t = t.replace(ch, '')
    return t

def loglikelihood_parts(model, context, continuation):
    ids_ctx = tok(context, add_special_tokens=False)['input_ids']
    ids_cont = tok(continuation, add_special_tokens=False)['input_ids']
    ids = ids_ctx + ids_cont
    with torch.no_grad():
        logits = model(torch.tensor([ids])).logits[0]
    lp = 0.0
    for i, cid in enumerate(ids_cont):
        pos = len(ids_ctx) + i - 1
        lp += torch.log_softmax(logits[pos], dim=-1)[cid].item()
    return lp, len(ids_cont)

def eval_norm(model, recs, normalize=False):
    correct, n = 0, 0
    preds = []
    for r in recs:
        instr = clean0(r['instruction'])
        ctx = f"<|im_start|>user\n{instr}<|im_end|>\n<|im_start|>assistant\n"
        lps = [loglikelihood_parts(model, ctx, c) for c in CHOICES]
        if normalize:
            scores = [lp / nt for lp, nt in lps]
        else:
            scores = [lp for lp, _ in lps]
        pred = max(range(7), key=lambda k: scores[k])
        preds.append(pred)
        correct += int(pred == r['gold'])
        n += 1
        if n % 250 == 0:
            print(f'  {n}/{len(recs)} acc={correct/n*100:.1f}%', flush=True)
    return correct / n * 100, preds

# ---------- 训练数据（与 1ep 完全同构） ----------
pairs = json.load(open(DATA, encoding='utf-8'))
print(f'训练对: {len(pairs)}')

def encode(pair):
    msgs = pair['messages']
    text = tok.apply_chat_template(msgs, tokenize=False)
    ids = tok(text, truncation=True, max_length=160)['input_ids']
    prompt = tok.apply_chat_template(msgs[:1] + [{'role': 'assistant', 'content': ''}], tokenize=False)
    plen = len(tok(prompt, add_special_tokens=False)['input_ids'])
    labels = [-100] * min(plen, len(ids)) + ids[min(plen, len(ids)):]
    return {'input_ids': ids, 'labels': labels}

class DS(torch.utils.data.Dataset):
    def __init__(self, pairs):
        self.data = [encode(p) for p in pairs]
    def __len__(self):
        return len(self.data)
    def __getitem__(self, i):
        return self.data[i]

def collate(batch):
    mx = max(len(b['input_ids']) for b in batch)
    pad = tok.pad_token_id or tok.eos_token_id
    input_ids, labels, attn = [], [], []
    for b in batch:
        n = mx - len(b['input_ids'])
        input_ids.append(b['input_ids'] + [pad] * n)
        labels.append(b['labels'] + [-100] * n)
        attn.append([1] * len(b['input_ids']) + [0] * n)
    return {'input_ids': torch.tensor(input_ids), 'labels': torch.tensor(labels), 'attention_mask': torch.tensor(attn)}

ds = DS(pairs)
args = TrainingArguments(
    output_dir=os.path.join(ROOT, 'injection/ckpt'),
    per_device_train_batch_size=16,
    gradient_accumulation_steps=2,
    num_train_epochs=3,
    learning_rate=2e-4,
    logging_steps=50,
    save_strategy='no',
    report_to=[],
    use_cpu=True,
    dataloader_num_workers=0,
)

model_tr = get_peft_model(AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.float32),
                          LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                                      target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'],
                                      task_type='CAUSAL_LM'))
trainer = Trainer(model=model_tr, args=args, train_dataset=ds, data_collator=collate)
t0 = time.time()
trainer.train()
print(f'3epoch 训练用时: {(time.time()-t0)/60:.1f} 分钟')
model_tr.save_pretrained(OUT)
print(f'保存: {OUT}')

# ---------- 3ep 复测 ----------
del model_tr, trainer
model3 = PeftModel.from_pretrained(AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32), OUT)
model3.eval()
recs = json.load(open(os.path.join(ROOT, 'injection/data/heldout_words_1000.jsonl'), encoding='utf-8'))
recs_gold = [r['gold'] for r in recs]
gold_cnt = Counter(recs_gold)

acc3, preds3 = eval_norm(model3, recs)
lvl_hits3 = Counter()
for g, p in zip(recs_gold, preds3):
    if g == p:
        lvl_hits3[g] += 1
lvl_preds3 = Counter(preds3)
print('\n===== 3epoch 结果 =====')
print(f'总似然判别: {acc3:.1f}%')
print('按 gold 级召回:', {LEVELS[g]: f'{100*lvl_hits3[g]/gold_cnt[g]:.1f}%' for g in range(7)})
print('预测分布:', {LEVELS[k]: v for k, v in sorted(lvl_preds3.items())})

results = json.load(open(RESULT, encoding='utf-8'))
results.update({
    '三epoch_acc': acc3,
    '三epoch_按级召回': {LEVELS[g]: round(100 * lvl_hits3[g] / gold_cnt[g], 1) for g in range(7)},
    '三epoch_预测分布': {LEVELS[k]: v for k, v in sorted(lvl_preds3.items())},
    '三epoch_preds': preds3,
})
json.dump(results, open(RESULT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'\n保存: {RESULT}')