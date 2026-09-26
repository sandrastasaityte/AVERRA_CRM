import streamlit as st
from datetime import date

from database import get_session
from models import Job, Client


def show_jobs():

    st.title("Jobs")
    st.caption("Create and manage client job requirements.")

    session = get_session()

    # ============================================================
    # SESSION STATE
    # ============================================================

    if "editing_job_id" not in st.session_state:
        st.session_state.editing_job_id = None

    if "confirm_delete_job_id" not in st.session_state:
        st.session_state.confirm_delete_job_id = None

    # ============================================================
    # LOAD DATA
    # ============================================================

    clients = session.query(Client).order_by(
        Client.company_name
    ).all()

    if not clients:
        st.warning("Please add a client first.")
        session.close()
        return

    editing_job = None

    if st.session_state.editing_job_id is not None:

        editing_job = session.get(
            Job,
            st.session_state.editing_job_id
        )

        if editing_job is None:
            st.session_state.editing_job_id = None
        else:
            st.subheader(
                f"Edit Job — {editing_job.position}"
            )

    # ============================================================
    # JOB FORM
    # ============================================================

    if editing_job is None:
        st.subheader("Create Job")

    with st.form("job_form"):

        # --------------------------------------------------------
        # CLIENT
        # --------------------------------------------------------

        client_options = {
            f"{client.company_name} (ID: {client.id})": client.id
            for client in clients
        }

        client_ids = list(client_options.values())

        if editing_job and editing_job.client_id in client_ids:
            client_index = client_ids.index(
                editing_job.client_id
            )
        else:
            client_index = 0

        selected_client = st.selectbox(
            "Client",
            list(client_options.keys()),
            index=client_index
        )

        # --------------------------------------------------------
        # JOB DETAILS
        # --------------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            position = st.text_input(
                "Position",
                value=(
                    editing_job.position
                    if editing_job
                    else ""
                ),
                placeholder="Example: Remote Finance Specialist"
            )

        with col2:

            department = st.text_input(
                "Department",
                value=(
                    editing_job.department
                    if editing_job
                    else ""
                ),
                placeholder="Example: Finance"
            )

        skills_required = st.text_area(
            "Skills Required",
            value=(
                editing_job.skills_required
                if editing_job
                else ""
            ),
            placeholder=(
                "Example: Excel, Power BI, "
                "reconciliations, treasury"
            )
        )

        experience_required = st.text_input(
            "Experience Required",
            value=(
                editing_job.experience_required
                if editing_job
                else ""
            ),
            placeholder="Example: 3+ years in finance operations"
        )

        # --------------------------------------------------------
        # BUDGET
        # --------------------------------------------------------

        st.subheader("Client Budget")

        col3, col4 = st.columns(2)

        with col3:

            client_budget = st.number_input(
                "Monthly Budget",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                value=(
                    float(editing_job.client_budget or 0.0)
                    if editing_job
                    else 0.0
                )
            )

        with col4:

            currencies = [
                "GBP",
                "EUR",
                "USD",
                "INR"
            ]

            current_currency = (
                editing_job.currency
                if editing_job
                else "GBP"
            )

            currency_index = (
                currencies.index(current_currency)
                if current_currency in currencies
                else 0
            )

            currency = st.selectbox(
                "Currency",
                currencies,
                index=currency_index
            )

        # --------------------------------------------------------
        # OPENINGS / WORK PATTERN
        # --------------------------------------------------------

        col5, col6 = st.columns(2)

        with col5:

            openings = st.number_input(
                "Number of Openings",
                min_value=1,
                step=1,
                value=(
                    editing_job.openings
                    if editing_job
                    else 1
                )
            )

        with col6:

            work_patterns = [
                "Full-time",
                "Part-time",
                "Contract",
                "Temporary"
            ]

            current_work_pattern = (
                editing_job.work_pattern
                if editing_job
                else "Full-time"
            )

            work_pattern_index = (
                work_patterns.index(current_work_pattern)
                if current_work_pattern in work_patterns
                else 0
            )

            work_pattern = st.selectbox(
                "Work Pattern",
                work_patterns,
                index=work_pattern_index
            )

        # --------------------------------------------------------
        # LOCATION
        # --------------------------------------------------------

        remote_country = st.text_input(
            "Remote Country",
            value=(
                editing_job.remote_country
                if editing_job
                else "India"
            ),
            placeholder="Example: India"
        )

        # --------------------------------------------------------
        # DATES
        # --------------------------------------------------------

        col7, col8 = st.columns(2)

        with col7:

            date_opened = st.date_input(
                "Date Opened",
                value=(
                    editing_job.date_opened
                    if editing_job and editing_job.date_opened
                    else date.today()
                )
            )

        with col8:

            closing_date = st.date_input(
                "Closing Date",
                value=(
                    editing_job.closing_date
                    if editing_job and editing_job.closing_date
                    else date.today()
                )
            )

        # --------------------------------------------------------
        # STATUS / PRIORITY
        # --------------------------------------------------------

        col9, col10 = st.columns(2)

        with col9:

            statuses = [
                "Open",
                "On Hold",
                "Closed",
                "Filled",
                "Cancelled"
            ]

            current_status = (
                editing_job.status
                if editing_job
                else "Open"
            )

            status_index = (
                statuses.index(current_status)
                if current_status in statuses
                else 0
            )

            status = st.selectbox(
                "Job Status",
                statuses,
                index=status_index
            )

        with col10:

            priorities = [
                "Low",
                "Medium",
                "High",
                "Urgent"
            ]

            current_priority = (
                editing_job.priority
                if editing_job
                else "Medium"
            )

            priority_index = (
                priorities.index(current_priority)
                if current_priority in priorities
                else 1
            )

            priority = st.selectbox(
                "Priority",
                priorities,
                index=priority_index
            )

        # --------------------------------------------------------
        # NOTES
        # --------------------------------------------------------

        notes = st.text_area(
            "Notes",
            value=(
                editing_job.notes
                if editing_job
                else ""
            ),
            placeholder="Additional job information..."
        )

        # --------------------------------------------------------
        # BUTTON
        # --------------------------------------------------------

        submitted = st.form_submit_button(
            "Save Changes"
            if editing_job
            else "Create Job",
            use_container_width=True
        )

        # ========================================================
        # SAVE
        # ========================================================

        if submitted:

            if not position.strip():

                st.error(
                    "Position is required."
                )

            elif closing_date < date_opened:

                st.error(
                    "Closing date cannot be before the opening date."
                )

            else:

                selected_client_id = client_options[
                    selected_client
                ]

                if editing_job:

                    editing_job.client_id = selected_client_id
                    editing_job.position = position.strip()
                    editing_job.department = department.strip()
                    editing_job.skills_required = skills_required.strip()
                    editing_job.experience_required = experience_required.strip()
                    editing_job.client_budget = client_budget
                    editing_job.currency = currency
                    editing_job.openings = openings
                    editing_job.work_pattern = work_pattern
                    editing_job.remote_country = remote_country.strip()
                    editing_job.date_opened = date_opened
                    editing_job.closing_date = closing_date
                    editing_job.status = status
                    editing_job.priority = priority
                    editing_job.notes = notes.strip()

                    session.commit()

                    st.success(
                        "Job updated successfully."
                    )

                    st.session_state.editing_job_id = None

                    st.rerun()

                else:

                    job = Job(
                        client_id=selected_client_id,
                        position=position.strip(),
                        department=department.strip(),
                        skills_required=skills_required.strip(),
                        experience_required=experience_required.strip(),
                        client_budget=client_budget,
                        currency=currency,
                        openings=openings,
                        work_pattern=work_pattern,
                        remote_country=remote_country.strip(),
                        date_opened=date_opened,
                        closing_date=closing_date,
                        status=status,
                        priority=priority,
                        notes=notes.strip()
                    )

                    session.add(job)
                    session.commit()

                    st.success(
                        "Job created successfully."
                    )

                    st.rerun()

    # ============================================================
    # JOB REGISTER
    # ============================================================

    st.divider()

    st.subheader("Job Register")

    jobs = session.query(Job).order_by(
        Job.date_opened.desc(),
        Job.id.desc()
    ).all()

    if not jobs:

        st.info(
            "No jobs have been created yet."
        )

        session.close()
        return

    # ============================================================
    # FILTERS
    # ============================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        search = st.text_input(
            "Search",
            placeholder="Position, client or department..."
        )

    with col2:

        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Open",
                "On Hold",
                "Closed",
                "Filled",
                "Cancelled"
            ]
        )

    with col3:

        priority_filter = st.selectbox(
            "Priority",
            [
                "All",
                "Low",
                "Medium",
                "High",
                "Urgent"
            ]
        )

    # ============================================================
    # APPLY FILTERS
    # ============================================================

    filtered_jobs = jobs

    if search:

        search_lower = search.lower()

        filtered_jobs = [
            job
            for job in filtered_jobs
            if (
                search_lower
                in (job.position or "").lower()
            )
            or (
                search_lower
                in (job.department or "").lower()
            )
            or (
                job.client
                and search_lower
                in (job.client.company_name or "").lower()
            )
        ]

    if status_filter != "All":

        filtered_jobs = [
            job
            for job in filtered_jobs
            if job.status == status_filter
        ]

    if priority_filter != "All":

        filtered_jobs = [
            job
            for job in filtered_jobs
            if job.priority == priority_filter
        ]

    # ============================================================
    # DISPLAY JOBS
    # ============================================================

    if not filtered_jobs:

        st.info(
            "No jobs match your filters."
        )

    else:

        for job in filtered_jobs:

            client_name = (
                job.client.company_name
                if job.client
                else "Unknown Client"
            )

            candidate_count = (
                len(job.candidates)
                if hasattr(job, "candidates")
                and job.candidates
                else 0
            )

            placement_count = (
                len(job.placements)
                if hasattr(job, "placements")
                and job.placements
                else 0
            )

            with st.container(border=True):

                col1, col2, col3, col4, col5 = st.columns(
                    [2, 3, 2, 2, 2]
                )

                # ------------------------------------------------
                # JOB
                # ------------------------------------------------

                with col1:

                    st.write(
                        f"**#{job.id} — {job.position}**"
                    )

                    st.caption(
                        job.department or "No department"
                    )

                # ------------------------------------------------
                # CLIENT
                # ------------------------------------------------

                with col2:

                    st.write(
                        f"**{client_name}**"
                    )

                    st.caption(
                        f"{job.openings} opening(s)"
                    )

                # ------------------------------------------------
                # BUDGET
                # ------------------------------------------------

                with col3:

                    st.write(
                        f"Budget: **"
                        f"{job.currency} "
                        f"{job.client_budget or 0:,.2f}"
                        f"**"
                    )

                    st.caption(
                        job.work_pattern or ""
                    )

                # ------------------------------------------------
                # STATUS
                # ------------------------------------------------

                with col4:

                    st.write(
                        f"Status: **{job.status}**"
                    )

                    st.write(
                        f"Priority: **{job.priority}**"
                    )

                # ------------------------------------------------
                # ACTIVITY
                # ------------------------------------------------

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
                        use_container_width=True
                    )

                    delete_btn = st.button(
                        "Delete",
                        key=f"delete_job_{job.id}",
                        use_container_width=True
                    )

                # ------------------------------------------------
                # EDIT
                # ------------------------------------------------

                if edit_btn:

                    st.session_state.editing_job_id = job.id
                    st.rerun()

                # ------------------------------------------------
                # DELETE
                # ------------------------------------------------

                if delete_btn:

                    st.session_state.confirm_delete_job_id = job.id
                    st.rerun()

                # ------------------------------------------------
                # DELETE CONFIRMATION
                # ------------------------------------------------

                if (
                    st.session_state.confirm_delete_job_id
                    == job.id
                ):

                    has_candidates = (
                        hasattr(job, "candidates")
                        and len(job.candidates) > 0
                    )

                    has_placements = (
                        hasattr(job, "placements")
                        and len(job.placements) > 0
                    )

                    if has_candidates or has_placements:

                        st.warning(
                            "This job cannot be deleted because "
                            "it has candidates or placements."
                        )

                        if st.button(
                            "Close",
                            key=f"close_delete_{job.id}"
                        ):

                            st.session_state.confirm_delete_job_id = None
                            st.rerun()

                    else:

                        st.warning(
                            f"Are you sure you want to delete "
                            f"job #{job.id}?"
                        )

                        confirm_col1, confirm_col2 = st.columns(2)

                        with confirm_col1:

                            confirm_delete = st.button(
                                "Yes, Delete Job",
                                key=f"confirm_job_{job.id}",
                                type="primary",
                                use_container_width=True
                            )

                        with confirm_col2:

                            cancel_delete = st.button(
                                "Cancel",
                                key=f"cancel_job_{job.id}",
                                use_container_width=True
                            )

                        if cancel_delete:

                            st.session_state.confirm_delete_job_id = None
                            st.rerun()

                        if confirm_delete:

                            session.delete(job)
                            session.commit()

                            st.success(
                                "Job deleted successfully."
                            )

                            st.session_state.confirm_delete_job_id = None

                            st.rerun()

                # ------------------------------------------------
                # ADDITIONAL DETAILS
                # ------------------------------------------------

                with st.expander("View Job Details"):

                    st.write(
                        f"**Skills Required:** "
                        f"{job.skills_required or 'Not specified'}"
                    )

                    st.write(
                        f"**Experience Required:** "
                        f"{job.experience_required or 'Not specified'}"
                    )

                    st.write(
                        f"**Remote Country:** "
                        f"{job.remote_country or 'Not specified'}"
                    )

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

                    if job.notes:

                        st.write(
                            f"**Notes:** {job.notes}"
                        )

    # ============================================================
    # CLOSE SESSION
    # ============================================================

    session.close()