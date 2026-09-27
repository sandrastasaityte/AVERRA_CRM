
import streamlit as st
from datetime import date

from database import get_session
from models import Contract, Client, Placement


# ============================================================
# CONSTANTS
# ============================================================

CONTRACT_TYPES = [
    "Master Services Agreement",
    "Service Agreement",
    "Staffing Agreement",
    "Outsourcing Agreement",
    "Statement of Work",
    "Other",
]

CONTRACT_STATUSES = [
    "Draft",
    "Active",
    "Signed",
    "Expired",
    "Terminated",
]

CURRENCIES = [
    "GBP",
    "EUR",
    "USD",
    "INR",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_client_name(contract):
    if contract.client:
        return contract.client.company_name or "Unknown Client"

    return "No Client"


def get_placement_label(placement):
    client_name = (
        placement.client.company_name
        if placement.client
        else "No Client"
    )

    position = placement.position or "Unnamed Position"

    return f"{position} - {client_name} (ID {placement.id})"


def is_renewal_due(contract):
    if not contract.renewal_date:
        return False

    if contract.status in ["Expired", "Terminated"]:
        return False

    return contract.renewal_date <= date.today()


def is_expired(contract):
    if contract.status == "Expired":
        return True

    if contract.end_date:
        return contract.end_date < date.today()

    return False


def days_until_renewal(contract):
    if not contract.renewal_date:
        return None

    return (contract.renewal_date - date.today()).days


# ============================================================
# MAIN SCREEN
# ============================================================

def show_contracts():

    st.title("Contracts")
    st.caption(
        "Manage client contracts, agreements, renewals and contract values."
    )

    session = get_session()

    try:

        # ========================================================
        # LOAD CLIENTS
        # ========================================================

        clients = (
            session.query(Client)
            .order_by(Client.company_name.asc())
            .all()
        )

        # ========================================================
        # LOAD PLACEMENTS
        # ========================================================

        placements = (
            session.query(Placement)
            .order_by(
                Placement.start_date.desc(),
                Placement.id.desc()
            )
            .all()
        )

        # ========================================================
        # LOAD CONTRACTS
        # ========================================================

        all_contracts = (
            session.query(Contract)
            .order_by(
                Contract.start_date.desc(),
                Contract.id.desc()
            )
            .all()
        )

        # ========================================================
        # CONTRACT METRICS
        # ========================================================

        total_contracts = len(all_contracts)

        active_contracts = sum(
            1
            for contract in all_contracts
            if contract.status == "Active"
        )

        signed_contracts = sum(
            1
            for contract in all_contracts
            if contract.status == "Signed"
        )

        draft_contracts = sum(
            1
            for contract in all_contracts
            if contract.status == "Draft"
        )

        renewal_due = sum(
            1
            for contract in all_contracts
            if is_renewal_due(contract)
        )

        expired_contracts = sum(
            1
            for contract in all_contracts
            if is_expired(contract)
        )

        # ========================================================
        # OVERVIEW
        # ========================================================

        st.subheader("Contract Overview")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Total Contracts",
                total_contracts
            )

        with col2:
            st.metric(
                "Active",
                active_contracts
            )

        with col3:
            st.metric(
                "Signed",
                signed_contracts
            )

        with col4:
            st.metric(
                "Draft",
                draft_contracts
            )

        with col5:
            st.metric(
                "Renewal Due",
                renewal_due
            )

        if expired_contracts > 0:

            st.warning(
                f"{expired_contracts} contract(s) are expired "
                "or past their end date."
            )

        # ========================================================
        # ADD CONTRACT
        # ========================================================

        st.divider()
        st.header("Add Contract")

        if not clients:

            st.warning(
                "Please add a client before creating a contract."
            )

            return

        # ========================================================
        # CLIENT OPTIONS
        # ========================================================

        client_options = {}

        for client in clients:

            label = (
                f"{client.company_name} "
                f"(ID {client.id})"
            )

            client_options[label] = client.id

        # ========================================================
        # ADD CONTRACT FORM
        # ========================================================

        with st.form("add_contract_form"):

            col1, col2 = st.columns(2)

            # ----------------------------------------------------
            # LEFT COLUMN
            # ----------------------------------------------------

            with col1:

                selected_client = st.selectbox(
                    "Client *",
                    list(client_options.keys())
                )

                contract_number = st.text_input(
                    "Contract Number *",
                    placeholder="e.g. AV-UK-2026-001"
                )

                contract_type = st.selectbox(
                    "Contract Type",
                    CONTRACT_TYPES
                )

                # ------------------------------------------------
                # Placement
                # ------------------------------------------------

                selected_client_id = client_options[
                    selected_client
                ]

                client_placements = [
                    placement
                    for placement in placements
                    if placement.client_id == selected_client_id
                ]

                placement_options = {
                    get_placement_label(placement): placement.id
                    for placement in client_placements
                }

                selected_placement = st.selectbox(
                    "Placement",
                    ["No Placement"]
                    + list(placement_options.keys())
                )

            # ----------------------------------------------------
            # RIGHT COLUMN
            # ----------------------------------------------------

            with col2:

                start_date = st.date_input(
                    "Start Date",
                    value=date.today()
                )

                has_end_date = st.checkbox(
                    "Set End Date",
                    value=False
                )

                if has_end_date:

                    end_date = st.date_input(
                        "End Date",
                        value=date.today()
                    )

                else:

                    end_date = None

                has_signed_date = st.checkbox(
                    "Set Signed Date",
                    value=False
                )

                if has_signed_date:

                    signed_date = st.date_input(
                        "Signed Date",
                        value=date.today()
                    )

                else:

                    signed_date = None

                has_renewal_date = st.checkbox(
                    "Set Renewal Date",
                    value=False
                )

                if has_renewal_date:

                    renewal_date = st.date_input(
                        "Renewal Date",
                        value=date.today()
                    )

                else:

                    renewal_date = None

            # ====================================================
            # FINANCIAL DETAILS
            # ====================================================

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
                    CURRENCIES
                )

            with col3:

                status = st.selectbox(
                    "Status",
                    CONTRACT_STATUSES
                )

            # ====================================================
            # DOCUMENT / NOTES
            # ====================================================

            document_link = st.text_input(
                "Document Link",
                placeholder="https://..."
            )

            notes = st.text_area(
                "Notes",
                placeholder="Additional contract information..."
            )

            submitted = st.form_submit_button(
                "Create Contract",
                use_container_width=True
            )

            # ====================================================
            # CREATE CONTRACT
            # ====================================================

            if submitted:

                clean_contract_number = (
                    contract_number.strip()
                )

                # ------------------------------------------------
                # VALIDATION
                # ------------------------------------------------

                if not clean_contract_number:

                    st.error(
                        "Contract Number is required."
                    )

                elif (
                    end_date
                    and end_date < start_date
                ):

                    st.error(
                        "End Date cannot be before Start Date."
                    )

                elif (
                    signed_date
                    and signed_date > date.today()
                ):

                    st.error(
                        "Signed Date cannot be in the future."
                    )

                elif (
                    renewal_date
                    and renewal_date < start_date
                ):

                    st.error(
                        "Renewal Date cannot be before "
                        "the contract Start Date."
                    )

                else:

                    # --------------------------------------------
                    # CHECK DUPLICATE CONTRACT NUMBER
                    # --------------------------------------------

                    duplicate = (
                        session.query(Contract)
                        .filter(
                            Contract.contract_number.ilike(
                                clean_contract_number
                            )
                        )
                        .first()
                    )

                    if duplicate:

                        st.error(
                            "A contract with this "
                            "Contract Number already exists."
                        )

                    else:

                        placement_id = None

                        if (
                            selected_placement
                            != "No Placement"
                        ):

                            placement_id = (
                                placement_options[
                                    selected_placement
                                ]
                            )

                        # ----------------------------------------
                        # CREATE OBJECT
                        # ----------------------------------------

                        contract = Contract(
                            client_id=selected_client_id,
                            placement_id=placement_id,
                            contract_number=clean_contract_number,
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

        # ========================================================
        # CONTRACT REGISTER
        # ========================================================

        st.divider()
        st.header("Contract Register")

        # ========================================================
        # FILTERS
        # ========================================================

        col1, col2, col3 = st.columns(3)

        with col1:

            status_filter = st.selectbox(
                "Filter by Status",
                ["All"] + CONTRACT_STATUSES
            )

        with col2:

            search = st.text_input(
                "Search Contracts",
                placeholder=(
                    "Contract number, client, type or notes..."
                )
            )

        with col3:

            renewal_filter = st.selectbox(
                "Renewal",
                [
                    "All",
                    "Renewal Due",
                    "No Renewal Date",
                    "Future Renewal"
                ]
            )

        # ========================================================
        # APPLY FILTERS
        # ========================================================

        filtered_contracts = all_contracts

        # --------------------------------------------------------
        # Status
        # --------------------------------------------------------

        if status_filter != "All":

            filtered_contracts = [
                contract
                for contract in filtered_contracts
                if contract.status == status_filter
            ]

        # --------------------------------------------------------
        # Search
        # --------------------------------------------------------

        if search.strip():

            search_text = search.lower().strip()

            filtered_contracts = [
                contract
                for contract in filtered_contracts
                if (
                    search_text
                    in (
                        contract.contract_number or ""
                    ).lower()

                    or search_text
                    in get_client_name(
                        contract
                    ).lower()

                    or search_text
                    in (
                        contract.contract_type or ""
                    ).lower()

                    or search_text
                    in (
                        contract.notes or ""
                    ).lower()
                )
            ]

        # --------------------------------------------------------
        # Renewal filter
        # --------------------------------------------------------

        if renewal_filter == "Renewal Due":

            filtered_contracts = [
                contract
                for contract in filtered_contracts
                if is_renewal_due(contract)
            ]

        elif renewal_filter == "No Renewal Date":

            filtered_contracts = [
                contract
                for contract in filtered_contracts
                if not contract.renewal_date
            ]

        elif renewal_filter == "Future Renewal":

            filtered_contracts = [
                contract
                for contract in filtered_contracts
                if (
                    contract.renewal_date
                    and contract.renewal_date > date.today()
                )
            ]

        # ========================================================
        # RESULT COUNT
        # ========================================================

        st.write(
            f"Showing **{len(filtered_contracts)}** contract(s)"
        )

        # ========================================================
        # DISPLAY CONTRACTS
        # ========================================================

        if not filtered_contracts:

            st.info(
                "No contracts match the selected filters."
            )

        for contract in filtered_contracts:

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(
                    [3, 3, 2, 2]
                )

                # =================================================
                # CONTRACT INFORMATION
                # =================================================

                with col1:

                    st.subheader(
                        contract.contract_number
                        or "Unnamed Contract"
                    )

                    st.write(
                        get_client_name(contract)
                    )

                    st.caption(
                        contract.contract_type
                        or "Contract type not specified"
                    )

                    if contract.placement:

                        st.caption(
                            "Placement: "
                            + (
                                contract.placement.position
                                or "Unnamed Position"
                            )
                        )

                # =================================================
                # STATUS / DATES
                # =================================================

                with col2:

                    st.write("**Status**")

                    if contract.status == "Active":

                        st.success(
                            contract.status
                        )

                    elif contract.status == "Signed":

                        st.info(
                            contract.status
                        )

                    elif contract.status == "Expired":

                        st.error(
                            contract.status
                        )

                    elif contract.status == "Terminated":

                        st.error(
                            contract.status
                        )

                    else:

                        st.warning(
                            contract.status or "Draft"
                        )

                    if contract.start_date:

                        st.caption(
                            f"Start: {contract.start_date}"
                        )

                    if contract.end_date:

                        st.caption(
                            f"End: {contract.end_date}"
                        )

                        if (
                            contract.end_date < date.today()
                            and contract.status
                            not in [
                                "Expired",
                                "Terminated"
                            ]
                        ):

                            st.error(
                                "End date has passed."
                            )

                # =================================================
                # CONTRACT VALUE
                # =================================================

                with col3:

                    st.write("**Contract Value**")

                    st.write(
                        f"{contract.currency or 'GBP'} "
                        f"{contract.contract_value or 0:,.2f}"
                    )

                    if contract.signed_date:

                        st.caption(
                            f"Signed: {contract.signed_date}"
                        )

                    if contract.renewal_date:

                        days = days_until_renewal(
                            contract
                        )

                        st.caption(
                            f"Renewal: {contract.renewal_date}"
                        )

                        if days is not None:

                            if days < 0:

                                st.error(
                                    "Renewal overdue by "
                                    f"{abs(days)} day(s)."
                                )

                            elif days == 0:

                                st.warning(
                                    "Renewal is due today."
                                )

                            elif days <= 30:

                                st.warning(
                                    f"Renewal in {days} day(s)."
                                )

                            else:

                                st.caption(
                                    f"{days} day(s) until renewal."
                                )

                # =================================================
                # ACTIONS
                # =================================================

                with col4:

                    if contract.document_link:

                        st.link_button(
                            "Open Document",
                            contract.document_link,
                            use_container_width=True
                        )

                    if st.button(
                        "Edit",
                        key=f"edit_contract_{contract.id}",
                        use_container_width=True
                    ):

                        st.session_state[
                            "editing_contract_id"
                        ] = contract.id

                        st.rerun()

                # =================================================
                # NOTES
                # =================================================

                if contract.notes:

                    st.caption(
                        f"Notes: {contract.notes}"
                    )

        # ========================================================
        # EDIT CONTRACT
        # ========================================================

        editing_id = st.session_state.get(
            "editing_contract_id"
        )

        if editing_id:

            contract = session.get(
                Contract,
                editing_id
            )

            if not contract:

                st.session_state.pop(
                    "editing_contract_id",
                    None
                )

                st.warning(
                    "The selected contract could not be found."
                )

                return

            st.divider()
            st.header("Edit Contract")

            # ====================================================
            # CLIENT OPTIONS
            # ====================================================

            client_names = list(
                client_options.keys()
            )

            current_client_label = None

            for label, client_id in client_options.items():

                if client_id == contract.client_id:

                    current_client_label = label
                    break

            if current_client_label is None:

                current_client_label = client_names[0]

            client_index = client_names.index(
                current_client_label
            )

            # ====================================================
            # EDIT FORM
            # ====================================================

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

                current_type = (
                    contract.contract_type
                    if contract.contract_type
                    in CONTRACT_TYPES
                    else "Other"
                )

                edit_contract_type = st.selectbox(
                    "Contract Type",
                    CONTRACT_TYPES,
                    index=CONTRACT_TYPES.index(
                        current_type
                    )
                )

                # =================================================
                # PLACEMENTS FOR SELECTED CLIENT
                # =================================================

                selected_edit_client_id = client_options[
                    edit_client
                ]

                selected_client_placements = [
                    placement
                    for placement in placements
                    if placement.client_id
                    == selected_edit_client_id
                ]

                selected_placement_options = {
                    get_placement_label(placement): placement.id
                    for placement
                    in selected_client_placements
                }

                selected_placement_names = (
                    ["No Placement"]
                    + list(
                        selected_placement_options.keys()
                    )
                )

                current_edit_placement = (
                    "No Placement"
                )

                if (
                    contract.placement_id
                    and contract.client_id
                    == selected_edit_client_id
                ):

                    for (
                        label,
                        placement_id
                    ) in selected_placement_options.items():

                        if (
                            placement_id
                            == contract.placement_id
                        ):

                            current_edit_placement = label
                            break

                edit_placement_index = (
                    selected_placement_names.index(
                        current_edit_placement
                    )
                )

                edit_placement = st.selectbox(
                    "Placement",
                    selected_placement_names,
                    index=edit_placement_index
                )

                # =================================================
                # DATES
                # =================================================

                col1, col2 = st.columns(2)

                with col1:

                    edit_start_date = st.date_input(
                        "Start Date",
                        value=(
                            contract.start_date
                            or date.today()
                        )
                    )

                    edit_has_end_date = st.checkbox(
                        "Set End Date",
                        value=(
                            contract.end_date is not None
                        )
                    )

                    if edit_has_end_date:

                        edit_end_date = st.date_input(
                            "End Date",
                            value=(
                                contract.end_date
                                or date.today()
                            )
                        )

                    else:

                        edit_end_date = None

                with col2:

                    edit_has_signed_date = st.checkbox(
                        "Set Signed Date",
                        value=(
                            contract.signed_date is not None
                        )
                    )

                    if edit_has_signed_date:

                        edit_signed_date = st.date_input(
                            "Signed Date",
                            value=(
                                contract.signed_date
                                or date.today()
                            )
                        )

                    else:

                        edit_signed_date = None

                    edit_has_renewal_date = st.checkbox(
                        "Set Renewal Date",
                        value=(
                            contract.renewal_date is not None
                        )
                    )

                    if edit_has_renewal_date:

                        edit_renewal_date = st.date_input(
                            "Renewal Date",
                            value=(
                                contract.renewal_date
                                or date.today()
                            )
                        )

                    else:

                        edit_renewal_date = None

                # =================================================
                # FINANCIAL INFORMATION
                # =================================================

                col1, col2, col3 = st.columns(3)

                with col1:

                    edit_value = st.number_input(
                        "Contract Value",
                        min_value=0.0,
                        value=float(
                            contract.contract_value or 0
                        ),
                        step=100.0
                    )

                with col2:

                    current_currency = (
                        contract.currency
                        if contract.currency
                        in CURRENCIES
                        else "GBP"
                    )

                    edit_currency = st.selectbox(
                        "Currency",
                        CURRENCIES,
                        index=CURRENCIES.index(
                            current_currency
                        )
                    )

                with col3:

                    current_status = (
                        contract.status
                        if contract.status
                        in CONTRACT_STATUSES
                        else "Draft"
                    )

                    edit_status = st.selectbox(
                        "Status",
                        CONTRACT_STATUSES,
                        index=CONTRACT_STATUSES.index(
                            current_status
                        )
                    )

                # =================================================
                # DOCUMENT / NOTES
                # =================================================

                edit_document_link = st.text_input(
                    "Document Link",
                    value=contract.document_link or ""
                )

                edit_notes = st.text_area(
                    "Notes",
                    value=contract.notes or ""
                )

                # =================================================
                # BUTTONS
                # =================================================

                col1, col2 = st.columns(2)

                with col1:

                    save = st.form_submit_button(
                        "Save Changes",
                        use_container_width=True
                    )

                with col2:

                    cancel = st.form_submit_button(
                        "Cancel",
                        use_container_width=True
                    )

                # =================================================
                # CANCEL
                # =================================================

                if cancel:

                    st.session_state.pop(
                        "editing_contract_id",
                        None
                    )

                    st.rerun()

                # =================================================
                # SAVE
                # =================================================

                if save:

                    clean_contract_number = (
                        edit_contract_number.strip()
                    )

                    if not clean_contract_number:

                        st.error(
                            "Contract Number is required."
                        )

                    elif (
                        edit_end_date
                        and edit_end_date
                        < edit_start_date
                    ):

                        st.error(
                            "End Date cannot be before "
                            "Start Date."
                        )

                    elif (
                        edit_signed_date
                        and edit_signed_date
                        > date.today()
                    ):

                        st.error(
                            "Signed Date cannot be in the future."
                        )

                    elif (
                        edit_renewal_date
                        and edit_renewal_date
                        < edit_start_date
                    ):

                        st.error(
                            "Renewal Date cannot be before "
                            "the contract Start Date."
                        )

                    else:

                        # ----------------------------------------
                        # DUPLICATE NUMBER CHECK
                        # ----------------------------------------

                        duplicate = (
                            session.query(Contract)
                            .filter(
                                Contract.contract_number.ilike(
                                    clean_contract_number
                                ),
                                Contract.id != contract.id
                            )
                            .first()
                        )

                        if duplicate:

                            st.error(
                                "Another contract already uses "
                                "this Contract Number."
                            )

                        else:

                            # ------------------------------------
                            # UPDATE CLIENT
                            # ------------------------------------

                            contract.client_id = (
                                selected_edit_client_id
                            )

                            # ------------------------------------
                            # UPDATE PLACEMENT
                            # ------------------------------------

                            if (
                                edit_placement
                                == "No Placement"
                            ):

                                contract.placement_id = None

                            else:

                                contract.placement_id = (
                                    selected_placement_options[
                                        edit_placement
                                    ]
                                )

                            # ------------------------------------
                            # UPDATE CONTRACT
                            # ------------------------------------

                            contract.contract_number = (
                                clean_contract_number
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

                            # ------------------------------------
                            # SAVE
                            # ------------------------------------

                            session.commit()

                            st.session_state.pop(
                                "editing_contract_id",
                                None
                            )

                            st.success(
                                "Contract updated successfully."
                            )

                            st.rerun()

    finally:

        session.close()

