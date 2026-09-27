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

        if st.session_state.editing_employee_id is not None:

            editing_employee = session.get(
                Employee,
                st.session_state.editing_employee_id,
            )

            if editing_employee is None:

                st.session_state.editing_employee_id = None

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
            in ["Available Now", "Available Soon"]
        )

        placed_employees = sum(
            1
            for employee in employees
            if employee.employment_status == "Placed"
        )

        former_employees = sum(
            1
            for employee in employees
            if employee.employment_status == "Former Employee"
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

            st.subheader("Edit Employee")

        else:

            st.subheader("Add New Employee")

        # ========================================================
        # EMPLOYEE FORM
        # ========================================================

        with st.form("employee_form"):

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
                    placeholder="employee@example.com",
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
                placeholder="Example: Finance Analyst",
            )

            # ----------------------------------------------------
            # EXPERIENCE / ENGLISH
            # ----------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                current_experience = 0.0

                if editing_employee:
                    current_experience = float(
                        editing_employee.years_experience or 0
                    )

                years_experience = st.number_input(
                    "Years of Experience",
                    min_value=0.0,
                    step=0.5,
                    format="%.1f",
                    value=current_experience,
                )

            with col2:

                if (
                    editing_employee
                    and editing_employee.english_level
                    in ENGLISH_LEVELS
                ):

                    english_index = ENGLISH_LEVELS.index(
                        editing_employee.english_level
                    )

                else:

                    english_index = 0

                english_level = st.selectbox(
                    "English Level",
                    ENGLISH_LEVELS,
                    index=english_index,
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

                status_index = EMPLOYEE_STATUSES.index(
                    editing_employee.employment_status
                )

            else:

                status_index = 0

            employment_status = st.selectbox(
                "Employment Status",
                EMPLOYEE_STATUSES,
                index=status_index,
            )

            # ----------------------------------------------------
            # MONTHLY RATE
            # ----------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                current_rate = 0.0

                if editing_employee:
                    current_rate = float(
                        editing_employee.expected_monthly_rate or 0
                    )

                expected_monthly_rate = st.number_input(
                    "Expected Monthly Rate",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    value=current_rate,
                )

            with col2:

                if (
                    editing_employee
                    and editing_employee.currency
                    in CURRENCIES
                ):

                    currency_index = CURRENCIES.index(
                        editing_employee.currency
                    )

                else:

                    currency_index = 0

                currency = st.selectbox(
                    "Currency",
                    CURRENCIES,
                    index=currency_index,
                )

            # ----------------------------------------------------
            # CV
            # ----------------------------------------------------

            cv_link = st.text_input(
                "CV / Resume Link",
                value=(
                    editing_employee.cv_link
                    if editing_employee
                    else ""
                ),
                placeholder="https://...",
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
                    "Additional information about the employee..."
                ),
            )

            # ----------------------------------------------------
            # FORM BUTTON
            # ----------------------------------------------------

            submitted = st.form_submit_button(
                "Save Changes"
                if editing_employee
                else "Add Employee",
                use_container_width=True,
            )

            # ====================================================
            # SAVE FORM
            # ====================================================

            if submitted:

                first_name_clean = clean_text(first_name)
                last_name_clean = clean_text(last_name)
                country_clean = clean_text(country)
                city_clean = clean_text(city)
                email_clean = clean_text(email).lower()
                phone_clean = clean_text(phone)
                role_clean = clean_text(role)
                cv_link_clean = clean_text(cv_link)
                notes_clean = clean_text(notes)

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

                elif not valid_email(email_clean):

                    st.error(
                        "Please enter a valid email address."
                    )

                elif expected_monthly_rate < 0:

                    st.error(
                        "Expected monthly rate cannot be negative."
                    )

                else:

                    # ============================================
                    # DUPLICATE EMAIL CHECK
                    # ============================================

                    duplicate = None

                    if email_clean:

                        duplicate_query = (
                            session.query(Employee)
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
                            "Another employee already uses "
                            "this email address."
                        )

                    else:

                        # ========================================
                        # UPDATE EMPLOYEE
                        # ========================================

                        if editing_employee:

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

                            editing_employee.cv_link = (
                                cv_link_clean
                            )

                            editing_employee.notes = (
                                notes_clean
                            )

                            session.commit()

                            st.session_state.editing_employee_id = (
                                None
                            )

                            st.success(
                                "Employee updated successfully."
                            )

                            st.rerun()

                        # ========================================
                        # ADD EMPLOYEE
                        # ========================================

                        else:

                            new_employee = Employee(
                                first_name=first_name_clean,
                                last_name=last_name_clean,
                                country=country_clean,
                                city=city_clean,
                                email=email_clean,
                                phone=phone_clean,
                                role=role_clean,
                                years_experience=years_experience,
                                english_level=english_level,
                                availability=availability,
                                expected_monthly_rate=(
                                    expected_monthly_rate
                                ),
                                currency=currency,
                                employment_status=(
                                    employment_status
                                ),
                                cv_link=cv_link_clean,
                                notes=notes_clean,
                            )

                            session.add(
                                new_employee
                            )

                            session.commit()

                            st.success(
                                "Employee added successfully."
                            )

                            st.rerun()

        # ========================================================
        # EMPLOYEE REGISTER
        # ========================================================

        st.divider()

        st.subheader("Employee Register")

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
                    "Name, role, email, city or country..."
                ),
            )

        with col2:

            status_filter = st.selectbox(
                "Employment Status",
                ["All"] + EMPLOYEE_STATUSES,
            )

        with col3:

            availability_filter = st.selectbox(
                "Availability",
                ["All"] + AVAILABILITY_OPTIONS,
            )

        filtered = employees

        # ========================================================
        # SEARCH FILTER
        # ========================================================

        if search.strip():

            search_lower = search.strip().lower()

            filtered = [
                employee
                for employee in filtered
                if search_lower
                in employee_search_text(employee)
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
                "No employees match the selected filters."
            )

        # ========================================================
        # EMPLOYEE CARDS
        # ========================================================

        for employee in filtered:

            full_name = employee_name(employee)

            with st.container(border=True):

                col1, col2, col3 = st.columns(
                    [3, 2, 1]
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
                            f"Email: {employee.email}"
                        )

                    if employee.phone:

                        st.write(
                            f"Phone: {employee.phone}"
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
                            + ", ".join(location_parts)
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
                        employee.years_experience or 0
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
                        employee.expected_monthly_rate or 0
                    )

                    currency_display = (
                        employee.currency or "GBP"
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
                        key=f"edit_employee_{employee.id}",
                        use_container_width=True,
                    )

                    delete_btn = st.button(
                        "Delete",
                        key=f"delete_employee_{employee.id}",
                        use_container_width=True,
                    )

                # =================================================
                # EDIT
                # =================================================

                if edit_btn:

                    st.session_state.editing_employee_id = (
                        employee.id
                    )

                    st.rerun()

                # =================================================
                # DELETE REQUEST
                # =================================================

                if delete_btn:

                    st.session_state.confirm_delete_employee_id = (
                        employee.id
                    )

                    st.rerun()

                # =================================================
                # DELETE CONFIRMATION
                # =================================================

                if (
                    st.session_state.confirm_delete_employee_id
                    == employee.id
                ):

                    st.warning(
                        f"Are you sure you want to delete "
                        f"**{full_name}**?"
                    )

                    st.caption(
                        "Employees with related CRM records "
                        "should normally be marked as "
                        "'Former Employee' instead of deleted."
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

                        st.session_state.confirm_delete_employee_id = (
                            None
                        )

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
                                    "This employee cannot be "
                                    "deleted because related "
                                    "CRM records exist."
                                )

                                st.info(
                                    "Related records: "
                                    + ", ".join(
                                        related_records
                                    )
                                    + ". Mark the employee as "
                                    "'Former Employee' instead."
                                )

                                st.session_state.confirm_delete_employee_id = (
                                    None
                                )

                            else:

                                session.delete(
                                    employee
                                )

                                session.commit()

                                st.session_state.confirm_delete_employee_id = (
                                    None
                                )

                                st.success(
                                    "Employee deleted successfully."
                                )

                                st.rerun()

                        except Exception as error:

                            session.rollback()

                            st.error(
                                "The employee could not be deleted."
                            )

                            st.exception(error)

                # =================================================
                # CV LINK
                # =================================================

                if employee.cv_link:

                    st.markdown(
                        f"[Open CV / Resume]"
                        f"({employee.cv_link})"
                    )

                # =================================================
                # NOTES
                # =================================================

                if employee.notes:

                    st.caption(
                        f"Notes: {employee.notes}"
                    )

    except Exception as error:

        session.rollback()

        st.error(
            "An error occurred while loading "
            "the Employees screen."
        )

        st.exception(error)

    finally:

        session.close()