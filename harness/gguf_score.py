# -*- coding: utf-8 -*-
"""gguf_score.py —— 用 llama-server（llama.cpp）对 CC-Eval multiple_choice 题打分。

评分逻辑与 lm-evaluation-harness 一致：context = instruction + " "（特殊 token 开），
continuation = 候选（单独分词，无特殊 token）；对数似然求和取 argmax。
llama.cpp 不暴露 prompt 对数概率，这里用"全词表 top_logprobs + 强制逐 token 前缀"：
候选 token 序列建成 trie，每个 trie 节点一次请求（cache_prompt 复用前缀 KV），
从全词表 top_logprobs 中取目标 token 的精确 logprob —— 结果与 lm-eval 严格同口径。

用法（harness/ 下）：
  ../.venv/Scripts/python.exe gguf_score.py \
      --gguf ../models/Qwen2.5-7B-GGUF/qwen2.5-7b-instruct-q8_0-00001-of-00003.gguf \
      --data data/cceval_pho_poly.jsonl \
      --out ../results/harness/Qwen2.5-7B-q8_0/pho_poly.json --budget 240
支持断点续跑：--out 已存在时从已完成条数继续。
"""
import argparse, json, os, subprocess, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, '..', '..', 'llamacpp', 'cc_eval_srv.exe')


def post(port, path, payload, timeout=180):
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}',
                                 data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def wait_ready(port, proc, timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            raise RuntimeError('llama-server 退出，代码 ' + str(proc.returncode))
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=3) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        time.sleep(2)
    raise TimeoutError('llama-server 启动超时')


class Scorer:
    def __init__(self, port):
        self.port = port

    def tokenize(self, text, special):
        return post(self.port, '/tokenize', {'content': text, 'add_special': special}, 30)['tokens']

    def next_logprobs(self, prefix_ids):
        """返回 {token_id: logprob}：在 prefix_ids 之后每个候选 token 的对数概率。
        用 /v1/completions（prompt=token ids），规避原生 /completion 在采样到
        半 UTF-8 token 时省略 completion_probabilities 的问题。失败重试。"""
        for attempt in range(4):
            try:
                # max_tokens=4：采样到半个 UTF-8 token 时，让后续 token 补齐字节序列，
                # 否则 llama-server 会因文本不可解码而返回 logprobs=null
                r = post(self.port, '/v1/completions',
                         {'prompt': prefix_ids, 'max_tokens': 4, 'logprobs': 500000,
                          'temperature': 0.0})
                cp = r['choices'][0]['logprobs']['content'][0]
                return {e['id']: e['logprob'] for e in cp['top_logprobs']}
            except Exception as e:
                if attempt == 3:
                    print('FAILED prefix_len=', len(prefix_ids), type(e).__name__,
                          'resp=', json.dumps(r, ensure_ascii=False)[:500] if 'r' in dir() else 'no-resp',
                          flush=True)
                    raise
                time.sleep(2 * (attempt + 1))

    def score_choices(self, ctx_ids, choice_ids_list):
        """trie 共享前缀，逐节点一次请求，返回每个候选的总 logprob。"""
        scores = [0.0] * len(choice_ids_list)
        # 节点: (path tuple) -> [(choice_idx, next_pos)]
        root = {'__choices__': []}
        for i, ids in enumerate(choice_ids_list):
            node = root
            for pos, t in enumerate(ids):
                node = node.setdefault(t, {})
                node.setdefault('__choices__', []).append((i, pos))
        def walk(node, path):
            if '__choices__' in node:
                lp = self.next_logprobs(list(path))
                children = {k: v for k, v in node.items() if k != '__choices__'}
                for tok, child in children.items():
                    for (ci, pos) in child.get('__choices__', []):
                        scores[ci] += lp.get(tok, -100.0)
                    walk(child, path + (tok,))
        walk(root, tuple(ctx_ids))
        return scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gguf', required=True)
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--port', type=int, default=8477)
    ap.add_argument('--ctx', type=int, default=1024)
    ap.add_argument('--threads', type=int, default=14)
    ap.add_argument('--budget', type=float, default=250.0)
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.data, encoding='utf-8')]
    preds = []
    if os.path.exists(args.out):  # 断点续跑
        old = json.load(open(args.out, encoding='utf-8'))
        preds = old.get('preds', [])
        print(f'续跑：已有 {len(preds)}/{len(rows)}', flush=True)
    todo = rows[len(preds):]

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    log = open(args.out + '.server.log', 'w', encoding='utf-8', errors='replace')
    proc = subprocess.Popen([SERVER, '-m', args.gguf, '--port', str(args.port),
                             '--ctx-size', str(args.ctx), '-t', str(args.threads),
                             '--cache-reuse', '256', '--no-warmup', '--mlock'],
                            stdout=log, stderr=subprocess.STDOUT)
    try:
        wait_ready(args.port, proc)
        sc = Scorer(args.port)
        print('server ready', flush=True)
        t0 = time.time()
        for k, r in enumerate(todo):
            ctx_ids = sc.tokenize(r['instruction'] + ' ', True)
            choice_ids = [sc.tokenize(c, False) for c in r['choices']]
            s = sc.score_choices(ctx_ids, choice_ids)
            pred = max(range(len(s)), key=lambda i: s[i])
            preds.append({'item_id': r.get('item_id'), 'gold': r['gold'], 'pred': pred,
                          'correct': pred == r['gold']})
            n = len(preds)
            # 每题落盘：环境可能随时回收进程，进度零丢失优先
            acc0 = sum(p['correct'] for p in preds) / max(1, len(preds))
            with open(args.out, 'w', encoding='utf-8') as f:
                json.dump({'gguf': args.gguf, 'data': args.data, 'n': len(preds),
                           'total': len(rows), 'acc': acc0,
                           'complete': len(preds) == len(rows),
                           'seconds': time.time() - t0, 'preds': preds}, f, ensure_ascii=False, indent=1)
            if n % 10 == 0:
                el = time.time() - t0
                print(f'{n}/{len(rows)}  {el:.0f}s  eta {el / max(1, n - (len(rows) - len(todo))) * (len(rows) - n):.0f}s',
                      flush=True)
            if time.time() - t0 > args.budget:
                print('预算用尽，保存进度', flush=True)
                break
        acc = sum(p['correct'] for p in preds) / max(1, len(preds))
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump({'gguf': args.gguf, 'data': args.data, 'n': len(preds),
                       'total': len(rows), 'acc': acc, 'complete': len(preds) == len(rows),
                       'seconds': time.time() - t0, 'preds': preds}, f, ensure_ascii=False, indent=1)
        print(f'ACC {acc:.4f} ({sum(p["correct"] for p in preds)}/{len(preds)})'
              f'{" [完成]" if len(preds) == len(rows) else " [部分]"} -> {args.out}', flush=True)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except Exception:
            proc.kill()
        log.close()


if __name__ == '__main__':
    main()
