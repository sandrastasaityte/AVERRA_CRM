import os
import re
from pathlib import Path

import streamlit as st

from database import get_session
from models import Employee


# ============================================================
# CONSTANTS
# ============================================================

EMPLOYEE_STATUSES = [
    "Sourced",
    "Available",
    "Interviewing",
    "Placed",
    "On Leave",
    "Unavailable",
    "Former Employee",
]

ENGLISH_LEVELS = [
    "Basic",
    "Intermediate",
    "Advanced",
    "Fluent",
    "Native",
]

AVAILABILITY_OPTIONS = [
    "Available Now",
    "Available Soon",
    "Currently Working",
    "Unavailable",
]

CURRENCIES = [
    "GBP",
    "EUR",
    "USD",
    "INR",
]

ALLOWED_CV_TYPES = [
    "pdf",
    "doc",
    "docx",
]

MAX_CV_SIZE_MB = 10

# Project root:
# AVERRA_CRM/
#     screens/
#     data/
#
# Path(__file__).resolve().parent = AVERRA_CRM/screens
# .parent = AVERRA_CRM
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CV_FOLDER = PROJECT_ROOT / "data" / "cvs"


# ============================================================
# HELPERS
# ============================================================

def employee_name(employee):
    """Return the employee's full name."""

    if employee is None:
        return "Unknown Employee"

    first_name = (employee.first_name or "").strip()
    last_name = (employee.last_name or "").strip()

    full_name = f"{first_name} {last_name}".strip()

    if full_name:
        return full_name

    return f"Employee {employee.id}"


def clean_text(value):
    """Convert a value to clean text."""

    if value is None:
        return ""

    return str(value).strip()


def valid_email(email):
    """Basic email validation."""

    email = clean_text(email)

    if not email:
        return True

    return (
        "@" in email
        and "." in email.split("@")[-1]
    )


def valid_url(url):
    """Validate a basic HTTP/HTTPS URL."""

    url = clean_text(url)

    if not url:
        return True

    return (
        url.lower().startswith("http://")
        or url.lower().startswith("https://")
    )


def employee_search_text(employee):
    """Build searchable employee text."""

    values = [
        employee.first_name,
        employee.last_name,
        employee.role,
        employee.email,
        employee.phone,
        employee.city,
        employee.country,
        employee.employment_status,
        employee.availability,
        employee.english_level,
    ]

    return " ".join(
        clean_text(value).lower()
        for value in values
        if value
    )


def clear_employee_editing():
    """Clear employee editing state."""

    st.session_state.editing_employee_id = None


def clear_employee_delete_confirmation():
    """Clear employee delete confirmation."""

    st.session_state.confirm_delete_employee_id = None


def ensure_cv_folder():
    """Create the CV storage folder if it does not exist."""

    CV_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )


def safe_filename(value):
    """
    Convert text into a filesystem-safe filename.
    """

    value = clean_text(value)

    if not value:
        return "employee"

    value = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        value,
    )

    value = value.strip("_")

    return value or "employee"


def get_uploaded_cv_path(employee):
    """
    Return the local CV path if employee.cv_link
    points to a stored local CV.
    """

    cv_link = clean_text(employee.cv_link)

    if not cv_link:
        return None

    # Only treat paths beginning with data/cvs/
    # as locally stored CV files.
    if not cv_link.replace("\\", "/").startswith(
        "data/cvs/"
    ):
        return None

    relative_path = Path(
        cv_link.replace("\\", "/")
    )

    full_path = (
        PROJECT_ROOT / relative_path
    ).resolve()

    try:
        full_path.relative_to(
            CV_FOLDER.resolve()
        )
    except ValueError:
        return None

    return full_path


def delete_local_cv(employee):
    """
    Delete an employee's locally stored CV.

    Returns True if a file was deleted,
    False if there was no local CV.
    """

    cv_path = get_uploaded_cv_path(employee)

    if not cv_path:
        return False

    if cv_path.exists() and cv_path.is_file():

        try:
            cv_path.unlink()
            return True

        except OSError:
            return False

    return False


