import streamlit as st
from datetime import date

from database import get_session
from models import (
    Activity,
    Client,
    ClientContact,
    Employee,
    Job,
    Candidate,
    Placement,
    Contract,
)


# ============================================================
# CONSTANTS
# ============================================================

ACTIVITY_TYPES = [
    "Call",
    "Email",
    "Meeting",
    "Note",
    "Follow-up",
    "Task",
]

ACTIVITY_STATUSES = [
    "Open",
    "Completed",
    "Cancelled",
]

PRIORITIES = [
    "Low",
    "Medium",
    "High",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_client_name(client):
    if not client:
        return "No Client"

    return client.company_name or "Unnamed Client"


def get_contact_name(contact):
    if not contact:
        return "No Contact"

    name = " ".join(
        part
        for part in [
            contact.first_name,
            contact.last_name,
        ]
        if part
    )

    return name or "Unnamed Contact"


def get_employee_name(employee):
    if not employee:
        return "Unassigned"

    name = " ".join(
        part
        for part in [
            employee.first_name,
            employee.last_name,
        ]
        if part
    )

    return name or "Unnamed Employee"


def get_candidate_name(candidate):
    if not candidate:
        return "No Candidate"

    if candidate.employee:
        return get_employee_name(candidate.employee)

    return f"Candidate #{candidate.id}"


def get_placement_name(placement):
    if not placement:
        return "No Placement"

    employee_name = get_employee_name(
        placement.employee
    )

    position = placement.position or "Placement"

    return f"{position} - {employee_name}"


def get_contract_name(contract):
    if not contract:
        return "No Contract"

    return (
        contract.contract_number
        or f"Contract #{contract.id}"
    )


# ============================================================
# MAIN ACTIVITIES SCREEN
# ============================================================

def show_activities():

    st.title("Activities")

    st.caption(
        "Manage calls, emails, meetings, notes, tasks and follow-ups."
    )

    session = get_session()

    try:

        # ========================================================
        # LOAD DATA
        # ========================================================

        clients = (
            session.query(Client)
            .order_by(Client.company_name.asc())
            .all()
        )

        contacts = (
            session.query(ClientContact)
            .order_by(ClientContact.first_name.asc())
            .all()
        )

        employees = (
            session.query(Employee)
            .order_by(Employee.first_name.asc())
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

        activities = (
            session.query(Activity)
            .order_by(
                Activity.activity_date.desc(),
                Activity.id.desc()
            )
            .all()
        )

        # ========================================================
        # DROPDOWN OPTIONS
        # ========================================================

        client_options = {
            client.company_name: client.id
            for client in clients
        }

        contact_options = {
            (
                f"{get_contact_name(contact)} - "
                f"{get_client_name(contact.client)}"
            ): contact.id
            for contact in contacts
        }

        employee_options = {
            get_employee_name(employee): employee.id
            for employee in employees
        }

        job_options = {
            (
                f"{job.position} - "
                f"{get_client_name(job.client)}"
            ): job.id
            for job in jobs
        }

        candidate_options = {
            (
                f"{get_candidate_name(candidate)} - "
                f"Candidate #{candidate.id}"
            ): candidate.id
            for candidate in candidates
        }

        placement_options = {
            (
                f"{get_placement_name(placement)} - "
                f"Placement #{placement.id}"
            ): placement.id
            for placement in placements
        }

        contract_options = {
            (
                f"{get_contract_name(contract)} - "
                f"{get_client_name(contract.client)}"
            ): contract.id
            for contract in contracts
        }

        # ========================================================
        # STATISTICS
        # ========================================================

        total_activities = len(activities)

        open_activities = sum(
            1
            for activity in activities
            if activity.status == "Open"
        )

        completed_activities = sum(
            1
            for activity in activities
            if activity.status == "Completed"
        )

        today_activities = sum(
            1
            for activity in activities
            if activity.activity_date == date.today()
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Total Activities",
                total_activities
            )

        with col2:

            st.metric(
                "Open",
                open_activities
            )

        with col3:

            st.metric(
                "Completed",
                completed_activities
            )

        with col4:

            st.metric(
                "Today",
                today_activities
            )

        # ========================================================
        # ADD ACTIVITY
        # ========================================================

        st.divider()

        st.header("Add Activity")

        with st.form("add_activity_form"):

            # ====================================================
            # BASIC INFORMATION
            # ====================================================

            st.subheader("Activity Details")

            col1, col2 = st.columns(2)

            with col1:

                activity_type = st.selectbox(
                    "Activity Type *",
                    ACTIVITY_TYPES
                )

                subject = st.text_input(
                    "Subject *",
                    placeholder=(
                        "Example: Follow up with client "
                        "about Finance Analyst vacancy"
                    )
                )

                activity_date = st.date_input(
                    "Activity Date",
                    value=date.today()
                )

                due_date = st.date_input(
                    "Due Date",
                    value=None
                )

            with col2:

                status = st.selectbox(
                    "Status",
                    ACTIVITY_STATUSES
                )

                priority = st.selectbox(
                    "Priority",
                    PRIORITIES
                )

                assigned_to = st.selectbox(
                    "Assigned To",
                    ["Unassigned"] +
                    list(employee_options.keys())
                )

            # ====================================================
            # CLIENT INFORMATION
            # ====================================================

            st.subheader("Client")

            col1, col2 = st.columns(2)

            with col1:

                selected_client = st.selectbox(
                    "Client",
                    ["No Client"] +
                    list(client_options.keys())
                )

            with col2:

                selected_contact = st.selectbox(
                    "Client Contact",
                    ["No Contact"] +
                    list(contact_options.keys())
                )

            # ====================================================
            # RECRUITMENT
            # ====================================================

            st.subheader("Recruitment")

            col1, col2 = st.columns(2)

            with col1:

                selected_job = st.selectbox(
                    "Job",
                    ["No Job"] +
                    list(job_options.keys())
                )

            with col2:

                selected_candidate = st.selectbox(
                    "Candidate",
                    ["No Candidate"] +
                    list(candidate_options.keys())
                )

            # ====================================================
            # PLACEMENT / CONTRACT
            # ====================================================

            st.subheader("Placement / Contract")

            col1, col2 = st.columns(2)

            with col1:

                selected_placement = st.selectbox(
                    "Placement",
                    ["No Placement"] +
                    list(placement_options.keys())
                )

            with col2:

                selected_contract = st.selectbox(
                    "Contract",
                    ["No Contract"] +
                    list(contract_options.keys())
                )

            # ====================================================
            # NOTES
            # ====================================================

            notes = st.text_area(
                "Notes",
                placeholder=(
                    "Enter details of the call, email, "
                    "meeting, task or follow-up..."
                )
            )

            # ====================================================
            # SUBMIT
            # ====================================================

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

                    new_activity = Activity(
                        activity_type=activity_type,
                        subject=subject.strip(),
                        activity_date=activity_date,
                        due_date=due_date,
                        status=status,
                        priority=priority,
                        notes=notes.strip(),
                    )

                    # ------------------------------------------------
                    # CLIENT
                    # ------------------------------------------------

                    if selected_client != "No Client":

                        new_activity.client_id = (
                            client_options[
                                selected_client
                            ]
                        )

                    # ------------------------------------------------
                    # CONTACT
                    # ------------------------------------------------

                    if selected_contact != "No Contact":

                        new_activity.contact_id = (
                            contact_options[
                                selected_contact
                            ]
                        )

                    # ------------------------------------------------
                    # ASSIGNED EMPLOYEE
                    # ------------------------------------------------

                    if assigned_to != "Unassigned":

                        new_activity.assigned_to_id = (
                            employee_options[
                                assigned_to
                            ]
                        )

                    # ------------------------------------------------
                    # JOB
                    # ------------------------------------------------

                    if selected_job != "No Job":

                        new_activity.job_id = (
                            job_options[
                                selected_job
                            ]
                        )

                    # ------------------------------------------------
                    # CANDIDATE
                    # ------------------------------------------------

                    if selected_candidate != "No Candidate":

                        new_activity.candidate_id = (
                            candidate_options[
                                selected_candidate
                            ]
                        )

                    # ------------------------------------------------
                    # PLACEMENT
                    # ------------------------------------------------

                    if selected_placement != "No Placement":

                        new_activity.placement_id = (
                            placement_options[
                                selected_placement
                            ]
                        )

                    # ------------------------------------------------
                    # CONTRACT
                    # ------------------------------------------------

                    if selected_contract != "No Contract":

                        new_activity.contract_id = (
                            contract_options[
                                selected_contract
                            ]
                        )

                    # ------------------------------------------------
                    # SAVE
                    # ------------------------------------------------

                    session.add(new_activity)
                    session.commit()

                    st.success(
                        "Activity created successfully."
                    )

                    st.rerun()

        # ========================================================
        # ACTIVITY REGISTER
        # ========================================================

        st.divider()

        st.header("Activity Register")

        # ========================================================
        # FILTERS
        # ========================================================

        col1, col2, col3 = st.columns(3)

        with col1:

            type_filter = st.selectbox(
                "Activity Type",
                ["All"] + ACTIVITY_TYPES
            )

        with col2:

            status_filter = st.selectbox(
                "Status",
                ["All"] + ACTIVITY_STATUSES
            )

        with col3:

            priority_filter = st.selectbox(
                "Priority",
                ["All"] + PRIORITIES
            )

        col1, col2 = st.columns(2)

        with col1:

            client_filter = st.selectbox(
                "Client",
                ["All"] +
                list(client_options.keys())
            )

        with col2:

            search = st.text_input(
                "Search",
                placeholder=(
                    "Search subject, notes, client, "
                    "contact or employee..."
                )
            )

        # ========================================================
        # APPLY FILTERS
        # ========================================================

        filtered_activities = activities

        if type_filter != "All":

            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity.activity_type == type_filter
            ]

        if status_filter != "All":

            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity.status == status_filter
            ]

        if priority_filter != "All":

            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity.priority == priority_filter
            ]

        if client_filter != "All":

            selected_client_id = (
                client_options[client_filter]
            )

            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity.client_id == selected_client_id
            ]

        if search:

            search_text = search.lower().strip()

            filtered_activities = [
                activity
                for activity in filtered_activities
                if (
                    search_text
                    in (
                        activity.subject or ""
                    ).lower()

                    or search_text
                    in (
                        activity.notes or ""
                    ).lower()

                    or search_text
                    in get_client_name(
                        activity.client
                    ).lower()

                    or search_text
                    in get_contact_name(
                        activity.contact
                    ).lower()

                    or search_text
                    in get_employee_name(
                        activity.assigned_employee
                    ).lower()
                )
            ]

        st.write(
            f"Showing **{len(filtered_activities)}** "
            f"activity/activities"
        )

        # ========================================================
        # DISPLAY ACTIVITIES
        # ========================================================

        if not filtered_activities:

            st.info(
                "No activities match the selected filters."
            )

        else:

            for activity in filtered_activities:

                with st.container(border=True):

                    col1, col2, col3, col4 = st.columns(
                        [3, 2, 2, 2]
                    )

                    # ============================================
                    # ACTIVITY
                    # ============================================

                    with col1:

                        st.subheader(
                            activity.subject
                        )

                        st.caption(
                            activity.activity_type
                        )

                        if activity.notes:

                            st.write(
                                activity.notes
                            )

                    # ============================================
                    # DATE
                    # ============================================

                    with col2:

                        st.write(
                            "**Date**"
                        )

                        if activity.activity_date:

                            st.write(
                                activity.activity_date
                            )

                        if activity.due_date:

                            st.caption(
                                f"Due: "
                                f"{activity.due_date}"
                            )

                    # ============================================
                    # STATUS
                    # ============================================

                    with col3:

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

                    # ============================================
                    # CLIENT / CONTACT
                    # ============================================

                    with col4:

                        st.write(
                            "**Client**"
                        )

                        if activity.client:

                            st.write(
                                get_client_name(
                                    activity.client
                                )
                            )

                        else:

                            st.write(
                                "No Client"
                            )

                        if activity.contact:

                            st.caption(
                                get_contact_name(
                                    activity.contact
                                )
                            )

                    # ============================================
                    # ADDITIONAL LINKS
                    # ============================================

                    linked_items = []

                    if activity.assigned_employee:

                        linked_items.append(
                            "Assigned: "
                            + get_employee_name(
                                activity.assigned_employee
                            )
                        )

                    if activity.job:

                        linked_items.append(
                            "Job: "
                            + (
                                activity.job.position
                                or f"Job #{activity.job.id}"
                            )
                        )

                    if activity.candidate:

                        linked_items.append(
                            "Candidate: "
                            + get_candidate_name(
                                activity.candidate
                            )
                        )

                    if activity.placement:

                        linked_items.append(
                            "Placement: "
                            + get_placement_name(
                                activity.placement
                            )
                        )

                    if activity.contract:

                        linked_items.append(
                            "Contract: "
                            + get_contract_name(
                                activity.contract
                            )
                        )

                    if linked_items:

                        st.caption(
                            " | ".join(linked_items)
                        )

    except Exception as e:

        session.rollback()

        st.error(
            f"Unable to load Activities: {e}"
        )

    finally:

        session.close()