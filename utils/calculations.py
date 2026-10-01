from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


# ============================================================
# CONSTANTS
# ============================================================

MONEY_DECIMAL_PLACES = 2
MONEY_QUANTIZER = Decimal("0.01")


# ============================================================
# BASIC NUMBER / MONEY HELPERS
# ============================================================

def to_float(value, default=0.0):
    """Safely convert a value to float."""
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_decimal(value, default=Decimal("0")):
    """Safely convert a value to Decimal."""
    if value is None:
        return default

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def round_money(value):
    """Round a monetary value to two decimal places."""
    decimal_value = to_decimal(value)

    return decimal_value.quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )


def money_to_float(value):
    """Convert a monetary value to float."""
    return float(round_money(value))


def safe_divide(numerator, denominator, default=0.0):
    """Safely divide two numbers."""
    numerator = to_float(numerator)
    denominator = to_float(denominator)

    if denominator == 0:
        return default

    return numerator / denominator


def percentage(numerator, denominator, default=0.0):
    """Calculate a percentage."""
    return safe_divide(
        numerator,
        denominator,
        default=default,
    ) * 100


# ============================================================
# PLACEMENT FINANCIAL CALCULATIONS
# ============================================================

def calculate_gross_margin(
    client_monthly_fee,
    worker_monthly_cost,
):
    """Calculate monthly gross margin."""
    revenue = to_float(client_monthly_fee)
    cost = to_float(worker_monthly_cost)

    return round(
        revenue - cost,
        MONEY_DECIMAL_PLACES,
    )


def calculate_gross_margin_percentage(
    client_monthly_fee,
    worker_monthly_cost,
):
    """Calculate gross margin percentage."""
    revenue = to_float(client_monthly_fee)

    if revenue <= 0:
        return 0.0

    margin = calculate_gross_margin(
        client_monthly_fee,
        worker_monthly_cost,
    )

    return round(
        (margin / revenue) * 100,
        2,
    )


def calculate_annual_revenue(monthly_fee):
    """Calculate annual revenue from a monthly fee."""
    return round(
        to_float(monthly_fee) * 12,
        MONEY_DECIMAL_PLACES,
    )


def calculate_annual_cost(monthly_cost):
    """Calculate annual worker cost."""
    return round(
        to_float(monthly_cost) * 12,
        MONEY_DECIMAL_PLACES,
    )


def calculate_annual_margin(
    monthly_fee,
    monthly_cost,
):
    """Calculate annual gross margin."""
    return round(
        calculate_gross_margin(
            monthly_fee,
            monthly_cost,
        ) * 12,
        MONEY_DECIMAL_PLACES,
    )


def calculate_placement_financials(placement):
    """Return the main financial figures for a placement."""
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

    margin = calculate_gross_margin(
        revenue,
        cost,
    )

    margin_percentage = calculate_gross_margin_percentage(
        revenue,
        cost,
    )

    return {
        "monthly_revenue": round(
            revenue,
            MONEY_DECIMAL_PLACES,
        ),
        "monthly_cost": round(
            cost,
            MONEY_DECIMAL_PLACES,
        ),
        "monthly_margin": margin,
        "margin_percentage": margin_percentage,
        "annual_revenue": calculate_annual_revenue(
            revenue
        ),
        "annual_cost": calculate_annual_cost(
            cost
        ),
        "annual_margin": calculate_annual_margin(
            revenue,
            cost,
        ),
    }


def placement_is_operational(placement):
    """Return True when a placement is operational."""
    status = getattr(
        placement,
        "status",
        None,
    )

    return status in {
        "Active",
        "Scheduled",
    }


def placement_has_negative_margin(placement):
    """Return True when placement margin is negative."""
    return calculate_gross_margin(
        getattr(
            placement,
            "client_monthly_fee",
            0,
        ),
        getattr(
            placement,
            "worker_monthly_cost",
            0,
        ),
    ) < 0


def is_active_placement(placement):
    """Check whether placement is active."""
    return getattr(
        placement,
        "status",
        None,
    ) == "Active"


def is_scheduled_placement(placement):
    """Check whether placement is scheduled."""
    return getattr(
        placement,
        "status",
        None,
    ) == "Scheduled"


def is_completed_placement(placement):
    """Check whether placement is completed."""
    return getattr(
        placement,
        "status",
        None,
    ) == "Completed"


def is_terminated_placement(placement):
    """Check whether placement is terminated."""
    return getattr(
        placement,
        "status",
        None,
    ) == "Terminated"


# ============================================================
# INVOICE CALCULATIONS
# ============================================================

