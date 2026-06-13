const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "AI 智慧記帳助理 - 期末專案報告";

// ── Color palette ──────────────────────────────────
const DG = "004D20";    // dark green  (headers, title bg)
const MG = "00662A";    // mid green   (secondary header)
const PG = "00A050";    // primary green (accents, arrows)
const AG = "00C060";    // accent green (bright highlight)
const LG = "F1FAF3";    // light green bg
const WH = "FFFFFF";    // white
const BT = "1A2E1A";    // body text (dark green-gray)
const MT = "557060";    // muted text
const CB = "C8E6C9";    // card border

// ── Helper: slide header bar ──────────────────────
function addHeader(s, title, subtitle) {
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.05, fill: { color: DG }, line: { color: DG } });
  s.addText(title, {
    x: 0.45, y: 0.04, w: 9.1, h: 0.62,
    fontSize: 28, fontFace: "Arial Black", color: WH,
    bold: true, align: "left", valign: "bottom", margin: 0,
  });
  s.addText(subtitle, {
    x: 0.45, y: 0.68, w: 9.1, h: 0.34,
    fontSize: 12, fontFace: "Calibri", color: "A8D5B5",
    align: "left", valign: "top", margin: 0,
  });
}

// ── Helper: colored box with multi-line text ──────
function flowBox(s, x, y, w, h, lines, bg, fg) {
  fg = fg || WH;
  s.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h, fill: { color: bg }, line: { color: bg },
    shadow: { type: "outer", blur: 3, offset: 1, angle: 135, color: "000000", opacity: 0.15 },
  });
  var items = lines.map(function(t, i) {
    return { text: t, options: { breakLine: i < lines.length - 1 } };
  });
  s.addText(items, {
    x, y, w, h, fontSize: 11, fontFace: "Calibri", color: fg,
    bold: true, align: "center", valign: "middle", margin: 0.05,
  });
}

// ── Helper: horizontal / vertical lines ──────────
function arrowR(s, x, y, w) {
  s.addShape(pres.shapes.LINE, { x: x, y: y, w: w, h: 0, line: { color: PG, width: 2.5 } });
}
function arrowD(s, x, y, h) {
  s.addShape(pres.shapes.LINE, { x: x, y: y, w: 0, h: h, line: { color: PG, width: 2.5 } });
}

// ══════════════════════════════════════════════════
// SLIDE 1 — 封面
// ══════════════════════════════════════════════════
(function() {
  var s = pres.addSlide();
  s.background = { color: DG };

  // Top accent stripe
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.12, fill: { color: AG }, line: { color: AG } });

  // Decorative circle (icon area)
  s.addShape(pres.shapes.OVAL, {
    x: 3.9, y: 0.65, w: 2.2, h: 2.2,
    fill: { color: MG }, line: { color: AG, width: 3 },
  });
  s.addText("💰", { x: 3.9, y: 0.65, w: 2.2, h: 2.2, fontSize: 56, align: "center", valign: "middle", margin: 0 });

  // Main title
  s.addText("AI 智慧記帳助理", {
    x: 0.5, y: 2.95, w: 9, h: 1.05,
    fontSize: 46, fontFace: "Arial Black", color: WH,
    bold: true, align: "center", valign: "middle", margin: 0,
  });

  // Subtitle
  s.addText("結合 RAG、HyDE、LLM/VLM 與 n8n 的智慧生活記帳機器人", {
    x: 0.5, y: 4.08, w: 9, h: 0.58,
    fontSize: 15, fontFace: "Calibri", color: "A8D5B5",
    align: "center", valign: "middle", margin: 0,
  });

  // Thin divider
  s.addShape(pres.shapes.RECTANGLE, { x: 3.5, y: 4.72, w: 3.0, h: 0.05, fill: { color: PG }, line: { color: PG } });

  // Report label
  s.addText("期末專案報告", {
    x: 0.5, y: 4.84, w: 9, h: 0.44,
    fontSize: 14, fontFace: "Calibri", color: "7BC09A",
    align: "center", valign: "middle", margin: 0,
  });

  // Bottom stripe
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.52, w: 10, h: 0.1, fill: { color: AG }, line: { color: AG } });
})();