def save_uploaded_cv(
    uploaded_file,
    employee_id,
    first_name,
    last_name,
):
    """
    Save an uploaded CV to data/cvs/.

    Returns:
        relative database path, or None
    """

    if uploaded_file is None:
        return None

    original_name = clean_text(
        uploaded_file.name
    )

    extension = (
        Path(original_name)
        .suffix
        .lower()
        .lstrip(".")
    )

    if extension not in ALLOWED_CV_TYPES:

        raise ValueError(
            "Invalid CV file type. "
            "Please upload PDF, DOC or DOCX."
        )

    file_size = len(
        uploaded_file.getvalue()
    )

    max_size = (
        MAX_CV_SIZE_MB
        * 1024
        * 1024
    )

    if file_size > max_size:

        raise ValueError(
            f"CV file is too large. "
            f"Maximum size is {MAX_CV_SIZE_MB} MB."
        )

    ensure_cv_folder()

    first = safe_filename(
        first_name
    )

    last = safe_filename(
        last_name
    )

    filename = (
        f"employee_{employee_id}_"
        f"{first}_{last}.{extension}"
    )

    destination = CV_FOLDER / filename

    # If an old file with the same generated name
    # exists, replace it.
    with open(
        destination,
        "wb",
    ) as file:

        file.write(
            uploaded_file.getvalue()
        )

    # Store a portable relative path in database.
    relative_path = (
        Path("data")
        / "cvs"
        / filename
    )

    return relative_path.as_posix()


def display_local_cv(employee):
    """
    Display Open and Download controls
    for a locally uploaded CV.
    """

    cv_path = get_uploaded_cv_path(
        employee
    )

    if not cv_path or not cv_path.exists():

        return False

    try:

        with open(
            cv_path,
            "rb",
        ) as file:

            cv_bytes = file.read()

        filename = cv_path.name

        col1, col2 = st.columns(2)

        with col1:

            st.download_button(
                "Download CV",
                data=cv_bytes,
                file_name=filename,
                mime=get_cv_mime_type(
                    cv_path
                ),
                key=(
                    f"download_cv_"
                    f"{employee.id}"
                ),
                use_container_width=True,
            )

        with col2:

            if cv_path.suffix.lower() == ".pdf":

                st.markdown(
                    f"""
                    <a href="data:application/pdf;base64,"
                    target="_blank">
                    </a>
                    """,
                    unsafe_allow_html=True,
                )

                # Streamlit's download button is reliable
                # for the actual file. The PDF can also be
                # opened through the browser using the link
                # below when supported.
                import base64

                encoded = base64.b64encode(
                    cv_bytes
                ).decode("utf-8")

                pdf_link = (
                    f'<a href="data:application/pdf;'
                    f'base64,{encoded}" '
                    f'target="_blank" '
                    f'style="text-decoration:none;">'
                    f'Open CV'
                    f'</a>'
                )

                st.markdown(
                    pdf_link,
                    unsafe_allow_html=True,
                )

            else:

                st.caption(
                    "Use Download CV to open this file."
                )

        return True

    except OSError:

        st.warning(
            "The stored CV file could not be opened."
        )

        return False


def get_cv_mime_type(path):
    """Return MIME type for a CV file."""

    extension = path.suffix.lower()

    if extension == ".pdf":
        return "application/pdf"

    if extension == ".docx":
        return (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )

    if extension == ".doc":
        return "application/msword"

    return "application/octet-stream"


# ============================================================
# MAIN SCREEN
# ============================================================