def calculate_invoice_total(subtotal, tax=0):
    """Calculate invoice total."""
    return round(
        to_float(subtotal) + to_float(tax),
        MONEY_DECIMAL_PLACES,
    )


def calculate_invoice_balance(
    total_amount,
    amount_paid,
):
    """Calculate outstanding invoice balance."""
    total = to_float(total_amount)
    paid = to_float(amount_paid)

    return round(
        max(total - paid, 0),
        MONEY_DECIMAL_PLACES,
    )


def calculate_invoice_payment_percentage(
    total_amount,
    amount_paid,
):
    """Calculate percentage of invoice paid."""
    total = to_float(total_amount)
    paid = to_float(amount_paid)

    if total <= 0:
        return 0.0

    value = (paid / total) * 100

    return round(
        min(max(value, 0), 100),
        2,
    )


def invoice_is_paid(invoice):
    """Check whether invoice is fully paid."""
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

    return total > 0 and paid >= total


def invoice_is_partially_paid(invoice):
    """Check whether invoice is partially paid."""
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

    return (
        total > 0
        and paid > 0
        and paid < total
    )


def invoice_is_outstanding(invoice):
    """Check whether invoice has an outstanding balance."""
    return calculate_invoice_balance(
        getattr(
            invoice,
            "total_amount",
            0,
        ),
        getattr(
            invoice,
            "amount_paid",
            0,
        ),
    ) > 0


def invoice_is_overpaid(invoice):
    """Check whether payments exceed invoice total."""
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

    return paid > total


def invoice_is_unpaid(invoice):
    """Check whether invoice has no payment."""
    return (
        to_float(
            getattr(
                invoice,
                "amount_paid",
                0,
            )
        )
        <= 0
    )


def invoice_is_open(invoice):
    """Check whether invoice is open."""
    status = getattr(
        invoice,
        "status",
        None,
    )

    return status not in {
        "Cancelled",
        "Paid",
    }


def invoice_is_cancelled(invoice):
    """Check whether invoice is cancelled."""
    return getattr(
        invoice,
        "status",
        None,
    ) == "Cancelled"


def invoice_status_from_amounts(
    total_amount,
    amount_paid,
    current_status=None,
    due_date=None,
    today=None,
):
    """Determine invoice status from amounts and due date."""
    total = to_float(total_amount)
    paid = to_float(amount_paid)

    if current_status == "Cancelled":
        return "Cancelled"

    if total <= 0:
        return current_status or "Draft"

    if paid >= total:
        return "Paid"

    if paid > 0:
        if due_date is not None:
            check_date = today or date.today()

            if due_date < check_date:
                return "Overdue"

        return "Partially Paid"

    if due_date is not None:
        check_date = today or date.today()

        if due_date < check_date:
            return "Overdue"

    return current_status or "Sent"


# ============================================================
# PAYMENT CALCULATIONS
# ============================================================

def get_payment_amount(payment):
    """Return payment amount safely."""
    return to_float(
        getattr(
            payment,
            "amount",
            0,
        )
    )


def is_successful_payment_status(status):
    """Check whether payment was successfully received."""
    return status == "Received"


def calculate_remaining_balance(
    invoice_total,
    payments,
):
    """Calculate invoice balance from payment records."""
    total = to_float(invoice_total)

    received = calculate_received_payments(
        payments
    )

    return round(
        max(total - received, 0),
        MONEY_DECIMAL_PLACES,
    )


def calculate_total_payments(payments):
    """Calculate total value of payment records."""
    total = 0.0

    for payment in payments or []:
        total += get_payment_amount(
            payment
        )

    return round(
        total,
        MONEY_DECIMAL_PLACES,
    )


def calculate_received_payments(payments):
    """Calculate total successfully received payments."""
    total = 0.0

    for payment in payments or []:
        status = getattr(
            payment,
            "status",
            None,
        )

        if is_successful_payment_status(status):
            total += get_payment_amount(
                payment
            )

    return round(
        total,
        MONEY_DECIMAL_PLACES,
    )


def payment_fits_invoice(
    invoice,
    payment_amount,
):
    """Check whether payment fits remaining invoice balance."""
    amount = to_float(payment_amount)

    balance = calculate_invoice_balance(
        getattr(
            invoice,
            "total_amount",
            0,
        ),
        getattr(
            invoice,
            "amount_paid",
            0,
        ),
    )

    return (
        amount > 0
        and amount <= balance
    )


