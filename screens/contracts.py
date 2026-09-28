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

def normalize_text(value):
    """
    Normalize text for reliable comparisons and searching.
    """

    return " ".join(
        str(value or "").strip().lower().split()
    )


def normalize_url(url):
    """
    Add HTTPS when a user enters a bare domain.
    """

    url = str(url or "").strip()

    if not url:
        return ""

    lower_url = url.lower()

    if (
        lower_url.startswith("http://")
        or lower_url.startswith("https://")
    ):
        return url

    return f"https://{url}"


def is_valid_url(url):
    """
    Basic URL validation.
    """

    url = str(url or "").strip()

    if not url:
        return True

    lower_url = url.lower()

    return (
        lower_url.startswith("http://")
        or lower_url.startswith("https://")
    )


def get_client_name(contract):
    """
    Return a safe client name.
    """

    if contract.client:

        return (
            contract.client.company_name
            or f"Client {contract.client.id}"
        )

    return "No Client"


def get_client_label(client):
    """
    Return a safe dropdown label.
    """

    company_name = (
        client.company_name or ""
    ).strip()

    if not company_name:
        company_name = f"Client {client.id}"

    return f"{company_name} (ID {client.id})"


def get_placement_label(placement):
    """
    Return a safe placement label.
    """

    position = (
        placement.position
        or "Unnamed Position"
    )

    if placement.client:

        client_name = (
            placement.client.company_name
            or f"Client {placement.client.id}"
        )

    else:

        client_name = "No Client"

    return (
        f"{position} - "
        f"{client_name} "
        f"(ID {placement.id})"
    )


def get_status_display(status):
    """
    Return a safe contract status.
    """

    return status or "Draft"


def get_days_until_renewal(contract):
    """
    Return number of days until renewal.

    Negative = overdue.
    Zero = today.
    Positive = future.
    """

    if not contract.renewal_date:
        return None

    return (
        contract.renewal_date
        - date.today()
    ).days


def get_renewal_state(contract):
    """
    Return the renewal state.

    Possible values:

        None
        Overdue
        Today
        Soon
        Future
    """

    if not contract.renewal_date:
        return None

    if contract.status in [
        "Expired",
        "Terminated",
    ]:
        return None

    days = get_days_until_renewal(
        contract
    )

    if days is None:
        return None

    if days < 0:
        return "Overdue"

    if days == 0:
        return "Today"

    if days <= 30:
        return "Soon"

    return "Future"


def get_renewal_label(contract):
    """
    Return a human-readable renewal label.
    """

    if not contract.renewal_date:
        return "No renewal date"

    formatted_date = (
        contract.renewal_date.strftime(
            "%d %b %Y"
        )
    )

    state = get_renewal_state(
        contract
    )

    if state == "Overdue":

        days = abs(
            get_days_until_renewal(
                contract
            )
        )

        return (
            f"{formatted_date} "
            f"(overdue by {days} days)"
        )

    if state == "Today":

        return (
            f"{formatted_date} "
            "(due today)"
        )

    if state == "Soon":

        days = get_days_until_renewal(
            contract
        )

        return (
            f"{formatted_date} "
            f"({days} days)"
        )

    return formatted_date


def is_expired(contract):
    """
    Return True if the contract is expired
    either by status or by end date.
    """

    if contract.status == "Expired":
        return True

    if (
        contract.end_date
        and contract.end_date < date.today()
        and contract.status != "Terminated"
    ):
        return True

    return False


def is_renewal_due(contract):
    """
    Return True when renewal is today or overdue.
    """

    if not contract.renewal_date:
        return False

    if contract.status in [
        "Expired",
        "Terminated",
    ]:
        return False

    return (
        contract.renewal_date
        <= date.today()
    )


def find_duplicate_contract_number(
    session,
    contract_number,
    exclude_id=None,
):
    """
    Find another contract with the same
    normalized contract number.

    This is intentionally checked in Python
    so that values such as:

        AV-001
        av-001
        AV 001

    can be treated consistently.
    """

    normalized_number = normalize_text(
        contract_number
    )

    if not normalized_number:
        return None

    contracts = (
        session.query(Contract)
        .all()
    )

    for contract in contracts:

        if (
            exclude_id is not None
            and contract.id == exclude_id
        ):
            continue

        existing_number = normalize_text(
            contract.contract_number
        )

        if (
            existing_number
            and existing_number
            == normalized_number
        ):
            return contract

    return None


