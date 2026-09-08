# -*- coding: utf-8 -*-
"""GF0025 标准知识注入：Qwen2.5-0.5B 基座 LoRA SFT（CPU float32）
8,170 指令对（词定级 7,767 + 语法定级 403），chat 模板，LoRA r=16
"""
import json, os, sys, time, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model

MODEL = os.path.join(ROOT, 'models/Qwen2.5-0.5B')
DATA = os.path.join(ROOT, 'injection/data/sft_train_fast.json')
OUT = os.path.join(ROOT, 'injection/qwen05b_gf0025_lora')

torch.set_num_threads(20)
print('torch threads:', torch.get_num_threads())

tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32)
model.config.use_cache = False

lora = LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05,
    target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj'],
    task_type='CAUSAL_LM',
)
model = get_peft_model(model, lora)
model.print_trainable_parameters()

pairs = json.load(open(DATA, encoding='utf-8'))
print(f'训练对: {len(pairs)}')

def encode(pair):
    msgs = pair['messages']
    text = tok.apply_chat_template(msgs, tokenize=False)
    ids = tok(text, truncation=True, max_length=160)['input_ids']
    # 只对 assistant 部分计 loss：找 assistant 起始位置
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
print(f'编码完成: {len(ds)} 条')

args = TrainingArguments(
    output_dir=os.path.join(ROOT, 'injection/ckpt'),
    per_device_train_batch_size=16,
    gradient_accumulation_steps=2,   # 有效 batch 32
    num_train_epochs=1,
    learning_rate=2e-4,
    logging_steps=50,
    save_strategy='no',
    report_to=[],
    use_cpu=True,
    dataloader_num_workers=0,
)

trainer = Trainer(model=model, args=args, train_dataset=ds, data_collator=collate)
t0 = time.time()
trainer.train()
print(f'训练用时: {(time.time()-t0)/60:.1f} 分钟')

model.save_pretrained(OUT)
tok.save_pretrained(OUT)
print(f'LoRA 保存: {OUT}')