def payment_would_overpay(
    invoice,
    payment_amount,
):
    """Check whether payment would overpay invoice."""
    amount = to_float(payment_amount)

    balance = calculate_invoice_balance(
        getattr(
            invoice,
            "total_amount",
            0,
        ),
        getattr(
            invoice,
            "amount_paid",
            0,
        ),
    )

    return amount > balance


def payment_is_valid(payment):
    """Perform basic payment validation."""
    amount = get_payment_amount(payment)

    if amount <= 0:
        return False

    status = getattr(
        payment,
        "status",
        None,
    )

    return status in {
        "Received",
        "Pending",
        "Failed",
        "Reversed",
    }


# ============================================================
# DATE HELPERS
# ============================================================

def days_between(start_date, end_date):
    """Return number of days between two dates."""
    if not start_date or not end_date:
        return None

    return (
        end_date - start_date
    ).days


def days_from_today(target_date):
    """Return number of days from today."""
    if not target_date:
        return None

    return (
        target_date - date.today()
    ).days


def is_date_overdue(target_date):
    """Check whether date is before today."""
    if not target_date:
        return False

    return target_date < date.today()


def is_date_today(target_date):
    """Check whether date is today."""
    if not target_date:
        return False

    return target_date == date.today()


def is_date_future(target_date):
    """Check whether date is after today."""
    if not target_date:
        return False

    return target_date > date.today()


def is_date_today_or_past(target_date):
    """Check whether date is today or earlier."""
    if not target_date:
        return False

    return target_date <= date.today()


def calculate_days_overdue(target_date):
    """Return number of days overdue."""
    if not target_date:
        return 0

    difference = (
        date.today() - target_date
    ).days

    return max(difference, 0)


# ============================================================
# CONTRACT CALCULATIONS
# ============================================================

def days_until_renewal(contract):
    """Return days until contract renewal."""
    renewal_date = getattr(
        contract,
        "renewal_date",
        None,
    )

    if not renewal_date:
        return None

    return (
        renewal_date - date.today()
    ).days


def contract_is_expired(contract):
    """Check whether contract has expired."""
    end_date = getattr(
        contract,
        "end_date",
        None,
    )

    if not end_date:
        return False

    return end_date < date.today()


def contract_renewal_due(
    contract,
    days=30,
):
    """Check whether renewal is due within given days."""
    days_remaining = days_until_renewal(contract)

    if days_remaining is None:
        return False

    return 0 <= days_remaining <= days


def contract_renewal_overdue(contract):
    """Check whether renewal date has passed."""
    days_remaining = days_until_renewal(contract)

    if days_remaining is None:
        return False

    return days_remaining < 0


def contract_renewal_today(contract):
    """Check whether renewal is today."""
    return days_until_renewal(contract) == 0


def contract_renewal_soon(
    contract,
    days=30,
):
    """Check whether renewal is approaching."""
    return contract_renewal_due(
        contract,
        days=days,
    )


def contract_is_current(contract):
    """Check whether contract is currently valid."""
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

    today = date.today()

    if start_date and today < start_date:
        return False

    if end_date and today > end_date:
        return False

    return True


def contract_started(contract):
    """Check whether contract has started."""
    start_date = getattr(
        contract,
        "start_date",
        None,
    )

    if not start_date:
        return False

    return start_date <= date.today()


def contract_starts_in_future(contract):
    """Check whether contract starts in the future."""
    start_date = getattr(
        contract,
        "start_date",
        None,
    )

    if not start_date:
        return False

    return start_date > date.today()


def contract_duration_days(contract):
    """Return contract duration in days."""
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

    if not start_date or not end_date:
        return None

    return (
        end_date - start_date
    ).days


def contract_is_terminated(contract):
    """Check whether contract is terminated."""
    return getattr(
        contract,
        "status",
        None,
    ) == "Terminated"


def contract_is_signed(contract):
    """Check whether contract is signed."""
    return getattr(
        contract,
        "status",
        None,
    ) == "Signed"


def contract_is_active(contract):
    """Check whether contract is active."""
    return getattr(
        contract,
        "status",
        None,
    ) == "Active"


def contract_is_draft(contract):
    """Check whether contract is draft."""
    return getattr(
        contract,
        "status",
        None,
    ) == "Draft"


def contract_is_operational(contract):
    """Check whether contract is operational."""
    return (
        getattr(
            contract,
            "status",
            None,
        )
        in {
            "Active",
            "Signed",
        }
        and contract_is_current(contract)
    )


# ============================================================
# JOB CALCULATIONS
# ============================================================

