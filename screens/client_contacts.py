
import streamlit as st

from database import get_session
from models import Client, ClientContact


# ============================================================
# CONSTANTS
# ============================================================

CONTACT_STATUSES = [
    "Active",
    "Inactive",
]

CONTACT_METHODS = [
    "Email",
    "Phone",
    "LinkedIn",
    "Other",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_full_name(contact):
    """Return the contact's full name."""

    first_name = (
        contact.first_name or ""
    ).strip()

    last_name = (
        contact.last_name or ""
    ).strip()

    full_name = (
        f"{first_name} {last_name}"
    ).strip()

    return full_name or f"Contact {contact.id}"


def is_valid_email(email):
    """Basic email validation."""

    email = (
        email or ""
    ).strip()

    if not email:
        return True

    return (
        "@" in email
        and "." in email.split("@")[-1]
    )


def is_primary(contact):
    """Check whether a contact is marked as primary."""

    return contact.primary_contact == "Yes"


# ============================================================
# MAIN CLIENT CONTACTS SCREEN
# ============================================================

def show_client_contacts():

    st.title("Client Contacts")

    st.caption(
        "Manage contacts and key decision-makers "
        "for AVERRA clients."
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
        # LOAD CONTACTS
        # ========================================================

        contacts = (
            session.query(ClientContact)
            .order_by(
                ClientContact.first_name.asc(),
                ClientContact.last_name.asc(),
            )
            .all()
        )

        # ========================================================
        # SESSION STATE
        # ========================================================

        if "editing_contact_id" not in st.session_state:

            st.session_state.editing_contact_id = None

        # ========================================================
        # CLIENT OPTIONS
        # ========================================================

        client_labels = [
            (
                f"{client.company_name} "
                f"(ID: {client.id})"
            )
            for client in clients
        ]

        client_lookup = {
            (
                f"{client.company_name} "
                f"(ID: {client.id})"
            ): client
            for client in clients
        }

        # ========================================================
        # OVERVIEW
        # ========================================================

        st.subheader("Overview")

        total_contacts = len(contacts)

        active_contacts = sum(
            1
            for contact in contacts
            if contact.status == "Active"
        )

        primary_contacts = sum(
            1
            for contact in contacts
            if is_primary(contact)
        )

        companies_with_contacts = len(
            {
                contact.client_id
                for contact in contacts
                if contact.client_id is not None
            }
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Total Contacts",
                total_contacts,
            )

        with col2:

            st.metric(
                "Active Contacts",
                active_contacts,
            )

        with col3:

            st.metric(
                "Primary Contacts",
                primary_contacts,
            )

        with col4:

            st.metric(
                "Companies With Contacts",
                companies_with_contacts,
            )

        st.divider()

        # ========================================================
        # ADD / EDIT CONTACT
        # ========================================================

        editing_contact = None

        editing_contact_id = (
            st.session_state.editing_contact_id
        )

        if editing_contact_id:

            editing_contact = session.get(
                ClientContact,
                editing_contact_id,
            )

        # ========================================================
        # DEFAULT VALUES
        # ========================================================

        if editing_contact:

            st.subheader(
                "Edit Client Contact"
            )

            if editing_contact.client:

                selected_client_label = (
                    f"{editing_contact.client.company_name} "
                    f"(ID: {editing_contact.client.id})"
                )

            else:

                selected_client_label = (
                    client_labels[0]
                    if client_labels
                    else None
                )

            default_first_name = (
                editing_contact.first_name or ""
            )

            default_last_name = (
                editing_contact.last_name or ""
            )

            default_job_title = (
                editing_contact.job_title or ""
            )

            default_email = (
                editing_contact.email or ""
            )

            default_phone = (
                editing_contact.phone or ""
            )

            default_linkedin = (
                editing_contact.linkedin or ""
            )

            default_preferred_contact = (
                editing_contact.preferred_contact
                or "Email"
            )

            default_primary = (
                editing_contact.primary_contact
                == "Yes"
            )

            default_status = (
                editing_contact.status
                or "Active"
            )

            default_notes = (
                editing_contact.notes or ""
            )

        else:

            st.subheader(
                "Add Client Contact"
            )

            selected_client_label = (
                client_labels[0]
                if client_labels
                else None
            )

            default_first_name = ""
            default_last_name = ""
            default_job_title = ""
            default_email = ""
            default_phone = ""
            default_linkedin = ""
            default_preferred_contact = "Email"
            default_primary = False
            default_status = "Active"
            default_notes = ""

        # ========================================================
        # NO CLIENTS
        # ========================================================

        if not clients:

            st.warning(
                "No clients exist yet. "
                "Add a client before creating a contact."
            )

        else:

            # ====================================================
            # CONTACT FORM
            # ====================================================

            with st.form(
                "client_contact_form",
                clear_on_submit=False,
            ):

                client_choice = st.selectbox(
                    "Client",
                    client_labels,
                    index=(
                        client_labels.index(
                            selected_client_label
                        )
                        if selected_client_label
                        in client_labels
                        else 0
                    ),
                )

                # ====================================================
                # CONTACT INFORMATION
                # ====================================================

                col1, col2 = st.columns(2)

                with col1:

                    first_name = st.text_input(
                        "First Name",
                        value=default_first_name,
                    )

                    job_title = st.text_input(
                        "Job Title",
                        value=default_job_title,
                        placeholder=(
                            "e.g. Finance Director"
                        ),
                    )

                    email = st.text_input(
                        "Email",
                        value=default_email,
                    )

                    phone = st.text_input(
                        "Phone",
                        value=default_phone,
                    )

                with col2:

                    last_name = st.text_input(
                        "Last Name",
                        value=default_last_name,
                    )

                    linkedin = st.text_input(
                        "LinkedIn",
                        value=default_linkedin,
                    )

                    preferred_contact = st.selectbox(
                        "Preferred Contact Method",
                        CONTACT_METHODS,
                        index=(
                            CONTACT_METHODS.index(
                                default_preferred_contact
                            )
                            if default_preferred_contact
                            in CONTACT_METHODS
                            else 0
                        ),
                    )

                    status = st.selectbox(
                        "Status",
                        CONTACT_STATUSES,
                        index=(
                            CONTACT_STATUSES.index(
                                default_status
                            )
                            if default_status
                            in CONTACT_STATUSES
                            else 0
                        ),
                    )

                # ====================================================
                # PRIMARY CONTACT
                # ====================================================

                primary_contact = st.checkbox(
                    "Primary Contact",
                    value=default_primary,
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

                if editing_contact:

                    submitted = st.form_submit_button(
                        "Update Contact",
                        use_container_width=True,
                    )

                else:

                    submitted = st.form_submit_button(
                        "Add Contact",
                        use_container_width=True,
                    )

                # ====================================================
                # PROCESS FORM
                # ====================================================

                if submitted:

                    first_name = first_name.strip()
                    last_name = last_name.strip()
                    job_title = job_title.strip()
                    email = email.strip()
                    phone = phone.strip()
                    linkedin = linkedin.strip()
                    notes = notes.strip()

                    # ================================================
                    # VALIDATION
                    # ================================================

                    if not first_name:

                        st.error(
                            "First name is required."
                        )

                    elif not is_valid_email(email):

                        st.error(
                            "Please enter a valid email address."
                        )

                    else:

                        selected_client = (
                            client_lookup[
                                client_choice
                            ]
                        )

                        # ============================================
                        # DUPLICATE CHECK
                        # ============================================

                        duplicate_query = (
                            session.query(
                                ClientContact
                            )
                            .filter(
                                ClientContact.client_id
                                == selected_client.id,

                                ClientContact.first_name.ilike(
                                    first_name
                                ),

                                ClientContact.last_name.ilike(
                                    last_name
                                ),
                            )
                        )

                        if editing_contact:

                            duplicate_query = (
                                duplicate_query.filter(
                                    ClientContact.id
                                    != editing_contact.id
                                )
                            )

                        duplicate = (
                            duplicate_query.first()
                        )

                        if duplicate:

                            st.error(
                                "A contact with this name "
                                "already exists for this client."
                            )

                        else:

                            # ========================================
                            # PRIMARY CONTACT CONTROL
                            # ========================================

                            if primary_contact:

                                existing_primary = (
                                    session.query(
                                        ClientContact
                                    )
                                    .filter(
                                        ClientContact.client_id
                                        == selected_client.id,

                                        ClientContact.primary_contact
                                        == "Yes",
                                    )
                                    .all()
                                )

                                for contact in existing_primary:

                                    if (
                                        not editing_contact
                                        or contact.id
                                        != editing_contact.id
                                    ):

                                        contact.primary_contact = (
                                            "No"
                                        )

                            # ========================================
                            # UPDATE EXISTING CONTACT
                            # ========================================

                            if editing_contact:

                                editing_contact.client_id = (
                                    selected_client.id
                                )

                                editing_contact.first_name = (
                                    first_name
                                )

                                editing_contact.last_name = (
                                    last_name
                                )

                                editing_contact.job_title = (
                                    job_title
                                )

                                editing_contact.email = (
                                    email
                                )

                                editing_contact.phone = (
                                    phone
                                )

                                editing_contact.linkedin = (
                                    linkedin
                                )

                                editing_contact.preferred_contact = (
                                    preferred_contact
                                )

                                editing_contact.primary_contact = (
                                    "Yes"
                                    if primary_contact
                                    else "No"
                                )

                                editing_contact.status = (
                                    status
                                )

                                editing_contact.notes = (
                                    notes
                                )

                                message = (
                                    "Client contact updated "
                                    "successfully."
                                )

                            # ========================================
                            # CREATE NEW CONTACT
                            # ========================================

                            else:

                                new_contact = ClientContact(
                                    client_id=(
                                        selected_client.id
                                    ),
                                    first_name=(
                                        first_name
                                    ),
                                    last_name=(
                                        last_name
                                    ),
                                    job_title=(
                                        job_title
                                    ),
                                    email=(
                                        email
                                    ),
                                    phone=(
                                        phone
                                    ),
                                    linkedin=(
                                        linkedin
                                    ),
                                    preferred_contact=(
                                        preferred_contact
                                    ),
                                    primary_contact=(
                                        "Yes"
                                        if primary_contact
                                        else "No"
                                    ),
                                    status=(
                                        status
                                    ),
                                    notes=(
                                        notes
                                    ),
                                )

                                session.add(
                                    new_contact
                                )

                                message = (
                                    "Client contact added "
                                    "successfully."
                                )

                            # ========================================
                            # SAVE
                            # ========================================

                            session.commit()

                            st.session_state[
                                "editing_contact_id"
                            ] = None

                            st.success(
                                message
                            )

                            st.rerun()

            # ====================================================
            # CANCEL EDITING
            # ====================================================

            if editing_contact:

                if st.button(
                    "Cancel Editing",
                    use_container_width=True,
                ):

                    st.session_state[
                        "editing_contact_id"
                    ] = None

                    st.rerun()

        st.divider()

        # ========================================================
        # CONTACT REGISTER
        # ========================================================

        st.subheader(
            "Contact Register"
        )

        search_text = st.text_input(
            "Search Contacts",
            placeholder=(
                "Search name, company, job title, "
                "email, phone or notes..."
            ),
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            status_filter = st.selectbox(
                "Status",
                ["All Statuses"]
                + CONTACT_STATUSES,
            )

        with col2:

            contact_type_filter = st.selectbox(
                "Contact Type",
                [
                    "All Contacts",
                    "Primary Contacts",
                    "Non-Primary Contacts",
                ],
            )

        with col3:

            client_filter = st.selectbox(
                "Client",
                ["All Clients"]
                + client_labels,
            )

        # ========================================================
        # APPLY FILTERS
        # ========================================================

        filtered_contacts = []

        search_lower = (
            search_text.strip().lower()
        )

        for contact in contacts:

            client = contact.client

            company_name = (
                client.company_name
                if client
                else "Unknown Client"
            )

            full_name = get_full_name(
                contact
            )

            # ====================================================
            # SEARCH FILTER
            # ====================================================

            if search_lower:

                combined_text = " ".join(
                    [
                        full_name,
                        company_name,
                        contact.job_title or "",
                        contact.email or "",
                        contact.phone or "",
                        contact.linkedin or "",
                        contact.notes or "",
                    ]
                ).lower()

                if search_lower not in combined_text:

                    continue

            # ====================================================
            # STATUS FILTER
            # ====================================================

            if (
                status_filter != "All Statuses"
                and contact.status
                != status_filter
            ):

                continue

            # ====================================================
            # CONTACT TYPE FILTER
            # ====================================================

            if (
                contact_type_filter
                == "Primary Contacts"
                and not is_primary(contact)
            ):

                continue

            if (
                contact_type_filter
                == "Non-Primary Contacts"
                and is_primary(contact)
            ):

                continue

            # ====================================================
            # CLIENT FILTER
            # ====================================================

            if (
                client_filter
                != "All Clients"
            ):

                selected_client = (
                    client_lookup.get(
                        client_filter
                    )
                )

                if not selected_client:

                    continue

                if (
                    contact.client_id
                    != selected_client.id
                ):

                    continue

            filtered_contacts.append(
                contact
            )

        # ========================================================
        # REGISTER SUMMARY
        # ========================================================

        st.caption(
            f"Showing {len(filtered_contacts)} "
            f"of {len(contacts)} contacts"
        )

        # ========================================================
        # NO RESULTS
        # ========================================================

        if not filtered_contacts:

            st.info(
                "No contacts match your filters."
            )

        # ========================================================
        # DISPLAY CONTACTS
        # ========================================================

        else:

            for contact in filtered_contacts:

                with st.container(
                    border=True
                ):

                    col1, col2, col3 = st.columns(
                        [3, 2, 1]
                    )

                    # ================================================
                    # CONTACT
                    # ================================================

                    with col1:

                        primary_label = (
                            " ⭐ Primary"
                            if is_primary(contact)
                            else ""
                        )

                        st.markdown(
                            f"### "
                            f"{get_full_name(contact)}"
                            f"{primary_label}"
                        )

                        if contact.client:

                            st.write(
                                f"**Company:** "
                                f"{contact.client.company_name}"
                            )

                        else:

                            st.write(
                                "**Company:** "
                                "Unknown"
                            )

                        if contact.job_title:

                            st.write(
                                f"**Job Title:** "
                                f"{contact.job_title}"
                            )

                    # ================================================
                    # CONTACT DETAILS
                    # ================================================

                    with col2:

                        if contact.email:

                            st.write(
                                f"**Email:** "
                                f"{contact.email}"
                            )

                        if contact.phone:

                            st.write(
                                f"**Phone:** "
                                f"{contact.phone}"
                            )

                        if contact.preferred_contact:

                            st.write(
                                f"**Preferred:** "
                                f"{contact.preferred_contact}"
                            )

                        st.write(
                            f"**Status:** "
                            f"{contact.status or 'Not specified'}"
                        )

                    # ================================================
                    # ACTIONS
                    # ================================================

                    with col3:

                        if st.button(
                            "Edit",
                            key=(
                                f"edit_contact_"
                                f"{contact.id}"
                            ),
                            use_container_width=True,
                        ):

                            st.session_state[
                                "editing_contact_id"
                            ] = contact.id

                            st.rerun()

                        if st.button(
                            "Delete",
                            key=(
                                f"delete_contact_"
                                f"{contact.id}"
                            ),
                            use_container_width=True,
                        ):

                            st.session_state[
                                f"confirm_delete_contact_"
                                f"{contact.id}"
                            ] = True

                    # ================================================
                    # LINKEDIN
                    # ================================================

                    if contact.linkedin:

                        st.caption(
                            f"LinkedIn: "
                            f"{contact.linkedin}"
                        )

                    # ================================================
                    # NOTES
                    # ================================================

                    if contact.notes:

                        st.caption(
                            f"Notes: "
                            f"{contact.notes}"
                        )

                    # ================================================
                    # DELETE CONFIRMATION
                    # ================================================

                    if st.session_state.get(
                        (
                            f"confirm_delete_contact_"
                            f"{contact.id}"
                        ),
                        False,
                    ):

                        st.warning(
                            "Are you sure you want to "
                            "delete this contact?"
                        )

                        confirm_col1, confirm_col2 = (
                            st.columns(2)
                        )

                        with confirm_col1:

                            if st.button(
                                "Yes, Delete",
                                key=(
                                    f"confirm_yes_contact_"
                                    f"{contact.id}"
                                ),
                                use_container_width=True,
                            ):

                                session.delete(
                                    contact
                                )

                                session.commit()

                                st.session_state[
                                    (
                                        f"confirm_delete_contact_"
                                        f"{contact.id}"
                                    )
                                ] = False

                                st.success(
                                    "Contact deleted successfully."
                                )

                                st.rerun()

                        with confirm_col2:

                            if st.button(
                                "Cancel",
                                key=(
                                    f"confirm_no_contact_"
                                    f"{contact.id}"
                                ),
                                use_container_width=True,
                            ):

                                st.session_state[
                                    (
                                        f"confirm_delete_contact_"
                                        f"{contact.id}"
                                    )
                                ] = False

                                st.rerun()

    except Exception as error:

        session.rollback()

        st.error(
            "An error occurred while loading "
            "the Client Contacts screen."
        )

        st.exception(error)

    finally:

        session.close()
