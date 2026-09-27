import streamlit as st
from datetime import date

from database import get_session
from models import Invoice, Client, Placement


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
        return clean_text(invoice.client.company_name) or "Unknown Client"

    return "Unknown Client"


def get_placement_label(placement):
    """Return a readable placement label."""

    employee_name = "Unknown Employee"

    if placement.employee:
        first_name = clean_text(placement.employee.first_name)
        last_name = clean_text(placement.employee.last_name)

        employee_name = f"{first_name} {last_name}".strip()

        if not employee_name:
            employee_name = "Unknown Employee"

    client_name = "Unknown Client"

    if placement.client:
        client_name = (
            clean_text(placement.client.company_name)
            or "Unknown Client"
        )

    position = clean_text(placement.position) or "No Position"

    return (
        f"Placement #{placement.id} - "
        f"{client_name} - "
        f"{employee_name} - "
        f"{position}"
    )


def get_balance_due(invoice):
    """Safely calculate invoice balance."""

    total = float(invoice.total_amount or 0)
    paid = float(invoice.amount_paid or 0)

    return max(total - paid, 0)


def get_effective_status(invoice):
    """
    Return the displayed status.

    If an invoice is not cancelled or paid and the due date
    has passed while money remains outstanding, display Overdue.
    """

    current_status = clean_text(invoice.status)

    if current_status in ["Paid", "Cancelled"]:
        return current_status

    balance = get_balance_due(invoice)

    if (
        invoice.due_date
        and invoice.due_date < date.today()
        and balance > 0
    ):
        return "Overdue"

    return current_status or "Draft"


def has_payments(invoice):
    """Safely determine whether payments are attached."""

    payments = getattr(invoice, "payments", None)

    if payments is not None:
        try:
            return len(payments) > 0
        except TypeError:
            return bool(payments)

    return float(getattr(invoice, "amount_paid", 0) or 0) > 0


def format_money(currency, amount):
    """Format an invoice amount."""
    return f"{currency} {float(amount or 0):,.2f}"


# ============================================================
# MAIN SCREEN
# ============================================================

