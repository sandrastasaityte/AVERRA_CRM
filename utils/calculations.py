from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


# ============================================================
# CONSTANTS
# ============================================================

MONEY_DECIMAL_PLACES = 2
MONEY_QUANTIZER = Decimal("0.01")


# ============================================================
# NUMBER / MONEY HELPERS
# ============================================================

def to_float(value, default=0.0):
    """
    Safely convert a value to float.
    """
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_decimal(value, default=Decimal("0.00")):
    """
    Safely convert a value to Decimal.
    """
    if value is None:
        return default

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def round_money(value):
    """
    Round a monetary value to 2 decimal places.
    """
    amount = to_decimal(value)
    return amount.quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)


def money_to_float(value):
    """
    Convert money to a rounded float.
    """
    return float(round_money(value))


def safe_divide(numerator, denominator, default=0.0):
    """
    Safely divide two numbers.
    """
    numerator = to_float(numerator)
    denominator = to_float(denominator)

    if denominator == 0:
        return default

    return numerator / denominator


def percentage(numerator, denominator, default=0.0):
    """
    Calculate percentage.

    Example:
        percentage(25, 100) -> 25.0
    """
    return safe_divide(numerator, denominator, default) * 100


# ============================================================
# PLACEMENT FINANCIAL CALCULATIONS
# ============================================================

def calculate_gross_margin(monthly_fee, monthly_cost):
    """
    Monthly gross margin.

    Gross Margin = Monthly Fee - Monthly Worker Cost
    """
    fee = to_decimal(monthly_fee)
    cost = to_decimal(monthly_cost)

    return round_money(fee - cost)


def calculate_gross_margin_percentage(monthly_fee, monthly_cost):
    """
    Gross margin percentage based on monthly client fee.
    """
    fee = to_float(monthly_fee)
    cost = to_float(monthly_cost)

    if fee <= 0:
        return 0.0

    return round(safe_divide(fee - cost, fee) * 100, 2)


def calculate_annual_revenue(monthly_fee):
    """
    Annual revenue based on monthly client fee.
    """
    return round_money(to_decimal(monthly_fee) * 12)


def calculate_annual_cost(monthly_cost):
    """
    Annual worker cost based on monthly worker cost.
    """
    return round_money(to_decimal(monthly_cost) * 12)


def calculate_annual_margin(monthly_fee, monthly_cost):
    """
    Annual gross margin.
    """
    return round_money(
        calculate_gross_margin(monthly_fee, monthly_cost) * 12
    )


def calculate_placement_financials(monthly_fee, monthly_cost):
    """
    Return a financial summary for a placement.
    """
    monthly_fee = round_money(monthly_fee)
    monthly_cost = round_money(monthly_cost)

    monthly_margin = calculate_gross_margin(
        monthly_fee,
        monthly_cost
    )

    margin_percentage = calculate_gross_margin_percentage(
        monthly_fee,
        monthly_cost
    )

    annual_revenue = calculate_annual_revenue(monthly_fee)
    annual_cost = calculate_annual_cost(monthly_cost)
    annual_margin = calculate_annual_margin(
        monthly_fee,
        monthly_cost
    )

    return {
        "monthly_fee": monthly_fee,
        "monthly_cost": monthly_cost,
        "monthly_margin": monthly_margin,
        "margin_percentage": margin_percentage,
        "annual_revenue": annual_revenue,
        "annual_cost": annual_cost,
        "annual_margin": annual_margin,
    }


def placement_is_operational(placement):
    """
    True when placement is Active or Scheduled.
    """
    status = getattr(placement, "status", None)

    return status in ["Active", "Scheduled"]


def placement_has_negative_margin(placement):
    """
    Check whether placement has negative monthly margin.
    """
    margin = calculate_gross_margin(
        getattr(placement, "client_monthly_fee", 0),
        getattr(placement, "worker_monthly_cost", 0),
    )

    return margin < 0


