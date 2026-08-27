#!/usr/bin/env python3
"""CarbonTally — synthetic OCR test document generator.

Reproducible generator for the OCR synthetic-test set (Phase 6 of the OCR
pipeline task). Produces a small electricity-invoice style corpus in the
requested output directory:

- ``electricity_digital.pdf``  — a digital (text-layer) PDF via reportlab
- ``electricity_scanned.pdf``  — a scanned-style PDF (text rendered to an
  image, then wrapped in a PDF via Pillow)
- ``electricity_invoice.jpg``  — a JPG photograph-style invoice image
- ``electricity_invoice.png``  — a PNG of the same layout

No real customer documents are used; the content is deterministic synthetic
fixture data (supplier, quantity+unit, amount/currency, activity, dates).

Usage:
  .venv/bin/python tools/generate_synthetic_documents.py [output_dir]
"""
from __future__ import annotations

import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/synth_docs"


def _build_lines() -> list[str]:
    """The synthetic electricity-invoice text lines (also the ground truth)."""
    return [
        "Meridian Fuel Supplies Ltd",
        "11 Power Road, Manchester M1 4BT",
        "Electricity Supply Invoice",
        "Invoice number: INV-2026-0417",
        "Invoice date: 15/01/2026",
        "Supply address: 1 Carbon Way, Manchester M1 4BT",
        "Billing period: 01/01/2026 - 31/01/2026",
        "Electricity consumption: 12500 kWh",
        "Unit price: 0.25 GBP/kWh",
        "Net amount: 3125.00 GBP",
        "VAT (20%): 625.00 GBP",
        "Total amount: 3750.00 GBP",
        "Payment due: 14/02/2026",
        "Thank you for your business.",
    ]


def _make_digital_pdf(path: str) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(path, pagesize=A4)
    y = 800
    for line in _build_lines():
        c.drawString(60, y, line)
        y -= 28
    c.showPage()
    c.save()


def _make_image(width: int = 1100, height: int = 700) -> "object":
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
    y = 40
    for line in _build_lines():
        draw.text((30, y), line, fill="black", font=font)
        y += 42
    return img


def _make_scanned_pdf(path: str) -> None:
    img = _make_image()
    img.save(path, "PDF", resolution=150.0)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    _make_digital_pdf(os.path.join(OUT, "electricity_digital.pdf"))
    img = _make_image()
    img.save(os.path.join(OUT, "electricity_invoice.png"))
    img.convert("RGB").save(
        os.path.join(OUT, "electricity_invoice.jpg"), "JPEG", quality=92
    )
    _make_scanned_pdf(os.path.join(OUT, "electricity_scanned.pdf"))

    print(f"Generated synthetic documents in {OUT}:")
    for name in sorted(os.listdir(OUT)):
        full = os.path.join(OUT, name)
        print(f"  {name}  ({os.path.getsize(full)} bytes)")
    print("\nGround truth lines:")
    for line in _build_lines():
        print(f"  {line}")


if __name__ == "__main__":
    main()
