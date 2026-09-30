import streamlit as st
from datetime import date

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

PAYMENT_SUCCESS_STATUSES = [
    "Received",
]

PAYMENT_NON_SUCCESS_STATUSES = [
    "Pending",
    "Failed",
    "Reversed",
]

CURRENCIES = [
    "GBP",
    "EUR",
    "USD",
    "INR",
]


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(value):
    """Safely return cleaned text."""

    if value is None:
        return ""

    return str(value).strip()


def safe_float(value):
    """Safely convert a value to float."""

    try:
        return float(value or 0)

    except (TypeError, ValueError):
        return 0.0


def get_client_name(client):
    """Return client company name safely."""

    if not client:
        return "Unknown Client"

    return (
        clean_text(
            getattr(
                client,
                "company_name",
                "",
            )
        )
        or "Unknown Client"
    )


def get_employee_name(employee):
    """Return employee full name safely."""

    if not employee:
        return "Unknown Employee"

    first_name = clean_text(
        getattr(
            employee,
            "first_name",
            "",
        )
    )

    last_name = clean_text(
        getattr(
            employee,
            "last_name",
            "",
        )
    )

    name = " ".join(
        part
        for part in [
            first_name,
            last_name,
        ]
        if part
    )

    return name or "Unknown Employee"


def get_job_label(job):
    """Return readable job label."""

    if not job:
        return "No Job"

    position = (
        clean_text(
            getattr(
                job,
                "position",
                "",
            )
        )
        or f"Job #{getattr(job, 'id', '?')}"
    )

    return position


def get_status(record):
    """Safely return a record status."""

    return (
        clean_text(
            getattr(
                record,
                "status",
                "",
            )
        )
        or "Unknown"
    )


def get_currency(record):
    """Safely return record currency."""

    return (
        clean_text(
            getattr(
                record,
                "currency",
                "",
            )
        )
        or "GBP"
    )


# ============================================================
# RELATIONSHIP HELPERS
# ============================================================

def get_client_id_from_job(job):
    """Safely return job client ID."""

    if not job:
        return None

    return getattr(
        job,
        "client_id",
        None,
    )


def get_client_id_from_candidate(candidate):
    """
    Safely determine candidate client through:

        Candidate -> Job -> Client
    """

    if not candidate:
        return None

    job = getattr(
        candidate,
        "job",
        None,
    )

    if job:
        return getattr(
            job,
            "client_id",
            None,
        )

    return None


def get_client_id_from_contract(contract):
    """
    Determine contract client.

    Supports:
        Contract.client_id
    and
        Contract.placement.client_id
    """

    if not contract:
        return None

    direct_client_id = getattr(
        contract,
        "client_id",
        None,
    )

    if direct_client_id:
        return direct_client_id

    placement = getattr(
        contract,
        "placement",
        None,
    )

    if placement:
        return getattr(
            placement,
            "client_id",
            None,
        )

    return None


def get_client_id_from_invoice(invoice):
    """
    Determine invoice client.

    Supports:
        Invoice.client_id
    and
        Invoice.placement.client_id
    """

    if not invoice:
        return None

    direct_client_id = getattr(
        invoice,
        "client_id",
        None,
    )

    if direct_client_id:
        return direct_client_id

    placement = getattr(
        invoice,
        "placement",
        None,
    )

    if placement:
        return getattr(
            placement,
            "client_id",
            None,
        )

    return None


def get_client_id_from_payment(
    payment,
):
    """
    Determine payment client through:

        Payment -> Invoice -> Client
    """

    if not payment:
        return None

    invoice = getattr(
        payment,
        "invoice",
        None,
    )

    if invoice:
        return get_client_id_from_invoice(
            invoice
        )

    return None


# ============================================================
# PLACEMENT FINANCIAL HELPERS
# ============================================================

def get_placement_client_fee(
    placement,
):
    """Return placement client fee."""

    return max(
        safe_float(
            getattr(
                placement,
                "client_monthly_fee",
                0,
            )
        ),
        0.0,
    )


def get_placement_worker_cost(
    placement,
):
    """Return placement worker cost."""

    return max(
        safe_float(
            getattr(
                placement,
                "worker_monthly_cost",
                0,
            )
        ),
        0.0,
    )


def get_placement_margin(
    placement,
):
    """Calculate placement gross margin."""

    return (
        get_placement_client_fee(
            placement
        )
        - get_placement_worker_cost(
            placement
        )
    )


def get_placement_margin_percentage(
    placement,
):
    """Calculate placement margin percentage."""

    revenue = get_placement_client_fee(
        placement
    )

    if revenue <= 0:
        return 0.0

    return (
        get_placement_margin(
            placement
        )
        / revenue
    ) * 100


# ============================================================
# INVOICE HELPERS
# ============================================================

