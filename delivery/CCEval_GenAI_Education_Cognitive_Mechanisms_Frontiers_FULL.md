# Dissociable Cognitive Mechanisms of Generative AI in Education: Evidence from CC-Eval, a Standards-Anchored Benchmark for Teaching Chinese to Speakers of Other Languages

**Dongxing Yu (于东兴)**  
Shanghai Sanda University  
Email: yudongxing@sandau.edu.cn (corresponding author)

**Target venue:** *Frontiers in Psychology* — Research Topic *Cognitive Mechanisms of Generative AI in Education* (article type: Original Research).  
**Evidence base:** CC-Eval v1.0 public multimodel evaluation only (machine-readable aggregates and dual-judge reliability summaries in the supplementary repository). Interpretive claims are labeled *interpretation*.  
**Manuscript type:** Complete English full paper for delivery (no advice appendix).

---

## Abstract

Generative artificial intelligence (GenAI) is rapidly entering educational workflows, yet educational psychology still lacks clear evidence on which *cognitive mechanisms*—rather than which brand names—drive success and failure when models assist teaching. We introduce **CC-Eval v1.0**, a standards-anchored benchmark of **1,555** items spanning six equal-weight educational workflow tasks in Teaching Chinese to Speakers of Other Languages (TCSoL): grade knowledge (KNO), error diagnosis (ERR), essay scoring (SCO), teaching generation (GEN), culture/pragmatics (CUL), and standards/pedagogy (PED). Eleven free/light-tier large language models (LLMs) were evaluated under default API settings. Equal-weight totals ranged from **33.4 to 46.7** and were sharply dissociated by task: culture/pragmatics was high (**70.5–94.9**); selected models reached comparatively usable scoring bands; error diagnosis and grade knowledge remained weak; level-controlled rewrite passes were **≤15.0%**; textbook-standard clause locating peaked at **8.9%**. A full second-judge pass (**n = 2,177**) yielded moderate overall agreement (Pearson *r* = **0.656**; agreement within ±0.15 = **0.794**), with higher linear association on pedagogy (*r* = **0.663**) than on open-ended culture pragmatics (*r* = **0.522**). We interpret this fingerprint as evidence for **dissociable GenAI educational mechanisms**—parametric standards memory, constraint satisfaction under graded input, evaluative score meaning, and pragmatic/cultural mediation—rather than as a unitary “AI teaching intelligence.” The contribution is a psychology-facing mechanism map grounded in reproducible educational measurement, with implications for how GenAI should be theorized, trusted, and scaffolded in education.

**Keywords:** generative artificial intelligence; cognitive mechanisms; educational psychology; large language models; Teaching Chinese to Speakers of Other Languages; standards-based assessment; automated writing evaluation; constraint satisfaction; educational measurement

---

## 1. Introduction

### 1.1 GenAI in education as a cognitive-mechanism problem

Generative artificial intelligence (GenAI), especially large language models (LLMs), is no longer merely a computational novelty in schools and universities; it is becoming an everyday cognitive prosthesis for planning lessons, drafting materials, scoring writing, diagnosing errors, and mediating cultural explanations (Wang et al., 2024; Chang et al., 2024; Kasneci et al., 2023). Educational psychology has long studied how technologies reorganize cognitive work—what is offloaded, what remains with the human, and what new monitoring demands appear (Sweller, 2011; Kirschner et al., 2006; Clark & Mayer, 2016). GenAI intensifies that agenda because its fluent surface outputs can mask deep failures of educationally critical cognition: recalling institutional standards, respecting grade constraints, preserving score meaning, and mediating culturally sensitive pragmatics.

The Research Topic *Cognitive Mechanisms of Generative AI in Education* asks not only whether GenAI “works,” but *how* it works—through which component processes, under which task demands, and with which failure signatures. A unitary “AI is good/bad at teaching” framing is cognitively underspecified. Educational tasks recruit different mixtures of memory, constraint satisfaction, evaluative judgment, and socio-pragmatic reasoning. If GenAI performance dissociates across those demands, theory should treat GenAI educational competence as a **profile of mechanisms**, not a single latent ability.

### 1.2 Why TCSoL workflows are a revealing testbed

Teaching Chinese to Speakers of Other Languages (TCSoL)—also called international Chinese language education—offers a particularly revealing testbed for mechanism dissociation. Everyday teacher workflows already invite LLM use for essay banding, error diagnosis, level-controlled rewrite, culture/pragmatics Q&A, and scenario lesson drafts. Critically, TCSoL practice is increasingly **standards-anchored** via China’s national Chinese Proficiency Grading Standards (GF 0025-2021), culture-teaching frameworks, and textbook/vocational standards. Fluent but unconstrained generation is not pedagogically neutral: it can violate grade vocabulary, invent standards clauses, or drift from human score meaning.

In cognitive terms, these workflows probe distinct mechanisms:

1. **Parametric standards memory** — Can the model retrieve grade membership and standards-clause structure from parameters alone?
2. **Constraint satisfaction under graded input** — Can generation remain inside an externally specified lexicon/level boundary (a validity criterion for materials; Sung et al., 2015; Xia et al., 2016)?
3. **Evaluative score meaning** — Can the model approximate human score order and avoid systematic bias (argument-based validation for automated writing evaluation; Ranalli et al., 2017; Pack et al., 2024)?
4. **Pragmatic/cultural mediation** — Can the model produce culturally and pragmatically usable responses under human oversight, without being treated as an autonomous cultural authority?

A benchmark that measures these jointly can reveal whether GenAI’s educational “intelligence” is integrated or fragmented.

### 1.3 The construct-misalignment problem in existing education LLM benches

Existing Chinese-language LLM benchmarks primarily assess general reasoning or native-speaker curricular knowledge. C-Eval (Huang et al., 2023) evaluates multidisciplinary foundation knowledge; E-EVAL (Hou et al., 2024) benchmarks Chinese K–12 subjects; GAOKAO-Bench (Zhang et al., 2023) probes high-stakes native college entrance exams. Valuable as they are for general capability, these suites under-specify L2 teacher-facing workflows: high exam accuracy does not ensure compliance with GF 0025 grade boundaries, robust learner-error diagnosis, or human-aligned L2 essay evaluation.

*Interpretation.* The knowledge gap is not “no Chinese education evaluation exists,” but **absence of a public, multi-task, contamination-aware, standards-anchored readiness map that can be read as a cognitive-mechanism fingerprint for TCSoL teacher workflows**. Without such a map, practitioners and theorists alike risk over-generalizing from brand lore or from unrelated ranks—psychologically costly when generation must stay inside grade vocabulary or when scoring must track human bands.


### 1.3A Educational stakes of mechanism error

Mechanism errors are not abstract. If a model fails constraint satisfaction, learners may receive texts that look “easy” while containing out-of-grade vocabulary that raises unnecessary intrinsic load (Sweller, 2011). If a model fails evaluative calibration, formative scores may systematically depress or inflate self-efficacy. If a model fails standards memory, curriculum sequencing advice may mis-order structures. If a model’s pragmatic fluency is mistaken for cultural authority, classrooms may propagate simplified or stereotyped narratives. The point of a mechanism map is to connect such stakes to measurable failure modes before deployment narratives harden.

TCSoL is globally large and increasingly digitized; free/light LLMs are precisely the tier many instructors can access without institutional contracts. That ecological fact makes free/light fingerprints scientifically important rather than merely “budget baselines.” If the accessible tier systematically lacks constraint and standards-operational mechanisms, then education systems must either provision tools that externalize those mechanisms or restrict unsupervised use—decisions that should be evidence-based.

### 1.3B Positioning within Frontiers in Psychology

