# -*- coding: utf-8 -*-
"""CC-Eval V1.0 题库生成器：从标准层数据 + HSK 语料自动生成评测题"""
import json, re, random, os
from collections import defaultdict, Counter

random.seed(20260905)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'items', 'v1.0')
os.makedirs(OUT, exist_ok=True)

STD = os.path.join(ROOT, 'standard', 'gf0025-2021')
vocab = json.load(open(os.path.join(STD, 'vocabulary.json'), encoding='utf-8'))
chars = json.load(open(os.path.join(STD, 'characters.json'), encoding='utf-8'))
grammar = json.load(open(os.path.join(STD, 'grammar.json'), encoding='utf-8'))
culture = json.load(open(os.path.join(ROOT, 'standard', 'culture-framework', 'culture_sections.json'), encoding='utf-8'))
teacher = json.load(open(os.path.join(ROOT, 'standard', 'other-standards', 'teacher_competence.json'), encoding='utf-8'))
textbook = json.load(open(os.path.join(ROOT, 'standard', 'other-standards', 'textbook_evaluation.json'), encoding='utf-8'))
voc = json.load(open(os.path.join(ROOT, 'standard', 'other-standards', 'vocational_chinese.json'), encoding='utf-8'))
essays = [json.loads(l) for l in open(os.path.join(ROOT, 'corpus', 'hsk_corpus.jsonl'), encoding='utf-8')]

LVL_CODE = lambda lv: 7 if lv == '7-9' else (int(lv) if isinstance(lv, (int, str)) and str(lv).isdigit() else 9)
seq_counters = defaultdict(int)
def mkid(task, lv):
    seq_counters[(task, LVL_CODE(lv))] += 1
    return f"CCE-{task}-{LVL_CODE(lv)}-{seq_counters[(task, LVL_CODE(lv))]:04d}"

items = []

# ============ KNO 等级知识 400 ============
# 1) 语法点等级定位 200
gp_pool = [g for g in grammar if g.get('item') and len(g['item']) <= 20]
for g in random.sample(gp_pool, min(200, len(gp_pool))):
    items.append({
        "item_id": mkid("KNO", g['level']), "version": "1.0.0",
        "task_type": "KNO", "sub_type": "kno.grammar_level",
        "anchor": {"level": g['level'], "grammar_no": g['no']},
        "prompt": {
            "instruction": f"根据《国际中文教育中文水平等级标准》（GF 0025-2021）语法等级大纲，语法点「{g['item']}」（{g['category']}—{g['subcategory']}）属于哪个等级？请只回答一个等级：1、2、3、4、5、6 或 7-9，不要解释。",
            "input": ""},
        "reference": {"answer": str(g['level'])},
        "scoring": {"type": "exact_match"},
        "provenance": {"source": "gf0025-2021", "source_id": f"grammar#{g['no']}", "license": "标准字段引用", "contamination_risk": "high"},
        "meta": {"tags": ["语法", "等级定位"], "review_status": "draft", "created": "2026-09-05"}})
# 2) 词等级定位 150（只用单义词）
for v in random.sample(vocab, 150):
    items.append({
        "item_id": mkid("KNO", v['level']), "version": "1.0.0",
        "task_type": "KNO", "sub_type": "kno.vocab_level",
        "anchor": {"level": v['level'], "vocab_no": v['no']},
        "prompt": {"instruction": f"根据《国际中文教育中文水平等级标准》（GF 0025-2021）词汇表，词语「{v['word']}」{('（' + v['pos'] + '）') if v['pos'] else ''}属于哪个等级？请只回答一个等级：1、2、3、4、5、6 或 7-9，不要解释。", "input": ""},
        "reference": {"answer": str(v['level'])},
        "scoring": {"type": "exact_match"},
        "provenance": {"source": "gf0025-2021", "source_id": f"vocab#{v['no']}", "license": "标准字段引用", "contamination_risk": "high"},
        "meta": {"tags": ["词汇", "等级定位"], "review_status": "draft", "created": "2026-09-05"}})
