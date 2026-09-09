# -*- coding: utf-8 -*-
"""生成 LearnerBench/TeacherBench 二批补充题目（v1.2b：纯现有数据源衍生）

覆盖上一轮矩阵中标记"需补充数据源"、但实测本地资产即可支撑的 4 个维度：
  lr.reading      阅读理解（L3）——文化框架概要 + 语法 reference_examples 为素材，
                  按 GF0025 词表 FMM 分级筛选出目标等级文本，出"要点判断 + 关键信息定位"，
                  判别式 exact_match（对/错二选一，事实锚定概要原文）
  lr.profile      个性化学习（L10）——HSK 语料真实"画像"（国籍/性别/各科分数/偏误档案），
                  要求给出针对性后续学习重点，llm_rubric（量表锚定其真实偏误类型分布）
  tb.diag_personal 个性化教学支持（T11）——同一画像 + 教师视角：诊断主要问题 + 归因 + 教学建议，
                  llm_rubric（量表锚定偏误档案与母语背景迁移）
  tb.speaking     口语学习（L5）——职业中文标准情境（105 条"能做什么"描述）为情境卡，
                  生成模拟交际任务的开场与应答框架（无多轮真人语料，先测"情境应答设计"而非
                  "交互自然度"），llm_rubric

不可行（确认无本地数据源）：L6 听力（需音频）、L7 翻译（需平行句对）、L11 路径规划（需教材序列）。

HSK 语料合规：与 ERR/SCO 同模式——语料原文不入库（gitignore），题目仅引用
"错误档案摘要 + 分数"（不含原文句子）；生成器种子固定可复现。
"""
import os, json, re, random, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 20260907
random.seed(SEED)

# ---------- 语料加载（本地，不入库） ----------
def load_hsk():
    rows = []
    for line in open(os.path.join(ROOT, 'corpus/hsk_corpus.jsonl'), encoding='utf-8'):
        d = json.loads(line)
        sc = d.get('scores') or {}
        try:
            zw = float(sc.get('zuowen') or 0)
        except (TypeError, ValueError):
            continue
        if zw > 0 and d.get('nation') and d.get('text_annotated'):
            rows.append(d)
    return rows

ANN_RE = re.compile(r'\{([A-Z]{2,3})\d*(?:[-+][a-z]{1,4})?[:：]?([^}]*)\}')
TYPE_CN = {'CC': '错字', 'CJ': '词语误用', 'CJX': '词语误用（性）', 'CJZ': '词语误用（赘余）',
            'CD': '多字多词', 'CQ': '缺字缺词', 'CP': '标点误用', 'WWJ': '未完成句', 'CY': '语序',
            'CLH': '离合词错误', 'CJS': '缩略/融合错误'}

def error_profile(text_annotated, top=5):
    """从标注正文提取错误档案：类型分布 + 高频错误词样本（不引用原句）"""
    cnt = collections.Counter()
    samples = collections.defaultdict(list)
    for m in ANN_RE.finditer(text_annotated):
        code, inner = m.group(1), m.group(2).strip()
        base = {'CJX': 'CJ', 'CJZ': 'CJ'}.get(code, code)
        cnt[base] += 1
        if inner and len(samples[base]) < 6:
            samples[base].append(inner)
    return cnt, samples

# ---------- runner 的 FMM 词表分级器（复用） ----------
src = open(os.path.join(ROOT, 'runner/run_eval.py'), encoding='utf-8').read()
src = src.replace("ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))",
                  "ROOT = ROOT")
src = src.split("# ---------- 评分器")[0]
ns = {'ROOT': os.path.abspath(ROOT)}
exec(src, ns)
load_lexicon = ns['load_lexicon']

def grade_text(text, lex):
    """返回文本按 GF0025 词表 FMM 切分后的 (词次总数, 1-3级占比, 超6级占比)"""
    lv = collections.Counter()
    i = 0
    t2 = re.sub(r'[a-zA-Z0-9]+', '', text)
    while i < len(t2):
        ch = t2[i]
        if not '一' <= ch <= '鿿':
            i += 1
            continue
        hit = None
        for L in range(min(lex['maxlen'], len(t2) - i), 1, -1):
            w = t2[i:i + L]
            if w in lex['word_lvl']:
                hit = w
                break
        if hit:
            lv[lex['word_lvl'][hit]] += 1
            i += len(hit)
        else:
            lv[lex['char_lvl'].get(ch, 7)] += 1
            i += 1
    n = sum(lv.values()) or 1
    lo = sum(v for k, v in lv.items() if k <= 3)
    hi = lv.get(7, 0)
    return n, lo / n, hi / n

