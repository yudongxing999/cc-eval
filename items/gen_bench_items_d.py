# -*- coding: utf-8 -*-
"""生成 ResearchBench 八维专家量表题目（v1.2d 批次）

覆盖此前仅缺专家量表的 8 个维度（R1/R2/R5/R6/R7/R8/R9/R10）：
  rb.topic    研究选题（10 题）——真实领域现象 → 提出 2 个可研究问题
  rb.question 研究问题设计（10 题）——模糊研究兴趣 → 转化为可检验问题
  rb.review_lit 文献综述（10 题）——4 篇真实文献 odd-one-out（可机判定位 + 评委说理）
  rb.design   研究设计（10 题）——研究问题+数据条件 → 设计研究方案
  rb.analysis 数据分析（10 题）——真实数据场景 → 选择统计方法并解释
  rb.corpus   语料与计算分析（10 题）——真实语料研究问题 → 设计处理分析流程
  rb.academic_writing 学术写作（10 题）——研究要点 → 写方法段/讨论段
  rb.interpret 结果解释（10 题）——真实研究结果 → 解释含义与边界

量表：全部八维使用 schema/rb_rubrics.json（RB-Rubric-1.0，
于东兴个人设计，迁移自其《学术论文写作》课程评价体系）。

题面素材（全部本地真实数据）：
  - CC-Eval 自身 v1.0 评测发现（真实研究现象/结果，report/ 与 results/）
  - HSK 语料画像统计（rb.corpus 的真实研究问题素材）
  - report/lit/ 41 条真实文献（rb.review_lit 的 odd-one-out）
种子 20260908，可复现。
"""
import os, json, random, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 20260908
random.seed(SEED)

RUBRICS = json.load(open(os.path.join(ROOT, 'schema/rb_rubrics.json'), encoding='utf-8'))['rubrics']

def rubric_of(sub):
    r = RUBRICS[sub]
    return [{'dim': d['dim'], 'max': d['max'],
             'desc': f"{d['excellent']}｜中档：{d['pass']}｜低档：{d['poor']}"}
            for d in r['dims']]

items = []

def add_item(sub, instruction, inp, tags, source, source_id, contam,
             gold_meta=None, ref=None, anchor=None, scoring='llm_rubric'):
    seq = sum(1 for it in items if it['sub_type'] == sub) + 1
    it = {
        'item_id': f'CCE-PED-8-{seq:04d}',  # 占位，最后接续编号
        'version': '1.2.0',
        'task_type': 'PED',
        'sub_type': sub,
        'anchor': anchor or {'rubric_ref': f'schema/rb_rubrics.json#{sub}'},
        'prompt': {'system': '你是国际中文教育领域的研究方法专家与学术写作导师。',
                   'instruction': instruction, 'input': inp},
        'reference': {},
        'scoring': {'type': scoring},
        'provenance': {'source': source, 'source_id': source_id,
                       'license': '标准字段引用/公开官方资料',
                       'contamination_risk': contam},
        'meta': {'bench': RUBRICS[sub]['bench'], 'tags': tags,
                 'review_status': 'draft', 'created': '2026-09-08',
                 'rubric_designer': '于东兴', 'rubric_version': 'RB-Rubric-1.0'},
    }
    if ref is not None or gold_meta:
        it['reference']['answer'] = ref
    if gold_meta:
        it['reference']['gold_meta'] = gold_meta
    if scoring == 'llm_rubric':
        it['scoring']['rubric'] = rubric_of(sub)
    items.append(it)

