"""P12-IMPL-01 — deterministic invoice header + item-table parsing.
This module is the parsing vocabulary introduced by the P12-IMPL-01 PDF
extraction foundation. It is deliberately:
pure — functions over text, no I/O, no side effects, no database;
deterministic — no AI, no model, no randomness;
fail-closed — a value is returned only when the document actually supports
it; anything uncertain is left to the caller as `None` so the existing
`unresolved` mechanism can report it. Nothing is fabricated.
It is consumed by :mod:`services.extraction_suggestions`, which is the existing
"raw text → suggested `extracted_data`" adapter. No parallel extraction
system is created: the deterministic :class:`engines.extraction.DocumentExtractionEngine`
still owns generic `Key: value` and named-pattern fields, and this module only
adds the invoice-specific structures the canonical corpus requires:
a supplier document-header strategy that does not rely on a literal
`Supplier:` label (with guards, see :func:`extract_supplier_header`);
unambiguous date normalisation to ISO;
billing period ranges (start/end);
the item-table region and its rows (description/quantity/unit/rate/net).
Governance note (P12-IMPL-01 §23): this is a deterministic, always-on parse of an
explicit item table with hard exclusions. It is not the P1 shaper and does
not change P1's mode, allowlist or promotion state.
"""
from __future__ import annotations
import re
from typing import Optional


# ── dates ───────────────────────────────────────────────────────────────────

#: Month token -> month number. Keys are matched against the first 4 then first 3
#: letters of the printed month name, so they must be bare tokens with no
#: padding: a trailing space here silently breaks every month-name date and
#: every printed billing period (``Feb 02, 2026`` / ``1 February 2026``).
_MONTHS = {
    "jan": 1,  "feb": 2,  "mar": 3,  "apr": 4,  "may": 5,  "jun": 6,
    "jul": 7,  "aug": 8,  "sep": 9,  "sept": 9,  "oct": 10,  "nov": 11,  "dec": 12,
}

