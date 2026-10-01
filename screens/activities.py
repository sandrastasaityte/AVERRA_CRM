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

def safe_text(value, fallback=""):
    if value is None:
        return fallback

    text = str(value).strip()

    return text if text else fallback


def get_client_name(client):
    if not client:
        return "No Client"

    return safe_text(
        getattr(client, "company_name", None),
        f"Client #{getattr(client, 'id', '')}",
    )


def get_contact_name(contact):
    if not contact:
        return "No Contact"

    first_name = safe_text(getattr(contact, "first_name", None))
    last_name = safe_text(getattr(contact, "last_name", None))

    full_name = f"{first_name} {last_name}".strip()

    return full_name or f"Contact #{getattr(contact, 'id', '')}"


def get_employee_name(employee):
    if not employee:
        return "Unassigned"

    first_name = safe_text(getattr(employee, "first_name", None))
    last_name = safe_text(getattr(employee, "last_name", None))

    full_name = f"{first_name} {last_name}".strip()

    return full_name or f"Employee #{getattr(employee, 'id', '')}"


def get_candidate_name(candidate):
    if not candidate:
        return "No Candidate"

    employee = getattr(candidate, "employee", None)

    if employee:
        return get_employee_name(employee)

    first_name = safe_text(getattr(candidate, "first_name", None))
    last_name = safe_text(getattr(candidate, "last_name", None))

    full_name = f"{first_name} {last_name}".strip()

    return full_name or f"Candidate #{getattr(candidate, 'id', '')}"


def get_job_name(job):
    if not job:
        return "No Job"

    position = safe_text(
        getattr(job, "position", None),
        f"Job #{getattr(job, 'id', '')}",
    )

    client = getattr(job, "client", None)

    if client:
        return f"{position} — {get_client_name(client)}"

    return position


def get_placement_name(placement):
    if not placement:
        return "No Placement"

    position = safe_text(
        getattr(placement, "position", None),
        f"Placement #{getattr(placement, 'id', '')}",
    )

    employee = getattr(placement, "employee", None)

    if employee:
        return f"{position} — {get_employee_name(employee)}"

    return position


def get_contract_name(contract):
    if not contract:
        return "No Contract"

    contract_number = safe_text(
        getattr(contract, "contract_number", None),
        f"Contract #{getattr(contract, 'id', '')}",
    )

    client = getattr(contract, "client", None)

    if client:
        return f"{contract_number} — {get_client_name(client)}"

    return contract_number


# ============================================================
# SEARCH
# ============================================================

def build_activity_search_text(activity):
    parts = [
        safe_text(getattr(activity, "activity_type", None)),
        safe_text(getattr(activity, "subject", None)),
        safe_text(getattr(activity, "status", None)),
        safe_text(getattr(activity, "priority", None)),
        safe_text(getattr(activity, "notes", None)),
    ]

    client = getattr(activity, "client", None)
    contact = getattr(activity, "contact", None)
    employee = getattr(activity, "assigned_employee", None)
    job = getattr(activity, "job", None)
    candidate = getattr(activity, "candidate", None)
    placement = getattr(activity, "placement", None)
    contract = getattr(activity, "contract", None)

    parts.extend(
        [
            get_client_name(client),
            get_contact_name(contact),
            get_employee_name(employee),
            get_job_name(job),
            get_candidate_name(candidate),
            get_placement_name(placement),
            get_contract_name(contract),
        ]
    )

    return " ".join(parts).lower()


# ============================================================
# DATE HELPERS
# ============================================================

def activity_is_overdue(activity):
    due_date = getattr(activity, "due_date", None)
    status = getattr(activity, "status", None)

    if not due_date:
        return False

    return due_date < date.today() and status == "Open"


def activity_is_due_today(activity):
    due_date = getattr(activity, "due_date", None)
    status = getattr(activity, "status", None)

    if not due_date:
        return False

    return due_date == date.today() and status == "Open"


def activity_is_upcoming(activity):
    due_date = getattr(activity, "due_date", None)
    status = getattr(activity, "status", None)

    if not due_date:
        return False

    today = date.today()
    end_date = today + timedelta(days=7)

    return (
        today < due_date <= end_date
        and status == "Open"
    )


def activity_is_future(activity):
    due_date = getattr(activity, "due_date", None)

    if not due_date:
        return False

    return due_date > date.today()


# ============================================================
# DATABASE HELPERS
# ============================================================

def save_activity(session, activity):
    session.add(activity)
    session.commit()
    session.refresh(activity)

    return activity


def update_activity(session, activity):
    session.add(activity)
    session.commit()
    session.refresh(activity)

    return activity


def delete_activity(session, activity):
    session.delete(activity)
    session.commit()


# ============================================================
# FILTER HELPERS
# ============================================================

def filter_contacts_by_client(contacts, client_id):
    if not client_id:
        return contacts

    return [
        contact
        for contact in contacts
        if getattr(contact, "client_id", None) == client_id
    ]


def filter_jobs_by_client(jobs, client_id):
    if not client_id:
        return jobs

    return [
        job
        for job in jobs
        if getattr(job, "client_id", None) == client_id
    ]


