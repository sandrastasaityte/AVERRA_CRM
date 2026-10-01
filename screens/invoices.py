import csv
import io
from datetime import date
from xml.sax.saxutils import escape

import streamlit as st

from database import get_session
from models import Invoice, Client, Placement

from utils.calculations import calculate_invoice_balance
from utils.helpers import valid_url


# ============================================================
# CONSTANTS
# ============================================================

CURRENCIES = [
    "GBP",
    "EUR",
    "USD",
    "INR",
]

INVOICE_STATUSES = [
    "Draft",
    "Sent",
    "Partially Paid",
    "Paid",
    "Overdue",
    "Cancelled",
]

MAX_INVOICE_NUMBER_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 500
MAX_NOTES_LENGTH = 2000

FILTER_VERSION_KEY = "invoice_filter_version"


# ============================================================
# GENERAL HELPERS
# ============================================================

def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_invoice_number(value):
    value = clean_text(value)
    return " ".join(value.split())


def get_client_name(client):
    if not client:
        return "Unknown Client"

    company_name = clean_text(
        getattr(client, "company_name", None)
    )

    if company_name:
        return company_name

    name = clean_text(
        getattr(client, "name", None)
    )

    return name or "Unknown Client"


def get_client_address(client):
    if not client:
        return ""

    parts = []

    possible_fields = [
        "address",
        "address_line_1",
        "address_line_2",
        "city",
        "county",
        "postcode",
        "postal_code",
        "country",
    ]

    for field in possible_fields:
        value = clean_text(
            getattr(client, field, None)
        )

        if value and value not in parts:
            parts.append(value)

    return ", ".join(parts)


def get_employee_name(employee):
    if not employee:
        return "Unknown Employee"

    full_name = clean_text(
        getattr(employee, "full_name", None)
    )

    if full_name:
        return full_name

    first_name = clean_text(
        getattr(employee, "first_name", None)
    )

    last_name = clean_text(
        getattr(employee, "last_name", None)
    )

    name = " ".join(
        part
        for part in [first_name, last_name]
        if part
    )

    return name or "Unknown Employee"


def get_placement_label(placement):
    if not placement:
        return "No Placement"

    employee_name = get_employee_name(
        getattr(placement, "employee", None)
    )

    position = clean_text(
        getattr(placement, "position", None)
    )

    if employee_name != "Unknown Employee" and position:
        return f"{employee_name} — {position}"

    if employee_name != "Unknown Employee":
        return employee_name

    if position:
        return position

    placement_id = getattr(
        placement,
        "id",
        None,
    )

    if placement_id:
        return f"Placement #{placement_id}"

    return "Placement"


def format_money(amount, currency):
    amount = safe_float(amount)

    currency = clean_text(currency) or "GBP"

    return f"{currency} {amount:,.2f}"


def format_date(value):
    if not value:
        return "—"

    try:
        return value.strftime("%d %b %Y")
    except AttributeError:
        return str(value)


# ============================================================
# INVOICE CALCULATIONS
# ============================================================

def get_balance_due(invoice):
    total = safe_float(
        getattr(
            invoice,
            "total_amount",
            0.0,
        )
    )

    paid = safe_float(
        getattr(
            invoice,
            "amount_paid",
            0.0,
        )
    )

    try:
        balance = safe_float(
            calculate_invoice_balance(
                total,
                paid,
            )
        )
    except Exception:
        balance = total - paid

    return max(
        round(balance, 2),
        0.0,
    )


def get_payment_count(invoice):
    payments = getattr(
        invoice,
        "payments",
        None,
    )

    if payments is None:
        return 0

    try:
        return len(payments)
    except TypeError:
        return 0


def has_payments(invoice):
    return get_payment_count(invoice) > 0


def get_payment_percentage(invoice):
    total = safe_float(
        getattr(
            invoice,
            "total_amount",
            0.0,
        )
    )

    paid = safe_float(
        getattr(
            invoice,
            "amount_paid",
            0.0,
        )
    )

    if total <= 0:
        return 0.0

    percentage = (
        paid / total
    ) * 100

    return max(
        0.0,
        min(
            100.0,
            percentage,
        ),
    )


def get_effective_status(invoice):
    """
    Calculates the operational status shown in the UI.

    The stored database status is not modified automatically.
    """

    stored_status = clean_text(
        getattr(
            invoice,
            "status",
            None,
        )
    )

    if stored_status == "Cancelled":
        return "Cancelled"

    total = safe_float(
        getattr(
            invoice,
            "total_amount",
            0.0,
        )
    )

    paid = safe_float(
        getattr(
            invoice,
            "amount_paid",
            0.0,
        )
    )

    balance = get_balance_due(invoice)

    if total > 0 and paid >= total:
        return "Paid"

    due_date = getattr(
        invoice,
        "due_date",
        None,
    )

    if (
        balance > 0
        and due_date
        and due_date < date.today()
    ):
        return "Overdue"

    if paid > 0 and balance > 0:
        return "Partially Paid"

    return stored_status or "Draft"


def calculate_days_overdue(invoice):
    if get_balance_due(invoice) <= 0:
        return 0

    due_date = getattr(
        invoice,
        "due_date",
        None,
    )

    if not due_date:
        return 0

    if due_date >= date.today():
        return 0

    return (
        date.today() - due_date
    ).days


def get_invoice_age(invoice):
    invoice_date = getattr(
        invoice,
        "invoice_date",
        None,
    )

    if not invoice_date:
        return 0

    if invoice_date > date.today():
        return 0

    return (
        date.today() - invoice_date
    ).days


# ============================================================
# DATA QUALITY HELPERS
# ============================================================

def get_invoice_data_warnings(invoice):
    warnings = []

    total = safe_float(
        getattr(
            invoice,
            "total_amount",
            0.0,
        )
    )

    paid = safe_float(
        getattr(
            invoice,
            "amount_paid",
            0.0,
        )
    )

    subtotal = safe_float(
        getattr(
            invoice,
            "subtotal",
            0.0,
        )
    )

    tax = safe_float(
        getattr(
            invoice,
            "tax",
            0.0,
        )
    )

    if abs(
        total - round(subtotal + tax, 2)
    ) > 0.01:
        warnings.append(
            "Total does not equal subtotal plus tax."
        )

    if paid < 0:
        warnings.append(
            "Amount paid is negative."
        )

    if paid > total:
        warnings.append(
            "Amount paid is greater than the invoice total."
        )

    if (
        getattr(invoice, "due_date", None)
        and getattr(invoice, "invoice_date", None)
        and invoice.due_date < invoice.invoice_date
    ):
        warnings.append(
            "Due date is earlier than invoice date."
        )

    return warnings


