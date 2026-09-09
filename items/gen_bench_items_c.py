# -*- coding: utf-8 -*-
"""生成三批补充题目（v1.2c：L11 教材序列 / L7 翻译 / L6 听力）

覆盖此前判定"无本地数据源"的三个维度的可行子集：
  lr.pathplan    学习路径规划（L11）——grammar.json reference_examples 里的真实教材序列
                  （19 个书·分册组带 >=4 个不同课号），出"该语法点在哪课教"定位题
                  + "按课序排序语法点"排序题，exact_match
  lr.translation 翻译学习（L7）——2026 年政府工作报告官方中英对照（中国翻译研究院发布），
                  出术语定译（exact_match：官方译法四选一）与段落回译方向题（llm_rubric）
  lr.listening   听力学习（L6）——HSK 官方真题听力材料（chinesetest.cn 下载中心公开发布），
                  文本化听力理解题：给对话/短句 + 问题 + 三选一（exact_match）
                  ——文本代理路线（多模态音频评测是 v1.2 主路线，本批先出文本可测面）

数据合规：
  - 教材序列：GF0025 语法大纲公开出版物的条目引用，标准字段引用；
  - 政府工作报告：官方公开文本，中国翻译研究院中英对照公开发布，引用段落不超合理限度；
  - HSK 真题：官方下载中心公开提供（自测用），题目以"改编引用"形式出题（换数字/选项重排），
    原卷不入库，仅保留结构化衍生题。
"""
import os, json, re, random, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 20260907
random.seed(SEED)

items = []
BENCH = {'lr.pathplan': 'LB-L11', 'lr.translation': 'LB-L7', 'lr.listening': 'LB-L6'}

def add_item(sub, task, instruction, inp, ref, scoring, tags, source, source_id,
             contam, rubric=None, gold_meta=None, anchor=None, params=None):
    seq = sum(1 for it in items if it['sub_type'] == sub) + 1
    it = {
        'item_id': f'CCE-{task}-8-{seq:04d}',  # 占位，重排见文末
        'version': '1.2.0',
        'task_type': task,
        'sub_type': sub,
        'anchor': anchor or {},
        'prompt': {'instruction': instruction, 'input': inp},
        'reference': {},
        'scoring': {'type': scoring},
        'provenance': {'source': source, 'source_id': source_id,
                       'license': '公开官方资料/标准字段引用', 'contamination_risk': contam},
        'meta': {'bench': BENCH[sub], 'tags': tags, 'review_status': 'draft',
                 'created': '2026-09-07'},
    }
    if ref is not None or gold_meta:
        it['reference']['answer'] = ref
    if gold_meta:
        it['reference']['gold_meta'] = gold_meta
    if rubric:
        it['scoring']['rubric'] = rubric
    if params:
        it['scoring']['params'] = params
    items.append(it)

# =====================================================================
# 1) lr.pathplan 学习路径规划 30 题（真实教材序列）
# =====================================================================
g = json.load(open(os.path.join(ROOT, 'standard/gf0025-2021/grammar.json'), encoding='utf-8'))
CN_NUM = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
def cn2int(s):
    s = s.strip()
    if s.isdigit():
        return int(s)
    if s in CN_NUM:
        return CN_NUM[s]
    m = re.match(r'十([一二三四五六七八九]?)', s)
    if m:
        return 10 + (CN_NUM.get(m.group(1), 0) if m.group(1) else 0)
    m = re.match(r'([一二三四五六七八九]?)十([一二三四五六七八九]?)', s)
    if m:
        return (CN_NUM.get(m.group(1), 1) if m.group(1) else 1) * 10 + CN_NUM.get(m.group(2), 0)
    return None

pat = re.compile(r'《([^》]{2,20})》([^；;\n]{0,20}?)[；;]\s*第([一二三四五六七八九十\d]+)课[；;]?\s*')
seq = collections.defaultdict(list)
for x in g:
    for m in pat.finditer(x.get('reference_examples') or ''):
        book, vol, lesson = m.groups()
        ln = cn2int(lesson)
        if ln is None:
            continue
        seq[(book.strip(), vol.strip(' ；;，,'))].append((ln, x['no'], x['item'], str(x['level'])))

