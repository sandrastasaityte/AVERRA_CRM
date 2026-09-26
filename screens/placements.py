import streamlit as st
from database import get_session
from models import Placement, Client, Employee, Job


def show_placements():

    st.title("Placements")
    st.caption("Manage active and historical employee placements.")

    session = get_session()

    # ============================================================
    # LOAD DATA
    # ============================================================

    clients = (
        session.query(Client)
        .order_by(Client.company_name.asc())
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

    # ============================================================
    # ADD PLACEMENT
    # ============================================================

    st.header("Add Placement")

    if not clients:
        st.warning(
            "Please add a client before creating a placement."
        )
        session.close()
        return

    if not employees:
        st.warning(
            "Please add an employee before creating a placement."
        )
        session.close()
        return

    client_options = {
        client.company_name: client.id
        for client in clients
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

    with st.form("add_placement_form"):

        col1, col2 = st.columns(2)

        with col1:

            selected_client = st.selectbox(
                "Client *",
                list(client_options.keys())
            )

            selected_employee = st.selectbox(
                "Employee *",
                list(employee_options.keys())
            )

            selected_job = st.selectbox(
                "Job",
                ["No Job"] + list(job_options.keys())
            )

            position = st.text_input(
                "Position *"
            )

        with col2:

            start_date = st.date_input(
                "Start Date"
            )

            end_date = st.date_input(
                "End Date",
                value=None
            )

            status = st.selectbox(
                "Status",
                [
                    "Active",
                    "Scheduled",
                    "Completed",
                    "Terminated"
                ]
            )

            billing_frequency = st.selectbox(
                "Billing Frequency",
                [
                    "Monthly",
                    "Weekly",
                    "Daily",
                    "Hourly"
                ]
            )

        col1, col2, col3 = st.columns(3)

        with col1:

            client_monthly_fee = st.number_input(
                "Client Monthly Fee",
                min_value=0.0,
                step=100.0
            )

        with col2:

            worker_monthly_cost = st.number_input(
                "Worker Monthly Cost",
                min_value=0.0,
                step=100.0
            )

        with col3:

            currency = st.selectbox(
                "Currency",
                [
                    "GBP",
                    "EUR",
                    "USD",
                    "INR"
                ]
            )

        notes = st.text_area(
            "Notes"
        )

        submitted = st.form_submit_button(
            "Create Placement",
            use_container_width=True
        )

        if submitted:

            if not position.strip():

                st.error(
                    "Position is required."
                )

            elif (
                end_date is not None
                and end_date < start_date
            ):

                st.error(
                    "End Date cannot be before Start Date."
                )

            else:

                job_id = None

                if selected_job != "No Job":
                    job_id = job_options[selected_job]

                placement = Placement(
                    client_id=client_options[
                        selected_client
                    ],
                    employee_id=employee_options[
                        selected_employee
                    ],
                    job_id=job_id,
                    position=position.strip(),
                    start_date=start_date,
                    end_date=end_date,
                    client_monthly_fee=client_monthly_fee,
                    worker_monthly_cost=worker_monthly_cost,
                    currency=currency,
                    billing_frequency=billing_frequency,
                    status=status,
                    notes=notes.strip()
                )

                session.add(placement)
                session.commit()

                st.success(
                    "Placement created successfully."
                )

                st.rerun()

    # ============================================================
    # PLACEMENT REGISTER
    # ============================================================

    st.divider()

    st.header("Placement Register")

    placements = (
        session.query(Placement)
        .order_by(
            Placement.start_date.desc()
        )
        .all()
    )

    if not placements:

        st.info(
            "No placements have been created yet."
        )

        session.close()
        return

    # ============================================================
    # FILTERS
    # ============================================================

    col1, col2 = st.columns(2)

    with col1:

        status_filter = st.selectbox(
            "Filter by Status",
            [
                "All",
                "Active",
                "Scheduled",
                "Completed",
                "Terminated"
            ]
        )

    with col2:

        search = st.text_input(
            "Search",
            placeholder="Employee, client or position..."
        )

    filtered_placements = placements

    if status_filter != "All":

        filtered_placements = [
            placement
            for placement in filtered_placements
            if placement.status == status_filter
        ]

    if search:

        search_text = search.lower()

        filtered_placements = [
            placement
            for placement in filtered_placements
            if (
                search_text
                in (placement.position or "").lower()
                or search_text
                in (
                    placement.client.company_name
                    if placement.client
                    else ""
                ).lower()
                or search_text
                in (
                    f"{placement.employee.first_name} "
                    f"{placement.employee.last_name}"
                    if placement.employee
                    else ""
                ).lower()
            )
        ]

    st.write(
        f"Showing **{len(filtered_placements)}** placement(s)"
    )

    # ============================================================
    # DISPLAY PLACEMENTS
    # ============================================================

    for placement in filtered_placements:

        with st.container(border=True):

            col1, col2, col3, col4 = st.columns(
                [3, 3, 2, 2]
            )

            # ----------------------------------------------------
            # PLACEMENT
            # ----------------------------------------------------

            with col1:

                st.subheader(
                    placement.position
                )

                if placement.employee:

                    employee_name = " ".join(
                        part
                        for part in [
                            placement.employee.first_name,
                            placement.employee.last_name
                        ]
                        if part
                    )

                    st.write(
                        employee_name
                    )

                if placement.client:

                    st.caption(
                        placement.client.company_name
                    )

            # ----------------------------------------------------
            # DATES / STATUS
            # ----------------------------------------------------

            with col2:

                st.write("**Status**")

                st.write(
                    placement.status or "—"
                )

                if placement.start_date:

                    st.caption(
                        f"Start: {placement.start_date}"
                    )

                if placement.end_date:

                    st.caption(
                        f"End: {placement.end_date}"
                    )

            # ----------------------------------------------------
            # FINANCIALS
            # ----------------------------------------------------

            with col3:

                st.write("**Financials**")

                st.write(
                    f"{placement.currency} "
                    f"{placement.client_monthly_fee:,.2f}"
                )

                st.caption(
                    "Client monthly fee"
                )

                st.write(
                    f"{placement.currency} "
                    f"{placement.worker_monthly_cost:,.2f}"
                )

                st.caption(
                    "Worker monthly cost"
                )

            # ----------------------------------------------------
            # MARGIN
            # ----------------------------------------------------

            with col4:

                st.write("**Gross Margin**")

                st.write(
                    f"{placement.currency} "
                    f"{placement.gross_margin:,.2f}"
                )

                st.caption(
                    f"{placement.gross_margin_percentage:.1f}%"
                )

                if st.button(
                    "Edit",
                    key=f"edit_placement_{placement.id}"
                ):

                    st.session_state[
                        "editing_placement_id"
                    ] = placement.id

                    st.rerun()

            if placement.notes:

                st.caption(
                    f"Notes: {placement.notes}"
                )

    # ============================================================
    # EDIT PLACEMENT
    # ============================================================

    editing_id = st.session_state.get(
        "editing_placement_id"
    )

    if editing_id:

        placement = session.get(
            Placement,
            editing_id
        )

        if placement:

            st.divider()

            st.header(
                "Edit Placement"
            )

            with st.form(
                f"edit_placement_form_{placement.id}"
            ):

                client_names = list(
                    client_options.keys()
                )

                current_client = (
                    placement.client.company_name
                    if placement.client
                    else None
                )

                client_index = (
                    client_names.index(current_client)
                    if current_client in client_names
                    else 0
                )

                employee_names = list(
                    employee_options.keys()
                )

                current_employee = (
                    f"{placement.employee.first_name} "
                    f"{placement.employee.last_name}"
                    if placement.employee
                    else None
                )

                employee_index = (
                    employee_names.index(current_employee)
                    if current_employee in employee_names
                    else 0
                )

                edit_client = st.selectbox(
                    "Client",
                    client_names,
                    index=client_index
                )

                edit_employee = st.selectbox(
                    "Employee",
                    employee_names,
                    index=employee_index
                )

                edit_job_options = [
                    "No Job"
                ] + list(job_options.keys())

                current_job_name = "No Job"

                if placement.job_id:

                    for name, job_id in job_options.items():

                        if job_id == placement.job_id:

                            current_job_name = name
                            break

                job_index = edit_job_options.index(
                    current_job_name
                )

                edit_job = st.selectbox(
                    "Job",
                    edit_job_options,
                    index=job_index
                )

                edit_position = st.text_input(
                    "Position",
                    value=placement.position or ""
                )

                col1, col2 = st.columns(2)

                with col1:

                    edit_start_date = st.date_input(
                        "Start Date",
                        value=placement.start_date
                    )

                with col2:

                    edit_end_date = st.date_input(
                        "End Date",
                        value=placement.end_date
                    )

                edit_status = st.selectbox(
                    "Status",
                    [
                        "Active",
                        "Scheduled",
                        "Completed",
                        "Terminated"
                    ],
                    index=[
                        "Active",
                        "Scheduled",
                        "Completed",
                        "Terminated"
                    ].index(
                        placement.status
                        if placement.status
                        in [
                            "Active",
                            "Scheduled",
                            "Completed",
                            "Terminated"
                        ]
                        else "Active"
                    )
                )

                edit_billing_frequency = st.selectbox(
                    "Billing Frequency",
                    [
                        "Monthly",
                        "Weekly",
                        "Daily",
                        "Hourly"
                    ],
                    index=[
                        "Monthly",
                        "Weekly",
                        "Daily",
                        "Hourly"
                    ].index(
                        placement.billing_frequency
                        if placement.billing_frequency
                        in [
                            "Monthly",
                            "Weekly",
                            "Daily",
                            "Hourly"
                        ]
                        else "Monthly"
                    )
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    edit_fee = st.number_input(
                        "Client Monthly Fee",
                        min_value=0.0,
                        value=float(
                            placement.client_monthly_fee or 0
                        ),
                        step=100.0
                    )

                with col2:

                    edit_cost = st.number_input(
                        "Worker Monthly Cost",
                        min_value=0.0,
                        value=float(
                            placement.worker_monthly_cost or 0
                        ),
                        step=100.0
                    )

                with col3:

                    currencies = [
                        "GBP",
                        "EUR",
                        "USD",
                        "INR"
                    ]

                    current_currency = (
                        placement.currency
                        if placement.currency in currencies
                        else "GBP"
                    )

                    edit_currency = st.selectbox(
                        "Currency",
                        currencies,
                        index=currencies.index(
                            current_currency
                        )
                    )

                edit_notes = st.text_area(
                    "Notes",
                    value=placement.notes or ""
                )

                save = st.form_submit_button(
                    "Save Changes",
                    use_container_width=True
                )

                if save:

                    if not edit_position.strip():

                        st.error(
                            "Position is required."
                        )

                    elif (
                        edit_end_date is not None
                        and edit_end_date < edit_start_date
                    ):

                        st.error(
                            "End Date cannot be before Start Date."
                        )

                    else:

                        placement.client_id = (
                            client_options[edit_client]
                        )

                        placement.employee_id = (
                            employee_options[edit_employee]
                        )

                        if edit_job == "No Job":

                            placement.job_id = None

                        else:

                            placement.job_id = (
                                job_options[edit_job]
                            )

                        placement.position = (
                            edit_position.strip()
                        )

                        placement.start_date = (
                            edit_start_date
                        )

                        placement.end_date = (
                            edit_end_date
                        )

                        placement.status = (
                            edit_status
                        )

                        placement.billing_frequency = (
                            edit_billing_frequency
                        )

                        placement.client_monthly_fee = (
                            edit_fee
                        )

                        placement.worker_monthly_cost = (
                            edit_cost
                        )

                        placement.currency = (
                            edit_currency
                        )

                        placement.notes = (
                            edit_notes.strip()
                        )

                        session.commit()

                        st.session_state.pop(
                            "editing_placement_id",
                            None
                        )

                        st.success(
                            "Placement updated successfully."
                        )

                        st.rerun()

            if st.button(
                "Cancel",
                key=f"cancel_placement_{placement.id}"
            ):

                st.session_state.pop(
                    "editing_placement_id",
                    None
                )

                st.rerun()

    session.close()