// ══════════════════════════════════════════════════
// SLIDE 2 — 動機與目的
// ══════════════════════════════════════════════════
(function() {
  var s = pres.addSlide();
  s.background = { color: LG };
  addHeader(s, "動機與目的", "Motivation & Purpose");

  // ── Left card: Problem ────────────────────────
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 1.18, w: 4.35, h: 3.98,
    fill: { color: WH }, line: { color: CB, width: 1 },
    shadow: { type: "outer", blur: 8, offset: 2, angle: 135, color: "000000", opacity: 0.1 },
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 1.18, w: 4.35, h: 0.58, fill: { color: PG }, line: { color: PG } });
  s.addText("😕  問題現況", {
    x: 0.42, y: 1.18, w: 4.12, h: 0.58,
    fontSize: 15, fontFace: "Calibri", color: WH,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "現代人普遍記帳習慣不佳", options: { bullet: true, breakLine: true } },
    { text: "傳統 App 操作繁瑣、學習成本高", options: { bullet: true, breakLine: true } },
    { text: "收據容易遺失，消費難以追蹤", options: { bullet: true, breakLine: true } },
    { text: "群組分帳計算耗時費力", options: { bullet: true, breakLine: true } },
    { text: "多元消費管道難以整合管理", options: { bullet: true } },
  ], {
    x: 0.55, y: 1.85, w: 3.95, h: 3.15,
    fontSize: 13.5, fontFace: "Calibri", color: BT,
    valign: "top", paraSpaceAfter: 8,
  });

  // ── Right card: Solution ──────────────────────
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.0, y: 1.18, w: 4.7, h: 3.98,
    fill: { color: WH }, line: { color: CB, width: 1 },
    shadow: { type: "outer", blur: 8, offset: 2, angle: 135, color: "000000", opacity: 0.1 },
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.0, y: 1.18, w: 4.7, h: 0.58, fill: { color: DG }, line: { color: DG } });
  s.addText("💡  解決方案", {
    x: 5.12, y: 1.18, w: 4.48, h: 0.58,
    fontSize: 15, fontFace: "Calibri", color: WH,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "LINE Bot：零學習成本的對話式記帳", options: { bullet: true, breakLine: true } },
    { text: "LINE 是台灣使用率最高的通訊軟體", options: { bullet: true, breakLine: true } },
    { text: "VLM 自動辨識收據與發票圖片", options: { bullet: true, breakLine: true } },
    { text: "RAG + HyDE 支援智慧消費查詢", options: { bullet: true, breakLine: true } },
    { text: "群組 @mention 自動計算分帳金額", options: { bullet: true } },
  ], {
    x: 5.15, y: 1.85, w: 4.4, h: 3.15,
    fontSize: 13.5, fontFace: "Calibri", color: BT,
    valign: "top", paraSpaceAfter: 8,
  });
})();

