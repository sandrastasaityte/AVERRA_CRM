import csv
import io
from datetime import date

import streamlit as st

from database import get_session
from models import Invoice, Client, Placement

from utils.calculations import (
    calculate_invoice_balance,
    calculate_payment_percentage,
    invoice_is_overpaid,
)
from utils.helpers import (
    valid_url,
)


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


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    """Return safely cleaned text."""

    if value is None:
        return ""

    return str(value).strip()


def get_client_name(invoice):
    """Return invoice client name."""

    if invoice.client:

        return (
            clean_text(invoice.client.company_name)
            or "Unknown Client"
        )

    return "Unknown Client"


def get_client_address(client):
    """Return a readable client address."""

    if not client:
        return ""

    parts = [
        clean_text(getattr(client, "address", "")),
        clean_text(getattr(client, "city", "")),
        clean_text(getattr(client, "postcode", "")),
        clean_text(getattr(client, "country", "")),
    ]

    return ", ".join(
        part for part in parts if part
    )


def get_placement_label(placement):
    """Return a readable placement label."""

    employee_name = "Unknown Employee"

    if placement.employee:

        first_name = clean_text(
            placement.employee.first_name
        )

        last_name = clean_text(
            placement.employee.last_name
        )

        employee_name = (
            f"{first_name} {last_name}"
        ).strip()

        if not employee_name:

            employee_name = "Unknown Employee"

    client_name = "Unknown Client"

    if placement.client:

        client_name = (
            clean_text(
                placement.client.company_name
            )
            or "Unknown Client"
        )

    position = (
        clean_text(placement.position)
        or "No Position"
    )

    return (
        f"Placement #{placement.id} - "
        f"{client_name} - "
        f"{employee_name} - "
        f"{position}"
    )


def get_balance_due(invoice):
    """Calculate the current invoice balance."""

    return calculate_invoice_balance(
        invoice.total_amount,
        invoice.amount_paid,
    )


def get_effective_status(invoice):
    """
    Return the displayed invoice status.

    Overdue is displayed automatically when:
    - invoice is not Paid
    - invoice is not Cancelled
    - due date has passed
    - balance remains outstanding
    """

    current_status = clean_text(
        invoice.status
    )

    if current_status in [
        "Paid",
        "Cancelled",
    ]:
        return current_status

    balance = get_balance_due(invoice)

    if (
        invoice.due_date
        and invoice.due_date < date.today()
        and balance > 0
    ):
        return "Overdue"

    return current_status or "Draft"


def get_payment_count(invoice):
    """Return number of recorded payments."""

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
    """Determine whether payments are attached."""

    if get_payment_count(invoice) > 0:
        return True

    return (
        float(
            getattr(
                invoice,
                "amount_paid",
                0,
            )
            or 0
        )
        > 0
    )


def format_money(currency, amount):
    """Format an invoice amount."""

    return (
        f"{currency} "
        f"{float(amount or 0):,.2f}"
    )


def get_currency_totals(invoices):
    """
    Return invoice totals grouped by currency.

    Important:
    GBP, EUR, USD and INR are never added together.
    """

    totals = {}

    for invoice in invoices:

        currency = (
            clean_text(
                invoice.currency
            )
            or "GBP"
        )

        if currency not in totals:

            totals[currency] = {
                "invoiced": 0.0,
                "paid": 0.0,
                "outstanding": 0.0,
                "overdue": 0.0,
                "count": 0,
            }

        total = float(
            invoice.total_amount or 0
        )

        paid = float(
            invoice.amount_paid or 0
        )

        balance = get_balance_due(invoice)

        totals[currency]["invoiced"] += total
        totals[currency]["paid"] += paid
        totals[currency]["outstanding"] += balance
        totals[currency]["count"] += 1

        if (
            get_effective_status(invoice)
            == "Overdue"
        ):

            totals[currency]["overdue"] += balance

    return totals


