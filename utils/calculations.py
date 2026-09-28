from datetime import date


# ============================================================
# GENERAL NUMBER HELPERS
# ============================================================

def to_float(value, default=0.0):
    """
    Safely convert a value to float.
    """
    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def safe_divide(numerator, denominator, default=0.0):
    """
    Safely divide two numbers.
    """
    numerator = to_float(numerator)
    denominator = to_float(denominator)

    if denominator == 0:
        return default

    return numerator / denominator


# ============================================================
# PLACEMENT CALCULATIONS
# ============================================================

def calculate_gross_margin(
    client_monthly_fee,
    worker_monthly_cost,
):
    """
    Gross margin = client fee - worker cost.
    """
    revenue = to_float(client_monthly_fee)
    cost = to_float(worker_monthly_cost)

    return revenue - cost


def calculate_gross_margin_percentage(
    client_monthly_fee,
    worker_monthly_cost,
):
    """
    Gross margin percentage.
    """
    revenue = to_float(client_monthly_fee)

    if revenue == 0:
        return 0.0

    margin = calculate_gross_margin(
        client_monthly_fee,
        worker_monthly_cost,
    )

    return (margin / revenue) * 100


def calculate_annual_revenue(
    monthly_fee,
):
    """
    Convert monthly revenue to annual revenue.
    """
    return to_float(monthly_fee) * 12


def calculate_annual_worker_cost(
    monthly_cost,
):
    """
    Convert monthly worker cost to annual worker cost.
    """
    return to_float(monthly_cost) * 12


def calculate_annual_gross_margin(
    monthly_fee,
    monthly_worker_cost,
):
    """
    Convert monthly gross margin to annual gross margin.
    """
    monthly_margin = calculate_gross_margin(
        monthly_fee,
        monthly_worker_cost,
    )

    return monthly_margin * 12


def placement_is_active(status):
    """
    Check whether a placement is currently active.
    """
    return status == "Active"


def placement_is_scheduled(status):
    """
    Check whether a placement is scheduled.
    """
    return status == "Scheduled"


def placement_is_completed(status):
    """
    Check whether a placement has been completed.
    """
    return status == "Completed"


def placement_is_terminated(status):
    """
    Check whether a placement has been terminated.
    """
    return status == "Terminated"


def placement_is_current(status):
    """
    Check whether a placement contributes to current
    operating economics.

    Current = Active or Scheduled.
    """
    return status in [
        "Active",
        "Scheduled",
    ]


# ============================================================
# INVOICE CALCULATIONS
# ============================================================

def calculate_invoice_total(
    subtotal,
    tax,
):
    """
    Invoice total = subtotal + tax.
    """
    subtotal = to_float(subtotal)
    tax = to_float(tax)

    return subtotal + tax


def calculate_invoice_balance(
    total_amount,
    amount_paid,
):
    """
    Invoice balance = total amount - amount paid.

    Balance cannot be negative.
    """
    total = to_float(total_amount)
    paid = to_float(amount_paid)

    return max(total - paid, 0.0)


def calculate_payment_percentage(
    total_amount,
    amount_paid,
):
    """
    Percentage of invoice paid.

    This is not capped at 100%, so an overpayment
    can be identified.
    """
    total = to_float(total_amount)
    paid = to_float(amount_paid)

    if total == 0:
        return 0.0

    return (paid / total) * 100


def invoice_is_paid(
    total_amount,
    amount_paid,
):
    """
    Check whether the invoice has been fully paid.
    """
    total = to_float(total_amount)
    paid = to_float(amount_paid)

    return total > 0 and paid >= total


def invoice_is_outstanding(
    total_amount,
    amount_paid,
):
    """
    Check whether an invoice still has an outstanding balance.
    """
    return calculate_invoice_balance(
        total_amount,
        amount_paid,
    ) > 0


def invoice_is_overpaid(
    total_amount,
    amount_paid,
):
    """
    Check whether payments exceed the invoice total.
    """
    total = to_float(total_amount)
    paid = to_float(amount_paid)

    return paid > total


def invoice_is_open(status):
    """
    Check whether an invoice is still operationally open.
    """
    return status in [
        "Draft",
        "Sent",
        "Partially Paid",
        "Overdue",
    ]


# ============================================================
# PAYMENT CALCULATIONS
# ============================================================