// ══════════════════════════════════════════════════
// SLIDE 3 — 技術架構總覽
// ══════════════════════════════════════════════════
(function() {
  var s = pres.addSlide();
  s.background = { color: WH };
  addHeader(s, "技術架構總覽", "System Architecture Overview");

  // ── Row 1: input flow ─────────────────────────
  var bh = 0.65, r1y = 1.3;
  flowBox(s, 0.2,  r1y, 1.4,  bh, ["👤 使用者"],        "1565C0");
  arrowR(s, 1.6,   r1y + bh / 2, 0.35);
  flowBox(s, 1.95, r1y, 1.5,  bh, ["💬 LINE"],           "00B900");
  arrowR(s, 3.45,  r1y + bh / 2, 0.35);
  flowBox(s, 3.8,  r1y, 1.25, bh, ["⚙️ n8n"],            "E65100");
  arrowR(s, 5.05,  r1y + bh / 2, 0.4);
  flowBox(s, 5.45, r1y, 2.1,  bh, ["🚀 FastAPI", "後端伺服器"], DG);

  // FastAPI center x = 5.45 + 1.05 = 6.5
  var fapiCx = 6.5;
  arrowD(s, fapiCx, r1y + bh, 0.3);

  // ── Horizontal fan connector ──────────────────
  var r2y = r1y + bh + 0.3; // 2.25
  var bw2 = 2.62;
  var b1x = 0.4, b2x = 3.57, b3x = 6.74;
  var b1cx = b1x + bw2 / 2; // 1.71
  var b2cx = b2x + bw2 / 2; // 4.88
  var b3cx = b3x + bw2 / 2; // 8.05

  // Horizontal line from b1cx to b3cx
  s.addShape(pres.shapes.LINE, { x: b1cx, y: r2y, w: b3cx - b1cx, h: 0, line: { color: PG, width: 2.5 } });
  // Vertical drops to branch boxes
  [b1cx, b2cx, b3cx].forEach(function(cx) { arrowD(s, cx, r2y, 0.28); });

  // ── Row 2: processing boxes ───────────────────
  var bh2 = 0.8;
  flowBox(s, b1x, r2y + 0.28, bw2, bh2, ["🧠 Gemini LLM",  "意圖分類 / 記帳解析"], MG);
  flowBox(s, b2x, r2y + 0.28, bw2, bh2, ["👁️ Gemini VLM",  "收據 / 圖片辨識"],    MG);
  flowBox(s, b3x, r2y + 0.28, bw2, bh2, ["🔍 RAG + HyDE",  "智慧查詢引擎"],       MG);

  // ── Row 3: output ─────────────────────────────
  var r3y = r2y + 0.28 + bh2 + 0.25; // 3.61
  arrowD(s, b2cx, r2y + 0.28 + bh2, 0.25); // center connector
  flowBox(s, 0.4, r3y, 9.2, bh, ["🗄️ SQLite 資料存取  →  LINE 訊息回覆  ＋  📊 Web Dashboard"], "00695C");
})();

// ══════════════════════════════════════════════════
// SLIDE 4 — n8n 工作流程
// ══════════════════════════════════════════════════
(function() {
  var s = pres.addSlide();
  s.background = { color: LG };
  addHeader(s, "n8n 工作流程", "n8n Workflow Design");

  var steps = [
    { num: "1", title: "LINE Webhook 接收",   desc: "LINE 伺服器將用戶事件即時推送至 n8n（文字 / 圖片 / 群組加入）" },
    { num: "2", title: "Code Node 前處理",    desc: "清理控制字元與特殊符號，避免 JSON 解析錯誤，解析 eventType" },
    { num: "3", title: "群組 @mention 偵測",  desc: "以 @ 切割訊息，提取完整顯示名稱（支援含空格的多字名稱）" },
    { num: "4", title: "HTTP Request 轉發",   desc: "將清理後的事件 POST 至 FastAPI /process 端點進行 AI 處理" },
    { num: "5", title: "FastAPI 處理與回覆",  desc: "LLM 分類意圖、執行對應邏輯，再透過 LINE Messaging API 回覆" },
  ];

  var stepH = 0.73, stepGap = 0.1;
  var totalH = steps.length * stepH + (steps.length - 1) * stepGap;
  var startY = (5.625 - 1.05 - totalH) / 2 + 1.05;

  steps.forEach(function(step, i) {
    var y = startY + i * (stepH + stepGap);

    // Number circle
    s.addShape(pres.shapes.OVAL, { x: 0.3, y: y, w: stepH, h: stepH, fill: { color: DG }, line: { color: DG } });
    s.addText(step.num, {
      x: 0.3, y: y, w: stepH, h: stepH,
      fontSize: 22, fontFace: "Arial Black", color: WH,
      bold: true, align: "center", valign: "middle", margin: 0,
    });

    // Card
    s.addShape(pres.shapes.RECTANGLE, {
      x: 1.22, y: y, w: 8.5, h: stepH,
      fill: { color: WH }, line: { color: CB, width: 1 },
      shadow: { type: "outer", blur: 4, offset: 1, angle: 135, color: "000000", opacity: 0.08 },
    });
    // Left accent
    s.addShape(pres.shapes.RECTANGLE, { x: 1.22, y: y, w: 0.08, h: stepH, fill: { color: PG }, line: { color: PG } });

    s.addText(step.title, {
      x: 1.42, y: y + 0.05, w: 8.1, h: 0.3,
      fontSize: 14, fontFace: "Calibri", color: DG,
      bold: true, align: "left", valign: "middle", margin: 0,
    });
    s.addText(step.desc, {
      x: 1.42, y: y + 0.36, w: 8.1, h: 0.33,
      fontSize: 12, fontFace: "Calibri", color: MT,
      align: "left", valign: "top", margin: 0,
    });

    // Connector to next step
    if (i < steps.length - 1) {
      arrowD(s, 0.3 + stepH / 2, y + stepH, stepGap);
    }
  });
})();

