import csv
import io
from datetime import date
from xml.sax.saxutils import escape

import streamlit as st

from database import get_session
from models import Invoice, Client, Placement

from utils.calculations import (
    calculate_invoice_balance,
    calculate_payment_percentage,
)
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

MAX_DESCRIPTION_LENGTH = 500
MAX_NOTES_LENGTH = 2000


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

    if employee_name and position:
        return f"{employee_name} — {position}"

    if employee_name:
        return employee_name

    if position:
        return position

    return f"Placement #{placement.id}"


# ============================================================
# INVOICE CALCULATIONS
# ============================================================

def get_balance_due(invoice):
    total = safe_float(
        getattr(invoice, "total_amount", 0.0)
    )

    paid = safe_float(
        getattr(invoice, "amount_paid", 0.0)
    )

    try:
        calculated_balance = calculate_invoice_balance(
            total,
            paid,
        )

        balance = safe_float(
            calculated_balance
        )

    except Exception:
        balance = total - paid

    return max(balance, 0.0)


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


def get_effective_status(invoice):
    """
    Calculates the status displayed to the user without
    changing the stored database status.
    """

    stored_status = clean_text(
        getattr(invoice, "status", None)
    )

    if stored_status == "Cancelled":
        return "Cancelled"

    total = safe_float(
        getattr(invoice, "total_amount", 0.0)
    )

    paid = safe_float(
        getattr(invoice, "amount_paid", 0.0)
    )

    balance = get_balance_due(invoice)

    if total > 0 and paid >= total:
        return "Paid"

    if paid > 0 and balance > 0:
        due_date = getattr(
            invoice,
            "due_date",
            None,
        )

        if due_date and due_date < date.today():
            return "Overdue"

        return "Partially Paid"

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

    return stored_status or "Draft"


def calculate_days_overdue(invoice):
    balance = get_balance_due(invoice)

    if balance <= 0:
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


def get_payment_percentage(invoice):
    total = safe_float(
        getattr(invoice, "total_amount", 0.0)
    )

    paid = safe_float(
        getattr(invoice, "amount_paid", 0.0)
    )

    try:
        percentage = calculate_payment_percentage(
            total,
            paid,
        )

        percentage = safe_float(
            percentage
        )

    except Exception:
        if total <= 0:
            return 0.0

        percentage = (
            paid / total
        ) * 100

    return max(
        0.0,
        min(100.0, percentage),
    )


def format_money(amount, currency):
    amount = safe_float(amount)

    return f"{currency} {amount:,.2f}"


# ============================================================
# CURRENCY SUMMARY
# ============================================================