# 3) 字等级定位 50（排除多音重复字）
char_count = Counter(c['char'] for c in chars)
uniq_chars = [c for c in chars if char_count[c['char']] == 1]
for c in random.sample(uniq_chars, 50):
    items.append({
        "item_id": mkid("KNO", c['level']), "version": "1.0.0",
        "task_type": "KNO", "sub_type": "kno.char_level",
        "anchor": {"level": c['level'], "char": c['char']},
        "prompt": {"instruction": f"根据《国际中文教育中文水平等级标准》（GF 0025-2021）汉字表，汉字「{c['char']}」（{c['pinyin']}）属于哪个等级？请只回答一个等级：1、2、3、4、5、6 或 7-9，不要解释。", "input": ""},
        "reference": {"answer": str(c['level'])},
        "scoring": {"type": "exact_match"},
        "provenance": {"source": "gf0025-2021", "source_id": f"char#{c['no']}", "license": "标准字段引用", "contamination_risk": "high"},
        "meta": {"tags": ["汉字", "等级定位"], "review_status": "draft", "created": "2026-09-05"}})

# ============ ERR 偏误识别与纠正 400 ============
ANN_RE = re.compile(r'\{([A-Z]{2,3})\d*(?:[-+][a-z]{1,4})?[:：]?([^}]*)\}')
MARK_RE = re.compile(r'[\[［][A-Za-zＡ-Ｚ][^\]］]{0,3}[\]］]')
TYPE_MAP = {"CC": "错字", "CD": "多字/多词", "CQ": "缺字/缺词", "CJ": "词语误用", "CP": "标点误用"}
CODE_RE = {"CC": "CC", "CD": "CD", "CQ": "CQ", "CJ": "CJ", "CJX": "CJ", "CJZ": "CJ", "CP": "CP"}

def clean_text(t):
    """先全局去掉 [BC]/[B历] 这类位置标记，再断句，避免标记被切到两句之间"""
    return MARK_RE.sub('', t)

def raw_surface(sent):
    """还原学习者原文：CD 保留内容，CQ 及其余标注去掉标注部分，[X] 位置标记删除"""
    def rep(m):
        code, inner = m.group(1), m.group(2)
        base = CODE_RE.get(code)
        if base == "CD": return inner
        if base == "CQ": return ""
        return ""  # CC/CJ/CP 等：花括号内为改正内容，原文在括号前
    s = ANN_RE.sub(rep, sent)
    return MARK_RE.sub('', s).strip()

def gold_correction(code, inner):
    base = CODE_RE.get(code, code)
    if base == "CD": return f"应删去「{inner}」"
    if base == "CQ": return f"应补上「{inner}」"
    if base == "CC": return f"错字，应改为「{inner}」"
    if base == "CJ": return f"用词不当，应改为「{inner}」"
    if base == "CP": return f"标点应改为「{inner}」"
    return inner

quota = {"CC": 130, "CJ": 120, "CQ": 80, "CD": 50, "CP": 20}
picked = defaultdict(list)
random.shuffle(essays)
for r in essays:
    if all(len(picked[k]) >= quota[k] for k in quota): break
    text = clean_text(r['text_annotated'])
    for sent in re.split(r'[。！？!?\n]', text):
        sent = sent.strip()
        marks = ANN_RE.findall(sent)
        known = [(CODE_RE[c], c, i) for c, i in marks if c in CODE_RE]
        if len(marks) != 1 or len(known) != 1: continue
        base, code, inner = known[0]
        if len(picked[base]) >= quota[base]: continue
        inner = inner.strip()
        if not inner or len(inner) > 10 or re.search(r'[{}【】\[\]［］]', inner): continue
        if re.fullmatch(r'[a-zA-Z]+', inner): continue
        raw = raw_surface(sent)
        if not (8 <= len(raw) <= 60) or '×' in raw or ANN_RE.search(raw) or MARK_RE.search(sent): continue
        if not re.search(r'[一-鿿]', raw): continue
        picked[base].append((r, raw, base, inner, sent))
for base, lst in picked.items():
    for r, raw, b, inner, orig in lst:
        items.append({
            "item_id": mkid("ERR", 9), "version": "1.0.0",
            "task_type": "ERR", "sub_type": "err.detect_and_correct",
            "anchor": {"level": "7-9"},
            "prompt": {
                "system": "你是一位国际中文教师，正在批改外国学习者的汉语作文。",
                "instruction": "下列句子出自外国学习者作文，含有一处偏误。请：1）指出偏误类型（错字/词语误用/多字多词/缺字缺词/标点误用/语序）；2）给出改正后的完整句子。",
                "input": raw},
            "reference": {"answer": gold_correction(b if b != "CJ" else "CJ", inner),
                          "gold_meta": {"error_type": TYPE_MAP[b], "correction": inner, "annotated": orig}},
            "scoring": {"type": "set_overlap", "params": {"fields": ["error_type", "correction_contains"], "min_overlap": 0.5}},
            "provenance": {"source": "hsk-corpus", "source_id": r['id'], "license": "学术研究使用（授权申请中）", "contamination_risk": "mid"},
            "meta": {"tags": ["偏误", TYPE_MAP[b], r['nation']], "review_status": "draft", "created": "2026-09-05"}})