# ============================================================
# CURRENCY SUMMARY
# ============================================================

def get_currency_totals(invoices):
    totals = {}

    for invoice in invoices:
        currency = clean_text(
            getattr(
                invoice,
                "currency",
                None,
            )
        ) or "GBP"

        if currency not in totals:
            totals[currency] = {
                "invoice_count": 0,
                "total": 0.0,
                "paid": 0.0,
                "balance": 0.0,
                "overdue": 0.0,
            }

        totals[currency]["invoice_count"] += 1

        totals[currency]["total"] += safe_float(
            getattr(
                invoice,
                "total_amount",
                0.0,
            )
        )

        totals[currency]["paid"] += safe_float(
            getattr(
                invoice,
                "amount_paid",
                0.0,
            )
        )

        balance = get_balance_due(invoice)

        totals[currency]["balance"] += balance

        if get_effective_status(invoice) == "Overdue":
            totals[currency]["overdue"] += balance

    return totals


# ============================================================
# CSV EXPORT
# ============================================================

def get_csv_bytes(invoices):
    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(
        [
            "Invoice Number",
            "Client",
            "Placement",
            "Invoice Date",
            "Due Date",
            "Invoice Age (Days)",
            "Description",
            "Subtotal",
            "Tax",
            "Total Amount",
            "Amount Paid",
            "Balance Due",
            "Payment %",
            "Currency",
            "Stored Status",
            "Effective Status",
            "Days Overdue",
            "Payment Count",
            "Document Link",
            "Notes",
        ]
    )

    for invoice in invoices:
        writer.writerow(
            [
                clean_text(
                    getattr(
                        invoice,
                        "invoice_number",
                        "",
                    )
                ),
                get_client_name(
                    getattr(
                        invoice,
                        "client",
                        None,
                    )
                ),
                get_placement_label(
                    getattr(
                        invoice,
                        "placement",
                        None,
                    )
                ),
                format_date(
                    getattr(
                        invoice,
                        "invoice_date",
                        None,
                    )
                ),
                format_date(
                    getattr(
                        invoice,
                        "due_date",
                        None,
                    )
                ),
                get_invoice_age(invoice),
                clean_text(
                    getattr(
                        invoice,
                        "description",
                        "",
                    )
                ),
                safe_float(
                    getattr(
                        invoice,
                        "subtotal",
                        0.0,
                    )
                ),
                safe_float(
                    getattr(
                        invoice,
                        "tax",
                        0.0,
                    )
                ),
                safe_float(
                    getattr(
                        invoice,
                        "total_amount",
                        0.0,
                    )
                ),
                safe_float(
                    getattr(
                        invoice,
                        "amount_paid",
                        0.0,
                    )
                ),
                get_balance_due(invoice),
                round(
                    get_payment_percentage(invoice),
                    2,
                ),
                clean_text(
                    getattr(
                        invoice,
                        "currency",
                        "",
                    )
                ),
                clean_text(
                    getattr(
                        invoice,
                        "status",
                        "",
                    )
                ),
                get_effective_status(invoice),
                calculate_days_overdue(invoice),
                get_payment_count(invoice),
                clean_text(
                    getattr(
                        invoice,
                        "document_link",
                        "",
                    )
                ),
                clean_text(
                    getattr(
                        invoice,
                        "notes",
                        "",
                    )
                ),
            ]
        )

    return output.getvalue().encode(
        "utf-8-sig"
    )


# ============================================================
# PDF HELPERS
# ============================================================

def pdf_text(value, fallback=""):
    value = clean_text(value)

    if not value:
        value = fallback

    return escape(
        value
    ).replace(
        "\n",
        "<br/>",
    )


