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
    return clean_text(value).lower()


def truncate_text(value, max_length=80):
    """
    Shorten long text for display.
    """
    text = clean_text(value)

    if len(text) <= max_length:
        return text

    return text[: max_length - 3] + "..."


def build_full_name(first_name="", last_name=""):
    """
    Build a person's full name safely.
    """
    first = clean_text(first_name)
    last = clean_text(last_name)

    return " ".join(part for part in [first, last] if part)


# ============================================================
# VALIDATION HELPERS
# ============================================================

def valid_email(email):
    """
    Basic email validation.
    """
    email = clean_text(email)

    if not email:
        return False

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(re.match(pattern, email))


def valid_url(url):
    """
    Basic URL validation.
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
    Return True when value can be converted to a number
    greater than or equal to zero.
    """
    try:
        return float(value) >= 0
    except (TypeError, ValueError):
        return False


def is_positive_integer(value):
    """
    Return True when value is an integer greater than or equal to 1.
    """
    try:
        return int(value) >= 1
    except (TypeError, ValueError):
        return False


# ============================================================
# DATE HELPERS
# ============================================================

def format_date(value, empty_value=""):
    """
    Format date/datetime values as YYYY-MM-DD.
    """
    if value is None:
        return empty_value

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    return clean_text(value)


def format_datetime(value, empty_value=""):
    """
    Format datetime values for display.
    """
    if value is None:
        return empty_value

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    return clean_text(value)


def is_past_date(value):
    """
    Return True if a date is before today.
    """
    if value is None:
        return False

    if isinstance(value, datetime):
        value = value.date()

    if isinstance(value, date):
        return value < date.today()

    return False


def is_future_date(value):
    """
    Return True if a date is after today.
    """
    if value is None:
        return False

    if isinstance(value, datetime):
        value = value.date()

    if isinstance(value, date):
        return value > date.today()

    return False


# ============================================================
# MONEY / NUMBER HELPERS
# ============================================================

def to_float(value, default=0.0):
    """
    Safely convert a value to float.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default=0):
    """
    Safely convert a value to integer.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def format_money(amount, currency="GBP", decimals=2):
    """
    Format a monetary amount.

    Example:
        format_money(1250, "GBP")
        -> £1,250.00
    """

    amount = to_float(amount)

    symbols = {
        "GBP": "£",
        "EUR": "€",
        "USD": "$",
        "INR": "₹",
    }

    symbol = symbols.get(clean_text(currency).upper(), clean_text(currency))

    if symbol:
        return f"{symbol}{amount:,.{decimals}f}"

    return f"{amount:,.{decimals}f}"


def format_percentage(value, decimals=1):
    """
    Format a percentage value.

    Example:
        format_percentage(25.5)
        -> 25.5%
    """
    value = to_float(value)

    return f"{value:.{decimals}f}%"


# ============================================================
# MODEL / OBJECT HELPERS
# ============================================================

def safe_getattr(obj, attribute, default=""):
    """
    Safely retrieve an attribute from an object.
    """
    if obj is None:
        return default

    return getattr(obj, attribute, default)


def get_client_name(client):
    """
    Return a client's company name.
    """
    if not client:
        return "Unknown Client"

    return clean_text(
        getattr(client, "company_name", "")
    ) or "Unknown Client"


def get_employee_name(employee):
    """
    Return an employee's full name.
    """
    if not employee:
        return "Unknown Employee"

    name = build_full_name(
        getattr(employee, "first_name", ""),
        getattr(employee, "last_name", ""),
    )

    return name or "Unknown Employee"


def get_contact_name(contact):
    """
    Return a client's contact full name.
    """
    if not contact:
        return "Unknown Contact"

    name = build_full_name(
        getattr(contact, "first_name", ""),
        getattr(contact, "last_name", ""),
    )

    return name or "Unknown Contact"


def get_job_label(job):
    """
    Return a readable job label.
    """
    if not job:
        return "Unknown Job"

    position = clean_text(
        getattr(job, "position", "")
    )

    client = getattr(job, "client", None)

    client_name = get_client_name(client)

    if position and client_name != "Unknown Client":
        return f"{position} — {client_name}"

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
        getattr(placement, "position", "")
    )

    employee = getattr(placement, "employee", None)
    client = getattr(placement, "client", None)

    employee_name = get_employee_name(employee)
    client_name = get_client_name(client)

    parts = []

    if position:
        parts.append(position)

    if employee_name != "Unknown Employee":
        parts.append(employee_name)

    if client_name != "Unknown Client":
        parts.append(client_name)

    return " — ".join(parts) if parts else "Unknown Placement"


def get_contract_label(contract):
    """
    Return a readable contract label.
    """
    if not contract:
        return "Unknown Contract"

    contract_number = clean_text(
        getattr(contract, "contract_number", "")
    )

    contract_type = clean_text(
        getattr(contract, "contract_type", "")
    )

    if contract_number and contract_type:
        return f"{contract_number} — {contract_type}"

    return contract_number or contract_type or "Unknown Contract"