# ============ SCO 作文评分 250 ============
def strip_essay(text):
    text = clean_text(text)
    lines = text.split('\n')
    while len(lines) > 1:
        head = lines[0].strip()
        is_meta = ('Title' in head) or (re.search(r'\d{6}', head) and len(re.findall(r'[一-鿿]', head)) < 12) or not head
        if is_meta: lines = lines[1:]
        else: break
    body = '\n'.join(lines)
    body = ANN_RE.sub(lambda m: m.group(2) if CODE_RE.get(m.group(1)) == 'CD' else '', body)
    return MARK_RE.sub('', body).strip()

bands = [(0, 59), (60, 69), (70, 79), (80, 89), (90, 100)]
pool_by_band = defaultdict(list)
for r in essays:
    try: sc = float(r['scores']['zuowen'])
    except (ValueError, TypeError): continue
    txt = strip_essay(r['text_annotated'])
    if not (150 <= len(txt) <= 900): continue
    for lo, hi in bands:
        if lo <= sc <= hi:
            pool_by_band[(lo, hi)].append((r, txt, sc)); break
for (lo, hi), pool in pool_by_band.items():
    random.shuffle(pool)
    for r, txt, sc in pool[:50]:
        items.append({
            "item_id": mkid("SCO", 9), "version": "1.0.0",
            "task_type": "SCO", "sub_type": "sco.essay_score",
            "anchor": {"level": "7-9"},
            "prompt": {
                "system": "你是 HSK（高等）作文阅卷员，按 0-100 分评分。",
                "instruction": f"请为下面这篇外国学习者的 HSK 高等作文评分（0-100 的整数），并用两三句话说明评分依据。作文题目：《{r['title']}》。只输出 JSON：{{\"score\": 分数, \"reason\": \"依据\"}}",
                "input": txt},
            "reference": {"answer": int(sc), "gold_meta": {"zuowen_score": sc, "certificate": r['certificate'], "nation": r['nation'], "exam_date": r['exam_date']}},
            "scoring": {"type": "numeric_proximity", "params": {"tolerance_full": 10, "tolerance_half": 20}},
            "provenance": {"source": "hsk-corpus", "source_id": r['id'], "license": "学术研究使用（授权申请中）", "contamination_risk": "mid"},
            "meta": {"tags": ["作文评分", f"band{lo}-{hi}"], "review_status": "draft", "created": "2026-09-05"}})

# ============ GEN 分级生成 300 ============
# 词级索引（FMM 用）
word_lvl = {}
for v in vocab:
    lv = LVL_CODE(v['level'])
    if v['word'] not in word_lvl or lv < word_lvl[v['word']]:
        word_lvl[v['word']] = lv
# 1) 限级改写 120：输入句取文化框架概要中含高等级词（level>=5 或表外）的句子
hard_sents = []
for s in culture:
    for sent in re.split(r'[。！？]', s['summary']):
        sent = sent.strip()
        if 20 <= len(sent) <= 70 and any(w in sent for w in word_lvl if word_lvl[w] >= 5):
            hard_sents.append((s['section'], sent))
random.shuffle(hard_sents)
for i, (secname, sent) in enumerate(hard_sents[:120]):
    tgt = 1 + (i % 3)  # 目标等级 1/2/3 轮换
    items.append({
        "item_id": mkid("GEN", tgt), "version": "1.0.0",
        "task_type": "GEN", "sub_type": "gen.level_controlled_rewrite",
        "anchor": {"level": tgt, "culture_section": secname},
        "prompt": {"instruction": f"把下面这段话改写给汉语 {tgt} 级水平的学习者。要求：用词不超过《等级标准》{tgt} 级词汇；句子简短；保留原意。", "input": sent},
        "reference": {"answer": None, "gold_meta": {"note": "开放生成，无唯一答案"}},
        "scoring": {"type": "deterministic_rule", "params": {"check": "vocab_level", "max_vocab_level": tgt, "vocab_table": "gf0025-2021/vocabulary.json"}},
        "constraints": {"max_vocab_level": tgt},
        "provenance": {"source": "culture-framework", "source_id": secname, "license": "标准字段引用", "contamination_risk": "low"},
        "meta": {"tags": ["分级", "改写"], "review_status": "draft", "created": "2026-09-05"}})
