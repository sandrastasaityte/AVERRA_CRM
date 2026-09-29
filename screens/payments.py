
import streamlit as st
from datetime import date

from database import get_session
from models import Payment, Invoice


# ============================================================
# CONSTANTS
# ============================================================

PAYMENT_METHODS = [
    "Bank Transfer",
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


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    """Return a safely cleaned text value."""
    if value is None:
        return ""

    return str(value).strip()


def get_invoice_number(payment):
    """Return the invoice number for a payment."""
    if payment.invoice:
        return clean_text(payment.invoice.invoice_number) or "Unknown Invoice"

    return "Unknown Invoice"


def get_client_name(payment):
    """Return the client name for a payment."""
    if payment.invoice and payment.invoice.client:
        return (
            clean_text(payment.invoice.client.company_name)
            or "Unknown Client"
        )

    return "Unknown Client"


def get_invoice_balance(invoice):
    """Return the current outstanding invoice balance."""
    if not invoice:
        return 0.0

    try:
        return max(float(invoice.balance_due or 0), 0.0)
    except (TypeError, ValueError):
        return 0.0


def get_invoice_total(invoice):
    """Return the invoice total."""
    if not invoice:
        return 0.0

    try:
        return max(float(invoice.total_amount or 0), 0.0)
    except (TypeError, ValueError):
        return 0.0


def get_invoice_paid(invoice):
    """Return the invoice amount already marked as paid."""
    if not invoice:
        return 0.0

    try:
        return max(float(invoice.amount_paid or 0), 0.0)
    except (TypeError, ValueError):
        return 0.0


def format_money(amount, currency):
    """Format a monetary amount."""
    try:
        amount = float(amount or 0)
    except (TypeError, ValueError):
        amount = 0.0

    return f"{currency} {amount:,.2f}"


def get_payment_count_by_status(payments, status):
    """Count payments by status."""
    return sum(
        1
        for payment in payments
        if payment.status == status
    )


def get_total_by_status(payments, status):
    """Calculate payment value by status.

    Payments are only aggregated here by their recorded status.
    Different currencies are intentionally NOT mixed.
    """
    totals = {}

    for payment in payments:

        if payment.status != status:
            continue

        currency = clean_text(payment.currency) or "Unknown"

        try:
            amount = float(payment.amount or 0)
        except (TypeError, ValueError):
            amount = 0.0

        totals[currency] = totals.get(currency, 0.0) + amount

    return totals


def get_csv_bytes(payments):
    """Create a CSV export of the payment register."""
    import csv
    import io

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(
        [
            "Payment ID",
            "Payment Date",
            "Invoice Number",
            "Client",
            "Amount",
            "Currency",
            "Payment Method",
            "Status",
            "Reference",
            "Notes",
        ]
    )

    for payment in payments:

        writer.writerow(
            [
                payment.id,
                payment.payment_date.isoformat()
                if payment.payment_date
                else "",
                get_invoice_number(payment),
                get_client_name(payment),
                payment.amount or 0,
                payment.currency or "",
                payment.payment_method or "",
                payment.status or "",
                payment.reference or "",
                payment.notes or "",
            ]
        )

    return output.getvalue().encode("utf-8")


# ============================================================
# MAIN SCREEN
# ============================================================

def show_payments():

    st.title("Payments")
    st.caption(
        "Record and track client invoice payments."
    )

    session = get_session()

    try:

        # ========================================================
        # LOAD INVOICES
        # ========================================================

        invoices = session.query(Invoice).order_by(
            Invoice.invoice_date.desc(),
            Invoice.id.desc()
        ).all()

        if not invoices:

            st.warning(
                "Please create an invoice before recording a payment."
            )

            return

        # ========================================================
        # RECORD PAYMENT
        # ========================================================

        st.subheader("Record Payment")

        # --------------------------------------------------------
        # CREATE INVOICE OPTIONS
        # --------------------------------------------------------

        invoice_options = {}

        for invoice in invoices:

            client_name = (
                invoice.client.company_name
                if invoice.client
                else "Unknown Client"
            )

            balance = get_invoice_balance(invoice)

            status = invoice.status or "Unknown"

            label = (
                f"{invoice.invoice_number} | "
                f"{client_name} | "
                f"{invoice.currency} "
                f"{balance:,.2f} outstanding | "
                f"{status}"
            )

            invoice_options[label] = invoice.id

        # --------------------------------------------------------
        # PAYMENT FORM
        # --------------------------------------------------------

        with st.form("add_payment_form"):

            selected_invoice = st.selectbox(
                "Invoice",
                list(invoice_options.keys())
            )

            selected_invoice_id = invoice_options[
                selected_invoice
            ]

            invoice = session.query(Invoice).filter(
                Invoice.id == selected_invoice_id
            ).first()

            # ----------------------------------------------------
            # INVOICE SUMMARY
            # ----------------------------------------------------

            if invoice:

                invoice_total = get_invoice_total(invoice)
                invoice_paid = get_invoice_paid(invoice)
                invoice_balance = get_invoice_balance(invoice)

                st.info(
                    f"Invoice total: "
                    f"**{format_money(invoice_total, invoice.currency)}**  \n"
                    f"Already paid: "
                    f"**{format_money(invoice_paid, invoice.currency)}**  \n"
                    f"Outstanding: "
                    f"**{format_money(invoice_balance, invoice.currency)}**"
                )

                if invoice.status == "Cancelled":

                    st.warning(
                        "This invoice is cancelled. "
                        "Payments should not normally be recorded "
                        "against a cancelled invoice."
                    )

                elif invoice_balance <= 0:

                    st.success(
                        "This invoice is already fully paid."
                    )

            # ----------------------------------------------------
            # PAYMENT DETAILS
            # ----------------------------------------------------

            payment_date = st.date_input(
                "Payment Date",
                value=date.today()
            )

            amount = st.number_input(
                "Payment Amount",
                min_value=0.01,
                step=100.00,
                format="%.2f"
            )

            col1, col2 = st.columns(2)

            with col1:

                payment_method = st.selectbox(
                    "Payment Method",
                    PAYMENT_METHODS
                )

            with col2:

                status = st.selectbox(
                    "Payment Status",
                    PAYMENT_STATUSES
                )

            reference = st.text_input(
                "Payment Reference",
                placeholder="Example: BANK-2026-001"
            )

            notes = st.text_area(
                "Notes",
                placeholder="Payment notes..."
            )

            submitted = st.form_submit_button(
                "Record Payment",
                use_container_width=True
            )

            # ====================================================
            # PROCESS PAYMENT
            # ====================================================

            if submitted:

                reference = clean_text(reference)
                notes = clean_text(notes)

                # ------------------------------------------------
                # BASIC VALIDATION
                # ------------------------------------------------

                if not invoice:

                    st.error(
                        "Selected invoice could not be found."
                    )

                elif payment_date > date.today():

                    st.error(
                        "Payment date cannot be in the future."
                    )

                elif amount <= 0:

                    st.error(
                        "Payment amount must be greater than zero."
                    )

                elif invoice.status == "Cancelled":

                    st.error(
                        "Payments cannot be recorded against "
                        "a cancelled invoice."
                    )

                elif (
                    status == "Received"
                    and get_invoice_balance(invoice) <= 0
                ):

                    st.error(
                        "This invoice has no outstanding balance."
                    )

                elif (
                    status == "Received"
                    and amount > get_invoice_balance(invoice)
                ):

                    st.error(
                        "Payment cannot be greater than the "
                        "outstanding invoice balance."
                    )

                else:

                    # --------------------------------------------
                    # CREATE PAYMENT
                    # --------------------------------------------

                    payment = Payment(
                        invoice_id=invoice.id,
                        payment_date=payment_date,
                        amount=amount,
                        currency=invoice.currency,
                        payment_method=payment_method,
                        reference=reference,
                        status=status,
                        notes=notes,
                    )

                    session.add(payment)

                    # --------------------------------------------
                    # UPDATE INVOICE
                    #
                    # Only RECEIVED payments affect the invoice's
                    # amount_paid and payment status.
                    # --------------------------------------------

                    if status == "Received":

                        current_paid = get_invoice_paid(invoice)
                        invoice_total = get_invoice_total(invoice)

                        new_paid = current_paid + amount

                        if new_paid >= invoice_total:

                            invoice.amount_paid = invoice_total
                            invoice.status = "Paid"

                        else:

                            invoice.amount_paid = new_paid
                            invoice.status = "Partially Paid"

                    session.commit()

                    st.success(
                        "Payment recorded successfully."
                    )

                    st.rerun()

        # ========================================================
        # PAYMENT REGISTER
        # ========================================================

        st.divider()

        st.subheader("Payment Register")

        payments = session.query(Payment).order_by(
            Payment.payment_date.desc(),
            Payment.id.desc()
        ).all()

        # ========================================================
        # KPI SUMMARY
        # ========================================================

        received_payments = [
            payment
            for payment in payments
            if payment.status == "Received"
        ]

        pending_payments = [
            payment
            for payment in payments
            if payment.status == "Pending"
        ]

        failed_payments = [
            payment
            for payment in payments
            if payment.status == "Failed"
        ]

        reversed_payments = [
            payment
            for payment in payments
            if payment.status == "Reversed"
        ]

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Received",
                len(received_payments)
            )

        with col2:

            st.metric(
                "Pending",
                len(pending_payments)
            )

        with col3:

            st.metric(
                "Failed",
                len(failed_payments)
            )

        with col4:

            st.metric(
                "Reversed",
                len(reversed_payments)
            )

        # ========================================================
        # RECEIVED TOTALS BY CURRENCY
        # ========================================================

        received_totals = get_total_by_status(
            payments,
            "Received"
        )

        if received_totals:

            st.caption("Received payment totals")

            total_columns = st.columns(
                min(len(received_totals), 4)
            )

            for index, (currency, total) in enumerate(
                received_totals.items()
            ):

                with total_columns[index % len(total_columns)]:

                    st.metric(
                        currency,
                        f"{total:,.2f}"
                    )

        # ========================================================
        # NO PAYMENTS
        # ========================================================

        if not payments:

            st.info(
                "No payments have been recorded yet."
            )

            return

        # ========================================================
        # FILTERS
        # ========================================================

        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:

            search = st.text_input(
                "Search",
                placeholder="Invoice, client or reference..."
            )

        with col2:

            status_filter = st.selectbox(
                "Payment Status",
                ["All"] + PAYMENT_STATUSES
            )

        with col3:

            method_filter = st.selectbox(
                "Payment Method",
                ["All"] + PAYMENT_METHODS
            )

        # ========================================================
        # FILTER PAYMENTS
        # ========================================================

        filtered_payments = payments

        # --------------------------------------------------------
        # SEARCH
        # --------------------------------------------------------

        if search:

            search_lower = search.lower().strip()

            filtered_payments = [
                payment
                for payment in filtered_payments

                if (
                    search_lower
                    in get_invoice_number(payment).lower()
                )

                or (
                    search_lower
                    in get_client_name(payment).lower()
                )

                or (
                    search_lower
                    in clean_text(payment.reference).lower()
                )

                or (
                    search_lower
                    in clean_text(payment.notes).lower()
                )
            ]

        # --------------------------------------------------------
        # STATUS
        # --------------------------------------------------------

        if status_filter != "All":

            filtered_payments = [
                payment
                for payment in filtered_payments
                if payment.status == status_filter
            ]

        # --------------------------------------------------------
        # METHOD
        # --------------------------------------------------------

        if method_filter != "All":

            filtered_payments = [
                payment
                for payment in filtered_payments
                if payment.payment_method == method_filter
            ]

        # ========================================================
        # EXPORT
        # ========================================================

        st.download_button(
            label="Download Payment Register CSV",
            data=get_csv_bytes(filtered_payments),
            file_name="averra_payment_register.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.caption(
            f"Showing {len(filtered_payments)} "
            f"of {len(payments)} payments."
        )

        # ========================================================
        # DISPLAY
        # ========================================================

        if not filtered_payments:

            st.info(
                "No payments match your filters."
            )

        else:

            for payment in filtered_payments:

                invoice_number = get_invoice_number(payment)
                client_name = get_client_name(payment)

                payment_currency = (
                    clean_text(payment.currency)
                    or "Unknown"
                )

                payment_status = (
                    clean_text(payment.status)
                    or "Unknown"
                )

                payment_method = (
                    clean_text(payment.payment_method)
                    or "Unknown"
                )

                amount = payment.amount or 0

                # ------------------------------------------------
                # PAYMENT CARD
                # ------------------------------------------------

                with st.container(border=True):

                    col1, col2, col3, col4 = st.columns(
                        [2, 3, 2, 2]
                    )

                    # --------------------------------------------
                    # DATE
                    # --------------------------------------------

                    with col1:

                        if payment.payment_date:

                            st.write(
                                f"**{payment.payment_date.strftime('%d %b %Y')}**"
                            )

                        else:

                            st.write(
                                "**No payment date**"
                            )

                        st.caption(
                            f"Payment ID: {payment.id}"
                        )

                    # --------------------------------------------
                    # INVOICE / CLIENT
                    # --------------------------------------------

                    with col2:

                        st.write(
                            f"**{invoice_number}**"
                        )

                        st.caption(
                            client_name
                        )

                    # --------------------------------------------
                    # AMOUNT
                    # --------------------------------------------

                    with col3:

                        st.write(
                            f"**{payment_currency} "
                            f"{amount:,.2f}**"
                        )

                        st.caption(
                            payment_method
                        )

                    # --------------------------------------------
                    # STATUS / REFERENCE
                    # --------------------------------------------

                    with col4:

                        st.write(
                            f"**{payment_status}**"
                        )

                        if payment.reference:

                            st.caption(
                                f"Reference: {payment.reference}"
                            )

                        else:

                            st.caption(
                                "No payment reference"
                            )

                    # --------------------------------------------
                    # NOTES
                    # --------------------------------------------

                    if payment.notes:

                        st.caption(
                            f"Notes: {payment.notes}"
                        )

                    # --------------------------------------------
                    # INVOICE BALANCE
                    # --------------------------------------------

                    if payment.invoice:

                        current_balance = get_invoice_balance(
                            payment.invoice
                        )

                        st.caption(
                            f"Current invoice balance: "
                            f"{format_money(current_balance, payment.invoice.currency)}"
                        )

    except Exception as e:

        session.rollback()

        st.error(
            "An error occurred while loading Payments."
        )

        # Keep the actual exception visible during development.
        st.exception(e)

    finally:

        session.close()