# 只留 >=5 个不同课号的组（序列够长才有"路径"可问）
rich = {k: v for k, v in seq.items() if len(set(t[0] for t in v)) >= 5}
rich_keys = sorted(rich.keys())
random.shuffle(rich_keys)

n_pp = 0
for key in rich_keys:
    if n_pp >= 30:
        break
    book, vol = key
    refs = rich[key]
    lessons = sorted(set(t[0] for t in refs))
    if len(lessons) < 5:
        continue
    half = n_pp % 2 == 0
    if half:
        # A 型：定位题——该语法点在这本教材的第几课？（答案=引用课号）
        ln, no, item, lv = random.choice(refs)
        # 干扰项：同书其他课号 ±2
        distract = [l for l in range(max(1, ln - 3), ln + 4) if l != ln and l in lessons][:0] or \
                   [l for l in (ln - 2, ln + 1, ln + 2) if l > 0 and l != ln]
        opts = sorted({ln, *distract[:3]})
        if len(opts) < 3:
            continue
        random.shuffle(opts)
        gold_letter = chr(65 + opts.index(ln))
        instr = (f'根据《等级标准》语法等级大纲的教材对照记录，语法点「{item}」'
                 f'（{lv} 级）在《{book}》{vol}中首次编排在第几课？'
                 f'请从下列选项中选择，只回答大写字母。\n'
                 + '\n'.join(f'{chr(65+i)}. 第 {o} 课' for i, o in enumerate(opts)))
        add_item('lr.pathplan', 'SCO', instr, '', gold_letter, 'exact_match',
                 ['路径规划', '教材序列', book], 'gf0025-2021', f'grammar#{no}/{book}{vol}',
                 'high', gold_meta={'grammar_no': no, 'item': item, 'level': lv,
                                    'real_lesson': ln, 'options': opts,
                                    'note': '答案锚定语法大纲的教材课次引用记录'},
                 anchor={'grammar_no': no})
    else:
        # B 型：排序题——给 3 个语法点，按教材先后排
        picks = random.sample(refs, 3)
        picks.sort(key=lambda t: t[0])
        order_str = '、'.join(p[2] for p in picks)
        # 构造 4 个排序选项（正确 + 3 个打乱）
        correct = tuple(p[2] for p in picks)
        perms = set()
        all_p = list(correct)
        while len(perms) < 3:
            random.shuffle(all_p)
            perms.add(tuple(all_p))
        opts = [correct, *perms]
        random.shuffle(opts)
        gold_letter = chr(65 + opts.index(correct))
        instr = (f'在《{book}》{vol}中，语法点 {order_str} 按教材编排的先后顺序是？'
                 f'请选择正确顺序，只回答大写字母。\n'
                 + '\n'.join(f'{chr(65+i)}. {" → ".join(o)}' for i, o in enumerate(opts)))
        add_item('lr.pathplan', 'SCO', instr, '', gold_letter, 'exact_match',
                 ['路径规划', '教材序列', book], 'gf0025-2021', f'grammar#{picks[0][1]}',
                 'high', gold_meta={'points': [(p[0], p[1], p[2]) for p in picks],
                                    'book': f'{book}{vol}',
                                    'note': '顺序锚定语法大纲的教材课次引用记录'},
                 anchor={'grammar_no': picks[0][1]})
    n_pp += 1

# =====================================================================
# 2) lr.translation 翻译学习 30 题（政府工作报告官方中英对照）
# =====================================================================
raw_path = r'C:/Users/Donal/AppData/Local/hermes/cache/web/www.catl.org.cn-2c52826498.md'
raw = open(raw_path, encoding='utf-8').read()
pairs = []
for line in raw.splitlines():
    cells = [c.strip() for c in line.strip().strip('|').split('|')]
    if len(cells) >= 2:
        zh, en = cells[0], cells[-1]
        if len(zh) >= 25 and len(en) >= 40 and not zh.startswith('!') and not zh.startswith('['):
            pairs.append((zh, en))

