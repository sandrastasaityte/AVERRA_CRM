from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# ============================================================

# GENERAL NUMBER / MONEY HELPERS

# ============================================================

MONEY_DECIMAL_PLACES = Decimal("0.01")

def to_float(value, default=0.0):
"""
Safely convert a value to float.

```
Handles:
- None
- integers
- floats
- Decimal
- numeric strings
- strings containing commas
- invalid values
"""

try:
    if value is None:
        return default

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return default

        value = value.replace(",", "")

    return float(value)

except (TypeError, ValueError, InvalidOperation):
    return default
```

def to_decimal(value, default=Decimal("0.00")):
"""
Safely convert a value to Decimal.

```
Decimal is preferred for financial calculations where
exact two-decimal monetary values are required.
"""

try:

    if value is None:
        return default

    if isinstance(value, Decimal):
        return value

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return default

        value = value.replace(",", "")

    return Decimal(str(value))

except (InvalidOperation, TypeError, ValueError):
    return default
```

def round_money(value):
"""
Round a monetary value to two decimal places.
"""

```
decimal_value = to_decimal(value)

return decimal_value.quantize(
    MONEY_DECIMAL_PLACES,
    rounding=ROUND_HALF_UP,
)
```

def money_to_float(value):
"""
Round money and return it as float.

```
Useful when displaying or storing calculated values.
"""

return float(
    round_money(value)
)
```

def safe_divide(
numerator,
denominator,
default=0.0,
):
"""
Safely divide two numbers.
"""

```
numerator = to_float(numerator)
denominator = to_float(denominator)

if denominator == 0:
    return default

return numerator / denominator
```

def percentage(
numerator,
denominator,
default=0.0,
):
"""
Calculate a percentage safely.

```
Example:
    percentage(25, 100) -> 25.0
"""

denominator = to_float(denominator)

if denominator == 0:
    return default

return (
    to_float(numerator)
    / denominator
) * 100
```

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

```
revenue = to_float(
    client_monthly_fee
)

cost = to_float(
    worker_monthly_cost
)

return money_to_float(
    revenue - cost
)
```

def calculate_gross_margin_percentage(
client_monthly_fee,
worker_monthly_cost,
):
"""
Gross margin percentage.

```
Formula:

    (Revenue - Cost) / Revenue * 100
"""

revenue = to_float(
    client_monthly_fee
)

if revenue == 0:
    return 0.0

margin = calculate_gross_margin(
    client_monthly_fee,
    worker_monthly_cost,
)

return (
    margin / revenue
) * 100
```

def calculate_annual_revenue(
monthly_fee,
):
"""
Convert monthly revenue to annual revenue.
"""

```
return money_to_float(
    to_float(monthly_fee) * 12
)
```

def calculate_annual_worker_cost(
monthly_cost,
):
"""
Convert monthly worker cost to annual
worker cost.
"""

```
return money_to_float(
    to_float(monthly_cost) * 12
)
```

def calculate_annual_gross_margin(
monthly_fee,
monthly_worker_cost,
):
"""
Convert monthly gross margin to annual
gross margin.
"""

```
monthly_margin = calculate_gross_margin(
    monthly_fee,
    monthly_worker_cost,
)

return money_to_float(
    monthly_margin * 12
)
```

def calculate_placement_financials(
client_monthly_fee,
worker_monthly_cost,
):
"""
Return a complete placement financial
calculation.

```
Returns:

    {
        "monthly_revenue": ...,
        "monthly_cost": ...,
        "monthly_margin": ...,
        "margin_percentage": ...,
        "annual_revenue": ...,
        "annual_cost": ...,
        "annual_margin": ...
    }
"""

revenue = money_to_float(
    client_monthly_fee
)

cost = money_to_float(
    worker_monthly_cost
)

margin = money_to_float(
    revenue - cost
)

margin_percentage = (
    percentage(
        margin,
        revenue,
    )
    if revenue
    else 0.0
)

return {
    "monthly_revenue": revenue,
    "monthly_cost": cost,
    "monthly_margin": margin,
    "margin_percentage": margin_percentage,
    "annual_revenue": money_to_float(
        revenue * 12
    ),
    "annual_cost": money_to_float(
        cost * 12
    ),
    "annual_margin": money_to_float(
        margin * 12
    ),
}
```