def placement_has_positive_margin(placement):
    """
    Check whether placement has positive monthly margin.
    """
    margin = calculate_gross_margin(
        getattr(placement, "client_monthly_fee", 0),
        getattr(placement, "worker_monthly_cost", 0),
    )

    return margin > 0


def placement_is_break_even(placement):
    """
    Check whether placement has zero monthly margin.
    """
    margin = calculate_gross_margin(
        getattr(placement, "client_monthly_fee", 0),
        getattr(placement, "worker_monthly_cost", 0),
    )

    return margin == 0


def is_active_placement(placement):
    return getattr(placement, "status", None) == "Active"


def is_scheduled_placement(placement):
    return getattr(placement, "status", None) == "Scheduled"


def is_completed_placement(placement):
    return getattr(placement, "status", None) == "Completed"


def is_terminated_placement(placement):
    return getattr(placement, "status", None) == "Terminated"


# ============================================================
# INVOICE CALCULATIONS
# ============================================================

def calculate_invoice_total(invoice):
    """
    Return invoice total amount.
    """
    return round_money(
        getattr(invoice, "total_amount", 0)
    )


def calculate_invoice_balance(invoice):
    """
    Calculate invoice outstanding balance.

    Balance = Total Amount - Amount Paid
    """
    total = to_decimal(
        getattr(invoice, "total_amount", 0)
    )

    paid = to_decimal(
        getattr(invoice, "amount_paid", 0)
    )

    balance = total - paid

    if balance < 0:
        balance = Decimal("0.00")

    return round_money(balance)


def calculate_invoice_payment_percentage(invoice):
    """
    Calculate percentage of invoice that has been paid.
    """
    total = to_float(
        getattr(invoice, "total_amount", 0)
    )

    paid = to_float(
        getattr(invoice, "amount_paid", 0)
    )

    if total <= 0:
        return 0.0

    result = (paid / total) * 100

    return round(result, 2)


def calculate_payment_percentage(invoice):
    """
    Compatibility function.

    Older screens, including invoices.py, may import
    calculate_payment_percentage().

    This function intentionally delegates to the newer
    calculate_invoice_payment_percentage() function.
    """
    return calculate_invoice_payment_percentage(invoice)


def invoice_is_paid(invoice):
    """
    Check whether invoice is fully paid.
    """
    total = to_decimal(
        getattr(invoice, "total_amount", 0)
    )

    paid = to_decimal(
        getattr(invoice, "amount_paid", 0)
    )

    return total > 0 and paid >= total


def invoice_is_partially_paid(invoice):
    """
    Check whether invoice has received some but not all payment.
    """
    total = to_decimal(
        getattr(invoice, "total_amount", 0)
    )

    paid = to_decimal(
        getattr(invoice, "amount_paid", 0)
    )

    return paid > 0 and paid < total


def invoice_is_outstanding(invoice):
    """
    Check whether invoice has an outstanding balance.
    """
    return calculate_invoice_balance(invoice) > 0


def invoice_is_overpaid(invoice):
    """
    Check whether payments exceed invoice total.
    """
    total = to_decimal(
        getattr(invoice, "total_amount", 0)
    )

    paid = to_decimal(
        getattr(invoice, "amount_paid", 0)
    )

    return paid > total


def invoice_is_unpaid(invoice):
    """
    Check whether invoice has received no payment.
    """
    paid = to_decimal(
        getattr(invoice, "amount_paid", 0)
    )

    return paid <= 0


def invoice_is_open(invoice):
    """
    Check whether invoice is still open.
    """
    status = getattr(invoice, "status", None)

    return status not in [
        "Paid",
        "Cancelled",
        "Canceled",
    ]


def invoice_is_cancelled(invoice):
    """
    Check whether invoice is cancelled.
    """
    status = getattr(invoice, "status", None)

    return status in [
        "Cancelled",
        "Canceled",
    ]