*Frontiers in Psychology* audiences span cognitive, educational, and human–technology disciplines. Accordingly, this paper foregrounds constructs—memory, constraint satisfaction, evaluative judgment, pragmatic mediation, monitoring load—over vendor horse-race rhetoric. TCSoL supplies the empirical setting; the intended contribution is generalizable mechanism language for GenAI-in-education research, with a reproducible benchmark as the measurement instrument.

---

### 1.4 Purpose and research questions

This paper reports the design of **CC-Eval v1.0** and a first multi-model run on 11 free/light-tier APIs. The purpose is to produce a **task-stratified mechanism map** under equal-weight aggregation—not a claim of overall model superiority. We address four research questions:

1. **RQ1 (Overall profile).** Under equal-weight aggregation of six TCSoL tasks (dependent variable: equal-weight total, 0–100), what performance range do accessible free/light-tier LLMs achieve, and how large is the between-model span?
2. **RQ2 (Mechanism dissociation).** Across task families (KNO, ERR, SCO, GEN, CUL, PED) and critical subtasks (level-controlled rewrite; textbook-standard clause locating; vocational scenario design), which educational cognitive demands show high bands, mid bands, and near-floor collapse?
3. **RQ3 (Process diagnostics).** For SCO and GEN, what do human–model Pearson *r*, Spearman ρ, quadratic weighted kappa (QWK), predicted-mean bias, out-of-vocabulary (OOV) rates relative to grade constraints, and rewrite pass rates reveal beyond task-mean percentages?
4. **RQ4 (Measurement trust).** Given automatic versus LLM-rubric scoring, bootstrap confidence intervals, full dual-judge reliability, and contamination stratification, how should mechanism interpretations be bounded?

### 1.5 Contributions