def placement_is_active(
status,
):
"""
Check whether a placement is currently active.
"""

```
return status == "Active"
```

def placement_is_scheduled(
status,
):
"""
Check whether a placement is scheduled.
"""

```
return status == "Scheduled"
```

def placement_is_completed(
status,
):
"""
Check whether a placement has been completed.
"""

```
return status == "Completed"
```

def placement_is_terminated(
status,
):
"""
Check whether a placement has been terminated.
"""

```
return status == "Terminated"
```

def placement_is_current(
status,
):
"""
Check whether a placement contributes to
current operating economics.

```
Current = Active or Scheduled.
"""

return status in [
    "Active",
    "Scheduled",
]
```

def placement_is_operational(
status,
):
"""
Alias-style helper for placements that are
operationally active.
"""

```
return status in [
    "Active",
    "Scheduled",
]
```

def placement_has_negative_margin(
client_monthly_fee,
worker_monthly_cost,
):
"""
Return True when worker cost is greater
than client revenue.
"""

```
return calculate_gross_margin(
    client_monthly_fee,
    worker_monthly_cost,
) < 0
```

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

```
subtotal = to_float(subtotal)
tax = to_float(tax)

return money_to_float(
    subtotal + tax
)
```

def calculate_invoice_balance(
total_amount,
amount_paid,
):
"""
Invoice balance = total amount - amount paid.

```
Balance cannot be negative.
"""

total = to_float(
    total_amount
)

paid = to_float(
    amount_paid
)

return money_to_float(
    max(total - paid, 0.0)
)
```

def calculate_invoice_outstanding(
total_amount,
amount_paid,
):
"""
Alias for invoice balance.
"""

```
return calculate_invoice_balance(
    total_amount,
    amount_paid,
)
```

def calculate_payment_percentage(
total_amount,
amount_paid,
):
"""
Percentage of invoice paid.

```
This is intentionally not capped at 100%.
Therefore an overpayment produces a value
greater than 100%.
"""

total = to_float(
    total_amount
)

paid = to_float(
    amount_paid
)

if total == 0:
    return 0.0

return (
    paid / total
) * 100
```

def invoice_is_paid(
total_amount,
amount_paid,
):
"""
Check whether the invoice has been fully paid.
"""

```
total = to_float(
    total_amount
)

paid = to_float(
    amount_paid
)

return (
    total > 0
    and paid >= total
)
```

def invoice_is_partially_paid(
total_amount,
amount_paid,
):
"""
Check whether an invoice has received
some payment but remains outstanding.
"""

```
total = to_float(
    total_amount
)

paid = to_float(
    amount_paid
)

return (
    total > 0
    and paid > 0
    and paid < total
)
```

def invoice_is_outstanding(
total_amount,
amount_paid,
):
"""
Check whether an invoice still has
an outstanding balance.
"""

```
return (
    calculate_invoice_balance(
        total_amount,
        amount_paid,
    )
    > 0
)
```

def invoice_is_overpaid(
total_amount,
amount_paid,
):
"""
Check whether payments exceed
the invoice total.
"""

```
total = to_float(
    total_amount
)

paid = to_float(
    amount_paid
)

return paid > total
```

def invoice_is_unpaid(
total_amount,
amount_paid,
):
"""
Check whether an invoice has received
no payment.
"""

```
return (
    to_float(amount_paid)
    <= 0
    and to_float(total_amount)
    > 0
)
```

def invoice_is_open(
status,
):
"""
Check whether an invoice is still
operationally open.
"""

```
return status in [
    "Draft",
    "Sent",
    "Partially Paid",
    "Overdue",
]
```

def invoice_is_cancelled(
status,
):
"""
Check whether an invoice is cancelled.
"""

```
return status == "Cancelled"
```

def invoice_status_from_amounts(
total_amount,
amount_paid,
current_status=None,
):
"""
Determine an invoice payment status
from monetary values.

```
Cancelled status is preserved.

Otherwise:

    total <= 0
        -> Draft

    paid >= total
        -> Paid

    paid > 0
        -> Partially Paid

    current status == Overdue
        -> Overdue

    otherwise
        -> Sent
"""

if current_status == "Cancelled":
    return "Cancelled"

