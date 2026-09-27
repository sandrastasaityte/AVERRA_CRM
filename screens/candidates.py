
import streamlit as st
from datetime import date

from database import get_session
from models import Candidate, Job, Employee


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


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_employee_name(employee):

    if not employee:
        return "Unknown Employee"

    return " ".join(
        part
        for part in [
            employee.first_name,
            employee.last_name,
        ]
        if part
    ).strip() or f"Employee #{employee.id}"


def get_job_name(job):

    if not job:
        return "Unknown Job"

    position = job.position or f"Job #{job.id}"

    if job.client:
        return (
            f"{position} - "
            f"{job.client.company_name}"
        )

    return f"{position} - No Client"


def get_candidate_search_text(candidate):

    employee_name = get_employee_name(
        candidate.employee
    )

    job_name = ""

    if candidate.job:
        job_name = candidate.job.position or ""

    company_name = ""

    if candidate.job and candidate.job.client:
        company_name = (
            candidate.job.client.company_name
            or ""
        )

    return " ".join(
        [
            employee_name,
            job_name,
            company_name,
            candidate.status or "",
            candidate.client_feedback or "",
            candidate.notes or "",
        ]
    ).lower()


def interview_status(candidate):

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
                Job.date_opened.desc()
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
            )
            .all()
        )

        # ========================================================
        # CREATE JOB OPTIONS
        # ========================================================

        job_options = {
            get_job_name(job): job.id
            for job in jobs
        }

        # ========================================================
        # CREATE EMPLOYEE OPTIONS
        # ========================================================

        employee_options = {}

        for employee in employees:

            employee_name = get_employee_name(
                employee
            )

            role = employee.role or "No role"

            employee_options[
                f"{employee_name} - {role}"
            ] = employee.id

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

            with st.form("add_candidate_form"):

                # ====================================================
                # BASIC INFORMATION
                # ====================================================

                col1, col2 = st.columns(2)

                with col1:

                    selected_job = st.selectbox(
                        "Job *",
                        list(job_options.keys()),
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
                        list(employee_options.keys()),
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

                # ====================================================
                # CLIENT FEEDBACK
                # ====================================================

                client_feedback = st.text_area(
                    "Client Feedback",
                    placeholder=(
                        "Enter feedback received from the client..."
                    ),
                )

                # ====================================================
                # INTERNAL NOTES
                # ====================================================

                notes = st.text_area(
                    "Notes",
                    placeholder=(
                        "Internal recruitment notes..."
                    ),
                )

                # ====================================================
                # SUBMIT BUTTON
                # ====================================================

                submitted = st.form_submit_button(
                    "Submit Candidate",
                    use_container_width=True,
                )

                if submitted:

                    job_id = job_options[
                        selected_job
                    ]

                    employee_id = employee_options[
                        selected_employee
                    ]

                    # ================================================
                    # DUPLICATE CHECK
                    # ================================================

                    existing_candidate = (
                        session.query(Candidate)
                        .filter(
                            Candidate.job_id == job_id,
                            Candidate.employee_id == employee_id,
                        )
                        .first()
                    )

                    if existing_candidate:

                        st.warning(
                            "This employee has already been submitted "
                            "for this job."
                        )

                    else:

                        candidate = Candidate(
                            job_id=job_id,
                            employee_id=employee_id,
                            date_submitted=date_submitted,
                            status=status,
                            interview_date=interview_date,
                            client_feedback=(
                                client_feedback.strip()
                            ),
                            notes=notes.strip(),
                        )

                        session.add(candidate)
                        session.commit()

                        st.success(
                            "Candidate submitted successfully."
                        )

                        st.rerun()

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

        total_candidates = len(candidates)

        submitted_count = sum(
            1
            for candidate in candidates
            if candidate.status == "Submitted"
        )

        shortlisted_count = sum(
            1
            for candidate in candidates
            if candidate.status == "Shortlisted"
        )

        interview_count = sum(
            1
            for candidate in candidates
            if candidate.status == "Interview"
        )

        offer_count = sum(
            1
            for candidate in candidates
            if candidate.status == "Offer"
        )

        placed_count = sum(
            1
            for candidate in candidates
            if candidate.status == "Placed"
        )

        # ========================================================
        # SUMMARY DISPLAY
        # ========================================================

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:

            st.metric(
                "Total",
                total_candidates,
            )

        with col2:

            st.metric(
                "Submitted",
                submitted_count,
            )

        with col3:

            st.metric(
                "Shortlisted",
                shortlisted_count,
            )

        with col4:

            st.metric(
                "Interview",
                interview_count,
            )

        with col5:

            st.metric(
                "Offer",
                offer_count,
            )

        with col6:

            st.metric(
                "Placed",
                placed_count,
            )

        # ========================================================
        # FILTERS
        # ========================================================

        st.subheader("Filters")

        col1, col2, col3 = st.columns(3)

        with col1:

            search = st.text_input(
                "Search",
                placeholder=(
                    "Employee, job, company, notes..."
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
                [
                    "All",
                    "Today",
                    "Upcoming",
                    "Past",
                    "No Interview",
                ],
            )

        # ========================================================
        # APPLY SEARCH FILTER
        # ========================================================

        filtered_candidates = candidates

        if search:

            search_text = search.strip().lower()

            filtered_candidates = [
                candidate
                for candidate in filtered_candidates
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
                for candidate in filtered_candidates
                if candidate.status == status_filter
            ]

        # ========================================================
        # APPLY INTERVIEW FILTER
        # ========================================================

        if interview_filter != "All":

            if interview_filter == "No Interview":

                filtered_candidates = [
                    candidate
                    for candidate in filtered_candidates
                    if not candidate.interview_date
                ]

            else:

                filtered_candidates = [
                    candidate
                    for candidate in filtered_candidates
                    if interview_status(candidate)
                    == interview_filter
                ]

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

            company_name = ""

            if (
                candidate.job
                and candidate.job.client
            ):

                company_name = (
                    candidate.job.client.company_name
                    or ""
                )

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(
                    [3, 3, 2, 1]
                )

                # ====================================================
                # CANDIDATE
                # ====================================================

                with col1:

                    st.subheader(
                        employee_name
                    )

                    if candidate.employee:

                        if candidate.employee.role:

                            st.caption(
                                candidate.employee.role
                            )

                # ====================================================
                # JOB
                # ====================================================

                with col2:

                    st.write("**Job**")

                    st.write(
                        job_name
                    )

                    if company_name:

                        st.caption(
                            company_name
                        )

                # ====================================================
                # STATUS
                # ====================================================

                with col3:

                    st.write("**Status**")

                    st.write(
                        candidate.status or "—"
                    )

                    if candidate.date_submitted:

                        st.caption(
                            "Submitted: "
                            f"{candidate.date_submitted}"
                        )

                    if candidate.interview_date:

                        interview_state = (
                            interview_status(
                                candidate
                            )
                        )

                        st.caption(
                            "Interview: "
                            f"{candidate.interview_date}"
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

                # ====================================================
                # ACTIONS
                # ====================================================

                with col4:

                    if st.button(
                        "Edit",
                        key=(
                            f"edit_candidate_"
                            f"{candidate.id}"
                        ),
                    ):

                        st.session_state[
                            "editing_candidate_id"
                        ] = candidate.id

                        st.session_state.pop(
                            "deleting_candidate_id",
                            None,
                        )

                        st.rerun()

                    if st.button(
                        "Delete",
                        key=(
                            f"delete_candidate_"
                            f"{candidate.id}"
                        ),
                    ):

                        st.session_state[
                            "deleting_candidate_id"
                        ] = candidate.id

                        st.session_state.pop(
                            "editing_candidate_id",
                            None,
                        )

                        st.rerun()

                # ====================================================
                # DETAILS
                # ====================================================

                if candidate.client_feedback:

                    st.caption(
                        "Client Feedback: "
                        f"{candidate.client_feedback}"
                    )

                if candidate.notes:

                    st.caption(
                        f"Notes: {candidate.notes}"
                    )

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

                st.warning(
                    "Are you sure you want to delete this candidate?"
                )

                employee_name = get_employee_name(
                    candidate.employee
                )

                st.write(
                    f"**Candidate:** {employee_name}"
                )

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "Yes, Delete Candidate",
                        key="confirm_delete_candidate",
                        use_container_width=True,
                    ):

                        session.delete(candidate)
                        session.commit()

                        st.session_state.pop(
                            "deleting_candidate_id",
                            None,
                        )

                        st.success(
                            "Candidate deleted successfully."
                        )

                        st.rerun()

                with col2:

                    if st.button(
                        "Cancel",
                        key="cancel_delete_candidate",
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

                st.header("Edit Candidate")

                # ====================================================
                # JOB OPTIONS
                # ====================================================

                job_names = list(
                    job_options.keys()
                )

                employee_names = list(
                    employee_options.keys()
                )

                # ====================================================
                # CURRENT JOB
                # ====================================================

                current_job_name = None

                for name, job_id in job_options.items():

                    if job_id == candidate.job_id:

                        current_job_name = name
                        break

                if (
                    current_job_name
                    in job_names
                ):

                    job_index = job_names.index(
                        current_job_name
                    )

                else:

                    job_index = 0

                # ====================================================
                # CURRENT EMPLOYEE
                # ====================================================

                current_employee_name = None

                for (
                    name,
                    employee_id,
                ) in employee_options.items():

                    if (
                        employee_id
                        == candidate.employee_id
                    ):

                        current_employee_name = name
                        break

                if (
                    current_employee_name
                    in employee_names
                ):

                    employee_index = employee_names.index(
                        current_employee_name
                    )

                else:

                    employee_index = 0

                # ====================================================
                # EDIT FORM
                # ====================================================

                with st.form(
                    f"edit_candidate_form_{candidate.id}"
                ):

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
                        index=CANDIDATE_STATUSES.index(
                            current_status
                        ),
                    )

                    edit_date_submitted = st.date_input(
                        "Date Submitted",
                        value=(
                            candidate.date_submitted
                            or date.today()
                        ),
                    )

                    edit_interview_scheduled = st.checkbox(
                        "Interview Scheduled",
                        value=(
                            candidate.interview_date
                            is not None
                        ),
                    )

                    edit_interview_date = None

                    if edit_interview_scheduled:

                        edit_interview_date = st.date_input(
                            "Interview Date",
                            value=(
                                candidate.interview_date
                                or date.today()
                            ),
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
                    # SAVE CHANGES
                    # ====================================================

                    if save:

                        new_job_id = job_options[
                            edit_job
                        ]

                        new_employee_id = (
                            employee_options[
                                edit_employee
                            ]
                        )

                        # ================================================
                        # DUPLICATE CHECK
                        # ================================================

                        duplicate = (
                            session.query(Candidate)
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
                                "Another candidate record already "
                                "exists for this employee and job."
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

                            session.commit()

                            st.session_state.pop(
                                "editing_candidate_id",
                                None,
                            )

                            st.success(
                                "Candidate updated successfully."
                            )

                            st.rerun()

                    # ====================================================
                    # CANCEL EDIT
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
            "An error occurred while loading the Candidates screen."
        )

        st.exception(error)

    finally:

        session.close()
