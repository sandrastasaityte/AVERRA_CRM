
import streamlit as st
from datetime import date

from database import get_session
from models import Placement, Client, Employee, Job


# ============================================================
# CONSTANTS
# ============================================================

PLACEMENT_STATUSES = [
    "Active",
    "Scheduled",
    "Completed",
    "Terminated",
]

BILLING_FREQUENCIES = [
    "Monthly",
    "Weekly",
    "Daily",
    "Hourly",
]

CURRENCIES = [
    "GBP",
    "EUR",
    "USD",
    "INR",
]


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    """Safely return cleaned text."""

    if value is None:
        return ""

    return str(value).strip()


def get_employee_name(employee):
    """Return employee full name safely."""

    if not employee:
        return "Unknown Employee"

    first_name = clean_text(
        employee.first_name
    )

    last_name = clean_text(
        employee.last_name
    )

    full_name = " ".join(
        part
        for part in [
            first_name,
            last_name,
        ]
        if part
    )

    return full_name or "Unknown Employee"


def get_client_name(client):
    """Return client company name safely."""

    if not client:
        return "Unknown Client"

    return (
        clean_text(client.company_name)
        or "Unknown Client"
    )


def get_job_label(job):
    """Return readable job label."""

    if not job:
        return "No Job"

    position = (
        clean_text(job.position)
        or f"Job #{job.id}"
    )

    client_name = get_client_name(
        job.client
    )

    return (
        f"{position} — {client_name}"
    )


def get_status_icon(status):
    """Return visual status indicator."""

    icons = {
        "Active": "🟢",
        "Scheduled": "🔵",
        "Completed": "⚪",
        "Terminated": "🔴",
    }

    return icons.get(
        status,
        "⚪",
    )


def get_status(placement):
    """Return safe placement status."""

    return (
        clean_text(placement.status)
        or "Active"
    )


def get_currency(placement):
    """Return safe currency."""

    return (
        clean_text(placement.currency)
        or "GBP"
    )


def get_client_fee(placement):
    """Return client fee safely."""

    return float(
        placement.client_monthly_fee or 0
    )


def get_worker_cost(placement):
    """Return worker cost safely."""

    return float(
        placement.worker_monthly_cost or 0
    )


def calculate_margin(placement):
    """Calculate gross margin safely."""

    return (
        get_client_fee(placement)
        - get_worker_cost(placement)
    )


def calculate_margin_percentage(placement):
    """Calculate gross margin percentage safely."""

    client_fee = get_client_fee(
        placement
    )

    if client_fee <= 0:
        return 0.0

    margin = calculate_margin(
        placement
    )

    return (
        margin / client_fee
    ) * 100


def get_days_active(placement):
    """Return number of days since placement started."""

    if not placement.start_date:
        return None

    end_date = (
        placement.end_date
        or date.today()
    )

    return max(
        0,
        (end_date - placement.start_date).days,
    )


def has_contracts(placement):
    """
    Safely check whether the placement has
    contracts attached.
    """

    contracts = getattr(
        placement,
        "contracts",
        None,
    )

    if contracts is None:
        return False

    try:
        return len(contracts) > 0

    except TypeError:
        return False


def is_active_or_scheduled(placement):
    """Return whether placement is currently active/scheduled."""

    return get_status(placement) in [
        "Active",
        "Scheduled",
    ]


# ============================================================
# MAIN SCREEN
# ============================================================

