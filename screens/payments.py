import csv
import io
from datetime import date

import streamlit as st

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


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(value):
    """Return a safely cleaned text value."""

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


# ============================================================
# INVOICE HELPERS
# ============================================================

def get_invoice_number(payment):
    """Return the invoice number for a payment."""

    if payment and payment.invoice:

        return (
            clean_text(
                payment.invoice.invoice_number
            )
            or f"Invoice #{payment.invoice.id}"
        )

    return "Unknown Invoice"


def get_client_name(payment):
    """Return the client name for a payment."""

    if (
        payment
        and payment.invoice
        and payment.invoice.client
    ):

        return (
            clean_text(
                payment.invoice.client.company_name
            )
            or "Unknown Client"
        )

    return "Unknown Client"


def get_invoice_currency(invoice):
    """Return the invoice currency."""

    if not invoice:
        return "GBP"

    return (
        clean_text(
            invoice.currency
        )
        or "GBP"
    )


def get_invoice_total(invoice):
    """Return the invoice total."""

    if not invoice:
        return 0.0

    return max(
        round_money(
            invoice.total_amount
        ),
        0.0,
    )


def get_invoice_paid(invoice):
    """Return the amount currently recorded as paid."""

    if not invoice:
        return 0.0

    return max(
        round_money(
            invoice.amount_paid
        ),
        0.0,
    )


def get_invoice_balance(invoice):
    """
    Return the current invoice balance.

    Uses the Invoice model balance_due property/field
    where available.
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

    except (TypeError, ValueError, AttributeError):

        return get_calculated_invoice_balance(
            invoice
        )


def get_calculated_invoice_balance(invoice):
    """
    Calculate invoice balance independently:

        invoice total - amount paid
    """

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
    """
    Return effective payment state.

    Values:
        Unpaid
        Partially Paid
        Paid
    """

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

    if paid >= total:
        return "Paid"

    return "Partially Paid"


def get_invoice_data_warning(invoice):
    """
    Detect obvious invoice/payment inconsistencies.
    """

    if not invoice:
        return None

    total = get_invoice_total(
        invoice
    )

    paid = get_invoice_paid(
        invoice
    )

    stored_balance = get_invoice_balance(
        invoice
    )

    calculated_balance = (
        get_calculated_invoice_balance(
            invoice
        )
    )

    tolerance = 0.01

    if paid > total + tolerance:

        return (
            "The recorded amount paid is greater "
            "than the invoice total."
        )

    if (
        abs(
            stored_balance
            - calculated_balance
        )
        > tolerance
    ):

        return (
            "The stored invoice balance does not "
            "match the invoice total minus amount paid."
        )

    return None


def get_invoice_status(invoice):
    """Return the stored invoice status."""

    if not invoice:
        return "Unknown"

    return (
        clean_text(
            invoice.status
        )
        or "Unknown"
    )


def is_invoice_cancelled(invoice):
    """Return True when an invoice is cancelled."""

    return (
        get_invoice_status(invoice)
        == "Cancelled"
    )


# ============================================================
# PAYMENT HELPERS
# ============================================================

def get_payment_amount(payment):
    """Return a safely converted payment amount."""

    if not payment:
        return 0.0

    return max(
        round_money(
            payment.amount
        ),
        0.0,
    )


def get_payment_count_by_status(
    payments,
    status,
):
    """Count payments by status."""

    return sum(
        1
        for payment in payments
        if clean_text(
            payment.status
        ) == status
    )


def get_total_by_status(
    payments,
    status,
):
    """
    Calculate payment totals by currency.

    Different currencies are never combined.
    """

    totals = {}

    for payment in payments:

        if (
            clean_text(
                payment.status
            )
            != status
        ):
            continue

        currency = (
            clean_text(
                payment.currency
            )
            or "Unknown"
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
    """
    Calculate payment totals by currency.

    Different currencies are never combined.
    """

    totals = {}

    for payment in payments:

        currency = (
            clean_text(
                payment.currency
            )
            or "Unknown"
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


def get_payment_status_icon(status):
    """Return a visual indicator for payment status."""

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


def payment_is_received(payment):
    """Return True if the payment counts as received."""

    return (
        clean_text(
            payment.status
        )
        == "Received"
    )


def payment_is_non_received(payment):
    """Return True if payment is not currently received."""

    return (
        clean_text(
            payment.status
        )
        in NON_RECEIVED_STATUSES
    )


# ============================================================
# DUPLICATE / INTEGRITY HELPERS
# ============================================================

def has_duplicate_reference(
    session,
    invoice_id,
    reference,
):
    """
    Check whether the same payment reference
    already exists for the invoice.

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

        existing_reference = (
            clean_text(
                payment.reference
            )
        )

        if (
            existing_reference.lower()
            == reference_lower
        ):

            return True

    return False