# ---------- 素材：CC-Eval 真实评测发现（rb.topic / rb.interpret / rb.question 素材） ----------
PHENOMENA = [
    ('作文评分偏差', '2026 年一项针对 11 个大模型的评测发现：部分旗舰档模型（豆包 seed-1-6、混元 hy3）在给外国学习者 HSK 作文评分时，容差得分只有 44-49 分（满分 100），明显低于轻量档模型（ernie 76.8、deepseek-chat 75.8）；但其预测分与人工分的 Spearman 相关却达 0.60-0.68（全场次高）。分析显示其预测均值比人工均值系统性低 16-18 分。'),
    ('等级知识缺失', '一项评测显示，11 个主流大模型判断《等级标准》词语等级的准确率仅 12%-35%，且错误呈方向性：语气词「啦」（实际六级）11 个模型全部判为一至四级；新一代模型 deepseek-v4-flash 生成能力明显强于上一代（50.8 vs 36.6），但等级知识反而下降（22.5 vs 35.2）。'),
    ('限级改写失守', '评测发现，让大模型把一段文字改写为 HSK 一级学习者可懂的文本时，11 个模型通过率最高仅 15%：产出文本人眼看「像」一级（句子短、语义保留），但对照词表检查，「音乐」（二级）、「自己」（二级）、「里面」（三级）等词全部超纲；平均超限词率最高达 22.55%。'),
    ('文化高分现象', '一项多模型评测中，文化国情问答是全维度最高分（70.5-94.9），各模型差距小；但同一批模型在标准条文定位任务上最高仅 8.9%（11 个中 5 个为 0%）。场景化教学设计题（评委评分）各模型均在 98-100%。'),
    ('听力占位回答', '对三个开源小模型（0.5B/0.5B-Instruct/1.5B-Instruct）的 loglikelihood 评测发现：音节合法性判断（二选一）三模型全部 50%（等于随机），逐样本分析显示模型恒定选同一标签；但多音字定音任务 1.5B 达 80%，高于随机基线 47.8%。'),
]

# ---------- 素材：HSK 语料画像（rb.corpus 的真实研究问题） ----------
import json as _json
hsk_stats = None
try:
    nations = collections.Counter()
    for line in open(os.path.join(ROOT, 'corpus/hsk_corpus.jsonl'), encoding='utf-8'):
        d = _json.loads(line)
        if d.get('nation'):
            nations[d['nation']] += 1
    hsk_stats = nations.most_common(6)
except FileNotFoundError:
    hsk_stats = [('韩国', 4163), ('日本', 3165), ('新加坡', 842), ('印度尼西亚', 738), ('马来西亚', 420)]

# ---------- 素材：lit 文献（rb.review_lit odd-one-out） ----------
import csv
LIT = []
lit_dir = os.path.join(ROOT, 'report/lit')
for fn in os.listdir(lit_dir):
    if not fn.endswith('.csv'):
        continue
    for row in csv.DictReader(open(os.path.join(lit_dir, fn), encoding='utf-8-sig', newline='')):
        t, au, yr, ab = (row.get('title') or '').strip(), (row.get('authors') or '').strip(), \
                        (row.get('year') or '').strip(), (row.get('abstract') or '').strip()
        if t and au and yr and len(ab) > 80:
            LIT.append({'title': t, 'authors': au, 'year': yr, 'abstract': ab, 'csv': fn[:-4]})
_seen = set()
LIT = [x for x in LIT if not (x['title'].lower() in _seen or _seen.add(x['title'].lower()))]

# 按主题组划分方法类别（odd-one-out 的金标依据：跨组抽 3 篇同主题 + 1 篇异主题）
by_group = collections.defaultdict(list)
for x in LIT:
    by_group[x['csv']].append(x)

# =====================================================================
# R1 rb.topic 研究选题 10 题
# =====================================================================
for i, (name, phen) in enumerate(PHENOMENA):
    add_item('rb.topic',
             (f'下面是国际中文教育大模型评测中的一个真实研究现象。请基于该现象提出 2 个值得研究的'
              f'研究问题（选题），并分别说明：1）研究价值（谁需要这个答案）；2）可研究性'
              f'（在现有数据与方法条件下如何检验）；3）与既有文献的关系（填补/扩展/反驳什么）。'
              f'每个问题 3-5 句话。\n\n【现象】{phen}'),
             '', ['研究选题', name], 'cceval-findings', f'finding/{name}', 'mid',
             gold_meta={'phenomenon': phen[:300],
                        'note': '量表 RB-Rubric-1.0 rb.topic；设计者于东兴'})

