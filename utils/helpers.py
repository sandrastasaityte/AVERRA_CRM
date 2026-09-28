from pathlib import Path
from datetime import date, datetime
import re


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_text(value):
    """
    Convert a value to clean text.

    None becomes an empty string.
    """
    if value is None:
        return ""

    return str(value).strip()


def normalise_text(value):
    """
    Normalise text for searching and comparisons.
    """
    return clean_text(value).casefold()


def truncate_text(
    value,
    max_length=80,
):
    """
    Shorten long text for display.
    """
    text = clean_text(value)

    if len(text) <= max_length:
        return text

    if max_length <= 3:
        return text[:max_length]

    return text[: max_length - 3] + "..."


def build_full_name(
    first_name="",
    last_name="",
):
    """
    Build a person's full name safely.
    """
    first = clean_text(first_name)
    last = clean_text(last_name)

    return " ".join(
        part
        for part in [first, last]
        if part
    )


# ============================================================
# VALIDATION HELPERS
# ============================================================

def valid_email(email):
    """
    Perform basic email validation.
    """
    email = clean_text(email)

    if not email:
        return False

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(
        re.match(
            pattern,
            email,
        )
    )


def valid_url(url):
    """
    Perform basic URL validation.
    """
    url = clean_text(url)

    if not url:
        return False

    return (
        url.startswith("http://")
        or url.startswith("https://")
    )


def is_positive_number(value):
    """
    Return True when value can be converted to a
    number greater than or equal to zero.
    """
    try:
        return float(value) >= 0
    except (TypeError, ValueError):
        return False


def is_positive_integer(value):
    """
    Return True when value is an integer greater than
    or equal to 1.
    """
    try:
        return int(value) >= 1
    except (TypeError, ValueError):
        return False


# ============================================================
# DATE HELPERS
# ============================================================

def format_date(
    value,
    empty_value="",
):
    """
    Format date/datetime values as YYYY-MM-DD.
    """
    if value is None:
        return empty_value

    if isinstance(value, datetime):
        return value.strftime(
            "%Y-%m-%d"
        )

    if isinstance(value, date):
        return value.strftime(
            "%Y-%m-%d"
        )

    return clean_text(value)


def format_datetime(
    value,
    empty_value="",
):
    """
    Format datetime values for display.
    """
    if value is None:
        return empty_value

    if isinstance(value, datetime):
        return value.strftime(
            "%Y-%m-%d %H:%M"
        )

    if isinstance(value, date):
        return value.strftime(
            "%Y-%m-%d"
        )

    return clean_text(value)


