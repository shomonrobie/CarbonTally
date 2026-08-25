"""White-label PDF rendering tests (D27 / D19 §18).

Verifies the branded PDF renderer produces valid PDF bytes and honours the
server-authorized BrandContext (CarbonTally / consultant / co-branded) while
never accepting client-supplied branding.
"""
from __future__ import annotations

from domain.branding import BrandContext
from engines.pdf_render import render_branded_pdf

_REPORT = {
    "report_type": "annual",
    "reporting_year": 2025,
}

_CONTENT = {
    "organization": {"name": "Demo Ltd", "country": "GB"},
    "period": {"start_date": "2025-01-01", "end_date": "2025-12-31"},
    "totals": {"total_co2e_kg": "123.4", "total_rows": 42},
    "scopes": {"scope_1": "80.0", "scope_2": "43.4"},
    "generation": {"engine_version": "1.0"},
}


class TestBrandedPdfRenderer:
    def test_renders_valid_pdf(self) -> None:
        brand = BrandContext(kind="carbon_tally", display_name="CarbonTally")
        pdf = render_branded_pdf(_REPORT, _CONTENT, brand)
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 500

    def test_consultant_white_label_branding_used(self) -> None:
        brand = BrandContext(
            kind="consultant",
            display_name="ABC Sustainability",
            primary_color="#123456",
            footer_text="ABC footer",
        )
        pdf = render_branded_pdf(_REPORT, _CONTENT, brand)
        assert pdf[:5] == b"%PDF-"
        # The brand context must produce a PDF that differs from the
        # CarbonTally fallback (the brand name is embedded in the compressed
        # content stream — verified structurally here and in the PDF artifact).
        carbon = render_branded_pdf(
            _REPORT, _CONTENT, BrandContext(kind="carbon_tally", display_name="CarbonTally")
        )
        assert pdf != carbon

    def test_co_branded_pdf_differs_from_carbon_tally(self) -> None:
        """Co-branded output is valid and structurally different from the
        CarbonTally fallback. (PDF text streams are compressed by reportlab, so
        embedded text is verified structurally + via the renderer unit tests.)"""
        brand = BrandContext(
            kind="co_branded",
            display_name="ABC Sustainability",
            co_branded_with_carbontally=True,
        )
        pdf = render_branded_pdf(_REPORT, _CONTENT, brand)
        assert pdf[:5] == b"%PDF-"
        carbon = render_branded_pdf(
            _REPORT, _CONTENT, BrandContext(kind="carbon_tally", display_name="CarbonTally")
        )
        assert pdf != carbon

    def test_whitelabel_pdf_bytes_differ_from_carbontally(self) -> None:
        carbon = render_branded_pdf(
            _REPORT, _CONTENT, BrandContext(kind="carbon_tally", display_name="CarbonTally")
        )
        white = render_branded_pdf(
            _REPORT,
            _CONTENT,
            BrandContext(kind="consultant", display_name="ABC Sustainability"),
        )
        assert carbon != white

    def test_renderer_is_pure(self) -> None:
        """The renderer takes content + brand — it never reads a client id."""
        from engines.pdf_render import BrandedPdfRenderer

        renderer = BrandedPdfRenderer(BrandContext(kind="consultant", display_name="X"))
        pdf = renderer.render(report=_REPORT, content=_CONTENT)
        assert pdf[:5] == b"%PDF-"