def show_employees():

    st.title("Employees")

    st.caption(
        "Manage remote workers, availability, experience "
        "and cost information."
    )

    session = get_session()

    try:

        # ========================================================
        # SESSION STATE
        # ========================================================

        if "editing_employee_id" not in st.session_state:

            st.session_state.editing_employee_id = None

        if "confirm_delete_employee_id" not in st.session_state:

            st.session_state.confirm_delete_employee_id = None

        # ========================================================
        # LOAD EMPLOYEES
        # ========================================================

        employees = (
            session.query(Employee)
            .order_by(
                Employee.first_name,
                Employee.last_name,
            )
            .all()
        )

        # ========================================================
        # FIND EMPLOYEE BEING EDITED
        # ========================================================

        editing_employee = None

        if (
            st.session_state.editing_employee_id
            is not None
        ):

            editing_employee = session.get(
                Employee,
                st.session_state.editing_employee_id,
            )

            if editing_employee is None:

                clear_employee_editing()

        # ========================================================
        # KPI OVERVIEW
        # ========================================================

        total_employees = len(employees)

        active_employees = sum(
            1
            for employee in employees
            if employee.employment_status
            != "Former Employee"
        )

        available_employees = sum(
            1
            for employee in employees
            if employee.availability
            in [
                "Available Now",
                "Available Soon",
            ]
        )

        placed_employees = sum(
            1
            for employee in employees
            if employee.employment_status
            == "Placed"
        )

        former_employees = sum(
            1
            for employee in employees
            if employee.employment_status
            == "Former Employee"
        )

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:

            st.metric(
                "Total Employees",
                total_employees,
            )

        with col2:

            st.metric(
                "Active",
                active_employees,
            )

        with col3:

            st.metric(
                "Available",
                available_employees,
            )

        with col4:

            st.metric(
                "Placed",
                placed_employees,
            )

        with col5:

            st.metric(
                "Former",
                former_employees,
            )

        st.divider()

        # ========================================================
        # FORM TITLE
        # ========================================================

        if editing_employee:

            st.subheader(
                "Edit Employee"
            )

        else:

            st.subheader(
                "Add New Employee"
            )

        # ========================================================
        # EMPLOYEE FORM
        # ========================================================

        with st.form(
            "employee_form"
        ):

            # ----------------------------------------------------
            # NAME
            # ----------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                first_name = st.text_input(
                    "First Name",
                    value=(
                        editing_employee.first_name
                        if editing_employee
                        else ""
                    ),
                    placeholder="Example: John",
                )

            with col2:

                last_name = st.text_input(
                    "Last Name",
                    value=(
                        editing_employee.last_name
                        if editing_employee
                        else ""
                    ),
                    placeholder="Example: Smith",
                )

            # ----------------------------------------------------
            # LOCATION
            # ----------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                country = st.text_input(
                    "Country",
                    value=(
                        editing_employee.country
                        if editing_employee
                        else "India"
                    ),
                    placeholder="Example: India",
                )

            with col2:

                city = st.text_input(
                    "City",
                    value=(
                        editing_employee.city
                        if editing_employee
                        else ""
                    ),
                    placeholder="Example: Bangalore",
                )

            # ----------------------------------------------------
            # CONTACT
            # ----------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                email = st.text_input(
                    "Email",
                    value=(
                        editing_employee.email
                        if editing_employee
                        else ""
                    ),
                    placeholder=(
                        "employee@example.com"
                    ),
                )

            with col2:

                phone = st.text_input(
                    "Phone",
                    value=(
                        editing_employee.phone
                        if editing_employee
                        else ""
                    ),
                    placeholder="+91...",
                )

            # ----------------------------------------------------
            # ROLE
            # ----------------------------------------------------

            role = st.text_input(
                "Role / Position",
                value=(
                    editing_employee.role
                    if editing_employee
                    else ""
                ),
                placeholder=(
                    "Example: Finance Analyst"
                ),
            )

            # ----------------------------------------------------
            # EXPERIENCE / ENGLISH
            # ----------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                current_experience = 0.0

                if editing_employee:

                    current_experience = float(
                        editing_employee.years_experience
                        or 0
                    )

                years_experience = (
                    st.number_input(
                        "Years of Experience",
                        min_value=0.0,
                        step=0.5,
                        format="%.1f",
                        value=current_experience,
                    )
                )

            with col2:

                if (
                    editing_employee
                    and editing_employee.english_level
                    in ENGLISH_LEVELS
                ):

                    english_index = (
                        ENGLISH_LEVELS.index(
                            editing_employee.english_level
                        )
                    )

                else:

                    english_index = 0

                english_level = (
                    st.selectbox(
                        "English Level",
                        ENGLISH_LEVELS,
                        index=english_index,
                    )
                )

            # ----------------------------------------------------
            # AVAILABILITY
            # ----------------------------------------------------

            if (
                editing_employee
                and editing_employee.availability
                in AVAILABILITY_OPTIONS
            ):

                availability_index = (
                    AVAILABILITY_OPTIONS.index(
                        editing_employee.availability
                    )
                )

            else:

                availability_index = 0

            availability = st.selectbox(
                "Availability",
                AVAILABILITY_OPTIONS,
                index=availability_index,
            )

            # ----------------------------------------------------
            # EMPLOYMENT STATUS
            # ----------------------------------------------------

            if (
                editing_employee
                and editing_employee.employment_status
                in EMPLOYEE_STATUSES
            ):

                status_index = (
                    EMPLOYEE_STATUSES.index(
                        editing_employee.employment_status
                    )
                )

            else:

                status_index = 0

            employment_status = (
                st.selectbox(
                    "Employment Status",
                    EMPLOYEE_STATUSES,
                    index=status_index,
                )
            )

            # ----------------------------------------------------
            # MONTHLY RATE
            # ----------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                current_rate = 0.0

                if editing_employee:

                    current_rate = float(
                        editing_employee.expected_monthly_rate
                        or 0
                    )

                expected_monthly_rate = (
                    st.number_input(
                        "Expected Monthly Rate",
                        min_value=0.0,
                        step=100.0,
                        format="%.2f",
                        value=current_rate,
                    )
                )

            with col2:

                if (
                    editing_employee
                    and editing_employee.currency
                    in CURRENCIES
                ):

                    currency_index = (
                        CURRENCIES.index(
                            editing_employee.currency
                        )
                    )

                else:

                    currency_index = 0

                currency = st.selectbox(
                    "Currency",
                    CURRENCIES,
                    index=currency_index,
                )

            # ----------------------------------------------------
            # CV / RESUME
            # ----------------------------------------------------

            st.markdown(
                "### CV / Resume"
            )

            if editing_employee:

                existing_local_cv = (
                    get_uploaded_cv_path(
                        editing_employee
                    )
                )

                if (
                    existing_local_cv
                    and existing_local_cv.exists()
                ):

                    st.info(
                        f"Current uploaded CV: "
                        f"{existing_local_cv.name}"
                    )

                elif editing_employee.cv_link:

                    st.info(
                        "An external CV link is currently "
                        "stored for this employee."
                    )

            uploaded_cv = st.file_uploader(
                "Upload CV / Resume",
                type=ALLOWED_CV_TYPES,
                help=(
                    f"Accepted formats: PDF, DOC, DOCX. "
                    f"Maximum file size: "
                    f"{MAX_CV_SIZE_MB} MB."
                ),
            )

            cv_link = st.text_input(
                "External CV / Resume Link",
                value=(
                    editing_employee.cv_link
                    if (
                        editing_employee
                        and not get_uploaded_cv_path(
                            editing_employee
                        )
                    )
                    else ""
                ),
                placeholder=(
                    "https://..."
                ),
            )

            if uploaded_cv:

                st.caption(
                    f"Selected file: "
                    f"{uploaded_cv.name}"
                )

            # ----------------------------------------------------
            # NOTES
            # ----------------------------------------------------

            notes = st.text_area(
                "Notes",
                value=(
                    editing_employee.notes
                    if editing_employee
                    else ""
                ),
                placeholder=(
                    "Additional information about "
                    "the employee..."
                ),
            )

            # ----------------------------------------------------
            # FORM BUTTON
            # ----------------------------------------------------

            submitted = st.form_submit_button(
                (
                    "Save Changes"
                    if editing_employee
                    else "Add Employee"
                ),
                use_container_width=True,
            )

            # ====================================================
            # SAVE FORM
            # ====================================================

            if submitted:

                first_name_clean = (
                    clean_text(first_name)
                )

                last_name_clean = (
                    clean_text(last_name)
                )

                country_clean = (
                    clean_text(country)
                )

                city_clean = (
                    clean_text(city)
                )

                email_clean = (
                    clean_text(email).lower()
                )

                phone_clean = (
                    clean_text(phone)
                )

                role_clean = (
                    clean_text(role)
                )

                cv_link_clean = (
                    clean_text(cv_link)
                )

                notes_clean = (
                    clean_text(notes)
                )

                # ------------------------------------------------
                # VALIDATION
                # ------------------------------------------------

                if not first_name_clean:

                    st.error(
                        "First name is required."
                    )

                elif not role_clean:

                    st.error(
                        "Role / Position is required."
                    )

                elif not valid_email(
                    email_clean
                ):

                    st.error(
                        "Please enter a valid email "
                        "address."
                    )

                elif (
                    not uploaded_cv
                    and cv_link_clean
                    and not valid_url(
                        cv_link_clean
                    )
                ):

                    st.error(
                        "CV / Resume link must start "
                        "with http:// or https://."
                    )

                else:

                    # ============================================
                    # DUPLICATE EMAIL CHECK
                    # ============================================

                    duplicate = None

                    if email_clean:

                        duplicate_query = (
                            session.query(
                                Employee
                            )
                            .filter(
                                Employee.email.ilike(
                                    email_clean
                                )
                            )
                        )

                        if editing_employee:

                            duplicate_query = (
                                duplicate_query.filter(
                                    Employee.id
                                    != editing_employee.id
                                )
                            )

                        duplicate = (
                            duplicate_query.first()
                        )

                    if duplicate:

                        st.error(
                            "Another employee already "
                            "uses this email address."
                        )

                    else:

                        try:

                            # ====================================
                            # UPDATE EMPLOYEE
                            # ====================================

                            if editing_employee:

                                old_cv_path = (
                                    get_uploaded_cv_path(
                                        editing_employee
                                    )
                                )

                                editing_employee.first_name = (
                                    first_name_clean
                                )

                                editing_employee.last_name = (
                                    last_name_clean
                                )

                                editing_employee.country = (
                                    country_clean
                                )

                                editing_employee.city = (
                                    city_clean
                                )

                                editing_employee.email = (
                                    email_clean
                                )

                                editing_employee.phone = (
                                    phone_clean
                                )

                                editing_employee.role = (
                                    role_clean
                                )

                                editing_employee.years_experience = (
                                    years_experience
                                )

                                editing_employee.english_level = (
                                    english_level
                                )

                                editing_employee.availability = (
                                    availability
                                )

                                editing_employee.expected_monthly_rate = (
                                    expected_monthly_rate
                                )

                                editing_employee.currency = (
                                    currency
                                )

                                editing_employee.employment_status = (
                                    employment_status
                                )

                                editing_employee.notes = (
                                    notes_clean
                                )

                                # --------------------------------
                                # CV HANDLING
                                # --------------------------------

                                if uploaded_cv:

                                    new_cv_link = (
                                        save_uploaded_cv(
                                            uploaded_cv,
                                            editing_employee.id,
                                            first_name_clean,
                                            last_name_clean,
                                        )
                                    )

                                    editing_employee.cv_link = (
                                        new_cv_link
                                    )

                                elif cv_link_clean:

                                    editing_employee.cv_link = (
                                        cv_link_clean
                                    )

                                elif (
                                    not uploaded_cv
                                    and not cv_link_clean
                                ):

                                    # Keep an existing local CV
                                    # if the user has not supplied
                                    # a replacement or URL.
                                    if (
                                        not old_cv_path
                                        or not old_cv_path.exists()
                                    ):

                                        editing_employee.cv_link = ""

                                session.commit()

                                # --------------------------------
                                # Remove replaced local CV
                                # --------------------------------

                                if (
                                    uploaded_cv
                                    and old_cv_path
                                    and old_cv_path.exists()
                                ):

                                    try:

                                        if (
                                            old_cv_path
                                            != get_uploaded_cv_path(
                                                editing_employee
                                            )
                                        ):

                                            old_cv_path.unlink()

                                    except OSError:
                                        pass

                                clear_employee_editing()

                                st.success(
                                    "Employee updated "
                                    "successfully."
                                )

                                st.rerun()

                            # ====================================
                            # ADD EMPLOYEE
                            # ====================================

                            else:

                                new_employee = Employee(
                                    first_name=(
                                        first_name_clean
                                    ),
                                    last_name=(
                                        last_name_clean
                                    ),
                                    country=(
                                        country_clean
                                    ),
                                    city=(
                                        city_clean
                                    ),
                                    email=(
                                        email_clean
                                    ),
                                    phone=(
                                        phone_clean
                                    ),
                                    role=(
                                        role_clean
                                    ),
                                    years_experience=(
                                        years_experience
                                    ),
                                    english_level=(
                                        english_level
                                    ),
                                    availability=(
                                        availability
                                    ),
                                    expected_monthly_rate=(
                                        expected_monthly_rate
                                    ),
                                    currency=(
                                        currency
                                    ),
                                    employment_status=(
                                        employment_status
                                    ),
                                    cv_link="",
                                    notes=(
                                        notes_clean
                                    ),
                                )

                                session.add(
                                    new_employee
                                )

                                session.flush()

                                # ----------------------------
                                # CV
                                # ----------------------------

                                if uploaded_cv:

                                    new_cv_link = (
                                        save_uploaded_cv(
                                            uploaded_cv,
                                            new_employee.id,
                                            first_name_clean,
                                            last_name_clean,
                                        )
                                    )

                                    new_employee.cv_link = (
                                        new_cv_link
                                    )

                                elif cv_link_clean:

                                    new_employee.cv_link = (
                                        cv_link_clean
                                    )

                                session.commit()

                                st.success(
                                    "Employee added "
                                    "successfully."
                                )

                                st.rerun()

                        except Exception as error:

                            session.rollback()

                            st.error(
                                "The employee could not "
                                "be saved."
                            )

                            st.exception(
                                error
                            )

        # ========================================================
        # EMPLOYEE REGISTER
        # ========================================================

        st.divider()

        st.subheader(
            "Employee Register"
        )

        if not employees:

            st.info(
                "No employees have been added yet."
            )

            return

        # ========================================================
        # FILTERS
        # ========================================================

        col1, col2, col3 = st.columns(3)

        with col1:

            search = st.text_input(
                "Search Employees",
                placeholder=(
                    "Name, role, email, city "
                    "or country..."
                ),
            )

        with col2:

            status_filter = st.selectbox(
                "Employment Status",
                ["All"] + EMPLOYEE_STATUSES,
            )

        with col3:

            availability_filter = (
                st.selectbox(
                    "Availability",
                    ["All"] + AVAILABILITY_OPTIONS,
                )
            )

        filtered = employees

        # ========================================================
        # SEARCH FILTER
        # ========================================================

        if search.strip():

            search_lower = (
                search.strip().lower()
            )

            filtered = [
                employee
                for employee in filtered
                if search_lower
                in employee_search_text(
                    employee
                )
            ]

        # ========================================================
        # STATUS FILTER
        # ========================================================

        if status_filter != "All":

            filtered = [
                employee
                for employee in filtered
                if employee.employment_status
                == status_filter
            ]

        # ========================================================
        # AVAILABILITY FILTER
        # ========================================================

        if availability_filter != "All":

            filtered = [
                employee
                for employee in filtered
                if employee.availability
                == availability_filter
            ]

        # ========================================================
        # RESULT COUNT
        # ========================================================

        st.write(
            f"**{len(filtered)} employee(s) found**"
        )

        if not filtered:

            st.info(
                "No employees match the "
                "selected filters."
            )

        # ========================================================
        # EMPLOYEE CARDS
        # ========================================================

        for employee in filtered:

            full_name = employee_name(
                employee
            )

            with st.container(
                border=True
            ):

                col1, col2, col3 = (
                    st.columns(
                        [3, 2, 1]
                    )
                )

                # ------------------------------------------------
                # EMPLOYEE INFORMATION
                # ------------------------------------------------

                with col1:

                    st.subheader(
                        full_name
                    )

                    if employee.role:

                        st.caption(
                            employee.role
                        )

                    if employee.email:

                        st.write(
                            f"Email: "
                            f"{employee.email}"
                        )

                    if employee.phone:

                        st.write(
                            f"Phone: "
                            f"{employee.phone}"
                        )

                    location_parts = []

                    if employee.city:

                        location_parts.append(
                            employee.city
                        )

                    if employee.country:

                        location_parts.append(
                            employee.country
                        )

                    if location_parts:

                        st.caption(
                            "Location: "
                            + ", ".join(
                                location_parts
                            )
                        )

                # ------------------------------------------------
                # EMPLOYEE DETAILS
                # ------------------------------------------------

                with col2:

                    st.write(
                        f"**Status:** "
                        f"{employee.employment_status or 'Not specified'}"
                    )

                    st.write(
                        f"**Availability:** "
                        f"{employee.availability or 'Not specified'}"
                    )

                    experience = (
                        employee.years_experience
                        or 0
                    )

                    st.write(
                        f"**Experience:** "
                        f"{experience:g} years"
                    )

                    st.write(
                        f"**English:** "
                        f"{employee.english_level or 'Not specified'}"
                    )

                    rate = (
                        employee.expected_monthly_rate
                        or 0
                    )

                    currency_display = (
                        employee.currency
                        or "GBP"
                    )

                    st.write(
                        f"**Expected Rate:** "
                        f"{currency_display} "
                        f"{rate:,.2f}/month"
                    )

                # ------------------------------------------------
                # ACTIONS
                # ------------------------------------------------

                with col3:

                    edit_btn = st.button(
                        "Edit",
                        key=(
                            f"edit_employee_"
                            f"{employee.id}"
                        ),
                        use_container_width=True,
                    )

                    delete_btn = st.button(
                        "Delete",
                        key=(
                            f"delete_employee_"
                            f"{employee.id}"
                        ),
                        use_container_width=True,
                    )

                # =================================================
                # EDIT
                # =================================================

                if edit_btn:

                    st.session_state.editing_employee_id = (
                        employee.id
                    )

                    clear_employee_delete_confirmation()

                    st.rerun()

                # =================================================
                # DELETE REQUEST
                # =================================================

                if delete_btn:

                    st.session_state.confirm_delete_employee_id = (
                        employee.id
                    )

                    clear_employee_editing()

                    st.rerun()

                # =================================================
                # DELETE CONFIRMATION
                # =================================================

                if (
                    st.session_state
                    .confirm_delete_employee_id
                    == employee.id
                ):

                    st.warning(
                        f"Are you sure you want to "
                        f"delete **{full_name}**?"
                    )

                    st.caption(
                        "Employees with related CRM "
                        "records should normally be "
                        "marked as 'Former Employee' "
                        "instead of deleted."
                    )

                    c1, c2 = st.columns(2)

                    with c1:

                        confirm = st.button(
                            "Yes, Delete Employee",
                            key=(
                                f"confirm_delete_employee_"
                                f"{employee.id}"
                            ),
                            type="primary",
                            use_container_width=True,
                        )

                    with c2:

                        cancel = st.button(
                            "Cancel",
                            key=(
                                f"cancel_delete_employee_"
                                f"{employee.id}"
                            ),
                            use_container_width=True,
                        )

                    if cancel:

                        clear_employee_delete_confirmation()

                        st.rerun()

                    if confirm:

                        try:

                            # ------------------------------------
                            # CHECK RELATED RECORDS
                            # ------------------------------------

                            related_records = []

                            candidates = getattr(
                                employee,
                                "candidates",
                                None,
                            )

                            placements = getattr(
                                employee,
                                "placements",
                                None,
                            )

                            activities = getattr(
                                employee,
                                "activities",
                                None,
                            )

                            skills = getattr(
                                employee,
                                "skills",
                                None,
                            )

                            if candidates:

                                related_records.append(
                                    "candidates"
                                )

                            if placements:

                                related_records.append(
                                    "placements"
                                )

                            if activities:

                                related_records.append(
                                    "activities"
                                )

                            if skills:

                                related_records.append(
                                    "skills"
                                )

                            if related_records:

                                st.error(
                                    "This employee "
                                    "cannot be deleted "
                                    "because related "
                                    "CRM records exist."
                                )

                                st.info(
                                    "Related records: "
                                    + ", ".join(
                                        related_records
                                    )
                                    + ". Mark the "
                                    "employee as "
                                    "'Former Employee' "
                                    "instead."
                                )

                                clear_employee_delete_confirmation()

                            else:

                                # ----------------------------
                                # Delete local CV first
                                # ----------------------------

                                delete_local_cv(
                                    employee
                                )

                                session.delete(
                                    employee
                                )

                                session.commit()

                                clear_employee_delete_confirmation()

                                st.success(
                                    "Employee deleted "
                                    "successfully."
                                )

                                st.rerun()

                        except Exception as error:

                            session.rollback()

                            st.error(
                                "The employee could "
                                "not be deleted."
                            )

                            st.exception(
                                error
                            )

                # =================================================
                # CV
                # =================================================

                if employee.cv_link:

                    local_cv_path = (
                        get_uploaded_cv_path(
                            employee
                        )
                    )

                    if (
                        local_cv_path
                        and local_cv_path.exists()
                    ):

                        st.markdown(
                            "**CV / Resume**"
                        )

                        display_local_cv(
                            employee
                        )

                    else:

                        st.markdown(
                            f"[Open CV / Resume]"
                            f"({employee.cv_link})"
                        )

                # =================================================
                # NOTES
                # =================================================

                if employee.notes:

                    st.caption(
                        f"Notes: "
                        f"{employee.notes}"
                    )

    except Exception as error:

        session.rollback()

        st.error(
            "An error occurred while "
            "loading the Employees screen."
        )

        st.exception(
            error
        )

    finally:

        session.close()