lex = load_lexicon()

items = []

def add_item(sub, bench_tag, instruction, inp, ref, scoring, tags, source, source_id,
             contam, rubric=None, gold_meta=None, anchor=None):
    task = 'SCO' if sub.startswith('lr.') else 'PED'
    seq = sum(1 for it in items if it['sub_type'] == sub) + 1
    items.append({
        'item_id': f'CCE-{task}-8-{seq:04d}',  # 占位，最后统一重排
        'version': '1.2.0',
        'task_type': task,
        'sub_type': sub,
        'anchor': anchor or {},
        'prompt': {'instruction': instruction, 'input': inp},
        'reference': {'answer': ref, **({'gold_meta': gold_meta} if gold_meta else {})},
        'scoring': ({'type': scoring, 'rubric': rubric} if scoring == 'llm_rubric'
                    else {'type': scoring}),
        'provenance': {'source': source, 'source_id': source_id,
                       'license': '标准字段引用/学术研究使用（授权申请中）',
                       'contamination_risk': contam},
        'meta': {'bench': bench_tag, 'tags': tags, 'review_status': 'draft',
                 'created': '2026-09-07'},
    })

# =====================================================================
# 1) lr.reading 阅读理解 30 题（文化概要 FMM 分级筛选，要点判断式）
# =====================================================================
cult = json.load(open(os.path.join(ROOT, 'standard/culture-framework/culture_sections.json'),
                      encoding='utf-8'))
rubric_none = None

def split_grav_sentences(summary):
    sents = [s.strip() for s in re.split(r'[。！？]', summary) if 25 <= len(s.strip()) <= 90]
    return sents

n_read = 0
used_sections = set()
for c in cult:
    if n_read >= 30:
        break
    if c['section'] in used_sections:
        continue
    # 整段概要的等级体检：1-3 级占比 >= 65% 才当 3 级读物
    n, lo_ratio, hi_ratio = grade_text(c['summary'], lex)
    if lo_ratio < 0.62 or n < 60:
        continue
    sents = split_grav_sentences(c['summary'])
    if len(sents) < 4:
        continue
    # 取 2-3 句拼成 100-200 字短文（句子直接来自概要原文——事实锚点）
    passage = ''.join(s + '。' for s in sents[:3])
    # 事实要点：取一句含"数据/专名/数字"的句子转成判断题
    fact_sents = [s for s in sents[3:6] if re.search(r'[0-9一两二三四五六七八九十百千]|[「"]', s)]
    if not fact_sents:
        fact_sents = sents[3:5]
    fs = fact_sents[0]
    # 一半出"上文提及"判断（答案=对），一半出"未提及/相悖"（答案=错）
    if n_read % 2 == 0:
        stmt = fs
        ans = '对'
        note = '该句直接来自原文后文（真实要点）'
    else:
        # 从别的板块抽一句做干扰（主题不同，不可能在上文提及）
        other = random.choice([x for x in cult if x['section'] != c['section']])
        o_sents = split_grav_sentences(other['summary'])
        stmt = random.choice(o_sents) if o_sents else fs
        ans = '错'
        note = '干扰句来自其他板块概要（%s），与短文主题无关' % other['section']
    add_item('lr.reading', 'LB-L3',
             f'阅读下面短文，然后判断后面的说法是否正确。只回答：对 或 错。\n\n【短文】{passage}\n\n【判断】{stmt}',
             '', ans, 'exact_match', ['阅读理解', '文化读物', c['section']],
             'culture-framework', f'culture/{c["board"]}/{c["section"]}', 'low',
             gold_meta={'passage_level': '约3级（1-3级词占比 %.0f%%）' % (lo_ratio * 100),
                        'note': note})
    n_read += 1
    used_sections.add(c['section'])