// ══════════════════════════════════════════════════
// SLIDE 5 — LLM 與 VLM 應用
// ══════════════════════════════════════════════════
(function() {
  var s = pres.addSlide();
  s.background = { color: WH };
  addHeader(s, "LLM 與 VLM 應用", "Language Model & Vision Model Integration");

  // ── Left: LLM ────────────────────────────────
  var cardH = 4.1;
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 1.1, w: 4.35, h: cardH,
    fill: { color: LG }, line: { color: CB },
    shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.08 },
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 1.1, w: 4.35, h: 0.62, fill: { color: DG }, line: { color: DG } });
  s.addText("🧠  LLM — Gemini 2.5 Flash", {
    x: 0.42, y: 1.1, w: 4.15, h: 0.62,
    fontSize: 14, fontFace: "Calibri", color: WH,
    bold: true, align: "left", valign: "middle", margin: 0,
  });

  var llmData = [
    { section: "意圖分類", items: ["add_record — 新增記帳紀錄", "query — 智慧查詢消費", "aa — 群組 AA 分帳", "other — 一般對話回覆"] },
    { section: "記帳資訊解析", items: ["金額、類別、日期、備註", "收入 / 支出方向判斷"] },
    { section: "AA 分帳解析", items: ["總金額、分帳人數", "項目描述、付款方"] },
  ];
  var llmY = 1.82;
  llmData.forEach(function(d) {
    s.addText(d.section, { x: 0.5, y: llmY, w: 4.0, h: 0.28, fontSize: 12.5, fontFace: "Calibri", color: PG, bold: true, align: "left", valign: "middle", margin: 0 });
    llmY += 0.28;
    var items = d.items.map(function(t, i) { return { text: t, options: { bullet: true, breakLine: i < d.items.length - 1 } }; });
    var ih = d.items.length * 0.28;
    s.addText(items, { x: 0.55, y: llmY, w: 3.9, h: ih, fontSize: 12, fontFace: "Calibri", color: BT, valign: "top", paraSpaceAfter: 2 });
    llmY += ih + 0.14;
  });

  // ── Right: VLM ───────────────────────────────
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.1, y: 1.1, w: 4.6, h: cardH,
    fill: { color: LG }, line: { color: CB },
    shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.08 },
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.1, y: 1.1, w: 4.6, h: 0.62, fill: { color: MG }, line: { color: MG } });
  s.addText("👁️  VLM — Gemini 2.5 Flash Vision", {
    x: 5.22, y: 1.1, w: 4.38, h: 0.62,
    fontSize: 14, fontFace: "Calibri", color: WH,
    bold: true, align: "left", valign: "middle", margin: 0,
  });

  var vlmData = [
    { section: "支援圖片類型", items: ["實體收據 / 發票照片", "LINE Pay 付款截圖", "其他消費憑證圖片"] },
    { section: "自動提取資訊", items: ["消費金額（含幣別）", "店家名稱與消費類別", "消費日期與備註"] },
    { section: "使用流程", items: ["用戶拍照 → 傳送至 LINE Bot", "VLM 分析圖片 → 自動建立記帳", "回覆確認訊息，可即時編輯"] },
  ];
  var vlmY = 1.82;
  vlmData.forEach(function(d) {
    s.addText(d.section, { x: 5.25, y: vlmY, w: 4.25, h: 0.28, fontSize: 12.5, fontFace: "Calibri", color: PG, bold: true, align: "left", valign: "middle", margin: 0 });
    vlmY += 0.28;
    var items = d.items.map(function(t, i) { return { text: t, options: { bullet: true, breakLine: i < d.items.length - 1 } }; });
    var ih = d.items.length * 0.28;
    s.addText(items, { x: 5.3, y: vlmY, w: 4.15, h: ih, fontSize: 12, fontFace: "Calibri", color: BT, valign: "top", paraSpaceAfter: 2 });
    vlmY += ih + 0.14;
  });
})();

