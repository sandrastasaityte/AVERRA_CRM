import csv
import io
from datetime import date, timedelta

import streamlit as st
from sqlalchemy.exc import IntegrityError

from database import get_session
from models import Payment, Invoice


# ============================================================
# CONSTANTS
# ============================================================

PAYMENT_METHODS = [
    "Bank Transfer",
    "Monzo",
    "Revolut",
    "Wise",
    "Card",
    "Direct Debit",
    "Cash",
    "Other",
]

PAYMENT_STATUSES = [
    "Received",
    "Pending",
    "Failed",
    "Reversed",
]

NON_RECEIVED_STATUSES = {
    "Pending",
    "Failed",
    "Reversed",
}

CURRENCIES = [
    "GBP",
    "EUR",
    "USD",
    "INR",
]

MAX_REFERENCE_LENGTH = 200
MAX_NOTES_LENGTH = 2000

PAYMENT_DATE_FILTERS = [
    "All Dates",
    "Today",
    "Last 7 Days",
    "Last 30 Days",
    "Last 90 Days",
    "This Year",
    "Custom Range",
]

RECONCILIATION_FILTERS = [
    "All",
    "Reconciled",
    "Needs Reconciliation",
]

PAYMENT_ACTION_FILTERS = [
    "All",
    "Received Payments",
    "Pending Payments",
    "Failed Payments",
    "Reversed Payments",
]


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(value):
    """Safely clean text."""

    if value is None:
        return ""

    return str(value).strip()


def safe_float(value, default=0.0):
    """Safely convert a value to float."""

    try:
        return float(value or 0)

    except (TypeError, ValueError):
        return default


def round_money(value):
    """Round financial values to two decimal places."""

    return round(
        safe_float(value),
        2,
    )


def format_money(currency, amount):
    """Format a monetary value."""

    currency = clean_text(currency) or "GBP"

    return (
        f"{currency} "
        f"{round_money(amount):,.2f}"
    )


def format_date(value):
    """Format a date for display."""

    if not value:
        return "No date"

    try:

        return value.strftime(
            "%d/%m/%Y"
        )

    except AttributeError:

        return str(value)


def get_date_value(value):
    """Safely return a date value."""

    if isinstance(value, date):
        return value

    return None


def get_payment_age_days(payment):
    """Return payment age in days."""

    payment_date = get_date_value(
        getattr(
            payment,
            "payment_date",
            None,
        )
    )

    if not payment_date:
        return None

    return max(
        (
            date.today()
            - payment_date
        ).days,
        0,
    )


# ============================================================
# INVOICE HELPERS
# ============================================================

def get_invoice_number(invoice):
    """Return a safe invoice number."""

    if not invoice:
        return "Unknown Invoice"

    return (
        clean_text(
            getattr(
                invoice,
                "invoice_number",
                None,
            )
        )
        or f"Invoice #{invoice.id}"
    )


def get_invoice_number_from_payment(payment):
    """Return the payment's invoice number."""

    if not payment:
        return "Unknown Invoice"

    return get_invoice_number(
        getattr(
            payment,
            "invoice",
            None,
        )
    )


def get_client_name_from_invoice(invoice):
    """Return invoice client name."""

    if (
        invoice
        and getattr(
            invoice,
            "client",
            None,
        )
    ):

        return (
            clean_text(
                getattr(
                    invoice.client,
                    "company_name",
                    None,
                )
            )
            or "Unknown Client"
        )

    return "Unknown Client"


def get_client_name(payment):
    """Return payment client name."""

    if not payment:
        return "Unknown Client"

    return get_client_name_from_invoice(
        getattr(
            payment,
            "invoice",
            None,
        )
    )


def get_invoice_currency(invoice):
    """Return invoice currency."""

    if not invoice:
        return "GBP"

    return (
        clean_text(
            getattr(
                invoice,
                "currency",
                None,
            )
        )
        or "GBP"
    )


def get_invoice_total(invoice):
    """Return invoice total."""

    if not invoice:
        return 0.0

    return max(
        round_money(
            getattr(
                invoice,
                "total_amount",
                0,
            )
        ),
        0.0,
    )


def get_invoice_paid(invoice):
    """Return invoice amount paid."""

    if not invoice:
        return 0.0

    return max(
        round_money(
            getattr(
                invoice,
                "amount_paid",
                0,
            )
        ),
        0.0,
    )


def get_calculated_invoice_balance(invoice):
    """Calculate invoice balance from total minus amount paid."""

    if not invoice:
        return 0.0

    total = get_invoice_total(
        invoice
    )

    paid = get_invoice_paid(
        invoice
    )

    return max(
        round_money(
            total - paid
        ),
        0.0,
    )


def get_invoice_balance(invoice):
    """
    Return invoice balance.

    Uses the model balance_due property when available,
    otherwise calculates it independently.
    """

    if not invoice:
        return 0.0

    try:

        return max(
            round_money(
                invoice.balance_due
            ),
            0.0,
        )

    except (
        TypeError,
        ValueError,
        AttributeError,
    ):

        return get_calculated_invoice_balance(
            invoice
        )


def get_payment_percentage(invoice):
    """Return percentage of invoice paid."""

    total = get_invoice_total(
        invoice
    )

    if total <= 0:
        return 0.0

    paid = min(
        get_invoice_paid(invoice),
        total,
    )

    return (
        paid / total
    ) * 100


def get_payment_state(invoice):
    """Return effective payment state."""

    if not invoice:
        return "Unpaid"

    total = get_invoice_total(
        invoice
    )

    paid = get_invoice_paid(
        invoice
    )

    if total <= 0:
        return "Unpaid"

    if paid <= 0:
        return "Unpaid"

    if paid >= total - 0.01:
        return "Paid"

    return "Partially Paid"


def get_invoice_status(invoice):
    """Return stored invoice status."""

    if not invoice:
        return "Unknown"

    return (
        clean_text(
            getattr(
                invoice,
                "status",
                None,
            )
        )
        or "Unknown"
    )


def is_invoice_cancelled(invoice):
    """Return True if invoice is cancelled."""

    return (
        get_invoice_status(invoice)
        == "Cancelled"
    )


def is_invoice_fully_paid(invoice):
    """Return True if invoice is fully paid."""

    total = get_invoice_total(
        invoice
    )

    paid = get_invoice_paid(
        invoice
    )

    return (
        total > 0
        and paid >= total - 0.01
    )


# ============================================================
# PAYMENT HELPERS
# ============================================================

def get_payment_amount(payment):
    """Return safe payment amount."""

    if not payment:
        return 0.0

    return max(
        round_money(
            getattr(
                payment,
                "amount",
                0,
            )
        ),
        0.0,
    )