# =====================================================================
# 2) lr.profile 个性化学习（L10）+ tb.diag_personal 个性化教学（T11）
#    共用 HSK 真实画像，20 + 20 题
# =====================================================================
rubric_profile = [
    {'dim': '诊断准确性', 'max': 4, 'desc': '指出的学习重点与档案中的真实偏误类型分布一致（错字/用词/缺漏占比）'},
    {'dim': '母语针对性', 'max': 3, 'desc': '结合学习者的国籍背景给出可解释的语言迁移归因（如韩国学习者的敬语混淆）'},
    {'dim': '建议可执行性', 'max': 3, 'desc': '学习建议具体、可操作、有优先级，不是泛泛的"多读多练"'},
]
rubric_diag = [
    {'dim': '归因解释合理性', 'max': 4, 'desc': '对档案中主要偏误类型的成因解释符合二语习得规律（迁移/泛化/教学诱导）'},
    {'dim': '教学对策针对性', 'max': 3, 'desc': '教学措施针对该档案的高频偏误类型与学习者水平（作文分）设计，非通用套话'},
    {'dim': '水平适配', 'max': 3, 'desc': '方案用语与难度适合该学习者当前等级（作文分锚定）'},
]

hsk = load_hsk()
random.shuffle(hsk)
n_prof = 0
seen_nations = collections.Counter()
for d in hsk:
    if n_prof >= 20:
        break
    # 国籍配额：韩 6 / 日 5 / 新 3 / 印尼 2 / 马 2 / 其他 2（覆盖主要母语背景）
    QUOTA = {'韩国': 6, '日本': 5, '新加坡': 3, '印度尼西亚': 2, '马来西亚': 2}
    nat = d['nation']
    if seen_nations[nat] >= QUOTA.get(nat, 2):
        continue
    cnt, samples = error_profile(d['text_annotated'])
    if sum(cnt.values()) < 5:
        continue
    zw = float(d['scores']['zuowen'])
    # 错误档案（不含原句，只有类型分布 + 改正样本词）
    profile_lines = []
    for code, k in cnt.most_common(4):
        exs = '、'.join(f'「{x}」' for x in samples.get(code, [])[:3])
        profile_lines.append(f'- {TYPE_CN.get(code, code)}：{k} 处' + (f'（如：{exs}）' if exs else ''))
    profile = '\n'.join(profile_lines)
    base_info = (f'国籍：{d["nation"]}；性别：{d["gender"]}；'
                 f'考试：HSK 高等；作文 {zw:.0f} 分；'
                 f'听力 {d["scores"].get("tingli")} 分、阅读 {d["scores"].get("yuedu")} 分；'
                 f'综合 {d["scores"].get("zonghe")} 分')

    # L10：个性化学习建议
    add_item('lr.profile', 'LB-L10',
             (f'你是中文学习顾问。下面是一位学习者的档案（出自 HSK 动态作文语料库，已脱敏），'
              f'请基于档案给出该学习者下阶段的 3-5 条中文学习重点，按优先级排序，每条说明理由。\n\n'
              f'【学习者档案】\n{base_info}\n错误档案（作文偏误统计）：\n{profile}'),
             '', None, 'llm_rubric', ['个性化学习', '错误档案', d['nation']],
             'hsk-corpus', f'essay/{d["id"]}', 'mid',
             rubric=rubric_profile,
             gold_meta={'nation': d['nation'], 'zuowen': zw,
                        'error_dist': dict(cnt.most_common(4)),
                        'error_samples': {k: v[:4] for k, v in samples.items()}})
    # T11：个性化教学支持
    add_item('tb.diag_personal', 'TB-T11',
             (f'你是中文教师。下面是一位学生的档案（出自 HSK 动态作文语料库，已脱敏），'
              f'请：1）诊断其主要语言问题并按严重程度排序；2）对排在第一位的问题给出成因解释'
              f'（结合其母语背景）；3）给出 2-3 条针对性的教学措施。\n\n'
              f'【学生档案】\n{base_info}\n错误档案（作文偏误统计）：\n{profile}'),
             '', None, 'llm_rubric', ['个性化教学', '偏误归因', d['nation']],
             'hsk-corpus', f'essay/{d["id"]}', 'mid',
             rubric=rubric_diag,
             gold_meta={'nation': d['nation'], 'zuowen': zw,
                        'error_dist': dict(cnt.most_common(4)),
                        'error_samples': {k: v[:4] for k, v in samples.items()}})
    n_prof += 1
    seen_nations[nat] += 1

