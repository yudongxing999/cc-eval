import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, Header, HeadingLevel, ImportedXmlComponent,
  Packer, PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType, convertInchesToTwip,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node create.js /abs/out.docx");
fs.mkdirSync(path.dirname(outputPath), { recursive: true });

const T = String.raw;
const palette = { dark: "263238", primary: "37474F", light: "78909C", fill: "EEF3F6", accent: "00695C" };
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };

const run = (text, options = {}) => new TextRun({ text, font, size: 24, ...options });
const para = (children, options = {}) => new Paragraph({
  spacing: { after: 160, line: 300 }, ...options,
  children: Array.isArray(children) ? children : [children],
});
const bodyPara = (text, options = {}) =>
  para(run(text), { indent: { firstLine: convertInchesToTwip(0.33) }, ...options });
const heading = (text, level = 1) =>
  para(run(text, { bold: true, size: level === 1 ? 30 : 26, color: palette.dark }), {
    heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 140 },
  });
const bullet = (text) =>
  para(run(text), { bullet: { level: 0 }, spacing: { after: 100, line: 300 } });

const cell = (text, options = {}) => new TableCell({
  children: [para(run(text, { size: 20 }), { spacing: { after: 0, line: 260 } })],
  margins: { top: 80, bottom: 80, left: 100, right: 100 },
  ...options,
});

const makeTable = (widths, headerRow, dataRows) => {
  const total = widths.reduce((a, b) => a + b, 0);
  const mkRow = (rowData, isHeader) => new TableRow({
    children: rowData.map((c, i) => cell(String(c), {
      width: { size: widths[i], type: WidthType.DXA },
      ...(isHeader ? { shading: { type: ShadingType.CLEAR, fill: palette.fill } } : {}),
    })),
  });
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [mkRow(headerRow, true), ...dataRows.map((r) => mkRow(r, false))],
  });
};