def get_payment_status(payment):
    """Return payment status."""

    if not payment:
        return "Unknown"

    return (
        clean_text(
            getattr(
                payment,
                "status",
                None,
            )
        )
        or "Unknown"
    )


def payment_is_received(payment):
    """Return True when payment counts as received."""

    return (
        get_payment_status(payment)
        == "Received"
    )


def payment_is_non_received(payment):
    """Return True when payment is not received."""

    return (
        get_payment_status(payment)
        in NON_RECEIVED_STATUSES
    )


def get_payment_status_icon(status):
    """Return payment status icon."""

    icons = {
        "Received": "🟢",
        "Pending": "🟡",
        "Failed": "🔴",
        "Reversed": "🟠",
    }

    return icons.get(
        status,
        "⚪",
    )


def get_payment_currency(payment):
    """Return payment currency."""

    return (
        clean_text(
            getattr(
                payment,
                "currency",
                None,
            )
        )
        or "GBP"
    )


def get_payment_method(payment):
    """Return payment method."""

    return (
        clean_text(
            getattr(
                payment,
                "payment_method",
                None,
            )
        )
        or "Not specified"
    )


def get_payment_reference(payment):
    """Return payment reference."""

    return clean_text(
        getattr(
            payment,
            "reference",
            None,
        )
    )


# ============================================================
# PAYMENT TOTALS
# ============================================================

def get_total_by_status(
    payments,
    status,
):
    """
    Calculate totals by currency for a payment status.

    Currencies are deliberately kept separate.
    """

    totals = {}

    for payment in payments:

        if (
            get_payment_status(payment)
            != status
        ):
            continue

        currency = get_payment_currency(
            payment
        )

        amount = get_payment_amount(
            payment
        )

        totals[currency] = round_money(
            totals.get(
                currency,
                0.0,
            )
            + amount
        )

    return totals


def get_total_by_currency(payments):
    """Calculate payment totals by currency."""

    totals = {}

    for payment in payments:

        currency = get_payment_currency(
            payment
        )

        amount = get_payment_amount(
            payment
        )

        totals[currency] = round_money(
            totals.get(
                currency,
                0.0,
            )
            + amount
        )

    return totals


# ============================================================
# INVOICE PAYMENT RECONCILIATION
# ============================================================

def get_received_payments_for_invoice(
    payments,
    invoice_id,
):
    """Return received payments for an invoice."""

    return [
        payment
        for payment in payments
        if (
            getattr(
                payment,
                "invoice_id",
                None,
            )
            == invoice_id
            and payment_is_received(
                payment
            )
        )
    ]


def get_invoice_received_total_from_payments(
    payments,
    invoice_id,
):
    """
    Calculate received payment total directly
    from Payment records.
    """

    total = 0.0

    for payment in get_received_payments_for_invoice(
        payments,
        invoice_id,
    ):

        total += get_payment_amount(
            payment
        )

    return round_money(
        total
    )


def reconcile_invoice_from_payments(
    invoice,
    payments,
):
    """
    Recalculate Invoice.amount_paid from
    actual Received payment records.

    This is the core financial reconciliation
    mechanism for the Payments screen.
    """

    if not invoice:
        return

    received_total = (
        get_invoice_received_total_from_payments(
            payments,
            invoice.id,
        )
    )

    invoice_total = get_invoice_total(
        invoice
    )

    if invoice_total <= 0:

        invoice.amount_paid = 0.0

        return

    invoice.amount_paid = min(
        received_total,
        invoice_total,
    )

    if invoice.status == "Cancelled":
        return

    if invoice.amount_paid <= 0:

        if invoice.status in {
            "Paid",
            "Partially Paid",
        }:

            invoice.status = "Sent"

    elif (
        invoice.amount_paid
        >= invoice_total - 0.01
    ):

        invoice.amount_paid = (
            invoice_total
        )

        invoice.status = "Paid"

    else:

        invoice.status = (
            "Partially Paid"
        )


def get_invoice_reconciliation_status(
    invoice,
    payments,
):
    """
    Compare Invoice.amount_paid with
    actual Received Payment records.
    """

    if not invoice:
        return {
            "matched": True,
            "invoice_paid": 0.0,
            "payment_paid": 0.0,
            "difference": 0.0,
        }

    invoice_paid = get_invoice_paid(
        invoice
    )

    payment_paid = (
        get_invoice_received_total_from_payments(
            payments,
            invoice.id,
        )
    )

    difference = round_money(
        invoice_paid
        - payment_paid
    )

    return {
        "matched": abs(difference) <= 0.01,
        "invoice_paid": invoice_paid,
        "payment_paid": payment_paid,
        "difference": difference,
    }


def get_reconciliation_label(
    invoice,
    payments,
):
    """Return readable reconciliation state."""

    reconciliation = (
        get_invoice_reconciliation_status(
            invoice,
            payments,
        )
    )

    if reconciliation["matched"]:
        return "Reconciled"

    return "Needs Reconciliation"


# ============================================================
# DATA QUALITY
# ============================================================

def get_invoice_data_warning(
    invoice,
    payments=None,
):
    """
    Detect invoice/payment inconsistencies.
    """

    if not invoice:
        return None

    total = get_invoice_total(
        invoice
    )

    paid = get_invoice_paid(
        invoice
    )

    calculated_balance = (
        get_calculated_invoice_balance(
            invoice
        )
    )

    if paid > total + 0.01:

        return (
            "The recorded amount paid is greater "
            "than the invoice total."
        )

    if payments is not None:

        reconciliation = (
            get_invoice_reconciliation_status(
                invoice,
                payments,
            )
        )

        if not reconciliation["matched"]:

            return (
                "Invoice amount paid does not match "
                "the total of its Received payment records."
            )

    try:

        stored_balance = round_money(
            invoice.balance_due
        )

        if (
            abs(
                stored_balance
                - calculated_balance
            )
            > 0.01
        ):

            return (
                "The stored invoice balance does not "
                "match invoice total minus amount paid."
            )

    except AttributeError:

        pass

    return None


def get_payment_data_warnings(
    payment,
    invoice,
):
    """Return payment-level data quality warnings."""

    warnings = []

    amount = get_payment_amount(
        payment
    )

    status = get_payment_status(
        payment
    )

    payment_currency = get_payment_currency(
        payment
    )

    invoice_currency = get_invoice_currency(
        invoice
    )

    if amount <= 0:

        warnings.append(
            "Payment amount is zero or invalid."
        )

    if (
        invoice
        and payment_currency
        != invoice_currency
    ):

        warnings.append(
            "Payment currency does not match invoice currency."
        )

    if (
        status == "Received"
        and invoice
        and is_invoice_cancelled(invoice)
    ):

        warnings.append(
            "Received payment is attached to a cancelled invoice."
        )

    payment_date = get_date_value(
        getattr(
            payment,
            "payment_date",
            None,
        )
    )

    if (
        payment_date
        and payment_date > date.today()
    ):

        warnings.append(
            "Payment date is in the future."
        )

    return warnings