# 5 个现象 × 2 = 10 个选题位，但每题含 2 问；再补 5 题用课程学生真实选题情境
COURSE_TOPICS = [
    '华裔与非华裔学习者在「不/没」否定结构上的偏误对比（HSK 语料库，98 样本，卡方检验）',
    '汉语二语学习者阅读理解中高低阶认知能力的作用（有声思维干预）',
    '汉语句末语气词「呢」的二语习得：语示分类与不对称习得',
    '中文教材文本可读性特征对母语教材与国际中文教材的区分力（回归分析）',
    '汉语儿缀的南方方音变体：发音生理与声学实验个案研究',
]
for topic in COURSE_TOPICS:
    add_item('rb.topic',
             (f'一位研究生计划研究：「{topic}」。请你以导师身份评估这个选题：1）研究价值'
              f'（谁需要这个答案，说明理由）；2）可研究性（在现有数据/方法条件下能否检验，'
              f'缺什么条件）；3）学术定位（该选题与既有文献的关系：填补/扩展/反驳什么）。'
              f'共 4-6 句话。'),
             '', ['研究选题', '真实选题'], 'course-topics', f'topic/{topic[:20]}', 'low',
             gold_meta={'topic': topic,
                        'note': '量表 RB-Rubric-1.0 rb.topic；选题情境来自真实课堂选题（已匿名化）'})

# =====================================================================
# R2 rb.question 研究问题设计 10 题
# =====================================================================
VAGUE = [
    ('作文评分偏差', '我想研究一下大模型给学生作文打分准不准。'),
    ('等级知识', '我想看看大模型知不知道中文词汇的难度等级。'),
    ('限级改写', '我想研究 AI 能不能帮老师把课文改简单点。'),
    ('文化教学', '我想研究大模型能不能用来教中国文化。'),
    ('偏误诊断', '我想研究 AI 能不能发现学生作文里的语法错误。'),
    ('听力理解', '我想研究语音识别对汉语学习者听力的帮助。'),
    ('阅读分级', '我想研究怎么自动判断一篇文章适不适合某个水平的学生。'),
    ('口语评分', '我想研究 AI 给口语考试打分靠不靠谱。'),
    ('词典释义', '我想研究大模型给中文词汇下的定义适不适合外国学生。'),
    ('教材评价', '我想研究能不能用 AI 按标准自动审查中文教材。'),
]
for name, vague in VAGUE:
    add_item('rb.question',
             (f'一位研究生的原始兴趣陈述如下：「{vague}」\n'
              f'请把这个模糊兴趣转化为 2 个明确的可检验研究问题。每个问题须包含：'
              f'1）用可观察变量表述的问题本身；2）可检验的假设（含预期方向）；'
              f'3）判据（什么结果算支持/不支持假设）。'),
             '', ['研究问题设计', name], 'synthetic', f'vague/{name}', 'low',
             gold_meta={'vague_interest': vague,
                        'note': '量表 RB-Rubric-1.0 rb.question；设计者于东兴'})

# =====================================================================
# R5 rb.review_lit 文献综述 10 题（odd-one-out：3 同主题 + 1 异主题）
# =====================================================================
groups = [k for k, v in by_group.items() if len(v) >= 3]
for i in range(10):
    main_g = groups[i % len(groups)]
    other_g = groups[(i + 1) % len(groups)] if len(groups) > 1 else None
    if not other_g:
        break
    main_papers = random.sample(by_group[main_g], min(3, len(by_group[main_g])))
    odd_paper = random.choice(by_group[other_g])
    papers = main_papers + [odd_paper]
    random.shuffle(papers)
    odd_letter = chr(65 + papers.index(odd_paper))
    listing = '\n\n'.join(
        f'{chr(65+j)}. 《{p["title"]}》（{p["year"]}）\n摘要要点：{p["abstract"][:150]}'
        for j, p in enumerate(papers))
    add_item('rb.review_lit',
             (f'下面是 4 篇文献的摘要。其中 3 篇在研究主题/方法上同类，1 篇不同类。'
              f'请：1）指出哪一篇是不同类的（只答字母）；2）用 3-4 句话综合概括其余 3 篇'
              f'的共识与分歧，并指出该主题下尚存的研究空白。\n\n{listing}'),
             '', ['文献综述', 'odd-one-out', main_g], 'lit-records',
             f'lit/{main_g}+{other_g}', 'low',
             ref=odd_letter, gold_meta={'odd': odd_paper['title'], 'main_group': main_g,
                                        'odd_group': other_g,
                                        'note': 'odd-one-out 定位可机判（首行字母）；综合与空白部分走评委量表'},
             scoring='llm_rubric')