_ISO_DATE_RE = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_NUMERIC_DATE_RE = re.compile(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$")
_MONTH_NAME_FIRST_RE = re.compile(
    r"^([A-Za-z]{3,9}).?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})$"
)
_DAY_MONTH_NAME_RE = re.compile(
    r"^(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9}).?,?\s+(\d{4})$"
)


def _iso(year: int, month: int, day: int) -> Optional[str]:
    if not (1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2200):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_date(value: Optional[str]) -> Optional[str]:
    """Normalise a printed date to `YYYY-MM-DD`; `None` when not certain.
    Accepted unambiguous forms: ``YYYY-MM-DD`` and month-name forms
    (``Feb 02, 2026``, ``2 February 2026``).
    ``d{1,2}-m{1,2}-y{4}`` is interpreted **day-first** (UK invoice convention,
    matching the corpus and the product's locale). Day-first is chosen
    deliberately and deterministically rather than guessed per document, and the
    caller always preserves the raw printed string, so an ambiguous source value
    is never silently lost.
    """
    if not value:
        return None
    text = " ".join(str(value).strip().split())
    if not text:
        return None
    m = _ISO_DATE_RE.match(text)
    if m:
        return _iso(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = _NUMERIC_DATE_RE.match(text)
    if m:
        return _iso(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    m = _MONTH_NAME_FIRST_RE.match(text)
    if m:
        month = _MONTHS.get(m.group(1)[:4].lower()) or _MONTHS.get(m.group(1)[:3].lower())
        if month:
            return _iso(int(m.group(3)), month, int(m.group(2)))
    m = _DAY_MONTH_NAME_RE.match(text)
    if m:
        month = _MONTHS.get(m.group(2)[:4].lower()) or _MONTHS.get(m.group(2)[:3].lower())
        if month:
            return _iso(int(m.group(3)), month, int(m.group(1)))
    return None


#: Separators between the two ends of a printed billing period.
_PERIOD_SPLIT_RE = re.compile(r"\s*(?:–|—|--|to)\s*|\s+-\s+", re.IGNORECASE)


def parse_period(value: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Split a printed period into `(start_iso, end_iso)` dates.
    Returns (None, None) unless **both** ends parse — an end date is never
    invented, and a single date is not promoted to a period.
    """
    if not value:
        return (None, None)
    parts = [p for p in _PERIOD_SPLIT_RE.split(str(value).strip()) if p.strip()]
    if len(parts) != 2:
        return (None, None)
    start, end = parse_date(parts[0]), parse_date(parts[1])
    if not start or not end:
        return (None, None)
    return (start, end)


# ── supplier document-header strategy ───────────────────────────────────────

#: Company-name evidence tokens. A header line is treated as a supplier identity
#: only when it carries commercial-name evidence AND is embedded in an address
#: block — never merely because it is the first line.
_COMPANY_MARKERS = re.compile(
    r"(?i)\b(ltd|limited|plc|llp|inc|incorporated|corp|corporation|company|group|"
    r"holdings|partners|solutions|services|systems|supplies|supply|recycling|"
    r"utilities|energy|logistics|environmental|industries)\b"
)

_POSTCODE_RE = re.compile(r"(?i)\b[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}\b")

#: A document-type marker that ends the sender header block.
_DOC_MARKER_RE = re.compile(
    r"(?i)^\s*(?:tax\s+|vat\s+|waste\s+|utility\s+)?"
    r"(invoice|bill|statement|credit\s+note|remittance|delivery\s+note|receipt)\b"
)

_AMOUNTISH_RE = re.compile(r"[£$€]|\b\d[\d,]*\.\d{2}\b")
_WORD_RE = re.compile(r"[A-Za-z]+")

#: Recipient/customer markers — lines starting with these are NEVER the supplier.
_RECIPIENT_MARKERS = (
    "recipient:", "customer:", "bill to:", "client:", "buyer:",
)


def _strip_decorative(line: str) -> str:
    """Strip leading non-alphabetic decorative characters (♦, !, ", ★, ●, etc.).
    Returns the cleaned line for scoring purposes. The original line is never
    modified in storage — only used for evidence scoring.
    """
    return re.sub(r"^[^A-Za-z]+", "", line).strip()


def _header_evidence(line: str, following: list[str]) -> int:
    stripped = line.strip()
    if not (3 <= len(stripped) <= 80):
        return 0
    if _AMOUNTISH_RE.search(stripped) or _POSTCODE_RE.fullmatch(stripped):
        return 0
    if parse_date(stripped):
        return 0

    # Reject lines that are clearly the document recipient, not sender
    lower = stripped.lower()
    if any(lower.startswith(m) for m in _RECIPIENT_MARKERS):
        return 0

    # Strip leading decorative characters for scoring
    clean = _strip_decorative(stripped)
    if len(clean) < 3:
        return 0

    # Find all individual alphabetic words
    words = _WORD_RE.findall(clean)
    if len(words) < 2:
        return 0
    
    # Check if at least one word starts with an uppercase letter
    if not any(w[0].isupper() for w in words):
        return 0

    # Base score: company marker present
    score = 1 if _COMPANY_MARKERS.search(clean) else 0

    # Boost: company name with address context is more likely the supplier
    if _COMPANY_MARKERS.search(clean):
        score += 1

    # Address context: the next few lines of the header block look like an address
    for nxt in following[:4]:
        candidate = nxt.strip()
        if _POSTCODE_RE.search(candidate) or (
            candidate and any(ch.isdigit() for ch in candidate)
        ):
            score += 1
            break
    return score


def extract_supplier_header(text: str, max_header_lines: int = 12) -> tuple[Optional[str], dict]:
    """Detect the sender (supplier) identity from an invoice header block.
    Returns ``(supplier_name_or_None, evidence)``. ``None`` means *uncertain* and
    the caller must keep the field unresolved — this function never guesses.
    The strategy is structural, never positional-circular: a candidate must be a
    plausible company name **and** sit inside an address block that terminates at
    the document-type marker, and the best candidate must strictly outrank the
    runner-up.
    """
    lines = [ln.strip() for ln in (text or "").splitlines()]
    marker = len(lines)
    for index, line in enumerate(lines[:max_header_lines]):
        if _DOC_MARKER_RE.match(line):
            marker = index
            break
    else:
        marker = min(marker, max_header_lines)
    block = lines[:marker]
    scored: list[tuple[int, int, str]] = []
    for index, line in enumerate(block):
        score = _header_evidence(line, block[index + 1:])
        if score:
            scored.append((score, -index, line))
    if not scored:
        return (None, {"strategy": "header_block", "candidates": [], "reason": "no candidate line"})
    scored.sort(reverse=True)
    best = scored[0]
    runner_up = scored[1] if len(scored) > 1 else None
    evidence = {
        "strategy": "header_block",
        "candidates": [{"line": s[2], "score": s[0]} for s in scored],
        "marker_line": lines[marker] if marker < len(lines) else None,
    }
    if runner_up and runner_up[0] >= best[0]:
        evidence["reason"] = "ambiguous header candidates"
        return (None, evidence)
    if best[0] < 2:
        evidence["reason"] = "insufficient header evidence"
        return (None, evidence)
    evidence["selected"] = best[2]
    return (best[2], evidence)


# ── item table ──────────────────────────────────────────────────────────────

#: B-02 (CT-CARBONTALLY-FOUNDATION-CLOSURE-02). The header is anchored on the
#: first column label. The measured real corpus prints either
#: `Description …` or `Item …` — e.g. `border_double_fuel.pdf` (text layer,
#: extracted 2026-10-09) prints exactly
#: `Item Quantity Unit Price Amount` — so `item` is accepted as a first
#: column label alongside `description` (and the `item description` /
#: `details` spellings for the same column). Nothing else about the header
#: vocabulary, the column order, or the trailing total-column set changes.
_TABLE_HEADER_RE = re.compile(
    r"(?i)^\s*(?:item\s+description|item|description|details|service)\s+"
    # Quantity column. The measured corpus prints `Qty`, `Quantity` AND
    # `Consumption` — e.g. `Service ConsumptionUnit Unit Price Total` — and the
    # label is frequently squashed against the following column
    # ("ConsumptionUnit"), hence `\s*` (not `\s+`) before the unit label.
    r"(?:qty|quantity|consumption|volume)?\s*unit\s*"
    r"(?:rate|unit\s+price|price)?\s+"
    r"(?:subtotal|net\s+amount|net\s+total|amount|total)\s*$"
)

#: B-02 — the currency token printed in front of a money column. The same real
#: document prints the ISO code (`GBP1.40`, `GBP3,071.20`) rather than, and
#: as well as, the symbol (`£1.40`), so both forms are accepted. This is a
#: prefix on the rate/amount columns only: a currency token in the unit column
#: is still rejected by :func:`canonical_unit` (measured P1 defect guard, kept).
_CURRENCY_PREFIX = r"(?:(?:[£$€]|(?i:gbp|eur|usd))\s*)?"

#: Optional second word for the multi-word unit spellings that exist in
#: `_UNIT_ALIASES` ("cubic metres"). A closed alternation rather than a generic
#: `[A-Za-z]+` on purpose: a generic word would swallow a following currency code
#: ("units GBP" would be captured as the unit, `canonical_unit` would reject it,
#: and the row would be dropped).
_MULTIWORD_UNIT_TAIL = r"(?:\s+(?:metres?|meters?))?"

_ROW_RE = re.compile(
    r"^(?P<desc>.+?)\s+(?P<qty>\d{1,3}(?:[,\s]\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s+"
    r"(?P<unit>[A-Za-z][A-Za-z³\-]{0,15}" + _MULTIWORD_UNIT_TAIL + r")\s+"
    + _CURRENCY_PREFIX
    + r"(?P<rate>\d[\d,]*(?:\.\d+)?)\s+"
    + _CURRENCY_PREFIX
    + r"(?P<amount>\d[\d,]*(?:\.\d+)?)$"
)

#: Lines that terminate the item-table region. Labels are matched on the printed
#: prefix; the vocabulary covers the total/tax/payment/footer labels measured in
#: the corpus (Subtotal, Net Amount, Net Total, Net Payable, VAT, Tax, GST, Total,
#: Total Due, Payment Information, Bank, Terms, Page n, ...).
_TABLE_STOP_RE = re.compile(
    r"(?i)^\s*(?:sub\s+total|net\s+amount|net\s+total|net\s+payable|vat|gst|tax|"
    r"total|amount\s+due|balance|payment|bank|account|sort\s+code|iban|swift|"
    r"reference|terms|notes|page\s*\d|approved|paid|company\s+reg|vat\s+no)\b"
)

#: A currency token is never a physical activity unit.
_CURRENCY_TOKENS = {"gbp", "eur", "usd", "pounds", "pound", "sterling", "£", "€", "$"}

#: Unit alias → canonical token (mass + distance aliases only; the repository's
#: unit vocabulary otherwise governs).
_UNIT_ALIASES = {
    "t": "tonnes", "ton": "tonnes", "tons": "tonnes",
    "tonne": "tonnes", "tonnes": "tonnes",
    # B-03a (REMEDIATION-03): `mi` is the standard mileage abbreviation printed
    # in the item table's unit column ("700 mi"). `miles` is already an
    # accepted physical unit in this vocabulary and in `core.units`, so the
    # alias is a missing spelling — not new vocabulary. Measured on the local
    # corpus before the fix: 36 printed rows across the travel documents were
    # dropped entirely (ground truth expected 3 lines each).
    "mi": "miles", "mile": "miles", "miles": "miles",
    # Extended vocabulary for multi-word and hyphenated units
    "kilowatt-hours": "kwh",
    "kilowatt-hour": "kwh",
    "kilowatthours": "kwh",
    "cubic metres": "m3",
    "cubic meters": "m3",
    "cubic metre": "m3",
    "cubic meter": "m3",
    # B-04: the corpus prints the long spelling in the item table's unit column
    # ("89 kilometres"). `km` was already the canonical token; only the spelling
    # was missing, so every transport/logistics row was dropped.
    "kilometres": "km", "kilometers": "km",
    "kilometre": "km", "kilometer": "km",
    # `units` / `unit` / `each` are deliberately ABSENT: they are count tokens,
    # and B-03 pins `canonical_unit` to reject them (fail-closed) pending the
    # PO decision PD-C. Do not reintroduce them to improve a metric.
    "l": "litres",
}

_KNOWN_UNITS_PARSER = {
    "kwh", "mwh", "m3", "m³", "litres", "liters", "litre", "liter", "l",
    "tonnes", "kg", "miles", "km", "mile", "grosscv",
    # Extended vocabulary
    "kilowatt-hours", "kilowatt-hour",
    "cubic metres", "cubic meters", "cubic metre", "cubic meter",
    # B-03 / PD-C: no "units" count token here — see `_UNIT_ALIASES`.
}


#: Individual column labels recognised in multi-line headers.
#: Each line of the header block is checked against these.
_COLUMN_LABELS = {
    # First column (description)
    "description", "item", "service", "details", "activity",
    # Quantity column
    "qty", "quantity", "consumption", "volume",
    # Unit column
    "unit", "units",
    # Rate column
    "rate", "price", "unit price", "unit rate",
    # Amount column
    "amount", "total", "subtotal", "sub total", "net amount",
    "net total", "line total",
}

#: Minimum number of recognised column labels on consecutive lines
#: to declare a multi-line table header.
_MIN_HEADER_LABELS = 3


def _find_multiline_header(lines: list[str], max_scan: int = 30) -> int | None:
    """Detect a table header spread across consecutive single-label lines.

    Returns the index of the first data row (i.e., one past the last header
    label line), or None if no multi-line header is found.

    This handles synthetic PDFs where each column label is printed on its own
    line (e.g., "Description" / "Qty" / "Unit" / "Rate" / "Amount" on separate
    lines) rather than on a single header row.
    """
    for i in range(min(len(lines), max_scan)):
        label = lines[i].strip().lower()
        if label not in _COLUMN_LABELS:
            continue

        # Count consecutive recognised labels starting from this line
        count = 1
        j = i + 1
        while j < min(len(lines), max_scan):
            next_label = lines[j].strip().lower()
            if next_label in _COLUMN_LABELS:
                count += 1
                j += 1
            else:
                break

        if count >= _MIN_HEADER_LABELS:
            return j  # First data row is after the last label line

    return None


def _to_number(value: str) -> float:
    """Parse a printed numeric value, stripping commas AND spaces.
    Space-stripping is required for space-separated thousands (e.g., "2 200" → 2200).
    """
    return float(str(value).replace(",", "").replace(" ", ""))


def canonical_unit(token: str) -> Optional[str]:
    """Canonical unit token, or `None` when the token is not a physical unit.
    A **currency** token is never a unit (this is the explicit guard against the
    measured P1 defect where GBP was emitted as a unit).
    """
    key = (token or "").strip().lower()
    if not key or key in _CURRENCY_TOKENS:
        return None
    key = _UNIT_ALIASES.get(key, key)
    return key if key in _KNOWN_UNITS_PARSER else None


def _desquash(line: str) -> str:
    """Insert whitespace at common squashing boundaries.
    Examples:
      '600units 29.24 GBP17424.00' → '600 units 29.24 GBP 17424.00'
      '33,600kilowatt-hoursUSD0.20' → '33,600 kilowatt-hours USD 0.20'
    The original printed line is kept verbatim in `source_line` for provenance;
    only the parse input is repaired.
    """
    # digit → letter (e.g., "600units" → "600 units")
    line = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", line)
    # letter → ISO currency code (e.g., "kilowatt-hoursUSD0.20" →
    # "kilowatt-hours USD0.20"). Measured: without this the unit group captures
    # "hoursUSD", canonical_unit() rejects it, and the whole row is dropped.
    line = re.sub(r"(?i)(?<=[a-z])(?=gbp|eur|usd)", " ", line)
    # ISO currency code → digit (e.g., "GBP1.40" → "GBP 1.40")
    line = re.sub(r"(?i)(?<=gbp|eur|usd)(?=\d)", " ", line)
    # letter(s) → digit (e.g., "hours0.20" → "hours 0.20").
    # Requires TWO letters before the digit, so a single-letter label prefix is
    # left intact. Measured defect: "Water supply - Q2 400 cubic metres" was
    # split to "Q 2 400", the quantity group then read "2 400" as one number, and
    # the row was emitted with quantity 2400 instead of the printed 400 — a
    # fabricated 6x overstatement on a compliance-reporting platform.
    line = re.sub(r"(?<=[A-Za-z]{2})(?=\d)", " ", line)
    return line


def extract_invoice_lines(text: str) -> list[dict]:
    """Extract trustworthy item rows from a printed invoice item table.
    Returns a list of dicts, each carrying the printed values plus provenance.
    A row is accepted only when **all** of the following hold:
    1. it appears after a recognised item-table header row
       (:data:`_TABLE_HEADER_RE` OR a multi-line header of consecutive column labels);
    2. it has a non-empty textual description;
    3. it has a numeric quantity in the quantity column region;
    4. its unit token is a physical unit (never a currency);
    5. it is not a total/tax/payment/footer/registration row — the region stops at
       the first :data:`_TABLE_STOP_RE` label, so ``Subtotal``/``Net Amount``/
       ``VAT``/``GST``/``Total``/``Net Payable``/``Payment Information``/``Bank``/
       ``Page n`` can never become lines.
    Arithmetic is **reported, not enforced**: ``arithmetic_ok`` records whether
    ``quantity × rate ≈ net`` within tolerance. It is never used to rewrite a
    printed value.
    """
    lines = (text or "").splitlines()
    start = None

    # Try 1: Single-line header (existing behaviour)
    for index, raw in enumerate(lines):
        if _TABLE_HEADER_RE.match(raw.strip()):
            start = index + 1
            break

    # Try 2: Multi-line header (NEW — each column label on its own line)
    if start is None:
        start = _find_multiline_header(lines)

    if start is None:
        return []

    rows: list[dict] = []
    for offset, raw in enumerate(lines[start:], start=start + 1):
        printed = raw.strip()
        if not printed:
            continue
        if _TABLE_STOP_RE.match(printed):
            break

        # Apply desquash for parsing; keep original for provenance
        line = _desquash(printed)

        match = _ROW_RE.match(line)
        if not match:
            continue

        unit = canonical_unit(match.group("unit"))
        if not unit:
            continue

        description = " ".join(match.group("desc").split())
        if not description:
            continue

        quantity = _to_number(match.group("qty"))
        rate = _to_number(match.group("rate"))
        amount = _to_number(match.group("amount"))
        deviation = abs(quantity * rate - amount)

        rows.append(
            {
                "line_number": len(rows) + 1,
                "description": description,
                "quantity": quantity,
                "unit": unit,
                "unit_raw": match.group("unit"),
                "unit_price": rate,
                "net_amount": amount,
                "source_line": printed,  # Original, not desquashed — provenance
                "source_line_number": offset,
                "arithmetic_ok": deviation <= max(0.02, abs(amount) * 0.005),
                "arithmetic_deviation": round(deviation, 4),
                "extraction_method": "det:pdf_table",
            }
        )
    return rows
