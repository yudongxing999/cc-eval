# -*- coding: utf-8 -*-
"""评审意见1（剂量防御）+ 意见4（先验偏置校准）补充实验

实验A（剂量）：从既有 LoRA ckpt 继续训练 2 个 epoch（共 3 epoch），
  复测 heldout_words_1000，看 2/3/5/6 级是否出现非零预测——
  "阶梯式相变"假设：宏观三元范畴（初/中/高）先建立，细粒度亚级后调谐。
实验B（口径）：选项 token 先验偏置检验——
  ① 基座对七个 CHOICES 的"裸先验"P(choice|通用语境)，看是否有系统性抑制；
  ② 长度归一化判别（per-token average log-likelihood）重判 1,000 题，看结论是否翻转。
"""
import json, os, sys, time, math
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'injection'))
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

torch.set_num_threads(10)

BASE = os.path.join(ROOT, 'models/Qwen2.5-0.5B')
DATA = os.path.join(ROOT, 'injection/data/sft_train_fast.json')
LORA = os.path.join(ROOT, 'injection/qwen05b_gf0025_lora')
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
    """返回 (总对数似然, 续写 token 数)——长度归一化用"""
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

# ---------- 实验B-1：选项 token 裸先验（用基座测） ----------
print('===== B-1: 选项裸先验（基座，通用语境）=====')
model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32)
model.eval()

ctxs = {
    '空语境': '',
    '任务语境（不含词条）': '根据《国际中文教育中文水平等级标准》（GF 0025-2021）词汇表，词语「学习」（动）属于哪个等级？请只回答一个等级：1、2、3、4、5、6 或 7-9，不要解释。',
}
prior = {}
for ctx_name, ctx in ctxs.items():
    row = {}
    for ch in CHOICES:
        lp, ntok = loglikelihood_parts(model, ctx, ch)
        row[ch] = {'sum_lp': round(lp, 2), 'per_token': round(lp / ntok, 3), 'ntok': ntok}
    prior[ctx_name] = row
    print(ctx_name, json.dumps(row, ensure_ascii=False))

# ---------- 加载 LoRA，先做当前模型（1ep）的长度归一化复测 ----------
print('\n===== B-2: 长度归一化判别复测（1ep LoRA）=====')
model = PeftModel.from_pretrained(model, LORA)
model.eval()

recs = json.load(open(os.path.join(ROOT, 'injection/data/heldout_words_1000.jsonl'), encoding='utf-8'))

def eval_norm(model, recs, normalize):
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

t0 = time.time()
acc_sum, preds_sum = eval_norm(model, recs, normalize=False)
print(f'1ep 总似然判别: {acc_sum:.1f}%（复现用，{(time.time()-t0)/60:.0f}min）')
t0 = time.time()
acc_norm, preds_norm = eval_norm(model, recs, normalize=True)
print(f'1ep 长度归一化判别: {acc_norm:.1f}%（{(time.time()-t0)/60:.0f}min）')

from collections import Counter
by_level = defaultdict = None
lvl_hits = Counter()
lvl_preds = Counter()
recs_gold = [r['gold'] for r in recs]
for g, p in zip(recs_gold, preds_norm):
    if g == p:
        lvl_hits[g] += 1
    lvl_preds[p] += 1
print('长度归一化下按 gold 级的召回:', {LEVELS[g]: f'{100*lvl_hits[g]/max(1,sum(1 for x in recs_gold if x==g)):.1f}%' for g in range(7)})
print('预测分布:', {LEVELS[k]: v for k, v in sorted(lvl_preds.items())})

results = {
    '选项先验': prior,
    '一epoch_总似然': acc_sum,
    '一epoch_长度归一': acc_norm,
    '一epoch_归一化召回': {LEVELS[g]: round(100 * lvl_hits[g] / max(1, sum(1 for x in recs_gold if x == g)), 1) for g in range(7)},
    '一epoch_归一化预测分布': {LEVELS[k]: v for k, v in sorted(lvl_preds.items())},
}

# ---------- 实验A：剂量——从 LoRA 继续训 2 epoch ----------
print('\n===== A: 剂量实验（3 epoch 总计）=====')
from peft import LoraConfig, get_peft_model
from transformers import Trainer, TrainingArguments

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
    num_train_epochs=3,   # 总计 3 epoch（Trainer 从头计——用 3 epoch 完整重训，与 1ep 同初始化可对照）
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

# 3ep 模型复测
del model_tr
model3 = PeftModel.from_pretrained(AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32), OUT)
model3.eval()
acc3, preds3 = eval_norm(model3, recs, normalize=False)
lvl_hits3 = Counter()
for g, p in zip(recs_gold, preds3):
    if g == p:
        lvl_hits3[g] += 1
lvl_preds3 = Counter(p for p in preds3)
gold_cnt = Counter(recs_gold)
print('\n===== 3epoch 结果 =====')
print(f'总似然判别: {acc3:.1f}%')
print('按 gold 级召回:', {LEVELS[g]: f'{100*lvl_hits3[g]/gold_cnt[g]:.1f}%' for g in range(7)})
print('预测分布:', {LEVELS[k]: v for k, v in sorted(lvl_preds3.items())})

results.update({
    '三epoch_acc': acc3,
    '三epoch_按级召回': {LEVELS[g]: round(100 * lvl_hits3[g] / gold_cnt[g], 1) for g in range(7)},
    '三epoch_预测分布': {LEVELS[k]: v for k, v in sorted(lvl_preds3.items())},
    '三epoch_preds': preds3,
    '一epoch_preds_norm': preds_norm,
})
json.dump(results, open(RESULT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'\n保存: {RESULT}')