def invoice_status_from_amounts(
    total_amount,
    amount_paid,
    due_date=None,
    today=None,
):
    """
    Determine an invoice status from financial values and due date.
    """
    total = to_decimal(total_amount)
    paid = to_decimal(amount_paid)

    if today is None:
        today = date.today()

    if total <= 0:
        return "Draft"

    if paid >= total:
        return "Paid"

    if paid > 0:
        if due_date and due_date < today:
            return "Overdue"

        return "Partially Paid"

    if due_date and due_date < today:
        return "Overdue"

    return "Unpaid"


# ============================================================
# PAYMENT CALCULATIONS
# ============================================================

def get_payment_amount(payment):
    """
    Safely retrieve payment amount.
    """
    return round_money(
        getattr(payment, "amount", 0)
    )


def is_successful_payment_status(status):
    """
    Determine whether payment status represents received funds.
    """
    if status is None:
        return False

    return str(status).strip().lower() in [
        "received",
        "paid",
        "completed",
        "successful",
    ]


def calculate_remaining_balance(
    invoice_total,
    payments=None,
):
    """
    Calculate remaining invoice balance from payment records.
    """
    total = to_decimal(invoice_total)

    received = Decimal("0.00")

    if payments:
        for payment in payments:
            status = getattr(payment, "status", None)

            if is_successful_payment_status(status):
                received += to_decimal(
                    getattr(payment, "amount", 0)
                )

    balance = total - received

    if balance < 0:
        balance = Decimal("0.00")

    return round_money(balance)


def calculate_total_payments(payments):
    """
    Calculate total value of all payment records.
    """
    total = Decimal("0.00")

    if payments:
        for payment in payments:
            total += to_decimal(
                getattr(payment, "amount", 0)
            )

    return round_money(total)


def calculate_received_payments(payments):
    """
    Calculate total successfully received payments.
    """
    total = Decimal("0.00")

    if payments:
        for payment in payments:
            status = getattr(payment, "status", None)

            if is_successful_payment_status(status):
                total += to_decimal(
                    getattr(payment, "amount", 0)
                )

    return round_money(total)


def calculate_pending_payments(payments):
    """
    Calculate total pending payments.
    """
    total = Decimal("0.00")

    if payments:
        for payment in payments:
            status = getattr(payment, "status", None)

            if str(status).strip().lower() == "pending":
                total += to_decimal(
                    getattr(payment, "amount", 0)
                )

    return round_money(total)


def calculate_failed_payments(payments):
    """
    Calculate total failed payments.
    """
    total = Decimal("0.00")

    if payments:
        for payment in payments:
            status = getattr(payment, "status", None)

            if str(status).strip().lower() in [
                "failed",
                "declined",
                "rejected",
            ]:
                total += to_decimal(
                    getattr(payment, "amount", 0)
                )

    return round_money(total)


def calculate_reversed_payments(payments):
    """
    Calculate total reversed payments.
    """
    total = Decimal("0.00")

    if payments:
        for payment in payments:
            status = getattr(payment, "status", None)

            if str(status).strip().lower() in [
                "reversed",
                "refunded",
            ]:
                total += to_decimal(
                    getattr(payment, "amount", 0)
                )

    return round_money(total)


def payment_fits_invoice(
    payment_amount,
    invoice_balance,
):
    """
    Check whether payment does not exceed invoice balance.
    """
    payment = to_decimal(payment_amount)
    balance = to_decimal(invoice_balance)

    return payment <= balance


def payment_would_overpay(
    payment_amount,
    invoice_balance,
):
    """
    Check whether payment would cause overpayment.
    """
    payment = to_decimal(payment_amount)
    balance = to_decimal(invoice_balance)

    return payment > balance


def payment_is_valid(payment_amount):
    """
    Check whether payment amount is positive.
    """
    return to_decimal(payment_amount) > 0


# ============================================================
# DATE CALCULATIONS
# ============================================================

