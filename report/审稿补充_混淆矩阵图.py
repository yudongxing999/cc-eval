# -*- coding: utf-8 -*-
"""意见5：混淆矩阵热力图（未见词条 n=1,000，行=金标等级，列=模型预测）
投稿稿正文版：黑白灰阶（期刊印刷友好），行百分比归一。
"""
import json, os
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 混淆矩阵（与 report/审稿补充_混淆矩阵.md 同源：preds_heldout.json）
d = json.load(open(os.path.join(ROOT, 'injection/preds_heldout.json'), encoding='utf-8'))
LV = ['1', '2', '3', '4', '5', '6', '7-9']
cm = np.zeros((7, 7))
for r in d:
    cm[r['gold'], r['pred']] += 1

# 行归一（每个金标等级的预测去向）
cmn = cm / cm.sum(axis=1, keepdims=True) * 100

fig, ax = plt.subplots(figsize=(7.2, 5.6))
im = ax.imshow(cmn, cmap='Greys', vmin=0, vmax=100, aspect='auto')

for i in range(7):
    for j in range(7):
        v = cmn[i, j]
        text_color = 'white' if v > 55 else 'black'
        ax.text(j, i, f'{cm[i,j]:.0f}\n({v:.0f}%)', ha='center', va='center',
                fontsize=9, color=text_color)

ax.set_xticks(range(7))
ax.set_xticklabels(LV, fontsize=11)
ax.set_yticks(range(7))
ax.set_yticklabels(LV, fontsize=11)
ax.set_xlabel('模型预测等级', fontsize=12)
ax.set_ylabel('GF 0025 金标等级', fontsize=12)
ax.set_title('未见词条定级的混淆矩阵（n=1,000，行百分比）', fontsize=12)

cbar = fig.colorbar(im, ax=ax, shrink=0.85)
cbar.set_label('行百分比 (%)', fontsize=10)

plt.tight_layout()
out = os.path.join(ROOT, 'report/审稿补充_混淆矩阵图.png')
fig.savefig(out, dpi=200, facecolor='white')
print('保存:', out)

# 附：多数类基线的混淆矩阵对照（全猜 7-9）
cm2 = np.zeros((7, 7))
for r in d:
    cm2[r['gold'], 6] += 1
print('注：多数类基线的列合计只有 7-9 一列非零（全猜 7-9），论文中以文字表述即可，不需第二张图。')