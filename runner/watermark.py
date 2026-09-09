# -*- coding: utf-8 -*-
"""CC-Eval 交付水印系统 v1.1

三层透明水印（打水印 / 提取验证）：

  层1 零宽字符水印（零视觉影响）
      每题题面文本中插入不可见序列：BOM 定界 + 缩写签名（每字符 3 个零宽三态字母）
      + 每题独立指纹（mark+tag+item_id 的 SHA256 派生 3 字母）。
      U+200B/200C/200D/FEFF 在编辑器、浏览器、PDF、LLM tokenizer 中均不可见。

  层2 word-joiner 水印（U+2060，抗"只滤零宽"的清洗）
      按 50% 签名奇偶性在 provenance.license 的首个逗号前插入 U+2060。

  层3 元数据署名（可见但低调）
      meta.wm = "v1:<MARK>:<tag>"，provenance.license 追加「｜MARK·tag」。
      不是隐蔽水印，是合规署名——配合层1/2 的隐蔽层形成互补。

提取：extract 模式报告三层各自的存在比例与解码签名。

用法：
  打水印：  python watermark.py embed --in a.jsonl --out b.jsonl --mark YDX --tag to-xxx
  提取验证：python watermark.py extract --in b.jsonl
  抽查原文：python watermark.py extract --in a.jsonl   （应报告无水印，作为对照）

设计：于东兴（Dongxing Yu）· 2026-09-08
"""
import os, sys, json, argparse, hashlib

ZW = {'A': '\u200b', 'B': '\u200c', 'C': '\u200d'}   # 零宽三态字母
ZWMARK = '\ufeff'                                     # BOM 定界
WJ = '\u2060'                                         # word joiner（层2）

def mark_to_zw(mark):
    """缩写 -> 零宽序列：BOM + 每字符 3 个三态字母（base-3, 1-26=字母, 0/27=非字母）+ BOM"""
    seq = [ZWMARK]
    for ch in mark.upper():
        v = (ord(ch) - ord('A') + 1) if ch.isalpha() else 0
        seq.append(ZW['ABC'[v % 3]] + ZW['ABC'[(v // 3) % 3]] + ZW['ABC'[(v // 9) % 3]])
    seq.append(ZWMARK)
    return ''.join(seq)

def extract_zw(text):
    """零宽序列 -> 字母串。只解码「BOM 定界之间且长度为 3 的倍数」的段：
    mark 段（每字符 3 个三态字母）；定界外的零宽（指纹段、孤立字符）不参与解码，
    避免指纹被误读为字母。"""
    if ZWMARK not in text:
        return None
    vals = {'\u200b': 0, '\u200c': 1, '\u200d': 2}
    segs = text.split(ZWMARK)
    out = []
    for si in range(1, len(segs) - 1):          # 只看定界符之间的段
        s = segs[si]
        if not s or len(s) % 3 or any(c not in vals for c in s):
            continue
        chunk = []
        for i in range(0, len(s), 3):
            v = vals[s[i]] + vals[s[i + 1]] * 3 + vals[s[i + 2]] * 9
            chunk.append(chr(ord('A') + v - 1) if 1 <= v <= 26 else '?')
        if chunk and '?' not in chunk:
            out.append(''.join(chunk))
    return ''.join(out) if out else None

def item_fingerprint(mark, tag, item_id):
    """每题独立 3 字母指纹（嵌入在签名后，逐题可查：这题属于哪个交付批次）"""
    h = int(hashlib.sha256(f'cc-eval-wm-v1|{mark}|{tag}|{item_id}'.encode()).hexdigest()[:4], 16)
    return ZW['ABC'[h % 3]] + ZW['ABC'[(h // 3) % 3]] + ZW['ABC'[(h // 9) % 3]]

def embed_line(text, payload):
    """在文本首个句读标点后插入零宽载荷（清洗者需知道位置才能去除）"""
    for i, ch in enumerate(text):
        if ch in '，。：；、':
            return text[:i + 1] + payload + text[i + 1:]
    return text + payload

def do_embed(args):
    items = [json.loads(l) for l in open(args.infile, encoding='utf-8') if l.strip()]
    base_payload = mark_to_zw(args.mark)
    print(f'签名: {args.mark} | 交付标签: {args.tag}')
    print(f'层1 零宽载荷: {len(base_payload)} 个不可见字符（每题再 +3 指纹字符）')
    with open(args.outfile, 'w', encoding='utf-8') as f:
        for it in items:
            payload = base_payload + item_fingerprint(args.mark, args.tag, it['item_id'])
            p = it.setdefault('prompt', {})
            if p.get('instruction'):
                p['instruction'] = embed_line(p['instruction'], payload)
            if p.get('input'):
                p['input'] = embed_line(p['input'], payload)
            # 层2：license 首字符前插 word-joiner（按签名奇偶，一半题目）
            lic = it.setdefault('provenance', {}).setdefault('license', '')
            fp = item_fingerprint(args.mark, args.tag, it['item_id'])
            if lic and (ord(fp[0]) + ord(fp[1])) % 2 == 0:
                it['provenance']['license'] = WJ + lic
            # 层3：可见署名
            # 层3：可见署名（保留层2 的 WJ 前缀，追加在末尾）
            cur = it['provenance']['license']
            it['provenance']['license'] = cur + (f'｜{args.mark}·{args.tag}' if cur else f'{args.mark}·{args.tag}')
            it.setdefault('meta', {})['wm'] = f'v1:{args.mark}:{args.tag}'
            f.write(json.dumps(it, ensure_ascii=False) + '\n')
    print(f'已写入 {len(items)} 题 -> {args.outfile}')

def do_extract(args):
    items = [json.loads(l) for l in open(args.infile, encoding='utf-8') if l.strip()]
    n_zw, marks, n_wj, meta_wm, fp_examples = 0, set(), 0, set(), []
    for it in items:
        fields = [it.get('prompt', {}).get('instruction', ''), it.get('prompt', {}).get('input', '')]
        has = any(ZWMARK in f for f in fields)
        if has:
            n_zw += 1
            for f in fields:
                m = extract_zw(f)
                if m and '?' not in m:
                    marks.add(m)
        if WJ in it.get('provenance', {}).get('license', ''):
            n_wj += 1
        w = it.get('meta', {}).get('wm', '')
        if w:
            meta_wm.add(w)
    print(f'检查 {len(items)} 题')
    print(f'层1 零宽水印: {n_zw} 题携带（{n_zw / max(len(items), 1) * 100:.0f}%）')
    print(f'  解码签名: {sorted(marks)[:5]}')
    print(f'层2 word-joiner: {n_wj} 题携带')
    print(f'层3 元数据署名: {sorted(meta_wm)}')
    if n_zw == 0 and not meta_wm:
        print('结论: 未发现 CC-Eval 交付水印（原文或已全量清洗）')

def main():
    ap = argparse.ArgumentParser(description='CC-Eval 交付水印 v1.1（设计：于东兴）')
    sub = ap.add_subparsers(dest='cmd')
    e = sub.add_parser('embed')
    e.add_argument('--in', dest='infile', required=True)
    e.add_argument('--out', dest='outfile', required=True)
    e.add_argument('--mark', default='YDX', help='姓名缩写签名，如 YDX')
    e.add_argument('--tag', default='delivery', help='交付对象标签（区分批次）')
    x = sub.add_parser('extract')
    x.add_argument('--in', dest='infile', required=True)
    args = ap.parse_args()
    if args.cmd == 'embed':
        do_embed(args)
    elif args.cmd == 'extract':
        do_extract(args)
    else:
        ap.print_help()

if __name__ == '__main__':
    main()