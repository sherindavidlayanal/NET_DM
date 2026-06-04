const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, BorderStyle, WidthType, ShadingType, HeadingLevel,
  LevelFormat, PageNumber, NumberFormat, Header, Footer, TabStopType,
  TabStopPosition
} = require("docx");
const fs = require("fs");
const path = require("path");

// ── colour palette (Cardiff and Vale UHB) ────────────────────────────────────
const NAVY  = "003087";
const GOLD  = "C8A951";
const LIGHT = "E8EEF7";
const WHITE = "FFFFFF";
const GREY  = "F5F5F5";
const DARK  = "1A1A1A";
const MID   = "555555";

// ── helpers ───────────────────────────────────────────────────────────────────
const border = (color = "CCCCCC") => ({
  style: BorderStyle.SINGLE, size: 1, color
});
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const allBorders = (c) => ({ top: border(c), bottom: border(c), left: border(c), right: border(c) });
const noBorders   = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function heading(text, level = 1) {
  const sizes = { 1: 28, 2: 24, 3: 22 };
  const colors = { 1: NAVY, 2: NAVY, 3: MID };
  return new Paragraph({
    spacing: { before: level === 1 ? 320 : 240, after: 120 },
    children: [new TextRun({
      text, bold: true, size: sizes[level], color: colors[level], font: "Arial"
    })]
  });
}

function body(text, { bold = false, color = DARK, size = 20, spacing = 160, italic = false } = {}) {
  return new Paragraph({
    spacing: { after: spacing },
    children: [new TextRun({ text, bold, color, size, font: "Arial", italics: italic })]
  });
}

function bullet(text, bold_prefix = "") {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 100 },
    children: [
      ...(bold_prefix ? [new TextRun({ text: bold_prefix + " ", bold: true, size: 20, font: "Arial", color: DARK })] : []),
      new TextRun({ text, size: 20, font: "Arial", color: DARK })
    ]
  });
}

function divider(color = GOLD) {
  return new Paragraph({
    spacing: { after: 0, before: 0 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color, space: 1 } },
    children: []
  });
}

function spacer(after = 160) {
  return new Paragraph({ spacing: { after }, children: [] });
}

// ── KPI card table ────────────────────────────────────────────────────────────
function kpiTable() {
  const kpis = [
    { value: "74.7%", label: "ENETS ready" },
    { value: "84.0%", label: "MDT rate"    },
    { value: "40",    label: "High queries" },
    { value: "104",   label: "Overdue F/U"  },
  ];
  const colW = 2256; // 4 × 2256 = 9024 ≈ content width

  return new Table({
    width: { size: 9024, type: WidthType.DXA },
    columnWidths: [colW, colW, colW, colW],
    rows: [
      new TableRow({
        children: kpis.map(k =>
          new TableCell({
            width: { size: colW, type: WidthType.DXA },
            borders: allBorders(NAVY),
            shading: { fill: NAVY, type: ShadingType.CLEAR },
            margins: { top: 120, bottom: 120, left: 160, right: 160 },
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 60 },
                children: [new TextRun({ text: k.value, bold: true, size: 36, color: GOLD, font: "Arial" })]
              }),
              new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { after: 0 },
                children: [new TextRun({ text: k.label, size: 18, color: WHITE, font: "Arial" })]
              })
            ]
          })
        )
      })
    ]
  });
}

// ── compliance table ──────────────────────────────────────────────────────────
function complianceTable() {
  const rows_data = [
    ["Tumour site recorded",           "100%", "Ready"],
    ["Tumour grade (Ki-67)",           "97%",  "Ready"],
    ["Chromogranin A measured",        "82%",  "Review"],
    ["Imaging at diagnosis",           "95%",  "Ready"],
    ["MDT discussion documented",      "84%",  "Review"],
    ["ENETS all fields complete",      "74.7%","Not Ready"],
    ["Follow-up within 12 months",     "69%",  "Not Ready"],
  ];

  const statusColor = (s) =>
    s === "Ready" ? "1A6B3C" : s === "Review" ? "7A4F00" : "8B1A1A";
  const statusBg = (s) =>
    s === "Ready" ? "E6F4EC" : s === "Review" ? "FEF3CD" : "FDECEA";

  const headerRow = new TableRow({
    tableHeader: true,
    children: ["ENETS Data Field", "Completeness", "Status"].map((h, i) =>
      new TableCell({
        width: { size: [4800, 2112, 2112][i], type: WidthType.DXA },
        borders: allBorders(NAVY),
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({
          children: [new TextRun({ text: h, bold: true, size: 18, color: WHITE, font: "Arial" })]
        })]
      })
    )
  });

  const dataRows = rows_data.map((row, ri) =>
    new TableRow({
      children: row.map((cell, ci) => {
        const isStatus = ci === 2;
        return new TableCell({
          width: { size: [4800, 2112, 2112][ci], type: WidthType.DXA },
          borders: allBorders("CCCCCC"),
          shading: {
            fill: isStatus ? statusBg(cell) : (ri % 2 === 0 ? WHITE : GREY),
            type: ShadingType.CLEAR
          },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({
            children: [new TextRun({
              text: cell,
              size: 18,
              font: "Arial",
              color: isStatus ? statusColor(cell) : DARK,
              bold: isStatus
            })]
          })]
        });
      })
    })
  );

  return new Table({
    width: { size: 9024, type: WidthType.DXA },
    columnWidths: [4800, 2112, 2112],
    rows: [headerRow, ...dataRows]
  });
}