def get_invoice_total(invoice):
    """Return invoice total."""

    for field in [
        "total",
        "total_amount",
        "grand_total",
        "amount",
    ]:

        if hasattr(
            invoice,
            field,
        ):

            value = safe_float(
                getattr(
                    invoice,
                    field,
                )
            )

            if value != 0:
                return value

    return 0.0


def get_invoice_paid(invoice):
    """Return invoice amount paid."""

    return max(
        safe_float(
            getattr(
                invoice,
                "amount_paid",
                0,
            )
        ),
        0.0,
    )


def get_invoice_balance(invoice):
    """Return invoice outstanding balance."""

    return max(
        get_invoice_total(
            invoice
        )
        - get_invoice_paid(
            invoice
        ),
        0.0,
    )


# ============================================================
# PAYMENT HELPERS
# ============================================================

def get_payment_amount(payment):
    """Return payment amount safely."""

    for field in [
        "amount",
        "payment_amount",
        "value",
    ]:

        if hasattr(
            payment,
            field,
        ):

            return max(
                safe_float(
                    getattr(
                        payment,
                        field,
                    )
                ),
                0.0,
            )

    return 0.0


# ============================================================
# AGGREGATION HELPERS
# ============================================================

def count_by_status(
    records,
):
    """Return status counts."""

    result = {}

    for record in records:

        status = get_status(
            record
        )

        result[status] = (
            result.get(
                status,
                0,
            )
            + 1
        )

    return result


def add_currency_value(
    totals,
    currency,
    value,
):
    """Add value while keeping currencies separate."""

    currency = (
        clean_text(currency)
        or "GBP"
    )

    totals[currency] = (
        totals.get(
            currency,
            0.0,
        )
        + safe_float(value)
    )


def format_currency_amounts(
    totals,
):
    """Format currency totals."""

    if not totals:
        return "0.00"

    parts = []

    for currency, amount in sorted(
        totals.items()
    ):

        parts.append(
            f"{currency} {amount:,.2f}"
        )

    return " | ".join(
        parts
    )


# ============================================================
# DATE HELPERS
# ============================================================

def format_date(value):
    """Format dates safely."""

    if not value:
        return "—"

    try:
        return value.strftime(
            "%d %b %Y"
        )

    except AttributeError:
        return clean_text(
            value
        )


# ============================================================
# FILTER HELPERS
# ============================================================

def matches_client(
    record_client_id,
    selected_client_id,
):
    """Return whether record matches selected client."""

    if selected_client_id is None:
        return True

    return (
        record_client_id
        == selected_client_id
    )


def matches_currency(
    record,
    currency_filter,
):
    """Return whether record matches currency filter."""

    if currency_filter == "All":
        return True

    return (
        get_currency(record)
        == currency_filter
    )


# ============================================================
# MAIN REPORTS SCREEN
# ============================================================

