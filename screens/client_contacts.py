import streamlit as st

from database import get_session
from models import Client, ClientContact


def show_client_contacts():

    st.title("Client Contacts")
    st.caption("Manage contacts for AVERRA clients.")

    session = get_session()

    # ============================================================
    # ADD CONTACT
    # ============================================================

    st.header("Add Contact")

    clients = (
        session.query(Client)
        .order_by(Client.company_name.asc())
        .all()
    )

    if not clients:

        st.info(
            "Please add a client first before adding a contact."
        )

        session.close()
        return

    client_options = {
        client.company_name: client.id
        for client in clients
    }

    with st.form("add_contact_form"):

        selected_company = st.selectbox(
            "Client *",
            list(client_options.keys())
        )

        col1, col2 = st.columns(2)

        with col1:

            first_name = st.text_input(
                "First Name *"
            )

            last_name = st.text_input(
                "Last Name"
            )

            job_title = st.text_input(
                "Job Title"
            )

            email = st.text_input(
                "Email"
            )

        with col2:

            phone = st.text_input(
                "Phone"
            )

            linkedin = st.text_input(
                "LinkedIn"
            )

            preferred_contact = st.selectbox(
                "Preferred Contact",
                [
                    "",
                    "Email",
                    "Phone",
                    "LinkedIn"
                ]
            )

            primary_contact = st.checkbox(
                "Primary Contact"
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
                    "First Name is required."
                )

            else:

                client_id = client_options[
                    selected_company
                ]

                contact = ClientContact(
                    client_id=client_id,
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
                    "Contact added successfully."
                )

                st.rerun()

    # ============================================================
    # CONTACT REGISTER
    # ============================================================

    st.divider()

    st.header("Contact Register")

    contacts = (
        session.query(ClientContact)
        .join(Client)
        .order_by(
            Client.company_name.asc(),
            ClientContact.first_name.asc()
        )
        .all()
    )

    if not contacts:

        st.info(
            "No client contacts have been added yet."
        )

        session.close()
        return

    # ============================================================
    # SEARCH
    # ============================================================

    search = st.text_input(
        "Search Contacts",
        placeholder="Name, company, email or job title..."
    )

    filtered_contacts = contacts

    if search:

        search_text = search.lower()

        filtered_contacts = [
            contact
            for contact in contacts
            if (
                search_text
                in (
                    f"{contact.first_name or ''} "
                    f"{contact.last_name or ''}"
                ).lower()
                or search_text
                in (
                    contact.client.company_name
                    if contact.client
                    else ""
                ).lower()
                or search_text
                in (contact.email or "").lower()
                or search_text
                in (contact.job_title or "").lower()
            )
        ]

    st.write(
        f"Showing **{len(filtered_contacts)}** contact(s)"
    )

    # ============================================================
    # DISPLAY CONTACTS
    # ============================================================

    for contact in filtered_contacts:

        with st.container(border=True):

            col1, col2, col3, col4 = st.columns(
                [3, 3, 3, 1]
            )

            # ----------------------------------------------------
            # CONTACT
            # ----------------------------------------------------

            with col1:

                full_name = " ".join(
                    part
                    for part in [
                        contact.first_name,
                        contact.last_name
                    ]
                    if part
                )

                st.subheader(
                    full_name or "Unnamed Contact"
                )

                if contact.job_title:

                    st.write(
                        contact.job_title
                    )

                if contact.primary_contact:

                    st.caption(
                        "⭐ Primary Contact"
                    )

            # ----------------------------------------------------
            # COMPANY
            # ----------------------------------------------------

            with col2:

                st.write("**Company**")

                if contact.client:

                    st.write(
                        contact.client.company_name
                    )

                else:

                    st.write("—")

                st.caption(
                    contact.status or "—"
                )

            # ----------------------------------------------------
            # CONTACT DETAILS
            # ----------------------------------------------------

            with col3:

                st.write("**Contact Details**")

                if contact.email:

                    st.write(
                        contact.email
                    )

                if contact.phone:

                    st.write(
                        contact.phone
                    )

                if contact.preferred_contact:

                    st.caption(
                        f"Preferred: "
                        f"{contact.preferred_contact}"
                    )

            # ----------------------------------------------------
            # EDIT
            # ----------------------------------------------------

            with col4:

                if st.button(
                    "Edit",
                    key=f"edit_contact_{contact.id}"
                ):

                    st.session_state[
                        "editing_contact_id"
                    ] = contact.id

                    st.rerun()

            if contact.linkedin:

                st.caption(
                    f"LinkedIn: {contact.linkedin}"
                )

            if contact.notes:

                st.caption(
                    f"Notes: {contact.notes}"
                )

    # ============================================================
    # EDIT CONTACT
    # ============================================================

    editing_id = st.session_state.get(
        "editing_contact_id"
    )

    if editing_id:

        contact = session.get(
            ClientContact,
            editing_id
        )

        if contact:

            st.divider()

            st.header(
                "Edit Client Contact"
            )

            edit_client_options = {
                client.company_name: client.id
                for client in clients
            }

            current_company = (
                contact.client.company_name
                if contact.client
                else None
            )

            company_names = list(
                edit_client_options.keys()
            )

            if current_company in company_names:

                company_index = company_names.index(
                    current_company
                )

            else:

                company_index = 0

            with st.form(
                f"edit_contact_form_{contact.id}"
            ):

                edit_company = st.selectbox(
                    "Client",
                    company_names,
                    index=company_index
                )

                col1, col2 = st.columns(2)

                with col1:

                    edit_first_name = st.text_input(
                        "First Name",
                        value=contact.first_name or ""
                    )

                    edit_last_name = st.text_input(
                        "Last Name",
                        value=contact.last_name or ""
                    )

                    edit_job_title = st.text_input(
                        "Job Title",
                        value=contact.job_title or ""
                    )

                    edit_email = st.text_input(
                        "Email",
                        value=contact.email or ""
                    )

                with col2:

                    edit_phone = st.text_input(
                        "Phone",
                        value=contact.phone or ""
                    )

                    edit_linkedin = st.text_input(
                        "LinkedIn",
                        value=contact.linkedin or ""
                    )

                    contact_methods = [
                        "",
                        "Email",
                        "Phone",
                        "LinkedIn"
                    ]

                    current_method = (
                        contact.preferred_contact
                        if contact.preferred_contact
                        in contact_methods
                        else ""
                    )

                    edit_preferred = st.selectbox(
                        "Preferred Contact",
                        contact_methods,
                        index=contact_methods.index(
                            current_method
                        )
                    )

                    statuses = [
                        "Active",
                        "Inactive"
                    ]

                    current_status = (
                        contact.status
                        if contact.status in statuses
                        else "Active"
                    )

                    edit_status = st.selectbox(
                        "Status",
                        statuses,
                        index=statuses.index(
                            current_status
                        )
                    )

                edit_primary = st.checkbox(
                    "Primary Contact",
                    value=bool(
                        contact.primary_contact
                    )
                )

                edit_notes = st.text_area(
                    "Notes",
                    value=contact.notes or ""
                )

                save = st.form_submit_button(
                    "Save Changes",
                    use_container_width=True
                )

                if save:

                    if not edit_first_name.strip():

                        st.error(
                            "First Name is required."
                        )

                    else:

                        contact.client_id = (
                            edit_client_options[
                                edit_company
                            ]
                        )

                        contact.first_name = (
                            edit_first_name.strip()
                        )

                        contact.last_name = (
                            edit_last_name.strip()
                        )

                        contact.job_title = (
                            edit_job_title.strip()
                        )

                        contact.email = (
                            edit_email.strip()
                        )

                        contact.phone = (
                            edit_phone.strip()
                        )

                        contact.linkedin = (
                            edit_linkedin.strip()
                        )

                        contact.preferred_contact = (
                            edit_preferred
                        )

                        contact.primary_contact = (
                            edit_primary
                        )

                        contact.status = (
                            edit_status
                        )

                        contact.notes = (
                            edit_notes.strip()
                        )

                        session.commit()

                        st.session_state.pop(
                            "editing_contact_id",
                            None
                        )

                        st.success(
                            "Contact updated successfully."
                        )

                        st.rerun()

            if st.button(
                "Cancel",
                key=f"cancel_contact_edit_{contact.id}"
            ):

                st.session_state.pop(
                    "editing_contact_id",
                    None
                )

                st.rerun()

    session.close()