def calculate_openings_remaining(job):
    """Calculate remaining openings for a job."""
    openings = int(
        to_float(
            getattr(
                job,
                "openings",
                0,
            )
        )
    )

    placements = getattr(
        job,
        "placements",
        None,
    ) or []

    filled = sum(
        1
        for placement in placements
        if getattr(
            placement,
            "status",
            None,
        )
        in {
            "Active",
            "Scheduled",
            "Completed",
        }
    )

    return max(
        openings - filled,
        0,
    )


def job_is_open(job):
    """Check whether a job is open."""
    return getattr(
        job,
        "status",
        None,
    ) == "Open"


def job_is_closed(job):
    """Check whether a job is closed."""
    return getattr(
        job,
        "status",
        None,
    ) in {
        "Closed",
        "Cancelled",
    }


def job_is_active(job):
    """Check whether a job is active."""
    return getattr(
        job,
        "status",
        None,
    ) in {
        "Open",
        "On Hold",
    }


def job_is_filled(job):
    """Check whether a job is filled."""
    return getattr(
        job,
        "status",
        None,
    ) == "Filled"


def job_is_cancelled(job):
    """Check whether a job is cancelled."""
    return getattr(
        job,
        "status",
        None,
    ) == "Cancelled"


# ============================================================
# CANDIDATE CALCULATIONS
# ============================================================

def candidate_is_active(candidate):
    """Check whether candidate is actively progressing."""
    return getattr(
        candidate,
        "status",
        None,
    ) in {
        "Submitted",
        "Shortlisted",
        "Interview",
        "Offer",
    }


def candidate_is_placed(candidate):
    """Check whether candidate has been placed."""
    return getattr(
        candidate,
        "status",
        None,
    ) == "Placed"


def candidate_is_rejected(candidate):
    """Check whether candidate has been rejected."""
    return getattr(
        candidate,
        "status",
        None,
    ) == "Rejected"


def candidate_is_withdrawn(candidate):
    """Check whether candidate has withdrawn."""
    return getattr(
        candidate,
        "status",
        None,
    ) == "Withdrawn"


def candidate_is_closed(candidate):
    """Check whether candidate is closed."""
    return getattr(
        candidate,
        "status",
        None,
    ) in {
        "Placed",
        "Rejected",
        "Withdrawn",
    }


def candidate_is_interview_stage(candidate):
    """Check whether candidate is at interview stage."""
    return getattr(
        candidate,
        "status",
        None,
    ) == "Interview"


def candidate_is_offer_stage(candidate):
    """Check whether candidate is at offer stage."""
    return getattr(
        candidate,
        "status",
        None,
    ) == "Offer"


# ============================================================
# EMPLOYEE CALCULATIONS
# ============================================================

def employee_is_active(employee):
    """Check whether employee is active."""
    return getattr(
        employee,
        "employment_status",
        None,
    ) != "Former Employee"


def employee_is_available(employee):
    """Check whether employee is currently available."""
    return getattr(
        employee,
        "availability",
        None,
    ) == "Available Now"


def employee_is_placed(employee):
    """Check whether employee is placed."""
    return getattr(
        employee,
        "employment_status",
        None,
    ) == "Placed"


def employee_is_former(employee):
    """Check whether employee is former employee."""
    return getattr(
        employee,
        "employment_status",
        None,
    ) == "Former Employee"


def employee_is_unavailable(employee):
    """Check whether employee is unavailable."""
    return getattr(
        employee,
        "availability",
        None,
    ) == "Unavailable"


def employee_is_interviewing(employee):
    """Check whether employee is interviewing."""
    return getattr(
        employee,
        "employment_status",
        None,
    ) == "Interviewing"


def employee_is_on_leave(employee):
    """Check whether employee is on leave."""
    return getattr(
        employee,
        "employment_status",
        None,
    ) == "On Leave"


# ============================================================
# CRM COUNT HELPERS
# ============================================================

def count_by_status(records, status):
    """Count records matching a status."""
    return sum(
        1
        for record in records or []
        if getattr(
            record,
            "status",
            None,
        ) == status
    )


def count_by_currency(records, currency):
    """Count records matching a currency."""
    return sum(
        1
        for record in records or []
        if getattr(
            record,
            "currency",
            None,
        ) == currency
    )


def count_records(records):
    """Safely count records."""
    if records is None:
        return 0

    try:
        return len(records)
    except TypeError:
        return 0


# ============================================================
# FINANCIAL TOTALS
# ============================================================

def calculate_total_revenue(
    placements,
    active_only=False,
):
    """Calculate total monthly placement revenue."""
    total = 0.0

    for placement in placements or []:

        if active_only and not is_active_placement(
            placement
        ):
            continue

        total += to_float(
            getattr(
                placement,
                "client_monthly_fee",
                0,
            )
        )

    return round(
        total,
        MONEY_DECIMAL_PLACES,
    )


