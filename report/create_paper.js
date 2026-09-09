import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, Header, HeadingLevel, Packer, PageNumber,
  Paragraph, ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
  convertInchesToTwip,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node create_paper.js /abs/out.docx");
const mdPath = path.join(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1")), "论文完整稿.md");

const md = fs.readFileSync(mdPath, "utf-8");

// 字体：正文宋体五号(10.5pt=21半点)，一级标题黑体五号加粗居中，二级标题黑体五号左齐
const fontBody = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const fontHead = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimHei" };

const run = (text, options = {}) => new TextRun({ text, font: fontBody, size: 21, ...options });
const para = (children, options = {}) => new Paragraph({
  spacing: { after: 120, line: 320 },
  ...options,
  children: Array.isArray(children) ? children : [children],
});

// 解析 **bold** 行内标记
function inline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return parts.map((seg) => {
    if (seg.startsWith("**") && seg.endsWith("**")) return run(seg.slice(2, -2), { bold: true });
    return run(seg);
  });
}

const p = (text) => para(inline(text), { indent: { firstLine: 420 } });
const pNoIndent = (text) => para(inline(text));

const h1 = (text) => para([new TextRun({ text, font: fontHead, size: 21, bold: true })], {
  heading: HeadingLevel.HEADING_1,
  alignment: AlignmentType.CENTER,
  spacing: { before: 280, after: 200 },
});
const h2 = (text) => para([new TextRun({ text, font: fontHead, size: 21, bold: true })], {
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 220, after: 140 },
});

// 表格
const cellMargins = { top: 80, bottom: 80, left: 100, right: 100 };
function makeCell(text, width, header) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    margins: cellMargins,
    shading: header ? { type: ShadingType.CLEAR, fill: "F2F2F2" } : undefined,
    children: [para([new TextRun({ text: text.trim(), font: fontBody, size: 18, bold: !!header })], {
      spacing: { after: 0, line: 260 },
      alignment: AlignmentType.CENTER,
    })],
  });
}

function makeTable(rows) {
  const ncols = rows[0].length;
  const total = 9000;
  const widths = Array(ncols).fill(Math.floor(total / ncols));
  widths[ncols - 1] = total - widths.slice(0, -1).reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map((r, ri) => new TableRow({
      children: r.map((c, ci) => makeCell(c, widths[ci], ri === 0)),
    })),
  });
}

// 逐行解析 markdown
const lines = md.split(/\r?\n/);
const children = [];
let i = 0;
while (i < lines.length) {
  const line = lines[i];
  if (!line.trim()) { i++; continue; }

  // 表格块
  if (line.trim().startsWith("|")) {
    const rows = [];
    while (i < lines.length && lines[i].trim().startsWith("|")) {
      const cells = lines[i].trim().replace(/^\||\|$/g, "").split("|").map((s) => s.trim());
      if (!cells.every((c) => /^:?-{2,}:?$/.test(c))) rows.push(cells);
      i++;
    }
    if (rows.length) children.push(makeTable(rows), para(run(""), { spacing: { after: 60 } }));
    continue;
  }

  if (line.startsWith("### ")) { children.push(h2(line.slice(4).trim())); i++; continue; }
  if (line.startsWith("## ")) { children.push(h1(line.slice(3).trim())); i++; continue; }
  if (line.startsWith("# ")) {
    children.push(para([new TextRun({ text: line.slice(2).trim(), font: fontHead, size: 32, bold: true })], {
      alignment: AlignmentType.CENTER, spacing: { after: 240 },
    }));
    i++; continue;
  }

  // 参考文献条目与英文摘要不缩进
  const noIndent = /^（双向匿名|^[*A-Za-z(]|^网络资源|^宾帅|^杜月明|^江新|^王蕾|^王亚敏|^吴思远|^肖锐|^左虹|^中外语言/.test(line.trim());
  children.push(noIndent ? pNoIndent(line.trim()) : p(line.trim()));
  i++;
}

const doc = new Document({
  features: { updateFields: false },
  styles: { default: { document: { run: { font: fontBody, size: 21 } } } },
  sections: [{
    properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [para(
      new TextRun({ children: [PageNumber.CURRENT], font: fontBody, size: 18 }),
      { alignment: AlignmentType.CENTER, spacing: { after: 0 } },
    )] }) },
    children,
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(doc));
console.log("written:", outputPath);
