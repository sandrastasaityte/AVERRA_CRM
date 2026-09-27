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
    "Closed",
    "Filled",
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
            clean_text(job.client.company_name)
            or "Unknown Client"
        )

    return "Unknown Client"


def get_candidate_count(job):
    """Safely return candidate count."""
    candidates = getattr(job, "candidates", None)

    if candidates is None:
        return 0

    try:
        return len(candidates)
    except TypeError:
        return 0


def get_placement_count(job):
    """Safely return placement count."""
    placements = getattr(job, "placements", None)

    if placements is None:
        return 0

    try:
        return len(placements)
    except TypeError:
        return 0


def get_priority_icon(priority):
    """Return a simple visual indicator for priority."""

    icons = {
        "Low": "🟢",
        "Medium": "🟡",
        "High": "🟠",
        "Urgent": "🔴",
    }

    return icons.get(priority, "⚪")


def get_job_status(job):
    """Return a safe job status."""
    return clean_text(job.status) or "Open"


def get_days_to_closing(job):
    """Return days remaining until closing date."""

    if not job.closing_date:
        return None

    return (job.closing_date - date.today()).days


def get_closing_label(job):
    """Return readable closing-date information."""

    days = get_days_to_closing(job)

    if days is None:
        return "No closing date"

    if days < 0:
        return f"Closed {abs(days)} day(s) ago"

    if days == 0:
        return "Closes today"

    if days == 1:
        return "Closes tomorrow"

    return f"{days} days remaining"


# ============================================================
# MAIN SCREEN
# ============================================================

