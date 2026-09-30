import streamlit as st
from datetime import date

from database import get_session
from models import (
    Placement,
    Client,
    Employee,
    Job,
    Contract,
    Invoice,
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


def get_employee_name(employee):
    """Return employee full name safely."""

    if not employee:
        return "Unknown Employee"

    first_name = clean_text(
        employee.first_name
    )

    last_name = clean_text(
        employee.last_name
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
            client.company_name
        )
        or "Unknown Client"
    )


def get_job_label(job):
    """Return readable job label."""

    if not job:
        return "No Job"

    position = (
        clean_text(job.position)
        or f"Job #{job.id}"
    )

    client_name = get_client_name(
        job.client
    )

    return (
        f"{position} — {client_name}"
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

    return (
        clean_text(
            placement.status
        )
        or "Active"
    )


def get_currency(placement):
    """Return safe placement currency."""

    return (
        clean_text(
            placement.currency
        )
        or "GBP"
    )


def get_client_fee(placement):
    """Return client fee safely."""

    try:
        return max(
            float(
                placement.client_monthly_fee
                or 0
            ),
            0.0,
        )

    except (TypeError, ValueError):
        return 0.0


def get_worker_cost(placement):
    """Return worker cost safely."""

    try:
        return max(
            float(
                placement.worker_monthly_cost
                or 0
            ),
            0.0,
        )

    except (TypeError, ValueError):
        return 0.0


def calculate_margin(placement):
    """Calculate gross margin."""

    return (
        get_client_fee(placement)
        - get_worker_cost(placement)
    )


def calculate_margin_percentage(placement):
    """Calculate gross margin percentage."""

    client_fee = get_client_fee(
        placement
    )

    if client_fee <= 0:
        return 0.0

    return (
        calculate_margin(placement)
        / client_fee
    ) * 100


def get_days_active(placement):
    """Return number of days since placement started."""

    if not placement.start_date:
        return None

    end_date = (
        placement.end_date
        or date.today()
    )

    return max(
        0,
        (
            end_date
            - placement.start_date
        ).days,
    )


# ============================================================
# RELATIONSHIP HELPERS
# ============================================================

def get_contracts(placement):
    """Return linked contracts safely."""

    contracts = getattr(
        placement,
        "contracts",
        None,
    )

    if contracts is None:
        return []

    try:
        return list(contracts)

    except TypeError:
        return []


def get_invoices(placement):
    """Return linked invoices safely."""

    invoices = getattr(
        placement,
        "invoices",
        None,
    )

    if invoices is None:
        return []

    try:
        return list(invoices)

    except TypeError:
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

    invoice_ids = [
        invoice.id
        for invoice in invoices
        if invoice and invoice.id
    ]

    if not invoice_ids:
        return []

    try:
        return (
            session.query(Payment)
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
    return len(
        get_contracts(placement)
    ) > 0


def has_invoices(placement):
    return len(
        get_invoices(placement)
    ) > 0


def has_payments(
    session,
    placement,
):
    return len(
        get_payments_for_placement(
            session,
            placement,
        )
    ) > 0


# ============================================================
# HISTORY / PROTECTION HELPERS
# ============================================================

def has_financial_history(
    session,
    placement,
):
    """
    Return True if a placement has contracts,
    invoices or payments.
    """

    return (
        has_contracts(placement)
        or has_invoices(placement)
        or has_payments(
            session,
            placement,
        )
    )


def get_history_summary(
    session,
    placement,
):
    """Return counts of linked historical records."""

    contracts = get_contracts(
        placement
    )

    invoices = get_invoices(
        placement
    )

    payments = get_payments_for_placement(
        session,
        placement,
    )

    return {
        "contracts": len(contracts),
        "invoices": len(invoices),
        "payments": len(payments),
    }


# ============================================================
# DATE / STATUS HELPERS
# ============================================================

def validate_dates(
    start_date,
    end_date,
):
    """Validate placement dates."""

    errors = []

    if not start_date:
        errors.append(
            "Start Date is required."
        )

    if (
        end_date
        and start_date
        and end_date < start_date
    ):
        errors.append(
            "End Date cannot be before Start Date."
        )

    return errors


def validate_status(
    status,
    start_date,
    end_date,
):
    """Validate logical placement status."""

    errors = []

    today = date.today()

    if (
        status == "Active"
        and start_date
        and start_date > today
    ):
        errors.append(
            "An Active placement cannot have "
            "a future Start Date."
        )

    if (
        status == "Scheduled"
        and start_date
        and start_date <= today
    ):
        errors.append(
            "A Scheduled placement should have "
            "a future Start Date. If work has already "
            "started, use Active."
        )

    if (
        status in [
            "Completed",
            "Terminated",
        ]
        and not end_date
    ):
        errors.append(
            f"A {status} placement should have "
            "an End Date."
        )

    return errors


def get_status_description(status):
    """Return a short explanation of each status."""

    descriptions = {
        "Active": "Employee is currently working on the placement.",
        "Scheduled": "Placement agreed but work has not started.",
        "Completed": "Placement finished normally.",
        "Terminated": "Placement ended before normal completion.",
    }

    return descriptions.get(
        status,
        "",
    )


# ============================================================
# OVERLAP PROTECTION
# ============================================================

def dates_overlap(
    start_a,
    end_a,
    start_b,
    end_b,
):
    """
    Determine whether two placement periods overlap.

    Open-ended placements are treated as continuing
    indefinitely.
    """

    if not start_a or not start_b:
        return False

    effective_end_a = (
        end_a
        or date.max
    )

    effective_end_b = (
        end_b
        or date.max
    )

    return (
        start_a <= effective_end_b
        and start_b <= effective_end_a
    )


def find_employee_overlapping_placements(
    session,
    employee_id,
    start_date,
    end_date,
    exclude_id=None,
):
    """
    Find active/scheduled placements for the same employee
    whose dates overlap the proposed placement.
    """

    query = (
        session.query(Placement)
        .filter(
            Placement.employee_id
            == employee_id,

            Placement.status.in_(
                [
                    "Active",
                    "Scheduled",
                ]
            ),
        )
    )

    if exclude_id is not None:

        query = query.filter(
            Placement.id
            != exclude_id
        )

    existing = query.all()

    overlaps = []

    for placement in existing:

        if dates_overlap(
            start_date,
            end_date,
            placement.start_date,
            placement.end_date,
        ):
            overlaps.append(
                placement
            )

    return overlaps


# ============================================================
# CLIENT / JOB CONSISTENCY
# ============================================================

def get_jobs_for_client(
    jobs,
    client_id,
):
    """Return jobs belonging to a selected client."""

    return [
        job
        for job in jobs
        if job.client_id
        == client_id
    ]


# ============================================================
# FINANCIAL SUMMARY
# ============================================================

def get_currency_totals(
    placements,
    value_function,
    statuses=None,
):
    """
    Calculate totals separately by currency.

    Currencies are never combined.
    """

    totals = {}

    if statuses is None:
        statuses = PLACEMENT_STATUSES

    for placement in placements:

        if (
            get_status(placement)
            not in statuses
        ):
            continue

        currency = get_currency(
            placement
        )

        value = value_function(
            placement
        )

        totals[currency] = (
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

    return " | ".join(parts)


# ============================================================
# SEARCH
# ============================================================

def get_placement_search_text(
    placement,
):
    """Return searchable placement text."""

    parts = [
        str(
            placement.id
        ),
        clean_text(
            placement.position
        ),
        clean_text(
            placement.status
        ),
        clean_text(
            placement.currency
        ),
        clean_text(
            placement.billing_frequency
        ),
    ]

    if placement.client:
        parts.append(
            get_client_name(
                placement.client
            )
        )

    if placement.employee:
        parts.append(
            get_employee_name(
                placement.employee
            )
        )

    if placement.job:
        parts.append(
            get_job_label(
                placement.job
            )
        )

    return " ".join(
        parts
    ).lower()


# ============================================================
# MAIN SCREEN
# ============================================================

def show_placements():

    st.title("Placements")

    st.caption(
        "Manage active, scheduled and historical employee placements."
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
                Job.position.asc()
            )
            .all()
        )

        placements = (
            session.query(Placement)
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
        # EDITING STATE
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
        # ADD / EDIT HEADER
        # ====================================================

        if editing_placement:

            st.subheader(
                "Edit Placement"
            )

            history = get_history_summary(
                session,
                editing_placement,
            )

            if any(
                history.values()
            ):

                st.info(
                    "This placement has historical records. "
                    "Core relationship and financial changes are "
                    "subject to additional protection."
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
        # CURRENT CLIENT
        # ====================================================

        if editing_placement:

            current_client_id = (
                editing_placement.client_id
            )

            client_index = (
                client_ids.index(
                    current_client_id
                )
                if current_client_id
                in client_ids
                else 0
            )

        else:

            client_index = 0

        # ====================================================
        # CURRENT EMPLOYEE
        # ====================================================

        if editing_placement:

            current_employee_id = (
                editing_placement.employee_id
            )

            employee_index = (
                employee_ids.index(
                    current_employee_id
                )
                if current_employee_id
                in employee_ids
                else 0
            )

        else:

            employee_index = 0

        # ====================================================
        # CURRENT JOB
        # ====================================================

        if editing_placement:

            current_job_id = (
                editing_placement.job_id
            )

        else:

            current_job_id = None

        # ====================================================
        # CURRENT VALUES
        # ====================================================

        current_status = (
            get_status(
                editing_placement
            )
            if editing_placement
            else "Scheduled"
        )

        current_frequency = (
            clean_text(
                editing_placement.billing_frequency
            )
            if editing_placement
            else "Monthly"
        )

        current_currency = (
            get_currency(
                editing_placement
            )
            if editing_placement
            else "GBP"
        )

        current_position = (
            clean_text(
                editing_placement.position
            )
            if editing_placement
            else ""
        )

        current_notes = (
            clean_text(
                editing_placement.notes
            )
            if editing_placement
            else ""
        )

        # ====================================================
        # FORM
        # ====================================================

        form_key = (
            "edit_placement_form"
            if editing_placement
            else "add_placement_form"
        )

        with st.form(form_key):

            # =================================================
            # CLIENT / EMPLOYEE
            # =================================================

            col1, col2 = st.columns(2)

            with col1:

                selected_client = st.selectbox(
                    "Client *",
                    client_labels,
                    index=client_index,
                    key=(
                        "edit_client"
                        if editing_placement
                        else "add_client"
                    ),
                )

            with col2:

                selected_employee = st.selectbox(
                    "Employee *",
                    employee_labels,
                    index=employee_index,
                    key=(
                        "edit_employee"
                        if editing_placement
                        else "add_employee"
                    ),
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

            # =================================================
            # JOBS FOR CLIENT
            # =================================================

            client_jobs = get_jobs_for_client(
                jobs,
                selected_client_id,
            )

            job_options = {
                "No Job": None
            }

            for job in client_jobs:

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

            current_job_label = "No Job"

            for label, job_id in job_options.items():

                if (
                    job_id
                    == current_job_id
                ):

                    current_job_label = label

                    break

            if (
                current_job_label
                not in job_labels
            ):
                current_job_label = "No Job"

            job_index = job_labels.index(
                current_job_label
            )

            selected_job = st.selectbox(
                "Job",
                job_labels,
                index=job_index,
                key=(
                    "edit_job"
                    if editing_placement
                    else "add_job"
                ),
            )

            selected_job_id = (
                job_options[
                    selected_job
                ]
            )

            # =================================================
            # POSITION
            # =================================================

            position = st.text_input(
                "Position *",
                value=current_position,
                placeholder=(
                    "Example: Finance Operations Specialist"
                ),
                key=(
                    "edit_position"
                    if editing_placement
                    else "add_position"
                ),
            )

            # =================================================
            # DATES
            # =================================================

            col1, col2 = st.columns(2)

            with col1:

                start_date = st.date_input(
                    "Start Date",
                    value=(
                        editing_placement.start_date
                        if (
                            editing_placement
                            and editing_placement.start_date
                        )
                        else date.today()
                    ),
                    key=(
                        "edit_start_date"
                        if editing_placement
                        else "add_start_date"
                    ),
                )

            with col2:

                end_date = st.date_input(
                    "End Date",
                    value=(
                        editing_placement.end_date
                        if (
                            editing_placement
                            and editing_placement.end_date
                        )
                        else None
                    ),
                    key=(
                        "edit_end_date"
                        if editing_placement
                        else "add_end_date"
                    ),
                )

            # =================================================
            # STATUS / BILLING
            # =================================================

            col1, col2 = st.columns(2)

            with col1:

                status_index = (
                    PLACEMENT_STATUSES.index(
                        current_status
                    )
                    if current_status
                    in PLACEMENT_STATUSES
                    else 0
                )

                status = st.selectbox(
                    "Status",
                    PLACEMENT_STATUSES,
                    index=status_index,
                    key=(
                        "edit_status"
                        if editing_placement
                        else "add_status"
                    ),
                )

                st.caption(
                    get_status_description(
                        status
                    )
                )

            with col2:

                frequency_index = (
                    BILLING_FREQUENCIES.index(
                        current_frequency
                    )
                    if current_frequency
                    in BILLING_FREQUENCIES
                    else 0
                )

                billing_frequency = st.selectbox(
                    "Billing Frequency",
                    BILLING_FREQUENCIES,
                    index=frequency_index,
                    key=(
                        "edit_frequency"
                        if editing_placement
                        else "add_frequency"
                    ),
                )

            # =================================================
            # FINANCIALS
            # =================================================

            st.subheader(
                "Financials"
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
                    key=(
                        "edit_client_fee"
                        if editing_placement
                        else "add_client_fee"
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
                    key=(
                        "edit_worker_cost"
                        if editing_placement
                        else "add_worker_cost"
                    ),
                )

            with col3:

                currency_index = (
                    CURRENCIES.index(
                        current_currency
                    )
                    if current_currency
                    in CURRENCIES
                    else 0
                )

                currency = st.selectbox(
                    "Currency",
                    CURRENCIES,
                    index=currency_index,
                    key=(
                        "edit_currency"
                        if editing_placement
                        else "add_currency"
                    ),
                )

            # =================================================
            # NOTES
            # =================================================

            notes = st.text_area(
                "Notes",
                value=current_notes,
                placeholder=(
                    "Additional placement information..."
                ),
                key=(
                    "edit_notes"
                    if editing_placement
                    else "add_notes"
                ),
            )

            # =================================================
            # SAVE
            # =================================================

            submitted = st.form_submit_button(
                "Save Changes"
                if editing_placement
                else "Create Placement",
                type="primary",
                use_container_width=True,
            )

            if submitted:

                errors = []

                position_clean = clean_text(
                    position
                )

                notes_clean = clean_text(
                    notes
                )

                # =============================================
                # BASIC VALIDATION
                # =============================================

                if not position_clean:

                    errors.append(
                        "Position is required."
                    )

                errors.extend(
                    validate_dates(
                        start_date,
                        end_date,
                    )
                )

                errors.extend(
                    validate_status(
                        status,
                        start_date,
                        end_date,
                    )
                )

                # =============================================
                # FINANCIAL VALIDATION
                # =============================================

                if client_monthly_fee < 0:

                    errors.append(
                        "Client Monthly Fee cannot be negative."
                    )

                if worker_monthly_cost < 0:

                    errors.append(
                        "Worker Monthly Cost cannot be negative."
                    )

                # =============================================
                # CLIENT / JOB VALIDATION
                # =============================================

                selected_job_object = None

                if selected_job_id:

                    selected_job_object = session.get(
                        Job,
                        selected_job_id,
                    )

                    if not selected_job_object:

                        errors.append(
                            "The selected job could not be found."
                        )

                    elif (
                        selected_job_object.client_id
                        != selected_client_id
                    ):

                        errors.append(
                            "The selected job belongs to a "
                            "different client."
                        )

                # =============================================
                # EMPLOYEE OVERLAP CHECK
                # =============================================

                if not errors:

                    exclude_id = (
                        editing_placement.id
                        if editing_placement
                        else None
                    )

                    overlapping = (
                        find_employee_overlapping_placements(
                            session,
                            selected_employee_id,
                            start_date,
                            end_date,
                            exclude_id=exclude_id,
                        )
                    )

                    if overlapping:

                        for overlap in overlapping:

                            overlap_employee = (
                                get_employee_name(
                                    overlap.employee
                                )
                            )

                            overlap_position = (
                                clean_text(
                                    overlap.position
                                )
                            )

                            overlap_start = (
                                overlap.start_date.strftime(
                                    "%d %b %Y"
                                )
                                if overlap.start_date
                                else "Unknown"
                            )

                            overlap_end = (
                                overlap.end_date.strftime(
                                    "%d %b %Y"
                                )
                                if overlap.end_date
                                else "Open-ended"
                            )

                            errors.append(
                                "The employee already has an "
                                f"overlapping {get_status(overlap).lower()} "
                                f"placement: #{overlap.id} "
                                f"{overlap_position} "
                                f"({overlap_start} – {overlap_end})."
                            )

                # =============================================
                # HISTORY PROTECTION
                # =============================================

                if (
                    editing_placement
                    and not errors
                ):

                    history = (
                        get_history_summary(
                            session,
                            editing_placement,
                        )
                    )

                    has_history = any(
                        history.values()
                    )

                    if has_history:

                        # -------------------------------------
                        # Client cannot change after history.
                        # -------------------------------------

                        if (
                            selected_client_id
                            != editing_placement.client_id
                        ):

                            errors.append(
                                "Client cannot be changed because "
                                "this placement has historical records."
                            )

                        # -------------------------------------
                        # Employee cannot change after history.
                        # -------------------------------------

                        if (
                            selected_employee_id
                            != editing_placement.employee_id
                        ):

                            errors.append(
                                "Employee cannot be changed because "
                                "this placement has historical records."
                            )

                        # -------------------------------------
                        # Job cannot change after history.
                        # -------------------------------------

                        if (
                            selected_job_id
                            != editing_placement.job_id
                        ):

                            errors.append(
                                "Job cannot be changed because "
                                "this placement has historical records."
                            )

                        # -------------------------------------
                        # Currency protection.
                        # -------------------------------------

                        if (
                            currency
                            != get_currency(
                                editing_placement
                            )
                        ):

                            errors.append(
                                "Currency cannot be changed because "
                                "this placement has historical records."
                            )

                # =============================================
                # DISPLAY ERRORS
                # =============================================

                if errors:

                    for error in errors:

                        st.error(
                            error
                        )

                else:

                    try:

                        # =====================================
                        # UPDATE
                        # =====================================

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

                            st.session_state.editing_placement_id = (
                                None
                            )

                            st.success(
                                "Placement updated successfully."
                            )

                            st.rerun()

                        # =====================================
                        # CREATE
                        # =====================================

                        else:

                            placement = Placement(
                                client_id=(
                                    selected_client_id
                                ),
                                employee_id=(
                                    selected_employee_id
                                ),
                                job_id=(
                                    selected_job_id
                                ),
                                position=(
                                    position_clean
                                ),
                                start_date=(
                                    start_date
                                ),
                                end_date=(
                                    end_date
                                ),
                                client_monthly_fee=(
                                    client_monthly_fee
                                ),
                                worker_monthly_cost=(
                                    worker_monthly_cost
                                ),
                                currency=(
                                    currency
                                ),
                                billing_frequency=(
                                    billing_frequency
                                ),
                                status=status,
                                notes=(
                                    notes_clean
                                ),
                            )

                            session.add(
                                placement
                            )

                            session.commit()

                            st.success(
                                "Placement created successfully."
                            )

                            st.rerun()

                    except Exception as exc:

                        session.rollback()

                        st.error(
                            "The placement could not be saved."
                        )

                        st.exception(
                            exc
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
        # REGISTER
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
        # KPIs
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

        active_client_fee_totals = (
            get_currency_totals(
                placements,
                get_client_fee,
                statuses=[
                    "Active"
                ],
            )
        )

        active_worker_cost_totals = (
            get_currency_totals(
                placements,
                get_worker_cost,
                statuses=[
                    "Active"
                ],
            )
        )

        active_margin_totals = (
            get_currency_totals(
                placements,
                calculate_margin,
                statuses=[
                    "Active"
                ],
            )
        )

        k1, k2, k3, k4, k5 = st.columns(
            5
        )

        k1.metric(
            "Total",
            total_placements,
        )

        k2.metric(
            "Active",
            active_placements,
        )

        k3.metric(
            "Scheduled",
            scheduled_placements,
        )

        k4.metric(
            "Completed",
            completed_placements,
        )

        k5.metric(
            "Terminated",
            terminated_placements,
        )

        # ====================================================
        # FINANCIAL SUMMARY
        # ====================================================

        st.caption(
            "Active placement financials are shown separately "
            "by currency. Currencies are never combined."
        )

        f1, f2, f3 = st.columns(3)

        with f1:

            st.write(
                "**Active Client Fees**"
            )

            st.write(
                format_currency_totals(
                    active_client_fee_totals
                )
            )

        with f2:

            st.write(
                "**Active Worker Costs**"
            )

            st.write(
                format_currency_totals(
                    active_worker_cost_totals
                )
            )

        with f3:

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

        filter_col1, filter_col2, filter_col3 = st.columns(
            3
        )

        with filter_col1:

            status_filter = st.selectbox(
                "Status",
                [
                    "All",
                    *PLACEMENT_STATUSES,
                ],
                key="placement_status_filter",
            )

        with filter_col2:

            client_filter_options = {
                "All Clients": None
            }

            for client in clients:

                client_filter_options[
                    f"{get_client_name(client)} "
                    f"(ID: {client.id})"
                ] = client.id

            selected_client_filter = st.selectbox(
                "Client",
                list(
                    client_filter_options.keys()
                ),
                key="placement_client_filter",
            )

        with filter_col3:

            currency_filter = st.selectbox(
                "Currency",
                [
                    "All",
                    *CURRENCIES,
                ],
                key="placement_currency_filter",
            )

        filter_col4, filter_col5 = st.columns(
            2
        )

        with filter_col4:

            employee_filter_options = {
                "All Employees": None
            }

            for employee in employees:

                employee_filter_options[
                    f"{get_employee_name(employee)} "
                    f"(ID: {employee.id})"
                ] = employee.id

            selected_employee_filter = st.selectbox(
                "Employee",
                list(
                    employee_filter_options.keys()
                ),
                key="placement_employee_filter",
            )

        with filter_col5:

            search = st.text_input(
                "Search",
                placeholder=(
                    "Employee, client, job, position..."
                ),
                key="placement_search",
            )

        # ====================================================
        # APPLY FILTERS
        # ====================================================

        filtered_placements = []

        selected_client_filter_id = (
            client_filter_options[
                selected_client_filter
            ]
        )

        selected_employee_filter_id = (
            employee_filter_options[
                selected_employee_filter
            ]
        )

        for placement in placements:

            if (
                status_filter != "All"
                and get_status(
                    placement
                )
                != status_filter
            ):
                continue

            if (
                selected_client_filter_id
                is not None
                and placement.client_id
                != selected_client_filter_id
            ):
                continue

            if (
                selected_employee_filter_id
                is not None
                and placement.employee_id
                != selected_employee_filter_id
            ):
                continue

            if (
                currency_filter != "All"
                and get_currency(
                    placement
                )
                != currency_filter
            ):
                continue

            if clean_text(search):

                search_lower = (
                    clean_text(
                        search
                    ).lower()
                )

                if (
                    search_lower
                    not in get_placement_search_text(
                        placement
                    )
                ):
                    continue

            filtered_placements.append(
                placement
            )

        # ====================================================
        # RESULT COUNT
        # ====================================================

        st.caption(
            f"Showing "
            f"{len(filtered_placements)} "
            f"of "
            f"{len(placements)} "
            f"placement(s)"
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

            employee_name = get_employee_name(
                placement.employee
            )

            client_name = get_client_name(
                placement.client
            )

            job_name = get_job_label(
                placement.job
            )

            status = get_status(
                placement
            )

            currency = get_currency(
                placement
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

            history = get_history_summary(
                session,
                placement,
            )

            with st.container(
                border=True
            ):

                # ==========================================
                # MAIN CARD
                # ==========================================

                col1, col2, col3, col4, col5 = (
                    st.columns(
                        [
                            2.2,
                            2.3,
                            2,
                            2,
                            1.8,
                        ]
                    )
                )

                with col1:

                    st.write(
                        f"**#{placement.id} — "
                        f"{clean_text(placement.position)}**"
                    )

                    st.caption(
                        employee_name
                    )

                with col2:

                    st.write(
                        f"**{client_name}**"
                    )

                    st.caption(
                        job_name
                        if placement.job
                        else "No linked job"
                    )

                with col3:

                    st.write(
                        f"{get_status_icon(status)} "
                        f"**{status}**"
                    )

                    if placement.start_date:

                        st.caption(
                            "Start: "
                            f"{placement.start_date.strftime('%d %b %Y')}"
                        )

                    if placement.end_date:

                        st.caption(
                            "End: "
                            f"{placement.end_date.strftime('%d %b %Y')}"
                        )

                with col4:

                    st.write(
                        f"Client: **"
                        f"{currency} "
                        f"{client_fee:,.2f}**"
                    )

                    st.caption(
                        f"Worker: "
                        f"{currency} "
                        f"{worker_cost:,.2f}"
                    )

                    st.caption(
                        f"Margin: "
                        f"{currency} "
                        f"{margin:,.2f}"
                    )

                with col5:

                    st.write(
                        f"**{margin_percentage:.1f}% margin**"
                    )

                    if (
                        history["contracts"]
                        or history["invoices"]
                        or history["payments"]
                    ):

                        st.caption(
                            "📁 History protected"
                        )

                    edit_button = st.button(
                        "Edit",
                        key=(
                            f"edit_placement_"
                            f"{placement.id}"
                        ),
                        use_container_width=True,
                    )

                    delete_button = st.button(
                        "Delete",
                        key=(
                            f"delete_placement_"
                            f"{placement.id}"
                        ),
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
                # DELETE PROTECTION
                # ==========================================

                if (
                    st.session_state.confirm_delete_placement_id
                    == placement.id
                ):

                    if (
                        history["contracts"]
                        or history["invoices"]
                        or history["payments"]
                    ):

                        st.error(
                            "This placement cannot be deleted "
                            "because it contains business history."
                        )

                        if history["contracts"]:

                            st.caption(
                                f"Contracts: "
                                f"{history['contracts']}"
                            )

                        if history["invoices"]:

                            st.caption(
                                f"Invoices: "
                                f"{history['invoices']}"
                            )

                        if history["payments"]:

                            st.caption(
                                f"Payments: "
                                f"{history['payments']}"
                            )

                        st.info(
                            "Use Edit to change the status to "
                            "Completed or Terminated instead of deleting "
                            "a historical placement."
                        )

                        if st.button(
                            "Close",
                            key=(
                                f"close_delete_"
                                f"{placement.id}"
                            ),
                            use_container_width=True,
                        ):

                            st.session_state.confirm_delete_placement_id = (
                                None
                            )

                            st.rerun()

                    else:

                        st.warning(
                            f"Are you sure you want to permanently "
                            f"delete placement #{placement.id}?"
                        )

                        confirm_col1, confirm_col2 = (
                            st.columns(2)
                        )

                        with confirm_col1:

                            confirm_delete = st.button(
                                "Yes, Delete Placement",
                                key=(
                                    f"confirm_delete_"
                                    f"{placement.id}"
                                ),
                                type="primary",
                                use_container_width=True,
                            )

                        with confirm_col2:

                            cancel_delete = st.button(
                                "Cancel",
                                key=(
                                    f"cancel_delete_"
                                    f"{placement.id}"
                                ),
                                use_container_width=True,
                            )

                        if cancel_delete:

                            st.session_state.confirm_delete_placement_id = (
                                None
                            )

                            st.rerun()

                        if confirm_delete:

                            try:

                                session.delete(
                                    placement
                                )

                                session.commit()

                                st.session_state.confirm_delete_placement_id = (
                                    None
                                )

                                st.success(
                                    "Placement deleted successfully."
                                )

                                st.rerun()

                            except Exception as exc:

                                session.rollback()

                                st.error(
                                    "The placement could not be deleted."
                                )

                                st.exception(
                                    exc
                                )

                # ==========================================
                # DETAILS
                # ==========================================

                with st.expander(
                    "View Placement Details"
                ):

                    detail_col1, detail_col2 = (
                        st.columns(2)
                    )

                    with detail_col1:

                        st.write(
                            "**Placement ID:** "
                            f"#{placement.id}"
                        )

                        st.write(
                            "**Employee:** "
                            f"{employee_name}"
                        )

                        st.write(
                            "**Client:** "
                            f"{client_name}"
                        )

                        st.write(
                            "**Position:** "
                            f"{clean_text(placement.position)}"
                        )

                        st.write(
                            "**Job:** "
                            f"{job_name}"
                        )

                        st.write(
                            "**Status:** "
                            f"{status}"
                        )

                        st.write(
                            "**Billing Frequency:** "
                            f"{clean_text(placement.billing_frequency) or 'Not specified'}"
                        )

                    with detail_col2:

                        if placement.start_date:

                            st.write(
                                "**Start Date:** "
                                f"{placement.start_date.strftime('%d %b %Y')}"
                            )

                        if placement.end_date:

                            st.write(
                                "**End Date:** "
                                f"{placement.end_date.strftime('%d %b %Y')}"
                            )

                        days_active = get_days_active(
                            placement
                        )

                        if days_active is not None:

                            st.write(
                                "**Duration:** "
                                f"{days_active} day(s)"
                            )

                        st.write(
                            "**Currency:** "
                            f"{currency}"
                        )

                        st.write(
                            "**Client Fee:** "
                            f"{currency} "
                            f"{client_fee:,.2f}"
                        )

                        st.write(
                            "**Worker Cost:** "
                            f"{currency} "
                            f"{worker_cost:,.2f}"
                        )

                        st.write(
                            "**Gross Margin:** "
                            f"{currency} "
                            f"{margin:,.2f} "
                            f"({margin_percentage:.1f}%)"
                        )

                    # --------------------------------------
                    # HISTORY
                    # --------------------------------------

                    st.markdown(
                        "#### Linked History"
                    )

                    h1, h2, h3 = st.columns(3)

                    h1.metric(
                        "Contracts",
                        history["contracts"],
                    )

                    h2.metric(
                        "Invoices",
                        history["invoices"],
                    )

                    h3.metric(
                        "Payments",
                        history["payments"],
                    )

                    if (
                        history["contracts"]
                        or history["invoices"]
                        or history["payments"]
                    ):

                        st.caption(
                            "This placement contains historical "
                            "business records and is protected from deletion."
                        )

                    if placement.notes:

                        st.markdown(
                            "#### Notes"
                        )

                        st.write(
                            clean_text(
                                placement.notes
                            )
                        )

    except Exception as exc:

        session.rollback()

        st.error(
            "An error occurred while loading placements."
        )

        st.exception(
            exc
        )

    finally:

        session.close()