def filter_candidates_by_job(candidates, job_id):
    if not job_id:
        return candidates

    return [
        candidate
        for candidate in candidates
        if getattr(candidate, "job_id", None) == job_id
    ]


def filter_placements_by_client(placements, client_id):
    if not client_id:
        return placements

    return [
        placement
        for placement in placements
        if getattr(placement, "client_id", None) == client_id
    ]


def filter_contracts_by_client(contracts, client_id):
    if not client_id:
        return contracts

    return [
        contract
        for contract in contracts
        if getattr(contract, "client_id", None) == client_id
    ]


# ============================================================
# RELATIONSHIP VALIDATION
# ============================================================

def validate_relationships(
    client_id,
    contact_id,
    job_id,
    candidate_id,
    placement_id,
    contract_id,
    contacts,
    jobs,
    candidates,
    placements,
    contracts,
):
    errors = []

    contact = next(
        (
            item
            for item in contacts
            if getattr(item, "id", None) == contact_id
        ),
        None,
    )

    job = next(
        (
            item
            for item in jobs
            if getattr(item, "id", None) == job_id
        ),
        None,
    )

    candidate = next(
        (
            item
            for item in candidates
            if getattr(item, "id", None) == candidate_id
        ),
        None,
    )

    placement = next(
        (
            item
            for item in placements
            if getattr(item, "id", None) == placement_id
        ),
        None,
    )

    contract = next(
        (
            item
            for item in contracts
            if getattr(item, "id", None) == contract_id
        ),
        None,
    )

    # --------------------------------------------------------
    # CONTACT -> CLIENT
    # --------------------------------------------------------

    if client_id and contact:
        contact_client_id = getattr(contact, "client_id", None)

        if contact_client_id and contact_client_id != client_id:
            errors.append(
                "The selected contact does not belong to the selected client."
            )

    # --------------------------------------------------------
    # JOB -> CLIENT
    # --------------------------------------------------------

    if client_id and job:
        job_client_id = getattr(job, "client_id", None)

        if job_client_id and job_client_id != client_id:
            errors.append(
                "The selected job does not belong to the selected client."
            )

    # --------------------------------------------------------
    # CANDIDATE -> JOB
    # --------------------------------------------------------

    if job_id and candidate:
        candidate_job_id = getattr(candidate, "job_id", None)

        if candidate_job_id and candidate_job_id != job_id:
            errors.append(
                "The selected candidate does not belong to the selected job."
            )

    # --------------------------------------------------------
    # CANDIDATE -> CLIENT THROUGH JOB
    # --------------------------------------------------------

    if client_id and candidate:
        candidate_job_id = getattr(candidate, "job_id", None)

        if candidate_job_id:
            candidate_job = next(
                (
                    item
                    for item in jobs
                    if getattr(item, "id", None) == candidate_job_id
                ),
                None,
            )

            if candidate_job:
                candidate_client_id = getattr(
                    candidate_job,
                    "client_id",
                    None,
                )

                if (
                    candidate_client_id
                    and candidate_client_id != client_id
                ):
                    errors.append(
                        "The selected candidate is associated with a different client."
                    )

    # --------------------------------------------------------
    # PLACEMENT -> CLIENT
    # --------------------------------------------------------

    if client_id and placement:
        placement_client_id = getattr(
            placement,
            "client_id",
            None,
        )

        if (
            placement_client_id
            and placement_client_id != client_id
        ):
            errors.append(
                "The selected placement does not belong to the selected client."
            )

    # --------------------------------------------------------
    # CONTRACT -> CLIENT
    # --------------------------------------------------------

    if client_id and contract:
        contract_client_id = getattr(
            contract,
            "client_id",
            None,
        )

        if (
            contract_client_id
            and contract_client_id != client_id
        ):
            errors.append(
                "The selected contract does not belong to the selected client."
            )

    return errors


# ============================================================
# DROPDOWN HELPERS
# ============================================================

def get_selected_label(options, selected_id, label_function):
    if selected_id is None:
        return "None"

    for option in options:
        if getattr(option, "id", None) == selected_id:
            return label_function(option)

    return "None"


def get_option_id(options, selected_label, label_function):
    if selected_label == "None":
        return None

    for option in options:
        if label_function(option) == selected_label:
            return getattr(option, "id", None)

    return None


# ============================================================
# VALIDATION
# ============================================================

def validate_activity_subject(subject):
    errors = []

    if not subject or not subject.strip():
        errors.append("Activity subject is required.")

    elif len(subject.strip()) < 2:
        errors.append(
            "Activity subject must contain at least 2 characters."
        )

    elif len(subject.strip()) > 255:
        errors.append(
            "Activity subject cannot exceed 255 characters."
        )

    return errors


