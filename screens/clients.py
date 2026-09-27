
import streamlit as st

from database import get_session
from models import Client


# ============================================================
# CONSTANTS
# ============================================================

CLIENT_STATUSES = [
    "Lead",
    "Contacted",
    "Replied",
    "Call",
    "Proposal",
    "Negotiation",
    "Contract",
    "Won",
    "Lost",
]

COMPANY_SIZES = [
    "",
    "1-10",
    "11-50",
    "51-200",
    "201-500",
    "501-1,000",
    "1,001-5,000",
    "5,001-10,000",
    "10,000+",
]

LEAD_SOURCES = [
    "",
    "LinkedIn",
    "Website",
    "Referral",
    "Email",
    "Cold Call",
    "Networking",
    "Job Board",
    "Other",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_location(client):
    """Return a readable client location."""

    return ", ".join(
        part
        for part in [
            client.city,
            client.country,
        ]
        if part
    )


def get_status_label(status):
    """Return a readable status label."""

    if not status:
        return "—"

    return status


# ============================================================
# MAIN CLIENTS SCREEN
# ============================================================

def show_clients():

    st.title("Clients")

    st.caption(
        "Manage AVERRA clients, prospects and sales pipeline."
    )

    session = get_session()

    try:

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
        # CLIENT OVERVIEW
        # ========================================================

        total_clients = len(clients)

        active_pipeline = sum(
            1
            for client in clients
            if client.status not in [
                "Won",
                "Lost",
            ]
        )

        won_clients = sum(
            1
            for client in clients
            if client.status == "Won"
        )

        lost_clients = sum(
            1
            for client in clients
            if client.status == "Lost"
        )

        st.header("Client Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Total Clients",
                total_clients,
            )

        with col2:

            st.metric(
                "Active Pipeline",
                active_pipeline,
            )

        with col3:

            st.metric(
                "Won",
                won_clients,
            )

        with col4:

            st.metric(
                "Lost",
                lost_clients,
            )

        st.divider()

        # ========================================================
        # ADD NEW CLIENT
        # ========================================================

        st.header("Add New Client")

        with st.form("add_client_form"):

            # ====================================================
            # COMPANY INFORMATION
            # ====================================================

            col1, col2 = st.columns(2)

            with col1:

                company_name = st.text_input(
                    "Company Name *"
                )

                industry = st.text_input(
                    "Industry"
                )

                website = st.text_input(
                    "Website"
                )

                country = st.text_input(
                    "Country",
                    value="UK",
                )

                city = st.text_input(
                    "City"
                )

            # ====================================================
            # ADDRESS / CLASSIFICATION
            # ====================================================

            with col2:

                address = st.text_input(
                    "Address"
                )

                postcode = st.text_input(
                    "Postcode"
                )

                company_size = st.selectbox(
                    "Company Size",
                    COMPANY_SIZES,
                )

                status = st.selectbox(
                    "Status",
                    CLIENT_STATUSES,
                )

                lead_source = st.selectbox(
                    "Lead Source",
                    LEAD_SOURCES,
                )

            # ====================================================
            # ACCOUNT MANAGEMENT
            # ====================================================

            account_owner = st.text_input(
                "Account Owner"
            )

            next_follow_up = st.date_input(
                "Next Follow-Up",
                value=None,
            )

            notes = st.text_area(
                "Notes"
            )

            submitted = st.form_submit_button(
                "Add Client",
                use_container_width=True,
            )

            # ====================================================
            # PROCESS NEW CLIENT
            # ====================================================

            if submitted:

                clean_company_name = (
                    company_name.strip()
                )

                if not clean_company_name:

                    st.error(
                        "Company Name is required."
                    )

                else:

                    # ============================================
                    # DUPLICATE CHECK
                    # ============================================

                    existing_client = (
                        session.query(Client)
                        .filter(
                            Client.company_name.ilike(
                                clean_company_name
                            )
                        )
                        .first()
                    )

                    if existing_client:

                        st.error(
                            "A client with this company "
                            "name already exists."
                        )

                    else:

                        new_client = Client(
                            company_name=(
                                clean_company_name
                            ),
                            industry=(
                                industry.strip()
                            ),
                            website=(
                                website.strip()
                            ),
                            country=(
                                country.strip()
                            ),
                            city=(
                                city.strip()
                            ),
                            address=(
                                address.strip()
                            ),
                            postcode=(
                                postcode.strip()
                            ),
                            company_size=(
                                company_size
                            ),
                            status=(
                                status
                            ),
                            lead_source=(
                                lead_source
                            ),
                            next_follow_up=(
                                next_follow_up
                            ),
                            account_owner=(
                                account_owner.strip()
                            ),
                            notes=(
                                notes.strip()
                            ),
                        )

                        session.add(
                            new_client
                        )

                        session.commit()

                        st.success(
                            f"{clean_company_name} "
                            "added successfully."
                        )

                        st.rerun()

        st.divider()

        # ========================================================
        # CLIENT REGISTER
        # ========================================================

        st.header("Client Register")

        if not clients:

            st.info(
                "No clients have been added yet."
            )

        else:

            # ====================================================
            # FILTER OPTIONS
            # ====================================================

            industries = sorted(
                {
                    client.industry
                    for client in clients
                    if client.industry
                }
            )

            countries = sorted(
                {
                    client.country
                    for client in clients
                    if client.country
                }
            )

            # ====================================================
            # FILTERS
            # ====================================================

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                search = st.text_input(
                    "Search",
                    placeholder=(
                        "Company, industry, city, "
                        "website or owner..."
                    ),
                )

            with col2:

                status_filter = st.selectbox(
                    "Status",
                    ["All"] + CLIENT_STATUSES,
                )

            with col3:

                industry_filter = st.selectbox(
                    "Industry",
                    ["All"] + industries,
                )

            with col4:

                country_filter = st.selectbox(
                    "Country",
                    ["All"] + countries,
                )

            # ====================================================
            # APPLY FILTERS
            # ====================================================

            filtered_clients = clients

            # ----------------------------------------------------
            # SEARCH
            # ----------------------------------------------------

            if search:

                search_text = (
                    search.strip().lower()
                )

                filtered_clients = [
                    client
                    for client in filtered_clients
                    if (
                        search_text
                        in (
                            client.company_name
                            or ""
                        ).lower()

                        or search_text
                        in (
                            client.industry
                            or ""
                        ).lower()

                        or search_text
                        in (
                            client.city
                            or ""
                        ).lower()

                        or search_text
                        in (
                            client.country
                            or ""
                        ).lower()

                        or search_text
                        in (
                            client.website
                            or ""
                        ).lower()

                        or search_text
                        in (
                            client.account_owner
                            or ""
                        ).lower()

                        or search_text
                        in (
                            client.lead_source
                            or ""
                        ).lower()

                        or search_text
                        in (
                            client.notes
                            or ""
                        ).lower()
                    )
                ]

            # ----------------------------------------------------
            # STATUS
            # ----------------------------------------------------

            if status_filter != "All":

                filtered_clients = [
                    client
                    for client in filtered_clients
                    if client.status
                    == status_filter
                ]

            # ----------------------------------------------------
            # INDUSTRY
            # ----------------------------------------------------

            if industry_filter != "All":

                filtered_clients = [
                    client
                    for client in filtered_clients
                    if client.industry
                    == industry_filter
                ]

            # ----------------------------------------------------
            # COUNTRY
            # ----------------------------------------------------

            if country_filter != "All":

                filtered_clients = [
                    client
                    for client in filtered_clients
                    if client.country
                    == country_filter
                ]

            # ====================================================
            # FILTER RESULT
            # ====================================================

            st.write(
                f"Showing **{len(filtered_clients)}** "
                f"client(s)"
            )

            # ====================================================
            # DISPLAY CLIENTS
            # ====================================================

            for client in filtered_clients:

                with st.container(
                    border=True
                ):

                    col1, col2, col3, col4 = (
                        st.columns(
                            [3, 2, 3, 1]
                        )
                    )

                    # ============================================
                    # COMPANY
                    # ============================================

                    with col1:

                        st.subheader(
                            client.company_name
                        )

                        if client.industry:

                            st.write(
                                client.industry
                            )

                        location = get_location(
                            client
                        )

                        if location:

                            st.caption(
                                location
                            )

                    # ============================================
                    # STATUS
                    # ============================================

                    with col2:

                        st.write(
                            "**Pipeline Status**"
                        )

                        st.write(
                            get_status_label(
                                client.status
                            )
                        )

                        if client.lead_source:

                            st.caption(
                                f"Source: "
                                f"{client.lead_source}"
                            )

                    # ============================================
                    # DETAILS
                    # ============================================

                    with col3:

                        st.write(
                            "**Details**"
                        )

                        if client.website:

                            st.write(
                                client.website
                            )

                        if client.company_size:

                            st.caption(
                                f"Size: "
                                f"{client.company_size}"
                            )

                        if client.account_owner:

                            st.caption(
                                f"Owner: "
                                f"{client.account_owner}"
                            )

                        if client.next_follow_up:

                            st.caption(
                                "Follow-up: "
                                f"{client.next_follow_up}"
                            )

                    # ============================================
                    # ACTIONS
                    # ============================================

                    with col4:

                        if st.button(
                            "Edit",
                            key=(
                                f"edit_client_"
                                f"{client.id}"
                            ),
                            use_container_width=True,
                        ):

                            st.session_state[
                                "editing_client_id"
                            ] = client.id

                            st.session_state.pop(
                                "deleting_client_id",
                                None,
                            )

                            st.rerun()

                        if st.button(
                            "Delete",
                            key=(
                                f"delete_client_"
                                f"{client.id}"
                            ),
                            use_container_width=True,
                        ):

                            st.session_state[
                                "deleting_client_id"
                            ] = client.id

                            st.session_state.pop(
                                "editing_client_id",
                                None,
                            )

                            st.rerun()

                    # ============================================
                    # NOTES
                    # ============================================

                    if client.notes:

                        st.write(
                            "**Notes**"
                        )

                        st.caption(
                            client.notes
                        )

            # ====================================================
            # DELETE CLIENT
            # ====================================================

            deleting_id = st.session_state.get(
                "deleting_client_id"
            )

            if deleting_id:

                client = session.get(
                    Client,
                    deleting_id,
                )

                if client:

                    st.divider()

                    st.warning(
                        "Are you sure you want to delete "
                        f"{client.company_name}?"
                    )

                    st.warning(
                        "Deleting a client may affect "
                        "related contacts, jobs, placements, "
                        "contracts, invoices and activities."
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "Yes, Delete Client",
                            key="confirm_delete_client",
                            use_container_width=True,
                        ):

                            session.delete(
                                client
                            )

                            session.commit()

                            st.session_state.pop(
                                "deleting_client_id",
                                None,
                            )

                            st.success(
                                "Client deleted successfully."
                            )

                            st.rerun()

                    with col2:

                        if st.button(
                            "Cancel",
                            key="cancel_delete_client",
                            use_container_width=True,
                        ):

                            st.session_state.pop(
                                "deleting_client_id",
                                None,
                            )

                            st.rerun()

            # ====================================================
            # EDIT CLIENT
            # ====================================================

            editing_id = st.session_state.get(
                "editing_client_id"
            )

            if editing_id:

                client = session.get(
                    Client,
                    editing_id,
                )

                if client:

                    st.divider()

                    st.header(
                        f"Edit Client: "
                        f"{client.company_name}"
                    )

                    with st.form(
                        f"edit_client_{client.id}"
                    ):

                        # ========================================
                        # COMPANY INFORMATION
                        # ========================================

                        col1, col2 = st.columns(2)

                        with col1:

                            edit_company_name = (
                                st.text_input(
                                    "Company Name *",
                                    value=(
                                        client.company_name
                                        or ""
                                    ),
                                )
                            )

                            edit_industry = (
                                st.text_input(
                                    "Industry",
                                    value=(
                                        client.industry
                                        or ""
                                    ),
                                )
                            )

                            edit_website = (
                                st.text_input(
                                    "Website",
                                    value=(
                                        client.website
                                        or ""
                                    ),
                                )
                            )

                            edit_country = (
                                st.text_input(
                                    "Country",
                                    value=(
                                        client.country
                                        or ""
                                    ),
                                )
                            )

                            edit_city = (
                                st.text_input(
                                    "City",
                                    value=(
                                        client.city
                                        or ""
                                    ),
                                )
                            )

                        # ========================================
                        # ADDRESS / CLASSIFICATION
                        # ========================================

                        with col2:

                            edit_address = (
                                st.text_input(
                                    "Address",
                                    value=(
                                        client.address
                                        or ""
                                    ),
                                )
                            )

                            edit_postcode = (
                                st.text_input(
                                    "Postcode",
                                    value=(
                                        client.postcode
                                        or ""
                                    ),
                                )
                            )

                            current_size = (
                                client.company_size
                                if client.company_size
                                in COMPANY_SIZES
                                else ""
                            )

                            edit_company_size = (
                                st.selectbox(
                                    "Company Size",
                                    COMPANY_SIZES,
                                    index=(
                                        COMPANY_SIZES.index(
                                            current_size
                                        )
                                    ),
                                )
                            )

                            current_status = (
                                client.status
                                if client.status
                                in CLIENT_STATUSES
                                else "Lead"
                            )

                            edit_status = (
                                st.selectbox(
                                    "Status",
                                    CLIENT_STATUSES,
                                    index=(
                                        CLIENT_STATUSES.index(
                                            current_status
                                        )
                                    ),
                                )
                            )

                            current_source = (
                                client.lead_source
                                if client.lead_source
                                in LEAD_SOURCES
                                else ""
                            )

                            edit_lead_source = (
                                st.selectbox(
                                    "Lead Source",
                                    LEAD_SOURCES,
                                    index=(
                                        LEAD_SOURCES.index(
                                            current_source
                                        )
                                    ),
                                )
                            )

                        # ========================================
                        # ACCOUNT MANAGEMENT
                        # ========================================

                        edit_account_owner = (
                            st.text_input(
                                "Account Owner",
                                value=(
                                    client.account_owner
                                    or ""
                                ),
                            )
                        )

                        edit_next_follow_up = (
                            st.date_input(
                                "Next Follow-Up",
                                value=(
                                    client.next_follow_up
                                ),
                            )
                        )

                        edit_notes = (
                            st.text_area(
                                "Notes",
                                value=(
                                    client.notes
                                    or ""
                                ),
                            )
                        )

                        # ========================================
                        # FORM BUTTONS
                        # ========================================

                        col1, col2 = st.columns(2)

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

                        # ========================================
                        # SAVE EDIT
                        # ========================================

                        if save:

                            clean_company_name = (
                                edit_company_name.strip()
                            )

                            if not clean_company_name:

                                st.error(
                                    "Company Name is required."
                                )

                            else:

                                duplicate = (
                                    session.query(
                                        Client
                                    )
                                    .filter(
                                        Client.company_name.ilike(
                                            clean_company_name
                                        ),
                                        Client.id
                                        != client.id,
                                    )
                                    .first()
                                )

                                if duplicate:

                                    st.error(
                                        "Another client with this "
                                        "company name already exists."
                                    )

                                else:

                                    client.company_name = (
                                        clean_company_name
                                    )

                                    client.industry = (
                                        edit_industry.strip()
                                    )

                                    client.website = (
                                        edit_website.strip()
                                    )

                                    client.country = (
                                        edit_country.strip()
                                    )

                                    client.city = (
                                        edit_city.strip()
                                    )

                                    client.address = (
                                        edit_address.strip()
                                    )

                                    client.postcode = (
                                        edit_postcode.strip()
                                    )

                                    client.company_size = (
                                        edit_company_size
                                    )

                                    client.status = (
                                        edit_status
                                    )

                                    client.lead_source = (
                                        edit_lead_source
                                    )

                                    client.account_owner = (
                                        edit_account_owner.strip()
                                    )

                                    client.next_follow_up = (
                                        edit_next_follow_up
                                    )

                                    client.notes = (
                                        edit_notes.strip()
                                    )

                                    session.commit()

                                    st.session_state.pop(
                                        "editing_client_id",
                                        None,
                                    )

                                    st.success(
                                        "Client updated successfully."
                                    )

                                    st.rerun()

                        # ========================================
                        # CANCEL EDIT
                        # ========================================

                        if cancel:

                            st.session_state.pop(
                                "editing_client_id",
                                None,
                            )

                            st.rerun()

    except Exception as error:

        session.rollback()

        st.error(
            "An error occurred while loading "
            "the Clients screen."
        )

        st.exception(error)

    finally:

        session.close()

