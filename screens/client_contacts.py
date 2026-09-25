import streamlit as st

from database import get_session
from models import Client, ClientContact


def show_client_contacts():

    st.title("Client Contacts")
    st.caption("Manage contacts and decision-makers for each client.")

    session = get_session()

    clients = session.query(Client).order_by(
        Client.company_name
    ).all()

    if not clients:
        st.warning("Please add a client first.")
        session.close()
        return

    # ============================================================
    # ADD CONTACT
    # ============================================================

    st.subheader("Add Client Contact")

    with st.form("add_client_contact_form"):

        client_options = {
            f"{client.company_name} (ID: {client.id})": client.id
            for client in clients
        }

        selected_client = st.selectbox(
            "Client",
            list(client_options.keys())
        )

        col1, col2 = st.columns(2)

        with col1:

            first_name = st.text_input(
                "First Name"
            )

        with col2:

            last_name = st.text_input(
                "Last Name"
            )

        job_title = st.text_input(
            "Job Title",
            placeholder="Example: Finance Director"
        )

        col3, col4 = st.columns(2)

        with col3:

            email = st.text_input(
                "Email"
            )

        with col4:

            phone = st.text_input(
                "Phone"
            )

        linkedin = st.text_input(
            "LinkedIn",
            placeholder="LinkedIn profile URL"
        )

        col5, col6 = st.columns(2)

        with col5:

            preferred_contact = st.selectbox(
                "Preferred Contact",
                [
                    "Email",
                    "Phone",
                    "LinkedIn",
                    "WhatsApp",
                    "Other"
                ]
            )

        with col6:

            primary_contact = st.selectbox(
                "Primary Contact",
                [
                    "Yes",
                    "No"
                ]
            )

        status = st.selectbox(
            "Status",
            [
                "Active",
                "Inactive"
            ]
        )

        notes = st.text_area(
            "Notes"
        )

        submitted = st.form_submit_button(
            "Add Contact",
            use_container_width=True
        )

        if submitted:

            if not first_name.strip():

                st.error(
                    "First name is required."
                )

            elif not email.strip() and not phone.strip():

                st.error(
                    "Please provide an email address or phone number."
                )

            else:

                contact = ClientContact(
                    client_id=client_options[selected_client],
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                    job_title=job_title.strip(),
                    email=email.strip(),
                    phone=phone.strip(),
                    linkedin=linkedin.strip(),
                    preferred_contact=preferred_contact,
                    primary_contact=primary_contact,
                    status=status,
                    notes=notes.strip()
                )

                session.add(contact)
                session.commit()

                st.success(
                    "Client contact added successfully."
                )

                st.rerun()

    # ============================================================
    # CONTACT REGISTER
    # ============================================================

    st.divider()

    st.subheader("Contact Register")

    contacts = session.query(ClientContact).order_by(
        ClientContact.first_name
    ).all()

    if not contacts:

        st.info(
            "No client contacts have been added yet."
        )

        session.close()
        return

    # ============================================================
    # FILTERS
    # ============================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        search = st.text_input(
            "Search",
            placeholder="Name, email or company..."
        )

    with col2:

        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Active",
                "Inactive"
            ]
        )

    with col3:

        primary_filter = st.selectbox(
            "Primary Contact",
            [
                "All",
                "Yes",
                "No"
            ]
        )

    filtered_contacts = contacts

    # ============================================================
    # SEARCH
    # ============================================================

    if search:

        search_lower = search.lower()

        filtered_contacts = [
            contact
            for contact in filtered_contacts
            if (
                search_lower
                in (
                    f"{contact.first_name or ''} "
                    f"{contact.last_name or ''}"
                ).lower()

                or search_lower
                in (contact.email or "").lower()

                or (
                    contact.client
                    and search_lower
                    in (
                        contact.client.company_name or ""
                    ).lower()
                )
            )
        ]

    # ============================================================
    # STATUS FILTER
    # ============================================================

    if status_filter != "All":

        filtered_contacts = [
            contact
            for contact in filtered_contacts
            if contact.status == status_filter
        ]

    # ============================================================
    # PRIMARY FILTER
    # ============================================================

    if primary_filter != "All":

        filtered_contacts = [
            contact
            for contact in filtered_contacts
            if contact.primary_contact == primary_filter
        ]

    # ============================================================
    # DISPLAY
    # ============================================================

    if not filtered_contacts:

        st.info(
            "No contacts match your filters."
        )

    else:

        for contact in filtered_contacts:

            client_name = (
                contact.client.company_name
                if contact.client
                else "Unknown Client"
            )

            full_name = (
                f"{contact.first_name or ''} "
                f"{contact.last_name or ''}"
            ).strip()

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(
                    [2, 3, 2, 2]
                )

                with col1:

                    st.write(
                        f"**{full_name}**"
                    )

                    if contact.job_title:

                        st.caption(
                            contact.job_title
                        )

                with col2:

                    st.write(
                        f"**{client_name}**"
                    )

                    if contact.email:

                        st.caption(
                            contact.email
                        )

                with col3:

                    if contact.phone:

                        st.write(
                            contact.phone
                        )

                    if contact.preferred_contact:

                        st.caption(
                            f"Preferred: "
                            f"{contact.preferred_contact}"
                        )

                with col4:

                    st.write(
                        f"Status: **{contact.status}**"
                    )

                    st.write(
                        f"Primary: **"
                        f"{contact.primary_contact}"
                        f"**"
                    )

                if contact.linkedin:

                    st.link_button(
                        "LinkedIn",
                        contact.linkedin
                    )

                if contact.notes:

                    st.caption(
                        f"Notes: {contact.notes}"
                    )

    session.close()