# =====================================================================
# R6 rb.design 研究设计 10 题
# =====================================================================
DESIGN_TASKS = [
    ('作文评分偏差', '研究问题：旗舰模型作文评分的系统性压分能否用一个线性校准修正？',
     '可用资源：某模型对 250 篇 HSK 作文的预测分 + 语料库人工分（训练/测试需分开）；无新增标注预算。'),
    ('等级知识', '研究问题：检索增强（外挂词表检索）能把大模型的词语定级准确率从 22% 提升到多少？',
     '可用资源：GF0025 词汇表（11092 词，带等级）；400 道定级题；一个可调用的通用大模型 API；无 GPU。'),
    ('限级改写', '研究问题：解码时施加词表硬约束（constrained decoding）能否把限级改写通过率从 15% 提到 60%+？',
     '可用资源：开源 7B 指令模型与本地推理环境；GF0025 词表与 FMM 校验器；120 道限级改写题。'),
    ('偏误诊断', '研究问题：按母语背景（韩/日）分组的偏误类型分布是否有显著差异？',
     '可用资源：HSK 动态作文语料库（11328 篇，含国籍与偏误标注）；无实验被试预算。'),
    ('听力理解', '研究问题：学习者朗读音频经 ASR 转写后，大模型能否诊断出与目标文本的声调偏差位置？',
     '可用资源：30 段已人工标注偏差位置的朗读音频；一个支持音频输入的商业 API；一个仅支持文本的开源模型作对照。'),
    ('阅读分级', '研究问题：词表覆盖率（FMM 词级统计）对国际中文教材难度的预测力有多强？',
     '可用资源：40 册教材全文电子版（含出版方标注的适用等级）；GF0025 词表；已标注的人工难度评级。'),
    ('口语评分', '研究问题：LLM 评委与 3 名人类教师对口语考试录音评分的一致性（QWK）是否达到可接受水平？',
     '可用资源：60 段口语考试录音与人类评分；一个音频输入 API；评分量表（PSC 简化版）。'),
    ('文化教学', '研究问题：大模型生成的文化讲解中刻板印象出现率有多高，提示词工程能否降低？',
     '可用资源：文化框架 32 板块内容；3 个大模型 API；2 名专家评审（每人可评 100 条）。'),
    ('词典释义', '研究问题：大模型词汇释义的用词等级是否超出目标学习者水平？',
     '可用资源：GF0025 词表与 FMM 等级校验器；从 3 个大模型采集的 200 条释义。'),
    ('教材评价', '研究问题：大模型能否按《国际中文教材评价标准》的 85 条指标自动审查教材文本？',
     '可用资源：教材评价标准结构化数据（85 条三级指标）；10 册教材文本；人类专家审查结果作金标。'),
]
for name, rq, res in DESIGN_TASKS:
    add_item('rb.design',
             (f'{rq}\n\n【可用资源】{res}\n\n请设计一个研究方案，须覆盖：1）设计类型与理由；'
              f'2）被试/样本与来源；3）材料与工具；4）流程步骤；5）分析方法与判据；'
              f'6）伦理与质量控制。分条作答，共 6-10 句。'),
             '', ['研究设计', name], 'synthetic', f'design/{name}', 'low',
             gold_meta={'rq': rq, 'resources': res,
                        'note': '量表 RB-Rubric-1.0 rb.design；设计任务基于 CC-Eval 评测发现构造'})