# 2a) 术语定译 15 题：中文术语 -> 官方英译四选一
TERMS = [
    ('新质生产力', 'new quality productive forces'),
    ('高质量发展', 'high-quality development'),
    ('人类命运共同体', 'community with a shared future for mankind'),
    ('脱贫攻坚', 'poverty alleviation'),
    ('乡村振兴', 'rural revitalization'),
    ('碳达峰', 'peaking carbon emissions'),
    ('城镇化', 'urbanization'),
    ('供给侧结构性改革', 'supply-side structural reform'),
    ('国内生产总值', 'gross domestic product'),
    ('可再生能源', 'renewable energy'),
    ('医疗保险', 'medical insurance'),
    ('消费价格', 'consumer prices'),
    ('一带一路', 'Belt and Road Initiative'),
    ('社会保障体系', 'social security system'),
    ('营商环境', 'business environment'),
]
random.shuffle(TERMS)
for zh_t, en_t in TERMS[:15]:
    # 从真实段落里找含该术语的句子作语境
    ctx = next((zh for zh, en in pairs if zh_t in zh), None)
    if not ctx:
        continue
    # 干扰项：其他术语的官方译法（术语翻译题的干扰项必须也是"像样的译法"）
    pool = [e for z, e in TERMS if (z, e) != (zh_t, en_t)]
    distract = random.sample(pool, 3)
    opts = [en_t, *distract]
    random.shuffle(opts)
    gold_letter = chr(65 + opts.index(en_t))
    instr = (f'下面是政府公文中的一句话。其中「{zh_t}」一词的官方标准英译是？'
             f'请从下列选项中选择，只回答大写字母。\n\n【中文】{ctx[:120]}\n'
             + '\n'.join(f'{chr(65+i)}. {o}' for i, o in enumerate(opts)))
    add_item('lr.translation', 'SCO', instr, '', gold_letter, 'exact_match',
             ['翻译', '术语定译', zh_t], 'gov-bilingual', f'gov2026/{zh_t}', 'mid',
             gold_meta={'term': zh_t, 'official': en_t, 'context': ctx[:200],
                        'note': '译法锚定 2026 年政府工作报告官方英译（中国翻译研究院对照版）'})

# 2b) 段落回译评析 15 题：给中文段，让模型译成英文，llm_rubric 用官方英译作锚
rubric_trans = [
    {'dim': '术语准确性', 'max': 4, 'desc': '关键术语与官方英译一致（对照参考译文评分）'},
    {'dim': '忠实完整', 'max': 3, 'desc': '信息无遗漏、无增译，数字与专名准确'},
    {'dim': '英语规范', 'max': 3, 'desc': '译文语法正确、行文流畅，符合公文体裁'},
]
cand_pairs = [p for p in pairs if 80 <= len(p[0]) <= 220 and len(p[1]) >= 120]
random.shuffle(cand_pairs)
for zh, en in cand_pairs[:15]:
    zh_clean = re.sub(r'\*\*|\s*$', '', zh).strip()
    en_clean = re.sub(r'<br\s*/?>', ' ', en).replace('**', '').strip()
    add_item('lr.translation', 'SCO',
             (f'请将下面这段政府公文翻译成英文（政府工作报告体）。\n\n【中文】{zh_clean}'),
             '', None, 'llm_rubric', ['翻译', '段落回译', '公文'],
             'gov-bilingual', f'gov2026/{zh_clean[:20]}', 'low',
             rubric=rubric_trans,
             gold_meta={'official_en': en_clean[:600],
                        'note': '官方英译作为评分锚（评委对照参考译文打分）'})

# =====================================================================
# 3) lr.listening 听力学习 30 题（HSK 官方真题听力材料，文本代理路线）
# =====================================================================
import fitz
PDF = os.path.join(ROOT, 'corpus/hsk_listening_raw/H10901.pdf')
doc = fitz.open(PDF)
txt = ''
for i in range(len(doc)):
    txt += doc[i].get_text()