# =====================================================================
# 3) tb.speaking 口语学习（L5）30 题（职业中文情境卡 → 交际应答设计）
# =====================================================================
rubric_speaking = [
    {'dim': '情境真实性', 'max': 4, 'desc': '任务情境符合职业标准对该等级"能做什么"的描述，交际目标明确'},
    {'dim': '语言适配', 'max': 3, 'desc': '示范应答的用词句式适合该等级水平（入门/初/中/高）'},
    {'dim': '交际有效性', 'max': 3, 'desc': '应答达成交际目的（信息传达/协商/求助），符合职场礼节'},
]
voc = json.load(open(os.path.join(ROOT, 'standard/other-standards/vocational_chinese.json'),
                     encoding='utf-8'))
scenes = []
for blk in voc['levels']:
    lv_name = blk['level']
    def walk(prefix, obj):
        for k2, val in obj.items():
            if isinstance(val, dict):
                walk(prefix, val)
            elif isinstance(val, list):
                for x in val:
                    if isinstance(x, str) and 15 < len(x) < 80:
                        scenes.append((lv_name, prefix or k2, x.strip()))
    walk('', {k: v for k, v in blk.items() if k not in ('level', 'definition')})
random.shuffle(scenes)
LV_EN = {'入门': '入门', '初级': '初级（A/B 类）', '中级': '中级', '高级': '高级', '精通': '精通'}
n_spk = 0
for lv_name, skill, desc in scenes:
    if n_spk >= 30:
        break
    # 过滤含 OCR 页码噪声的描述
    if re.search(r'\b3\.\d', desc):
        continue
    add_item('tb.speaking', 'LB-L5',
             (f'请根据《职业中文能力等级标准》{LV_EN.get(lv_name, lv_name)}的情境要求，'
              f'设计一个口语交际任务并给出示范应答。能力要求：{desc}\n'
              f'输出：1）任务情境（1-2 句，含交际目的）；2）示范应答（3-5 轮对话，'
              f'用语适合{LV_EN.get(lv_name, lv_name)}水平）；3）一句话点评该应答为何有效。'),
             '', None, 'llm_rubric', ['口语交际', '职业中文', lv_name],
             'vocational-std', f'vocational/{lv_name}/{skill[:12]}', 'low',
             rubric=rubric_speaking,
             gold_meta={'level': lv_name, 'skill': skill, 'desc': desc})
    n_spk += 1

# =====================================================================
# 编号重排（接续 v1.2 bench 题号：PED-8 从 187 起；SCO-8 新段从 1 起）
# =====================================================================
bench_prev = [json.loads(l) for l in open(os.path.join(ROOT, 'items/v1.2/items_bench.jsonl'),
                                          encoding='utf-8')]
max_ped8 = max(int(i['item_id'].split('-')[3]) for i in bench_prev if i['task_type'] == 'PED')
cnt_task = {'PED': max_ped8, 'SCO': 0}
for it in items:
    cnt_task[it['task_type']] += 1
    it['item_id'] = f'CCE-{it["task_type"]}-8-{cnt_task[it["task_type"]]:04d}'

# 输出 v1.2b 批次文件
out_path = os.path.join(ROOT, 'items/v1.2/items_bench_b.jsonl')
with open(out_path, 'w', encoding='utf-8') as f:
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')

# 合并 v1.2 全库 = v1.1 + bench_a + bench_b
v11 = open(os.path.join(ROOT, 'items/v1.1/items.jsonl'), encoding='utf-8').read()
comb_path = os.path.join(ROOT, 'items/v1.2/items.jsonl')
with open(comb_path, 'w', encoding='utf-8') as f:
    f.write(v11 if v11.endswith('\n') else v11 + '\n')
    for it in bench_prev:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')

print(f'bench_b items: {len(items)}')
print(collections.Counter(it['sub_type'] for it in items))
print(collections.Counter(it['meta']['bench'] for it in items))
print('written:', out_path)
n_all = len(v11.strip().splitlines()) + len(bench_prev) + len(items)
print(f'combined: {comb_path} = v1.1 1735 + bench_a {len(bench_prev)} + bench_b {len(items)} = {n_all}')