# ============================================================
# DUPLICATE REFERENCE
# ============================================================

def has_duplicate_reference(
    session,
    invoice_id,
    reference,
    exclude_payment_id=None,
):
    """
    Check whether a payment reference already exists
    for the same invoice.

    Blank references are allowed.
    """

    reference = clean_text(
        reference
    )

    if not reference:
        return False

    payments = (
        session.query(Payment)
        .filter(
            Payment.invoice_id
            == invoice_id
        )
        .all()
    )

    reference_lower = (
        reference.lower()
    )

    for payment in payments:

        if (
            exclude_payment_id is not None
            and payment.id
            == exclude_payment_id
        ):

            continue

        existing_reference = (
            get_payment_reference(
                payment
            )
        )

        if (
            existing_reference.lower()
            == reference_lower
        ):

            return True

    return False


# ============================================================
# VALIDATION
# ============================================================

def validate_payment_data(
    payment_date,
    payment_amount,
    payment_status,
    selected_invoice,
    reference,
    session,
):
    """Validate payment before saving."""

    errors = []

    payment_amount = round_money(
        payment_amount
    )

    reference = clean_text(
        reference
    )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    if not payment_date:

        errors.append(
            "Please provide a payment date."
        )

    elif payment_date > date.today():

        errors.append(
            "Payment date cannot be in the future."
        )

    # --------------------------------------------------------
    # AMOUNT
    # --------------------------------------------------------

    if payment_amount <= 0:

        errors.append(
            "Payment amount must be greater than zero."
        )

    # --------------------------------------------------------
    # INVOICE
    # --------------------------------------------------------

    if not selected_invoice:

        errors.append(
            "Please select an invoice."
        )

        return errors

    # --------------------------------------------------------
    # CANCELLED
    # --------------------------------------------------------

    if is_invoice_cancelled(
        selected_invoice
    ):

        errors.append(
            "Payments cannot be recorded against a cancelled invoice."
        )

    # --------------------------------------------------------
    # INVOICE TOTAL
    # --------------------------------------------------------

    total = get_invoice_total(
        selected_invoice
    )

    balance = get_invoice_balance(
        selected_invoice
    )

    if (
        payment_status
        == "Received"
    ):

        if total <= 0:

            errors.append(
                "A Received payment cannot be recorded "
                "for an invoice with a zero total."
            )

        elif balance <= 0.01:

            errors.append(
                "This invoice is already fully paid."
            )

        elif (
            payment_amount
            > balance + 0.01
        ):

            currency = get_invoice_currency(
                selected_invoice
            )

            errors.append(
                "Payment cannot exceed the current "
                f"balance of {format_money(currency, balance)}."
            )

    # --------------------------------------------------------
    # NON-RECEIVED PAYMENT
    # --------------------------------------------------------

    if payment_status != "Received":

        if payment_amount <= 0:

            errors.append(
                "Payment amount must be greater than zero."
            )

    # --------------------------------------------------------
    # REFERENCE
    # --------------------------------------------------------

    if len(reference) > MAX_REFERENCE_LENGTH:

        errors.append(
            f"Payment reference cannot exceed "
            f"{MAX_REFERENCE_LENGTH} characters."
        )

    # --------------------------------------------------------
    # DUPLICATE REFERENCE
    # --------------------------------------------------------

    if reference:

        if has_duplicate_reference(
            session,
            selected_invoice.id,
            reference,
        ):

            errors.append(
                "A payment with this reference already "
                "exists for this invoice."
            )

    return errors


# ============================================================
# CSV EXPORT
# ============================================================

def get_csv_bytes(payments):
    """Create CSV export."""

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow(
        [
            "Payment ID",
            "Payment Date",
            "Payment Age Days",
            "Invoice Number",
            "Client",
            "Amount",
            "Currency",
            "Payment Method",
            "Reference",
            "Status",
            "Invoice Total",
            "Invoice Paid",
            "Invoice Balance",
            "Payment State",
            "Reconciliation",
            "Notes",
        ]
    )

    for payment in payments:

        payment_date = getattr(
            payment,
            "payment_date",
            None,
        )

        payment_date_text = (
            payment_date.strftime(
                "%Y-%m-%d"
            )
            if payment_date
            else ""
        )

        invoice = getattr(
            payment,
            "invoice",
            None,
        )

        reconciliation = (
            get_reconciliation_label(
                invoice,
                [
                    payment,
                    *(
                        getattr(
                            invoice,
                            "payments",
                            [],
                        )
                        or []
                    ),
                ],
            )
            if invoice
            else "Unknown"
        )

        writer.writerow(
            [
                payment.id,
                payment_date_text,
                get_payment_age_days(
                    payment
                ),
                get_invoice_number_from_payment(
                    payment
                ),
                get_client_name(
                    payment
                ),
                f"{get_payment_amount(payment):.2f}",
                get_payment_currency(
                    payment
                ),
                get_payment_method(
                    payment
                ),
                get_payment_reference(
                    payment
                ),
                get_payment_status(
                    payment
                ),
                (
                    f"{get_invoice_total(invoice):.2f}"
                    if invoice
                    else ""
                ),
                (
                    f"{get_invoice_paid(invoice):.2f}"
                    if invoice
                    else ""
                ),
                (
                    f"{get_invoice_balance(invoice):.2f}"
                    if invoice
                    else ""
                ),
                (
                    get_payment_state(invoice)
                    if invoice
                    else ""
                ),
                reconciliation,
                clean_text(
                    getattr(
                        payment,
                        "notes",
                        None,
                    )
                ),
            ]
        )

    return output.getvalue().encode(
        "utf-8-sig"
    )


# ============================================================
# INVOICE LABEL
# ============================================================

def build_invoice_label(invoice):
    """Build a safe invoice dropdown label."""

    number = get_invoice_number(
        invoice
    )

    client = get_client_name_from_invoice(
        invoice
    )

    currency = get_invoice_currency(
        invoice
    )

    balance = get_invoice_balance(
        invoice
    )

    state = get_payment_state(
        invoice
    )

    return (
        f"{number} | "
        f"{client} | "
        f"Balance: "
        f"{currency} "
        f"{balance:,.2f} | "
        f"{state}"
    )