def show_invoices():

    st.title("Invoices")

    st.caption(
        "Create and manage client invoices, payments and outstanding balances."
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
            .order_by(Client.company_name)
            .all()
        )

        if not clients:

            st.warning(
                "Please add a client before creating an invoice."
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

        if st.session_state.editing_invoice_id is not None:

            editing_invoice = session.get(
                Invoice,
                st.session_state.editing_invoice_id,
            )

            if editing_invoice is None:

                st.session_state.editing_invoice_id = None

        # ====================================================
        # PAGE TITLE
        # ====================================================

        if editing_invoice:

            st.subheader(
                f"Edit Invoice #{editing_invoice.invoice_number}"
            )

        else:

            st.subheader("Create Invoice")

        # ====================================================
        # CLIENT OPTIONS
        # ====================================================

        client_options = {
            f"{clean_text(client.company_name)} "
            f"(ID: {client.id})": client.id
            for client in clients
        }

        client_labels = list(client_options.keys())
        client_values = list(client_options.values())

        # ====================================================
        # CURRENT CLIENT
        # ====================================================

        if (
            editing_invoice
            and editing_invoice.client_id in client_values
        ):

            client_index = client_values.index(
                editing_invoice.client_id
            )

        else:

            client_index = 0

        # ====================================================
        # PLACEMENT OPTIONS
        # ====================================================

        placement_options = {
            "No placement": None
        }

        for placement in placements:

            placement_options[
                get_placement_label(placement)
            ] = placement.id

        placement_labels = list(placement_options.keys())
        placement_values = list(placement_options.values())

        if (
            editing_invoice
            and editing_invoice.placement_id in placement_values
        ):

            placement_index = placement_values.index(
                editing_invoice.placement_id
            )

        else:

            placement_index = 0

        # ====================================================
        # FORM
        # ====================================================

        with st.form("invoice_form"):

            # =================================================
            # CLIENT
            # =================================================

            selected_client = st.selectbox(
                "Client",
                client_labels,
                index=client_index,
            )

            # =================================================
            # PLACEMENT
            # =================================================

            selected_placement = st.selectbox(
                "Related Placement",
                placement_labels,
                index=placement_index,
            )

            # =================================================
            # BASIC INFORMATION
            # =================================================

            invoice_number = st.text_input(
                "Invoice Number",
                value=(
                    clean_text(editing_invoice.invoice_number)
                    if editing_invoice
                    else ""
                ),
                placeholder="Example: INV-2026-001",
            )

            description = st.text_area(
                "Description",
                value=(
                    clean_text(editing_invoice.description)
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

            st.subheader("Invoice Dates")

            date_col1, date_col2 = st.columns(2)

            with date_col1:

                invoice_date = st.date_input(
                    "Invoice Date",
                    value=(
                        editing_invoice.invoice_date
                        if editing_invoice
                        and editing_invoice.invoice_date
                        else date.today()
                    ),
                )

            with date_col2:

                due_date = st.date_input(
                    "Due Date",
                    value=(
                        editing_invoice.due_date
                        if editing_invoice
                        and editing_invoice.due_date
                        else date.today()
                    ),
                )

            # =================================================
            # AMOUNTS
            # =================================================

            st.subheader("Invoice Amount")

            amount_col1, amount_col2 = st.columns(2)

            with amount_col1:

                subtotal = st.number_input(
                    "Subtotal",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    value=(
                        float(editing_invoice.subtotal or 0)
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
                        float(editing_invoice.tax or 0)
                        if editing_invoice
                        else 0.0
                    ),
                )

            total_amount = subtotal + tax

            st.info(
                f"Invoice Total: **{total_amount:,.2f}**"
            )

            # =================================================
            # CURRENCY / STATUS
            # =================================================

            finance_col1, finance_col2 = st.columns(2)

            with finance_col1:

                current_currency = (
                    clean_text(editing_invoice.currency)
                    if editing_invoice
                    else ""
                )

                currency_index = (
                    CURRENCIES.index(current_currency)
                    if current_currency in CURRENCIES
                    else 0
                )

                currency = st.selectbox(
                    "Currency",
                    CURRENCIES,
                    index=currency_index,
                )

            with finance_col2:

                current_status = (
                    clean_text(editing_invoice.status)
                    if editing_invoice
                    else ""
                )

                status_index = (
                    INVOICE_STATUSES.index(current_status)
                    if current_status in INVOICE_STATUSES
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
                    clean_text(editing_invoice.document_link)
                    if editing_invoice
                    else ""
                ),
                placeholder="Paste invoice PDF/document link",
            )

            # =================================================
            # NOTES
            # =================================================

            notes = st.text_area(
                "Notes",
                value=(
                    clean_text(editing_invoice.notes)
                    if editing_invoice
                    else ""
                ),
                placeholder="Invoice notes...",
            )

            # =================================================
            # SUBMIT
            # =================================================

            submitted = st.form_submit_button(
                "Save Changes"
                if editing_invoice
                else "Create Invoice",
                use_container_width=True,
            )

            if submitted:

                invoice_number_clean = invoice_number.strip()
                description_clean = description.strip()
                document_link_clean = document_link.strip()
                notes_clean = notes.strip()

                # =============================================
                # VALIDATION
                # =============================================

                if not invoice_number_clean:

                    st.error(
                        "Invoice number is required."
                    )

                elif due_date < invoice_date:

                    st.error(
                        "Due date cannot be before invoice date."
                    )

                elif subtotal < 0:

                    st.error(
                        "Subtotal cannot be negative."
                    )

                elif tax < 0:

                    st.error(
                        "Tax cannot be negative."
                    )

                else:

                    # =========================================
                    # DUPLICATE CHECK
                    # =========================================

                    duplicate_query = (
                        session.query(Invoice)
                        .filter(
                            Invoice.invoice_number
                            == invoice_number_clean
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
                            client_options[selected_client]
                        )

                        selected_placement_id = (
                            placement_options[
                                selected_placement
                            ]
                        )

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

                                st.session_state.editing_invoice_id = (
                                    None
                                )

                                st.success(
                                    "Invoice updated successfully."
                                )

                                st.rerun()

                            except Exception as e:

                                session.rollback()

                                st.error(
                                    f"Could not update invoice: {e}"
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
                                amount_paid=0,
                                currency=currency,
                                status=status,
                                document_link=document_link_clean,
                                notes=notes_clean,
                            )

                            try:

                                session.add(invoice)
                                session.commit()

                                st.success(
                                    "Invoice created successfully."
                                )

                                st.rerun()

                            except Exception as e:

                                session.rollback()

                                st.error(
                                    f"Could not create invoice: {e}"
                                )

        # ====================================================
        # INVOICE REGISTER
        # ====================================================

        st.divider()

        st.subheader("Invoice Register")

        invoices = (
            session.query(Invoice)
            .order_by(
                Invoice.invoice_date.desc(),
                Invoice.id.desc(),
            )
            .all()
        )

        # ====================================================
        # KPI SECTION
        # ====================================================

        if invoices:

            total_invoices = len(invoices)

            total_invoiced = sum(
                float(invoice.total_amount or 0)
                for invoice in invoices
            )

            total_paid = sum(
                float(invoice.amount_paid or 0)
                for invoice in invoices
            )

            total_outstanding = sum(
                get_balance_due(invoice)
                for invoice in invoices
            )

            total_overdue = sum(
                get_balance_due(invoice)
                for invoice in invoices
                if get_effective_status(invoice) == "Overdue"
            )

            k1, k2, k3, k4, k5 = st.columns(5)

            with k1:

                st.metric(
                    "Invoices",
                    total_invoices,
                )

            with k2:

                st.metric(
                    "Total Invoiced",
                    f"{total_invoiced:,.2f}",
                )

            with k3:

                st.metric(
                    "Total Paid",
                    f"{total_paid:,.2f}",
                )

            with k4:

                st.metric(
                    "Outstanding",
                    f"{total_outstanding:,.2f}",
                )

            with k5:

                st.metric(
                    "Overdue",
                    f"{total_overdue:,.2f}",
                )

        if not invoices:

            st.info(
                "No invoices have been created yet."
            )

            return

        # ====================================================
        # FILTERS
        # ====================================================

        filter_col1, filter_col2, filter_col3 = st.columns(3)

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

        # Search
        if search.strip():

            search_lower = search.strip().lower()

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
                    in get_client_name(invoice).lower()
                )
                or (
                    search_lower
                    in clean_text(
                        invoice.description
                    ).lower()
                )
            ]

        # Status
        if status_filter != "All":

            filtered = [
                invoice
                for invoice in filtered
                if get_effective_status(invoice)
                == status_filter
            ]

        # Currency
        if currency_filter != "All":

            filtered = [
                invoice
                for invoice in filtered
                if clean_text(invoice.currency)
                == currency_filter
            ]

        # ====================================================
        # FILTER RESULT
        # ====================================================

        st.caption(
            f"Showing {len(filtered)} of {len(invoices)} invoice(s)"
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

            client_name = get_client_name(invoice)

            balance_due = get_balance_due(invoice)

            displayed_status = get_effective_status(invoice)

            total_amount = float(
                invoice.total_amount or 0
            )

            amount_paid = float(
                invoice.amount_paid or 0
            )

            currency = clean_text(
                invoice.currency
            ) or "GBP"

            with st.container(border=True):

                # ==========================================
                # MAIN INFORMATION
                # ==========================================

                col1, col2, col3, col4, col5 = st.columns(
                    [2, 3, 2, 2, 1]
                )

                # ------------------------------------------
                # INVOICE
                # ------------------------------------------

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

                # ------------------------------------------
                # CLIENT
                # ------------------------------------------

                with col2:

                    st.write(
                        f"**{client_name}**"
                    )

                    description_text = clean_text(
                        invoice.description
                    )

                    if description_text:

                        st.caption(
                            description_text
                        )

                # ------------------------------------------
                # AMOUNTS
                # ------------------------------------------

                with col3:

                    st.write(
                        f"Total: **"
                        f"{format_money(currency, total_amount)}"
                        f"**"
                    )

                    st.write(
                        f"Paid: **"
                        f"{format_money(currency, amount_paid)}"
                        f"**"
                    )

                # ------------------------------------------
                # STATUS
                # ------------------------------------------

                with col4:

                    st.write(
                        f"Status: **{displayed_status}**"
                    )

                    st.write(
                        f"Balance: **"
                        f"{format_money(currency, balance_due)}"
                        f"**"
                    )

                    if invoice.due_date:

                        st.caption(
                            "Due: "
                            + invoice.due_date.strftime(
                                "%d %b %Y"
                            )
                        )

                # ------------------------------------------
                # ACTIONS
                # ------------------------------------------

                with col5:

                    edit_btn = st.button(
                        "Edit",
                        key=f"edit_invoice_{invoice.id}",
                        use_container_width=True,
                    )

                    delete_btn = st.button(
                        "Delete",
                        key=f"delete_invoice_{invoice.id}",
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
                        f"Are you sure you want to delete "
                        f"invoice **{clean_text(invoice.invoice_number)}**?"
                    )

                    st.caption(
                        "Invoices with recorded payments should "
                        "not normally be deleted."
                    )

                    confirm_col1, confirm_col2 = st.columns(2)

                    with confirm_col1:

                        confirm_delete = st.button(
                            "Yes, Delete Invoice",
                            key=(
                                f"confirm_delete_invoice_"
                                f"{invoice.id}"
                            ),
                            type="primary",
                            use_container_width=True,
                        )

                    with confirm_col2:

                        cancel_delete = st.button(
                            "Cancel",
                            key=(
                                f"cancel_delete_invoice_"
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

                        # ==================================
                        # PAYMENT CHECK
                        # ==================================

                        if has_payments(invoice):

                            st.error(
                                "This invoice cannot be deleted "
                                "because payments are attached to it."
                            )

                            st.session_state.confirm_delete_invoice_id = (
                                None
                            )

                        else:

                            try:

                                session.delete(invoice)
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
                                    f"Could not delete invoice: {e}"
                                )

                # ==========================================
                # DOCUMENT
                # ==========================================

                if clean_text(invoice.document_link):

                    st.link_button(
                        "Open Invoice",
                        invoice.document_link,
                    )

                # ==========================================
                # NOTES
                # ==========================================

                if clean_text(invoice.notes):

                    st.caption(
                        f"Notes: {clean_text(invoice.notes)}"
                    )

    except Exception as e:

        session.rollback()

        st.error(
            f"An error occurred while loading invoices: {e}"
        )

    finally:

        session.close()