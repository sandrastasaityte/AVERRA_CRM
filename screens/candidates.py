import streamlit as st
from datetime import date, timedelta

from database import get_session
from models import (
    Candidate,
    Job,
    Employee,
    Activity,
)


# ============================================================
# CONSTANTS
# ============================================================

CANDIDATE_STATUSES = [
    "Submitted",
    "Shortlisted",
    "Interview",
    "Offer",
    "Placed",
    "Rejected",
    "Withdrawn",
]


INTERVIEW_FILTERS = [
    "All",
    "Today",
    "Upcoming",
    "Past",
    "No Interview",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_employee_name(employee):
    """
    Return a readable employee name.
    """

    if not employee:
        return "Unknown Employee"

    full_name = " ".join(
        str(part).strip()
        for part in [
            employee.first_name,
            employee.last_name,
        ]
        if part and str(part).strip()
    ).strip()

    return full_name or f"Employee #{employee.id}"


def get_job_name(job):
    """
    Return a readable job name including client.
    """

    if not job:
        return "Unknown Job"

    position = (
        job.position
        or f"Job #{job.id}"
    )

    if job.client:

        company_name = (
            job.client.company_name
            or "Unknown Client"
        )

        return (
            f"{position} - "
            f"{company_name}"
        )

    return f"{position} - No Client"


def get_company_name(candidate):
    """
    Return the client company for a candidate.
    """

    if (
        candidate
        and candidate.job
        and candidate.job.client
    ):

        return (
            candidate.job.client.company_name
            or ""
        )

    return ""


def get_candidate_search_text(candidate):
    """
    Build searchable text for a candidate.
    """

    employee_name = get_employee_name(
        candidate.employee
    )

    employee_role = ""

    if candidate.employee:
        employee_role = (
            candidate.employee.role
            or ""
        )

    job_name = ""

    if candidate.job:
        job_name = (
            candidate.job.position
            or ""
        )

    company_name = get_company_name(
        candidate
    )

    candidate_id = str(
        getattr(candidate, "id", "")
    )

    return " ".join(
        [
            candidate_id,
            employee_name,
            employee_role,
            job_name,
            company_name,
            candidate.status or "",
            candidate.client_feedback or "",
            candidate.notes or "",
        ]
    ).lower()


def interview_status(candidate):
    """
    Return interview timing state.

    Possible values:
    - None
    - Past
    - Today
    - Upcoming
    """

    if not candidate:
        return None

    if not candidate.interview_date:
        return None

    if candidate.status in [
        "Rejected",
        "Withdrawn",
        "Placed",
    ]:
        return None

    today = date.today()

    if candidate.interview_date < today:
        return "Past"

    if candidate.interview_date == today:
        return "Today"

    return "Upcoming"


def get_interview_label(candidate):
    """
    Return a readable interview label.
    """

    if not candidate.interview_date:
        return "No interview"

    state = interview_status(candidate)

    if state == "Today":
        return "Interview today"

    if state == "Upcoming":
        return "Upcoming interview"

    if state == "Past":
        return "Interview date passed"

    return "Interview scheduled"


def candidate_has_activities(session, candidate_id):
    """
    Check whether the candidate is referenced by Activities.

    Candidates with CRM history should not be casually deleted.
    """

    return (
        session.query(Activity)
        .filter(
            Activity.candidate_id == candidate_id
        )
        .count()
        > 0
    )


def get_activity_count(session, candidate_id):
    """
    Return number of activities linked to candidate.
    """

    return (
        session.query(Activity)
        .filter(
            Activity.candidate_id == candidate_id
        )
        .count()
    )


def validate_candidate_dates(
    date_submitted,
    interview_date,
):
    """
    Validate candidate date relationships.
    """

    if not date_submitted:
        return "Date submitted is required."

    if (
        interview_date
        and interview_date < date_submitted
    ):
        return (
            "Interview date cannot be earlier "
            "than the candidate submission date."
        )

    return None


def validate_candidate_status(
    status,
    interview_date,
):
    """
    Validate relationship between status and interview date.
    """

    if status == "Interview" and not interview_date:
        return (
            "Candidates with status 'Interview' "
            "should have an interview date."
        )

    return None


def get_status_counts(candidates):
    """
    Return candidate counts by status.
    """

    return {
        status: sum(
            1
            for candidate in candidates
            if candidate.status == status
        )
        for status in CANDIDATE_STATUSES
    }


def get_current_job_label(
    job_options,
    job_id,
):
    """
    Find the dropdown label for a job ID.
    """

    for label, record_id in job_options.items():

        if record_id == job_id:
            return label

    return None


def get_current_employee_label(
    employee_options,
    employee_id,
):
    """
    Find the dropdown label for an employee ID.
    """

    for label, record_id in employee_options.items():

        if record_id == employee_id:
            return label

    return None


def build_job_options(jobs):
    """
    Build unique job dropdown options.
    """

    options = {}

    for job in jobs:

        base_label = get_job_name(job)

        label = (
            f"{base_label} "
            f"(Job #{job.id})"
        )

        options[label] = job.id

    return options


def build_employee_options(employees):
    """
    Build unique employee dropdown options.
    """

    options = {}

    for employee in employees:

        employee_name = get_employee_name(
            employee
        )

        role = (
            employee.role
            or "No role"
        )

        country = (
            employee.country
            or ""
        )

        label = (
            f"{employee_name} - "
            f"{role}"
        )

        if country:
            label += f" - {country}"

        label += (
            f" (Employee #{employee.id})"
        )

        options[label] = employee.id

    return options


# ============================================================
# MAIN CANDIDATES SCREEN
# ============================================================

def show_candidates():

    st.title("Candidates")

    st.caption(
        "Manage employee submissions and recruitment pipeline."
    )

    session = get_session()

    try:

        # ========================================================
        # LOAD JOBS
        # ========================================================

        jobs = (
            session.query(Job)
            .order_by(
                Job.date_opened.desc(),
                Job.id.desc(),
            )
            .all()
        )

        # ========================================================
        # LOAD EMPLOYEES
        # ========================================================

        employees = (
            session.query(Employee)
            .order_by(
                Employee.first_name.asc(),
                Employee.last_name.asc(),
                Employee.id.asc(),
            )
            .all()
        )

        # ========================================================
        # CREATE OPTIONS
        # ========================================================

        job_options = build_job_options(
            jobs
        )

        employee_options = build_employee_options(
            employees
        )

        # ========================================================
        # SUBMIT CANDIDATE
        # ========================================================

        st.header("Submit Candidate")

        if not jobs:

            st.info(
                "Please create a Job before submitting a candidate."
            )

        elif not employees:

            st.info(
                "Please add an Employee before submitting a candidate."
            )

        else:

            with st.form(
                "add_candidate_form"
            ):

                st.markdown(
                    "### Candidate Submission"
                )

                col1, col2 = st.columns(2)

                with col1:

                    selected_job = st.selectbox(
                        "Job *",
                        list(
                            job_options.keys()
                        ),
                    )

                    date_submitted = st.date_input(
                        "Date Submitted",
                        value=date.today(),
                    )

                    status = st.selectbox(
                        "Candidate Status",
                        CANDIDATE_STATUSES,
                    )

                with col2:

                    selected_employee = st.selectbox(
                        "Employee *",
                        list(
                            employee_options.keys()
                        ),
                    )

                    interview_scheduled = st.checkbox(
                        "Interview Scheduled"
                    )

                    interview_date = None

                    if interview_scheduled:

                        interview_date = st.date_input(
                            "Interview Date",
                            value=date.today(),
                        )

                st.markdown(
                    "### Client Feedback"
                )

                client_feedback = st.text_area(
                    "Client Feedback",
                    placeholder=(
                        "Enter feedback received "
                        "from the client..."
                    ),
                )

                st.markdown(
                    "### Internal Notes"
                )

                notes = st.text_area(
                    "Notes",
                    placeholder=(
                        "Internal recruitment notes..."
                    ),
                )

                submitted = st.form_submit_button(
                    "Submit Candidate",
                    use_container_width=True,
                )

                if submitted:

                    job_id = job_options[
                        selected_job
                    ]

                    employee_id = (
                        employee_options[
                            selected_employee
                        ]
                    )

                    # ================================================
                    # DATE VALIDATION
                    # ================================================

                    date_error = (
                        validate_candidate_dates(
                            date_submitted,
                            interview_date,
                        )
                    )

                    # ================================================
                    # STATUS VALIDATION
                    # ================================================

                    status_error = (
                        validate_candidate_status(
                            status,
                            interview_date,
                        )
                    )

                    if date_error:

                        st.error(
                            date_error
                        )

                    elif status_error:

                        st.warning(
                            status_error
                        )

                    else:

                        # ============================================
                        # DUPLICATE CHECK
                        # ============================================

                        existing_candidate = (
                            session.query(Candidate)
                            .filter(
                                Candidate.job_id
                                == job_id,
                                Candidate.employee_id
                                == employee_id,
                            )
                            .first()
                        )

                        if existing_candidate:

                            st.warning(
                                "This employee has already "
                                "been submitted for this job."
                            )

                            st.info(
                                "You can update the existing "
                                "candidate record instead of "
                                "creating a duplicate."
                            )

                        else:

                            candidate = Candidate(
                                job_id=job_id,
                                employee_id=employee_id,
                                date_submitted=(
                                    date_submitted
                                ),
                                status=status,
                                interview_date=(
                                    interview_date
                                ),
                                client_feedback=(
                                    client_feedback.strip()
                                ),
                                notes=(
                                    notes.strip()
                                ),
                            )

                            try:

                                session.add(
                                    candidate
                                )

                                session.commit()

                                st.success(
                                    "Candidate submitted successfully."
                                )

                                st.rerun()

                            except Exception as error:

                                session.rollback()

                                st.error(
                                    "The candidate could "
                                    "not be created."
                                )

                                st.exception(
                                    error
                                )

        # ========================================================
        # CANDIDATE REGISTER
        # ========================================================

        st.divider()

        st.header("Candidate Register")

        candidates = (
            session.query(Candidate)
            .order_by(
                Candidate.date_submitted.desc(),
                Candidate.id.desc(),
            )
            .all()
        )

        # ========================================================
        # NO CANDIDATES
        # ========================================================

        if not candidates:

            st.info(
                "No candidates have been submitted yet."
            )

            return

        # ========================================================
        # SUMMARY COUNTS
        # ========================================================

        status_counts = get_status_counts(
            candidates
        )

        total_candidates = len(
            candidates
        )

        interviews_today = sum(
            1
            for candidate in candidates
            if interview_status(candidate)
            == "Today"
        )

        upcoming_interviews = sum(
            1
            for candidate in candidates
            if interview_status(candidate)
            == "Upcoming"
        )

        past_interviews = sum(
            1
            for candidate in candidates
            if interview_status(candidate)
            == "Past"
        )

        no_interview = sum(
            1
            for candidate in candidates
            if not candidate.interview_date
        )

        # ========================================================
        # SUMMARY DISPLAY
        # ========================================================

        st.subheader(
            "Recruitment Pipeline"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Total",
                total_candidates,
            )

        with col2:

            st.metric(
                "Submitted",
                status_counts["Submitted"],
            )

        with col3:

            st.metric(
                "Shortlisted",
                status_counts["Shortlisted"],
            )

        with col4:

            st.metric(
                "Interview",
                status_counts["Interview"],
            )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Offer",
                status_counts["Offer"],
            )

        with col2:

            st.metric(
                "Placed",
                status_counts["Placed"],
            )

        with col3:

            st.metric(
                "Rejected",
                status_counts["Rejected"],
            )

        with col4:

            st.metric(
                "Withdrawn",
                status_counts["Withdrawn"],
            )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Interviews Today",
                interviews_today,
            )

        with col2:

            st.metric(
                "Upcoming Interviews",
                upcoming_interviews,
            )

        with col3:

            st.metric(
                "Past Interviews",
                past_interviews,
            )

        with col4:

            st.metric(
                "No Interview",
                no_interview,
            )

        # ========================================================
        # FILTERS
        # ========================================================

        st.subheader(
            "Filters"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            search = st.text_input(
                "Search",
                placeholder=(
                    "Employee, job, company, "
                    "role, status, notes or ID..."
                ),
            )

        with col2:

            status_filter = st.selectbox(
                "Status",
                ["All"] + CANDIDATE_STATUSES,
            )

        with col3:

            interview_filter = st.selectbox(
                "Interview",
                INTERVIEW_FILTERS,
            )

        # ========================================================
        # ADDITIONAL FILTERS
        # ========================================================

        col1, col2 = st.columns(2)

        with col1:

            company_filter_options = [
                "All"
            ]

            company_names = sorted(
                {
                    get_company_name(candidate)
                    for candidate in candidates
                    if get_company_name(candidate)
                }
            )

            company_filter_options.extend(
                company_names
            )

            company_filter = st.selectbox(
                "Client",
                company_filter_options,
            )

        with col2:

            role_options = [
                "All"
            ]

            role_names = sorted(
                {
                    candidate.employee.role
                    for candidate in candidates
                    if (
                        candidate.employee
                        and candidate.employee.role
                    )
                }
            )

            role_options.extend(
                role_names
            )

            role_filter = st.selectbox(
                "Employee Role",
                role_options,
            )

        # ========================================================
        # DATE FILTERS
        # ========================================================

        col1, col2 = st.columns(2)

        with col1:

            submitted_from = st.date_input(
                "Submitted From",
                value=None,
            )

        with col2:

            submitted_to = st.date_input(
                "Submitted To",
                value=None,
            )

        # ========================================================
        # APPLY SEARCH FILTER
        # ========================================================

        filtered_candidates = list(
            candidates
        )

        if search:

            search_text = (
                search.strip().lower()
            )

            filtered_candidates = [
                candidate
                for candidate
                in filtered_candidates
                if search_text
                in get_candidate_search_text(
                    candidate
                )
            ]

        # ========================================================
        # APPLY STATUS FILTER
        # ========================================================

        if status_filter != "All":

            filtered_candidates = [
                candidate
                for candidate
                in filtered_candidates
                if candidate.status
                == status_filter
            ]

        # ========================================================
        # APPLY INTERVIEW FILTER
        # ========================================================

        if interview_filter != "All":

            if interview_filter == "No Interview":

                filtered_candidates = [
                    candidate
                    for candidate
                    in filtered_candidates
                    if not candidate.interview_date
                ]

            else:

                filtered_candidates = [
                    candidate
                    for candidate
                    in filtered_candidates
                    if interview_status(
                        candidate
                    )
                    == interview_filter
                ]

        # ========================================================
        # APPLY CLIENT FILTER
        # ========================================================

        if company_filter != "All":

            filtered_candidates = [
                candidate
                for candidate
                in filtered_candidates
                if get_company_name(candidate)
                == company_filter
            ]

        # ========================================================
        # APPLY ROLE FILTER
        # ========================================================

        if role_filter != "All":

            filtered_candidates = [
                candidate
                for candidate
                in filtered_candidates
                if (
                    candidate.employee
                    and candidate.employee.role
                    == role_filter
                )
            ]

        # ========================================================
        # APPLY SUBMITTED DATE FILTER
        # ========================================================

        if submitted_from:

            filtered_candidates = [
                candidate
                for candidate
                in filtered_candidates
                if (
                    candidate.date_submitted
                    and candidate.date_submitted
                    >= submitted_from
                )
            ]

        if submitted_to:

            filtered_candidates = [
                candidate
                for candidate
                in filtered_candidates
                if (
                    candidate.date_submitted
                    and candidate.date_submitted
                    <= submitted_to
                )
            ]

        if (
            submitted_from
            and submitted_to
            and submitted_from > submitted_to
        ):

            st.warning(
                "Submitted From cannot be later "
                "than Submitted To."
            )

            filtered_candidates = []

        # ========================================================
        # FILTER RESULT
        # ========================================================

        st.write(
            f"Showing **{len(filtered_candidates)}** "
            f"candidate(s)"
        )

        # ========================================================
        # DISPLAY CANDIDATES
        # ========================================================

        if not filtered_candidates:

            st.info(
                "No candidates match the selected filters."
            )

        for candidate in filtered_candidates:

            employee_name = get_employee_name(
                candidate.employee
            )

            job_name = get_job_name(
                candidate.job
            )

            company_name = get_company_name(
                candidate
            )

            linked_activity_count = (
                get_activity_count(
                    session,
                    candidate.id,
                )
            )

            with st.container(
                border=True
            ):

                # ====================================================
                # HEADER
                # ====================================================

                col1, col2, col3 = st.columns(
                    [4, 4, 2]
                )

                with col1:

                    st.subheader(
                        employee_name
                    )

                    st.caption(
                        f"Candidate #{candidate.id}"
                    )

                    if candidate.employee:

                        if candidate.employee.role:

                            st.caption(
                                candidate.employee.role
                            )

                        if candidate.employee.country:

                            st.caption(
                                candidate.employee.country
                            )

                with col2:

                    st.write(
                        "**Job**"
                    )

                    st.write(
                        job_name
                    )

                    if company_name:

                        st.caption(
                            company_name
                        )

                with col3:

                    st.write(
                        "**Status**"
                    )

                    st.write(
                        candidate.status
                        or "—"
                    )

                    if candidate.date_submitted:

                        st.caption(
                            "Submitted: "
                            f"{candidate.date_submitted}"
                        )

                # ====================================================
                # INTERVIEW INFORMATION
                # ====================================================

                if candidate.interview_date:

                    st.divider()

                    col1, col2, col3 = st.columns(3)

                    with col1:

                        st.write(
                            "**Interview Date**"
                        )

                        st.write(
                            candidate.interview_date
                        )

                    with col2:

                        interview_state = (
                            interview_status(
                                candidate
                            )
                        )

                        st.write(
                            "**Interview Status**"
                        )

                        if interview_state == "Today":

                            st.warning(
                                "Interview today"
                            )

                        elif interview_state == "Upcoming":

                            st.info(
                                "Upcoming interview"
                            )

                        elif interview_state == "Past":

                            st.caption(
                                "Interview date passed"
                            )

                        else:

                            st.caption(
                                "No active interview"
                            )

                    with col3:

                        st.write(
                            "**Interview Label**"
                        )

                        st.write(
                            get_interview_label(
                                candidate
                            )
                        )

                # ====================================================
                # FEEDBACK / NOTES
                # ====================================================

                if candidate.client_feedback:

                    st.divider()

                    st.write(
                        "**Client Feedback**"
                    )

                    st.write(
                        candidate.client_feedback
                    )

                if candidate.notes:

                    st.write(
                        "**Internal Notes**"
                    )

                    st.write(
                        candidate.notes
                    )

                # ====================================================
                # ACTIVITY INFORMATION
                # ====================================================

                st.divider()

                if linked_activity_count > 0:

                    st.info(
                        f"CRM Activities linked: "
                        f"{linked_activity_count}"
                    )

                else:

                    st.caption(
                        "No CRM activities linked."
                    )

                # ====================================================
                # ACTIONS
                # ====================================================

                action_col1, action_col2, action_col3 = (
                    st.columns(3)
                )

                with action_col1:

                    if st.button(
                        "Edit",
                        key=(
                            f"edit_candidate_"
                            f"{candidate.id}"
                        ),
                        use_container_width=True,
                    ):

                        st.session_state[
                            "editing_candidate_id"
                        ] = candidate.id

                        st.session_state.pop(
                            "deleting_candidate_id",
                            None,
                        )

                        st.rerun()

                with action_col2:

                    if (
                        candidate.status
                        not in [
                            "Placed",
                            "Rejected",
                            "Withdrawn",
                        ]
                        and st.button(
                            "Mark Interview",
                            key=(
                                f"interview_candidate_"
                                f"{candidate.id}"
                            ),
                            use_container_width=True,
                        )
                    ):

                        if not candidate.interview_date:

                            candidate.interview_date = (
                                date.today()
                            )

                        candidate.status = (
                            "Interview"
                        )

                        try:

                            session.commit()

                            st.success(
                                "Candidate moved to Interview."
                            )

                            st.rerun()

                        except Exception as error:

                            session.rollback()

                            st.error(
                                "Unable to update candidate."
                            )

                            st.exception(
                                error
                            )

                with action_col3:

                    if st.button(
                        "Delete",
                        key=(
                            f"delete_candidate_"
                            f"{candidate.id}"
                        ),
                        use_container_width=True,
                    ):

                        st.session_state[
                            "deleting_candidate_id"
                        ] = candidate.id

                        st.session_state.pop(
                            "editing_candidate_id",
                            None,
                        )

                        st.rerun()

        # ========================================================
        # DELETE CANDIDATE
        # ========================================================

        deleting_id = st.session_state.get(
            "deleting_candidate_id"
        )

        if deleting_id:

            candidate = session.get(
                Candidate,
                deleting_id,
            )

            if candidate:

                st.divider()

                st.header(
                    "Delete Candidate"
                )

                employee_name = get_employee_name(
                    candidate.employee
                )

                job_name = get_job_name(
                    candidate.job
                )

                st.write(
                    f"**Candidate:** {employee_name}"
                )

                st.write(
                    f"**Job:** {job_name}"
                )

                linked_activity_count = (
                    get_activity_count(
                        session,
                        candidate.id,
                    )
                )

                if linked_activity_count > 0:

                    st.warning(
                        "This candidate has "
                        f"**{linked_activity_count}** linked "
                        "CRM activity record(s)."
                    )

                    st.info(
                        "Deletion is blocked because the "
                        "candidate has CRM history. "
                        "Use Rejected or Withdrawn to retain "
                        "the recruitment history."
                    )

                    if st.button(
                        "Cancel",
                        key=(
                            "cancel_delete_candidate_blocked"
                        ),
                        use_container_width=True,
                    ):

                        st.session_state.pop(
                            "deleting_candidate_id",
                            None,
                        )

                        st.rerun()

                else:

                    st.warning(
                        "Are you sure you want to permanently "
                        "delete this candidate?"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "Yes, Delete Candidate",
                            key=(
                                "confirm_delete_candidate"
                            ),
                            use_container_width=True,
                        ):

                            try:

                                session.delete(
                                    candidate
                                )

                                session.commit()

                                st.session_state.pop(
                                    "deleting_candidate_id",
                                    None,
                                )

                                st.success(
                                    "Candidate deleted successfully."
                                )

                                st.rerun()

                            except Exception as error:

                                session.rollback()

                                st.error(
                                    "The candidate could "
                                    "not be deleted."
                                )

                                st.exception(
                                    error
                                )

                    with col2:

                        if st.button(
                            "Cancel",
                            key=(
                                "cancel_delete_candidate"
                            ),
                            use_container_width=True,
                        ):

                            st.session_state.pop(
                                "deleting_candidate_id",
                                None,
                            )

                            st.rerun()

        # ========================================================
        # EDIT CANDIDATE
        # ========================================================

        editing_id = st.session_state.get(
            "editing_candidate_id"
        )

        if editing_id:

            candidate = session.get(
                Candidate,
                editing_id,
            )

            if candidate:

                st.divider()

                st.header(
                    "Edit Candidate"
                )

                job_names = list(
                    job_options.keys()
                )

                employee_names = list(
                    employee_options.keys()
                )

                current_job_name = (
                    get_current_job_label(
                        job_options,
                        candidate.job_id,
                    )
                )

                current_employee_name = (
                    get_current_employee_label(
                        employee_options,
                        candidate.employee_id,
                    )
                )

                if current_job_name in job_names:

                    job_index = (
                        job_names.index(
                            current_job_name
                        )
                    )

                else:

                    job_index = 0

                if (
                    current_employee_name
                    in employee_names
                ):

                    employee_index = (
                        employee_names.index(
                            current_employee_name
                        )
                    )

                else:

                    employee_index = 0

                with st.form(
                    f"edit_candidate_form_{candidate.id}"
                ):

                    st.markdown(
                        f"Editing Candidate #{candidate.id}"
                    )

                    edit_job = st.selectbox(
                        "Job",
                        job_names,
                        index=job_index,
                    )

                    edit_employee = st.selectbox(
                        "Employee",
                        employee_names,
                        index=employee_index,
                    )

                    current_status = (
                        candidate.status
                        if candidate.status
                        in CANDIDATE_STATUSES
                        else "Submitted"
                    )

                    edit_status = st.selectbox(
                        "Status",
                        CANDIDATE_STATUSES,
                        index=(
                            CANDIDATE_STATUSES.index(
                                current_status
                            )
                        ),
                    )

                    edit_date_submitted = (
                        st.date_input(
                            "Date Submitted",
                            value=(
                                candidate.date_submitted
                                or date.today()
                            ),
                        )
                    )

                    edit_interview_scheduled = (
                        st.checkbox(
                            "Interview Scheduled",
                            value=(
                                candidate.interview_date
                                is not None
                            ),
                        )
                    )

                    edit_interview_date = None

                    if edit_interview_scheduled:

                        edit_interview_date = (
                            st.date_input(
                                "Interview Date",
                                value=(
                                    candidate.interview_date
                                    or date.today()
                                ),
                            )
                        )

                    edit_feedback = st.text_area(
                        "Client Feedback",
                        value=(
                            candidate.client_feedback
                            or ""
                        ),
                    )

                    edit_notes = st.text_area(
                        "Notes",
                        value=(
                            candidate.notes
                            or ""
                        ),
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        save = st.form_submit_button(
                            "Save Changes",
                            use_container_width=True,
                        )

                    with col2:

                        cancel = st.form_submit_button(
                            "Cancel",
                            use_container_width=True,
                        )

                    # ====================================================
                    # SAVE
                    # ====================================================

                    if save:

                        new_job_id = (
                            job_options[
                                edit_job
                            ]
                        )

                        new_employee_id = (
                            employee_options[
                                edit_employee
                            ]
                        )

                        date_error = (
                            validate_candidate_dates(
                                edit_date_submitted,
                                edit_interview_date,
                            )
                        )

                        status_error = (
                            validate_candidate_status(
                                edit_status,
                                edit_interview_date,
                            )
                        )

                        if date_error:

                            st.error(
                                date_error
                            )

                        elif status_error:

                            st.warning(
                                status_error
                            )

                        else:

                            duplicate = (
                                session.query(
                                    Candidate
                                )
                                .filter(
                                    Candidate.job_id
                                    == new_job_id,

                                    Candidate.employee_id
                                    == new_employee_id,

                                    Candidate.id
                                    != candidate.id,
                                )
                                .first()
                            )

                            if duplicate:

                                st.error(
                                    "Another candidate record "
                                    "already exists for this employee "
                                    "and job."
                                )

                            else:

                                candidate.job_id = (
                                    new_job_id
                                )

                                candidate.employee_id = (
                                    new_employee_id
                                )

                                candidate.status = (
                                    edit_status
                                )

                                candidate.date_submitted = (
                                    edit_date_submitted
                                )

                                candidate.interview_date = (
                                    edit_interview_date
                                )

                                candidate.client_feedback = (
                                    edit_feedback.strip()
                                )

                                candidate.notes = (
                                    edit_notes.strip()
                                )

                                try:

                                    session.commit()

                                    st.session_state.pop(
                                        "editing_candidate_id",
                                        None,
                                    )

                                    st.success(
                                        "Candidate updated successfully."
                                    )

                                    st.rerun()

                                except Exception as error:

                                    session.rollback()

                                    st.error(
                                        "The candidate could "
                                        "not be updated."
                                    )

                                    st.exception(
                                        error
                                    )

                    # ====================================================
                    # CANCEL
                    # ====================================================

                    if cancel:

                        st.session_state.pop(
                            "editing_candidate_id",
                            None,
                        )

                        st.rerun()

    except Exception as error:

        session.rollback()

        st.error(
            "An error occurred while loading "
            "the Candidates screen."
        )

        st.exception(
            error
        )

    finally:

        session.close()