# =====================================================================
# R7 rb.analysis 数据分析 10 题
# =====================================================================
ANALYSIS_TASKS = [
    ('卡方', '你研究韩/日学习者「不/没」偏误类型分布差异（各 50 人），偏误类型 4 类。问：用什么统计方法？前提假设如何检验？结果怎么解读？'),
    ('t 检验', '你比较两个大模型在同一 250 篇作文上的评分与人工分之差的均值（同一批作文，两个模型配对）。问：配对还是独立样本？如何报告？'),
    ('QWK', '你让 LLM 评委和 3 名人类教师给 60 段口语录音打分（1-5 分），需要报告一致性。问：为什么不用简单百分比一致？QWK 怎么算、怎么解读？'),
    ('相关', '你计算模型预测分与人工分的 Spearman ρ=0.60（n=250）。问：这能说明什么、不能说明什么？需要补充什么分析？'),
    ('回归', '你想检验词表覆盖率、句长、语法点密度对教材难度（1-6 级）的预测力。问：用什么回归？如何处理等级因变量？'),
    ('效应量', '你的实验组通过率 62%、对照组 45%（各 60 人），χ²=4.02, p=0.045。问：还缺什么必须报告的量？如何解读实际意义？'),
    ('多重比较', '你在 11 个模型上两两比较 KNO 准确率（45 次比较），其中 3 次p<0.05。问：这 3 次比较可信吗？如何校正？'),
    ('抽样', '你从 11328 篇作文中按分数段分层抽样 250 篇。问：为什么要分层？样本量对置信区间宽度的影响如何量化？'),
    ('异常值', '你的作文评分数据中 3 篇的模型预测分比人工分低 60+ 分。问：剔除前应做什么检查？对结论稳健性的影响如何评估？'),
    ('信度', '两名标注员对 100 句偏误类型独立标注，一致率 78%。问：用什么系数、什么水平算可接受？不一致样本怎么处理？'),
]
for name, task in ANALYSIS_TASKS:
    add_item('rb.analysis', task, '', ['数据分析', name], 'synthetic', f'analysis/{name}', 'low',
             gold_meta={'scenario': task[:120],
                        'note': '量表 RB-Rubric-1.0 rb.analysis；场景基于 CC-Eval 评测中的真实统计问题'})

# =====================================================================
# R8 rb.corpus 语料与计算分析 10 题
# =====================================================================
CORPUS_TASKS = [
    ('偏误分布', f'研究问题：HSK 动态作文语料库中韩国（{hsk_stats[0][1]} 篇）与日本（{hsk_stats[1][1]} 篇）学习者的错字（CC）与用词（CJ）偏误占比是否存在国籍差异？请设计语料处理与分析流程，须覆盖：数据抽取与清洗、偏误标注解析（{{CC}}/{{CJ}} 代码）、分组与统计、混淆因素控制、复现保障（脚本与种子）。'),
    ('超限词率', '研究问题：三个大模型限级改写的超限词率（OOV 率）差异是否由分词口径引起？请设计一个控制分词口径的对比分析流程（FMM 词表切分 vs 第三方分词器），并说明如何检验口径敏感性。'),
    ('作文难度', '研究问题：作文文本特征（句长、词汇等级分布、连接词密度）能否预测 HSK 作文人工分数？请设计特征工程与回归分析流程，含特征定义、缺失处理、过拟合控制。'),
    ('音节覆盖', '研究问题：大模型训练语料中 GF0025 音节表的覆盖率如何间接测量？请设计一个用模型行为（音节合法性判断准确率）反推知识覆盖的实验流程。'),
    ('主题聚类', '研究问题：11328 篇作文按题目聚为 30 组后，各组的偏误类型构成是否不同？请设计聚类与构成对比的分析流程，含多重比较处理。'),
    ('词汇增长', '研究问题：GF0025 词表从 1 级到 6 级的词汇增长曲线是否与教材生词表的引入节奏一致？请设计两者对齐分析的流程。'),
    ('标注一致性', '研究问题：HSK 语料库偏误标注中 CC 与 CJX 的边界一致性如何？请设计抽样复核流程（样本量、双人独立标注、Kappa 计算、仲裁规则）。'),
    ('评委漂移', '研究问题：LLM 评委在 198 道主观题上的打分是否存在会话内漂移（前 100 题 vs 后 98 题的均值差异）？请设计检测与控制流程。'),
    ('文本相似度', '研究问题：模型限级改写产出与原文的语义保持度如何量化？请设计一个基于字面重叠与语义嵌入双指标的相似度分析流程，并说明两指标分歧时的处理。'),
    ('文化主题分布', '研究问题：32 个文化板块的概要文本在词汇等级分布上的差异是否影响学习者可读性？请设计 FMM 分级统计与板块间对比的分析流程。'),
]
for name, task in CORPUS_TASKS:
    add_item('rb.corpus', task, '', ['语料分析', name], 'cceval-assets', f'corpus/{name}', 'low',
             gold_meta={'scenario': task[:150],
                        'note': '量表 RB-Rubric-1.0 rb.corpus；任务基于 CC-Eval 真实数据资产构造'})

