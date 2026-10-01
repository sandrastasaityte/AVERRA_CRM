import streamlit as st
from datetime import date

from database import get_session
from models import (
    Placement,
    Client,
    Employee,
    Job,
    Payment,
)


# ============================================================
# CONSTANTS
# ============================================================

PLACEMENT_STATUSES = [
    "Active",
    "Scheduled",
    "Completed",
    "Terminated",
]

BILLING_FREQUENCIES = [
    "Monthly",
    "Weekly",
    "Daily",
    "Hourly",
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


def safe_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def round_money(value):
    """Round a financial value to two decimal places."""
    return round(
        safe_float(value),
        2,
    )


# ============================================================
# DISPLAY HELPERS
# ============================================================

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

    full_name = " ".join(
        part
        for part in [
            first_name,
            last_name,
        ]
        if part
    )

    return full_name or "Unknown Employee"


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


def get_job_label(job):
    """Return readable job label safely."""

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
        or f"Job #{getattr(job, 'id', '')}"
    )

    client = getattr(
        job,
        "client",
        None,
    )

    client_name = get_client_name(
        client
    )

    return (
        f"{position} — "
        f"{client_name}"
    )


def get_status_icon(status):
    """Return visual status indicator."""

    icons = {
        "Active": "🟢",
        "Scheduled": "🔵",
        "Completed": "⚪",
        "Terminated": "🔴",
    }

    return icons.get(
        status,
        "⚪",
    )


def get_status(placement):
    """Return safe placement status."""

    if not placement:
        return "Scheduled"

    status = clean_text(
        getattr(
            placement,
            "status",
            "",
        )
    )

    return (
        status
        if status in PLACEMENT_STATUSES
        else "Scheduled"
    )


def get_currency(placement):
    """Return safe placement currency."""

    if not placement:
        return "GBP"

    currency = clean_text(
        getattr(
            placement,
            "currency",
            "",
        )
    )

    return (
        currency
        if currency in CURRENCIES
        else "GBP"
    )


def get_billing_frequency(placement):
    """Return safe billing frequency."""

    if not placement:
        return "Monthly"

    frequency = clean_text(
        getattr(
            placement,
            "billing_frequency",
            "",
        )
    )

    return (
        frequency
        if frequency in BILLING_FREQUENCIES
        else "Monthly"
    )


# ============================================================
# FINANCIAL HELPERS
# ============================================================

def get_client_fee(placement):
    """Return client monthly fee safely."""

    if not placement:
        return 0.0

    return max(
        round_money(
            getattr(
                placement,
                "client_monthly_fee",
                0,
            )
        ),
        0.0,
    )


def get_worker_cost(placement):
    """Return worker monthly cost safely."""

    if not placement:
        return 0.0

    return max(
        round_money(
            getattr(
                placement,
                "worker_monthly_cost",
                0,
            )
        ),
        0.0,
    )


def calculate_margin(placement):
    """Calculate gross margin."""

    return round_money(
        get_client_fee(
            placement
        )
        - get_worker_cost(
            placement
        )
    )


def calculate_margin_percentage(placement):
    """Calculate gross margin percentage."""

    client_fee = get_client_fee(
        placement
    )

    if client_fee <= 0:
        return 0.0

    margin = calculate_margin(
        placement
    )

    return round(
        (
            margin
            / client_fee
        )
        * 100,
        1,
    )


def get_margin_status(placement):
    """Return descriptive margin status."""

    margin = calculate_margin(
        placement
    )

    if margin > 0:
        return "Positive"

    if margin < 0:
        return "Negative"

    return "Break-even"


# ============================================================
# DATE / LIFECYCLE HELPERS
# ============================================================

def get_days_active(placement):
    """Return number of active days."""

    if not placement:
        return None

    start_date = getattr(
        placement,
        "start_date",
        None,
    )

    if not start_date:
        return None

    today = date.today()

    if start_date > today:
        return 0

    end_date = getattr(
        placement,
        "end_date",
        None,
    )

    if end_date and end_date < today:
        calculation_end = end_date
    else:
        calculation_end = today

    return max(
        0,
        (
            calculation_end
            - start_date
        ).days,
    )


def get_days_until_start(placement):
    """Return number of days until placement starts."""

    if not placement:
        return None

    start_date = getattr(
        placement,
        "start_date",
        None,
    )

    if not start_date:
        return None

    return (
        start_date
        - date.today()
    ).days


def is_future_start(placement):
    """Return True if placement starts in the future."""

    days = get_days_until_start(
        placement
    )

    return (
        days is not None
        and days > 0
    )


def is_currently_active(placement):
    """Return True if placement is active today."""

    if get_status(
        placement
    ) != "Active":
        return False

    start_date = getattr(
        placement,
        "start_date",
        None,
    )

    if not start_date:
        return False

    today = date.today()

    if start_date > today:
        return False

    end_date = getattr(
        placement,
        "end_date",
        None,
    )

    if end_date and end_date < today:
        return False

    return True


def is_expired_active_placement(placement):
    """Return True if active placement has passed end date."""

    end_date = getattr(
        placement,
        "end_date",
        None,
    )

    return (
        get_status(
            placement
        ) == "Active"
        and end_date is not None
        and end_date < date.today()
    )


def is_ending_soon(
    placement,
    days=30,
):
    """Return True if active placement ends within given days."""

    if not is_currently_active(
        placement
    ):
        return False

    end_date = getattr(
        placement,
        "end_date",
        None,
    )

    if not end_date:
        return False

    remaining_days = (
        end_date
        - date.today()
    ).days

    return (
        0
        <= remaining_days
        <= days
    )


