import csv
import io
from datetime import date, datetime, timedelta

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
    "Current Month",
    "Last 30 Days",
    "Next 30 Days",
]

CLIENT_SORT_OPTIONS = [
    "Client A-Z",
    "Revenue - Highest",
    "Outstanding - Highest",
    "Margin - Highest",
    "Jobs - Highest",
    "Placements - Highest",
]

QUALITY_SCOPES = [
    "Current Filters",
    "All Records",
]


# ============================================================
# GENERAL HELPERS
# ============================================================

def clean_text(value):
    if value is None:
        return ""

    try:
        return str(value).strip()
    except Exception:
        return ""


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        if value is None:
            return default

        return int(value)

    except (TypeError, ValueError):
        return default


def to_date(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):

        text = value.strip()

        if not text:
            return None

        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
        ]

        for fmt in formats:

            try:
                return datetime.strptime(
                    text,
                    fmt,
                ).date()

            except ValueError:
                continue

    return None


def format_date(value):
    parsed = to_date(value)

    if parsed is None:
        return "-"

    return parsed.strftime("%d/%m/%Y")


def format_number(value, decimals=2):
    return f"{safe_float(value):,.{decimals}f}"


def format_currency(value, currency="GBP"):
    return f"{currency} {safe_float(value):,.2f}"


def get_status(record, default=""):
    if record is None:
        return default

    return (
        clean_text(
            getattr(
                record,
                "status",
                default,
            )
        )
        or default
    )


def get_currency(record, default="GBP"):
    if record is None:
        return default

    return (
        clean_text(
            getattr(
                record,
                "currency",
                default,
            )
        )
        or default
    )


# ============================================================
# NAME / LABEL HELPERS
# ============================================================

def get_client_name(client):
    if client is None:
        return "Unknown Client"

    for field in [
        "company_name",
        "name",
        "company",
        "client_name",
    ]:

        value = clean_text(
            getattr(
                client,
                field,
                None,
            )
        )

        if value:
            return value

    return f"Client #{getattr(client, 'id', '?')}"


def get_employee_name(employee):
    if employee is None:
        return "Unknown Employee"

    full_name = clean_text(
        getattr(
            employee,
            "full_name",
            None,
        )
    )

    if full_name:
        return full_name

    first_name = clean_text(
        getattr(
            employee,
            "first_name",
            None,
        )
    )

    last_name = clean_text(
        getattr(
            employee,
            "last_name",
            None,
        )
    )

    combined = f"{first_name} {last_name}".strip()

    if combined:
        return combined

    name = clean_text(
        getattr(
            employee,
            "name",
            None,
        )
    )

    if name:
        return name

    return f"Employee #{getattr(employee, 'id', '?')}"


def get_job_label(job):
    if job is None:
        return "Unknown Job"

    position = clean_text(
        getattr(
            job,
            "position",
            None,
        )
    )

    if position:
        job_id = getattr(
            job,
            "id",
            None,
        )

        if job_id is not None:
            return f"{position} #{job_id}"

        return position

    title = clean_text(
        getattr(
            job,
            "title",
            None,
        )
    )

    if title:
        return title

    return f"Job #{getattr(job, 'id', '?')}"


def get_candidate_name(candidate):
    if candidate is None:
        return "Unknown Candidate"

    full_name = clean_text(
        getattr(
            candidate,
            "full_name",
            None,
        )
    )

    if full_name:
        return full_name

    first_name = clean_text(
        getattr(
            candidate,
            "first_name",
            None,
        )
    )

    last_name = clean_text(
        getattr(
            candidate,
            "last_name",
            None,
        )
    )

    combined = f"{first_name} {last_name}".strip()

    if combined:
        return combined

    name = clean_text(
        getattr(
            candidate,
            "name",
            None,
        )
    )

    if name:
        return name

    return f"Candidate #{getattr(candidate, 'id', '?')}"


def get_invoice_number(invoice):
    if invoice is None:
        return "Unknown Invoice"

    for field in [
        "invoice_number",
        "number",
        "reference",
    ]:

        value = clean_text(
            getattr(
                invoice,
                field,
                None,
            )
        )

        if value:
            return value

    return f"Invoice #{getattr(invoice, 'id', '?')}"


def get_contract_number(contract):
    if contract is None:
        return "Unknown Contract"

    for field in [
        "contract_number",
        "number",
        "reference",
    ]:

        value = clean_text(
            getattr(
                contract,
                field,
                None,
            )
        )

        if value:
            return value

    return f"Contract #{getattr(contract, 'id', '?')}"


# ============================================================
# RELATIONSHIP HELPERS
# ============================================================

def get_client_id_from_job(job):
    if job is None:
        return None

    return getattr(
        job,
        "client_id",
        None,
    )


def get_client_id_from_candidate(candidate):
    if candidate is None:
        return None

    direct_client_id = getattr(
        candidate,
        "client_id",
        None,
    )

    if direct_client_id is not None:
        return direct_client_id

    job = getattr(
        candidate,
        "job",
        None,
    )

    if job is not None:
        return getattr(
            job,
            "client_id",
            None,
        )

    return None


def get_client_id_from_placement(placement):
    if placement is None:
        return None

    direct_client_id = getattr(
        placement,
        "client_id",
        None,
    )

    if direct_client_id is not None:
        return direct_client_id

    client = getattr(
        placement,
        "client",
        None,
    )

    if client is not None:
        return getattr(
            client,
            "id",
            None,
        )

    return None


def get_client_id_from_contract(contract):
    if contract is None:
        return None

    direct_client_id = getattr(
        contract,
        "client_id",
        None,
    )

    if direct_client_id is not None:
        return direct_client_id

    client = getattr(
        contract,
        "client",
        None,
    )

    if client is not None:
        return getattr(
            client,
            "id",
            None,
        )

    placement = getattr(
        contract,
        "placement",
        None,
    )

    if placement is not None:
        return get_client_id_from_placement(
            placement
        )

    return None


def get_client_id_from_invoice(invoice):
    if invoice is None:
        return None

    direct_client_id = getattr(
        invoice,
        "client_id",
        None,
    )

    if direct_client_id is not None:
        return direct_client_id

    client = getattr(
        invoice,
        "client",
        None,
    )

    if client is not None:
        return getattr(
            client,
            "id",
            None,
        )

    placement = getattr(
        invoice,
        "placement",
        None,
    )

    if placement is not None:
        return get_client_id_from_placement(
            placement
        )

    return None


def get_client_id_from_payment(payment):
    if payment is None:
        return None

    direct_client_id = getattr(
        payment,
        "client_id",
        None,
    )

    if direct_client_id is not None:
        return direct_client_id

    invoice = getattr(
        payment,
        "invoice",
        None,
    )

    if invoice is not None:
        return get_client_id_from_invoice(
            invoice
        )

    return None


# ============================================================
# PLACEMENT FINANCIAL HELPERS
# ============================================================

def get_placement_client_fee(placement):
    if placement is None:
        return 0.0

    for field in [
        "client_monthly_fee",
        "client_fee",
        "monthly_fee",
        "billing_amount",
        "revenue",
    ]:

        value = getattr(
            placement,
            field,
            None,
        )

        if value is not None:
            return safe_float(
                value
            )

    return 0.0


def get_placement_worker_cost(placement):
    if placement is None:
        return 0.0

    for field in [
        "worker_monthly_cost",
        "worker_cost",
        "employee_cost",
        "monthly_cost",
        "cost",
    ]:

        value = getattr(
            placement,
            field,
            None,
        )

        if value is not None:
            return safe_float(
                value
            )

    return 0.0


def get_placement_margin(placement):
    revenue = get_placement_client_fee(
        placement
    )

    cost = get_placement_worker_cost(
        placement
    )

    return revenue - cost