def days_between(start_date, end_date):
    """
    Number of days between two dates.
    """
    if not start_date or not end_date:
        return 0

    return (end_date - start_date).days


def days_from_today(target_date):
    """
    Positive = future.
    Negative = past.
    Zero = today.
    """
    if not target_date:
        return 0

    return (target_date - date.today()).days


def is_date_overdue(target_date):
    """
    Check whether date is before today.
    """
    if not target_date:
        return False

    return target_date < date.today()


def is_date_today(target_date):
    """
    Check whether date is today.
    """
    if not target_date:
        return False

    return target_date == date.today()


def is_date_future(target_date):
    """
    Check whether date is in the future.
    """
    if not target_date:
        return False

    return target_date > date.today()


def is_date_today_or_past(target_date):
    """
    Check whether date is today or in the past.
    """
    if not target_date:
        return False

    return target_date <= date.today()


def calculate_days_overdue(target_date):
    """
    Number of days overdue.

    Returns 0 when date is today or in the future.
    """
    if not target_date:
        return 0

    days = (date.today() - target_date).days

    return max(days, 0)


# ============================================================
# CONTRACT CALCULATIONS
# ============================================================

def days_until_renewal(contract):
    """
    Number of days until contract renewal.
    """
    renewal_date = getattr(
        contract,
        "renewal_date",
        None,
    )

    if not renewal_date:
        return None

    return (renewal_date - date.today()).days


def contract_is_expired(contract):
    """
    Check whether contract end date has passed.
    """
    end_date = getattr(
        contract,
        "end_date",
        None,
    )

    if not end_date:
        return False

    return end_date < date.today()


def contract_renewal_due(contract, days=30):
    """
    Check whether contract renewal is within the next N days.
    """
    renewal_date = getattr(
        contract,
        "renewal_date",
        None,
    )

    if not renewal_date:
        return False

    difference = (renewal_date - date.today()).days

    return 0 <= difference <= days


def contract_renewal_overdue(contract):
    """
    Check whether renewal date has passed.
    """
    renewal_date = getattr(
        contract,
        "renewal_date",
        None,
    )

    if not renewal_date:
        return False

    return renewal_date < date.today()


def contract_renewal_today(contract):
    """
    Check whether renewal is today.
    """
    renewal_date = getattr(
        contract,
        "renewal_date",
        None,
    )

    return renewal_date == date.today()


def contract_renewal_soon(contract, days=30):
    """
    Check whether renewal is approaching.
    """
    return contract_renewal_due(contract, days)


def contract_is_current(contract):
    """
    Check whether contract is currently within its dates.
    """
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
    """
    Check whether contract has started.
    """
    start_date = getattr(
        contract,
        "start_date",
        None,
    )

    if not start_date:
        return False

    return start_date <= date.today()


def contract_starts_in_future(contract):
    """
    Check whether contract starts in the future.
    """
    start_date = getattr(
        contract,
        "start_date",
        None,
    )

    if not start_date:
        return False

    return start_date > date.today()


def contract_duration_days(contract):
    """
    Calculate contract duration.
    """
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
        return 0

    return (end_date - start_date).days


def contract_is_terminated(contract):
    """
    Check whether contract is terminated.
    """
    return getattr(contract, "status", None) == "Terminated"


def contract_is_signed(contract):
    """
    Check whether contract status represents a signed contract.
    """
    status = getattr(contract, "status", None)

    return status in [
        "Signed",
        "Active",
        "Completed",
    ]


def contract_is_active(contract):
    """
    Check whether contract status is Active.
    """
    return getattr(contract, "status", None) == "Active"


def contract_is_draft(contract):
    """
    Check whether contract is still a draft.
    """
    return getattr(contract, "status", None) == "Draft"


def contract_is_operational(contract):
    """
    Check whether contract is currently operational.
    """
    return contract_is_active(contract) and contract_is_current(contract)


