# -*- coding: utf-8 -*-
"""生成 PHO 语音维度题目（v1.1 增量）
子任务：
  pho.syl_legal   音节合法性判断（合法/非法）
  pho.syl_level   音节定级（1-6 / 7-9）
  pho.tone_actual 词语实际读音（变调/轻声/儿化）
  pho.polyphonic  多音字语境定音
锚定：GF 0025-2021 音节表 + 词汇表（词汇表拼音为实际读音标注）+ 汉字表
"""
import os, json, re, random, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 20260906
random.seed(SEED)

STD = os.path.join(ROOT, 'standard/gf0025-2021')
syllables = json.load(open(os.path.join(STD, 'syllables.json'), encoding='utf-8'))
vocab = json.load(open(os.path.join(STD, 'vocabulary.json'), encoding='utf-8'))
chars = json.load(open(os.path.join(STD, 'characters.json'), encoding='utf-8'))

def lc(lv): return 7 if lv == '7-9' else int(lv)

# ---------- 拼音工具 ----------
INITIALS = ['zh', 'ch', 'sh', 'b', 'p', 'm', 'f', 'd', 't', 'n', 'l',
            'g', 'k', 'h', 'j', 'q', 'x', 'r', 'z', 'c', 's', 'y', 'w']
TONE2NUM = {}
for base, marks in [('a', 'āáǎà'), ('o', 'ōóǒò'), ('e', 'ēéěè'),
                    ('i', 'īíǐì'), ('u', 'ūúǔù'), ('ü', 'ǖǘǚǜ'), ('ê', 'ếề')]:
    for i, mch in enumerate(marks, 1):
        TONE2NUM[mch] = (base, str(i))

def canon(p):
    """拼音规范化：小写、ü 归一、声调符转数字原位、去空格隔音符"""
    p = p.lower().replace('u:', 'ü').replace('v', 'ü')
    out = []
    for ch in p:
        if ch in TONE2NUM:
            b, n = TONE2NUM[ch]
            out.append(b + n)
        elif ch.isalpha() or ch.isdigit():
            out.append(ch)
    return ''.join(out)

def plain(syl):
    """带调音节 -> 无调音节"""
    return re.sub(r'[0-9]', '', canon(syl))

def tone_of(syl):
    m = re.search(r'[1-5]', canon(syl))
    return m.group(0) if m else '5'

MARK_ORDER = {'a': 0, 'o': 1, 'e': 2}
NUM2MARK = {b + str(i): m for (b, marks) in [('a', 'āáǎà'), ('o', 'ōóǒò'), ('e', 'ēéěè'),
            ('i', 'īíǐì'), ('u', 'ūúǔù'), ('ü', 'ǖǘǚǜ')] for i, m in enumerate(marks, 1)}

def add_tone(plain_syl, tone):
    """给无调音节加声调（a/e 优先，ou 标 o，其余标末元音）"""
    if tone == '5':
        return plain_syl
    vowels = [i for i, ch in enumerate(plain_syl) if ch in 'aoeiuü']
    if not vowels:
        return plain_syl
    target = None
    for v in ('a', 'e'):
        for i in vowels:
            if plain_syl[i] == v:
                target = i
                break
        if target is not None:
            break
    if target is None:
        ou = plain_syl.find('ou')
        if ou >= 0:
            target = ou
    if target is None:
        target = vowels[-1] if plain_syl[vowels[-1]] != 'i' or 'u' not in plain_syl else vowels[-1]
        # iu/ui 标末元音
        target = vowels[-1] if plain_syl[vowels[-2] if len(vowels) > 1 else vowels[-1]] + plain_syl[vowels[-1]] in ('iu', 'ui') else target
    ch = plain_syl[target]
    marked = NUM2MARK.get(ch + tone)
    if not marked:
        return plain_syl
    return plain_syl[:target] + marked + plain_syl[target + 1:]

# ---------- 音节表索引 ----------
syl_set = {s['syllable'] for s in syllables}              # 带调合法音节
plain2tones = collections.defaultdict(set)                # 无调 -> 已证声调集
for s in syllables:
    plain2tones[plain(s['syllable'])].add(tone_of(s['syllable']))

def split_syllables(pinyin):
    """用合法音节集贪心最长匹配切分（词表内部多音节）"""
    s = pinyin.lower().replace('u:', 'ü')
    out, i = [], 0
    while i < len(s):
        hit = None
        for L in range(len(s) - i, 0, -1):
            cand = s[i:i + L]
            if cand in {x.lower() for x in syl_set}:
                hit = cand
                break
        if hit is None:
            return None
        out.append(hit)
        i += len(hit)
    return out

SYL_LOWER = {x.lower() for x in syl_set}