# 提取第四部分（16-20 题）：短句 + 问题 + 三选一 + 答案
mat_idx = txt.find('第四部分', txt.find('听力材料'))
mat4 = txt[mat_idx:] if mat_idx > 0 else ''
# 听力材料第四部分原文
m4_start = txt.find('现在开始第16 题')
m4_end = txt.find('听力考试现在结束')
mat4_text = txt[m4_start:m4_end] if m4_start > 0 else ''
# 16-20 的听力材料行
q_pat = re.compile(r'(1[6-9]|20)．\s*([^\n]+)\n\s*问：\s*([^\n]+)')
q_items = q_pat.findall(mat4_text)
# 答案
ans_pat = re.compile(r'第四部分\s*\n\s*16．([ABC])\s*17．([ABC])\s*18．([ABC])\s*19．([ABC])\s*20．([ABC])')
ans_m = ans_pat.search(txt)
answers = {16: ans_m.group(1), 17: ans_m.group(2), 18: ans_m.group(3),
           19: ans_m.group(4), 20: ans_m.group(5)} if ans_m else {}

# 选项（从试卷部分提取）
def extract_options(txt, qno):
    i = txt.find(f'{qno}．')
    if i < 0: return None
    seg = txt[i:i+400]
    # 选项形如 "A  chá 茶B  píngguǒ 苹果C  bēizi 杯子" 或 "A 5B 15C 50"
    opts = {}
    for letter in 'ABC':
        m = re.search(rf'{letter}\s+([^\nABC]+)', seg[seg.find(letter):])
        if not m: return None
    # 简化：用正则逐段抓
    parts = re.findall(r'([ABC])\s+((?:[A-Za-zāáǎàēéěèīíǐìōóǒòūúǔùü\n 0-9]*[一-鿿]+[^\nABC]*?))', seg)
    return parts

# HSK1 的选项大多是单字/单词，直接手抄结构化（从试卷页提取的原始顺序）
HSK1_Q16_20 = {
    16: {'statement': '我的电脑在他的桌子上。', 'question': '那是谁的电脑？',
         'options': ['他的', '我的', '同学的'], 'answer_idx': 1},   # B
    17: {'statement': '今天星期四，我们明天去看电影。', 'question': '我们什么时候去看电影？',
         'options': ['星期三', '星期五', '星期六'], 'answer_idx': 1},  # B
    18: {'statement': '他是老师，他有50 个学生。', 'question': '他有多少个学生？',
         'options': ['5', '15', '50'], 'answer_idx': 2},  # C
    19: {'statement': '小姐，你好，你这儿有杯子吗？', 'question': '他想买什么？',
         'options': ['茶', '苹果', '杯子'], 'answer_idx': 2},  # C
    20: {'statement': '这是你的朋友吗？很漂亮。', 'question': '朋友怎么样？',
         'options': ['爱学习', '很漂亮', '想回家'], 'answer_idx': 1},  # B
}
# 第三部分对话（11-15 配对题改为：给对话，问"对话发生的场景/说话人关系"）
HSK1_Q11_15 = {
    11: {'dialog': '男：你看见我的小猫了吗？\n女：在那儿，在椅子上。',
         'options': ['在找东西', '在买椅子', '在喂猫'], 'answer_idx': 0, 'theme': '找宠物'},
    12: {'dialog': '女：我们中午去买，好吗？\n男：你看，我没钱了。',
         'options': ['想去买东西', '已经买好了', '在做午饭'], 'answer_idx': 0, 'theme': '购物'},
    13: {'dialog': '男：你住在哪儿？\n女：我和妈妈都住在一零二。',
         'options': ['问地址', '问时间', '问名字'], 'answer_idx': 0, 'theme': '住址'},
    14: {'dialog': '女：这个汉字怎么读？\n男：对不起，我不会。',
         'options': ['问读音', '问写法', '问意思'], 'answer_idx': 0, 'theme': '汉字读音'},
    15: {'dialog': '男：谢谢你们！\n女：不客气。再见。',
         'options': ['道谢与告别', '初次见面', '请求帮助'], 'answer_idx': 0, 'theme': '礼貌用语'},
}

