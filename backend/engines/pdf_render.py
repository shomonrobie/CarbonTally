"""White-label PDF rendering (D27 / D19 §18).

Consumes a report's structured ``generated_content`` plus the SERVER-authorized
:class:`BrandContext` (CarbonTally / consultant / co-branded) and renders a
branded PDF. The branding is always derived server-side from the authorized
consultant relationship — a client-supplied brand input is NEVER accepted.

Modes:
    carbon_tally  -> CarbonTally branding
    consultant    -> consultant white-label (CarbonTally invisible)
    co_branded    -> both brands

The renderer is pure I/O (bytes out); the API layer authorizes the request and
resolves the brand. reportlab is the only rendering dependency.
"""
from __future__ import annotations

import io
from typing import Any, Optional

from reportlab.lib import colors as rlcolors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from domain.branding import CARBON_TALLY_BRAND, BrandContext


def _hex_to_reportlab(value: Optional[str], fallback: str) -> Any:
    """Convert a hex colour to a reportlab color (safe fallback on garbage)."""
    try:
        value = (value or fallback).strip()
        if not value.startswith("#"):
            raise ValueError
        return rlcolors.HexColor(value)
    except Exception:  # noqa: BLE001
        return rlcolors.HexColor(fallback)


def _flatten(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    """Flatten a nested JSON-ish dict into ``(label, value)`` rows."""
    rows: list[tuple[str, str]] = []
    if value is None:
        return rows
    if isinstance(value, dict):
        for key, item in value.items():
            label = f"{prefix} {key}".strip() if prefix else str(key)
            if isinstance(item, (dict, list)):
                rows.extend(_flatten(item, label))
            else:
                rows.append((label, _fmt(item)))
        return rows
    if isinstance(value, list):
        for index, item in enumerate(value):
            rows.extend(_flatten(item, f"{prefix} [{index}]"))
        return rows
    return [(prefix, _fmt(value))]


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    return str(value)


class BrandedPdfRenderer:
    """Render report content into a branded PDF."""

    def __init__(self, brand: BrandContext) -> None:
        self.brand = brand
        self.primary = _hex_to_reportlab(brand.primary_color, CARBON_TALLY_BRAND["primary_color"])
        self.secondary = _hex_to_reportlab(brand.secondary_color, CARBON_TALLY_BRAND["secondary_color"])

    def render(self, *, report: dict[str, Any], content: dict[str, Any]) -> bytes:
        """Return the branded PDF bytes for one report."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=18 * mm,
            bottomMargin=16 * mm,
            title=(report.get("report_type") or "CarbonTally") + " Report",
            author=self.brand.display_name or "CarbonTally",
        )

        styles = getSampleStyleSheet()
        h1 = ParagraphStyle(
            "BrandH1", parent=styles["Heading1"], textColor=self.primary, fontSize=20,
            spaceAfter=2, spaceBefore=10,
        )
        h2 = ParagraphStyle(
            "BrandH2", parent=styles["Heading2"], textColor=self.primary, fontSize=13,
            spaceBefore=8, spaceAfter=2,
        )
        body = ParagraphStyle(
            "BrandBody", parent=styles["BodyText"], fontSize=9.5, leading=13,
            textColor=rlcolors.HexColor("#1e293b"),
        )
        small = ParagraphStyle(
            "BrandSmall", parent=styles["BodyText"], fontSize=8, leading=11,
            textColor=rlcolors.HexColor("#64748b"),
        )

        story: list[Any] = []

        # Header band
        header_table = Table(
            [
                [
                    Paragraph(
                        f'<font color="white"><b>{self._escape(self.brand.display_name or "CarbonTally")}</b></font>',
                        ParagraphStyle("Brand", fontName="Helvetica-Bold", fontSize=16, textColor=rlcolors.white),
                    ),
                    Paragraph(
                        f'<font color="white" size="9">{self._escape(report.get("report_type") or "")}'
                        f' — {self._escape(str(report.get("reporting_year") or ""))}</font>',
                        small,
                    ),
                ]
            ],
            colWidths=[110 * mm, 68 * mm],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.primary),
                    ("TEXTCOLOR", (0, 0), (-1, -1), rlcolors.white),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 6))

        # Section order follows the engine's report sections.
        section_titles = {
            "metadata": "Report metadata",
            "organization": "Organization",
            "period": "Reporting period",
            "totals": "Emissions totals",
            "scopes": "Scope summaries",
            "activities": "Category / activity summaries",
            "validation": "Validation",
            "benchmarking": "Benchmarking",
            "provenance": "Factor provenance",
            "calculation": "Calculation information",
            "lineage": "Source lineage",
            "generation": "Generation metadata",
        }
        for section_id, title in section_titles.items():
            payload = content.get(section_id)
            if not payload:
                continue
            story.append(Paragraph(self._escape(title), h2))
            rows = _flatten(payload)
            if rows:
                data = [[Paragraph(f"<b>{self._escape(k)}</b>", small), Paragraph(self._escape(v), body)] for k, v in rows]
                table = Table(data, colWidths=[70 * mm, 108 * mm])
                table.setStyle(
                    TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.25, rlcolors.HexColor("#e2e8f0")),
                            ("BACKGROUND", (0, 0), (0, -1), rlcolors.HexColor("#f8fafc")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 6))

        # Footer band
        footer_lines = []
        if self.brand.footer_text:
            footer_lines.append(self._escape(self.brand.footer_text))
        if self.brand.website:
            footer_lines.append(self._escape(self.brand.website))
        if self.brand.support_email:
            footer_lines.append(f"Support: {self._escape(self.brand.support_email)}")
        if self.brand.co_branded_with_carbontally:
            footer_lines.append("Powered by CarbonTally")
        story.append(Spacer(1, 10))
        story.append(
            Table(
                [[Paragraph("<br/>".join(footer_lines) or "&nbsp;", small)]],
                colWidths=[178 * mm],
            )
        )

        doc.build(
            story,
            onFirstPage=lambda c, _d: self._draw_footer(c),
            onLaterPages=lambda c, _d: self._draw_footer(c),
        )
        return buffer.getvalue()

    def _draw_footer(self, canvas_obj: canvas.Canvas) -> None:
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 7.5)
        canvas_obj.setFillColor(rlcolors.HexColor("#94a3b8"))
        canvas_obj.drawString(
            16 * mm, 10 * mm,
            f"{self.brand.display_name or 'CarbonTally'} — generated {self._today()}",
        )
        canvas_obj.drawRightString(
            194 * mm, 10 * mm, f"Page {canvas_obj.getPageNumber()}",
        )
        canvas_obj.restoreState()

    @staticmethod
    def _today() -> str:
        from datetime import date

        return date.today().isoformat()

    @staticmethod
    def _escape(value: Any) -> str:
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


def render_branded_pdf(report: dict[str, Any], content: dict[str, Any], brand: BrandContext) -> bytes:
    """One-call renderer: branded PDF bytes for a report."""
    return BrandedPdfRenderer(brand).render(report=report, content=content)