def split_syllables2(pinyin):
    """声调不敏感切分：先转成无调串按合法无调音节集贪心最长匹配，再映射回带调子串；
    词尾孤立 r 并入前一音节（儿化）"""
    s = pinyin.lower().replace('u:', 'ü')
    ps = ''.join(TONE2NUM[ch][0] if ch in TONE2NUM else ch for ch in s)
    plain_set = set(plain2tones.keys())
    out, i = [], 0
    while i < len(ps):
        hit = None
        for L in range(len(ps) - i, 0, -1):
            if ps[i:i + L] in plain_set:
                hit = ps[i:i + L]
                break
        if hit is None:
            if i == len(ps) - 1 and ps[i] == 'r' and out:
                out[-1] += 'r'
                break
            return None
        out.append(hit)
        i += len(hit)
    else:
        pass
    res, j = [], 0
    for p in out:
        res.append(s[j:j + len(p)])
        j += len(p)
    return res

items = []
def add_item(sub, level, anchor, instruction, answer, tags, source_id, contam):
    seq = sum(1 for it in items if it['sub_type'] == sub) + 1
    items.append({
        'item_id': f'CCE-PHO-{level}-{seq:04d}-{sub.split(".")[1]}'.replace('-', '-', 1),
        'version': '1.1.0',
        'task_type': 'PHO',
        'sub_type': sub,
        'anchor': anchor,
        'prompt': {'instruction': instruction, 'input': ''},
        'reference': {'answer': answer},
        'scoring': {'type': 'exact_match'},
        'provenance': {'source': 'gf0025-2021', 'source_id': source_id,
                       'license': '标准字段引用', 'contamination_risk': contam},
        'meta': {'tags': tags, 'review_status': 'draft', 'created': '2026-09-06'},
    })

# ---------- 1) pho.syl_legal 音节合法性 60 题（30 合法 + 30 非法） ----------
legal_sample = random.sample(syllables, 30)
for syl in legal_sample:
    add_item('pho.syl_legal', 9, {'syllable': syl},
             f'根据《国际中文教育中文水平等级标准》（GF 0025-2021）音节表，带调音节「{syl}」是否为合法的普通话音节？请只回答：合法 或 非法。',
             '合法', ['语音', '音节'], f'syllable#{syl}', 'mid')

fake_pool = []
# (a) 声韵组合不存在型
ini_fin = set()
for pl in plain2tones:
    ini = ''
    for cand in INITIALS:
        if pl.startswith(cand):
            ini = cand
            break
    ini_fin.add((ini, pl[len(ini):]))
inis = sorted({x[0] for x in ini_fin})
fins = sorted({x[1] for x in ini_fin})
plain_set = set(plain2tones.keys())
for ini in inis:
    for fin in fins:
        if not fin or (ini, fin) in ini_fin:
            continue
        if fin == 'er' and ini:  # er 不与声母相拼
            continue
        cand = ini + fin
        if ini in ('j', 'q', 'x') and fin.startswith('ü'):
            cand = ini + 'u' + fin[1:]  # j/q/x 后 ü 省略两点
            if cand in plain_set:
                continue
        fake_pool.append(cand)
# (b) 声调不存在型
for pl, tones in plain2tones.items():
    for t in '1234':
        if t not in tones:
            fake_pool.append(add_tone(pl, t) + f'§t{t}')
random.shuffle(fake_pool)
seen_fake = set()
fakes = []
for f in fake_pool:
    tone_tag = None
    if '§t' in f:
        f, tone_tag = f.split('§t')
        syl = f
    else:
        syl = add_tone(f, random.choice('1234'))
    if syl.lower() in SYL_LOWER or syl in seen_fake or len(syl) < 2:
        continue
    seen_fake.add(syl)
    fakes.append(syl)
    if len(fakes) >= 30:
        break
for syl in fakes:
    add_item('pho.syl_legal', 9, {'syllable': syl},
             f'根据《国际中文教育中文水平等级标准》（GF 0025-2021）音节表，带调音节「{syl}」是否为合法的普通话音节？请只回答：合法 或 非法。',
             '非法', ['语音', '音节'], f'fake-syllable#{syl}', 'low')

# ---------- 2) pho.syl_level 音节定级 40 题 ----------
for s in random.sample(syllables, 40):
    lv = s['level'] if s['level'] != '7-9' else '7-9'
    add_item('pho.syl_level', lc(s['level']), {'syllable': s['syllable'], 'level': s['level']},
             f'根据《国际中文教育中文水平等级标准》（GF 0025-2021）音节表，带调音节「{s["syllable"]}」（例字：{s["example_char"]}）属于哪个等级？请只回答一个等级：1、2、3、4、5、6 或 7-9，不要解释。',
             str(lv), ['语音', '音节', '等级定位'], f'syllable#{s["no"]}', 'high')