# ============================================================
# JOB CALCULATIONS
# ============================================================

def calculate_openings_remaining(job, placements=None):
    """
    Calculate remaining job openings.

    Completed and Active placements count as filled.
    """
    openings = int(
        to_float(
            getattr(job, "openings", 0)
        )
    )

    if openings < 0:
        openings = 0

    filled = 0

    if placements:
        for placement in placements:
            status = getattr(
                placement,
                "status",
                None,
            )

            if status in [
                "Active",
                "Completed",
            ]:
                filled += 1

    return max(openings - filled, 0)


def job_is_open(job):
    """
    Check whether job is open.
    """
    status = getattr(job, "status", None)

    return status in [
        "Open",
        "Active",
    ]


def job_is_closed(job):
    """
    Check whether job is closed.
    """
    status = getattr(job, "status", None)

    return status in [
        "Closed",
        "Completed",
    ]


def job_is_active(job):
    """
    Check whether job is active.
    """
    return getattr(job, "status", None) == "Active"


def job_is_filled(job, placements=None):
    """
    Check whether all job openings are filled.
    """
    return calculate_openings_remaining(
        job,
        placements
    ) == 0


def job_is_cancelled(job):
    """
    Check whether job is cancelled.
    """
    return getattr(job, "status", None) in [
        "Cancelled",
        "Canceled",
    ]


# ============================================================
# CANDIDATE CALCULATIONS
# ============================================================

def candidate_is_active(candidate):
    """
    Check whether candidate is in an active recruitment stage.
    """
    status = getattr(candidate, "status", None)

    return status in [
        "Submitted",
        "Shortlisted",
        "Interview",
        "Offer",
    ]


def candidate_is_placed(candidate):
    """
    Check whether candidate is placed.
    """
    return getattr(candidate, "status", None) == "Placed"


def candidate_is_rejected(candidate):
    """
    Check whether candidate is rejected.
    """
    return getattr(candidate, "status", None) == "Rejected"


def candidate_is_withdrawn(candidate):
    """
    Check whether candidate withdrew.
    """
    return getattr(candidate, "status", None) == "Withdrawn"


def candidate_is_closed(candidate):
    """
    Check whether candidate is in a closed status.
    """
    status = getattr(candidate, "status", None)

    return status in [
        "Placed",
        "Rejected",
        "Withdrawn",
    ]


def candidate_is_interview_stage(candidate):
    """
    Check whether candidate is at interview stage.
    """
    return getattr(candidate, "status", None) == "Interview"


def candidate_is_offer_stage(candidate):
    """
    Check whether candidate is at offer stage.
    """
    return getattr(candidate, "status", None) == "Offer"


# ============================================================
# EMPLOYEE CALCULATIONS
# ============================================================

def employee_is_active(employee):
    """
    Check whether employee is not a former employee.
    """
    status = getattr(
        employee,
        "employment_status",
        None,
    )

    return status not in [
        "Former Employee",
        "Former",
        "Terminated",
    ]


def employee_is_available(employee):
    """
    Check whether employee is available.
    """
    availability = getattr(
        employee,
        "availability",
        None,
    )

    return str(availability).strip().lower() in [
        "available",
        "yes",
        "true",
    ]


def employee_is_placed(employee):
    """
    Check whether employee has a placement.
    """
    placements = getattr(
        employee,
        "placements",
        None,
    )

    if not placements:
        return False

    for placement in placements:
        if getattr(
            placement,
            "status",
            None
        ) in [
            "Active",
            "Scheduled",
        ]:
            return True

    return False


def employee_is_former(employee):
    """
    Check whether employee is a former employee.
    """
    status = getattr(
        employee,
        "employment_status",
        None,
    )

    return status in [
        "Former Employee",
        "Former",
        "Terminated",
    ]


def employee_is_unavailable(employee):
    """
    Check whether employee is unavailable.
    """
    return not employee_is_available(employee)


