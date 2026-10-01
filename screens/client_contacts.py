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
        or f"Contact #{contact.id}"
    )


def get_client_name(client):
    """Return a safe client/company name."""

    if not client:
        return "Unknown Client"

    return (
        client.company_name
        or f"Client #{client.id}"
    )


def get_client_label(client):
    """
    Return a collision-safe client label.

    Client ID is intentionally included so that
    duplicate company names cannot cause ambiguity.
    """

    return (
        f"{get_client_name(client)} "
        f"(Client #{client.id})"
    )


def get_contact_label(contact):
    """Return a useful contact label."""

    return (
        f"{get_full_name(contact)} "
        f"(Contact #{contact.id})"
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

    if " " in email:
        return False

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

    linkedin_lower = (
        linkedin.lower()
    )

    valid_prefixes = (
        "https://www.linkedin.com/",
        "https://linkedin.com/",
        "http://www.linkedin.com/",
        "http://linkedin.com/",
    )

    return linkedin_lower.startswith(
        valid_prefixes
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
            Activity.contact_id == contact_id
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


def clear_all_delete_confirmations(
    contacts,
):
    """Clear all contact delete confirmations."""

    for contact in contacts:

        clear_delete_confirmation(
            contact.id
        )


def clear_edit_state():
    """Clear the current contact edit state."""

    st.session_state[
        "editing_contact_id"
    ] = None


def normalize_text(value):
    """Return safely stripped text."""

    return (
        value or ""
    ).strip()


def get_contact_search_text(contact):
    """
    Build searchable text for a contact.
    """

    client_name = (
        get_client_name(contact.client)
        if contact.client
        else "Unknown Client"
    )

    values = [
        get_full_name(contact),
        client_name,
        contact.job_title or "",
        contact.email or "",
        contact.phone or "",
        contact.linkedin or "",
        contact.preferred_contact or "",
        contact.status or "",
        contact.primary_contact or "",
        contact.notes or "",
    ]

    return " ".join(
        values
    ).lower()


def get_primary_contact(
    session,
    client_id,
    exclude_contact_id=None,
):
    """
    Return the existing primary contact for a client,
    excluding a specified contact when editing.
    """

    query = (
        session.query(ClientContact)
        .filter(
            ClientContact.client_id == client_id,
            ClientContact.primary_contact == "Yes",
        )
    )

    if exclude_contact_id:

        query = query.filter(
            ClientContact.id
            != exclude_contact_id
        )

    return query.first()


def validate_contact(
    first_name,
    email,
    linkedin,
):
    """
    Validate contact information.

    Returns:
        list[str]: validation errors
    """

    errors = []

    if not first_name:

        errors.append(
            "First name is required."
        )

    if not is_valid_email(email):

        errors.append(
            "Please enter a valid email address."
        )

    if not is_valid_linkedin(linkedin):

        errors.append(
            "Please enter a valid LinkedIn URL."
        )

    return errors


# ============================================================
# MAIN CLIENT CONTACTS SCREEN
# ============================================================

def show_client_contacts():

    st.title("Client Contacts")

    st.caption(
        "Manage contacts, decision-makers and "
        "relationship information for AVERRA clients."
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
        # CLIENT LOOKUPS
        # ========================================================

        client_labels = []
        client_lookup = {}

        for client in clients:

            label = get_client_label(
                client
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
                if contact.client_id is not None
            }
        )

        contacts_without_email = sum(
            1
            for contact in contacts
            if not normalize_text(
                contact.email
            )
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

        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:

            st.metric(
                "Inactive Contacts",
                inactive_contacts,
            )

        with col2:

            st.metric(
                "With CRM Activities",
                contacts_with_activities,
            )

        with col3:

            st.metric(
                "Missing Email",
                contacts_without_email,
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
            # EDIT DEFAULT VALUES
            # ====================================================

            if editing_contact.client:

                selected_client_label = (
                    get_client_label(
                        editing_contact.client
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

                    first_name = normalize_text(
                        first_name
                    )

                    last_name = normalize_text(
                        last_name
                    )

                    job_title = normalize_text(
                        job_title
                    )

                    email = normalize_text(
                        email
                    )

                    phone = normalize_text(
                        phone
                    )

                    linkedin = normalize_text(
                        linkedin
                    )

                    notes = normalize_text(
                        notes
                    )

                    selected_client = (
                        client_lookup.get(
                            client_choice
                        )
                    )

                    # ================================================
                    # VALIDATION
                    # ================================================

                    validation_errors = (
                        validate_contact(
                            first_name,
                            email,
                            linkedin,
                        )
                    )

                    if not selected_client:

                        validation_errors.append(
                            "Please select a valid client."
                        )

                    if validation_errors:

                        for error_message in (
                            validation_errors
                        ):

                            st.error(
                                error_message
                            )

                    else:

                        # ============================================
                        # DUPLICATE NAME CHECK
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

                            try:

                                # ====================================
                                # PRIMARY CONTACT CONTROL
                                # ====================================

                                if primary_contact:

                                    existing_primary = (
                                        get_primary_contact(
                                            session,
                                            selected_client.id,
                                            (
                                                editing_contact.id
                                                if editing_contact
                                                else None
                                            ),
                                        )
                                    )

                                    if existing_primary:

                                        existing_primary.primary_contact = (
                                            "No"
                                        )

                                # ====================================
                                # UPDATE EXISTING CONTACT
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
                                # CREATE NEW CONTACT
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

        # ========================================================
        # SEARCH
        # ========================================================

        search_text = st.text_input(
            "Search Contacts",
            placeholder=(
                "Search name, company, job title, "
                "email, phone, LinkedIn or notes..."
            ),
        )

        # ========================================================
        # FILTERS
        # ========================================================

        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:

            status_filter = st.selectbox(
                "Status",
                [
                    "All Statuses"
                ]
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
                [
                    "All Clients"
                ]
                + client_labels,
            )

        # ========================================================
        # SECOND FILTER ROW
        # ========================================================

        col1, col2 = (
            st.columns(2)
        )

        with col1:

            activity_filter = st.selectbox(
                "CRM Activity",
                [
                    "All Contacts",
                    "With Activities",
                    "Without Activities",
                ],
            )

        with col2:

            sort_order = st.selectbox(
                "Sort By",
                [
                    "Name A-Z",
                    "Name Z-A",
                    "Company A-Z",
                    "Status",
                    "Primary First",
                ],
            )

        # ========================================================
        # CLEAR FILTERS
        # ========================================================

        filter_active = (
            bool(search_text.strip())
            or status_filter
            != "All Statuses"
            or contact_type_filter
            != "All Contacts"
            or client_filter
            != "All Clients"
            or activity_filter
            != "All Contacts"
        )

        if filter_active:

            if st.button(
                "Clear Filters",
                use_container_width=True,
            ):

                st.rerun()

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

            # ====================================================
            # SEARCH
            # ====================================================

            if search_lower:

                combined_text = (
                    get_contact_search_text(
                        contact
                    )
                )

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

            # ====================================================
            # ACTIVITY
            # ====================================================

            activity_count = (
                get_activity_count(
                    session,
                    contact.id,
                )
            )

            if (
                activity_filter
                == "With Activities"
                and activity_count == 0
            ):

                continue

            if (
                activity_filter
                == "Without Activities"
                and activity_count > 0
            ):

                continue

            filtered_contacts.append(
                contact
            )

        # ========================================================
        # SORT RESULTS
        # ========================================================

        if sort_order == "Name A-Z":

            filtered_contacts.sort(
                key=lambda contact: (
                    get_full_name(contact)
                    .lower()
                )
            )

        elif sort_order == "Name Z-A":

            filtered_contacts.sort(
                key=lambda contact: (
                    get_full_name(contact)
                    .lower()
                ),
                reverse=True,
            )

        elif sort_order == "Company A-Z":

            filtered_contacts.sort(
                key=lambda contact: (
                    get_client_name(
                        contact.client
                    ).lower()
                )
            )

        elif sort_order == "Status":

            filtered_contacts.sort(
                key=lambda contact: (
                    contact.status or ""
                ).lower()
            )

        elif sort_order == "Primary First":

            filtered_contacts.sort(
                key=lambda contact: (
                    not is_primary(contact),
                    get_full_name(contact).lower(),
                )
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
                            [3, 3, 1]
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

                        st.caption(
                            f"Contact #{contact.id}"
                        )

                        st.write(
                            f"**Company:** "
                            f"{get_client_name(contact.client)}"
                        )

                        if contact.job_title:

                            st.write(
                                f"**Job Title:** "
                                f"{contact.job_title}"
                            )

                        st.write(
                            f"**Status:** "
                            f"{contact.status or 'Not specified'}"
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

                        else:

                            st.caption(
                                "Email: Not provided"
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

                        if contact.linkedin:

                            st.markdown(
                                "[Open LinkedIn profile]"
                                f"({contact.linkedin})"
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

                            clear_all_delete_confirmations(
                                contacts
                            )

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

                            clear_all_delete_confirmations(
                                contacts
                            )

                            st.session_state[
                                f"confirm_delete_contact_"
                                f"{contact.id}"
                            ] = True

                            clear_edit_state()

                            st.rerun()

                    # ================================================
                    # NOTES
                    # ================================================

                    if contact.notes:

                        with st.expander(
                            "View Notes"
                        ):

                            st.write(
                                contact.notes
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
                                "Deletion is blocked for this contact."
                            )

                            st.info(
                                f"This contact has "
                                f"{activity_count} linked CRM "
                                f"activity record(s). "
                                f"Keeping the contact preserves "
                                f"your CRM history."
                            )

                            st.write(
                                "Recommended action: change "
                                "the contact status to "
                                "**Inactive** instead."
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

        st.exception(
            error
        )

    finally:

        session.close()