def validate_activity_dates(activity_date, due_date):
    errors = []

    if activity_date and due_date:
        if due_date < activity_date:
            errors.append(
                "Due date cannot be earlier than the activity date."
            )

    return errors


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
    st.markdown("### Edit Activity")

    current_client_id = getattr(activity, "client_id", None)
    current_contact_id = getattr(activity, "contact_id", None)
    current_employee_id = getattr(activity, "assigned_to_id", None)
    current_job_id = getattr(activity, "job_id", None)
    current_candidate_id = getattr(activity, "candidate_id", None)
    current_placement_id = getattr(activity, "placement_id", None)
    current_contract_id = getattr(activity, "contract_id", None)

    # --------------------------------------------------------
    # FILTER OPTIONS
    # --------------------------------------------------------

    filtered_contacts = filter_contacts_by_client(
        contacts,
        current_client_id,
    )

    filtered_jobs = filter_jobs_by_client(
        jobs,
        current_client_id,
    )

    filtered_candidates = filter_candidates_by_job(
        candidates,
        current_job_id,
    )

    filtered_placements = filter_placements_by_client(
        placements,
        current_client_id,
    )

    filtered_contracts = filter_contracts_by_client(
        contracts,
        current_client_id,
    )

    # Always keep the existing selected record visible.
    if (
        current_contact_id
        and not any(
            getattr(item, "id", None) == current_contact_id
            for item in filtered_contacts
        )
    ):
        current_contact = next(
            (
                item
                for item in contacts
                if getattr(item, "id", None) == current_contact_id
            ),
            None,
        )

        if current_contact:
            filtered_contacts.append(current_contact)

    if (
        current_job_id
        and not any(
            getattr(item, "id", None) == current_job_id
            for item in filtered_jobs
        )
    ):
        current_job = next(
            (
                item
                for item in jobs
                if getattr(item, "id", None) == current_job_id
            ),
            None,
        )

        if current_job:
            filtered_jobs.append(current_job)

    if (
        current_candidate_id
        and not any(
            getattr(item, "id", None) == current_candidate_id
            for item in filtered_candidates
        )
    ):
        current_candidate = next(
            (
                item
                for item in candidates
                if getattr(item, "id", None) == current_candidate_id
            ),
            None,
        )

        if current_candidate:
            filtered_candidates.append(current_candidate)

    if (
        current_placement_id
        and not any(
            getattr(item, "id", None) == current_placement_id
            for item in filtered_placements
        )
    ):
        current_placement = next(
            (
                item
                for item in placements
                if getattr(item, "id", None) == current_placement_id
            ),
            None,
        )

        if current_placement:
            filtered_placements.append(current_placement)

    if (
        current_contract_id
        and not any(
            getattr(item, "id", None) == current_contract_id
            for item in filtered_contracts
        )
    ):
        current_contract = next(
            (
                item
                for item in contracts
                if getattr(item, "id", None) == current_contract_id
            ),
            None,
        )

        if current_contract:
            filtered_contracts.append(current_contract)

    # --------------------------------------------------------
    # FORM
    # --------------------------------------------------------

    with st.form(
        key=f"edit_activity_form_{activity.id}",
        clear_on_submit=False,
    ):
        col1, col2, col3 = st.columns(3)

        with col1:
            activity_type = st.selectbox(
                "Activity Type",
                ACTIVITY_TYPES,
                index=(
                    ACTIVITY_TYPES.index(activity.activity_type)
                    if activity.activity_type in ACTIVITY_TYPES
                    else 0
                ),
            )

        with col2:
            status = st.selectbox(
                "Status",
                ACTIVITY_STATUSES,
                index=(
                    ACTIVITY_STATUSES.index(activity.status)
                    if activity.status in ACTIVITY_STATUSES
                    else 0
                ),
            )

        with col3:
            priority = st.selectbox(
                "Priority",
                PRIORITIES,
                index=(
                    PRIORITIES.index(activity.priority)
                    if activity.priority in PRIORITIES
                    else 1
                ),
            )

        subject = st.text_input(
            "Subject",
            value=safe_text(activity.subject),
            max_chars=255,
        )

        col1, col2 = st.columns(2)

        with col1:
            activity_date = st.date_input(
                "Activity Date",
                value=(
                    activity.activity_date
                    if activity.activity_date
                    else date.today()
                ),
            )

        with col2:
            due_date = st.date_input(
                "Due Date",
                value=activity.due_date,
            )

        st.markdown("#### Relationships")

        col1, col2 = st.columns(2)

        with col1:
            client_labels = ["None"] + [
                get_client_name(client)
                for client in clients
            ]

            current_client_label = get_selected_label(
                clients,
                current_client_id,
                get_client_name,
            )

            client = st.selectbox(
                "Client",
                client_labels,
                index=(
                    client_labels.index(current_client_label)
                    if current_client_label in client_labels
                    else 0
                ),
            )

        with col2:
            contact_labels = ["None"] + [
                get_contact_name(contact)
                for contact in filtered_contacts
            ]

            current_contact_label = get_selected_label(
                filtered_contacts,
                current_contact_id,
                get_contact_name,
            )

            contact = st.selectbox(
                "Client Contact",
                contact_labels,
                index=(
                    contact_labels.index(current_contact_label)
                    if current_contact_label in contact_labels
                    else 0
                ),
            )

        col1, col2 = st.columns(2)

        with col1:
            employee_labels = ["None"] + [
                get_employee_name(employee)
                for employee in employees
            ]

            current_employee_label = get_selected_label(
                employees,
                current_employee_id,
                get_employee_name,
            )

            assigned_employee = st.selectbox(
                "Assigned To",
                employee_labels,
                index=(
                    employee_labels.index(current_employee_label)
                    if current_employee_label in employee_labels
                    else 0
                ),
            )

        with col2:
            job_labels = ["None"] + [
                get_job_name(job)
                for job in filtered_jobs
            ]

            current_job_label = get_selected_label(
                filtered_jobs,
                current_job_id,
                get_job_name,
            )

            job = st.selectbox(
                "Job",
                job_labels,
                index=(
                    job_labels.index(current_job_label)
                    if current_job_label in job_labels
                    else 0
                ),
            )

        col1, col2 = st.columns(2)

        with col1:
            candidate_labels = ["None"] + [
                get_candidate_name(candidate)
                for candidate in filtered_candidates
            ]

            current_candidate_label = get_selected_label(
                filtered_candidates,
                current_candidate_id,
                get_candidate_name,
            )

            candidate = st.selectbox(
                "Candidate",
                candidate_labels,
                index=(
                    candidate_labels.index(current_candidate_label)
                    if current_candidate_label in candidate_labels
                    else 0
                ),
            )

        with col2:
            placement_labels = ["None"] + [
                get_placement_name(placement)
                for placement in filtered_placements
            ]

            current_placement_label = get_selected_label(
                filtered_placements,
                current_placement_id,
                get_placement_name,
            )

            placement = st.selectbox(
                "Placement",
                placement_labels,
                index=(
                    placement_labels.index(current_placement_label)
                    if current_placement_label in placement_labels
                    else 0
                ),
            )

        contract_labels = ["None"] + [
            get_contract_name(contract)
            for contract in filtered_contracts
        ]

        current_contract_label = get_selected_label(
            filtered_contracts,
            current_contract_id,
            get_contract_name,
        )

        contract = st.selectbox(
            "Contract",
            contract_labels,
            index=(
                contract_labels.index(current_contract_label)
                if current_contract_label in contract_labels
                else 0
            ),
        )

        notes = st.text_area(
            "Notes",
            value=safe_text(activity.notes),
            height=150,
        )

        col1, col2 = st.columns(2)

        with col1:
            save_button = st.form_submit_button(
                "Save Changes",
                use_container_width=True,
                type="primary",
            )

        with col2:
            cancel_button = st.form_submit_button(
                "Cancel",
                use_container_width=True,
            )

    if cancel_button:
        st.session_state.pop("editing_activity_id", None)
        st.rerun()

    if save_button:
        errors = []

        errors.extend(
            validate_activity_subject(subject)
        )

        errors.extend(
            validate_activity_dates(
                activity_date,
                due_date,
            )
        )

        selected_client_id = get_option_id(
            clients,
            client,
            get_client_name,
        )

        selected_contact_id = get_option_id(
            contacts,
            contact,
            get_contact_name,
        )

        selected_employee_id = get_option_id(
            employees,
            assigned_employee,
            get_employee_name,
        )

        selected_job_id = get_option_id(
            jobs,
            job,
            get_job_name,
        )

        selected_candidate_id = get_option_id(
            candidates,
            candidate,
            get_candidate_name,
        )

        selected_placement_id = get_option_id(
            placements,
            placement,
            get_placement_name,
        )

        selected_contract_id = get_option_id(
            contracts,
            contract,
            get_contract_name,
        )

        errors.extend(
            validate_relationships(
                selected_client_id,
                selected_contact_id,
                selected_job_id,
                selected_candidate_id,
                selected_placement_id,
                selected_contract_id,
                contacts,
                jobs,
                candidates,
                placements,
                contracts,
            )
        )

        if errors:
            for error in errors:
                st.error(error)

        else:
            activity.activity_type = activity_type
            activity.subject = subject.strip()
            activity.activity_date = activity_date
            activity.due_date = due_date
            activity.status = status
            activity.priority = priority
            activity.notes = notes.strip()

            activity.client_id = selected_client_id
            activity.contact_id = selected_contact_id
            activity.assigned_to_id = selected_employee_id
            activity.job_id = selected_job_id
            activity.candidate_id = selected_candidate_id
            activity.placement_id = selected_placement_id
            activity.contract_id = selected_contract_id

            update_activity(session, activity)

            st.session_state.pop(
                "editing_activity_id",
                None,
            )

            st.success("Activity updated successfully.")
            st.rerun()