# 2) 看词写话 120：同级词组合
by_lvl = defaultdict(list)
for v in vocab:
    lv = LVL_CODE(v['level'])
    if lv <= 5 and 2 <= len(v['word']) <= 4:
        by_lvl[lv].append(v)
for lv in range(1, 6):
    for _ in range(24):
        ws = random.sample(by_lvl[lv], 4)
        words = [w['word'] for w in ws]
        items.append({
            "item_id": mkid("GEN", lv), "version": "1.0.0",
            "task_type": "GEN", "sub_type": "gen.words_to_passage",
            "anchor": {"level": lv, "vocab_no": [w['no'] for w in ws]},
            "prompt": {"instruction": f"用下面 4 个词语写一段 3-5 句的话，供汉语 {lv} 级学习者阅读。4 个词都必须用到；其他用词不得超过 {lv} 级。", "input": "、".join(words)},
            "reference": {"answer": None, "gold_meta": {"required_words": words}},
            "scoring": {"type": "deterministic_rule", "params": {"check": "contains_words+vocab_level", "required_words": words, "max_vocab_level": lv}},
            "constraints": {"max_vocab_level": lv},
            "provenance": {"source": "gf0025-2021", "source_id": ",".join(str(w['no']) for w in ws), "license": "标准字段引用", "contamination_risk": "low"},
            "meta": {"tags": ["分级", "写话"], "review_status": "draft", "created": "2026-09-05"}})
# 3) 语法点造句 60
gp_s = random.sample([g for g in grammar if LVL_CODE(g['level']) <= 6 and g.get('item')], 60)
for g in gp_s:
    items.append({
        "item_id": mkid("GEN", g['level']), "version": "1.0.0",
        "task_type": "GEN", "sub_type": "gen.grammar_sentence",
        "anchor": {"level": g['level'], "grammar_no": g['no']},
        "prompt": {"instruction": f"用语法点「{g['item']}」写一个句子，语境适合{g['level']}级汉语学习者课堂练习。", "input": ""},
        "reference": {"answer": None, "gold_meta": {"grammar_content": g['content'][:200]}},
        "scoring": {"type": "llm_rubric", "rubric": [
            {"dim": "语法点使用正确", "max": 5, "desc": f"正确使用了「{g['item']}」"},
            {"dim": "等级适配", "max": 3, "desc": "用词与句式复杂度符合目标等级"},
            {"dim": "自然度", "max": 2, "desc": "句子自然、语境清楚"}]},
        "provenance": {"source": "gf0025-2021", "source_id": f"grammar#{g['no']}", "license": "标准字段引用", "contamination_risk": "low"},
        "meta": {"tags": ["语法", "造句"], "review_status": "draft", "created": "2026-09-05"}})

# ============ CUL 文化语用 128 ============
for s in culture:
    for tr in s['teaching_refs'][:3]:  # 每板块取三个学段
        stage = tr['stage']
        objs = tr.get('objectives', [])[:2]
        items.append({
            "item_id": mkid("CUL", 9), "version": "1.0.0",
            "task_type": "CUL", "sub_type": "cul.pragmatic_reasoning",
            "anchor": {"culture_section": f"{s['board']}/{s['section']}"},
            "prompt": {
                "system": "你是国际中文教育文化课教师。",
                "instruction": f"一位{stage}学段的外国学生在学习「{s['section']}」时向你提问，请你给出文化上准确、适合该学段理解的解答。\n\n学生问题：请结合具体例子，介绍中国「{s['section']}」方面最值得了解的内容，以及它与学习者本国文化可能的不同。",
                "input": ""},
            "reference": {"answer": None, "gold_meta": {"section": s['section'], "board": s['board'], "stage": stage, "objectives": objs, "summary_excerpt": s['summary'][:300]}},
            "scoring": {"type": "llm_rubric", "rubric": [
                {"dim": "文化准确性", "max": 4, "desc": "内容与文化框架该项目的概要和教学目标一致，无事实错误"},
                {"dim": "学段适配", "max": 3, "desc": f"深度与表达适合{stage}学段"},
                {"dim": "跨文化意识", "max": 3, "desc": "恰当比较中外差异，避免刻板印象"}]},
            "provenance": {"source": "culture-framework", "source_id": f"{s['board']}/{s['section']}", "license": "标准字段引用", "contamination_risk": "mid"},
            "meta": {"tags": ["文化", s['board'], stage], "review_status": "draft", "created": "2026-09-05"}})

