import streamlit as st
from datetime import date

from database import get_session
from models import Invoice, Client, Placement


CURRENCIES = [
    "GBP",
    "EUR",
    "USD",
    "INR"
]

INVOICE_STATUSES = [
    "Draft",
    "Sent",
    "Partially Paid",
    "Paid",
    "Overdue",
    "Cancelled"
]


def show_invoices():

    st.title("Invoices")
    st.caption(
        "Create and manage client invoices and outstanding balances."
    )

    session = get_session()

    # ============================================================
    # SESSION STATE
    # ============================================================

    if "editing_invoice_id" not in st.session_state:
        st.session_state.editing_invoice_id = None

    if "confirm_delete_invoice_id" not in st.session_state:
        st.session_state.confirm_delete_invoice_id = None

    # ============================================================
    # LOAD DATA
    # ============================================================

    clients = (
        session.query(Client)
        .order_by(Client.company_name)
        .all()
    )

    placements = (
        session.query(Placement)
        .order_by(Placement.id.desc())
        .all()
    )

    if not clients:

        st.warning(
            "Please add a client first."
        )

        session.close()
        return

    # ============================================================
    # EDITING
    # ============================================================

    editing_invoice = None

    if st.session_state.editing_invoice_id is not None:

        editing_invoice = session.get(
            Invoice,
            st.session_state.editing_invoice_id
        )

        if editing_invoice is None:

            st.session_state.editing_invoice_id = None

    # ============================================================
    # FORM TITLE
    # ============================================================

    if editing_invoice:

        st.subheader(
            f"Edit Invoice (ID: {editing_invoice.id})"
        )

    else:

        st.subheader(
            "Create Invoice"
        )

    # ============================================================
    # ADD / EDIT FORM
    # ============================================================

    with st.form("invoice_form"):

        # ========================================================
        # CLIENT
        # ========================================================

        client_options = {
            f"{client.company_name} (ID: {client.id})":
            client.id
            for client in clients
        }

        client_values = list(
            client_options.values()
        )

        if (
            editing_invoice
            and editing_invoice.client_id in client_values
        ):

            client_index = client_values.index(
                editing_invoice.client_id
            )

        else:

            client_index = 0

        selected_client = st.selectbox(
            "Client",
            list(client_options.keys()),
            index=client_index
        )

        # ========================================================
        # PLACEMENT
        # ========================================================

        placement_options = {
            "No placement": None
        }

        for placement in placements:

            employee_name = (
                f"{placement.employee.first_name} "
                f"{placement.employee.last_name or ''}"
                if placement.employee
                else "Unknown Employee"
            )

            client_name = (
                placement.client.company_name
                if placement.client
                else "Unknown Client"
            )

            position = (
                placement.position
                if placement.position
                else "No position"
            )

            placement_options[
                f"Placement #{placement.id} - "
                f"{client_name} - "
                f"{employee_name} - "
                f"{position}"
            ] = placement.id

        placement_values = list(
            placement_options.values()
        )

        if (
            editing_invoice
            and editing_invoice.placement_id in placement_values
        ):

            placement_index = placement_values.index(
                editing_invoice.placement_id
            )

        else:

            placement_index = 0

        selected_placement = st.selectbox(
            "Related Placement",
            list(placement_options.keys()),
            index=placement_index
        )

        # ========================================================
        # BASIC FIELDS
        # ========================================================

        invoice_number = st.text_input(
            "Invoice Number",
            value=(
                editing_invoice.invoice_number
                if editing_invoice
                else ""
            ),
            placeholder="Example: INV-2026-001"
        )

        description = st.text_area(
            "Description",
            value=(
                editing_invoice.description
                if editing_invoice
                else ""
            ),
            placeholder=(
                "Example: Remote finance specialist "
                "services - October 2026"
            )
        )

        # ========================================================
        # DATES
        # ========================================================

        col1, col2 = st.columns(2)

        with col1:

            invoice_date = st.date_input(
                "Invoice Date",
                value=(
                    editing_invoice.invoice_date
                    if editing_invoice
                    else date.today()
                )
            )

        with col2:

            due_date = st.date_input(
                "Due Date",
                value=(
                    editing_invoice.due_date
                    if editing_invoice
                    else date.today()
                )
            )

        # ========================================================
        # AMOUNTS
        # ========================================================

        st.subheader(
            "Invoice Amount"
        )

        col3, col4 = st.columns(2)

        with col3:

            subtotal = st.number_input(
                "Subtotal",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                value=(
                    float(
                        editing_invoice.subtotal or 0
                    )
                    if editing_invoice
                    else 0.0
                )
            )

        with col4:

            tax = st.number_input(
                "Tax",
                min_value=0.0,
                step=10.0,
                format="%.2f",
                value=(
                    float(
                        editing_invoice.tax or 0
                    )
                    if editing_invoice
                    else 0.0
                )
            )

        total_amount = subtotal + tax

        st.info(
            f"Invoice Total: **{total_amount:,.2f}**"
        )

        # ========================================================
        # CURRENCY / STATUS
        # ========================================================

        col5, col6 = st.columns(2)

        with col5:

            if (
                editing_invoice
                and editing_invoice.currency in CURRENCIES
            ):

                currency_index = CURRENCIES.index(
                    editing_invoice.currency
                )

            else:

                currency_index = 0

            currency = st.selectbox(
                "Currency",
                CURRENCIES,
                index=currency_index
            )

        with col6:

            if (
                editing_invoice
                and editing_invoice.status in INVOICE_STATUSES
            ):

                status_index = INVOICE_STATUSES.index(
                    editing_invoice.status
                )

            else:

                status_index = 0

            status = st.selectbox(
                "Invoice Status",
                INVOICE_STATUSES,
                index=status_index
            )

        # ========================================================
        # DOCUMENT
        # ========================================================

        document_link = st.text_input(
            "Invoice Document Link",
            value=(
                editing_invoice.document_link
                if editing_invoice
                else ""
            ),
            placeholder="Paste invoice PDF/document link"
        )

        # ========================================================
        # NOTES
        # ========================================================

        notes = st.text_area(
            "Notes",
            value=(
                editing_invoice.notes
                if editing_invoice
                else ""
            ),
            placeholder="Invoice notes..."
        )

        # ========================================================
        # SUBMIT
        # ========================================================

        submitted = st.form_submit_button(
            "Save Changes"
            if editing_invoice
            else "Create Invoice",
            use_container_width=True
        )

        if submitted:

            # ----------------------------------------------------
            # VALIDATION
            # ----------------------------------------------------

            if not invoice_number.strip():

                st.error(
                    "Invoice number is required."
                )

            elif due_date < invoice_date:

                st.error(
                    "Due date cannot be before invoice date."
                )

            else:

                # ------------------------------------------------
                # DUPLICATE INVOICE NUMBER
                # ------------------------------------------------

                duplicate_query = (
                    session.query(Invoice)
                    .filter(
                        Invoice.invoice_number
                        == invoice_number.strip()
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
                        "An invoice with this invoice number "
                        "already exists."
                    )

                else:

                    selected_client_id = (
                        client_options[
                            selected_client
                        ]
                    )

                    selected_placement_id = (
                        placement_options[
                            selected_placement
                        ]
                    )

                    # ============================================
                    # UPDATE
                    # ============================================

                    if editing_invoice:

                        editing_invoice.client_id = (
                            selected_client_id
                        )

                        editing_invoice.placement_id = (
                            selected_placement_id
                        )

                        editing_invoice.invoice_number = (
                            invoice_number.strip()
                        )

                        editing_invoice.invoice_date = (
                            invoice_date
                        )

                        editing_invoice.due_date = (
                            due_date
                        )

                        editing_invoice.description = (
                            description.strip()
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
                            document_link.strip()
                        )

                        editing_invoice.notes = (
                            notes.strip()
                        )

                        session.commit()

                        st.session_state.editing_invoice_id = (
                            None
                        )

                        st.success(
                            "Invoice updated successfully."
                        )

                        st.rerun()

                    # ============================================
                    # CREATE
                    # ============================================

                    else:

                        invoice = Invoice(

                            client_id=selected_client_id,

                            placement_id=selected_placement_id,

                            invoice_number=(
                                invoice_number.strip()
                            ),

                            invoice_date=invoice_date,

                            due_date=due_date,

                            description=(
                                description.strip()
                            ),

                            subtotal=subtotal,

                            tax=tax,

                            total_amount=total_amount,

                            amount_paid=0,

                            currency=currency,

                            status=status,

                            document_link=(
                                document_link.strip()
                            ),

                            notes=notes.strip()
                        )

                        session.add(
                            invoice
                        )

                        session.commit()

                        st.success(
                            "Invoice created successfully."
                        )

                        st.rerun()

    # ============================================================
    # INVOICE REGISTER
    # ============================================================

    st.divider()

    st.subheader(
        "Invoice Register"
    )

    invoices = (
        session.query(Invoice)
        .order_by(
            Invoice.invoice_date.desc(),
            Invoice.id.desc()
        )
        .all()
    )

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
            ["All"] + INVOICE_STATUSES
        )

    with col3:

        currency_filter = st.selectbox(
            "Currency",
            ["All"] + CURRENCIES
        )

    filtered = invoices

    # ============================================================
    # SEARCH
    # ============================================================

    if search:

        search_lower = search.lower()

        filtered = [

            invoice

            for invoice in filtered

            if (
                search_lower
                in (
                    invoice.invoice_number
                    or ""
                ).lower()
            )

            or (
                invoice.client
                and search_lower
                in (
                    invoice.client.company_name
                    or ""
                ).lower()
            )
        ]

    # ============================================================
    # STATUS FILTER
    # ============================================================

    if status_filter != "All":

        filtered = [

            invoice

            for invoice in filtered

            if invoice.status == status_filter
        ]

    # ============================================================
    # CURRENCY FILTER
    # ============================================================

    if currency_filter != "All":

        filtered = [

            invoice

            for invoice in filtered

            if invoice.currency == currency_filter
        ]

    # ============================================================
    # DISPLAY
    # ============================================================

    if not filtered:

        st.info(
            "No invoices match your filters."
        )

    else:

        for invoice in filtered:

            client_name = (
                invoice.client.company_name
                if invoice.client
                else "Unknown Client"
            )

            balance_due = (
                invoice.balance_due
            )

            with st.container(border=True):

                col1, col2, col3, col4, col5 = st.columns(
                    [2, 3, 2, 2, 1]
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
                # AMOUNTS
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
                            "Due: "
                            + invoice.due_date.strftime(
                                "%d %b %Y"
                            )
                        )

                # ------------------------------------------------
                # ACTIONS
                # ------------------------------------------------

                with col5:

                    edit_btn = st.button(
                        "Edit",
                        key=f"edit_invoice_{invoice.id}",
                        use_container_width=True
                    )

                    delete_btn = st.button(
                        "Delete",
                        key=f"delete_invoice_{invoice.id}",
                        use_container_width=True
                    )

                # =================================================
                # EDIT
                # =================================================

                if edit_btn:

                    st.session_state.editing_invoice_id = (
                        invoice.id
                    )

                    st.rerun()

                # =================================================
                # DELETE REQUEST
                # =================================================

                if delete_btn:

                    st.session_state.confirm_delete_invoice_id = (
                        invoice.id
                    )

                    st.rerun()

                # =================================================
                # DELETE CONFIRMATION
                # =================================================

                if (
                    st.session_state.confirm_delete_invoice_id
                    == invoice.id
                ):

                    st.warning(
                        f"Are you sure you want to delete "
                        f"invoice **{invoice.invoice_number}**?"
                    )

                    st.caption(
                        "Invoices with recorded payments should "
                        "not normally be deleted."
                    )

                    c1, c2 = st.columns(2)

                    with c1:

                        confirm = st.button(
                            "Yes, Delete Invoice",
                            key=(
                                f"confirm_delete_invoice_"
                                f"{invoice.id}"
                            ),
                            type="primary",
                            use_container_width=True
                        )

                    with c2:

                        cancel = st.button(
                            "Cancel",
                            key=(
                                f"cancel_delete_invoice_"
                                f"{invoice.id}"
                            ),
                            use_container_width=True
                        )

                    if cancel:

                        st.session_state.confirm_delete_invoice_id = (
                            None
                        )

                        st.rerun()

                    if confirm:

                        # ------------------------------------------------
                        # PAYMENT CHECK
                        # ------------------------------------------------

                        payments = getattr(
                            invoice,
                            "payments",
                            []
                        )

                        if payments:

                            st.error(
                                "This invoice cannot be deleted "
                                "because payments are attached to it."
                            )

                            st.session_state.confirm_delete_invoice_id = (
                                None
                            )

                        else:

                            session.delete(
                                invoice
                            )

                            session.commit()

                            st.success(
                                "Invoice deleted successfully."
                            )

                            st.session_state.confirm_delete_invoice_id = (
                                None
                            )

                            st.rerun()

                # =================================================
                # DOCUMENT
                # =================================================

                if invoice.document_link:

                    st.link_button(
                        "Open Invoice",
                        invoice.document_link
                    )

                # =================================================
                # NOTES
                # =================================================

                if invoice.notes:

                    st.caption(
                        f"Notes: {invoice.notes}"
                    )

    session.close()