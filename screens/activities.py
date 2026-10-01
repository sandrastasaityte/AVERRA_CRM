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
# DISPLAY HELPERS
# ============================================================

def get_client_name(client):
    if not client:
        return "No Client"

    return (
        getattr(client, "company_name", None)
        or f"Client #{getattr(client, 'id', '')}"
    )


def get_contact_name(contact):
    if not contact:
        return "No Contact"

    name = " ".join(
        str(part).strip()
        for part in [
            getattr(contact, "first_name", None),
            getattr(contact, "last_name", None),
        ]
        if part and str(part).strip()
    )

    return name or f"Contact #{getattr(contact, 'id', '')}"


def get_employee_name(employee):
    if not employee:
        return "Unassigned"

    name = " ".join(
        str(part).strip()
        for part in [
            getattr(employee, "first_name", None),
            getattr(employee, "last_name", None),
        ]
        if part and str(part).strip()
    )

    return name or f"Employee #{getattr(employee, 'id', '')}"


def get_candidate_name(candidate):
    if not candidate:
        return "No Candidate"

    employee = getattr(candidate, "employee", None)

    if employee:
        return get_employee_name(employee)

    return f"Candidate #{getattr(candidate, 'id', '')}"


def get_placement_name(placement):
    if not placement:
        return "No Placement"

    employee = getattr(placement, "employee", None)

    employee_name = get_employee_name(employee)

    position = (
        getattr(placement, "position", None)
        or "Placement"
    )

    return f"{position} - {employee_name}"


def get_contract_name(contract):
    if not contract:
        return "No Contract"

    return (
        getattr(contract, "contract_number", None)
        or f"Contract #{getattr(contract, 'id', '')}"
    )


def get_job_name(job):
    if not job:
        return "No Job"

    return (
        getattr(job, "position", None)
        or f"Job #{getattr(job, 'id', '')}"
    )


def safe_text(value):
    return str(value or "").strip().lower()


# ============================================================
# SEARCH
# ============================================================

def build_activity_search_text(activity):
    values = [
        getattr(activity, "subject", None),
        getattr(activity, "notes", None),
        getattr(activity, "activity_type", None),
        getattr(activity, "status", None),
        getattr(activity, "priority", None),
        get_client_name(getattr(activity, "client", None)),
        get_contact_name(getattr(activity, "contact", None)),
        get_employee_name(
            getattr(activity, "assigned_employee", None)
        ),
        get_candidate_name(
            getattr(activity, "candidate", None)
        ),
        get_placement_name(
            getattr(activity, "placement", None)
        ),
        get_contract_name(
            getattr(activity, "contract", None)
        ),
        get_job_name(
            getattr(activity, "job", None)
        ),
    ]

    return " ".join(
        safe_text(value)
        for value in values
        if value
    )


# ============================================================
# DATE / STATUS HELPERS
# ============================================================

def activity_is_overdue(activity):
    if not activity:
        return False

    if activity.status != "Open":
        return False

    if not activity.due_date:
        return False

    return activity.due_date < date.today()


def activity_is_due_today(activity):
    if not activity:
        return False

    if activity.status != "Open":
        return False

    if not activity.due_date:
        return False

    return activity.due_date == date.today()


def activity_is_upcoming(activity):
    if not activity:
        return False

    if activity.status != "Open":
        return False

    if not activity.due_date:
        return False

    today = date.today()
    end_date = today + timedelta(days=7)

    return today < activity.due_date <= end_date


def activity_is_future(activity):
    if not activity:
        return False

    if activity.status != "Open":
        return False

    if not activity.due_date:
        return False

    return activity.due_date > date.today()


# ============================================================
# DATABASE HELPERS
# ============================================================

def save_activity(session, activity):
    try:
        session.add(activity)
        session.commit()
        session.refresh(activity)

        return True, None

    except Exception as error:
        session.rollback()
        return False, error


def update_activity(session, activity):
    try:
        session.commit()
        session.refresh(activity)

        return True, None

    except Exception as error:
        session.rollback()
        return False, error


def delete_activity(session, activity):
    try:
        session.delete(activity)
        session.commit()

        return True, None

    except Exception as error:
        session.rollback()
        return False, error


