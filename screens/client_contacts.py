import streamlit as st

from database import get_session
from models import (
    Client,
    ClientContact,
    Activity,
)


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

    return (
        full_name
        or f"Contact {contact.id}"
    )


def get_client_label(client):
    """Return a consistent client label."""

    company_name = (
        client.company_name
        or "Unnamed Client"
    )

    return (
        f"{company_name} "
        f"(ID: {client.id})"
    )


def is_valid_email(email):
    """
    Basic email validation.

    Empty email is allowed because the model
    does not require an email address.
    """

    email = (
        email or ""
    ).strip()

    if not email:
        return True

    if email.count("@") != 1:
        return False

    local_part, domain = email.split("@")

    if not local_part:
        return False

    if not domain:
        return False

    if "." not in domain:
        return False

    if domain.startswith("."):
        return False

    if domain.endswith("."):
        return False

    if " " in email:
        return False

    return True


def is_valid_linkedin(linkedin):
    """
    Basic LinkedIn URL validation.

    Empty LinkedIn URL is allowed.
    """

    linkedin = (
        linkedin or ""
    ).strip()

    if not linkedin:
        return True

    linkedin_lower = linkedin.lower()

    return (
        linkedin_lower.startswith(
            "https://www.linkedin.com/"
        )
        or linkedin_lower.startswith(
            "https://linkedin.com/"
        )
        or linkedin_lower.startswith(
            "http://www.linkedin.com/"
        )
        or linkedin_lower.startswith(
            "http://linkedin.com/"
        )
    )


def is_primary(contact):
    """Return True if the contact is marked as primary."""

    return (
        contact.primary_contact == "Yes"
    )


def get_activity_count(
    session,
    contact_id,
):
    """Return the number of activities linked to a contact."""

    return (
        session.query(Activity)
        .filter(
            Activity.contact_id
            == contact_id
        )
        .count()
    )


def clear_delete_confirmation(
    contact_id,
):
    """Clear delete confirmation state."""

    st.session_state.pop(
        f"confirm_delete_contact_{contact_id}",
        None,
    )