def get_csv_bytes(invoices):
    """Create downloadable invoice CSV data."""

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow(
        [
            "Invoice ID",
            "Invoice Number",
            "Client",
            "Placement ID",
            "Invoice Date",
            "Due Date",
            "Description",
            "Subtotal",
            "Tax",
            "Total Amount",
            "Amount Paid",
            "Balance Due",
            "Currency",
            "Status",
            "Payment Count",
            "Document Link",
            "Notes",
        ]
    )

    for invoice in invoices:

        writer.writerow(
            [
                invoice.id,
                clean_text(
                    invoice.invoice_number
                ),
                get_client_name(invoice),
                invoice.placement_id
                if invoice.placement_id
                else "",
                invoice.invoice_date
                if invoice.invoice_date
                else "",
                invoice.due_date
                if invoice.due_date
                else "",
                clean_text(
                    invoice.description
                ),
                float(
                    invoice.subtotal or 0
                ),
                float(
                    invoice.tax or 0
                ),
                float(
                    invoice.total_amount or 0
                ),
                float(
                    invoice.amount_paid or 0
                ),
                get_balance_due(invoice),
                clean_text(
                    invoice.currency
                ),
                get_effective_status(
                    invoice
                ),
                get_payment_count(
                    invoice
                ),
                clean_text(
                    invoice.document_link
                ),
                clean_text(
                    invoice.notes
                ),
            ]
        )

    return output.getvalue().encode(
        "utf-8-sig"
    )


