
import streamlit as st
from datetime import date, timedelta

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
    """Return a safe client display name."""

    if not client:
        return "No Client"

    return (
        getattr(client, "company_name", None)
        or f"Client #{getattr(client, 'id', '')}"
    )


def get_contact_name(contact):
    """Return a safe contact display name."""

    if not contact:
        return "No Contact"

    name = " ".join(
        part.strip()
        for part in [
            getattr(contact, "first_name", None),
            getattr(contact, "last_name", None),
        ]
        if part and str(part).strip()
    )

    return name or f"Contact #{getattr(contact, 'id', '')}"


def get_employee_name(employee):
    """Return a safe employee display name."""

    if not employee:
        return "Unassigned"

    name = " ".join(
        part.strip()
        for part in [
            getattr(employee, "first_name", None),
            getattr(employee, "last_name", None),
        ]
        if part and str(part).strip()
    )

    return name or f"Employee #{getattr(employee, 'id', '')}"


def get_candidate_name(candidate):
    """Return candidate name through linked employee."""

    if not candidate:
        return "No Candidate"

    if getattr(candidate, "employee", None):
        return get_employee_name(candidate.employee)

    return f"Candidate #{getattr(candidate, 'id', '')}"


def get_placement_name(placement):
    """Return a readable placement name."""

    if not placement:
        return "No Placement"

    employee_name = get_employee_name(
        getattr(placement, "employee", None)
    )

    position = (
        getattr(placement, "position", None)
        or "Placement"
    )

    return f"{position} - {employee_name}"


def get_contract_name(contract):
    """Return contract number or fallback identifier."""

    if not contract:
        return "No Contract"

    return (
        getattr(contract, "contract_number", None)
        or f"Contract #{getattr(contract, 'id', '')}"
    )


def activity_is_overdue(activity):
    """Return True when an open activity is past its due date."""

    if not activity:
        return False

    if activity.status != "Open":
        return False

    if not activity.due_date:
        return False

    return activity.due_date < date.today()


def activity_is_due_today(activity):
    """Return True when an open activity is due today."""

    if not activity:
        return False

    if activity.status != "Open":
        return False

    return activity.due_date == date.today()


def activity_is_upcoming(activity):
    """Return True when an open activity is due within 7 days."""

    if not activity:
        return False

    if activity.status != "Open":
        return False

    if not activity.due_date:
        return False

    today = date.today()
    end_date = today + timedelta(days=7)

    return today < activity.due_date <= end_date


def safe_text(value):
    """Convert nullable values into safe searchable text."""

    return str(value or "").strip().lower()


def build_activity_search_text(activity):
    """Build searchable text from an activity and its relationships."""

    values = [
        activity.subject,
        activity.notes,
        activity.activity_type,
        activity.status,
        activity.priority,
        get_client_name(activity.client),
        get_contact_name(activity.contact),
        get_employee_name(activity.assigned_employee),
        get_candidate_name(activity.candidate),
        get_placement_name(activity.placement),
        get_contract_name(activity.contract),
    ]

    if activity.job:
        values.append(
            getattr(activity.job, "position", None)
            or f"Job #{getattr(activity.job, 'id', '')}"
        )

    return " ".join(
        safe_text(value)
        for value in values
        if value
    )


def save_activity(session, activity):
    """Safely save an activity."""

    try:
        session.add(activity)
        session.commit()
        return True, None

    except Exception as error:
        session.rollback()
        return False, error


