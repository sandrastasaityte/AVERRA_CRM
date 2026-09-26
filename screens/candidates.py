```python
import streamlit as st
from datetime import date

from database import get_session
from models import Candidate, Employee, Job


CANDIDATE_STATUSES = [
    "New",
    "Screening",
    "Interviewing",
    "Shortlisted",
    "Offered",
    "Placed",
    "Unavailable",
    "Rejected",
    "Inactive"
]


def show_candidates():

    st.title("Candidates")
    st.caption(
        "Manage employee submissions to client jobs, recruitment stages and candidate decisions."
    )

    session = get_session()

    # ============================================================
    # GET EMPLOYEES AND JOBS
    # ============================================================

    employees = (
        session.query(Employee)
        .order_by(Employee.first_name, Employee.last_name)
        .all()
    )

    jobs = (
        session.query(Job)
        .order_by(Job.position)
        .all()
    )

    # ============================================================
    # ADD CANDIDATE
    # ============================================================

    st.subheader("Submit Candidate")

    if not employees:
        st.warning(
            "No employees exist yet. Add an employee before submitting a candidate."
        )

    elif not jobs:
        st.warning(
            "No jobs exist yet. Add a job before submitting a candidate."
        )

    else:

        employee_options = {
            f"{employee.first_name} {employee.last_name} "
            f"({employee.role or 'No role'})": employee.id
            for employee in employees
        }

        job_options = {
            f"{job.position} — {job.client.company_name}": job.id
            for job in jobs
        }

        with st.form("add_candidate_form"):

            col1, col2 = st.columns(2)

            with col1:

                selected_employee = st.selectbox(
                    "Employee / Candidate",
                    list(employee_options.keys())
                )

                date_submitted = st.date_input(
                    "Date Submitted",
                    value=date.today()
                )

                status = st.selectbox(
                    "Status",
                    CANDIDATE_STATUSES
                )

            with col2:

                selected_job = st.selectbox(
                    "Job",
                    list(job_options.keys())
                )

                interview_date = st.date_input(
                    "Interview Date",
                    value=None
                )

                decision_date = st.date_input(
                    "Decision Date",
                    value=None
                )

            client_feedback = st.text_area(
                "Client Feedback",
                placeholder="Enter feedback received from the client..."
            )

            notes = st.text_area(
                "Notes",
                placeholder="Recruitment notes, interview details, next steps..."
            )

            submitted = st.form_submit_button(
                "Submit Candidate",
                use_container_width=True
            )

            if submitted:

                employee_id = employee_options[selected_employee]
                job_id = job_options[selected_job]

                # ------------------------------------------------
                # CHECK FOR DUPLICATE SUBMISSION
                # ------------------------------------------------

                duplicate = (
                    session.query(Candidate)
                    .filter(
                        Candidate.employee_id == employee_id,
                        Candidate.job_id == job_id
                    )
                    .first()
                )

                if duplicate:
                    st.error(
                        "This employee has already been submitted for this job."
                    )

                else:

                    candidate = Candidate(
                        employee_id=employee_id,
                        job_id=job_id,
                        date_submitted=date_submitted,
                        status=status,
                        interview_date=interview_date,
                        client_feedback=client_feedback.strip(),
                        decision_date=decision_date,
                        notes=notes.strip()
                    )

                    session.add(candidate)
                    session.commit()

                    st.success(
                        "Candidate submitted successfully."
                    )

                    st.rerun()

    st.divider()

    # ============================================================
    # CANDIDATE REGISTER
    # ==========
```