const xmlEscape = (v) => String(v)
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level, page }) => {
    const indent = Math.max(0, level - 1) * 360;
    return `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/>
      <w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs>
      <w:ind w:left="${indent}"/></w:pPr>
      <w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`;
  }).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:sdtPr><w:alias w:val="目录"/></w:sdtPr>
    <w:sdtContent>
      <w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/>
        <w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText>
        <w:fldChar w:fldCharType="separate"/></w:r></w:p>
      ${cached}
      <w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
    </w:sdtContent>
  </w:sdt>`).root[0];
};

// ==================== 数据 ====================
const leaderboard = [
  ["1", "Kimi k3-agent（月之暗面）", "46.7", "29.0", "33.3", "78.6", "48.7", "94.9", "45.0"],
  ["2", "deepseek-chat（DeepSeek）", "44.2", "35.2", "31.4", "75.8", "36.6", "84.7", "41.7"],
  ["3", "deepseek-v4-flash（腾讯TokenHub）", "42.9", "22.5", "30.5", "70.8", "50.8", "88.9", "42.5"],
  ["4", "hy3（腾讯混元）", "42.2", "23.8", "32.8", "48.6", "59.7", "92.0", "43.3"],
  ["5", "grok-3-mini-fast（xAI）", "41.2", "24.8", "28.0", "58.6", "53.7", "87.4", "40.3"],
  ["6", "Kimi k2d6-agent（月之暗面）", "39.4", "21.2", "36.1", "55.8", "40.0", "85.6", "44.1"],
  ["7", "ernie-4.5-turbo（百度）", "38.4", "20.2", "24.1", "76.8", "35.0", "82.4", "42.5"],
  ["8", "qwen-flash（阿里）", "38.2", "12.2", "30.8", "74.2", "38.4", "80.4", "43.8"],
  ["9", "doubao-seed-1-6（字节跳动）", "37.9", "20.2", "34.0", "44.4", "46.6", "86.3", "41.1"],
  ["10", "step-3.7-flash（阶跃星辰）", "37.0", "15.8", "32.0", "63.3", "37.4", "77.5", "40.8"],
  ["11", "glm-4-flash（智谱）", "33.4", "12.0", "21.5", "74.2", "31.4", "70.5", "37.1"],
];

const taskDesign = [
  ["KNO", "等级知识：判断音节/汉字/词汇/语法点在三等九级中的级别", "400", "GF 0025-2021 音节、汉字、词汇、语法四张等级表"],
  ["ERR", "偏误识别与纠正：指出学习者语句的偏误类型并改正", "377", "HSK 动态作文语料库偏误标注"],
  ["SCO", "作文评分对齐：为学习者作文打分并对齐人工分数", "250", "HSK 动态作文语料库人工评分"],
  ["GEN", "教学生成：限级改写、给词成段、语法点造句", "300", "词表约束程序化构造（新编，防污染）"],
  ["CUL", "文化国情与语用推理", "78", "《国际中文教育用中国文化和国情教学参考框架》"],
  ["PED", "标准条文定位与场景化教学设计", "150", "教材评价标准 / 教师专业能力标准 / 职业中文能力等级标准"],
];

const rewriteTable = [
  ["混元 hy3", "15.0%"], ["Kimi k3-agent", "8.3%"], ["grok-3-mini-fast", "5.8%"],
  ["deepseek-v4-flash", "4.2%"], ["豆包 doubao-seed-1-6", "2.5%"], ["智谱 glm-4-flash", "1.7%"],
  ["ernie / qwen / stepfun", "0.8%"], ["k2d6-agent / deepseek-chat", "0.0%"],
];

const tocEntries = [
  { title: T`一、项目背景与问题定位`, level: 1, page: 2 },
  { title: T`二、总体设计思路`, level: 1, page: 3 },
  { title: T`三、基准建设过程`, level: 1, page: 4 },
  { title: T`四、首轮评测结果`, level: 1, page: 5 },
  { title: T`五、方法学讨论与局限`, level: 1, page: 7 },
  { title: T`六、下一步建设思路`, level: 1, page: 8 },
  { title: T`七、附录：开源仓库与资源清单`, level: 1, page: 9 },
];

// ==================== 文档 ====================
const title = T`CC-Eval 国际中文教育大模型评测基准`;
const subtitle = T`设计思路 · 首轮评测结果 · 建设规划`;

const children = [
  // 标题页
  para(run(title, { bold: true, size: 40, color: palette.dark }), {
    heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 2400, after: 240 },
  }),
  para(run(subtitle, { size: 28, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 1600 } }),
  para(run(T`作者：于东兴（Dongxing Yu）`, { size: 24 }), { alignment: AlignmentType.CENTER, spacing: { after: 120 } }),
  para(run(T`日期：2026 年 9 月 6 日`, { size: 24 }), { alignment: AlignmentType.CENTER, spacing: { after: 120 } }),
  para(run(T`版本：v1.0（首轮跑量）`, { size: 24 }), { alignment: AlignmentType.CENTER, spacing: { after: 120 } }),
  para(run(T`开源仓库：https://github.com/yudongxing999/cc-eval（MIT License）`, { size: 20, color: palette.light }), { alignment: AlignmentType.CENTER }),
  new Paragraph({ children: [new PageBreak()] }),

  // 目录
  para(run(T`目  录`, { bold: true, size: 30, color: palette.dark }), { spacing: { before: 240, after: 160 } }),
  para(run(T`（在 Word/WPS 中右键目录选择"更新域"可刷新页码）`, { italics: true, size: 18, color: palette.light })),
  toc(tocEntries),
  new Paragraph({ children: [new PageBreak()] }),

  // 一、背景
  heading(T`一、项目背景与问题定位`),
  bodyPara(T`通用大语言模型正加速进入中文教学场景：教师用它写教案、改作文，学生用它练表达、问文化，教材编者用它做分级改写。但一个基础性问题始终缺乏系统回答：这些通用模型在国际中文教育（Teaching Chinese to Speakers of Other Languages）的具体工作中到底能不能用、哪里能用、哪里不能用。`),
  bodyPara(T`现有通用评测基准（如 MMLU、C-Eval、SuperCLUE 等）测的是模型的通用知识与推理能力，无法回答上述问题。国际中文教育有其独特的专业约束：教学内容和进度受《国际中文教育中文水平等级标准》（GF 0025-2021）"三等九级"体系严格规约；学习者偏误处理需要面向二语习得的专业判断；教材与课堂用语必须做等级可控的语言生成。这些能力无法从通用 benchmark 的分数中推断。`),
  bodyPara(T`由此，本项目提出并搭建了 CC-Eval（Chinese Language Education Evaluation）——一套以权威标准文件为骨架、以真实学习者语料为素材、以教学实用价值为标尺的垂直评测基准，对当前主流通用大模型进行常规化测试，为"AI 辅助国际中文教育"的落地提供选型依据与能力边界地图。`),

  // 二、设计思路
  heading(T`二、总体设计思路`),
  heading(T`2.1 标准做骨架`, 2),
  bodyPara(T`以四份权威标准文件结构化为基准的约束集与出题源：《国际中文教育中文水平等级标准》（GF 0025-2021，音节 1110 条、汉字 3000 字、词汇 11092 条、语法 572 条）、《国际中文教育用中国文化和国情教学参考框架》、《国际中文教材评价标准》、《国际中文教师专业能力标准》与《职业中文能力等级标准》。标准条文既是题目的"答案锚点"，也是生成类任务的"硬约束"（如限级词表）。`),
  heading(T`2.2 语料做血肉`, 2),
  bodyPara(T`引入北京语言大学 HSK 动态作文语料库（2.0 版）的真实学习者语料：本次共获取 11328 篇带偏误标注与人工分数的作文，用于构造偏误识别（ERR）与作文评分（SCO）两类任务。真实中介语语料保证了任务的生态效度——模型面对的不是编者臆造的"病句"，而是真实课堂中发生的语言错误。语料使用严格遵循授权流程（已向语料库中心提交使用申请），开源仓库不包含语料原文。`),
  heading(T`2.3 任务做检验`, 2),
  bodyPara(T`从教学现场的真实工作出发，抽象出六类任务共 1555 道题目，覆盖"知识—判断—评分—生成—文化—合规"的完整链条：`),
  makeTable([900, 3300, 800, 4000], ["代码", "任务说明", "题量", "素材来源"], taskDesign),
  para(run("")),
  heading(T`2.4 评分双轨制`, 2),
  bodyPara(T`1357 道客观题由四类确定性自动评分器评判（精确匹配、数值邻近、集合重叠、规则校验），保证结果完全可复现；198 道开放题由 LLM 评委按预置量表打分。评分器与量表全部开源，任何机构可独立复跑验证。`),

  // 三、建设过程
  heading(T`三、基准建设过程`),
  heading(T`3.1 数据层：标准结构化与全书级校验`, 2),
  bodyPara(T`等级标准原始文档为扫描版 PDF，本项目采用"社区转录基线 + OCR 交叉校验 + 全书级复核"的三级工艺：先以社区开源转录为基线，再对扫描页做 200-300 DPI 渲染与 RapidOCR 识别逐词比对，最后以《等级标准（应用解读本）》三册全书的"音序总表+分级表"双表对四张表逐条复核、原书仲裁。全书级复核共确认 8 处社区转录错误（如词汇"显"五级→六级、汉字"谋/悬/抢/馒/素"六级→高等），已形成 errata.json 勘误表回馈社区。`),
  heading(T`3.2 题库层：schema 驱动与污染控制`, 2),
  bodyPara(T`题目以统一 JSON Schema 描述（任务类型、锚定等级、提示词、参考答案、评分方式、来源与污染风险标记），由生成器程序化构造（随机种子 20260905，结果可复现）。针对大模型评测普遍存在的训练数据污染问题，题库做了显式分层：KNO/ERR 题素材来自公开标准与公开语料（污染风险中，低分比高分更有信息量）；GEN/PED 题为本次新构造（污染风险低）。`),
  heading(T`3.3 评测层：多供应商工程化跑测`, 2),
  bodyPara(T`评测运行器以 OpenAI 兼容协议接入各厂商 API，支持断点续跑、并发控制与 RPM 限速适配。首轮共接入 10 家厂商：8 家直连官方 API，腾讯两款模型经 TokenHub 国际站（新加坡节点）接入；豆包通过火山方舟推理接入点接入。跑测过程处理了免费层限速（阶跃 RPM=10）、试用额度耗尽（TokenHub 100 万 token）、日配额限制（Gemini 约 20 次/天）等真实工程约束——这些约束本身也是"实用价值"的一部分，已计入报告。`),

  // 四、结果
  heading(T`四、首轮评测结果`),
  heading(T`4.1 总分榜`, 2),
  bodyPara(T`2026 年 9 月 5-6 日完成首轮跑量：11 个模型各完成 1555 题全量测试与评委补评。各厂商均选用免费/轻量档或当前可用档模型，代表"低成本可及"的实用价值基线。六类任务等权汇总（百分制）结果如下：`),
  makeTable([620, 2210, 780, 760, 760, 760, 760, 760, 760],
    ["排名", "模型（厂商）", "总分", "KNO", "ERR", "SCO", "GEN", "CUL", "PED"], leaderboard),
  para(run("")),
  bodyPara(T`注：Kimi 两款的 CUL 等主观题由同族模型 k3-agent 担任评委，横比时建议预留 5-10 分下调空间；Gemini 因免费层日配额限制（约 20 次/天）未能完成全量，不入榜。`),
  heading(T`4.2 关键发现`, 2),
  para(run(T`发现一："限级生成"是全行业共同短板。`, { bold: true }), { spacing: { before: 160, after: 80 } }),
  bodyPara(T`把一段文字严格改写为指定等级可懂（用词不超出目标词表），120 道题中表现最好的混元 hy3 也只有 15.0% 通过率，多数模型接近零分：`),
  makeTable([4500, 1800], ["模型", "限级改写通过率"], rewriteTable),
  para(run("")),
  bodyPara(T`这意味着分级阅读材料编写、教材课文改写等场景不能依赖通用模型开箱完成，必须外挂词表约束（检索增强、解码约束或生成后校验）。`),
  para(run(T`发现二："等级知识"普遍薄弱且不稳定。`, { bold: true }), { spacing: { before: 160, after: 80 } }),
  bodyPara(T`判断字、词、语法点归属三等九级中的哪一级，最好的 deepseek-chat 也仅 35.2%，通义、智谱接近随机水平（12 分左右）。模型并未可靠内化等级标准表，"该教不该教、先教后教"的决策不可直接采信模型直觉，需要外挂标准检索。`),
  para(run(T`发现三：作文评分整体可用，但选型不能凭品牌。`, { bold: true }), { spacing: { before: 160, after: 80 } }),
  bodyPara(T`以语料库人工分数为锚，k3（78.6）、文心（76.8）、deepseek-chat（75.8）处于可用区，可作为辅助批改工具（仍建议人工抽检）；而旗舰档的豆包（44.4）、混元（48.6）反而大幅落后，评分口径与教学人工标准的对齐度与模型档位不成正相关，采购选型前必须单测。`),
  para(run(T`发现四：文化国情与语用是共同强项。`, { bold: true }), { spacing: { before: 160, after: 80 } }),
  bodyPara(T`各模型 CUL 维度均在 70-95 分区间，文化常识问答与语用得体性判断可直接投入使用。`),
  para(run(T`发现五："懂教学常识"不等于"懂标准条文"。`, { bold: true }), { spacing: { before: 160, after: 80 } }),
  bodyPara(T`场景化教学设计题各模型普遍 98-100 分，但要求定位教材文本违反《国际中文教材评价标准》的具体条款时，11 个模型中 5 个为 0%、最高仅 8.9%。通用模型不能承担标准合规性审查工作。`),
  para(run(T`发现六：偏误归因中等偏弱。`, { bold: true }), { spacing: { before: 160, after: 80 } }),
  bodyPara(T`真实学习者语料的偏误识别与纠正任务得分区间 21.5-36.1%：给出改正尚可辅助，偏误类型归因不可尽信。`),
  para(run(T`发现七：新一代模型生成能力进步明显，但标准记忆未同步改善。`, { bold: true }), { spacing: { before: 160, after: 80 } }),
  bodyPara(T`deepseek-v4-flash 教学生成维度 50.8，显著强于官方 deepseek-chat（36.6）；但其等级知识（22.5）反而低于前代（35.2），"标准记忆"并未随版本升级自动变好——垂直知识仍需显式注入。`),

  // 五、局限
  heading(T`五、方法学讨论与局限`),
  bullet(T`数据污染：部分题目素材来自公开文本，模型训练时可能见过；本基准对污染做了显式分层标记，解读时低分（连见过的都答不对）比高分更具诊断价值。`),
  bullet(T`评委偏差：开放题由单一 LLM 评委（k3-agent）评分，存在同族偏袒与评委漂移；v1.1 将引入第二异源评委与人工抽检校准（锚定 CGED/CLTC/MuCGEC 公开评测集）。`),
  bullet(T`档位偏差：本轮一律使用免费/轻量档模型，结论适用于该档位，不代表各厂旗舰最高水平。`),
  bullet(T`采样噪声：单次采样、默认温度，分数存在约 ±2 分的波动；正式版将对关键任务做多采样。`),
  bullet(T`接入差异：腾讯两款模型经 TokenHub 国际站中转，网关行为与官方直连略有差异，但对评分内容无实质影响。`),

  // 六、建设规划
  heading(T`六、下一步建设思路`),
  heading(T`6.1 短期（1 个月内）：补全与加固`, 2),
  bullet(T`补齐 Gemini 全量评测（需绑定计费的 key），完成 12 模型完整榜单；`),
  bullet(T`扩充 CUL/PED 题量至各 200 题，均衡六类任务权重；`),
  bullet(T`引入第二异源评委，双评委分歧题自动转人工仲裁；`),
  bullet(T`向 HSK 动态作文语料库中心正式提交批量使用申请，完成 627 道题目的合规授权闭环。`),
  heading(T`6.2 中期（1 个学期）：专业化与正式发布`, 2),
  bullet(T`招募国际中文教育专业团队：题目质量复核、评分量表信效度检验、人工校准集建设；`),
  bullet(T`发布 v1.1：加入各厂旗舰档模型对比、多采样投票、人工校准后的分数修订；`),
  bullet(T`撰写学术论文，投稿至语言智能评测或国际中文教育相关期刊/会议。`),
  heading(T`6.3 长期：社区化与常态化`, 2),
  bullet(T`建设公开 leaderboard 站点，按季度跟踪主流模型版本迭代；`),
  bullet(T`以开源社区（GitHub: yudongxing999/cc-eval，MIT 协议）吸纳题目贡献与厂商自测；`),
  bullet(T`与标准研制机构联动：评测中暴露的"模型等级知识薄弱"证据，可反向服务于等级标准的数字化推广与教师培训；`),
  bullet(T`扩展评测场景：口语评测、课堂互动、教材全链条审读，最终形成"国际中文教育 AI 工具选型标准"。`),

  // 七、附录
  heading(T`七、附录：开源仓库与资源清单`),
  bullet(T`开源仓库：https://github.com/yudongxing999/cc-eval（MIT License，署名：于东兴 Dongxing Yu）`),
  bullet(T`仓库内容：四份标准结构化数据（含 errata 勘误）、题目 JSON Schema、公开版题库 928 题与可复现生成器、评测运行器与评委脚本、首轮报告与 11 模型逐题原始输出。`),
  bullet(T`合规说明：HSK 语料原文及其衍生题目不随仓库发布，获授权用户可用生成器重建完整 1555 题；标准原始扫描件与全书 OCR 文本因版权原因不入库。`),
  bullet(T`首轮详细数据：results/REPORT_v1.0_multimodel.md（多模型对比报告）、results/multimodel_summary.json（机读汇总）。`),
];

const doc = new Document({
  features: { updateFields: true },
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    headers: { default: new Header({ children: [para(run(T`CC-Eval 国际中文教育大模型评测基准 · 项目报告`, { size: 18, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 18 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(doc));
console.log("written:", outputPath);