# ============================================================
# DROPDOWN BUILDERS
# ============================================================

def build_client_options(clients):
    options = {}

    for client in clients:
        label = (
            f"{get_client_name(client)} "
            f"(ID: {client.id})"
        )

        options[label] = client.id

    return options


def build_contact_options(contacts):
    options = {}

    for contact in contacts:
        label = (
            f"{get_contact_name(contact)} - "
            f"{get_client_name(contact.client)} "
            f"(ID: {contact.id})"
        )

        options[label] = contact.id

    return options


def build_employee_options(employees):
    options = {}

    for employee in employees:
        label = (
            f"{get_employee_name(employee)} "
            f"(ID: {employee.id})"
        )

        options[label] = employee.id

    return options


def build_job_options(jobs):
    options = {}

    for job in jobs:
        label = (
            f"{get_job_name(job)} - "
            f"{get_client_name(job.client)} "
            f"(ID: {job.id})"
        )

        options[label] = job.id

    return options


def build_candidate_options(candidates):
    options = {}

    for candidate in candidates:
        label = (
            f"{get_candidate_name(candidate)} - "
            f"Candidate #{candidate.id}"
        )

        options[label] = candidate.id

    return options


def build_placement_options(placements):
    options = {}

    for placement in placements:
        label = (
            f"{get_placement_name(placement)} - "
            f"Placement #{placement.id}"
        )

        options[label] = placement.id

    return options


def build_contract_options(contracts):
    options = {}

    for contract in contracts:
        label = (
            f"{get_contract_name(contract)} - "
            f"{get_client_name(contract.client)} "
            f"(ID: {contract.id})"
        )

        options[label] = contract.id

    return options


def get_selected_label(options, selected_id, default_label):
    if not selected_id:
        return default_label

    for label, record_id in options.items():
        if record_id == selected_id:
            return label

    return default_label


def get_option_id(options, selected_value, empty_value):
    if selected_value == empty_value:
        return None

    return options.get(selected_value)


# ============================================================
# VALIDATION
# ============================================================

def validate_activity_dates(activity_date, due_date):
    if not activity_date:
        return "Activity Date is required."

    if due_date and due_date < activity_date:
        return "Due Date cannot be earlier than Activity Date."

    return None


def validate_activity_subject(subject):
    clean_subject = str(subject or "").strip()

    if not clean_subject:
        return "Subject is required."

    if len(clean_subject) > 200:
        return "Subject must be 200 characters or fewer."

    return None


# ============================================================
# EDIT ACTIVITY
# ============================================================