def show_reports():

    st.title(
        "Reports & Analytics"
    )

    st.caption(
        "Management reporting across clients, recruitment, "
        "placements, contracts, invoices and payments."
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
                Job.id.desc()
            )
            .all()
        )

        candidates = (
            session.query(Candidate)
            .order_by(
                Candidate.id.desc()
            )
            .all()
        )

        placements = (
            session.query(Placement)
            .order_by(
                Placement.id.desc()
            )
            .all()
        )

        contracts = (
            session.query(Contract)
            .order_by(
                Contract.id.desc()
            )
            .all()
        )

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
                Payment.id.desc()
            )
            .all()
        )

        # ====================================================
        # REPORT FILTERS
        # ====================================================

        st.subheader(
            "Report Filters"
        )

        filter_col1, filter_col2 = st.columns(
            2
        )

        client_filter_options = {
            "All Clients": None
        }

        for client in clients:

            client_filter_options[
                f"{get_client_name(client)} "
                f"(ID: {client.id})"
            ] = client.id

        with filter_col1:

            selected_client_label = st.selectbox(
                "Client",
                list(
                    client_filter_options.keys()
                ),
                key="reports_client_filter",
            )

        with filter_col2:

            selected_currency = st.selectbox(
                "Currency",
                [
                    "All",
                    *CURRENCIES,
                ],
                key="reports_currency_filter",
            )

        selected_client_id = (
            client_filter_options[
                selected_client_label
            ]
        )

        # ====================================================
        # FILTER RECORDS
        # ====================================================

        filtered_clients = [
            client
            for client in clients
            if (
                selected_client_id is None
                or client.id
                == selected_client_id
            )
        ]

        filtered_employees = employees

        filtered_jobs = [
            job
            for job in jobs
            if matches_client(
                get_client_id_from_job(job),
                selected_client_id,
            )
        ]

        filtered_candidates = [
            candidate
            for candidate in candidates
            if matches_client(
                get_client_id_from_candidate(
                    candidate
                ),
                selected_client_id,
            )
        ]

        filtered_placements = [
            placement
            for placement in placements
            if matches_client(
                getattr(
                    placement,
                    "client_id",
                    None,
                ),
                selected_client_id,
            )
            and matches_currency(
                placement,
                selected_currency,
            )
        ]

        filtered_contracts = [
            contract
            for contract in contracts
            if matches_client(
                get_client_id_from_contract(
                    contract
                ),
                selected_client_id,
            )
        ]

        filtered_invoices = [
            invoice
            for invoice in invoices
            if matches_client(
                get_client_id_from_invoice(
                    invoice
                ),
                selected_client_id,
            )
            and matches_currency(
                invoice,
                selected_currency,
            )
        ]

        filtered_payments = [
            payment
            for payment in payments
            if matches_client(
                get_client_id_from_payment(
                    payment
                ),
                selected_client_id,
            )
            and matches_currency(
                payment,
                selected_currency,
            )
        ]

        # ====================================================
        # FILTER SUMMARY
        # ====================================================

        if selected_client_id is not None:

            st.info(
                f"Reports filtered to: "
                f"**{selected_client_label.split(' (ID:')[0]}**"
            )

        if selected_currency != "All":

            st.info(
                f"Financial reports filtered to: "
                f"**{selected_currency}**"
            )

        # ====================================================
        # EXECUTIVE SUMMARY
        # ====================================================

        st.divider()

        st.subheader(
            "Executive Summary"
        )

        active_placements = [
            placement
            for placement in filtered_placements
            if get_status(
                placement
            ) == "Active"
        ]

        scheduled_placements = [
            placement
            for placement in filtered_placements
            if get_status(
                placement
            ) == "Scheduled"
        ]

        open_jobs = [
            job
            for job in filtered_jobs
            if get_status(
                job
            ) in JOB_OPEN_STATUSES
        ]

        open_invoices = [
            invoice
            for invoice in filtered_invoices
            if get_status(
                invoice
            ) in INVOICE_OPEN_STATUSES
        ]

        received_payments = [
            payment
            for payment in filtered_payments
            if get_status(
                payment
            ) in PAYMENT_SUCCESS_STATUSES
        ]

        outstanding_totals = {}

        for invoice in open_invoices:

            add_currency_value(
                outstanding_totals,
                get_currency(invoice),
                get_invoice_balance(
                    invoice
                ),
            )

        received_payment_totals = {}

        for payment in received_payments:

            add_currency_value(
                received_payment_totals,
                get_currency(payment),
                get_payment_amount(
                    payment
                ),
            )

        e1, e2, e3, e4, e5, e6 = st.columns(
            6
        )

        e1.metric(
            "Clients",
            len(
                filtered_clients
            ),
        )

        e2.metric(
            "Employees",
            len(
                filtered_employees
            ),
        )

        e3.metric(
            "Open Jobs",
            len(
                open_jobs
            ),
        )

        e4.metric(
            "Active Placements",
            len(
                active_placements
            ),
        )

        e5.metric(
            "Candidates",
            len(
                filtered_candidates
            ),
        )

        e6.metric(
            "Open Invoices",
            len(
                open_invoices
            ),
        )

        st.caption(
            "Financial values below remain separated by currency."
        )

        f1, f2, f3 = st.columns(3)

        with f1:

            st.write(
                "**Outstanding Invoice Balance**"
            )

            st.write(
                format_currency_amounts(
                    outstanding_totals
                )
            )

        with f2:

            st.write(
                "**Received Payments**"
            )

            st.write(
                format_currency_amounts(
                    received_payment_totals
                )
            )

        with f3:

            st.write(
                "**Active Placements**"
            )

            active_revenue = {}

            for placement in active_placements:

                add_currency_value(
                    active_revenue,
                    get_currency(
                        placement
                    ),
                    get_placement_client_fee(
                        placement
                    ),
                )

            st.write(
                format_currency_amounts(
                    active_revenue
                )
            )

        # ====================================================
        # TABS
        # ====================================================

        (
            tab_pipeline,
            tab_jobs,
            tab_placements,
            tab_financials,
            tab_contracts,
            tab_invoices,
            tab_payments,
            tab_clients,
            tab_quality,
        ) = st.tabs(
            [
                "Recruitment Pipeline",
                "Jobs",
                "Placements",
                "Financials",
                "Contracts",
                "Invoices",
                "Payments",
                "Client Performance",
                "Data Quality",
            ]
        )

        # ====================================================
        # RECRUITMENT PIPELINE
        # ====================================================

        with tab_pipeline:

            st.subheader(
                "Recruitment Pipeline"
            )

            candidate_statuses = count_by_status(
                filtered_candidates
            )

            submitted_count = (
                candidate_statuses.get(
                    "Submitted",
                    0,
                )
            )

            shortlisted_count = (
                candidate_statuses.get(
                    "Shortlisted",
                    0,
                )
            )

            interview_count = (
                candidate_statuses.get(
                    "Interview",
                    0,
                )
            )

            offer_count = (
                candidate_statuses.get(
                    "Offer",
                    0,
                )
            )

            placed_count = (
                candidate_statuses.get(
                    "Placed",
                    0,
                )
            )

            rejected_count = (
                candidate_statuses.get(
                    "Rejected",
                    0,
                )
            )

            withdrawn_count = (
                candidate_statuses.get(
                    "Withdrawn",
                    0,
                )
            )

            p1, p2, p3, p4 = st.columns(4)

            p1.metric(
                "Submitted",
                submitted_count,
            )

            p2.metric(
                "Shortlisted",
                shortlisted_count,
            )

            p3.metric(
                "Interview",
                interview_count,
            )

            p4.metric(
                "Offer",
                offer_count,
            )

            p5, p6, p7, p8 = st.columns(4)

            p5.metric(
                "Placed",
                placed_count,
            )

            p6.metric(
                "Rejected",
                rejected_count,
            )

            p7.metric(
                "Withdrawn",
                withdrawn_count,
            )

            p8.metric(
                "Total Candidates",
                len(
                    filtered_candidates
                ),
            )

            st.markdown(
                "### Candidate Status Breakdown"
            )

            if candidate_statuses:

                for status, count in sorted(
                    candidate_statuses.items()
                ):

                    st.write(
                        f"**{status}:** {count}"
                    )

            else:

                st.info(
                    "No candidates found for the selected filters."
                )

            st.markdown(
                "### Pipeline Placements"
            )

            pipeline_statuses = {}

            for placement in filtered_placements:

                status = get_status(
                    placement
                )

                if status in PLACEMENT_PIPELINE_STATUSES:

                    pipeline_statuses[
                        status
                    ] = (
                        pipeline_statuses.get(
                            status,
                            0,
                        )
                        + 1
                    )

            pp1, pp2 = st.columns(2)

            with pp1:

                pp1.metric(
                    "Active",
                    pipeline_statuses.get(
                        "Active",
                        0,
                    ),
                )

            with pp2:

                pp2.metric(
                    "Scheduled",
                    pipeline_statuses.get(
                        "Scheduled",
                        0,
                    ),
                )

        # ====================================================
        # JOB REPORT
        # ====================================================

        with tab_jobs:

            st.subheader(
                "Job Report"
            )

            job_statuses = count_by_status(
                filtered_jobs
            )

            j1, j2, j3 = st.columns(3)

            j1.metric(
                "Total Jobs",
                len(
                    filtered_jobs
                ),
            )

            j2.metric(
                "Open Jobs",
                sum(
                    1
                    for job in filtered_jobs
                    if get_status(job)
                    in JOB_OPEN_STATUSES
                ),
            )

            j3.metric(
                "Closed / Other",
                sum(
                    1
                    for job in filtered_jobs
                    if get_status(job)
                    not in JOB_OPEN_STATUSES
                ),
            )

            st.markdown(
                "### Job Status Breakdown"
            )

            if job_statuses:

                for status, count in sorted(
                    job_statuses.items()
                ):

                    st.write(
                        f"**{status}:** {count}"
                    )

            else:

                st.info(
                    "No jobs found for the selected client."
                )

            st.markdown(
                "### Job Register"
            )

            for job in filtered_jobs:

                job_position = (
                    clean_text(
                        getattr(
                            job,
                            "position",
                            "",
                        )
                    )
                    or f"Job #{job.id}"
                )

                client_name = get_client_name(
                    getattr(
                        job,
                        "client",
                        None,
                    )
                )

                status = get_status(
                    job
                )

                with st.container(
                    border=True
                ):

                    c1, c2, c3 = st.columns(3)

                    with c1:

                        st.write(
                            f"**#{job.id} — "
                            f"{job_position}**"
                        )

                        st.caption(
                            client_name
                        )

                    with c2:

                        st.write(
                            f"Status: **{status}**"
                        )

                        openings = getattr(
                            job,
                            "openings",
                            None,
                        )

                        if openings is not None:

                            st.caption(
                                f"Openings: {openings}"
                            )

                    with c3:

                        st.write(
                            "Recruitment activity"
                        )

                        job_candidate_count = sum(
                            1
                            for candidate
                            in filtered_candidates
                            if getattr(
                                candidate,
                                "job_id",
                                None,
                            )
                            == job.id
                        )

                        st.caption(
                            f"Candidates: "
                            f"{job_candidate_count}"
                        )

        # ====================================================
        # PLACEMENT REPORT
        # ====================================================

        with tab_placements:

            st.subheader(
                "Placement Report"
            )

            completed_placements = [
                placement
                for placement in filtered_placements
                if get_status(
                    placement
                ) == "Completed"
            ]

            terminated_placements = [
                placement
                for placement in filtered_placements
                if get_status(
                    placement
                ) == "Terminated"
            ]

            r1, r2, r3, r4 = st.columns(4)

            r1.metric(
                "Total",
                len(
                    filtered_placements
                ),
            )

            r2.metric(
                "Active",
                len(
                    active_placements
                ),
            )

            r3.metric(
                "Completed",
                len(
                    completed_placements
                ),
            )

            r4.metric(
                "Terminated",
                len(
                    terminated_placements
                ),
            )

            st.markdown(
                "### Placement Register"
            )

            if not filtered_placements:

                st.info(
                    "No placements found for the selected filters."
                )

            else:

                for placement in filtered_placements:

                    employee_name = get_employee_name(
                        getattr(
                            placement,
                            "employee",
                            None,
                        )
                    )

                    client_name = get_client_name(
                        getattr(
                            placement,
                            "client",
                            None,
                        )
                    )

                    status = get_status(
                        placement
                    )

                    currency = get_currency(
                        placement
                    )

                    revenue = (
                        get_placement_client_fee(
                            placement
                        )
                    )

                    cost = (
                        get_placement_worker_cost(
                            placement
                        )
                    )

                    margin = (
                        get_placement_margin(
                            placement
                        )
                    )

                    margin_percentage = (
                        get_placement_margin_percentage(
                            placement
                        )
                    )

                    with st.container(
                        border=True
                    ):

                        c1, c2, c3, c4 = st.columns(
                            4
                        )

                        with c1:

                            st.write(
                                f"**#{placement.id} — "
                                f"{clean_text(getattr(placement, 'position', ''))}**"
                            )

                            st.caption(
                                employee_name
                            )

                        with c2:

                            st.write(
                                f"Client: **{client_name}**"
                            )

                            st.caption(
                                f"Status: {status}"
                            )

                        with c3:

                            st.write(
                                f"Revenue: **"
                                f"{currency} "
                                f"{revenue:,.2f}**"
                            )

                            st.caption(
                                f"Cost: {currency} "
                                f"{cost:,.2f}"
                            )

                        with c4:

                            st.write(
                                f"Margin: **"
                                f"{currency} "
                                f"{margin:,.2f}**"
                            )

                            st.caption(
                                f"{margin_percentage:.1f}%"
                            )

        # ====================================================
        # FINANCIAL REPORTS
        # ====================================================

        with tab_financials:

            st.subheader(
                "Placement Financials"
            )

            revenue_totals = {}

            cost_totals = {}

            margin_totals = {}

            for placement in active_placements:

                currency = get_currency(
                    placement
                )

                revenue = (
                    get_placement_client_fee(
                        placement
                    )
                )

                cost = (
                    get_placement_worker_cost(
                        placement
                    )
                )

                margin = (
                    get_placement_margin(
                        placement
                    )
                )

                add_currency_value(
                    revenue_totals,
                    currency,
                    revenue,
                )

                add_currency_value(
                    cost_totals,
                    currency,
                    cost,
                )

                add_currency_value(
                    margin_totals,
                    currency,
                    margin,
                )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.write(
                    "**Active Client Revenue**"
                )

                st.write(
                    format_currency_amounts(
                        revenue_totals
                    )
                )

            with c2:

                st.write(
                    "**Active Worker Cost**"
                )

                st.write(
                    format_currency_amounts(
                        cost_totals
                    )
                )

            with c3:

                st.write(
                    "**Active Gross Margin**"
                )

                st.write(
                    format_currency_amounts(
                        margin_totals
                    )
                )

            st.markdown(
                "### Margin by Placement"
            )

            for placement in active_placements:

                margin = get_placement_margin(
                    placement
                )

                margin_percentage = (
                    get_placement_margin_percentage(
                        placement
                    )
                )

                currency = get_currency(
                    placement
                )

                employee_name = get_employee_name(
                    getattr(
                        placement,
                        "employee",
                        None,
                    )
                )

                st.write(
                    f"**#{placement.id} "
                    f"{employee_name}** — "
                    f"{currency} {margin:,.2f} "
                    f"({margin_percentage:.1f}%)"
                )

            st.markdown(
                "### Invoice Outstanding Balance"
            )

            invoice_balance_totals = {}

            invoice_total_totals = {}

            invoice_paid_totals = {}

            for invoice in filtered_invoices:

                currency = get_currency(
                    invoice
                )

                total = get_invoice_total(
                    invoice
                )

                paid = get_invoice_paid(
                    invoice
                )

                balance = get_invoice_balance(
                    invoice
                )

                add_currency_value(
                    invoice_total_totals,
                    currency,
                    total,
                )

                add_currency_value(
                    invoice_paid_totals,
                    currency,
                    paid,
                )

                add_currency_value(
                    invoice_balance_totals,
                    currency,
                    balance,
                )

            i1, i2, i3 = st.columns(3)

            with i1:

                st.write(
                    "**Invoice Total**"
                )

                st.write(
                    format_currency_amounts(
                        invoice_total_totals
                    )
                )

            with i2:

                st.write(
                    "**Amount Paid**"
                )

                st.write(
                    format_currency_amounts(
                        invoice_paid_totals
                    )
                )

            with i3:

                st.write(
                    "**Outstanding**"
                )

                st.write(
                    format_currency_amounts(
                        invoice_balance_totals
                    )
                )

        # ====================================================
        # CONTRACT REPORT
        # ====================================================

        with tab_contracts:

            st.subheader(
                "Contract Report"
            )

            contract_statuses = count_by_status(
                filtered_contracts
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Total Contracts",
                len(
                    filtered_contracts
                ),
            )

            c2.metric(
                "Active",
                contract_statuses.get(
                    "Active",
                    0,
                ),
            )

            c3.metric(
                "Signed",
                contract_statuses.get(
                    "Signed",
                    0,
                ),
            )

            c4.metric(
                "Expired",
                contract_statuses.get(
                    "Expired",
                    0,
                ),
            )

            st.markdown(
                "### Contract Status Breakdown"
            )

            if contract_statuses:

                for status, count in sorted(
                    contract_statuses.items()
                ):

                    st.write(
                        f"**{status}:** {count}"
                    )

            else:

                st.info(
                    "No contracts found for the selected client."
                )

            st.markdown(
                "### Contract Register"
            )

            for contract in filtered_contracts:

                contract_number = clean_text(
                    getattr(
                        contract,
                        "contract_number",
                        "",
                    )
                )

                contract_type = clean_text(
                    getattr(
                        contract,
                        "contract_type",
                        "",
                    )
                )

                status = get_status(
                    contract
                )

                start_date = getattr(
                    contract,
                    "start_date",
                    None,
                )

                end_date = getattr(
                    contract,
                    "end_date",
                    None,
                )

                with st.container(
                    border=True
                ):

                    st.write(
                        f"**{contract_number or f'Contract #{contract.id}'}**"
                    )

                    st.caption(
                        f"Type: "
                        f"{contract_type or 'Not specified'}"
                    )

                    st.write(
                        f"Status: **{status}**"
                    )

                    st.caption(
                        f"Start: {format_date(start_date)} "
                        f"| End: {format_date(end_date)}"
                    )

        # ====================================================
        # INVOICE REPORT
        # ====================================================

        with tab_invoices:

            st.subheader(
                "Invoice Report"
            )

            invoice_statuses = count_by_status(
                filtered_invoices
            )

            total_invoice_value = {}

            paid_invoice_value = {}

            outstanding_invoice_value = {}

            for invoice in filtered_invoices:

                currency = get_currency(
                    invoice
                )

                add_currency_value(
                    total_invoice_value,
                    currency,
                    get_invoice_total(
                        invoice
                    ),
                )

                add_currency_value(
                    paid_invoice_value,
                    currency,
                    get_invoice_paid(
                        invoice
                    ),
                )

                add_currency_value(
                    outstanding_invoice_value,
                    currency,
                    get_invoice_balance(
                        invoice
                    ),
                )

            inv1, inv2, inv3 = st.columns(3)

            inv1.metric(
                "Invoices",
                len(
                    filtered_invoices
                ),
            )

            inv2.metric(
                "Open",
                len(
                    open_invoices
                ),
            )

            inv3.metric(
                "Statuses",
                len(
                    invoice_statuses
                ),
            )

            st.markdown(
                "### Invoice Values"
            )

            ic1, ic2, ic3 = st.columns(3)

            with ic1:

                st.write(
                    "**Invoice Value**"
                )

                st.write(
                    format_currency_amounts(
                        total_invoice_value
                    )
                )

            with ic2:

                st.write(
                    "**Paid**"
                )

                st.write(
                    format_currency_amounts(
                        paid_invoice_value
                    )
                )

            with ic3:

                st.write(
                    "**Outstanding**"
                )

                st.write(
                    format_currency_amounts(
                        outstanding_invoice_value
                    )
                )

            st.markdown(
                "### Invoice Status Breakdown"
            )

            for status, count in sorted(
                invoice_statuses.items()
            ):

                st.write(
                    f"**{status}:** {count}"
                )

            st.markdown(
                "### Invoice Register"
            )

            for invoice in filtered_invoices:

                invoice_number = clean_text(
                    getattr(
                        invoice,
                        "invoice_number",
                        "",
                    )
                )

                currency = get_currency(
                    invoice
                )

                total = get_invoice_total(
                    invoice
                )

                paid = get_invoice_paid(
                    invoice
                )

                balance = get_invoice_balance(
                    invoice
                )

                with st.container(
                    border=True
                ):

                    c1, c2, c3, c4 = st.columns(4)

                    with c1:

                        st.write(
                            f"**{invoice_number or f'Invoice #{invoice.id}'}**"
                        )

                        st.caption(
                            f"Status: {get_status(invoice)}"
                        )

                    with c2:

                        st.write(
                            f"Total: **{currency} "
                            f"{total:,.2f}**"
                        )

                    with c3:

                        st.write(
                            f"Paid: **{currency} "
                            f"{paid:,.2f}**"
                        )

                    with c4:

                        st.write(
                            f"Balance: **{currency} "
                            f"{balance:,.2f}**"
                        )

        # ====================================================
        # PAYMENT REPORT
        # ====================================================

        with tab_payments:

            st.subheader(
                "Payment Report"
            )

            received_payments = [
                payment
                for payment in filtered_payments
                if get_status(payment)
                in PAYMENT_SUCCESS_STATUSES
            ]

            non_received_payments = [
                payment
                for payment in filtered_payments
                if get_status(payment)
                in PAYMENT_NON_SUCCESS_STATUSES
            ]

            received_totals = {}

            non_received_totals = {}

            for payment in received_payments:

                add_currency_value(
                    received_totals,
                    get_currency(payment),
                    get_payment_amount(payment),
                )

            for payment in non_received_payments:

                add_currency_value(
                    non_received_totals,
                    get_currency(payment),
                    get_payment_amount(payment),
                )

            pm1, pm2, pm3 = st.columns(3)

            pm1.metric(
                "Total Payment Records",
                len(
                    filtered_payments
                ),
            )

            pm2.metric(
                "Received",
                len(
                    received_payments
                ),
            )

            pm3.metric(
                "Pending / Failed / Reversed",
                len(
                    non_received_payments
                ),
            )

            st.markdown(
                "### Payment Values"
            )

            pc1, pc2 = st.columns(2)

            with pc1:

                st.write(
                    "**Received Value**"
                )

                st.write(
                    format_currency_amounts(
                        received_totals
                    )
                )

            with pc2:

                st.write(
                    "**Non-Received Value**"
                )

                st.write(
                    format_currency_amounts(
                        non_received_totals
                    )
                )

            payment_statuses = count_by_status(
                filtered_payments
            )

            st.markdown(
                "### Payment Status Breakdown"
            )

            for status, count in sorted(
                payment_statuses.items()
            ):

                st.write(
                    f"**{status}:** {count}"
                )

            st.markdown(
                "### Payment Register"
            )

            for payment in filtered_payments:

                amount = get_payment_amount(
                    payment
                )

                currency = get_currency(
                    payment
                )

                reference = clean_text(
                    getattr(
                        payment,
                        "reference",
                        "",
                    )
                )

                payment_date = getattr(
                    payment,
                    "payment_date",
                    None,
                )

                with st.container(
                    border=True
                ):

                    c1, c2, c3, c4 = st.columns(4)

                    with c1:

                        st.write(
                            f"**Payment #{payment.id}**"
                        )

                        st.caption(
                            f"Status: {get_status(payment)}"
                        )

                    with c2:

                        st.write(
                            f"Amount: **{currency} "
                            f"{amount:,.2f}**"
                        )

                    with c3:

                        st.write(
                            f"Date: "
                            f"{format_date(payment_date)}"
                        )

                    with c4:

                        st.write(
                            f"Reference: "
                            f"{reference or '—'}"
                        )

        # ====================================================
        # CLIENT PERFORMANCE
        # ====================================================

        with tab_clients:

            st.subheader(
                "Client Performance"
            )

            if not filtered_clients:

                st.info(
                    "No clients found."
                )

            else:

                for client in filtered_clients:

                    client_id = client.id

                    client_jobs = [
                        job
                        for job in filtered_jobs
                        if get_client_id_from_job(job)
                        == client_id
                    ]

                    client_candidates = [
                        candidate
                        for candidate
                        in filtered_candidates
                        if get_client_id_from_candidate(
                            candidate
                        )
                        == client_id
                    ]

                    client_placements = [
                        placement
                        for placement
                        in filtered_placements
                        if getattr(
                            placement,
                            "client_id",
                            None,
                        )
                        == client_id
                    ]

                    client_invoices = [
                        invoice
                        for invoice
                        in filtered_invoices
                        if get_client_id_from_invoice(
                            invoice
                        )
                        == client_id
                    ]

                    client_active_placements = [
                        placement
                        for placement
                        in client_placements
                        if get_status(
                            placement
                        ) == "Active"
                    ]

                    client_revenue = {}

                    client_margin = {}

                    for placement in client_active_placements:

                        currency = get_currency(
                            placement
                        )

                        add_currency_value(
                            client_revenue,
                            currency,
                            get_placement_client_fee(
                                placement
                            ),
                        )

                        add_currency_value(
                            client_margin,
                            currency,
                            get_placement_margin(
                                placement
                            ),
                        )

                    client_outstanding = {}

                    for invoice in client_invoices:

                        add_currency_value(
                            client_outstanding,
                            get_currency(invoice),
                            get_invoice_balance(invoice),
                        )

                    with st.container(
                        border=True
                    ):

                        st.markdown(
                            f"### {get_client_name(client)}"
                        )

                        c1, c2, c3, c4 = st.columns(4)

                        c1.metric(
                            "Jobs",
                            len(
                                client_jobs
                            ),
                        )

                        c2.metric(
                            "Candidates",
                            len(
                                client_candidates
                            ),
                        )

                        c3.metric(
                            "Active Placements",
                            len(
                                client_active_placements
                            ),
                        )

                        c4.metric(
                            "Invoices",
                            len(
                                client_invoices
                            ),
                        )

                        st.write(
                            "**Active Placement Revenue:** "
                            f"{format_currency_amounts(client_revenue)}"
                        )

                        st.write(
                            "**Active Placement Margin:** "
                            f"{format_currency_amounts(client_margin)}"
                        )

                        st.write(
                            "**Outstanding Invoices:** "
                            f"{format_currency_amounts(client_outstanding)}"
                        )

        # ====================================================
        # DATA QUALITY
        # ====================================================

        with tab_quality:

            st.subheader(
                "Data Quality Checks"
            )

            quality_issues = []

            # -----------------------------------------------
            # Jobs without client
            # -----------------------------------------------

            for job in jobs:

                if getattr(
                    job,
                    "client_id",
                    None,
                ) is None:

                    quality_issues.append(
                        f"Job #{job.id} has no client."
                    )

            # -----------------------------------------------
            # Placements without client
            # -----------------------------------------------

            for placement in placements:

                if getattr(
                    placement,
                    "client_id",
                    None,
                ) is None:

                    quality_issues.append(
                        f"Placement #{placement.id} has no client."
                    )

                if getattr(
                    placement,
                    "employee_id",
                    None,
                ) is None:

                    quality_issues.append(
                        f"Placement #{placement.id} has no employee."
                    )

                if not clean_text(
                    getattr(
                        placement,
                        "position",
                        "",
                    )
                ):

                    quality_issues.append(
                        f"Placement #{placement.id} has no position."
                    )

                if (
                    getattr(
                        placement,
                        "start_date",
                        None,
                    )
                    and getattr(
                        placement,
                        "end_date",
                        None,
                    )
                    and placement.end_date
                    < placement.start_date
                ):

                    quality_issues.append(
                        f"Placement #{placement.id} has an "
                        "end date before its start date."
                    )

                if (
                    get_placement_client_fee(
                        placement
                    )
                    < get_placement_worker_cost(
                        placement
                    )
                ):

                    quality_issues.append(
                        f"Placement #{placement.id} has a "
                        "negative gross margin."
                    )

            # -----------------------------------------------
            # Candidates without employee/job
            # -----------------------------------------------

            for candidate in candidates:

                if getattr(
                    candidate,
                    "employee_id",
                    None,
                ) is None:

                    quality_issues.append(
                        f"Candidate #{candidate.id} has no employee."
                    )

                if getattr(
                    candidate,
                    "job_id",
                    None,
                ) is None:

                    quality_issues.append(
                        f"Candidate #{candidate.id} has no job."
                    )

            # -----------------------------------------------
            # Invoice balance checks
            # -----------------------------------------------

            for invoice in invoices:

                total = get_invoice_total(
                    invoice
                )

                paid = get_invoice_paid(
                    invoice
                )

                if paid > total and total >= 0:

                    quality_issues.append(
                        f"Invoice #{invoice.id} appears to be "
                        "overpaid."
                    )

            # -----------------------------------------------
            # Payment checks
            # -----------------------------------------------

            for payment in payments:

                amount = get_payment_amount(
                    payment
                )

                if amount <= 0:

                    quality_issues.append(
                        f"Payment #{payment.id} has a "
                        "zero or negative amount."
                    )

                if getattr(
                    payment,
                    "invoice_id",
                    None,
                ) is None:

                    quality_issues.append(
                        f"Payment #{payment.id} has no invoice."
                    )

            # -----------------------------------------------
            # Summary
            # -----------------------------------------------

            q1, q2 = st.columns(2)

            q1.metric(
                "Issues Found",
                len(
                    quality_issues
                ),
            )

            q2.metric(
                "Status",
                "Review Required"
                if quality_issues
                else "OK",
            )

            if quality_issues:

                st.warning(
                    "The following records may require review."
                )

                for issue in quality_issues:

                    st.write(
                        f"⚠️ {issue}"
                    )

            else:

                st.success(
                    "No basic data-quality issues were detected."
                )

        # ====================================================
        # REPORT NOTES
        # ====================================================

        st.divider()

        st.caption(
            "Reports are read-only and do not modify CRM records."
        )

        st.caption(
            "Financial values are deliberately kept separate "
            "by currency. GBP, EUR, USD and INR are not added together."
        )

        st.caption(
            "Client filtering is applied where the underlying "
            "record can be linked reliably to a client."
        )

    except Exception as exc:

        session.rollback()

        st.error(
            "An error occurred while generating the reports."
        )

        st.exception(
            exc
        )

    finally:

        session.close()