# =====================================================================
# R9 rb.academic_writing 学术写作 10 题
# =====================================================================
WRITING_TASKS = [
    ('方法段', '研究要点：比较 11 个大模型在国际中文教育 1555 题基准上的表现；六类任务四类确定性评分器；温度默认、单次采样；断点续跑。请写方法段（150-250 字），覆盖：设计、被测模型、题库构成、评分方式、局限。'),
    ('方法段2', '研究要点：对 3 个开源小模型做 loglikelihood 评测（不生成文本，比较候选答案的 log 概率）；0-shot；CPU 推理；与随机基线对照。请写方法段（150-250 字），含复现所需关键信息。'),
    ('讨论段', '结果要点：旗舰档模型作文评分容差得分 44-49 显著低于轻量档 74-77，但 Spearman ρ 反而最高（0.60-0.68），预测均值系统性低 16-18 分。请写讨论段（150-250 字），须含：发现→与文献对话→机制解释→局限与未来工作（讨论四件套）。'),
    ('讨论段2', '结果要点：大模型限级改写通过率最高仅 15%，但超限词率呈连续梯度（1.3%-18.4%）；人眼评估与词表校验结论相反。请写讨论段（150-250 字），四件套齐全。'),
    ('引言段', '背景：通用大模型进入国际中文教育但缺乏客观评价标准。缺口：通用基准无法外推垂直场景。贡献：构建四原则与 1555 题基准，11 模型实证。请按 and–but–therefore 写引言（150-250 字）。'),
    ('摘要', '研究：构建国际中文教育大模型评测基准（六类任务 1555 题，四类确定性评分器），对 11 个模型实测；发现三个背离现象（等级知识缺失/限级生成失守/评分效度倒挂）。请写 200-300 字结构式摘要（背景-方法-结果-意义）。'),
    ('结果段', '数据：KNO 维度 11 模型准确率 12.0%-35.2%，Wilson 95% CI 最宽 ±5 个百分点；McNemar 检验最高与最低差异 p<0.001。请写结果段（150-250 字），按"问题—证据—小结"组织，每段末有小结句。'),
    ('结果段2', '数据：限级改写 120 题，通过率 hy3 15.0% / k3 8.3% / 其余 <6%；OOV 率中位数 hy3 1.32% / glm 18.35%。请写结果段（150-250 字），呈现两条指标的对照证据链。'),
    ('回应审稿', '审稿意见："SCO 评分的 ±10/±20 容差判据可能受恒定打分策略投机；建议报告 QWK。"请写一段回应（80-150 字）：感谢→行动（我们做了什么修改/补充）→定位（改在哪一节），语气专业、逐条回应。'),
    ('局限段', '研究局限：评委单一（同族偏袒风险）、单次采样（±2 分噪声）、轻量档模型（不代表上限）。请写"局限与未来工作"段（150-250 字），每条局限须配一个具体可检验的未来工作。'),
]
for name, task in WRITING_TASKS:
    add_item('rb.academic_writing', task, '', ['学术写作', name], 'cceval-findings',
             f'writing/{name}', 'low',
             gold_meta={'task': task[:100],
                        'note': '量表 RB-Rubric-1.0 rb.academic_writing；任务基于 CC-Eval 论文真实写作情境'})