def employee_is_interviewing(employee):
    """
    Check whether employee is marked as interviewing.
    """
    availability = getattr(
        employee,
        "availability",
        None,
    )

    return str(availability).strip().lower() == "interviewing"


def employee_is_on_leave(employee):
    """
    Check whether employee is on leave.
    """
    availability = getattr(
        employee,
        "availability",
        None,
    )

    return str(availability).strip().lower() in [
        "leave",
        "on leave",
    ]


# ============================================================
# COUNT CALCULATIONS
# ============================================================

def count_by_status(records):
    """
    Return dictionary containing record counts by status.
    """
    counts = {}

    if not records:
        return counts

    for record in records:
        status = getattr(
            record,
            "status",
            None
        )

        if status is None:
            status = "Unknown"

        counts[status] = counts.get(status, 0) + 1

    return counts


def count_by_currency(records):
    """
    Return dictionary containing record counts by currency.
    """
    counts = {}

    if not records:
        return counts

    for record in records:
        currency = getattr(
            record,
            "currency",
            None
        )

        if currency is None:
            currency = "Unknown"

        counts[currency] = counts.get(currency, 0) + 1

    return counts


def count_records(records):
    """
    Safely count records.
    """
    if not records:
        return 0

    return len(records)


# ============================================================
# FINANCIAL TOTALS
# ============================================================

def calculate_total_revenue(placements):
    """
    Calculate total annual revenue across placements.
    """
    total = Decimal("0.00")

    if placements:
        for placement in placements:
            total += to_decimal(
                getattr(
                    placement,
                    "client_monthly_fee",
                    0
                )
            ) * 12

    return round_money(total)


def calculate_total_worker_cost(placements):
    """
    Calculate total annual worker cost.
    """
    total = Decimal("0.00")

    if placements:
        for placement in placements:
            total += to_decimal(
                getattr(
                    placement,
                    "worker_monthly_cost",
                    0
                )
            ) * 12

    return round_money(total)


def calculate_total_margin(placements):
    """
    Calculate total annual gross margin.
    """
    revenue = calculate_total_revenue(placements)
    cost = calculate_total_worker_cost(placements)

    return round_money(
        to_decimal(revenue) - to_decimal(cost)
    )


def calculate_total_invoice_value(invoices):
    """
    Calculate total invoice value.
    """
    total = Decimal("0.00")

    if invoices:
        for invoice in invoices:
            total += to_decimal(
                getattr(
                    invoice,
                    "total_amount",
                    0
                )
            )

    return round_money(total)


def calculate_total_invoice_paid(invoices):
    """
    Calculate total invoice amount paid.
    """
    total = Decimal("0.00")

    if invoices:
        for invoice in invoices:
            total += to_decimal(
                getattr(
                    invoice,
                    "amount_paid",
                    0
                )
            )

    return round_money(total)


def calculate_total_invoice_outstanding(invoices):
    """
    Calculate total outstanding invoice balance.
    """
    total = Decimal("0.00")

    if invoices:
        for invoice in invoices:
            total += to_decimal(
                calculate_invoice_balance(invoice)
            )

    return round_money(total)


def calculate_financial_summary(
    placements=None,
    invoices=None,
):
    """
    Return a combined financial summary.
    """
    revenue = calculate_total_revenue(
        placements or []
    )

    worker_cost = calculate_total_worker_cost(
        placements or []
    )

    margin = calculate_total_margin(
        placements or []
    )

    invoice_value = calculate_total_invoice_value(
        invoices or []
    )

    invoice_paid = calculate_total_invoice_paid(
        invoices or []
    )

    invoice_outstanding = calculate_total_invoice_outstanding(
        invoices or []
    )

    return {
        "annual_revenue": revenue,
        "annual_worker_cost": worker_cost,
        "annual_margin": margin,
        "invoice_value": invoice_value,
        "invoice_paid": invoice_paid,
        "invoice_outstanding": invoice_outstanding,
    }


