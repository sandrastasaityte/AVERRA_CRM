import streamlit as st
from datetime import date

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

PIPELINE_STATUSES = [
    "Lead",
    "Contacted",
    "Replied",
    "Call",
    "Proposal",
    "Negotiation",
    "Contract",
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


def normalize_text(value):
    """Normalize text for comparisons."""

    return " ".join(
        (value or "").strip().lower().split()
    )


def normalize_website(website):
    """
    Normalize a website URL.

    Examples:

        example.com
        -> https://example.com

        www.example.com
        -> https://www.example.com

        https://example.com
        -> https://example.com
    """

    website = (
        website or ""
    ).strip()

    if not website:
        return ""

    website_lower = website.lower()

    if (
        website_lower.startswith("http://")
        or website_lower.startswith("https://")
    ):
        return website

    if website_lower.startswith("www."):
        return f"https://{website}"

    return f"https://{website}"


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
        return len(client.contacts)
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
    """
    Return counts of records linked to a client.

    These relationships are used to prevent accidental
    deletion of clients that already have CRM history.
    """

    counts = {
        "contacts": 0,
        "jobs": 0,
        "placements": 0,
        "activities": 0,
        "contracts": 0,
        "invoices": 0,
    }

    try:
        counts["contacts"] = len(
            client.contacts
        )
    except Exception:
        pass

    try:
        counts["jobs"] = len(
            client.jobs
        )
    except Exception:
        pass

    try:
        counts["placements"] = len(
            client.placements
        )
    except Exception:
        pass

    try:
        counts["activities"] = len(
            client.activities
        )
    except Exception:
        pass

    try:
        counts["contracts"] = len(
            client.contracts
        )
    except Exception:
        pass

    try:
        counts["invoices"] = len(
            client.invoices
        )
    except Exception:
        pass

    return counts


def has_related_records(client):
    """Return True if the client has any linked CRM records."""

    counts = get_related_record_counts(
        client
    )

    return any(
        count > 0
        for count in counts.values()
    )


def get_follow_up_state(client):
    """
    Return the follow-up state.

    Possible values:

        None
        Overdue
        Today
        Upcoming
    """

    follow_up = client.next_follow_up

    if not follow_up:
        return None

    today = date.today()

    if follow_up < today:
        return "Overdue"

    if follow_up == today:
        return "Today"

    return "Upcoming"


def get_follow_up_label(client):
    """Return a human-readable follow-up label."""

    follow_up = client.next_follow_up

    if not follow_up:
        return "No follow-up scheduled"

    state = get_follow_up_state(
        client
    )

    formatted_date = follow_up.strftime(
        "%d %b %Y"
    )

    if state == "Overdue":
        return f"Overdue — {formatted_date}"

    if state == "Today":
        return f"Today — {formatted_date}"

    return f"{formatted_date}"


def clear_delete_confirmation(client_id):
    """Clear delete confirmation state."""

    st.session_state[
        f"confirm_delete_client_{client_id}"
    ] = False


def clear_edit_state():
    """Clear the current client being edited."""

    st.session_state[
        "editing_client_id"
    ] = None


def get_status_display(client):
    """Return a safe client status."""

    return (
        client.status
        or "Not specified"
    )


def get_account_owner_display(client):
    """Return a safe account owner value."""

    return (
        client.account_owner
        or "Not specified"
    )


def get_related_records_summary(client):
    """
    Build a readable related-record summary.
    """

    related_counts = (
        get_related_record_counts(
            client
        )
    )

    related_parts = []

    for label, key in [
        ("Contacts", "contacts"),
        ("Jobs", "jobs"),
        ("Placements", "placements"),
        ("Activities", "activities"),
        ("Contracts", "contracts"),
        ("Invoices", "invoices"),
    ]:

        count = related_counts[key]

        if count > 0:

            related_parts.append(
                f"{label}: {count}"
            )

    return related_parts


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

            st.session_state[
                "editing_client_id"
            ] = None

        # ========================================================
        # VALIDATE EDITING STATE
        # ========================================================

        editing_client_id = (
            st.session_state.get(
                "editing_client_id"
            )
        )

        editing_client = None

        if editing_client_id:

            editing_client = session.get(
                Client,
                editing_client_id,
            )

            if not editing_client:

                clear_edit_state()

                editing_client_id = None

        # ========================================================
        # OVERVIEW
        # ========================================================

        st.subheader("Overview")

        total_clients = len(
            clients
        )

        active_clients = sum(
            1
            for client in clients
            if client.status == "Active"
        )

        pipeline_clients = sum(
            1
            for client in clients
            if client.status
            in PIPELINE_STATUSES
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

        overdue_followups = sum(
            1
            for client in clients
            if get_follow_up_state(client)
            == "Overdue"
        )

        today_followups = sum(
            1
            for client in clients
            if get_follow_up_state(client)
            == "Today"
        )

        upcoming_followups = sum(
            1
            for client in clients
            if get_follow_up_state(client)
            == "Upcoming"
        )

        clients_without_followup = sum(
            1
            for client in clients
            if not client.next_follow_up
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

        # ========================================================
        # SALES / FOLLOW-UP SUMMARY
        # ========================================================

        st.divider()

        summary_col1, summary_col2, summary_col3, summary_col4 = (
            st.columns(4)
        )

        with summary_col1:

            st.metric(
                "Overdue",
                overdue_followups,
            )

        with summary_col2:

            st.metric(
                "Today",
                today_followups,
            )

        with summary_col3:

            st.metric(
                "Upcoming",
                upcoming_followups,
            )

        with summary_col4:

            st.metric(
                "No Follow-Up",
                clients_without_followup,
            )

        if lost_clients > 0:

            st.caption(
                f"Lost clients: {lost_clients}"
            )

        st.divider()

        # ========================================================
        # ADD / EDIT CLIENT
        # ========================================================

        if editing_client:

            st.subheader(
                f"Edit Client — "
                f"{get_client_name(editing_client)}"
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
                        "e.g. Accounting, Architecture, Technology"
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
                        COMPANY_SIZES.index(
                            default_company_size
                        ) + 1
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
                        LEAD_SOURCES.index(
                            default_lead_source
                        ) + 1
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

                has_follow_up = st.checkbox(
                    "Schedule Follow-Up",
                    value=(
                        default_next_follow_up
                        is not None
                    ),
                )

                if has_follow_up:

                    if default_next_follow_up:

                        next_follow_up = st.date_input(
                            "Next Follow-Up",
                            value=default_next_follow_up,
                        )

                    else:

                        next_follow_up = st.date_input(
                            "Next Follow-Up",
                            value=date.today(),
                        )

                else:

                    next_follow_up = None

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
                height=120,
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

                website = normalize_website(
                    website
                )

                city = (
                    city.strip()
                )

                address = (
                    address.strip()
                )

                postcode = (
                    postcode.strip()
                    .upper()
                )

                account_owner = (
                    account_owner.strip()
                )

                notes = (
                    notes.strip()
                )

                # ================================================
                # PLACEHOLDER VALUES
                # ================================================

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

                elif len(company_name) > 255:

                    st.error(
                        "Company name is too long."
                    )

                elif not is_valid_website(
                    website
                ):

                    st.error(
                        "Please enter a valid website URL."
                    )

                elif (
                    next_follow_up
                    and next_follow_up < date.today()
                    and status
                    in ["Lead", "Contacted", "Replied", "Call",
                        "Proposal", "Negotiation", "Contract"]
                ):

                    st.warning(
                        "The selected follow-up date is in the past. "
                        "This client will appear as Overdue."
                    )

                    # Continue saving intentionally.

                    normalized_company_name = (
                        normalize_text(
                            company_name
                        )
                    )

                    duplicate = None

                    for existing_client in clients:

                        if (
                            editing_client
                            and existing_client.id
                            == editing_client.id
                        ):
                            continue

                        existing_name = (
                            normalize_text(
                                existing_client.company_name
                            )
                        )

                        if (
                            existing_name
                            == normalized_company_name
                        ):

                            duplicate = (
                                existing_client
                            )

                            break

                    if duplicate:

                        st.error(
                            "A client with this company name "
                            "already exists."
                        )

                    else:

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

                        else:

                            new_client = Client(
                                company_name=company_name,
                                industry=industry,
                                website=website,
                                country=country,
                                city=city,
                                address=address,
                                postcode=postcode,
                                company_size=company_size,
                                status=status,
                                lead_source=lead_source,
                                next_follow_up=next_follow_up,
                                account_owner=account_owner,
                                notes=notes,
                            )

                            session.add(
                                new_client
                            )

                            message = (
                                "Client added successfully."
                            )

                        try:

                            session.commit()

                            clear_edit_state()

                            st.success(
                                message
                            )

                            st.rerun()

                        except Exception as error:

                            session.rollback()

                            st.error(
                                "The client could not be saved."
                            )

                            st.exception(
                                error
                            )

                else:

                    # ============================================
                    # DUPLICATE COMPANY CHECK
                    # ============================================

                    normalized_company_name = (
                        normalize_text(
                            company_name
                        )
                    )

                    duplicate = None

                    for existing_client in clients:

                        if (
                            editing_client
                            and existing_client.id
                            == editing_client.id
                        ):
                            continue

                        existing_name = (
                            normalize_text(
                                existing_client.company_name
                            )
                        )

                        if (
                            existing_name
                            == normalized_company_name
                        ):

                            duplicate = (
                                existing_client
                            )

                            break

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
                                company_name=company_name,
                                industry=industry,
                                website=website,
                                country=country,
                                city=city,
                                address=address,
                                postcode=postcode,
                                company_size=company_size,
                                status=status,
                                lead_source=lead_source,
                                next_follow_up=next_follow_up,
                                account_owner=account_owner,
                                notes=notes,
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

                            clear_edit_state()

                            st.success(
                                message
                            )

                            st.rerun()

                        except Exception as error:

                            session.rollback()

                            st.error(
                                "The client could not be saved."
                            )

                            st.exception(
                                error
                            )

        # ========================================================
        # CANCEL EDITING
        # ========================================================

        if editing_client:

            if st.button(
                "Cancel Editing",
                use_container_width=True,
            ):

                clear_edit_state()

                st.rerun()

        st.divider()

        # ========================================================
        # CLIENT REGISTER
        # ========================================================

        st.subheader(
            "Client Register"
        )

        # ========================================================
        # SEARCH
        # ========================================================

        search_text = st.text_input(
            "Search Clients",
            placeholder=(
                "Search company, industry, city, "
                "country, website, owner or notes..."
            ),
        )

        # ========================================================
        # FILTERS
        # ========================================================

        col1, col2, col3, col4 = st.columns(4)

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

        with col4:

            follow_up_filter = st.selectbox(
                "Follow-Up",
                [
                    "All",
                    "Overdue",
                    "Today",
                    "Upcoming",
                    "No Follow-Up",
                ],
            )

        col5, col6, col7 = st.columns(3)

        with col5:

            company_size_filter = st.selectbox(
                "Company Size",
                ["All Sizes"]
                + COMPANY_SIZES,
            )

        with col6:

            account_owners = sorted(
                {
                    client.account_owner.strip()
                    for client in clients
                    if client.account_owner
                    and client.account_owner.strip()
                }
            )

            account_owner_filter = st.selectbox(
                "Account Owner",
                ["All Owners"]
                + account_owners,
            )

        with col7:

            sort_order = st.selectbox(
                "Sort",
                [
                    "Company Name",
                    "Follow-Up Priority",
                    "Newest First",
                    "Status",
                ],
            )

        # ========================================================
        # RESET FILTERS
        # ========================================================

        if st.button(
            "Reset Filters",
            use_container_width=True,
        ):

            st.rerun()

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
            # STATUS
            # ====================================================

            if (
                status_filter != "All Statuses"
                and client.status
                != status_filter
            ):

                continue

            # ====================================================
            # COUNTRY
            # ====================================================

            if (
                country_filter != "All Countries"
                and client.country
                != country_filter
            ):

                continue

            # ====================================================
            # LEAD SOURCE
            # ====================================================

            if (
                lead_source_filter != "All Sources"
                and client.lead_source
                != lead_source_filter
            ):

                continue

            # ====================================================
            # COMPANY SIZE
            # ====================================================

            if (
                company_size_filter
                != "All Sizes"
                and client.company_size
                != company_size_filter
            ):

                continue

            # ====================================================
            # ACCOUNT OWNER
            # ====================================================

            if (
                account_owner_filter
                != "All Owners"
                and (
                    client.account_owner
                    or ""
                ).strip()
                != account_owner_filter
            ):

                continue

            # ====================================================
            # FOLLOW-UP
            # ====================================================

            follow_up_state = (
                get_follow_up_state(
                    client
                )
            )

            if (
                follow_up_filter != "All"
                and follow_up_filter
                != "No Follow-Up"
                and follow_up_state
                != follow_up_filter
            ):

                continue

            if (
                follow_up_filter
                == "No Follow-Up"
                and client.next_follow_up
            ):

                continue

            filtered_clients.append(
                client
            )

        # ========================================================
        # SORT RESULTS
        # ========================================================

        if sort_order == "Company Name":

            filtered_clients.sort(
                key=lambda client:
                get_client_name(client).lower()
            )

        elif sort_order == "Newest First":

            filtered_clients.sort(
                key=lambda client:
                client.id or 0,
                reverse=True,
            )

        elif sort_order == "Status":

            filtered_clients.sort(
                key=lambda client:
                (
                    client.status or ""
                ).lower()
            )

        elif sort_order == "Follow-Up Priority":

            def follow_up_sort_key(client):

                state = (
                    get_follow_up_state(
                        client
                    )
                )

                priority = {
                    "Overdue": 0,
                    "Today": 1,
                    "Upcoming": 2,
                    None: 3,
                }

                follow_up_date = (
                    client.next_follow_up
                    or date.max
                )

                return (
                    priority.get(
                        state,
                        3,
                    ),
                    follow_up_date,
                    get_client_name(
                        client
                    ).lower(),
                )

            filtered_clients.sort(
                key=follow_up_sort_key
            )

        # ========================================================
        # REGISTER SUMMARY
        # ========================================================

        st.caption(
            f"Showing "
            f"{len(filtered_clients)} "
            f"of "
            f"{len(clients)} "
            f"clients"
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

                    col1, col2, col3 = (
                        st.columns(
                            [3, 2, 1]
                        )
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
                            f"{get_status_display(client)}"
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

                        if client.company_size:

                            st.write(
                                f"**Company Size:** "
                                f"{client.company_size}"
                            )

                    # ============================================
                    # CLIENT DETAILS
                    # ============================================

                    with col2:

                        if client.website:

                            st.markdown(
                                f"[Website]({client.website})"
                            )

                        st.write(
                            f"**Lead Source:** "
                            f"{client.lead_source or 'Not specified'}"
                        )

                        st.write(
                            f"**Account Owner:** "
                            f"{get_account_owner_display(client)}"
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

                            follow_up_state = (
                                get_follow_up_state(
                                    client
                                )
                            )

                            if (
                                follow_up_state
                                == "Overdue"
                            ):

                                st.error(
                                    f"**Follow-Up:** "
                                    f"{get_follow_up_label(client)}"
                                )

                            elif (
                                follow_up_state
                                == "Today"
                            ):

                                st.warning(
                                    f"**Follow-Up:** "
                                    f"{get_follow_up_label(client)}"
                                )

                            else:

                                st.write(
                                    f"**Next Follow-Up:** "
                                    f"{get_follow_up_label(client)}"
                                )

                        else:

                            st.caption(
                                "No follow-up scheduled"
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
                    # RELATED RECORDS
                    # ============================================

                    related_parts = (
                        get_related_records_summary(
                            client
                        )
                    )

                    if related_parts:

                        st.caption(
                            "Related records: "
                            + " | ".join(
                                related_parts
                            )
                        )

                    else:

                        st.caption(
                            "Related records: None"
                        )

                    # ============================================
                    # ADDRESS
                    # ============================================

                    if client.address:

                        address_text = (
                            client.address
                        )

                        if client.postcode:

                            address_text += (
                                f", "
                                f"{client.postcode}"
                            )

                        st.caption(
                            f"Address: "
                            f"{address_text}"
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

                        # ========================================
                        # PROTECTED CLIENT
                        # ========================================

                        if has_related_records(
                            client
                        ):

                            st.warning(
                                "This client has related "
                                "CRM records and should not "
                                "be deleted."
                            )

                            related_items = []

                            for label, key in [
                                ("Contacts", "contacts"),
                                ("Jobs", "jobs"),
                                ("Placements", "placements"),
                                ("Activities", "activities"),
                                ("Contracts", "contracts"),
                                ("Invoices", "invoices"),
                            ]:

                                count = (
                                    related_counts[
                                        key
                                    ]
                                )

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
                                "For CRM history protection, "
                                "keep this client and change "
                                "its status to Inactive or Lost "
                                "instead of deleting it."
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

                        # ========================================
                        # CLIENT WITHOUT HISTORY
                        # ========================================

                        else:

                            st.warning(
                                "This client has no linked "
                                "CRM records. Are you sure "
                                "you want to permanently delete it?"
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

        st.exception(
            error
        )

    finally:

        session.close()