total = to_float(
    total_amount
)

paid = to_float(
    amount_paid
)

if total <= 0:
    return "Draft"

if paid >= total:
    return "Paid"

if paid > 0:
    return "Partially Paid"

if current_status == "Overdue":
    return "Overdue"

return "Sent"
```

# ============================================================

# PAYMENT CALCULATIONS

# ============================================================

def get_payment_amount(
payment,
):
"""
Safely obtain a payment amount.

```
Supports Payment objects and numeric values.
"""

if payment is None:
    return 0.0

if hasattr(
    payment,
    "amount",
):

    return to_float(
        getattr(
            payment,
            "amount",
            0,
        )
    )

if hasattr(
    payment,
    "payment_amount",
):

    return to_float(
        getattr(
            payment,
            "payment_amount",
            0,
        )
    )

return to_float(
    payment
)
```

def is_successful_payment_status(
status,
):
"""
Determine whether a payment status
should count as received money.

```
Pending, Failed and Reversed payments
are excluded.
"""

return status == "Received"
```

def calculate_remaining_balance(
invoice_total,
existing_payments,
):
"""
Calculate remaining invoice balance.

```
Existing payments may be:
- Payment objects
- numeric amounts

Only payments with status "Received"
are included when payment objects contain
a status field.
"""

total = to_float(
    invoice_total
)

paid = 0.0

for payment in (
    existing_payments or []
):

    if hasattr(
        payment,
        "status",
    ):

        status = getattr(
            payment,
            "status",
            None,
        )

        if not is_successful_payment_status(
            status
        ):

            continue

    paid += get_payment_amount(
        payment
    )

return money_to_float(
    max(total - paid, 0.0)
)
```

def calculate_total_payments(
payments,
successful_only=False,
):
"""
Calculate the total amount of payments.

```
If successful_only=True, only payments with
status "Received" are counted.
"""

total = 0.0

for payment in (
    payments or []
):

    if (
        successful_only
        and hasattr(
            payment,
            "status",
        )
    ):

        if not is_successful_payment_status(
            getattr(
                payment,
                "status",
                None,
            )
        ):

            continue

    total += get_payment_amount(
        payment
    )

return money_to_float(
    total
)
```

def calculate_received_payments(
payments,
):
"""
Calculate only successfully received
payments.
"""

```
return calculate_total_payments(
    payments,
    successful_only=True,
)
```

def payment_fits_invoice(
payment_amount,
invoice_balance,
):
"""
Check whether a payment fits within
the outstanding invoice balance.

```
Exact payment is allowed.
Overpayment is rejected.
"""

payment = to_float(
    payment_amount
)

balance = to_float(
    invoice_balance
)

return (
    payment > 0
    and payment <= balance
)
```

def payment_would_overpay(
payment_amount,
invoice_balance,
):
"""
Check whether a payment would exceed
the remaining invoice balance.
"""

```
payment = to_float(
    payment_amount
)

balance = to_float(
    invoice_balance
)

return (
    payment > balance
    and payment > 0
)
```

def payment_is_valid(
payment_amount,
):
"""
Check whether a payment amount is positive.
"""

```
return (
    to_float(payment_amount)
    > 0
)
```

# ============================================================

# DATE CALCULATIONS

# ============================================================

def days_between(
start_date,
end_date,
):
"""
Return number of days between two dates.

```
Returns 0 when either date is missing.
"""

if not start_date or not end_date:
    return 0

return (
    end_date - start_date
).days
```

def days_from_today(
target_date,
):
"""
Return number of days from today
to a target date.

```
Positive = future
Zero = today
Negative = past
"""

if not target_date:
    return None

return (
    target_date - date.today()
).days
```

def is_overdue(
due_date,
):
"""
Check whether a date has passed.
"""

```
if not due_date:
    return False

return due_date < date.today()
```

def is_due_today(
due_date,
):
"""
Check whether a date is today.
"""

```
if not due_date:
    return False

return due_date == date.today()
```

def is_future_date(
target_date,
):
"""
Check whether a date is in the future.
"""

```
if not target_date:
    return False

return target_date > date.today()
```

def is_today_or_past(
target_date,
):
"""
Check whether a date is today or in the past.
"""

```
if not target_date:
    return False

return target_date <= date.today()
```

def days_overdue(
due_date,
):
"""
Return the number of days a date is overdue.

