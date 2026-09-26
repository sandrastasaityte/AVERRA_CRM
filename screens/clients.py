import streamlit as st

from database import get_session
from models import Client


def show_clients():

    st.title("Clients")
    st.subheader("AVERRA Client Management")

    session = get_session()

    # ============================================================
    # ADD NEW CLIENT
    # ============================================================

    st.header("Add New Client")

    with st.form("add_client_form"):

        col1, col2 = st.columns(2)

        with col1:
            company_name = st.text_input("Company Name *")
            industry = st.text_input("Industry")
            website = st.text_input("Website")
            country = st.text_input("Country", value="UK")
            city = st.text_input("City")

        with col2:
            address = st.text_input("Address")
            postcode = st.text_input("Postcode")

            company_size = st.selectbox(
                "Company Size",
                [
                    "",
                    "1-10",
                    "11-50",
                    "51-200",
                    "201-500",
                    "501-1,000",
                    "1,001-5,000",
                    "5,001-10,000",
                    "10,000+"
                ]
            )

            status = st.selectbox(
                "Status",
                [
                    "Lead",
                    "Contacted",
                    "Replied",
                    "Call",
                    "Proposal",
                    "Negotiation",
                    "Contract",
                    "Won",
                    "Lost"
                ]
            )

            lead_source = st.selectbox(
                "Lead Source",
                [
                    "",
                    "LinkedIn",
                    "Website",
                    "Referral",
                    "Email",
                    "Cold Call",
                    "Networking",
                    "Job Board",
                    "Other"
                ]
            )

        account_owner = st.text_input("Account Owner")

        notes = st.text_area("Notes")

        submitted = st.form_submit_button(
            "Add Client",
            use_container_width=True
        )

        if submitted:

            if not company_name.strip():
                st.error("Company Name is required.")

            else:

                existing_client = (
                    session.query(Client)
                    .filter(
                        Client.company_name.ilike(
                            company_name.strip()
                        )
                    )
                    .first()
                )

                if existing_client:

                    st.error(
                        "A client with this company name already exists."
                    )

                else:

                    new_client = Client(
                        company_name=company_name.strip(),
                        industry=industry.strip(),
                        website=website.strip(),
                        country=country.strip(),
                        city=city.strip(),
                        address=address.strip(),
                        postcode=postcode.strip(),
                        company_size=company_size,
                        status=status,
                        lead_source=lead_source,
                        account_owner=account_owner.strip(),
                        notes=notes.strip()
                    )

                    session.add(new_client)
                    session.commit()

                    st.success(
                        f"{company_name.strip()} added successfully."
                    )

                    st.rerun()

    # ============================================================
    # CLIENT LIST
    # ============================================================

    st.divider()

    st.header("Client Register")

    clients = (
        session.query(Client)
        .order_by(Client.company_name.asc())
        .all()
    )

    if not clients:

        st.info("No clients have been added yet.")

        session.close()
        return

    # ============================================================
    # FILTERS
    # ============================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        search = st.text_input(
            "Search Clients",
            placeholder="Company, industry or city..."
        )

    with col2:

        status_filter = st.selectbox(
            "Filter by Status",
            [
                "All",
                "Lead",
                "Contacted",
                "Replied",
                "Call",
                "Proposal",
                "Negotiation",
                "Contract",
                "Won",
                "Lost"
            ]
        )

    with col3:

        industries = sorted(
            {
                client.industry
                for client in clients
                if client.industry
            }
        )

        industry_filter = st.selectbox(
            "Filter by Industry",
            ["All"] + industries
        )

    # ============================================================
    # APPLY FILTERS
    # ============================================================

    filtered_clients = clients

    if search:

        search_text = search.lower()

        filtered_clients = [
            client
            for client in filtered_clients
            if (
                search_text
                in (client.company_name or "").lower()
                or search_text
                in (client.industry or "").lower()
                or search_text
                in (client.city or "").lower()
            )
        ]

    if status_filter != "All":

        filtered_clients = [
            client
            for client in filtered_clients
            if client.status == status_filter
        ]

    if industry_filter != "All":

        filtered_clients = [
            client
            for client in filtered_clients
            if client.industry == industry_filter
        ]

    st.write(
        f"Showing **{len(filtered_clients)}** client(s)"
    )

    # ============================================================
    # DISPLAY CLIENTS
    # ============================================================

    for client in filtered_clients:

        with st.container(border=True):

            col1, col2, col3, col4 = st.columns(
                [3, 2, 3, 1]
            )

            # ----------------------------------------------------
            # COMPANY
            # ----------------------------------------------------

            with col1:

                st.subheader(
                    client.company_name
                )

                if client.industry:

                    st.write(
                        client.industry
                    )

                location = ", ".join(
                    part
                    for part in [
                        client.city,
                        client.country
                    ]
                    if part
                )

                if location:

                    st.caption(location)

            # ----------------------------------------------------
            # STATUS
            # ----------------------------------------------------

            with col2:

                st.write("**Status**")

                st.write(
                    client.status or "—"
                )

                if client.lead_source:

                    st.caption(
                        f"Source: {client.lead_source}"
                    )

            # ----------------------------------------------------
            # DETAILS
            # ----------------------------------------------------

            with col3:

                st.write("**Details**")

                if client.website:

                    st.write(
                        client.website
                    )

                if client.company_size:

                    st.caption(
                        f"Size: {client.company_size}"
                    )

                if client.account_owner:

                    st.caption(
                        f"Owner: {client.account_owner}"
                    )

            # ----------------------------------------------------
            # ACTION
            # ----------------------------------------------------

            with col4:

                if st.button(
                    "Edit",
                    key=f"edit_{client.id}"
                ):

                    st.session_state[
                        "editing_client_id"
                    ] = client.id

                    st.rerun()

            if client.notes:

                st.caption(
                    f"Notes: {client.notes}"
                )

    # ============================================================
    # EDIT CLIENT
    # ============================================================

    editing_id = st.session_state.get(
        "editing_client_id"
    )

    if editing_id:

        client = session.get(
            Client,
            editing_id
        )

        if client:

            st.divider()

            st.header(
                f"Edit Client: {client.company_name}"
            )

            with st.form(
                f"edit_client_{client.id}"
            ):

                col1, col2 = st.columns(2)

                with col1:

                    edit_company_name = st.text_input(
                        "Company Name",
                        value=client.company_name or ""
                    )

                    edit_industry = st.text_input(
                        "Industry",
                        value=client.industry or ""
                    )

                    edit_website = st.text_input(
                        "Website",
                        value=client.website or ""
                    )

                    edit_country = st.text_input(
                        "Country",
                        value=client.country or ""
                    )

                    edit_city = st.text_input(
                        "City",
                        value=client.city or ""
                    )

                with col2:

                    edit_address = st.text_input(
                        "Address",
                        value=client.address or ""
                    )

                    edit_postcode = st.text_input(
                        "Postcode",
                        value=client.postcode or ""
                    )

                    sizes = [
                        "",
                        "1-10",
                        "11-50",
                        "51-200",
                        "201-500",
                        "501-1,000",
                        "1,001-5,000",
                        "5,001-10,000",
                        "10,000+"
                    ]

                    current_size = (
                        client.company_size
                        if client.company_size in sizes
                        else ""
                    )

                    edit_company_size = st.selectbox(
                        "Company Size",
                        sizes,
                        index=sizes.index(current_size)
                    )

                    statuses = [
                        "Lead",
                        "Contacted",
                        "Replied",
                        "Call",
                        "Proposal",
                        "Negotiation",
                        "Contract",
                        "Won",
                        "Lost"
                    ]

                    current_status = (
                        client.status
                        if client.status in statuses
                        else "Lead"
                    )

                    edit_status = st.selectbox(
                        "Status",
                        statuses,
                        index=statuses.index(current_status)
                    )

                    sources = [
                        "",
                        "LinkedIn",
                        "Website",
                        "Referral",
                        "Email",
                        "Cold Call",
                        "Networking",
                        "Job Board",
                        "Other"
                    ]

                    current_source = (
                        client.lead_source
                        if client.lead_source in sources
                        else ""
                    )

                    edit_lead_source = st.selectbox(
                        "Lead Source",
                        sources,
                        index=sources.index(current_source)
                    )

                edit_account_owner = st.text_input(
                    "Account Owner",
                    value=client.account_owner or ""
                )

                edit_notes = st.text_area(
                    "Notes",
                    value=client.notes or ""
                )

                save = st.form_submit_button(
                    "Save Changes",
                    use_container_width=True
                )

                if save:

                    if not edit_company_name.strip():

                        st.error(
                            "Company Name is required."
                        )

                    else:

                        client.company_name = (
                            edit_company_name.strip()
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

                        client.notes = (
                            edit_notes.strip()
                        )

                        session.commit()

                        st.session_state.pop(
                            "editing_client_id",
                            None
                        )

                        st.success(
                            "Client updated successfully."
                        )

                        st.rerun()

            if st.button(
                "Cancel",
                key=f"cancel_edit_{client.id}"
            ):

                st.session_state.pop(
                    "editing_client_id",
                    None
                )

                st.rerun()

    session.close()