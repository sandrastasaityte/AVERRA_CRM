import streamlit as st
from datetime import date

from database import get_session
from models import Payment, Invoice


def show_payments():

    st.title("Payments")
    st.caption("Record and track client invoice payments.")

    session = get_session()

    # ============================================================
    # LOAD INVOICES
    # ============================================================

    invoices = session.query(Invoice).order_by(
        Invoice.invoice_date.desc(),
        Invoice.id.desc()
    ).all()

    if not invoices:
        st.warning("Please create an invoice first.")
        session.close()
        return

    # ============================================================
    # RECORD PAYMENT
    # ============================================================

    st.subheader("Record Payment")

    with st.form("add_payment_form"):

        invoice_options = {}

        for invoice in invoices:

            client_name = (
                invoice.client.company_name
                if invoice.client
                else "Unknown Client"
            )

            balance = invoice.balance_due

            invoice_options[
                f"{invoice.invoice_number} | "
                f"{client_name} | "
                f"{invoice.currency} {balance:,.2f} outstanding"
            ] = invoice.id

        selected_invoice = st.selectbox(
            "Invoice",
            list(invoice_options.keys())
        )

        selected_invoice_id = invoice_options[selected_invoice]

        invoice = session.query(Invoice).filter(
            Invoice.id == selected_invoice_id
        ).first()

        if invoice:

            st.info(
                f"Invoice total: "
                f"**{invoice.currency} "
                f"{invoice.total_amount or 0:,.2f}**  \n"
                f"Already paid: "
                f"**{invoice.currency} "
                f"{invoice.amount_paid or 0:,.2f}**  \n"
                f"Outstanding: "
                f"**{invoice.currency} "
                f"{invoice.balance_due:,.2f}**"
            )

        # --------------------------------------------------------
        # PAYMENT DETAILS
        # --------------------------------------------------------

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
                [
                    "Bank Transfer",
                    "Revolut",
                    "Wise",
                    "Card",
                    "Direct Debit",
                    "Cash",
                    "Other"
                ]
            )

        with col2:

            status = st.selectbox(
                "Payment Status",
                [
                    "Received",
                    "Pending",
                    "Failed",
                    "Reversed"
                ]
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

        if submitted:

            if amount <= 0:

                st.error(
                    "Payment amount must be greater than zero."
                )

            elif not invoice:

                st.error(
                    "Selected invoice could not be found."
                )

            elif status == "Received" and amount > invoice.balance_due:

                st.error(
                    "Payment cannot be greater than the "
                    "outstanding invoice balance."
                )

            else:

                payment = Payment(
                    invoice_id=invoice.id,
                    payment_date=payment_date,
                    amount=amount,
                    currency=invoice.currency,
                    payment_method=payment_method,
                    reference=reference.strip(),
                    status=status,
                    notes=notes.strip()
                )

                session.add(payment)

                # ------------------------------------------------
                # UPDATE INVOICE
                # ------------------------------------------------

                if status == "Received":

                    invoice.amount_paid = (
                        invoice.amount_paid or 0
                    ) + amount

                    if invoice.amount_paid >= invoice.total_amount:

                        invoice.amount_paid = invoice.total_amount

                        invoice.status = "Paid"

                    elif invoice.amount_paid > 0:

                        invoice.status = "Partially Paid"

                session.commit()

                st.success(
                    "Payment recorded successfully."
                )

                st.rerun()

    # ============================================================
    # PAYMENT REGISTER
    # ============================================================

    st.divider()

    st.subheader("Payment Register")

    payments = session.query(Payment).order_by(
        Payment.payment_date.desc(),
        Payment.id.desc()
    ).all()

    if not payments:

        st.info(
            "No payments have been recorded yet."
        )

        session.close()
        return

    # ============================================================
    # FILTERS
    # ============================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        search = st.text_input(
            "Search",
            placeholder="Invoice or reference..."
        )

    with col2:

        status_filter = st.selectbox(
            "Payment Status",
            [
                "All",
                "Received",
                "Pending",
                "Failed",
                "Reversed"
            ]
        )

    with col3:

        method_filter = st.selectbox(
            "Payment Method",
            [
                "All",
                "Bank Transfer",
                "Revolut",
                "Wise",
                "Card",
                "Direct Debit",
                "Cash",
                "Other"
            ]
        )

    # ============================================================
    # APPLY FILTERS
    # ============================================================

    filtered_payments = payments

    if search:

        search_lower = search.lower()

        filtered_payments = [
            payment
            for payment in filtered_payments

            if (
                payment.invoice
                and search_lower
                in (
                    payment.invoice.invoice_number or ""
                ).lower()
            )

            or (
                search_lower
                in (payment.reference or "").lower()
            )
        ]

    if status_filter != "All":

        filtered_payments = [
            payment
            for payment in filtered_payments
            if payment.status == status_filter
        ]

    if method_filter != "All":

        filtered_payments = [
            payment
            for payment in filtered_payments
            if payment.payment_method == method_filter
        ]

    # ============================================================
    # DISPLAY
    # ============================================================

    if not filtered_payments:

        st.info(
            "No payments match your filters."
        )

    else:

        for payment in filtered_payments:

            invoice_number = (
                payment.invoice.invoice_number
                if payment.invoice
                else "Unknown Invoice"
            )

            client_name = (
                payment.invoice.client.company_name
                if payment.invoice
                and payment.invoice.client
                else "Unknown Client"
            )

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(
                    [2, 3, 2, 2]
                )

                # ------------------------------------------------
                # DATE
                # ------------------------------------------------

                with col1:

                    if payment.payment_date:

                        st.write(
                            f"**{payment.payment_date.strftime('%d %b %Y')}**"
                        )

                    st.caption(
                        payment.status
                    )

                # ------------------------------------------------
                # INVOICE / CLIENT
                # ------------------------------------------------

                with col2:

                    st.write(
                        f"**{invoice_number}**"
                    )

                    st.caption(
                        client_name
                    )

                # ------------------------------------------------
                # AMOUNT
                # ------------------------------------------------

                with col3:

                    st.write(
                        f"**{payment.currency} "
                        f"{payment.amount:,.2f}**"
                    )

                    st.caption(
                        payment.payment_method
                    )

                # ------------------------------------------------
                # REFERENCE
                # ------------------------------------------------

                with col4:

                    if payment.reference:

                        st.write(
                            f"Reference: "
                            f"**{payment.reference}**"
                        )

                    else:

                        st.caption(
                            "No payment reference"
                        )

                if payment.notes:

                    st.caption(
                        f"Notes: {payment.notes}"
                    )

    session.close()