# -*- coding: utf-8 -*-
"""CC-Eval 评测运行器：OpenAI 兼容接口，断点续跑，确定性评分器"""
import os, sys, json, re, time, argparse
from concurrent.futures import ThreadPoolExecutor
import urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- 词表 & FMM ----------
_vocab_cache = {}
def load_lexicon():
    if _vocab_cache: return _vocab_cache
    vocab = json.load(open(os.path.join(ROOT, 'standard/gf0025-2021/vocabulary.json'), encoding='utf-8'))
    chars = json.load(open(os.path.join(ROOT, 'standard/gf0025-2021/characters.json'), encoding='utf-8'))
    wl, cl = {}, {}
    def lc(lv): return 7 if lv == '7-9' else int(lv)
    for v in vocab:
        lv = lc(v['level'])
        if v['word'] not in wl or lv < wl[v['word']]: wl[v['word']] = lv
    for c in chars:
        lv = lc(c['level'])
        if c['char'] not in cl or lv < cl[c['char']]: cl[c['char']] = lv
    _vocab_cache.update(word_lvl=wl, char_lvl=cl, maxlen=max(len(w) for w in wl))
    return _vocab_cache

def check_vocab_level(text, max_lvl):
    """FMM 切分，返回 (通过?, 超级词列表)"""
    lx = load_lexicon()
    wl, cl, mx = lx['word_lvl'], lx['char_lvl'], lx['maxlen']
    violations, i = [], 0
    text = re.sub(r'[a-zA-Z0-9]+', '', text)  # 西文数字豁免
    while i < len(text):
        ch = text[i]
        if not '一' <= ch <= '鿿': i += 1; continue
        hit = None
        for L in range(min(mx, len(text) - i), 1, -1):
            w = text[i:i+L]
            if w in wl: hit = w; break
        if hit:
            if wl[hit] > max_lvl: violations.append(hit)
            i += len(hit)
        else:
            if cl.get(ch, 7) > max_lvl: violations.append(ch)
            i += 1
    return (len(violations) == 0, violations)

# ---------- 输出清洗 ----------
def clean_output(s):
    s = re.sub(r'<think>.*?</think>', '', s, flags=re.S)
    return s.strip()

# ---------- 评分器 ----------
# 拼音规范化：声调符→数字原位，ü 归一，去空格/隔音符/连字符
TONE2NUM = {}
for _base, _marks in [('a', 'āáǎà'), ('o', 'ōóǒò'), ('e', 'ēéěè'),
                      ('i', 'īíǐì'), ('u', 'ūúǔù'), ('ü', 'ǖǘǚǜ'), ('ê', 'ếề')]:
    for _i, _m in enumerate(_marks, 1):
        TONE2NUM[_m] = _base + str(_i)

def canon_pinyin(s):
    s = s.lower().replace('u:', 'ü').replace('v', 'ü')
    out = []
    for ch in s:
        if ch in TONE2NUM:
            out.append(TONE2NUM[ch])
        elif ch.isalpha() or ch.isdigit():
            out.append(ch)
    return ''.join(out)

PY_TOKEN = re.compile(r"[A-Za-züÜāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ][A-Za-züÜāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ0-9'·\-]*")
def extract_pinyin(out):
    o = clean_output(out)
    m = PY_TOKEN.search(o)
    return canon_pinyin(m.group(0)) if m else canon_pinyin(o)

NUM_CN = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5', '六': '6'}
def norm_level(s):
    s = clean_output(s)
    m = re.search(r'7[-—~到]9|高等', s)
    if m: return '7-9'
    m = re.search(r'[1-6]', s)
    if m: return m.group(0)
    for k, v in NUM_CN.items():
        if k in s: return v
    return s

def score_exact(item, out):
    gold = str(item['reference']['answer'])
    st = item['sub_type']
    if st.startswith('kno.') or st == 'pho.syl_level':
        return 1.0 if norm_level(out) == gold else 0.0
    if st == 'pho.syl_legal':
        o = clean_output(out)
        if re.search(r'非法|不合法|不存在|不是合法|不属于|不合法', o):
            pred = '非法'
        elif '合法' in o:
            pred = '合法'
        else:
            return 0.0
        return 1.0 if pred == gold else 0.0
    if st in ('pho.tone_actual', 'pho.polyphonic'):
        return 1.0 if extract_pinyin(out) == canon_pinyin(gold) else 0.0
    pred = clean_output(out).strip('。「」 \n')
    gold_n = gold.strip()
    return 1.0 if (pred == gold_n or gold_n in pred and len(pred) <= len(gold_n) + 6) else 0.0

def score_numeric(item, out):
    gold = float(item['reference']['answer'])
    tol_full = item['scoring']['params'].get('tolerance_full', 10)
    tol_half = item['scoring']['params'].get('tolerance_half', 20)
    pred = None
    m = re.search(r'"score"\s*[:：]\s*(\d+)', out)
    if not m: m = re.search(r'(\d{1,3})\s*分', out)
    if not m: m = re.search(r'\b(\d{1,3})\b', clean_output(out))
    if m: pred = float(m.group(1))
    if pred is None: return 0.0
    d = abs(pred - gold)
    return 1.0 if d <= tol_full else (0.5 if d <= tol_half else 0.0)