def calculate_total_worker_cost(
    placements,
    active_only=False,
):
    """Calculate total monthly worker cost."""
    total = 0.0

    for placement in placements or []:

        if active_only and not is_active_placement(
            placement
        ):
            continue

        total += to_float(
            getattr(
                placement,
                "worker_monthly_cost",
                0,
            )
        )

    return round(
        total,
        MONEY_DECIMAL_PLACES,
    )


def calculate_total_margin(
    placements,
    active_only=False,
):
    """Calculate total monthly gross margin."""
    revenue = calculate_total_revenue(
        placements,
        active_only=active_only,
    )

    cost = calculate_total_worker_cost(
        placements,
        active_only=active_only,
    )

    return round(
        revenue - cost,
        MONEY_DECIMAL_PLACES,
    )


def calculate_total_invoice_value(invoices):
    """Calculate total invoice value."""
    total = 0.0

    for invoice in invoices or []:
        total += to_float(
            getattr(
                invoice,
                "total_amount",
                0,
            )
        )

    return round(
        total,
        MONEY_DECIMAL_PLACES,
    )


def calculate_total_invoice_paid(invoices):
    """Calculate total amount paid across invoices."""
    total = 0.0

    for invoice in invoices or []:
        total += to_float(
            getattr(
                invoice,
                "amount_paid",
                0,
            )
        )

    return round(
        total,
        MONEY_DECIMAL_PLACES,
    )


def calculate_total_invoice_outstanding(invoices):
    """Calculate total outstanding invoice value."""
    total = 0.0

    for invoice in invoices or []:
        total += calculate_invoice_balance(
            getattr(
                invoice,
                "total_amount",
                0,
            ),
            getattr(
                invoice,
                "amount_paid",
                0,
            ),
        )

    return round(
        total,
        MONEY_DECIMAL_PLACES,
    )


def calculate_financial_summary(
    placements=None,
    invoices=None,
):
    """Return a combined financial summary."""
    placements = placements or []
    invoices = invoices or []

    revenue = calculate_total_revenue(
        placements
    )

    worker_cost = calculate_total_worker_cost(
        placements
    )

    margin = calculate_total_margin(
        placements
    )

    invoice_total = calculate_total_invoice_value(
        invoices
    )

    invoice_paid = calculate_total_invoice_paid(
        invoices
    )

    invoice_outstanding = (
        calculate_total_invoice_outstanding(
            invoices
        )
    )

    return {
        "monthly_revenue": revenue,
        "monthly_worker_cost": worker_cost,
        "monthly_gross_margin": margin,
        "invoice_total": invoice_total,
        "invoice_paid": invoice_paid,
        "invoice_outstanding": invoice_outstanding,
    }


# ============================================================
# DATA QUALITY HELPERS
# ============================================================

def is_positive_amount(value):
    """Check whether value is positive."""
    return to_float(value) > 0


def is_non_negative_amount(value):
    """Check whether value is zero or positive."""
    return to_float(value) >= 0


def dates_are_valid(
    start_date,
    end_date,
):
    """Check whether start date is not after end date."""
    if not start_date or not end_date:
        return True

    return start_date <= end_date


def amount_is_valid_for_invoice(
    total_amount,
    amount_paid,
):
    """Check whether amount paid is valid for invoice."""
    total = to_float(total_amount)
    paid = to_float(amount_paid)

    return (
        total >= 0
        and paid >= 0
        and paid <= total
    )


# ============================================================
# FORMATTING HELPERS
# ============================================================

def format_money(
    amount,
    currency="GBP",
):
    """Format a monetary amount."""
    return f"{currency} {to_float(amount):,.2f}"


def format_percentage(value):
    """Format a percentage."""
    return f"{to_float(value):.2f}%"


def format_number(value):
    """Format a number."""
    return f"{to_float(value):,.2f}"


# ============================================================
# GENERAL RECORD SUMMARY
# ============================================================

def summarise_record_counts(
    records,
    status_values=None,
):
    """Return record counts grouped by status."""
    summary = {}

    if not records:
        return summary

    if status_values is None:
        status_values = sorted(
            {
                getattr(
                    record,
                    "status",
                    None,
                )
                for record in records
                if getattr(
                    record,
                    "status",
                    None,
                )
            }
        )

    for status in status_values:
        summary[status] = count_by_status(
            records,
            status,
        )

    return summary