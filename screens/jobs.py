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


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    """Safely return cleaned text."""

    if value is None:
        return ""

    return str(value).strip()


def get_client_name(job):
    """Return the client's company name."""

    if job.client:

        return (
            clean_text(
                job.client.company_name
            )
            or "Unknown Client"
        )

    return "Unknown Client"


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
    Return active/scheduled placement count.

    Completed and terminated placements are not counted
    as current filled positions.
    """

    placements = getattr(
        job,
        "placements",
        None,
    )

    if not placements:
        return 0

    active_statuses = {
        "Active",
        "Scheduled",
    }

    count = 0

    for placement in placements:

        status = clean_text(
            getattr(
                placement,
                "status",
                "",
            )
        )

        if status in active_statuses:

            count += 1

    return count


def get_total_openings(job):
    """Return total number of openings."""

    try:

        return max(
            int(job.openings or 0),
            0,
        )

    except (TypeError, ValueError):

        return 0


def get_remaining_openings(job):
    """
    Return remaining openings.

    Existing active/scheduled placements are treated
    as filled positions.
    """

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
    """Return percentage of openings filled."""

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


def get_priority_icon(priority):
    """Return a visual indicator for priority."""

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


def get_job_status(job):
    """Return a safe job status."""

    return (
        clean_text(
            job.status
        )
        or "Open"
    )


def get_days_to_closing(job):
    """Return days remaining until closing date."""

    if not job.closing_date:

        return None

    return (
        job.closing_date
        - date.today()
    ).days


def get_closing_state(job):
    """
    Return a simple closing state.

    Possible values:
    - no_date
    - overdue
    - today
    - tomorrow
    - upcoming
    """

    days = get_days_to_closing(job)

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

    days = get_days_to_closing(job)

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


def get_status_display(job):
    """
    Return a more informative status.

    If a job has all openings filled while still marked Open,
    show the underlying status plus the fill information.
    """

    status = get_job_status(job)

    remaining = get_remaining_openings(job)

    if (
        status == "Open"
        and remaining == 0
        and get_total_openings(job) > 0
    ):

        return "Filled"

    return status


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
    """
    Return whether the job has recruitment/business history.
    """

    return (
        job_has_candidates(job)
        or job_has_placements(job)
    )


def get_search_text(job):
    """Return combined searchable job text."""

    values = [
        job.position,
        job.department,
        job.skills_required,
        job.experience_required,
        job.remote_country,
        job.work_pattern,
        job.status,
        job.priority,
        get_client_name(job),
        job.notes,
    ]

    return " ".join(
        clean_text(value).lower()
        for value in values
        if clean_text(value)
    )


def validate_job_status(
    status,
    openings,
    active_placements,
):
    """
    Validate logical relationship between status,
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
        and active_placements >= openings
        and openings > 0
    ):

        return (
            "All openings are already filled. "
            "Please use Filled status."
        )

    return None