def calculate_remaining_balance(
    invoice_total,
    existing_payments,
):
    """
    Calculate remaining invoice balance.

    existing_payments can be:
    - a list of Payment objects
    - a list of numeric amounts
    """

    total = to_float(invoice_total)

    paid = 0.0

    for payment in existing_payments or []:

        if hasattr(payment, "amount"):
            amount = getattr(
                payment,
                "amount",
                0,
            )
        else:
            amount = payment

        paid += to_float(amount)

    return max(total - paid, 0.0)


def calculate_total_payments(
    payments,
):
    """
    Calculate the total amount of payments.
    """
    total = 0.0

    for payment in payments or []:

        if hasattr(payment, "amount"):
            amount = getattr(
                payment,
                "amount",
                0,
            )
        else:
            amount = payment

        total += to_float(amount)

    return total


def payment_fits_invoice(
    payment_amount,
    invoice_balance,
):
    """
    Check whether a payment fits within the
    outstanding invoice balance.
    """
    payment = to_float(payment_amount)
    balance = to_float(invoice_balance)

    return payment > 0 and payment <= balance


def payment_is_valid(
    payment_amount,
):
    """
    Check whether a payment amount is positive.
    """
    return to_float(payment_amount) > 0


# ============================================================
# DATE CALCULATIONS
# ============================================================

def days_between(
    start_date,
    end_date,
):
    """
    Return number of days between two dates.
    """
    if not start_date or not end_date:
        return 0

    return (end_date - start_date).days


def days_from_today(
    target_date,
):
    """
    Return number of days from today to a target date.

    Positive = future
    Zero = today
    Negative = past
    """
    if not target_date:
        return None

    return (target_date - date.today()).days


def is_overdue(
    due_date,
):
    """
    Check whether a date has passed.
    """
    if not due_date:
        return False

    return due_date < date.today()


def is_due_today(
    due_date,
):
    """
    Check whether a date is today.
    """
    if not due_date:
        return False

    return due_date == date.today()


def is_future_date(
    target_date,
):
    """
    Check whether a date is in the future.
    """
    if not target_date:
        return False

    return target_date > date.today()


def days_overdue(
    due_date,
):
    """
    Return the number of days a date is overdue.

    Returns 0 when the date is not overdue.
    """
    if not due_date:
        return 0

    days = (date.today() - due_date).days

    return max(days, 0)


# ============================================================
# CONTRACT CALCULATIONS
# ============================================================

def days_until_renewal(
    renewal_date,
):
    """
    Return number of days until contract renewal.
    """
    return days_from_today(renewal_date)


def contract_is_expired(
    end_date,
):
    """
    Check whether a contract has expired.
    """
    if not end_date:
        return False

    return end_date < date.today()


def contract_renewal_due(
    renewal_date,
    warning_days=30,
):
    """
    Check whether a contract renewal is due within
    the specified warning period.

    Includes contracts renewing today.
    """
    if not renewal_date:
        return False

    days = days_until_renewal(
        renewal_date
    )

    if days is None:
        return False

    return 0 <= days <= warning_days


def contract_is_current(
    start_date,
    end_date,
):
    """
    Check whether a contract is currently active
    based on its dates.
    """
    today = date.today()

    if start_date and today < start_date:
        return False

    if end_date and today > end_date:
        return False

    return True


# ============================================================
# JOB CALCULATIONS
# ============================================================

def calculate_openings_remaining(
    total_openings,
    placements_count,
):
    """
    Calculate how many job openings remain.
    """
    openings = int(
        to_float(total_openings)
    )

    placements = int(
        to_float(placements_count)
    )

    return max(
        openings - placements,
        0,
    )


def job_is_open(
    status,
):
    """
    Check whether a job is considered open.
    """
    return status in [
        "Open",
        "On Hold",
    ]


def job_is_closed(
    status,
):
    """
    Check whether a job is closed or filled.
    """
    return status in [
        "Closed",
        "Filled",
        "Cancelled",
    ]


def job_is_active(
    status,
):
    """
    Check whether a job is actively being worked on.
    """
    return status in [
        "Open",
        "On Hold",
    ]


# ============================================================
# CANDIDATE CALCULATIONS
# ============================================================

def candidate_is_active(
    status,
):
    """
    Check whether a candidate is still active
    in the recruitment pipeline.
    """
    return status in [
        "Submitted",
        "Shortlisted",
        "Interview",
        "Offer",
    ]


def candidate_is_placed(
    status,
):
    """
    Check whether a candidate has been placed.
    """
    return status == "Placed"


def candidate_is_rejected(
    status,
):
    """
    Check whether a candidate has been rejected.
    """
    return status == "Rejected"


def candidate_is_withdrawn(
    status,
):
    """
    Check whether a candidate has withdrawn.
    """
    return status == "Withdrawn"