def get_received_payments_for_invoice(
    payments,
    invoice_id,
):
    """Return received payments for an invoice."""

    return [
        payment
        for payment in payments
        if (
            payment.invoice_id
            == invoice_id
            and payment_is_received(
                payment
            )
        )
    ]


def get_non_received_payments_for_invoice(
    payments,
    invoice_id,
):
    """Return pending/failed/reversed payments for an invoice."""

    return [
        payment
        for payment in payments
        if (
            payment.invoice_id
            == invoice_id
            and payment_is_non_received(
                payment
            )
        )
    ]


def get_invoice_received_total_from_payments(
    payments,
    invoice_id,
):
    """
    Calculate received payments directly from
    payment records.
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


# ============================================================
# CSV EXPORT
# ============================================================

def get_csv_bytes(payments):
    """Create a CSV export of the payment register."""

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow(
        [
            "Payment ID",
            "Payment Date",
            "Invoice Number",
            "Client",
            "Amount",
            "Currency",
            "Payment Method",
            "Reference",
            "Status",
            "Notes",
        ]
    )

    for payment in payments:

        payment_date = getattr(
            payment,
            "payment_date",
            None,
        )

        if payment_date:

            payment_date_text = (
                payment_date.strftime(
                    "%Y-%m-%d"
                )
            )

        else:

            payment_date_text = ""

        writer.writerow(
            [
                payment.id,
                payment_date_text,
                get_invoice_number(
                    payment
                ),
                get_client_name(
                    payment
                ),
                f"{get_payment_amount(payment):.2f}",
                (
                    clean_text(
                        payment.currency
                    )
                    or "GBP"
                ),
                clean_text(
                    payment.payment_method
                ),
                clean_text(
                    payment.reference
                ),
                clean_text(
                    payment.status
                ),
                clean_text(
                    payment.notes
                ),
            ]
        )

    return output.getvalue().encode(
        "utf-8-sig"
    )


# ============================================================
# MAIN SCREEN
# ============================================================

def show_payments():

    st.title(
        "Payments"
    )

    st.caption(
        "Record, monitor and review client payments against invoices."
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
        # KPI CALCULATIONS
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
            if clean_text(
                payment.status
            ) == "Pending"
        ]

        failed_payments = [
            payment
            for payment in payments
            if clean_text(
                payment.status
            ) == "Failed"
        ]

        reversed_payments = [
            payment
            for payment in payments
            if clean_text(
                payment.status
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

        # ====================================================
        # KPI SECTION
        # ====================================================

        col1, col2, col3, col4 = st.columns(
            4
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
            "Failed / Reversed",
            (
                len(failed_payments)
                + len(reversed_payments)
            ),
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
                received_totals.items()
            ):

                columns[
                    index
                    % len(columns)
                ].metric(
                    currency,
                    f"{amount:,.2f}",
                )

        else:

            st.info(
                "No received payments recorded yet."
            )

        # ====================================================
        # PENDING TOTALS
        # ====================================================

        if pending_totals:

            st.caption(
                "Pending payment amounts are shown separately "
                "and are not included in invoice amount paid."
            )

            pending_columns = st.columns(
                min(
                    len(pending_totals),
                    4,
                )
            )

            for index, (
                currency,
                amount,
            ) in enumerate(
                pending_totals.items()
            ):

                pending_columns[
                    index
                    % len(pending_columns)
                ].metric(
                    f"Pending {currency}",
                    f"{amount:,.2f}",
                )

        # ====================================================
        # RECORD NEW PAYMENT
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

            def invoice_label(invoice_id):

                invoice = (
                    invoice_options[
                        invoice_id
                    ]
                )

                number = (
                    clean_text(
                        invoice.invoice_number
                    )
                    or f"Invoice #{invoice.id}"
                )

                if (
                    invoice.client
                    and getattr(
                        invoice.client,
                        "company_name",
                        None,
                    )
                ):

                    client = clean_text(
                        invoice.client.company_name
                    )

                else:

                    client = "Unknown Client"

                balance = (
                    get_invoice_balance(
                        invoice
                    )
                )

                currency = (
                    get_invoice_currency(
                        invoice
                    )
                )

                state = (
                    get_payment_state(
                        invoice
                    )
                )

                return (
                    f"{number} | "
                    f"{client} | "
                    f"Balance: "
                    f"{currency} "
                    f"{balance:,.2f} | "
                    f"{state}"
                )

            selected_invoice_id = st.selectbox(
                "Invoice",
                options=invoice_ids,
                format_func=invoice_label,
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

            calculated_balance = (
                get_calculated_invoice_balance(
                    selected_invoice
                )
            )

            percentage = (
                get_payment_percentage(
                    selected_invoice
                )
            )

            currency = (
                get_invoice_currency(
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
                f"{currency} {total:,.2f}",
            )

            summary_col2.metric(
                "Amount Paid",
                f"{currency} {paid:,.2f}",
            )

            summary_col3.metric(
                "Balance Due",
                f"{currency} {balance:,.2f}",
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
                f"{percentage:.1f}% of the invoice has been recorded as paid."
            )

            # ------------------------------------------------
            # PAYMENT HISTORY FOR SELECTED INVOICE
            # ------------------------------------------------

            selected_invoice_payments = [
                payment
                for payment in payments
                if payment.invoice_id
                == selected_invoice_id
            ]

            if selected_invoice_payments:

                received_total = (
                    get_invoice_received_total_from_payments(
                        payments,
                        selected_invoice_id,
                    )
                )

                st.caption(
                    f"Recorded received payments for this invoice: "
                    f"{currency} {received_total:,.2f}"
                )

            # ------------------------------------------------
            # DATA CONSISTENCY WARNING
            # ------------------------------------------------

            warning = (
                get_invoice_data_warning(
                    selected_invoice
                )
            )

            if warning:

                st.warning(
                    warning
                )

            # ------------------------------------------------
            # CANCELLED INVOICE
            # ------------------------------------------------

            if is_invoice_cancelled(
                selected_invoice
            ):

                st.error(
                    "This invoice is cancelled. "
                    "Payments cannot be recorded against a cancelled invoice."
                )

            # ------------------------------------------------
            # ZERO VALUE INVOICE
            # ------------------------------------------------

            if total <= 0:

                st.warning(
                    "This invoice has a zero or missing total. "
                    "A received payment cannot be recorded until "
                    "the invoice total is corrected."
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
                    )

                    payment_amount = st.number_input(
                        f"Amount ({currency})",
                        min_value=0.0,
                        step=0.01,
                        format="%.2f",
                    )

                    payment_method = st.selectbox(
                        "Payment Method",
                        options=PAYMENT_METHODS,
                    )

                with col2:

                    payment_status = st.selectbox(
                        "Payment Status",
                        options=PAYMENT_STATUSES,
                        index=0,
                    )

                    reference = st.text_input(
                        "Payment Reference",
                        placeholder=(
                            "Bank reference, transaction ID, etc."
                        ),
                    )

                    notes = st.text_area(
                        "Notes",
                        placeholder=(
                            "Optional payment notes..."
                        ),
                    )

                submitted = st.form_submit_button(
                    "Record Payment",
                    type="primary",
                    use_container_width=True,
                )

            # ------------------------------------------------
            # PROCESS PAYMENT
            # ------------------------------------------------

            if submitted:

                errors = []

                payment_amount = round_money(
                    payment_amount
                )

                reference = clean_text(
                    reference
                )

                notes = clean_text(
                    notes
                )

                # --------------------------------------------
                # DATE VALIDATION
                # --------------------------------------------

                if payment_date > date.today():

                    errors.append(
                        "Payment date cannot be in the future."
                    )

                # --------------------------------------------
                # AMOUNT VALIDATION
                # --------------------------------------------

                if payment_amount <= 0:

                    errors.append(
                        "Payment amount must be greater than zero."
                    )

                # --------------------------------------------
                # CANCELLED INVOICE
                # --------------------------------------------

                if is_invoice_cancelled(
                    selected_invoice
                ):

                    errors.append(
                        "Payments cannot be recorded against a cancelled invoice."
                    )

                # --------------------------------------------
                # RECEIVED PAYMENT VALIDATION
                # --------------------------------------------

                if (
                    payment_status
                    == "Received"
                ):

                    if total <= 0:

                        errors.append(
                            "A received payment cannot be recorded for an invoice with a zero total."
                        )

                    elif balance <= 0.01:

                        errors.append(
                            "This invoice is already fully paid."
                        )

                    elif (
                        payment_amount
                        > balance
                        + 0.01
                    ):

                        errors.append(
                            f"Payment cannot exceed the current "
                            f"balance of {currency} {balance:,.2f}."
                        )

                # --------------------------------------------
                # NON-RECEIVED PAYMENT VALIDATION
                # --------------------------------------------

                if (
                    payment_status
                    in NON_RECEIVED_STATUSES
                    and payment_amount <= 0
                ):

                    errors.append(
                        "A payment amount greater than zero is required."
                    )

                # --------------------------------------------
                # DUPLICATE REFERENCE
                # --------------------------------------------

                if reference:

                    if has_duplicate_reference(
                        session,
                        selected_invoice_id,
                        reference,
                    ):

                        errors.append(
                            "A payment with this reference already exists for this invoice."
                        )

                # --------------------------------------------
                # SAVE
                # --------------------------------------------

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

                        # Payment currency always follows
                        # invoice currency.
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

                        # ------------------------------------
                        # RECEIVED PAYMENT
                        # ------------------------------------

                        if (
                            payment_status
                            == "Received"
                        ):

                            new_amount_paid = round_money(
                                paid
                                + payment_amount
                            )

                            if (
                                new_amount_paid
                                >= total
                                - 0.01
                            ):

                                selected_invoice.amount_paid = (
                                    total
                                )

                                selected_invoice.status = (
                                    "Paid"
                                )

                            else:

                                selected_invoice.amount_paid = (
                                    new_amount_paid
                                )

                                selected_invoice.status = (
                                    "Partially Paid"
                                )

                        # ------------------------------------
                        # OTHER PAYMENT STATUSES
                        # ------------------------------------

                        else:

                            # Pending, Failed and Reversed
                            # payments do not increase
                            # invoice.amount_paid.
                            pass

                        session.commit()

                        st.success(
                            "Payment recorded successfully."
                        )

                        st.rerun()

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
                    clean_text(
                        payment.currency
                    )
                    for payment in payments
                    if clean_text(
                        payment.currency
                    )
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

        invoice_filter_options = {
            "All": None
        }

        for invoice in invoices:

            number = (
                clean_text(
                    invoice.invoice_number
                )
                or f"Invoice #{invoice.id}"
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

        # ====================================================
        # APPLY FILTERS
        # ====================================================

        filtered_payments = []

        search_lower = clean_text(
            search
        ).lower()

        for payment in payments:

            payment_status = clean_text(
                payment.status
            )

            payment_method = clean_text(
                payment.payment_method
            )

            payment_currency = clean_text(
                payment.currency
            )

            if (
                status_filter != "All"
                and payment_status
                != status_filter
            ):

                continue

            if (
                method_filter != "All"
                and payment_method
                != method_filter
            ):

                continue

            if (
                currency_filter != "All"
                and payment_currency
                != currency_filter
            ):

                continue

            if (
                invoice_filter_id
                is not None
                and payment.invoice_id
                != invoice_filter_id
            ):

                continue

            if search_lower:

                search_text = " ".join(
                    [
                        get_invoice_number(
                            payment
                        ),
                        get_client_name(
                            payment
                        ),
                        clean_text(
                            payment.reference
                        ),
                        clean_text(
                            payment.notes
                        ),
                        payment_status,
                        payment_method,
                        payment_currency,
                    ]
                ).lower()

                if (
                    search_lower
                    not in search_text
                ):

                    continue

            filtered_payments.append(
                payment
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
            if clean_text(
                payment.status
            ) == "Pending"
        ]

        filtered_failed = [
            payment
            for payment in filtered_payments
            if clean_text(
                payment.status
            ) == "Failed"
        ]

        filtered_reversed = [
            payment
            for payment in filtered_payments
            if clean_text(
                payment.status
            ) == "Reversed"
        ]

        filtered_totals = (
            get_total_by_status(
                filtered_payments,
                "Received",
            )
        )

        if filtered_payments:

            st.caption(
                f"Showing {len(filtered_payments)} payment "
                f"record(s)."
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
                    filtered_totals.items()
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
            )

        # ====================================================
        # PAYMENT CARDS
        # ====================================================

        for payment in filtered_payments:

            status = clean_text(
                payment.status
            )

            status_icon = (
                get_payment_status_icon(
                    status
                )
            )

            amount = get_payment_amount(
                payment
            )

            currency = (
                clean_text(
                    payment.currency
                )
                or "GBP"
            )

            invoice = payment.invoice

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

            if payment_date:

                payment_date_text = (
                    payment_date.strftime(
                        "%d/%m/%Y"
                    )
                )

            else:

                payment_date_text = (
                    "No date"
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
                        f"{get_invoice_number(payment)}"
                    )

                    st.write(
                        get_client_name(
                            payment
                        )
                    )

                    st.caption(
                        f"Payment date: "
                        f"{payment_date_text}"
                    )

                with col2:

                    st.metric(
                        "Amount",
                        f"{currency} {amount:,.2f}",
                    )

                with col3:

                    st.write(
                        f"**Method:** "
                        f"{clean_text(payment.payment_method) or 'Not specified'}"
                    )

                    st.write(
                        f"**Status:** "
                        f"{status or 'Unknown'}"
                    )

                with col4:

                    st.write(
                        "**Invoice Balance:**"
                    )

                    st.write(
                        f"{currency} "
                        f"{current_balance:,.2f}"
                    )

                    reference = clean_text(
                        payment.reference
                    )

                    if reference:

                        st.caption(
                            f"Ref: {reference}"
                        )

                # --------------------------------------------
                # PAYMENT EFFECT
                # --------------------------------------------

                if status == "Received":

                    st.success(
                        "This payment has been included "
                        "in the invoice amount paid."
                    )

                elif status == "Pending":

                    st.warning(
                        "Pending payment — it has not "
                        "been added to the invoice amount paid."
                    )

                elif status == "Failed":

                    st.error(
                        "Failed payment — it has not "
                        "been added to the invoice amount paid."
                    )

                elif status == "Reversed":

                    st.warning(
                        "Reversed payment — it does not "
                        "increase the invoice amount paid."
                    )

                # --------------------------------------------
                # NOTES
                # --------------------------------------------

                payment_notes = clean_text(
                    payment.notes
                )

                if payment_notes:

                    st.caption(
                        f"Notes: {payment_notes}"
                    )

        # ====================================================
        # FINANCIAL HISTORY PROTECTION
        # ====================================================

        if payments:

            st.divider()

            st.caption(
                "Payment records are intentionally not editable "
                "or deletable from this screen. This protects "
                "the financial history of the CRM. Corrections "
                "should be recorded through a controlled "
                "adjustment or reversal process."
            )

    except Exception:

        session.rollback()

        st.error(
            "The Payments screen could not be loaded. "
            "Please check the invoice and payment data."
        )

    finally:

        session.close()