```
Returns 0 when the date is not overdue.
"""

if not due_date:
    return 0

days = (
    date.today() - due_date
).days

return max(
    days,
    0,
)
```

# ============================================================

# CONTRACT CALCULATIONS

# ============================================================

def days_until_renewal(
renewal_date,
):
"""
Return number of days until contract renewal.

```
Positive = future
Zero = today
Negative = overdue
"""

return days_from_today(
    renewal_date
)
```

def contract_is_expired(
end_date,
):
"""
Check whether a contract has expired
based on its end date.
"""

```
if not end_date:
    return False

return end_date < date.today()
```

def contract_renewal_due(
renewal_date,
warning_days=30,
):
"""
Check whether a contract renewal is due
within the specified warning period.

```
Includes contracts renewing today.

Does not consider contract status because this
helper only receives a date.
"""

if not renewal_date:
    return False

days = days_until_renewal(
    renewal_date
)

if days is None:
    return False

return (
    0
    <= days
    <= warning_days
)
```

def contract_renewal_overdue(
renewal_date,
):
"""
Check whether a renewal date has passed.
"""

```
if not renewal_date:
    return False

return renewal_date < date.today()
```

def contract_renewal_today(
renewal_date,
):
"""
Check whether renewal is due today.
"""

```
if not renewal_date:
    return False

return renewal_date == date.today()
```

def contract_renewal_soon(
renewal_date,
warning_days=30,
):
"""
Check whether renewal is approaching.

```
Includes today and excludes already overdue
renewal dates.
"""

return contract_renewal_due(
    renewal_date,
    warning_days,
)
```

def contract_is_current(
start_date,
end_date,
):
"""
Check whether a contract is currently active
based purely on its dates.

```
A missing start date does not automatically make
a contract invalid.

A missing end date means the contract has no
date-based expiry.
"""

today = date.today()

if (
    start_date
    and today < start_date
):

    return False

if (
    end_date
    and today > end_date
):

    return False

return True
```

def contract_has_started(
start_date,
):
"""
Check whether a contract has started.
"""

```
if not start_date:
    return False

return start_date <= date.today()
```

def contract_starts_in_future(
start_date,
):
"""
Check whether a contract starts in the future.
"""

```
if not start_date:
    return False

return start_date > date.today()
```

def contract_duration_days(
start_date,
end_date,
):
"""
Calculate contract duration in days.

```
Returns 0 when dates are missing or invalid.
"""

if not start_date or not end_date:
    return 0

if end_date < start_date:
    return 0

return (
    end_date - start_date
).days
```

def contract_is_terminated(
status,
):
"""
Check whether a contract is terminated.
"""

```
return status == "Terminated"
```

def contract_is_signed(
status,
):
"""
Check whether a contract is signed.
"""

```
return status == "Signed"
```

def contract_is_active(
status,
):
"""
Check whether a contract has Active status.
"""

```
return status == "Active"
```

def contract_is_draft(
status,
):
"""
Check whether a contract is a draft.
"""

```
return status == "Draft"
```

def contract_is_expired_status(
status,
):
"""
Check whether a contract has Expired status.
"""

```
return status == "Expired"
```

def contract_is_operational(
status,
):
"""
Check whether a contract is operationally
relevant.

```
Active and Signed contracts are considered
operational here.
"""

return status in [
    "Active",
    "Signed",
]
```

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

```
openings = int(
    max(
        to_float(
            total_openings
        ),
        0,
    )
)

placements = int(
    max(
        to_float(
            placements_count
        ),
        0,
    )
)

return max(
    openings - placements,
    0,
)
```

def job_is_open(
status,
):
"""
Check whether a job is considered open.
"""

```
return status in [
    "Open",
    "On Hold",
]
```

def job_is_closed(
status,
):
"""
Check whether a job is closed or filled.
"""

```
return status in [
    "Closed",
    "Filled",
    "Cancelled",
]
```

def job_is_active(
status,
):
"""
Check whether a job is actively being worked on.
"""

```
return status in [
    "Open",
    "On Hold",
]
```

def job_is_filled(
status,
):
"""
Check whether a job is filled.
"""

```
return status == "Filled"
```

