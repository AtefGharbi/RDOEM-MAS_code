// Render paper JSON (blocks) to .docx with docx-js.
// Block types: title, authors, h1, h2, h3, p (runs), eq, list (items of runs), table, figure, caption, pagebreak, refs
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType, HeadingLevel,
  WidthType, ShadingType, BorderStyle, LevelFormat, Footer, PageNumber, TabStopType,
} = require("docx");

const [, , inJson, outDocx] = process.argv;
const doc = JSON.parse(fs.readFileSync(inJson, "utf8"));
const FONT = "Times New Roman";
const PAGE_W = 12240, MARGIN = 1080, CONTENT_W = PAGE_W - 2 * MARGIN; // US Letter, 0.75" margins

function runs(rs, base = {}) {
  if (typeof rs === "string") rs = [rs];
  return rs.map((r) => {
    if (typeof r === "string") return new TextRun({ text: r, font: FONT, size: base.size || 20, ...base });
    const o = { text: r.t, font: r.mono ? "Cambria Math" : FONT, size: r.size || base.size || 20, ...base };
    if (r.b) o.bold = true;
    if (r.i) o.italics = true;
    if (r.sub) o.subScript = true;
    if (r.sup) o.superScript = true;
    if (r.color) o.color = r.color;
    return new TextRun(o);
  });
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const borders = { top: border, bottom: border, left: border, right: border };

function table(b) {
  const ncol = b.header.length;
  const widths = b.widths
    ? b.widths.map((w) => Math.round((w / b.widths.reduce((a, c) => a + c, 0)) * CONTENT_W))
    : Array(ncol).fill(Math.floor(CONTENT_W / ncol));
  const diff = CONTENT_W - widths.reduce((a, c) => a + c, 0);
  widths[widths.length - 1] += diff;
  const fs_ = b.size || 16;
  const mk = (cells, head) =>
    new TableRow({
      tableHeader: head,
      children: cells.map((c, j) =>
        new TableCell({
          borders,
          width: { size: widths[j], type: WidthType.DXA },
          shading: head ? { fill: "D9E2F3", type: ShadingType.CLEAR, color: "auto" } : undefined,
          margins: { top: 40, bottom: 40, left: 80, right: 80 },
          children: [new Paragraph({
            alignment: j === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
            children: runs(c, { size: fs_, bold: head }),
          })],
        })
      ),
    });
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [mk(b.header, true), ...b.rows.map((r) => mk(r, false))],
  });
}

const children = [];
for (const b of doc.blocks) {
  switch (b.type) {
    case "title":
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
        children: runs(b.text, { size: 34, bold: true }) }));
      break;
    case "authors":
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
        children: runs(b.text, { size: 20, italics: true }) }));
      break;
    case "h1":
      children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 240, after: 100 },
        children: runs(b.text, { size: 24, bold: true }) }));
      break;
    case "h2":
      children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 160, after: 80 },
        children: runs(b.text, { size: 21, bold: true, italics: true }) }));
      break;
    case "h3":
      children.push(new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 120, after: 60 },
        children: runs(b.text, { size: 20, italics: true }) }));
      break;
    case "p":
      children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 100, line: 264 },
        indent: b.indent === false ? undefined : { firstLine: 0 }, children: runs(b.runs) }));
      break;
    case "box":
      children.push(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { before: 60, after: 120, line: 264 },
        shading: { fill: "EEF3FA", type: ShadingType.CLEAR, color: "auto" },
        border: { top: border, bottom: border, left: border, right: border },
        indent: { left: 240, right: 240 }, children: runs(b.runs) }));
      break;
    case "eq":
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 60 },
        tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_W }],
        children: [...runs([{ t: b.text, mono: true, size: 20 }]),
          ...(b.num ? [new TextRun({ text: `\u2003\u2003(${b.num})`, font: FONT, size: 20 })] : [])] }));
      break;
    case "list":
      b.items.forEach((it) => children.push(new Paragraph({
        numbering: { reference: b.ordered ? "num" : "bul", level: 0, instance: b.instance || 0 },
        alignment: AlignmentType.JUSTIFIED, spacing: { after: 60, line: 264 }, children: runs(it) })));
      break;
    case "algo":
      children.push(new Paragraph({ spacing: { before: 120, after: 40 },
        border: { top: { style: BorderStyle.SINGLE, size: 8, color: "000000" },
          bottom: { style: BorderStyle.SINGLE, size: 4, color: "000000" } },
        children: runs(b.title, { bold: true, size: 19 }) }));
      b.lines.forEach((ln, i) => children.push(new Paragraph({ spacing: { after: 20, line: 250 },
        indent: { left: 240 + 240 * (ln.level || 0), hanging: 240 },
        children: runs(ln.runs, { size: 18 }) })));
      children.push(new Paragraph({ spacing: { after: 160 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: "000000" } }, children: [] }));
      break;
    case "table":
      if (b.caption) children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 60 },
        keepNext: true, children: runs(b.caption, { size: 18, bold: false }) }));
      children.push(table(b));
      if (b.note) children.push(new Paragraph({ spacing: { before: 40, after: 160 }, children: runs(b.note, { size: 16, italics: true }) }));
      else children.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
      break;
    case "figure": {
      const img = fs.readFileSync(b.path);
      const w = b.width || 620, h = Math.round(w * b.aspect);
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 }, keepNext: true,
        children: [new ImageRun({ type: "png", data: img, transformation: { width: w, height: h },
          altText: { title: b.alt || "figure", description: b.alt || "figure", name: path.basename(b.path) } })] }));
      children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 160 },
        children: runs(b.caption, { size: 17 }) }));
      break;
    }
    case "refs":
      b.items.forEach((r, i) => children.push(new Paragraph({ spacing: { after: 40 }, indent: { left: 440, hanging: 440 },
        children: runs([`[${i + 1}]\t` + r], { size: 17 }),
        tabStops: [{ type: TabStopType.LEFT, position: 440 }] })));
      break;
    case "pagebreak":
      children.push(new Paragraph({ pageBreakBefore: true, children: [] }));
      break;
  }
}

const d = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: FONT, color: "1F3864" }, paragraph: { spacing: { before: 240, after: 100 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 21, bold: true, italics: true, font: FONT, color: "1F3864" }, paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 20, italics: true, font: FONT }, paragraph: { spacing: { before: 120, after: 60 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1)", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 15840 }, margin: { top: 1080, bottom: 1080, left: MARGIN, right: MARGIN } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 })] })] }) },
    children,
  }],
});
Packer.toBuffer(d).then((buf) => { fs.writeFileSync(outDocx, buf); console.log("wrote", outDocx); });
