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
    "Active",
    "Inactive",
]

LEAD_SOURCES = [
    "Website",
    "LinkedIn",
    "Referral",
    "Cold Outreach",
    "Email",
    "Job Board",
    "Networking",
    "Existing Client",
    "Other",
]

COMPANY_SIZES = [
    "1-10",
    "11-50",
    "51-200",
    "201-500",
    "501-1000",
    "1001-5000",
    "5001+",
]

COUNTRIES = [
    "UK",
    "Ireland",
    "Lithuania",
    "Germany",
    "France",
    "Netherlands",
    "United States",
    "Canada",
    "Australia",
    "Other",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_client_name(client):
    """Return the client's company name."""

    company_name = (
        client.company_name or ""
    ).strip()

    return (
        company_name
        or f"Client {client.id}"
    )


def get_client_label(client):
    """Return a consistent client label."""

    return (
        f"{get_client_name(client)} "
        f"(ID: {client.id})"
    )


def is_valid_website(website):
    """Basic website URL validation."""

    website = (
        website or ""
    ).strip()

    if not website:
        return True

    website_lower = website.lower()

    return (
        website_lower.startswith("http://")
        or website_lower.startswith("https://")
    )


def get_contact_count(client):
    """Return number of contacts linked to a client."""

    try:

        return len(
            client.contacts
        )

    except Exception:

        return 0


def get_primary_contact_count(client):
    """Return number of primary contacts linked to a client."""

    try:

        return sum(
            1
            for contact in client.contacts
            if contact.primary_contact == "Yes"
        )

    except Exception:

        return 0


def get_related_record_counts(client):
    """Return counts of records linked to a client."""

    try:

        return {
            "contacts": len(client.contacts),
            "jobs": len(client.jobs),
            "placements": len(client.placements),
            "activities": len(client.activities),
            "contracts": len(client.contracts),
            "invoices": len(client.invoices),
        }

    except Exception:

        return {
            "contacts": 0,
            "jobs": 0,
            "placements": 0,
            "activities": 0,
            "contracts": 0,
            "invoices": 0,
        }


def has_related_records(client):
    """Check whether the client has linked CRM records."""

    counts = get_related_record_counts(
        client
    )

    return any(
        count > 0
        for count in counts.values()
    )


def clear_delete_confirmation(client_id):
    """Clear delete confirmation state."""

    st.session_state[
        f"confirm_delete_client_{client_id}"
    ] = False


# ============================================================
# MAIN CLIENTS SCREEN
# ============================================================

def show_clients():

    st.title("Clients")

    st.caption(
        "Manage AVERRA clients, prospects and business relationships."
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
        # SESSION STATE
        # ========================================================

        if "editing_client_id" not in st.session_state:

            st.session_state.editing_client_id = None

        # ========================================================
        # OVERVIEW
        # ========================================================

        st.subheader("Overview")

        total_clients = len(clients)

        active_clients = sum(
            1
            for client in clients
            if client.status == "Active"
        )

        pipeline_clients = sum(
            1
            for client in clients
            if client.status in [
                "Lead",
                "Contacted",
                "Replied",
                "Call",
                "Proposal",
                "Negotiation",
                "Contract",
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

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Total Clients",
                total_clients,
            )

        with col2:

            st.metric(
                "Active",
                active_clients,
            )

        with col3:

            st.metric(
                "Pipeline",
                pipeline_clients,
            )

        with col4:

            st.metric(
                "Won",
                won_clients,
            )

        st.divider()

        # ========================================================
        # ADD / EDIT CLIENT
        # ========================================================

        editing_client = None

        editing_client_id = (
            st.session_state.editing_client_id
        )

        if editing_client_id:

            editing_client = session.get(
                Client,
                editing_client_id,
            )

            if not editing_client:

                st.session_state.editing_client_id = None

                editing_client_id = None

        # ========================================================
        # DEFAULT VALUES
        # ========================================================

        if editing_client:

            st.subheader(
                "Edit Client"
            )

            default_company_name = (
                editing_client.company_name
                or ""
            )

            default_industry = (
                editing_client.industry
                or ""
            )

            default_website = (
                editing_client.website
                or ""
            )

            default_country = (
                editing_client.country
                or "UK"
            )

            default_city = (
                editing_client.city
                or ""
            )

            default_address = (
                editing_client.address
                or ""
            )

            default_postcode = (
                editing_client.postcode
                or ""
            )

            default_company_size = (
                editing_client.company_size
                or ""
            )

            default_status = (
                editing_client.status
                or "Lead"
            )

            default_lead_source = (
                editing_client.lead_source
                or ""
            )

            default_next_follow_up = (
                editing_client.next_follow_up
            )

            default_account_owner = (
                editing_client.account_owner
                or ""
            )

            default_notes = (
                editing_client.notes
                or ""
            )

        else:

            st.subheader(
                "Add Client"
            )

            default_company_name = ""
            default_industry = ""
            default_website = ""
            default_country = "UK"
            default_city = ""
            default_address = ""
            default_postcode = ""
            default_company_size = ""
            default_status = "Lead"
            default_lead_source = ""
            default_next_follow_up = None
            default_account_owner = ""
            default_notes = ""

        # ========================================================
        # CLIENT FORM
        # ========================================================

        with st.form(
            "client_form",
            clear_on_submit=False,
        ):

            company_name = st.text_input(
                "Company Name *",
                value=default_company_name,
                placeholder="e.g. ABC Limited",
            )

            col1, col2 = st.columns(2)

            # ====================================================
            # COMPANY INFORMATION
            # ====================================================

            with col1:

                industry = st.text_input(
                    "Industry",
                    value=default_industry,
                    placeholder=(
                        "e.g. Accounting, "
                        "Architecture, Technology"
                    ),
                )

                website = st.text_input(
                    "Website",
                    value=default_website,
                    placeholder=(
                        "https://www.example.com"
                    ),
                )

                country = st.selectbox(
                    "Country",
                    COUNTRIES,
                    index=(
                        COUNTRIES.index(
                            default_country
                        )
                        if default_country
                        in COUNTRIES
                        else 0
                    ),
                )

                city = st.text_input(
                    "City",
                    value=default_city,
                )

                company_size = st.selectbox(
                    "Company Size",
                    ["Not specified"]
                    + COMPANY_SIZES,
                    index=(
                        (
                            COMPANY_SIZES.index(
                                default_company_size
                            )
                            + 1
                        )
                        if default_company_size
                        in COMPANY_SIZES
                        else 0
                    ),
                )

            # ====================================================
            # SALES INFORMATION
            # ====================================================

            with col2:

                status = st.selectbox(
                    "Status",
                    CLIENT_STATUSES,
                    index=(
                        CLIENT_STATUSES.index(
                            default_status
                        )
                        if default_status
                        in CLIENT_STATUSES
                        else 0
                    ),
                )

                lead_source = st.selectbox(
                    "Lead Source",
                    ["Not specified"]
                    + LEAD_SOURCES,
                    index=(
                        (
                            LEAD_SOURCES.index(
                                default_lead_source
                            )
                            + 1
                        )
                        if default_lead_source
                        in LEAD_SOURCES
                        else 0
                    ),
                )

                account_owner = st.text_input(
                    "Account Owner",
                    value=default_account_owner,
                    placeholder="e.g. Sandra",
                )

                next_follow_up = st.date_input(
                    "Next Follow-Up",
                    value=default_next_follow_up,
                    min_value=None,
                )

            # ====================================================
            # ADDRESS
            # ====================================================

            address = st.text_input(
                "Address",
                value=default_address,
            )

            postcode = st.text_input(
                "Postcode",
                value=default_postcode,
            )

            # ====================================================
            # NOTES
            # ====================================================

            notes = st.text_area(
                "Notes",
                value=default_notes,
            )

            # ====================================================
            # SUBMIT
            # ====================================================

            if editing_client:

                submitted = st.form_submit_button(
                    "Update Client",
                    use_container_width=True,
                )

            else:

                submitted = st.form_submit_button(
                    "Add Client",
                    use_container_width=True,
                )

            # ====================================================
            # PROCESS FORM
            # ====================================================

            if submitted:

                company_name = (
                    company_name.strip()
                )

                industry = (
                    industry.strip()
                )

                website = (
                    website.strip()
                )

                city = (
                    city.strip()
                )

                address = (
                    address.strip()
                )

                postcode = (
                    postcode.strip()
                )

                account_owner = (
                    account_owner.strip()
                )

                notes = (
                    notes.strip()
                )

                # Convert placeholder selections
                if company_size == "Not specified":

                    company_size = ""

                if lead_source == "Not specified":

                    lead_source = ""

                # ================================================
                # VALIDATION
                # ================================================

                if not company_name:

                    st.error(
                        "Company name is required."
                    )

                elif not is_valid_website(
                    website
                ):

                    st.error(
                        "Please enter a valid website URL "
                        "starting with http:// or https://."
                    )

                else:

                    # ============================================
                    # DUPLICATE CHECK
                    # ============================================

                    duplicate_query = (
                        session.query(Client)
                        .filter(
                            Client.company_name.ilike(
                                company_name
                            )
                        )
                    )

                    if editing_client:

                        duplicate_query = (
                            duplicate_query.filter(
                                Client.id
                                != editing_client.id
                            )
                        )

                    duplicate = (
                        duplicate_query.first()
                    )

                    if duplicate:

                        st.error(
                            "A client with this company name "
                            "already exists."
                        )

                    else:

                        # ========================================
                        # UPDATE EXISTING CLIENT
                        # ========================================

                        if editing_client:

                            editing_client.company_name = (
                                company_name
                            )

                            editing_client.industry = (
                                industry
                            )

                            editing_client.website = (
                                website
                            )

                            editing_client.country = (
                                country
                            )

                            editing_client.city = (
                                city
                            )

                            editing_client.address = (
                                address
                            )

                            editing_client.postcode = (
                                postcode
                            )

                            editing_client.company_size = (
                                company_size
                            )

                            editing_client.status = (
                                status
                            )

                            editing_client.lead_source = (
                                lead_source
                            )

                            editing_client.next_follow_up = (
                                next_follow_up
                            )

                            editing_client.account_owner = (
                                account_owner
                            )

                            editing_client.notes = (
                                notes
                            )

                            message = (
                                "Client updated successfully."
                            )

                        # ========================================
                        # CREATE NEW CLIENT
                        # ========================================

                        else:

                            new_client = Client(
                                company_name=(
                                    company_name
                                ),
                                industry=(
                                    industry
                                ),
                                website=(
                                    website
                                ),
                                country=(
                                    country
                                ),
                                city=(
                                    city
                                ),
                                address=(
                                    address
                                ),
                                postcode=(
                                    postcode
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
                                    account_owner
                                ),
                                notes=(
                                    notes
                                ),
                            )

                            session.add(
                                new_client
                            )

                            message = (
                                "Client added successfully."
                            )

                        # ========================================
                        # SAVE
                        # ========================================

                        try:

                            session.commit()

                            st.session_state[
                                "editing_client_id"
                            ] = None

                            st.success(
                                message
                            )

                            st.rerun()

                        except Exception as error:

                            session.rollback()

                            st.error(
                                "The client could not be saved."
                            )

                            st.exception(error)

        # ========================================================
        # CANCEL EDITING
        # ========================================================

        if editing_client:

            if st.button(
                "Cancel Editing",
                use_container_width=True,
            ):

                st.session_state[
                    "editing_client_id"
                ] = None

                st.rerun()

        st.divider()

        # ========================================================
        # CLIENT REGISTER
        # ========================================================

        st.subheader(
            "Client Register"
        )

        search_text = st.text_input(
            "Search Clients",
            placeholder=(
                "Search company, industry, "
                "city, country, website, owner or notes..."
            ),
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            status_filter = st.selectbox(
                "Status",
                ["All Statuses"]
                + CLIENT_STATUSES,
            )

        with col2:

            country_filter = st.selectbox(
                "Country",
                ["All Countries"]
                + COUNTRIES,
            )

        with col3:

            lead_source_filter = st.selectbox(
                "Lead Source",
                ["All Sources"]
                + LEAD_SOURCES,
            )

        # ========================================================
        # APPLY FILTERS
        # ========================================================

        filtered_clients = []

        search_lower = (
            search_text.strip().lower()
        )

        for client in clients:

            # ====================================================
            # SEARCH
            # ====================================================

            if search_lower:

                combined_text = " ".join(
                    [
                        client.company_name or "",
                        client.industry or "",
                        client.website or "",
                        client.country or "",
                        client.city or "",
                        client.address or "",
                        client.postcode or "",
                        client.company_size or "",
                        client.status or "",
                        client.lead_source or "",
                        client.account_owner or "",
                        client.notes or "",
                    ]
                ).lower()

                if search_lower not in combined_text:

                    continue

            # ====================================================
            # STATUS FILTER
            # ====================================================

            if (
                status_filter != "All Statuses"
                and client.status
                != status_filter
            ):

                continue

            # ====================================================
            # COUNTRY FILTER
            # ====================================================

            if (
                country_filter != "All Countries"
                and client.country
                != country_filter
            ):

                continue

            # ====================================================
            # LEAD SOURCE FILTER
            # ====================================================

            if (
                lead_source_filter
                != "All Sources"
                and client.lead_source
                != lead_source_filter
            ):

                continue

            filtered_clients.append(
                client
            )

        # ========================================================
        # REGISTER SUMMARY
        # ========================================================

        st.caption(
            f"Showing {len(filtered_clients)} "
            f"of {len(clients)} clients"
        )

        # ========================================================
        # NO RESULTS
        # ========================================================

        if not filtered_clients:

            st.info(
                "No clients match your filters."
            )

        # ========================================================
        # DISPLAY CLIENTS
        # ========================================================

        else:

            for client in filtered_clients:

                with st.container(
                    border=True
                ):

                    col1, col2, col3 = st.columns(
                        [3, 2, 1]
                    )

                    # ============================================
                    # CLIENT INFORMATION
                    # ============================================

                    with col1:

                        st.markdown(
                            f"### "
                            f"{get_client_name(client)}"
                        )

                        st.write(
                            f"**Industry:** "
                            f"{client.industry or 'Not specified'}"
                        )

                        st.write(
                            f"**Status:** "
                            f"{client.status or 'Not specified'}"
                        )

                        st.write(
                            f"**Country:** "
                            f"{client.country or 'Not specified'}"
                        )

                        if client.city:

                            st.write(
                                f"**City:** "
                                f"{client.city}"
                            )

                    # ============================================
                    # CLIENT DETAILS
                    # ============================================

                    with col2:

                        if client.website:

                            st.markdown(
                                f"[Website]"
                                f"({client.website})"
                            )

                        st.write(
                            f"**Lead Source:** "
                            f"{client.lead_source or 'Not specified'}"
                        )

                        st.write(
                            f"**Account Owner:** "
                            f"{client.account_owner or 'Not specified'}"
                        )

                        st.write(
                            f"**Contacts:** "
                            f"{get_contact_count(client)}"
                        )

                        st.write(
                            f"**Primary Contacts:** "
                            f"{get_primary_contact_count(client)}"
                        )

                        if client.next_follow_up:

                            st.write(
                                f"**Next Follow-Up:** "
                                f"{client.next_follow_up.strftime('%d %b %Y')}"
                            )

                    # ============================================
                    # ACTIONS
                    # ============================================

                    with col3:

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
                                (
                                    f"confirm_delete_client_"
                                    f"{client.id}"
                                )
                            ] = True

                            st.rerun()

                    # ============================================
                    # ADDRESS
                    # ============================================

                    if client.address:

                        address_text = (
                            client.address
                        )

                        if client.postcode:

                            address_text += (
                                f", {client.postcode}"
                            )

                        st.caption(
                            f"Address: {address_text}"
                        )

                    # ============================================
                    # NOTES
                    # ============================================

                    if client.notes:

                        st.caption(
                            f"Notes: "
                            f"{client.notes}"
                        )

                    # ============================================
                    # DELETE CONFIRMATION
                    # ============================================

                    if st.session_state.get(
                        (
                            f"confirm_delete_client_"
                            f"{client.id}"
                        ),
                        False,
                    ):

                        related_counts = (
                            get_related_record_counts(
                                client
                            )
                        )

                        if has_related_records(
                            client
                        ):

                            st.warning(
                                "This client has related "
                                "CRM records and should not "
                                "be deleted."
                            )

                            related_items = []

                            for label, count in [
                                (
                                    "Contacts",
                                    related_counts["contacts"],
                                ),
                                (
                                    "Jobs",
                                    related_counts["jobs"],
                                ),
                                (
                                    "Placements",
                                    related_counts["placements"],
                                ),
                                (
                                    "Activities",
                                    related_counts["activities"],
                                ),
                                (
                                    "Contracts",
                                    related_counts["contracts"],
                                ),
                                (
                                    "Invoices",
                                    related_counts["invoices"],
                                ),
                            ]:

                                if count > 0:

                                    related_items.append(
                                        f"{label}: {count}"
                                    )

                            st.write(
                                " | ".join(
                                    related_items
                                )
                            )

                            st.info(
                                "Instead of deleting the client, "
                                "change its status to Inactive "
                                "or Lost."
                            )

                            if st.button(
                                "Cancel",
                                key=(
                                    f"cancel_delete_client_"
                                    f"{client.id}"
                                ),
                                use_container_width=True,
                            ):

                                clear_delete_confirmation(
                                    client.id
                                )

                                st.rerun()

                        else:

                            st.warning(
                                "Are you sure you want to "
                                "delete this client?"
                            )

                            confirm_col1, confirm_col2 = (
                                st.columns(2)
                            )

                            with confirm_col1:

                                if st.button(
                                    "Yes, Delete",
                                    key=(
                                        f"confirm_yes_client_"
                                        f"{client.id}"
                                    ),
                                    use_container_width=True,
                                ):

                                    try:

                                        session.delete(
                                            client
                                        )

                                        session.commit()

                                        clear_delete_confirmation(
                                            client.id
                                        )

                                        st.success(
                                            "Client deleted "
                                            "successfully."
                                        )

                                        st.rerun()

                                    except Exception as error:

                                        session.rollback()

                                        clear_delete_confirmation(
                                            client.id
                                        )

                                        st.error(
                                            "The client could "
                                            "not be deleted."
                                        )

                                        st.exception(
                                            error
                                        )

                            with confirm_col2:

                                if st.button(
                                    "Cancel",
                                    key=(
                                        f"confirm_no_client_"
                                        f"{client.id}"
                                    ),
                                    use_container_width=True,
                                ):

                                    clear_delete_confirmation(
                                        client.id
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