# ============================================================
# RELATIONSHIP HELPERS
# ============================================================

def get_contracts(placement):
    """Return contracts safely."""

    if not placement:
        return []

    contracts = getattr(
        placement,
        "contracts",
        None,
    )

    if contracts is None:
        return []

    try:
        return list(
            contracts
        )

    except (TypeError, AttributeError):
        return []


def get_invoices(placement):
    """Return invoices safely."""

    if not placement:
        return []

    invoices = getattr(
        placement,
        "invoices",
        None,
    )

    if invoices is None:
        return []

    try:
        return list(
            invoices
        )

    except (TypeError, AttributeError):
        return []


def get_payments_for_placement(
    session,
    placement,
):
    """
    Find payments through:

    Placement
        ↓
    Invoice
        ↓
    Payment
    """

    invoices = get_invoices(
        placement
    )

    invoice_ids = []

    for invoice in invoices:

        invoice_id = getattr(
            invoice,
            "id",
            None,
        )

        if invoice_id is not None:
            invoice_ids.append(
                invoice_id
            )

    if not invoice_ids:
        return []

    try:

        return (
            session.query(
                Payment
            )
            .filter(
                Payment.invoice_id.in_(
                    invoice_ids
                )
            )
            .all()
        )

    except Exception:

        return []


def has_contracts(placement):
    """Return True when contracts exist."""

    return bool(
        get_contracts(
            placement
        )
    )


def has_invoices(placement):
    """Return True when invoices exist."""

    return bool(
        get_invoices(
            placement
        )
    )


def has_payments(
    session,
    placement,
):
    """Return True when payments exist."""

    return bool(
        get_payments_for_placement(
            session,
            placement,
        )
    )


def has_financial_history(
    session,
    placement,
):
    """Return True if financial history exists."""

    if has_contracts(
        placement
    ):
        return True

    if has_invoices(
        placement
    ):
        return True

    if has_payments(
        session,
        placement,
    ):
        return True

    return False


# ============================================================
# FINANCIAL SUMMARY HELPERS
# ============================================================

def get_currency_totals(
    placements,
    value_function,
    statuses=None,
):
    """Calculate totals separately by currency."""

    totals = {}

    if statuses is None:
        statuses = PLACEMENT_STATUSES

    for placement in placements:

        if (
            get_status(
                placement
            )
            not in statuses
        ):
            continue

        currency = get_currency(
            placement
        )

        value = round_money(
            value_function(
                placement
            )
        )

        totals[currency] = round_money(
            totals.get(
                currency,
                0.0,
            )
            + value
        )

    return totals


def format_currency_totals(
    totals,
):
    """Format currency totals for display."""

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
# MAIN SCREEN
# ============================================================

