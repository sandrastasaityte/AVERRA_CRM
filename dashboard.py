import streamlit as st

from database import get_session
from models import (
    Client,
    ClientContact,
    Employee,
    EmployeeSkill,
    Job,
    Candidate,
    Placement,
    Contract,
    Invoice,
    Payment,
)


# ============================================================
# HELPERS
# ============================================================

def safe_count(query):
    """Return the number of records in a SQLAlchemy query."""
    try:
        return query.count()
    except Exception:
        return 0


def currency_totals(records, amount_getter):
    """Group amounts by currency."""
    totals = {}

    for record in records:
        currency = getattr(record, "currency", None) or "N/A"

        try:
            amount = float(amount_getter(record) or 0)
        except (TypeError, ValueError):
            amount = 0

        totals[currency] = totals.get(currency, 0) + amount

    return totals


def format_currency_amount(currency, amount):
    """Format financial values without performing FX conversion."""
    return f"{currency} {amount:,.2f}"


def get_placement_margin(placement):
    """Calculate placement gross margin."""
    try:
        revenue = float(getattr(placement, "client_monthly_fee", 0) or 0)
    except (TypeError, ValueError):
        revenue = 0

    try:
        cost = float(getattr(placement, "worker_monthly_cost", 0) or 0)
    except (TypeError, ValueError):
        cost = 0

    return revenue - cost


def get_invoice_total(invoice):
    """Get invoice total."""
    try:
        return float(getattr(invoice, "total_amount", 0) or 0)
    except (TypeError, ValueError):
        return 0


def get_invoice_paid(invoice):
    """Get amount paid on invoice."""
    try:
        return float(getattr(invoice, "amount_paid", 0) or 0)
    except (TypeError, ValueError):
        return 0


def get_invoice_balance(invoice):
    """Calculate invoice balance."""
    return max(get_invoice_total(invoice) - get_invoice_paid(invoice), 0)


def get_payment_amount(payment):
    """Get payment amount."""
    try:
        return float(getattr(payment, "amount", 0) or 0)
    except (TypeError, ValueError):
        return 0


def get_client_name(client):
    """Return client company name."""
    return getattr(client, "company_name", None) or "Unnamed Client"


def get_employee_name(employee):
    """Return employee full name."""
    first = getattr(employee, "first_name", "") or ""
    last = getattr(employee, "last_name", "") or ""

    name = f"{first} {last}".strip()

    return name or "Unnamed Employee"


# ============================================================
# MAIN DASHBOARD
# ============================================================

