import streamlit as st
from database import get_session
from models import Contract, Client, Placement


def show_contracts():

    st.title("Contracts")
    st.caption("Manage client contracts and agreements.")

    session = get_session()

    # ============================================================
    # LOAD DATA
    # ============================================================

    clients = (
        session.query(Client)
        .order_by(Client.company_name.asc())
        .all()
    )

    placements = (
        session.query(Placement)
        .order_by(Placement.start_date.desc())
        .all()
    )

    # ============================================================
    # ADD CONTRACT
    # ============================================================

    st.header("Add Contract")

    if not clients:
        st.warning(
            "Please add a client before creating a contract."
        )
        session.close()
        return

    client_options = {
        client.company_name: client.id
        for client in clients
    }

    placement_options = {
        f"{placement.position} - "
        f"{placement.client.company_name if placement.client else 'No Client'}": placement.id
        for placement in placements
    }

    with st.form("add_contract_form"):

        col1, col2 = st.columns(2)

        with col1:

            selected_client = st.selectbox(
                "Client *",
                list(client_options.keys())
            )

            contract_number = st.text_input(
                "Contract Number *"
            )

            contract_type = st.selectbox(
                "Contract Type",
                [
                    "Master Services Agreement",
                    "Service Agreement",
                    "Staffing Agreement",
                    "Outsourcing Agreement",
                    "Statement of Work",
                    "Other"
                ]
            )

            selected_placement = st.selectbox(
                "Placement",
                ["No Placement"] + list(
                    placement_options.keys()
                )
            )

        with col2:

            start_date = st.date_input(
                "Start Date"
            )

            end_date = st.date_input(
                "End Date",
                value=None
            )

            signed_date = st.date_input(
                "Signed Date",
                value=None
            )

            renewal_date = st.date_input(
                "Renewal Date",
                value=None
            )

        col1, col2, col3 = st.columns(3)

        with col1:

            contract_value = st.number_input(
                "Contract Value",
                min_value=0.0,
                step=100.0
            )

        with col2:

            currency = st.selectbox(
                "Currency",
                [
                    "GBP",
                    "EUR",
                    "USD",
                    "INR"
                ]
            )

        with col3:

            status = st.selectbox(
                "Status",
                [
                    "Draft",
                    "Active",
                    "Signed",
                    "Expired",
                    "Terminated"
                ]
            )

        document_link = st.text_input(
            "Document Link",
            placeholder="https://..."
        )

        notes = st.text_area(
            "Notes"
        )

        submitted = st.form_submit_button(
            "Create Contract",
            use_container_width=True
        )

        if submitted:

            if not contract_number.strip():

                st.error(
                    "Contract Number is required."
                )

            elif (
                end_date is not None
                and end_date < start_date
            ):

                st.error(
                    "End Date cannot be before Start Date."
                )

            else:

                placement_id = None

                if selected_placement != "No Placement":

                    placement_id = (
                        placement_options[
                            selected_placement
                        ]
                    )

                contract = Contract(
                    client_id=client_options[
                        selected_client
                    ],
                    placement_id=placement_id,
                    contract_number=contract_number.strip(),
                    contract_type=contract_type,
                    start_date=start_date,
                    end_date=end_date,
                    contract_value=contract_value,
                    currency=currency,
                    status=status,
                    signed_date=signed_date,
                    renewal_date=renewal_date,
                    document_link=document_link.strip(),
                    notes=notes.strip()
                )

                session.add(contract)
                session.commit()

                st.success(
                    "Contract created successfully."
                )

                st.rerun()

    # ============================================================
    # CONTRACT REGISTER
    # ============================================================

    st.divider()

    st.header("Contract Register")

    contracts = (
        session.query(Contract)
        .order_by(
            Contract.start_date.desc()
        )
        .all()
    )

    if not contracts:

        st.info(
            "No contracts have been created yet."
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
                "Draft",
                "Active",
                "Signed",
                "Expired",
                "Terminated"
            ]
        )

    with col2:

        search = st.text_input(
            "Search Contracts",
            placeholder="Contract number, client or type..."
        )

    filtered_contracts = contracts

    if status_filter != "All":

        filtered_contracts = [
            contract
            for contract in filtered_contracts
            if contract.status == status_filter
        ]

    if search:

        search_text = search.lower()

        filtered_contracts = [
            contract
            for contract in filtered_contracts
            if (
                search_text
                in (contract.contract_number or "").lower()
                or search_text
                in (
                    contract.client.company_name
                    if contract.client
                    else ""
                ).lower()
                or search_text
                in (contract.contract_type or "").lower()
            )
        ]

    st.write(
        f"Showing **{len(filtered_contracts)}** contract(s)"
    )

    # ============================================================
    # DISPLAY CONTRACTS
    # ============================================================

    for contract in filtered_contracts:

        with st.container(border=True):

            col1, col2, col3, col4 = st.columns(
                [3, 3, 2, 2]
            )

            with col1:

                st.subheader(
                    contract.contract_number
                )

                if contract.client:

                    st.write(
                        contract.client.company_name
                    )

                st.caption(
                    contract.contract_type or "—"
                )

            with col2:

                st.write("**Status**")

                st.write(
                    contract.status or "—"
                )

                if contract.start_date:

                    st.caption(
                        f"Start: {contract.start_date}"
                    )

                if contract.end_date:

                    st.caption(
                        f"End: {contract.end_date}"
                    )

            with col3:

                st.write("**Contract Value**")

                st.write(
                    f"{contract.currency} "
                    f"{contract.contract_value or 0:,.2f}"
                )

                if contract.signed_date:

                    st.caption(
                        f"Signed: {contract.signed_date}"
                    )

                if contract.renewal_date:

                    st.caption(
                        f"Renewal: {contract.renewal_date}"
                    )

            with col4:

                if contract.document_link:

                    st.link_button(
                        "Open Document",
                        contract.document_link
                    )

                if st.button(
                    "Edit",
                    key=f"edit_contract_{contract.id}"
                ):

                    st.session_state[
                        "editing_contract_id"
                    ] = contract.id

                    st.rerun()

            if contract.notes:

                st.caption(
                    f"Notes: {contract.notes}"
                )

    # ============================================================
    # EDIT CONTRACT
    # ============================================================

    editing_id = st.session_state.get(
        "editing_contract_id"
    )

    if editing_id:

        contract = session.get(
            Contract,
            editing_id
        )

        if contract:

            st.divider()

            st.header("Edit Contract")

            client_names = list(
                client_options.keys()
            )

            current_client = (
                contract.client.company_name
                if contract.client
                else None
            )

            client_index = (
                client_names.index(current_client)
                if current_client in client_names
                else 0
            )

            placement_names = [
                "No Placement"
            ] + list(
                placement_options.keys()
            )

            current_placement = "No Placement"

            if contract.placement_id:

                for name, placement_id in placement_options.items():

                    if placement_id == contract.placement_id:

                        current_placement = name
                        break

            placement_index = placement_names.index(
                current_placement
            )

            with st.form(
                f"edit_contract_form_{contract.id}"
            ):

                edit_client = st.selectbox(
                    "Client",
                    client_names,
                    index=client_index
                )

                edit_contract_number = st.text_input(
                    "Contract Number",
                    value=contract.contract_number or ""
                )

                contract_types = [
                    "Master Services Agreement",
                    "Service Agreement",
                    "Staffing Agreement",
                    "Outsourcing Agreement",
                    "Statement of Work",
                    "Other"
                ]

                current_type = (
                    contract.contract_type
                    if contract.contract_type in contract_types
                    else "Other"
                )

                edit_contract_type = st.selectbox(
                    "Contract Type",
                    contract_types,
                    index=contract_types.index(
                        current_type
                    )
                )

                edit_placement = st.selectbox(
                    "Placement",
                    placement_names,
                    index=placement_index
                )

                col1, col2 = st.columns(2)

                with col1:

                    edit_start_date = st.date_input(
                        "Start Date",
                        value=contract.start_date
                    )

                    edit_end_date = st.date_input(
                        "End Date",
                        value=contract.end_date
                    )

                    edit_signed_date = st.date_input(
                        "Signed Date",
                        value=contract.signed_date
                    )

                with col2:

                    edit_renewal_date = st.date_input(
                        "Renewal Date",
                        value=contract.renewal_date
                    )

                    edit_value = st.number_input(
                        "Contract Value",
                        min_value=0.0,
                        value=float(
                            contract.contract_value or 0
                        ),
                        step=100.0
                    )

                    currencies = [
                        "GBP",
                        "EUR",
                        "USD",
                        "INR"
                    ]

                    current_currency = (
                        contract.currency
                        if contract.currency in currencies
                        else "GBP"
                    )

                    edit_currency = st.selectbox(
                        "Currency",
                        currencies,
                        index=currencies.index(
                            current_currency
                        )
                    )

                statuses = [
                    "Draft",
                    "Active",
                    "Signed",
                    "Expired",
                    "Terminated"
                ]

                current_status = (
                    contract.status
                    if contract.status in statuses
                    else "Draft"
                )

                edit_status = st.selectbox(
                    "Status",
                    statuses,
                    index=statuses.index(
                        current_status
                    )
                )

                edit_document_link = st.text_input(
                    "Document Link",
                    value=contract.document_link or ""
                )

                edit_notes = st.text_area(
                    "Notes",
                    value=contract.notes or ""
                )

                save = st.form_submit_button(
                    "Save Changes",
                    use_container_width=True
                )

                if save:

                    if not edit_contract_number.strip():

                        st.error(
                            "Contract Number is required."
                        )

                    elif (
                        edit_end_date is not None
                        and edit_end_date < edit_start_date
                    ):

                        st.error(
                            "End Date cannot be before Start Date."
                        )

                    else:

                        contract.client_id = (
                            client_options[edit_client]
                        )

                        if edit_placement == "No Placement":

                            contract.placement_id = None

                        else:

                            contract.placement_id = (
                                placement_options[
                                    edit_placement
                                ]
                            )

                        contract.contract_number = (
                            edit_contract_number.strip()
                        )

                        contract.contract_type = (
                            edit_contract_type
                        )

                        contract.start_date = (
                            edit_start_date
                        )

                        contract.end_date = (
                            edit_end_date
                        )

                        contract.contract_value = (
                            edit_value
                        )

                        contract.currency = (
                            edit_currency
                        )

                        contract.status = (
                            edit_status
                        )

                        contract.signed_date = (
                            edit_signed_date
                        )

                        contract.renewal_date = (
                            edit_renewal_date
                        )

                        contract.document_link = (
                            edit_document_link.strip()
                        )

                        contract.notes = (
                            edit_notes.strip()
                        )

                        session.commit()

                        st.session_state.pop(
                            "editing_contract_id",
                            None
                        )

                        st.success(
                            "Contract updated successfully."
                        )

                        st.rerun()

            if st.button(
                "Cancel",
                key=f"cancel_contract_{contract.id}"
            ):

                st.session_state.pop(
                    "editing_contract_id",
                    None
                )

                st.rerun()

    session.close()