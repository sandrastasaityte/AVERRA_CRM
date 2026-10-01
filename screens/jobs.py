import streamlit as st
from datetime import date

from database import get_session
from models import Job, Client


# ============================================================
# CONSTANTS
# ============================================================

CURRENCIES = [
    "GBP",
    "EUR",
    "USD",
    "INR",
]

JOB_STATUSES = [
    "Open",
    "On Hold",
    "Filled",
    "Closed",
    "Cancelled",
]

JOB_PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Urgent",
]

WORK_PATTERNS = [
    "Full-time",
    "Part-time",
    "Contract",
    "Temporary",
]

ACTIVE_PLACEMENT_STATUSES = {
    "Active",
    "Scheduled",
}


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
        return float(value or 0)

    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    """Safely convert a value to integer."""

    try:
        return int(value or 0)

    except (TypeError, ValueError):
        return default


def get_client_name(job):
    """Return the client's company name."""

    client = getattr(
        job,
        "client",
        None,
    )

    if client:

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

    return "Unknown Client"


def get_client_label(client):
    """Return a unique client label."""

    company_name = (
        clean_text(
            getattr(
                client,
                "company_name",
                "",
            )
        )
        or "Unnamed Client"
    )

    return (
        f"{company_name} "
        f"(ID: {client.id})"
    )


# ============================================================
# RECRUITMENT COUNTS
# ============================================================

def get_candidate_count(job):
    """Return the number of candidates linked to a job."""

    candidates = getattr(
        job,
        "candidates",
        None,
    )

    if candidates is None:
        return 0

    try:
        return len(candidates)

    except TypeError:
        return 0


def get_placement_count(job):
    """Return the number of placements linked to a job."""

    placements = getattr(
        job,
        "placements",
        None,
    )

    if placements is None:
        return 0

    try:
        return len(placements)

    except TypeError:
        return 0


def get_active_placement_count(job):
    """
    Return the number of current filled positions.

    Active and Scheduled placements count as current
    filled positions.
    """

    placements = getattr(
        job,
        "placements",
        None,
    )

    if not placements:
        return 0

    count = 0

    for placement in placements:

        status = clean_text(
            getattr(
                placement,
                "status",
                "",
            )
        )

        if status in ACTIVE_PLACEMENT_STATUSES:

            count += 1

    return count


def get_total_openings(job):
    """Return the total number of openings."""

    return max(
        safe_int(
            getattr(
                job,
                "openings",
                0,
            )
        ),
        0,
    )


def get_remaining_openings(job):
    """Return the number of unfilled openings."""

    total_openings = get_total_openings(
        job
    )

    active_placements = (
        get_active_placement_count(
            job
        )
    )

    return max(
        total_openings - active_placements,
        0,
    )


def get_job_fill_percentage(job):
    """Return percentage of openings currently filled."""

    total_openings = get_total_openings(
        job
    )

    if total_openings <= 0:
        return 0.0

    filled = min(
        get_active_placement_count(job),
        total_openings,
    )

    return (
        filled / total_openings
    ) * 100


def job_has_candidates(job):
    """Return whether the job has candidates."""

    return (
        get_candidate_count(job) > 0
    )


def job_has_placements(job):
    """Return whether the job has placements."""

    return (
        get_placement_count(job) > 0
    )


def job_has_history(job):
    """Return whether the job has recruitment history."""

    return (
        job_has_candidates(job)
        or job_has_placements(job)
    )


# ============================================================
# STATUS / PRIORITY
# ============================================================

def get_job_status(job):
    """Return a safe stored job status."""

    return (
        clean_text(
            getattr(
                job,
                "status",
                "",
            )
        )
        or "Open"
    )


def get_status_display(job):
    """
    Return the operational job status.

    If a job is stored as Open but all openings are
    already filled, display Filled.
    """

    status = get_job_status(
        job
    )

    total_openings = get_total_openings(
        job
    )

    active_placements = (
        get_active_placement_count(
            job
        )
    )

    if (
        status == "Open"
        and total_openings > 0
        and active_placements >= total_openings
    ):

        return "Filled"

    return status


def get_priority(job):
    """Return a safe priority."""

    return (
        clean_text(
            getattr(
                job,
                "priority",
                "",
            )
        )
        or "Medium"
    )


def get_priority_icon(priority):
    """Return a visual priority indicator."""

    icons = {
        "Low": "🟢",
        "Medium": "🟡",
        "High": "🟠",
        "Urgent": "🔴",
    }

    return icons.get(
        priority,
        "⚪",
    )


# ============================================================
# DATES
# ============================================================

def get_days_to_closing(job):
    """Return number of days until the closing date."""

    closing_date = getattr(
        job,
        "closing_date",
        None,
    )

    if not closing_date:
        return None

    return (
        closing_date
        - date.today()
    ).days


def get_closing_state(job):
    """
    Return closing-date state.

    Values:
    - no_date
    - overdue
    - today
    - tomorrow
    - upcoming
    """

    days = get_days_to_closing(
        job
    )

    if days is None:
        return "no_date"

    if days < 0:
        return "overdue"

    if days == 0:
        return "today"

    if days == 1:
        return "tomorrow"

    return "upcoming"