TYPE_KW = {
    "错字": ["错字", "别字"],
    "词语误用": ["词语误用", "用词", "错词", "搭配不当"],
    "多字/多词": ["多字", "多词", "多余", "冗余", "删去", "删掉", "删除"],
    "缺字/缺词": ["缺字", "缺词", "缺少", "遗漏", "漏"],
    "标点误用": ["标点"],
    "语序": ["语序", "词序"],
}
def score_err(item, out):
    g = item['reference']['gold_meta']
    etype, corr = g['error_type'], g['correction']
    o = clean_output(out)
    t_ok = any(kw in o for kw in TYPE_KW.get(etype, [etype]))
    c_ok = corr and corr in o
    if etype == "多字/多词":
        c_ok = bool(re.search(r'(删|去掉|多余)[^。]{0,8}' + re.escape(corr), o)) or (corr in o and any(k in o for k in ['删', '多余', '去掉']))
    return (1.0 if t_ok else 0.0) * 0.5 + (0.5 if c_ok else 0.0)

def score_gen(item, out):
    o = clean_output(out)
    p = item['scoring']['params']
    max_lvl = p.get('max_vocab_level', 9)
    ok, viol = check_vocab_level(o, max_lvl)
    req = p.get('required_words') or []
    missing = [w for w in req if w not in o]
    total = (1 if ok else 0) + (1 if not missing else 0)
    return total / 2 if req else (1.0 if ok else 0.0)

SCORERS = {"exact_match": score_exact, "numeric_proximity": score_numeric,
           "set_overlap": score_err, "deterministic_rule": score_gen}

# ---------- API ----------
def chat(base, key, model, messages, tries=4, thinking=False):
    body = {"model": model, "messages": messages}
    if thinking:
        body["thinking"] = {"type": "disabled"}
    url = base.rstrip('/')
    if url.endswith('chat/completions'):
        pass  # 完整 URL 直接用
    elif not re.search(r'/v\d[a-z0-9]*$', url):
        url += '/v1'
    if not url.endswith('chat/completions'):
        url += '/chat/completions'
    for att in range(tries):
        try:
            req = urllib.request.Request(url,
                data=json.dumps(body).encode(),
                headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.load(r)
            return resp['choices'][0]['message']['content']
        except Exception as e:
            if att == tries - 1: return f"__ERROR__ {type(e).__name__}: {e}"
            time.sleep(2 * (att + 1))

def run_one(base, key, model, item, thinking=False):
    msgs = []
    if item['prompt'].get('system'):
        msgs.append({"role": "system", "content": item['prompt']['system']})
    q = item['prompt']['instruction'] + ('\n\n' + item['prompt']['input'] if item['prompt'].get('input') else '')
    msgs.append({"role": "user", "content": q})
    out = chat(base, key, model, msgs, thinking=thinking)
    st = item['scoring']['type']
    if out.startswith('__ERROR__'):
        return {"output": out, "score": None, "error": True}
    if st == 'llm_rubric':
        return {"output": out, "score": None, "note": "pending judge"}
    try:
        return {"output": out, "score": SCORERS[st](item, out)}
    except Exception as e:
        return {"output": out, "score": None, "error": f"scorer: {e}"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--name', default=None, help='结果目录名，默认同 model')
    ap.add_argument('--base', default=None)
    ap.add_argument('--key', default=None)
    ap.add_argument('--thinking-off', action='store_true', help='发送 thinking disabled（仅 Kimi 网关）')
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--budget', type=int, default=260, help='本次运行秒数预算')
    ap.add_argument('--only-scorer', default=None)
    ap.add_argument('--rpm', type=float, default=0, help='每分钟请求上限，0=不限')
    def _default_items():
        v11 = os.path.join(ROOT, 'items/v1.1/items.jsonl')
        v10 = os.path.join(ROOT, 'items/v1.0/items.jsonl')
        return v11 if os.path.isfile(v11) else v10
    ap.add_argument('--items', default=_default_items(), help='题库文件路径（默认优先 v1.1）')
    ap.add_argument('--max-items', type=int, default=0, help='最多施测题数（0=不限，烟测用）')
    args = ap.parse_args()

    base = args.base or os.environ['KIMI_BASE_URL']
    key = args.key or os.environ['KIMI_API_KEY']
    name = args.name or args.model
    items = [json.loads(l) for l in open(args.items, encoding='utf-8')]
    outdir = os.path.join(ROOT, 'results', name)
    os.makedirs(outdir, exist_ok=True)
    done = {f[:-5] for f in os.listdir(outdir) if f.endswith('.json')}
    todo = [i for i in items if i['item_id'] not in done]
    if args.only_scorer:
        todo = [i for i in todo if i['scoring']['type'] == args.only_scorer]
    if args.max_items > 0:
        todo = todo[:args.max_items]
    print(f"name={name} model={args.model} total={len(items)} done={len(done)} todo={len(todo)}")

    t0 = time.time(); n = 0
    from concurrent.futures import as_completed
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {}
        for it in todo:
            if time.time() - t0 > args.budget: break
            futs[ex.submit(run_one, base, key, args.model, it, args.thinking_off)] = it
            if args.rpm > 0:
                time.sleep(60.0 / args.rpm)
        for fut in as_completed(futs):
            it = futs[fut]
            try:
                res = fut.result()
            except Exception as e:
                res = {"output": "", "score": None, "error": str(e)}
            with open(os.path.join(outdir, it['item_id'] + '.json'), 'w', encoding='utf-8') as f:
                json.dump({"item_id": it['item_id'], "model": args.model, **res}, f, ensure_ascii=False)
            n += 1
            if n % 50 == 0: print(f"  progress {n}/{len(todo)} elapsed={time.time()-t0:.0f}s", flush=True)
    print(f"DONE batch={n} elapsed={time.time()-t0:.0f}s")

if __name__ == '__main__':
    main()