# ============================================================
# DATA QUALITY / VALIDATION
# ============================================================

def is_positive_amount(value):
    """
    Check whether amount is greater than zero.
    """
    return to_decimal(value) > 0


def is_non_negative_amount(value):
    """
    Check whether amount is zero or greater.
    """
    return to_decimal(value) >= 0


def dates_are_valid(start_date, end_date):
    """
    Check whether end date is not before start date.
    """
    if not start_date or not end_date:
        return True

    return end_date >= start_date


def amount_is_valid_for_invoice(
    payment_amount,
    invoice_balance,
):
    """
    Check whether payment is positive and does not
    exceed the invoice balance.
    """
    payment = to_decimal(payment_amount)
    balance = to_decimal(invoice_balance)

    if payment <= 0:
        return False

    if payment > balance:
        return False

    return True


# ============================================================
# FORMATTING
# ============================================================

def format_money(
    amount,
    currency="GBP",
):
    """
    Format monetary amount.

    Example:
        format_money(1250, "GBP")
        -> GBP 1,250.00
    """
    value = money_to_float(amount)

    return f"{currency} {value:,.2f}"


def format_percentage(value):
    """
    Format percentage.
    """
    return f"{to_float(value):,.2f}%"


def format_number(value, decimals=2):
    """
    Format a number with commas.
    """
    number = to_float(value)

    return f"{number:,.{decimals}f}"


# ============================================================
# RECORD SUMMARY
# ============================================================

def summarise_record_counts(
    clients=None,
    jobs=None,
    candidates=None,
    employees=None,
    placements=None,
    contracts=None,
    invoices=None,
    payments=None,
):
    """
    Return a simple CRM record count summary.
    """
    return {
        "clients": count_records(clients),
        "jobs": count_records(jobs),
        "candidates": count_records(candidates),
        "employees": count_records(employees),
        "placements": count_records(placements),
        "contracts": count_records(contracts),
        "invoices": count_records(invoices),
        "payments": count_records(payments),
    }


# ============================================================
# CURRENCY-SPECIFIC FINANCIAL TOTALS
# ============================================================

def calculate_revenue_by_currency(placements):
    """
    Calculate annual revenue grouped by currency.
    """
    totals = {}

    if not placements:
        return totals

    for placement in placements:
        currency = getattr(
            placement,
            "currency",
            None
        ) or "GBP"

        revenue = (
            to_decimal(
                getattr(
                    placement,
                    "client_monthly_fee",
                    0
                )
            ) * 12
        )

        totals[currency] = (
            totals.get(currency, Decimal("0.00"))
            + revenue
        )

    return {
        currency: round_money(amount)
        for currency, amount in totals.items()
    }


def calculate_cost_by_currency(placements):
    """
    Calculate annual worker cost grouped by currency.
    """
    totals = {}

    if not placements:
        return totals

    for placement in placements:
        currency = getattr(
            placement,
            "currency",
            None
        ) or "GBP"

        cost = (
            to_decimal(
                getattr(
                    placement,
                    "worker_monthly_cost",
                    0
                )
            ) * 12
        )

        totals[currency] = (
            totals.get(currency, Decimal("0.00"))
            + cost
        )

    return {
        currency: round_money(amount)
        for currency, amount in totals.items()
    }


def calculate_margin_by_currency(placements):
    """
    Calculate annual gross margin grouped by currency.
    """
    revenue = calculate_revenue_by_currency(
        placements
    )

    cost = calculate_cost_by_currency(
        placements
    )

    currencies = set(
        revenue.keys()
    ) | set(
        cost.keys()
    )

    totals = {}

    for currency in currencies:
        totals[currency] = round_money(
            to_decimal(
                revenue.get(
                    currency,
                    Decimal("0.00")
                )
            )
            -
            to_decimal(
                cost.get(
                    currency,
                    Decimal("0.00")
                )
            )
        )

    return totals