# ============================================================
# MAIN SCREEN
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
            .order_by(
                ClientContact.first_name.asc(),
                ClientContact.last_name.asc(),
            )
            .all()
        )

        employees = (
            session.query(Employee)
            .order_by(
                Employee.first_name.asc(),
                Employee.last_name.asc(),
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

        activities = (
            session.query(Activity)
            .order_by(
                Activity.activity_date.desc(),
                Activity.id.desc(),
            )
            .all()
        )

        # ========================================================
        # DROPDOWN OPTIONS
        # ========================================================

        client_options = {
            get_client_name(client): client.id
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
                f"{getattr(job, 'position', None) or f'Job #{job.id}'} - "
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

        today = date.today()

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
            if activity.activity_date == today
        )

        overdue_activities = sum(
            1
            for activity in activities
            if activity_is_overdue(activity)
        )

        due_today = sum(
            1
            for activity in activities
            if activity_is_due_today(activity)
        )

        upcoming_activities = sum(
            1
            for activity in activities
            if activity_is_upcoming(activity)
        )

        # ========================================================
        # KPI ROW 1
        # ========================================================

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Activities",
                total_activities,
            )

        with col2:
            st.metric(
                "Open",
                open_activities,
            )

        with col3:
            st.metric(
                "Completed",
                completed_activities,
            )

        with col4:
            st.metric(
                "Today",
                today_activities,
            )

        # ========================================================
        # KPI ROW 2
        # ========================================================

        col1, col2, col3 = st.columns(3)

        with col1:
            if overdue_activities > 0:
                st.error(
                    f"Overdue: {overdue_activities}"
                )
            else:
                st.success("Overdue: 0")

        with col2:
            if due_today > 0:
                st.warning(
                    f"Due Today: {due_today}"
                )
            else:
                st.info("Due Today: 0")

        with col3:
            st.info(
                f"Next 7 Days: {upcoming_activities}"
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
                    ACTIVITY_TYPES,
                )

                subject = st.text_input(
                    "Subject *",
                    placeholder=(
                        "Example: Follow up with client "
                        "about Finance Analyst vacancy"
                    ),
                )

                activity_date = st.date_input(
                    "Activity Date",
                    value=today,
                )

                due_date = st.date_input(
                    "Due Date",
                    value=None,
                )

            with col2:

                status = st.selectbox(
                    "Status",
                    ACTIVITY_STATUSES,
                    index=0,
                )

                priority = st.selectbox(
                    "Priority",
                    PRIORITIES,
                    index=1,
                )

                assigned_to = st.selectbox(
                    "Assigned To",
                    ["Unassigned"] +
                    list(employee_options.keys()),
                )

            # ====================================================
            # CLIENT
            # ====================================================

            st.subheader("Client")

            col1, col2 = st.columns(2)

            with col1:

                selected_client = st.selectbox(
                    "Client",
                    ["No Client"] +
                    list(client_options.keys()),
                )

            with col2:

                selected_contact = st.selectbox(
                    "Client Contact",
                    ["No Contact"] +
                    list(contact_options.keys()),
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
                    list(job_options.keys()),
                )

            with col2:

                selected_candidate = st.selectbox(
                    "Candidate",
                    ["No Candidate"] +
                    list(candidate_options.keys()),
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
                    list(placement_options.keys()),
                )

            with col2:

                selected_contract = st.selectbox(
                    "Contract",
                    ["No Contract"] +
                    list(contract_options.keys()),
                )

            # ====================================================
            # NOTES
            # ====================================================

            notes = st.text_area(
                "Notes",
                placeholder=(
                    "Enter details of the call, email, "
                    "meeting, task or follow-up..."
                ),
            )

            # ====================================================
            # SUBMIT
            # ====================================================

            submitted = st.form_submit_button(
                "Create Activity",
                use_container_width=True,
            )

            if submitted:

                clean_subject = subject.strip()
                clean_notes = notes.strip()

                # ------------------------------------------------
                # VALIDATION
                # ------------------------------------------------

                if not clean_subject:

                    st.error(
                        "Subject is required."
                    )

                elif (
                    due_date
                    and activity_date
                    and due_date < activity_date
                ):

                    st.error(
                        "Due Date cannot be earlier than "
                        "Activity Date."
                    )

                else:

                    new_activity = Activity(
                        activity_type=activity_type,
                        subject=clean_subject,
                        activity_date=activity_date,
                        due_date=due_date,
                        status=status,
                        priority=priority,
                        notes=clean_notes,
                    )

                    # ------------------------------------------------
                    # CLIENT
                    # ------------------------------------------------

                    if selected_client != "No Client":

                        new_activity.client_id = (
                            client_options[selected_client]
                        )

                    # ------------------------------------------------
                    # CONTACT
                    # ------------------------------------------------

                    if selected_contact != "No Contact":

                        new_activity.contact_id = (
                            contact_options[selected_contact]
                        )

                    # ------------------------------------------------
                    # ASSIGNED EMPLOYEE
                    # ------------------------------------------------

                    if assigned_to != "Unassigned":

                        new_activity.assigned_to_id = (
                            employee_options[assigned_to]
                        )

                    # ------------------------------------------------
                    # JOB
                    # ------------------------------------------------

                    if selected_job != "No Job":

                        new_activity.job_id = (
                            job_options[selected_job]
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

                    success, error = save_activity(
                        session,
                        new_activity,
                    )

                    if success:

                        st.success(
                            "Activity created successfully."
                        )

                        st.rerun()

                    else:

                        st.error(
                            f"Unable to create activity: {error}"
                        )

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
                ["All"] + ACTIVITY_TYPES,
            )

        with col2:

            status_filter = st.selectbox(
                "Status",
                ["All"] + ACTIVITY_STATUSES,
            )

        with col3:

            priority_filter = st.selectbox(
                "Priority",
                ["All"] + PRIORITIES,
            )

        col1, col2, col3 = st.columns(3)

        with col1:

            client_filter = st.selectbox(
                "Client",
                ["All"] +
                list(client_options.keys()),
            )

        with col2:

            assigned_filter = st.selectbox(
                "Assigned To",
                ["All"] +
                list(employee_options.keys()),
            )

        with col3:

            timing_filter = st.selectbox(
                "Timing",
                [
                    "All",
                    "Overdue",
                    "Due Today",
                    "Next 7 Days",
                    "No Due Date",
                ],
            )

        search = st.text_input(
            "Search Activities",
            placeholder=(
                "Search subject, notes, client, contact, "
                "employee, job, candidate, placement or contract..."
            ),
        )

        # ========================================================
        # APPLY FILTERS
        # ========================================================

        filtered_activities = list(activities)

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

        if assigned_filter != "All":

            selected_employee_id = (
                employee_options[assigned_filter]
            )

            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity.assigned_to_id
                == selected_employee_id
            ]

        if timing_filter == "Overdue":

            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity_is_overdue(activity)
            ]

        elif timing_filter == "Due Today":

            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity_is_due_today(activity)
            ]

        elif timing_filter == "Next 7 Days":

            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity_is_upcoming(activity)
            ]

        elif timing_filter == "No Due Date":

            filtered_activities = [
                activity
                for activity in filtered_activities
                if not activity.due_date
            ]

        if search:

            search_text = search.strip().lower()

            filtered_activities = [
                activity
                for activity in filtered_activities
                if search_text
                in build_activity_search_text(activity)
            ]

        # ========================================================
        # RESULTS COUNT
        # ========================================================

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

                overdue = activity_is_overdue(activity)
                due_today = activity_is_due_today(activity)

                with st.container(border=True):

                    # ====================================================
                    # HEADER
                    # ====================================================

                    col1, col2 = st.columns([5, 2])

                    with col1:

                        st.subheader(
                            activity.subject
                        )

                        st.caption(
                            f"{activity.activity_type} • "
                            f"{activity.priority or 'No Priority'}"
                        )

                    with col2:

                        if overdue:

                            st.error("OVERDUE")

                        elif due_today:

                            st.warning("DUE TODAY")

                        elif activity.status == "Completed":

                            st.success("COMPLETED")

                        elif activity.status == "Cancelled":

                            st.info("CANCELLED")

                        else:

                            st.write(
                                activity.status or "Open"
                            )

                    # ====================================================
                    # MAIN INFORMATION
                    # ====================================================

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:

                        st.write("**Activity Date**")

                        st.write(
                            activity.activity_date
                            or "—"
                        )

                        if activity.due_date:

                            st.caption(
                                f"Due: {activity.due_date}"
                            )

                    with col2:

                        st.write("**Client**")

                        st.write(
                            get_client_name(
                                activity.client
                            )
                        )

                        if activity.contact:

                            st.caption(
                                get_contact_name(
                                    activity.contact
                                )
                            )

                    with col3:

                        st.write("**Assigned To**")

                        st.write(
                            get_employee_name(
                                activity.assigned_employee
                            )
                        )

                        if activity.job:

                            st.caption(
                                "Job: "
                                + (
                                    getattr(
                                        activity.job,
                                        "position",
                                        None,
                                    )
                                    or
                                    f"Job #{activity.job.id}"
                                )
                            )

                    with col4:

                        st.write("**Linked Record**")

                        linked = []

                        if activity.candidate:

                            linked.append(
                                "Candidate: "
                                + get_candidate_name(
                                    activity.candidate
                                )
                            )

                        if activity.placement:

                            linked.append(
                                "Placement: "
                                + get_placement_name(
                                    activity.placement
                                )
                            )

                        if activity.contract:

                            linked.append(
                                "Contract: "
                                + get_contract_name(
                                    activity.contract
                                )
                            )

                        if linked:

                            for item in linked:

                                st.caption(item)

                        else:

                            st.caption(
                                "No additional links"
                            )

                    # ====================================================
                    # NOTES
                    # ====================================================

                    if activity.notes:

                        st.divider()

                        st.write(
                            "**Notes**"
                        )

                        st.write(
                            activity.notes
                        )

                    # ====================================================
                    # ACTIONS
                    # ====================================================

                    st.divider()

                    action_col1, action_col2, action_col3 = (
                        st.columns(3)
                    )

                    # ------------------------------------------------
                    # COMPLETE
                    # ------------------------------------------------

                    with action_col1:

                        if (
                            activity.status == "Open"
                            and st.button(
                                "Mark Completed",
                                key=f"complete_{activity.id}",
                                use_container_width=True,
                            )
                        ):

                            try:

                                activity.status = "Completed"

                                session.commit()

                                st.success(
                                    "Activity marked as completed."
                                )

                                st.rerun()

                            except Exception as error:

                                session.rollback()

                                st.error(
                                    f"Unable to update activity: {error}"
                                )

                    # ------------------------------------------------
                    # CANCEL
                    # ------------------------------------------------

                    with action_col2:

                        if (
                            activity.status == "Open"
                            and st.button(
                                "Cancel",
                                key=f"cancel_{activity.id}",
                                use_container_width=True,
                            )
                        ):

                            try:

                                activity.status = "Cancelled"

                                session.commit()

                                st.success(
                                    "Activity cancelled."
                                )

                                st.rerun()

                            except Exception as error:

                                session.rollback()

                                st.error(
                                    f"Unable to cancel activity: {error}"
                                )

                    # ------------------------------------------------
                    # DELETE
                    # ------------------------------------------------

                    with action_col3:

                        delete_key = (
                            f"delete_confirm_{activity.id}"
                        )

                        if not st.session_state.get(
                            delete_key,
                            False,
                        ):

                            if st.button(
                                "Delete",
                                key=f"delete_{activity.id}",
                                use_container_width=True,
                            ):

                                st.session_state[
                                    delete_key
                                ] = True

                                st.rerun()

                        else:

                            st.warning(
                                "Delete this activity permanently?"
                            )

                            confirm_col1, confirm_col2 = (
                                st.columns(2)
                            )

                            with confirm_col1:

                                if st.button(
                                    "Yes, Delete",
                                    key=(
                                        f"confirm_delete_"
                                        f"{activity.id}"
                                    ),
                                    use_container_width=True,
                                ):

                                    try:

                                        session.delete(
                                            activity
                                        )

                                        session.commit()

                                        st.success(
                                            "Activity deleted."
                                        )

                                        st.session_state.pop(
                                            delete_key,
                                            None,
                                        )

                                        st.rerun()

                                    except Exception as error:

                                        session.rollback()

                                        st.error(
                                            "Unable to delete "
                                            f"activity: {error}"
                                        )

                            with confirm_col2:

                                if st.button(
                                    "Keep",
                                    key=(
                                        f"keep_activity_"
                                        f"{activity.id}"
                                    ),
                                    use_container_width=True,
                                ):

                                    st.session_state.pop(
                                        delete_key,
                                        None,
                                    )

                                    st.rerun()

    except Exception as error:

        session.rollback()

        st.error(
            f"Unable to load Activities: {error}"
        )

    finally:

        session.close()