def render_edit_activity(
    session,
    activity,
    clients,
    contacts,
    employees,
    jobs,
    candidates,
    placements,
    contracts,
):
    edit_key = f"edit_activity_{activity.id}"

    st.subheader(
        f"Edit Activity #{activity.id}"
    )

    client_options = build_client_options(clients)
    contact_options = build_contact_options(contacts)
    employee_options = build_employee_options(employees)
    job_options = build_job_options(jobs)
    candidate_options = build_candidate_options(candidates)
    placement_options = build_placement_options(placements)
    contract_options = build_contract_options(contracts)

    client_labels = [
        "No Client"
    ] + list(client_options.keys())

    contact_labels = [
        "No Contact"
    ] + list(contact_options.keys())

    employee_labels = [
        "Unassigned"
    ] + list(employee_options.keys())

    job_labels = [
        "No Job"
    ] + list(job_options.keys())

    candidate_labels = [
        "No Candidate"
    ] + list(candidate_options.keys())

    placement_labels = [
        "No Placement"
    ] + list(placement_options.keys())

    contract_labels = [
        "No Contract"
    ] + list(contract_options.keys())

    current_client_label = get_selected_label(
        client_options,
        activity.client_id,
        "No Client",
    )

    current_contact_label = get_selected_label(
        contact_options,
        activity.contact_id,
        "No Contact",
    )

    current_employee_label = get_selected_label(
        employee_options,
        activity.assigned_to_id,
        "Unassigned",
    )

    current_job_label = get_selected_label(
        job_options,
        activity.job_id,
        "No Job",
    )

    current_candidate_label = get_selected_label(
        candidate_options,
        activity.candidate_id,
        "No Candidate",
    )

    current_placement_label = get_selected_label(
        placement_options,
        activity.placement_id,
        "No Placement",
    )

    current_contract_label = get_selected_label(
        contract_options,
        activity.contract_id,
        "No Contract",
    )

    activity_type_index = (
        ACTIVITY_TYPES.index(activity.activity_type)
        if activity.activity_type in ACTIVITY_TYPES
        else 0
    )

    status_index = (
        ACTIVITY_STATUSES.index(activity.status)
        if activity.status in ACTIVITY_STATUSES
        else 0
    )

    priority_index = (
        PRIORITIES.index(activity.priority)
        if activity.priority in PRIORITIES
        else 1
    )

    with st.form(edit_key):

        st.markdown("### Activity Details")

        col1, col2 = st.columns(2)

        with col1:

            activity_type = st.selectbox(
                "Activity Type",
                ACTIVITY_TYPES,
                index=activity_type_index,
            )

            subject = st.text_input(
                "Subject *",
                value=activity.subject or "",
                max_chars=200,
            )

            activity_date = st.date_input(
                "Activity Date",
                value=activity.activity_date or date.today(),
            )

            due_date = st.date_input(
                "Due Date",
                value=activity.due_date,
            )

        with col2:

            status = st.selectbox(
                "Status",
                ACTIVITY_STATUSES,
                index=status_index,
            )

            priority = st.selectbox(
                "Priority",
                PRIORITIES,
                index=priority_index,
            )

            assigned_to = st.selectbox(
                "Assigned To",
                employee_labels,
                index=(
                    employee_labels.index(
                        current_employee_label
                    )
                    if current_employee_label in employee_labels
                    else 0
                ),
            )

        st.markdown("### Client")

        col1, col2 = st.columns(2)

        with col1:

            selected_client = st.selectbox(
                "Client",
                client_labels,
                index=(
                    client_labels.index(
                        current_client_label
                    )
                    if current_client_label in client_labels
                    else 0
                ),
            )

        with col2:

            selected_contact = st.selectbox(
                "Client Contact",
                contact_labels,
                index=(
                    contact_labels.index(
                        current_contact_label
                    )
                    if current_contact_label in contact_labels
                    else 0
                ),
            )

        st.markdown("### Recruitment")

        col1, col2 = st.columns(2)

        with col1:

            selected_job = st.selectbox(
                "Job",
                job_labels,
                index=(
                    job_labels.index(
                        current_job_label
                    )
                    if current_job_label in job_labels
                    else 0
                ),
            )

        with col2:

            selected_candidate = st.selectbox(
                "Candidate",
                candidate_labels,
                index=(
                    candidate_labels.index(
                        current_candidate_label
                    )
                    if current_candidate_label in candidate_labels
                    else 0
                ),
            )

        st.markdown("### Placement / Contract")

        col1, col2 = st.columns(2)

        with col1:

            selected_placement = st.selectbox(
                "Placement",
                placement_labels,
                index=(
                    placement_labels.index(
                        current_placement_label
                    )
                    if current_placement_label in placement_labels
                    else 0
                ),
            )

        with col2:

            selected_contract = st.selectbox(
                "Contract",
                contract_labels,
                index=(
                    contract_labels.index(
                        current_contract_label
                    )
                    if current_contract_label in contract_labels
                    else 0
                ),
            )

        notes = st.text_area(
            "Notes",
            value=activity.notes or "",
        )

        col1, col2 = st.columns(2)

        with col1:

            save_changes = st.form_submit_button(
                "Save Changes",
                use_container_width=True,
            )

        with col2:

            cancel_edit = st.form_submit_button(
                "Cancel",
                use_container_width=True,
            )

        if cancel_edit:

            st.session_state.pop(
                edit_key,
                None,
            )

            st.rerun()

        if save_changes:

            clean_subject = subject.strip()
            clean_notes = notes.strip()

            subject_error = validate_activity_subject(
                clean_subject
            )

            date_error = validate_activity_dates(
                activity_date,
                due_date,
            )

            if subject_error:

                st.error(subject_error)

            elif date_error:

                st.error(date_error)

            else:

                activity.activity_type = activity_type
                activity.subject = clean_subject
                activity.activity_date = activity_date
                activity.due_date = due_date
                activity.status = status
                activity.priority = priority
                activity.notes = clean_notes

                activity.client_id = get_option_id(
                    client_options,
                    selected_client,
                    "No Client",
                )

                activity.contact_id = get_option_id(
                    contact_options,
                    selected_contact,
                    "No Contact",
                )

                activity.assigned_to_id = get_option_id(
                    employee_options,
                    assigned_to,
                    "Unassigned",
                )

                activity.job_id = get_option_id(
                    job_options,
                    selected_job,
                    "No Job",
                )

                activity.candidate_id = get_option_id(
                    candidate_options,
                    selected_candidate,
                    "No Candidate",
                )

                activity.placement_id = get_option_id(
                    placement_options,
                    selected_placement,
                    "No Placement",
                )

                activity.contract_id = get_option_id(
                    contract_options,
                    selected_contract,
                    "No Contract",
                )

                success, error = update_activity(
                    session,
                    activity,
                )

                if success:

                    st.success(
                        "Activity updated successfully."
                    )

                    st.session_state.pop(
                        edit_key,
                        None,
                    )

                    st.rerun()

                else:

                    st.error(
                        f"Unable to update activity: {error}"
                    )


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

        client_options = build_client_options(clients)
        contact_options = build_contact_options(contacts)
        employee_options = build_employee_options(employees)
        job_options = build_job_options(jobs)
        candidate_options = build_candidate_options(candidates)
        placement_options = build_placement_options(placements)
        contract_options = build_contract_options(contracts)

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

        cancelled_activities = sum(
            1
            for activity in activities
            if activity.status == "Cancelled"
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

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            if overdue_activities > 0:
                st.error(
                    f"Overdue: {overdue_activities}"
                )
            else:
                st.success(
                    "Overdue: 0"
                )

        with col2:

            if due_today > 0:
                st.warning(
                    f"Due Today: {due_today}"
                )
            else:
                st.info(
                    "Due Today: 0"
                )

        with col3:

            st.info(
                f"Next 7 Days: {upcoming_activities}"
            )

        with col4:

            st.caption(
                f"Cancelled: {cancelled_activities}"
            )

        # ========================================================
        # ADD ACTIVITY
        # ========================================================

        st.divider()

        st.header("Add Activity")

        with st.form("add_activity_form"):

            st.markdown("### Activity Details")

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
                    max_chars=200,
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

            st.markdown("### Client")

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

            st.markdown("### Recruitment")

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

            st.markdown("### Placement / Contract")

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

            notes = st.text_area(
                "Notes",
                placeholder=(
                    "Enter details of the call, email, "
                    "meeting, task or follow-up..."
                ),
            )

            submitted = st.form_submit_button(
                "Create Activity",
                use_container_width=True,
            )

            if submitted:

                clean_subject = subject.strip()
                clean_notes = notes.strip()

                subject_error = validate_activity_subject(
                    clean_subject
                )

                date_error = validate_activity_dates(
                    activity_date,
                    due_date,
                )

                if subject_error:

                    st.error(subject_error)

                elif date_error:

                    st.error(date_error)

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

                    if selected_client != "No Client":

                        new_activity.client_id = (
                            client_options[selected_client]
                        )

                    if selected_contact != "No Contact":

                        new_activity.contact_id = (
                            contact_options[selected_contact]
                        )

                    if assigned_to != "Unassigned":

                        new_activity.assigned_to_id = (
                            employee_options[assigned_to]
                        )

                    if selected_job != "No Job":

                        new_activity.job_id = (
                            job_options[selected_job]
                        )

                    if selected_candidate != "No Candidate":

                        new_activity.candidate_id = (
                            candidate_options[selected_candidate]
                        )

                    if selected_placement != "No Placement":

                        new_activity.placement_id = (
                            placement_options[selected_placement]
                        )

                    if selected_contract != "No Contract":

                        new_activity.contract_id = (
                            contract_options[selected_contract]
                        )

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
                    "Future",
                    "No Due Date",
                ],
            )

        col1, col2 = st.columns(2)

        with col1:

            start_date_filter = st.date_input(
                "Activity Date From",
                value=None,
            )

        with col2:

            end_date_filter = st.date_input(
                "Activity Date To",
                value=None,
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

            selected_client_id = client_options[
                client_filter
            ]

            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity.client_id == selected_client_id
            ]

        if assigned_filter != "All":

            selected_employee_id = employee_options[
                assigned_filter
            ]

            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity.assigned_to_id
                == selected_employee_id
            ]

        if start_date_filter:

            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity.activity_date
                and activity.activity_date >= start_date_filter
            ]

        if end_date_filter:

            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity.activity_date
                and activity.activity_date <= end_date_filter
            ]

        if (
            start_date_filter
            and end_date_filter
            and start_date_filter > end_date_filter
        ):

            st.warning(
                "Activity Date From cannot be later than "
                "Activity Date To."
            )

            filtered_activities = []

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

        elif timing_filter == "Future":

            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity_is_future(activity)
            ]

        elif timing_filter == "No Due Date":

            filtered_activities = [
                activity
                for activity in filtered_activities
                if not activity.due_date
            ]

        if search:

            search_text = search.strip().lower()

            if search_text:

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

                edit_key = (
                    f"edit_activity_{activity.id}"
                )

                delete_key = (
                    f"delete_confirm_{activity.id}"
                )

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
                    # EDIT FORM
                    # ====================================================

                    if st.session_state.get(
                        edit_key,
                        False,
                    ):

                        render_edit_activity(
                            session=session,
                            activity=activity,
                            clients=clients,
                            contacts=contacts,
                            employees=employees,
                            jobs=jobs,
                            candidates=candidates,
                            placements=placements,
                            contracts=contracts,
                        )

                        st.divider()

                    # ====================================================
                    # MAIN INFORMATION
                    # ====================================================

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:

                        st.write(
                            "**Activity Date**"
                        )

                        st.write(
                            activity.activity_date
                            or "—"
                        )

                        if activity.due_date:

                            st.caption(
                                f"Due: {activity.due_date}"
                            )

                    with col2:

                        st.write(
                            "**Client**"
                        )

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

                        st.write(
                            "**Assigned To**"
                        )

                        st.write(
                            get_employee_name(
                                activity.assigned_employee
                            )
                        )

                        if activity.job:

                            st.caption(
                                "Job: "
                                + get_job_name(
                                    activity.job
                                )
                            )

                    with col4:

                        st.write(
                            "**Linked Record**"
                        )

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

                    action_col1, action_col2, action_col3, action_col4 = (
                        st.columns(4)
                    )

                    # ------------------------------------------------
                    # COMPLETE
                    # ------------------------------------------------

                    with action_col1:

                        if (
                            activity.status == "Open"
                            and st.button(
                                "Mark Completed",
                                key=(
                                    f"complete_"
                                    f"{activity.id}"
                                ),
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
                                    "Unable to update activity: "
                                    f"{error}"
                                )

                    # ------------------------------------------------
                    # CANCEL
                    # ------------------------------------------------

                    with action_col2:

                        if (
                            activity.status == "Open"
                            and st.button(
                                "Cancel",
                                key=(
                                    f"cancel_"
                                    f"{activity.id}"
                                ),
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
                                    "Unable to cancel activity: "
                                    f"{error}"
                                )

                    # ------------------------------------------------
                    # EDIT
                    # ------------------------------------------------

                    with action_col3:

                        if st.button(
                            "Edit",
                            key=f"edit_{activity.id}",
                            use_container_width=True,
                        ):

                            st.session_state[
                                edit_key
                            ] = not st.session_state.get(
                                edit_key,
                                False,
                            )

                            st.rerun()

                    # ------------------------------------------------
                    # DELETE
                    # ------------------------------------------------

                    with action_col4:

                        if not st.session_state.get(
                            delete_key,
                            False,
                        ):

                            if st.button(
                                "Delete",
                                key=(
                                    f"delete_"
                                    f"{activity.id}"
                                ),
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

                                    success, error = (
                                        delete_activity(
                                            session,
                                            activity,
                                        )
                                    )

                                    if success:

                                        st.session_state.pop(
                                            delete_key,
                                            None,
                                        )

                                        st.success(
                                            "Activity deleted."
                                        )

                                        st.rerun()

                                    else:

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