# ============ PED 教学专业能力 150 ============
# 1) 标准归属题（exact_match）：教师标准 45 + 教材指标 45
tc_flat = [(b['l1'], b['l2'], it) for b in teacher['competency_framework'] for it in b['items']]
for l1, l2, it in random.sample(tc_flat, 45):
    items.append({
        "item_id": mkid("PED", 9), "version": "1.0.0",
        "task_type": "PED", "sub_type": "ped.teacher_std_locate",
        "anchor": {"teacher_competence": f"{l1}/{l2}"},
        "prompt": {"instruction": f"根据《国际中文教师专业能力标准》，能力描述「{it}」属于哪个二级能力领域？只回答领域名称。", "input": ""},
        "reference": {"answer": l2},
        "scoring": {"type": "exact_match"},
        "provenance": {"source": "teacher-std", "source_id": f"{l1}/{l2}", "license": "标准字段引用", "contamination_risk": "mid"},
        "meta": {"tags": ["教师标准"], "review_status": "draft", "created": "2026-09-05"}})
te_flat = [(b['l1'], b['l2'], it) for b in textbook['qualitative'] + textbook['normative'] for it in b['items']]
for l1, l2, it in random.sample(te_flat, 45):
    items.append({
        "item_id": mkid("PED", 9), "version": "1.0.0",
        "task_type": "PED", "sub_type": "ped.textbook_std_locate",
        "anchor": {"textbook_indicator": f"{l1}/{l2}"},
        "prompt": {"instruction": f"根据《国际中文教材评价标准》，评价内容「{it}」属于哪个一级指标？只回答指标名称。", "input": ""},
        "reference": {"answer": l1},
        "scoring": {"type": "exact_match"},
        "provenance": {"source": "textbook-std", "source_id": f"{l1}/{l2}", "license": "标准字段引用", "contamination_risk": "mid"},
        "meta": {"tags": ["教材标准"], "review_status": "draft", "created": "2026-09-05"}})
# 2) 职业中文场景 60
vc_combos = []
for lv in voc['levels']:
    branches = [(None, lv)] + [(c, lv[c]) for c in ('class_A', 'class_B') if isinstance(lv.get(c), dict)]
    for cls, node in branches:
        for sk in ('听力理解', '口语表达', '阅读理解', '书面写作'):
            for desc in (node.get(sk) or []):
                desc = re.sub(r'\s*\d+(\.\d+)*\s*$', '', desc).strip()
                if desc and len(desc) >= 8:
                    tag = f"{lv['level']}{'（' + cls[-1] + '类）' if cls else ''}"
                    vc_combos.append((tag, sk, desc))
random.shuffle(vc_combos)
for lvname, sk, desc in vc_combos[:60]:
    items.append({
        "item_id": mkid("PED", 9), "version": "1.0.0",
        "task_type": "PED", "sub_type": "ped.vocational_scenario",
        "anchor": {"level": lvname},
        "prompt": {
            "system": "你是职业中文课程设计专家。",
            "instruction": f"根据《职业中文能力等级标准》{lvname}{sk}的要求「{desc}」，设计一个课堂情景任务：说明场景、学习者的任务、完成标准。200 字以内。",
            "input": ""},
        "reference": {"answer": None, "gold_meta": {"level": lvname, "skill": sk, "descriptor": desc}},
        "scoring": {"type": "llm_rubric", "rubric": [
            {"dim": "与等级描述一致", "max": 4, "desc": "任务难度与标准要求相符"},
            {"dim": "职业场景真实性", "max": 3, "desc": "场景贴近真实职场"},
            {"dim": "可操作性", "max": 3, "desc": "任务可直接用于课堂"}]},
        "provenance": {"source": "vocational-std", "source_id": f"{lvname}/{sk}", "license": "标准字段引用", "contamination_risk": "low"},
        "meta": {"tags": ["职业中文", sk], "review_status": "draft", "created": "2026-09-05"}})

# ============ 输出 ============
out_path = os.path.join(OUT, 'items.jsonl')
with open(out_path, 'w', encoding='utf-8') as f:
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')

cnt = Counter(i['task_type'] for i in items)
sub = Counter(i['sub_type'] for i in items)
scr = Counter(i['scoring']['type'] for i in items)
print('TOTAL', len(items))
print('by task:', dict(cnt))
print('by subtype:', dict(sub))
print('by scorer:', dict(scr))
err_fill = {k: len(v) for k, v in picked.items()}
print('ERR filled:', err_fill)
sco_fill = {f"{k[0]}-{k[1]}": min(len(v), 50) for k, v in pool_by_band.items()}
print('SCO bands:', sco_fill)