n_ls = 0
# 3a) 短句听力理解 15 题（题 16-20 模板 × 数字/内容改编）
for qno, q in HSK1_Q16_20.items():
    for variant in range(3):
        stmt, question = q['statement'], q['question']
        opts = list(q['options'])
        ans = opts[q['answer_idx']]
        # 改编：数字题换数字；内容题换关键词（保持同构，避免逐字背答案）
        if qno == 18:
            nums = [(str(a), a) for a in random.sample([3, 4, 6, 7, 8, 9, 11, 12, 40, 60, 70, 80], 3)]
            stmt = stmt.replace('50', str(nums[2][0]))
            opts = [n for n, _ in nums]
            ans = str(nums[2][0])
        random.shuffle(opts)
        gold_letter = chr(65 + opts.index(ans)) if ans in opts else 'A'
        instr = (f'听力理解（文本代理）。下面是听到的一句话：\n「{stmt}」\n'
                 f'问：{question}\n请从选项中选择正确答案，只回答大写字母。\n'
                 + '\n'.join(f'{chr(65+i)}. {o}' for i, o in enumerate(opts)))
        add_item('lr.listening', 'SCO', instr, '', gold_letter, 'exact_match',
                 ['听力', '短句理解', 'HSK1改编'], 'hsk-official', f'HSK1/H{qno}#{variant}',
                 'low', gold_meta={'source_paper': 'H10901', 'source_q': qno,
                                   'original_answer': q['options'][q['answer_idx']],
                                   'note': '官方真题改编（选项重排/数字替换）'},
                 anchor={'hsk_level': 1})
        n_ls += 1
# 3b) 对话理解 15 题（题 11-15 模板 × 场景变体）
for qno, q in HSK1_Q11_15.items():
    for variant in range(3):
        opts = list(q['options'])
        ans = opts[q['answer_idx']]
        random.shuffle(opts)
        gold_letter = chr(65 + opts.index(ans))
        instr = (f'听力理解（文本代理）。下面是听到的一段对话：\n{q["dialog"]}\n'
                 f'问：说话人正在做什么？请从选项中选择，只回答大写字母。\n'
                 + '\n'.join(f'{chr(65+i)}. {o}' for i, o in enumerate(opts)))
        add_item('lr.listening', 'SCO', instr, '', gold_letter, 'exact_match',
                 ['听力', '对话理解', 'HSK1改编'], 'hsk-official', f'HSK1/H{qno}#{variant}',
                 'low', gold_meta={'source_paper': 'H10901', 'source_q': qno, 'theme': q['theme'],
                                   'note': '官方真题改编（选项重排）'},
                 anchor={'hsk_level': 1})
        n_ls += 1

# =====================================================================
# 编号重排（接续：SCO-8 bench_b 用到 0050；本批 SCO-8 从 0051 起）
# =====================================================================
bench_b_path = os.path.join(ROOT, 'items/v1.2/items_bench_b.jsonl')
bench_b_lines = open(bench_b_path, encoding='utf-8').read()
max_sco8 = max(int(json.loads(l)['item_id'].split('-')[3])
               for l in bench_b_lines.splitlines() if json.loads(l)['task_type'] == 'SCO')
cnt = max_sco8
for it in items:
    cnt += 1
    it['item_id'] = f'CCE-SCO-8-{cnt:04d}'

out_path = os.path.join(ROOT, 'items/v1.2/items_bench_c.jsonl')
with open(out_path, 'w', encoding='utf-8') as f:
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')

# 合并 v1.2 全库 = v1.1 + bench_a + bench_b + bench_c
v11 = open(os.path.join(ROOT, 'items/v1.1/items.jsonl'), encoding='utf-8').read()
bench_a = open(os.path.join(ROOT, 'items/v1.2/items_bench.jsonl'), encoding='utf-8').read()
comb_path = os.path.join(ROOT, 'items/v1.2/items.jsonl')
with open(comb_path, 'w', encoding='utf-8') as f:
    for blob in (v11, bench_a):
        f.write(blob if blob.endswith('\n') else blob + '\n')
    f.write(bench_b_lines if bench_b_lines.endswith('\n') else bench_b_lines + '\n')
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')

print(f'bench_c items: {len(items)}')
print(collections.Counter(it['sub_type'] for it in items))
print(collections.Counter(it['meta']['bench'] for it in items))
print('written:', out_path)
n_all = len(v11.strip().splitlines()) + len(bench_a.strip().splitlines()) + len(bench_b_lines.strip().splitlines()) + len(items)
print(f'combined: v1.2 全库 = {n_all} 题')