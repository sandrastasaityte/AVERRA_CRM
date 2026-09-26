import streamlit as st

from database import get_session
from models import Candidate, Job, Employee, Client


def show_candidates():

    st.title("Candidates")
    st.caption("Manage employee submissions and recruitment pipeline.")

    session = get_session()

    # ============================================================
    # ADD CANDIDATE
    # ============================================================

    st.header("Submit Candidate")

    jobs = (
        session.query(Job)
        .join(Client)
        .order_by(Job.date_opened.desc())
        .all()
    )

    employees = (
        session.query(Employee)
        .order_by(
            Employee.first_name.asc(),
            Employee.last_name.asc()
        )
        .all()
    )

    if not jobs:

        st.info(
            "Please create a Job before submitting a candidate."
        )

        session.close()
        return

    if not employees:

        st.info(
            "Please add an Employee before submitting a candidate."
        )

        session.close()
        return

    job_options = {
        f"{job.position} - {job.client.company_name}": job.id
        for job in jobs
    }

    employee_options = {
        (
            f"{employee.first_name} "
            f"{employee.last_name} - "
            f"{employee.role or 'No role'}"
        ): employee.id
        for employee in employees
    }

    with st.form("add_candidate_form"):

        selected_job = st.selectbox(
            "Job *",
            list(job_options.keys())
        )

        selected_employee = st.selectbox(
            "Employee *",
            list(employee_options.keys())
        )

        date_submitted = st.date_input(
            "Date Submitted"
        )

        status = st.selectbox(
            "Candidate Status",
            [
                "Submitted",
                "Shortlisted",
                "Interview",
                "Offer",
                "Placed",
                "Rejected",
                "Withdrawn"
            ]
        )

        interview_date = st.date_input(
            "Interview Date",
            value=None
        )

        client_feedback = st.text_area(
            "Client Feedback"
        )

        notes = st.text_area(
            "Notes"
        )

        submitted = st.form_submit_button(
            "Submit Candidate",
            use_container_width=True
        )

        if submitted:

            job_id = job_options[selected_job]

            employee_id = employee_options[
                selected_employee
            ]

            candidate = Candidate(
                job_id=job_id,
                employee_id=employee_id,
                date_submitted=date_submitted,
                status=status,
                interview_date=interview_date,
                client_feedback=client_feedback.strip(),
                notes=notes.strip()
            )

            session.add(candidate)
            session.commit()

            st.success(
                "Candidate submitted successfully."
            )

            st.rerun()

    # ============================================================
    # CANDIDATE REGISTER
    # ============================================================

    st.divider()

    st.header("Candidate Register")

    candidates = (
        session.query(Candidate)
        .order_by(
            Candidate.date_submitted.desc()
        )
        .all()
    )

    if not candidates:

        st.info(
            "No candidates have been submitted yet."
        )

        session.close()
        return

    # ============================================================
    # FILTERS
    # ============================================================

    col1, col2 = st.columns(2)

    with col1:

        search = st.text_input(
            "Search",
            placeholder="Candidate, job or company..."
        )

    with col2:

        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Submitted",
                "Shortlisted",
                "Interview",
                "Offer",
                "Placed",
                "Rejected",
                "Withdrawn"
            ]
        )

    # ============================================================
    # APPLY FILTERS
    # ============================================================

    filtered_candidates = candidates

    if search:

        search_text = search.lower()

        filtered_candidates = [
            candidate
            for candidate in filtered_candidates
            if (
                search_text
                in (
                    f"{candidate.employee.first_name if candidate.employee else ''} "
                    f"{candidate.employee.last_name if candidate.employee else ''}"
                ).lower()
                or search_text
                in (
                    candidate.job.position
                    if candidate.job
                    else ""
                ).lower()
                or search_text
                in (
                    candidate.job.client.company_name
                    if candidate.job and candidate.job.client
                    else ""
                ).lower()
            )
        ]

    if status_filter != "All":

        filtered_candidates = [
            candidate
            for candidate in filtered_candidates
            if candidate.status == status_filter
        ]

    st.write(
        f"Showing **{len(filtered_candidates)}** candidate(s)"
    )

    # ============================================================
    # DISPLAY CANDIDATES
    # ============================================================

    for candidate in filtered_candidates:

        with st.container(border=True):

            col1, col2, col3, col4 = st.columns(
                [3, 3, 2, 1]
            )

            # ----------------------------------------------------
            # CANDIDATE
            # ----------------------------------------------------

            with col1:

                if candidate.employee:

                    employee_name = " ".join(
                        part
                        for part in [
                            candidate.employee.first_name,
                            candidate.employee.last_name
                        ]
                        if part
                    )

                    st.subheader(
                        employee_name
                    )

                    if candidate.employee.role:

                        st.write(
                            candidate.employee.role
                        )

                else:

                    st.subheader(
                        "Unknown Employee"
                    )

            # ----------------------------------------------------
            # JOB
            # ----------------------------------------------------

            with col2:

                st.write("**Job**")

                if candidate.job:

                    st.write(
                        candidate.job.position
                    )

                    if candidate.job.client:

                        st.caption(
                            candidate.job.client.company_name
                        )

                else:

                    st.write("—")

            # ----------------------------------------------------
            # STATUS
            # ----------------------------------------------------

            with col3:

                st.write("**Status**")

                st.write(
                    candidate.status or "—"
                )

                if candidate.date_submitted:

                    st.caption(
                        f"Submitted: "
                        f"{candidate.date_submitted}"
                    )

                if candidate.interview_date:

                    st.caption(
                        f"Interview: "
                        f"{candidate.interview_date}"
                    )

            # ----------------------------------------------------
            # EDIT
            # ----------------------------------------------------

            with col4:

                if st.button(
                    "Edit",
                    key=f"edit_candidate_{candidate.id}"
                ):

                    st.session_state[
                        "editing_candidate_id"
                    ] = candidate.id

                    st.rerun()

            if candidate.client_feedback:

                st.caption(
                    f"Client Feedback: "
                    f"{candidate.client_feedback}"
                )

            if candidate.notes:

                st.caption(
                    f"Notes: {candidate.notes}"
                )

    # ============================================================
    # EDIT CANDIDATE
    # ============================================================

    editing_id = st.session_state.get(
        "editing_candidate_id"
    )

    if editing_id:

        candidate = session.get(
            Candidate,
            editing_id
        )

        if candidate:

            st.divider()

            st.header(
                "Edit Candidate"
            )

            with st.form(
                f"edit_candidate_form_{candidate.id}"
            ):

                job_names = list(
                    job_options.keys()
                )

                current_job_name = None

                for name, job_id in job_options.items():

                    if job_id == candidate.job_id:

                        current_job_name = name
                        break

                if current_job_name in job_names:

                    job_index = job_names.index(
                        current_job_name
                    )

                else:

                    job_index = 0

                employee_names = list(
                    employee_options.keys()
                )

                current_employee_name = None

                for name, employee_id in employee_options.items():

                    if employee_id == candidate.employee_id:

                        current_employee_name = name
                        break

                if current_employee_name in employee_names:

                    employee_index = employee_names.index(
                        current_employee_name
                    )

                else:

                    employee_index = 0

                edit_job = st.selectbox(
                    "Job",
                    job_names,
                    index=job_index
                )

                edit_employee = st.selectbox(
                    "Employee",
                    employee_names,
                    index=employee_index
                )

                edit_statuses = [
                    "Submitted",
                    "Shortlisted",
                    "Interview",
                    "Offer",
                    "Placed",
                    "Rejected",
                    "Withdrawn"
                ]

                current_status = (
                    candidate.status
                    if candidate.status in edit_statuses
                    else "Submitted"
                )

                edit_status = st.selectbox(
                    "Status",
                    edit_statuses,
                    index=edit_statuses.index(
                        current_status
                    )
                )

                edit_date_submitted = st.date_input(
                    "Date Submitted",
                    value=candidate.date_submitted
                )

                edit_interview_date = st.date_input(
                    "Interview Date",
                    value=candidate.interview_date
                )

                edit_feedback = st.text_area(
                    "Client Feedback",
                    value=candidate.client_feedback or ""
                )

                edit_notes = st.text_area(
                    "Notes",
                    value=candidate.notes or ""
                )

                save = st.form_submit_button(
                    "Save Changes",
                    use_container_width=True
                )

                if save:

                    candidate.job_id = job_options[
                        edit_job
                    ]

                    candidate.employee_id = employee_options[
                        edit_employee
                    ]

                    candidate.status = edit_status

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
                        None
                    )

                    st.success(
                        "Candidate updated successfully."
                    )

                    st.rerun()

            if st.button(
                "Cancel",
                key=f"cancel_candidate_{candidate.id}"
            ):

                st.session_state.pop(
                    "editing_candidate_id",
                    None
                )

                st.rerun()

    session.close()