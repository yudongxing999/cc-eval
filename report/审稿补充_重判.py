# -*- coding: utf-8 -*-
"""实验B 重做——真正保守的重判（逐项豁免三类争议，给算法伪影定上界）：
豁免规则（全部朝"不违规"偏置）：
  R1 切分歧义：违规词表词若可被拆成两个更低级的词表词（如"世界"=世+界 若均≤目标）→ 豁免
  R2 专名豁免：违规词/字属于朝代（唐宋隋秦汉明清元晋周商）、地名（圳珠沪粤闽赣）、
     人名姓氏高频字 → 豁免（标准把专名判高级是内容语义而非词汇语法）
  R3 合成词豁免：多字违规词含"专、络、者、均、脉"类语素字且整词不在低级词表 → 疑似模型自造组合 → 豁免
"""
import json, re, os, sys, random
from collections import Counter

sys.path.insert(0, 'runner')
from run_eval import check_vocab_level, clean_output, load_lexicon

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODELS = ['deepseek', 'qwen', 'zhipu', 'ernie', 'grok', 'stepfun', 'doubao', 'hunyuan',
          'k2d6-agent', 'k3-agent', 'tchub-dsv4f']
audit = json.load(open('report/论文二_全量审计.json', encoding='utf-8'))
lx = load_lexicon()
WL, CL = lx['word_lvl'], lx['char_lvl']

DYNASTY = set('唐宋隋秦汉明清元晋周商鲁楚齐梁陈魏吴越郑蔡滕薛虞夏殷辽金')
PLACE = set('圳珠沪粤闽赣皖豫鄂湘桂琼滇黔陇青藏疆蒙藏壮彝傣')
SURNAME = set('赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜')
FUNC_MORPHEME = set('专者均络脉项层序')  # 模型合成词常见语素

def can_reparse(word, cap):
    """R1: 词表词能否拆成两个更低级词表词（切分歧义可能）"""
    if len(word) < 2 or word not in WL:
        return False
    for k in range(1, len(word)):
        a, b = word[:k], word[k:]
        if a in WL and b in WL and WL[a] <= cap and WL[b] <= cap:
            return True
    return False

def is_proper(word):
    """R2: 专名性质（朝代/地名/姓氏）"""
    chars = set(word)
    if chars & (DYNASTY | PLACE | SURNAME):
        return True
    return False

def is_blend(word):
    """R3: 疑似模型自造合成词：多字、不在词表（回退产物）或含罕见语素"""
    if word not in WL and len(word) >= 2:
        return True
    if set(word) & FUNC_MORPHEME and len(word) >= 2:
        return True
    return False

def conservative_rejudge(out, cap):
    """最保守重判：三类争议全部豁免，返回铁违规列表"""
    ok, viol = check_vocab_level(out, cap)
    hard = []
    for v in viol:
        if v in WL:  # 词表词
            if can_reparse(v, cap):
                continue
            if is_proper(v):
                continue
            hard.append(v)
        else:  # 单字回退
            if is_proper(v):
                continue
            if is_blend(v):
                continue
            hard.append(v)
    return hard

# 全量重判（不只 50 篇——全量 1,320 篇都跑，给最强的上界证据）
tot_orig = tot_hard = 0
pass_orig = pass_hard = 0
n_flip_pass = 0
for m in MODELS:
    for r in audit[m]:
        out = clean_output(json.load(open(f'results/{m}/{r["item_id"]}.json', encoding='utf-8'))['output'] or '')
        cap = r['target']
        _, viol = check_vocab_level(out, cap)
        hard = conservative_rejudge(out, cap)
        tot_orig += len(viol)
        tot_hard += len(hard)
        p_orig = (len(viol) == 0)
        p_hard = (len(hard) == 0)
        pass_orig += p_orig
        pass_hard += p_hard
        if p_orig != p_hard:
            n_flip_pass += 1

print('===== 全量保守重判（1,320 篇）=====')
print(f'原判违规: {tot_orig} 词 → 保守重判铁违规: {tot_hard} 词（{tot_hard/tot_orig*100:.1f}%）')
print(f'原判通过: {pass_orig} 篇 → 保守重判通过: {pass_hard} 篇（翻转 {n_flip_pass} 篇）')
po = 1 - n_flip_pass / 1320
p1, p2 = pass_orig/1320, pass_hard/1320
pe = p1*p2 + (1-p1)*(1-p2)
kappa = (po - pe) / (1 - pe)
print(f'Cohen Kappa（通过判定，全量）: {kappa:.3f}')
print(f'违规密度下界: 每百字原 18.6 → 保守 {tot_hard/sum(max(r["hnz"],1) for m in MODELS for r in audit[m])*100:.1f}')

res = {
    '全量保守重判': {
        'viol_orig': tot_orig, 'viol_hard': tot_hard,
        'ratio': round(tot_hard/tot_orig, 3),
        'pass_orig': pass_orig, 'pass_hard': pass_hard, 'flip': n_flip_pass,
        'kappa': round(kappa, 3),
    }
}
json.dump(res, open('report/审稿补充_当代语言学实验.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n保存: report/审稿补充_当代语言学实验.json')