def show_placements():

    st.title(
        "Placements"
    )

    st.caption(
        "Manage employee placements from assignment through completion."
    )

    session = get_session()

    # ========================================================
    # SESSION STATE
    # ========================================================

    if (
        "editing_placement_id"
        not in st.session_state
    ):
        st.session_state.editing_placement_id = None

    if (
        "confirm_delete_placement_id"
        not in st.session_state
    ):
        st.session_state.confirm_delete_placement_id = None

    try:

        # ====================================================
        # LOAD DATA
        # ====================================================

        clients = (
            session.query(
                Client
            )
            .order_by(
                Client.company_name.asc()
            )
            .all()
        )

        employees = (
            session.query(
                Employee
            )
            .order_by(
                Employee.first_name.asc(),
                Employee.last_name.asc(),
            )
            .all()
        )

        jobs = (
            session.query(
                Job
            )
            .order_by(
                Job.position.asc()
            )
            .all()
        )

        placements = (
            session.query(
                Placement
            )
            .order_by(
                Placement.start_date.desc(),
                Placement.id.desc(),
            )
            .all()
        )

        # ====================================================
        # REQUIRED DATA
        # ====================================================

        if not clients:

            st.warning(
                "Please add a client before creating a placement."
            )

            return

        if not employees:

            st.warning(
                "Please add an employee before creating a placement."
            )

            return

        # ====================================================
        # CURRENT EDIT
        # ====================================================

        editing_placement = None

        editing_id = (
            st.session_state.editing_placement_id
        )

        if editing_id is not None:

            editing_placement = session.get(
                Placement,
                editing_id,
            )

            if editing_placement is None:

                st.session_state.editing_placement_id = None

        # ====================================================
        # FORM HEADER
        # ====================================================

        if editing_placement:

            st.subheader(
                "Edit Placement"
            )

            st.caption(
                f"Editing Placement #{editing_placement.id}"
            )

        else:

            st.subheader(
                "Add Placement"
            )

        # ====================================================
        # CLIENT OPTIONS
        # ====================================================

        client_options = {}

        for client in clients:

            label = (
                f"{get_client_name(client)} "
                f"(ID: {client.id})"
            )

            client_options[
                label
            ] = client.id

        client_labels = list(
            client_options.keys()
        )

        client_ids = list(
            client_options.values()
        )

        # ====================================================
        # EMPLOYEE OPTIONS
        # ====================================================

        employee_options = {}

        for employee in employees:

            label = (
                f"{get_employee_name(employee)} "
                f"(ID: {employee.id})"
            )

            employee_options[
                label
            ] = employee.id

        employee_labels = list(
            employee_options.keys()
        )

        employee_ids = list(
            employee_options.values()
        )

        # ====================================================
        # JOB OPTIONS
        # ====================================================

        job_options = {}

        for job in jobs:

            label = (
                f"{get_job_label(job)} "
                f"(ID: {job.id})"
            )

            job_options[
                label
            ] = job.id

        job_labels = list(
            job_options.keys()
        )

        job_selection_labels = [
            "No Job",
            *job_labels,
        ]

        # ====================================================
        # CURRENT CLIENT
        # ====================================================

        if editing_placement:

            current_client_id = getattr(
                editing_placement,
                "client_id",
                None,
            )

            client_index = (
                client_ids.index(
                    current_client_id
                )
                if current_client_id in client_ids
                else 0
            )

        else:

            client_index = 0

        # ====================================================
        # CURRENT EMPLOYEE
        # ====================================================

        if editing_placement:

            current_employee_id = getattr(
                editing_placement,
                "employee_id",
                None,
            )

            employee_index = (
                employee_ids.index(
                    current_employee_id
                )
                if current_employee_id in employee_ids
                else 0
            )

        else:

            employee_index = 0

        # ====================================================
        # CURRENT JOB
        # ====================================================

        current_job_label = "No Job"

        if (
            editing_placement
            and getattr(
                editing_placement,
                "job_id",
                None,
            )
        ):

            for label, job_id in job_options.items():

                if (
                    job_id
                    == editing_placement.job_id
                ):

                    current_job_label = label
                    break

        job_index = (
            job_selection_labels.index(
                current_job_label
            )
            if current_job_label in job_selection_labels
            else 0
        )

        # ====================================================
        # FORM
        # ====================================================

        form_key = (
            "edit_placement_form"
            if editing_placement
            else "add_placement_form"
        )

        with st.form(
            form_key
        ):

            # ------------------------------------------------
            # CLIENT / EMPLOYEE
            # ------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                selected_client = st.selectbox(
                    "Client *",
                    client_labels,
                    index=client_index,
                )

            with col2:

                selected_employee = st.selectbox(
                    "Employee *",
                    employee_labels,
                    index=employee_index,
                )

            # ------------------------------------------------
            # JOB / POSITION
            # ------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                selected_job = st.selectbox(
                    "Job",
                    job_selection_labels,
                    index=job_index,
                )

            with col2:

                position = st.text_input(
                    "Position *",
                    value=(
                        clean_text(
                            getattr(
                                editing_placement,
                                "position",
                                "",
                            )
                        )
                        if editing_placement
                        else ""
                    ),
                    placeholder="Example: Finance Specialist",
                )

            # ------------------------------------------------
            # DATES
            # ------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                start_date = st.date_input(
                    "Start Date *",
                    value=(
                        getattr(
                            editing_placement,
                            "start_date",
                            None,
                        )
                        if (
                            editing_placement
                            and getattr(
                                editing_placement,
                                "start_date",
                                None,
                            )
                        )
                        else date.today()
                    ),
                )

            with col2:

                has_end_date = st.checkbox(
                    "Set End Date",
                    value=(
                        bool(
                            editing_placement
                            and getattr(
                                editing_placement,
                                "end_date",
                                None,
                            )
                        )
                    ),
                )

                if has_end_date:

                    end_date = st.date_input(
                        "End Date",
                        value=(
                            getattr(
                                editing_placement,
                                "end_date",
                                None,
                            )
                            if (
                                editing_placement
                                and getattr(
                                    editing_placement,
                                    "end_date",
                                    None,
                                )
                            )
                            else date.today()
                        ),
                    )

                else:

                    end_date = None

            # ------------------------------------------------
            # STATUS / BILLING
            # ------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                current_status = (
                    get_status(
                        editing_placement
                    )
                    if editing_placement
                    else "Scheduled"
                )

                status_index = (
                    PLACEMENT_STATUSES.index(
                        current_status
                    )
                    if current_status in PLACEMENT_STATUSES
                    else 0
                )

                status = st.selectbox(
                    "Status",
                    PLACEMENT_STATUSES,
                    index=status_index,
                )

            with col2:

                current_frequency = (
                    get_billing_frequency(
                        editing_placement
                    )
                    if editing_placement
                    else "Monthly"
                )

                frequency_index = (
                    BILLING_FREQUENCIES.index(
                        current_frequency
                    )
                    if current_frequency in BILLING_FREQUENCIES
                    else 0
                )

                billing_frequency = st.selectbox(
                    "Billing Frequency",
                    BILLING_FREQUENCIES,
                    index=frequency_index,
                )

            # ------------------------------------------------
            # FINANCIALS
            # ------------------------------------------------

            st.subheader(
                "Financials"
            )

            st.caption(
                "Client Monthly Fee and Worker Monthly Cost "
                "are stored as monthly values in the current database. "
                "Billing Frequency is recorded separately."
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                client_monthly_fee = st.number_input(
                    "Client Monthly Fee",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    value=(
                        get_client_fee(
                            editing_placement
                        )
                        if editing_placement
                        else 0.0
                    ),
                )

            with col2:

                worker_monthly_cost = st.number_input(
                    "Worker Monthly Cost",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    value=(
                        get_worker_cost(
                            editing_placement
                        )
                        if editing_placement
                        else 0.0
                    ),
                )

            with col3:

                current_currency = (
                    get_currency(
                        editing_placement
                    )
                    if editing_placement
                    else "GBP"
                )

                currency_index = (
                    CURRENCIES.index(
                        current_currency
                    )
                    if current_currency in CURRENCIES
                    else 0
                )

                currency = st.selectbox(
                    "Currency",
                    CURRENCIES,
                    index=currency_index,
                )

            # ------------------------------------------------
            # NOTES
            # ------------------------------------------------

            notes = st.text_area(
                "Notes",
                value=(
                    clean_text(
                        getattr(
                            editing_placement,
                            "notes",
                            "",
                        )
                    )
                    if editing_placement
                    else ""
                ),
                placeholder="Additional placement information...",
            )

            # ------------------------------------------------
            # SUBMIT
            # ------------------------------------------------

            submitted = st.form_submit_button(
                (
                    "Save Changes"
                    if editing_placement
                    else "Create Placement"
                ),
                type="primary",
                use_container_width=True,
            )

        # ====================================================
        # PROCESS FORM
        # ====================================================

        if submitted:

            errors = []

            position_clean = clean_text(
                position
            )

            notes_clean = clean_text(
                notes
            )

            selected_client_id = (
                client_options[
                    selected_client
                ]
            )

            selected_employee_id = (
                employee_options[
                    selected_employee
                ]
            )

            selected_job_id = None

            if selected_job != "No Job":

                selected_job_id = (
                    job_options[
                        selected_job
                    ]
                )

            client_monthly_fee = round_money(
                client_monthly_fee
            )

            worker_monthly_cost = round_money(
                worker_monthly_cost
            )

            # ================================================
            # REQUIRED FIELD VALIDATION
            # ================================================

            if not position_clean:

                errors.append(
                    "Position is required."
                )

            if not start_date:

                errors.append(
                    "Start Date is required."
                )

            # ================================================
            # DATE VALIDATION
            # ================================================

            if (
                end_date
                and start_date
                and end_date < start_date
            ):

                errors.append(
                    "End Date cannot be before Start Date."
                )

            if (
                status == "Active"
                and start_date
                and start_date > date.today()
            ):

                errors.append(
                    "An Active placement cannot have a future Start Date."
                )

            if (
                status == "Active"
                and end_date
                and end_date < date.today()
            ):

                errors.append(
                    "An Active placement cannot have an End Date "
                    "that has already passed. Change the status to "
                    "Completed or Terminated."
                )

            if (
                status == "Completed"
                and not end_date
            ):

                errors.append(
                    "A Completed placement must have an End Date."
                )

            if (
                status == "Terminated"
                and not end_date
            ):

                errors.append(
                    "A Terminated placement must have an End Date."
                )

            if (
                status in [
                    "Completed",
                    "Terminated",
                ]
                and start_date
                and start_date > date.today()
            ):

                errors.append(
                    f"A {status} placement cannot have a future Start Date."
                )

            if (
                status in [
                    "Completed",
                    "Terminated",
                ]
                and end_date
                and end_date > date.today()
            ):

                errors.append(
                    f"A {status} placement cannot have a future End Date."
                )

            # ================================================
            # FINANCIAL VALIDATION
            # ================================================

            if client_monthly_fee < 0:

                errors.append(
                    "Client monthly fee cannot be negative."
                )

            if worker_monthly_cost < 0:

                errors.append(
                    "Worker monthly cost cannot be negative."
                )

            # ================================================
            # JOB VALIDATION
            # ================================================

            selected_job_object = None

            if selected_job_id:

                selected_job_object = session.get(
                    Job,
                    selected_job_id,
                )

                if selected_job_object is None:

                    errors.append(
                        "The selected job could not be found."
                    )

                else:

                    job_client_id = getattr(
                        selected_job_object,
                        "client_id",
                        None,
                    )

                    if (
                        job_client_id
                        != selected_client_id
                    ):

                        errors.append(
                            "The selected job belongs to a different "
                            "client. Please select a matching client and job."
                        )

            # ================================================
            # FINANCIAL HISTORY
            # ================================================

            attached_contracts = []

            attached_invoices = []

            attached_payments = []

            if editing_placement:

                attached_contracts = get_contracts(
                    editing_placement
                )

                attached_invoices = get_invoices(
                    editing_placement
                )

                attached_payments = (
                    get_payments_for_placement(
                        session,
                        editing_placement,
                    )
                )

            has_history = bool(
                attached_contracts
                or attached_invoices
                or attached_payments
            )

            # ================================================
            # PROTECT CLIENT
            # ================================================

            if (
                editing_placement
                and (
                    editing_placement.client_id
                    != selected_client_id
                )
                and has_history
            ):

                errors.append(
                    "Client cannot be changed because this placement "
                    "already has financial history attached."
                )

            # ================================================
            # PROTECT EMPLOYEE
            # ================================================

            if (
                editing_placement
                and (
                    editing_placement.employee_id
                    != selected_employee_id
                )
                and has_history
            ):

                errors.append(
                    "Employee cannot be changed because this placement "
                    "already has financial history attached."
                )

            # ================================================
            # PROTECT CURRENCY
            # ================================================

            if (
                editing_placement
                and currency
                != get_currency(
                    editing_placement
                )
                and has_history
            ):

                errors.append(
                    "Currency cannot be changed because this placement "
                    "already has financial history attached."
                )

            # ================================================
            # PROTECT JOB
            # ================================================

            if (
                editing_placement
                and (
                    getattr(
                        editing_placement,
                        "job_id",
                        None,
                    )
                    != selected_job_id
                )
                and (
                    attached_invoices
                    or attached_payments
                )
            ):

                errors.append(
                    "Job cannot be changed because this placement "
                    "already has invoice or payment history."
                )

            # ================================================
            # DUPLICATE PLACEMENT CHECK
            # ================================================

            if (
                selected_job_id
                and status in [
                    "Active",
                    "Scheduled",
                ]
            ):

                duplicate_query = (
                    session.query(
                        Placement
                    )
                    .filter(
                        Placement.employee_id
                        == selected_employee_id,

                        Placement.job_id
                        == selected_job_id,

                        Placement.status.in_(
                            [
                                "Active",
                                "Scheduled",
                            ]
                        ),
                    )
                )

                if editing_placement:

                    duplicate_query = (
                        duplicate_query.filter(
                            Placement.id
                            != editing_placement.id
                        )
                    )

                duplicate = (
                    duplicate_query.first()
                )

                if duplicate:

                    errors.append(
                        "This employee already has an Active "
                        "or Scheduled placement for this job."
                    )

            # ================================================
            # SHOW ERRORS
            # ================================================

            if errors:

                for error in errors:

                    st.error(
                        error
                    )

            # ================================================
            # SAVE
            # ================================================

            else:

                try:

                    if editing_placement:

                        editing_placement.client_id = (
                            selected_client_id
                        )

                        editing_placement.employee_id = (
                            selected_employee_id
                        )

                        editing_placement.job_id = (
                            selected_job_id
                        )

                        editing_placement.position = (
                            position_clean
                        )

                        editing_placement.start_date = (
                            start_date
                        )

                        editing_placement.end_date = (
                            end_date
                        )

                        editing_placement.status = (
                            status
                        )

                        editing_placement.billing_frequency = (
                            billing_frequency
                        )

                        editing_placement.client_monthly_fee = (
                            client_monthly_fee
                        )

                        editing_placement.worker_monthly_cost = (
                            worker_monthly_cost
                        )

                        editing_placement.currency = (
                            currency
                        )

                        editing_placement.notes = (
                            notes_clean
                        )

                        session.commit()

                        st.session_state.editing_placement_id = None

                        st.success(
                            "Placement updated successfully."
                        )

                        st.rerun()

                    else:

                        placement = Placement(
                            client_id=selected_client_id,
                            employee_id=selected_employee_id,
                            job_id=selected_job_id,
                            position=position_clean,
                            start_date=start_date,
                            end_date=end_date,
                            client_monthly_fee=client_monthly_fee,
                            worker_monthly_cost=worker_monthly_cost,
                            currency=currency,
                            billing_frequency=billing_frequency,
                            status=status,
                            notes=notes_clean,
                        )

                        session.add(
                            placement
                        )

                        session.commit()

                        st.success(
                            "Placement created successfully."
                        )

                        st.rerun()

                except Exception as error:

                    session.rollback()

                    st.error(
                        "The placement could not be saved."
                    )

                    st.caption(
                        f"Error: {error}"
                    )

        # ====================================================
        # CANCEL EDITING
        # ====================================================

        if editing_placement:

            if st.button(
                "Cancel Editing",
                use_container_width=True,
            ):

                st.session_state.editing_placement_id = None

                st.rerun()

        # ====================================================
        # PLACEMENT REGISTER
        # ====================================================

        st.divider()

        st.subheader(
            "Placement Register"
        )

        if not placements:

            st.info(
                "No placements have been created yet."
            )

            return

        # ====================================================
        # KPI CALCULATIONS
        # ====================================================

        total_placements = len(
            placements
        )

        active_placements = sum(
            1
            for placement in placements
            if get_status(
                placement
            ) == "Active"
        )

        scheduled_placements = sum(
            1
            for placement in placements
            if get_status(
                placement
            ) == "Scheduled"
        )

        completed_placements = sum(
            1
            for placement in placements
            if get_status(
                placement
            ) == "Completed"
        )

        terminated_placements = sum(
            1
            for placement in placements
            if get_status(
                placement
            ) == "Terminated"
        )

        currently_active = sum(
            1
            for placement in placements
            if is_currently_active(
                placement
            )
        )

        future_starts = sum(
            1
            for placement in placements
            if is_future_start(
                placement
            )
        )

        expired_active = sum(
            1
            for placement in placements
            if is_expired_active_placement(
                placement
            )
        )

        negative_margin_placements = sum(
            1
            for placement in placements
            if calculate_margin(
                placement
            ) < 0
        )

        # ====================================================
        # ACTIVE FINANCIAL TOTALS
        # ====================================================

        active_placements_list = [
            placement
            for placement in placements
            if is_currently_active(
                placement
            )
        ]

        active_client_fee_totals = (
            get_currency_totals(
                active_placements_list,
                get_client_fee,
                statuses=[
                    "Active"
                ],
            )
        )

        active_worker_cost_totals = (
            get_currency_totals(
                active_placements_list,
                get_worker_cost,
                statuses=[
                    "Active"
                ],
            )
        )

        active_margin_totals = (
            get_currency_totals(
                active_placements_list,
                calculate_margin,
                statuses=[
                    "Active"
                ],
            )
        )

        # ====================================================
        # KPI DISPLAY
        # ====================================================

        k1, k2, k3, k4, k5, k6 = st.columns(6)

        with k1:

            st.metric(
                "Total",
                total_placements,
            )

        with k2:

            st.metric(
                "Active",
                active_placements,
            )

        with k3:

            st.metric(
                "Currently Active",
                currently_active,
            )

        with k4:

            st.metric(
                "Scheduled",
                scheduled_placements,
            )

        with k5:

            st.metric(
                "Completed",
                completed_placements,
            )

        with k6:

            st.metric(
                "Terminated",
                terminated_placements,
            )

        # ====================================================
        # ALERTS
        # ====================================================

        alert_col1, alert_col2, alert_col3 = st.columns(3)

        with alert_col1:

            if future_starts:

                st.info(
                    f"{future_starts} placement(s) "
                    "have future start dates."
                )

        with alert_col2:

            if expired_active:

                st.warning(
                    f"{expired_active} Active placement(s) "
                    "have passed their end date."
                )

        with alert_col3:

            if negative_margin_placements:

                st.error(
                    f"{negative_margin_placements} placement(s) "
                    "have negative gross margin."
                )

        # ====================================================
        # FINANCIAL SUMMARY
        # ====================================================

        st.caption(
            "Active financial totals are kept separate by currency."
        )

        financial_col1, financial_col2, financial_col3 = st.columns(3)

        with financial_col1:

            st.write(
                "**Active Client Fees**"
            )

            st.write(
                format_currency_totals(
                    active_client_fee_totals
                )
            )

        with financial_col2:

            st.write(
                "**Active Worker Costs**"
            )

            st.write(
                format_currency_totals(
                    active_worker_cost_totals
                )
            )

        with financial_col3:

            st.write(
                "**Active Gross Margin**"
            )

            st.write(
                format_currency_totals(
                    active_margin_totals
                )
            )

        # ====================================================
        # FILTERS
        # ====================================================

        st.divider()

        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

        with filter_col1:

            status_filter = st.selectbox(
                "Status",
                [
                    "All",
                    *PLACEMENT_STATUSES,
                ],
            )

        with filter_col2:

            client_filter_options = {
                "All Clients": None
            }

            for client in clients:

                label = (
                    f"{get_client_name(client)} "
                    f"(ID: {client.id})"
                )

                client_filter_options[
                    label
                ] = client.id

            selected_client_filter = st.selectbox(
                "Client",
                list(
                    client_filter_options.keys()
                ),
            )

        with filter_col3:

            currency_filter = st.selectbox(
                "Currency",
                [
                    "All",
                    *CURRENCIES,
                ],
            )

        with filter_col4:

            search = st.text_input(
                "Search",
                placeholder=(
                    "ID, employee, client, job or position..."
                ),
            )

        # ====================================================
        # OPERATIONAL FILTER
        # ====================================================

        operational_filter = st.selectbox(
            "Operational View",
            [
                "All Placements",
                "Currently Active",
                "Future Starts",
                "Expired Active",
                "Negative Margin",
                "Ending Within 30 Days",
                "With Contracts",
                "With Invoices",
                "With Payments",
            ],
        )

        # ====================================================
        # APPLY FILTERS
        # ====================================================

        filtered_placements = list(
            placements
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if status_filter != "All":

            filtered_placements = [
                placement
                for placement in filtered_placements
                if get_status(
                    placement
                ) == status_filter
            ]

        # ----------------------------------------------------
        # CLIENT
        # ----------------------------------------------------

        selected_client_filter_id = (
            client_filter_options[
                selected_client_filter
            ]
        )

        if selected_client_filter_id is not None:

            filtered_placements = [
                placement
                for placement in filtered_placements
                if getattr(
                    placement,
                    "client_id",
                    None,
                )
                == selected_client_filter_id
            ]

        # ----------------------------------------------------
        # CURRENCY
        # ----------------------------------------------------

        if currency_filter != "All":

            filtered_placements = [
                placement
                for placement in filtered_placements
                if get_currency(
                    placement
                ) == currency_filter
            ]

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        search_lower = clean_text(
            search
        ).lower()

        if search_lower:

            filtered_placements = [
                placement
                for placement in filtered_placements
                if (
                    search_lower
                    in str(
                        getattr(
                            placement,
                            "id",
                            "",
                        )
                    ).lower()
                )
                or (
                    search_lower
                    in clean_text(
                        getattr(
                            placement,
                            "position",
                            "",
                        )
                    ).lower()
                )
                or (
                    getattr(
                        placement,
                        "client",
                        None,
                    )
                    and search_lower
                    in get_client_name(
                        placement.client
                    ).lower()
                )
                or (
                    getattr(
                        placement,
                        "employee",
                        None,
                    )
                    and search_lower
                    in get_employee_name(
                        placement.employee
                    ).lower()
                )
                or (
                    getattr(
                        placement,
                        "job",
                        None,
                    )
                    and search_lower
                    in get_job_label(
                        placement.job
                    ).lower()
                )
            ]

        # ----------------------------------------------------
        # OPERATIONAL FILTER
        # ----------------------------------------------------

        if operational_filter == "Currently Active":

            filtered_placements = [
                placement
                for placement in filtered_placements
                if is_currently_active(
                    placement
                )
            ]

        elif operational_filter == "Future Starts":

            filtered_placements = [
                placement
                for placement in filtered_placements
                if is_future_start(
                    placement
                )
            ]

        elif operational_filter == "Expired Active":

            filtered_placements = [
                placement
                for placement in filtered_placements
                if is_expired_active_placement(
                    placement
                )
            ]

        elif operational_filter == "Negative Margin":

            filtered_placements = [
                placement
                for placement in filtered_placements
                if calculate_margin(
                    placement
                ) < 0
            ]

        elif operational_filter == "Ending Within 30 Days":

            filtered_placements = [
                placement
                for placement in filtered_placements
                if is_ending_soon(
                    placement,
                    30,
                )
            ]

        elif operational_filter == "With Contracts":

            filtered_placements = [
                placement
                for placement in filtered_placements
                if has_contracts(
                    placement
                )
            ]

        elif operational_filter == "With Invoices":

            filtered_placements = [
                placement
                for placement in filtered_placements
                if has_invoices(
                    placement
                )
            ]

        elif operational_filter == "With Payments":

            filtered_placements = [
                placement
                for placement in filtered_placements
                if has_payments(
                    session,
                    placement,
                )
            ]

        # ====================================================
        # RESULT COUNT
        # ====================================================

        st.caption(
            f"Showing {len(filtered_placements)} "
            f"of {len(placements)} placement(s)"
        )

        if not filtered_placements:

            st.info(
                "No placements match your filters."
            )

            return

        # ====================================================
        # DISPLAY PLACEMENTS
        # ====================================================

        for placement in filtered_placements:

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

            job = getattr(
                placement,
                "job",
                None,
            )

            employee_name = get_employee_name(
                employee
            )

            client_name = get_client_name(
                client
            )

            job_name = get_job_label(
                job
            )

            status = get_status(
                placement
            )

            currency = get_currency(
                placement
            )

            billing_frequency = (
                get_billing_frequency(
                    placement
                )
            )

            client_fee = get_client_fee(
                placement
            )

            worker_cost = get_worker_cost(
                placement
            )

            margin = calculate_margin(
                placement
            )

            margin_percentage = (
                calculate_margin_percentage(
                    placement
                )
            )

            margin_status = (
                get_margin_status(
                    placement
                )
            )

            with st.container(
                border=True
            ):

                # ==========================================
                # MAIN ROW
                # ==========================================

                col1, col2, col3, col4, col5 = st.columns(
                    [
                        2.2,
                        2.2,
                        2.0,
                        2.2,
                        1.6,
                    ]
                )

                # ------------------------------------------
                # PLACEMENT
                # ------------------------------------------

                with col1:

                    st.write(
                        f"**#{placement.id} — "
                        f"{clean_text(getattr(placement, 'position', ''))}**"
                    )

                    st.caption(
                        employee_name
                    )

                    if is_currently_active(
                        placement
                    ):

                        st.caption(
                            "🟢 Currently active"
                        )

                    elif is_future_start(
                        placement
                    ):

                        days = get_days_until_start(
                            placement
                        )

                        st.caption(
                            f"🔵 Starts in {days} day(s)"
                        )

                # ------------------------------------------
                # CLIENT / JOB
                # ------------------------------------------

                with col2:

                    st.write(
                        f"**{client_name}**"
                    )

                    st.caption(
                        job_name
                    )

                # ------------------------------------------
                # DATES / STATUS
                # ------------------------------------------

                with col3:

                    st.write(
                        f"{get_status_icon(status)} "
                        f"**{status}**"
                    )

                    start_date_value = getattr(
                        placement,
                        "start_date",
                        None,
                    )

                    end_date_value = getattr(
                        placement,
                        "end_date",
                        None,
                    )

                    if start_date_value:

                        st.caption(
                            "Start: "
                            f"{start_date_value.strftime('%d %b %Y')}"
                        )

                    if end_date_value:

                        st.caption(
                            "End: "
                            f"{end_date_value.strftime('%d %b %Y')}"
                        )

                    if is_expired_active_placement(
                        placement
                    ):

                        st.warning(
                            "End date passed"
                        )

                # ------------------------------------------
                # FINANCIALS
                # ------------------------------------------

                with col4:

                    st.write(
                        f"Client: **{currency} "
                        f"{client_fee:,.2f}**"
                    )

                    st.caption(
                        f"Worker: {currency} "
                        f"{worker_cost:,.2f}"
                    )

                    if margin < 0:

                        st.error(
                            f"Margin: {currency} "
                            f"{margin:,.2f}"
                        )

                    else:

                        st.caption(
                            f"Margin: {currency} "
                            f"{margin:,.2f}"
                        )

                    st.caption(
                        f"{billing_frequency} | "
                        f"{margin_percentage:.1f}%"
                    )

                # ------------------------------------------
                # ACTIONS
                # ------------------------------------------

                with col5:

                    st.write(
                        f"**{margin_percentage:.1f}%**"
                    )

                    edit_button = st.button(
                        "Edit",
                        key=f"edit_placement_{placement.id}",
                        use_container_width=True,
                    )

                    delete_button = st.button(
                        "Delete",
                        key=f"delete_placement_{placement.id}",
                        use_container_width=True,
                    )

                # ==========================================
                # EDIT
                # ==========================================

                if edit_button:

                    st.session_state.editing_placement_id = (
                        placement.id
                    )

                    st.session_state.confirm_delete_placement_id = (
                        None
                    )

                    st.rerun()

                # ==========================================
                # DELETE REQUEST
                # ==========================================

                if delete_button:

                    st.session_state.confirm_delete_placement_id = (
                        placement.id
                    )

                    st.session_state.editing_placement_id = (
                        None
                    )

                    st.rerun()

                # ==========================================
                # DELETE CONFIRMATION
                # ==========================================

                if (
                    st.session_state.confirm_delete_placement_id
                    == placement.id
                ):

                    placement_contracts = get_contracts(
                        placement
                    )

                    placement_invoices = get_invoices(
                        placement
                    )

                    placement_payments = (
                        get_payments_for_placement(
                            session,
                            placement,
                        )
                    )

                    if placement_contracts:

                        st.error(
                            "This placement cannot be deleted "
                            "because it has contract history."
                        )

                        st.caption(
                            f"Contracts attached: "
                            f"{len(placement_contracts)}"
                        )

                        if st.button(
                            "Close",
                            key=f"close_contract_delete_{placement.id}",
                            use_container_width=True,
                        ):

                            st.session_state.confirm_delete_placement_id = None

                            st.rerun()

                    elif placement_invoices:

                        st.error(
                            "This placement cannot be deleted "
                            "because it has invoice history."
                        )

                        st.caption(
                            f"Invoices attached: "
                            f"{len(placement_invoices)}"
                        )

                        if st.button(
                            "Close",
                            key=f"close_invoice_delete_{placement.id}",
                            use_container_width=True,
                        ):

                            st.session_state.confirm_delete_placement_id = None

                            st.rerun()

                    elif placement_payments:

                        st.error(
                            "This placement cannot be deleted "
                            "because it has payment history."
                        )

                        st.caption(
                            f"Payments attached: "
                            f"{len(placement_payments)}"
                        )

                        if st.button(
                            "Close",
                            key=f"close_payment_delete_{placement.id}",
                            use_container_width=True,
                        ):

                            st.session_state.confirm_delete_placement_id = None

                            st.rerun()

                    else:

                        st.warning(
                            f"Are you sure you want to delete "
                            f"Placement #{placement.id}?"
                        )

                        confirm_col1, confirm_col2 = st.columns(2)

                        with confirm_col1:

                            confirm_delete = st.button(
                                "Yes, Delete",
                                key=f"confirm_delete_{placement.id}",
                                type="primary",
                                use_container_width=True,
                            )

                        with confirm_col2:

                            cancel_delete = st.button(
                                "Cancel",
                                key=f"cancel_delete_{placement.id}",
                                use_container_width=True,
                            )

                        if cancel_delete:

                            st.session_state.confirm_delete_placement_id = None

                            st.rerun()

                        if confirm_delete:

                            try:

                                session.delete(
                                    placement
                                )

                                session.commit()

                                st.session_state.confirm_delete_placement_id = None

                                st.success(
                                    "Placement deleted successfully."
                                )

                                st.rerun()

                            except Exception as error:

                                session.rollback()

                                st.error(
                                    "The placement could not be deleted."
                                )

                                st.caption(
                                    f"Error: {error}"
                                )

                # ==========================================
                # DETAILS
                # ==========================================

                with st.expander(
                    "View Placement Details"
                ):

                    detail_col1, detail_col2 = st.columns(2)

                    with detail_col1:

                        st.write(
                            f"**Placement ID:** #{placement.id}"
                        )

                        st.write(
                            f"**Employee:** {employee_name}"
                        )

                        st.write(
                            f"**Client:** {client_name}"
                        )

                        st.write(
                            f"**Position:** "
                            f"{clean_text(getattr(placement, 'position', ''))}"
                        )

                        st.write(
                            f"**Job:** {job_name}"
                        )

                        st.write(
                            f"**Status:** {status}"
                        )

                        st.write(
                            f"**Billing Frequency:** "
                            f"{billing_frequency}"
                        )

                    with detail_col2:

                        start_date_value = getattr(
                            placement,
                            "start_date",
                            None,
                        )

                        end_date_value = getattr(
                            placement,
                            "end_date",
                            None,
                        )

                        if start_date_value:

                            st.write(
                                "**Start Date:** "
                                f"{start_date_value.strftime('%d %b %Y')}"
                            )

                        if end_date_value:

                            st.write(
                                "**End Date:** "
                                f"{end_date_value.strftime('%d %b %Y')}"
                            )

                        days_active = get_days_active(
                            placement
                        )

                        if days_active is not None:

                            st.write(
                                f"**Duration:** "
                                f"{days_active} day(s)"
                            )

                        st.write(
                            f"**Currency:** {currency}"
                        )

                        st.write(
                            f"**Client Monthly Fee:** "
                            f"{currency} {client_fee:,.2f}"
                        )

                        st.write(
                            f"**Worker Monthly Cost:** "
                            f"{currency} {worker_cost:,.2f}"
                        )

                        st.write(
                            f"**Gross Margin:** "
                            f"{currency} {margin:,.2f}"
                        )

                        st.write(
                            f"**Margin Percentage:** "
                            f"{margin_percentage:.1f}%"
                        )

                        st.write(
                            f"**Margin Status:** "
                            f"{margin_status}"
                        )

                        st.write(
                            f"**Contracts:** "
                            f"{len(get_contracts(placement))}"
                        )

                        st.write(
                            f"**Invoices:** "
                            f"{len(get_invoices(placement))}"
                        )

                        st.write(
                            f"**Payments:** "
                            f"{len(get_payments_for_placement(session, placement))}"
                        )

                    placement_notes = clean_text(
                        getattr(
                            placement,
                            "notes",
                            "",
                        )
                    )

                    if placement_notes:

                        st.write(
                            f"**Notes:** {placement_notes}"
                        )

    except Exception as error:

        session.rollback()

        st.error(
            "An error occurred while loading the Placements screen."
        )

        st.caption(
            f"Error: {error}"
        )

    finally:

        session.close()