def generate_invoice_pdf(invoice):
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import (
            getSampleStyleSheet,
            ParagraphStyle,
        )
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )

    except ImportError:
        raise RuntimeError(
            "PDF generation requires reportlab. "
            "Make sure reportlab is installed."
        )

    try:
        buffer = io.BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "InvoiceTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=22,
            spaceAfter=12,
        )

        right_style = ParagraphStyle(
            "RightStyle",
            parent=styles["Normal"],
            alignment=TA_RIGHT,
        )

        small_style = ParagraphStyle(
            "SmallStyle",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
        )

        story = []

        invoice_number = clean_text(
            getattr(
                invoice,
                "invoice_number",
                "",
            )
        )

        currency = clean_text(
            getattr(
                invoice,
                "currency",
                "",
            )
        ) or "GBP"

        subtotal = safe_float(
            getattr(
                invoice,
                "subtotal",
                0.0,
            )
        )

        tax = safe_float(
            getattr(
                invoice,
                "tax",
                0.0,
            )
        )

        total = safe_float(
            getattr(
                invoice,
                "total_amount",
                0.0,
            )
        )

        paid = safe_float(
            getattr(
                invoice,
                "amount_paid",
                0.0,
            )
        )

        balance = get_balance_due(invoice)

        client = getattr(
            invoice,
            "client",
            None,
        )

        placement = getattr(
            invoice,
            "placement",
            None,
        )

        story.append(
            Paragraph(
                "INVOICE",
                title_style,
            )
        )

        header_data = [
            [
                Paragraph(
                    "<b>Invoice Number</b>",
                    styles["Normal"],
                ),
                Paragraph(
                    pdf_text(invoice_number),
                    styles["Normal"],
                ),
            ],
            [
                Paragraph(
                    "<b>Invoice Date</b>",
                    styles["Normal"],
                ),
                Paragraph(
                    pdf_text(
                        format_date(
                            getattr(
                                invoice,
                                "invoice_date",
                                None,
                            )
                        )
                    ),
                    styles["Normal"],
                ),
            ],
            [
                Paragraph(
                    "<b>Due Date</b>",
                    styles["Normal"],
                ),
                Paragraph(
                    pdf_text(
                        format_date(
                            getattr(
                                invoice,
                                "due_date",
                                None,
                            )
                        )
                    ),
                    styles["Normal"],
                ),
            ],
            [
                Paragraph(
                    "<b>Status</b>",
                    styles["Normal"],
                ),
                Paragraph(
                    pdf_text(
                        get_effective_status(invoice)
                    ),
                    styles["Normal"],
                ),
            ],
        ]

        header_table = Table(
            header_data,
            colWidths=[
                45 * mm,
                45 * mm,
            ],
        )

        header_table.setStyle(
            TableStyle(
                [
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.lightgrey,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(header_table)
        story.append(Spacer(1, 12))

        story.append(
            Paragraph(
                "<b>Bill To</b>",
                styles["Heading3"],
            )
        )

        story.append(
            Paragraph(
                pdf_text(
                    get_client_name(client)
                ),
                styles["Normal"],
            )
        )

        client_address = get_client_address(client)

        if client_address:
            story.append(
                Paragraph(
                    pdf_text(client_address),
                    styles["Normal"],
                )
            )

        story.append(Spacer(1, 10))

        if placement:
            story.append(
                Paragraph(
                    (
                        "<b>Placement:</b> "
                        f"{pdf_text(get_placement_label(placement))}"
                    ),
                    styles["Normal"],
                )
            )

            story.append(
                Spacer(1, 8)
            )

        description = clean_text(
            getattr(
                invoice,
                "description",
                "",
            )
        )

        if not description:
            description = get_placement_label(
                placement
            )

        line_data = [
            [
                Paragraph(
                    "<b>Description</b>",
                    styles["Normal"],
                ),
                Paragraph(
                    "<b>Amount</b>",
                    right_style,
                ),
            ],
            [
                Paragraph(
                    pdf_text(description),
                    styles["Normal"],
                ),
                Paragraph(
                    format_money(
                        subtotal,
                        currency,
                    ),
                    right_style,
                ),
            ],
        ]

        line_table = Table(
            line_data,
            colWidths=[
                125 * mm,
                35 * mm,
            ],
        )

        line_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(line_table)
        story.append(Spacer(1, 12))

        totals_data = [
            [
                Paragraph(
                    "<b>Subtotal</b>",
                    styles["Normal"],
                ),
                Paragraph(
                    format_money(
                        subtotal,
                        currency,
                    ),
                    right_style,
                ),
            ],
            [
                Paragraph(
                    "<b>Tax</b>",
                    styles["Normal"],
                ),
                Paragraph(
                    format_money(
                        tax,
                        currency,
                    ),
                    right_style,
                ),
            ],
            [
                Paragraph(
                    "<b>Total</b>",
                    styles["Normal"],
                ),
                Paragraph(
                    (
                        f"<b>{format_money(total, currency)}</b>"
                    ),
                    right_style,
                ),
            ],
            [
                Paragraph(
                    "<b>Amount Paid</b>",
                    styles["Normal"],
                ),
                Paragraph(
                    format_money(
                        paid,
                        currency,
                    ),
                    right_style,
                ),
            ],
            [
                Paragraph(
                    "<b>Balance Due</b>",
                    styles["Normal"],
                ),
                Paragraph(
                    (
                        f"<b>{format_money(balance, currency)}</b>"
                    ),
                    right_style,
                ),
            ],
        ]

        totals_table = Table(
            totals_data,
            colWidths=[
                125 * mm,
                35 * mm,
            ],
        )

        totals_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(totals_table)
        story.append(Spacer(1, 14))

        notes = clean_text(
            getattr(
                invoice,
                "notes",
                "",
            )
        )

        if notes:
            story.append(
                Paragraph(
                    "<b>Notes</b>",
                    styles["Heading3"],
                )
            )

            story.append(
                Paragraph(
                    pdf_text(notes),
                    styles["Normal"],
                )
            )

            story.append(
                Spacer(1, 10)
            )

        story.append(
            Paragraph(
                (
                    "Payment status: "
                    f"{pdf_text(get_effective_status(invoice))}"
                ),
                small_style,
            )
        )

        story.append(
            Paragraph(
                (
                    "Payment progress: "
                    f"{get_payment_percentage(invoice):.1f}%"
                ),
                small_style,
            )
        )

        days_overdue = calculate_days_overdue(
            invoice
        )

        if days_overdue > 0:
            story.append(
                Paragraph(
                    f"Days overdue: {days_overdue}",
                    small_style,
                )
            )

        story.append(
            Spacer(1, 15)
        )

        story.append(
            Paragraph(
                "Generated by AVERRA Staffing Solutions CRM",
                small_style,
            )
        )

        document.build(story)

        buffer.seek(0)

        return buffer.getvalue()

    except Exception as error:
        raise RuntimeError(
            f"The invoice PDF could not be generated: {error}"
        )


# ============================================================
# VALIDATION
# ============================================================

def validate_invoice_data(
    invoice_number,
    invoice_date,
    due_date,
    subtotal,
    tax,
    total_amount,
    currency,
    status,
    description,
    document_link,
):
    errors = []

    invoice_number = normalize_invoice_number(
        invoice_number
    )

    description = clean_text(
        description
    )

    document_link = clean_text(
        document_link
    )

    if not invoice_number:
        errors.append(
            "Invoice number is required."
        )

    if len(invoice_number) > MAX_INVOICE_NUMBER_LENGTH:
        errors.append(
            (
                "Invoice number cannot exceed "
                f"{MAX_INVOICE_NUMBER_LENGTH} characters."
            )
        )

    if not invoice_date:
        errors.append(
            "Invoice date is required."
        )

    if not due_date:
        errors.append(
            "Due date is required."
        )

    if invoice_date and due_date:
        if due_date < invoice_date:
            errors.append(
                "Due date cannot be earlier than the invoice date."
            )

    subtotal = safe_float(subtotal)
    tax = safe_float(tax)
    total_amount = safe_float(total_amount)

    if subtotal < 0:
        errors.append(
            "Subtotal cannot be negative."
        )

    if tax < 0:
        errors.append(
            "Tax cannot be negative."
        )

    if total_amount <= 0:
        errors.append(
            "Total amount must be greater than zero."
        )

    expected_total = round(
        subtotal + tax,
        2,
    )

    if abs(
        total_amount - expected_total
    ) > 0.01:
        errors.append(
            "Total amount must equal subtotal plus tax."
        )

    if currency not in CURRENCIES:
        errors.append(
            "Please select a valid currency."
        )

    if status not in INVOICE_STATUSES:
        errors.append(
            "Please select a valid invoice status."
        )

    if len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            (
                "Description cannot exceed "
                f"{MAX_DESCRIPTION_LENGTH} characters."
            )
        )

    if document_link:
        try:
            if not valid_url(document_link):
                errors.append(
                    "Document link is not a valid URL."
                )
        except Exception:
            errors.append(
                "Document link is not a valid URL."
            )

    return errors


def validate_payment_status(
    status,
    total_amount,
    amount_paid,
    due_date,
    invoice=None,
):
    errors = []

    total_amount = safe_float(
        total_amount
    )

    amount_paid = safe_float(
        amount_paid
    )

    if amount_paid < 0:
        errors.append(
            "Amount paid cannot be negative."
        )

    if amount_paid > total_amount:
        errors.append(
            "Amount paid cannot exceed the invoice total."
        )

    if status == "Paid":
        if amount_paid < total_amount:
            errors.append(
                "A Paid invoice must be fully paid."
            )

    if status == "Partially Paid":
        if amount_paid <= 0:
            errors.append(
                "A Partially Paid invoice must have a payment."
            )

        elif amount_paid >= total_amount:
            errors.append(
                "A fully paid invoice should use the Paid status."
            )

    if status == "Overdue":
        if amount_paid >= total_amount:
            errors.append(
                "A fully paid invoice cannot be Overdue."
            )

        elif not due_date:
            errors.append(
                "An Overdue invoice must have a due date."
            )

        elif due_date >= date.today():
            errors.append(
                "Overdue status requires a due date in the past."
            )

    if status == "Draft":
        if amount_paid > 0:
            errors.append(
                "A Draft invoice cannot have recorded payments."
            )

    if status == "Cancelled":
        if invoice is not None and has_payments(invoice):
            errors.append(
                (
                    "An invoice with recorded payments "
                    "cannot be cancelled."
                )
            )

    return errors


# ============================================================
# DUPLICATE CHECK
# ============================================================

def find_duplicate_invoice(
    session,
    invoice_number,
    exclude_id=None,
):
    normalized_number = normalize_invoice_number(
        invoice_number
    ).lower()

    if not normalized_number:
        return None

    invoices = (
        session.query(Invoice)
        .all()
    )

    for invoice in invoices:
        if (
            exclude_id is not None
            and invoice.id == exclude_id
        ):
            continue

        existing_number = normalize_invoice_number(
            getattr(
                invoice,
                "invoice_number",
                "",
            )
        ).lower()

        if existing_number == normalized_number:
            return invoice

    return None


# ============================================================
# SESSION STATE
# ============================================================

def clear_invoice_state():
    st.session_state.editing_invoice_id = None
    st.session_state.confirm_delete_invoice_id = None


def reset_invoice_filters():
    current_version = st.session_state.get(
        FILTER_VERSION_KEY,
        0,
    )

    st.session_state[FILTER_VERSION_KEY] = (
        current_version + 1
    )


# ============================================================
# MAIN SCREEN
# ============================================================

def show_invoices():
    st.title("Invoices")

    st.caption(
        "Create, manage, track and export client invoices."
    )

    session = get_session()

    if "editing_invoice_id" not in st.session_state:
        st.session_state.editing_invoice_id = None

    if "confirm_delete_invoice_id" not in st.session_state:
        st.session_state.confirm_delete_invoice_id = None

    if FILTER_VERSION_KEY not in st.session_state:
        st.session_state[FILTER_VERSION_KEY] = 0

    try:
        # ====================================================
        # LOAD CLIENTS
        # ====================================================

        clients = (
            session.query(Client)
            .order_by(Client.id.desc())
            .all()
        )

        if not clients:
            st.warning(
                "No clients exist yet. Create a client before creating an invoice."
            )
            return

        # ====================================================
        # LOAD PLACEMENTS
        # ====================================================

        placements = (
            session.query(Placement)
            .order_by(Placement.id.desc())
            .all()
        )

        # ====================================================
        # LOAD EDITING INVOICE
        # ====================================================

        editing_invoice = None

        if st.session_state.editing_invoice_id:
            editing_invoice = (
                session.query(Invoice)
                .filter(
                    Invoice.id
                    == st.session_state.editing_invoice_id
                )
                .first()
            )

            if not editing_invoice:
                st.session_state.editing_invoice_id = None

        # ====================================================
        # CREATE / EDIT FORM
        # ====================================================

        if editing_invoice:
            st.subheader(
                f"Edit Invoice #{editing_invoice.invoice_number}"
            )
        else:
            st.subheader("Create Invoice")

        client_labels = [
            (
                f"{client.id} — "
                f"{get_client_name(client)}"
            )
            for client in clients
        ]

        client_map = {
            (
                f"{client.id} — "
                f"{get_client_name(client)}"
            ): client.id
            for client in clients
        }

        if editing_invoice:
            current_client_id = (
                editing_invoice.client_id
            )

            current_client_index = 0

            for index, client in enumerate(clients):
                if client.id == current_client_id:
                    current_client_index = index
                    break
        else:
            current_client_index = 0

        with st.form(
            "invoice_form",
            clear_on_submit=False,
        ):
            selected_client_label = st.selectbox(
                "Client *",
                options=client_labels,
                index=current_client_index,
            )

            selected_client_id = client_map[
                selected_client_label
            ]

            client_placements = [
                placement
                for placement in placements
                if placement.client_id
                == selected_client_id
            ]

            placement_labels = [
                (
                    f"{placement.id} — "
                    f"{get_placement_label(placement)}"
                )
                for placement in client_placements
            ]

            placement_map = {
                (
                    f"{placement.id} — "
                    f"{get_placement_label(placement)}"
                ): placement.id
                for placement in client_placements
            }

            selected_placement_id = None

            if placement_labels:
                placement_default_index = 0

                if editing_invoice:
                    for index, placement in enumerate(
                        client_placements
                    ):
                        if (
                            placement.id
                            == editing_invoice.placement_id
                        ):
                            placement_default_index = index
                            break

                selected_placement_label = st.selectbox(
                    "Placement",
                    options=placement_labels,
                    index=placement_default_index,
                )

                selected_placement_id = placement_map[
                    selected_placement_label
                ]

            else:
                st.info(
                    "This client has no placements. "
                    "The invoice can still be created without a placement."
                )

            col1, col2 = st.columns(2)

            with col1:
                invoice_number = st.text_input(
                    "Invoice Number *",
                    value=(
                        editing_invoice.invoice_number
                        if editing_invoice
                        else ""
                    ) or "",
                    max_chars=MAX_INVOICE_NUMBER_LENGTH,
                    placeholder="e.g. INV-0001",
                )

            with col2:
                description = st.text_input(
                    "Description",
                    value=(
                        editing_invoice.description
                        if editing_invoice
                        else ""
                    ) or "",
                    max_chars=MAX_DESCRIPTION_LENGTH,
                    placeholder=(
                        "e.g. Remote Accountant — September 2026"
                    ),
                )

            col1, col2 = st.columns(2)

            with col1:
                invoice_date = st.date_input(
                    "Invoice Date *",
                    value=(
                        editing_invoice.invoice_date
                        if editing_invoice
                        else date.today()
                    ),
                )

            with col2:
                due_date = st.date_input(
                    "Due Date *",
                    value=(
                        editing_invoice.due_date
                        if editing_invoice
                        else date.today()
                    ),
                )

            col1, col2 = st.columns(2)

            with col1:
                subtotal = st.number_input(
                    "Subtotal *",
                    min_value=0.0,
                    value=(
                        safe_float(
                            editing_invoice.subtotal
                        )
                        if editing_invoice
                        else 0.0
                    ),
                    step=0.01,
                    format="%.2f",
                )

            with col2:
                tax = st.number_input(
                    "Tax",
                    min_value=0.0,
                    value=(
                        safe_float(
                            editing_invoice.tax
                        )
                        if editing_invoice
                        else 0.0
                    ),
                    step=0.01,
                    format="%.2f",
                )

            total_amount = round(
                subtotal + tax,
                2,
            )

            currency_default = (
                editing_invoice.currency
                if (
                    editing_invoice
                    and editing_invoice.currency
                    in CURRENCIES
                )
                else "GBP"
            )

            col1, col2 = st.columns(2)

            with col1:
                currency = st.selectbox(
                    "Currency *",
                    options=CURRENCIES,
                    index=CURRENCIES.index(
                        currency_default
                    ),
                )

            with col2:
                status_default = (
                    editing_invoice.status
                    if (
                        editing_invoice
                        and editing_invoice.status
                        in INVOICE_STATUSES
                    )
                    else "Draft"
                )

                status = st.selectbox(
                    "Status *",
                    options=INVOICE_STATUSES,
                    index=INVOICE_STATUSES.index(
                        status_default
                    ),
                )

            st.metric(
                "Calculated Total",
                format_money(
                    total_amount,
                    currency,
                ),
            )

            if editing_invoice:
                existing_paid_display = safe_float(
                    getattr(
                        editing_invoice,
                        "amount_paid",
                        0.0,
                    )
                )

                if existing_paid_display > 0:
                    st.info(
                        (
                            "Payments already recorded: "
                            f"{format_money(existing_paid_display, currency)}. "
                            "The invoice total cannot be reduced below "
                            "the amount already paid."
                        )
                    )

            document_link = st.text_input(
                "Document Link",
                value=(
                    editing_invoice.document_link
                    if editing_invoice
                    else ""
                ) or "",
                placeholder="https://...",
            )

            notes = st.text_area(
                "Notes",
                value=(
                    editing_invoice.notes
                    if editing_invoice
                    else ""
                ) or "",
                max_chars=MAX_NOTES_LENGTH,
                height=120,
            )

            submitted = st.form_submit_button(
                (
                    "Update Invoice"
                    if editing_invoice
                    else "Create Invoice"
                ),
                type="primary",
                use_container_width=True,
            )

        # ====================================================
        # SAVE FORM
        # ====================================================

        if submitted:
            invoice_number = normalize_invoice_number(
                invoice_number
            )

            description = clean_text(
                description
            )

            document_link = clean_text(
                document_link
            )

            notes = clean_text(
                notes
            )

            validation_errors = validate_invoice_data(
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                due_date=due_date,
                subtotal=subtotal,
                tax=tax,
                total_amount=total_amount,
                currency=currency,
                status=status,
                description=description,
                document_link=document_link,
            )

            if len(notes) > MAX_NOTES_LENGTH:
                validation_errors.append(
                    (
                        "Notes cannot exceed "
                        f"{MAX_NOTES_LENGTH} characters."
                    )
                )

            # ------------------------------------------------
            # Validate client
            # ------------------------------------------------

            selected_client = (
                session.query(Client)
                .filter(
                    Client.id
                    == selected_client_id
                )
                .first()
            )

            if not selected_client:
                validation_errors.append(
                    "Selected client could not be found."
                )

            # ------------------------------------------------
            # Validate placement
            # ------------------------------------------------

            selected_placement = None

            if selected_placement_id:
                selected_placement = (
                    session.query(Placement)
                    .filter(
                        Placement.id
                        == selected_placement_id
                    )
                    .first()
                )

                if not selected_placement:
                    validation_errors.append(
                        "Selected placement could not be found."
                    )

                elif (
                    selected_placement.client_id
                    != selected_client_id
                ):
                    validation_errors.append(
                        (
                            "Selected placement does not belong "
                            "to the selected client."
                        )
                    )

            # ------------------------------------------------
            # Existing payment protection
            # ------------------------------------------------

            existing_paid = (
                safe_float(
                    getattr(
                        editing_invoice,
                        "amount_paid",
                        0.0,
                    )
                )
                if editing_invoice
                else 0.0
            )

            if editing_invoice:
                if total_amount < existing_paid:
                    validation_errors.append(
                        (
                            "Invoice total cannot be lower "
                            "than the amount already paid."
                        )
                    )

                if (
                    editing_invoice.currency
                    and editing_invoice.currency != currency
                    and has_payments(editing_invoice)
                ):
                    validation_errors.append(
                        (
                            "Currency cannot be changed "
                            "after payments have been recorded."
                        )
                    )

            # ------------------------------------------------
            # Payment/status validation
            # ------------------------------------------------

            validation_errors.extend(
                validate_payment_status(
                    status=status,
                    total_amount=total_amount,
                    amount_paid=existing_paid,
                    due_date=due_date,
                    invoice=editing_invoice,
                )
            )

            # ------------------------------------------------
            # Duplicate invoice number
            # ------------------------------------------------

            duplicate_invoice = find_duplicate_invoice(
                session=session,
                invoice_number=invoice_number,
                exclude_id=(
                    editing_invoice.id
                    if editing_invoice
                    else None
                ),
            )

            if duplicate_invoice:
                validation_errors.append(
                    (
                        "An invoice with this invoice number "
                        "already exists."
                    )
                )

            # ------------------------------------------------
            # Display errors
            # ------------------------------------------------

            if validation_errors:
                for error in validation_errors:
                    st.error(error)

            # ------------------------------------------------
            # SAVE
            # ------------------------------------------------

            else:
                try:
                    if editing_invoice:
                        editing_invoice.client_id = (
                            selected_client_id
                        )

                        editing_invoice.placement_id = (
                            selected_placement_id
                        )

                        editing_invoice.invoice_number = (
                            invoice_number
                        )

                        editing_invoice.invoice_date = (
                            invoice_date
                        )

                        editing_invoice.due_date = (
                            due_date
                        )

                        editing_invoice.description = (
                            description
                        )

                        editing_invoice.subtotal = (
                            subtotal
                        )

                        editing_invoice.tax = (
                            tax
                        )

                        editing_invoice.total_amount = (
                            total_amount
                        )

                        editing_invoice.currency = (
                            currency
                        )

                        editing_invoice.status = (
                            status
                        )

                        editing_invoice.document_link = (
                            document_link
                        )

                        editing_invoice.notes = (
                            notes
                        )

                        session.commit()

                        success_message = (
                            f"Invoice {invoice_number} "
                            "updated successfully."
                        )

                    else:
                        new_invoice = Invoice(
                            client_id=selected_client_id,
                            placement_id=selected_placement_id,
                            invoice_number=invoice_number,
                            invoice_date=invoice_date,
                            due_date=due_date,
                            description=description,
                            subtotal=subtotal,
                            tax=tax,
                            total_amount=total_amount,
                            amount_paid=0.0,
                            currency=currency,
                            status=status,
                            document_link=document_link,
                            notes=notes,
                        )

                        session.add(
                            new_invoice
                        )

                        session.commit()

                        success_message = (
                            f"Invoice {invoice_number} "
                            "created successfully."
                        )

                    clear_invoice_state()

                    st.success(
                        success_message
                    )

                    st.rerun()

                except Exception as error:
                    session.rollback()

                    st.error(
                        (
                            "The invoice could not be saved. "
                            "Please check the entered information."
                        )
                    )

                    st.caption(
                        f"Technical detail: {error}"
                    )

        # ====================================================
        # INVOICE REGISTER
        # ====================================================

        st.divider()

        st.subheader(
            "Invoice Register"
        )

        invoices = (
            session.query(Invoice)
            .order_by(
                Invoice.invoice_date.desc(),
                Invoice.id.desc(),
            )
            .all()
        )

        if not invoices:
            st.info(
                "No invoices have been created yet."
            )
            return

        # ====================================================
        # OVERALL KPI SUMMARY
        # ====================================================

        total_invoice_count = len(
            invoices
        )

        paid_count = sum(
            1
            for invoice in invoices
            if get_effective_status(invoice)
            == "Paid"
        )

        overdue_count = sum(
            1
            for invoice in invoices
            if get_effective_status(invoice)
            == "Overdue"
        )

        cancelled_count = sum(
            1
            for invoice in invoices
            if get_effective_status(invoice)
            == "Cancelled"
        )

        open_count = sum(
            1
            for invoice in invoices
            if get_effective_status(invoice)
            in [
                "Draft",
                "Sent",
                "Partially Paid",
                "Overdue",
            ]
        )

        outstanding_total = sum(
            get_balance_due(invoice)
            for invoice in invoices
            if get_effective_status(invoice)
            != "Cancelled"
        )

        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

        kpi1.metric(
            "Invoices",
            total_invoice_count,
        )

        kpi2.metric(
            "Open",
            open_count,
        )

        kpi3.metric(
            "Paid",
            paid_count,
        )

        kpi4.metric(
            "Overdue",
            overdue_count,
        )

        kpi5.metric(
            "Cancelled",
            cancelled_count,
        )

        # ====================================================
        # FINANCIAL SUMMARY
        # ====================================================

        currency_totals = get_currency_totals(
            invoices
        )

        st.markdown(
            "### Financial Summary"
        )

        for currency in sorted(
            currency_totals.keys()
        ):
            totals = currency_totals[
                currency
            ]

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                f"{currency} Invoiced",
                format_money(
                    totals["total"],
                    currency,
                ),
            )

            c2.metric(
                f"{currency} Paid",
                format_money(
                    totals["paid"],
                    currency,
                ),
            )

            c3.metric(
                f"{currency} Outstanding",
                format_money(
                    totals["balance"],
                    currency,
                ),
            )

            c4.metric(
                f"{currency} Overdue",
                format_money(
                    totals["overdue"],
                    currency,
                ),
            )

        # ====================================================
        # FILTERS
        # ====================================================

        st.markdown(
            "### Search & Filters"
        )

        filter_version = st.session_state[
            FILTER_VERSION_KEY
        ]

        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            search = st.text_input(
                "Search",
                placeholder=(
                    "Invoice number, client, placement, description..."
                ),
                key=(
                    f"invoice_search_"
                    f"{filter_version}"
                ),
            )

        with filter_col2:
            client_filter_options = [
                "All Clients"
            ] + [
                get_client_name(client)
                for client in clients
            ]

            client_filter = st.selectbox(
                "Client",
                options=client_filter_options,
                key=(
                    f"invoice_client_filter_"
                    f"{filter_version}"
                ),
            )

        filter_col1, filter_col2, filter_col3, filter_col4 = (
            st.columns(4)
        )

        with filter_col1:
            status_filter = st.selectbox(
                "Status",
                options=[
                    "All"
                ] + INVOICE_STATUSES,
                key=(
                    f"invoice_status_filter_"
                    f"{filter_version}"
                ),
            )

        with filter_col2:
            currency_filter = st.selectbox(
                "Currency",
                options=[
                    "All"
                ] + CURRENCIES,
                key=(
                    f"invoice_currency_filter_"
                    f"{filter_version}"
                ),
            )

        with filter_col3:
            overdue_filter = st.selectbox(
                "Overdue",
                options=[
                    "All",
                    "Overdue Only",
                    "Not Overdue",
                ],
                key=(
                    f"invoice_overdue_filter_"
                    f"{filter_version}"
                ),
            )

        with filter_col4:
            sort_option = st.selectbox(
                "Sort",
                options=[
                    "Invoice Date — Newest",
                    "Invoice Date — Oldest",
                    "Due Date — Soonest",
                    "Due Date — Latest",
                    "Amount — Highest",
                    "Balance — Highest",
                    "Client — A-Z",
                ],
                key=(
                    f"invoice_sort_"
                    f"{filter_version}"
                ),
            )

        reset_col, count_col = st.columns(
            [1, 3]
        )

        with reset_col:
            if st.button(
                "Reset Filters",
                key=(
                    f"reset_invoice_filters_"
                    f"{filter_version}"
                ),
                use_container_width=True,
            ):
                reset_invoice_filters()
                st.rerun()

        filtered_invoices = []

        search_lower = clean_text(
            search
        ).lower()

        for invoice in invoices:
            invoice_number = clean_text(
                getattr(
                    invoice,
                    "invoice_number",
                    "",
                )
            )

            description = clean_text(
                getattr(
                    invoice,
                    "description",
                    "",
                )
            )

            client_name = get_client_name(
                getattr(
                    invoice,
                    "client",
                    None,
                )
            )

            placement_label = get_placement_label(
                getattr(
                    invoice,
                    "placement",
                    None,
                )
            )

            effective_status = get_effective_status(
                invoice
            )

            currency = clean_text(
                getattr(
                    invoice,
                    "currency",
                    "",
                )
            )

            searchable_text = " ".join(
                [
                    invoice_number,
                    description,
                    client_name,
                    placement_label,
                    effective_status,
                    currency,
                ]
            ).lower()

            if (
                search_lower
                and search_lower not in searchable_text
            ):
                continue

            if (
                client_filter != "All Clients"
                and client_name != client_filter
            ):
                continue

            if (
                status_filter != "All"
                and effective_status != status_filter
            ):
                continue

            if (
                currency_filter != "All"
                and currency != currency_filter
            ):
                continue

            days_overdue = calculate_days_overdue(
                invoice
            )

            if (
                overdue_filter == "Overdue Only"
                and days_overdue <= 0
            ):
                continue

            if (
                overdue_filter == "Not Overdue"
                and days_overdue > 0
            ):
                continue

            filtered_invoices.append(
                invoice
            )

        # ====================================================
        # SORT
        # ====================================================

        if sort_option == "Invoice Date — Newest":
            filtered_invoices.sort(
                key=lambda invoice: (
                    getattr(
                        invoice,
                        "invoice_date",
                        None,
                    ) or date.min
                ),
                reverse=True,
            )

        elif sort_option == "Invoice Date — Oldest":
            filtered_invoices.sort(
                key=lambda invoice: (
                    getattr(
                        invoice,
                        "invoice_date",
                        None,
                    ) or date.min
                )
            )

        elif sort_option == "Due Date — Soonest":
            filtered_invoices.sort(
                key=lambda invoice: (
                    getattr(
                        invoice,
                        "due_date",
                        None,
                    ) or date.max
                )
            )

        elif sort_option == "Due Date — Latest":
            filtered_invoices.sort(
                key=lambda invoice: (
                    getattr(
                        invoice,
                        "due_date",
                        None,
                    ) or date.min
                ),
                reverse=True,
            )

        elif sort_option == "Amount — Highest":
            filtered_invoices.sort(
                key=lambda invoice: safe_float(
                    getattr(
                        invoice,
                        "total_amount",
                        0.0,
                    )
                ),
                reverse=True,
            )

        elif sort_option == "Balance — Highest":
            filtered_invoices.sort(
                key=lambda invoice: get_balance_due(
                    invoice
                ),
                reverse=True,
            )

        elif sort_option == "Client — A-Z":
            filtered_invoices.sort(
                key=lambda invoice: (
                    get_client_name(
                        getattr(
                            invoice,
                            "client",
                            None,
                        )
                    ).lower()
                )
            )

        with count_col:
            st.caption(
                (
                    f"Showing {len(filtered_invoices)} "
                    f"of {len(invoices)} invoices"
                )
            )

        # ====================================================
        # FILTERED EXPORT
        # ====================================================

        export_col1, export_col2 = st.columns(2)

        with export_col1:
            st.download_button(
                label="Export All Invoices CSV",
                data=get_csv_bytes(
                    invoices
                ),
                file_name="averra_invoices_all.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with export_col2:
            st.download_button(
                label="Export Filtered CSV",
                data=get_csv_bytes(
                    filtered_invoices
                ),
                file_name="averra_invoices_filtered.csv",
                mime="text/csv",
                disabled=not filtered_invoices,
                use_container_width=True,
            )

        # ====================================================
        # FILTERED SUMMARY
        # ====================================================

        if filtered_invoices:
            filtered_total = sum(
                safe_float(
                    getattr(
                        invoice,
                        "total_amount",
                        0.0,
                    )
                )
                for invoice in filtered_invoices
            )

            filtered_balance = sum(
                get_balance_due(invoice)
                for invoice in filtered_invoices
            )

            filtered_overdue = sum(
                get_balance_due(invoice)
                for invoice in filtered_invoices
                if get_effective_status(invoice)
                == "Overdue"
            )

            s1, s2, s3 = st.columns(3)

            s1.metric(
                "Filtered Invoice Value",
                f"{filtered_total:,.2f}",
            )

            s2.metric(
                "Filtered Outstanding",
                f"{filtered_balance:,.2f}",
            )

            s3.metric(
                "Filtered Overdue",
                f"{filtered_overdue:,.2f}",
            )

        # ====================================================
        # EMPTY FILTER RESULT
        # ====================================================

        if not filtered_invoices:
            st.info(
                "No invoices match the selected filters."
            )
            return

        # ====================================================
        # INVOICE CARDS
        # ====================================================

        for invoice in filtered_invoices:
            invoice_id = invoice.id

            invoice_number = clean_text(
                getattr(
                    invoice,
                    "invoice_number",
                    "",
                )
            )

            currency = clean_text(
                getattr(
                    invoice,
                    "currency",
                    "",
                )
            ) or "GBP"

            total = safe_float(
                getattr(
                    invoice,
                    "total_amount",
                    0.0,
                )
            )

            paid = safe_float(
                getattr(
                    invoice,
                    "amount_paid",
                    0.0,
                )
            )

            balance = get_balance_due(
                invoice
            )

            effective_status = get_effective_status(
                invoice
            )

            payment_percentage = get_payment_percentage(
                invoice
            )

            days_overdue = calculate_days_overdue(
                invoice
            )

            invoice_age = get_invoice_age(
                invoice
            )

            client = getattr(
                invoice,
                "client",
                None,
            )

            placement = getattr(
                invoice,
                "placement",
                None,
            )

            st.markdown("---")

            header_col1, header_col2 = st.columns(
                [4, 1]
            )

            with header_col1:
                st.markdown(
                    f"### Invoice {invoice_number}"
                )

                st.write(
                    f"**Client:** "
                    f"{get_client_name(client)}"
                )

                if placement:
                    st.write(
                        f"**Placement:** "
                        f"{get_placement_label(placement)}"
                    )

            with header_col2:
                st.metric(
                    "Status",
                    effective_status,
                )

            info1, info2, info3, info4, info5 = (
                st.columns(5)
            )

            with info1:
                st.write(
                    "**Invoice Date**"
                )

                st.write(
                    format_date(
                        getattr(
                            invoice,
                            "invoice_date",
                            None,
                        )
                    )
                )

            with info2:
                st.write(
                    "**Due Date**"
                )

                st.write(
                    format_date(
                        getattr(
                            invoice,
                            "due_date",
                            None,
                        )
                    )
                )

            with info3:
                st.write(
                    "**Total**"
                )

                st.write(
                    format_money(
                        total,
                        currency,
                    )
                )

            with info4:
                st.write(
                    "**Paid**"
                )

                st.write(
                    format_money(
                        paid,
                        currency,
                    )
                )

            with info5:
                st.write(
                    "**Balance**"
                )

                st.write(
                    format_money(
                        balance,
                        currency,
                    )
                )

            payment_col1, payment_col2 = st.columns(
                2
            )

            with payment_col1:
                st.progress(
                    payment_percentage / 100
                )

                st.caption(
                    (
                        f"{payment_percentage:.1f}% paid — "
                        f"{format_money(paid, currency)} "
                        f"of "
                        f"{format_money(total, currency)}"
                    )
                )

            with payment_col2:
                if days_overdue > 0:
                    st.error(
                        (
                            f"{days_overdue} "
                            "days overdue"
                        )
                    )
                elif balance <= 0 and total > 0:
                    st.success(
                        "Fully paid."
                    )
                else:
                    st.caption(
                        (
                            f"Invoice age: "
                            f"{invoice_age} days."
                        )
                    )

            description = clean_text(
                getattr(
                    invoice,
                    "description",
                    "",
                )
            )

            if description:
                st.write(
                    f"**Description:** {description}"
                )

            payment_count = get_payment_count(
                invoice
            )

            if payment_count:
                st.caption(
                    (
                        f"{payment_count} payment"
                        f"{'s' if payment_count != 1 else ''} "
                        "recorded."
                    )
                )

            # ------------------------------------------------
            # DATA WARNINGS
            # ------------------------------------------------

            data_warnings = get_invoice_data_warnings(
                invoice
            )

            if data_warnings:
                with st.expander(
                    "Data Quality Warnings"
                ):
                    for warning in data_warnings:
                        st.warning(
                            warning
                        )

            # ------------------------------------------------
            # DOCUMENT
            # ------------------------------------------------

            document_link = clean_text(
                getattr(
                    invoice,
                    "document_link",
                    "",
                )
            )

            if document_link:
                try:
                    if valid_url(document_link):
                        st.link_button(
                            "Open Invoice Document",
                            document_link,
                        )
                    else:
                        st.caption(
                            "Stored document link is not a valid URL."
                        )
                except Exception:
                    st.caption(
                        "Stored document link could not be validated."
                    )

            # ------------------------------------------------
            # NOTES
            # ------------------------------------------------

            notes = clean_text(
                getattr(
                    invoice,
                    "notes",
                    "",
                )
            )

            if notes:
                with st.expander(
                    "Notes"
                ):
                    st.write(notes)

            # ------------------------------------------------
            # ACTION BUTTONS
            # ------------------------------------------------

            action1, action2, action3 = st.columns(
                3
            )

            with action1:
                if st.button(
                    "Edit",
                    key=(
                        f"edit_invoice_"
                        f"{invoice_id}"
                    ),
                    use_container_width=True,
                ):
                    st.session_state.editing_invoice_id = (
                        invoice_id
                    )

                    st.session_state.confirm_delete_invoice_id = (
                        None
                    )

                    st.rerun()

            with action2:
                try:
                    pdf_bytes = generate_invoice_pdf(
                        invoice
                    )

                    safe_pdf_name = (
                        invoice_number
                        or f"invoice-{invoice_id}"
                    )

                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=(
                            f"{safe_pdf_name}.pdf"
                        ),
                        mime="application/pdf",
                        key=(
                            f"pdf_invoice_"
                            f"{invoice_id}"
                        ),
                        use_container_width=True,
                    )

                except RuntimeError as error:
                    st.warning(
                        str(error)
                    )

            with action3:
                if st.button(
                    "Delete",
                    key=(
                        f"delete_invoice_"
                        f"{invoice_id}"
                    ),
                    use_container_width=True,
                ):
                    st.session_state.confirm_delete_invoice_id = (
                        invoice_id
                    )

            # ------------------------------------------------
            # DELETE CONFIRMATION
            # ------------------------------------------------

            if (
                st.session_state.confirm_delete_invoice_id
                == invoice_id
            ):
                st.warning(
                    (
                        f"Are you sure you want to delete "
                        f"invoice {invoice_number}?"
                    )
                )

                if has_payments(invoice):
                    st.error(
                        (
                            "This invoice cannot be deleted "
                            "because it has recorded payments. "
                            "Use Cancelled status instead."
                        )
                    )

                    if st.button(
                        "Close",
                        key=(
                            f"close_delete_"
                            f"{invoice_id}"
                        ),
                        use_container_width=True,
                    ):
                        st.session_state.confirm_delete_invoice_id = (
                            None
                        )

                        st.rerun()

                else:
                    confirm_col1, confirm_col2 = (
                        st.columns(2)
                    )

                    with confirm_col1:
                        if st.button(
                            "Yes, Delete",
                            key=(
                                f"confirm_delete_"
                                f"{invoice_id}"
                            ),
                            type="primary",
                            use_container_width=True,
                        ):
                            try:
                                session.delete(
                                    invoice
                                )

                                session.commit()

                                st.session_state.confirm_delete_invoice_id = (
                                    None
                                )

                                st.success(
                                    (
                                        f"Invoice "
                                        f"{invoice_number} "
                                        "deleted successfully."
                                    )
                                )

                                st.rerun()

                            except Exception as error:
                                session.rollback()

                                st.error(
                                    (
                                        "The invoice could "
                                        "not be deleted."
                                    )
                                )

                                st.caption(
                                    f"Technical detail: {error}"
                                )

                    with confirm_col2:
                        if st.button(
                            "Cancel",
                            key=(
                                f"cancel_delete_"
                                f"{invoice_id}"
                            ),
                            use_container_width=True,
                        ):
                            st.session_state.confirm_delete_invoice_id = (
                                None
                            )

                            st.rerun()

        # ====================================================
        # EDIT MODE CONTROLS
        # ====================================================

        if editing_invoice:
            st.divider()

            if st.button(
                "Cancel Editing",
                use_container_width=True,
            ):
                clear_invoice_state()
                st.rerun()

    except Exception as error:
        session.rollback()

        st.error(
            (
                "The invoices screen could not be loaded. "
                "Please check the database and invoice data."
            )
        )

        st.caption(
            f"Technical detail: {error}"
        )

    finally:
        session.close()


# ============================================================
# COMPATIBILITY ENTRY POINT
# ============================================================

def main():
    show_invoices()


if __name__ == "__main__":
    main()