# ============================================================
# DATE FILTER
# ============================================================

def payment_matches_date_filter(
    payment,
    date_filter,
    custom_start=None,
    custom_end=None,
):
    """Check whether payment matches selected date filter."""

    payment_date = get_date_value(
        getattr(
            payment,
            "payment_date",
            None,
        )
    )

    if date_filter == "All Dates":

        return True

    if not payment_date:

        return False

    today = date.today()

    if date_filter == "Today":

        return payment_date == today

    if date_filter == "Last 7 Days":

        start_date = (
            today
            - timedelta(days=6)
        )

        return (
            start_date
            <= payment_date
            <= today
        )

    if date_filter == "Last 30 Days":

        start_date = (
            today
            - timedelta(days=29)
        )

        return (
            start_date
            <= payment_date
            <= today
        )

    if date_filter == "Last 90 Days":

        start_date = (
            today
            - timedelta(days=89)
        )

        return (
            start_date
            <= payment_date
            <= today
        )

    if date_filter == "This Year":

        return (
            payment_date.year
            == today.year
        )

    if date_filter == "Custom Range":

        if not custom_start:
            return False

        if not custom_end:
            return False

        return (
            custom_start
            <= payment_date
            <= custom_end
        )

    return True


# ============================================================
# PAYMENT REGISTER SEARCH
# ============================================================

def get_payment_search_text(payment):
    """Build searchable payment text."""

    invoice = getattr(
        payment,
        "invoice",
        None,
    )

    return " ".join(
        [
            get_invoice_number_from_payment(
                payment
            ),
            get_client_name(
                payment
            ),
            get_payment_reference(
                payment
            ),
            clean_text(
                getattr(
                    payment,
                    "notes",
                    None,
                )
            ),
            get_payment_status(
                payment
            ),
            get_payment_method(
                payment
            ),
            get_payment_currency(
                payment
            ),
            (
                get_invoice_status(invoice)
                if invoice
                else ""
            ),
        ]
    ).lower()


# ============================================================
# MAIN SCREEN
# ============================================================

