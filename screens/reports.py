import streamlit as st

from database import get_session
from models import (
    Client,
    Employee,
    Job,
    Candidate,
    Placement,
    Contract,
    Invoice,
    Payment,
)


# ============================================================
# CONSTANTS
# ============================================================

PLACEMENT_ACTIVE_STATUSES = [
    "Active",
]

PLACEMENT_PIPELINE_STATUSES = [
    "Active",
    "Scheduled",
]

JOB_OPEN_STATUSES = [
    "Open",
]

INVOICE_OPEN_STATUSES = [
    "Draft",
    "Sent",
    "Overdue",
    "Partially Paid",
]


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    """Safely return cleaned text."""

    if value is None:
        return ""

    return str(value).strip()


def get_client_name(client):
    """Return client name safely."""

    if not client:
        return "Unknown Client"

    return (
        clean_text(client.company_name)
        or "Unknown Client"
    )


def get_employee_name(employee):
    """Return employee full name safely."""

    if not employee:
        return "Unknown Employee"

    first_name = clean_text(
        employee.first_name
    )

    last_name = clean_text(
        employee.last_name
    )

    return " ".join(
        part
        for part in [
            first_name,
            last_name,
        ]
        if part
    ) or "Unknown Employee"


def get_currency(value):
    """Return safe currency."""

    return (
        clean_text(value)
        or "GBP"
    )


def get_placement_revenue(placement):
    """Return placement client fee."""

    return float(
        placement.client_monthly_fee or 0
    )


def get_placement_cost(placement):
    """Return placement worker cost."""

    return float(
        placement.worker_monthly_cost or 0
    )


def get_placement_margin(placement):
    """Calculate placement gross margin."""

    return (
        get_placement_revenue(placement)
        - get_placement_cost(placement)
    )


def get_margin_percentage(
    placement
):
    """Calculate placement margin percentage."""

    revenue = get_placement_revenue(
        placement
    )

    if revenue <= 0:
        return 0.0

    margin = get_placement_margin(
        placement
    )

    return (
        margin / revenue
    ) * 100


def get_invoice_total(invoice):
    """Return invoice total safely."""

    return float(
        invoice.total_amount or 0
    )


def get_invoice_paid(invoice):
    """Return invoice paid amount safely."""

    return float(
        invoice.amount_paid or 0
    )


def get_invoice_balance(invoice):
    """Calculate invoice balance."""

    return max(
        get_invoice_total(invoice)
        - get_invoice_paid(invoice),
        0,
    )


def get_payment_amount(payment):
    """Return payment amount safely."""

    return float(
        payment.amount or 0
    )


def count_by_status(items):
    """Return dictionary containing counts by status."""

    results = {}

    for item in items:

        status = clean_text(
            getattr(
                item,
                "status",
                None,
            )
        ) or "Unknown"

        results[status] = (
            results.get(status, 0) + 1
        )

    return results


# ============================================================
# MAIN REPORTS SCREEN
# ============================================================