// ── 30-day plan table ─────────────────────────────────────────────────────────
function planTable() {
  const rows_data = [
    ["Days 1–5",   "Audit",      "Full audit of existing databases against ENETS mandatory field list. Identify top data gaps and produce gap report for Lead Consultant."],
    ["Days 6–10",  "Quick wins", "Resolve top 3 recurring data quality issues. Set up automated validation rules in Excel/Access as interim measure while Power BI is configured."],
    ["Days 11–20", "Reporting",  "Build first version of monthly Power BI dashboard: service overview, ENETS compliance tracker, open query log. Share draft with Service Manager for feedback."],
    ["Days 21–30", "Systems",    "Document all data flows and sources. Draft standard operating procedure for data entry. Begin scoping Digital Teams meeting to discuss longer-term database development."],
  ];

  const headerRow = new TableRow({
    tableHeader: true,
    children: ["Period", "Focus", "Actions"].map((h, i) =>
      new TableCell({
        width: { size: [1440, 1440, 6144][i], type: WidthType.DXA },
        borders: allBorders(NAVY),
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({
          children: [new TextRun({ text: h, bold: true, size: 18, color: WHITE, font: "Arial" })]
        })]
      })
    )
  });

  const dataRows = rows_data.map((row, ri) =>
    new TableRow({
      children: row.map((cell, ci) =>
        new TableCell({
          width: { size: [1440, 1440, 6144][ci], type: WidthType.DXA },
          borders: allBorders("CCCCCC"),
          shading: { fill: ri % 2 === 0 ? WHITE : GREY, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({
            children: [new TextRun({
              text: cell,
              size: 18,
              font: "Arial",
              color: DARK,
              bold: ci < 2
            })]
          })]
        })
      )
    })
  );

  return new Table({
    width: { size: 9024, type: WidthType.DXA },
    columnWidths: [1440, 1440, 6144],
    rows: [headerRow, ...dataRows]
  });
}

