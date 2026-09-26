```python
import streamlit as st

from database import get_session
from models import Client, ClientContact


CONTACT_METHODS = [
    "Email",
    "Phone",
    "LinkedIn",
    "WhatsApp",
    "Other"
]

CONTACT_STATUSES = [
    "Active",
    "Inactive"
]


def show_client_contacts():

    st.title("Client Contacts")
    st.caption("Manage contacts and decision-makers for each client.")

    session = get_session()

    # ============================================================
    # LOAD CLIENTS
    # ============================================================

    clients = (
        session.query(Client)
        .order_by(Client.company_name)
        .all()
    )

    if not clients:

        st.warning("Please add a client first.")

        session.close()
        return

    # ============================================================
    # ADD CONTACT
    # ============================================================

    st.subheader("Add Client Contact")

    client_options = {
        f"{client.company_name}": client.id
        for client in clients
    }

    with st.form("add_client_contact_form"):

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

        col1, col2 = st.columns(2)

        with col1:

            job_title = st.text_input(
                "Job Title",
                placeholder="Example: Finance Director"
            )

        with col2:

            email = st.text_input(
                "Email"
            )

        col1, col2 = st.columns(2)

        with col1:

            phone = st.text_input(
                "Phone"
            )

        with col2:

            linkedin = st.text_input(
                "LinkedIn",
                placeholder="LinkedIn profile URL"
            )

        col1, col2 = st.columns(2)

        with col1:

            preferred_contact = st.selectbox(
                "Preferred Contact",
                CONTACT_METHODS
            )

        with col2:

            primary_contact = st.selectbox(
                "Primary Contact",
                ["Yes", "No"]
            )

        status = st.selectbox(
            "Status",
            CONTACT_STATUSES
        )

        notes = st.text_area(
            "Notes",
            placeholder="Additional information about this contact..."
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

    st.divider()

    # ============================================================
    # CONTACT REGISTER
    # ============================================================

    st.subheader("Contact Register")

    contacts = (
        session.query(ClientContact)
        .order_by(
            ClientContact.first_name,
            ClientContact.last_name
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
    # FILTERS
    # ============================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        search = st.text_input(
            "Search",
            placeholder="Name, email, phone or company..."
        )

    with col2:

        status_filter = st.selectbox(
            "Status",
            ["All"] + CONTACT_STATUSES
        )

    with col3:

        primary_filter = st.selectbox(
            "Primary Contact",
            ["All", "Yes", "No"]
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

            if search_lower in (
                f"{contact.first_name or ''} "
                f"{contact.last_name or ''}"
            ).lower()

            or search_lower in (
                contact.email or ""
            ).lower()

            or search_lower in (
                contact.phone or ""
            ).lower()

            or (
                contact.client
                and search_lower in (
                    contact.client.company_name or ""
                ).lower()
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
    # PRIMARY CONTACT FILTER
    # ============================================================

    if primary_filter != "All":

        filtered_contacts = [

            contact

            for contact in filtered_contacts

            if contact.primary_contact == primary_filter
        ]

    st.write(
        f"**{len(filtered_contacts)} contact(s) found**"
    )

    if not filtered_contacts:

        st.info(
            "No contacts match your filters."
        )

        session.close()
        return

    # ============================================================
    # DISPLAY CONTACTS
    # ============================================================

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

            # ----------------------------------------------------
            # CONTACT
            # ----------------------------------------------------

            with col1:

                st.write(
                    f"**{full_name}**"
                )

                if contact.job_title:

                    st.caption(
                        contact.job_title
                    )

            # ----------------------------------------------------
            # CLIENT
            # ----------------------------------------------------

            with col2:

                st.write(
                    f"**{client_name}**"
                )

                if contact.email:

                    st.caption(
                        contact.email
                    )

                if contact.phone:

                    st.caption(
                        contact.phone
                    )

            # ----------------------------------------------------
            # CONTACT PREFERENCE
            # ----------------------------------------------------

            with col3:

                if contact.preferred_contact:

                    st.write(
                        f"Preferred: **"
                        f"{contact.preferred_contact}**"
                    )

                st.write(
                    f"Status: **{contact.status}**"
                )

                st.write(
                    f"Primary: **"
                    f"{contact.primary_contact}**"
                )

            # ----------------------------------------------------
            # ACTIONS
            # ----------------------------------------------------

            with col4:

                edit_button = st.button(
                    "Edit",
                    key=f"edit_contact_{contact.id}",
                    use_container_width=True
                )

                delete_button = st.button(
                    "Delete",
                    key=f"delete_contact_{contact.id}",
                    use_container_width=True
                )

            # ====================================================
            # LINKEDIN
            # ====================================================

            if contact.linkedin:

                st.link_button(
                    "Open LinkedIn",
                    contact.linkedin
                )

            # ====================================================
            # EDIT CONTACT
            # ====================================================

            if edit_button:

                st.session_state[
                    f"editing_contact_{contact.id}"
                ] = True

                st.rerun()

            if st.session_state.get(
                f"editing_contact_{contact.id}",
                False
            ):

                st.markdown(
                    "### Edit Contact"
                )

                with st.form(
                    f"edit_contact_form_{contact.id}"
                ):

                    col1, col2 = st.columns(2)

                    with col1:

                        edited_first_name = st.text_input(
                            "First Name",
                            value=contact.first_name or ""
                        )

                        edited_last_name = st.text_input(
                            "Last Name",
                            value=contact.last_name or ""
                        )

                        edited_job_title = st.text_input(
                            "Job Title",
                            value=contact.job_title or ""
                        )

                        edited_email = st.text_input(
                            "Email",
                            value=contact.email or ""
                        )

                    with col2:

                        edited_phone = st.text_input(
                            "Phone",
                            value=contact.phone or ""
                        )

                        edited_linkedin = st.text_input(
                            "LinkedIn",
                            value=contact.linkedin or ""
                        )

                        edited_status = st.selectbox(
                            "Status",
                            CONTACT_STATUSES,
                            index=(
                                CONTACT_STATUSES.index(
                                    contact.status
                                )
                                if contact.status
                                in CONTACT_STATUSES
                                else 0
                            )
                        )

                        edited_primary = st.selectbox(
                            "Primary Contact",
                            ["Yes", "No"],
                            index=(
                                ["Yes", "No"].index(
                                    contact.primary_contact
                                )
                                if contact.primary_contact
                                in ["Yes", "No"]
                                else 0
                            )
                        )

                    edited_preferred = st.selectbox(
                        "Preferred Contact",
                        CONTACT_METHODS,
                        index=(
                            CONTACT_METHODS.index(
                                contact.preferred_contact
                            )
                            if contact.preferred_contact
                            in CONTACT_METHODS
                            else 0
                        )
                    )

                    edited_notes = st.text_area(
                        "Notes",
                        value=contact.notes or ""
                    )

                    save_col, cancel_col = st.columns(2)

                    save_changes = (
                        save_col.form_submit_button(
                            "Save Changes",
                            use_container_width=True
                        )
                    )

                    cancel_edit = (
                        cancel_col.form_submit_button(
                            "Cancel",
                            use_container_width=True
                        )
                    )

                    if cancel_edit:

                        st.session_state[
                            f"editing_contact_{contact.id}"
                        ] = False

                        st.rerun()

                    if save_changes:

                        if not edited_first_name.strip():

                            st.error(
                                "First name is required."
                            )

                        elif (
                            not edited_email.strip()
                            and not edited_phone.strip()
                        ):

                            st.error(
                                "Please provide an email address "
                                "or phone number."
                            )

                        else:

                            contact.first_name = (
                                edited_first_name.strip()
                            )

                            contact.last_name = (
                                edited_last_name.strip()
                            )

                            contact.job_title = (
                                edited_job_title.strip()
                            )

                            contact.email = (
                                edited_email.strip()
                            )

                            contact.phone = (
                                edited_phone.strip()
                            )

                            contact.linkedin = (
                                edited_linkedin.strip()
                            )

                            contact.preferred_contact = (
                                edited_preferred
                            )

                            contact.primary_contact = (
                                edited_primary
                            )

                            contact.status = (
                                edited_status
                            )

                            contact.notes = (
                                edited_notes.strip()
                            )

                            session.commit()

                            st.session_state[
                                f"editing_contact_{contact.id}"
                            ] = False

                            st.success(
                                "Contact updated successfully."
                            )

                            st.rerun()

            # ====================================================
            # DELETE CONTACT
            # ====================================================

            if delete_button:

                st.session_state[
                    f"confirm_delete_contact_{contact.id}"
                ] = True

                st.rerun()

            if st.session_state.get(
                f"confirm_delete_contact_{contact.id}",
                False
            ):

                st.warning(
                    f"Are you sure you want to delete "
                    f"**{full_name}**?"
                )

                st.caption(
                    "A contact with related activities should "
                    "normally be marked Inactive rather than deleted."
                )

                confirm_col, cancel_col = st.columns(2)

                if confirm_col.button(
                    "Yes, Delete Contact",
                    key=f"confirm_delete_{contact.id}",
                    type="primary",
                    use_container_width=True
                ):

                    # ------------------------------------------------
                    # CHECK RELATED ACTIVITIES
                    # ------------------------------------------------

                    has_activities = bool(
                        getattr(
                            contact,
                            "activities",
                            []
                        )
                    )

                    if has_activities:

                        st.error(
                            "This contact cannot be deleted because "
                            "related activities exist. Mark the "
                            "contact as 'Inactive' instead."
                        )

                        st.session_state[
                            f"confirm_delete_contact_{contact.id}"
                        ] = False

                    else:

                        session.delete(contact)
                        session.commit()

                        st.success(
                            "Contact deleted successfully."
                        )

                        st.session_state[
                            f"confirm_delete_contact_{contact.id}"
                        ] = False

                        st.rerun()

                if cancel_col.button(
                    "Cancel",
                    key=f"cancel_delete_{contact.id}",
                    use_container_width=True
                ):

                    st.session_state[
                        f"confirm_delete_contact_{contact.id}"
                    ] = False

                    st.rerun()

            # ====================================================
            # NOTES
            # ====================================================

            if contact.notes:

                st.caption(
                    f"Notes: {contact.notes}"
                )

    session.close()
```