def get_client_placements(
    placements,
    client_id,
):
    """
    Return placements belonging only to a client.
    """

    return [
        placement
        for placement in placements
        if placement.client_id == client_id
    ]


def validate_contract_dates(
    start_date,
    end_date,
    signed_date,
    renewal_date,
):
    """
    Return an error message if contract dates
    are invalid.

    Returns:
        None = valid
        str  = error message
    """

    today = date.today()

    if (
        end_date
        and end_date < start_date
    ):
        return (
            "End Date cannot be before "
            "Start Date."
        )

    if (
        signed_date
        and signed_date > today
    ):
        return (
            "Signed Date cannot be "
            "in the future."
        )

    if (
        signed_date
        and signed_date < start_date
    ):
        return (
            "Signed Date cannot be before "
            "the contract Start Date."
        )

    if (
        renewal_date
        and renewal_date < start_date
    ):
        return (
            "Renewal Date cannot be before "
            "the contract Start Date."
        )

    if (
        renewal_date
        and end_date
        and renewal_date < end_date
    ):
        return (
            "Renewal Date should normally be "
            "on or after the End Date."
        )

    return None


def get_contract_search_text(contract):
    """
    Build searchable text for a contract.
    """

    parts = [
        contract.contract_number,
        contract.contract_type,
        contract.status,
        contract.currency,
        contract.notes,
        get_client_name(contract),
    ]

    if contract.placement:

        parts.extend(
            [
                contract.placement.position,
            ]
        )

    return normalize_text(
        " ".join(
            str(part or "")
            for part in parts
        )
    )


# ============================================================
# MAIN SCREEN
# ============================================================

