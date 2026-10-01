import base64
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

PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

CV_FOLDER = (
    PROJECT_ROOT
    / "data"
    / "cvs"
)


# ============================================================
# HELPERS
# ============================================================

def employee_name(employee):
    """Return an employee's full name safely."""

    if employee is None:
        return "Unknown Employee"

    first_name = clean_text(
        getattr(
            employee,
            "first_name",
            "",
        )
    )

    last_name = clean_text(
        getattr(
            employee,
            "last_name",
            "",
        )
    )

    full_name = (
        f"{first_name} {last_name}"
    ).strip()

    if full_name:
        return full_name

    employee_id = getattr(
        employee,
        "id",
        None,
    )

    if employee_id is not None:
        return f"Employee {employee_id}"

    return "Unknown Employee"


def clean_text(value):
    """Convert a value into cleaned text."""

    if value is None:
        return ""

    return str(value).strip()


def normalize_text(value):
    """
    Normalize text for searching and
    duplicate comparisons.
    """

    return " ".join(
        clean_text(value)
        .lower()
        .split()
    )


def normalize_email(email):
    """Normalize an email address."""

    return clean_text(
        email
    ).lower()


def valid_email(email):
    """Perform basic email validation."""

    email = normalize_email(
        email
    )

    if not email:
        return True

    if len(email) > 254:
        return False

    if email.count("@") != 1:
        return False

    local_part, domain = (
        email.split("@")
    )

    if not local_part or not domain:
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


def valid_url(url):
    """Validate a basic HTTP/HTTPS URL."""

    url = clean_text(url)

    if not url:
        return True

    return (
        url.lower().startswith(
            "http://"
        )
        or url.lower().startswith(
            "https://"
        )
    )


def employee_search_text(employee):
    """Build normalized searchable employee text."""

    if employee is None:
        return ""

    values = [
        getattr(
            employee,
            "first_name",
            "",
        ),
        getattr(
            employee,
            "last_name",
            "",
        ),
        getattr(
            employee,
            "role",
            "",
        ),
        getattr(
            employee,
            "email",
            "",
        ),
        getattr(
            employee,
            "phone",
            "",
        ),
        getattr(
            employee,
            "city",
            "",
        ),
        getattr(
            employee,
            "country",
            "",
        ),
        getattr(
            employee,
            "employment_status",
            "",
        ),
        getattr(
            employee,
            "availability",
            "",
        ),
        getattr(
            employee,
            "english_level",
            "",
        ),
        getattr(
            employee,
            "notes",
            "",
        ),
    ]

    return normalize_text(
        " ".join(
            clean_text(value)
            for value in values
            if value
        )
    )


def clear_employee_editing():
    """Clear employee editing state."""

    st.session_state[
        "editing_employee_id"
    ] = None


def clear_employee_delete_confirmation():
    """Clear employee delete confirmation."""

    st.session_state[
        "confirm_delete_employee_id"
    ] = None


def reset_employee_states():
    """Clear all employee UI states."""

    clear_employee_editing()
    clear_employee_delete_confirmation()


def ensure_cv_folder():
    """Create the CV folder when required."""

    CV_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )


def safe_filename(value):
    """Convert text into a filesystem-safe filename."""

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
    Return a validated local CV path.

    Only paths under data/cvs/ are accepted.
    """

    if employee is None:
        return None

    cv_link = clean_text(
        getattr(
            employee,
            "cv_link",
            "",
        )
    )

    if not cv_link:
        return None

    normalized = (
        cv_link
        .replace("\\", "/")
    )

    if not normalized.startswith(
        "data/cvs/"
    ):
        return None

    relative_path = Path(
        normalized
    )

    full_path = (
        PROJECT_ROOT
        / relative_path
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

    Returns True if a file was deleted.
    """

    cv_path = get_uploaded_cv_path(
        employee
    )

    if not cv_path:
        return False

    if not cv_path.exists():
        return False

    if not cv_path.is_file():
        return False

    try:

        cv_path.unlink()

        return True

    except OSError:

        return False