def to_date(value):
    """
    Safely convert a value to a date.

    Supports:
    - date
    - datetime
    - YYYY-MM-DD strings

    Returns None when conversion fails.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    value = clean_text(value)

    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()

    except ValueError:
        return None


def is_past_date(value):
    """
    Return True if a date is before today.
    """
    value = to_date(value)

    if value is None:
        return False

    return value < date.today()


def is_future_date(value):
    """
    Return True if a date is after today.
    """
    value = to_date(value)

    if value is None:
        return False

    return value > date.today()


def is_today(value):
    """
    Return True if a date is today.
    """
    value = to_date(value)

    if value is None:
        return False

    return value == date.today()


def days_from_today(value):
    """
    Return number of days from today.

    Positive = future
    Zero = today
    Negative = past
    """
    value = to_date(value)

    if value is None:
        return None

    return (
        value - date.today()
    ).days


# ============================================================
# MONEY / NUMBER HELPERS
# ============================================================

def to_float(
    value,
    default=0.0,
):
    """
    Safely convert a value to float.
    """
    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def to_int(
    value,
    default=0,
):
    """
    Safely convert a value to integer.
    """
    try:
        if value is None:
            return default

        return int(value)

    except (TypeError, ValueError):
        return default


def format_money(
    amount,
    currency="GBP",
    decimals=2,
):
    """
    Format a monetary amount.

    Examples:
        format_money(1250, "GBP")
        -> £1,250.00

        format_money(1250, "EUR")
        -> €1,250.00
    """
    amount = to_float(amount)

    currency = clean_text(
        currency
    ).upper()

    symbols = {
        "GBP": "£",
        "EUR": "€",
        "USD": "$",
        "INR": "₹",
    }

    symbol = symbols.get(
        currency,
        currency,
    )

    if symbol:
        return (
            f"{symbol}"
            f"{amount:,.{decimals}f}"
        )

    return (
        f"{amount:,.{decimals}f}"
    )


def format_percentage(
    value,
    decimals=1,
):
    """
    Format a percentage value.

    Example:
        format_percentage(25.5)
        -> 25.5%
    """
    value = to_float(value)

    return (
        f"{value:.{decimals}f}%"
    )


# ============================================================
# MODEL / OBJECT HELPERS
# ============================================================

def safe_getattr(
    obj,
    attribute,
    default="",
):
    """
    Safely retrieve an attribute from an object.
    """
    if obj is None:
        return default

    return getattr(
        obj,
        attribute,
        default,
    )


def get_client_name(client):
    """
    Return a client's company name.
    """
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
    """
    Return an employee's full name.
    """
    if not employee:
        return "Unknown Employee"

    name = build_full_name(
        getattr(
            employee,
            "first_name",
            "",
        ),
        getattr(
            employee,
            "last_name",
            "",
        ),
    )

    return (
        name
        or "Unknown Employee"
    )


def get_contact_name(contact):
    """
    Return a client's contact full name.
    """
    if not contact:
        return "Unknown Contact"

    name = build_full_name(
        getattr(
            contact,
            "first_name",
            "",
        ),
        getattr(
            contact,
            "last_name",
            "",
        ),
    )

    return (
        name
        or "Unknown Contact"
    )


def get_job_label(job):
    """
    Return a readable job label.
    """
    if not job:
        return "Unknown Job"

    position = clean_text(
        getattr(
            job,
            "position",
            "",
        )
    )

    client = getattr(
        job,
        "client",
        None,
    )

    client_name = get_client_name(
        client
    )

    if (
        position
        and client_name != "Unknown Client"
    ):
        return (
            f"{position} — "
            f"{client_name}"
        )

    if position:
        return position

    return "Unknown Job"


def get_placement_label(placement):
    """
    Return a readable placement label.
    """
    if not placement:
        return "Unknown Placement"

    position = clean_text(
        getattr(
            placement,
            "position",
            "",
        )
    )

    employee = getattr(
        placement,
        "employee",
        None,
    )

    client = getattr(
        placement,
        "client",
        None,
    )

    employee_name = get_employee_name(
        employee
    )

    client_name = get_client_name(
        client
    )

    parts = []

    if position:
        parts.append(position)

    if employee_name != "Unknown Employee":
        parts.append(employee_name)

    if client_name != "Unknown Client":
        parts.append(client_name)

    if parts:
        return " — ".join(parts)

    return "Unknown Placement"


def get_contract_label(contract):
    """
    Return a readable contract label.
    """
    if not contract:
        return "Unknown Contract"

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

    if (
        contract_number
        and contract_type
    ):
        return (
            f"{contract_number} — "
            f"{contract_type}"
        )

    return (
        contract_number
        or contract_type
        or "Unknown Contract"
    )


def get_invoice_label(invoice):
    """
    Return a readable invoice label.
    """
    if not invoice:
        return "Unknown Invoice"

    invoice_number = clean_text(
        getattr(
            invoice,
            "invoice_number",
            "",
        )
    )

    client = getattr(
        invoice,
        "client",
        None,
    )

    client_name = get_client_name(
        client
    )

    if (
        invoice_number
        and client_name != "Unknown Client"
    ):
        return (
            f"{invoice_number} — "
            f"{client_name}"
        )

    return (
        invoice_number
        or "Unknown Invoice"
    )


def get_candidate_label(candidate):
    """
    Return a readable candidate label.
    """
    if not candidate:
        return "Unknown Candidate"

    employee = getattr(
        candidate,
        "employee",
        None,
    )

    job = getattr(
        candidate,
        "job",
        None,
    )

    employee_name = get_employee_name(
        employee
    )

    job_label = get_job_label(
        job
    )

    if (
        employee_name != "Unknown Employee"
        and job_label != "Unknown Job"
    ):
        return (
            f"{employee_name} — "
            f"{job_label}"
        )

    if employee_name != "Unknown Employee":
        return employee_name

    if job_label != "Unknown Job":
        return job_label

    return "Unknown Candidate"


def get_payment_label(payment):
    """
    Return a readable payment label.
    """
    if not payment:
        return "Unknown Payment"

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

    formatted_date = format_date(
        payment_date
    )

    if reference and formatted_date:
        return (
            f"{reference} — "
            f"{formatted_date}"
        )

    return (
        reference
        or formatted_date
        or "Unknown Payment"
    )


# ============================================================
# STATUS HELPERS
# ============================================================

def get_status_icon(status):
    """
    Return a simple icon for common CRM statuses.
    """
    status = normalise_text(
        status
    )

    icons = {
        # Positive / active
        "active": "🟢",
        "available": "🟢",
        "won": "🟢",
        "placed": "🟢",
        "paid": "🟢",
        "received": "🟢",
        "completed": "🟢",
        "signed": "🟢",

        # In progress / neutral
        "scheduled": "🔵",
        "submitted": "🔵",
        "shortlisted": "🔵",
        "interview": "🔵",
        "open": "🔵",
        "draft": "🔵",
        "pending": "🔵",

        # Waiting / attention
        "contacted": "🟡",
        "replied": "🟡",
        "call": "🟡",
        "proposal": "🟡",
        "negotiation": "🟡",
        "offer": "🟡",
        "on hold": "🟡",
        "interviewing": "🟡",

        # Negative / closed
        "lost": "🔴",
        "rejected": "🔴",
        "withdrawn": "🔴",
        "terminated": "🔴",
        "expired": "🔴",
        "failed": "🔴",
        "overdue": "🔴",
        "cancelled": "🔴",
        "unavailable": "🔴",
        "former employee": "🔴",

        # Other attention states
        "on leave": "🟠",
        "reversed": "🟠",
        "partially paid": "🟠",
    }

    return icons.get(
        status,
        "⚪",
    )


def format_status(status):
    """
    Return status with a visual icon.
    """
    status = clean_text(
        status
    )

    if not status:
        return "⚪ Unknown"

    return (
        f"{get_status_icon(status)} "
        f"{status}"
    )


# ============================================================
# SEARCH HELPERS
# ============================================================

def matches_search(
    value,
    search_term,
):
    """
    Case-insensitive search helper.
    """
    search_term = normalise_text(
        search_term
    )

    if not search_term:
        return True

    return (
        search_term
        in normalise_text(value)
    )


def object_matches_search(
    obj,
    search_term,
    fields,
):
    """
    Search multiple object fields.

    Example:

        object_matches_search(
            client,
            "acme",
            [
                "company_name",
                "city",
                "industry",
            ],
        )
    """

    search_term = normalise_text(
        search_term
    )

    if not search_term:
        return True

    if obj is None:
        return False

    for field in fields:

        value = getattr(
            obj,
            field,
            "",
        )

        if (
            search_term
            in normalise_text(value)
        ):
            return True

    return False


def build_search_text(
    obj,
    fields,
):
    """
    Build one searchable text string from
    multiple object fields.
    """
    if obj is None:
        return ""

    values = []

    for field in fields:

        value = getattr(
            obj,
            field,
            "",
        )

        value = clean_text(
            value
        )

        if value:
            values.append(value)

    return " ".join(values)


# ============================================================
# LIST / COLLECTION HELPERS
# ============================================================

def unique_values(values):
    """
    Return unique non-empty values while
    preserving original order.
    """
    result = []
    seen = set()

    for value in values or []:

        cleaned = clean_text(
            value
        )

        if not cleaned:
            continue

        key = normalise_text(
            cleaned
        )

        if key not in seen:
            seen.add(key)
            result.append(cleaned)

    return result


def sort_by_attribute(
    records,
    attribute,
    reverse=False,
):
    """
    Safely sort model records by an attribute.

    Text values are normalised before sorting.
    """
    return sorted(
        list(records or []),
        key=lambda item: normalise_text(
            getattr(
                item,
                attribute,
                "",
            )
        ),
        reverse=reverse,
    )


def sort_by_date(
    records,
    attribute,
    reverse=False,
):
    """
    Safely sort records by a date attribute.

    Missing dates are placed at the end.
    """

    def sort_key(item):
        value = getattr(
            item,
            attribute,
            None,
        )

        parsed = to_date(value)

        if parsed is None:
            return date.min

        return parsed

    return sorted(
        list(records or []),
        key=sort_key,
        reverse=reverse,
    )


# ============================================================
# DISPLAY HELPERS
# ============================================================

def display_or_dash(value):
    """
    Display a dash when a value is empty.
    """
    value = clean_text(value)

    return (
        value
        if value
        else "—"
    )


def display_yes_no(value):
    """
    Convert a boolean into Yes/No.
    """
    return (
        "Yes"
        if bool(value)
        else "No"
    )


def display_count(value):
    """
    Format an integer count.
    """
    return f"{to_int(value):,}"


# ============================================================
# CRM FINANCIAL HELPERS
# ============================================================

def get_balance_due(invoice):
    """
    Calculate the outstanding invoice balance.
    """
    if not invoice:
        return 0.0

    total = to_float(
        getattr(
            invoice,
            "total_amount",
            0,
        )
    )

    paid = to_float(
        getattr(
            invoice,
            "amount_paid",
            0,
        )
    )

    return max(
        total - paid,
        0.0,
    )


def get_invoice_payment_percentage(
    invoice,
):
    """
    Calculate the percentage of an invoice paid.
    """
    if not invoice:
        return 0.0

    total = to_float(
        getattr(
            invoice,
            "total_amount",
            0,
        )
    )

    paid = to_float(
        getattr(
            invoice,
            "amount_paid",
            0,
        )
    )

    if total == 0:
        return 0.0

    return (
        paid / total
    ) * 100


def get_margin(placement):
    """
    Calculate placement gross margin.
    """
    if not placement:
        return 0.0

    revenue = to_float(
        getattr(
            placement,
            "client_monthly_fee",
            0,
        )
    )

    cost = to_float(
        getattr(
            placement,
            "worker_monthly_cost",
            0,
        )
    )

    return revenue - cost


def get_margin_percentage(
    placement,
):
    """
    Calculate placement gross margin percentage.
    """
    revenue = to_float(
        getattr(
            placement,
            "client_monthly_fee",
            0,
        )
    )

    if revenue == 0:
        return 0.0

    return (
        get_margin(placement)
        / revenue
    ) * 100


def is_invoice_overdue(
    invoice,
):
    """
    Determine whether an invoice is currently overdue.

    Paid and Cancelled invoices are not considered overdue.
    """
    if not invoice:
        return False

    status = normalise_text(
        getattr(
            invoice,
            "status",
            "",
        )
    )

    if status in {
        "paid",
        "cancelled",
    }:
        return False

    due_date = getattr(
        invoice,
        "due_date",
        None,
    )

    due_date = to_date(
        due_date
    )

    if due_date is None:
        return False

    balance = get_balance_due(
        invoice
    )

    return (
        due_date < date.today()
        and balance > 0
    )


def get_days_overdue(
    invoice,
):
    """
    Return the number of days an invoice is overdue.

    Returns 0 when it is not overdue.
    """
    if not invoice:
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

    if not is_invoice_overdue(
        invoice
    ):
        return 0

    return max(
        (
            date.today()
            - due_date
        ).days,
        0,
    )


# ============================================================
# EXPORT / FILE HELPERS
# ============================================================

def get_project_root():
    """
    Return the AVERRA CRM project root.
    """
    return Path(
        __file__
    ).resolve().parent.parent


def get_data_folder():
    """
    Return the AVERRA CRM data folder.
    """
    return (
        get_project_root()
        / "data"
    )


def get_exports_folder():
    """
    Return the AVERRA CRM exports folder.
    """
    folder = (
        get_data_folder()
        / "exports"
    )

    folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    return folder


# ============================================================
# GENERIC DISPLAY LABEL
# ============================================================

def get_record_label(
    record,
    fallback="Unknown Record",
):
    """
    Try to produce a readable label for a CRM record.

    Useful when a screen needs a generic label.
    """

    if not record:
        return fallback

    # Client
    company_name = clean_text(
        getattr(
            record,
            "company_name",
            "",
        )
    )

    if company_name:
        return company_name

    # Person
    person_name = build_full_name(
        getattr(
            record,
            "first_name",
            "",
        ),
        getattr(
            record,
            "last_name",
            "",
        ),
    )

    if person_name:
        return person_name

    # Job
    position = clean_text(
        getattr(
            record,
            "position",
            "",
        )
    )

    if position:
        return position

    # Contract
    contract_number = clean_text(
        getattr(
            record,
            "contract_number",
            "",
        )
    )

    if contract_number:
        return contract_number

    # Invoice
    invoice_number = clean_text(
        getattr(
            record,
            "invoice_number",
            "",
        )
    )

    if invoice_number:
        return invoice_number

    # Generic ID
    record_id = getattr(
        record,
        "id",
        None,
    )

    if record_id is not None:
        return f"{fallback} #{record_id}"

    return fallback