def generate_invoice_pdf(invoice):
    """
    Generate a professional PDF invoice.

    Requires reportlab.
    """

    try:

        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
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
            "Add 'reportlab' to requirements.txt "
            "and redeploy the application."
        )

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

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["Normal"]

    story = []

    # ========================================================
    # COMPANY HEADER
    # ========================================================

    story.append(
        Paragraph(
            "<b>AVERRA STAFFING SOLUTIONS LTD</b>",
            title_style,
        )
    )

    story.append(
        Spacer(1, 5 * mm)
    )

    story.append(
        Paragraph(
            "<b>INVOICE</b>",
            heading_style,
        )
    )

    story.append(
        Spacer(1, 5 * mm)
    )

    # ========================================================
    # CLIENT INFORMATION
    # ========================================================

    client = invoice.client

    client_name = (
        clean_text(
            client.company_name
        )
        if client
        else "Unknown Client"
    )

    client_address = (
        get_client_address(client)
        if client
        else ""
    )

    invoice_date_text = (
        invoice.invoice_date.strftime(
            "%d %B %Y"
        )
        if invoice.invoice_date
        else ""
    )

    due_date_text = (
        invoice.due_date.strftime(
            "%d %B %Y"
        )
        if invoice.due_date
        else ""
    )

    invoice_information = [
        [
            Paragraph(
                "<b>Bill To</b>",
                normal_style,
            ),
            Paragraph(
                "<b>Invoice Details</b>",
                normal_style,
            ),
        ],
        [
            Paragraph(
                client_name,
                normal_style,
            ),
            Paragraph(
                (
                    f"Invoice Number: "
                    f"{clean_text(invoice.invoice_number)}"
                    f"<br/>"
                    f"Invoice Date: "
                    f"{invoice_date_text}"
                    f"<br/>"
                    f"Due Date: "
                    f"{due_date_text}"
                ),
                normal_style,
            ),
        ],
    ]

    if client_address:

        invoice_information[1][0] = Paragraph(
            (
                f"{client_name}"
                f"<br/>{client_address}"
            ),
            normal_style,
        )

    information_table = Table(
        invoice_information,
        colWidths=[
            85 * mm,
            85 * mm,
        ],
    )

    information_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
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

    story.append(
        information_table
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    # ========================================================
    # DESCRIPTION
    # ========================================================

    description = (
        clean_text(
            invoice.description
        )
        or "Professional staffing / outsourcing services"
    )

    currency = (
        clean_text(
            invoice.currency
        )
        or "GBP"
    )

    subtotal = float(
        invoice.subtotal or 0
    )

    tax = float(
        invoice.tax or 0
    )

    total = float(
        invoice.total_amount or 0
    )

    paid = float(
        invoice.amount_paid or 0
    )

    balance = get_balance_due(
        invoice
    )

    item_table = Table(
        [
            [
                Paragraph(
                    "<b>Description</b>",
                    normal_style,
                ),
                Paragraph(
                    "<b>Amount</b>",
                    normal_style,
                ),
            ],
            [
                Paragraph(
                    description,
                    normal_style,
                ),
                Paragraph(
                    f"{currency} {subtotal:,.2f}",
                    normal_style,
                ),
            ],
        ],
        colWidths=[
            130 * mm,
            40 * mm,
        ],
    )

    item_table.setStyle(
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
                    "ALIGN",
                    (1, 1),
                    (1, 1),
                    "RIGHT",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(
        item_table
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    # ========================================================
    # TOTALS
    # ========================================================

    totals_table = Table(
        [
            [
                "Subtotal",
                f"{currency} {subtotal:,.2f}",
            ],
            [
                "Tax",
                f"{currency} {tax:,.2f}",
            ],
            [
                "Total",
                f"{currency} {total:,.2f}",
            ],
            [
                "Paid",
                f"{currency} {paid:,.2f}",
            ],
            [
                "Balance Due",
                f"{currency} {balance:,.2f}",
            ],
        ],
        colWidths=[
            130 * mm,
            40 * mm,
        ],
    )

    totals_table.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT",
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
                (
                    "LINEABOVE",
                    (0, 2),
                    (-1, 2),
                    1,
                    colors.black,
                ),
                (
                    "LINEABOVE",
                    (0, 4),
                    (-1, 4),
                    1,
                    colors.black,
                ),
            ]
        )
    )

    story.append(
        totals_table
    )

    story.append(
        Spacer(1, 10 * mm)
    )

    # ========================================================
    # PAYMENT INFORMATION
    # ========================================================

    story.append(
        Paragraph(
            "<b>Payment Information</b>",
            heading_style,
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    story.append(
        Paragraph(
            (
                "Please make payment by the invoice due date. "
                "Payment details should be provided separately "
                "by AVERRA if not already included in the "
                "commercial agreement."
            ),
            normal_style,
        )
    )

    # ========================================================
    # NOTES
    # ========================================================

    notes = clean_text(
        invoice.notes
    )

    if notes:

        story.append(
            Spacer(1, 8 * mm)
        )

        story.append(
            Paragraph(
                "<b>Notes</b>",
                heading_style,
            )
        )

        story.append(
            Paragraph(
                notes,
                normal_style,
            )
        )

    # ========================================================
    # FOOTER
    # ========================================================

    story.append(
        Spacer(1, 15 * mm)
    )

    story.append(
        Paragraph(
            "AVERRA STAFFING SOLUTIONS LTD",
            normal_style,
        )
    )

    document.build(
        story
    )

    buffer.seek(0)

    return buffer.getvalue()


def clear_invoice_state():
    """Clear invoice editing/deletion state."""

    st.session_state.editing_invoice_id = None
    st.session_state.confirm_delete_invoice_id = None


# ============================================================
# MAIN SCREEN
# ============================================================

def show_invoices():

    st.title("Invoices")

    st.caption(
        "Create invoices, download professional PDF invoices, "
        "export invoice data to CSV and track outstanding balances."
    )

    session = get_session()

    # ========================================================
    # SESSION STATE
    # ========================================================

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
            .order_by(
                Client.company_name
            )
            .all()
        )

        if not clients:

            st.warning(
                "Please add a client before creating an invoice."
            )

            return

        # ====================================================
        # LOAD ALL PLACEMENTS
        # ====================================================

        placements = (
            session.query(Placement)
            .order_by(
                Placement.id.desc()
            )
            .all()
        )

        # ====================================================
        # LOAD EDITING INVOICE
        # ====================================================

        editing_invoice = None

        if (
            st.session_state.editing_invoice_id
            is not None
        ):

            editing_invoice = session.get(
                Invoice,
                st.session_state.editing_invoice_id,
            )

            if editing_invoice is None:

                st.session_state.editing_invoice_id = None

        # ====================================================
        # PAGE SECTION
        # ====================================================

        if editing_invoice:

            st.subheader(
                "Edit Invoice "
                f"#{clean_text(editing_invoice.invoice_number)}"
            )

        else:

            st.subheader(
                "Create Invoice"
            )

        # ====================================================
        # CLIENT OPTIONS
        # ====================================================

        client_options = {
            (
                f"{clean_text(client.company_name)} "
                f"(ID: {client.id})"
            ): client.id
            for client in clients
        }

        client_labels = list(
            client_options.keys()
        )

        client_values = list(
            client_options.values()
        )

        if (
            editing_invoice
            and editing_invoice.client_id
            in client_values
        ):

            client_index = client_values.index(
                editing_invoice.client_id
            )

        else:

            client_index = 0

        # ====================================================
        # CURRENT CLIENT ID
        # ====================================================

        current_client_id = (
            editing_invoice.client_id
            if editing_invoice
            else client_values[client_index]
        )

        # ====================================================
        # PLACEMENTS FOR CURRENT CLIENT
        # ====================================================

        client_placements = [
            placement
            for placement in placements
            if placement.client_id
            == current_client_id
        ]

        placement_options = {
            "No placement": None
        }

        for placement in client_placements:

            placement_options[
                get_placement_label(
                    placement
                )
            ] = placement.id

        placement_labels = list(
            placement_options.keys()
        )

        placement_values = list(
            placement_options.values()
        )

        if (
            editing_invoice
            and editing_invoice.placement_id
            in placement_values
        ):

            placement_index = placement_values.index(
                editing_invoice.placement_id
            )

        else:

            placement_index = 0

        # ====================================================
        # FORM
        # ====================================================

        with st.form(
            "invoice_form"
        ):

            # =================================================
            # CLIENT
            # =================================================

            selected_client = st.selectbox(
                "Client",
                client_labels,
                index=client_index,
            )

            selected_client_id = (
                client_options[
                    selected_client
                ]
            )

            # =================================================
            # PLACEMENT
            # =================================================

            # The form cannot dynamically reload its options
            # when the client changes. The selected client is
            # therefore validated again when saving.

            current_client_placements = [
                placement
                for placement in placements
                if placement.client_id
                == selected_client_id
            ]

            dynamic_placement_options = {
                "No placement": None
            }

            for placement in current_client_placements:

                dynamic_placement_options[
                    get_placement_label(
                        placement
                    )
                ] = placement.id

            dynamic_placement_labels = list(
                dynamic_placement_options.keys()
            )

            # Make sure the index is valid.

            safe_placement_index = (
                placement_index
                if placement_index
                < len(dynamic_placement_labels)
                else 0
            )

            selected_placement = st.selectbox(
                "Related Placement",
                dynamic_placement_labels,
                index=safe_placement_index,
            )

            # =================================================
            # BASIC INFORMATION
            # =================================================

            invoice_number = st.text_input(
                "Invoice Number",
                value=(
                    clean_text(
                        editing_invoice.invoice_number
                    )
                    if editing_invoice
                    else ""
                ),
                placeholder="Example: INV-2026-001",
            )

            description = st.text_area(
                "Description",
                value=(
                    clean_text(
                        editing_invoice.description
                    )
                    if editing_invoice
                    else ""
                ),
                placeholder=(
                    "Example: Remote finance specialist "
                    "services - October 2026"
                ),
            )

            # =================================================
            # DATES
            # =================================================

            st.subheader(
                "Invoice Dates"
            )

            date_col1, date_col2 = st.columns(2)

            with date_col1:

                invoice_date = st.date_input(
                    "Invoice Date",
                    value=(
                        editing_invoice.invoice_date
                        if (
                            editing_invoice
                            and editing_invoice.invoice_date
                        )
                        else date.today()
                    ),
                )

            with date_col2:

                due_date = st.date_input(
                    "Due Date",
                    value=(
                        editing_invoice.due_date
                        if (
                            editing_invoice
                            and editing_invoice.due_date
                        )
                        else date.today()
                    ),
                )

            # =================================================
            # AMOUNTS
            # =================================================

            st.subheader(
                "Invoice Amount"
            )

            amount_col1, amount_col2 = st.columns(2)

            with amount_col1:

                subtotal = st.number_input(
                    "Subtotal",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    value=(
                        float(
                            editing_invoice.subtotal
                            or 0
                        )
                        if editing_invoice
                        else 0.0
                    ),
                )

            with amount_col2:

                tax = st.number_input(
                    "Tax",
                    min_value=0.0,
                    step=10.0,
                    format="%.2f",
                    value=(
                        float(
                            editing_invoice.tax
                            or 0
                        )
                        if editing_invoice
                        else 0.0
                    ),
                )

            total_amount = (
                subtotal + tax
            )

            st.info(
                f"Invoice Total: "
                f"**{total_amount:,.2f}**"
            )

            # =================================================
            # CURRENCY / STATUS
            # =================================================

            finance_col1, finance_col2 = st.columns(2)

            with finance_col1:

                current_currency = (
                    clean_text(
                        editing_invoice.currency
                    )
                    if editing_invoice
                    else ""
                )

                currency_index = (
                    CURRENCIES.index(
                        current_currency
                    )
                    if current_currency
                    in CURRENCIES
                    else 0
                )

                currency = st.selectbox(
                    "Currency",
                    CURRENCIES,
                    index=currency_index,
                )

            with finance_col2:

                current_status = (
                    clean_text(
                        editing_invoice.status
                    )
                    if editing_invoice
                    else ""
                )

                status_index = (
                    INVOICE_STATUSES.index(
                        current_status
                    )
                    if current_status
                    in INVOICE_STATUSES
                    else 0
                )

                status = st.selectbox(
                    "Invoice Status",
                    INVOICE_STATUSES,
                    index=status_index,
                )

            # =================================================
            # DOCUMENT
            # =================================================

            document_link = st.text_input(
                "Invoice Document Link",
                value=(
                    clean_text(
                        editing_invoice.document_link
                    )
                    if editing_invoice
                    else ""
                ),
                placeholder=(
                    "Optional external invoice document link"
                ),
            )

            # =================================================
            # NOTES
            # =================================================

            notes = st.text_area(
                "Notes",
                value=(
                    clean_text(
                        editing_invoice.notes
                    )
                    if editing_invoice
                    else ""
                ),
                placeholder="Invoice notes...",
            )

            # =================================================
            # SUBMIT
            # =================================================

            submitted = st.form_submit_button(
                (
                    "Save Changes"
                    if editing_invoice
                    else "Create Invoice"
                ),
                use_container_width=True,
            )

            if submitted:

                invoice_number_clean = (
                    invoice_number.strip()
                )

                description_clean = (
                    description.strip()
                )

                document_link_clean = (
                    document_link.strip()
                )

                notes_clean = (
                    notes.strip()
                )

                # =============================================
                # VALIDATION
                # =============================================

                validation_error = None

                if not invoice_number_clean:

                    validation_error = (
                        "Invoice number is required."
                    )

                elif due_date < invoice_date:

                    validation_error = (
                        "Due date cannot be before "
                        "invoice date."
                    )

                elif subtotal < 0:

                    validation_error = (
                        "Subtotal cannot be negative."
                    )

                elif tax < 0:

                    validation_error = (
                        "Tax cannot be negative."
                    )

                elif (
                    document_link_clean
                    and not valid_url(
                        document_link_clean
                    )
                ):

                    validation_error = (
                        "Please enter a valid document URL."
                    )

                # =============================================
                # SELECTED PLACEMENT
                # =============================================

                selected_placement_id = (
                    dynamic_placement_options[
                        selected_placement
                    ]
                )

                selected_placement_object = None

                if selected_placement_id:

                    selected_placement_object = (
                        session.get(
                            Placement,
                            selected_placement_id,
                        )
                    )

                    if (
                        selected_placement_object
                        is None
                    ):

                        validation_error = (
                            "The selected placement "
                            "could not be found."
                        )

                    elif (
                        selected_placement_object.client_id
                        != selected_client_id
                    ):

                        validation_error = (
                            "The selected placement "
                            "does not belong to the selected client."
                        )

                # =============================================
                # EXISTING PAYMENT VALIDATION
                # =============================================

                existing_paid = 0.0

                if editing_invoice:

                    existing_paid = float(
                        editing_invoice.amount_paid
                        or 0
                    )

                    if (
                        total_amount
                        < existing_paid
                    ):

                        validation_error = (
                            "Invoice total cannot be lower "
                            "than the amount already paid."
                        )

                    if (
                        has_payments(
                            editing_invoice
                        )
                        and currency
                        != clean_text(
                            editing_invoice.currency
                        )
                    ):

                        validation_error = (
                            "Currency cannot be changed "
                            "after payments have been recorded."
                        )

                # =============================================
                # PAYMENT / STATUS VALIDATION
                # =============================================

                if (
                    existing_paid
                    > total_amount
                ):

                    validation_error = (
                        "Amount paid cannot be greater "
                        "than the invoice total."
                    )

                if (
                    status == "Paid"
                    and total_amount
                    > existing_paid
                ):

                    validation_error = (
                        "An invoice cannot be marked Paid "
                        "while a balance remains outstanding."
                    )

                if (
                    status == "Partially Paid"
                    and existing_paid <= 0
                ):

                    validation_error = (
                        "Partially Paid requires a payment "
                        "to have been recorded."
                    )

                if (
                    status == "Cancelled"
                    and has_payments(
                        editing_invoice
                    )
                    if editing_invoice
                    else False
                ):

                    validation_error = (
                        "An invoice with recorded payments "
                        "should not be cancelled from this screen."
                    )

                if validation_error:

                    st.error(
                        validation_error
                    )

                else:

                    # =========================================
                    # DUPLICATE INVOICE NUMBER
                    # =========================================

                    duplicate_query = (
                        session.query(
                            Invoice
                        )
                        .filter(
                            Invoice.invoice_number.ilike(
                                invoice_number_clean
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

                    duplicate = (
                        duplicate_query.first()
                    )

                    if duplicate:

                        st.error(
                            "An invoice with this invoice "
                            "number already exists."
                        )

                    else:

                        # =====================================
                        # UPDATE
                        # =====================================

                        if editing_invoice:

                            editing_invoice.client_id = (
                                selected_client_id
                            )

                            editing_invoice.placement_id = (
                                selected_placement_id
                            )

                            editing_invoice.invoice_number = (
                                invoice_number_clean
                            )

                            editing_invoice.invoice_date = (
                                invoice_date
                            )

                            editing_invoice.due_date = (
                                due_date
                            )

                            editing_invoice.description = (
                                description_clean
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
                                document_link_clean
                            )

                            editing_invoice.notes = (
                                notes_clean
                            )

                            try:

                                session.commit()

                                clear_invoice_state()

                                st.success(
                                    "Invoice updated successfully."
                                )

                                st.rerun()

                            except Exception as e:

                                session.rollback()

                                st.error(
                                    "Could not update invoice: "
                                    f"{e}"
                                )

                        # =====================================
                        # CREATE
                        # =====================================

                        else:

                            invoice = Invoice(
                                client_id=selected_client_id,
                                placement_id=selected_placement_id,
                                invoice_number=invoice_number_clean,
                                invoice_date=invoice_date,
                                due_date=due_date,
                                description=description_clean,
                                subtotal=subtotal,
                                tax=tax,
                                total_amount=total_amount,
                                amount_paid=0.0,
                                currency=currency,
                                status=status,
                                document_link=document_link_clean,
                                notes=notes_clean,
                            )

                            try:

                                session.add(
                                    invoice
                                )

                                session.commit()

                                st.success(
                                    "Invoice created successfully."
                                )

                                st.rerun()

                            except Exception as e:

                                session.rollback()

                                st.error(
                                    "Could not create invoice: "
                                    f"{e}"
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

        # ====================================================
        # EXPORT ALL INVOICES
        # ====================================================

        if invoices:

            csv_data = get_csv_bytes(
                invoices
            )

            export_col1, export_col2 = st.columns(
                [1, 4]
            )

            with export_col1:

                st.download_button(
                    "Download CSV",
                    data=csv_data,
                    file_name=(
                        "averra_invoices.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                )

            with export_col2:

                st.caption(
                    "Download the complete invoice register "
                    "as an Excel-compatible CSV file."
                )

        # ====================================================
        # KPI SECTION
        # ====================================================

        if invoices:

            currency_totals = (
                get_currency_totals(
                    invoices
                )
            )

            st.markdown(
                "### Invoice Summary"
            )

            for currency in sorted(
                currency_totals.keys()
            ):

                totals = (
                    currency_totals[
                        currency
                    ]
                )

                st.markdown(
                    f"**{currency}**"
                )

                k1, k2, k3, k4, k5 = st.columns(5)

                with k1:

                    st.metric(
                        "Invoices",
                        totals["count"],
                    )

                with k2:

                    st.metric(
                        "Invoiced",
                        format_money(
                            currency,
                            totals["invoiced"],
                        ),
                    )

                with k3:

                    st.metric(
                        "Paid",
                        format_money(
                            currency,
                            totals["paid"],
                        ),
                    )

                with k4:

                    st.metric(
                        "Outstanding",
                        format_money(
                            currency,
                            totals["outstanding"],
                        ),
                    )

                with k5:

                    st.metric(
                        "Overdue",
                        format_money(
                            currency,
                            totals["overdue"],
                        ),
                    )

        if not invoices:

            st.info(
                "No invoices have been created yet."
            )

            return

        # ====================================================
        # FILTERS
        # ====================================================

        filter_col1, filter_col2, filter_col3 = (
            st.columns(3)
        )

        with filter_col1:

            search = st.text_input(
                "Search",
                placeholder=(
                    "Invoice number, client or description..."
                ),
            )

        with filter_col2:

            status_filter = st.selectbox(
                "Status",
                ["All"] + INVOICE_STATUSES,
            )

        with filter_col3:

            currency_filter = st.selectbox(
                "Currency",
                ["All"] + CURRENCIES,
            )

        # ====================================================
        # APPLY FILTERS
        # ====================================================

        filtered = invoices

        if search.strip():

            search_lower = (
                search.strip().lower()
            )

            filtered = [
                invoice
                for invoice in filtered
                if (
                    search_lower
                    in clean_text(
                        invoice.invoice_number
                    ).lower()
                )
                or (
                    search_lower
                    in get_client_name(
                        invoice
                    ).lower()
                )
                or (
                    search_lower
                    in clean_text(
                        invoice.description
                    ).lower()
                )
            ]

        if status_filter != "All":

            filtered = [
                invoice
                for invoice in filtered
                if get_effective_status(
                    invoice
                )
                == status_filter
            ]

        if currency_filter != "All":

            filtered = [
                invoice
                for invoice in filtered
                if clean_text(
                    invoice.currency
                )
                == currency_filter
            ]

        # ====================================================
        # FILTER RESULT
        # ====================================================

        st.caption(
            f"Showing {len(filtered)} "
            f"of {len(invoices)} invoice(s)"
        )

        if not filtered:

            st.info(
                "No invoices match your filters."
            )

            return

        # ====================================================
        # DISPLAY INVOICES
        # ====================================================

        for invoice in filtered:

            client_name = (
                get_client_name(invoice)
            )

            balance_due = (
                get_balance_due(invoice)
            )

            displayed_status = (
                get_effective_status(invoice)
            )

            total_amount = float(
                invoice.total_amount or 0
            )

            amount_paid = float(
                invoice.amount_paid or 0
            )

            currency = (
                clean_text(
                    invoice.currency
                )
                or "GBP"
            )

            payment_percentage = (
                calculate_payment_percentage(
                    total_amount,
                    amount_paid,
                )
            )

            with st.container(
                border=True
            ):

                # ==========================================
                # MAIN INFORMATION
                # ==========================================

                col1, col2, col3, col4, col5 = (
                    st.columns(
                        [2, 3, 2, 2, 1]
                    )
                )

                with col1:

                    st.write(
                        f"**{clean_text(invoice.invoice_number)}**"
                    )

                    if invoice.invoice_date:

                        st.caption(
                            invoice.invoice_date.strftime(
                                "%d %b %Y"
                            )
                        )

                with col2:

                    st.write(
                        f"**{client_name}**"
                    )

                    description_text = (
                        clean_text(
                            invoice.description
                        )
                    )

                    if description_text:

                        st.caption(
                            description_text
                        )

                with col3:

                    st.write(
                        "Total: **"
                        f"{format_money(currency, total_amount)}"
                        "**"
                    )

                    st.write(
                        "Paid: **"
                        f"{format_money(currency, amount_paid)}"
                        "**"
                    )

                    st.caption(
                        f"{payment_percentage:.0f}% paid"
                    )

                with col4:

                    st.write(
                        f"Status: **{displayed_status}**"
                    )

                    st.write(
                        "Balance: **"
                        f"{format_money(currency, balance_due)}"
                        "**"
                    )

                    if invoice.due_date:

                        st.caption(
                            "Due: "
                            + invoice.due_date.strftime(
                                "%d %b %Y"
                            )
                        )

                with col5:

                    edit_btn = st.button(
                        "Edit",
                        key=(
                            f"edit_invoice_"
                            f"{invoice.id}"
                        ),
                        use_container_width=True,
                    )

                    delete_btn = st.button(
                        "Delete",
                        key=(
                            f"delete_invoice_"
                            f"{invoice.id}"
                        ),
                        use_container_width=True,
                    )

                # ==========================================
                # ACTION BUTTONS
                # ==========================================

                action_col1, action_col2 = st.columns(
                    2
                )

                with action_col1:

                    pdf_available = True

                    try:

                        pdf_data = (
                            generate_invoice_pdf(
                                invoice
                            )
                        )

                    except Exception as e:

                        pdf_available = False

                        pdf_data = None

                        st.warning(
                            f"PDF unavailable: {e}"
                        )

                    if pdf_available:

                        pdf_filename = (
                            clean_text(
                                invoice.invoice_number
                            )
                            or f"invoice_{invoice.id}"
                        )

                        pdf_filename = (
                            pdf_filename
                            .replace("/", "-")
                            .replace("\\", "-")
                            + ".pdf"
                        )

                        st.download_button(
                            "Download Invoice PDF",
                            data=pdf_data,
                            file_name=pdf_filename,
                            mime="application/pdf",
                            key=(
                                f"download_pdf_"
                                f"{invoice.id}"
                            ),
                            use_container_width=True,
                        )

                with action_col2:

                    st.download_button(
                        "Download CSV",
                        data=get_csv_bytes(
                            [invoice]
                        ),
                        file_name=(
                            f"{clean_text(invoice.invoice_number)}"
                            ".csv"
                        ),
                        mime="text/csv",
                        key=(
                            f"download_csv_"
                            f"{invoice.id}"
                        ),
                        use_container_width=True,
                    )

                # ==========================================
                # EDIT
                # ==========================================

                if edit_btn:

                    st.session_state.editing_invoice_id = (
                        invoice.id
                    )

                    st.session_state.confirm_delete_invoice_id = (
                        None
                    )

                    st.rerun()

                # ==========================================
                # DELETE REQUEST
                # ==========================================

                if delete_btn:

                    st.session_state.confirm_delete_invoice_id = (
                        invoice.id
                    )

                    st.session_state.editing_invoice_id = (
                        None
                    )

                    st.rerun()

                # ==========================================
                # DELETE CONFIRMATION
                # ==========================================

                if (
                    st.session_state.confirm_delete_invoice_id
                    == invoice.id
                ):

                    st.warning(
                        "Are you sure you want to delete "
                        f"invoice **{clean_text(invoice.invoice_number)}**?"
                    )

                    if has_payments(invoice):

                        st.error(
                            "This invoice cannot be deleted "
                            "because payments are attached to it."
                        )

                        if st.button(
                            "Close",
                            key=(
                                f"close_delete_"
                                f"{invoice.id}"
                            ),
                        ):

                            st.session_state.confirm_delete_invoice_id = (
                                None
                            )

                            st.rerun()

                    else:

                        st.caption(
                            "Invoices should normally be "
                            "cancelled rather than deleted "
                            "once they have been issued."
                        )

                        confirm_col1, confirm_col2 = (
                            st.columns(2)
                        )

                        with confirm_col1:

                            confirm_delete = st.button(
                                "Yes, Delete Invoice",
                                key=(
                                    f"confirm_delete_"
                                    f"{invoice.id}"
                                ),
                                type="primary",
                                use_container_width=True,
                            )

                        with confirm_col2:

                            cancel_delete = st.button(
                                "Cancel",
                                key=(
                                    f"cancel_delete_"
                                    f"{invoice.id}"
                                ),
                                use_container_width=True,
                            )

                        if cancel_delete:

                            st.session_state.confirm_delete_invoice_id = (
                                None
                            )

                            st.rerun()

                        if confirm_delete:

                            try:

                                session.delete(
                                    invoice
                                )

                                session.commit()

                                st.session_state.confirm_delete_invoice_id = (
                                    None
                                )

                                st.success(
                                    "Invoice deleted successfully."
                                )

                                st.rerun()

                            except Exception as e:

                                session.rollback()

                                st.session_state.confirm_delete_invoice_id = (
                                    None
                                )

                                st.error(
                                    "Could not delete invoice: "
                                    f"{e}"
                                )

                # ==========================================
                # EXISTING DOCUMENT
                # ==========================================

                if clean_text(
                    invoice.document_link
                ):

                    st.link_button(
                        "Open Existing Invoice Link",
                        invoice.document_link,
                    )

                # ==========================================
                # NOTES
                # ==========================================

                if clean_text(
                    invoice.notes
                ):

                    st.caption(
                        "Notes: "
                        f"{clean_text(invoice.notes)}"
                    )

    except Exception as e:

        session.rollback()

        st.error(
            "An error occurred while loading invoices: "
            f"{e}"
        )

    finally:

        session.close()