def save_uploaded_cv(
    uploaded_file,
    employee_id,
    first_name,
    last_name,
):
    """
    Save an uploaded CV.

    Returns a portable database path.
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

    file_bytes = (
        uploaded_file.getvalue()
    )

    file_size = len(
        file_bytes
    )

    max_size = (
        MAX_CV_SIZE_MB
        * 1024
        * 1024
    )

    if file_size > max_size:

        raise ValueError(
            f"CV file is too large. "
            f"Maximum size is "
            f"{MAX_CV_SIZE_MB} MB."
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

    destination = (
        CV_FOLDER / filename
    )

    with open(
        destination,
        "wb",
    ) as file:

        file.write(
            file_bytes
        )

    relative_path = (
        Path("data")
        / "cvs"
        / filename
    )

    return relative_path.as_posix()


def get_cv_mime_type(path):
    """Return MIME type for a CV file."""

    extension = (
        path.suffix.lower()
    )

    if extension == ".pdf":
        return "application/pdf"

    if extension == ".docx":

        return (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )

    if extension == ".doc":
        return "application/msword"

    return (
        "application/octet-stream"
    )


def display_local_cv(employee):
    """Display download/open controls for a local CV."""

    cv_path = get_uploaded_cv_path(
        employee
    )

    if (
        not cv_path
        or not cv_path.exists()
        or not cv_path.is_file()
    ):

        return False

    try:

        with open(
            cv_path,
            "rb",
        ) as file:

            cv_bytes = file.read()

        filename = cv_path.name

        col1, col2 = (
            st.columns(2)
        )

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

            if (
                cv_path.suffix.lower()
                == ".pdf"
            ):

                encoded = (
                    base64.b64encode(
                        cv_bytes
                    ).decode(
                        "utf-8"
                    )
                )

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
                    "Use Download CV "
                    "to open this file."
                )

        return True

    except OSError:

        st.warning(
            "The stored CV file "
            "could not be opened."
        )

        return False


def get_employee_experience(employee):
    """Safely return years of experience."""

    try:

        value = float(
            getattr(
                employee,
                "years_experience",
                0,
            )
            or 0
        )

        return max(
            value,
            0.0,
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0.0


def get_employee_rate(employee):
    """Safely return expected monthly rate."""

    try:

        value = float(
            getattr(
                employee,
                "expected_monthly_rate",
                0,
            )
            or 0
        )

        return max(
            value,
            0.0,
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0.0


def validate_employee_form(
    first_name,
    role,
    email,
    years_experience,
    expected_monthly_rate,
):
    """Validate employee form values."""

    first_name = clean_text(
        first_name
    )

    role = clean_text(
        role
    )

    email = normalize_email(
        email
    )

    if not first_name:

        return (
            False,
            "First name is required.",
        )

    if len(first_name) > 100:

        return (
            False,
            "First name is too long.",
        )

    if len(
        clean_text(role)
    ) > 150:

        return (
            False,
            "Role / Position is too long.",
        )

    if not role:

        return (
            False,
            "Role / Position is required.",
        )

    if not valid_email(email):

        return (
            False,
            "Please enter a valid email address.",
        )

    try:

        experience = float(
            years_experience
        )

    except (
        TypeError,
        ValueError,
    ):

        return (
            False,
            "Years of experience must "
            "be a valid number.",
        )

    if experience < 0:

        return (
            False,
            "Years of experience cannot "
            "be negative.",
        )

    if experience > 100:

        return (
            False,
            "Years of experience cannot "
            "exceed 100 years.",
        )

    try:

        rate = float(
            expected_monthly_rate
        )

    except (
        TypeError,
        ValueError,
    ):

        return (
            False,
            "Expected monthly rate must "
            "be a valid number.",
        )

    if rate < 0:

        return (
            False,
            "Expected monthly rate cannot "
            "be negative.",
        )

    return (
        True,
        "",
    )


def find_duplicate_email(
    session,
    email,
    exclude_id=None,
):
    """
    Find another employee using the same email.

    Comparison is case-insensitive.
    """

    email = normalize_email(
        email
    )

    if not email:
        return None

    employees = (
        session.query(Employee)
        .all()
    )

    for employee in employees:

        if (
            exclude_id is not None
            and employee.id
            == exclude_id
        ):
            continue

        existing_email = (
            normalize_email(
                getattr(
                    employee,
                    "email",
                    "",
                )
            )
        )

        if (
            existing_email
            and existing_email
            == email
        ):

            return employee

    return None


def get_related_records(employee):
    """
    Safely identify related CRM records.

    Supports the relationship names currently
    used by the CRM.
    """

    related = []

    relationship_names = [
        (
            "candidates",
            "Candidates",
        ),
        (
            "placements",
            "Placements",
        ),
        (
            "activities",
            "Activities",
        ),
        (
            "skills",
            "Skills",
        ),
        (
            "employee_skills",
            "Skills",
        ),
    ]

    seen_labels = set()

    for attribute, label in (
        relationship_names
    ):

        try:

            records = getattr(
                employee,
                attribute,
                None,
            )

            if records and label not in seen_labels:

                related.append(
                    label
                )

                seen_labels.add(
                    label
                )

        except Exception:

            continue

    return related


# ============================================================
# MAIN SCREEN
# ============================================================

def show_employees():

    st.title("Employees")

    st.caption(
        "Manage remote workers, availability, "
        "experience and cost information."
    )

    session = get_session()

    try:

        # ========================================================
        # SESSION STATE
        # ========================================================

        if (
            "editing_employee_id"
            not in st.session_state
        ):

            st.session_state[
                "editing_employee_id"
            ] = None

        if (
            "confirm_delete_employee_id"
            not in st.session_state
        ):

            st.session_state[
                "confirm_delete_employee_id"
            ] = None

        # ========================================================
        # LOAD EMPLOYEES
        # ========================================================

        employees = (
            session.query(Employee)
            .order_by(
                Employee.first_name.asc(),
                Employee.last_name.asc(),
                Employee.id.asc(),
            )
            .all()
        )

        # ========================================================
        # CURRENT EDITING EMPLOYEE
        # ========================================================

        editing_employee = None

        editing_employee_id = (
            st.session_state[
                "editing_employee_id"
            ]
        )

        if editing_employee_id is not None:

            editing_employee = session.get(
                Employee,
                editing_employee_id,
            )

            if editing_employee is None:

                clear_employee_editing()

        # ========================================================
        # KPI CALCULATIONS
        # ========================================================

        total_employees = len(
            employees
        )

        active_employees = sum(
            1
            for employee in employees
            if clean_text(
                employee.employment_status
            )
            != "Former Employee"
        )

        available_now = sum(
            1
            for employee in employees
            if clean_text(
                employee.availability
            )
            == "Available Now"
        )

        available_soon = sum(
            1
            for employee in employees
            if clean_text(
                employee.availability
            )
            == "Available Soon"
        )

        available_employees = (
            available_now
            + available_soon
        )

        placed_employees = sum(
            1
            for employee in employees
            if clean_text(
                employee.employment_status
            )
            == "Placed"
        )

        interviewing_employees = sum(
            1
            for employee in employees
            if clean_text(
                employee.employment_status
            )
            == "Interviewing"
        )

        former_employees = sum(
            1
            for employee in employees
            if clean_text(
                employee.employment_status
            )
            == "Former Employee"
        )

        cv_count = sum(
            1
            for employee in employees
            if clean_text(
                getattr(
                    employee,
                    "cv_link",
                    "",
                )
            )
        )

        average_experience = (
            (
                sum(
                    get_employee_experience(
                        employee
                    )
                    for employee in employees
                )
                / total_employees
            )
            if total_employees
            else 0
        )

        # ========================================================
        # KPI DISPLAY
        # ========================================================

        col1, col2, col3, col4, col5 = (
            st.columns(5)
        )

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

        # ========================================================
        # SECONDARY METRICS
        # ========================================================

        if employees:

            metric_col1, metric_col2, metric_col3, metric_col4 = (
                st.columns(4)
            )

            with metric_col1:

                st.caption(
                    f"Available now: "
                    f"**{available_now}**"
                )

            with metric_col2:

                st.caption(
                    f"Available soon: "
                    f"**{available_soon}**"
                )

            with metric_col3:

                st.caption(
                    f"Interviewing: "
                    f"**{interviewing_employees}**"
                )

            with metric_col4:

                st.caption(
                    f"CVs recorded: "
                    f"**{cv_count}**"
                )

            st.caption(
                f"Average experience: "
                f"**{average_experience:.1f} years**"
            )

        st.divider()

        # ========================================================
        # FORM TITLE
        # ========================================================

        if editing_employee:

            st.subheader(
                "Edit Employee"
            )

            st.caption(
                f"Editing employee ID "
                f"{editing_employee.id}"
            )

        else:

            st.subheader(
                "Add New Employee"
            )

        # ========================================================
        # EMPLOYEE FORM
        # ========================================================

        with st.form(
            "employee_form",
            clear_on_submit=False,
        ):

            # ====================================================
            # NAME
            # ====================================================

            col1, col2 = (
                st.columns(2)
            )

            with col1:

                first_name = st.text_input(
                    "First Name",
                    value=(
                        clean_text(
                            editing_employee.first_name
                        )
                        if editing_employee
                        else ""
                    ),
                    placeholder="Example: John",
                )

            with col2:

                last_name = st.text_input(
                    "Last Name",
                    value=(
                        clean_text(
                            editing_employee.last_name
                        )
                        if editing_employee
                        else ""
                    ),
                    placeholder="Example: Smith",
                )

            # ====================================================
            # LOCATION
            # ====================================================

            col1, col2 = (
                st.columns(2)
            )

            with col1:

                country = st.text_input(
                    "Country",
                    value=(
                        clean_text(
                            editing_employee.country
                        )
                        if editing_employee
                        else "India"
                    ),
                    placeholder="Example: India",
                )

            with col2:

                city = st.text_input(
                    "City",
                    value=(
                        clean_text(
                            editing_employee.city
                        )
                        if editing_employee
                        else ""
                    ),
                    placeholder="Example: Bangalore",
                )

            # ====================================================
            # CONTACT
            # ====================================================

            col1, col2 = (
                st.columns(2)
            )

            with col1:

                email = st.text_input(
                    "Email",
                    value=(
                        clean_text(
                            editing_employee.email
                        )
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
                        clean_text(
                            editing_employee.phone
                        )
                        if editing_employee
                        else ""
                    ),
                    placeholder="+91...",
                )

            # ====================================================
            # ROLE
            # ====================================================

            role = st.text_input(
                "Role / Position",
                value=(
                    clean_text(
                        editing_employee.role
                    )
                    if editing_employee
                    else ""
                ),
                placeholder=(
                    "Example: Finance Analyst"
                ),
            )

            # ====================================================
            # EXPERIENCE / ENGLISH
            # ====================================================

            col1, col2 = (
                st.columns(2)
            )

            with col1:

                current_experience = (
                    get_employee_experience(
                        editing_employee
                    )
                    if editing_employee
                    else 0.0
                )

                years_experience = (
                    st.number_input(
                        "Years of Experience",
                        min_value=0.0,
                        max_value=100.0,
                        step=0.5,
                        format="%.1f",
                        value=current_experience,
                    )
                )

            with col2:

                current_english = (
                    clean_text(
                        editing_employee.english_level
                    )
                    if editing_employee
                    else ""
                )

                if (
                    current_english
                    in ENGLISH_LEVELS
                ):

                    english_index = (
                        ENGLISH_LEVELS.index(
                            current_english
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

            # ====================================================
            # AVAILABILITY
            # ====================================================

            current_availability = (
                clean_text(
                    editing_employee.availability
                )
                if editing_employee
                else ""
            )

            if (
                current_availability
                in AVAILABILITY_OPTIONS
            ):

                availability_index = (
                    AVAILABILITY_OPTIONS.index(
                        current_availability
                    )
                )

            else:

                availability_index = 0

            availability = st.selectbox(
                "Availability",
                AVAILABILITY_OPTIONS,
                index=availability_index,
            )

            # ====================================================
            # EMPLOYMENT STATUS
            # ====================================================

            current_status = (
                clean_text(
                    editing_employee.employment_status
                )
                if editing_employee
                else ""
            )

            if (
                current_status
                in EMPLOYEE_STATUSES
            ):

                status_index = (
                    EMPLOYEE_STATUSES.index(
                        current_status
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

            # ====================================================
            # MONTHLY RATE
            # ====================================================

            col1, col2 = (
                st.columns(2)
            )

            with col1:

                current_rate = (
                    get_employee_rate(
                        editing_employee
                    )
                    if editing_employee
                    else 0.0
                )

                expected_monthly_rate = (
                    st.number_input(
                        "Expected Monthly Rate",
                        min_value=0.0,
                        max_value=100000000.0,
                        step=100.0,
                        format="%.2f",
                        value=current_rate,
                    )
                )

            with col2:

                current_currency = (
                    clean_text(
                        editing_employee.currency
                    )
                    if editing_employee
                    else ""
                )

                if (
                    current_currency
                    in CURRENCIES
                ):

                    currency_index = (
                        CURRENCIES.index(
                            current_currency
                        )
                    )

                else:

                    currency_index = 0

                currency = st.selectbox(
                    "Currency",
                    CURRENCIES,
                    index=currency_index,
                )

            # ====================================================
            # CV / RESUME
            # ====================================================

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

                elif clean_text(
                    editing_employee.cv_link
                ):

                    st.info(
                        "An external CV link is "
                        "currently stored."
                    )

            uploaded_cv = (
                st.file_uploader(
                    "Upload CV / Resume",
                    type=ALLOWED_CV_TYPES,
                    help=(
                        f"Accepted formats: "
                        f"PDF, DOC, DOCX. "
                        f"Maximum size: "
                        f"{MAX_CV_SIZE_MB} MB."
                    ),
                )
            )

            existing_cv_is_local = (
                bool(
                    editing_employee
                    and get_uploaded_cv_path(
                        editing_employee
                    )
                )
            )

            existing_external_link = ""

            if (
                editing_employee
                and not existing_cv_is_local
            ):

                existing_external_link = (
                    clean_text(
                        editing_employee.cv_link
                    )
                )

            cv_link = st.text_input(
                "External CV / Resume Link",
                value=existing_external_link,
                placeholder="https://...",
                help=(
                    "Use this only when the CV "
                    "is hosted externally."
                ),
            )

            if uploaded_cv:

                st.caption(
                    f"Selected file: "
                    f"{uploaded_cv.name}"
                )

            # ====================================================
            # NOTES
            # ====================================================

            notes = st.text_area(
                "Notes",
                value=(
                    clean_text(
                        editing_employee.notes
                    )
                    if editing_employee
                    else ""
                ),
                placeholder=(
                    "Additional information "
                    "about the employee..."
                ),
            )

            # ====================================================
            # BUTTONS
            # ====================================================

            button_col1, button_col2 = (
                st.columns(2)
            )

            with button_col1:

                submitted = (
                    st.form_submit_button(
                        (
                            "Save Changes"
                            if editing_employee
                            else "Add Employee"
                        ),
                        type="primary",
                        use_container_width=True,
                    )
                )

            with button_col2:

                cancel_edit = False

                if editing_employee:

                    cancel_edit = (
                        st.form_submit_button(
                            "Cancel",
                            use_container_width=True,
                        )
                    )

            # ====================================================
            # CANCEL
            # ====================================================

            if cancel_edit:

                reset_employee_states()

                st.rerun()

            # ====================================================
            # SAVE
            # ====================================================

            if submitted:

                first_name_clean = (
                    clean_text(
                        first_name
                    )
                )

                last_name_clean = (
                    clean_text(
                        last_name
                    )
                )

                country_clean = (
                    clean_text(
                        country
                    )
                )

                city_clean = (
                    clean_text(
                        city
                    )
                )

                email_clean = (
                    normalize_email(
                        email
                    )
                )

                phone_clean = (
                    clean_text(
                        phone
                    )
                )

                role_clean = (
                    clean_text(
                        role
                    )
                )

                cv_link_clean = (
                    clean_text(
                        cv_link
                    )
                )

                notes_clean = (
                    clean_text(
                        notes
                    )
                )

                # ===============================================
                # FORM VALIDATION
                # ===============================================

                form_valid, form_error = (
                    validate_employee_form(
                        first_name_clean,
                        role_clean,
                        email_clean,
                        years_experience,
                        expected_monthly_rate,
                    )
                )

                if not form_valid:

                    st.error(
                        form_error
                    )

                elif (
                    last_name_clean
                    and len(last_name_clean)
                    > 100
                ):

                    st.error(
                        "Last name is too long."
                    )

                elif (
                    country_clean
                    and len(country_clean)
                    > 100
                ):

                    st.error(
                        "Country name is too long."
                    )

                elif (
                    city_clean
                    and len(city_clean)
                    > 100
                ):

                    st.error(
                        "City name is too long."
                    )

                elif (
                    email_clean
                    and len(email_clean)
                    > 254
                ):

                    st.error(
                        "Email address is too long."
                    )

                elif (
                    phone_clean
                    and len(phone_clean)
                    > 50
                ):

                    st.error(
                        "Phone number is too long."
                    )

                elif (
                    cv_link_clean
                    and not uploaded_cv
                    and not valid_url(
                        cv_link_clean
                    )
                ):

                    st.error(
                        "CV / Resume link must "
                        "start with http:// "
                        "or https://."
                    )

                elif (
                    len(notes_clean)
                    > 5000
                ):

                    st.error(
                        "Notes are too long. "
                        "Please use 5,000 characters "
                        "or fewer."
                    )

                elif (
                    uploaded_cv
                    and clean_text(
                        cv_link_clean
                    )
                ):

                    st.error(
                        "Please use either an uploaded "
                        "CV or an external CV link, "
                        "not both."
                    )

                else:

                    # ===========================================
                    # DUPLICATE EMAIL CHECK
                    # ===========================================

                    duplicate = (
                        find_duplicate_email(
                            session,
                            email_clean,
                            exclude_id=(
                                editing_employee.id
                                if editing_employee
                                else None
                            ),
                        )
                    )

                    if duplicate:

                        st.error(
                            "Another employee already "
                            "uses this email address."
                        )

                    else:

                        try:

                            # ===================================
                            # UPDATE
                            # ===================================

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
                                    float(
                                        years_experience
                                    )
                                )

                                editing_employee.english_level = (
                                    english_level
                                )

                                editing_employee.availability = (
                                    availability
                                )

                                editing_employee.expected_monthly_rate = (
                                    float(
                                        expected_monthly_rate
                                    )
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

                                # -------------------------------
                                # CV REPLACEMENT
                                # -------------------------------

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
                                    old_cv_path
                                    and old_cv_path.exists()
                                ):

                                    # Keep existing local CV.
                                    editing_employee.cv_link = (
                                        editing_employee.cv_link
                                    )

                                else:

                                    editing_employee.cv_link = ""

                                session.commit()

                                # --------------------------------
                                # Remove obsolete local CV
                                # --------------------------------

                                if (
                                    uploaded_cv
                                    and old_cv_path
                                    and old_cv_path.exists()
                                ):

                                    new_cv_path = (
                                        get_uploaded_cv_path(
                                            editing_employee
                                        )
                                    )

                                    try:

                                        if (
                                            new_cv_path
                                            and old_cv_path.resolve()
                                            != new_cv_path.resolve()
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

                            # ===================================
                            # CREATE
                            # ===================================

                            else:

                                new_employee = (
                                    Employee(
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
                                            float(
                                                years_experience
                                            )
                                        ),
                                        english_level=(
                                            english_level
                                        ),
                                        availability=(
                                            availability
                                        ),
                                        expected_monthly_rate=(
                                            float(
                                                expected_monthly_rate
                                            )
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
                                )

                                session.add(
                                    new_employee
                                )

                                session.flush()

                                # -------------------------------
                                # SAVE CV
                                # -------------------------------

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

                        except ValueError as error:

                            session.rollback()

                            st.error(
                                str(error)
                            )

                        except Exception:

                            session.rollback()

                            st.error(
                                "The employee could "
                                "not be saved. "
                                "Please check the "
                                "information and try again."
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
                "No employees have "
                "been added yet."
            )

            return

        # ========================================================
        # FILTERS
        # ========================================================

        col1, col2, col3, col4 = (
            st.columns(4)
        )

        with col1:

            search = st.text_input(
                "Search Employees",
                placeholder=(
                    "Name, role, email, "
                    "city or country..."
                ),
            )

        with col2:

            status_filter = (
                st.selectbox(
                    "Employment Status",
                    ["All"]
                    + EMPLOYEE_STATUSES,
                )
            )

        with col3:

            availability_filter = (
                st.selectbox(
                    "Availability",
                    ["All"]
                    + AVAILABILITY_OPTIONS,
                )
            )

        with col4:

            english_filter = (
                st.selectbox(
                    "English Level",
                    ["All"]
                    + ENGLISH_LEVELS,
                )
            )

        # ========================================================
        # EXPERIENCE FILTER
        # ========================================================

        experience_filter = (
            st.selectbox(
                "Experience",
                [
                    "All",
                    "Under 2 Years",
                    "2+ Years",
                    "5+ Years",
                    "10+ Years",
                    "15+ Years",
                ],
            )
        )

        # ========================================================
        # CV FILTER
        # ========================================================

        cv_filter = (
            st.selectbox(
                "CV / Resume",
                [
                    "All",
                    "CV Available",
                    "No CV",
                ],
            )
        )

        # ========================================================
        # SORT
        # ========================================================

        sort_option = (
            st.selectbox(
                "Sort Employees",
                [
                    "Name A-Z",
                    "Name Z-A",
                    "Experience High-Low",
                    "Experience Low-High",
                    "Rate High-Low",
                    "Rate Low-High",
                ],
            )
        )

        # ========================================================
        # FILTER DATA
        # ========================================================

        filtered = list(
            employees
        )

        # ========================================================
        # SEARCH
        # ========================================================

        if search.strip():

            search_text = (
                normalize_text(
                    search
                )
            )

            filtered = [
                employee
                for employee in filtered
                if search_text
                in employee_search_text(
                    employee
                )
            ]

        # ========================================================
        # STATUS
        # ========================================================

        if status_filter != "All":

            filtered = [
                employee
                for employee in filtered
                if clean_text(
                    employee.employment_status
                )
                == status_filter
            ]

        # ========================================================
        # AVAILABILITY
        # ========================================================

        if availability_filter != "All":

            filtered = [
                employee
                for employee in filtered
                if clean_text(
                    employee.availability
                )
                == availability_filter
            ]

        # ========================================================
        # ENGLISH
        # ========================================================

        if english_filter != "All":

            filtered = [
                employee
                for employee in filtered
                if clean_text(
                    employee.english_level
                )
                == english_filter
            ]

        # ========================================================
        # EXPERIENCE
        # ========================================================

        if (
            experience_filter
            != "All"
        ):

            if (
                experience_filter
                == "Under 2 Years"
            ):

                filtered = [
                    employee
                    for employee in filtered
                    if get_employee_experience(
                        employee
                    )
                    < 2
                ]

            elif (
                experience_filter
                == "2+ Years"
            ):

                filtered = [
                    employee
                    for employee in filtered
                    if get_employee_experience(
                        employee
                    )
                    >= 2
                ]

            elif (
                experience_filter
                == "5+ Years"
            ):

                filtered = [
                    employee
                    for employee in filtered
                    if get_employee_experience(
                        employee
                    )
                    >= 5
                ]

            elif (
                experience_filter
                == "10+ Years"
            ):

                filtered = [
                    employee
                    for employee in filtered
                    if get_employee_experience(
                        employee
                    )
                    >= 10
                ]

            elif (
                experience_filter
                == "15+ Years"
            ):

                filtered = [
                    employee
                    for employee in filtered
                    if get_employee_experience(
                        employee
                    )
                    >= 15
                ]

        # ========================================================
        # CV FILTER
        # ========================================================

        if cv_filter == "CV Available":

            filtered = [
                employee
                for employee in filtered
                if clean_text(
                    getattr(
                        employee,
                        "cv_link",
                        "",
                    )
                )
            ]

        elif cv_filter == "No CV":

            filtered = [
                employee
                for employee in filtered
                if not clean_text(
                    getattr(
                        employee,
                        "cv_link",
                        "",
                    )
                )
            ]

        # ========================================================
        # SORT
        # ========================================================

        if sort_option == "Name A-Z":

            filtered.sort(
                key=lambda employee:
                employee_name(
                    employee
                ).lower()
            )

        elif sort_option == "Name Z-A":

            filtered.sort(
                key=lambda employee:
                employee_name(
                    employee
                ).lower(),
                reverse=True,
            )

        elif (
            sort_option
            == "Experience High-Low"
        ):

            filtered.sort(
                key=get_employee_experience,
                reverse=True,
            )

        elif (
            sort_option
            == "Experience Low-High"
        ):

            filtered.sort(
                key=get_employee_experience
            )

        elif (
            sort_option
            == "Rate High-Low"
        ):

            filtered.sort(
                key=get_employee_rate,
                reverse=True,
            )

        elif (
            sort_option
            == "Rate Low-High"
        ):

            filtered.sort(
                key=get_employee_rate
            )

        # ========================================================
        # RESULT SUMMARY
        # ========================================================

        st.write(
            f"**{len(filtered)} "
            f"employee(s) found**"
        )

        if filtered:

            filtered_experience = (
                sum(
                    get_employee_experience(
                        employee
                    )
                    for employee in filtered
                )
            )

            filtered_average = (
                filtered_experience
                / len(filtered)
            )

            summary_col1, summary_col2, summary_col3 = (
                st.columns(3)
            )

            with summary_col1:

                st.metric(
                    "Filtered Employees",
                    len(filtered),
                )

            with summary_col2:

                st.metric(
                    "Average Experience",
                    f"{filtered_average:.1f} yrs",
                )

            with summary_col3:

                filtered_cv_count = sum(
                    1
                    for employee in filtered
                    if clean_text(
                        getattr(
                            employee,
                            "cv_link",
                            "",
                        )
                    )
                )

                st.metric(
                    "CVs Available",
                    filtered_cv_count,
                )

        else:

            st.info(
                "No employees match "
                "the selected filters."
            )

        # ========================================================
        # EMPLOYEE CARDS
        # ========================================================

        for employee in filtered:

            full_name = employee_name(
                employee
            )

            current_status = (
                clean_text(
                    employee.employment_status
                )
                or "Not specified"
            )

            current_availability = (
                clean_text(
                    employee.availability
                )
                or "Not specified"
            )

            current_english = (
                clean_text(
                    employee.english_level
                )
                or "Not specified"
            )

            experience = (
                get_employee_experience(
                    employee
                )
            )

            rate = (
                get_employee_rate(
                    employee
                )
            )

            currency_display = (
                clean_text(
                    employee.currency
                )
                or "GBP"
            )

            is_editing = (
                st.session_state[
                    "editing_employee_id"
                ]
                == employee.id
            )

            is_delete_pending = (
                st.session_state[
                    "confirm_delete_employee_id"
                ]
                == employee.id
            )

            with st.container(
                border=True
            ):

                col1, col2, col3 = (
                    st.columns(
                        [3, 2, 1]
                    )
                )

                # =================================================
                # EMPLOYEE INFORMATION
                # =================================================

                with col1:

                    st.subheader(
                        full_name
                    )

                    role_display = (
                        clean_text(
                            employee.role
                        )
                    )

                    if role_display:

                        st.caption(
                            role_display
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
                            clean_text(
                                employee.city
                            )
                        )

                    if employee.country:

                        location_parts.append(
                            clean_text(
                                employee.country
                            )
                        )

                    if location_parts:

                        st.caption(
                            "Location: "
                            + ", ".join(
                                location_parts
                            )
                        )

                # =================================================
                # EMPLOYEE DETAILS
                # =================================================

                with col2:

                    st.write(
                        f"**Status:** "
                        f"{current_status}"
                    )

                    st.write(
                        f"**Availability:** "
                        f"{current_availability}"
                    )

                    st.write(
                        f"**Experience:** "
                        f"{experience:g} years"
                    )

                    st.write(
                        f"**English:** "
                        f"{current_english}"
                    )

                    st.write(
                        f"**Expected Rate:** "
                        f"{currency_display} "
                        f"{rate:,.2f}/month"
                    )

                # =================================================
                # ACTIONS
                # =================================================

                with col3:

                    edit_btn = st.button(
                        "Edit",
                        key=(
                            f"edit_employee_"
                            f"{employee.id}"
                        ),
                        use_container_width=True,
                        disabled=is_editing,
                    )

                    delete_btn = st.button(
                        "Delete",
                        key=(
                            f"delete_employee_"
                            f"{employee.id}"
                        ),
                        use_container_width=True,
                        disabled=is_editing,
                    )

                # =================================================
                # EDIT
                # =================================================

                if edit_btn:

                    st.session_state[
                        "editing_employee_id"
                    ] = employee.id

                    clear_employee_delete_confirmation()

                    st.rerun()

                # =================================================
                # DELETE REQUEST
                # =================================================

                if delete_btn:

                    clear_employee_editing()

                    st.session_state[
                        "confirm_delete_employee_id"
                    ] = employee.id

                    st.rerun()

                # =================================================
                # DELETE CONFIRMATION
                # =================================================

                if is_delete_pending:

                    st.warning(
                        f"Are you sure you want to "
                        f"delete **{full_name}**?"
                    )

                    st.caption(
                        "Employees with related CRM "
                        "records should normally be "
                        "marked as **Former Employee** "
                        "rather than deleted."
                    )

                    c1, c2 = (
                        st.columns(2)
                    )

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

                            # ====================================
                            # RELATED RECORD CHECK
                            # ====================================

                            related_records = (
                                get_related_records(
                                    employee
                                )
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
                                # DELETE LOCAL CV
                                # ----------------------------

                                delete_local_cv(
                                    employee
                                )

                                # ----------------------------
                                # DELETE EMPLOYEE
                                # ----------------------------

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

                        except Exception:

                            session.rollback()

                            clear_employee_delete_confirmation()

                            st.error(
                                "The employee could "
                                "not be deleted. "
                                "The record may be "
                                "used by another "
                                "database record."
                            )

                # =================================================
                # CV
                # =================================================

                cv_link_display = (
                    clean_text(
                        getattr(
                            employee,
                            "cv_link",
                            "",
                        )
                    )
                )

                if cv_link_display:

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

                    elif valid_url(
                        cv_link_display
                    ):

                        st.markdown(
                            f"[Open CV / Resume]"
                            f"({cv_link_display})"
                        )

                    else:

                        st.caption(
                            "CV path is stored, "
                            "but the local file "
                            "could not be found."
                        )

                # =================================================
                # NOTES
                # =================================================

                notes_display = (
                    clean_text(
                        employee.notes
                    )
                )

                if notes_display:

                    st.caption(
                        f"Notes: "
                        f"{notes_display}"
                    )

    except Exception:

        session.rollback()

        st.error(
            "An error occurred while "
            "loading the Employees screen."
        )

    finally:

        session.close()