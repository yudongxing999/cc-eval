# -*- coding: utf-8 -*-
"""任务3：生成任务的标准知识注入检验——限级改写（论文二任务的注入/外挂修复对照）
三臂：
  A) 7B 原生（无注入）：直接改写
  B) 7B + 词表外挂提示：prompt 里给出目标级词表摘要（GF0025 N 级词全列太长——给 N 级允许词的说明+示例？）
     外挂的工程形态是解码约束，这里测提示形态的上限
  C) 0.5B 注入版（已有 LoRA）对照——太弱，跳过；用 7B 提示对照即可
评分：与论文二同口径（FMM 词表审计违规密度 + 通过率 + 保真）
"""
import json, os, subprocess, sys, time, urllib.request, random, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'runner'))
from run_eval import check_vocab_level, clean_output, load_lexicon

GGUF = os.path.join(ROOT, 'models/Qwen2.5-7B-GGUF/qwen2.5-7b-instruct-q8_0-00001-of-00003.gguf')
SERVER = os.path.join(ROOT, '..', 'llamacpp/llama-server.exe')
PORT = 8799
lx = load_lexicon()
WL = lx['word_lvl']

sample = json.load(open(os.path.join(ROOT, 'injection/gen_task_sample.json'), encoding='utf-8'))
items = {json.loads(l)['item_id']: json.loads(l) for l in open(os.path.join(ROOT, 'items/v1.1/items.jsonl'), encoding='utf-8')}

def ensure_server():
    # 启 llama-server（若未启动）
    try:
        urllib.request.urlopen(f'http://127.0.0.1:{PORT}/health', timeout=2)
        print('llama-server 已在运行')
        return
    except Exception:
        pass
    print('启动 llama-server...')
    subprocess.Popen([SERVER, '-m', GGUF, '--port', str(PORT), '-c', '8192', '-t', '16'],
                     stdout=open(os.path.join(os.environ['LOCALAPPDATA'], 'Temp', 'llama_gen.log'), 'w'),
                     stderr=subprocess.STDOUT)
    for _ in range(120):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{PORT}/health', timeout=2)
            print('就绪')
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError('server 启动失败')

def gen(prompt, max_tokens=400):
    body = {
        "model": "qwen", 
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens, "temperature": 0.7,
    }
    req = urllib.request.Request(f'http://127.0.0.1:{PORT}/v1/chat/completions',
        data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as r:
        resp = json.load(r)
    return resp['choices'][0]['message']['content']

# B 臂的词表提示：目标级的边界说明。GF0025 一级 497 词全列太长——工程外挂的提示形态：
# 给出"高频允许词样例 + 明确约束"。更公平的做法：给完整词表文件路径说明没法做（离线）——
# 测试两种提示强度：B1 轻提示（重申约束+3 个替换示例），B2 强提示（目标级词表全文按 60 字截断？）
# 决策：B1 = 原题面 + 显式重申；B2 = 原题面 + 附目标级词表前 200 词（长 prompt 测试）
def lvl_words(n, k=200):
    ws = [w for w, lv in WL.items() if (lv if isinstance(lv, int) else int(lv) if lv else 9) == n]
    random.seed(42)
    random.shuffle(ws)
    return ws[:k]

def run_arm(arm, out_path):
    results = []
    t0 = time.time()
    for idx, iid in enumerate(sample):
        it = items[iid]
        base_prompt = it['prompt']['instruction'] + '\n' + (it['prompt'].get('input') or '')
        m = re.search(r'(\d) 级', it['prompt']['instruction'])
        cap = int(m.group(1))
        if arm == 'A':
            prompt = base_prompt
        elif arm == 'B1':
            prompt = base_prompt + '\n\n【重要】输出中不得出现超出 ' + str(cap) + ' 级词表的任何词语。逐词自查：写完一段后检查每个词，把超纲词换成更简单的说法（如用"很多"代替"大量"）。'
        elif arm == 'B2':
            words = '、'.join(lvl_words(cap, 200))
            prompt = base_prompt + f'\n\n【词表提示】以下是《等级标准》{cap} 级的部分常用词（你只能使用这些等级以内的词）：{words}\n若必须表达高级概念，用这些简单词解释它。'
        out = gen(prompt)
        ok, viol = check_vocab_level(clean_output(out), cap)
        results.append({'item_id': iid, 'target': cap, 'arm': arm, 'pass': ok,
                        'n_viol': len(viol), 'viol': viol[:20], 'out': out})
        print(f'  {arm} {idx+1}/{len(sample)} {iid} pass={ok} 违规={len(viol)} ({(time.time()-t0)/60:.1f}min)', flush=True)
    json.dump(results, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    pr = sum(1 for r in results if r['pass']) / len(results) * 100
    mv = sum(r['n_viol'] for r in results) / len(results)
    print(f'{arm} 臂完成: 通过率 {pr:.1f}%，平均违规 {mv:.1f} 词/篇（n={len(results)}）')
    return pr, mv

ensure_server()
os.makedirs(os.path.join(ROOT, 'injection/gen_task'), exist_ok=True)
run_arm('A', os.path.join(ROOT, 'injection/gen_task/armA_native.json'))
run_arm('B1', os.path.join(ROOT, 'injection/gen_task/armB1_restate.json'))
run_arm('B2', os.path.join(ROOT, 'injection/gen_task/armB2_lexhint.json'))