def job_is_cancelled(
status,
):
"""
Check whether a job is cancelled.
"""

```
return status == "Cancelled"
```

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

```
return status in [
    "Submitted",
    "Shortlisted",
    "Interview",
    "Offer",
]
```

def candidate_is_placed(
status,
):
"""
Check whether a candidate has been placed.
"""

```
return status == "Placed"
```

def candidate_is_rejected(
status,
):
"""
Check whether a candidate has been rejected.
"""

```
return status == "Rejected"
```

def candidate_is_withdrawn(
status,
):
"""
Check whether a candidate has withdrawn.
"""

```
return status == "Withdrawn"
```

def candidate_is_closed(
status,
):
"""
Check whether a candidate is no longer
active in recruitment.
"""

```
return status in [
    "Placed",
    "Rejected",
    "Withdrawn",
]
```

def candidate_is_in_interview(
status,
):
"""
Check whether a candidate is currently
at interview stage.
"""

```
return status == "Interview"
```

def candidate_is_in_offer(
status,
):
"""
Check whether a candidate is at offer stage.
"""

```
return status == "Offer"
```

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

```
return status in [
    "Available",
    "Interviewing",
    "Placed",
    "On Leave",
]
```

def employee_is_available(
status,
):
"""
Check whether an employee is currently available.
"""

```
return status == "Available"
```

def employee_is_placed(
status,
):
"""
Check whether an employee is currently placed.
"""

```
return status == "Placed"
```

def employee_is_former(
status,
):
"""
Check whether an employee is a former employee.
"""

```
return status == "Former Employee"
```

def employee_is_unavailable(
status,
):
"""
Check whether an employee is unavailable.
"""

```
return status == "Unavailable"
```

def employee_is_interviewing(
status,
):
"""
Check whether an employee is currently
being interviewed.
"""

```
return status == "Interviewing"
```

def employee_is_on_leave(
status,
):
"""
Check whether an employee is on leave.
"""

```
return status == "On Leave"
```

# ============================================================

# CRM COUNTS

# ============================================================

def count_by_status(
records,
status_attribute="status",
):
"""
Count records grouped by status.

```
Returns:

    {
        "Open": 5,
        "Closed": 2,
    }
"""

results = {}

for record in (
    records or []
):

    status = getattr(
        record,
        status_attribute,
        None,
    )

    if not status:
        status = "Unknown"

    results[status] = (
        results.get(
            status,
            0,
        )
        \+ 1
    )

return results
```

def count_by_currency(
records,
):
"""
Count records grouped by currency.
"""

```
results = {}

for record in (
    records or []
):

    currency = getattr(
        record,
        "currency",
        None,
    )

    if not currency:
        currency = "N/A"

    results[currency] = (
        results.get(
            currency,
            0,
        )
        \+ 1
    )

return results
```

def count_records(
records,
):
"""
Safely count records.
"""

```
if not records:
    return 0

try:
    return len(records)

except TypeError:

    return sum(
        1
        for _ in records
    )
```

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

```
total = 0.0

for record in (
    records or []
):

    value = getattr(
        record,
        amount_attribute,
        0,
    )

    total += to_float(
        value
    )

return money_to_float(
    total
)
```

def totals_by_currency(
records,
amount_attribute,
):
"""
Sum an amount grouped by currency.

```
No foreign exchange conversion is performed.
"""

results = {}

for record in (
    records or []
):

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

    amount = to_float(
        amount
    )

    if currency not in results:
        results[currency] = 0.0

    results[currency] += amount

for currency in results:

    results[currency] = (
        money_to_float(
            results[currency]
        )
    )

return results
```

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

```
Parameters:

    placements:
        Iterable of Placement objects.

    statuses:
        Optional list of statuses to include.

        Example:
            ["Active"]

        or:
            ["Active", "Scheduled"]

    If statuses is None, all placements
    are included.

No FX conversion is performed.
"""

results = {}

for placement in (
    placements or []
):

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

    margin = (
        revenue - cost
    )

    if currency not in results:

        results[currency] = {
            "revenue": 0.0,
            "cost": 0.0,
            "margin": 0.0,
            "placement_count": 0,
        }

    results[currency][
        "revenue"
    ] += revenue

    results[currency][
        "cost"
    ] += cost

    results[currency][
        "margin"
    ] += margin

    results[currency][
        "placement_count"
    ] += 1

