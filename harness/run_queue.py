# -*- coding: utf-8 -*-
"""run_queue.py —— 断点续跑驱动：在时限内尽量多跑缺失分片，可随时中断重入。

用法（harness/ 下）：
  ../.venv/Scripts/python.exe run_queue.py --model ../models/Qwen2.5-3B-Instruct \
      --prefix cceval_kno_u --count 34 --budget 240
已完成任务自动跳过（扫描 results 目录）；每跑完一个分片立即落盘，被杀也无损。
"""
import argparse, glob, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, '..', '.venv', 'Scripts', 'python.exe')


def done_tasks(out_root):
    done = set()
    for root, _d, files in os.walk(out_root):
        for fn in files:
            if fn.startswith('results_') and fn.endswith('.json'):
                try:
                    r = json.load(open(os.path.join(root, fn), encoding='utf-8'))
                    done.update(r.get('results', {}).keys())
                except Exception:
                    pass
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--prefix', required=True, help='任务前缀，如 cceval_kno_u')
    ap.add_argument('--count', type=int, required=True)
    ap.add_argument('--budget', type=float, default=240.0, help='本次调用的时间预算（秒）')
    ap.add_argument('--batch', type=int, default=512)
    args = ap.parse_args()

    model_name = os.path.basename(args.model.rstrip('/\\'))
    out_root = os.path.join(HERE, '..', 'results/harness', model_name)
    t0 = time.time()
    done = done_tasks(out_root)
    todo = [f'{args.prefix}{i}' for i in range(1, args.count + 1)
            if f'{args.prefix}{i}' not in done]
    print(f'已完成 {len(done)} 个任务；待跑 {len(todo)}：{todo[:8]}{"..." if len(todo) > 8 else ""}', flush=True)

    env = dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false')
    for task in todo:
        if time.time() - t0 > args.budget:
            print('预算用尽，安全退出（已完成部分均已落盘）', flush=True)
            break
        print(f'>>> {task} ...', flush=True)
        cmd = [PY, '-m', 'lm_eval', '--model', 'hf',
               '--model_args', f'pretrained={args.model},dtype=float32',
               '--tasks', task, '--include_path', 'tasks',
               '--device', 'cpu', '--batch_size', str(args.batch),
               '--output_path', out_root]
        p = subprocess.run(cmd, cwd=HERE, env=env, capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
        ok = f'|{task}' in p.stdout
        acc = ''
        for line in p.stdout.splitlines():
            if line.startswith(f'|{task}'):
                acc = line
        print(f'<<< {task} {"OK " + acc if ok else "FAILED"}', flush=True)
    print(f'本次用时 {time.time() - t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