def get_currency_totals(invoices):
    totals = {}

    for invoice in invoices:
        currency = clean_text(
            getattr(invoice, "currency", None)
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

        totals[currency]["balance"] += (
            get_balance_due(invoice)
        )

        if (
            get_effective_status(invoice)
            == "Overdue"
        ):
            totals[currency]["overdue"] += (
                get_balance_due(invoice)
            )

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
                getattr(
                    invoice,
                    "invoice_date",
                    "",
                ),
                getattr(
                    invoice,
                    "due_date",
                    "",
                ),
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
                    get_payment_percentage(
                        invoice
                    ),
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

    return escape(value).replace(
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
            "Add reportlab to requirements.txt."
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
                    pdf_text(
                        invoice_number
                    ),
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
                        getattr(
                            invoice,
                            "invoice_date",
                            "",
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
                        getattr(
                            invoice,
                            "due_date",
                            "",
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
                        get_effective_status(
                            invoice
                        )
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

        client = getattr(
            invoice,
            "client",
            None,
        )

        client_name = get_client_name(
            client
        )

        client_address = get_client_address(
            client
        )

        story.append(
            Paragraph(
                "<b>Bill To</b>",
                styles["Heading3"],
            )
        )

        story.append(
            Paragraph(
                pdf_text(client_name),
                styles["Normal"],
            )
        )

        if client_address:
            story.append(
                Paragraph(
                    pdf_text(
                        client_address
                    ),
                    styles["Normal"],
                )
            )

        story.append(Spacer(1, 12))

        placement = getattr(
            invoice,
            "placement",
            None,
        )

        placement_label = get_placement_label(
            placement
        )

        description = clean_text(
            getattr(
                invoice,
                "description",
                "",
            )
        )

        line_description = (
            description
            if description
            else placement_label
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
                    pdf_text(
                        line_description
                    ),
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
                    f"<b>{format_money(total, currency)}</b>",
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
                    f"<b>{format_money(balance, currency)}</b>",
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

            story.append(Spacer(1, 10))

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

        story.append(Spacer(1, 15))

        story.append(
            Paragraph(
                "Generated by AVERRA Staffing Solutions CRM",
                small_style,
            )
        )

        document.build(story)

        buffer.seek(0)

        return buffer.getvalue()

    except Exception:
        raise RuntimeError(
            "The invoice PDF could not be generated."
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

    if not invoice_number:
        errors.append(
            "Invoice number is required."
        )

    if len(invoice_number) > 100:
        errors.append(
            "Invoice number cannot exceed 100 characters."
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
            f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters."
        )

    if document_link:
        try:
            if not valid_url(
                document_link
            ):
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
        if invoice is not None:
            if has_payments(invoice):
                errors.append(
                    "An invoice with payments cannot be cancelled."
                )

    return errors


# ============================================================
# SESSION STATE
# ============================================================

def clear_invoice_state():
    st.session_state.editing_invoice_id = None
    st.session_state.confirm_delete_invoice_id = None


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
            f"{client.id} — {get_client_name(client)}"
            for client in clients
        ]

        client_map = {
            f"{client.id} — {get_client_name(client)}":
                client.id
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

            default_client_label = (
                client_labels[
                    current_client_index
                ]
            )

        else:
            default_client_label = (
                client_labels[0]
            )

        with st.form(
            "invoice_form",
            clear_on_submit=False,
        ):
            selected_client_label = st.selectbox(
                "Client *",
                options=client_labels,
                index=client_labels.index(
                    default_client_label
                ),
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
                ):
                    placement.id
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

                selected_placement_id = (
                    placement_map[
                        selected_placement_label
                    ]
                )

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
                    ),
                    max_chars=100,
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

            submit_label = (
                "Update Invoice"
                if editing_invoice
                else "Create Invoice"
            )

            submitted = st.form_submit_button(
                submit_label,
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

            validation_errors = (
                validate_invoice_data(
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
            )

            if len(notes) > MAX_NOTES_LENGTH:
                validation_errors.append(
                    (
                        "Notes cannot exceed "
                        f"{MAX_NOTES_LENGTH} characters."
                    )
                )

            # -----------------------------------------------
            # Validate placement
            # -----------------------------------------------

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
                        "Selected placement does not belong to the selected client."
                    )

            # -----------------------------------------------
            # Existing payment protection
            # -----------------------------------------------

            existing_paid = (
                safe_float(
                    editing_invoice.amount_paid
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
                    and editing_invoice.currency
                    != currency
                    and has_payments(
                        editing_invoice
                    )
                ):
                    validation_errors.append(
                        (
                            "Currency cannot be changed "
                            "after payments have been recorded."
                        )
                    )

            # -----------------------------------------------
            # Payment/status validation
            # -----------------------------------------------

            validation_errors.extend(
                validate_payment_status(
                    status=status,
                    total_amount=total_amount,
                    amount_paid=existing_paid,
                    due_date=due_date,
                    invoice=editing_invoice,
                )
            )

            # -----------------------------------------------
            # Duplicate invoice number
            # -----------------------------------------------

            duplicate_query = (
                session.query(Invoice)
                .filter(
                    Invoice.invoice_number.ilike(
                        invoice_number
                    )
                )
            )

            if editing_invoice:
                duplicate_query = (
                    duplicate_query.filter(
                        Invoice.id
                        != editing_invoice.id
                    )
                )

            duplicate_invoice = (
                duplicate_query.first()
            )

            if duplicate_invoice:
                validation_errors.append(
                    (
                        "An invoice with this "
                        "invoice number already exists."
                    )
                )

            # -----------------------------------------------
            # Display validation errors
            # -----------------------------------------------

            if validation_errors:
                for error in validation_errors:
                    st.error(error)

            # -----------------------------------------------
            # SAVE
            # -----------------------------------------------

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

                        st.success(
                            (
                                f"Invoice {invoice_number} "
                                "updated successfully."
                            )
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

                        st.success(
                            (
                                f"Invoice {invoice_number} "
                                "created successfully."
                            )
                        )

                    clear_invoice_state()

                    st.rerun()

                except Exception:
                    session.rollback()

                    st.error(
                        (
                            "The invoice could not be saved. "
                            "Please check the entered information "
                            "and try again."
                        )
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
        # EXPORT
        # ====================================================

        st.download_button(
            label="Export All Invoices CSV",
            data=get_csv_bytes(
                invoices
            ),
            file_name="averra_invoices.csv",
            mime="text/csv",
        )

        # ====================================================
        # KPI SUMMARY
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

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

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

        # ====================================================
        # FINANCIAL SUMMARY BY CURRENCY
        # ====================================================

        currency_totals = (
            get_currency_totals(
                invoices
            )
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

        filter_col1, filter_col2, filter_col3 = (
            st.columns(3)
        )

        with filter_col1:
            search = st.text_input(
                "Search",
                placeholder=(
                    "Invoice number, client, description..."
                ),
            )

        with filter_col2:
            status_filter = st.selectbox(
                "Status",
                options=[
                    "All"
                ] + INVOICE_STATUSES,
            )

        with filter_col3:
            currency_filter = st.selectbox(
                "Currency",
                options=[
                    "All"
                ] + CURRENCIES,
            )

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

            placement_label = (
                get_placement_label(
                    getattr(
                        invoice,
                        "placement",
                        None,
                    )
                )
            )

            effective_status = (
                get_effective_status(
                    invoice
                )
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
                ]
            ).lower()

            if (
                search_lower
                and search_lower
                not in searchable_text
            ):
                continue

            if (
                status_filter != "All"
                and effective_status
                != status_filter
            ):
                continue

            if (
                currency_filter != "All"
                and currency
                != currency_filter
            ):
                continue

            filtered_invoices.append(
                invoice
            )

        st.caption(
            (
                f"Showing {len(filtered_invoices)} "
                f"of {len(invoices)} invoices"
            )
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

            effective_status = (
                get_effective_status(
                    invoice
                )
            )

            payment_percentage = (
                get_payment_percentage(
                    invoice
                )
            )

            days_overdue = (
                calculate_days_overdue(
                    invoice
                )
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

            st.markdown(
                "---"
            )

            header_col1, header_col2 = (
                st.columns(
                    [4, 1]
                )
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

            info1, info2, info3, info4 = (
                st.columns(4)
            )

            with info1:
                st.write(
                    "**Invoice Date**"
                )

                st.write(
                    str(
                        getattr(
                            invoice,
                            "invoice_date",
                            "",
                        )
                    )
                )

            with info2:
                st.write(
                    "**Due Date**"
                )

                st.write(
                    str(
                        getattr(
                            invoice,
                            "due_date",
                            "",
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
                    "**Balance Due**"
                )

                st.write(
                    format_money(
                        balance,
                        currency,
                    )
                )

            payment_col1, payment_col2 = (
                st.columns(2)
            )

            with payment_col1:
                st.progress(
                    payment_percentage / 100
                )

                st.caption(
                    (
                        f"{payment_percentage:.1f}% paid "
                        f"— "
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
                else:
                    st.caption(
                        "Payment is not currently overdue."
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

            document_link = clean_text(
                getattr(
                    invoice,
                    "document_link",
                    "",
                )
            )

            if document_link:
                try:
                    if valid_url(
                        document_link
                    ):
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

            # =================================================
            # ACTION BUTTONS
            # =================================================

            action1, action2, action3 = (
                st.columns(3)
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
                    pdf_bytes = (
                        generate_invoice_pdf(
                            invoice
                        )
                    )

                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=(
                            f"{invoice_number}.pdf"
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

            # =================================================
            # DELETE CONFIRMATION
            # =================================================

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

                            except Exception:
                                session.rollback()

                                st.error(
                                    (
                                        "The invoice could "
                                        "not be deleted."
                                    )
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

    except Exception:
        session.rollback()

        st.error(
            (
                "The invoices screen could not be loaded. "
                "Please check the database and invoice data."
            )
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