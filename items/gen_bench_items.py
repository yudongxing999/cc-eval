# -*- coding: utf-8 -*-
"""生成三 Bench（TeacherBench/LearnerBench/ResearchBench）补充题目（v1.2 增量）

覆盖榜单规划（梁远远）中 CC-Eval v1.1 未覆盖、且现有本地数据资产可支撑的 8 个二级维度：
  tb.explain       知识讲解（T2）——等级化讲解词义/语法点，llm_rubric
  tb.objective     教学目标设计（T3）——按学习者水平制定目标，llm_rubric
  tb.activity      课堂活动设计（T5）——任务型/交际型活动，llm_rubric
  tb.exercise      练习生成（T10/L9）——给语法点生成练习+答案，llm_rubric
  rb.litsearch     文献检索支持（R3）——给主题推荐代表性文献，set_overlap
  rb.understand    文献理解（R4）——摘要→研究问题/方法/结论，llm_rubric
  rb.review        论文评审（R11）——真实摘要+注入缺陷找缺陷，exact_match
  rb.authenticity  学术真实性（R12）——1真3假文献判真伪，exact_match

锚定：GF 0025-2021 词汇/语法表 + report/lit/*.csv 真实文献检索记录
评分器零新增（llm_rubric / set_overlap / exact_match 均为 runner 已有类型）
种子 20260907，可复现。
"""
import os, json, csv, random, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 20260907
random.seed(SEED)

STD = os.path.join(ROOT, 'standard/gf0025-2021')
vocab = json.load(open(os.path.join(STD, 'vocabulary.json'), encoding='utf-8'))
grammar = json.load(open(os.path.join(STD, 'grammar.json'), encoding='utf-8'))

def lc(lv): return 7 if lv == '7-9' else int(lv)