def show_placements():

    st.title("Placements")

    st.caption(
        "Manage active and historical employee placements."
    )

    session = get_session()

    # ========================================================
    # SESSION STATE
    # ========================================================

    if "editing_placement_id" not in st.session_state:

        st.session_state.editing_placement_id = None

    if "confirm_delete_placement_id" not in st.session_state:

        st.session_state.confirm_delete_placement_id = None

    try:

        # ====================================================
        # LOAD DATA
        # ====================================================

        clients = (
            session.query(Client)
            .order_by(
                Client.company_name.asc()
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
            .order_by(
                Job.position.asc()
            )
            .all()
        )

        # ====================================================
        # CHECK REQUIRED DATA
        # ====================================================

        if not clients:

            st.warning(
                "Please add a client before creating a placement."
            )

            return

        if not employees:

            st.warning(
                "Please add an employee before creating a placement."
            )

            return

        # ====================================================
        # EDITING PLACEMENT
        # ====================================================

        editing_placement = None

        editing_id = (
            st.session_state.editing_placement_id
        )

        if editing_id is not None:

            editing_placement = session.get(
                Placement,
                editing_id,
            )

            if editing_placement is None:

                st.session_state.editing_placement_id = (
                    None
                )

        # ====================================================
        # ADD / EDIT PLACEMENT
        # ====================================================

        if editing_placement:

            st.subheader(
                "Edit Placement"
            )

        else:

            st.subheader(
                "Add Placement"
            )

        # ====================================================
        # CLIENT OPTIONS
        # ====================================================

        client_options = {}

        for client in clients:

            client_name = get_client_name(
                client
            )

            label = (
                f"{client_name} "
                f"(ID: {client.id})"
            )

            client_options[label] = client.id

        client_labels = list(
            client_options.keys()
        )

        client_ids = list(
            client_options.values()
        )

        # ====================================================
        # EMPLOYEE OPTIONS
        # ====================================================

        employee_options = {}

        for employee in employees:

            employee_name = get_employee_name(
                employee
            )

            label = (
                f"{employee_name} "
                f"(ID: {employee.id})"
            )

            employee_options[label] = employee.id

        employee_labels = list(
            employee_options.keys()
        )

        employee_ids = list(
            employee_options.values()
        )

        # ====================================================
        # JOB OPTIONS
        # ====================================================

        job_options = {}

        for job in jobs:

            label = (
                f"{get_job_label(job)} "
                f"(ID: {job.id})"
            )

            job_options[label] = job.id

        job_labels = list(
            job_options.keys()
        )

        # ====================================================
        # CURRENT CLIENT
        # ====================================================

        if editing_placement:

            current_client_id = (
                editing_placement.client_id
            )

            client_index = (
                client_ids.index(
                    current_client_id
                )
                if current_client_id
                in client_ids
                else 0
            )

        else:

            client_index = 0

        # ====================================================
        # CURRENT EMPLOYEE
        # ====================================================

        if editing_placement:

            current_employee_id = (
                editing_placement.employee_id
            )

            employee_index = (
                employee_ids.index(
                    current_employee_id
                )
                if current_employee_id
                in employee_ids
                else 0
            )

        else:

            employee_index = 0

        # ====================================================
        # CURRENT JOB
        # ====================================================

        job_selection_labels = [
            "No Job"
        ] + job_labels

        current_job_label = "No Job"

        if (
            editing_placement
            and editing_placement.job_id
        ):

            for label, job_id in job_options.items():

                if (
                    job_id
                    == editing_placement.job_id
                ):

                    current_job_label = label

                    break

        job_index = (
            job_selection_labels.index(
                current_job_label
            )
            if current_job_label
            in job_selection_labels
            else 0
        )

        # ====================================================
        # FORM
        # ====================================================

        form_key = (
            "edit_placement_form"
            if editing_placement
            else "add_placement_form"
        )

        with st.form(form_key):

            # =================================================
            # CLIENT / EMPLOYEE / JOB
            # =================================================

            col1, col2 = st.columns(2)

            with col1:

                selected_client = st.selectbox(
                    "Client *",
                    client_labels,
                    index=client_index,
                )

                selected_employee = st.selectbox(
                    "Employee *",
                    employee_labels,
                    index=employee_index,
                )

            with col2:

                selected_job = st.selectbox(
                    "Job",
                    job_selection_labels,
                    index=job_index,
                )

                position = st.text_input(
                    "Position *",
                    value=(
                        clean_text(
                            editing_placement.position
                        )
                        if editing_placement
                        else ""
                    ),
                    placeholder=(
                        "Example: Finance Specialist"
                    ),
                )

            # =================================================
            # DATES / STATUS
            # =================================================

            col1, col2 = st.columns(2)

            with col1:

                start_date = st.date_input(
                    "Start Date",
                    value=(
                        editing_placement.start_date
                        if (
                            editing_placement
                            and editing_placement.start_date
                        )
                        else date.today()
                    ),
                )

            with col2:

                end_date = st.date_input(
                    "End Date",
                    value=(
                        editing_placement.end_date
                        if (
                            editing_placement
                            and editing_placement.end_date
                        )
                        else None
                    ),
                )

            col1, col2 = st.columns(2)

            with col1:

                current_status = (
                    get_status(
                        editing_placement
                    )
                    if editing_placement
                    else "Scheduled"
                )

                status_index = (
                    PLACEMENT_STATUSES.index(
                        current_status
                    )
                    if current_status
                    in PLACEMENT_STATUSES
                    else 0
                )

                status = st.selectbox(
                    "Status",
                    PLACEMENT_STATUSES,
                    index=status_index,
                )

            with col2:

                current_frequency = (
                    clean_text(
                        editing_placement.billing_frequency
                    )
                    if editing_placement
                    else "Monthly"
                )

                frequency_index = (
                    BILLING_FREQUENCIES.index(
                        current_frequency
                    )
                    if current_frequency
                    in BILLING_FREQUENCIES
                    else 0
                )

                billing_frequency = st.selectbox(
                    "Billing Frequency",
                    BILLING_FREQUENCIES,
                    index=frequency_index,
                )

            # =================================================
            # FINANCIALS
            # =================================================

            st.subheader(
                "Financials"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                client_monthly_fee = st.number_input(
                    "Client Monthly Fee",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    value=(
                        get_client_fee(
                            editing_placement
                        )
                        if editing_placement
                        else 0.0
                    ),
                )

            with col2:

                worker_monthly_cost = st.number_input(
                    "Worker Monthly Cost",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    value=(
                        get_worker_cost(
                            editing_placement
                        )
                        if editing_placement
                        else 0.0
                    ),
                )

            with col3:

                current_currency = (
                    get_currency(
                        editing_placement
                    )
                    if editing_placement
                    else "GBP"
                )

                currency_index = (
                    CURRENCIES.index(
                        current_currency
                    )
                    if current_currency
                    in CURRENCIES
                    else 0
                )

                currency = st.selectbox(
                    "Currency",
                    CURRENCIES,
                    index=currency_index,
                )

            notes = st.text_area(
                "Notes",
                value=(
                    clean_text(
                        editing_placement.notes
                    )
                    if editing_placement
                    else ""
                ),
                placeholder=(
                    "Additional placement information..."
                ),
            )

            # =================================================
            # SUBMIT
            # =================================================

            submitted = st.form_submit_button(
                "Save Changes"
                if editing_placement
                else "Create Placement",
                use_container_width=True,
            )

            if submitted:

                position_clean = (
                    position.strip()
                )

                notes_clean = (
                    notes.strip()
                )

                selected_client_id = (
                    client_options[
                        selected_client
                    ]
                )

                selected_employee_id = (
                    employee_options[
                        selected_employee
                    ]
                )

                selected_job_id = None

                if selected_job != "No Job":

                    selected_job_id = (
                        job_options[
                            selected_job
                        ]
                    )

                # =============================================
                # VALIDATION
                # =============================================

                if not position_clean:

                    st.error(
                        "Position is required."
                    )

                elif end_date and (
                    end_date < start_date
                ):

                    st.error(
                        "End Date cannot be "
                        "before Start Date."
                    )

                elif client_monthly_fee < 0:

                    st.error(
                        "Client monthly fee "
                        "cannot be negative."
                    )

                elif worker_monthly_cost < 0:

                    st.error(
                        "Worker monthly cost "
                        "cannot be negative."
                    )

                else:

                    # =========================================
                    # JOB / CLIENT VALIDATION
                    # =========================================

                    selected_job_object = None

                    if selected_job_id:

                        selected_job_object = (
                            session.get(
                                Job,
                                selected_job_id,
                            )
                        )

                    if (
                        selected_job_object
                        and selected_job_object.client_id
                        != selected_client_id
                    ):

                        st.error(
                            "The selected job belongs "
                            "to a different client. "
                            "Please select a matching client "
                            "and job."
                        )

                    else:

                        # =====================================
                        # DUPLICATE ACTIVE PLACEMENT CHECK
                        # =====================================

                        duplicate_placement = None

                        if (
                            selected_job_id
                            and status
                            in [
                                "Active",
                                "Scheduled",
                            ]
                        ):

                            existing_query = (
                                session.query(
                                    Placement
                                )
                                .filter(
                                    Placement.employee_id
                                    == selected_employee_id,
                                    Placement.job_id
                                    == selected_job_id,
                                    Placement.status.in_(
                                        [
                                            "Active",
                                            "Scheduled",
                                        ]
                                    ),
                                )
                            )

                            if editing_placement:

                                existing_query = (
                                    existing_query.filter(
                                        Placement.id
                                        != editing_placement.id
                                    )
                                )

                            duplicate_placement = (
                                existing_query.first()
                            )

                        if duplicate_placement:

                            st.error(
                                "This employee already has "
                                "an active or scheduled "
                                "placement for this job."
                            )

                        else:

                            # =================================
                            # UPDATE
                            # =================================

                            if editing_placement:

                                editing_placement.client_id = (
                                    selected_client_id
                                )

                                editing_placement.employee_id = (
                                    selected_employee_id
                                )

                                editing_placement.job_id = (
                                    selected_job_id
                                )

                                editing_placement.position = (
                                    position_clean
                                )

                                editing_placement.start_date = (
                                    start_date
                                )

                                editing_placement.end_date = (
                                    end_date
                                )

                                editing_placement.status = (
                                    status
                                )

                                editing_placement.billing_frequency = (
                                    billing_frequency
                                )

                                editing_placement.client_monthly_fee = (
                                    client_monthly_fee
                                )

                                editing_placement.worker_monthly_cost = (
                                    worker_monthly_cost
                                )

                                editing_placement.currency = (
                                    currency
                                )

                                editing_placement.notes = (
                                    notes_clean
                                )

                                try:

                                    session.commit()

                                    st.session_state.editing_placement_id = (
                                        None
                                    )

                                    st.success(
                                        "Placement updated successfully."
                                    )

                                    st.rerun()

                                except Exception as e:

                                    session.rollback()

                                    st.error(
                                        "Could not update "
                                        f"placement: {e}"
                                    )

                            # =================================
                            # CREATE
                            # =================================

                            else:

                                placement = Placement(
                                    client_id=(
                                        selected_client_id
                                    ),
                                    employee_id=(
                                        selected_employee_id
                                    ),
                                    job_id=(
                                        selected_job_id
                                    ),
                                    position=(
                                        position_clean
                                    ),
                                    start_date=(
                                        start_date
                                    ),
                                    end_date=(
                                        end_date
                                    ),
                                    client_monthly_fee=(
                                        client_monthly_fee
                                    ),
                                    worker_monthly_cost=(
                                        worker_monthly_cost
                                    ),
                                    currency=(
                                        currency
                                    ),
                                    billing_frequency=(
                                        billing_frequency
                                    ),
                                    status=status,
                                    notes=notes_clean,
                                )

                                try:

                                    session.add(
                                        placement
                                    )

                                    session.commit()

                                    st.success(
                                        "Placement created successfully."
                                    )

                                    st.rerun()

                                except Exception as e:

                                    session.rollback()

                                    st.error(
                                        "Could not create "
                                        f"placement: {e}"
                                    )

        # ====================================================
        # CANCEL EDITING
        # ====================================================

        if editing_placement:

            if st.button(
                "Cancel Editing",
                use_container_width=True,
            ):

                st.session_state.editing_placement_id = (
                    None
                )

                st.rerun()

        # ====================================================
        # PLACEMENT REGISTER
        # ====================================================

        st.divider()

        st.subheader(
            "Placement Register"
        )

        placements = (
            session.query(Placement)
            .order_by(
                Placement.start_date.desc(),
                Placement.id.desc(),
            )
            .all()
        )

        if not placements:

            st.info(
                "No placements have been created yet."
            )

            return

        # ====================================================
        # KPI SUMMARY
        # ====================================================

        total_placements = len(
            placements
        )

        active_placements = sum(
            1
            for placement in placements
            if get_status(placement)
            == "Active"
        )

        scheduled_placements = sum(
            1
            for placement in placements
            if get_status(placement)
            == "Scheduled"
        )

        completed_placements = sum(
            1
            for placement in placements
            if get_status(placement)
            == "Completed"
        )

        total_client_fees = sum(
            get_client_fee(placement)
            for placement in placements
            if get_status(placement)
            == "Active"
        )

        total_worker_costs = sum(
            get_worker_cost(placement)
            for placement in placements
            if get_status(placement)
            == "Active"
        )

        total_gross_margin = (
            total_client_fees
            - total_worker_costs
        )

        k1, k2, k3, k4, k5 = (
            st.columns(5)
        )

        with k1:

            st.metric(
                "Total Placements",
                total_placements,
            )

        with k2:

            st.metric(
                "Active",
                active_placements,
            )

        with k3:

            st.metric(
                "Scheduled",
                scheduled_placements,
            )

        with k4:

            st.metric(
                "Completed",
                completed_placements,
            )

        with k5:

            st.metric(
                "Active Gross Margin",
                f"£{total_gross_margin:,.2f}",
            )

        st.caption(
            "Active placement fees and costs are shown "
            "as entered and are not converted between currencies."
        )

        # ====================================================
        # FILTERS
        # ====================================================

        filter_col1, filter_col2, filter_col3 = (
            st.columns(3)
        )

        with filter_col1:

            status_filter = st.selectbox(
                "Status",
                ["All"] + PLACEMENT_STATUSES,
            )

        with filter_col2:

            search = st.text_input(
                "Search",
                placeholder=(
                    "Employee, client, "
                    "job or position..."
                ),
            )

        with filter_col3:

            currency_filter = st.selectbox(
                "Currency",
                ["All"] + CURRENCIES,
            )

        # ====================================================
        # APPLY FILTERS
        # ====================================================

        filtered_placements = placements

        if status_filter != "All":

            filtered_placements = [
                placement
                for placement
                in filtered_placements
                if get_status(
                    placement
                ) == status_filter
            ]

        if currency_filter != "All":

            filtered_placements = [
                placement
                for placement
                in filtered_placements
                if get_currency(
                    placement
                ) == currency_filter
            ]

        if search.strip():

            search_lower = (
                search.strip().lower()
            )

            filtered_placements = [
                placement
                for placement
                in filtered_placements
                if (
                    search_lower
                    in clean_text(
                        placement.position
                    ).lower()
                )
                or (
                    placement.client
                    and search_lower
                    in get_client_name(
                        placement.client
                    ).lower()
                )
                or (
                    placement.employee
                    and search_lower
                    in get_employee_name(
                        placement.employee
                    ).lower()
                )
                or (
                    placement.job
                    and search_lower
                    in get_job_label(
                        placement.job
                    ).lower()
                )
            ]

        # ====================================================
        # RESULT COUNT
        # ====================================================

        st.caption(
            f"Showing "
            f"{len(filtered_placements)} "
            f"of "
            f"{len(placements)} "
            f"placement(s)"
        )

        if not filtered_placements:

            st.info(
                "No placements match your filters."
            )

            return

        # ====================================================
        # DISPLAY PLACEMENTS
        # ====================================================

        for placement in filtered_placements:

            employee_name = get_employee_name(
                placement.employee
            )

            client_name = get_client_name(
                placement.client
            )

            job_name = get_job_label(
                placement.job
            )

            status = get_status(
                placement
            )

            currency = get_currency(
                placement
            )

            client_fee = get_client_fee(
                placement
            )

            worker_cost = get_worker_cost(
                placement
            )

            margin = calculate_margin(
                placement
            )

            margin_percentage = (
                calculate_margin_percentage(
                    placement
                )
            )

            with st.container(
                border=True
            ):

                # ==========================================
                # MAIN ROW
                # ==========================================

                col1, col2, col3, col4, col5 = (
                    st.columns(
                        [2.2, 2.3, 2, 2, 1.8]
                    )
                )

                # ------------------------------------------
                # PLACEMENT
                # ------------------------------------------

                with col1:

                    st.write(
                        f"**#{placement.id} — "
                        f"{clean_text(placement.position)}**"
                    )

                    st.caption(
                        employee_name
                    )

                # ------------------------------------------
                # CLIENT / JOB
                # ------------------------------------------

                with col2:

                    st.write(
                        f"**{client_name}**"
                    )

                    if placement.job:

                        st.caption(
                            job_name
                        )

                # ------------------------------------------
                # DATES / STATUS
                # ------------------------------------------

                with col3:

                    st.write(
                        f"{get_status_icon(status)} "
                        f"**{status}**"
                    )

                    if placement.start_date:

                        st.caption(
                            "Start: "
                            f"{placement.start_date.strftime('%d %b %Y')}"
                        )

                    if placement.end_date:

                        st.caption(
                            "End: "
                            f"{placement.end_date.strftime('%d %b %Y')}"
                        )

                # ------------------------------------------
                # FINANCIALS
                # ------------------------------------------

                with col4:

                    st.write(
                        f"Client: **"
                        f"{currency} "
                        f"{client_fee:,.2f}"
                        f"**"
                    )

                    st.caption(
                        f"Worker: "
                        f"{currency} "
                        f"{worker_cost:,.2f}"
                    )

                    st.caption(
                        f"Margin: "
                        f"{currency} "
                        f"{margin:,.2f}"
                    )

                # ------------------------------------------
                # ACTIONS
                # ------------------------------------------

                with col5:

                    st.write(
                        f"**{margin_percentage:.1f}%**"
                    )

                    edit_button = st.button(
                        "Edit",
                        key=(
                            f"edit_placement_"
                            f"{placement.id}"
                        ),
                        use_container_width=True,
                    )

                    delete_button = st.button(
                        "Delete",
                        key=(
                            f"delete_placement_"
                            f"{placement.id}"
                        ),
                        use_container_width=True,
                    )

                # ==========================================
                # EDIT
                # ==========================================

                if edit_button:

                    st.session_state.editing_placement_id = (
                        placement.id
                    )

                    st.session_state.confirm_delete_placement_id = (
                        None
                    )

                    st.rerun()

                # ==========================================
                # DELETE REQUEST
                # ==========================================

                if delete_button:

                    st.session_state.confirm_delete_placement_id = (
                        placement.id
                    )

                    st.session_state.editing_placement_id = (
                        None
                    )

                    st.rerun()

                # ==========================================
                # DELETE CONFIRMATION
                # ==========================================

                if (
                    st.session_state.confirm_delete_placement_id
                    == placement.id
                ):

                    if has_contracts(
                        placement
                    ):

                        st.warning(
                            "This placement cannot be "
                            "deleted because it has "
                            "contracts attached."
                        )

                        close_button = st.button(
                            "Close",
                            key=(
                                f"close_delete_"
                                f"{placement.id}"
                            ),
                            use_container_width=True,
                        )

                        if close_button:

                            st.session_state.confirm_delete_placement_id = (
                                None
                            )

                            st.rerun()

                    else:

                        st.warning(
                            f"Are you sure you want "
                            f"to delete placement "
                            f"**#{placement.id} — "
                            f"{clean_text(placement.position)}**?"
                        )

                        confirm_col1, confirm_col2 = (
                            st.columns(2)
                        )

                        with confirm_col1:

                            confirm_delete = st.button(
                                "Yes, Delete Placement",
                                key=(
                                    f"confirm_delete_"
                                    f"{placement.id}"
                                ),
                                type="primary",
                                use_container_width=True,
                            )

                        with confirm_col2:

                            cancel_delete = st.button(
                                "Cancel",
                                key=(
                                    f"cancel_delete_"
                                    f"{placement.id}"
                                ),
                                use_container_width=True,
                            )

                        if cancel_delete:

                            st.session_state.confirm_delete_placement_id = (
                                None
                            )

                            st.rerun()

                        if confirm_delete:

                            try:

                                session.delete(
                                    placement
                                )

                                session.commit()

                                st.session_state.confirm_delete_placement_id = (
                                    None
                                )

                                st.success(
                                    "Placement deleted successfully."
                                )

                                st.rerun()

                            except Exception as e:

                                session.rollback()

                                st.session_state.confirm_delete_placement_id = (
                                    None
                                )

                                st.error(
                                    "Could not delete "
                                    f"placement: {e}"
                                )

                # ==========================================
                # DETAILS
                # ==========================================

                with st.expander(
                    "View Placement Details"
                ):

                    detail_col1, detail_col2 = (
                        st.columns(2)
                    )

                    with detail_col1:

                        st.write(
                            "**Employee:** "
                            f"{employee_name}"
                        )

                        st.write(
                            "**Client:** "
                            f"{client_name}"
                        )

                        st.write(
                            "**Position:** "
                            f"{clean_text(placement.position)}"
                        )

                        st.write(
                            "**Job:** "
                            f"{job_name}"
                        )

                        st.write(
                            "**Billing Frequency:** "
                            f"{clean_text(placement.billing_frequency) or 'Not specified'}"
                        )

                    with detail_col2:

                        if placement.start_date:

                            st.write(
                                "**Start Date:** "
                                f"{placement.start_date.strftime('%d %b %Y')}"
                            )

                        if placement.end_date:

                            st.write(
                                "**End Date:** "
                                f"{placement.end_date.strftime('%d %b %Y')}"
                            )

                        days_active = get_days_active(
                            placement
                        )

                        if days_active is not None:

                            st.write(
                                "**Duration:** "
                                f"{days_active} day(s)"
                            )

                        st.write(
                            "**Client Fee:** "
                            f"{currency} "
                            f"{client_fee:,.2f}"
                        )

                        st.write(
                            "**Worker Cost:** "
                            f"{currency} "
                            f"{worker_cost:,.2f}"
                        )

                        st.write(
                            "**Gross Margin:** "
                            f"{currency} "
                            f"{margin:,.2f} "
                            f"({margin_percentage:.1f}%)"
                        )

                    if placement.notes:

                        st.write(
                            "**Notes:** "
                            f"{clean_text(placement.notes)}"
                        )

    except Exception as e:

        session.rollback()

        st.error(
            "An error occurred while loading placements: "
            f"{e}"
        )

    finally:

        session.close()