def show_contracts():

    st.title("Contracts")

    st.caption(
        "Manage client contracts, agreements, "
        "renewals and contract values."
    )

    session = get_session()

    try:

        # ========================================================
        # SESSION STATE
        # ========================================================

        if (
            "editing_contract_id"
            not in st.session_state
        ):

            st.session_state[
                "editing_contract_id"
            ] = None

        # ========================================================
        # LOAD CLIENTS
        # ========================================================

        clients = (
            session.query(Client)
            .order_by(
                Client.company_name.asc()
            )
            .all()
        )

        # ========================================================
        # LOAD PLACEMENTS
        # ========================================================

        placements = (
            session.query(Placement)
            .order_by(
                Placement.start_date.desc(),
                Placement.id.desc(),
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
                Contract.id.desc(),
            )
            .all()
        )

        # ========================================================
        # CLIENT OPTIONS
        #
        # IMPORTANT:
        # IDs are used as selectbox values.
        # Labels are generated separately.
        #
        # This avoids problems when two clients have
        # similar or identical names.
        # ========================================================

        client_ids = [
            client.id
            for client in clients
        ]

        client_labels = {
            client.id: get_client_label(client)
            for client in clients
        }

        # ========================================================
        # METRICS
        # ========================================================

        total_contracts = len(
            all_contracts
        )

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

        st.subheader(
            "Contract Overview"
        )

        col1, col2, col3, col4, col5 = (
            st.columns(5)
        )

        with col1:

            st.metric(
                "Total Contracts",
                total_contracts,
            )

        with col2:

            st.metric(
                "Active",
                active_contracts,
            )

        with col3:

            st.metric(
                "Signed",
                signed_contracts,
            )

        with col4:

            st.metric(
                "Draft",
                draft_contracts,
            )

        with col5:

            st.metric(
                "Renewal Due",
                renewal_due,
            )

        if expired_contracts:

            st.warning(
                f"{expired_contracts} contract(s) "
                "are expired or past their end date."
            )

        # ========================================================
        # ADD CONTRACT
        # ========================================================

        st.divider()

        st.header(
            "Add Contract"
        )

        if not clients:

            st.warning(
                "Please add a client before "
                "creating a contract."
            )

        else:

            with st.form(
                "add_contract_form",
                clear_on_submit=False,
            ):

                # =================================================
                # BASIC INFORMATION
                # =================================================

                col1, col2 = st.columns(2)

                with col1:

                    selected_client_id = (
                        st.selectbox(
                            "Client *",
                            client_ids,
                            format_func=(
                                lambda client_id:
                                client_labels.get(
                                    client_id,
                                    f"Client {client_id}",
                                )
                            ),
                        )
                    )

                    contract_number = (
                        st.text_input(
                            "Contract Number *",
                            placeholder=(
                                "e.g. AV-UK-2026-001"
                            ),
                        )
                    )

                    contract_type = (
                        st.selectbox(
                            "Contract Type",
                            CONTRACT_TYPES,
                        )
                    )

                with col2:

                    status = st.selectbox(
                        "Status",
                        CONTRACT_STATUSES,
                    )

                    currency = st.selectbox(
                        "Currency",
                        CURRENCIES,
                    )

                    contract_value = (
                        st.number_input(
                            "Contract Value",
                            min_value=0.0,
                            step=100.0,
                        )
                    )

                # =================================================
                # PLACEMENT
                # =================================================

                client_placements = (
                    get_client_placements(
                        placements,
                        selected_client_id,
                    )
                )

                placement_ids = [
                    placement.id
                    for placement
                    in client_placements
                ]

                placement_labels = {
                    placement.id:
                    get_placement_label(
                        placement
                    )
                    for placement
                    in client_placements
                }

                placement_choices = [
                    None
                ] + placement_ids

                selected_placement_id = (
                    st.selectbox(
                        "Placement",
                        placement_choices,
                        format_func=(
                            lambda placement_id:
                            (
                                "No Placement"
                                if placement_id is None
                                else placement_labels.get(
                                    placement_id,
                                    f"Placement {placement_id}",
                                )
                            )
                        ),
                    )
                )

                # =================================================
                # DATES
                # =================================================

                st.subheader(
                    "Contract Dates"
                )

                col1, col2, col3 = (
                    st.columns(3)
                )

                with col1:

                    start_date = st.date_input(
                        "Start Date",
                        value=date.today(),
                    )

                with col2:

                    has_end_date = st.checkbox(
                        "Set End Date"
                    )

                    if has_end_date:

                        end_date = (
                            st.date_input(
                                "End Date",
                                value=date.today(),
                            )
                        )

                    else:

                        end_date = None

                with col3:

                    has_signed_date = (
                        st.checkbox(
                            "Set Signed Date"
                        )
                    )

                    if has_signed_date:

                        signed_date = (
                            st.date_input(
                                "Signed Date",
                                value=date.today(),
                            )
                        )

                    else:

                        signed_date = None

                has_renewal_date = (
                    st.checkbox(
                        "Set Renewal Date"
                    )
                )

                if has_renewal_date:

                    renewal_date = (
                        st.date_input(
                            "Renewal Date",
                            value=date.today(),
                        )
                    )

                else:

                    renewal_date = None

                # =================================================
                # DOCUMENT
                # =================================================

                document_link = (
                    st.text_input(
                        "Document Link",
                        placeholder=(
                            "https://..."
                        ),
                    )
                )

                notes = st.text_area(
                    "Notes",
                    placeholder=(
                        "Additional contract information..."
                    ),
                )

                submitted = (
                    st.form_submit_button(
                        "Create Contract",
                        use_container_width=True,
                    )
                )

                # =================================================
                # CREATE
                # =================================================

                if submitted:

                    clean_number = (
                        contract_number.strip()
                    )

                    clean_document_link = (
                        normalize_url(
                            document_link
                        )
                    )

                    clean_notes = (
                        notes.strip()
                    )

                    # =============================================
                    # VALIDATION
                    # =============================================

                    if not clean_number:

                        st.error(
                            "Contract Number is required."
                        )

                    else:

                        date_error = (
                            validate_contract_dates(
                                start_date,
                                end_date,
                                signed_date,
                                renewal_date,
                            )
                        )

                        if date_error:

                            st.error(
                                date_error
                            )

                        elif not is_valid_url(
                            clean_document_link
                        ):

                            st.error(
                                "Please enter a valid "
                                "document URL."
                            )

                        else:

                            # =====================================
                            # DUPLICATE NUMBER
                            # =====================================

                            duplicate = (
                                find_duplicate_contract_number(
                                    session,
                                    clean_number,
                                )
                            )

                            if duplicate:

                                st.error(
                                    "A contract with this "
                                    "Contract Number already exists."
                                )

                            else:

                                # ================================
                                # PLACEMENT VALIDATION
                                # ================================

                                valid_placement = True

                                if (
                                    selected_placement_id
                                    is not None
                                ):

                                    placement_obj = (
                                        session.get(
                                            Placement,
                                            selected_placement_id,
                                        )
                                    )

                                    if (
                                        not placement_obj
                                        or placement_obj.client_id
                                        != selected_client_id
                                    ):

                                        valid_placement = False

                                        st.error(
                                            "The selected "
                                            "Placement does not "
                                            "belong to the "
                                            "selected Client."
                                        )

                                # ================================
                                # CREATE
                                # ================================

                                if valid_placement:

                                    try:

                                        contract = Contract(
                                            client_id=(
                                                selected_client_id
                                            ),
                                            placement_id=(
                                                selected_placement_id
                                            ),
                                            contract_number=(
                                                clean_number
                                            ),
                                            contract_type=(
                                                contract_type
                                            ),
                                            start_date=(
                                                start_date
                                            ),
                                            end_date=(
                                                end_date
                                            ),
                                            contract_value=(
                                                contract_value
                                            ),
                                            currency=(
                                                currency
                                            ),
                                            status=(
                                                status
                                            ),
                                            signed_date=(
                                                signed_date
                                            ),
                                            renewal_date=(
                                                renewal_date
                                            ),
                                            document_link=(
                                                clean_document_link
                                            ),
                                            notes=(
                                                clean_notes
                                            ),
                                        )

                                        session.add(
                                            contract
                                        )

                                        session.commit()

                                        st.success(
                                            "Contract created "
                                            "successfully."
                                        )

                                        st.rerun()

                                    except Exception as error:

                                        session.rollback()

                                        st.error(
                                            "The contract "
                                            "could not be created."
                                        )

                                        st.exception(
                                            error
                                        )

        # ========================================================
        # CONTRACT REGISTER
        # ========================================================

        st.divider()

        st.header(
            "Contract Register"
        )

        # ========================================================
        # FILTERS
        # ========================================================

        col1, col2, col3, col4 = (
            st.columns(4)
        )

        with col1:

            status_filter = st.selectbox(
                "Status",
                ["All"] + CONTRACT_STATUSES,
            )

        with col2:

            search = st.text_input(
                "Search",
                placeholder=(
                    "Contract number, client, "
                    "type, placement or notes..."
                ),
            )

        with col3:

            renewal_filter = st.selectbox(
                "Renewal",
                [
                    "All",
                    "Renewal Due",
                    "No Renewal Date",
                    "Future Renewal",
                ],
            )

        with col4:

            client_filter_options = (
                [None]
                + client_ids
            )

            client_filter = st.selectbox(
                "Client",
                client_filter_options,
                format_func=(
                    lambda client_id:
                    (
                        "All Clients"
                        if client_id is None
                        else client_labels.get(
                            client_id,
                            f"Client {client_id}",
                        )
                    )
                ),
            )

        # ========================================================
        # FILTER CONTRACTS
        # ========================================================

        filtered_contracts = list(
            all_contracts
        )

        # ========================================================
        # STATUS
        # ========================================================

        if status_filter != "All":

            filtered_contracts = [
                contract
                for contract
                in filtered_contracts
                if contract.status
                == status_filter
            ]

        # ========================================================
        # CLIENT
        # ========================================================

        if client_filter is not None:

            filtered_contracts = [
                contract
                for contract
                in filtered_contracts
                if contract.client_id
                == client_filter
            ]

        # ========================================================
        # SEARCH
        # ========================================================

        if search.strip():

            search_text = normalize_text(
                search
            )

            filtered_contracts = [
                contract
                for contract
                in filtered_contracts
                if search_text
                in get_contract_search_text(
                    contract
                )
            ]

        # ========================================================
        # RENEWAL
        # ========================================================

        if renewal_filter == "Renewal Due":

            filtered_contracts = [
                contract
                for contract
                in filtered_contracts
                if is_renewal_due(
                    contract
                )
            ]

        elif renewal_filter == "No Renewal Date":

            filtered_contracts = [
                contract
                for contract
                in filtered_contracts
                if not contract.renewal_date
            ]

        elif renewal_filter == "Future Renewal":

            filtered_contracts = [
                contract
                for contract
                in filtered_contracts
                if (
                    contract.renewal_date
                    and contract.renewal_date
                    > date.today()
                    and contract.status
                    not in [
                        "Expired",
                        "Terminated",
                    ]
                )
            ]

        # ========================================================
        # RESULT COUNT
        # ========================================================

        st.caption(
            f"Showing "
            f"{len(filtered_contracts)} "
            f"of "
            f"{len(all_contracts)} "
            f"contracts"
        )

        # ========================================================
        # DISPLAY CONTRACTS
        # ========================================================

        if not filtered_contracts:

            st.info(
                "No contracts match the "
                "selected filters."
            )

        else:

            for contract in (
                filtered_contracts
            ):

                with st.container(
                    border=True
                ):

                    col1, col2, col3, col4 = (
                        st.columns(
                            [3, 3, 2, 2]
                        )
                    )

                    # ============================================
                    # CONTRACT INFORMATION
                    # ============================================

                    with col1:

                        contract_title = (
                            contract.contract_number
                            or "Unnamed Contract"
                        )

                        st.markdown(
                            f"### {contract_title}"
                        )

                        st.write(
                            get_client_name(
                                contract
                            )
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

                    # ============================================
                    # STATUS / DATES
                    # ============================================

                    with col2:

                        status = (
                            get_status_display(
                                contract.status
                            )
                        )

                        if status == "Active":

                            st.success(
                                status
                            )

                        elif status == "Signed":

                            st.info(
                                status
                            )

                        elif status in [
                            "Expired",
                            "Terminated",
                        ]:

                            st.error(
                                status
                            )

                        else:

                            st.warning(
                                status
                            )

                        if contract.start_date:

                            st.caption(
                                f"Start: "
                                f"{contract.start_date.strftime('%d %b %Y')}"
                            )

                        if contract.end_date:

                            st.caption(
                                f"End: "
                                f"{contract.end_date.strftime('%d %b %Y')}"
                            )

                            if is_expired(
                                contract
                            ):

                                st.error(
                                    "Contract end date "
                                    "has passed."
                                )

                    # ============================================
                    # VALUE / RENEWAL
                    # ============================================

                    with col3:

                        st.write(
                            "**Contract Value**"
                        )

                        currency = (
                            contract.currency
                            or "GBP"
                        )

                        value = float(
                            contract.contract_value
                            or 0
                        )

                        st.write(
                            f"{currency} "
                            f"{value:,.2f}"
                        )

                        if contract.signed_date:

                            st.caption(
                                f"Signed: "
                                f"{contract.signed_date.strftime('%d %b %Y')}"
                            )

                        if contract.renewal_date:

                            renewal_state = (
                                get_renewal_state(
                                    contract
                                )
                            )

                            renewal_label = (
                                get_renewal_label(
                                    contract
                                )
                            )

                            if (
                                renewal_state
                                == "Overdue"
                            ):

                                st.error(
                                    f"Renewal: "
                                    f"{renewal_label}"
                                )

                            elif (
                                renewal_state
                                in [
                                    "Today",
                                    "Soon",
                                ]
                            ):

                                st.warning(
                                    f"Renewal: "
                                    f"{renewal_label}"
                                )

                            else:

                                st.caption(
                                    f"Renewal: "
                                    f"{renewal_label}"
                                )

                    # ============================================
                    # ACTIONS
                    # ============================================

                    with col4:

                        if contract.document_link:

                            st.link_button(
                                "Open Document",
                                contract.document_link,
                                use_container_width=True,
                            )

                        if st.button(
                            "Edit",
                            key=(
                                f"edit_contract_"
                                f"{contract.id}"
                            ),
                            use_container_width=True,
                        ):

                            st.session_state[
                                "editing_contract_id"
                            ] = contract.id

                            st.rerun()

                    # ============================================
                    # NOTES
                    # ============================================

                    if contract.notes:

                        st.caption(
                            f"Notes: "
                            f"{contract.notes}"
                        )

        # ========================================================
        # EDIT CONTRACT
        # ========================================================

        editing_id = (
            st.session_state.get(
                "editing_contract_id"
            )
        )

        if editing_id is None:

            return

        contract = session.get(
            Contract,
            editing_id,
        )

        if not contract:

            st.session_state[
                "editing_contract_id"
            ] = None

            st.warning(
                "The selected contract "
                "could not be found."
            )

            return

        # ========================================================
        # EDIT HEADER
        # ========================================================

        st.divider()

        st.header(
            "Edit Contract"
        )

        # ========================================================
        # EDIT CLIENT
        # ========================================================

        if not clients:

            st.error(
                "No clients are available."
            )

            return

        current_client_id = (
            contract.client_id
            if contract.client_id
            in client_ids
            else client_ids[0]
        )

        # ========================================================
        # EDIT FORM
        # ========================================================

        with st.form(
            f"edit_contract_form_{contract.id}"
        ):

            # =====================================================
            # BASIC INFORMATION
            # =====================================================

            edit_client_id = (
                st.selectbox(
                    "Client",
                    client_ids,
                    index=client_ids.index(
                        current_client_id
                    ),
                    format_func=(
                        lambda client_id:
                        client_labels.get(
                            client_id,
                            f"Client {client_id}",
                        )
                    ),
                )
            )

            edit_contract_number = (
                st.text_input(
                    "Contract Number",
                    value=(
                        contract.contract_number
                        or ""
                    ),
                )
            )

            current_type = (
                contract.contract_type
                if contract.contract_type
                in CONTRACT_TYPES
                else "Other"
            )

            edit_contract_type = (
                st.selectbox(
                    "Contract Type",
                    CONTRACT_TYPES,
                    index=CONTRACT_TYPES.index(
                        current_type
                    ),
                )
            )

            # =====================================================
            # PLACEMENT
            # =====================================================

            edit_client_placements = (
                get_client_placements(
                    placements,
                    edit_client_id,
                )
            )

            edit_placement_ids = [
                placement.id
                for placement
                in edit_client_placements
            ]

            edit_placement_labels = {
                placement.id:
                get_placement_label(
                    placement
                )
                for placement
                in edit_client_placements
            }

            edit_placement_choices = (
                [None]
                + edit_placement_ids
            )

            current_placement_id = (
                contract.placement_id
                if (
                    contract.placement_id
                    in edit_placement_ids
                )
                else None
            )

            edit_placement = (
                st.selectbox(
                    "Placement",
                    edit_placement_choices,
                    index=edit_placement_choices.index(
                        current_placement_id
                    ),
                    format_func=(
                        lambda placement_id:
                        (
                            "No Placement"
                            if placement_id is None
                            else edit_placement_labels.get(
                                placement_id,
                                f"Placement {placement_id}",
                            )
                        )
                    ),
                )
            )

            # =====================================================
            # DATES
            # =====================================================

            st.subheader(
                "Contract Dates"
            )

            col1, col2, col3 = (
                st.columns(3)
            )

            with col1:

                edit_start_date = (
                    st.date_input(
                        "Start Date",
                        value=(
                            contract.start_date
                            or date.today()
                        ),
                    )
                )

            with col2:

                edit_has_end_date = (
                    st.checkbox(
                        "Set End Date",
                        value=(
                            contract.end_date
                            is not None
                        ),
                    )
                )

                if edit_has_end_date:

                    edit_end_date = (
                        st.date_input(
                            "End Date",
                            value=(
                                contract.end_date
                                or date.today()
                            ),
                        )
                    )

                else:

                    edit_end_date = None

            with col3:

                edit_has_signed_date = (
                    st.checkbox(
                        "Set Signed Date",
                        value=(
                            contract.signed_date
                            is not None
                        ),
                    )
                )

                if edit_has_signed_date:

                    edit_signed_date = (
                        st.date_input(
                            "Signed Date",
                            value=(
                                contract.signed_date
                                or date.today()
                            ),
                        )
                    )

                else:

                    edit_signed_date = None

            edit_has_renewal_date = (
                st.checkbox(
                    "Set Renewal Date",
                    value=(
                        contract.renewal_date
                        is not None
                    ),
                )
            )

            if edit_has_renewal_date:

                edit_renewal_date = (
                    st.date_input(
                        "Renewal Date",
                        value=(
                            contract.renewal_date
                            or date.today()
                        ),
                    )
                )

            else:

                edit_renewal_date = None

            # =====================================================
            # FINANCIAL INFORMATION
            # =====================================================

            col1, col2, col3 = (
                st.columns(3)
            )

            with col1:

                edit_value = (
                    st.number_input(
                        "Contract Value",
                        min_value=0.0,
                        value=float(
                            contract.contract_value
                            or 0
                        ),
                        step=100.0,
                    )
                )

            with col2:

                current_currency = (
                    contract.currency
                    if contract.currency
                    in CURRENCIES
                    else "GBP"
                )

                edit_currency = (
                    st.selectbox(
                        "Currency",
                        CURRENCIES,
                        index=CURRENCIES.index(
                            current_currency
                        ),
                    )
                )

            with col3:

                current_status = (
                    contract.status
                    if contract.status
                    in CONTRACT_STATUSES
                    else "Draft"
                )

                edit_status = (
                    st.selectbox(
                        "Status",
                        CONTRACT_STATUSES,
                        index=CONTRACT_STATUSES.index(
                            current_status
                        ),
                    )
                )

            # =====================================================
            # DOCUMENT / NOTES
            # =====================================================

            edit_document_link = (
                st.text_input(
                    "Document Link",
                    value=(
                        contract.document_link
                        or ""
                    ),
                )
            )

            edit_notes = (
                st.text_area(
                    "Notes",
                    value=(
                        contract.notes
                        or ""
                    ),
                )
            )

            # =====================================================
            # BUTTONS
            # =====================================================

            col1, col2 = (
                st.columns(2)
            )

            with col1:

                save = (
                    st.form_submit_button(
                        "Save Changes",
                        use_container_width=True,
                    )
                )

            with col2:

                cancel = (
                    st.form_submit_button(
                        "Cancel",
                        use_container_width=True,
                    )
                )

            # =====================================================
            # CANCEL
            # =====================================================

            if cancel:

                st.session_state[
                    "editing_contract_id"
                ] = None

                st.rerun()

            # =====================================================
            # SAVE
            # =====================================================

            if save:

                clean_number = (
                    edit_contract_number.strip()
                )

                clean_document_link = (
                    normalize_url(
                        edit_document_link
                    )
                )

                clean_notes = (
                    edit_notes.strip()
                )

                # ================================================
                # BASIC VALIDATION
                # ================================================

                if not clean_number:

                    st.error(
                        "Contract Number is required."
                    )

                else:

                    date_error = (
                        validate_contract_dates(
                            edit_start_date,
                            edit_end_date,
                            edit_signed_date,
                            edit_renewal_date,
                        )
                    )

                    if date_error:

                        st.error(
                            date_error
                        )

                    elif not is_valid_url(
                        clean_document_link
                    ):

                        st.error(
                            "Please enter a valid "
                            "document URL."
                        )

                    else:

                        # ==========================================
                        # DUPLICATE CONTRACT NUMBER
                        # ==========================================

                        duplicate = (
                            find_duplicate_contract_number(
                                session,
                                clean_number,
                                exclude_id=contract.id,
                            )
                        )

                        if duplicate:

                            st.error(
                                "Another contract "
                                "already uses this "
                                "Contract Number."
                            )

                        else:

                            # ======================================
                            # PLACEMENT VALIDATION
                            # ======================================

                            valid_placement = True

                            if (
                                edit_placement
                                is not None
                            ):

                                placement_obj = (
                                    session.get(
                                        Placement,
                                        edit_placement,
                                    )
                                )

                                if (
                                    not placement_obj
                                    or placement_obj.client_id
                                    != edit_client_id
                                ):

                                    valid_placement = False

                                    st.error(
                                        "The selected "
                                        "Placement does not "
                                        "belong to the "
                                        "selected Client."
                                    )

                            # ======================================
                            # UPDATE
                            # ======================================

                            if valid_placement:

                                try:

                                    contract.client_id = (
                                        edit_client_id
                                    )

                                    contract.placement_id = (
                                        edit_placement
                                    )

                                    contract.contract_number = (
                                        clean_number
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
                                        clean_document_link
                                    )

                                    contract.notes = (
                                        clean_notes
                                    )

                                    session.commit()

                                    st.session_state[
                                        "editing_contract_id"
                                    ] = None

                                    st.success(
                                        "Contract updated "
                                        "successfully."
                                    )

                                    st.rerun()

                                except Exception as error:

                                    session.rollback()

                                    st.error(
                                        "The contract "
                                        "could not be updated."
                                    )

                                    st.exception(
                                        error

                                    )

    except Exception as error:

        session.rollback()

        st.error(
            "An error occurred while loading "
            "the Contracts screen."
        )

        st.exception(
            error
        )

    finally:

        session.close()