# ---------- 3) pho.tone_actual 实际读音 50 题（一变调/不变调/轻声/儿化） ----------
# 按"一/不所在音节的实际声调"精确分类，排除误收
char_readings0 = collections.defaultdict(set)
for c in chars:
    char_readings0[c['char']].add(c['pinyin'])

def classify_tone(w, py):
    """返回 (类别, 证据) 或 None"""
    parts = split_syllables2(py)
    if not parts:
        return None
    if py.lower().endswith('r') and w.endswith('儿'):
        # 儿化：词尾"儿"并入前一音节（如 哪儿 nǎr、一会儿 yíhuìr）
        return ('儿化', parts[-1]) if len(parts) == len(w) - 1 else None
    if len(parts) != len(w):
        return None
    for pos, ch in enumerate(w):
        if ch in '一不':
            cit = '1' if ch == '一' else '4'
            t = tone_of(parts[pos])
            if t != cit:
                return (f'{ch}变调', parts[pos])
    for pos, ch in enumerate(w):
        if ch not in '一不' and tone_of(parts[pos]) == '5':
            cit = char_readings0.get(ch, set())
            if any(tone_of(r) != '5' for r in cit):
                return ('轻声', parts[pos])
    return None

bycat = collections.defaultdict(list)
for x in vocab:
    w, py = x['word'], x['pinyin']
    if '∣' in py or len(w) < 2 or len(w) > 4:
        continue
    r = classify_tone(w, py)
    if r:
        bycat[r[0]].append((x, r[1]))
for k in bycat:
    random.shuffle(bycat[k])
picked = ([x for x, _ in bycat['一变调'][:12]] + [x for x, _ in bycat['不变调'][:12]]
          + [x for x, _ in bycat['轻声'][:15]] + [x for x, _ in bycat['儿化'][:11]])
for x in picked:
    add_item('pho.tone_actual', lc(x['level']), {'vocab_no': x['no'], 'level': x['level']},
             f'在普通话实际语流中，词语「{x["word"]}」的规范读音是什么？请只回答带声调的拼音（如 wǒmen），不要解释。',
             x['pinyin'], ['语音', '实际读音'], f'vocab#{x["no"]}', 'mid')

# ---------- 4) pho.polyphonic 多音字定音 30 题 ----------
char_readings = collections.defaultdict(set)
for c in chars:
    char_readings[c['char']].add(c['pinyin'])
poly = {k: v for k, v in char_readings.items() if len(v) > 1}
cands = []
for x in vocab:
    w, py = x['word'], x['pinyin']
    if '∣' in py or len(w) < 2 or len(w) > 4:
        continue
    hits = [i for i, ch in enumerate(w) if ch in poly]
    if not hits:
        continue
    parts = split_syllables2(py)
    if not parts or len(parts) != len(w):
        continue
    i = hits[0]
    gold = parts[i]
    # 该语境读音必须确实是多音字读音之一
    if gold not in {p.lower() for p in poly[w[i]]}:
        continue
    cands.append((x, i, gold))
random.shuffle(cands)
for x, i, gold in cands[:30]:
    ch = x['word'][i]
    add_item('pho.polyphonic', lc(x['level']), {'vocab_no': x['no'], 'char': ch, 'level': x['level']},
             f'词语「{x["word"]}」中，第 {i + 1} 个字「{ch}」在该词中的正确读音是什么？请只回答带声调的拼音，不要解释。',
             gold, ['语音', '多音字'], f'vocab#{x["no"]}#{ch}', 'mid')

# ---------- 编号重排 & 输出 ----------
cnt = collections.Counter()
for it in items:
    lvl = it['item_id'].split('-')[2]
    key = (lvl,)
    cnt[key] += 1
    it['item_id'] = f'CCE-PHO-{lvl}-{cnt[key]:04d}'

os.makedirs(os.path.join(ROOT, 'items/v1.1'), exist_ok=True)
pho_path = os.path.join(ROOT, 'items/v1.1/items_pho.jsonl')
with open(pho_path, 'w', encoding='utf-8') as f:
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')

v10 = open(os.path.join(ROOT, 'items/v1.0/items.jsonl'), encoding='utf-8').read()
comb_path = os.path.join(ROOT, 'items/v1.1/items.jsonl')
with open(comb_path, 'w', encoding='utf-8') as f:
    f.write(v10 if v10.endswith('\n') else v10 + '\n')
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')

print(f'PHO items: {len(items)}')
print(collections.Counter(it["sub_type"] for it in items))
print('合法/非法分布:', sum(1 for it in items if it["sub_type"]=="pho.syl_legal" and it["reference"]["answer"]=="合法"),
      '/', sum(1 for it in items if it["sub_type"]=="pho.syl_legal" and it["reference"]["answer"]=="非法"))
print('written:', pho_path)
print('combined:', comb_path, 'total:', len(v10.strip().splitlines()) + len(items))