def clear_edit_state():
    """Clear the current contact edit state."""

    st.session_state[
        "editing_contact_id"
    ] = None


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
                Client.company_name.asc(),
                Client.id.asc(),
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
                ClientContact.id.asc(),
            )
            .all()
        )

        # ========================================================
        # SESSION STATE
        # ========================================================

        if (
            "editing_contact_id"
            not in st.session_state
        ):

            st.session_state[
                "editing_contact_id"
            ] = None

        # ========================================================
        # CLIENT OPTIONS
        # ========================================================

        client_labels = []

        client_lookup = {}

        for client in clients:

            label = get_client_label(
                client
            )

            if label in client_lookup:

                label = (
                    f"{label} "
                    f"- Client #{client.id}"
                )

            client_labels.append(
                label
            )

            client_lookup[
                label
            ] = client

        # ========================================================
        # OVERVIEW
        # ========================================================

        st.subheader("Overview")

        total_contacts = len(
            contacts
        )

        active_contacts = sum(
            1
            for contact in contacts
            if contact.status == "Active"
        )

        inactive_contacts = sum(
            1
            for contact in contacts
            if contact.status == "Inactive"
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
                if contact.client_id
                is not None
            }
        )

        contacts_with_activities = sum(
            1
            for contact in contacts
            if get_activity_count(
                session,
                contact.id,
            ) > 0
        )

        col1, col2, col3, col4 = (
            st.columns(4)
        )

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

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Inactive Contacts",
                inactive_contacts,
            )

        with col2:

            st.metric(
                "Contacts With Activities",
                contacts_with_activities,
            )

        st.divider()

        # ========================================================
        # FIND EDITING CONTACT
        # ========================================================

        editing_contact = None

        editing_contact_id = (
            st.session_state.get(
                "editing_contact_id"
            )
        )

        if editing_contact_id:

            editing_contact = session.get(
                ClientContact,
                editing_contact_id,
            )

            if not editing_contact:

                clear_edit_state()

                editing_contact_id = None

        # ========================================================
        # ADD / EDIT CONTACT
        # ========================================================

        if editing_contact:

            st.subheader(
                "Edit Client Contact"
            )

            # ====================================================
            # DEFAULT EDIT VALUES
            # ====================================================

            if editing_contact.client:

                selected_client_label = (
                    get_client_label(
                        editing_contact.client
                    )
                )

                # If duplicate labels somehow exist,
                # find the matching option by client ID.
                if (
                    selected_client_label
                    not in client_labels
                ):

                    selected_client_label = (
                        next(
                            (
                                label
                                for label,
                                client
                                in client_lookup.items()
                                if client.id
                                == editing_contact.client_id
                            ),
                            None,
                        )
                    )

            else:

                selected_client_label = (
                    client_labels[0]
                    if client_labels
                    else None
                )

            default_first_name = (
                editing_contact.first_name
                or ""
            )

            default_last_name = (
                editing_contact.last_name
                or ""
            )

            default_job_title = (
                editing_contact.job_title
                or ""
            )

            default_email = (
                editing_contact.email
                or ""
            )

            default_phone = (
                editing_contact.phone
                or ""
            )

            default_linkedin = (
                editing_contact.linkedin
                or ""
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
                editing_contact.notes
                or ""
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
                    "Client *",
                    client_labels,
                    index=(
                        client_labels.index(
                            selected_client_label
                        )
                        if (
                            selected_client_label
                            in client_labels
                        )
                        else 0
                    ),
                )

                # ====================================================
                # CONTACT INFORMATION
                # ====================================================

                col1, col2 = st.columns(2)

                with col1:

                    first_name = st.text_input(
                        "First Name *",
                        value=(
                            default_first_name
                        ),
                    )

                    job_title = st.text_input(
                        "Job Title",
                        value=(
                            default_job_title
                        ),
                        placeholder=(
                            "e.g. Finance Director"
                        ),
                    )

                    email = st.text_input(
                        "Email",
                        value=(
                            default_email
                        ),
                    )

                    phone = st.text_input(
                        "Phone",
                        value=(
                            default_phone
                        ),
                    )

                with col2:

                    last_name = st.text_input(
                        "Last Name",
                        value=(
                            default_last_name
                        ),
                    )

                    linkedin = st.text_input(
                        "LinkedIn",
                        value=(
                            default_linkedin
                        ),
                        placeholder=(
                            "https://www.linkedin.com/in/..."
                        ),
                    )

                    preferred_contact = (
                        st.selectbox(
                            "Preferred Contact Method",
                            CONTACT_METHODS,
                            index=(
                                CONTACT_METHODS.index(
                                    default_preferred_contact
                                )
                                if (
                                    default_preferred_contact
                                    in CONTACT_METHODS
                                )
                                else 0
                            ),
                        )
                    )

                    status = st.selectbox(
                        "Status",
                        CONTACT_STATUSES,
                        index=(
                            CONTACT_STATUSES.index(
                                default_status
                            )
                            if (
                                default_status
                                in CONTACT_STATUSES
                            )
                            else 0
                        ),
                    )

                # ====================================================
                # PRIMARY CONTACT
                # ====================================================

                primary_contact = st.checkbox(
                    "Primary Contact",
                    value=default_primary,
                    help=(
                        "Only one contact per client "
                        "can be marked as the primary contact."
                    ),
                )

                # ====================================================
                # NOTES
                # ====================================================

                notes = st.text_area(
                    "Notes",
                    value=default_notes,
                    placeholder=(
                        "Internal notes about this contact..."
                    ),
                )

                # ====================================================
                # SUBMIT
                # ====================================================

                if editing_contact:

                    submitted = (
                        st.form_submit_button(
                            "Update Contact",
                            use_container_width=True,
                        )
                    )

                else:

                    submitted = (
                        st.form_submit_button(
                            "Add Contact",
                            use_container_width=True,
                        )
                    )

                # ====================================================
                # PROCESS FORM
                # ====================================================

                if submitted:

                    first_name = (
                        first_name.strip()
                    )

                    last_name = (
                        last_name.strip()
                    )

                    job_title = (
                        job_title.strip()
                    )

                    email = (
                        email.strip()
                    )

                    phone = (
                        phone.strip()
                    )

                    linkedin = (
                        linkedin.strip()
                    )

                    notes = (
                        notes.strip()
                    )

                    # ================================================
                    # VALIDATION
                    # ================================================

                    if not first_name:

                        st.error(
                            "First name is required."
                        )

                    elif not is_valid_email(
                        email
                    ):

                        st.error(
                            "Please enter a valid email address."
                        )

                    elif not is_valid_linkedin(
                        linkedin
                    ):

                        st.error(
                            "Please enter a valid LinkedIn URL."
                        )

                    else:

                        selected_client = (
                            client_lookup.get(
                                client_choice
                            )
                        )

                        if not selected_client:

                            st.error(
                                "Please select a valid client."
                            )

                        else:

                            # ========================================
                            # DUPLICATE NAME CHECK
                            # ========================================

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

                                try:

                                    # ====================================
                                    # PRIMARY CONTACT CONTROL
                                    # ====================================

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

                                        for contact in (
                                            existing_primary
                                        ):

                                            if (
                                                not editing_contact
                                                or contact.id
                                                != editing_contact.id
                                            ):

                                                contact.primary_contact = (
                                                    "No"
                                                )

                                    # ====================================
                                    # UPDATE
                                    # ====================================

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

                                    # ====================================
                                    # CREATE
                                    # ====================================

                                    else:

                                        new_contact = (
                                            ClientContact(
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
                                        )

                                        session.add(
                                            new_contact
                                        )

                                        message = (
                                            "Client contact added "
                                            "successfully."
                                        )

                                    # ====================================
                                    # SAVE
                                    # ====================================

                                    session.commit()

                                    clear_edit_state()

                                    st.success(
                                        message
                                    )

                                    st.rerun()

                                except Exception as error:

                                    session.rollback()

                                    st.error(
                                        "The contact could not "
                                        "be saved."
                                    )

                                    st.exception(
                                        error
                                    )

            # ====================================================
            # CANCEL EDITING
            # ====================================================

            if editing_contact:

                if st.button(
                    "Cancel Editing",
                    use_container_width=True,
                ):

                    clear_edit_state()

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
                "email, phone, LinkedIn or notes..."
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

            contact_type_filter = (
                st.selectbox(
                    "Contact Type",
                    [
                        "All Contacts",
                        "Primary Contacts",
                        "Non-Primary Contacts",
                    ],
                )
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

        selected_filter_client = None

        if (
            client_filter
            != "All Clients"
        ):

            selected_filter_client = (
                client_lookup.get(
                    client_filter
                )
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
            # SEARCH
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
                        contact.preferred_contact
                        or "",
                        contact.status or "",
                        contact.notes or "",
                    ]
                ).lower()

                if (
                    search_lower
                    not in combined_text
                ):

                    continue

            # ====================================================
            # STATUS
            # ====================================================

            if (
                status_filter
                != "All Statuses"
                and contact.status
                != status_filter
            ):

                continue

            # ====================================================
            # CONTACT TYPE
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
            # CLIENT
            # ====================================================

            if (
                selected_filter_client
                and contact.client_id
                != selected_filter_client.id
            ):

                continue

            filtered_contacts.append(
                contact
            )

        # ========================================================
        # REGISTER SUMMARY
        # ========================================================

        st.caption(
            f"Showing "
            f"{len(filtered_contacts)} "
            f"of "
            f"{len(contacts)} "
            f"contacts"
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

            for contact in (
                filtered_contacts
            ):

                with st.container(
                    border=True
                ):

                    col1, col2, col3 = (
                        st.columns(
                            [3, 2, 1]
                        )
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

                        activity_count = (
                            get_activity_count(
                                session,
                                contact.id,
                            )
                        )

                        st.caption(
                            f"CRM Activities: "
                            f"{activity_count}"
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

                            # Clear any delete state.
                            clear_delete_confirmation(
                                contact.id
                            )

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

                            st.session_state[
                                "editing_contact_id"
                            ] = None

                            st.rerun()

                    # ================================================
                    # LINKEDIN
                    # ================================================

                    if contact.linkedin:

                        st.markdown(
                            f"[LinkedIn profile]"
                            f"({contact.linkedin})"
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

                        activity_count = (
                            get_activity_count(
                                session,
                                contact.id,
                            )
                        )

                        if activity_count > 0:

                            st.warning(
                                "This contact has "
                                f"**{activity_count} linked CRM "
                                "activity record(s)**."
                            )

                            st.info(
                                "Deletion is blocked because "
                                "this contact has CRM history. "
                                "Change the contact to Inactive "
                                "instead if the person is no "
                                "longer active."
                            )

                            if st.button(
                                "Cancel",
                                key=(
                                    f"cancel_blocked_delete_"
                                    f"{contact.id}"
                                ),
                                use_container_width=True,
                            ):

                                clear_delete_confirmation(
                                    contact.id
                                )

                                st.rerun()

                        else:

                            st.warning(
                                "Are you sure you want to "
                                "permanently delete this contact?"
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

                                    try:

                                        session.delete(
                                            contact
                                        )

                                        session.commit()

                                        clear_delete_confirmation(
                                            contact.id
                                        )

                                        st.success(
                                            "Contact deleted "
                                            "successfully."
                                        )

                                        st.rerun()

                                    except Exception as error:

                                        session.rollback()

                                        clear_delete_confirmation(
                                            contact.id
                                        )

                                        st.error(
                                            "This contact could "
                                            "not be deleted."
                                        )

                                        st.exception(
                                            error
                                        )

                            with confirm_col2:

                                if st.button(
                                    "Cancel",
                                    key=(
                                        f"confirm_no_contact_"
                                        f"{contact.id}"
                                    ),
                                    use_container_width=True,
                                ):

                                    clear_delete_confirmation(
                                        contact.id
                                    )

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