def show_jobs():

    st.title("Jobs")

    st.caption(
        "Create and manage client job requirements, vacancies and recruitment activity."
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
            .order_by(Client.company_name)
            .all()
        )

        if not clients:

            st.warning(
                "Please add a client before creating a job."
            )

            return

        # ====================================================
        # LOAD EDITING JOB
        # ====================================================

        editing_job = None

        if st.session_state.editing_job_id is not None:

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
                f"Edit Job — {clean_text(editing_job.position)}"
            )

        else:

            st.subheader("Create Job")

        # ====================================================
        # CLIENT OPTIONS
        # ====================================================

        client_options = {
            f"{clean_text(client.company_name)} "
            f"(ID: {client.id})": client.id
            for client in clients
        }

        client_labels = list(client_options.keys())
        client_ids = list(client_options.values())

        if (
            editing_job
            and editing_job.client_id in client_ids
        ):

            client_index = client_ids.index(
                editing_job.client_id
            )

        else:

            client_index = 0

        # ====================================================
        # JOB FORM
        # ====================================================

        with st.form("job_form"):

            # =================================================
            # CLIENT
            # =================================================

            selected_client = st.selectbox(
                "Client",
                client_labels,
                index=client_index,
            )

            # =================================================
            # JOB DETAILS
            # =================================================

            st.subheader("Job Details")

            col1, col2 = st.columns(2)

            with col1:

                position = st.text_input(
                    "Position",
                    value=(
                        clean_text(editing_job.position)
                        if editing_job
                        else ""
                    ),
                    placeholder=(
                        "Example: Remote Finance Specialist"
                    ),
                )

            with col2:

                department = st.text_input(
                    "Department",
                    value=(
                        clean_text(editing_job.department)
                        if editing_job
                        else ""
                    ),
                    placeholder="Example: Finance",
                )

            skills_required = st.text_area(
                "Skills Required",
                value=(
                    clean_text(editing_job.skills_required)
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
                    "Example: 3+ years in finance operations"
                ),
            )

            # =================================================
            # CLIENT BUDGET
            # =================================================

            st.subheader("Client Budget")

            budget_col1, budget_col2 = st.columns(2)

            with budget_col1:

                client_budget = st.number_input(
                    "Monthly Budget",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    value=(
                        float(
                            editing_job.client_budget or 0.0
                        )
                        if editing_job
                        else 0.0
                    ),
                )

            with budget_col2:

                current_currency = (
                    clean_text(editing_job.currency)
                    if editing_job
                    else "GBP"
                )

                currency_index = (
                    CURRENCIES.index(current_currency)
                    if current_currency in CURRENCIES
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

            openings_col1, openings_col2 = st.columns(2)

            with openings_col1:

                openings = st.number_input(
                    "Number of Openings",
                    min_value=1,
                    step=1,
                    value=(
                        int(editing_job.openings or 1)
                        if editing_job
                        else 1
                    ),
                )

            with openings_col2:

                current_work_pattern = (
                    clean_text(editing_job.work_pattern)
                    if editing_job
                    else "Full-time"
                )

                work_pattern_index = (
                    WORK_PATTERNS.index(
                        current_work_pattern
                    )
                    if current_work_pattern in WORK_PATTERNS
                    else 0
                )

                work_pattern = st.selectbox(
                    "Work Pattern",
                    WORK_PATTERNS,
                    index=work_pattern_index,
                )

            # =================================================
            # REMOTE LOCATION
            # =================================================

            remote_country = st.text_input(
                "Remote Country",
                value=(
                    clean_text(editing_job.remote_country)
                    if editing_job
                    else "India"
                ),
                placeholder="Example: India",
            )

            # =================================================
            # DATES
            # =================================================

            st.subheader("Dates")

            date_col1, date_col2 = st.columns(2)

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
                        else date.today()
                    ),
                )

            # =================================================
            # STATUS / PRIORITY
            # =================================================

            status_col1, status_col2 = st.columns(2)

            with status_col1:

                current_status = (
                    clean_text(editing_job.status)
                    if editing_job
                    else "Open"
                )

                status_index = (
                    JOB_STATUSES.index(current_status)
                    if current_status in JOB_STATUSES
                    else 0
                )

                status = st.selectbox(
                    "Job Status",
                    JOB_STATUSES,
                    index=status_index,
                )

            with status_col2:

                current_priority = (
                    clean_text(editing_job.priority)
                    if editing_job
                    else "Medium"
                )

                priority_index = (
                    JOB_PRIORITIES.index(current_priority)
                    if current_priority in JOB_PRIORITIES
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
                    clean_text(editing_job.notes)
                    if editing_job
                    else ""
                ),
                placeholder="Additional job information...",
            )

            # =================================================
            # SUBMIT
            # =================================================

            submitted = st.form_submit_button(
                "Save Changes"
                if editing_job
                else "Create Job",
                use_container_width=True,
            )

            if submitted:

                position_clean = position.strip()
                department_clean = department.strip()
                skills_clean = skills_required.strip()
                experience_clean = experience_required.strip()
                remote_country_clean = remote_country.strip()
                notes_clean = notes.strip()

                # =============================================
                # VALIDATION
                # =============================================

                if not position_clean:

                    st.error(
                        "Position is required."
                    )

                elif date_opened > date.today():

                    st.error(
                        "Date opened cannot be in the future."
                    )

                elif closing_date < date_opened:

                    st.error(
                        "Closing date cannot be before the opening date."
                    )

                elif client_budget < 0:

                    st.error(
                        "Client budget cannot be negative."
                    )

                elif openings < 1:

                    st.error(
                        "There must be at least one opening."
                    )

                else:

                    selected_client_id = (
                        client_options[selected_client]
                    )

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
                            openings
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

                            st.session_state.editing_job_id = None

                            st.success(
                                "Job updated successfully."
                            )

                            st.rerun()

                        except Exception as e:

                            session.rollback()

                            st.error(
                                f"Could not update job: {e}"
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
                            experience_required=experience_clean,
                            client_budget=client_budget,
                            currency=currency,
                            openings=openings,
                            work_pattern=work_pattern,
                            remote_country=remote_country_clean,
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

                        except Exception as e:

                            session.rollback()

                            st.error(
                                f"Could not create job: {e}"
                            )

        # ====================================================
        # JOB REGISTER
        # ====================================================

        st.divider()

        st.subheader("Job Register")

        jobs = (
            session.query(Job)
            .order_by(
                Job.date_opened.desc(),
                Job.id.desc(),
            )
            .all()
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
            if get_job_status(job) == "Filled"
        )

        total_openings = sum(
            int(job.openings or 0)
            for job in jobs
        )

        total_candidates = sum(
            get_candidate_count(job)
            for job in jobs
        )

        k1, k2, k3, k4, k5 = st.columns(5)

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

        st.caption(
            f"Total candidates linked to jobs: {total_candidates}"
        )

        # ====================================================
        # FILTERS
        # ====================================================

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:

            search = st.text_input(
                "Search",
                placeholder=(
                    "Position, client, department or skills..."
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
        # APPLY FILTERS
        # ====================================================

        filtered_jobs = jobs

        if search.strip():

            search_lower = search.strip().lower()

            filtered_jobs = [
                job
                for job in filtered_jobs
                if (
                    search_lower
                    in clean_text(job.position).lower()
                )
                or (
                    search_lower
                    in clean_text(job.department).lower()
                )
                or (
                    search_lower
                    in clean_text(
                        job.skills_required
                    ).lower()
                )
                or (
                    search_lower
                    in clean_text(
                        job.experience_required
                    ).lower()
                )
                or (
                    search_lower
                    in clean_text(
                        job.remote_country
                    ).lower()
                )
                or (
                    search_lower
                    in get_client_name(job).lower()
                )
            ]

        if status_filter != "All":

            filtered_jobs = [
                job
                for job in filtered_jobs
                if get_job_status(job)
                == status_filter
            ]

        if priority_filter != "All":

            filtered_jobs = [
                job
                for job in filtered_jobs
                if clean_text(job.priority)
                == priority_filter
            ]

        # ====================================================
        # RESULT COUNT
        # ====================================================

        st.caption(
            f"Showing {len(filtered_jobs)} of {len(jobs)} job(s)"
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

            client_name = get_client_name(job)

            candidate_count = get_candidate_count(job)

            placement_count = get_placement_count(job)

            priority = clean_text(job.priority) or "Medium"

            status = get_job_status(job)

            closing_label = get_closing_label(job)

            with st.container(border=True):

                # ==========================================
                # MAIN JOB ROW
                # ==========================================

                col1, col2, col3, col4, col5 = st.columns(
                    [2.2, 2.5, 2, 2, 2]
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
                        clean_text(job.department)
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
                        f"{int(job.openings or 0)} opening(s)"
                    )

                    if job.remote_country:

                        st.caption(
                            f"Remote: "
                            f"{clean_text(job.remote_country)}"
                        )

                # ------------------------------------------
                # BUDGET
                # ------------------------------------------

                with col3:

                    budget = float(
                        job.client_budget or 0
                    )

                    currency = (
                        clean_text(job.currency)
                        or "GBP"
                    )

                    st.write(
                        f"Budget: **"
                        f"{currency} "
                        f"{budget:,.2f}"
                        f"**"
                    )

                    st.caption(
                        clean_text(job.work_pattern)
                        or "No work pattern"
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
                        f"Candidates: **{candidate_count}**"
                    )

                    st.write(
                        f"Placements: **{placement_count}**"
                    )

                    edit_btn = st.button(
                        "Edit",
                        key=f"edit_job_{job.id}",
                        use_container_width=True,
                    )

                    delete_btn = st.button(
                        "Delete",
                        key=f"delete_job_{job.id}",
                        use_container_width=True,
                    )

                # ==========================================
                # EDIT
                # ==========================================

                if edit_btn:

                    st.session_state.editing_job_id = job.id

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

                    st.session_state.editing_job_id = None

                    st.rerun()

                # ==========================================
                # DELETE CONFIRMATION
                # ==========================================

                if (
                    st.session_state.confirm_delete_job_id
                    == job.id
                ):

                    has_candidates = (
                        get_candidate_count(job) > 0
                    )

                    has_placements = (
                        get_placement_count(job) > 0
                    )

                    if has_candidates or has_placements:

                        st.warning(
                            "This job cannot be deleted because "
                            "it has candidates or placements attached."
                        )

                        close_delete = st.button(
                            "Close",
                            key=f"close_delete_{job.id}",
                            use_container_width=True,
                        )

                        if close_delete:

                            st.session_state.confirm_delete_job_id = (
                                None
                            )

                            st.rerun()

                    else:

                        st.warning(
                            f"Are you sure you want to delete "
                            f"job **#{job.id} — "
                            f"{clean_text(job.position)}**?"
                        )

                        confirm_col1, confirm_col2 = st.columns(2)

                        with confirm_col1:

                            confirm_delete = st.button(
                                "Yes, Delete Job",
                                key=f"confirm_job_{job.id}",
                                type="primary",
                                use_container_width=True,
                            )

                        with confirm_col2:

                            cancel_delete = st.button(
                                "Cancel",
                                key=f"cancel_job_{job.id}",
                                use_container_width=True,
                            )

                        if cancel_delete:

                            st.session_state.confirm_delete_job_id = (
                                None
                            )

                            st.rerun()

                        if confirm_delete:

                            try:

                                session.delete(job)
                                session.commit()

                                st.session_state.confirm_delete_job_id = (
                                    None
                                )

                                st.success(
                                    "Job deleted successfully."
                                )

                                st.rerun()

                            except Exception as e:

                                session.rollback()

                                st.session_state.confirm_delete_job_id = (
                                    None
                                )

                                st.error(
                                    f"Could not delete job: {e}"
                                )

                # ==========================================
                # JOB DETAILS
                # ==========================================

                with st.expander("View Job Details"):

                    detail_col1, detail_col2 = st.columns(2)

                    with detail_col1:

                        st.write(
                            f"**Skills Required:** "
                            f"{clean_text(job.skills_required) "
                            "or 'Not specified'}"
                        )

                        st.write(
                            f"**Experience Required:** "
                            f"{clean_text(job.experience_required) "
                            "or 'Not specified'}"
                        )

                        st.write(
                            f"**Remote Country:** "
                            f"{clean_text(job.remote_country) "
                            "or 'Not specified'}"
                        )

                    with detail_col2:

                        if job.date_opened:

                            st.write(
                                f"**Date Opened:** "
                                f"{job.date_opened.strftime('%d %b %Y')}"
                            )

                        if job.closing_date:

                            st.write(
                                f"**Closing Date:** "
                                f"{job.closing_date.strftime('%d %b %Y')}"
                            )

                        st.write(
                            f"**Work Pattern:** "
                            f"{clean_text(job.work_pattern) "
                            "or 'Not specified'}"
                        )

                    if job.notes:

                        st.write(
                            f"**Notes:** {clean_text(job.notes)}"
                        )

    except Exception as e:

        session.rollback()

        st.error(
            f"An error occurred while loading jobs: {e}"
        )

    finally:

        session.close()