def get_placement_margin_percentage(placement):
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
    """
    Safely obtain invoice total.

    IMPORTANT:
    This function deliberately avoids invoice.balance_due.
    """

    if invoice is None:
        return 0.0

    fields = [
        "total_amount",
        "total",
        "grand_total",
        "amount",
    ]

    for field in fields:

        try:
            value = getattr(
                invoice,
                field,
                None,
            )

        except Exception:
            value = None

        if value is None:
            continue

        try:
            return float(
                value or 0
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

    return 0.0


def get_invoice_paid(invoice):
    """
    Safely obtain invoice amount paid.

    IMPORTANT:
    This function deliberately avoids invoice.balance_due.
    """

    if invoice is None:
        return 0.0

    fields = [
        "amount_paid",
        "paid_amount",
        "payments_received",
    ]

    for field in fields:

        try:
            value = getattr(
                invoice,
                field,
                None,
            )

        except Exception:
            value = None

        if value is None:
            continue

        try:
            return float(
                value or 0
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

    return 0.0


def get_invoice_balance(invoice):
    """
    Safely calculate outstanding invoice balance.

    total - amount_paid
    """

    if invoice is None:
        return 0.0

    total = get_invoice_total(
        invoice
    )

    paid = get_invoice_paid(
        invoice
    )

    balance = total - paid

    if abs(balance) < 0.005:
        balance = 0.0

    return max(
        balance,
        0.0,
    )


def is_invoice_open(invoice):
    if invoice is None:
        return False

    status = get_status(
        invoice
    ).lower()

    if status in [
        "cancelled",
        "paid",
    ]:
        return False

    if status in [
        value.lower()
        for value in INVOICE_OPEN_STATUSES
    ]:
        return True

    return get_invoice_balance(
        invoice
    ) > 0


def get_invoice_overdue_days(
    invoice,
    today=None,
):
    if invoice is None:
        return 0

    if today is None:
        today = date.today()

    balance = get_invoice_balance(
        invoice
    )

    if balance <= 0:
        return 0

    due_date = to_date(
        getattr(
            invoice,
            "due_date",
            None,
        )
    )

    if due_date is None:
        return 0

    if due_date >= today:
        return 0

    return (
        today - due_date
    ).days


def is_invoice_overdue(
    invoice,
    today=None,
):
    return (
        get_invoice_overdue_days(
            invoice,
            today,
        )
        > 0
    )


# ============================================================
# PAYMENT HELPERS
# ============================================================

def get_payment_amount(payment):
    if payment is None:
        return 0.0

    fields = [
        "amount",
        "payment_amount",
        "value",
    ]

    for field in fields:

        value = getattr(
            payment,
            field,
            None,
        )

        if value is not None:
            return safe_float(
                value
            )

    return 0.0


def get_payment_status(payment):
    return get_status(
        payment,
        "Pending",
    )


def get_payment_date(payment):
    fields = [
        "payment_date",
        "received_date",
        "date",
        "created_at",
    ]

    for field in fields:

        value = getattr(
            payment,
            field,
            None,
        )

        parsed = to_date(
            value
        )

        if parsed is not None:
            return parsed

    return None


# ============================================================
# DATE HELPERS
# ============================================================

def get_primary_date(
    record,
    record_type,
):
    field_map = {

        "client": [
            "created_at",
            "date_created",
        ],

        "employee": [
            "hire_date",
            "start_date",
            "created_at",
        ],

        "job": [
            "date_opened",
            "created_at",
            "closing_date",
        ],

        "candidate": [
            "application_date",
            "created_at",
            "interview_date",
        ],

        "placement": [
            "start_date",
            "created_at",
            "end_date",
        ],

        "contract": [
            "start_date",
            "signed_date",
            "created_at",
            "renewal_date",
        ],

        "invoice": [
            "issue_date",
            "created_at",
            "due_date",
        ],

        "payment": [
            "payment_date",
            "received_date",
            "date",
            "created_at",
        ],
    }

    for field in field_map.get(
        record_type,
        [],
    ):

        value = getattr(
            record,
            field,
            None,
        )

        parsed = to_date(
            value
        )

        if parsed is not None:
            return parsed

    return None


def matches_period(
    record,
    record_type,
    period,
    today,
):
    if period == "All Time":
        return True

    record_date = get_primary_date(
        record,
        record_type,
    )

    if record_date is None:
        return True

    if period == "Current Month":

        first_day = today.replace(
            day=1
        )

        return (
            first_day
            <= record_date
            <= today
        )

    if period == "Last 30 Days":

        start_date = (
            today
            - timedelta(
                days=30
            )
        )

        return (
            start_date
            <= record_date
            <= today
        )

    if period == "Next 30 Days":

        end_date = (
            today
            + timedelta(
                days=30
            )
        )

        return (
            today
            <= record_date
            <= end_date
        )

    return True


# ============================================================
# SEARCH
# ============================================================

def record_search_text(
    record,
    record_type,
):
    if record is None:
        return ""

    values = []

    if record_type == "client":

        values.extend(
            [
                getattr(
                    record,
                    "company_name",
                    "",
                ),
                getattr(
                    record,
                    "name",
                    "",
                ),
                getattr(
                    record,
                    "email",
                    "",
                ),
                getattr(
                    record,
                    "website",
                    "",
                ),
                getattr(
                    record,
                    "country",
                    "",
                ),
            ]
        )

    elif record_type == "employee":

        values.extend(
            [
                get_employee_name(
                    record
                ),
                getattr(
                    record,
                    "email",
                    "",
                ),
                getattr(
                    record,
                    "role",
                    "",
                ),
                getattr(
                    record,
                    "job_title",
                    "",
                ),
                getattr(
                    record,
                    "country",
                    "",
                ),
            ]
        )

    elif record_type == "job":

        values.extend(
            [
                getattr(
                    record,
                    "position",
                    "",
                ),
                getattr(
                    record,
                    "department",
                    "",
                ),
                getattr(
                    record,
                    "skills_required",
                    "",
                ),
                getattr(
                    record,
                    "remote_country",
                    "",
                ),
            ]
        )

    elif record_type == "candidate":

        values.extend(
            [
                get_candidate_name(
                    record
                ),
                getattr(
                    record,
                    "email",
                    "",
                ),
                getattr(
                    record,
                    "phone",
                    "",
                ),
                getattr(
                    record,
                    "skills",
                    "",
                ),
            ]
        )

        job = getattr(
            record,
            "job",
            None,
        )

        if job is not None:
            values.append(
                get_job_label(
                    job
                )
            )

    elif record_type == "placement":

        values.extend(
            [
                getattr(
                    record,
                    "position",
                    "",
                ),
                getattr(
                    record,
                    "notes",
                    "",
                ),
            ]
        )

        client = getattr(
            record,
            "client",
            None,
        )

        employee = getattr(
            record,
            "employee",
            None,
        )

        job = getattr(
            record,
            "job",
            None,
        )

        if client is not None:
            values.append(
                get_client_name(
                    client
                )
            )

        if employee is not None:
            values.append(
                get_employee_name(
                    employee
                )
            )

        if job is not None:
            values.append(
                get_job_label(
                    job
                )
            )

    elif record_type == "contract":

        values.extend(
            [
                get_contract_number(
                    record
                ),
                getattr(
                    record,
                    "contract_type",
                    "",
                ),
                getattr(
                    record,
                    "notes",
                    "",
                ),
            ]
        )

    elif record_type == "invoice":

        values.extend(
            [
                get_invoice_number(
                    record
                ),
                getattr(
                    record,
                    "description",
                    "",
                ),
                getattr(
                    record,
                    "notes",
                    "",
                ),
            ]
        )

    elif record_type == "payment":

        values.extend(
            [
                getattr(
                    record,
                    "reference",
                    "",
                ),
                getattr(
                    record,
                    "payment_reference",
                    "",
                ),
                getattr(
                    record,
                    "notes",
                    "",
                ),
            ]
        )

    return " ".join(
        clean_text(value)
        for value in values
        if clean_text(value)
    ).lower()


def matches_search(
    record,
    record_type,
    search_text,
):
    search_text = clean_text(
        search_text
    ).lower()

    if not search_text:
        return True

    return (
        search_text
        in record_search_text(
            record,
            record_type,
        )
    )


# ============================================================
# FILTERING
# ============================================================

def matches_client(
    record,
    record_type,
    selected_client_id,
):
    if selected_client_id == "All Clients":
        return True

    try:
        selected_id = int(
            selected_client_id
        )
    except (
        TypeError,
        ValueError,
    ):
        return True

    if record_type == "client":

        return (
            getattr(
                record,
                "id",
                None,
            )
            == selected_id
        )

    if record_type == "job":

        return (
            get_client_id_from_job(
                record
            )
            == selected_id
        )

    if record_type == "candidate":

        return (
            get_client_id_from_candidate(
                record
            )
            == selected_id
        )

    if record_type == "placement":

        return (
            get_client_id_from_placement(
                record
            )
            == selected_id
        )

    if record_type == "contract":

        return (
            get_client_id_from_contract(
                record
            )
            == selected_id
        )

    if record_type == "invoice":

        return (
            get_client_id_from_invoice(
                record
            )
            == selected_id
        )

    if record_type == "payment":

        return (
            get_client_id_from_payment(
                record
            )
            == selected_id
        )

    return True


def matches_currency(
    record,
    selected_currency,
):
    if selected_currency == "All Currencies":
        return True

    return (
        get_currency(record)
        == selected_currency
    )


def filter_records(
    records,
    record_type,
    selected_client,
    selected_currency,
    search_text,
    period,
    today,
    financial=False,
):
    result = []

    for record in records:

        if not matches_client(
            record,
            record_type,
            selected_client,
        ):
            continue

        if financial:

            if not matches_currency(
                record,
                selected_currency,
            ):
                continue

        if not matches_search(
            record,
            record_type,
            search_text,
        ):
            continue

        if not matches_period(
            record,
            record_type,
            period,
            today,
        ):
            continue

        result.append(
            record
        )

    return result


# ============================================================
# AGGREGATION
# ============================================================

def count_by_status(records):
    counts = {}

    for record in records:

        status = get_status(
            record,
            "Unknown",
        )

        counts[status] = (
            counts.get(
                status,
                0,
            )
            + 1
        )

    return counts


def add_currency_value(
    container,
    currency,
    value,
):
    currency = (
        clean_text(currency)
        or "GBP"
    )

    container[currency] = (
        container.get(
            currency,
            0.0,
        )
        + safe_float(value)
    )


def format_currency_amounts(
    amounts,
):
    if not amounts:
        return "0.00"

    parts = []

    for currency in sorted(
        amounts.keys()
    ):

        parts.append(
            f"{currency} "
            f"{safe_float(amounts[currency]):,.2f}"
        )

    return " | ".join(
        parts
    )


def build_csv(
    headers,
    rows,
):
    output = io.StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow(
        headers
    )

    for row in rows:
        writer.writerow(
            row
        )

    return output.getvalue()


# ============================================================
# OPERATIONAL HELPERS
# ============================================================

def get_placement_start_date(
    placement
):
    return to_date(
        getattr(
            placement,
            "start_date",
            None,
        )
    )


def get_placement_end_date(
    placement
):
    return to_date(
        getattr(
            placement,
            "end_date",
            None,
        )
    )


def get_contract_renewal_date(
    contract
):
    return to_date(
        getattr(
            contract,
            "renewal_date",
            None,
        )
    )


def get_job_closing_date(job):
    return to_date(
        getattr(
            job,
            "closing_date",
            None,
        )
    )


def is_ending_soon(
    end_date,
    today,
    days=30,
):
    if end_date is None:
        return False

    return (
        today
        <= end_date
        <= today
        + timedelta(
            days=days
        )
    )


# ============================================================
# DATA QUALITY
# ============================================================

def collect_quality_issues(
    clients,
    employees,
    jobs,
    candidates,
    placements,
    contracts,
    invoices,
    payments,
    today,
):
    issues = {
        "Clients": [],
        "Employees": [],
        "Jobs": [],
        "Candidates": [],
        "Placements": [],
        "Contracts": [],
        "Invoices": [],
        "Payments": [],
    }

    # --------------------------------------------------------
    # CLIENTS
    # --------------------------------------------------------

    for client in clients:

        name = get_client_name(
            client
        )

        if name.startswith(
            "Client #"
        ):

            issues["Clients"].append(
                f"{name}: missing company name"
            )

    # --------------------------------------------------------
    # EMPLOYEES
    # --------------------------------------------------------

    for employee in employees:

        name = get_employee_name(
            employee
        )

        if name.startswith(
            "Employee #"
        ):

            issues["Employees"].append(
                f"{name}: missing employee name"
            )

    # --------------------------------------------------------
    # JOBS
    # --------------------------------------------------------

    for job in jobs:

        label = get_job_label(
            job
        )

        if (
            get_client_id_from_job(
                job
            )
            is None
        ):

            issues["Jobs"].append(
                f"{label}: missing client"
            )

        position = clean_text(
            getattr(
                job,
                "position",
                None,
            )
        )

        if not position:

            issues["Jobs"].append(
                f"Job #{getattr(job, 'id', '?')}: missing position"
            )

        opened = to_date(
            getattr(
                job,
                "date_opened",
                None,
            )
        )

        closing = get_job_closing_date(
            job
        )

        if (
            opened is not None
            and closing is not None
            and closing < opened
        ):

            issues["Jobs"].append(
                f"{label}: closing date before opening date"
            )

        budget = getattr(
            job,
            "client_budget",
            None,
        )

        if budget is not None:

            if safe_float(
                budget
            ) < 0:

                issues["Jobs"].append(
                    f"{label}: negative client budget"
                )

        openings = getattr(
            job,
            "openings",
            None,
        )

        if openings is not None:

            if safe_int(
                openings
            ) <= 0:

                issues["Jobs"].append(
                    f"{label}: openings should be greater than zero"
                )

    # --------------------------------------------------------
    # CANDIDATES
    # --------------------------------------------------------

    for candidate in candidates:

        label = get_candidate_name(
            candidate
        )

        job = getattr(
            candidate,
            "job",
            None,
        )

        job_id = getattr(
            candidate,
            "job_id",
            None,
        )

        if (
            job is None
            and job_id is None
        ):

            issues["Candidates"].append(
                f"{label}: missing job"
            )

        employee = getattr(
            candidate,
            "employee",
            None,
        )

        employee_id = getattr(
            candidate,
            "employee_id",
            None,
        )

        if (
            employee is None
            and employee_id is None
        ):

            issues["Candidates"].append(
                f"{label}: missing employee"
            )

        application_date = to_date(
            getattr(
                candidate,
                "application_date",
                None,
            )
        )

        interview_date = to_date(
            getattr(
                candidate,
                "interview_date",
                None,
            )
        )

        if (
            application_date is not None
            and interview_date is not None
            and interview_date
            < application_date
        ):

            issues["Candidates"].append(
                f"{label}: interview date before application date"
            )

    # --------------------------------------------------------
    # PLACEMENTS
    # --------------------------------------------------------

    for placement in placements:

        placement_id = getattr(
            placement,
            "id",
            "?",
        )

        if (
            get_client_id_from_placement(
                placement
            )
            is None
        ):

            issues["Placements"].append(
                f"Placement #{placement_id}: missing client"
            )

        if getattr(
            placement,
            "employee_id",
            None,
        ) is None:

            issues["Placements"].append(
                f"Placement #{placement_id}: missing employee"
            )

        position = clean_text(
            getattr(
                placement,
                "position",
                None,
            )
        )

        if not position:

            issues["Placements"].append(
                f"Placement #{placement_id}: missing position"
            )

        start_date = get_placement_start_date(
            placement
        )

        end_date = get_placement_end_date(
            placement
        )

        if (
            start_date is not None
            and end_date is not None
            and end_date < start_date
        ):

            issues["Placements"].append(
                f"Placement #{placement_id}: end date before start date"
            )

        status = get_status(
            placement
        )

        if (
            status == "Active"
            and end_date is not None
            and end_date < today
        ):

            issues["Placements"].append(
                f"Placement #{placement_id}: Active placement has passed end date"
            )

        if (
            status == "Scheduled"
            and start_date is not None
            and start_date < today
        ):

            issues["Placements"].append(
                f"Placement #{placement_id}: Scheduled placement has passed start date"
            )

        revenue = get_placement_client_fee(
            placement
        )

        cost = get_placement_worker_cost(
            placement
        )

        margin = revenue - cost

        if margin < 0:

            issues["Placements"].append(
                f"Placement #{placement_id}: negative margin"
            )

        if revenue < 0:

            issues["Placements"].append(
                f"Placement #{placement_id}: negative client fee"
            )

        if cost < 0:

            issues["Placements"].append(
                f"Placement #{placement_id}: negative worker cost"
            )

    # --------------------------------------------------------
    # CONTRACTS
    # --------------------------------------------------------

    for contract in contracts:

        label = get_contract_number(
            contract
        )

        start_date = to_date(
            getattr(
                contract,
                "start_date",
                None,
            )
        )

        end_date = to_date(
            getattr(
                contract,
                "end_date",
                None,
            )
        )

        renewal_date = get_contract_renewal_date(
            contract
        )

        if (
            start_date is not None
            and end_date is not None
            and end_date < start_date
        ):

            issues["Contracts"].append(
                f"{label}: end date before contract start"
            )

        if (
            renewal_date is not None
            and start_date is not None
            and renewal_date < start_date
        ):

            issues["Contracts"].append(
                f"{label}: renewal date before contract start"
            )

        if (
            renewal_date is not None
            and end_date is not None
            and renewal_date > end_date
        ):

            issues["Contracts"].append(
                f"{label}: renewal date after contract end"
            )

    # --------------------------------------------------------
    # INVOICES
    # --------------------------------------------------------

    for invoice in invoices:

        label = get_invoice_number(
            invoice
        )

        if (
            get_client_id_from_invoice(
                invoice
            )
            is None
        ):

            issues["Invoices"].append(
                f"{label}: missing client"
            )

        total = get_invoice_total(
            invoice
        )

        paid = get_invoice_paid(
            invoice
        )

        if paid < 0:

            issues["Invoices"].append(
                f"{label}: negative amount paid"
            )

        if paid > total + 0.01:

            issues["Invoices"].append(
                f"{label}: amount paid exceeds invoice total"
            )

        issue_date = to_date(
            getattr(
                invoice,
                "issue_date",
                None,
            )
        )

        due_date = to_date(
            getattr(
                invoice,
                "due_date",
                None,
            )
        )

        if (
            issue_date is not None
            and due_date is not None
            and due_date < issue_date
        ):

            issues["Invoices"].append(
                f"{label}: due date before issue date"
            )

        invoice_number = clean_text(
            getattr(
                invoice,
                "invoice_number",
                None,
            )
        )

        if not invoice_number:

            issues["Invoices"].append(
                f"Invoice #{getattr(invoice, 'id', '?')}: missing invoice number"
            )

    # --------------------------------------------------------
    # PAYMENTS
    # --------------------------------------------------------

    for payment in payments:

        payment_id = getattr(
            payment,
            "id",
            "?",
        )

        amount = get_payment_amount(
            payment
        )

        invoice = getattr(
            payment,
            "invoice",
            None,
        )

        invoice_id = getattr(
            payment,
            "invoice_id",
            None,
        )

        if (
            invoice is None
            and invoice_id is None
        ):

            issues["Payments"].append(
                f"Payment #{payment_id}: missing invoice"
            )

        if amount <= 0:

            issues["Payments"].append(
                f"Payment #{payment_id}: amount should be greater than zero"
            )

    return issues


# ============================================================
# MAIN REPORTS SCREEN
# ============================================================

def show_reports():

    session = get_session()

    try:

        today = date.today()

        # ====================================================
        # LOAD DATABASE
        # ====================================================

        clients = (
            session.query(Client)
            .order_by(
                Client.id
            )
            .all()
        )

        employees = (
            session.query(Employee)
            .order_by(
                Employee.id
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
        # HEADER
        # ====================================================

        st.title(
            "AVERRA Reports & Analytics"
        )

        st.caption(
            "Management dashboard covering recruitment, "
            "jobs, placements, contracts, invoices, "
            "payments and data quality."
        )

        # ====================================================
        # FILTERS
        # ====================================================

        st.subheader(
            "Report Filters"
        )

        col1, col2, col3, col4 = st.columns(
            4
        )

        client_options = [
            "All Clients"
        ]

        client_map = {}

        for client in clients:

            client_id = getattr(
                client,
                "id",
                None,
            )

            if client_id is None:
                continue

            name = get_client_name(
                client
            )

            label = (
                f"{name} (#{client_id})"
            )

            client_options.append(
                label
            )

            client_map[
                label
            ] = client_id

        with col1:

            selected_client_label = st.selectbox(
                "Client",
                client_options,
                key="reports_client_filter",
            )

        if selected_client_label == "All Clients":

            selected_client = (
                "All Clients"
            )

        else:

            selected_client = client_map.get(
                selected_client_label,
                "All Clients",
            )

        with col2:

            selected_currency = st.selectbox(
                "Currency",
                [
                    "All Currencies"
                ]
                + CURRENCIES,
                key="reports_currency_filter",
            )

        with col3:

            selected_period = st.selectbox(
                "Report Period",
                REPORT_PERIODS,
                key="reports_period_filter",
            )

        with col4:

            search_text = st.text_input(
                "Search",
                placeholder=(
                    "Client, employee, job, invoice..."
                ),
                key="reports_search_filter",
            )

        st.caption(
            "Date filters use the primary date available "
            "for each record type."
        )

        # ====================================================
        # FILTER DATA
        # ====================================================

        filtered_clients = filter_records(
            clients,
            "client",
            selected_client,
            "All Currencies",
            search_text,
            selected_period,
            today,
        )

        filtered_employees = filter_records(
            employees,
            "employee",
            selected_client,
            "All Currencies",
            search_text,
            selected_period,
            today,
        )

        filtered_jobs = filter_records(
            jobs,
            "job",
            selected_client,
            "All Currencies",
            search_text,
            selected_period,
            today,
        )

        filtered_candidates = filter_records(
            candidates,
            "candidate",
            selected_client,
            "All Currencies",
            search_text,
            selected_period,
            today,
        )

        filtered_placements = filter_records(
            placements,
            "placement",
            selected_client,
            selected_currency,
            search_text,
            selected_period,
            today,
            financial=True,
        )

        filtered_contracts = filter_records(
            contracts,
            "contract",
            selected_client,
            selected_currency,
            search_text,
            selected_period,
            today,
            financial=True,
        )

        filtered_invoices = filter_records(
            invoices,
            "invoice",
            selected_client,
            selected_currency,
            search_text,
            selected_period,
            today,
            financial=True,
        )

        filtered_payments = filter_records(
            payments,
            "payment",
            selected_client,
            selected_currency,
            search_text,
            selected_period,
            today,
            financial=True,
        )

        # ====================================================
        # EXECUTIVE CALCULATIONS
        # ====================================================

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
            if is_invoice_open(
                invoice
            )
        ]

        overdue_invoices = [
            invoice
            for invoice in filtered_invoices
            if is_invoice_overdue(
                invoice,
                today,
            )
        ]

        received_payments = [
            payment
            for payment in filtered_payments
            if get_payment_status(
                payment
            ) in PAYMENT_SUCCESS_STATUSES
        ]

        # ====================================================
        # FINANCIAL TOTALS
        # ====================================================

        invoice_total_by_currency = {}
        paid_by_currency = {}
        outstanding_by_currency = {}
        payment_received_by_currency = {}

        placement_revenue_by_currency = {}
        placement_cost_by_currency = {}
        placement_margin_by_currency = {}

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
                invoice_total_by_currency,
                currency,
                total,
            )

            add_currency_value(
                paid_by_currency,
                currency,
                paid,
            )

            add_currency_value(
                outstanding_by_currency,
                currency,
                balance,
            )

        for payment in received_payments:

            currency = get_currency(
                payment
            )

            amount = get_payment_amount(
                payment
            )

            add_currency_value(
                payment_received_by_currency,
                currency,
                amount,
            )

        for placement in active_placements:

            currency = get_currency(
                placement
            )

            revenue = get_placement_client_fee(
                placement
            )

            cost = get_placement_worker_cost(
                placement
            )

            margin = revenue - cost

            add_currency_value(
                placement_revenue_by_currency,
                currency,
                revenue,
            )

            add_currency_value(
                placement_cost_by_currency,
                currency,
                cost,
            )

            add_currency_value(
                placement_margin_by_currency,
                currency,
                margin,
            )

        negative_margin_placements = [
            placement
            for placement in filtered_placements
            if get_placement_margin(
                placement
            ) < 0
        ]

        ending_soon_placements = [
            placement
            for placement in filtered_placements
            if (
                get_status(
                    placement
                )
                in PLACEMENT_PIPELINE_STATUSES
                and is_ending_soon(
                    get_placement_end_date(
                        placement
                    ),
                    today,
                    30,
                )
            )
        ]

        contracts_renewing_soon = [
            contract
            for contract in filtered_contracts
            if is_ending_soon(
                get_contract_renewal_date(
                    contract
                ),
                today,
                30,
            )
        ]

        jobs_closing_soon = [
            job
            for job in filtered_jobs
            if (
                get_status(
                    job
                )
                in [
                    "Open",
                    "On Hold",
                ]
                and is_ending_soon(
                    get_job_closing_date(
                        job
                    ),
                    today,
                    30,
                )
            )
        ]

        # ====================================================
        # EXECUTIVE SUMMARY
        # ====================================================

        st.subheader(
            "Executive Summary"
        )

        k1, k2, k3, k4 = st.columns(
            4
        )

        with k1:
            st.metric(
                "Clients",
                len(filtered_clients),
            )

        with k2:
            st.metric(
                "Employees",
                len(filtered_employees),
            )

        with k3:
            st.metric(
                "Open Jobs",
                len(open_jobs),
            )

        with k4:
            st.metric(
                "Candidates",
                len(filtered_candidates),
            )

        k5, k6, k7, k8 = st.columns(
            4
        )

        with k5:
            st.metric(
                "Active Placements",
                len(active_placements),
            )

        with k6:
            st.metric(
                "Scheduled Placements",
                len(scheduled_placements),
            )

        with k7:
            st.metric(
                "Open Invoices",
                len(open_invoices),
            )

        with k8:
            st.metric(
                "Overdue Invoices",
                len(overdue_invoices),
            )

        # ====================================================
        # FINANCIAL OVERVIEW
        # ====================================================

        st.subheader(
            "Financial Overview"
        )

        f1, f2, f3, f4 = st.columns(
            4
        )

        with f1:

            st.metric(
                "Invoice Total",
                format_currency_amounts(
                    invoice_total_by_currency
                ),
            )

        with f2:

            st.metric(
                "Paid",
                format_currency_amounts(
                    paid_by_currency
                ),
            )

        with f3:

            st.metric(
                "Outstanding",
                format_currency_amounts(
                    outstanding_by_currency
                ),
            )

        with f4:

            st.metric(
                "Received Payments",
                format_currency_amounts(
                    payment_received_by_currency
                ),
            )

        # ====================================================
        # ATTENTION REQUIRED
        # ====================================================

        st.subheader(
            "Attention Required"
        )

        a1, a2, a3, a4 = st.columns(
            4
        )

        with a1:

            st.metric(
                "Negative Margin",
                len(
                    negative_margin_placements
                ),
            )

            if negative_margin_placements:

                with st.expander(
                    "View negative-margin placements"
                ):

                    for placement in negative_margin_placements[
                        :10
                    ]:

                        placement_id = getattr(
                            placement,
                            "id",
                            "?",
                        )

                        position = clean_text(
                            getattr(
                                placement,
                                "position",
                                "",
                            )
                        )

                        margin = get_placement_margin(
                            placement
                        )

                        currency = get_currency(
                            placement
                        )

                        margin_text = format_currency(
                            margin,
                            currency,
                        )

                        st.write(
                            f"• Placement #{placement_id} — "
                            f"{position or 'No position'} — "
                            f"Margin: {margin_text}"
                        )

        with a2:

            st.metric(
                "Overdue Invoices",
                len(
                    overdue_invoices
                ),
            )

            if overdue_invoices:

                with st.expander(
                    "View overdue invoices"
                ):

                    for invoice in overdue_invoices[
                        :10
                    ]:

                        invoice_name = get_invoice_number(
                            invoice
                        )

                        balance_text = format_currency(
                            get_invoice_balance(
                                invoice
                            ),
                            get_currency(
                                invoice
                            ),
                        )

                        overdue_days = get_invoice_overdue_days(
                            invoice,
                            today,
                        )

                        st.write(
                            f"• {invoice_name} — "
                            f"Outstanding: {balance_text} — "
                            f"{overdue_days} days overdue"
                        )

        with a3:

            st.metric(
                "Contracts Renewing",
                len(
                    contracts_renewing_soon
                ),
            )

            if contracts_renewing_soon:

                with st.expander(
                    "View upcoming renewals"
                ):

                    for contract in contracts_renewing_soon[
                        :10
                    ]:

                        contract_name = get_contract_number(
                            contract
                        )

                        renewal = format_date(
                            get_contract_renewal_date(
                                contract
                            )
                        )

                        st.write(
                            f"• {contract_name} — "
                            f"Renewal: {renewal}"
                        )

        with a4:

            st.metric(
                "Jobs Closing Soon",
                len(
                    jobs_closing_soon
                ),
            )

            if jobs_closing_soon:

                with st.expander(
                    "View jobs closing soon"
                ):

                    for job in jobs_closing_soon[
                        :10
                    ]:

                        job_name = get_job_label(
                            job
                        )

                        closing = format_date(
                            get_job_closing_date(
                                job
                            )
                        )

                        st.write(
                            f"• {job_name} — "
                            f"Closing: {closing}"
                        )

        st.divider()

        # ====================================================
        # TABS
        # ====================================================

        (
            tab_recruitment,
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
        # RECRUITMENT
        # ====================================================

        with tab_recruitment:

            st.subheader(
                "Recruitment Pipeline"
            )

            candidate_counts = count_by_status(
                filtered_candidates
            )

            placement_counts = count_by_status(
                filtered_placements
            )

            r1, r2 = st.columns(
                2
            )

            with r1:

                st.markdown(
                    "### Candidate Status"
                )

                if candidate_counts:

                    st.bar_chart(
                        candidate_counts
                    )

                    for status, count in sorted(
                        candidate_counts.items()
                    ):

                        st.write(
                            f"**{status}:** {count}"
                        )

                else:

                    st.info(
                        "No candidate records found."
                    )

            with r2:

                st.markdown(
                    "### Placement Status"
                )

                if placement_counts:

                    st.bar_chart(
                        placement_counts
                    )

                    for status, count in sorted(
                        placement_counts.items()
                    ):

                        st.write(
                            f"**{status}:** {count}"
                        )

                else:

                    st.info(
                        "No placement records found."
                    )

            st.markdown(
                "### Candidate Register"
            )

            candidate_rows = []

            for candidate in filtered_candidates:

                job = getattr(
                    candidate,
                    "job",
                    None,
                )

                employee = getattr(
                    candidate,
                    "employee",
                    None,
                )

                candidate_rows.append(
                    [
                        get_candidate_name(
                            candidate
                        ),
                        get_status(
                            candidate
                        ),
                        get_job_label(
                            job
                        ),
                        get_employee_name(
                            employee
                        ),
                        format_date(
                            getattr(
                                candidate,
                                "application_date",
                                None,
                            )
                        ),
                        format_date(
                            getattr(
                                candidate,
                                "interview_date",
                                None,
                            )
                        ),
                    ]
                )

            if candidate_rows:

                st.dataframe(
                    candidate_rows,
                    column_config={
                        0: "Candidate",
                        1: "Status",
                        2: "Job",
                        3: "Employee",
                        4: "Application Date",
                        5: "Interview Date",
                    },
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No candidates match the current filters."
                )

        # ====================================================
        # JOBS
        # ====================================================

        with tab_jobs:

            st.subheader(
                "Jobs"
            )

            job_counts = count_by_status(
                filtered_jobs
            )

            if job_counts:

                st.bar_chart(
                    job_counts
                )

                for status, count in sorted(
                    job_counts.items()
                ):

                    st.write(
                        f"**{status}:** {count}"
                    )

            else:

                st.info(
                    "No jobs match the current filters."
                )

            st.markdown(
                "### Job Register"
            )

            job_rows = []

            for job in filtered_jobs:

                client = getattr(
                    job,
                    "client",
                    None,
                )

                job_rows.append(
                    [
                        get_job_label(
                            job
                        ),
                        get_client_name(
                            client
                        ),
                        get_status(
                            job
                        ),
                        clean_text(
                            getattr(
                                job,
                                "department",
                                "",
                            )
                        ),
                        safe_int(
                            getattr(
                                job,
                                "openings",
                                0,
                            )
                        ),
                        get_currency(
                            job
                        ),
                        safe_float(
                            getattr(
                                job,
                                "client_budget",
                                0,
                            )
                        ),
                        format_date(
                            getattr(
                                job,
                                "date_opened",
                                None,
                            )
                        ),
                        format_date(
                            getattr(
                                job,
                                "closing_date",
                                None,
                            )
                        ),
                    ]
                )

            if job_rows:

                st.dataframe(
                    job_rows,
                    column_config={
                        0: "Job",
                        1: "Client",
                        2: "Status",
                        3: "Department",
                        4: "Openings",
                        5: "Currency",
                        6: "Budget",
                        7: "Opened",
                        8: "Closing",
                    },
                    use_container_width=True,
                    hide_index=True,
                )

                csv_data = build_csv(
                    [
                        "Job",
                        "Client",
                        "Status",
                        "Department",
                        "Openings",
                        "Currency",
                        "Budget",
                        "Opened",
                        "Closing",
                    ],
                    job_rows,
                )

                st.download_button(
                    "Download Jobs CSV",
                    data=csv_data,
                    file_name="averra_jobs_report.csv",
                    mime="text/csv",
                    key="reports_jobs_csv",
                )

            else:

                st.info(
                    "No jobs match the current filters."
                )

        # ====================================================
        # PLACEMENTS
        # ====================================================

        with tab_placements:

            st.subheader(
                "Placements"
            )

            placement_statuses = {
                "Total": len(
                    filtered_placements
                ),
                "Active": len(
                    [
                        p
                        for p in filtered_placements
                        if get_status(p)
                        == "Active"
                    ]
                ),
                "Scheduled": len(
                    [
                        p
                        for p in filtered_placements
                        if get_status(p)
                        == "Scheduled"
                    ]
                ),
                "Completed": len(
                    [
                        p
                        for p in filtered_placements
                        if get_status(p)
                        == "Completed"
                    ]
                ),
                "Terminated": len(
                    [
                        p
                        for p in filtered_placements
                        if get_status(p)
                        == "Terminated"
                    ]
                ),
            }

            pc1, pc2, pc3, pc4, pc5 = st.columns(
                5
            )

            with pc1:
                st.metric(
                    "Total",
                    placement_statuses["Total"],
                )

            with pc2:
                st.metric(
                    "Active",
                    placement_statuses["Active"],
                )

            with pc3:
                st.metric(
                    "Scheduled",
                    placement_statuses["Scheduled"],
                )

            with pc4:
                st.metric(
                    "Completed",
                    placement_statuses["Completed"],
                )

            with pc5:
                st.metric(
                    "Terminated",
                    placement_statuses["Terminated"],
                )

            st.markdown(
                "### Placement Register"
            )

            placement_rows = []

            for placement in filtered_placements:

                client = getattr(
                    placement,
                    "client",
                    None,
                )

                employee = getattr(
                    placement,
                    "employee",
                    None,
                )

                job = getattr(
                    placement,
                    "job",
                    None,
                )

                currency = get_currency(
                    placement
                )

                revenue = get_placement_client_fee(
                    placement
                )

                cost = get_placement_worker_cost(
                    placement
                )

                margin = (
                    revenue - cost
                )

                margin_pct = (
                    margin / revenue * 100
                    if revenue > 0
                    else 0
                )

                placement_rows.append(
                    [
                        getattr(
                            placement,
                            "id",
                            "",
                        ),
                        get_client_name(
                            client
                        ),
                        get_employee_name(
                            employee
                        ),
                        clean_text(
                            getattr(
                                placement,
                                "position",
                                "",
                            )
                        ),
                        get_job_label(
                            job
                        ),
                        get_status(
                            placement
                        ),
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
                        currency,
                        revenue,
                        cost,
                        margin,
                        f"{margin_pct:.1f}%",
                    ]
                )

            if placement_rows:

                st.dataframe(
                    placement_rows,
                    column_config={
                        0: "ID",
                        1: "Client",
                        2: "Employee",
                        3: "Position",
                        4: "Job",
                        5: "Status",
                        6: "Start",
                        7: "End",
                        8: "Currency",
                        9: "Revenue",
                        10: "Worker Cost",
                        11: "Margin",
                        12: "Margin %",
                    },
                    use_container_width=True,
                    hide_index=True,
                )

                csv_data = build_csv(
                    [
                        "ID",
                        "Client",
                        "Employee",
                        "Position",
                        "Job",
                        "Status",
                        "Start",
                        "End",
                        "Currency",
                        "Revenue",
                        "Worker Cost",
                        "Margin",
                        "Margin %",
                    ],
                    placement_rows,
                )

                st.download_button(
                    "Download Placements CSV",
                    data=csv_data,
                    file_name=(
                        "averra_placements_report.csv"
                    ),
                    mime="text/csv",
                    key="reports_placements_csv",
                )

            else:

                st.info(
                    "No placements match the current filters."
                )

        # ====================================================
        # FINANCIALS
        # ====================================================

        with tab_financials:

            st.subheader(
                "Financial Overview"
            )

            f1, f2, f3 = st.columns(
                3
            )

            with f1:

                st.metric(
                    "Active Revenue",
                    format_currency_amounts(
                        placement_revenue_by_currency
                    ),
                )

            with f2:

                st.metric(
                    "Active Worker Cost",
                    format_currency_amounts(
                        placement_cost_by_currency
                    ),
                )

            with f3:

                st.metric(
                    "Active Margin",
                    format_currency_amounts(
                        placement_margin_by_currency
                    ),
                )

            st.markdown(
                "### Invoice Collection"
            )

            collection_rows = []

            for currency in CURRENCIES:

                total = invoice_total_by_currency.get(
                    currency,
                    0.0,
                )

                paid = paid_by_currency.get(
                    currency,
                    0.0,
                )

                outstanding = outstanding_by_currency.get(
                    currency,
                    0.0,
                )

                collection_rate = (
                    paid / total * 100
                    if total > 0
                    else 0
                )

                collection_rows.append(
                    [
                        currency,
                        total,
                        paid,
                        outstanding,
                        f"{collection_rate:.1f}%",
                    ]
                )

            st.dataframe(
                collection_rows,
                column_config={
                    0: "Currency",
                    1: "Invoice Total",
                    2: "Paid",
                    3: "Outstanding",
                    4: "Collection Rate",
                },
                use_container_width=True,
                hide_index=True,
            )

            st.markdown(
                "### Margin Analysis"
            )

            margin_rows = []

            for placement in filtered_placements:

                revenue = get_placement_client_fee(
                    placement
                )

                cost = get_placement_worker_cost(
                    placement
                )

                margin = revenue - cost

                margin_pct = (
                    margin / revenue * 100
                    if revenue > 0
                    else 0
                )

                margin_rows.append(
                    [
                        getattr(
                            placement,
                            "id",
                            "",
                        ),
                        clean_text(
                            getattr(
                                placement,
                                "position",
                                "",
                            )
                        ),
                        get_currency(
                            placement
                        ),
                        revenue,
                        cost,
                        margin,
                        f"{margin_pct:.1f}%",
                    ]
                )

            if margin_rows:

                st.dataframe(
                    margin_rows,
                    column_config={
                        0: "Placement ID",
                        1: "Position",
                        2: "Currency",
                        3: "Revenue",
                        4: "Cost",
                        5: "Margin",
                        6: "Margin %",
                    },
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No placement financial data available."
                )

        # ====================================================
        # CONTRACTS
        # ====================================================

        with tab_contracts:

            st.subheader(
                "Contracts"
            )

            contract_counts = count_by_status(
                filtered_contracts
            )

            if contract_counts:

                st.bar_chart(
                    contract_counts
                )

                for status, count in sorted(
                    contract_counts.items()
                ):

                    st.write(
                        f"**{status}:** {count}"
                    )

            else:

                st.info(
                    "No contracts match the current filters."
                )

            st.markdown(
                "### Contract Register"
            )

            contract_rows = []

            for contract in filtered_contracts:

                client = getattr(
                    contract,
                    "client",
                    None,
                )

                placement = getattr(
                    contract,
                    "placement",
                    None,
                )

                contract_rows.append(
                    [
                        get_contract_number(
                            contract
                        ),
                        get_client_name(
                            client
                        ),
                        clean_text(
                            getattr(
                                contract,
                                "contract_type",
                                "",
                            )
                        ),
                        get_status(
                            contract
                        ),
                        get_currency(
                            contract
                        ),
                        safe_float(
                            getattr(
                                contract,
                                "contract_value",
                                0,
                            )
                        ),
                        format_date(
                            getattr(
                                contract,
                                "start_date",
                                None,
                            )
                        ),
                        format_date(
                            getattr(
                                contract,
                                "end_date",
                                None,
                            )
                        ),
                        format_date(
                            getattr(
                                contract,
                                "signed_date",
                                None,
                            )
                        ),
                        format_date(
                            getattr(
                                contract,
                                "renewal_date",
                                None,
                            )
                        ),
                        getattr(
                            placement,
                            "id",
                            "",
                        )
                        if placement
                        else "",
                    ]
                )

            if contract_rows:

                st.dataframe(
                    contract_rows,
                    column_config={
                        0: "Contract",
                        1: "Client",
                        2: "Type",
                        3: "Status",
                        4: "Currency",
                        5: "Value",
                        6: "Start",
                        7: "End",
                        8: "Signed",
                        9: "Renewal",
                        10: "Placement ID",
                    },
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No contracts match the current filters."
                )

        # ====================================================
        # INVOICES
        # ====================================================

        with tab_invoices:

            st.subheader(
                "Invoices"
            )

            i1, i2, i3 = st.columns(
                3
            )

            with i1:

                st.metric(
                    "Invoice Total",
                    format_currency_amounts(
                        invoice_total_by_currency
                    ),
                )

            with i2:

                st.metric(
                    "Paid",
                    format_currency_amounts(
                        paid_by_currency
                    ),
                )

            with i3:

                st.metric(
                    "Outstanding",
                    format_currency_amounts(
                        outstanding_by_currency
                    ),
                )

            invoice_counts = count_by_status(
                filtered_invoices
            )

            st.markdown(
                "### Invoice Status"
            )

            if invoice_counts:

                st.bar_chart(
                    invoice_counts
                )

                for status, count in sorted(
                    invoice_counts.items()
                ):

                    st.write(
                        f"**{status}:** {count}"
                    )

            else:

                st.info(
                    "No invoices match the current filters."
                )

            st.markdown(
                "### Invoice Register"
            )

            invoice_rows = []

            for invoice in filtered_invoices:

                client = getattr(
                    invoice,
                    "client",
                    None,
                )

                placement = getattr(
                    invoice,
                    "placement",
                    None,
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

                overdue_days = get_invoice_overdue_days(
                    invoice,
                    today,
                )

                invoice_rows.append(
                    [
                        get_invoice_number(
                            invoice
                        ),
                        get_client_name(
                            client
                        ),
                        clean_text(
                            getattr(
                                invoice,
                                "description",
                                "",
                            )
                        ),
                        get_status(
                            invoice
                        ),
                        get_currency(
                            invoice
                        ),
                        total,
                        paid,
                        balance,
                        format_date(
                            getattr(
                                invoice,
                                "issue_date",
                                None,
                            )
                        ),
                        format_date(
                            getattr(
                                invoice,
                                "due_date",
                                None,
                            )
                        ),
                        overdue_days,
                        getattr(
                            placement,
                            "id",
                            "",
                        )
                        if placement
                        else "",
                    ]
                )

            if invoice_rows:

                st.dataframe(
                    invoice_rows,
                    column_config={
                        0: "Invoice",
                        1: "Client",
                        2: "Description",
                        3: "Status",
                        4: "Currency",
                        5: "Total",
                        6: "Paid",
                        7: "Outstanding",
                        8: "Issue Date",
                        9: "Due Date",
                        10: "Overdue Days",
                        11: "Placement ID",
                    },
                    use_container_width=True,
                    hide_index=True,
                )

                csv_data = build_csv(
                    [
                        "Invoice",
                        "Client",
                        "Description",
                        "Status",
                        "Currency",
                        "Total",
                        "Paid",
                        "Outstanding",
                        "Issue Date",
                        "Due Date",
                        "Overdue Days",
                        "Placement ID",
                    ],
                    invoice_rows,
                )

                st.download_button(
                    "Download Invoices CSV",
                    data=csv_data,
                    file_name=(
                        "averra_invoices_report.csv"
                    ),
                    mime="text/csv",
                    key="reports_invoices_csv",
                )

            else:

                st.info(
                    "No invoices match the current filters."
                )

        # ====================================================
        # PAYMENTS
        # ====================================================

        with tab_payments:

            st.subheader(
                "Payments"
            )

            received_total = {}
            non_received_total = {}

            for payment in filtered_payments:

                currency = get_currency(
                    payment
                )

                amount = get_payment_amount(
                    payment
                )

                status = get_payment_status(
                    payment
                )

                if status in PAYMENT_SUCCESS_STATUSES:

                    add_currency_value(
                        received_total,
                        currency,
                        amount,
                    )

                else:

                    add_currency_value(
                        non_received_total,
                        currency,
                        amount,
                    )

            p1, p2 = st.columns(
                2
            )

            with p1:

                st.metric(
                    "Received",
                    format_currency_amounts(
                        received_total
                    ),
                )

            with p2:

                st.metric(
                    "Pending / Failed / Reversed",
                    format_currency_amounts(
                        non_received_total
                    ),
                )

            payment_counts = count_by_status(
                filtered_payments
            )

            st.markdown(
                "### Payment Status"
            )

            if payment_counts:

                st.bar_chart(
                    payment_counts
                )

                for status, count in sorted(
                    payment_counts.items()
                ):

                    st.write(
                        f"**{status}:** {count}"
                    )

            else:

                st.info(
                    "No payments match the current filters."
                )

            st.markdown(
                "### Payment Register"
            )

            payment_rows = []

            for payment in filtered_payments:

                invoice = getattr(
                    payment,
                    "invoice",
                    None,
                )

                reference = (
                    clean_text(
                        getattr(
                            payment,
                            "reference",
                            "",
                        )
                    )
                    or clean_text(
                        getattr(
                            payment,
                            "payment_reference",
                            "",
                        )
                    )
                )

                payment_rows.append(
                    [
                        getattr(
                            payment,
                            "id",
                            "",
                        ),
                        get_invoice_number(
                            invoice
                        ),
                        get_payment_status(
                            payment
                        ),
                        get_currency(
                            payment
                        ),
                        get_payment_amount(
                            payment
                        ),
                        format_date(
                            get_payment_date(
                                payment
                            )
                        ),
                        reference,
                    ]
                )

            if payment_rows:

                st.dataframe(
                    payment_rows,
                    column_config={
                        0: "ID",
                        1: "Invoice",
                        2: "Status",
                        3: "Currency",
                        4: "Amount",
                        5: "Payment Date",
                        6: "Reference",
                    },
                    use_container_width=True,
                    hide_index=True,
                )

                csv_data = build_csv(
                    [
                        "ID",
                        "Invoice",
                        "Status",
                        "Currency",
                        "Amount",
                        "Payment Date",
                        "Reference",
                    ],
                    payment_rows,
                )

                st.download_button(
                    "Download Payments CSV",
                    data=csv_data,
                    file_name=(
                        "averra_payments_report.csv"
                    ),
                    mime="text/csv",
                    key="reports_payments_csv",
                )

            else:

                st.info(
                    "No payments match the current filters."
                )

        # ====================================================
        # CLIENT PERFORMANCE
        # ====================================================

        with tab_clients:

            st.subheader(
                "Client Performance"
            )

            sort_option = st.selectbox(
                "Sort Clients",
                CLIENT_SORT_OPTIONS,
                key="reports_client_sort",
            )

            client_performance = []

            for client in filtered_clients:

                client_id = getattr(
                    client,
                    "id",
                    None,
                )

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
                    for candidate in filtered_candidates
                    if get_client_id_from_candidate(
                        candidate
                    )
                    == client_id
                ]

                client_placements = [
                    placement
                    for placement in filtered_placements
                    if get_client_id_from_placement(
                        placement
                    )
                    == client_id
                ]

                client_active_placements = [
                    placement
                    for placement in client_placements
                    if get_status(
                        placement
                    ) == "Active"
                ]

                client_invoices = [
                    invoice
                    for invoice in filtered_invoices
                    if get_client_id_from_invoice(
                        invoice
                    )
                    == client_id
                ]

                client_payments = [
                    payment
                    for payment in filtered_payments
                    if get_client_id_from_payment(
                        payment
                    )
                    == client_id
                ]

                revenue_by_currency = {}
                margin_by_currency = {}
                outstanding_by_currency_client = {}
                received_by_currency_client = {}

                for placement in client_active_placements:

                    currency = get_currency(
                        placement
                    )

                    revenue = get_placement_client_fee(
                        placement
                    )

                    margin = get_placement_margin(
                        placement
                    )

                    add_currency_value(
                        revenue_by_currency,
                        currency,
                        revenue,
                    )

                    add_currency_value(
                        margin_by_currency,
                        currency,
                        margin,
                    )

                for invoice in client_invoices:

                    currency = get_currency(
                        invoice
                    )

                    balance = get_invoice_balance(
                        invoice
                    )

                    add_currency_value(
                        outstanding_by_currency_client,
                        currency,
                        balance,
                    )

                for payment in client_payments:

                    if (
                        get_payment_status(
                            payment
                        )
                        not in PAYMENT_SUCCESS_STATUSES
                    ):
                        continue

                    currency = get_currency(
                        payment
                    )

                    amount = get_payment_amount(
                        payment
                    )

                    add_currency_value(
                        received_by_currency_client,
                        currency,
                        amount,
                    )

                client_performance.append(
                    {
                        "name": get_client_name(
                            client
                        ),
                        "jobs": len(
                            client_jobs
                        ),
                        "candidates": len(
                            client_candidates
                        ),
                        "placements": len(
                            client_placements
                        ),
                        "active_placements": len(
                            client_active_placements
                        ),
                        "invoices": len(
                            client_invoices
                        ),
                        "revenue": revenue_by_currency,
                        "margin": margin_by_currency,
                        "outstanding": outstanding_by_currency_client,
                        "received": received_by_currency_client,
                    }
                )

            if sort_option == "Client A-Z":

                client_performance.sort(
                    key=lambda item: item[
                        "name"
                    ].lower()
                )

            elif sort_option == "Revenue - Highest":

                client_performance.sort(
                    key=lambda item: sum(
                        item[
                            "revenue"
                        ].values()
                    ),
                    reverse=True,
                )

            elif sort_option == "Outstanding - Highest":

                client_performance.sort(
                    key=lambda item: sum(
                        item[
                            "outstanding"
                        ].values()
                    ),
                    reverse=True,
                )

            elif sort_option == "Margin - Highest":

                client_performance.sort(
                    key=lambda item: sum(
                        item[
                            "margin"
                        ].values()
                    ),
                    reverse=True,
                )

            elif sort_option == "Jobs - Highest":

                client_performance.sort(
                    key=lambda item: item[
                        "jobs"
                    ],
                    reverse=True,
                )

            elif sort_option == "Placements - Highest":

                client_performance.sort(
                    key=lambda item: item[
                        "placements"
                    ],
                    reverse=True,
                )

            client_rows = []

            for item in client_performance:

                client_rows.append(
                    [
                        item["name"],
                        item["jobs"],
                        item["candidates"],
                        item["placements"],
                        item["active_placements"],
                        item["invoices"],
                        format_currency_amounts(
                            item["revenue"]
                        ),
                        format_currency_amounts(
                            item["margin"]
                        ),
                        format_currency_amounts(
                            item["outstanding"]
                        ),
                        format_currency_amounts(
                            item["received"]
                        ),
                    ]
                )

            if client_rows:

                st.dataframe(
                    client_rows,
                    column_config={
                        0: "Client",
                        1: "Jobs",
                        2: "Candidates",
                        3: "Placements",
                        4: "Active Placements",
                        5: "Invoices",
                        6: "Active Revenue",
                        7: "Active Margin",
                        8: "Outstanding",
                        9: "Received",
                    },
                    use_container_width=True,
                    hide_index=True,
                )

                csv_data = build_csv(
                    [
                        "Client",
                        "Jobs",
                        "Candidates",
                        "Placements",
                        "Active Placements",
                        "Invoices",
                        "Active Revenue",
                        "Active Margin",
                        "Outstanding",
                        "Received",
                    ],
                    client_rows,
                )

                st.download_button(
                    "Download Client Performance CSV",
                    data=csv_data,
                    file_name=(
                        "averra_client_performance.csv"
                    ),
                    mime="text/csv",
                    key="reports_client_performance_csv",
                )

            else:

                st.info(
                    "No clients match the current filters."
                )

        # ====================================================
        # DATA QUALITY
        # ====================================================

        with tab_quality:

            st.subheader(
                "Data Quality"
            )

            quality_scope = st.selectbox(
                "Quality Check Scope",
                QUALITY_SCOPES,
                key="reports_quality_scope",
            )

            if quality_scope == "Current Filters":

                quality_clients = filtered_clients
                quality_employees = filtered_employees
                quality_jobs = filtered_jobs
                quality_candidates = filtered_candidates
                quality_placements = filtered_placements
                quality_contracts = filtered_contracts
                quality_invoices = filtered_invoices
                quality_payments = filtered_payments

            else:

                quality_clients = clients
                quality_employees = employees
                quality_jobs = jobs
                quality_candidates = candidates
                quality_placements = placements
                quality_contracts = contracts
                quality_invoices = invoices
                quality_payments = payments

            quality_issues = collect_quality_issues(
                quality_clients,
                quality_employees,
                quality_jobs,
                quality_candidates,
                quality_placements,
                quality_contracts,
                quality_invoices,
                quality_payments,
                today,
            )

            total_issues = sum(
                len(values)
                for values in quality_issues.values()
            )

            q1, q2 = st.columns(
                2
            )

            with q1:

                st.metric(
                    "Total Issues",
                    total_issues,
                )

            with q2:

                affected_categories = sum(
                    1
                    for values in quality_issues.values()
                    if values
                )

                st.metric(
                    "Affected Areas",
                    affected_categories,
                )

            if total_issues == 0:

                st.success(
                    "No data-quality issues were detected in the selected scope."
                )

            else:

                for category, category_issues in quality_issues.items():

                    if not category_issues:
                        continue

                    st.markdown(
                        f"### {category} "
                        f"({len(category_issues)})"
                    )

                    with st.expander(
                        f"View {category.lower()} issues"
                    ):

                        for issue in category_issues:

                            st.write(
                                f"• {issue}"
                            )

            st.caption(
                "Data-quality checks are advisory and are based "
                "on the fields currently available in the AVERRA CRM models."
            )

        # ====================================================
        # FOOTER
        # ====================================================

        st.divider()

        st.caption(
            "AVERRA CRM Reports"
        )

        st.caption(
            f"Report generated: {today.strftime('%d/%m/%Y')}"
        )

        st.caption(
            "Financial values remain separated by currency "
            "and are not converted between GBP, EUR, USD and INR."
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