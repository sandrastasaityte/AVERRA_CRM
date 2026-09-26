
import streamlit as st

from database import get_session
from models import Employee, EmployeeSkill


SKILL_CATEGORIES = [
    "Finance",
    "Accounting",
    "Treasury",
    "Data Analytics",
    "Technology",
    "Administration",
    "Customer Service",
    "Sales",
    "HR",
    "Engineering",
    "Architecture",
    "Other"
]

SKILL_LEVELS = [
    "Beginner",
    "Intermediate",
    "Advanced",
    "Expert"
]


def show_employee_skills():

    st.title("Employee Skills")
    st.caption(
        "Manage skills, qualifications and experience for remote workers."
    )

    session = get_session()

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

    if not employees:

        st.warning(
            "Please add an employee first."
        )

        session.close()
        return

    # ============================================================
    # SESSION STATE
    # ============================================================

    if "editing_skill_id" not in st.session_state:
        st.session_state.editing_skill_id = None

    editing_id = (
        st.session_state.editing_skill_id
    )

    editing_item = None

    if editing_id is not None:

        editing_item = session.get(
            EmployeeSkill,
            editing_id
        )

        # If the record no longer exists
        if editing_item is None:

            st.session_state.editing_skill_id = None
            editing_id = None

    # ============================================================
    # FORM TITLE
    # ============================================================

    if editing_item:

        st.subheader(
            f"Edit Employee Skill"
        )

    else:

        st.subheader(
            "Add Employee Skill"
        )

    # ============================================================
    # EMPLOYEE OPTIONS
    # ============================================================

    employee_options = {}

    for employee in employees:

        full_name = (
            f"{employee.first_name} "
            f"{employee.last_name or ''}"
        ).strip()

        employee_options[
            f"{full_name} (ID: {employee.id})"
        ] = employee.id

    employee_labels = list(
        employee_options.keys()
    )

    # ============================================================
    # ADD / EDIT FORM
    # ============================================================

    with st.form("employee_skill_form"):

        # --------------------------------------------------------
        # EMPLOYEE
        # --------------------------------------------------------

        if editing_item:

            current_employee_index = (
                list(employee_options.values()).index(
                    editing_item.employee_id
                )
            )

        else:

            current_employee_index = 0

        selected_employee = st.selectbox(
            "Employee",
            employee_labels,
            index=current_employee_index
        )

        # --------------------------------------------------------
        # SKILL
        # --------------------------------------------------------

        skill = st.text_input(
            "Skill",
            value=(
                editing_item.skill
                if editing_item
                else ""
            ),
            placeholder="Example: Excel"
        )

        # --------------------------------------------------------
        # CATEGORY
        # --------------------------------------------------------

        if (
            editing_item
            and editing_item.category in SKILL_CATEGORIES
        ):

            category_index = SKILL_CATEGORIES.index(
                editing_item.category
            )

        else:

            category_index = 0

        category = st.selectbox(
            "Category",
            SKILL_CATEGORIES,
            index=category_index
        )

        # --------------------------------------------------------
        # LEVEL
        # --------------------------------------------------------

        if (
            editing_item
            and editing_item.level in SKILL_LEVELS
        ):

            level_index = SKILL_LEVELS.index(
                editing_item.level
            )

        else:

            level_index = 0

        level = st.selectbox(
            "Skill Level",
            SKILL_LEVELS,
            index=level_index
        )

        # --------------------------------------------------------
        # EXPERIENCE
        # --------------------------------------------------------

        years_used = st.number_input(
            "Years Used",
            min_value=0.0,
            step=0.5,
            format="%.1f",
            value=(
                float(editing_item.years_used or 0)
                if editing_item
                else 0.0
            )
        )

        # --------------------------------------------------------
        # QUALIFICATION
        # --------------------------------------------------------

        qualification = st.text_input(
            "Qualification",
            value=(
                editing_item.qualification
                if editing_item
                else ""
            ),
            placeholder=(
                "Example: Microsoft Excel certification"
            )
        )

        # --------------------------------------------------------
        # NOTES
        # --------------------------------------------------------

        notes = st.text_area(
            "Notes",
            value=(
                editing_item.notes
                if editing_item
                else ""
            ),
            placeholder=(
                "Additional information about the skill..."
            )
        )

        # --------------------------------------------------------
        # SUBMIT
        # --------------------------------------------------------

        submitted = st.form_submit_button(
            "Save Changes"
            if editing_item
            else "Add Skill",
            use_container_width=True
        )

        if submitted:

            if not skill.strip():

                st.error(
                    "Skill is required."
                )

            else:

                employee_id = (
                    employee_options[selected_employee]
                )

                # =================================================
                # DUPLICATE CHECK
                # =================================================

                duplicate_query = (
                    session.query(EmployeeSkill)
                    .filter(
                        EmployeeSkill.employee_id
                        == employee_id,

                        EmployeeSkill.skill.ilike(
                            skill.strip()
                        )
                    )
                )

                if editing_item:

                    duplicate_query = duplicate_query.filter(
                        EmployeeSkill.id
                        != editing_item.id
                    )

                duplicate = (
                    duplicate_query.first()
                )

                if duplicate:

                    st.error(
                        "This employee already has this skill."
                    )

                else:

                    # =================================================
                    # UPDATE
                    # =================================================

                    if editing_item:

                        editing_item.employee_id = (
                            employee_id
                        )

                        editing_item.skill = (
                            skill.strip()
                        )

                        editing_item.category = (
                            category
                        )

                        editing_item.level = (
                            level
                        )

                        editing_item.years_used = (
                            years_used
                        )

                        editing_item.qualification = (
                            qualification.strip()
                        )

                        editing_item.notes = (
                            notes.strip()
                        )

                        session.commit()

                        st.session_state.editing_skill_id = (
                            None
                        )

                        st.success(
                            "Employee skill updated successfully."
                        )

                    # =================================================
                    # ADD
                    # =================================================

                    else:

                        new_skill = EmployeeSkill(
                            employee_id=employee_id,
                            skill=skill.strip(),
                            category=category,
                            level=level,
                            years_used=years_used,
                            qualification=qualification.strip(),
                            notes=notes.strip()
                        )

                        session.add(
                            new_skill
                        )

                        session.commit()

                        st.success(
                            "Employee skill added successfully."
                        )

                    st.rerun()

    # ============================================================
    # SKILL REGISTER
    # ============================================================

    st.divider()

    st.subheader(
        "Skill Register"
    )

    skills = (
        session.query(EmployeeSkill)
        .order_by(
            EmployeeSkill.skill
        )
        .all()
    )

    if not skills:

        st.info(
            "No employee skills have been added yet."
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
            placeholder="Employee or skill..."
        )

    with col2:

        category_filter = st.selectbox(
            "Category",
            ["All"] + SKILL_CATEGORIES
        )

    with col3:

        level_filter = st.selectbox(
            "Level",
            ["All"] + SKILL_LEVELS
        )

    filtered_skills = skills

    # ============================================================
    # SEARCH
    # ============================================================

    if search:

        search_lower = search.lower()

        filtered_skills = [

            item

            for item in filtered_skills

            if (
                search_lower
                in (item.skill or "").lower()
            )

            or (
                item.employee

                and search_lower
                in (
                    f"{item.employee.first_name} "
                    f"{item.employee.last_name or ''}"
                ).lower()
            )
        ]

    # ============================================================
    # CATEGORY FILTER
    # ============================================================

    if category_filter != "All":

        filtered_skills = [

            item

            for item in filtered_skills

            if item.category == category_filter
        ]

    # ============================================================
    # LEVEL FILTER
    # ============================================================

    if level_filter != "All":

        filtered_skills = [

            item

            for item in filtered_skills

            if item.level == level_filter
        ]

    # ============================================================
    # RESULT COUNT
    # ============================================================

    st.write(
        f"**{len(filtered_skills)} skill record(s) found**"
    )

    # ============================================================
    # DISPLAY
    # ============================================================

    if not filtered_skills:

        st.info(
            "No skills match your filters."
        )

    else:

        for item in filtered_skills:

            if item.employee:

                employee_name = (
                    f"{item.employee.first_name} "
                    f"{item.employee.last_name or ''}"
                ).strip()

            else:

                employee_name = (
                    "Unknown Employee"
                )

            with st.container(border=True):

                col1, col2, col3, col4, col5 = st.columns(
                    [2, 3, 2, 2, 2]
                )

                # ------------------------------------------------
                # EMPLOYEE
                # ------------------------------------------------

                with col1:

                    st.write(
                        f"**{employee_name}**"
                    )

                # ------------------------------------------------
                # SKILL
                # ------------------------------------------------

                with col2:

                    st.write(
                        f"**{item.skill}**"
                    )

                    if item.category:

                        st.caption(
                            item.category
                        )

                # ------------------------------------------------
                # LEVEL
                # ------------------------------------------------

                with col3:

                    st.write(
                        f"Level: **{item.level}**"
                    )

                    st.caption(
                        f"Experience: "
                        f"{item.years_used or 0:g} years"
                    )

                # ------------------------------------------------
                # QUALIFICATION
                # ------------------------------------------------

                with col4:

                    if item.qualification:

                        st.write(
                            f"**{item.qualification}**"
                        )

                # ------------------------------------------------
                # ACTIONS
                # ------------------------------------------------

                with col5:

                    edit_btn = st.button(
                        "Edit",
                        key=f"edit_skill_{item.id}",
                        use_container_width=True
                    )

                    delete_btn = st.button(
                        "Delete",
                        key=f"delete_skill_{item.id}",
                        use_container_width=True
                    )

                # =================================================
                # EDIT
                # =================================================

                if edit_btn:

                    st.session_state.editing_skill_id = (
                        item.id
                    )

                    st.rerun()

                # =================================================
                # DELETE
                # =================================================

                if delete_btn:

                    st.session_state[
                        f"confirm_delete_skill_{item.id}"
                    ] = True

                    st.rerun()

                if st.session_state.get(
                    f"confirm_delete_skill_{item.id}",
                    False
                ):

                    st.warning(
                        f"Delete **{item.skill}** "
                        f"from {employee_name}?"
                    )

                    confirm_col, cancel_col = st.columns(2)

                    if confirm_col.button(
                        "Yes, Delete",
                        key=f"confirm_skill_{item.id}",
                        type="primary",
                        use_container_width=True
                    ):

                        session.delete(
                            item
                        )

                        session.commit()

                        st.session_state[
                            f"confirm_delete_skill_{item.id}"
                        ] = False

                        st.success(
                            "Employee skill deleted successfully."
                        )

                        st.rerun()

                    if cancel_col.button(
                        "Cancel",
                        key=f"cancel_skill_{item.id}",
                        use_container_width=True
                    ):

                        st.session_state[
                            f"confirm_delete_skill_{item.id}"
                        ] = False

                        st.rerun()

                # =================================================
                # NOTES
                # =================================================

                if item.notes:

                    st.caption(
                        f"Notes: {item.notes}"
                    )

    session.close()