for currency, values in (
    results.items()
):

    values["revenue"] = (
        money_to_float(
            values["revenue"]
        )
    )

    values["cost"] = (
        money_to_float(
            values["cost"]
        )
    )

    values["margin"] = (
        money_to_float(
            values["margin"]
        )
    )

    revenue = values[
        "revenue"
    ]

    if revenue:

        values[
            "margin_percentage"
        ] = (
            values["margin"]
            / revenue
        ) * 100

    else:

        values[
            "margin_percentage"
        ] = 0.0

return results
```

# ============================================================

# INVOICE FINANCIAL SUMMARY

# ============================================================

def invoice_financial_summary(
invoices,
):
"""
Calculate invoiced, paid and outstanding
amounts grouped by currency.

```
No FX conversion is performed.
"""

results = {}

for invoice in (
    invoices or []
):

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

    results[currency][
        "invoiced"
    ] += total

    results[currency][
        "paid"
    ] += paid

    results[currency][
        "outstanding"
    ] += outstanding

    results[currency][
        "invoice_count"
    ] += 1

for currency, values in (
    results.items()
):

    values["invoiced"] = (
        money_to_float(
            values["invoiced"]
        )
    )

    values["paid"] = (
        money_to_float(
            values["paid"]
        )
    )

    values["outstanding"] = (
        money_to_float(
            values["outstanding"]
        )
    )

return results
```

# ============================================================

# PAYMENT FINANCIAL SUMMARY

# ============================================================

def payment_financial_summary(
payments,
successful_only=True,
):
"""
Calculate payment totals grouped by currency.

```
If successful_only=True, only payments with
status "Received" are included.

No FX conversion is performed.
"""

results = {}

for payment in (
    payments or []
):

    if (
        successful_only
        and hasattr(
            payment,
            "status",
        )
    ):

        if not is_successful_payment_status(
            getattr(
                payment,
                "status",
                None,
            )
        ):

            continue

    currency = (
        getattr(
            payment,
            "currency",
            None,
        )
        or "N/A"
    )

    amount = get_payment_amount(
        payment
    )

    if currency not in results:

        results[currency] = {
            "amount": 0.0,
            "payment_count": 0,
        }

    results[currency][
        "amount"
    ] += amount

    results[currency][
        "payment_count"
    ] += 1

for currency, values in (
    results.items()
):

    values["amount"] = (
        money_to_float(
            values["amount"]
        )
    )

return results
```

# ============================================================

# DATA QUALITY HELPERS

# ============================================================

def is_negative_amount(
value,
):
"""
Check whether a numeric amount is negative.
"""

```
return (
    to_float(value)
    < 0
)
```

def is_zero_or_negative_amount(
value,
):
"""
Check whether a numeric amount is zero
or negative.
"""

```
return (
    to_float(value)
    <= 0
)
```

def date_range_is_valid(
start_date,
end_date,
):
"""
Check whether a date range is valid.

```
Missing dates are allowed.
"""

if not start_date or not end_date:
    return True

return end_date >= start_date
```

def amount_is_within_limit(
amount,
maximum,
):
"""
Check whether an amount is non-negative
and does not exceed a specified maximum.
"""

```
amount = to_float(
    amount
)

maximum = to_float(
    maximum
)

return (
    amount >= 0
    and amount <= maximum
)
```

# ============================================================

# FORMATTING HELPERS

# ============================================================

def format_money(
amount,
currency="GBP",
):
"""
Format a monetary amount.

```
Example:
    format_money(1250, "GBP")
    -> "GBP 1,250.00"
"""

value = money_to_float(
    amount
)

return (
    f"{currency} "
    f"{value:,.2f}"
)
```

def format_percentage(
value,
decimal_places=1,
):
"""
Format a percentage for display.
"""

```
number = to_float(
    value
)

return (
    f"{number:.{decimal_places}f}%"
)
```

def format_date(
value,
empty_value="—",
):
"""
Format a date consistently.

```
Example:
    30 Sep 2026
"""

if not value:
    return empty_value

try:

    return value.strftime(
        "%d %b %Y"
    )

except AttributeError:

    return empty_value
```