def show_reports():

    st.title("Reports")

    st.caption(
        "AVERRA CRM business, recruitment and financial reports."
    )

    session = get_session()

    try:

        # ====================================================
        # LOAD DATA
        # ====================================================

        clients = (
            session.query(Client)
            .order_by(
                Client.company_name.asc()
            )
            .all()
        )

        employees = (
            session.query(Employee)
            .order_by(
                Employee.first_name.asc(),
                Employee.last_name.asc(),
            )
            .all()
        )

        jobs = (
            session.query(Job)
            .order_by(
                Job.date_opened.desc()
            )
            .all()
        )

        candidates = (
            session.query(Candidate)
            .order_by(
                Candidate.date_submitted.desc()
            )
            .all()
        )

        placements = (
            session.query(Placement)
            .order_by(
                Placement.start_date.desc()
            )
            .all()
        )

        contracts = (
            session.query(Contract)
            .order_by(
                Contract.start_date.desc()
            )
            .all()
        )

        invoices = (
            session.query(Invoice)
            .order_by(
                Invoice.invoice_date.desc()
            )
            .all()
        )

        payments = (
            session.query(Payment)
            .order_by(
                Payment.payment_date.desc()
            )
            .all()
        )

        # ====================================================
        # REPORT FILTER
        # ====================================================

        st.subheader(
            "Report Filters"
        )

        filter_col1, filter_col2 = (
            st.columns(2)
        )

        with filter_col1:

            report_currency = st.selectbox(
                "Financial Currency",
                [
                    "All",
                    "GBP",
                    "EUR",
                    "USD",
                    "INR",
                ],
            )

        with filter_col2:

            client_filter_options = [
                "All Clients"
            ]

            client_filter_map = {}

            for client in clients:

                name = get_client_name(
                    client
                )

                label = (
                    f"{name} "
                    f"(ID: {client.id})"
                )

                client_filter_options.append(
                    label
                )

                client_filter_map[
                    label
                ] = client.id

            selected_client_filter = (
                st.selectbox(
                    "Client",
                    client_filter_options,
                )
            )

        selected_client_id = None

        if (
            selected_client_filter
            != "All Clients"
        ):

            selected_client_id = (
                client_filter_map[
                    selected_client_filter
                ]
            )

        # ====================================================
        # SUMMARY
        # ====================================================

        st.divider()

        st.subheader(
            "CRM Summary"
        )

        total_open_jobs = sum(
            1
            for job in jobs
            if clean_text(job.status)
            in JOB_OPEN_STATUSES
        )

        total_active_placements = sum(
            1
            for placement in placements
            if clean_text(
                placement.status
            ) in PLACEMENT_ACTIVE_STATUSES
        )

        total_active_employees = sum(
            1
            for employee in employees
            if clean_text(
                employee.employment_status
            ) not in [
                "Former Employee",
                "Unavailable",
            ]
        )

        col1, col2, col3, col4, col5 = (
            st.columns(5)
        )

        with col1:

            st.metric(
                "Clients",
                len(clients),
            )

        with col2:

            st.metric(
                "Employees",
                total_active_employees,
            )

        with col3:

            st.metric(
                "Open Jobs",
                total_open_jobs,
            )

        with col4:

            st.metric(
                "Active Placements",
                total_active_placements,
            )

        with col5:

            st.metric(
                "Contracts",
                len(contracts),
            )

        # ====================================================
        # RECRUITMENT PIPELINE
        # ====================================================

        st.divider()

        st.subheader(
            "Recruitment Pipeline"
        )

        candidate_statuses = count_by_status(
            candidates
        )

        col1, col2, col3, col4 = (
            st.columns(4)
        )

        with col1:

            st.metric(
                "Jobs",
                len(jobs),
            )

        with col2:

            st.metric(
                "Candidates",
                len(candidates),
            )

        with col3:

            submitted_count = (
                candidate_statuses.get(
                    "Submitted",
                    0,
                )
            )

            st.metric(
                "Submitted",
                submitted_count,
            )

        with col4:

            interview_count = (
                candidate_statuses.get(
                    "Interview",
                    0,
                )
            )

            st.metric(
                "Interviews",
                interview_count,
            )

        # ====================================================
        # CANDIDATE PIPELINE
        # ====================================================

        st.write(
            "**Candidate Pipeline**"
        )

        if candidate_statuses:

            pipeline_col1, pipeline_col2 = (
                st.columns(2)
            )

            status_items = list(
                candidate_statuses.items()
            )

            midpoint = (
                len(status_items) + 1
            ) // 2

            with pipeline_col1:

                for status, count in (
                    status_items[:midpoint]
                ):

                    st.write(
                        f"**{status}:** {count}"
                    )

            with pipeline_col2:

                for status, count in (
                    status_items[midpoint:]
                ):

                    st.write(
                        f"**{status}:** {count}"
                    )

        else:

            st.info(
                "No candidates available."
            )

        # ====================================================
        # JOB STATUS
        # ====================================================

        st.divider()

        st.subheader(
            "Jobs by Status"
        )

        job_statuses = count_by_status(
            jobs
        )

        if job_statuses:

            for status, count in (
                job_statuses.items()
            ):

                st.write(
                    f"**{status}:** {count}"
                )

        else:

            st.info(
                "No jobs available."
            )

        # ====================================================
        # PLACEMENT SUMMARY
        # ====================================================

        st.divider()

        st.subheader(
            "Placement Summary"
        )

        placement_statuses = count_by_status(
            placements
        )

        if placement_statuses:

            for status, count in (
                placement_statuses.items()
            ):

                st.write(
                    f"**{status}:** {count}"
                )

        else:

            st.info(
                "No placements available."
            )

        # ====================================================
        # PLACEMENT FINANCIALS
        # ====================================================

        st.divider()

        st.subheader(
            "Placement Financials"
        )

        financial_placements = placements

        if selected_client_id is not None:

            financial_placements = [
                placement
                for placement
                in financial_placements
                if placement.client_id
                == selected_client_id
            ]

        if report_currency != "All":

            financial_placements = [
                placement
                for placement
                in financial_placements
                if get_currency(
                    placement.currency
                ) == report_currency
            ]

        # ----------------------------------------------------
        # Important:
        # Different currencies are NOT converted.
        # Therefore totals are only shown as grouped
        # by currency.
        # ----------------------------------------------------

        placement_currency_totals = {}

        for placement in (
            financial_placements
        ):

            currency = get_currency(
                placement.currency
            )

            if currency not in (
                placement_currency_totals
            ):

                placement_currency_totals[
                    currency
                ] = {
                    "revenue": 0.0,
                    "cost": 0.0,
                    "margin": 0.0,
                }

            revenue = (
                get_placement_revenue(
                    placement
                )
            )

            cost = (
                get_placement_cost(
                    placement
                )
            )

            margin = (
                revenue - cost
            )

            placement_currency_totals[
                currency
            ]["revenue"] += revenue

            placement_currency_totals[
                currency
            ]["cost"] += cost

            placement_currency_totals[
                currency
            ]["margin"] += margin

        if placement_currency_totals:

            for currency in sorted(
                placement_currency_totals
            ):

                totals = (
                    placement_currency_totals[
                        currency
                    ]
                )

                st.write(
                    f"### {currency}"
                )

                col1, col2, col3 = (
                    st.columns(3)
                )

                with col1:

                    st.metric(
                        "Monthly Client Revenue",
                        f"{currency} "
                        f"{totals['revenue']:,.2f}",
                    )

                with col2:

                    st.metric(
                        "Monthly Worker Cost",
                        f"{currency} "
                        f"{totals['cost']:,.2f}",
                    )

                with col3:

                    st.metric(
                        "Monthly Gross Margin",
                        f"{currency} "
                        f"{totals['margin']:,.2f}",
                    )

        else:

            st.info(
                "No placement financial data "
                "matches the selected filters."
            )

        # ====================================================
        # PLACEMENT REGISTER
        # ====================================================

        st.subheader(
            "Placement Register"
        )

        display_placements = placements

        if selected_client_id is not None:

            display_placements = [
                placement
                for placement
                in display_placements
                if placement.client_id
                == selected_client_id
            ]

        if report_currency != "All":

            display_placements = [
                placement
                for placement
                in display_placements
                if get_currency(
                    placement.currency
                ) == report_currency
            ]

        if display_placements:

            for placement in (
                display_placements
            ):

                client_name = (
                    get_client_name(
                        placement.client
                    )
                )

                employee_name = (
                    get_employee_name(
                        placement.employee
                    )
                )

                position = (
                    clean_text(
                        placement.position
                    )
                    or (
                        clean_text(
                            placement.job.position
                        )
                        if placement.job
                        else "No position"
                    )
                )

                currency = get_currency(
                    placement.currency
                )

                revenue = (
                    get_placement_revenue(
                        placement
                    )
                )

                worker_cost = (
                    get_placement_cost(
                        placement
                    )
                )

                margin = (
                    get_placement_margin(
                        placement
                    )
                )

                margin_percentage = (
                    get_margin_percentage(
                        placement
                    )
                )

                with st.container(
                    border=True
                ):

                    col1, col2, col3, col4 = (
                        st.columns(4)
                    )

                    with col1:

                        st.write(
                            f"**Placement "
                            f"#{placement.id}**"
                        )

                        st.caption(
                            client_name
                        )

                    with col2:

                        st.write(
                            f"**{employee_name}**"
                        )

                        st.caption(
                            position
                        )

                    with col3:

                        st.write(
                            f"Revenue: **"
                            f"{currency} "
                            f"{revenue:,.2f}"
                            f"**"
                        )

                        st.write(
                            f"Worker Cost: **"
                            f"{currency} "
                            f"{worker_cost:,.2f}"
                            f"**"
                        )

                    with col4:

                        st.write(
                            f"Margin: **"
                            f"{currency} "
                            f"{margin:,.2f}"
                            f"**"
                        )

                        st.caption(
                            f"Margin: "
                            f"{margin_percentage:.1f}%"
                        )

        else:

            st.info(
                "No placements match the selected filters."
            )

        # ====================================================
        # CONTRACT SUMMARY
        # ====================================================

        st.divider()

        st.subheader(
            "Contracts"
        )

        contract_statuses = count_by_status(
            contracts
        )

        if contract_statuses:

            col1, col2 = st.columns(2)

            status_items = list(
                contract_statuses.items()
            )

            midpoint = (
                len(status_items) + 1
            ) // 2

            with col1:

                for status, count in (
                    status_items[:midpoint]
                ):

                    st.write(
                        f"**{status}:** {count}"
                    )

            with col2:

                for status, count in (
                    status_items[midpoint:]
                ):

                    st.write(
                        f"**{status}:** {count}"
                    )

        else:

            st.info(
                "No contracts available."
            )

        # ====================================================
        # INVOICE SUMMARY
        # ====================================================

        st.divider()

        st.subheader(
            "Invoice Summary"
        )

        filtered_invoices = invoices

        if selected_client_id is not None:

            filtered_invoices = [
                invoice
                for invoice in filtered_invoices
                if invoice.client_id
                == selected_client_id
            ]

        if report_currency != "All":

            filtered_invoices = [
                invoice
                for invoice in filtered_invoices
                if get_currency(
                    invoice.currency
                ) == report_currency
            ]

        invoice_currency_totals = {}

        for invoice in filtered_invoices:

            currency = get_currency(
                invoice.currency
            )

            if currency not in (
                invoice_currency_totals
            ):

                invoice_currency_totals[
                    currency
                ] = {
                    "invoiced": 0.0,
                    "paid": 0.0,
                    "outstanding": 0.0,
                }

            invoice_currency_totals[
                currency
            ]["invoiced"] += (
                get_invoice_total(
                    invoice
                )
            )

            invoice_currency_totals[
                currency
            ]["paid"] += (
                get_invoice_paid(
                    invoice
                )
            )

            invoice_currency_totals[
                currency
            ]["outstanding"] += (
                get_invoice_balance(
                    invoice
                )
            )

        if invoice_currency_totals:

            for currency in sorted(
                invoice_currency_totals
            ):

                totals = (
                    invoice_currency_totals[
                        currency
                    ]
                )

                col1, col2, col3 = (
                    st.columns(3)
                )

                with col1:

                    st.metric(
                        "Total Invoiced",
                        f"{currency} "
                        f"{totals['invoiced']:,.2f}",
                    )

                with col2:

                    st.metric(
                        "Total Paid",
                        f"{currency} "
                        f"{totals['paid']:,.2f}",
                    )

                with col3:

                    st.metric(
                        "Outstanding",
                        f"{currency} "
                        f"{totals['outstanding']:,.2f}",
                    )

        else:

            st.info(
                "No invoices match the selected filters."
            )

        # ====================================================
        # INVOICE STATUS
        # ====================================================

        st.subheader(
            "Invoices by Status"
        )

        invoice_statuses = count_by_status(
            filtered_invoices
        )

        if invoice_statuses:

            for status, count in (
                invoice_statuses.items()
            ):

                st.write(
                    f"**{status}:** {count}"
                )

        else:

            st.info(
                "No invoice data available."
            )

        # ====================================================
        # PAYMENT SUMMARY
        # ====================================================

        st.divider()

        st.subheader(
            "Payments"
        )

        filtered_payments = payments

        if report_currency != "All":

            filtered_payments = [
                payment
                for payment in filtered_payments
                if get_currency(
                    payment.currency
                ) == report_currency
            ]

        payment_currency_totals = {}

        for payment in (
            filtered_payments
        ):

            currency = get_currency(
                payment.currency
            )

            if currency not in (
                payment_currency_totals
            ):

                payment_currency_totals[
                    currency
                ] = 0.0

            payment_currency_totals[
                currency
            ] += get_payment_amount(
                payment
            )

        if payment_currency_totals:

            for currency in sorted(
                payment_currency_totals
            ):

                col1, col2 = (
                    st.columns(2)
                )

                with col1:

                    st.metric(
                        "Payment Transactions",
                        sum(
                            1
                            for payment
                            in filtered_payments
                            if get_currency(
                                payment.currency
                            ) == currency
                        ),
                    )

                with col2:

                    st.metric(
                        "Payment Value",
                        f"{currency} "
                        f"{payment_currency_totals[currency]:,.2f}",
                    )

        else:

            st.info(
                "No payment data matches the selected filters."
            )

        # ====================================================
        # CLIENT SUMMARY
        # ====================================================

        st.divider()

        st.subheader(
            "Client Summary"
        )

        display_clients = clients

        if selected_client_id is not None:

            display_clients = [
                client
                for client in display_clients
                if client.id
                == selected_client_id
            ]

        if display_clients:

            for client in display_clients:

                client_jobs = [
                    job
                    for job in jobs
                    if job.client_id
                    == client.id
                ]

                client_placements = [
                    placement
                    for placement
                    in placements
                    if placement.client_id
                    == client.id
                ]

                client_invoices = [
                    invoice
                    for invoice
                    in invoices
                    if invoice.client_id
                    == client.id
                ]

                active_client_placements = [
                    placement
                    for placement
                    in client_placements
                    if clean_text(
                        placement.status
                    ) == "Active"
                ]

                client_candidates = [
                    candidate
                    for candidate
                    in candidates
                    if (
                        candidate.job
                        and candidate.job.client_id
                        == client.id
                    )
                ]

                with st.container(
                    border=True
                ):

                    st.write(
                        f"### "
                        f"{get_client_name(client)}"
                    )

                    if client.status:

                        st.caption(
                            clean_text(
                                client.status
                            )
                        )

                    col1, col2, col3, col4, col5 = (
                        st.columns(5)
                    )

                    with col1:

                        st.write(
                            f"Jobs: **"
                            f"{len(client_jobs)}**"
                        )

                    with col2:

                        st.write(
                            f"Candidates: **"
                            f"{len(client_candidates)}**"
                        )

                    with col3:

                        st.write(
                            f"Placements: **"
                            f"{len(client_placements)}**"
                        )

                    with col4:

                        st.write(
                            f"Active: **"
                            f"{len(active_client_placements)}**"
                        )

                    with col5:

                        st.write(
                            f"Invoices: **"
                            f"{len(client_invoices)}**"
                        )

        else:

            st.info(
                "No clients match the selected filter."
            )

        # ====================================================
        # REPORT NOTES
        # ====================================================

        st.divider()

        st.subheader(
            "Report Notes"
        )

        st.info(
            "Financial figures are grouped by currency. "
            "AVERRA CRM does not currently perform foreign "
            "exchange conversion, so GBP, EUR, USD and INR "
            "must not be added together as if they were the "
            "same currency."
        )

        st.caption(
            "Placement revenue and worker cost are monthly "
            "figures based on the values recorded in the "
            "Placement records."
        )

    except Exception as e:

        session.rollback()

        st.error(
            "An error occurred while generating reports: "
            f"{e}"
        )

    finally:

        session.close()