// ── document ──────────────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } }
      }]
    }]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 20, color: DARK } } }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            spacing: { after: 0 },
            children: [
              new TextRun({ text: "NET Service — Data Management Proposal", bold: true, size: 18, color: NAVY, font: "Arial" }),
              new TextRun({ text: "\t", font: "Arial" }),
              new TextRun({ text: "Cardiff and Vale University Health Board", size: 18, color: MID, font: "Arial" }),
            ],
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }]
          }),
          divider(GOLD),
        ]
      })
    },
    footers: {
      default: new Footer({
        children: [
          divider(NAVY),
          new Paragraph({
            spacing: { before: 80, after: 0 },
            children: [
              new TextRun({ text: "Sherin David Layanal  |  MSc Neuroscience, Queen Mary University of London", size: 16, color: MID, font: "Arial" }),
              new TextRun({ text: "\t", font: "Arial" }),
              new TextRun({ text: "Confidential — prepared for interview purposes", size: 16, color: MID, font: "Arial", italics: true }),
            ],
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }]
          })
        ]
      })
    },
    children: [

      // ── title block ─────────────────────────────────────────────────────────
      spacer(80),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun({ text: "PROPOSED APPROACH TO NET SERVICE", bold: true, size: 36, color: NAVY, font: "Arial" })]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun({ text: "DATA MANAGEMENT AND ENETS CoE READINESS", bold: true, size: 36, color: GOLD, font: "Arial" })]
      }),
      new Paragraph({
        spacing: { after: 200 },
        children: [new TextRun({ text: "Sherin David Layanal  ·  Data Manager (Band 5) Application  ·  May 2025", size: 18, color: MID, font: "Arial", italics: true })]
      }),
      divider(NAVY),
      spacer(200),

      // ── section 1: current challenge ────────────────────────────────────────
      heading("1.  Current challenge", 2),
      body("Neuroendocrine tumour services generate complex, longitudinal patient data spanning multiple health boards, treatment modalities, and external agencies. The South Wales NET Service holds ENETS Centre of Excellence accreditation — a standard that requires consistently complete, auditable patient data for annual international submission and periodic CoE audit visits."),
      body("Without a proactive, year-round data management approach, ENETS field completeness and submission readiness risk degrading gradually — creating a significant workload spike before each submission window and increasing the risk of findings at audit."),
      spacer(80),

      // ── KPI snapshot ────────────────────────────────────────────────────────
      heading("2.  Illustrative service data snapshot", 2),
      body("The table below reflects key data quality indicators from a synthetic 150-patient NET dataset built to mirror the structure of a real service database, using ENETS-mapped fields.", { color: MID, size: 18 }),
      spacer(100),
      kpiTable(),
      spacer(80),
      body("74.7% of patients are currently ENETS submission-ready. The primary driver of incompleteness is overdue follow-up documentation and missing Chromogranin A results — both addressable through targeted data management processes.", { color: MID, size: 18, italic: true }),
      spacer(120),

      // ── section 3: proposed architecture ────────────────────────────────────
      heading("3.  Proposed data management architecture", 2),
      bullet("Centralised ENETS-mapped database with mandatory field validation on entry — preventing incomplete records at source rather than cleaning downstream."),
      bullet("Automated quality rules flagging: missing ENETS fields, overdue follow-up (>365 days), Ki-67/grade mismatches, MDT discussion gaps, and treatment date errors."),
      bullet("Monthly Power BI dashboard (three views): service overview KPIs, ENETS compliance tracker with per-patient submission status, and open query log by severity."),
      bullet("Quarterly completeness audit mapped to ENETS CoE indicators — providing minimum three months lead time to resolve gaps before submission window."),
      bullet("Secure, role-based access in line with Caldicott Principles and GDPR; all systems registered with UHB Data Protection Officer."),
      spacer(120),

      // ── section 4: ENETS compliance ─────────────────────────────────────────
      heading("4.  ENETS field compliance — current state", 2),
      body("Illustrative field-level completeness across the synthetic dataset, demonstrating the type of reporting that would be available to the Lead NET Consultant and Service Manager in real time.", { color: MID, size: 18 }),
      spacer(100),
      complianceTable(),
      spacer(80),
      body("Fields marked 'Not Ready' represent the priority targets for the first 30 days. Chromogranin A and follow-up documentation are the highest-volume gaps.", { color: MID, size: 18, italic: true }),
      spacer(120),

      // ── section 5: 30-day plan ───────────────────────────────────────────────
      heading("5.  First 30 days — proposed actions", 2),
      spacer(60),
      planTable(),
      spacer(120),

      // ── section 6: why this matters ─────────────────────────────────────────
      heading("6.  Alignment with JCC and ENETS standards", 2),
      bullet("JCC service specification compliance: monthly reporting to Lead Consultant, Service Manager, and Finance/Commissioning teams built into dashboard from day one."),
      bullet("ENETS CoE accreditation: year-round submission readiness monitoring replaces annual reactive data cleaning — reducing risk at international audit visits."),
      bullet("Academic research support: validated, complete datasets enable the high-quality outcomes data required for manuscript preparation and clinical governance."),
      bullet("Cross-Wales collaboration: standardised reporting structure facilitates benchmarking with other NET centres across the UK."),
      spacer(160),

      divider(NAVY),
      spacer(80),
      body("This proposal was prepared by Sherin David Layanal as part of the application for the Data Manager (Band 5) post in the NET Service, Cardiff and Vale University Health Board. All patient data used is entirely synthetic and fictional.", { color: MID, size: 16, italic: true }),
    ]
  }]
});

// ── write file ─────────────────────────────────────────────────────────────────
const outDir = path.join(__dirname, "..", "outputs");
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
const outPath = path.join(outDir, "NET_Data_Management_Proposal.docx");

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log(`\nProposal saved → ${outPath}`);
});
