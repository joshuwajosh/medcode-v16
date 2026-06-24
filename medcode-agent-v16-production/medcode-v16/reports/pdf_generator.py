"""
MedCode AI V19 — PDF Report Generator
======================================
Generates HIPAA-compliant PDF reports for compliance, billing,
coding accuracy, and patient encounter documentation.
"""
from __future__ import annotations

import os
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from compliance.hipaa_report import HIPAAReportGenerator

_lock = threading.Lock()

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "reports",
)


def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


class _NumberedCanvas:
    """Helper to add page numbers and header/footer to each page."""

    def __init__(self, doc):
        self.doc = doc
        self.pages: List[str] = []

    def afterPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        page_num = canvas.getPageNumber()
        text = f"MedCode AI | Confidential | Page {page_num}"
        canvas.drawCentredString(letter[0] / 2, 0.4 * inch, text)
        canvas.restoreState()


def _build_styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontSize=18,
            spaceAfter=12,
            textColor=colors.HexColor("#1a237e"),
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Heading2"],
            fontSize=13,
            spaceAfter=8,
            textColor=colors.HexColor("#333333"),
        ),
        "section": ParagraphStyle(
            "SectionHeader",
            parent=base["Heading3"],
            fontSize=11,
            spaceBefore=10,
            spaceAfter=4,
            textColor=colors.HexColor("#1565c0"),
        ),
        "body": ParagraphStyle(
            "ReportBody",
            parent=base["BodyText"],
            fontSize=9,
            leading=13,
        ),
        "small": ParagraphStyle(
            "SmallText",
            parent=base["BodyText"],
            fontSize=7,
            leading=9,
            textColor=colors.grey,
        ),
    }


def _make_table(headers: List[str], rows: List[List[str]], col_widths: Optional[List[float]] = None) -> Table:
    data = [headers] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565c0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _risk_color(level: str) -> colors.Color:
    m = {"high": colors.HexColor("#c62828"), "moderate": colors.HexColor("#ef6c00"),
         "low": colors.HexColor("#2e7d32"), "minimal": colors.HexColor("#1565c0"),
         "pass": colors.HexColor("#2e7d32"), "fail": colors.HexColor("#c62828"),
         "warning": colors.HexColor("#ef6c00")}
    return m.get(level.lower(), colors.black)