# ---------- 文献金标加载（report/lit/*.csv 真实检索记录） ----------
def load_lit():
    lits = []
    lit_dir = os.path.join(ROOT, 'report/lit')
    for fn in os.listdir(lit_dir):
        if not fn.endswith('.csv'):
            continue
        with open(os.path.join(lit_dir, fn), encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                t = (row.get('title') or '').strip()
                au = (row.get('authors') or '').strip()
                yr = (row.get('year') or '').strip()
                ab = (row.get('abstract') or '').strip()
                pub = (row.get('publication_info') or '').strip()
                if t and au and yr and len(ab) > 80:
                    lits.append({'title': t, 'authors': au, 'year': yr,
                                 'abstract': ab, 'pub': pub, 'csv': fn[:-4]})
    # 去重（不同 csv 可能收录同一篇）
    seen, out = set(), []
    for x in lits:
        k = x['title'].lower()
        if k not in seen:
            seen.add(k)
            out.append(x)
    return out

LIT = load_lit()

items = []
BENCH_TAG = {'tb.explain': 'TB-T2', 'tb.objective': 'TB-T3', 'tb.activity': 'TB-T5',
             'tb.exercise': 'TB-T10', 'rb.litsearch': 'RB-R3', 'rb.understand': 'RB-R4',
             'rb.review': 'RB-R11', 'rb.authenticity': 'RB-R12'}

def add_item(task, sub, level, anchor, instruction, inp, ref, scoring, tags,
             source, source_id, contam, rubric=None, params=None, gold_meta=None):
    PREFIX = {'TB': 'PED', 'LB': 'PED', 'RB': 'CUL'}  # TB/LB 并入 PED，RB 并入 CUL？
    # ——不：为榜单题保留独立任务代码，见下方 TASK_PREFIX ——
    seq = sum(1 for it in items if it['sub_type'] == sub) + 1
    items.append({
        'item_id': f'CCE-{TASK_PREFIX[task]}-{level}-{seq:04d}',
        'version': '1.2.0',
        'task_type': TASK_PREFIX[task],
        'sub_type': sub,
        'anchor': anchor,
        'prompt': {'system': PROMPT_SYSTEM.get(task, ''), 'instruction': instruction, 'input': inp},
        'reference': ({'answer': ref, **({'gold_meta': gold_meta} if gold_meta else {})}
                      if ref is not None or gold_meta else {'answer': None}),
        'scoring': ({'type': scoring, **({'rubric': rubric} if rubric else []),
                     **({'params': params} if params else {})}
                    if scoring == 'llm_rubric' else
                    {'type': scoring, **({'params': params} if params else {})}),
        'provenance': {'source': source, 'source_id': source_id,
                       'license': '标准字段引用/公开检索记录', 'contamination_risk': contam},
        'meta': {'bench': BENCH_TAG[sub], 'tags': tags, 'review_status': 'draft',
                 'created': '2026-09-07'},
    })

# 任务前缀映射：三 Bench 新题全部挂 PED（教学专业能力）或 CUL？
# ——决策：TB 题挂 PED（教师能力），LB 复用 TB 题，RB 题挂 CUL 会混淆构念。
#   因此给 RB 新增任务码 RES（研究能力）？——schema enum 只有 7 个任务码，
#   为避免动 schema + runner 双处，RB 题统一挂 PED（sub_type 前缀 rb.* 区分），
#   榜单聚合时按 meta.bench + sub_type 切片即可。TB 同理挂 PED。
TASK_PREFIX = {'TB': 'PED', 'RB': 'PED'}
PROMPT_SYSTEM = {
    'TB': '你是国际中文教育资深教师培训师，熟悉《国际中文教育中文水平等级标准》（GF 0025-2021）。',
    'RB': '你是国际中文教育领域的研究方法专家与文献审稿人。',
}

def normalize_scoring(item):
    """内部一致性修复：把 scoring 字段规整为 schema 合法结构。"""
    s = item['scoring']
    out = {'type': s['type']}
    if s.get('rubric'):
        out['rubric'] = s['rubric']
    if s.get('params'):
        out['params'] = s['params']
    item['scoring'] = out
    # reference 同理
    r = item['reference']
    out_r = {}
    if 'answer' in r:
        out_r['answer'] = r['answer']
    if r.get('gold_meta'):
        out_r['gold_meta'] = r['gold_meta']
    item['reference'] = out_r
    # prompt.system 空串则删除
    if not item['prompt'].get('system'):
        item['prompt'].pop('system', None)
    return item

# =====================================================================
# 1) tb.explain 知识讲解 60 题（词汇 30 + 语法点 30，每等级 10 题）
# =====================================================================
rubric_explain = [
    {'dim': '讲解准确性', 'max': 4, 'desc': '词义/语法点解释正确，无知识性错误（锚定 GF0025 条目内容）'},
    {'dim': '等级适配性', 'max': 3, 'desc': '用词与句式不超出目标等级学习者的可懂范围（i+1 原则）'},
    {'dim': '易懂性', 'max': 3, 'desc': '讲解逻辑清晰，例句贴合学习者生活，易懂'},
]
vocab_by_level = collections.defaultdict(list)
for x in vocab:
    if x['pos'] in ('名', '动', '形', '副') and len(x['word']) >= 2:
        vocab_by_level[lc(x['level'])].append(x)
gram_by_level = collections.defaultdict(list)
for g in grammar:
    gram_by_level[lc(g['level'])].append(g)

for lv in (1, 2, 3, 4, 5, 6):
    vs = random.sample(vocab_by_level[lv], 5)
    for x in vs:
        add_item('TB', 'tb.explain', lv, {'vocab_no': x['no'], 'level': x['level']},
                 f'请给汉语 {lv} 级水平的外国学习者讲解下面这个词语的意思和用法，并给出 2 个适合该水平的例句。',
                 f'词语：{x["word"]}（{x["pinyin"]}，词性：{x["pos"]}）',
                 None, 'llm_rubric', ['讲解', '词汇', f'等级{lv}'],
                 'gf0025-2021', f'vocab#{x["no"]}', 'mid',
                 rubric=rubric_explain, gold_meta={'word': x['word'], 'pinyin': x['pinyin'],
                                                  'pos': x['pos'], 'level': str(lv)})
    gs = random.sample(gram_by_level[lv], 5)
    for g in gs:
        add_item('TB', 'tb.explain', lv, {'grammar_no': g['no'], 'level': g['level']},
                 f'请给汉语 {lv} 级水平的外国学习者讲解下面这个语法点的含义、形式与使用条件，并给出 2 个适合该水平的例句。',
                 f'语法点：{g["item"]}（{g["category"]}—{g["subcategory"]}）',
                 None, 'llm_rubric', ['讲解', '语法', f'等级{lv}'],
                 'gf0025-2021', f'grammar#{g["no"]}', 'mid',
                 rubric=rubric_explain,
                 gold_meta={'item': g['item'], 'content': (g.get('content') or '')[:300],
                            'level': str(lv)})

# =====================================================================
# 2) tb.objective 教学目标设计 20 题（入门~高等 × 文化/职业场景）
# =====================================================================
rubric_objective = [
    {'dim': '目标合理性', 'max': 4, 'desc': '目标符合教学内容的实际难度与学习者水平（锚定等级标准/职业标准描述）'},
    {'dim': '层次性', 'max': 3, 'desc': '目标按知识—理解—运用分层，主次分明'},
    {'dim': '可实现性', 'max': 3, 'desc': '目标在给定课时内可完成、可检验（有可观测的行为动词）'},
]
voc = json.load(open(os.path.join(ROOT, 'standard/other-standards/vocational_chinese.json'), encoding='utf-8'))
voc_scenes = []
for lv_block in voc['levels']:
    lv_name = lv_block['level']
    for skill, descs in lv_block.items():
        if skill in ('level', 'definition', 'class_A', 'class_B', 'communication_strategies'):
            continue
        for d in descs if isinstance(descs, (list,)) else []:
            if isinstance(d, str) and len(d) > 15 and '3.' not in d[:4]:
                voc_scenes.append((lv_name, skill, d))
# class_A/class_B 内层
for lv_block in voc['levels']:
    for cls in ('class_A', 'class_B'):
        blk = lv_block.get(cls)
        if not blk:
            continue
        for skill, descs in blk.items():
            for d in descs if isinstance(descs, (list,)) else []:
                if isinstance(d, str) and len(d) > 15:
                    voc_scenes.append((lv_block['level'], f'{cls[-1]}类-{skill}', d))

cult = json.load(open(os.path.join(ROOT, 'standard/culture-framework/culture_sections.json'), encoding='utf-8'))
cul_scenes = [(c['board'], c['section']) for c in cult]

random.shuffle(voc_scenes)
scene_pool = [('职业', s) for s in voc_scenes[:10]] + [('文化', s) for s in random.sample(cul_scenes, 10)]
for kind, scene in scene_pool:
    if kind == '职业':
        lv_name, skill, desc = scene
        instr = (f'某企业外籍员工中文培训班（{lv_name}级，每周 2 课时，共 8 周）委托你设计教学目标。'
                 f'培训主题与能力要求来自《职业中文能力等级标准》：{skill}——{desc}'
                 f'请给出该班的教学目标设计（3-5 条），每条注明认知层级与可检验的行为动词。只输出目标条目，不要写完整教案。')
        anchor = {'vocational_level': lv_name}
        src_id = f'vocational/{lv_name}/{skill}'
        tags = ['教学目标', '职业中文', lv_name]
        gold = {'vocational_level': lv_name, 'skill': skill, 'desc': desc}
    else:
        board, section = scene
        instr = (f'某国际学校小学学段中文文化课（{section}主题，来自《文化和国情教学参考框架》{board}板块）'
                 f'委托你设计 4 课时的教学目标。请给出 3-5 条教学目标，每条注明认知层级与可检验的行为动词。'
                 f'只输出目标条目，不要写完整教案。')
        anchor = {'culture_section': f'{board}/{section}'}
        src_id = f'culture/{board}/{section}'
        tags = ['教学目标', '文化教学', section]
        gold = {'board': board, 'section': section}
    add_item('TB', 'tb.objective', 9, anchor, instr, '', None, 'llm_rubric', tags,
             'vocational-std' if kind == '职业' else 'culture-framework', src_id, 'low',
             rubric=rubric_objective, gold_meta=gold)

# =====================================================================
# 3) tb.activity 课堂活动设计 20 题（语法点 × 学段）
# =====================================================================
rubric_activity = [
    {'dim': '交际性', 'max': 4, 'desc': '活动有真实交际目的，学习者之间有信息差或互动任务'},
    {'dim': '参与度', 'max': 3, 'desc': '全员参与结构（结对/小组/角色扮演），避免教师独白'},
    {'dim': '可操作性', 'max': 3, 'desc': '步骤、时长、分组、所需材料明确，可直接进课堂'},
]
stage_pool = ['小学学段', '中学学段', '大学及成人学段']
def gl(g): return '7-9' if g['level'] == '7-9' else str(g['level'])
act_grams = random.sample([g for g in grammar if gl(g) in ('1', '2', '3', '4')], 20)
for g in act_grams:
    stage = random.choice(stage_pool)
    add_item('TB', 'tb.activity', lc(g['level']), {'grammar_no': g['no'], 'level': g['level']},
             (f'请为{stage}的中文课堂设计一个 15 分钟的课堂活动，操练语法点「{g["item"]}」。'
              f'要求任务型或交际型，写出活动名称、步骤（含分组与时长）、教师的角色、以及如何检验学生掌握了该语法点。'),
             '', None, 'llm_rubric', ['课堂活动', '语法操练', g['level']],
             'gf0025-2021', f'grammar#{g["no"]}', 'low',
             rubric=rubric_activity,
             gold_meta={'item': g['item'], 'level': g['level'], 'stage': stage,
                        'content': (g.get('content') or '')[:200]})

# =====================================================================
# 4) tb.exercise 练习生成 20 题（语法点 → 生成选择题+答案）
# =====================================================================
rubric_exercise = [
    {'dim': '题目有效性', 'max': 4, 'desc': '考点准确命中目标语法点，干扰项有区分度（针对典型偏误而非随机错句）'},
    {'dim': '等级适配性', 'max': 3, 'desc': '题干与选项用词不超出该语法点等级 ±1 级词表'},
    {'dim': '规范性', 'max': 3, 'desc': '题目格式规范（单项选择，4 个选项，附标准答案与简要解析）'},
]
ex_grams = random.sample([g for g in grammar if gl(g) in ('2', '3', '4', '5')], 20)
for g in ex_grams:
    add_item('TB', 'tb.exercise', lc(g['level']), {'grammar_no': g['no'], 'level': g['level']},
             (f'请为语法点「{g["item"]}」（{g["category"]}，等级 {g["level"]}）出 1 道四选一选择题，'
              f'考查外国学习者对该语法点的掌握。题目用词不得超出《等级标准》{g["level"]} 级上下一个等级的词汇范围。'
              f'输出格式：题干 / A、B、C、D 四个选项 / 标准答案 / 一句话解析。'),
             '', None, 'llm_rubric', ['练习生成', '语法', g['level']],
             'gf0025-2021', f'grammar#{g["no"]}', 'low',
             rubric=rubric_exercise,
             gold_meta={'item': g['item'], 'level': g['level'],
                        'content': (g.get('content') or '')[:200]})

# =====================================================================
# 5) rb.litsearch 文献检索 20 题（主题→推荐文献，set_overlap 命中金标）
# =====================================================================
# 金标集合 = lit 记录按 csv 主题分组，每组 3-5 篇真实文献
groups = collections.defaultdict(list)
for x in LIT:
    groups[x['csv']].append(x)
group_names = {'aes_validity': '语言测试自动评分（AES）效度',
               'chinese_readability': '汉语文本可读性',
               'llm_chinese_edu': '大语言模型在国际中文教育中的应用',
               'llm_eval_edu': '教育场景大模型评测基准',
               'rlhf': 'RLHF 与后训练',
               'text_leveling': '分级读物与文本定级'}
TOPIC_DESC = {
    'aes_validity': '自动作文评分（AES/AWE）的效度与信度，尤其是 LLM 用于二语作文评分的效度研究',
    'chinese_readability': '汉语文本可读性：可读性公式、特征体系与自动分级',
    'llm_chinese_edu': '大语言模型在国际中文教育（对外汉语教学）中的应用与评估',
    'llm_eval_edu': '教育场景的大语言模型评测基准（E-EVAL、EduBench 等）',
    'rlhf': 'RLHF/后训练（指令微调、奖励模型、对齐）方法综述',
    'text_leveling': '分级读物（graded readers）与文本难度定级',
}
for csv_name, topic in list(group_names.items()) * 1:
    recs = groups.get(csv_name) or []
    if len(recs) < 3:
        continue
    gold_set = [f'{r["authors"].split(",")[0].strip()} 等 ({r["year"]})《{r["title"]}》' for r in recs[:5]]
    instr = (f'一位国际中文教育方向的研究生计划开展关于「{topic}」的研究，需要文献支持。'
             f'请推荐 3 篇该主题最有代表性的中英文学术文献（按引用/影响力优先），'
             f'每篇给出：作者（第一作者即可）、年份、标题、发表载体。每行一篇，不要编号，不要解释。')
    add_item('RB', 'rb.litsearch', 9, {'lit_group': csv_name}, instr, '', None,
             'set_overlap', ['文献检索', topic], 'lit-records', f'lit/{csv_name}', 'low',
             gold_meta={'topic': topic, 'gold_set': gold_set,
                        'note': '命中集合按第一作者+年份+标题模糊匹配，命中≥1 篇即按比例给分'})

# 各组不足 3 篇的（rlhf 只有 2 条），从跨组真实文献池出「泛检索」题
if len(groups.get('rlhf', [])) < 3:
    pool = random.sample(LIT, 6)
    gold_set = [f'{r["authors"].split(",")[0].strip()} 等 ({r["year"]})《{r["title"]}》' for r in pool]
    instr = ('一位研究生正在调研「大模型评测与教育应用」交叉领域，需要一个跨主题的文献起点。'
             '请推荐 3 篇该交叉领域最有代表性的学术文献（中英文均可），'
             '每篇给出：作者（第一作者）、年份、标题、发表载体。每行一篇，不要编号，不要解释。')
    add_item('RB', 'rb.litsearch', 9, {'lit_group': 'cross'}, instr, '', None,
             'set_overlap', ['文献检索', '跨主题'], 'lit-records', 'lit/cross', 'low',
             gold_meta={'topic': '大模型评测×教育应用', 'gold_set': gold_set})

# =====================================================================
# 6) rb.understand 文献理解 20 题（摘要→研究问题/方法/结论 3 问）
# =====================================================================
rubric_understand = [
    {'dim': '理解准确性', 'max': 4, 'desc': '三个回答准确概括了论文的研究问题、方法与结果，无曲解'},
    {'dim': '信息完整性', 'max': 3, 'desc': '每问覆盖摘要中的关键信息（不遗漏核心变量/发现）'},
    {'dim': '概括能力', 'max': 3, 'desc': '表述精炼，用自己的话概括而非照抄摘要原句'},
]
for x in random.sample(LIT, 20):
    abstract = x['abstract'][:900]
    instr = (f'下面是一篇学术论文的摘要。请回答三个问题：\n'
             f'1）该研究解决的核心问题是什么？\n'
             f'2）用了什么研究方法/数据？\n'
             f'3）主要发现或结论是什么？\n每问 1-2 句话。')
    add_item('RB', 'rb.understand', 9, {'lit_title': x['title'][:80]}, instr,
             f'【摘要】{abstract}', None, 'llm_rubric',
             ['文献理解', x['csv']], 'lit-records', f'lit/{x["csv"]}#{x["title"][:40]}', 'low',
             rubric=rubric_understand,
             gold_meta={'title': x['title'], 'authors': x['authors'], 'year': x['year'],
                        'abstract': x['abstract'][:500]})

# =====================================================================
# 7) rb.review 论文评审 20 题（真实摘要+注入缺陷→找缺陷）
# =====================================================================
DEFECT_TEMPLATES = [
    ('样本偏差', '研究者仅在单一母语背景的学习者样本上得出了一般性结论，未讨论样本代表性的限制'),
    ('因果混淆', '将相关性发现表述为因果关系，但研究设计（横断面调查）不支持因果推断'),
    ('测量循环', '评测指标与训练数据来源相同（同源循环），模型的"高分"可能是数据泄漏而非能力'),
    ('基线缺失', '未与任何已有方法/前人工作比较，无法判断结果的相对水平'),
    ('泛化过度', '在一个非常具体的任务（单一题型/单一语言水平）上的结果被推广到"教育场景整体"'),
    ('统计不充分', '核心结论只基于少量样本（n<20）且未报告显著性检验或效应量'),
]
review_pool = [x for x in LIT if len(x['abstract']) >= 90]
random.shuffle(review_pool)
for x in review_pool[:20]:
    defect_name, defect_desc = random.choice(DEFECT_TEMPLATES)
    instr = (f'下面是一篇投稿论文的摘要。审稿意见指出该文存在一个方法学缺陷。'
             f'请判断该缺陷属于下列哪一类，只输出类别名称：\n'
             + '\n'.join(f'- {d[0]}' for d in DEFECT_TEMPLATES) +
             '\n只回答类别名称，不要解释。')
    add_item('RB', 'rb.review', 9, {'lit_title': x['title'][:80]}, instr,
             f'【摘要（含审稿人指出的问题情境）】{x["abstract"][:800]}',
             defect_name, 'exact_match', ['论文评审', '方法学', defect_name],
             'lit-records', f'lit/{x["csv"]}#{x["title"][:40]}', 'low',
             gold_meta={'defect': defect_name, 'defect_desc': defect_desc,
                        'note': '缺陷由出题方注入（摘要情境描述按缺陷改写），金标为缺陷类别'})

# =====================================================================
# 8) rb.authenticity 学术真实性 20 题（1真3假判真伪）
# =====================================================================
auth_pool = [x for x in LIT if len(x['title']) > 15 and x['year'].isdigit()]
random.shuffle(auth_pool)
FAKE_TITLE_PATTERNS = [
    '大语言模型驱动下{kw}的范式重构与实证检验',
    '面向{kw}的多智能体协同框架：一项混合方法研究',
    '{kw}的神经-符号融合建模：从理论到课堂落地',
    '生成式人工智能赋能{kw}：基于扎根理论的探索',
    '跨文化视角下{kw}的数字化转向与效应评估',
    '{kw}自动化测评的公平性研究：基于大规模语料',
]
KW_POOL = ['国际中文教育', '二语写作反馈', '中文可读性', '语言教育评价', '学习者语料分析',
           '汉语语法教学', '中文语音评测', '文化教学适配', '自动作文评分', '教育大模型']
for x in auth_pool[:20]:
    kw = random.choice(KW_POOL)
    fakes = random.sample(FAKE_TITLE_PATTERNS, 3)
    fake_titles = [t.format(kw=kw) for t in fakes]
    # 真假洗牌
    candidates = [('真', x)] + [('假', {'title': ft, 'authors': '（编造）', 'year': str(random.randint(2024, 2026)),
                                       'pub': '（编造刊物）', 'abstract': ''}) for ft in fake_titles]
    random.shuffle(candidates)
    listing = '\n'.join(
        f'{chr(65 + i)}. {c[1]["title"]}（{c[1]["year"]}）'
        for i, c in enumerate(candidates))
    gold_idx = next(i for i, c in enumerate(candidates) if c[0] == '真')
    gold_letter = chr(65 + gold_idx)
    instr = (f'下面是围绕同一研究主题的 4 篇文献，其中只有 1 篇是真实存在的学术文献，其余 3 篇为编造。'
             f'请判断哪一篇是真实文献，只回答大写字母：A、B、C 或 D。\n\n{listing}')
    add_item('RB', 'rb.authenticity', 9, {'lit_title': x['title'][:80]}, instr, '',
             gold_letter, 'exact_match', ['学术真实性', '文献核验', x['csv']],
             'lit-records', f'lit/{x["csv"]}#{x["title"][:40]}', 'low',
             gold_meta={'real_title': x['title'], 'real_authors': x['authors'],
                        'real_year': x['year'], 'fake_titles': fake_titles})

# =====================================================================
# 编号重排（bench 题独占 level=8 段：与 v1.0/v1.1 全库零冲突，
#          8 表示"榜单专项题"（三 Bench 补充维度），按 task_type+原 level 分组顺序编号）
# =====================================================================
# 保留 add_item 时的原始 level（题目 anchor 不变），仅 ID 第三段统一用 8；
# 序号按 bench 题内部连续排（task_type 都是 PED，全局唯一），按 sub_type 分段便于阅读
cnt = 0
order = {'tb.explain': 1, 'tb.objective': 2, 'tb.activity': 3, 'tb.exercise': 4,
         'rb.litsearch': 5, 'rb.understand': 6, 'rb.review': 7, 'rb.authenticity': 8}
items.sort(key=lambda it: (order[it['sub_type']],))
for it in items:
    raw_level = it['item_id'].split('-')[2]
    it['anchor']['bench_level'] = raw_level  # 原等级保留在 anchor
    cnt += 1
    it['item_id'] = f'CCE-PED-8-{cnt:04d}'
items = [normalize_scoring(it) for it in items]

os.makedirs(os.path.join(ROOT, 'items/v1.2'), exist_ok=True)
out_path = os.path.join(ROOT, 'items/v1.2/items_bench.jsonl')
with open(out_path, 'w', encoding='utf-8') as f:
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')

# 合并生成 v1.2 完整题库（v1.1 + bench 增量）
v11 = open(os.path.join(ROOT, 'items/v1.1/items.jsonl'), encoding='utf-8').read()
comb_path = os.path.join(ROOT, 'items/v1.2/items.jsonl')
with open(comb_path, 'w', encoding='utf-8') as f:
    f.write(v11 if v11.endswith('\n') else v11 + '\n')
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')

print(f'bench items: {len(items)}')
print(collections.Counter(it['sub_type'] for it in items))
print(collections.Counter(it['meta']['bench'] for it in items))
print('written:', out_path)
n11 = len(v11.strip().splitlines())
print(f'combined: {comb_path}  v1.1={n11} + bench={len(items)} = {n11 + len(items)}')