# ============================================================
# EMPLOYEE CALCULATIONS
# ============================================================

def employee_is_active(
    status,
):
    """
    Check whether an employee is considered active
    in the workforce.
    """
    return status in [
        "Available",
        "Interviewing",
        "Placed",
        "On Leave",
    ]


def employee_is_available(
    status,
):
    """
    Check whether an employee is currently available.
    """
    return status == "Available"


def employee_is_placed(
    status,
):
    """
    Check whether an employee is currently placed.
    """
    return status == "Placed"


def employee_is_former(
    status,
):
    """
    Check whether an employee is a former employee.
    """
    return status == "Former Employee"


def employee_is_unavailable(
    status,
):
    """
    Check whether an employee is unavailable.
    """
    return status == "Unavailable"


# ============================================================
# CRM COUNTS
# ============================================================

def count_by_status(
    records,
    status_attribute="status",
):
    """
    Count records grouped by status.

    Returns:
        {
            "Open": 5,
            "Closed": 2,
        }
    """

    results = {}

    for record in records or []:

        status = getattr(
            record,
            status_attribute,
            None,
        )

        if not status:
            status = "Unknown"

        results[status] = (
            results.get(status, 0) + 1
        )

    return results


def count_by_currency(
    records,
):
    """
    Count records grouped by currency.
    """

    results = {}

    for record in records or []:

        currency = getattr(
            record,
            "currency",
            None,
        )

        if not currency:
            currency = "N/A"

        results[currency] = (
            results.get(currency, 0) + 1
        )

    return results


# ============================================================
# FINANCIAL TOTALS
# ============================================================

def total_amount(
    records,
    amount_attribute,
):
    """
    Sum a numeric field across records.
    """

    total = 0.0

    for record in records or []:

        value = getattr(
            record,
            amount_attribute,
            0,
        )

        total += to_float(value)

    return total


def totals_by_currency(
    records,
    amount_attribute,
):
    """
    Sum an amount grouped by currency.

    No foreign exchange conversion is performed.
    """

    results = {}

    for record in records or []:

        currency = (
            getattr(
                record,
                "currency",
                None,
            )
            or "N/A"
        )

        amount = getattr(
            record,
            amount_attribute,
            0,
        )

        amount = to_float(amount)

        results[currency] = (
            results.get(currency, 0) + amount
        )

    return results


# ============================================================
# PLACEMENT FINANCIAL SUMMARY
# ============================================================

def placement_financial_summary(
    placements,
    statuses=None,
):
    """
    Calculate placement revenue, cost and margin
    grouped by currency.

    Parameters:
        placements:
            Iterable of Placement objects.

        statuses:
            Optional list of statuses to include.

            Example:
                ["Active"]

            or:
                ["Active", "Scheduled"]

        If statuses is None, all placements are included.

    No FX conversion is performed.
    """

    results = {}

    for placement in placements or []:

        status = getattr(
            placement,
            "status",
            None,
        )

        if statuses is not None:
            if status not in statuses:
                continue

        currency = (
            getattr(
                placement,
                "currency",
                None,
            )
            or "N/A"
        )

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

        margin = revenue - cost

        if currency not in results:

            results[currency] = {
                "revenue": 0.0,
                "cost": 0.0,
                "margin": 0.0,
                "placement_count": 0,
            }

        results[currency]["revenue"] += revenue
        results[currency]["cost"] += cost
        results[currency]["margin"] += margin
        results[currency]["placement_count"] += 1

    for currency, values in results.items():

        revenue = values["revenue"]

        if revenue:

            values["margin_percentage"] = (
                values["margin"]
                / revenue
            ) * 100

        else:

            values["margin_percentage"] = 0.0

    return results


# ============================================================
# INVOICE FINANCIAL SUMMARY
# ============================================================

def invoice_financial_summary(
    invoices,
):
    """
    Calculate invoiced, paid and outstanding amounts
    grouped by currency.

    No FX conversion is performed.
    """

    results = {}

    for invoice in invoices or []:

        currency = (
            getattr(
                invoice,
                "currency",
                None,
            )
            or "N/A"
        )

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

        outstanding = max(
            total - paid,
            0.0,
        )

        if currency not in results:

            results[currency] = {
                "invoiced": 0.0,
                "paid": 0.0,
                "outstanding": 0.0,
                "invoice_count": 0,
            }

        results[currency]["invoiced"] += total
        results[currency]["paid"] += paid
        results[currency]["outstanding"] += outstanding
        results[currency]["invoice_count"] += 1

    return results