def get_closing_label(job):
    """Return readable closing-date information."""

    days = get_days_to_closing(
        job
    )

    if days is None:
        return "No closing date"

    if days < 0:

        return (
            f"Closed {abs(days)} day(s) ago"
        )

    if days == 0:
        return "Closes today"

    if days == 1:
        return "Closes tomorrow"

    return (
        f"{days} days remaining"
    )


# ============================================================
# SEARCH
# ============================================================

def get_search_text(job):
    """Return combined searchable text for a job."""

    values = [
        getattr(job, "position", ""),
        getattr(job, "department", ""),
        getattr(job, "skills_required", ""),
        getattr(job, "experience_required", ""),
        getattr(job, "remote_country", ""),
        getattr(job, "work_pattern", ""),
        getattr(job, "status", ""),
        getattr(job, "priority", ""),
        get_client_name(job),
        getattr(job, "notes", ""),
    ]

    return " ".join(
        clean_text(value).lower()
        for value in values
        if clean_text(value)
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_job_status(
    status,
    openings,
    active_placements,
):
    """
    Validate the logical relationship between job status,
    openings and active placements.
    """

    if active_placements > openings:

        return (
            "The job has more active/scheduled placements "
            "than the total number of openings."
        )

    if (
        status == "Filled"
        and active_placements < openings
    ):

        return (
            "A job can only be marked Filled when all "
            "openings have an active or scheduled placement."
        )

    if (
        status == "Open"
        and openings > 0
        and active_placements >= openings
    ):

        return (
            "All openings are already filled. "
            "Please use Filled status."
        )

    if (
        status == "Cancelled"
        and active_placements > 0
    ):

        return (
            "A job with active or scheduled placements "
            "cannot be marked Cancelled."
        )

    return None


def validate_job_dates(
    date_opened,
    closing_date,
):
    """Validate job opening and closing dates."""

    if date_opened > date.today():

        return (
            "Date opened cannot be in the future."
        )

    if (
        closing_date
        and closing_date < date_opened
    ):

        return (
            "Closing date cannot be before "
            "the opening date."
        )

    return None


def validate_job_budget(
    client_budget,
):
    """Validate the client budget."""

    if client_budget < 0:

        return (
            "Client budget cannot be negative."
        )

    return None


def validate_job_openings(
    openings,
):
    """Validate the number of openings."""

    if openings < 1:

        return (
            "Number of openings must be at least 1."
        )

    return None


# ============================================================
# STATE
# ============================================================

def clear_job_state():
    """Clear editing and deletion state."""

    st.session_state.editing_job_id = None
    st.session_state.confirm_delete_job_id = None


# ============================================================
# MAIN SCREEN
# ============================================================

def show_jobs():

    st.title("Jobs")

    st.caption(
        "Create and manage client job requirements, "
        "vacancies and recruitment activity."
    )

    session = get_session()

    # ========================================================
    # SESSION STATE
    # ========================================================

    if "editing_job_id" not in st.session_state:

        st.session_state.editing_job_id = None

    if "confirm_delete_job_id" not in st.session_state:

        st.session_state.confirm_delete_job_id = None

    try:

        # ====================================================
        # LOAD CLIENTS
        # ====================================================

        clients = (
            session.query(Client)
            .order_by(
                Client.company_name
            )
            .all()
        )

        if not clients:

            st.warning(
                "Please add a client before creating a job."
            )

            return

        # ====================================================
        # LOAD JOBS
        # ====================================================

        jobs = (
            session.query(Job)
            .order_by(
                Job.date_opened.desc(),
                Job.id.desc(),
            )
            .all()
        )

        # ====================================================
        # LOAD EDITING JOB
        # ====================================================

        editing_job = None

        if (
            st.session_state.editing_job_id
            is not None
        ):

            editing_job = session.get(
                Job,
                st.session_state.editing_job_id,
            )

            if editing_job is None:

                st.session_state.editing_job_id = None

        # ====================================================
        # FORM TITLE
        # ====================================================

        if editing_job:

            st.subheader(
                "Edit Job — "
                f"{clean_text(editing_job.position)}"
            )

        else:

            st.subheader(
                "Create Job"
            )

        # ====================================================
        # CLIENT OPTIONS
        # ====================================================

        client_options = {}

        for client in clients:

            label = get_client_label(
                client
            )

            client_options[label] = client.id

        client_labels = list(
            client_options.keys()
        )

        client_ids = list(
            client_options.values()
        )

        if (
            editing_job
            and editing_job.client_id
            in client_ids
        ):

            client_index = client_ids.index(
                editing_job.client_id
            )

        else:

            client_index = 0

        # ====================================================
        # FORM KEY
        # ====================================================

        form_key = (
            f"job_form_"
            f"{editing_job.id if editing_job else 'new'}"
        )

        # ====================================================
        # JOB FORM
        # ====================================================

        with st.form(
            form_key
        ):

            # =================================================
            # CLIENT
            # =================================================

            selected_client = st.selectbox(
                "Client",
                client_labels,
                index=client_index,
            )

            selected_client_id = (
                client_options[
                    selected_client
                ]
            )

            # =================================================
            # JOB DETAILS
            # =================================================

            st.subheader(
                "Job Details"
            )

            col1, col2 = st.columns(2)

            with col1:

                position = st.text_input(
                    "Position",
                    value=(
                        clean_text(
                            editing_job.position
                        )
                        if editing_job
                        else ""
                    ),
                    placeholder=(
                        "Example: "
                        "Remote Finance Specialist"
                    ),
                )

            with col2:

                department = st.text_input(
                    "Department",
                    value=(
                        clean_text(
                            editing_job.department
                        )
                        if editing_job
                        else ""
                    ),
                    placeholder=(
                        "Example: Finance"
                    ),
                )

            skills_required = st.text_area(
                "Skills Required",
                value=(
                    clean_text(
                        editing_job.skills_required
                    )
                    if editing_job
                    else ""
                ),
                placeholder=(
                    "Example: Excel, Power BI, "
                    "reconciliations, treasury"
                ),
            )

            experience_required = st.text_input(
                "Experience Required",
                value=(
                    clean_text(
                        editing_job.experience_required
                    )
                    if editing_job
                    else ""
                ),
                placeholder=(
                    "Example: 3+ years "
                    "in finance operations"
                ),
            )

            # =================================================
            # CLIENT BUDGET
            # =================================================

            st.subheader(
                "Client Budget"
            )

            budget_col1, budget_col2 = (
                st.columns(2)
            )

            with budget_col1:

                client_budget = st.number_input(
                    "Monthly Budget",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    value=(
                        safe_float(
                            getattr(
                                editing_job,
                                "client_budget",
                                0.0,
                            )
                        )
                        if editing_job
                        else 0.0
                    ),
                )

            with budget_col2:

                current_currency = (
                    clean_text(
                        getattr(
                            editing_job,
                            "currency",
                            "",
                        )
                    )
                    if editing_job
                    else "GBP"
                )

                currency_options = list(
                    CURRENCIES
                )

                if (
                    current_currency
                    and current_currency
                    not in currency_options
                ):

                    currency_options.insert(
                        0,
                        current_currency,
                    )

                currency_index = (
                    currency_options.index(
                        current_currency
                    )
                    if current_currency
                    in currency_options
                    else 0
                )

                currency = st.selectbox(
                    "Currency",
                    currency_options,
                    index=currency_index,
                )

            # =================================================
            # OPENINGS / WORK PATTERN
            # =================================================

            openings_col1, openings_col2 = (
                st.columns(2)
            )

            with openings_col1:

                current_openings = 1

                if editing_job:

                    current_openings = max(
                        safe_int(
                            getattr(
                                editing_job,
                                "openings",
                                1,
                            ),
                            1,
                        ),
                        1,
                    )

                openings = st.number_input(
                    "Number of Openings",
                    min_value=1,
                    step=1,
                    value=current_openings,
                )

            with openings_col2:

                current_work_pattern = (
                    clean_text(
                        getattr(
                            editing_job,
                            "work_pattern",
                            "",
                        )
                    )
                    if editing_job
                    else "Full-time"
                )

                work_pattern_options = list(
                    WORK_PATTERNS
                )

                if (
                    current_work_pattern
                    and current_work_pattern
                    not in work_pattern_options
                ):

                    work_pattern_options.insert(
                        0,
                        current_work_pattern,
                    )

                work_pattern_index = (
                    work_pattern_options.index(
                        current_work_pattern
                    )
                    if current_work_pattern
                    in work_pattern_options
                    else 0
                )

                work_pattern = st.selectbox(
                    "Work Pattern",
                    work_pattern_options,
                    index=work_pattern_index,
                )

            # =================================================
            # REMOTE COUNTRY
            # =================================================

            remote_country = st.text_input(
                "Remote Country",
                value=(
                    clean_text(
                        getattr(
                            editing_job,
                            "remote_country",
                            "",
                        )
                    )
                    if editing_job
                    else "India"
                ),
                placeholder="Example: India",
            )

            # =================================================
            # DATES
            # =================================================

            st.subheader(
                "Dates"
            )

            date_col1, date_col2 = (
                st.columns(2)
            )

            with date_col1:

                date_opened = st.date_input(
                    "Date Opened",
                    value=(
                        editing_job.date_opened
                        if (
                            editing_job
                            and editing_job.date_opened
                        )
                        else date.today()
                    ),
                )

            with date_col2:

                closing_date = st.date_input(
                    "Closing Date",
                    value=(
                        editing_job.closing_date
                        if (
                            editing_job
                            and editing_job.closing_date
                        )
                        else None
                    ),
                )

            # =================================================
            # STATUS / PRIORITY
            # =================================================

            status_col1, status_col2 = (
                st.columns(2)
            )

            with status_col1:

                current_status = (
                    clean_text(
                        getattr(
                            editing_job,
                            "status",
                            "",
                        )
                    )
                    if editing_job
                    else "Open"
                )

                status_options = list(
                    JOB_STATUSES
                )

                if (
                    current_status
                    and current_status
                    not in status_options
                ):

                    status_options.insert(
                        0,
                        current_status,
                    )

                status_index = (
                    status_options.index(
                        current_status
                    )
                    if current_status
                    in status_options
                    else 0
                )

                status = st.selectbox(
                    "Job Status",
                    status_options,
                    index=status_index,
                )

            with status_col2:

                current_priority = (
                    clean_text(
                        getattr(
                            editing_job,
                            "priority",
                            "",
                        )
                    )
                    if editing_job
                    else "Medium"
                )

                priority_options = list(
                    JOB_PRIORITIES
                )

                if (
                    current_priority
                    and current_priority
                    not in priority_options
                ):

                    priority_options.insert(
                        0,
                        current_priority,
                    )

                priority_index = (
                    priority_options.index(
                        current_priority
                    )
                    if current_priority
                    in priority_options
                    else 1
                )

                priority = st.selectbox(
                    "Priority",
                    priority_options,
                    index=priority_index,
                )

            # =================================================
            # NOTES
            # =================================================

            notes = st.text_area(
                "Notes",
                value=(
                    clean_text(
                        getattr(
                            editing_job,
                            "notes",
                            "",
                        )
                    )
                    if editing_job
                    else ""
                ),
                placeholder=(
                    "Additional job information..."
                ),
            )

            # =================================================
            # CURRENT RECRUITMENT INFORMATION
            # =================================================

            if editing_job:

                current_candidates = (
                    get_candidate_count(
                        editing_job
                    )
                )

                current_placements = (
                    get_placement_count(
                        editing_job
                    )
                )

                current_active_placements = (
                    get_active_placement_count(
                        editing_job
                    )
                )

                st.info(
                    f"Recruitment history: "
                    f"{current_candidates} candidate(s) · "
                    f"{current_placements} placement(s) · "
                    f"{current_active_placements} active/scheduled"
                )

            # =================================================
            # SUBMIT
            # =================================================

            submitted = st.form_submit_button(
                (
                    "Save Changes"
                    if editing_job
                    else "Create Job"
                ),
                use_container_width=True,
            )

            if submitted:

                position_clean = (
                    clean_text(position)
                )

                department_clean = (
                    clean_text(department)
                )

                skills_clean = (
                    clean_text(
                        skills_required
                    )
                )

                experience_clean = (
                    clean_text(
                        experience_required
                    )
                )

                remote_country_clean = (
                    clean_text(
                        remote_country
                    )
                )

                notes_clean = (
                    clean_text(notes)
                )

                validation_error = None

                # =============================================
                # BASIC VALIDATION
                # =============================================

                if not position_clean:

                    validation_error = (
                        "Position is required."
                    )

                elif len(position_clean) > 200:

                    validation_error = (
                        "Position must be 200 characters "
                        "or fewer."
                    )

                elif not remote_country_clean:

                    validation_error = (
                        "Remote country is required."
                    )

                # =============================================
                # DATE VALIDATION
                # =============================================

                if validation_error is None:

                    validation_error = (
                        validate_job_dates(
                            date_opened,
                            closing_date,
                        )
                    )

                # =============================================
                # BUDGET VALIDATION
                # =============================================

                if validation_error is None:

                    validation_error = (
                        validate_job_budget(
                            client_budget
                        )
                    )

                # =============================================
                # OPENINGS VALIDATION
                # =============================================

                if validation_error is None:

                    validation_error = (
                        validate_job_openings(
                            int(openings)
                        )
                    )

                # =============================================
                # CURRENT PLACEMENTS
                # =============================================

                active_placements = 0

                if editing_job:

                    active_placements = (
                        get_active_placement_count(
                            editing_job
                        )
                    )

                # =============================================
                # PROTECT EXISTING PLACEMENTS
                # =============================================

                if validation_error is None:

                    if (
                        active_placements
                        > int(openings)
                    ):

                        validation_error = (
                            "You cannot reduce the number "
                            "of openings below the number "
                            "of active or scheduled placements."
                        )

                # =============================================
                # STATUS VALIDATION
                # =============================================

                if validation_error is None:

                    validation_error = (
                        validate_job_status(
                            status,
                            int(openings),
                            active_placements,
                        )
                    )

                # =============================================
                # CLOSED / CANCELLED DATE VALIDATION
                # =============================================

                if (
                    validation_error is None
                    and status
                    in [
                        "Closed",
                        "Cancelled",
                    ]
                    and closing_date
                    and closing_date > date.today()
                ):

                    validation_error = (
                        "A Closed or Cancelled job should "
                        "not have a future closing date. "
                        "Change the closing date or use "
                        "Open/On Hold status."
                    )

                # =============================================
                # SAVE
                # =============================================

                if validation_error:

                    st.error(
                        validation_error
                    )

                else:

                    # =========================================
                    # UPDATE EXISTING JOB
                    # =========================================

                    if editing_job:

                        editing_job.client_id = (
                            selected_client_id
                        )

                        editing_job.position = (
                            position_clean
                        )

                        editing_job.department = (
                            department_clean
                        )

                        editing_job.skills_required = (
                            skills_clean
                        )

                        editing_job.experience_required = (
                            experience_clean
                        )

                        editing_job.client_budget = (
                            client_budget
                        )

                        editing_job.currency = (
                            currency
                        )

                        editing_job.openings = (
                            int(openings)
                        )

                        editing_job.work_pattern = (
                            work_pattern
                        )

                        editing_job.remote_country = (
                            remote_country_clean
                        )

                        editing_job.date_opened = (
                            date_opened
                        )

                        editing_job.closing_date = (
                            closing_date
                        )

                        editing_job.status = (
                            status
                        )

                        editing_job.priority = (
                            priority
                        )

                        editing_job.notes = (
                            notes_clean
                        )

                        try:

                            session.commit()

                            clear_job_state()

                            st.success(
                                "Job updated successfully."
                            )

                            st.rerun()

                        except Exception:

                            session.rollback()

                            st.error(
                                "Could not update the job. "
                                "Please check the entered information "
                                "and try again."
                            )

                    # =========================================
                    # CREATE NEW JOB
                    # =========================================

                    else:

                        job = Job(
                            client_id=selected_client_id,
                            position=position_clean,
                            department=department_clean,
                            skills_required=skills_clean,
                            experience_required=(
                                experience_clean
                            ),
                            client_budget=client_budget,
                            currency=currency,
                            openings=int(openings),
                            work_pattern=work_pattern,
                            remote_country=(
                                remote_country_clean
                            ),
                            date_opened=date_opened,
                            closing_date=closing_date,
                            status=status,
                            priority=priority,
                            notes=notes_clean,
                        )

                        try:

                            session.add(
                                job
                            )

                            session.commit()

                            st.success(
                                "Job created successfully."
                            )

                            st.rerun()

                        except Exception:

                            session.rollback()

                            st.error(
                                "Could not create the job. "
                                "Please check the entered information "
                                "and try again."
                            )

        # ====================================================
        # JOB REGISTER
        # ====================================================

        st.divider()

        st.subheader(
            "Job Register"
        )

        if not jobs:

            st.info(
                "No jobs have been created yet."
            )

            return

        # ====================================================
        # KPI CALCULATIONS
        # ====================================================

        total_jobs = len(
            jobs
        )

        open_jobs = sum(
            1
            for job in jobs
            if get_job_status(job) == "Open"
        )

        on_hold_jobs = sum(
            1
            for job in jobs
            if get_job_status(job) == "On Hold"
        )

        filled_jobs = sum(
            1
            for job in jobs
            if get_status_display(job)
            == "Filled"
        )

        closed_jobs = sum(
            1
            for job in jobs
            if get_job_status(job)
            == "Closed"
        )

        cancelled_jobs = sum(
            1
            for job in jobs
            if get_job_status(job)
            == "Cancelled"
        )

        total_openings = sum(
            get_total_openings(job)
            for job in jobs
        )

        filled_openings = sum(
            min(
                get_active_placement_count(job),
                get_total_openings(job),
            )
            for job in jobs
        )

        remaining_openings = sum(
            get_remaining_openings(job)
            for job in jobs
        )

        total_candidates = sum(
            get_candidate_count(job)
            for job in jobs
        )

        total_placements = sum(
            get_placement_count(job)
            for job in jobs
        )

        urgent_open_jobs = sum(
            1
            for job in jobs
            if (
                get_job_status(job)
                == "Open"
                and get_priority(job)
                == "Urgent"
            )
        )

        overdue_closing_jobs = sum(
            1
            for job in jobs
            if (
                get_job_status(job)
                in [
                    "Open",
                    "On Hold",
                ]
                and get_closing_state(job)
                == "overdue"
            )
        )

        closing_soon_jobs = sum(
            1
            for job in jobs
            if (
                get_job_status(job)
                in [
                    "Open",
                    "On Hold",
                ]
                and get_days_to_closing(job)
                is not None
                and 0
                <= get_days_to_closing(job)
                <= 7
            )
        )

        jobs_with_candidates = sum(
            1
            for job in jobs
            if job_has_candidates(job)
        )

        jobs_with_placements = sum(
            1
            for job in jobs
            if job_has_placements(job)
        )

        # ====================================================
        # PRIMARY KPIs
        # ====================================================

        k1, k2, k3, k4, k5 = (
            st.columns(5)
        )

        with k1:

            st.metric(
                "Total Jobs",
                total_jobs,
            )

        with k2:

            st.metric(
                "Open",
                open_jobs,
            )

        with k3:

            st.metric(
                "On Hold",
                on_hold_jobs,
            )

        with k4:

            st.metric(
                "Filled",
                filled_jobs,
            )

        with k5:

            st.metric(
                "Openings",
                total_openings,
            )

        # ====================================================
        # SECONDARY KPIs
        # ====================================================

        s1, s2, s3, s4, s5 = (
            st.columns(5)
        )

        with s1:

            st.metric(
                "Filled Openings",
                filled_openings,
            )

        with s2:

            st.metric(
                "Remaining",
                remaining_openings,
            )

        with s3:

            st.metric(
                "Candidates",
                total_candidates,
            )

        with s4:

            st.metric(
                "Placements",
                total_placements,
            )

        with s5:

            st.metric(
                "Urgent Open",
                urgent_open_jobs,
            )

        # ====================================================
        # OPERATIONAL WARNINGS
        # ====================================================

        if overdue_closing_jobs > 0:

            st.warning(
                f"{overdue_closing_jobs} open/on-hold "
                "job(s) have passed their closing date."
            )

        if closing_soon_jobs > 0:

            st.info(
                f"{closing_soon_jobs} open/on-hold "
                "job(s) are closing within 7 days."
            )

        st.caption(
            f"Closed jobs: {closed_jobs} · "
            f"Cancelled jobs: {cancelled_jobs} · "
            f"Jobs with candidates: {jobs_with_candidates} · "
            f"Jobs with placements: {jobs_with_placements}"
        )

        # ====================================================
        # FILTERS
        # ====================================================

        filter_col1, filter_col2, filter_col3 = (
            st.columns(3)
        )

        with filter_col1:

            search = st.text_input(
                "Search",
                placeholder=(
                    "Position, client, department, "
                    "skills or country..."
                ),
            )

        with filter_col2:

            status_filter = st.selectbox(
                "Status",
                ["All"] + JOB_STATUSES,
            )

        with filter_col3:

            priority_filter = st.selectbox(
                "Priority",
                ["All"] + JOB_PRIORITIES,
            )

        # ====================================================
        # CLIENT FILTER
        # ====================================================

        client_filter_options = {
            "All Clients": None
        }

        for client in clients:

            client_filter_options[
                get_client_label(client)
            ] = client.id

        client_filter = st.selectbox(
            "Client",
            list(
                client_filter_options.keys()
            ),
        )

        selected_client_filter_id = (
            client_filter_options[
                client_filter
            ]
        )

        # ====================================================
        # CLOSING / RECRUITMENT FILTERS
        # ====================================================

        closing_filter_col, recruitment_filter_col = (
            st.columns(2)
        )

        with closing_filter_col:

            closing_filter = st.selectbox(
                "Closing Date",
                [
                    "All",
                    "No Closing Date",
                    "Closing Today",
                    "Closing Within 7 Days",
                    "Closing Within 30 Days",
                    "Past Closing Date",
                ],
            )

        with recruitment_filter_col:

            recruitment_filter = st.selectbox(
                "Recruitment Activity",
                [
                    "All",
                    "Has Candidates",
                    "No Candidates",
                    "Has Placements",
                    "No Placements",
                    "Has Recruitment History",
                    "No Recruitment History",
                ],
            )

        # ====================================================
        # APPLY SEARCH
        # ====================================================

        filtered_jobs = list(
            jobs
        )

        if search.strip():

            search_lower = (
                search.strip().lower()
            )

            filtered_jobs = [
                job
                for job in filtered_jobs
                if search_lower
                in get_search_text(job)
            ]

        # ====================================================
        # CLIENT FILTER
        # ====================================================

        if (
            selected_client_filter_id
            is not None
        ):

            filtered_jobs = [
                job
                for job in filtered_jobs
                if job.client_id
                == selected_client_filter_id
            ]

        # ====================================================
        # STATUS FILTER
        # ====================================================

        if status_filter != "All":

            filtered_jobs = [
                job
                for job in filtered_jobs
                if get_job_status(job)
                == status_filter
            ]

        # ====================================================
        # PRIORITY FILTER
        # ====================================================

        if priority_filter != "All":

            filtered_jobs = [
                job
                for job in filtered_jobs
                if get_priority(job)
                == priority_filter
            ]

        # ====================================================
        # CLOSING FILTER
        # ====================================================

        if closing_filter != "All":

            if (
                closing_filter
                == "No Closing Date"
            ):

                filtered_jobs = [
                    job
                    for job in filtered_jobs
                    if not job.closing_date
                ]

            elif (
                closing_filter
                == "Closing Today"
            ):

                filtered_jobs = [
                    job
                    for job in filtered_jobs
                    if get_closing_state(job)
                    == "today"
                ]

            elif (
                closing_filter
                == "Closing Within 7 Days"
            ):

                filtered_jobs = [
                    job
                    for job in filtered_jobs
                    if (
                        get_days_to_closing(job)
                        is not None
                        and 0
                        <= get_days_to_closing(job)
                        <= 7
                    )
                ]

            elif (
                closing_filter
                == "Closing Within 30 Days"
            ):

                filtered_jobs = [
                    job
                    for job in filtered_jobs
                    if (
                        get_days_to_closing(job)
                        is not None
                        and 0
                        <= get_days_to_closing(job)
                        <= 30
                    )
                ]

            elif (
                closing_filter
                == "Past Closing Date"
            ):

                filtered_jobs = [
                    job
                    for job in filtered_jobs
                    if (
                        get_days_to_closing(job)
                        is not None
                        and get_days_to_closing(job)
                        < 0
                    )
                ]

        # ====================================================
        # RECRUITMENT FILTER
        # ====================================================

        if recruitment_filter != "All":

            if recruitment_filter == "Has Candidates":

                filtered_jobs = [
                    job
                    for job in filtered_jobs
                    if job_has_candidates(job)
                ]

            elif recruitment_filter == "No Candidates":

                filtered_jobs = [
                    job
                    for job in filtered_jobs
                    if not job_has_candidates(job)
                ]

            elif recruitment_filter == "Has Placements":

                filtered_jobs = [
                    job
                    for job in filtered_jobs
                    if job_has_placements(job)
                ]

            elif recruitment_filter == "No Placements":

                filtered_jobs = [
                    job
                    for job in filtered_jobs
                    if not job_has_placements(job)
                ]

            elif (
                recruitment_filter
                == "Has Recruitment History"
            ):

                filtered_jobs = [
                    job
                    for job in filtered_jobs
                    if job_has_history(job)
                ]

            elif (
                recruitment_filter
                == "No Recruitment History"
            ):

                filtered_jobs = [
                    job
                    for job in filtered_jobs
                    if not job_has_history(job)
                ]

        # ====================================================
        # RESULT COUNT
        # ====================================================

        st.caption(
            f"Showing {len(filtered_jobs)} "
            f"of {len(jobs)} job(s)"
        )

        if not filtered_jobs:

            st.info(
                "No jobs match your filters."
            )

            return

        # ====================================================
        # DISPLAY JOBS
        # ====================================================

        for job in filtered_jobs:

            client_name = (
                get_client_name(job)
            )

            candidate_count = (
                get_candidate_count(job)
            )

            placement_count = (
                get_placement_count(job)
            )

            active_placements = (
                get_active_placement_count(job)
            )

            total_openings_for_job = (
                get_total_openings(job)
            )

            remaining = (
                get_remaining_openings(job)
            )

            fill_percentage = (
                get_job_fill_percentage(job)
            )

            priority = get_priority(
                job
            )

            status = get_status_display(
                job
            )

            closing_label = (
                get_closing_label(job)
            )

            closing_state = (
                get_closing_state(job)
            )

            budget = safe_float(
                getattr(
                    job,
                    "client_budget",
                    0,
                )
            )

            currency = (
                clean_text(
                    getattr(
                        job,
                        "currency",
                        "",
                    )
                )
                or "GBP"
            )

            # =================================================
            # JOB CARD
            # =================================================

            with st.container(
                border=True
            ):

                col1, col2, col3, col4, col5 = (
                    st.columns(
                        [2.2, 2.5, 2, 2, 2]
                    )
                )

                # ---------------------------------------------
                # JOB
                # ---------------------------------------------

                with col1:

                    st.write(
                        f"**#{job.id} — "
                        f"{clean_text(job.position)}**"
                    )

                    department_text = (
                        clean_text(
                            getattr(
                                job,
                                "department",
                                "",
                            )
                        )
                        or "No department"
                    )

                    st.caption(
                        department_text
                    )

                # ---------------------------------------------
                # CLIENT
                # ---------------------------------------------

                with col2:

                    st.write(
                        f"**{client_name}**"
                    )

                    st.caption(
                        f"{total_openings_for_job} "
                        f"opening(s)"
                    )

                    remote_country = (
                        clean_text(
                            getattr(
                                job,
                                "remote_country",
                                "",
                            )
                        )
                    )

                    if remote_country:

                        st.caption(
                            "Remote: "
                            f"{remote_country}"
                        )

                # ---------------------------------------------
                # BUDGET
                # ---------------------------------------------

                with col3:

                    st.write(
                        "Budget: **"
                        f"{currency} "
                        f"{budget:,.2f}"
                        "**"
                    )

                    st.caption(
                        clean_text(
                            getattr(
                                job,
                                "work_pattern",
                                "",
                            )
                        )
                        or "No work pattern"
                    )

                    st.caption(
                        f"{active_placements}/"
                        f"{total_openings_for_job} "
                        "filled"
                    )

                # ---------------------------------------------
                # STATUS
                # ---------------------------------------------

                with col4:

                    st.write(
                        f"Status: **{status}**"
                    )

                    st.write(
                        f"{get_priority_icon(priority)} "
                        f"Priority: **{priority}**"
                    )

                    if (
                        closing_state
                        == "overdue"
                        and status
                        in [
                            "Open",
                            "On Hold",
                        ]
                    ):

                        st.error(
                            closing_label
                        )

                    elif (
                        closing_state
                        in [
                            "today",
                            "tomorrow",
                        ]
                        and status
                        in [
                            "Open",
                            "On Hold",
                        ]
                    ):

                        st.warning(
                            closing_label
                        )

                    else:

                        st.caption(
                            closing_label
                        )

                # ---------------------------------------------
                # ACTIVITY / ACTIONS
                # ---------------------------------------------

                with col5:

                    st.write(
                        f"Candidates: "
                        f"**{candidate_count}**"
                    )

                    st.write(
                        f"Remaining: "
                        f"**{remaining}**"
                    )

                    edit_btn = st.button(
                        "Edit",
                        key=(
                            f"edit_job_"
                            f"{job.id}"
                        ),
                        use_container_width=True,
                    )

                    delete_btn = st.button(
                        "Delete",
                        key=(
                            f"delete_job_"
                            f"{job.id}"
                        ),
                        use_container_width=True,
                    )

                # =================================================
                # FILL PROGRESS
                # =================================================

                st.progress(
                    min(
                        max(
                            fill_percentage / 100,
                            0.0,
                        ),
                        1.0,
                    )
                )

                st.caption(
                    f"Placement fill: "
                    f"{fill_percentage:.0f}% "
                    f"({active_placements} of "
                    f"{total_openings_for_job} openings)"
                )

                # =================================================
                # EDIT REQUEST
                # =================================================

                if edit_btn:

                    st.session_state.editing_job_id = (
                        job.id
                    )

                    st.session_state.confirm_delete_job_id = (
                        None
                    )

                    st.rerun()

                # =================================================
                # DELETE REQUEST
                # =================================================

                if delete_btn:

                    st.session_state.confirm_delete_job_id = (
                        job.id
                    )

                    st.session_state.editing_job_id = (
                        None
                    )

                    st.rerun()

                # =================================================
                # DELETE CONFIRMATION
                # =================================================

                if (
                    st.session_state.confirm_delete_job_id
                    == job.id
                ):

                    has_candidates = (
                        job_has_candidates(job)
                    )

                    has_placements = (
                        job_has_placements(job)
                    )

                    if (
                        has_candidates
                        or has_placements
                    ):

                        st.warning(
                            "This job cannot be deleted "
                            "because it has recruitment "
                            "or placement history."
                        )

                        st.caption(
                            f"Candidates: {candidate_count} · "
                            f"Placements: {placement_count}"
                        )

                        st.info(
                            "Keep the job and change its "
                            "status to Closed or Cancelled "
                            "instead."
                        )

                        close_delete = st.button(
                            "Close",
                            key=(
                                f"close_delete_"
                                f"{job.id}"
                            ),
                            use_container_width=True,
                        )

                        if close_delete:

                            st.session_state.confirm_delete_job_id = (
                                None
                            )

                            st.rerun()

                    else:

                        st.warning(
                            "Are you sure you want to "
                            "delete job "
                            f"**#{job.id} — "
                            f"{clean_text(job.position)}**?"
                        )

                        confirm_col1, confirm_col2 = (
                            st.columns(2)
                        )

                        with confirm_col1:

                            confirm_delete = st.button(
                                "Yes, Delete Job",
                                key=(
                                    f"confirm_job_"
                                    f"{job.id}"
                                ),
                                type="primary",
                                use_container_width=True,
                            )

                        with confirm_col2:

                            cancel_delete = st.button(
                                "Cancel",
                                key=(
                                    f"cancel_job_"
                                    f"{job.id}"
                                ),
                                use_container_width=True,
                            )

                        if cancel_delete:

                            st.session_state.confirm_delete_job_id = (
                                None
                            )

                            st.rerun()

                        if confirm_delete:

                            try:

                                session.delete(
                                    job
                                )

                                session.commit()

                                st.session_state.confirm_delete_job_id = (
                                    None
                                )

                                st.success(
                                    "Job deleted successfully."
                                )

                                st.rerun()

                            except Exception:

                                session.rollback()

                                st.session_state.confirm_delete_job_id = (
                                    None
                                )

                                st.error(
                                    "Could not delete the job. "
                                    "It may be linked to other "
                                    "records."
                                )

                # =================================================
                # JOB DETAILS
                # =================================================

                with st.expander(
                    "View Job Details"
                ):

                    detail_col1, detail_col2 = (
                        st.columns(2)
                    )

                    # ---------------------------------------------
                    # LEFT DETAILS
                    # ---------------------------------------------

                    with detail_col1:

                        skills_text = (
                            clean_text(
                                getattr(
                                    job,
                                    "skills_required",
                                    "",
                                )
                            )
                            or "Not specified"
                        )

                        experience_text = (
                            clean_text(
                                getattr(
                                    job,
                                    "experience_required",
                                    "",
                                )
                            )
                            or "Not specified"
                        )

                        remote_country_text = (
                            clean_text(
                                getattr(
                                    job,
                                    "remote_country",
                                    "",
                                )
                            )
                            or "Not specified"
                        )

                        st.write(
                            "**Skills Required:** "
                            f"{skills_text}"
                        )

                        st.write(
                            "**Experience Required:** "
                            f"{experience_text}"
                        )

                        st.write(
                            "**Remote Country:** "
                            f"{remote_country_text}"
                        )

                    # ---------------------------------------------
                    # RIGHT DETAILS
                    # ---------------------------------------------

                    with detail_col2:

                        if job.date_opened:

                            st.write(
                                "**Date Opened:** "
                                f"{job.date_opened.strftime('%d %b %Y')}"
                            )

                        if job.closing_date:

                            st.write(
                                "**Closing Date:** "
                                f"{job.closing_date.strftime('%d %b %Y')}"
                            )

                        work_pattern_text = (
                            clean_text(
                                getattr(
                                    job,
                                    "work_pattern",
                                    "",
                                )
                            )
                            or "Not specified"
                        )

                        st.write(
                            "**Work Pattern:** "
                            f"{work_pattern_text}"
                        )

                        st.write(
                            "**Status:** "
                            f"{status}"
                        )

                        st.write(
                            "**Priority:** "
                            f"{priority}"
                        )

                        st.write(
                            "**Client Budget:** "
                            f"{currency} "
                            f"{budget:,.2f} / month"
                        )

                    # ---------------------------------------------
                    # RECRUITMENT SUMMARY
                    # ---------------------------------------------

                    st.markdown(
                        "### Recruitment Summary"
                    )

                    summary_col1, summary_col2, summary_col3, summary_col4 = (
                        st.columns(4)
                    )

                    with summary_col1:

                        st.metric(
                            "Candidates",
                            candidate_count,
                        )

                    with summary_col2:

                        st.metric(
                            "Placements",
                            placement_count,
                        )

                    with summary_col3:

                        st.metric(
                            "Filled",
                            active_placements,
                        )

                    with summary_col4:

                        st.metric(
                            "Remaining",
                            remaining,
                        )

                    # ---------------------------------------------
                    # RECRUITMENT STATUS
                    # ---------------------------------------------

                    if candidate_count == 0:

                        st.caption(
                            "No candidates have been submitted "
                            "for this job yet."
                        )

                    else:

                        st.caption(
                            f"{candidate_count} candidate(s) "
                            "are linked to this job."
                        )

                    # ---------------------------------------------
                    # NOTES
                    # ---------------------------------------------

                    if clean_text(
                        getattr(
                            job,
                            "notes",
                            "",
                        )
                    ):

                        st.markdown(
                            "### Notes"
                        )

                        st.write(
                            clean_text(
                                job.notes
                            )
                        )

    except Exception:

        session.rollback()

        st.error(
            "An error occurred while loading jobs. "
            "Please refresh the page and try again."
        )

    finally:

        session.close()