# =====================================================================
# R10 rb.interpret 研究结果解释 10 题
# =====================================================================
INTERPRET_TASKS = [
    ('评分倒挂', '结果：豆包/混元旗舰档 SCO 容差得分 44-49 低于轻量档 74-77；Spearman ρ 0.60-0.68 为全场次高；预测均值低人工 16-18 分。请解释：1）这两个指标为何背离？2）"档位高=评分好"的直觉为何失效？3）据此给应用方一句可执行建议。'),
    ('KNO 低分', '结果：11 模型 KNO 准确率 12-35%（随机 14.3%），其中 2 个低于随机。请解释：1）低于随机说明什么？2）这一结果的"低分更具诊断力"如何成立？3）对"用大模型做定级决策"给出边界。'),
    ('OOV 梯度', '结果：限级改写通过率趋同地低（≤15%），但 OOV 率从 1.32% 到 18.35% 差一个数量级。请解释：1）两个指标各测什么构念？2）OOV 梯度对"硬约束 vs 软约束"工程路线的启示。'),
    ('音节占位', '结果：0.5B/0.5B-Instruct/1.5B 三模型音节合法性全部 50%，恒定选同一标签；多音字定音 1.5B 达 80%。请解释：1）"恒定选同一标签"与"真不知道"的行为区分？2）为何多音字定音反而有信号？'),
    ('PED 反差', '结果：场景化教学设计题各模型 98-100%，教材条文定位题最高 8.9%（5 个模型 0%）。请解释：1）为何同一 PED 维度内部分化如此极端？2）"会用教学常识"与"懂标准条文"的构念区分。'),
    ('缩放趋势', '结果：KNO 定级 0.5B 6.5% → 1.5B 15.8%（参数翻三倍，接近随机线 14.3%）；商用模型 88.5%。请解释：1）这个缩放趋势外推到 7B/70B 的合理预期与风险？2）与商用模型的差距如何解读。'),
    ('评委压缩', '结果：双评委抽检 30 题，绝对一致率 86.7% 但 Spearman ρ 仅 0.43、Pearson r 0.22，两评委均值高达 0.93-0.98。请解释：1）高一致率与弱相关为何并存？2）这对"用 LLM 评委给教学设计打分"的适用边界。'),
    ('变调失败', '结果：大模型对"一/不"变调、轻声、儿化的实际读音判断大量错误（如"一会儿"标为本调），但多音字语境定音较好。请解释：1）"词典知识"与"语流音变知识"的构念区分？2）这对语音教学应用的影响。'),
    ('污染分层', '结果：KNO 类（答案来自公开标准，污染高风险）模型得分反而不高于 GEN 类（新构造题，低污染）。请解释：1）为什么"背过仍答错"比"新题答错"更有诊断力？2）污染风险标注如何影响结论解读。'),
    ('校准可分离', '结果：豆包 Spearman ρ=0.60、QWK=0.34、容差分 44.4；线性校准其预测分后容差分升至 70+。请解释：1）校准前后什么变了什么没变？2）"区分能力"与"校准"为何是两个独立缺陷。'),
]
for name, task in INTERPRET_TASKS:
    add_item('rb.interpret', task, '', ['结果解释', name], 'cceval-findings',
             f'interpret/{name}', 'mid',
             gold_meta={'scenario': task[:150],
                        'note': '量表 RB-Rubric-1.0 rb.interpret；全部结果来自 CC-Eval v1.0 真实评测数据'})

# =====================================================================
# 编号重排：PED-8 接续 0237 起（前批最大 0236）
# =====================================================================
prev_max = 0
for fn in ['items_bench.jsonl', 'items_bench_b.jsonl']:
    for l in open(os.path.join(ROOT, 'items/v1.2', fn), encoding='utf-8'):
        d = json.loads(l)
        if d['item_id'].startswith('CCE-PED-8-'):
            prev_max = max(prev_max, int(d['item_id'].split('-')[3]))
cnt = prev_max
for it in items:
    cnt += 1
    it['item_id'] = f'CCE-PED-8-{cnt:04d}'

out_path = os.path.join(ROOT, 'items/v1.2/items_bench_d.jsonl')
with open(out_path, 'w', encoding='utf-8') as f:
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')

# 合并 v1.2 全库 = v1.1 + a + b + c + d
parts = []
v11 = open(os.path.join(ROOT, 'items/v1.1/items.jsonl'), encoding='utf-8').read()
parts.append(v11)
for fn in ['items_bench.jsonl', 'items_bench_b.jsonl', 'items_bench_c.jsonl']:
    parts.append(open(os.path.join(ROOT, 'items/v1.2', fn), encoding='utf-8').read())
comb_path = os.path.join(ROOT, 'items/v1.2/items.jsonl')
with open(comb_path, 'w', encoding='utf-8') as f:
    for blob in parts:
        f.write(blob if blob.endswith('\n') else blob + '\n')
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')

print(f'bench_d items: {len(items)}')
print(collections.Counter(it['sub_type'] for it in items))
print(collections.Counter(it['meta']['bench'] for it in items))
print('written:', out_path)
n = sum(len(b.strip().splitlines()) for b in parts) + len(items)
print(f'combined: v1.2 全库 = {n} 题')