def clear_job_state():
    """Clear job editing/deletion state."""

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

        client_options = {
            (
                f"{clean_text(client.company_name)} "
                f"(ID: {client.id})"
            ): client.id
            for client in clients
        }

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
        # JOB FORM
        # ====================================================

        with st.form(
            "job_form"
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
                        float(
                            editing_job.client_budget
                            or 0.0
                        )
                        if editing_job
                        else 0.0
                    ),
                )

            with budget_col2:

                current_currency = (
                    clean_text(
                        editing_job.currency
                    )
                    if editing_job
                    else "GBP"
                )

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
                )

            # =================================================
            # OPENINGS / WORK PATTERN
            # =================================================

            openings_col1, openings_col2 = (
                st.columns(2)
            )

            with openings_col1:

                openings = st.number_input(
                    "Number of Openings",
                    min_value=1,
                    step=1,
                    value=(
                        int(
                            editing_job.openings
                            or 1
                        )
                        if editing_job
                        else 1
                    ),
                )

            with openings_col2:

                current_work_pattern = (
                    clean_text(
                        editing_job.work_pattern
                    )
                    if editing_job
                    else "Full-time"
                )

                work_pattern_index = (
                    WORK_PATTERNS.index(
                        current_work_pattern
                    )
                    if current_work_pattern
                    in WORK_PATTERNS
                    else 0
                )

                work_pattern = st.selectbox(
                    "Work Pattern",
                    WORK_PATTERNS,
                    index=work_pattern_index,
                )

            # =================================================
            # REMOTE COUNTRY
            # =================================================

            remote_country = st.text_input(
                "Remote Country",
                value=(
                    clean_text(
                        editing_job.remote_country
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
                        editing_job.status
                    )
                    if editing_job
                    else "Open"
                )

                status_index = (
                    JOB_STATUSES.index(
                        current_status
                    )
                    if current_status
                    in JOB_STATUSES
                    else 0
                )

                status = st.selectbox(
                    "Job Status",
                    JOB_STATUSES,
                    index=status_index,
                )

            with status_col2:

                current_priority = (
                    clean_text(
                        editing_job.priority
                    )
                    if editing_job
                    else "Medium"
                )

                priority_index = (
                    JOB_PRIORITIES.index(
                        current_priority
                    )
                    if current_priority
                    in JOB_PRIORITIES
                    else 1
                )

                priority = st.selectbox(
                    "Priority",
                    JOB_PRIORITIES,
                    index=priority_index,
                )

            # =================================================
            # NOTES
            # =================================================

            notes = st.text_area(
                "Notes",
                value=(
                    clean_text(
                        editing_job.notes
                    )
                    if editing_job
                    else ""
                ),
                placeholder=(
                    "Additional job information..."
                ),
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
                    position.strip()
                )

                department_clean = (
                    department.strip()
                )

                skills_clean = (
                    skills_required.strip()
                )

                experience_clean = (
                    experience_required.strip()
                )

                remote_country_clean = (
                    remote_country.strip()
                )

                notes_clean = (
                    notes.strip()
                )

                validation_error = None

                # =============================================
                # BASIC VALIDATION
                # =============================================

                if not position_clean:

                    validation_error = (
                        "Position is required."
                    )

                elif date_opened > date.today():

                    validation_error = (
                        "Date opened cannot be "
                        "in the future."
                    )

                elif (
                    closing_date
                    and closing_date < date_opened
                ):

                    validation_error = (
                        "Closing date cannot be "
                        "before the opening date."
                    )

                elif client_budget < 0:

                    validation_error = (
                        "Client budget cannot "
                        "be negative."
                    )

                elif openings < 1:

                    validation_error = (
                        "There must be at least "
                        "one opening."
                    )

                elif not remote_country_clean:

                    validation_error = (
                        "Remote country is required."
                    )

                # =============================================
                # EXISTING PLACEMENTS
                # =============================================

                active_placements = 0

                if editing_job:

                    active_placements = (
                        get_active_placement_count(
                            editing_job
                        )
                    )

                # =============================================
                # OPENINGS VALIDATION
                # =============================================

                if validation_error is None:

                    if (
                        active_placements
                        > openings
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
                            openings,
                            active_placements,
                        )
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
                    # UPDATE
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

                        except Exception as error:

                            session.rollback()

                            st.error(
                                "Could not update job: "
                                f"{error}"
                            )

                    # =========================================
                    # CREATE
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

                            session.add(job)

                            session.commit()

                            st.success(
                                "Job created successfully."
                            )

                            st.rerun()

                        except Exception as error:

                            session.rollback()

                            st.error(
                                "Could not create job: "
                                f"{error}"
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
        # KPI SUMMARY
        # ====================================================

        total_jobs = len(jobs)

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
            if (
                get_status_display(job)
                == "Filled"
            )
        )

        closed_jobs = sum(
            1
            for job in jobs
            if get_job_status(job) == "Closed"
        )

        cancelled_jobs = sum(
            1
            for job in jobs
            if get_job_status(job) == "Cancelled"
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
                and clean_text(
                    job.priority
                )
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

        if overdue_closing_jobs > 0:

            st.warning(
                f"{overdue_closing_jobs} open/on-hold "
                "job(s) have passed their closing date."
            )

        st.caption(
            f"Closed jobs: {closed_jobs} · "
            f"Cancelled jobs: {cancelled_jobs}"
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
        # ADDITIONAL FILTER
        # ====================================================

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

        # ====================================================
        # APPLY SEARCH
        # ====================================================

        filtered_jobs = jobs

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
                if clean_text(
                    job.priority
                )
                == priority_filter
            ]

        # ====================================================
        # CLOSING FILTER
        # ====================================================

        if closing_filter != "All":

            if closing_filter == "No Closing Date":

                filtered_jobs = [
                    job
                    for job in filtered_jobs
                    if not job.closing_date
                ]

            elif closing_filter == "Closing Today":

                filtered_jobs = [
                    job
                    for job in filtered_jobs
                    if (
                        get_closing_state(job)
                        == "today"
                    )
                ]

            elif closing_filter == "Closing Within 7 Days":

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

            elif closing_filter == "Closing Within 30 Days":

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

            elif closing_filter == "Past Closing Date":

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

            priority = (
                clean_text(
                    job.priority
                )
                or "Medium"
            )

            status = get_status_display(
                job
            )

            closing_label = (
                get_closing_label(job)
            )

            budget = float(
                job.client_budget or 0
            )

            currency = (
                clean_text(
                    job.currency
                )
                or "GBP"
            )

            with st.container(
                border=True
            ):

                # ==========================================
                # MAIN JOB ROW
                # ==========================================

                col1, col2, col3, col4, col5 = (
                    st.columns(
                        [2.2, 2.5, 2, 2, 2]
                    )
                )

                # ------------------------------------------
                # JOB
                # ------------------------------------------

                with col1:

                    st.write(
                        f"**#{job.id} — "
                        f"{clean_text(job.position)}**"
                    )

                    department_text = (
                        clean_text(
                            job.department
                        )
                        or "No department"
                    )

                    st.caption(
                        department_text
                    )

                # ------------------------------------------
                # CLIENT
                # ------------------------------------------

                with col2:

                    st.write(
                        f"**{client_name}**"
                    )

                    st.caption(
                        f"{total_openings_for_job} "
                        f"opening(s)"
                    )

                    if job.remote_country:

                        st.caption(
                            "Remote: "
                            f"{clean_text(job.remote_country)}"
                        )

                # ------------------------------------------
                # BUDGET
                # ------------------------------------------

                with col3:

                    st.write(
                        "Budget: **"
                        f"{currency} "
                        f"{budget:,.2f}"
                        "**"
                    )

                    st.caption(
                        clean_text(
                            job.work_pattern
                        )
                        or "No work pattern"
                    )

                    st.caption(
                        f"{active_placements}/"
                        f"{total_openings_for_job} "
                        "filled"
                    )

                # ------------------------------------------
                # STATUS
                # ------------------------------------------

                with col4:

                    st.write(
                        f"Status: **{status}**"
                    )

                    st.write(
                        f"{get_priority_icon(priority)} "
                        f"Priority: **{priority}**"
                    )

                    st.caption(
                        closing_label
                    )

                # ------------------------------------------
                # ACTIVITY / ACTIONS
                # ------------------------------------------

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

                # ==========================================
                # FILL PROGRESS
                # ==========================================

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

                # ==========================================
                # EDIT
                # ==========================================

                if edit_btn:

                    st.session_state.editing_job_id = (
                        job.id
                    )

                    st.session_state.confirm_delete_job_id = (
                        None
                    )

                    st.rerun()

                # ==========================================
                # DELETE REQUEST
                # ==========================================

                if delete_btn:

                    st.session_state.confirm_delete_job_id = (
                        job.id
                    )

                    st.session_state.editing_job_id = (
                        None
                    )

                    st.rerun()

                # ==========================================
                # DELETE CONFIRMATION
                # ==========================================

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

                            except Exception as error:

                                session.rollback()

                                st.session_state.confirm_delete_job_id = (
                                    None
                                )

                                st.error(
                                    "Could not delete job: "
                                    f"{error}"
                                )

                # ==========================================
                # JOB DETAILS
                # ==========================================

                with st.expander(
                    "View Job Details"
                ):

                    detail_col1, detail_col2 = (
                        st.columns(2)
                    )

                    # --------------------------------------
                    # LEFT DETAILS
                    # --------------------------------------

                    with detail_col1:

                        skills_text = (
                            clean_text(
                                job.skills_required
                            )
                            or "Not specified"
                        )

                        experience_text = (
                            clean_text(
                                job.experience_required
                            )
                            or "Not specified"
                        )

                        remote_country_text = (
                            clean_text(
                                job.remote_country
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

                    # --------------------------------------
                    # RIGHT DETAILS
                    # --------------------------------------

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
                                job.work_pattern
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

                    # --------------------------------------
                    # RECRUITMENT SUMMARY
                    # --------------------------------------

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

                    if job.notes:

                        st.markdown(
                            "### Notes"
                        )

                        st.write(
                            clean_text(
                                job.notes
                            )
                        )

    except Exception as error:

        session.rollback()

        st.error(
            "An error occurred while loading jobs: "
            f"{error}"
        )

    finally:

        session.close()