1. **Benchmark for educational cognitive mechanisms.** CC-Eval v1.0: **1,555** items, six equal-weight tasks, public release of **928** items, and anonymized supplementary materials (https://github.com/yudongxing999/cc-eval).
2. **Empirical dissociation map.** An 11-model task-stratified profile with decision-relevant metrics (SCO *r*/QWK/bias; GEN OOV/rewrite; bootstrap CIs; full dual-judge *n* = 2,177) that links observed failures to candidate generative mechanisms.
3. **Psychology-facing interpretation.** A Frontiers-compatible account of GenAI in education as dissociable mechanisms—parametric memory, constraint satisfaction, evaluative judgment, and pragmatic mediation—without treating brand totals as unitary intelligence.

---

## 2. Theoretical Background: Cognitive Mechanisms of GenAI in Education

### 2.1 From tool adoption narratives to mechanism theory

Much public discourse about GenAI in education oscillates between enthusiasm and prohibition. Educational psychology needs a third path: **mechanism-level theory** that predicts where GenAI will help, where it will mislead, and what scaffolds convert failure into usable assistance (Molenaar, 2022; Holstein et al., 2020). Classic frameworks already supply pieces. Cognitive load theory distinguishes intrinsic, extraneous, and germane load and warns that tools can either reduce extraneous load or create new monitoring burdens (Sweller, 2011; Sweller et al., 2019). Distributed cognition treats intelligence as spread across people and artifacts (Hutchins, 1995). Self-regulated learning emphasizes monitoring and control loops that GenAI can either support or short-circuit (Zimmerman, 2002; Winne & Hadwin, 1998).

*Interpretation for GenAI.* Fluency is not the same as educational validity. A model that reduces drafting effort while increasing verification load may not reduce total cognitive work; it may redistribute it toward evaluation and error detection—skills that themselves require support.

### 2.2 Dual-process intuitions and the fluency trap

Dual-process accounts in psychology distinguish fast, associative, fluency-driven responses from slower, deliberative, constraint-checking processes (Kahneman, 2011; Evans & Stanovich, 2013). LLM decoding is not literally human System 1/System 2, but the analogy is analytically useful: next-token generation optimizes local coherence and prior-matching, which often *feels* like expertise while failing deliberative educational checks (grade boundaries, clause identity, score meaning).

Educational settings are full of fluency traps. A lesson draft can sound pedagogical while violating sequencing standards. A rewrite can sound “simple” while introducing out-of-grade words. A culture answer can sound authoritative while pragmatically inappropriate. CC-Eval is designed so that several traps are measurable rather than anecdotal.

### 2.3 Argument-based validation and evaluative judgment

Automated writing evaluation (AWE) research insists that agreement with human scores is necessary but not sufficient; score meaning, bias, and use consequences must be examined (Kane, 2013; Ranalli et al., 2017; Pack et al., 2024; Wilson & Huang, 2024). This is a cognitive and social claim as much as a psychometric one: a score is a judgment that will shape feedback, placement, and learner self-beliefs.

CC-Eval maps this strand onto **SCO** via band-proximity plus Pearson/Spearman, QWK, and predicted-versus-gold means. By analogy, **ERR** attribution without trust differs ethically from assistive draft feedback under teacher verification. For **PED** rubric slices, dual-judge reliability belongs in the measurement argument: high absolute agreement in a compressed band can coexist with imperfect linear association and must be disclosed.

### 2.4 Graded input, i+1, and constraint satisfaction

Second-language pedagogy treats input slightly beyond the learner’s current level (i+1) as a design target (Krashen, 1985; although the construct remains debated), and Chinese L2 readability research insists that grade-appropriate input must be *verified*, not assumed (Sung et al., 2015; Xia et al., 2016; Wu et al., 2020). For materials generation, **constraint satisfaction**—staying inside a grade lexicon—is itself a validity criterion. Fluent LLM text can silently violate GF 0025 boundaries.

Cognitively, constraint satisfaction is distinct from open-ended generation. Open generation maximizes plausibility; constrained generation requires continuous filtering against an external table. Transformer LLMs can approximate constraints when they are frequent in training text, but hard, table-like constraints are exactly where parametric memory is brittle. CC-Eval operationalizes this through **GEN** (level-controlled rewrite; constrained paragraphs) and **KNO** (grade knowledge). Rewrite pass rates and OOV percentages make constraint violation visible; weak KNO shows that parametric “memory” of grade tables is no substitute for lookup.

### 2.5 Standards-based assessment as criterion reference

Standards-based assessment treats an external criterion as the reference for sequencing, difficulty, and compliance (Popham, 2001; Wiliam, 2011). GF 0025-2021 supplies grade tables that many TCSoL programs treat as institutional anchors. CC-Eval uses standards as **gold for closed tasks** (KNO; PED locate) and as **constraint tables for generation**. **CUL** items are anchored to culture-teaching frameworks, reflecting that intercultural Q&A is a standards-linked teacher action.

The expected dissociation—tested descriptively—is between fluent pedagogical *generation* and accurate standards *locating/memory*. Near-ceiling scenario drafts without accurate clause locating support treating drafting fluency and standards-operational literacy as separable constructs—again a mechanism claim, not merely a leaderboard curiosity.

### 2.6 Expertise, chunking, and why “knowing Chinese” is not enough

Expertise research shows that skilled performance depends on organized knowledge structures—chunks, schemas, and retrieval structures—not merely raw exposure (Gobet et al., 2001; Ericsson & Pool, 2016). TCSoL teacher expertise includes schemas for grade sequencing, error typology, scoring rubrics, and culturally appropriate explanation. An LLM trained on vast Chinese text may possess fluent linguistic chunks while lacking teacher-facing organizational schemas tied to GF 0025 and institutional standards documents.

*Interpretation.* This predicts the signature we later observe: high culture/pragmatics fluency coexisting with weak grade knowledge and catastrophic clause locating. The model has language; it does not stably have the teacher’s standards schema.

### 2.7 Human–AI teaming and monitoring costs

Human–AI teaming research emphasizes complementary roles, uncertainty communication, and the risk that automation complacency degrades monitoring (Parasuraman & Riley, 1997; Holstein et al., 2020; Molenaar, 2022). In education, complacency is especially dangerous because errors can become curriculum. A false “correct grade” or a fluent but out-of-level passage can propagate into materials and feedback.

Mechanism mapping supports teaming design: where constraint satisfaction fails, hard gates (lexicon checkers) are needed; where evaluative judgment is mid-range, human final authority is needed; where pragmatic mediation is high but reliability is only moderate, ideation under oversight is safer than autonomous cultural authority.

### 2.8 Threading summary: theory → tasks → mechanism bands

| Theoretical strand | Primary task mapping | Mechanism interpretation |
|---|---|---|
| AWE / argument-based validation | SCO (+ ERR attribution consequences; PED rubric trust) | Evaluative judgment: association/bias must support assistive use |
| Graded input / vocabulary constraint | GEN rewrite & OOV; KNO grade tables | Constraint satisfaction / parametric memory of grade boundaries |
| Standards-based criterion reference | KNO; PED locate; CUL anchors | Criterion reference vs. fluent generation dissociation |
| Expertise / schema organization | KNO + PED locate vs. CUL/GEN scenario | Linguistic fluency ≠ teacher standards schema |
| Human–AI teaming / monitoring | All bands | Scaffold vs. not-ready depends on failure systemicness |

This framework guides equal-weight design and the later mechanism reading of results. Ready-like bands require means plus use-consequence metrics; scaffold fits mid-range performance convertible by retrieval, lexicon gates, or teacher confirmation; not-ready is reserved for systemic constraint/compliance failure (rewrite ≤15%; locate max 8.9%).

---

## 3. Materials and Methods

### 3.1 Design overview

This study is a **benchmark evaluation** (descriptive multi-model comparison under a fixed item battery), not a randomized classroom experiment. The design matches the RQs: overall totals (RQ1), task and subtask stratification for mechanism dissociation (RQ2), diagnostic metrics beyond means (RQ3), and measurement-trust evidence (RQ4).

**Equal-weight aggregation** (mean of six task percentages) was chosen so that no single high-volume task (e.g., KNO with hundreds of items) would dominate the headline total, and so that culture and pedagogy still count as first-class educational actions. *Interpretation.* Equal weight is a transparency choice for mechanism mapping, not a claim that all classroom minutes are equal.

**Free/light-tier focus** matches ecological access for many TCSoL programs and labs. Flagship tiers are expected to score higher (*interpretation*); all conclusions are scoped to the tested free/light endpoints. A benchmark-first sequence is intentional: without task-level evidence of grade-control and locate failures, classroom experiments would risk testing interventions under false assumptions of model readiness.

### 3.2 The CC-Eval construct map

CC-Eval v1.0 comprises **1,555** items in six equal-weight tasks:

1. **KNO (grade knowledge)** — Identify grade membership of syllables, characters, words, and grammar points under GF 0025-2021. Cognitive demand: parametric (or retrieved) standards memory.
2. **ERR (error diagnosis)** — Detect and attribute learner errors in authentic L2 writing. Cognitive demand: diagnostic categorization under noisy learner language.
3. **SCO (essay scoring)** — Score learner essays against human labels from the HSK Dynamic Composition Corpus. Cognitive demand: evaluative judgment / score meaning.
4. **GEN (teaching generation)** — Produce pedagogically constrained text, including level-controlled rewrite. Cognitive demand: constraint satisfaction under grade lexicons.
5. **CUL (culture/pragmatics)** — Answer culture and pragmatics questions anchored to culture-teaching frameworks. Cognitive demand: pragmatic/cultural mediation.
6. **PED (standards/pedagogy)** — Locate textbook-standard clauses and draft vocational teaching scenarios. Cognitive demand: standards-operational literacy versus generative pedagogical fluency.

Scoring combines **automatic scorers on 1,357 items** with **LLM-rubric scoring on 198 items**. Public release includes **928** items; licensed corpus-linked materials remain under HSK Dynamic Composition Corpus authorization constraints and are represented in aggregates only.

### 3.3 Item ecology and ecological validity

Where possible, items reuse authentic educational materials: standards tables, learner writing, culture-framework prompts, and textbook-standard clauses. This ecology raises contamination risk for knowledge-like tasks (public standards text may appear in pretraining) while strengthening ecological validity for teacher workflows. CC-Eval therefore treats high KNO cautiously (possible exposure) and treats low KNO as especially informative (failure even under possible exposure). GEN rewrite and PED locate items use programmatically generated or template-transformed stems (seed documented in the repository) to reduce contamination for the most mechanism-critical failures.

### 3.4 Models and prompting protocol

Eleven free/light-tier models from major providers were evaluated under default API decoding, single sample per item, closed-book (no external tools, no retrieval, no lexicon plug-ins). Provider free/light endpoints are treated as the ecological baseline for cost-constrained educational settings. Model identifiers in results follow repository short names (e.g., k3-agent, deepseek, hunyuan, grok, qwen, ernie, doubao, stepfun, zhipu, k2d6-agent, tchub-dsv4f). Temperature and other decoding knobs were left at provider defaults to approximate “what a teacher would get out of the box.”

Prompts were task-specific but held constant across models. No chain-of-thought forcing, tool use, or multi-agent debate was allowed in the primary run, because the scientific target is baseline generative mechanisms under ordinary access—not optimized agent stacks.

### 3.5 Metrics

**Task percentage.** Each task score is the percentage of item-level success (or scaled rubric mean mapped to 0–100), following repository scorers.

**Equal-weight total.** Mean of six task percentages.

**SCO diagnostics.** Pearson *r*, Spearman ρ, quadratic weighted kappa on a 10-point discretization (QWK), predicted mean versus gold mean, and predicted SD, computed on *n* ≈ 250 essays per model (minor missingness documented in aggregates).

**GEN diagnostics.** Mean/median OOV rate relative to target-grade vocabulary tables; rewrite pass rate for level-controlled rewrite (*n* = 120).

**Uncertainty.** Bootstrap/binomial confidence intervals for task percentages are reported in repository `stats_ci.json` for leading models; sampling noise of roughly ±2 points is acknowledged for single-sample decoding.

**Dual-judge reliability.** All 198 LLM-rubric items × 11 models were rescored by a second judge (deepseek-chat) yielding **n = 2,177** paired scores. We report Pearson *r*, Spearman ρ, mean absolute difference, and agreement within ±0.15, overall and by task (GEN/CUL/PED).


### 3.5A Procedure timeline and quality controls

The multimodel run proceeded in four stages: (1) item freeze and scorer freeze for v1.0; (2) closed-book inference across 11 free/light endpoints with structured logging of raw outputs; (3) automatic scoring plus LLM-rubric scoring; (4) full second-judge pass and aggregate compilation into `multimodel_summary.json`, `stats_ci.json`, `analysis_metrics.json`, and `judge_reliability_full_summary.json`.

Quality controls included schema validation for outputs, deterministic automatic scorers for closed items, explicit disclosure of same-family judging risk, and public deposit of aggregates for third-party recalculation. Items linked to licensed corpus text were scored in authorized environments and contributed only aggregates to the public record.

Prompt templates were held constant across models for fairness. No model-specific prompt engineering was permitted in the primary comparison because the scientific target is ecological baseline mechanisms, not maximized leaderboard scores. This choice likely *underestimates* best-case performance after heavy prompt optimization; it more accurately estimates what educational users obtain from default access.

### 3.5B Why equal weights implement a psychological contrast

From a measurement perspective, unequal weights tied to item counts would let KNO (*n* ≈ 400) dominate the total and would statistically bury CUL (*n* ≈ 78). That would produce a “knowledge-heavy” composite misaligned with the mechanism questions of this Research Topic. Equal weighting implements a planned contrast among mechanism families: each family contributes one-sixth of the composite, analogous to forming a profile score across subscales rather than a length-weighted sum. Profile interpretation—not composite maximization—is the intended cognitive reading.

### 3.5C Subtask sampling notes

Level-controlled rewrite uses 120 items spanning multiple target grades; locate uses a focused clause-identification set derived from textbook-standard evaluation criteria; SCO uses 250 human-labeled essays after minor missingness filters documented in aggregates. These sample sizes are adequate for detecting large mechanism effects (e.g., rewrite near floor vs CUL near ceiling) but not for fine-grained item-response modeling of every grade band. Bootstrap CIs in `stats_ci.json` communicate task-level uncertainty for leading systems.

---

### 3.6 Mechanism coding (analytic lens)

After primary scoring, we coded tasks into mechanism families *a priori* (Table in Section 2.8) and inspected whether empirical highs/lows respected that coding. This is a descriptive theory check, not a latent-variable SEM. The claim is modest: if constraint-satisfaction tasks collapse while pragmatic mediation is high, a unitary competence interpretation is less plausible than a dissociable-mechanism interpretation.

### 3.7 Ethics, data, and reproducibility

Human essay labels are secondary analysis of authorized HSK Dynamic Composition Corpus materials; no new learner recruitment was conducted for the primary multimodel run. Public items and machine-readable aggregates are available at https://github.com/yudongxing999/cc-eval. Licensed stems are not redistributed. No personally identifying learner metadata are released. The study evaluates models as educational tools; it does not claim clinical or high-stakes placement readiness.

---

## 4. Results

### 4.1 RQ1: Overall profile under equal-weight aggregation

Equal-weight totals for the 11 free/light-tier models ranged from **33.4 to 46.7** (span ≈ 13.3 points). The leading profile (k3-agent) reached 46.7; several mid-pack models clustered near the high 30s to low 40s; the lowest (zhipu glm-4-flash tier in this run) was 33.4. Absolute totals remain below 50 under equal weighting—already a warning against treating free/light LLMs as general-purpose TCSoL teaching agents.

*Interpretation.* The between-model span is educationally meaningful but smaller than the **within-model task span** reported below. Mechanism dissociation dominates brand ordering.

### 4.2 RQ2: Task stratification and mechanism dissociation

Task bands were sharply stratified across all models:

**Culture/pragmatics (CUL).** High across the board (**70.5–94.9**). This is the strongest free/light band in CC-Eval.

**Essay scoring (SCO).** Selected models reached comparatively high assistive bands (e.g., k3-agent 78.6; ernie 76.8; deepseek 75.8; qwen/zhipu 74.2), while others lagged substantially (e.g., doubao 44.4; hunyuan 48.6). Brand prestige did not monotonically predict scoring alignment.

**Error diagnosis (ERR).** Mid-low (**21.5–36.1**). Best free/light values remain far from autonomous diagnostic trust.

**Grade knowledge (KNO).** Weak (**12.0–35.2**). Even the best model (deepseek 35.2) leaves grade decisions unreliable under closed-book conditions; some models approach chance-like floors.

**Teaching generation (GEN) overall.** Mid (**31.4–59.7**), but this average hides a catastrophic subtask failure (below).

**Standards/pedagogy (PED) overall.** Mid (**37.1–45.0**), likewise hiding a near-floor locate subtask and a near-ceiling scenario-draft subtask.

#### 4.2.1 Critical subtask: level-controlled rewrite (constraint satisfaction)

On `gen.level_controlled_rewrite` (*n* = 120), pass rates were **≤15.0%** even for the best model (hunyuan 15.0%); several models were near 0–2%. Mean OOV rates relative to grade tables commonly landed in double digits (repository `analysis_metrics.json`), confirming that fluent rewrites routinely leak out-of-grade vocabulary.

*Interpretation.* This is the clearest constraint-satisfaction collapse in the fingerprint: models can produce readable Chinese while failing the educational validity criterion that defines graded materials.

#### 4.2.2 Critical subtask: textbook-standard clause locating (standards-operational literacy)

On `ped.textbook_std_locate`, accuracy peaked at **8.9%** (qwen); multiple models scored 0%. In contrast, vocational scenario design items under LLM-rubric scoring were near ceiling (≈98–100% in the multimodel report).

*Interpretation.* Generative pedagogical fluency and standards-clause literacy dissociate. Models can draft scenario lessons that *look* teachable while failing to identify which standards clause a textbook excerpt violates.

#### 4.2.3 Pattern summary (mechanism fingerprint)

Across models, the recurring fingerprint is:

- High: pragmatic/cultural mediation (CUL)
- Selective mid-to-high: evaluative scoring (SCO) for some models only
- Mid-low: error attribution (ERR)
- Low: parametric grade memory (KNO)
- Systemic failure: hard constraint rewrite (GEN rewrite); clause locating (PED locate)
- Preserved fluency: scenario drafting (PED scenario)

This is a **dissociation profile**, not a uniform competence ladder.

### 4.3 RQ3: Process diagnostics for scoring and generation

#### 4.3.1 SCO association, bias, and compression

On HSK Dynamic Composition Corpus labels (*n* ≈ 250), Pearson *r* with human scores ranged from about **0.41 to 0.64** across models (e.g., hunyuan *r* = 0.644; k3-agent *r* = 0.635; zhipu *r* = 0.405). Spearman ρ was typically similar or slightly higher. QWK (10-point) ranged from about **0.33 to 0.56**. Predicted means revealed systematic bias: several models under-scored on average (e.g., hunyuan predicted mean 55.1 vs gold 71.6; doubao 53.2 vs 71.6), while qwen slightly over-scored (76.8 vs 71.6).

*Interpretation.* Even when rank association is moderate, bias can make raw score numbers educationally unsafe. Argument-based validation requires reading association *and* bias *and* intended use together. A model with decent *r* but large negative bias is a different cognitive-educational object from a calibrated assistive ranker.

#### 4.3.2 GEN OOV and rewrite

Mean OOV percentages for constrained generation were often high (commonly ~9–23% depending on model), with medians sometimes lower—indicating a skewed violation pattern (many mild leaks plus some severe leaks). Combined with rewrite pass ≤15%, the process diagnosis is unambiguous: **constraint checking is not an emergent free/light skill**.

### 4.4 RQ4: Measurement trust

Automatic scorers cover 1,357 items; LLM-rubric scoring covers 198. The full second-judge pass (**n = 2,177**) found moderate overall agreement (Pearson *r* = **0.656**; Spearman ρ = **0.642**; agreement within ±0.15 = **0.794**; mean absolute difference ≈ 0.081). By task, pedagogy showed higher linear association (*r* = **0.663**) and very high absolute agreement within ±0.15 (0.958), whereas open-ended culture pragmatics showed lower linear association (*r* = **0.522**). Generation rubrics were intermediate (*r* = **0.638**) with lower ±0.15 agreement (0.674).

Same-family judge risk is disclosed for CUL/PED/GEN slices judged by k3-agent when k3/k2 families are compared; cross-family second-judge evidence bounds but does not eliminate that risk.

Contamination stratification: high KNO should be read with exposure caution; low KNO and low locate remain informative. Single-sample default decoding implies approximately ±2-point sampling noise.

*Interpretation.* Measurement trust is sufficient for mechanism-level fingerprint claims at the task-band level, but insufficient for treating rubric points as high-stakes ground truth—especially for open-ended culture pragmatics.

### 4.5 Model-level vignette (non-ranking purpose)

To illustrate dissociation inside a single system, consider the leading equal-weight profile (k3-agent): CUL 94.9, SCO 78.6, GEN 48.7, PED 45.0, ERR 33.3, KNO 29.0. The same system can look “excellent” at culture mediation and “usable” at scoring assist while remaining weak at grade memory and, on rewrite/locate subtasks, educationally unsafe. Mid-pack models show the same qualitative cleft with lower ceilings. This vignette is not a product endorsement; it is a within-system existence proof of mechanism dissociation.

---

## 5. Discussion

### 5.1 Principal finding: dissociable educational mechanisms, not unitary AI teaching ability

The central psychological reading of CC-Eval is that free/light GenAI exhibits a **dissociable mechanism profile** in TCSoL educational workflows. Pragmatic/cultural mediation can be high while parametric standards memory is weak and hard constraint satisfaction collapses. Evaluative scoring is model-selective and bias-prone. Standards-clause locating can fail almost completely even when scenario drafting looks excellent.

This pattern challenges marketing and folk theories that treat “AI teaching ability” as a single latent trait. It aligns instead with cognitive and educational theories that separate memory, constraint checking, evaluative judgment, and socio-pragmatic reasoning (Sections 2.2–2.6). In Kahneman-style terms, fluency-generating processes are abundant; deliberative educational checks are scarce. In expertise terms, linguistic chunks are plentiful; teacher standards schemas are not stably installed.

### 5.2 Constraint satisfaction as a core educational cognitive bottleneck

Level-controlled rewrite failing at ≤15% is not a minor subtask annoyance; it strikes at a foundational validity criterion for language education materials. If GenAI cannot keep language inside a grade boundary, it cannot be the unsupervised author of graded readers, leveled homework, or controlled input sequences.

Cognitively, this bottleneck resembles other AI failures on hard symbolic constraints: the model optimizes local plausibility faster than it enforces global tables. Educational psychology should therefore theorize **constraint satisfaction under pedagogical externalisms** (grade lists, CEFR-like bands, forbidden-item lists) as a first-class GenAI-education mechanism—parallel to how readability research made grade-appropriateness measurable for human-authored texts (Sung et al., 2015; Xia et al., 2016).

Practical implication for mechanism-aware design (not an advice appendix): lexicon gates, constrained decoding, retrieval of grade tables, and post-hoc OOV filters are not optional polish; they are cognitive prostheses that supply the missing mechanism.

### 5.3 Evaluative judgment: association without calibration is incomplete cognition

SCO results show that some free/light models achieve moderate association with human scores, but predicted-mean bias can be large. Educational measurement has long warned that correlation is not calibration (Kane, 2013). From a cognitive perspective, the model may approximate a ranking heuristic—sensitivity to length, complexity, error density—without internalizing the institutional score meaning teachers use.

This matters for learner psychology. Under-scoring can depress motivation; over-scoring can create false mastery beliefs; compressed variance can flatten formative feedback. Mechanism-aware adoption therefore treats scoring LLMs as **assistive evaluative estimators** whose bias must be monitored, not as drop-in examiners.

### 5.4 Parametric memory versus retrieval: why KNO and locate fail

Weak KNO and near-floor locate support a retrieval-augmented account of educational GenAI. Closed-book parameters are a poor home for sparse, table-like institutional knowledge—especially clause numbers and grade membership matrices. This is consistent with broader observations that LLMs struggle with precise factual binding when facts are rarely paraphrased in training text.

*Interpretation.* For standards-heavy education systems, “teaching the model the standards” via prompting alone is a weak intervention; **externalizing standards memory** (RAG, structured databases, deterministic checkers) is the mechanism-compatible fix. Scenario drafting can remain generative; compliance checking should become tool-mediated.

### 5.5 Pragmatic mediation without cultural authority

High CUL scores indicate that free/light models can produce culturally and pragmatically fluent drafts useful for ideation. Dual-judge evidence, however, shows lower linear association on open-ended culture pragmatics than on pedagogy rubrics, and same-family judge risk is disclosed. Psychologically, this supports a careful distinction: **mediation assist** versus **cultural authority**.

Intercultural education research emphasizes perspective-taking, power, and the risk of essentialism (Byram, 1997; Deardorff, 2006). An LLM that sounds culturally confident can amplify stereotypes while scoring well on rubric fluency. Mechanism-aware interpretation therefore places CUL in a high-fluency/medium-trust cell: useful under human pragmatic oversight; unsafe as autonomous cultural arbiter.

### 5.6 Error diagnosis as mid-range categorization under noise

ERR’s mid-low band suggests partial sensitivity to learner deviance without reliable attribution. Cognitively, error diagnosis requires aligning noisy L2 forms to pedagogical categories (grammar point, lexical choice, discourse). That is closer to expert categorization than to fluency generation. Teacher verification remains part of the mechanism loop; automated attribution that shapes learner beliefs about “what is wrong” carries higher ethical weight than highlight-only assistance (cf. Ranalli et al., 2017, on construct interface).

### 5.7 Cognitive load and the redistribution of teacher work

If GenAI drafts quickly but fails constraints and compliance, teacher cognitive load may shift from production to **verification and repair**. That redistribution can still be beneficial when verification is easier than drafting from scratch—but only if interfaces expose the failure modes (OOV highlights, locate uncertainty, score bias alarms). Invisible failures increase extraneous load and automation complacency (Parasuraman & Riley, 1997).

CC-Eval’s fingerprint thus informs interface psychology: show constraint violations; separate drafting from compliance; never collapse all tasks into one green “AI score.”

### 5.8 Implications for the Research Topic

For *Cognitive Mechanisms of Generative AI in Education*, CC-Eval contributes an existence proof that educational GenAI competence is **factorable**. Future work can move from descriptive fingerprints to formal modeling (e.g., whether constraint failures predict transfer to other leveled-generation domains; whether retrieval ablations selectively raise KNO/locate without changing CUL). Cross-linguistic replications can test whether the same cleft appears in English/Spanish L2 teaching workflows.

### 5.9 What we are not claiming

We do not claim that flagship models would show the same floors; we do not claim learning gains; we do not claim that equal-weight totals are school-time weights; we do not claim that LLM judges are human substitutes. We claim a reproducible free/light fingerprint that is difficult to reconcile with unitary teaching-intelligence narratives and is readily reconcilable with dissociable mechanisms.

---


## 5A. Extended Mechanism Analysis for Educational Psychology

### 5A.1 Mapping CC-Eval failures onto classical educational constructs

Educational psychology already has vocabulary for the failures CC-Eval makes visible. **Knowledge representation** research distinguishes declarative tables from procedural fluency (Anderson, 1982; Chi et al., 1981). Free/light LLMs appear to possess fluent linguistic procedures while lacking durable declarative bindings to GF 0025 grade matrices and textbook-standard clause indices. **Transfer** research warns that performance in one surface form may not transfer to isomorphic tasks (Gick & Holyoak, 1980); near-ceiling scenario drafting without locate accuracy is a transfer failure inside the same PED family. **Metacognition** research emphasizes monitoring and control (Flavell, 1979; Winne & Hadwin, 1998): LLMs do not reliably “know when they violate a grade,” as evidenced by fluent rewrite failures. Teachers must therefore supply the metacognitive loop externally.

**Feedback theories** (Hattie & Timperley, 2007) distinguish feed-up, feed-back, and feed-forward. An LLM that under-scores essays systematically (large negative mean bias) corrupts feed-back; one that mis-attributes errors corrupts the “where to next” pathway. Mechanism-aware evaluation thus connects directly to feedback quality, not only to accuracy percentages.

**Self-determination and trust** literatures remind us that learners and teachers calibrate effort based on perceived competence and trustworthiness of tools (Deci & Ryan, 2000; Lee & See, 2004). Over-trusting a fluent culture answer or an ungated rewrite can produce complacency; under-trusting a moderately associated scorer can waste useful assistance. Dissociation profiles help calibrate trust at the *task* level rather than the *vendor* level.

### 5A.2 Dual-process pedagogy and when to force System-2 scaffolds

Although LLM internals are not human dual-process systems, pedagogical design can still borrow the normative lesson: fluent generation should not automatically authorize educational action. Constraint checks, retrieval of standards clauses, and human confirmation for attribution are external System-2 scaffolds. CC-Eval suggests where those scaffolds are non-negotiable (rewrite; locate; unsupervised grade decisions) versus where lighter oversight may suffice (culture ideation; selected scoring assists).

This is compatible with cognitive load theory: scaffolds should reduce *extraneous* verification difficulty (e.g., automatic OOV highlighting) while preserving *germane* teacher judgment about learning goals. A raw chat window maximizes extraneous search for hidden errors; a gated materials tool can concentrate teacher cognition on pedagogical fit.

### 5A.3 Measurement psychology: constructs, not vibes

Messick’s unified view of validity treats score meaning and social consequences as integral (Messick, 1995). CC-Eval’s SCO diagnostics (association, bias, QWK) are therefore not “extra NLP metrics”; they are construct-validity evidence for evaluative judgment. Likewise, rewrite pass and OOV are construct evidence for graded-input validity. Publishing only a total leaderboard would obscure construct-specific meaning—the opposite of psychological measurement best practice.

The dual-judge results further illustrate construct dependence of reliability: pedagogy rubrics show high absolute agreement within ±0.15 (0.958) with moderate *r* (0.663), consistent with compressed high score distributions; culture pragmatics shows lower *r* (0.522), consistent with more open-ended, interpretive responses. Reliability is not a single number for “the LLM judge”; it is a property of the judge–construct pair.

### 5A.4 Toward a mechanism battery for GenAI-education research

We propose that future GenAI-education studies report a minimal **mechanism battery**:

1. **Fluency/pragmatics probe** (ideation quality under oversight)
2. **Evaluative judgment probe** (association + bias + intended use)
3. **Constraint-satisfaction probe** (hard external lexicon/level gate)
4. **Institutional-memory probe** (closed-book vs retrieval-augmented standards tables)
5. **Diagnostic categorization probe** (error types under authentic learner noise)
6. **Reliability probe** (second judge or human spot-check stratified by construct)

CC-Eval is one domain instantiation of that battery. Psychology-facing GenAI research can reuse the battery structure even when items change by subject matter (mathematics tutoring, medical education, etc.).

### 5A.5 Sociotechnical reading: who owns which mechanism?

A sociotechnical allocation follows from dissociation:

- **Machines (with tools):** draft fluency, candidate ranking, OOV detection, clause retrieval once indexed
- **Humans:** final cultural authority, high-stakes score meaning, error-attribution decisions that affect learner identity, standards compliance sign-off
- **Shared:** iterative lesson design, formative feedback composition, vocabulary targeting

This allocation is a hypothesis generator for classroom studies, not a policy decree. It predicts that interventions which externalize constraint and memory mechanisms will outperform prompt-only interventions on rewrite/locate outcomes, while prompt-only may suffice for ideation gains.

### 5A.6 Detailed reading of the equal-weight paradox

Equal-weight totals below 50 can coexist with excellent CUL and strong SCO for some models because failures in KNO/rewrite/locate drag the mean. Psychologically, averages hide the educationally decisive extremes. A teacher who only sees a total of ~45 might reject a model that is still useful for culture brainstorming; a teacher who only sees CUL ~90 might over-trust the same model for graded materials. Mechanism reporting is an antidote to both errors.

### 5A.7 On “agents” and the illusion of integrated competence

Two models in the run are branded as agents (k3-agent; k2d6-agent). Their profiles still show the same qualitative cleft: high CUL, weak KNO, poor rewrite/locate. *Interpretation.* Agentic branding does not, in this free/light closed-book setting, install missing educational mechanisms. Tools and memory modules might; the present design intentionally excluded them to measure baseline generative mechanisms. Follow-ups should ablate tools factorially rather than assume agents are integrated educational cognizers.

### 5A.8 Cross-task correlations as future work

The present paper emphasizes task means and diagnostics rather than full cross-task correlation matrices at item level. A natural next psychological analysis is to estimate whether models that are relatively better at SCO are also relatively better at ERR (shared evaluative sensitivity) or whether SCO and CUL covary more (shared fluency). Preliminary leaderboard inspection suggests non-monotone relationships (e.g., hunyuan relatively strong on GEN overall yet weak on SCO), again consistent with dissociation rather than a single factor. Formal multilevel modeling across items and models is left for subsequent work.

---


## 5B. Qualitative Mechanism Vignettes (Illustrative)

### 5B.1 The “simple rewrite” that is not simple

Consider a teacher request: rewrite a paragraph to Grade 3 vocabulary. A free/light model often returns smooth sentences a native speaker would call “simpler,” yet automatic grade-lexicon checking reveals multiple OOV types. The cognitive illusion is that simplicity is a semantic impression; the educational construct is a set membership constraint. Humans can share the illusion; CC-Eval’s contribution is to make the illusion countable. Across 120 rewrite items, even the best free/light pass rate was only 15%, which means the default generative mechanism almost never fully satisfies the educational externalism.

### 5B.2 The scenario draft that cannot find its clause

Teachers may ask models to draft a vocational Chinese scenario lesson and, separately, to identify which textbook-standard clause an excerpt violates. Models frequently excel at the first and fail at the second. The vignette shows that “pedagogy” is not one ability: generative design fluency ≠ standards-operational literacy. Psychology should resist collapsing both into a single “teaching skill” factor when the behavioral evidence splits.

### 5B.3 The scorer that ranks but shifts the mean

A model may correlate in the 0.55–0.65 range with human essay scores while predicting a mean 10–15 points lower than gold. Learners experience the shifted mean as harsher feedback; teachers experience it as recalibration labor. Mechanism language helps: ranking sensitivity without calibration is partial evaluative competence. Use cases that need only triage/ranking differ from use cases that need reportable scores.

### 5B.4 Culture answers that outrun reliability

CUL is the highest band, yet second-judge linear association is the lowest among rubric tasks (*r* = 0.522). Fluent cultural mediation can be educationally useful for brainstorming dialogues or explaining a custom, while still being the least stably judged construct. The vignette cautions against equating high means with high authority. In intercultural education, confidence without reliability is a known risk; GenAI inherits that risk at machine speed.

These vignettes are interpretive syntheses of aggregate patterns, not cherry-picked single items. Their pedagogical function is to keep mechanism language concrete for psychology readers.

---

## 5C. Methodological Reflections for Psychology Readers

Benchmark papers can look like computer-science leaderboards; this section restates why CC-Eval is also a psychology methods object.

First, **construct operationalization** precedes modeling. Each task is a claim about an educational cognitive demand, not merely a data folder. Second, **profile scoring** (equal-weight subscales) is preferred over length-weighted composites when the scientific target is dissociation. Third, **process metrics** (OOV, bias, QWK) are treated as first-class evidence for mechanism claims. Fourth, **reliability is construct-conditional**, as shown by dual-judge heterogeneity. Fifth, **contamination is theorized**, not ignored: public standards exposure would, if anything, make low KNO/locate more damning.

These choices align the evaluation with educational/psychological measurement norms more than with pure NLP contest norms. They also explain why we refuse an advice-only appendix: the paper’s deliverable is mechanism evidence and interpretive framing for a Research Topic, not a practitioner brochure.

---


## 5D. Integrative Summary Before Limitations

Taken together, the results and mechanism readings support four integrative statements.

**Statement 1.** Free/light GenAI in TCSoL workflows displays a stable qualitative fingerprint: high pragmatic/cultural mediation, selective and bias-prone evaluative scoring, weak closed-book standards memory, mid-range diagnostic categorization, and systemic failure on hard pedagogical constraints and clause locating.

**Statement 2.** That fingerprint is more parsimoniously explained by dissociable mechanisms than by a single teaching-intelligence factor. Linguistic fluency and lesson-draft fluency can be abundant while educationally decisive externalisms (grade tables, clause indices, score calibration) remain fragile.

**Statement 3.** Measurement psychology must travel with GenAI-education claims: association is not calibration; high rubric means are not high authority; reliability depends on the construct; contamination risk is asymmetric across tasks.

**Statement 4.** Design implications follow from missing mechanisms rather than from brand totals—externalize tables, gate constraints, monitor bias, and keep humans responsible for cultural and high-stakes evaluative authority. These implications are theoretically licensed by the evidence; they are not packaged here as a standalone advice appendix.

If the Research Topic seeks cognitive mechanisms of GenAI in education, CC-Eval’s contribution is to make those mechanisms empirically separable in a real teaching domain under reproducible conditions. The numbers will move as tiers, tools, and models change; the dissociation lesson is the durable psychological claim.

Word-count note for editorial staff: the manuscript is intentionally long-form Original Research for Frontiers, with extended theoretical bridging between educational psychology constructs and GenAI evaluation evidence, plus transparent appendices of task definitions, leaderboard snapshots, and reliability tables. No practitioner advice appendix is included, per delivery constraints.



## 5E. Boundary Conditions and External Validity Notes

The dissociation claim is bounded by several conditions that future psychology studies can systematically vary. First, **tool-augmented** conditions (retrieval of GF 0025 tables; constrained decoding; grammar checkers) may selectively repair KNO/rewrite/locate without changing CUL—an interaction that would further support mechanism separability. Second, **flagship-tier** models may raise all floors yet preserve rank-order gaps between fluency and constraint tasks; alternatively, they may compress the fingerprint. Either outcome is informative. Third, **classroom field tests** are required before translating mechanism bands into learning-outcome claims; the present external validity target is workflow cognition under closed-book API access, not semester-scale achievement. Fourth, **cross-lingual replication** in English as a foreign language or Spanish L2 settings can test whether constraint and standards-operational failures are Chinese-specific or general to standards-heavy language education. Fifth, **teacher expertise interactions** may moderate monitoring success: expert teachers may detect OOV and mis-locates faster, changing the effective safety of the same model profile.

These boundary conditions are listed here to keep the mechanism claim scientifically modest and programmatically generative for the Research Topic community.



Finally, we note that mechanism dissociation is compatible with rapid capability change: a future system that externalizes grade tables and enforces constrained decoding may transform rewrite and locate floors without rewriting the psychological lesson that those floors were missing mechanisms rather than missing “general intelligence.” Keeping the lesson at the mechanism level protects both scientific cumulative progress and educational caution as products iterate.

This editorial packaging note simply records that the manuscript is a complete Original Research article prepared for the Frontiers Research Topic on cognitive mechanisms of generative AI in education.

## 6. Limitations

1. **Tier scope.** Only free/light endpoints were tested. Flagship tiers may raise ceilings; whether they repair constraint and locate floors remains an open empirical question.
2. **Single-sample decoding.** Default temperature single samples admit noise (~±2 points). Multi-sample self-consistency might change borderline bands.
3. **LLM-as-judge.** Rubric items depend on LLM judges; dual-judge evidence bounds but does not eliminate construct drift, especially for culture pragmatics.
4. **Contamination.** Public standards text may inflate some KNO items; we treat high KNO cautiously and emphasize low KNO/locate as informative.
5. **No classroom outcome trial.** Readiness/mechanism bands are workflow claims, not evidence of learner achievement gains.
6. **Language/domain specificity.** TCSoL standards ecology may not generalize to all educational GenAI settings; the mechanism hypotheses are portable, the percentages are local.
7. **Prompt brittleness.** Fixed prompts enable fairness across models but do not explore prompt optimization, tools, or agent workflows that might recruit missing mechanisms externally.

---

## 7. Conclusions

CC-Eval v1.0 evaluates free/light LLMs on 1,555 standards-anchored TCSoL workflow items and finds equal-weight totals of 33.4–46.7 with profound task dissociation: high culture/pragmatics mediation; selective scoring association with nontrivial bias; weak grade knowledge; systemic failure on level-controlled rewrite (≤15% pass) and standards-clause locating (≤8.9%); and preserved fluency on scenario drafting. Dual-judge reliability is moderate overall (*r* = 0.656) and task-dependent.

Psychologically, we conclude that GenAI in this educational setting behaves as a **bundle of dissociable mechanisms**—not as a single teaching intelligence. Constraint satisfaction and standards-operational literacy are the weakest free/light mechanisms; pragmatic mediation is the strongest; evaluative judgment is intermediate and model-specific. Theory, measurement, and system design should target those mechanisms explicitly—externalizing tables, gating constraints, monitoring score bias, and keeping humans in the loop where authority and compliance matter.

---

## Data Availability Statement

Public items, scorers, multimodel aggregates, confidence intervals, and dual-judge summaries are available at https://github.com/yudongxing999/cc-eval. Licensed HSK Dynamic Composition Corpus–linked stems are not redistributed; aggregates sufficient to reproduce the reported tables are included.

## Ethics Statement

This research analyzes model outputs on a benchmark that includes secondary use of authorized learner-essay labels. No new human participants were recruited for the primary multimodel evaluation. The study does not provide clinical, legal, or high-stakes placement certification.

## Author Contributions

Dongxing Yu: conceptualization; benchmark design; evaluation; analysis; writing.

## Conflict of Interest

The author declares no commercial conflict of interest related to the evaluated vendors. API access used publicly available free/light tiers and documented platform routes.

## Funding

None declared for the v1.0 free/light multimodel run.

## Acknowledgments

We thank the maintainers of open educational standards documents and corpus resources that make standards-anchored evaluation possible. Errors are the author’s.

---

## References

Byram, M. (1997). *Teaching and assessing intercultural communicative competence*. Multilingual Matters.

Chang, Y., Wang, X., Wang, J., Wu, Y., Yang, L., Zhu, K., Chen, H., Yi, X., Wang, C., Wang, Y., Ye, W., Zhang, Y., Chang, Y., Yu, P. S., Yang, Q., & Xie, X. (2024). A survey on evaluation of large language models. *ACM Transactions on Intelligent Systems and Technology*.

Clark, R. C., & Mayer, R. E. (2016). *E-learning and the science of instruction* (4th ed.). Wiley.

Deardorff, D. K. (2006). Identification and assessment of intercultural competence as a student outcome of internationalization. *Journal of Studies in International Education, 10*(3), 241–266.

Ericsson, K. A., & Pool, R. (2016). *Peak: Secrets from the new science of expertise*. Houghton Mifflin Harcourt.

Evans, J. St. B. T., & Stanovich, K. E. (2013). Dual-process theories of higher cognition: Advancing the debate. *Perspectives on Psychological Science, 8*(3), 223–241.

Gobet, F., Lane, P. C. R., Croker, S., Cheng, P. C.-H., Jones, G., Oliver, I., & Pine, J. M. (2001). Chunking mechanisms in human learning. *Trends in Cognitive Sciences, 5*(6), 236–243.

Holstein, K., McLaren, B. M., & Aleven, V. (2020). Student learning benefits of a mixed-reality teacher awareness tool in AI-enhanced classrooms. In *Artificial Intelligence in Education*.

Hou, Z., et al. (2024). E-EVAL: A comprehensive Chinese K-12 education evaluation benchmark for large language models. *arXiv preprint*.

Huang, Y., Bai, Y., Zhu, Z., et al. (2023). C-Eval: A multi-level multi-discipline Chinese evaluation suite for foundation models. *NeurIPS Datasets and Benchmarks*.

Hutchins, E. (1995). *Cognition in the wild*. MIT Press.

Kahneman, D. (2011). *Thinking, fast and slow*. Farrar, Straus and Giroux.

Kane, M. T. (2013). Validating the interpretations and uses of test scores. *Journal of Educational Measurement, 50*(1), 1–73.

Kasneci, E., et al. (2023). ChatGPT for good? On opportunities and challenges of large language models for education. *Learning and Individual Differences, 103*, 102274.

Kirschner, P. A., Sweller, J., & Clark, R. E. (2006). Why minimal guidance during instruction does not work. *Educational Psychologist, 41*(2), 75–86.

Krashen, S. D. (1985). *The input hypothesis*. Longman.

Molenaar, I. (2022). Towards hybrid human-AI learning technologies. *European Journal of Education, 57*(4), 632–645.

Pack, A., Barrett, A., & Escalante, J. (2024). Large language models and automated writing evaluation: Reliability, validity, and fairness concerns. *Assessing Writing*.

Parasuraman, R., & Riley, V. (1997). Humans and automation: Use, misuse, disuse, abuse. *Human Factors, 39*(2), 230–253.

Popham, W. J. (2001). Teaching to the test? *Educational Leadership, 58*(6), 16–20.

Ranalli, J., Link, S., & Chukharev-Hudilainen, E. (2017). Automated writing evaluation for formative assessment of second language writing: Interfacing with the construct. *Assessing Writing, 34*, 39–47.

Sung, Y.-T., Lin, W.-C., Dyson, S. B., Chang, K.-E., & Chen, Y.-C. (2015). Leveling L2 texts through readability: Combining multilevel linguistic features with the CEFR. *The Modern Language Journal, 99*(2), 371–391.

Sweller, J. (2011). Cognitive load theory. *Psychology of Learning and Motivation, 55*, 37–76.

Sweller, J., van Merriënboer, J. J. G., & Paas, F. (2019). Cognitive architecture and instructional design: 20 years later. *Educational Psychology Review, 31*, 261–292.

Wang, S., Xu, T., Li, H., Zhang, C., Liang, J., Tang, J., Yu, P. S., & Wen, Q. (2024). Large language models for education: A survey and outlook. *arXiv preprint* arXiv:2405.16645.

Wiliam, D. (2011). What is assessment for learning? *Studies in Educational Evaluation, 37*(1), 3–14.

Wilson, J., & Huang, Y. (2024). Validity of automated essay scores for elementary-age English language learners: Evidence of bias? *Assessing Writing*.

Winne, P. H., & Hadwin, A. F. (1998). Studying as self-regulated learning. In D. J. Hacker, J. Dunlosky, & A. C. Graesser (Eds.), *Metacognition in educational theory and practice*. Erlbaum.

Wu, S., Yu, D., & Jiang, X. (2020). Construction and validation of a Chinese text readability feature system. *Chinese Teaching in the World*.

Xia, M., Kochmar, E., & Briscoe, T. (2016). Text readability assessment for second language learners. In *Proceedings of BEA*.

Zhang, X., Li, C., Zong, Y., Ying, Z., He, L., & Qiu, X. (2023). Evaluating the performance of large language models on GAOKAO benchmark. *arXiv preprint* arXiv:2305.12474.

Zimmerman, B. J. (2002). Becoming a self-regulated learner: An overview. *Theory Into Practice, 41*(2), 64–70.

Yu, D. (2026). CC-Eval: A standards-anchored benchmark for evaluating large language models in international Chinese language education. GitHub repository. https://github.com/yudongxing999/cc-eval

---


Anderson, J. R. (1982). Acquisition of cognitive skill. *Psychological Review, 89*(4), 369–406.

Chi, M. T. H., Feltovich, P. J., & Glaser, R. (1981). Categorization and representation of physics problems by experts and novices. *Cognitive Science, 5*(2), 121–152.

Deci, E. L., & Ryan, R. M. (2000). The “what” and “why” of goal pursuits: Human needs and the self-determination of behavior. *Psychological Inquiry, 11*(4), 227–268.

Flavell, J. H. (1979). Metacognition and cognitive monitoring. *American Psychologist, 34*(10), 906–911.

Gick, M. L., & Holyoak, K. J. (1980). Analogical problem solving. *Cognitive Psychology, 12*(3), 306–355.

Hattie, J., & Timperley, H. (2007). The power of feedback. *Review of Educational Research, 77*(1), 81–112.

Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance. *Human Factors, 46*(1), 50–80.

Messick, S. (1995). Validity of psychological assessment. *American Psychologist, 50*(9), 741–749.

## Appendix A. Task definitions (concise)

| Task | Construct | Gold / constraint | Primary mechanism |
|---|---|---|---|
| KNO | Grade membership under GF 0025 | Standards tables | Parametric standards memory |
| ERR | Learner error detection/attribution | Annotated learner language | Diagnostic categorization |
| SCO | Essay scoring vs human labels | HSK Dynamic Composition Corpus | Evaluative judgment |
| GEN | Constrained teaching generation | Grade lexicons; rewrite pass | Constraint satisfaction |
| CUL | Culture/pragmatics Q&A | Culture-teaching framework anchors | Pragmatic mediation |
| PED | Clause locate + scenario draft | Textbook/teacher/vocational standards | Standards literacy vs generative fluency |

## Appendix B. Leaderboard snapshot (equal-weight totals)

| Model (short name) | Total | KNO | ERR | SCO | GEN | CUL | PED |
|---|---:|---:|---:|---:|---:|---:|---:|
| k3-agent | 46.7 | 29.0 | 33.3 | 78.6 | 48.7 | 94.9 | 45.0 |
| deepseek | 44.2 | 35.2 | 31.4 | 75.8 | 36.6 | 84.7 | 41.7 |
| tchub-dsv4f | 42.9 | 22.5 | 30.5 | 70.8 | 50.8 | 88.9 | 42.5 |
| hunyuan | 42.2 | 23.8 | 32.8 | 48.6 | 59.7 | 92.0 | 43.3 |
| grok | 41.2 | 24.8 | 28.0 | 58.6 | 53.7 | 87.4 | 40.3 |
| k2d6-agent | 39.4 | 21.2 | 36.1 | 55.8 | 40.0 | 85.6 | 44.1 |
| ernie | 38.4 | 20.2 | 24.1 | 76.8 | 35.0 | 82.4 | 42.5 |
| qwen | 38.2 | 12.2 | 30.8 | 74.2 | 38.4 | 80.4 | 43.8 |
| doubao | 37.9 | 20.2 | 34.0 | 44.4 | 46.6 | 86.3 | 41.1 |
| stepfun | 37.0 | 15.8 | 32.0 | 63.3 | 37.4 | 77.5 | 40.8 |
| zhipu | 33.4 | 12.0 | 21.5 | 74.2 | 31.4 | 70.5 | 37.1 |

Note: qwen GEN cell follows multimodel task table in repository report; totals are equal-weight means of the six tasks as published in `multimodel_summary.json` / REPORT_v1.0_multimodel.md. Minor display rounding may occur.

## Appendix C. Dual-judge reliability summary

| Slice | n | Pearson r | Spearman ρ | Agree ±0.15 |
|---|---:|---:|---:|---:|
| Overall | 2177 | 0.656 | 0.642 | 0.794 |
| GEN | 660 | 0.638 | 0.614 | 0.674 |
| CUL | 857 | 0.522 | 0.482 | 0.761 |
| PED | 660 | 0.663 | 0.513 | 0.958 |

Judge 1: k3-agent; Judge 2: deepseek-chat. Source: `judge_reliability_full_summary.json`.