# ============================================================
# MAIN SCREEN
# ============================================================

def show_activities():
    st.title("Activities")

    session = get_session()

    try:
        # ====================================================
        # LOAD DATA
        # ====================================================

        activities = (
            session.query(Activity)
            .order_by(
                Activity.activity_date.desc(),
                Activity.id.desc(),
            )
            .all()
        )

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
            .order_by(Job.id.desc())
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

        # ====================================================
        # KPI CALCULATIONS
        # ====================================================

        total_activities = len(activities)

        open_activities = [
            activity
            for activity in activities
            if getattr(activity, "status", None) == "Open"
        ]

        completed_activities = [
            activity
            for activity in activities
            if getattr(activity, "status", None) == "Completed"
        ]

        overdue_activities = [
            activity
            for activity in activities
            if activity_is_overdue(activity)
        ]

        today_activities = [
            activity
            for activity in activities
            if activity_is_due_today(activity)
        ]

        upcoming_activities = [
            activity
            for activity in activities
            if activity_is_upcoming(activity)
        ]

        high_priority_open = [
            activity
            for activity in activities
            if (
                getattr(activity, "priority", None) == "High"
                and getattr(activity, "status", None) == "Open"
            )
        ]

        no_due_date = [
            activity
            for activity in activities
            if (
                getattr(activity, "due_date", None) is None
                and getattr(activity, "status", None) == "Open"
            )
        ]

        # ====================================================
        # KPI DISPLAY
        # ====================================================

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Activities",
                total_activities,
            )

        with col2:
            st.metric(
                "Open",
                len(open_activities),
            )

        with col3:
            st.metric(
                "Overdue",
                len(overdue_activities),
            )

        with col4:
            st.metric(
                "Due Today",
                len(today_activities),
            )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Upcoming 7 Days",
                len(upcoming_activities),
            )

        with col2:
            st.metric(
                "Completed",
                len(completed_activities),
            )

        with col3:
            st.metric(
                "High Priority",
                len(high_priority_open),
            )

        with col4:
            st.metric(
                "No Due Date",
                len(no_due_date),
            )

        st.divider()

        # ====================================================
        # ADD ACTIVITY
        # ====================================================

        with st.expander(
            "➕ Add New Activity",
            expanded=False,
        ):
            st.info(
                "For best data quality, select the Client first. "
                "The CRM will validate that contacts, jobs, candidates, "
                "placements and contracts belong to the selected client."
            )

            with st.form(
                key="add_activity_form",
                clear_on_submit=True,
            ):
                col1, col2, col3 = st.columns(3)

                with col1:
                    activity_type = st.selectbox(
                        "Activity Type",
                        ACTIVITY_TYPES,
                        index=0,
                    )

                with col2:
                    status = st.selectbox(
                        "Status",
                        ACTIVITY_STATUSES,
                        index=0,
                    )

                with col3:
                    priority = st.selectbox(
                        "Priority",
                        PRIORITIES,
                        index=1,
                    )

                subject = st.text_input(
                    "Subject",
                    max_chars=255,
                    placeholder="e.g. Follow up with client regarding candidate",
                )

                col1, col2 = st.columns(2)

                with col1:
                    activity_date = st.date_input(
                        "Activity Date",
                        value=date.today(),
                    )

                with col2:
                    due_date = st.date_input(
                        "Due Date",
                        value=None,
                    )

                st.markdown("#### Relationships")

                # ------------------------------------------------
                # Client
                # ------------------------------------------------

                client_labels = ["None"] + [
                    get_client_name(client)
                    for client in clients
                ]

                selected_client = st.selectbox(
                    "Client",
                    client_labels,
                    key="new_activity_client",
                )

                selected_client_id = get_option_id(
                    clients,
                    selected_client,
                    get_client_name,
                )

                # ------------------------------------------------
                # Filter dependent records by client
                # ------------------------------------------------

                filtered_contacts = filter_contacts_by_client(
                    contacts,
                    selected_client_id,
                )

                filtered_jobs = filter_jobs_by_client(
                    jobs,
                    selected_client_id,
                )

                filtered_placements = filter_placements_by_client(
                    placements,
                    selected_client_id,
                )

                filtered_contracts = filter_contracts_by_client(
                    contracts,
                    selected_client_id,
                )

                # ------------------------------------------------
                # Contact
                # ------------------------------------------------

                contact_labels = ["None"] + [
                    get_contact_name(contact)
                    for contact in filtered_contacts
                ]

                selected_contact = st.selectbox(
                    "Client Contact",
                    contact_labels,
                )

                # ------------------------------------------------
                # Employee
                # ------------------------------------------------

                employee_labels = ["None"] + [
                    get_employee_name(employee)
                    for employee in employees
                ]

                selected_employee = st.selectbox(
                    "Assigned To",
                    employee_labels,
                )

                # ------------------------------------------------
                # Job
                # ------------------------------------------------

                job_labels = ["None"] + [
                    get_job_name(job)
                    for job in filtered_jobs
                ]

                selected_job = st.selectbox(
                    "Job",
                    job_labels,
                )

                selected_job_id = get_option_id(
                    filtered_jobs,
                    selected_job,
                    get_job_name,
                )

                # ------------------------------------------------
                # Candidate
                # ------------------------------------------------

                filtered_candidates = filter_candidates_by_job(
                    candidates,
                    selected_job_id,
                )

                candidate_labels = ["None"] + [
                    get_candidate_name(candidate)
                    for candidate in filtered_candidates
                ]

                selected_candidate = st.selectbox(
                    "Candidate",
                    candidate_labels,
                )

                # ------------------------------------------------
                # Placement
                # ------------------------------------------------

                placement_labels = ["None"] + [
                    get_placement_name(placement)
                    for placement in filtered_placements
                ]

                selected_placement = st.selectbox(
                    "Placement",
                    placement_labels,
                )

                # ------------------------------------------------
                # Contract
                # ------------------------------------------------

                contract_labels = ["None"] + [
                    get_contract_name(contract)
                    for contract in filtered_contracts
                ]

                selected_contract = st.selectbox(
                    "Contract",
                    contract_labels,
                )

                notes = st.text_area(
                    "Notes",
                    height=150,
                    placeholder="Add notes, follow-up details, outcomes, etc.",
                )

                submit_activity = st.form_submit_button(
                    "Create Activity",
                    use_container_width=True,
                    type="primary",
                )

            if submit_activity:
                errors = []

                errors.extend(
                    validate_activity_subject(subject)
                )

                errors.extend(
                    validate_activity_dates(
                        activity_date,
                        due_date,
                    )
                )

                selected_contact_id = get_option_id(
                    filtered_contacts,
                    selected_contact,
                    get_contact_name,
                )

                selected_employee_id = get_option_id(
                    employees,
                    selected_employee,
                    get_employee_name,
                )

                selected_candidate_id = get_option_id(
                    filtered_candidates,
                    selected_candidate,
                    get_candidate_name,
                )

                selected_placement_id = get_option_id(
                    filtered_placements,
                    selected_placement,
                    get_placement_name,
                )

                selected_contract_id = get_option_id(
                    filtered_contracts,
                    selected_contract,
                    get_contract_name,
                )

                errors.extend(
                    validate_relationships(
                        selected_client_id,
                        selected_contact_id,
                        selected_job_id,
                        selected_candidate_id,
                        selected_placement_id,
                        selected_contract_id,
                        contacts,
                        jobs,
                        candidates,
                        placements,
                        contracts,
                    )
                )

                if errors:
                    for error in errors:
                        st.error(error)

                else:
                    new_activity = Activity(
                        activity_type=activity_type,
                        subject=subject.strip(),
                        activity_date=activity_date,
                        due_date=due_date,
                        status=status,
                        priority=priority,
                        notes=notes.strip(),
                        client_id=selected_client_id,
                        contact_id=selected_contact_id,
                        assigned_to_id=selected_employee_id,
                        job_id=selected_job_id,
                        candidate_id=selected_candidate_id,
                        placement_id=selected_placement_id,
                        contract_id=selected_contract_id,
                    )

                    save_activity(
                        session,
                        new_activity,
                    )

                    st.success(
                        "Activity created successfully."
                    )

                    st.rerun()

        # ====================================================
        # FILTERS
        # ====================================================

        st.subheader("Activity Register")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            filter_client_labels = ["All Clients"] + [
                get_client_name(client)
                for client in clients
            ]

            filter_client = st.selectbox(
                "Filter by Client",
                filter_client_labels,
            )

        with col2:
            filter_employee_labels = ["All Employees"] + [
                get_employee_name(employee)
                for employee in employees
            ]

            filter_employee = st.selectbox(
                "Filter by Assigned To",
                filter_employee_labels,
            )

        with col3:
            filter_type = st.selectbox(
                "Filter by Type",
                ["All Types"] + ACTIVITY_TYPES,
            )

        with col4:
            filter_status = st.selectbox(
                "Filter by Status",
                ["All Statuses"] + ACTIVITY_STATUSES,
            )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            filter_priority = st.selectbox(
                "Filter by Priority",
                ["All Priorities"] + PRIORITIES,
            )

        with col2:
            filter_timing = st.selectbox(
                "Timing",
                [
                    "All",
                    "Overdue",
                    "Due Today",
                    "Upcoming 7 Days",
                    "Future",
                    "No Due Date",
                ],
            )

        with col3:
            filter_job_labels = ["All Jobs"] + [
                get_job_name(job)
                for job in jobs
            ]

            filter_job = st.selectbox(
                "Filter by Job",
                filter_job_labels,
            )

        with col4:
            search = st.text_input(
                "Search",
                placeholder="Search activities...",
            )

        # ====================================================
        # DATE FILTER
        # ====================================================

        col1, col2 = st.columns(2)

        with col1:
            date_from = st.date_input(
                "Activity Date From",
                value=None,
            )

        with col2:
            date_to = st.date_input(
                "Activity Date To",
                value=None,
            )

        # ====================================================
        # APPLY FILTERS
        # ====================================================

        filtered_activities = list(activities)

        # Client
        if filter_client != "All Clients":
            selected_client_filter_id = get_option_id(
                clients,
                filter_client,
                get_client_name,
            )

            filtered_activities = [
                activity
                for activity in filtered_activities
                if getattr(activity, "client_id", None)
                == selected_client_filter_id
            ]

        # Employee
        if filter_employee != "All Employees":
            selected_employee_filter_id = get_option_id(
                employees,
                filter_employee,
                get_employee_name,
            )

            filtered_activities = [
                activity
                for activity in filtered_activities
                if getattr(activity, "assigned_to_id", None)
                == selected_employee_filter_id
            ]

        # Type
        if filter_type != "All Types":
            filtered_activities = [
                activity
                for activity in filtered_activities
                if getattr(activity, "activity_type", None)
                == filter_type
            ]

        # Status
        if filter_status != "All Statuses":
            filtered_activities = [
                activity
                for activity in filtered_activities
                if getattr(activity, "status", None)
                == filter_status
            ]

        # Priority
        if filter_priority != "All Priorities":
            filtered_activities = [
                activity
                for activity in filtered_activities
                if getattr(activity, "priority", None)
                == filter_priority
            ]

        # Job
        if filter_job != "All Jobs":
            selected_job_filter_id = get_option_id(
                jobs,
                filter_job,
                get_job_name,
            )

            filtered_activities = [
                activity
                for activity in filtered_activities
                if getattr(activity, "job_id", None)
                == selected_job_filter_id
            ]

        # Timing
        if filter_timing == "Overdue":
            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity_is_overdue(activity)
            ]

        elif filter_timing == "Due Today":
            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity_is_due_today(activity)
            ]

        elif filter_timing == "Upcoming 7 Days":
            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity_is_upcoming(activity)
            ]

        elif filter_timing == "Future":
            filtered_activities = [
                activity
                for activity in filtered_activities
                if activity_is_future(activity)
            ]

        elif filter_timing == "No Due Date":
            filtered_activities = [
                activity
                for activity in filtered_activities
                if getattr(activity, "due_date", None) is None
            ]

        # Date From
        if date_from:
            filtered_activities = [
                activity
                for activity in filtered_activities
                if (
                    getattr(activity, "activity_date", None)
                    and activity.activity_date >= date_from
                )
            ]

        # Date To
        if date_to:
            filtered_activities = [
                activity
                for activity in filtered_activities
                if (
                    getattr(activity, "activity_date", None)
                    and activity.activity_date <= date_to
                )
            ]

        # Search
        if search.strip():
            search_text = search.strip().lower()

            filtered_activities = [
                activity
                for activity in filtered_activities
                if search_text
                in build_activity_search_text(activity)
            ]

        # ====================================================
        # RESULTS SUMMARY
        # ====================================================

        st.caption(
            f"Showing {len(filtered_activities)} "
            f"of {len(activities)} activities"
        )

        if not filtered_activities:
            st.info(
                "No activities match the selected filters."
            )
            return

        # ====================================================
        # SORT
        # ====================================================

        def activity_sort_key(activity):
            if activity_is_overdue(activity):
                timing_rank = 0
            elif activity_is_due_today(activity):
                timing_rank = 1
            elif activity_is_upcoming(activity):
                timing_rank = 2
            else:
                timing_rank = 3

            due_date = getattr(
                activity,
                "due_date",
                None,
            )

            if due_date is None:
                due_sort = date.max
            else:
                due_sort = due_date

            activity_date_value = getattr(
                activity,
                "activity_date",
                None,
            )

            if activity_date_value is None:
                activity_date_value = date.min

            return (
                timing_rank,
                due_sort,
                -activity_date_value.toordinal(),
                -getattr(activity, "id", 0),
            )

        filtered_activities.sort(
            key=activity_sort_key
        )

        # ====================================================
        # EDIT MODE
        # ====================================================

        editing_activity_id = st.session_state.get(
            "editing_activity_id"
        )

        if editing_activity_id:
            editing_activity = next(
                (
                    activity
                    for activity in activities
                    if getattr(activity, "id", None)
                    == editing_activity_id
                ),
                None,
            )

            if editing_activity:
                st.divider()

                render_edit_activity(
                    session=session,
                    activity=editing_activity,
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
        # ACTIVITY CARDS
        # ====================================================

        for activity in filtered_activities:
            status = getattr(
                activity,
                "status",
                "Open",
            )

            priority = getattr(
                activity,
                "priority",
                "Medium",
            )

            due_date = getattr(
                activity,
                "due_date",
                None,
            )

            activity_date_value = getattr(
                activity,
                "activity_date",
                None,
            )

            client = getattr(
                activity,
                "client",
                None,
            )

            contact = getattr(
                activity,
                "contact",
                None,
            )

            employee = getattr(
                activity,
                "assigned_employee",
                None,
            )

            job = getattr(
                activity,
                "job",
                None,
            )

            candidate = getattr(
                activity,
                "candidate",
                None,
            )

            placement = getattr(
                activity,
                "placement",
                None,
            )

            contract = getattr(
                activity,
                "contract",
                None,
            )

            # ------------------------------------------------
            # STATUS DISPLAY
            # ------------------------------------------------

            if status == "Completed":
                status_icon = "✅"
            elif status == "Cancelled":
                status_icon = "❌"
            elif activity_is_overdue(activity):
                status_icon = "🔴"
            elif activity_is_due_today(activity):
                status_icon = "🟠"
            elif activity_is_upcoming(activity):
                status_icon = "🟡"
            else:
                status_icon = "🔵"

            if priority == "High":
                priority_icon = "🔴"
            elif priority == "Medium":
                priority_icon = "🟠"
            else:
                priority_icon = "🟢"

            subject = safe_text(
                getattr(activity, "subject", None),
                "Untitled Activity",
            )

            activity_type = safe_text(
                getattr(activity, "activity_type", None),
                "Activity",
            )

            # ------------------------------------------------
            # CARD
            # ------------------------------------------------

            with st.container(border=True):
                col1, col2 = st.columns(
                    [5, 2]
                )

                with col1:
                    st.markdown(
                        f"### {status_icon} {subject}"
                    )

                    st.caption(
                        f"{activity_type}  •  "
                        f"{priority_icon} {priority}  •  "
                        f"{status}"
                    )

                with col2:
                    if activity_date_value:
                        st.write(
                            f"**Activity:** "
                            f"{activity_date_value.strftime('%d %b %Y')}"
                        )

                    if due_date:
                        if activity_is_overdue(activity):
                            st.error(
                                f"Overdue: "
                                f"{due_date.strftime('%d %b %Y')}"
                            )

                        elif activity_is_due_today(activity):
                            st.warning(
                                "Due today"
                            )

                        else:
                            st.write(
                                f"**Due:** "
                                f"{due_date.strftime('%d %b %Y')}"
                            )

                    else:
                        st.write(
                            "**Due:** No due date"
                        )

                # --------------------------------------------
                # RELATIONSHIPS
                # --------------------------------------------

                relationship_parts = []

                if client:
                    relationship_parts.append(
                        f"**Client:** {get_client_name(client)}"
                    )

                if contact:
                    relationship_parts.append(
                        f"**Contact:** {get_contact_name(contact)}"
                    )

                if employee:
                    relationship_parts.append(
                        f"**Assigned:** {get_employee_name(employee)}"
                    )

                if job:
                    relationship_parts.append(
                        f"**Job:** {get_job_name(job)}"
                    )

                if candidate:
                    relationship_parts.append(
                        f"**Candidate:** {get_candidate_name(candidate)}"
                    )

                if placement:
                    relationship_parts.append(
                        f"**Placement:** {get_placement_name(placement)}"
                    )

                if contract:
                    relationship_parts.append(
                        f"**Contract:** {get_contract_name(contract)}"
                    )

                if relationship_parts:
                    st.markdown(
                        "  •  ".join(relationship_parts)
                    )

                notes = safe_text(
                    getattr(activity, "notes", None)
                )

                if notes:
                    st.markdown("**Notes**")
                    st.write(notes)

                # --------------------------------------------
                # ACTIONS
                # --------------------------------------------

                action1, action2, action3, action4 = st.columns(
                    4
                )

                with action1:
                    if (
                        status == "Open"
                        and st.button(
                            "✅ Complete",
                            key=f"complete_{activity.id}",
                            use_container_width=True,
                        )
                    ):
                        activity.status = "Completed"

                        update_activity(
                            session,
                            activity,
                        )

                        st.success(
                            "Activity completed."
                        )

                        st.rerun()

                with action2:
                    if (
                        status == "Open"
                        and st.button(
                            "❌ Cancel",
                            key=f"cancel_{activity.id}",
                            use_container_width=True,
                        )
                    ):
                        activity.status = "Cancelled"

                        update_activity(
                            session,
                            activity,
                        )

                        st.success(
                            "Activity cancelled."
                        )

                        st.rerun()

                with action3:
                    if st.button(
                        "✏️ Edit",
                        key=f"edit_{activity.id}",
                        use_container_width=True,
                    ):
                        st.session_state[
                            "editing_activity_id"
                        ] = activity.id

                        st.rerun()

                with action4:
                    if st.button(
                        "🗑️ Delete",
                        key=f"delete_{activity.id}",
                        use_container_width=True,
                    ):
                        st.session_state[
                            f"confirm_delete_activity_{activity.id}"
                        ] = True

                        st.rerun()

                # --------------------------------------------
                # DELETE CONFIRMATION
                # --------------------------------------------

                if st.session_state.get(
                    f"confirm_delete_activity_{activity.id}",
                    False,
                ):
                    st.warning(
                        "Are you sure you want to permanently "
                        "delete this activity?"
                    )

                    confirm_col1, confirm_col2 = st.columns(2)

                    with confirm_col1:
                        if st.button(
                            "Yes, Delete",
                            key=f"confirm_yes_{activity.id}",
                            use_container_width=True,
                            type="primary",
                        ):
                            delete_activity(
                                session,
                                activity,
                            )

                            st.session_state.pop(
                                f"confirm_delete_activity_{activity.id}",
                                None,
                            )

                            st.success(
                                "Activity deleted."
                            )

                            st.rerun()

                    with confirm_col2:
                        if st.button(
                            "Keep Activity",
                            key=f"confirm_no_{activity.id}",
                            use_container_width=True,
                        ):
                            st.session_state.pop(
                                f"confirm_delete_activity_{activity.id}",
                                None,
                            )

                            st.rerun()

    finally:
        session.close()