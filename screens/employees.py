import streamlit as st

from database import get_session
from models import Employee


EMPLOYEE_STATUSES = [
    "Sourced",
    "Available",
    "Interviewing",
    "Placed",
    "On Leave",
    "Unavailable",
    "Former Employee"
]

ENGLISH_LEVELS = [
    "Basic",
    "Intermediate",
    "Advanced",
    "Fluent",
    "Native"
]

AVAILABILITY_OPTIONS = [
    "Available Now",
    "Available Soon",
    "Currently Working",
    "Unavailable"
]

CURRENCIES = [
    "GBP",
    "EUR",
    "USD",
    "INR"
]


def show_employees():

    st.title("Employees")

    st.caption(
        "Manage remote workers, availability, experience and cost information."
    )

    session = get_session()

    # ============================================================
    # SESSION STATE
    # ============================================================

    if "editing_employee_id" not in st.session_state:
        st.session_state.editing_employee_id = None

    if "confirm_delete_employee_id" not in st.session_state:
        st.session_state.confirm_delete_employee_id = None

    # ============================================================
    # LOAD EMPLOYEES
    # ============================================================

    employees = (
        session.query(Employee)
        .order_by(
            Employee.first_name,
            Employee.last_name
        )
        .all()
    )

    # ============================================================
    # EDITING
    # ============================================================

    editing_employee = None

    if st.session_state.editing_employee_id is not None:

        editing_employee = session.get(
            Employee,
            st.session_state.editing_employee_id
        )

        if editing_employee is None:

            st.session_state.editing_employee_id = None

    # ============================================================
    # FORM TITLE
    # ============================================================

    if editing_employee:

        st.subheader("Edit Employee")

    else:

        st.subheader("Add New Employee")

    # ============================================================
    # EMPLOYEE FORM
    # ============================================================

    with st.form("employee_form"):

        # --------------------------------------------------------
        # NAME
        # --------------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            first_name = st.text_input(
                "First Name",
                value=(
                    editing_employee.first_name
                    if editing_employee
                    else ""
                ),
                placeholder="Example: John"
            )

        with col2:

            last_name = st.text_input(
                "Last Name",
                value=(
                    editing_employee.last_name
                    if editing_employee
                    else ""
                ),
                placeholder="Example: Smith"
            )

        # --------------------------------------------------------
        # LOCATION
        # --------------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            country = st.text_input(
                "Country",
                value=(
                    editing_employee.country
                    if editing_employee
                    else "India"
                ),
                placeholder="Example: India"
            )

        with col2:

            city = st.text_input(
                "City",
                value=(
                    editing_employee.city
                    if editing_employee
                    else ""
                ),
                placeholder="Example: Bangalore"
            )

        # --------------------------------------------------------
        # CONTACT
        # --------------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            email = st.text_input(
                "Email",
                value=(
                    editing_employee.email
                    if editing_employee
                    else ""
                )
            )

        with col2:

            phone = st.text_input(
                "Phone",
                value=(
                    editing_employee.phone
                    if editing_employee
                    else ""
                )
            )

        # --------------------------------------------------------
        # ROLE
        # --------------------------------------------------------

        role = st.text_input(
            "Role / Position",
            value=(
                editing_employee.role
                if editing_employee
                else ""
            ),
            placeholder=(
                "Example: Finance Analyst"
            )
        )

        # --------------------------------------------------------
        # EXPERIENCE / ENGLISH
        # --------------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            years_experience = st.number_input(
                "Years of Experience",
                min_value=0.0,
                step=0.5,
                format="%.1f",
                value=(
                    float(
                        editing_employee.years_experience or 0
                    )
                    if editing_employee
                    else 0.0
                )
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
                index=english_index
            )

        # --------------------------------------------------------
        # AVAILABILITY
        # --------------------------------------------------------

        if (
            editing_employee
            and editing_employee.availability
            in AVAILABILITY_OPTIONS
        ):

            availability_index = AVAILABILITY_OPTIONS.index(
                editing_employee.availability
            )

        else:

            availability_index = 0

        availability = st.selectbox(
            "Availability",
            AVAILABILITY_OPTIONS,
            index=availability_index
        )

        # --------------------------------------------------------
        # EMPLOYMENT STATUS
        # --------------------------------------------------------

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
            index=status_index
        )

        # --------------------------------------------------------
        # MONTHLY RATE
        # --------------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            expected_monthly_rate = st.number_input(
                "Expected Monthly Rate",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                value=(
                    float(
                        editing_employee.expected_monthly_rate or 0
                    )
                    if editing_employee
                    else 0.0
                )
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
                index=currency_index
            )

        # --------------------------------------------------------
        # CV
        # --------------------------------------------------------

        cv_link = st.text_input(
            "CV / Resume Link",
            value=(
                editing_employee.cv_link
                if editing_employee
                else ""
            ),
            placeholder="https://..."
        )

        # --------------------------------------------------------
        # NOTES
        # --------------------------------------------------------

        notes = st.text_area(
            "Notes",
            value=(
                editing_employee.notes
                if editing_employee
                else ""
            ),
            placeholder=(
                "Additional information about the employee..."
            )
        )

        # --------------------------------------------------------
        # SAVE
        # --------------------------------------------------------

        submitted = st.form_submit_button(
            "Save Changes"
            if editing_employee
            else "Add Employee",
            use_container_width=True
        )

        if submitted:

            # ----------------------------------------------------
            # VALIDATION
            # ----------------------------------------------------

            if not first_name.strip():

                st.error(
                    "First name is required."
                )

            elif not role.strip():

                st.error(
                    "Role / Position is required."
                )

            else:

                # ------------------------------------------------
                # DUPLICATE EMAIL CHECK
                # ------------------------------------------------

                duplicate = None

                if email.strip():

                    duplicate_query = (
                        session.query(Employee)
                        .filter(
                            Employee.email.ilike(
                                email.strip()
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
                        "Another employee already uses this email address."
                    )

                else:

                    # ============================================
                    # UPDATE
                    # ============================================

                    if editing_employee:

                        editing_employee.first_name = (
                            first_name.strip()
                        )

                        editing_employee.last_name = (
                            last_name.strip()
                        )

                        editing_employee.country = (
                            country.strip()
                        )

                        editing_employee.city = (
                            city.strip()
                        )

                        editing_employee.email = (
                            email.strip()
                        )

                        editing_employee.phone = (
                            phone.strip()
                        )

                        editing_employee.role = (
                            role.strip()
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
                            cv_link.strip()
                        )

                        editing_employee.notes = (
                            notes.strip()
                        )

                        session.commit()

                        st.session_state.editing_employee_id = (
                            None
                        )

                        st.success(
                            "Employee updated successfully."
                        )

                        st.rerun()

                    # ============================================
                    # ADD
                    # ============================================

                    else:

                        new_employee = Employee(

                            first_name=first_name.strip(),

                            last_name=last_name.strip(),

                            country=country.strip(),

                            city=city.strip(),

                            email=email.strip(),

                            phone=phone.strip(),

                            role=role.strip(),

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

                            cv_link=cv_link.strip(),

                            notes=notes.strip()
                        )

                        session.add(
                            new_employee
                        )

                        session.commit()

                        st.success(
                            "Employee added successfully."
                        )

                        st.rerun()

    # ============================================================
    # EMPLOYEE REGISTER
    # ============================================================

    st.divider()

    st.subheader(
        "Employee Register"
    )

    if not employees:

        st.info(
            "No employees have been added yet."
        )

        session.close()
        return

    # ============================================================
    # FILTERS
    # ============================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        search = st.text_input(
            "Search Employees",
            placeholder=(
                "Name, role, email, city or country..."
            )
        )

    with col2:

        status_filter = st.selectbox(
            "Employment Status",
            ["All"] + EMPLOYEE_STATUSES
        )

    with col3:

        availability_filter = st.selectbox(
            "Availability",
            ["All"] + AVAILABILITY_OPTIONS
        )

    filtered = employees

    # ============================================================
    # SEARCH
    # ============================================================

    if search:

        search_lower = search.lower()

        filtered = [

            employee

            for employee in filtered

            if (
                search_lower
                in (
                    f"{employee.first_name} "
                    f"{employee.last_name or ''}"
                ).lower()
            )

            or (
                search_lower
                in (employee.role or "").lower()
            )

            or (
                search_lower
                in (employee.email or "").lower()
            )

            or (
                search_lower
                in (employee.phone or "").lower()
            )

            or (
                search_lower
                in (employee.city or "").lower()
            )

            or (
                search_lower
                in (employee.country or "").lower()
            )
        ]

    # ============================================================
    # STATUS FILTER
    # ============================================================

    if status_filter != "All":

        filtered = [

            employee

            for employee in filtered

            if employee.employment_status
            == status_filter
        ]

    # ============================================================
    # AVAILABILITY FILTER
    # ============================================================

    if availability_filter != "All":

        filtered = [

            employee

            for employee in filtered

            if employee.availability
            == availability_filter
        ]

    # ============================================================
    # RESULT COUNT
    # ============================================================

    st.write(
        f"**{len(filtered)} employee(s) found**"
    )

    # ============================================================
    # DISPLAY
    # ============================================================

    for employee in filtered:

        employee_name = (
            f"{employee.first_name} "
            f"{employee.last_name or ''}"
        ).strip()

        with st.container(border=True):

            col1, col2, col3 = st.columns(
                [3, 2, 1]
            )

            # ----------------------------------------------------
            # EMPLOYEE INFORMATION
            # ----------------------------------------------------

            with col1:

                st.subheader(
                    employee_name
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

            # ----------------------------------------------------
            # EMPLOYEE DETAILS
            # ----------------------------------------------------

            with col2:

                st.write(
                    f"**Status:** "
                    f"{employee.employment_status}"
                )

                st.write(
                    f"**Availability:** "
                    f"{employee.availability}"
                )

                st.write(
                    f"Experience: "
                    f"{employee.years_experience or 0:g} years"
                )

                st.write(
                    f"English: "
                    f"{employee.english_level or 'Not specified'}"
                )

                st.write(
                    f"Expected Rate: "
                    f"{employee.currency or 'GBP'} "
                    f"{(employee.expected_monthly_rate or 0):,.2f}"
                    f"/month"
                )

            # ----------------------------------------------------
            # ACTIONS
            # ----------------------------------------------------

            with col3:

                edit_btn = st.button(
                    "Edit",
                    key=f"edit_employee_{employee.id}",
                    use_container_width=True
                )

                delete_btn = st.button(
                    "Delete",
                    key=f"delete_employee_{employee.id}",
                    use_container_width=True
                )

            # ====================================================
            # EDIT
            # ====================================================

            if edit_btn:

                st.session_state.editing_employee_id = (
                    employee.id
                )

                st.rerun()

            # ====================================================
            # DELETE
            # ====================================================

            if delete_btn:

                st.session_state.confirm_delete_employee_id = (
                    employee.id
                )

                st.rerun()

            if (
                st.session_state.confirm_delete_employee_id
                == employee.id
            ):

                st.warning(
                    f"Are you sure you want to delete "
                    f"**{employee_name}**?"
                )

                st.caption(
                    "Employees with related CRM records should "
                    "normally be marked as Former Employee "
                    "instead of being deleted."
                )

                c1, c2 = st.columns(2)

                with c1:

                    confirm = st.button(
                        "Yes, Delete Employee",
                        key=f"confirm_delete_employee_{employee.id}",
                        type="primary",
                        use_container_width=True
                    )

                with c2:

                    cancel = st.button(
                        "Cancel",
                        key=f"cancel_delete_employee_{employee.id}",
                        use_container_width=True
                    )

                if cancel:

                    st.session_state.confirm_delete_employee_id = (
                        None
                    )

                    st.rerun()

                if confirm:

                    # ------------------------------------------------
                    # CHECK RELATED RECORDS
                    # ------------------------------------------------

                    related = any([
                        getattr(
                            employee,
                            "candidates",
                            []
                        ),

                        getattr(
                            employee,
                            "placements",
                            []
                        ),

                        getattr(
                            employee,
                            "activities",
                            []
                        ),

                        getattr(
                            employee,
                            "skills",
                            []
                        )
                    ])

                    if related:

                        st.error(
                            "This employee cannot be deleted "
                            "because related CRM records exist. "
                            "Mark the employee as 'Former Employee' "
                            "instead."
                        )

                        st.session_state.confirm_delete_employee_id = (
                            None
                        )

                    else:

                        session.delete(
                            employee
                        )

                        session.commit()

                        st.success(
                            "Employee deleted successfully."
                        )

                        st.session_state.confirm_delete_employee_id = (
                            None
                        )

                        st.rerun()

            # ====================================================
            # CV LINK
            # ====================================================

            if employee.cv_link:

                st.markdown(
                    f"[Open CV / Resume]({employee.cv_link})"
                )

            # ====================================================
            # NOTES
            # ====================================================

            if employee.notes:

                st.caption(
                    f"Notes: {employee.notes}"
                )

    session.close()