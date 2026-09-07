# -*- coding: utf-8 -*-
"""对 llm_rubric 题用评委模型补评分"""
import os, sys, json, glob, re, time, argparse
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_eval import chat


def default_items_path():
    """v1.1 是 v1.0 超集（含 PHO）；优先用 v1.1，避免评委侧找不到题而漏评。"""
    v11 = os.path.join(ROOT, 'items/v1.1/items.jsonl')
    v10 = os.path.join(ROOT, 'items/v1.0/items.jsonl')
    return v11 if os.path.isfile(v11) else v10


def load_items(path):
    return {i['item_id']: i for i in (json.loads(l) for l in open(path, encoding='utf-8'))}


def main():
    ap = argparse.ArgumentParser(description='对 llm_rubric 题用评委模型补评分')
    ap.add_argument('eval_model', nargs='?', default='k2d6-agent')
    ap.add_argument('judge', nargs='?', default='k3-agent')
    ap.add_argument('--items', default=None, help='题库路径；默认优先 items/v1.1，否则 v1.0')
    args = ap.parse_args()

    EVAL_MODEL = args.eval_model
    JUDGE = args.judge
    base = os.environ['KIMI_BASE_URL']
    key = os.environ['KIMI_API_KEY']
    items_path = args.items or default_items_path()
    items = load_items(items_path)
    print(f'items={items_path}  n={len(items)}')

    def judge_one(it, answer):
        rub = '\n'.join(f"- {r['dim']}（满分{r['max']}）：{r['desc']}" for r in it['scoring']['rubric'])
        gold = json.dumps(it['reference'].get('gold_meta'), ensure_ascii=False)[:600]
        prompt = (f"你是评测评委。请根据量表给下面的模型回答打分。\n\n"
                  f"【题目指令】{it['prompt']['instruction']}\n【题目输入】{it['prompt'].get('input','')[:400]}\n"
                  f"【参考答案信息】{gold}\n\n【被评回答】{answer[:1500]}\n\n"
                  f"【量表】\n{rub}\n\n只输出 JSON：{{\"分数\": {{\"维度名\": 得分, ...}}, \"总分\": 数字}}")
        # thinking=True → run_eval.chat 发送 thinking disabled（与原先行为一致）
        out = chat(base, key, JUDGE, [{"role": "user", "content": prompt}], thinking=True)
        if out.startswith('__ERROR__'):
            return None
        m = re.search(r'"总分"\s*[:：]\s*(\d+(?:\.\d+)?)', out)
        if m:
            total = float(m.group(1))
            mx = sum(r['max'] for r in it['scoring']['rubric'])
            return total / mx
        return None

    todo = []
    for f in glob.glob(os.path.join(ROOT, 'results', EVAL_MODEL, '*.json')):
        d = json.load(open(f, encoding='utf-8'))
        it = items.get(d['item_id'])
        if it and it['scoring']['type'] == 'llm_rubric' and d.get('score') is None and not d.get('error'):
            todo.append((f, d, it))
    print(f'judge={JUDGE} pending={len(todo)}')

    def work(t):
        f, d, it = t
        s = judge_one(it, d.get('output', ''))
        if s is not None:
            d['score'] = s
            d['judge'] = JUDGE
            json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False)
        return s is not None

    n = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for ok in ex.map(work, todo):
            n += ok
            if n % 30 == 0: print(f'  judged {n}/{len(todo)}', flush=True)
    print('judged:', n)


if __name__ == '__main__':
    main()