// ══════════════════════════════════════════════════
// SLIDE 6 — RAG + HyDE + Pseudo Query
// ══════════════════════════════════════════════════
(function() {
  var s = pres.addSlide();
  s.background = { color: LG };
  addHeader(s, "RAG + HyDE + Pseudo Query", "Intelligent Retrieval System");

  var cols = [
    {
      abbr: "RAG", full: "Retrieval-Augmented\nGeneration", color: DG,
      items: [
        "建立個人消費記錄的向量索引",
        "查詢時以語意相似度檢索最相關歷史記錄",
        "結合 LLM 生成精確的查詢回答",
        "支援自然語言提問",
        "例：「上週吃飯花多少？」",
      ],
    },
    {
      abbr: "HyDE", full: "Hypothetical Document\nEmbeddings", color: MG,
      items: [
        "LLM 先依問題生成假設性答案",
        "將假設答案轉換為向量空間表示",
        "以假設向量進行語意相似度檢索",
        "比直接查詢問題語意更準確",
        "改善稀疏查詢的召回效果",
      ],
    },
    {
      abbr: "Pseudo\nQuery", full: "Multi-perspective\nQuery Expansion", color: "00695C",
      items: [
        "將使用者問題轉換為多種查詢視角",
        "模擬不同角度的可能問題描述",
        "擴大檢索涵蓋的資料範圍",
        "顯著提升整體召回率",
        "與 RAG / HyDE 協同運作",
      ],
    },
  ];

  var colW = 2.9, colH = 4.1, colGap = 0.22;
  var totalW = 3 * colW + 2 * colGap; // 9.14
  var startX = (10 - totalW) / 2;     // 0.43

  cols.forEach(function(col, i) {
    var x = startX + i * (colW + colGap);
    var y = 1.12;

    s.addShape(pres.shapes.RECTANGLE, {
      x: x, y: y, w: colW, h: colH,
      fill: { color: WH }, line: { color: CB },
      shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.1 },
    });
    var hdrH = 1.1;
    s.addShape(pres.shapes.RECTANGLE, { x: x, y: y, w: colW, h: hdrH, fill: { color: col.color }, line: { color: col.color } });

    // Abbreviation — tall enough for 1 or 2 lines of 22pt
    var abbrItems = col.abbr.split("\n").map(function(t, j, arr) {
      return { text: t, options: { breakLine: j < arr.length - 1 } };
    });
    s.addText(abbrItems, {
      x: x + 0.08, y: y + 0.05, w: colW - 0.16, h: 0.65,
      fontSize: 22, fontFace: "Arial Black", color: WH,
      bold: true, align: "center", valign: "middle", margin: 0,
    });
    s.addText(col.full, {
      x: x + 0.08, y: y + 0.72, w: colW - 0.16, h: 0.36,
      fontSize: 9, fontFace: "Calibri", color: "C8E6C9",
      align: "center", valign: "top", margin: 0,
    });

    var items = col.items.map(function(t, j) {
      return { text: t, options: { bullet: true, breakLine: j < col.items.length - 1 } };
    });
    s.addText(items, {
      x: x + 0.14, y: y + hdrH + 0.08, w: colW - 0.28, h: colH - hdrH - 0.15,
      fontSize: 12, fontFace: "Calibri", color: BT,
      valign: "top", paraSpaceAfter: 5,
    });
  });
})();

