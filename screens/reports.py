import csv
import io
from datetime import date, timedelta

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

PLACEMENT_COMPLETED_STATUSES = [
    "Completed",
    "Terminated",
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

REPORT_PERIODS = [
    "All Time",
    "This Month",
    "Last 30 Days",
    "Last 90 Days",
    "This Year",
    "Custom",
]

DATA_QUALITY_LEVELS = [
    "All",
    "Issues Only",
    "Clean Only",
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


def safe_int(value):
    """Safely convert a value to integer."""

    try:
        return int(value or 0)

    except (TypeError, ValueError):
        return 0


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


def format_percentage(value):
    """Format percentage."""

    return f"{safe_float(value):.1f}%"


def format_number(value):
    """Format number safely."""

    return f"{safe_float(value):,.2f}"


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

    direct_client_id = getattr(
        candidate,
        "client_id",
        None,
    )

    if direct_client_id:
        return direct_client_id

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


def get_client_id_from_payment(payment):
    """
    Determine payment client through:

        Payment -> Invoice -> Client
    """

    if not payment:
        return None

    direct_client_id = getattr(
        payment,
        "client_id",
        None,
    )

    if direct_client_id:
        return direct_client_id

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


def get_placement_job(placement):
    """Return placement job safely."""

    return getattr(
        placement,
        "job",
        None,
    )


def get_placement_client(placement):
    """Return placement client safely."""

    return getattr(
        placement,
        "client",
        None,
    )


def get_placement_employee(placement):
    """Return placement employee safely."""

    return getattr(
        placement,
        "employee",
        None,
    )


# ============================================================
# PLACEMENT FINANCIAL HELPERS
# ============================================================

def get_placement_client_fee(placement):
    """Return placement client monthly fee."""

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


def get_placement_worker_cost(placement):
    """Return placement worker monthly cost."""

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


def get_placement_margin(placement):
    """Calculate placement gross margin."""

    return (
        get_placement_client_fee(
            placement
        )
        - get_placement_worker_cost(
            placement
        )
    )


def get_placement_margin_percentage(placement):
    """Calculate placement gross margin percentage."""

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


def get_margin_status(placement):
    """Return placement margin classification."""

    margin = get_placement_margin(
        placement
    )

    revenue = get_placement_client_fee(
        placement
    )

    if revenue <= 0:
        return "No Revenue"

    if margin < 0:
        return "Negative"

    if margin == 0:
        return "Break-even"

    return "Positive"


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

    stored_balance = getattr(
        invoice,
        "balance_due",
        None,
    )

    if stored_balance is not None:

        return max(
            safe_float(
                stored_balance
            ),
            0.0,
        )

    return max(
        get_invoice_total(
            invoice
        )
        - get_invoice_paid(
            invoice
        ),
        0.0,
    )


def get_invoice_date(invoice):
    """
    Safely determine the most relevant invoice date.

    Supports common invoice date fields.
    """

    for field in [
        "invoice_date",
        "issue_date",
        "date_issued",
        "date",
        "due_date",
    ]:

        value = getattr(
            invoice,
            field,
            None,
        )

        if value:
            return value

    return None


def get_invoice_due_date(invoice):
    """Return invoice due date safely."""

    for field in [
        "due_date",
        "payment_due_date",
    ]:

        value = getattr(
            invoice,
            field,
            None,
        )

        if value:
            return value

    return None


def get_invoice_age_days(invoice):
    """Calculate invoice age."""

    invoice_date = get_invoice_date(
        invoice
    )

    if not invoice_date:
        return None

    try:

        return max(
            (
                date.today()
                - invoice_date
            ).days,
            0,
        )

    except TypeError:

        return None


def get_invoice_overdue_days(invoice):
    """Calculate overdue days."""

    due_date = get_invoice_due_date(
        invoice
    )

    if not due_date:
        return 0

    if get_invoice_balance(
        invoice
    ) <= 0:
        return 0

    try:

        return max(
            (
                date.today()
                - due_date
            ).days,
            0,
        )

    except TypeError:

        return 0


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


def get_payment_date(payment):
    """Return payment date safely."""

    for field in [
        "payment_date",
        "date_received",
        "received_date",
        "date",
    ]:

        value = getattr(
            payment,
            field,
            None,
        )

        if value:
            return value

    return None


# ============================================================
# AGGREGATION HELPERS
# ============================================================

def count_by_status(records):
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
        + safe_float(
            value
        )
    )


def format_currency_amounts(totals):
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


def get_currency_totals(
    records,
    value_function,
):
    """Create currency totals from records."""

    totals = {}

    for record in records:

        add_currency_value(
            totals,
            get_currency(record),
            value_function(record),
        )

    return totals


# ============================================================
# DATE FILTER HELPERS
# ============================================================

def get_record_date(
    record,
    fields,
):
    """Return first available date from a list of fields."""

    for field in fields:

        value = getattr(
            record,
            field,
            None,
        )

        if value:
            return value

    return None


def date_in_period(
    record,
    period,
    fields,
    custom_start=None,
    custom_end=None,
):
    """Determine whether record date belongs to report period."""

    if period == "All Time":
        return True

    record_date = get_record_date(
        record,
        fields,
    )

    if not record_date:
        return period == "All Time"

    today = date.today()

    if period == "This Month":

        return (
            record_date.year == today.year
            and record_date.month == today.month
        )

    if period == "Last 30 Days":

        return (
            today - timedelta(days=30)
            <= record_date
            <= today
        )

    if period == "Last 90 Days":

        return (
            today - timedelta(days=90)
            <= record_date
            <= today
        )

    if period == "This Year":

        return (
            record_date.year
            == today.year
        )

    if period == "Custom":

        if not custom_start or not custom_end:
            return True

        return (
            custom_start
            <= record_date
            <= custom_end
        )

    return True


# ============================================================
# DATA QUALITY HELPERS
# ============================================================

def get_placement_quality_issues(
    placement,
):
    """Return data-quality issues for a placement."""

    issues = []

    client_id = getattr(
        placement,
        "client_id",
        None,
    )

    employee_id = getattr(
        placement,
        "employee_id",
        None,
    )

    position = clean_text(
        getattr(
            placement,
            "position",
            "",
        )
    )

    start_date = getattr(
        placement,
        "start_date",
        None,
    )

    end_date = getattr(
        placement,
        "end_date",
        None,
    )

    status = get_status(
        placement
    )

    client_fee = get_placement_client_fee(
        placement
    )

    worker_cost = get_placement_worker_cost(
        placement
    )

    job = get_placement_job(
        placement
    )

    employee = get_placement_employee(
        placement
    )

    if client_id is None:
        issues.append(
            "No client linked."
        )

    if employee_id is None:
        issues.append(
            "No employee linked."
        )

    if not position:
        issues.append(
            "No position recorded."
        )

    if not start_date:
        issues.append(
            "No start date."
        )

    if (
        start_date
        and end_date
        and end_date < start_date
    ):
        issues.append(
            "End date is before start date."
        )

    if (
        status == "Active"
        and start_date
        and start_date > date.today()
    ):
        issues.append(
            "Active placement has a future start date."
        )

    if (
        status == "Scheduled"
        and start_date
        and start_date <= date.today()
    ):
        issues.append(
            "Scheduled placement has already reached its start date."
        )

    if (
        status == "Active"
        and end_date
        and end_date < date.today()
    ):
        issues.append(
            "Active placement has already ended."
        )

    if (
        status in PLACEMENT_COMPLETED_STATUSES
        and not end_date
    ):
        issues.append(
            "Completed/terminated placement has no end date."
        )

    if (
        status in PLACEMENT_COMPLETED_STATUSES
        and end_date
        and end_date > date.today()
    ):
        issues.append(
            "Completed/terminated placement has a future end date."
        )

    if client_fee <= 0:
        issues.append(
            "Client monthly fee is zero."
        )

    if worker_cost < 0:
        issues.append(
            "Worker cost is negative."
        )

    if client_fee > 0 and worker_cost > client_fee:
        issues.append(
            "Gross margin is negative."
        )

    if job:

        job_client_id = getattr(
            job,
            "client_id",
            None,
        )

        if (
            job_client_id is not None
            and client_id is not None
            and job_client_id
            != client_id
        ):
            issues.append(
                "Placement client does not match job client."
            )

        job_status = get_status(
            job
        )

        if (
            status in PLACEMENT_PIPELINE_STATUSES
            and job_status == "Cancelled"
        ):
            issues.append(
                "Placement is linked to a cancelled job."
            )

    if employee:

        employee_status = get_status(
            employee
        )

        if employee_status in [
            "Former Employee",
            "Unavailable",
        ]:
            issues.append(
                f"Employee status is {employee_status}."
            )

    return issues


def get_quality_issues_for_record(
    record_type,
    record,
):
    """Generic quality helper."""

    if record_type == "placement":
        return get_placement_quality_issues(
            record
        )

    return []


# ============================================================
# CSV EXPORT HELPERS
# ============================================================

def build_placement_csv(
    placements,
):
    """Build placement CSV."""

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow(
        [
            "Placement ID",
            "Client",
            "Employee",
            "Job",
            "Position",
            "Status",
            "Start Date",
            "End Date",
            "Currency",
            "Billing Frequency",
            "Client Monthly Fee",
            "Worker Monthly Cost",
            "Gross Margin",
            "Margin %",
            "Margin Status",
            "Data Quality Issues",
        ]
    )

    for placement in placements:

        client = get_placement_client(
            placement
        )

        employee = get_placement_employee(
            placement
        )

        job = get_placement_job(
            placement
        )

        issues = get_placement_quality_issues(
            placement
        )

        writer.writerow(
            [
                getattr(
                    placement,
                    "id",
                    "",
                ),
                get_client_name(client),
                get_employee_name(employee),
                get_job_label(job),
                clean_text(
                    getattr(
                        placement,
                        "position",
                        "",
                    )
                ),
                get_status(placement),
                format_date(
                    getattr(
                        placement,
                        "start_date",
                        None,
                    )
                ),
                format_date(
                    getattr(
                        placement,
                        "end_date",
                        None,
                    )
                ),
                get_currency(placement),
                clean_text(
                    getattr(
                        placement,
                        "billing_frequency",
                        "",
                    )
                ),
                f"{get_placement_client_fee(placement):.2f}",
                f"{get_placement_worker_cost(placement):.2f}",
                f"{get_placement_margin(placement):.2f}",
                f"{get_placement_margin_percentage(placement):.2f}",
                get_margin_status(placement),
                " | ".join(issues),
            ]
        )

    return output.getvalue()


def build_invoice_csv(
    invoices,
):
    """Build invoice CSV."""

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow(
        [
            "Invoice ID",
            "Invoice Number",
            "Client",
            "Status",
            "Currency",
            "Invoice Total",
            "Amount Paid",
            "Outstanding",
            "Invoice Date",
            "Due Date",
            "Age Days",
            "Overdue Days",
        ]
    )

    for invoice in invoices:

        client_id = get_client_id_from_invoice(
            invoice
        )

        client = getattr(
            invoice,
            "client",
            None,
        )

        if not client and client_id:
            client = None

        writer.writerow(
            [
                getattr(
                    invoice,
                    "id",
                    "",
                ),
                clean_text(
                    getattr(
                        invoice,
                        "invoice_number",
                        "",
                    )
                ),
                get_client_name(client),
                get_status(invoice),
                get_currency(invoice),
                f"{get_invoice_total(invoice):.2f}",
                f"{get_invoice_paid(invoice):.2f}",
                f"{get_invoice_balance(invoice):.2f}",
                format_date(
                    get_invoice_date(invoice)
                ),
                format_date(
                    get_invoice_due_date(invoice)
                ),
                get_invoice_age_days(invoice)
                if get_invoice_age_days(invoice)
                is not None
                else "",
                get_invoice_overdue_days(
                    invoice
                ),
            ]
        )

    return output.getvalue()


def build_payment_csv(
    payments,
):
    """Build payment CSV."""

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow(
        [
            "Payment ID",
            "Invoice ID",
            "Status",
            "Currency",
            "Amount",
            "Payment Date",
            "Reference",
        ]
    )

    for payment in payments:

        writer.writerow(
            [
                getattr(
                    payment,
                    "id",
                    "",
                ),
                getattr(
                    payment,
                    "invoice_id",
                    "",
                ),
                get_status(payment),
                get_currency(payment),
                f"{get_payment_amount(payment):.2f}",
                format_date(
                    get_payment_date(payment)
                ),
                clean_text(
                    getattr(
                        payment,
                        "reference",
                        "",
                    )
                ),
            ]
        )

    return output.getvalue()


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
        "AVERRA management dashboard covering "
        "clients, recruitment, placements, contracts, "
        "invoices, payments and data quality."
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

        filter_col1, filter_col2, filter_col3 = st.columns(
            3
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

        with filter_col3:

            selected_period = st.selectbox(
                "Report Period",
                REPORT_PERIODS,
                key="reports_period_filter",
            )

        selected_client_id = (
            client_filter_options[
                selected_client_label
            ]
        )

        custom_start = None
        custom_end = None

        if selected_period == "Custom":

            date_col1, date_col2 = st.columns(2)

            with date_col1:

                custom_start = st.date_input(
                    "Start Date",
                    value=date.today()
                    - timedelta(days=30),
                    key="reports_custom_start",
                )

            with date_col2:

                custom_end = st.date_input(
                    "End Date",
                    value=date.today(),
                    key="reports_custom_end",
                )

            if custom_start > custom_end:

                st.warning(
                    "Custom start date cannot be after "
                    "the custom end date."
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

        if selected_client_id is None:

            filtered_employees = employees

        else:

            employee_ids = {
                getattr(
                    placement,
                    "employee_id",
                    None,
                )
                for placement in placements
                if getattr(
                    placement,
                    "client_id",
                    None,
                )
                == selected_client_id
            }

            filtered_employees = [
                employee
                for employee in employees
                if employee.id
                in employee_ids
            ]

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
            and date_in_period(
                placement,
                selected_period,
                [
                    "start_date",
                    "created_at",
                ],
                custom_start,
                custom_end,
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
            and date_in_period(
                contract,
                selected_period,
                [
                    "start_date",
                    "signed_date",
                    "created_at",
                ],
                custom_start,
                custom_end,
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
            and date_in_period(
                invoice,
                selected_period,
                [
                    "invoice_date",
                    "issue_date",
                    "date_issued",
                    "date",
                    "due_date",
                    "created_at",
                ],
                custom_start,
                custom_end,
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
            and date_in_period(
                payment,
                selected_period,
                [
                    "payment_date",
                    "date_received",
                    "received_date",
                    "date",
                    "created_at",
                ],
                custom_start,
                custom_end,
            )
        ]

        # ====================================================
        # FILTER SUMMARY
        # ====================================================

        active_filter_count = 0

        if selected_client_id is not None:
            active_filter_count += 1

        if selected_currency != "All":
            active_filter_count += 1

        if selected_period != "All Time":
            active_filter_count += 1

        if active_filter_count:

            filter_parts = []

            if selected_client_id is not None:
                filter_parts.append(
                    selected_client_label.split(
                        " (ID:"
                    )[0]
                )

            if selected_currency != "All":
                filter_parts.append(
                    selected_currency
                )

            if selected_period != "All Time":
                filter_parts.append(
                    selected_period
                )

            st.info(
                " | ".join(
                    filter_parts
                )
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

        overdue_invoices = [
            invoice
            for invoice in filtered_invoices
            if (
                get_status(invoice)
                == "Overdue"
                or get_invoice_overdue_days(
                    invoice
                ) > 0
            )
        ]

        received_payments = [
            payment
            for payment in filtered_payments
            if get_status(
                payment
            ) in PAYMENT_SUCCESS_STATUSES
        ]

        outstanding_totals = (
            get_currency_totals(
                open_invoices,
                get_invoice_balance,
            )
        )

        received_payment_totals = (
            get_currency_totals(
                received_payments,
                get_payment_amount,
            )
        )

        active_revenue_totals = (
            get_currency_totals(
                active_placements,
                get_placement_client_fee,
            )
        )

        active_cost_totals = (
            get_currency_totals(
                active_placements,
                get_placement_worker_cost,
            )
        )

        active_margin_totals = (
            get_currency_totals(
                active_placements,
                get_placement_margin,
            )
        )

        negative_margin_placements = [
            placement
            for placement in filtered_placements
            if get_placement_margin(
                placement
            ) < 0
        ]

        quality_issue_count = sum(
            len(
                get_placement_quality_issues(
                    placement
                )
            )
            for placement in placements
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

        f1, f2, f3, f4 = st.columns(4)

        with f1:

            st.write(
                "**Active Monthly Revenue**"
            )

            st.write(
                format_currency_amounts(
                    active_revenue_totals
                )
            )

        with f2:

            st.write(
                "**Active Monthly Cost**"
            )

            st.write(
                format_currency_amounts(
                    active_cost_totals
                )
            )

        with f3:

            st.write(
                "**Active Gross Margin**"
            )

            st.write(
                format_currency_amounts(
                    active_margin_totals
                )
            )

        with f4:

            st.write(
                "**Outstanding Invoices**"
            )

            st.write(
                format_currency_amounts(
                    outstanding_totals
                )
            )

        st.caption(
            f"Received payments: "
            f"{format_currency_amounts(received_payment_totals)}"
            f" | Overdue invoices: {len(overdue_invoices)}"
            f" | Negative-margin placements: "
            f"{len(negative_margin_placements)}"
            f" | Placement quality issues: "
            f"{quality_issue_count}"
        )

        # ====================================================
        # MANAGEMENT ALERTS
        # ====================================================

        alerts = []

        today = date.today()

        for placement in filtered_placements:

            start_date = getattr(
                placement,
                "start_date",
                None,
            )

            end_date = getattr(
                placement,
                "end_date",
                None,
            )

            status = get_status(
                placement
            )

            if (
                status == "Scheduled"
                and start_date
                and 0
                <= (
                    start_date
                    - today
                ).days
                <= 30
            ):

                alerts.append(
                    (
                        "Scheduled start",
                        placement,
                        f"Starts in "
                        f"{(start_date - today).days} days."
                    )
                )

            if (
                status == "Active"
                and end_date
                and 0
                <= (
                    end_date
                    - today
                ).days
                <= 30
            ):

                alerts.append(
                    (
                        "Ending soon",
                        placement,
                        f"Ends in "
                        f"{(end_date - today).days} days."
                    )
                )

            if (
                status == "Active"
                and end_date
                and end_date < today
            ):

                alerts.append(
                    (
                        "Expired active placement",
                        placement,
                        "End date has passed."
                    )
                )

        if overdue_invoices:

            alerts.append(
                (
                    "Overdue invoices",
                    None,
                    f"{len(overdue_invoices)} invoice(s) "
                    "require collection review."
                )
            )

        if negative_margin_placements:

            alerts.append(
                (
                    "Negative margins",
                    None,
                    f"{len(negative_margin_placements)} "
                    "placement(s) have negative gross margin."
                )
            )

        if alerts:

            with st.expander(
                f"Management Alerts ({len(alerts)})",
                expanded=False,
            ):

                for alert_type, placement, message in alerts:

                    if placement:

                        employee_name = get_employee_name(
                            get_placement_employee(
                                placement
                            )
                        )

                        st.warning(
                            f"**{alert_type}:** "
                            f"Placement #{placement.id} "
                            f"({employee_name}) — "
                            f"{message}"
                        )

                    else:

                        st.warning(
                            f"**{alert_type}:** "
                            f"{message}"
                        )

        # ====================================================
        # TABS
        # ====================================================

        (
            tab_dashboard,
            tab_pipeline,
            tab_jobs,
            tab_placements,
            tab_financials,
            tab_contracts,
            tab_invoices,
            tab_payments,
            tab_clients,
            tab_quality,
            tab_exports,
        ) = st.tabs(
            [
                "Dashboard",
                "Recruitment Pipeline",
                "Jobs",
                "Placements",
                "Financials",
                "Contracts",
                "Invoices",
                "Payments",
                "Client Performance",
                "Data Quality",
                "Exports",
            ]
        )

        # ====================================================
        # DASHBOARD
        # ====================================================

        with tab_dashboard:

            st.subheader(
                "Management Dashboard"
            )

            d1, d2, d3, d4 = st.columns(4)

            d1.metric(
                "Scheduled Placements",
                len(
                    scheduled_placements
                ),
            )

            d2.metric(
                "Completed",
                len(
                    completed_placements
                ),
            )

            d3.metric(
                "Terminated",
                len(
                    terminated_placements
                ),
            )

            d4.metric(
                "Overdue Invoices",
                len(
                    overdue_invoices
                ),
            )

            st.markdown(
                "### Operational Overview"
            )

            overview_data = {
                "Metric": [
                    "Clients",
                    "Employees",
                    "Jobs",
                    "Candidates",
                    "Placements",
                    "Contracts",
                    "Invoices",
                    "Payments",
                ],
                "Count": [
                    len(filtered_clients),
                    len(filtered_employees),
                    len(filtered_jobs),
                    len(filtered_candidates),
                    len(filtered_placements),
                    len(filtered_contracts),
                    len(filtered_invoices),
                    len(filtered_payments),
                ],
            }

            st.dataframe(
                overview_data,
                use_container_width=True,
                hide_index=True,
            )

            st.markdown(
                "### Placement Status"
            )

            placement_statuses = count_by_status(
                filtered_placements
            )

            if placement_statuses:

                for status, count in sorted(
                    placement_statuses.items()
                ):

                    st.write(
                        f"**{status}:** {count}"
                    )

            else:

                st.info(
                    "No placements found."
                )

            st.markdown(
                "### Financial Snapshot"
            )

            financial_snapshot = {
                "Metric": [
                    "Active Revenue",
                    "Active Worker Cost",
                    "Active Gross Margin",
                    "Outstanding Invoices",
                    "Received Payments",
                ],
                "Value": [
                    format_currency_amounts(
                        active_revenue_totals
                    ),
                    format_currency_amounts(
                        active_cost_totals
                    ),
                    format_currency_amounts(
                        active_margin_totals
                    ),
                    format_currency_amounts(
                        outstanding_totals
                    ),
                    format_currency_amounts(
                        received_payment_totals
                    ),
                ],
            }

            st.dataframe(
                financial_snapshot,
                use_container_width=True,
                hide_index=True,
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

            pipeline_columns = st.columns(4)

            pipeline_status_order = [
                "Submitted",
                "Shortlisted",
                "Interview",
                "Offer",
            ]

            for index, status in enumerate(
                pipeline_status_order
            ):

                pipeline_columns[index].metric(
                    status,
                    candidate_statuses.get(
                        status,
                        0,
                    ),
                )

            placement_columns = st.columns(4)

            placement_columns[0].metric(
                "Placed",
                candidate_statuses.get(
                    "Placed",
                    0,
                ),
            )

            placement_columns[1].metric(
                "Rejected",
                candidate_statuses.get(
                    "Rejected",
                    0,
                ),
            )

            placement_columns[2].metric(
                "Withdrawn",
                candidate_statuses.get(
                    "Withdrawn",
                    0,
                ),
            )

            placement_columns[3].metric(
                "Total Candidates",
                len(
                    filtered_candidates
                ),
            )

            st.markdown(
                "### Candidate Status Breakdown"
            )

            if candidate_statuses:

                pipeline_rows = []

                for status, count in sorted(
                    candidate_statuses.items()
                ):

                    pipeline_rows.append(
                        {
                            "Status": status,
                            "Candidates": count,
                        }
                    )

                st.dataframe(
                    pipeline_rows,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No candidates found for the selected filters."
                )

            st.markdown(
                "### Pipeline Placements"
            )

            pp1, pp2 = st.columns(2)

            with pp1:

                st.metric(
                    "Active",
                    len(
                        active_placements
                    ),
                )

            with pp2:

                st.metric(
                    "Scheduled",
                    len(
                        scheduled_placements
                    ),
                )

            st.markdown(
                "### Recruitment Conversion Indicators"
            )

            total_candidates = len(
                filtered_candidates
            )

            conversion_rows = []

            if total_candidates > 0:

                conversion_rows = [
                    {
                        "Stage": "Shortlisted",
                        "Count": candidate_statuses.get(
                            "Shortlisted",
                            0,
                        ),
                        "Share": format_percentage(
                            (
                                candidate_statuses.get(
                                    "Shortlisted",
                                    0,
                                )
                                / total_candidates
                            )
                            * 100
                        ),
                    },
                    {
                        "Stage": "Interview",
                        "Count": candidate_statuses.get(
                            "Interview",
                            0,
                        ),
                        "Share": format_percentage(
                            (
                                candidate_statuses.get(
                                    "Interview",
                                    0,
                                )
                                / total_candidates
                            )
                            * 100
                        ),
                    },
                    {
                        "Stage": "Offer",
                        "Count": candidate_statuses.get(
                            "Offer",
                            0,
                        ),
                        "Share": format_percentage(
                            (
                                candidate_statuses.get(
                                    "Offer",
                                    0,
                                )
                                / total_candidates
                            )
                            * 100
                        ),
                    },
                    {
                        "Stage": "Placed",
                        "Count": candidate_statuses.get(
                            "Placed",
                            0,
                        ),
                        "Share": format_percentage(
                            (
                                candidate_statuses.get(
                                    "Placed",
                                    0,
                                )
                                / total_candidates
                            )
                            * 100
                        ),
                    },
                ]

            if conversion_rows:

                st.dataframe(
                    conversion_rows,
                    use_container_width=True,
                    hide_index=True,
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

            j1, j2, j3, j4 = st.columns(4)

            j1.metric(
                "Total Jobs",
                len(
                    filtered_jobs
                ),
            )

            j2.metric(
                "Open",
                sum(
                    1
                    for job in filtered_jobs
                    if get_status(job)
                    in JOB_OPEN_STATUSES
                ),
            )

            j3.metric(
                "On Hold",
                sum(
                    1
                    for job in filtered_jobs
                    if get_status(job)
                    == "On Hold"
                ),
            )

            j4.metric(
                "Filled / Closed",
                sum(
                    1
                    for job in filtered_jobs
                    if get_status(job)
                    in [
                        "Filled",
                        "Closed",
                    ]
                ),
            )

            st.markdown(
                "### Job Status Breakdown"
            )

            if job_statuses:

                rows = []

                for status, count in sorted(
                    job_statuses.items()
                ):

                    rows.append(
                        {
                            "Status": status,
                            "Jobs": count,
                        }
                    )

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No jobs found."
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

                job_placement_count = sum(
                    1
                    for placement
                    in filtered_placements
                    if getattr(
                        placement,
                        "job_id",
                        None,
                    )
                    == job.id
                )

                with st.container(
                    border=True
                ):

                    c1, c2, c3, c4 = st.columns(4)

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
                            "Candidates"
                        )

                        st.caption(
                            str(
                                job_candidate_count
                            )
                        )

                    with c4:

                        st.write(
                            "Placements"
                        )

                        st.caption(
                            str(
                                job_placement_count
                            )
                        )

        # ====================================================
        # PLACEMENT REPORT
        # ====================================================

        with tab_placements:

            st.subheader(
                "Placement Report"
            )

            r1, r2, r3, r4, r5, r6 = st.columns(
                6
            )

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
                "Scheduled",
                len(
                    scheduled_placements
                ),
            )

            r4.metric(
                "Completed",
                len(
                    completed_placements
                ),
            )

            r5.metric(
                "Terminated",
                len(
                    terminated_placements
                ),
            )

            r6.metric(
                "Negative Margin",
                len(
                    negative_margin_placements
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

                placement_rows = []

                for placement in filtered_placements:

                    employee_name = get_employee_name(
                        get_placement_employee(
                            placement
                        )
                    )

                    client_name = get_client_name(
                        get_placement_client(
                            placement
                        )
                    )

                    job_label = get_job_label(
                        get_placement_job(
                            placement
                        )
                    )

                    placement_rows.append(
                        {
                            "ID": getattr(
                                placement,
                                "id",
                                "",
                            ),
                            "Client": client_name,
                            "Employee": employee_name,
                            "Job": job_label,
                            "Position": clean_text(
                                getattr(
                                    placement,
                                    "position",
                                    "",
                                )
                            ),
                            "Status": get_status(
                                placement
                            ),
                            "Start": format_date(
                                getattr(
                                    placement,
                                    "start_date",
                                    None,
                                )
                            ),
                            "End": format_date(
                                getattr(
                                    placement,
                                    "end_date",
                                    None,
                                )
                            ),
                            "Revenue": (
                                f"{get_currency(placement)} "
                                f"{get_placement_client_fee(placement):,.2f}"
                            ),
                            "Cost": (
                                f"{get_currency(placement)} "
                                f"{get_placement_worker_cost(placement):,.2f}"
                            ),
                            "Margin": (
                                f"{get_currency(placement)} "
                                f"{get_placement_margin(placement):,.2f}"
                            ),
                            "Margin %": format_percentage(
                                get_placement_margin_percentage(
                                    placement
                                )
                            ),
                            "Quality": (
                                "Review"
                                if get_placement_quality_issues(
                                    placement
                                )
                                else "OK"
                            ),
                        }
                    )

                st.dataframe(
                    placement_rows,
                    use_container_width=True,
                    hide_index=True,
                )

                st.download_button(
                    "Download Placement Register CSV",
                    data=build_placement_csv(
                        filtered_placements
                    ),
                    file_name="averra_placement_report.csv",
                    mime="text/csv",
                    key="download_placement_report",
                )

        # ====================================================
        # FINANCIAL REPORTS
        # ====================================================

        with tab_financials:

            st.subheader(
                "Financial Performance"
            )

            revenue_totals = get_currency_totals(
                active_placements,
                get_placement_client_fee,
            )

            cost_totals = get_currency_totals(
                active_placements,
                get_placement_worker_cost,
            )

            margin_totals = get_currency_totals(
                active_placements,
                get_placement_margin,
            )

            invoice_total_totals = (
                get_currency_totals(
                    filtered_invoices,
                    get_invoice_total,
                )
            )

            invoice_paid_totals = (
                get_currency_totals(
                    filtered_invoices,
                    get_invoice_paid,
                )
            )

            invoice_balance_totals = (
                get_currency_totals(
                    filtered_invoices,
                    get_invoice_balance,
                )
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

            if active_placements:

                margin_rows = []

                for placement in active_placements:

                    margin_rows.append(
                        {
                            "Placement": (
                                f"#{placement.id}"
                            ),
                            "Employee": get_employee_name(
                                get_placement_employee(
                                    placement
                                )
                            ),
                            "Client": get_client_name(
                                get_placement_client(
                                    placement
                                )
                            ),
                            "Revenue": (
                                f"{get_currency(placement)} "
                                f"{get_placement_client_fee(placement):,.2f}"
                            ),
                            "Cost": (
                                f"{get_currency(placement)} "
                                f"{get_placement_worker_cost(placement):,.2f}"
                            ),
                            "Margin": (
                                f"{get_currency(placement)} "
                                f"{get_placement_margin(placement):,.2f}"
                            ),
                            "Margin %": format_percentage(
                                get_placement_margin_percentage(
                                    placement
                                )
                            ),
                            "Status": get_margin_status(
                                placement
                            ),
                        }
                    )

                st.dataframe(
                    margin_rows,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No active placements found."
                )

            st.markdown(
                "### Invoice Financial Position"
            )

            invoice_financial_rows = []

            for currency in sorted(
                set(
                    list(
                        invoice_total_totals.keys()
                    )
                    + list(
                        invoice_paid_totals.keys()
                    )
                    + list(
                        invoice_balance_totals.keys()
                    )
                )
            ):

                total = invoice_total_totals.get(
                    currency,
                    0.0,
                )

                paid = invoice_paid_totals.get(
                    currency,
                    0.0,
                )

                balance = invoice_balance_totals.get(
                    currency,
                    0.0,
                )

                collection_rate = (
                    paid / total * 100
                    if total > 0
                    else 0
                )

                invoice_financial_rows.append(
                    {
                        "Currency": currency,
                        "Invoice Value": f"{total:,.2f}",
                        "Paid": f"{paid:,.2f}",
                        "Outstanding": f"{balance:,.2f}",
                        "Collection %": format_percentage(
                            collection_rate
                        ),
                    }
                )

            if invoice_financial_rows:

                st.dataframe(
                    invoice_financial_rows,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No invoice financial data available."
                )

            st.markdown(
                "### Negative Margin Placements"
            )

            if negative_margin_placements:

                for placement in negative_margin_placements:

                    employee_name = get_employee_name(
                        get_placement_employee(
                            placement
                        )
                    )

                    st.error(
                        f"Placement #{placement.id} — "
                        f"{employee_name} — "
                        f"{get_currency(placement)} "
                        f"{get_placement_margin(placement):,.2f} "
                        f"margin"
                    )

            else:

                st.success(
                    "No negative-margin placements found "
                    "within the selected report."
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

            if contract_statuses:

                contract_rows = []

                for status, count in sorted(
                    contract_statuses.items()
                ):

                    contract_rows.append(
                        {
                            "Status": status,
                            "Contracts": count,
                        }
                    )

                st.dataframe(
                    contract_rows,
                    use_container_width=True,
                    hide_index=True,
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

                renewal_date = getattr(
                    contract,
                    "renewal_date",
                    None,
                )

                with st.container(
                    border=True
                ):

                    c1, c2, c3 = st.columns(3)

                    with c1:

                        st.write(
                            f"**{contract_number or f'Contract #{contract.id}'}**"
                        )

                        st.caption(
                            f"Type: "
                            f"{contract_type or 'Not specified'}"
                        )

                    with c2:

                        st.write(
                            f"Status: **{status}**"
                        )

                        st.caption(
                            f"Start: {format_date(start_date)} "
                            f"| End: {format_date(end_date)}"
                        )

                    with c3:

                        st.write(
                            "Renewal"
                        )

                        st.caption(
                            format_date(
                                renewal_date
                            )
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

            total_invoice_value = (
                get_currency_totals(
                    filtered_invoices,
                    get_invoice_total,
                )
            )

            paid_invoice_value = (
                get_currency_totals(
                    filtered_invoices,
                    get_invoice_paid,
                )
            )

            outstanding_invoice_value = (
                get_currency_totals(
                    filtered_invoices,
                    get_invoice_balance,
                )
            )

            inv1, inv2, inv3, inv4 = st.columns(4)

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
                "Overdue",
                len(
                    overdue_invoices
                ),
            )

            inv4.metric(
                "Statuses",
                len(
                    invoice_statuses
                ),
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

            if invoice_statuses:

                rows = []

                for status, count in sorted(
                    invoice_statuses.items()
                ):

                    rows.append(
                        {
                            "Status": status,
                            "Invoices": count,
                        }
                    )

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )

            st.markdown(
                "### Invoice Register"
            )

            invoice_rows = []

            for invoice in filtered_invoices:

                invoice_number = clean_text(
                    getattr(
                        invoice,
                        "invoice_number",
                        "",
                    )
                )

                invoice_rows.append(
                    {
                        "ID": getattr(
                            invoice,
                            "id",
                            "",
                        ),
                        "Invoice": (
                            invoice_number
                            or f"Invoice #{invoice.id}"
                        ),
                        "Status": get_status(
                            invoice
                        ),
                        "Currency": get_currency(
                            invoice
                        ),
                        "Total": f"{get_invoice_total(invoice):,.2f}",
                        "Paid": f"{get_invoice_paid(invoice):,.2f}",
                        "Balance": f"{get_invoice_balance(invoice):,.2f}",
                        "Invoice Date": format_date(
                            get_invoice_date(
                                invoice
                            )
                        ),
                        "Due Date": format_date(
                            get_invoice_due_date(
                                invoice
                            )
                        ),
                        "Overdue Days": get_invoice_overdue_days(
                            invoice
                        ),
                    }
                )

            if invoice_rows:

                st.dataframe(
                    invoice_rows,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No invoices found."
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
                if get_status(
                    payment
                ) in PAYMENT_SUCCESS_STATUSES
            ]

            non_received_payments = [
                payment
                for payment in filtered_payments
                if get_status(
                    payment
                ) in PAYMENT_NON_SUCCESS_STATUSES
            ]

            received_totals = (
                get_currency_totals(
                    received_payments,
                    get_payment_amount,
                )
            )

            non_received_totals = (
                get_currency_totals(
                    non_received_payments,
                    get_payment_amount,
                )
            )

            pm1, pm2, pm3 = st.columns(3)

            pm1.metric(
                "Payment Records",
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

            if payment_statuses:

                rows = []

                for status, count in sorted(
                    payment_statuses.items()
                ):

                    rows.append(
                        {
                            "Status": status,
                            "Payments": count,
                        }
                    )

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )

            st.markdown(
                "### Payment Register"
            )

            payment_rows = []

            for payment in filtered_payments:

                payment_rows.append(
                    {
                        "ID": getattr(
                            payment,
                            "id",
                            "",
                        ),
                        "Invoice ID": getattr(
                            payment,
                            "invoice_id",
                            "",
                        ),
                        "Status": get_status(
                            payment
                        ),
                        "Currency": get_currency(
                            payment
                        ),
                        "Amount": (
                            f"{get_payment_amount(payment):,.2f}"
                        ),
                        "Date": format_date(
                            get_payment_date(
                                payment
                            )
                        ),
                        "Reference": clean_text(
                            getattr(
                                payment,
                                "reference",
                                "",
                            )
                        ) or "—",
                    }
                )

            if payment_rows:

                st.dataframe(
                    payment_rows,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No payments found."
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

                client_rows = []

                for client in filtered_clients:

                    client_id = client.id

                    client_jobs = [
                        job
                        for job in filtered_jobs
                        if get_client_id_from_job(
                            job
                        )
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

                    client_revenue = (
                        get_currency_totals(
                            client_active_placements,
                            get_placement_client_fee,
                        )
                    )

                    client_margin = (
                        get_currency_totals(
                            client_active_placements,
                            get_placement_margin,
                        )
                    )

                    client_outstanding = (
                        get_currency_totals(
                            client_invoices,
                            get_invoice_balance,
                        )
                    )

                    client_rows.append(
                        {
                            "Client": get_client_name(
                                client
                            ),
                            "Jobs": len(
                                client_jobs
                            ),
                            "Candidates": len(
                                client_candidates
                            ),
                            "Active Placements": len(
                                client_active_placements
                            ),
                            "Invoices": len(
                                client_invoices
                            ),
                            "Active Revenue": (
                                format_currency_amounts(
                                    client_revenue
                                )
                            ),
                            "Active Margin": (
                                format_currency_amounts(
                                    client_margin
                                )
                            ),
                            "Outstanding": (
                                format_currency_amounts(
                                    client_outstanding
                                )
                            ),
                        }
                    )

                st.dataframe(
                    client_rows,
                    use_container_width=True,
                    hide_index=True,
                )

                st.markdown(
                    "### Client Detail"
                )

                for client in filtered_clients:

                    client_id = client.id

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

                    client_active = [
                        placement
                        for placement
                        in client_placements
                        if get_status(
                            placement
                        ) == "Active"
                    ]

                    with st.expander(
                        get_client_name(client)
                    ):

                        cc1, cc2, cc3, cc4 = st.columns(
                            4
                        )

                        cc1.metric(
                            "Jobs",
                            sum(
                                1
                                for job in filtered_jobs
                                if get_client_id_from_job(
                                    job
                                )
                                == client_id
                            ),
                        )

                        cc2.metric(
                            "Candidates",
                            sum(
                                1
                                for candidate
                                in filtered_candidates
                                if get_client_id_from_candidate(
                                    candidate
                                )
                                == client_id
                            ),
                        )

                        cc3.metric(
                            "Active Placements",
                            len(
                                client_active
                            ),
                        )

                        cc4.metric(
                            "Invoices",
                            sum(
                                1
                                for invoice
                                in filtered_invoices
                                if get_client_id_from_invoice(
                                    invoice
                                )
                                == client_id
                            ),
                        )

                        st.write(
                            "**Active Revenue:** "
                            f"{format_currency_amounts(get_currency_totals(client_active, get_placement_client_fee))}"
                        )

                        st.write(
                            "**Active Margin:** "
                            f"{format_currency_amounts(get_currency_totals(client_active, get_placement_margin))}"
                        )

        # ====================================================
        # DATA QUALITY
        # ====================================================

        with tab_quality:

            st.subheader(
                "Data Quality & Integrity"
            )

            quality_issues = []

            # ------------------------------------------------
            # CLIENT CHECKS
            # ------------------------------------------------

            for client in clients:

                if not clean_text(
                    getattr(
                        client,
                        "company_name",
                        "",
                    )
                ):

                    quality_issues.append(
                        (
                            "Client",
                            getattr(
                                client,
                                "id",
                                "?",
                            ),
                            "Client has no company name."
                        )
                    )

            # ------------------------------------------------
            # JOB CHECKS
            # ------------------------------------------------

            for job in jobs:

                if getattr(
                    job,
                    "client_id",
                    None,
                ) is None:

                    quality_issues.append(
                        (
                            "Job",
                            getattr(
                                job,
                                "id",
                                "?",
                            ),
                            "Job has no client."
                        )
                    )

                if not clean_text(
                    getattr(
                        job,
                        "position",
                        "",
                    )
                ):

                    quality_issues.append(
                        (
                            "Job",
                            getattr(
                                job,
                                "id",
                                "?",
                            ),
                            "Job has no position."
                        )
                    )

            # ------------------------------------------------
            # CANDIDATE CHECKS
            # ------------------------------------------------

            for candidate in candidates:

                if getattr(
                    candidate,
                    "employee_id",
                    None,
                ) is None:

                    quality_issues.append(
                        (
                            "Candidate",
                            getattr(
                                candidate,
                                "id",
                                "?",
                            ),
                            "Candidate has no employee."
                        )
                    )

                if getattr(
                    candidate,
                    "job_id",
                    None,
                ) is None:

                    quality_issues.append(
                        (
                            "Candidate",
                            getattr(
                                candidate,
                                "id",
                                "?",
                            ),
                            "Candidate has no job."
                        )
                    )

            # ------------------------------------------------
            # PLACEMENT CHECKS
            # ------------------------------------------------

            for placement in placements:

                issues = get_placement_quality_issues(
                    placement
                )

                for issue in issues:

                    quality_issues.append(
                        (
                            "Placement",
                            getattr(
                                placement,
                                "id",
                                "?",
                            ),
                            issue,
                        )
                    )

            # ------------------------------------------------
            # INVOICE CHECKS
            # ------------------------------------------------

            for invoice in invoices:

                total = get_invoice_total(
                    invoice
                )

                paid = get_invoice_paid(
                    invoice
                )

                if paid > total and total >= 0:

                    quality_issues.append(
                        (
                            "Invoice",
                            getattr(
                                invoice,
                                "id",
                                "?",
                            ),
                            "Amount paid exceeds invoice total."
                        )
                    )

                if total < 0:

                    quality_issues.append(
                        (
                            "Invoice",
                            getattr(
                                invoice,
                                "id",
                                "?",
                            ),
                            "Invoice total is negative."
                        )
                    )

                due_date = get_invoice_due_date(
                    invoice
                )

                invoice_date = get_invoice_date(
                    invoice
                )

                if (
                    invoice_date
                    and due_date
                    and due_date < invoice_date
                ):

                    quality_issues.append(
                        (
                            "Invoice",
                            getattr(
                                invoice,
                                "id",
                                "?",
                            ),
                            "Due date is before invoice date."
                        )
                    )

            # ------------------------------------------------
            # PAYMENT CHECKS
            # ------------------------------------------------

            for payment in payments:

                amount = get_payment_amount(
                    payment
                )

                if amount <= 0:

                    quality_issues.append(
                        (
                            "Payment",
                            getattr(
                                payment,
                                "id",
                                "?",
                            ),
                            "Payment has zero or negative amount."
                        )
                    )

                if getattr(
                    payment,
                    "invoice_id",
                    None,
                ) is None:

                    quality_issues.append(
                        (
                            "Payment",
                            getattr(
                                payment,
                                "id",
                                "?",
                            ),
                            "Payment has no invoice."
                        )
                    )

            # ------------------------------------------------
            # FILTER QUALITY VIEW
            # ------------------------------------------------

            q_filter = st.selectbox(
                "Quality View",
                DATA_QUALITY_LEVELS,
                key="reports_quality_filter",
            )

            displayed_quality_issues = (
                quality_issues
                if q_filter != "Clean Only"
                else []
            )

            q1, q2, q3 = st.columns(3)

            q1.metric(
                "Total Issues",
                len(
                    quality_issues
                ),
            )

            q2.metric(
                "Affected Records",
                len(
                    {
                        (
                            issue[0],
                            issue[1],
                        )
                        for issue in quality_issues
                    }
                ),
            )

            q3.metric(
                "Status",
                "Review Required"
                if quality_issues
                else "OK",
            )

            if q_filter == "Clean Only":

                if quality_issues:

                    st.info(
                        "Quality issues exist, but the view is "
                        "currently filtered to clean records."
                    )

                else:

                    st.success(
                        "No data-quality issues were detected."
                    )

            elif displayed_quality_issues:

                st.warning(
                    "The following records may require review."
                )

                quality_rows = []

                for record_type, record_id, issue in (
                    displayed_quality_issues
                ):

                    quality_rows.append(
                        {
                            "Record Type": record_type,
                            "Record ID": record_id,
                            "Issue": issue,
                        }
                    )

                st.dataframe(
                    quality_rows,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.success(
                    "No basic data-quality issues were detected."
                )

        # ====================================================
        # EXPORTS
        # ====================================================

        with tab_exports:

            st.subheader(
                "Report Exports"
            )

            st.caption(
                "Exports use the active report filters."
            )

            ex1, ex2, ex3 = st.columns(3)

            with ex1:

                st.markdown(
                    "### Placements"
                )

                st.write(
                    f"{len(filtered_placements)} "
                    "placement records"
                )

                st.download_button(
                    "Download Placements CSV",
                    data=build_placement_csv(
                        filtered_placements
                    ),
                    file_name="averra_placements.csv",
                    mime="text/csv",
                    key="export_placements_csv",
                )

            with ex2:

                st.markdown(
                    "### Invoices"
                )

                st.write(
                    f"{len(filtered_invoices)} "
                    "invoice records"
                )

                st.download_button(
                    "Download Invoices CSV",
                    data=build_invoice_csv(
                        filtered_invoices
                    ),
                    file_name="averra_invoices.csv",
                    mime="text/csv",
                    key="export_invoices_csv",
                )

            with ex3:

                st.markdown(
                    "### Payments"
                )

                st.write(
                    f"{len(filtered_payments)} "
                    "payment records"
                )

                st.download_button(
                    "Download Payments CSV",
                    data=build_payment_csv(
                        filtered_payments
                    ),
                    file_name="averra_payments.csv",
                    mime="text/csv",
                    key="export_payments_csv",
                )

            st.divider()

            st.markdown(
                "### Current Report Scope"
            )

            export_summary = {
                "Dataset": [
                    "Clients",
                    "Employees",
                    "Jobs",
                    "Candidates",
                    "Placements",
                    "Contracts",
                    "Invoices",
                    "Payments",
                ],
                "Records": [
                    len(filtered_clients),
                    len(filtered_employees),
                    len(filtered_jobs),
                    len(filtered_candidates),
                    len(filtered_placements),
                    len(filtered_contracts),
                    len(filtered_invoices),
                    len(filtered_payments),
                ],
            }

            st.dataframe(
                export_summary,
                use_container_width=True,
                hide_index=True,
            )

        # ====================================================
        # FOOTER
        # ====================================================

        st.divider()

        st.caption(
            "Reports are read-only and do not modify CRM records."
        )

        st.caption(
            "Financial values are deliberately kept separate "
            "by currency. GBP, EUR, USD and INR are never "
            "added together."
        )

        st.caption(
            "Client filtering is applied wherever the "
            "underlying record can be linked reliably to a client."
        )

        st.caption(
            "Report-period filters use the most relevant "
            "available date field for each record type."
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