def show_dashboard():
    st.title("AVERRA CRM Dashboard")

    st.caption(
        "Overview of clients, recruitment activity, placements, contracts and financials."
    )

    session = get_session()

    try:
        # ====================================================
        # LOAD DATA
        # ====================================================

        clients = session.query(Client).all()
        contacts = session.query(ClientContact).all()
        employees = session.query(Employee).all()
        skills = session.query(EmployeeSkill).all()
        jobs = session.query(Job).all()
        candidates = session.query(Candidate).all()
        placements = session.query(Placement).all()
        contracts = session.query(Contract).all()
        invoices = session.query(Invoice).all()
        payments = session.query(Payment).all()

        # ====================================================
        # TOP KPI COUNTS
        # ====================================================

        st.subheader("CRM Overview")

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "Clients",
            len(clients),
        )

        col2.metric(
            "Employees",
            len(employees),
        )

        col3.metric(
            "Open Jobs",
            sum(
                1
                for job in jobs
                if getattr(job, "status", "") in ["Open", "On Hold"]
            ),
        )

        col4.metric(
            "Candidates",
            len(candidates),
        )

        col5.metric(
            "Placements",
            sum(
                1
                for placement in placements
                if getattr(placement, "status", "") == "Active"
            ),
        )

        st.divider()

        # ====================================================
        # RECRUITMENT PIPELINE
        # ====================================================

        st.subheader("Recruitment Pipeline")

        pipeline_columns = st.columns(7)

        candidate_statuses = [
            "Submitted",
            "Shortlisted",
            "Interview",
            "Offer",
            "Placed",
            "Rejected",
            "Withdrawn",
        ]

        for column, status in zip(pipeline_columns, candidate_statuses):
            count = sum(
                1
                for candidate in candidates
                if getattr(candidate, "status", None) == status
            )

            column.metric(status, count)

        st.divider()

        # ====================================================
        # JOBS
        # ====================================================

        st.subheader("Jobs")

        job_columns = st.columns(4)

        job_statuses = [
            "Open",
            "On Hold",
            "Filled",
            "Closed",
        ]

        for column, status in zip(job_columns, job_statuses):
            count = sum(
                1
                for job in jobs
                if getattr(job, "status", None) == status
            )

            column.metric(status, count)

        st.divider()

        # ====================================================
        # PLACEMENTS
        # ====================================================

        st.subheader("Placement Overview")

        placement_columns = st.columns(4)

        placement_statuses = [
            "Active",
            "Scheduled",
            "Completed",
            "Terminated",
        ]

        for column, status in zip(
            placement_columns,
            placement_statuses,
        ):
            count = sum(
                1
                for placement in placements
                if getattr(placement, "status", None) == status
            )

            column.metric(status, count)

        # ====================================================
        # PLACEMENT FINANCIALS
        # ====================================================

        st.markdown("### Placement Financials")

        placement_revenue = currency_totals(
            placements,
            lambda p: getattr(p, "client_monthly_fee", 0),
        )

        placement_cost = currency_totals(
            placements,
            lambda p: getattr(p, "worker_monthly_cost", 0),
        )

        placement_margin = {}

        for placement in placements:
            currency = getattr(placement, "currency", None) or "N/A"

            placement_margin[currency] = (
                placement_margin.get(currency, 0)
                + get_placement_margin(placement)
            )

        if placement_revenue:
            financial_rows = []

            currencies = sorted(
                set(
                    list(placement_revenue.keys())
                    + list(placement_cost.keys())
                    + list(placement_margin.keys())
                )
            )

            for currency in currencies:
                revenue = placement_revenue.get(currency, 0)
                cost = placement_cost.get(currency, 0)
                margin = placement_margin.get(currency, 0)

                margin_percentage = (
                    (margin / revenue) * 100
                    if revenue
                    else 0
                )

                financial_rows.append(
                    {
                        "Currency": currency,
                        "Monthly Revenue": f"{revenue:,.2f}",
                        "Monthly Worker Cost": f"{cost:,.2f}",
                        "Gross Margin": f"{margin:,.2f}",
                        "Margin %": f"{margin_percentage:.1f}%",
                    }
                )

            st.dataframe(
                financial_rows,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No placement financial data available yet.")

        st.divider()

        # ====================================================
        # INVOICING
        # ====================================================

        st.subheader("Invoicing")

        invoice_total = currency_totals(
            invoices,
            get_invoice_total,
        )

        invoice_paid = currency_totals(
            invoices,
            get_invoice_paid,
        )

        invoice_outstanding = currency_totals(
            invoices,
            get_invoice_balance,
        )

        invoice_columns = st.columns(3)

        invoice_columns[0].metric(
            "Invoices",
            len(invoices),
        )

        invoice_columns[1].metric(
            "Overdue",
            sum(
                1
                for invoice in invoices
                if getattr(invoice, "status", "") == "Overdue"
            ),
        )

        invoice_columns[2].metric(
            "Payments",
            len(payments),
        )

        if invoices:
            st.markdown("#### Invoice Financials")

            invoice_rows = []

            currencies = sorted(
                set(
                    list(invoice_total.keys())
                    + list(invoice_paid.keys())
                    + list(invoice_outstanding.keys())
                )
            )

            for currency in currencies:
                invoice_rows.append(
                    {
                        "Currency": currency,
                        "Total Invoiced": f"{invoice_total.get(currency, 0):,.2f}",
                        "Total Paid": f"{invoice_paid.get(currency, 0):,.2f}",
                        "Outstanding": f"{invoice_outstanding.get(currency, 0):,.2f}",
                    }
                )

            st.dataframe(
                invoice_rows,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No invoices available yet.")

        st.divider()

        # ====================================================
        # CONTRACTS
        # ====================================================

        st.subheader("Contracts")

        contract_columns = st.columns(4)

        contract_statuses = [
            "Draft",
            "Active",
            "Signed",
            "Expired",
        ]

        for column, status in zip(
            contract_columns,
            contract_statuses,
        ):
            count = sum(
                1
                for contract in contracts
                if getattr(contract, "status", None) == status
            )

            column.metric(status, count)

        st.divider()

        # ====================================================
        # CLIENT OVERVIEW
        # ====================================================

        st.subheader("Client Overview")

        if clients:
            client_rows = []

            for client in clients:
                client_id = getattr(client, "id", None)

                client_jobs = [
                    job
                    for job in jobs
                    if getattr(job, "client_id", None) == client_id
                ]

                client_candidates = [
                    candidate
                    for candidate in candidates
                    if getattr(
                        getattr(candidate, "job", None),
                        "client_id",
                        None,
                    ) == client_id
                ]

                client_placements = [
                    placement
                    for placement in placements
                    if getattr(placement, "client_id", None) == client_id
                ]

                active_placements = [
                    placement
                    for placement in client_placements
                    if getattr(placement, "status", None) == "Active"
                ]

                client_invoices = [
                    invoice
                    for invoice in invoices
                    if getattr(invoice, "client_id", None) == client_id
                ]

                client_rows.append(
                    {
                        "Client": get_client_name(client),
                        "Status": getattr(client, "status", "") or "",
                        "Jobs": len(client_jobs),
                        "Candidates": len(client_candidates),
                        "Placements": len(client_placements),
                        "Active Placements": len(active_placements),
                        "Invoices": len(client_invoices),
                    }
                )

            client_rows.sort(
                key=lambda row: row["Client"].lower()
            )

            st.dataframe(
                client_rows,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No clients available yet.")

        st.divider()

        # ====================================================
        # RECENT / UPCOMING ITEMS
        # ====================================================

        st.subheader("Activity Snapshot")

        snapshot_columns = st.columns(3)

        snapshot_columns[0].metric(
            "Client Contacts",
            len(contacts),
        )

        snapshot_columns[1].metric(
            "Employee Skills",
            len(skills),
        )

        snapshot_columns[2].metric(
            "Total Payments",
            len(payments),
        )

        # ====================================================
        # RECENT JOBS
        # ====================================================

        st.markdown("### Recent Jobs")

        recent_jobs = sorted(
            jobs,
            key=lambda job: getattr(job, "date_opened", None)
            or __import__("datetime").date.min,
            reverse=True,
        )[:10]

        if recent_jobs:
            recent_job_rows = []

            for job in recent_jobs:
                client = getattr(job, "client", None)

                recent_job_rows.append(
                    {
                        "Position": getattr(job, "position", "") or "",
                        "Client": (
                            get_client_name(client)
                            if client
                            else "Unknown"
                        ),
                        "Status": getattr(job, "status", "") or "",
                        "Priority": getattr(job, "priority", "") or "",
                        "Opened": getattr(
                            job,
                            "date_opened",
                            None,
                        ),
                    }
                )

            st.dataframe(
                recent_job_rows,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No jobs available yet.")

        # ====================================================
        # DASHBOARD NOTES
        # ====================================================

        st.divider()

        with st.expander("Dashboard Notes"):
            st.markdown(
                """
                **AVERRA CRM dashboard**

                - Financial figures are kept in their original currencies.
                - No automatic GBP/EUR/USD/INR conversion is performed.
                - Placement gross margin is calculated as client fee minus worker cost.
                - Invoice outstanding amounts are calculated from total minus amount paid.
                - Dashboard figures are based on the records currently stored in the CRM.
                """
            )

    except Exception as exc:
        st.error("Unable to load the dashboard.")
        st.exception(exc)

    finally:
        session.close()