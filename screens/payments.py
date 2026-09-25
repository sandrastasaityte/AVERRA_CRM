import streamlit as st
from datetime import date

from database import get_session
from models import Invoice, Client, Placement


def show_invoices():

    st.title("Invoices")
    st.caption("Create and manage client invoices.")

    session = get_session()

    # ============================================================
    # LOAD DATA
    # ============================================================

    clients = session.query(Client).order_by(
        Client.company_name
    ).all()

    placements = session.query(Placement).order_by(
        Placement.id.desc()
    ).all()

    if not clients:
        st.warning("Please add a client first.")
        session.close()
        return

    # ============================================================
    # ADD INVOICE
    # ============================================================

    st.subheader("Create Invoice")

    with st.form("add_invoice_form"):

        client_options = {
            f"{client.company_name} (ID: {client.id})": client.id
            for client in clients
        }

        selected_client = st.selectbox(
            "Client",
            list(client_options.keys())
        )

        placement_options = {
            "No placement": None
        }

        for placement in placements:

            employee_name = "Unknown Employee"

            if placement.employee:
                employee_name = (
                    f"{placement.employee.first_name} "
                    f"{placement.employee.last_name or ''}"
                ).strip()

            placement_options[
                f"Placement #{placement.id} - "
                f"{employee_name} - "
                f"{placement.position or 'No position'}"
            ] = placement.id

        selected_placement = st.selectbox(
            "Related Placement",
            list(placement_options.keys())
        )

        invoice_number = st.text_input(
            "Invoice Number",
            placeholder="Example: INV-2026-001"
        )

        description = st.text_area(
            "Description",
            placeholder="Example: Remote finance specialist services - October 2026"
        )

        # --------------------------------------------------------
        # DATES
        # --------------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            invoice_date = st.date_input(
                "Invoice Date",
                value=date.today()
            )

        with col2:

            due_date = st.date_input(
                "Due Date",
                value=date.today()
            )

        # --------------------------------------------------------
        # AMOUNTS
        # --------------------------------------------------------

        st.subheader("Invoice Amount")

        col3, col4 = st.columns(2)

        with col3:

            subtotal = st.number_input(
                "Subtotal",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )

        with col4:

            tax = st.number_input(
                "Tax",
                min_value=0.0,
                step=10.0,
                format="%.2f"
            )

        total_amount = subtotal + tax

        st.info(
            f"Invoice Total: **£{total_amount:,.2f}**"
        )

        # --------------------------------------------------------
        # CURRENCY / STATUS
        # --------------------------------------------------------

        col5, col6 = st.columns(2)

        with col5:

            currency = st.selectbox(
                "Currency",
                [
                    "GBP",
                    "EUR",
                    "USD",
                    "INR"
                ]
            )

        with col6:

            status = st.selectbox(
                "Invoice Status",
                [
                    "Draft",
                    "Sent",
                    "Partially Paid",
                    "Paid",
                    "Overdue",
                    "Cancelled"
                ]
            )

        document_link = st.text_input(
            "Invoice Document Link",
            placeholder="Paste invoice PDF/document link"
        )

        notes = st.text_area(
            "Notes",
            placeholder="Invoice notes..."
        )

        submitted = st.form_submit_button(
            "Create Invoice",
            use_container_width=True
        )

        if submitted:

            if not invoice_number.strip():

                st.error(
                    "Invoice number is required."
                )

            elif due_date < invoice_date:

                st.error(
                    "Due date cannot be before invoice date."
                )

            else:

                existing_invoice = session.query(
                    Invoice
                ).filter(
                    Invoice.invoice_number
                    == invoice_number.strip()
                ).first()

                if existing_invoice:

                    st.error(
                        "An invoice with this invoice number already exists."
                    )

                else:

                    invoice = Invoice(
                        client_id=client_options[selected_client],
                        placement_id=placement_options[selected_placement],
                        invoice_number=invoice_number.strip(),
                        invoice_date=invoice_date,
                        due_date=due_date,
                        description=description.strip(),
                        subtotal=subtotal,
                        tax=tax,
                        total_amount=total_amount,
                        amount_paid=0,
                        currency=currency,
                        status=status,
                        document_link=document_link.strip(),
                        notes=notes.strip()
                    )

                    session.add(invoice)
                    session.commit()

                    st.success(
                        "Invoice created successfully."
                    )

                    st.rerun()

    # ============================================================
    # INVOICE REGISTER
    # ============================================================

    st.divider()

    st.subheader("Invoice Register")

    invoices = session.query(Invoice).order_by(
        Invoice.invoice_date.desc(),
        Invoice.id.desc()
    ).all()

    if not invoices:

        st.info(
            "No invoices have been created yet."
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
            placeholder="Invoice number or client..."
        )

    with col2:

        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Draft",
                "Sent",
                "Partially Paid",
                "Paid",
                "Overdue",
                "Cancelled"
            ]
        )

    with col3:

        currency_filter = st.selectbox(
            "Currency",
            [
                "All",
                "GBP",
                "EUR",
                "USD",
                "INR"
            ]
        )

    # ============================================================
    # APPLY FILTERS
    # ============================================================

    filtered_invoices = invoices

    if search:

        search_lower = search.lower()

        filtered_invoices = [
            invoice
            for invoice in filtered_invoices
            if (
                search_lower
                in (invoice.invoice_number or "").lower()

                or (
                    invoice.client
                    and search_lower
                    in (
                        invoice.client.company_name or ""
                    ).lower()
                )
            )
        ]

    if status_filter != "All":

        filtered_invoices = [
            invoice
            for invoice in filtered_invoices
            if invoice.status == status_filter
        ]

    if currency_filter != "All":

        filtered_invoices = [
            invoice
            for invoice in filtered_invoices
            if invoice.currency == currency_filter
        ]

    # ============================================================
    # DISPLAY
    # ============================================================

    if not filtered_invoices:

        st.info(
            "No invoices match your filters."
        )

    else:

        for invoice in filtered_invoices:

            client_name = (
                invoice.client.company_name
                if invoice.client
                else "Unknown Client"
            )

            balance_due = invoice.balance_due

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(
                    [2, 3, 2, 2]
                )

                # ------------------------------------------------
                # INVOICE
                # ------------------------------------------------

                with col1:

                    st.write(
                        f"**{invoice.invoice_number}**"
                    )

                    if invoice.invoice_date:

                        st.caption(
                            invoice.invoice_date.strftime(
                                "%d %b %Y"
                            )
                        )

                # ------------------------------------------------
                # CLIENT
                # ------------------------------------------------

                with col2:

                    st.write(
                        f"**{client_name}**"
                    )

                    if invoice.description:

                        st.caption(
                            invoice.description
                        )

                # ------------------------------------------------
                # AMOUNT
                # ------------------------------------------------

                with col3:

                    st.write(
                        f"Total: **"
                        f"{invoice.currency} "
                        f"{invoice.total_amount or 0:,.2f}"
                        f"**"
                    )

                    st.write(
                        f"Paid: **"
                        f"{invoice.currency} "
                        f"{invoice.amount_paid or 0:,.2f}"
                        f"**"
                    )

                # ------------------------------------------------
                # STATUS
                # ------------------------------------------------

                with col4:

                    st.write(
                        f"Status: **{invoice.status}**"
                    )

                    st.write(
                        f"Balance: **"
                        f"{invoice.currency} "
                        f"{balance_due:,.2f}"
                        f"**"
                    )

                    if invoice.due_date:

                        st.caption(
                            f"Due: "
                            f"{invoice.due_date.strftime('%d %b %Y')}"
                        )

                # ------------------------------------------------
                # DOCUMENT
                # ------------------------------------------------

                if invoice.document_link:

                    st.link_button(
                        "Open Invoice",
                        invoice.document_link
                    )

                if invoice.notes:

                    st.caption(
                        f"Notes: {invoice.notes}"
                    )

    session.close()