// ══════════════════════════════════════════════════
// SLIDE 7 — 系統功能展示
// ══════════════════════════════════════════════════
(function() {
  var s = pres.addSlide();
  s.background = { color: WH };
  addHeader(s, "系統功能展示", "System Features");

  var cardH = 4.12;

  // ── Left: Personal ───────────────────────────
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 1.1, w: 4.35, h: cardH,
    fill: { color: LG }, line: { color: CB },
    shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.08 },
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 1.1, w: 4.35, h: 0.6, fill: { color: DG }, line: { color: DG } });
  s.addText("📱  個人記帳功能", {
    x: 0.42, y: 1.1, w: 4.15, h: 0.6,
    fontSize: 15.5, fontFace: "Calibri", color: WH,
    bold: true, align: "left", valign: "middle", margin: 0,
  });

  var personal = [
    { icon: "✏️", title: "自然語言記帳",    desc: "「早餐80元」即可自動建立記帳，無需填表" },
    { icon: "📷", title: "收據圖片記帳",    desc: "拍照上傳，VLM 自動辨識金額、類別、日期" },
    { icon: "🔍", title: "智慧查詢 (RAG)", desc: "「上週吃飯花多少？」等自然語言消費查詢" },
    { icon: "📊", title: "消費統計儀表板",  desc: "圓餅圖、長條圖、記錄明細，即時更新顯示" },
  ];
  personal.forEach(function(f, i) {
    var fy = 1.82 + i * 0.83;
    s.addText(f.icon, { x: 0.45, y: fy, w: 0.42, h: 0.3, fontSize: 16, align: "center", valign: "middle", margin: 0 });
    s.addText(f.title, { x: 0.92, y: fy + 0.02, w: 3.55, h: 0.28, fontSize: 13, fontFace: "Calibri", color: DG, bold: true, align: "left", valign: "middle", margin: 0 });
    s.addText(f.desc,  { x: 0.92, y: fy + 0.3,  w: 3.55, h: 0.38, fontSize: 11.5, fontFace: "Calibri", color: MT, align: "left", valign: "top", margin: 0 });
    if (i < personal.length - 1) {
      s.addShape(pres.shapes.LINE, { x: 0.45, y: fy + 0.73, w: 4.0, h: 0, line: { color: "D4ECD4", width: 1 } });
    }
  });

  // ── Right: Group ─────────────────────────────
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.05, y: 1.1, w: 4.65, h: cardH,
    fill: { color: LG }, line: { color: CB },
    shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.08 },
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.05, y: 1.1, w: 4.65, h: 0.6, fill: { color: MG }, line: { color: MG } });
  s.addText("👥  群組分帳功能", {
    x: 5.18, y: 1.1, w: 4.44, h: 0.6,
    fontSize: 15.5, fontFace: "Calibri", color: WH,
    bold: true, align: "left", valign: "middle", margin: 0,
  });

  var group = [
    { icon: "@",  title: "@mention 觸發",  desc: "群組內 @機器人 即觸發，支援含空格多字名稱" },
    { icon: "💸", title: "AA 分帳計算",    desc: "「三個人平分 @A @B」→ 自動算每人金額" },
    { icon: "📋", title: "欠款記錄追蹤",   desc: "成員欠款一覽，可點擊查看各筆分帳明細" },
    { icon: "✅", title: "一鍵結清欠款",   desc: "標記結清後即時同步更新儀表板欠款面板" },
  ];
  group.forEach(function(f, i) {
    var fy = 1.82 + i * 0.83;
    var isAt = (f.icon === "@");
    s.addText(f.icon, { x: 5.2, y: fy, w: 0.42, h: 0.3, fontSize: isAt ? 18 : 16, fontFace: isAt ? "Arial Black" : "Calibri", color: isAt ? DG : undefined, bold: isAt, align: "center", valign: "middle", margin: 0 });
    s.addText(f.title, { x: 5.67, y: fy + 0.02, w: 3.85, h: 0.28, fontSize: 13, fontFace: "Calibri", color: DG, bold: true, align: "left", valign: "middle", margin: 0 });
    s.addText(f.desc,  { x: 5.67, y: fy + 0.3,  w: 3.85, h: 0.38, fontSize: 11.5, fontFace: "Calibri", color: MT, align: "left", valign: "top", margin: 0 });
    if (i < group.length - 1) {
      s.addShape(pres.shapes.LINE, { x: 5.2, y: fy + 0.73, w: 4.35, h: 0, line: { color: "D4ECD4", width: 1 } });
    }
  });
})();