def get_invoice_label(invoice):
    """
    Return a readable invoice label.
    """
    if not invoice:
        return "Unknown Invoice"

    invoice_number = clean_text(
        getattr(invoice, "invoice_number", "")
    )

    client = getattr(invoice, "client", None)
    client_name = get_client_name(client)

    if invoice_number and client_name != "Unknown Client":
        return f"{invoice_number} — {client_name}"

    return invoice_number or "Unknown Invoice"


# ============================================================
# STATUS HELPERS
# ============================================================

def get_status_icon(status):
    """
    Return a simple icon for common CRM statuses.
    """
    status = clean_text(status).lower()

    icons = {
        "active": "🟢",
        "available": "🟢",
        "won": "🟢",
        "placed": "🟢",
        "paid": "🟢",
        "received": "🟢",
        "completed": "🟢",
        "signed": "🟢",

        "scheduled": "🔵",
        "submitted": "🔵",
        "shortlisted": "🔵",
        "interview": "🔵",
        "open": "🔵",
        "draft": "🔵",
        "pending": "🔵",

        "contacted": "🟡",
        "replied": "🟡",
        "call": "🟡",
        "proposal": "🟡",
        "negotiation": "🟡",
        "offer": "🟡",
        "on hold": "🟡",
        "interviewing": "🟡",

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

        "on leave": "🟠",
        "reversed": "🟠",
    }

    return icons.get(status, "⚪")


def format_status(status):
    """
    Return status with a visual icon.
    """
    status = clean_text(status)

    if not status:
        return "⚪ Unknown"

    return f"{get_status_icon(status)} {status}"


# ============================================================
# SEARCH HELPERS
# ============================================================

def matches_search(value, search_term):
    """
    Case-insensitive search helper.
    """
    search_term = normalise_text(search_term)

    if not search_term:
        return True

    return search_term in normalise_text(value)


def object_matches_search(obj, search_term, fields):
    """
    Search multiple object fields.

    Example:
        object_matches_search(
            client,
            "acme",
            ["company_name", "city", "industry"]
        )
    """
    search_term = normalise_text(search_term)

    if not search_term:
        return True

    for field in fields:
        value = getattr(obj, field, "")

        if search_term in normalise_text(value):
            return True

    return False


# ============================================================
# LIST / COLLECTION HELPERS
# ============================================================

def unique_values(values):
    """
    Return unique non-empty values while preserving order.
    """
    result = []
    seen = set()

    for value in values:
        cleaned = clean_text(value)

        if not cleaned:
            continue

        key = cleaned.lower()

        if key not in seen:
            seen.add(key)
            result.append(cleaned)

    return result


def sort_by_attribute(records, attribute, reverse=False):
    """
    Safely sort model records by an attribute.
    """
    return sorted(
        list(records or []),
        key=lambda item: normalise_text(
            getattr(item, attribute, "")
        ),
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

    return value if value else "—"


def display_yes_no(value):
    """
    Convert a boolean into Yes/No.
    """
    return "Yes" if bool(value) else "No"


def display_count(value):
    """
    Format an integer count.
    """
    return f"{to_int(value):,}"


# ============================================================
# CRM-SPECIFIC HELPERS
# ============================================================

def get_balance_due(invoice):
    """
    Calculate the outstanding invoice balance.
    """
    if not invoice:
        return 0.0

    total = to_float(
        getattr(invoice, "total_amount", 0)
    )

    paid = to_float(
        getattr(invoice, "amount_paid", 0)
    )

    return max(total - paid, 0.0)


def get_margin(placement):
    """
    Calculate placement gross margin.
    """
    if not placement:
        return 0.0

    revenue = to_float(
        getattr(placement, "client_monthly_fee", 0)
    )

    cost = to_float(
        getattr(placement, "worker_monthly_cost", 0)
    )

    return revenue - cost


def get_margin_percentage(placement):
    """
    Calculate placement gross margin percentage.
    """
    revenue = to_float(
        getattr(placement, "client_monthly_fee", 0)
    )

    if revenue == 0:
        return 0.0

    return (get_margin(placement) / revenue) * 100


def is_invoice_overdue(invoice):
    """
    Determine whether an invoice is currently overdue.
    """
    if not invoice:
        return False

    status = normalise_text(
        getattr(invoice, "status", "")
    )

    if status in {"paid", "cancelled"}:
        return False

    due_date = getattr(invoice, "due_date", None)

    if due_date is None:
        return False

    if isinstance(due_date, datetime):
        due_date = due_date.date()

    balance = get_balance_due(invoice)

    return due_date < date.today() and balance > 0


def get_days_until_date(value):
    """
    Return number of days from today until a date.

    Positive = future
    Zero = today
    Negative = past
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        value = value.date()

    if not isinstance(value, date):
        return None

    return (value - date.today()).days