def show_payments():

    st.title(
        "Payments"
    )

    st.caption(
        "Record, reconcile and monitor client payments against invoices."
    )

    session = get_session()

    try:

        # ====================================================
        # LOAD DATA
        # ====================================================

        invoices = (
            session.query(Invoice)
            .order_by(
                Invoice.id.desc()
            )
            .all()
        )

        payments = (
            session.query(Payment)
            .order_by(
                Payment.payment_date.desc(),
                Payment.id.desc(),
            )
            .all()
        )

        # ====================================================
        # GLOBAL RECONCILIATION CHECK
        # ====================================================

        reconciliation_issues = []

        for invoice in invoices:

            reconciliation = (
                get_invoice_reconciliation_status(
                    invoice,
                    payments,
                )
            )

            if not reconciliation["matched"]:

                reconciliation_issues.append(
                    invoice
                )

        # ====================================================
        # PAYMENT STATUS GROUPS
        # ====================================================

        received_payments = [
            payment
            for payment in payments
            if payment_is_received(
                payment
            )
        ]

        pending_payments = [
            payment
            for payment in payments
            if get_payment_status(
                payment
            ) == "Pending"
        ]

        failed_payments = [
            payment
            for payment in payments
            if get_payment_status(
                payment
            ) == "Failed"
        ]

        reversed_payments = [
            payment
            for payment in payments
            if get_payment_status(
                payment
            ) == "Reversed"
        ]

        received_totals = (
            get_total_by_status(
                payments,
                "Received",
            )
        )

        pending_totals = (
            get_total_by_status(
                payments,
                "Pending",
            )
        )

        failed_totals = (
            get_total_by_status(
                payments,
                "Failed",
            )
        )

        reversed_totals = (
            get_total_by_status(
                payments,
                "Reversed",
            )
        )

        # ====================================================
        # TOP-LEVEL RECONCILIATION WARNING
        # ====================================================

        if reconciliation_issues:

            st.warning(
                f"{len(reconciliation_issues)} invoice(s) "
                "have payment reconciliation differences."
            )

            with st.expander(
                "View reconciliation issues"
            ):

                for invoice in reconciliation_issues:

                    reconciliation = (
                        get_invoice_reconciliation_status(
                            invoice,
                            payments,
                        )
                    )

                    currency = (
                        get_invoice_currency(
                            invoice
                        )
                    )

                    difference = abs(
                        reconciliation[
                            "difference"
                        ]
                    )

                    st.write(
                        f"**{get_invoice_number(invoice)}** — "
                        f"{get_client_name_from_invoice(invoice)} — "
                        f"Difference: "
                        f"{format_money(currency, difference)}"
                    )

        # ====================================================
        # KPI SECTION
        # ====================================================

        col1, col2, col3, col4, col5, col6 = st.columns(
            6
        )

        col1.metric(
            "Payment Records",
            len(payments),
        )

        col2.metric(
            "Received",
            len(received_payments),
        )

        col3.metric(
            "Pending",
            len(pending_payments),
        )

        col4.metric(
            "Failed",
            len(failed_payments),
        )

        col5.metric(
            "Reversed",
            len(reversed_payments),
        )

        col6.metric(
            "Reconciliation Issues",
            len(reconciliation_issues),
        )

        # ====================================================
        # RECEIVED TOTALS
        # ====================================================

        st.subheader(
            "Received Payments"
        )

        if received_totals:

            columns = st.columns(
                min(
                    len(received_totals),
                    4,
                )
            )

            for index, (
                currency,
                amount,
            ) in enumerate(
                sorted(
                    received_totals.items()
                )
            ):

                columns[
                    index % len(columns)
                ].metric(
                    currency,
                    f"{amount:,.2f}",
                )

        else:

            st.info(
                "No received payments recorded yet."
            )

        # ====================================================
        # NON-RECEIVED TOTALS
        # ====================================================

        non_received_totals = {}

        for source_totals in [
            pending_totals,
            failed_totals,
            reversed_totals,
        ]:

            for currency, amount in (
                source_totals.items()
            ):

                non_received_totals[
                    currency
                ] = round_money(
                    non_received_totals.get(
                        currency,
                        0.0,
                    )
                    + amount
                )

        if non_received_totals:

            st.caption(
                "Pending, failed and reversed amounts are "
                "tracked separately and do not increase "
                "invoice amount paid."
            )

            columns = st.columns(
                min(
                    len(non_received_totals),
                    4,
                )
            )

            for index, (
                currency,
                amount,
            ) in enumerate(
                sorted(
                    non_received_totals.items()
                )
            ):

                columns[
                    index % len(columns)
                ].metric(
                    f"Non-Received {currency}",
                    f"{amount:,.2f}",
                )

        # ====================================================
        # RECORD PAYMENT
        # ====================================================

        st.divider()

        st.subheader(
            "Record Payment"
        )

        if not invoices:

            st.info(
                "Create an invoice before recording a payment."
            )

        else:

            invoice_options = {
                invoice.id: invoice
                for invoice in invoices
            }

            invoice_ids = list(
                invoice_options.keys()
            )

            selected_invoice_id = st.selectbox(
                "Invoice",
                options=invoice_ids,
                format_func=lambda invoice_id:
                    build_invoice_label(
                        invoice_options[
                            invoice_id
                        ]
                    ),
                key="payment_invoice_selector",
            )

            selected_invoice = (
                invoice_options[
                    selected_invoice_id
                ]
            )

            # ------------------------------------------------
            # INVOICE SUMMARY
            # ------------------------------------------------

            total = get_invoice_total(
                selected_invoice
            )

            paid = get_invoice_paid(
                selected_invoice
            )

            balance = get_invoice_balance(
                selected_invoice
            )

            currency = get_invoice_currency(
                selected_invoice
            )

            percentage = (
                get_payment_percentage(
                    selected_invoice
                )
            )

            payment_state = (
                get_payment_state(
                    selected_invoice
                )
            )

            invoice_status = (
                get_invoice_status(
                    selected_invoice
                )
            )

            summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(
                4
            )

            summary_col1.metric(
                "Invoice Total",
                format_money(
                    currency,
                    total,
                ),
            )

            summary_col2.metric(
                "Amount Paid",
                format_money(
                    currency,
                    paid,
                ),
            )

            summary_col3.metric(
                "Balance Due",
                format_money(
                    currency,
                    balance,
                ),
            )

            summary_col4.metric(
                "Payment State",
                payment_state,
            )

            st.progress(
                min(
                    max(
                        percentage / 100,
                        0.0,
                    ),
                    1.0,
                )
            )

            st.caption(
                f"{percentage:.1f}% of the invoice "
                "has been recorded as paid."
            )

            # ------------------------------------------------
            # RECONCILIATION
            # ------------------------------------------------

            reconciliation = (
                get_invoice_reconciliation_status(
                    selected_invoice,
                    payments,
                )
            )

            if reconciliation["matched"]:

                st.success(
                    "Payment records reconcile with "
                    "the invoice amount paid."
                )

            else:

                difference = (
                    reconciliation[
                        "difference"
                    ]
                )

                st.error(
                    "Reconciliation difference: "
                    f"{format_money(currency, abs(difference))}. "
                    "The invoice amount paid does not currently "
                    "match its Received payment records."
                )

                reconcile_col1, reconcile_col2 = st.columns(
                    [1, 3]
                )

                with reconcile_col1:

                    reconcile_clicked = st.button(
                        "Reconcile Invoice",
                        type="primary",
                        key=(
                            f"reconcile_invoice_"
                            f"{selected_invoice.id}"
                        ),
                        use_container_width=True,
                    )

                with reconcile_col2:

                    st.caption(
                        "This recalculates Invoice.amount_paid "
                        "from the invoice's Received payment records."
                    )

                if reconcile_clicked:

                    try:

                        invoice_payments = (
                            session.query(Payment)
                            .filter(
                                Payment.invoice_id
                                == selected_invoice.id
                            )
                            .all()
                        )

                        reconcile_invoice_from_payments(
                            selected_invoice,
                            invoice_payments,
                        )

                        session.commit()

                        st.success(
                            "Invoice reconciled successfully."
                        )

                        st.rerun()

                    except Exception:

                        session.rollback()

                        st.error(
                            "The invoice could not be reconciled."
                        )

            # ------------------------------------------------
            # DATA WARNING
            # ------------------------------------------------

            warning = (
                get_invoice_data_warning(
                    selected_invoice,
                    payments,
                )
            )

            if warning:

                st.warning(
                    warning
                )

            # ------------------------------------------------
            # SELECTED INVOICE PAYMENT HISTORY
            # ------------------------------------------------

            selected_invoice_payments = [
                payment
                for payment in payments
                if payment.invoice_id
                == selected_invoice_id
            ]

            if selected_invoice_payments:

                st.markdown(
                    "#### Payment History"
                )

                for payment in selected_invoice_payments:

                    payment_status = (
                        get_payment_status(
                            payment
                        )
                    )

                    payment_amount = (
                        get_payment_amount(
                            payment
                        )
                    )

                    payment_reference = (
                        get_payment_reference(
                            payment
                        )
                    )

                    payment_age = (
                        get_payment_age_days(
                            payment
                        )
                    )

                    age_text = (
                        f"{payment_age} day(s) old"
                        if payment_age is not None
                        else "Age unknown"
                    )

                    st.write(
                        f"{get_payment_status_icon(payment_status)} "
                        f"{format_date(payment.payment_date)} — "
                        f"{format_money(currency, payment_amount)} — "
                        f"{payment_status} — "
                        f"{age_text}"
                        + (
                            f" — Ref: {payment_reference}"
                            if payment_reference
                            else ""
                        )
                    )

            # ------------------------------------------------
            # CANCELLED INVOICE
            # ------------------------------------------------

            if is_invoice_cancelled(
                selected_invoice
            ):

                st.error(
                    "This invoice is cancelled. "
                    "Payments cannot be recorded against it."
                )

            # ------------------------------------------------
            # ZERO VALUE INVOICE
            # ------------------------------------------------

            if total <= 0:

                st.warning(
                    "This invoice has a zero or missing total. "
                    "Correct the invoice before recording "
                    "a Received payment."
                )

            # ------------------------------------------------
            # FULLY PAID
            # ------------------------------------------------

            if (
                total > 0
                and balance <= 0.01
                and invoice_status
                != "Cancelled"
            ):

                st.success(
                    "This invoice is currently fully paid."
                )

            # ------------------------------------------------
            # PAYMENT FORM
            # ------------------------------------------------

            form_disabled = (
                is_invoice_cancelled(
                    selected_invoice
                )
                or total <= 0
                or balance <= 0.01
            )

            with st.form(
                "record_payment_form",
                clear_on_submit=True,
            ):

                col1, col2 = st.columns(
                    2
                )

                with col1:

                    payment_date = st.date_input(
                        "Payment Date",
                        value=date.today(),
                        disabled=form_disabled,
                    )

                    payment_amount = st.number_input(
                        f"Amount ({currency})",
                        min_value=0.0,
                        step=0.01,
                        format="%.2f",
                        disabled=form_disabled,
                    )

                    payment_method = st.selectbox(
                        "Payment Method",
                        options=PAYMENT_METHODS,
                        disabled=form_disabled,
                    )

                with col2:

                    payment_status = st.selectbox(
                        "Payment Status",
                        options=PAYMENT_STATUSES,
                        index=0,
                        disabled=form_disabled,
                    )

                    reference = st.text_input(
                        "Payment Reference",
                        placeholder=(
                            "Bank reference, transaction ID, etc."
                        ),
                        disabled=form_disabled,
                    )

                    notes = st.text_area(
                        "Notes",
                        placeholder=(
                            "Optional payment notes..."
                        ),
                        disabled=form_disabled,
                    )

                submitted = st.form_submit_button(
                    "Record Payment",
                    type="primary",
                    use_container_width=True,
                    disabled=form_disabled,
                )

            # ------------------------------------------------
            # PROCESS PAYMENT
            # ------------------------------------------------

            if submitted:

                payment_amount = round_money(
                    payment_amount
                )

                reference = clean_text(
                    reference
                )

                notes = clean_text(
                    notes
                )

                errors = validate_payment_data(
                    payment_date,
                    payment_amount,
                    payment_status,
                    selected_invoice,
                    reference,
                    session,
                )

                if len(notes) > MAX_NOTES_LENGTH:

                    errors.append(
                        f"Notes cannot exceed "
                        f"{MAX_NOTES_LENGTH} characters."
                    )

                if errors:

                    for error in errors:

                        st.error(
                            error
                        )

                else:

                    try:

                        payment = Payment()

                        payment.invoice_id = (
                            selected_invoice_id
                        )

                        payment.payment_date = (
                            payment_date
                        )

                        payment.amount = (
                            payment_amount
                        )

                        # Always inherit currency
                        # from the invoice.
                        payment.currency = (
                            currency
                        )

                        payment.payment_method = (
                            payment_method
                        )

                        payment.reference = (
                            reference
                        )

                        payment.status = (
                            payment_status
                        )

                        payment.notes = (
                            notes
                        )

                        session.add(
                            payment
                        )

                        session.flush()

                        # ------------------------------------
                        # RECONCILE INVOICE
                        # ------------------------------------

                        refreshed_payments = (
                            session.query(Payment)
                            .filter(
                                Payment.invoice_id
                                == selected_invoice_id
                            )
                            .all()
                        )

                        reconcile_invoice_from_payments(
                            selected_invoice,
                            refreshed_payments,
                        )

                        session.commit()

                        st.success(
                            "Payment recorded successfully "
                            "and invoice totals reconciled."
                        )

                        st.rerun()

                    except IntegrityError:

                        session.rollback()

                        st.error(
                            "The payment could not be saved "
                            "because of a database integrity error. "
                            "Check the invoice and payment reference."
                        )

                    except Exception:

                        session.rollback()

                        st.error(
                            "The payment could not be recorded. "
                            "Please check the invoice and payment details."
                        )

        # ====================================================
        # PAYMENT REGISTER
        # ====================================================

        st.divider()

        st.subheader(
            "Payment Register"
        )

        # ====================================================
        # FILTERS
        # ====================================================

        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(
            4
        )

        with filter_col1:

            search = st.text_input(
                "Search",
                placeholder=(
                    "Invoice, client, reference..."
                ),
                key="payment_search",
            )

        with filter_col2:

            status_filter = st.selectbox(
                "Status",
                options=[
                    "All",
                    *PAYMENT_STATUSES,
                ],
                key="payment_status_filter",
            )

        with filter_col3:

            method_filter = st.selectbox(
                "Payment Method",
                options=[
                    "All",
                    *PAYMENT_METHODS,
                ],
                key="payment_method_filter",
            )

        with filter_col4:

            currencies = sorted(
                {
                    get_payment_currency(
                        payment
                    )
                    for payment in payments
                }
            )

            currency_filter = st.selectbox(
                "Currency",
                options=[
                    "All",
                    *currencies,
                ],
                key="payment_currency_filter",
            )

        # ====================================================
        # SECOND FILTER ROW
        # ====================================================

        filter_col5, filter_col6, filter_col7, filter_col8 = st.columns(
            4
        )

        with filter_col5:

            client_options = {
                "All": None
            }

            client_names = sorted(
                {
                    get_client_name(payment)
                    for payment in payments
                }
            )

            for client_name in client_names:

                client_options[
                    client_name
                ] = client_name

            client_filter_label = st.selectbox(
                "Client",
                options=list(
                    client_options.keys()
                ),
                key="payment_client_filter",
            )

            client_filter = (
                client_options[
                    client_filter_label
                ]
            )

        with filter_col6:

            invoice_filter_options = {
                "All": None
            }

            for invoice in invoices:

                number = get_invoice_number(
                    invoice
                )

                if number in invoice_filter_options:

                    number = (
                        f"{number} "
                        f"(ID {invoice.id})"
                    )

                invoice_filter_options[
                    number
                ] = invoice.id

            invoice_filter_label = st.selectbox(
                "Invoice",
                options=list(
                    invoice_filter_options.keys()
                ),
                key="payment_invoice_filter",
            )

            invoice_filter_id = (
                invoice_filter_options[
                    invoice_filter_label
                ]
            )

        with filter_col7:

            date_filter = st.selectbox(
                "Payment Date",
                options=PAYMENT_DATE_FILTERS,
                key="payment_date_filter",
            )

        with filter_col8:

            reconciliation_filter = st.selectbox(
                "Reconciliation",
                options=RECONCILIATION_FILTERS,
                key="payment_reconciliation_filter",
            )

        # ====================================================
        # CUSTOM DATE RANGE
        # ====================================================

        custom_start = None
        custom_end = None

        if date_filter == "Custom Range":

            date_col1, date_col2 = st.columns(
                2
            )

            with date_col1:

                custom_start = st.date_input(
                    "Start Date",
                    value=(
                        date.today()
                        - timedelta(days=30)
                    ),
                    key="payment_custom_start",
                )

            with date_col2:

                custom_end = st.date_input(
                    "End Date",
                    value=date.today(),
                    key="payment_custom_end",
                )

            if custom_start > custom_end:

                st.error(
                    "Custom start date cannot be after the end date."
                )

        # ====================================================
        # ACTION FILTER
        # ====================================================

        action_filter = st.selectbox(
            "Payment Type",
            options=PAYMENT_ACTION_FILTERS,
            key="payment_action_filter",
        )

        # ====================================================
        # SORT
        # ====================================================

        sort_option = st.selectbox(
            "Sort Payments",
            options=[
                "Newest Payment Date",
                "Oldest Payment Date",
                "Highest Amount",
                "Lowest Amount",
                "Invoice Number",
                "Client A-Z",
                "Reference A-Z",
            ],
            key="payment_sort",
        )

        # ====================================================
        # APPLY FILTERS
        # ====================================================

        filtered_payments = []

        search_lower = clean_text(
            search
        ).lower()

        for payment in payments:

            payment_status = (
                get_payment_status(
                    payment
                )
            )

            payment_method = (
                get_payment_method(
                    payment
                )
            )

            payment_currency = (
                get_payment_currency(
                    payment
                )
            )

            payment_client = (
                get_client_name(
                    payment
                )
            )

            payment_invoice = getattr(
                payment,
                "invoice",
                None,
            )

            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

            if (
                status_filter != "All"
                and payment_status
                != status_filter
            ):

                continue

            # ------------------------------------------------
            # METHOD
            # ------------------------------------------------

            if (
                method_filter != "All"
                and payment_method
                != method_filter
            ):

                continue

            # ------------------------------------------------
            # CURRENCY
            # ------------------------------------------------

            if (
                currency_filter != "All"
                and payment_currency
                != currency_filter
            ):

                continue

            # ------------------------------------------------
            # CLIENT
            # ------------------------------------------------

            if (
                client_filter is not None
                and payment_client
                != client_filter
            ):

                continue

            # ------------------------------------------------
            # INVOICE
            # ------------------------------------------------

            if (
                invoice_filter_id
                is not None
                and payment.invoice_id
                != invoice_filter_id
            ):

                continue

            # ------------------------------------------------
            # DATE
            # ------------------------------------------------

            if not payment_matches_date_filter(
                payment,
                date_filter,
                custom_start,
                custom_end,
            ):

                continue

            # ------------------------------------------------
            # RECONCILIATION
            # ------------------------------------------------

            if (
                reconciliation_filter
                != "All"
            ):

                if not payment_invoice:

                    payment_reconciliation = (
                        "Needs Reconciliation"
                    )

                else:

                    payment_reconciliation = (
                        get_reconciliation_label(
                            payment_invoice,
                            payments,
                        )
                    )

                if (
                    payment_reconciliation
                    != reconciliation_filter
                ):

                    continue

            # ------------------------------------------------
            # ACTION TYPE
            # ------------------------------------------------

            if (
                action_filter
                == "Received Payments"
                and payment_status
                != "Received"
            ):

                continue

            if (
                action_filter
                == "Pending Payments"
                and payment_status
                != "Pending"
            ):

                continue

            if (
                action_filter
                == "Failed Payments"
                and payment_status
                != "Failed"
            ):

                continue

            if (
                action_filter
                == "Reversed Payments"
                and payment_status
                != "Reversed"
            ):

                continue

            # ------------------------------------------------
            # SEARCH
            # ------------------------------------------------

            if search_lower:

                search_text = (
                    get_payment_search_text(
                        payment
                    )
                )

                if (
                    search_lower
                    not in search_text
                ):

                    continue

            filtered_payments.append(
                payment
            )

        # ====================================================
        # SORT FILTERED PAYMENTS
        # ====================================================

        if sort_option == "Newest Payment Date":

            filtered_payments.sort(
                key=lambda payment: (
                    getattr(
                        payment,
                        "payment_date",
                        None,
                    )
                    or date.min,
                    payment.id or 0,
                ),
                reverse=True,
            )

        elif sort_option == "Oldest Payment Date":

            filtered_payments.sort(
                key=lambda payment: (
                    getattr(
                        payment,
                        "payment_date",
                        None,
                    )
                    or date.min,
                    payment.id or 0,
                )
            )

        elif sort_option == "Highest Amount":

            filtered_payments.sort(
                key=lambda payment:
                    get_payment_amount(
                        payment
                    ),
                reverse=True,
            )

        elif sort_option == "Lowest Amount":

            filtered_payments.sort(
                key=lambda payment:
                    get_payment_amount(
                        payment
                    )
            )

        elif sort_option == "Invoice Number":

            filtered_payments.sort(
                key=lambda payment:
                    get_invoice_number_from_payment(
                        payment
                    ).lower()
            )

        elif sort_option == "Client A-Z":

            filtered_payments.sort(
                key=lambda payment:
                    get_client_name(
                        payment
                    ).lower()
            )

        elif sort_option == "Reference A-Z":

            filtered_payments.sort(
                key=lambda payment:
                    get_payment_reference(
                        payment
                    ).lower()
            )

        # ====================================================
        # FILTERED SUMMARY
        # ====================================================

        filtered_received = [
            payment
            for payment in filtered_payments
            if payment_is_received(
                payment
            )
        ]

        filtered_pending = [
            payment
            for payment in filtered_payments
            if get_payment_status(
                payment
            ) == "Pending"
        ]

        filtered_failed = [
            payment
            for payment in filtered_payments
            if get_payment_status(
                payment
            ) == "Failed"
        ]

        filtered_reversed = [
            payment
            for payment in filtered_payments
            if get_payment_status(
                payment
            ) == "Reversed"
        ]

        filtered_totals = (
            get_total_by_status(
                filtered_payments,
                "Received",
            )
        )

        filtered_pending_totals = (
            get_total_by_status(
                filtered_payments,
                "Pending",
            )
        )

        if filtered_payments:

            st.caption(
                f"Showing {len(filtered_payments)} "
                "payment record(s)."
            )

            summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(
                4
            )

            summary_col1.metric(
                "Received",
                len(filtered_received),
            )

            summary_col2.metric(
                "Pending",
                len(filtered_pending),
            )

            summary_col3.metric(
                "Failed",
                len(filtered_failed),
            )

            summary_col4.metric(
                "Reversed",
                len(filtered_reversed),
            )

            if filtered_totals:

                st.caption(
                    "Received totals:"
                )

                summary_columns = st.columns(
                    min(
                        len(
                            filtered_totals
                        ),
                        4,
                    )
                )

                for index, (
                    currency,
                    amount,
                ) in enumerate(
                    sorted(
                        filtered_totals.items()
                    )
                ):

                    summary_columns[
                        index
                        % len(
                            summary_columns
                        )
                    ].metric(
                        f"Received {currency}",
                        f"{amount:,.2f}",
                    )

            if filtered_pending_totals:

                st.caption(
                    "Pending totals:"
                )

                pending_columns = st.columns(
                    min(
                        len(
                            filtered_pending_totals
                        ),
                        4,
                    )
                )

                for index, (
                    currency,
                    amount,
                ) in enumerate(
                    sorted(
                        filtered_pending_totals.items()
                    )
                ):

                    pending_columns[
                        index
                        % len(
                            pending_columns
                        )
                    ].metric(
                        f"Pending {currency}",
                        f"{amount:,.2f}",
                    )

        else:

            st.info(
                "No payments match the selected filters."
            )

        # ====================================================
        # CSV EXPORT
        # ====================================================

        if filtered_payments:

            csv_bytes = get_csv_bytes(
                filtered_payments
            )

            st.download_button(
                "Export Payments to CSV",
                data=csv_bytes,
                file_name=(
                    "averra_payments.csv"
                ),
                mime="text/csv",
                key="export_payments_csv",
            )

        # ====================================================
        # PAYMENT CARDS
        # ====================================================

        for payment in filtered_payments:

            status = get_payment_status(
                payment
            )

            status_icon = (
                get_payment_status_icon(
                    status
                )
            )

            amount = get_payment_amount(
                payment
            )

            currency = get_payment_currency(
                payment
            )

            invoice = getattr(
                payment,
                "invoice",
                None,
            )

            current_balance = (
                get_invoice_balance(
                    invoice
                )
                if invoice
                else 0.0
            )

            payment_date = getattr(
                payment,
                "payment_date",
                None,
            )

            payment_age = (
                get_payment_age_days(
                    payment
                )
            )

            payment_warnings = (
                get_payment_data_warnings(
                    payment,
                    invoice,
                )
            )

            with st.container(
                border=True
            ):

                col1, col2, col3, col4 = st.columns(
                    [
                        2.2,
                        1.3,
                        1.5,
                        1.5,
                    ]
                )

                with col1:

                    st.markdown(
                        f"### {status_icon} "
                        f"{get_invoice_number_from_payment(payment)}"
                    )

                    st.write(
                        get_client_name(
                            payment
                        )
                    )

                    st.caption(
                        "Payment date: "
                        f"{format_date(payment_date)}"
                    )

                    if payment_age is not None:

                        st.caption(
                            f"Payment age: "
                            f"{payment_age} day(s)"
                        )

                with col2:

                    st.metric(
                        "Amount",
                        format_money(
                            currency,
                            amount,
                        ),
                    )

                with col3:

                    st.write(
                        "**Method:** "
                        f"{get_payment_method(payment)}"
                    )

                    st.write(
                        "**Status:** "
                        f"{status}"
                    )

                    reference = (
                        get_payment_reference(
                            payment
                        )
                    )

                    if reference:

                        st.caption(
                            f"Ref: {reference}"
                        )

                with col4:

                    st.write(
                        "**Invoice Balance:**"
                    )

                    st.write(
                        format_money(
                            currency,
                            current_balance,
                        )
                    )

                    if invoice:

                        st.caption(
                            f"Payment state: "
                            f"{get_payment_state(invoice)}"
                        )

                # --------------------------------------------
                # PAYMENT EFFECT
                # --------------------------------------------

                if status == "Received":

                    st.success(
                        "Received payment — included "
                        "in the invoice amount paid."
                    )

                elif status == "Pending":

                    st.warning(
                        "Pending payment — not included "
                        "in the invoice amount paid."
                    )

                elif status == "Failed":

                    st.error(
                        "Failed payment — not included "
                        "in the invoice amount paid."
                    )

                elif status == "Reversed":

                    st.warning(
                        "Reversed payment — not included "
                        "in the invoice amount paid."
                    )

                # --------------------------------------------
                # DATA WARNINGS
                # --------------------------------------------

                if payment_warnings:

                    for warning in payment_warnings:

                        st.warning(
                            warning
                        )

                # --------------------------------------------
                # RECONCILIATION
                # --------------------------------------------

                if invoice:

                    reconciliation = (
                        get_invoice_reconciliation_status(
                            invoice,
                            payments,
                        )
                    )

                    if reconciliation["matched"]:

                        st.caption(
                            "✓ Invoice payment records reconciled"
                        )

                    else:

                        st.error(
                            "Invoice reconciliation required."
                        )

                # --------------------------------------------
                # NOTES
                # --------------------------------------------

                payment_notes = clean_text(
                    getattr(
                        payment,
                        "notes",
                        None,
                    )
                )

                if payment_notes:

                    with st.expander(
                        "Payment Notes"
                    ):

                        st.write(
                            payment_notes
                        )

        # ====================================================
        # UNPAID / PARTIALLY PAID INVOICE MONITOR
        # ====================================================

        st.divider()

        st.subheader(
            "Invoice Payment Monitor"
        )

        unpaid_invoices = [
            invoice
            for invoice in invoices
            if (
                not is_invoice_cancelled(
                    invoice
                )
                and get_invoice_total(invoice)
                > 0
                and get_invoice_balance(invoice)
                > 0.01
            )
        ]

        fully_paid_invoices = [
            invoice
            for invoice in invoices
            if is_invoice_fully_paid(
                invoice
            )
        ]

        monitor_col1, monitor_col2, monitor_col3 = st.columns(
            3
        )

        monitor_col1.metric(
            "Invoices With Balance",
            len(unpaid_invoices),
        )

        monitor_col2.metric(
            "Fully Paid Invoices",
            len(fully_paid_invoices),
        )

        monitor_col3.metric(
            "Reconciliation Issues",
            len(reconciliation_issues),
        )

        if unpaid_invoices:

            with st.expander(
                "View invoices with outstanding balances"
            ):

                for invoice in unpaid_invoices[:100]:

                    invoice_currency = (
                        get_invoice_currency(
                            invoice
                        )
                    )

                    invoice_balance = (
                        get_invoice_balance(
                            invoice
                        )
                    )

                    invoice_percentage = (
                        get_payment_percentage(
                            invoice
                        )
                    )

                    st.write(
                        f"**{get_invoice_number(invoice)}** — "
                        f"{get_client_name_from_invoice(invoice)} — "
                        f"Balance: "
                        f"{format_money(invoice_currency, invoice_balance)} — "
                        f"{invoice_percentage:.1f}% paid"
                    )

        # ====================================================
        # FINANCIAL HISTORY PROTECTION
        # ====================================================

        if payments:

            st.divider()

            st.info(
                "Payment records are protected from direct "
                "editing and deletion on this screen. "
                "Received payments affect invoice balances; "
                "Pending, Failed and Reversed payments do not."
            )

            st.caption(
                "For a future production version, corrections "
                "can be handled through a controlled reversal/"
                "adjustment workflow with an audit trail."
            )

    except Exception as exc:

        session.rollback()

        st.error(
            "The Payments screen could not be loaded. "
            "Please check the invoice and payment data."
        )

        with st.expander(
            "Technical error details"
        ):

            st.code(
                str(exc)
            )

    finally:

        session.close()