def _add_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.HexColor("#1a237e"))
    canvas.drawString(0.6 * inch, letter[1] - 0.5 * inch, "MedCode AI — Confidential Report")
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(letter[0] - 0.6 * inch, letter[1] - 0.5 * inch,
                           datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
    canvas.setFont("Helvetica", 8)
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(letter[0] / 2, 0.4 * inch, f"MedCode AI V19 | HIPAA-Compliant | Page {page_num}")
    canvas.restoreState()


class PDFGenerator:
    """Thread-safe PDF report generator using ReportLab."""

    def generate_report(self, report_type: str, data: Dict[str, Any], output_path: str) -> str:
        _ensure_output_dir()
        os.makedirs(os.path.dirname(output_path) or OUTPUT_DIR, exist_ok=True)

        builders = {
            "hipaa_compliance": self._build_hipaa_report,
            "claim_summary": self._build_claim_summary,
            "coding_accuracy": self._build_coding_accuracy,
            "patient_coding": self._build_patient_coding,
        }

        builder = builders.get(report_type)
        if not builder:
            raise ValueError(f"Unknown report type: {report_type}. Use one of: {list(builders.keys())}")

        with _lock:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                leftMargin=0.6 * inch,
                rightMargin=0.6 * inch,
                topMargin=0.8 * inch,
                bottomMargin=0.7 * inch,
            )
            elements = builder(data, _build_styles())
            doc.build(elements, onFirstPage=_add_header_footer, onLaterPages=_add_header_footer)

        return output_path

    def _build_hipaa_report(self, data: Dict[str, Any], s: Dict[str, ParagraphStyle]) -> List:
        gen = HIPAAReportGenerator()
        report = gen.generate_report()
        report_dict = data.get("report", report.to_dict()) if data.get("report") else report.to_dict()

        elements = [
            Paragraph("HIPAA Compliance Report", s["title"]),
            Paragraph(f"Report ID: {report_dict.get('report_id', 'N/A')}", s["small"]),
            Paragraph(f"Generated: {report_dict.get('generated_at', datetime.utcnow().isoformat())}", s["small"]),
            Spacer(1, 0.15 * inch),
        ]

        summary = report_dict.get("summary", {})
        elements.append(Paragraph("Compliance Summary", s["subtitle"]))
        summary_rows = [
            ["Metric", "Value"],
            ["Total Checks", str(summary.get("total_checks", 0))],
            ["Passed", str(summary.get("passed", 0))],
            ["Failed", str(summary.get("failed", 0))],
            ["Warnings", str(summary.get("warnings", 0))],
            ["Compliance Score", f"{summary.get('compliance_score', 0)}%"],
        ]
        elements.append(_make_table(summary_rows[0], summary_rows[1:], col_widths=[3.5 * inch, 2.5 * inch]))
        elements.append(Spacer(1, 0.15 * inch))

        elements.append(Paragraph("Security Controls Status", s["subtitle"]))
        checks = report_dict.get("checks", [])
        if checks:
            check_rows = []
            for c in checks:
                check_rows.append([
                    c.get("check_id", ""),
                    c.get("category", ""),
                    c.get("status", "").upper(),
                    c.get("details", "")[:80],
                ])
            elements.append(_make_table(
                ["Requirement", "Category", "Status", "Details"],
                check_rows,
                col_widths=[1.3 * inch, 1.2 * inch, 0.8 * inch, 3.0 * inch],
            ))
        elements.append(Spacer(1, 0.15 * inch))

        elements.append(Paragraph("Recommendations", s["subtitle"]))
        for rec in report_dict.get("recommendations", []):
            elements.append(Paragraph(f"• {rec}", s["body"]))

        return elements

    def _build_claim_summary(self, data: Dict[str, Any], s: Dict[str, ParagraphStyle]) -> List:
        claims = data.get("claims", [])
        summary = data.get("summary", {})

        elements = [
            Paragraph("Claim Summary Report", s["title"]),
            Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", s["small"]),
            Spacer(1, 0.15 * inch),
        ]

        elements.append(Paragraph("Batch Overview", s["subtitle"]))
        overview_rows = [
            ["Metric", "Value"],
            ["Total Claims", str(summary.get("total_claims", len(claims)))],
            ["Total Charges", f"${summary.get('total_charges', 0):,.2f}"],
            ["Average Charge", f"${summary.get('average_charge', 0):,.2f}"],
            ["Revenue at Risk", f"${summary.get('revenue_at_risk', 0):,.2f}"],
        ]
        elements.append(_make_table(overview_rows[0], overview_rows[1:], col_widths=[3.0 * inch, 3.0 * inch]))
        elements.append(Spacer(1, 0.15 * inch))

        elements.append(Paragraph("Claim Details", s["subtitle"]))
        if claims:
            claim_rows = []
            for c in claims:
                claim_rows.append([
                    c.get("claim_id", ""),
                    c.get("patient_name", "")[:20],
                    c.get("payer_name", "")[:15],
                    f"${c.get('total_charges', 0):,.2f}",
                    c.get("denial_risk", "low").upper(),
                    c.get("status", "draft"),
                ])
            elements.append(_make_table(
                ["Claim ID", "Patient", "Payer", "Charges", "Risk", "Status"],
                claim_rows,
                col_widths=[1.1 * inch, 1.1 * inch, 1.0 * inch, 1.0 * inch, 0.8 * inch, 0.9 * inch],
            ))
        else:
            elements.append(Paragraph("No claims in this report.", s["body"]))

        elements.append(Spacer(1, 0.15 * inch))

        elements.append(Paragraph("Payer Breakdown", s["subtitle"]))
        payer_dist = summary.get("payer_distribution", {})
        if payer_dist:
            payer_rows = [[p, str(n)] for p, n in payer_dist.items()]
            elements.append(_make_table(["Payer", "Count"], payer_rows, col_widths=[3.5 * inch, 2.5 * inch]))

        return elements

    def _build_coding_accuracy(self, data: Dict[str, Any], s: Dict[str, ParagraphStyle]) -> List:
        metrics = data.get("metrics", {})
        code_dist = data.get("code_distribution", [])
        specialty = data.get("specialty_breakdown", [])

        elements = [
            Paragraph("Coding Accuracy Report", s["title"]),
            Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", s["small"]),
            Spacer(1, 0.15 * inch),
        ]

        elements.append(Paragraph("Accuracy Metrics", s["subtitle"]))
        metric_rows = [
            ["Metric", "Value"],
            ["Overall Accuracy", f"{metrics.get('accuracy', 0):.1f}%"],
            ["CPT Accuracy", f"{metrics.get('cpt_accuracy', 0):.1f}%"],
            ["ICD Accuracy", f"{metrics.get('icd_accuracy', 0):.1f}%"],
            ["Modifier Accuracy", f"{metrics.get('modifier_accuracy', 0):.1f}%"],
            ["Total Encounters", str(metrics.get('total_encounters', 0))],
            ["Correctly Coded", str(metrics.get('correctly_coded', 0))],
            ["Errors Found", str(metrics.get('errors_found', 0))],
        ]
        elements.append(_make_table(metric_rows[0], metric_rows[1:], col_widths=[3.0 * inch, 3.0 * inch]))
        elements.append(Spacer(1, 0.15 * inch))

        elements.append(Paragraph("Code Distribution", s["subtitle"]))
        if code_dist:
            cd_rows = [[d.get("category", ""), str(d.get("count", 0)), f"{d.get('percentage', 0):.1f}%"] for d in code_dist]
            elements.append(_make_table(
                ["Category", "Count", "Percentage"],
                cd_rows,
                col_widths=[2.5 * inch, 1.5 * inch, 2.0 * inch],
            ))
        elements.append(Spacer(1, 0.15 * inch))

        elements.append(Paragraph("Specialty Breakdown", s["subtitle"]))
        if specialty:
            sp_rows = [[sp.get("specialty", ""), str(sp.get("count", 0)), f"{sp.get('accuracy', 0):.1f}%"]
                       for sp in specialty]
            elements.append(_make_table(
                ["Specialty", "Encounters", "Accuracy"],
                sp_rows,
                col_widths=[2.5 * inch, 1.5 * inch, 2.0 * inch],
            ))

        return elements

    def _build_patient_coding(self, data: Dict[str, Any], s: Dict[str, ParagraphStyle]) -> List:
        patient = data.get("patient", {})
        codes = data.get("codes", [])

        elements = [
            Paragraph("Patient Coding Report", s["title"]),
            Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", s["small"]),
            Spacer(1, 0.15 * inch),
        ]

        elements.append(Paragraph("Patient Information", s["subtitle"]))
        info_rows = [
            ["Field", "Value"],
            ["Session ID", patient.get("session_id", "N/A")],
            ["Patient Name", patient.get("patient_name", "REDACTED")],
            ["Date of Service", patient.get("date_of_service", "N/A")],
            ["Encounter Type", patient.get("encounter_type", "N/A")],
            ["Specialty", patient.get("specialty", "N/A")],
        ]
        elements.append(_make_table(info_rows[0], info_rows[1:], col_widths=[2.5 * inch, 3.5 * inch]))
        elements.append(Spacer(1, 0.15 * inch))

        elements.append(Paragraph("Assigned Codes", s["subtitle"]))
        if codes:
            code_rows = []
            for c in codes:
                code_rows.append([
                    c.get("code", ""),
                    c.get("type", ""),
                    c.get("description", "")[:50],
                    c.get("confidence", "N/A"),
                    c.get("status", "final"),
                ])
            elements.append(_make_table(
                ["Code", "Type", "Description", "Confidence", "Status"],
                code_rows,
                col_widths=[0.9 * inch, 0.7 * inch, 2.8 * inch, 1.0 * inch, 0.8 * inch],
            ))
        else:
            elements.append(Paragraph("No codes assigned for this encounter.", s["body"]))

        return elements


def generate_report(report_type: str, data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    _ensure_output_dir()
    if not output_path:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f"{report_type}_{ts}.pdf")

    gen = PDFGenerator()
    return gen.generate_report(report_type, data, output_path)