// ══════════════════════════════════════════════════
// SLIDE 8 — 結論與未來展望
// ══════════════════════════════════════════════════
(function() {
  var s = pres.addSlide();
  s.background = { color: DG };

  // Top stripe
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.12, fill: { color: AG }, line: { color: AG } });

  // Title area
  s.addText("結論與未來展望", {
    x: 0.45, y: 0.15, w: 9.1, h: 0.72,
    fontSize: 30, fontFace: "Arial Black", color: WH,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  s.addText("Conclusion & Future Work", {
    x: 0.45, y: 0.87, w: 9.1, h: 0.3,
    fontSize: 12.5, fontFace: "Calibri", color: "A8D5B5",
    align: "left", valign: "top", margin: 0,
  });

  // Divider
  s.addShape(pres.shapes.LINE, { x: 0.45, y: 1.23, w: 9.1, h: 0, line: { color: PG, width: 1 } });

  // ── Left: Results ─────────────────────────────
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 1.38, w: 4.4, h: 3.78,
    fill: { color: MG, transparency: 30 }, line: { color: PG, width: 1 },
  });
  s.addText("🏆  專案成果", {
    x: 0.5, y: 1.5, w: 4.0, h: 0.42,
    fontSize: 16, fontFace: "Calibri", color: AG,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "完整實作 LINE Bot 智慧記帳系統", options: { bullet: true, breakLine: true } },
    { text: "整合 RAG / HyDE / LLM / VLM / n8n 五大技術", options: { bullet: true, breakLine: true } },
    { text: "支援個人記帳與群組 AA 分帳", options: { bullet: true, breakLine: true } },
    { text: "收據圖片辨識，高準確率自動建立記帳", options: { bullet: true, breakLine: true } },
    { text: "即時 Web 儀表板呈現完整消費分析", options: { bullet: true } },
  ], {
    x: 0.5, y: 2.02, w: 4.0, h: 3.0,
    fontSize: 13.5, fontFace: "Calibri", color: "E8F5E9",
    valign: "top", paraSpaceAfter: 9,
  });

  // ── Right: Future ─────────────────────────────
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.1, y: 1.38, w: 4.6, h: 3.78,
    fill: { color: MG, transparency: 30 }, line: { color: PG, width: 1 },
  });
  s.addText("🚀  未來展望", {
    x: 5.3, y: 1.5, w: 4.2, h: 0.42,
    fontSize: 16, fontFace: "Calibri", color: AG,
    bold: true, align: "left", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "串接銀行 / 信用卡帳單自動同步", options: { bullet: true, breakLine: true } },
    { text: "多用戶帳本與群組消費比較報表", options: { bullet: true, breakLine: true } },
    { text: "預算設定與超支即時警示通知", options: { bullet: true, breakLine: true } },
    { text: "支援更多語言、幣別與匯率換算", options: { bullet: true, breakLine: true } },
    { text: "語音記帳（STT 語音轉文字辨識）", options: { bullet: true } },
  ], {
    x: 5.3, y: 2.02, w: 4.2, h: 3.0,
    fontSize: 13.5, fontFace: "Calibri", color: "E8F5E9",
    valign: "top", paraSpaceAfter: 9,
  });

  // Bottom stripe
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.52, w: 10, h: 0.1, fill: { color: AG }, line: { color: AG } });
})();

// ── Write file ────────────────────────────────────
var outPath = "C:\\Users\\cchen\\OneDrive\\桌面\\期末總覽\\ai-accounting-bot\\AI智慧記帳助理_期末簡報.pptx";
pres.writeFile({ fileName: outPath })
  .then(function() { console.log("✅ 簡報已產生：" + outPath); })
  .catch(function(e) { console.error("❌ 錯誤:", e); process.exit(1); });
