# Full second-judge reliability (v1.0 llm_rubric)

- **Date:** 2026-09-16
- **Judge1:** k3-agent (scores already stored in `results/<model>/*.json`)
- **Judge2:** deepseek-chat (independent family)
- **Coverage:** n=**2177** pairs = **198/198** unique llm_rubric items × 11 models (deepseek missing 1 item)
- **Failures:** 0
- **Script:** `runner/judge_reliability_full.py` (checkpointed)

## Overall

| Metric | Value |
|---|---:|
| Pearson r | **0.6562** |
| Spearman rho | **0.6423** |
| Agreement within ±0.15 | **0.7942** |
| Mean abs. diff. | **0.0808** |
| k3 mean | 0.881 |
| judge2 mean | 0.874 |

Compare prior samples: n=30 r≈0.219; n=120 r≈0.520. Full-population r is higher and means nearly unbiased.

## By task

| Task | n | Pearson r | Spearman | Agree±0.15 | MAD | k3 mean | j2 mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| GEN | 660 | 0.6378 | 0.6135 | 0.6742 | 0.1141 | 0.8277 | 0.8570 |
| CUL | 857 | 0.5216 | 0.4817 | 0.7608 | 0.0981 | 0.8461 | 0.8147 |
| PED | 660 | 0.6631 | 0.5129 | 0.9576 | 0.0252 | 0.9795 | 0.9680 |

## Same-family note (CUL)

k3-agent CUL: k3 mean 0.949 vs j2 0.931 (bias +0.018). k2d6 CUL: 0.856 vs 0.817 (bias +0.038). Mild positive bias, smaller than the earlier 5–10 point caution on the equal-weight % scale, but still relevant for interpreting top CUL ranks.

## Artifacts

- Full pairs: `results/judge_reliability_full.json`
- Metrics only: `results/judge_reliability_full_summary.json`
- Checkpoint: `results/judge_reliability_full.checkpoint.jsonl`
