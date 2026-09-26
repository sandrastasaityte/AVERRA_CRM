import streamlit as st
from database import get_session
from models import Activity


def show_activities():

    st.title("Activities")
    st.caption(
        "Manage calls, emails, meetings, follow-ups and tasks."
    )

    session = get_session()

    # ============================================================
    # GET RELATED MODELS FROM ACTIVITY RELATIONSHIPS
    # ============================================================

    Client = Activity.client.property.mapper.class_
    ClientContact = Activity.contact.property.mapper.class_
    Employee = Activity.assigned_to.property.mapper.class_
    Job = Activity.job.property.mapper.class_
    Candidate = Activity.candidate.property.mapper.class_
    Placement = Activity.placement.property.mapper.class_
    Contract = Activity.contract.property.mapper.class_

    # ============================================================
    # LOAD DATA
    # ============================================================

    clients = (
        session.query(Client)
        .order_by(Client.company_name.asc())
        .all()
    )

    contacts = (
        session.query(ClientContact)
        .order_by(
            ClientContact.first_name.asc(),
            ClientContact.last_name.asc()
        )
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

    jobs = (
        session.query(Job)
        .order_by(Job.position.asc())
        .all()
    )

    candidates = (
        session.query(Candidate)
        .order_by(Candidate.id.desc())
        .all()
    )

    placements = (
        session.query(Placement)
        .order_by(Placement.id.desc())
        .all()
    )

    contracts = (
        session.query(Contract)
        .order_by(Contract.id.desc())
        .all()
    )

    # ============================================================
    # ADD ACTIVITY
    # ============================================================

    st.header("Add Activity")

    client_options = {
        client.company_name: client.id
        for client in clients
    }

    contact_options = {
        f"{contact.first_name} {contact.last_name}": contact.id
        for contact in contacts
    }

    employee_options = {
        f"{employee.first_name} {employee.last_name}": employee.id
        for employee in employees
    }

    job_options = {
        f"{job.position} - "
        f"{job.client.company_name if job.client else 'No Client'}": job.id
        for job in jobs
    }

    candidate_options = {
        f"Candidate #{candidate.id}": candidate.id
        for candidate in candidates
    }

    placement_options = {}

    for placement in placements:

        if placement.employee:

            employee_name = " ".join(
                part
                for part in [
                    placement.employee.first_name,
                    placement.employee.last_name
                ]
                if part
            )

            placement_name = (
                f"{placement.position} - {employee_name}"
            )

        else:

            placement_name = (
                f"Placement #{placement.id}"
            )

        placement_options[placement_name] = placement.id

    contract_options = {
        f"{contract.contract_number} - "
        f"{contract.client.company_name if contract.client else 'No Client'}": contract.id
        for contract in contracts
    }

    # ============================================================
    # ACTIVITY FORM
    # ============================================================

    with st.form("add_activity_form"):

        col1, col2 = st.columns(2)

        # --------------------------------------------------------
        # LEFT COLUMN
        # --------------------------------------------------------

        with col1:

            activity_type = st.selectbox(
                "Activity Type",
                [
                    "Call",
                    "Email",
                    "Meeting",
                    "Follow-up",
                    "Task",
                    "Note",
                    "Interview",
                    "Other"
                ]
            )

            subject = st.text_input(
                "Subject *"
            )

            activity_date = st.date_input(
                "Activity Date"
            )

            due_date = st.date_input(
                "Due Date"
            )

        # --------------------------------------------------------
        # RIGHT COLUMN
        # --------------------------------------------------------

        with col2:

            status = st.selectbox(
                "Status",
                [
                    "Open",
                    "In Progress",
                    "Completed",
                    "Cancelled"
                ]
            )

            priority = st.selectbox(
                "Priority",
                [
                    "Low",
                    "Normal",
                    "High",
                    "Urgent"
                ]
            )

            assigned_to = st.selectbox(
                "Assigned To",
                ["Unassigned"] + list(
                    employee_options.keys()
                )
            )

            client = st.selectbox(
                "Client",
                ["No Client"] + list(
                    client_options.keys()
                )
            )

        # --------------------------------------------------------
        # CONTACT / JOB
        # --------------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            contact = st.selectbox(
                "Contact",
                ["No Contact"] + list(
                    contact_options.keys()
                )
            )

            job = st.selectbox(
                "Job",
                ["No Job"] + list(
                    job_options.keys()
                )
            )

        # --------------------------------------------------------
        # CANDIDATE / PLACEMENT
        # --------------------------------------------------------

        with col2:

            candidate = st.selectbox(
                "Candidate",
                ["No Candidate"] + list(
                    candidate_options.keys()
                )
            )

            placement = st.selectbox(
                "Placement",
                ["No Placement"] + list(
                    placement_options.keys()
                )
            )

        # --------------------------------------------------------
        # CONTRACT
        # --------------------------------------------------------

        contract = st.selectbox(
            "Contract",
            ["No Contract"] + list(
                contract_options.keys()
            )
        )

        # --------------------------------------------------------
        # NOTES
        # --------------------------------------------------------

        notes = st.text_area(
            "Notes"
        )

        # --------------------------------------------------------
        # SUBMIT
        # --------------------------------------------------------

        submitted = st.form_submit_button(
            "Create Activity",
            use_container_width=True
        )

        if submitted:

            if not subject.strip():

                st.error(
                    "Subject is required."
                )

            else:

                activity = Activity(
                    client_id=(
                        client_options[client]
                        if client != "No Client"
                        else None
                    ),

                    contact_id=(
                        contact_options[contact]
                        if contact != "No Contact"
                        else None
                    ),

                    assigned_to_id=(
                        employee_options[assigned_to]
                        if assigned_to != "Unassigned"
                        else None
                    ),

                    job_id=(
                        job_options[job]
                        if job != "No Job"
                        else None
                    ),

                    candidate_id=(
                        candidate_options[candidate]
                        if candidate != "No Candidate"
                        else None
                    ),

                    placement_id=(
                        placement_options[placement]
                        if placement != "No Placement"
                        else None
                    ),

                    contract_id=(
                        contract_options[contract]
                        if contract != "No Contract"
                        else None
                    ),

                    activity_type=activity_type,
                    subject=subject.strip(),
                    activity_date=activity_date,
                    due_date=due_date,
                    status=status,
                    priority=priority,
                    notes=notes.strip()
                )

                session.add(activity)
                session.commit()

                st.success(
                    "Activity created successfully."
                )

                st.rerun()

    # ============================================================
    # ACTIVITY REGISTER
    # ============================================================

    st.divider()

    st.header("Activity Register")

    activities = (
        session.query(Activity)
        .order_by(
            Activity.activity_date.desc()
        )
        .all()
    )

    if not activities:

        st.info(
            "No activities have been created yet."
        )

        session.close()
        return

    # ============================================================
    # FILTERS
    # ============================================================

    col1, col2, col3 = st.columns(3)

    # ------------------------------------------------------------
    # STATUS FILTER
    # ------------------------------------------------------------

    with col1:

        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Open",
                "In Progress",
                "Completed",
                "Cancelled"
            ]
        )

    # ------------------------------------------------------------
    # ACTIVITY TYPE FILTER
    # ------------------------------------------------------------

    with col2:

        type_filter = st.selectbox(
            "Activity Type",
            [
                "All",
                "Call",
                "Email",
                "Meeting",
                "Follow-up",
                "Task",
                "Note",
                "Interview",
                "Other"
            ]
        )

    # ------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------

    with col3:

        search = st.text_input(
            "Search",
            placeholder="Subject, client or notes..."
        )

    # ============================================================
    # APPLY FILTERS
    # ============================================================

    filtered_activities = activities

    if status_filter != "All":

        filtered_activities = [
            activity
            for activity in filtered_activities
            if activity.status == status_filter
        ]

    if type_filter != "All":

        filtered_activities = [
            activity
            for activity in filtered_activities
            if activity.activity_type == type_filter
        ]

    if search:

        search_text = search.lower()

        filtered_activities = [
            activity
            for activity in filtered_activities
            if (
                search_text
                in (activity.subject or "").lower()

                or search_text
                in (activity.notes or "").lower()

                or search_text
                in (
                    activity.client.company_name
                    if activity.client
                    else ""
                ).lower()
            )
        ]

    st.write(
        f"Showing **{len(filtered_activities)}** "
        f"activity/activities"
    )

    # ============================================================
    # DISPLAY ACTIVITIES
    # ============================================================

    for activity in filtered_activities:

        with st.container(border=True):

            col1, col2, col3, col4 = st.columns(
                [3, 3, 2, 2]
            )

            # ----------------------------------------------------
            # ACTIVITY
            # ----------------------------------------------------

            with col1:

                st.subheader(
                    activity.subject
                )

                st.caption(
                    activity.activity_type or "—"
                )

                if activity.client:

                    st.write(
                        activity.client.company_name
                    )

            # ----------------------------------------------------
            # STATUS
            # ----------------------------------------------------

            with col2:

                st.write(
                    "**Status**"
                )

                st.write(
                    activity.status or "—"
                )

                st.caption(
                    f"Priority: "
                    f"{activity.priority or '—'}"
                )

            # ----------------------------------------------------
            # DATES
            # ----------------------------------------------------

            with col3:

                st.write(
                    "**Dates**"
                )

                if activity.activity_date:

                    st.write(
                        f"Activity: "
                        f"{activity.activity_date}"
                    )

                if activity.due_date:

                    st.caption(
                        f"Due: "
                        f"{activity.due_date}"
                    )

            # ----------------------------------------------------
            # ASSIGNED EMPLOYEE
            # ----------------------------------------------------

            with col4:

                if activity.assigned_to:

                    employee_name = " ".join(
                        part
                        for part in [
                            activity.assigned_to.first_name,
                            activity.assigned_to.last_name
                        ]
                        if part
                    )

                    st.write(
                        employee_name
                    )

                else:

                    st.write(
                        "Unassigned"
                    )

            # ----------------------------------------------------
            # NOTES
            # ----------------------------------------------------

            if activity.notes:

                st.caption(
                    f"Notes: {activity.notes}"
                )

    # ============================================================
    # CLOSE DATABASE SESSION
    # ============================================================

    session.close()