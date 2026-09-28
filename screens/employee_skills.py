import streamlit as st

from database import get_session
from models import Employee, EmployeeSkill


# ============================================================
# CONSTANTS
# ============================================================

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
    "Other",
]

SKILL_LEVELS = [
    "Beginner",
    "Intermediate",
    "Advanced",
    "Expert",
]


# ============================================================
# HELPERS
# ============================================================

def employee_name(employee):
    """Return the employee's full name safely."""

    if employee is None:
        return "Unknown Employee"

    first_name = (
        employee.first_name or ""
    ).strip()

    last_name = (
        employee.last_name or ""
    ).strip()

    full_name = (
        f"{first_name} {last_name}"
    ).strip()

    if full_name:
        return full_name

    return f"Employee {employee.id}"


def employee_label(employee):
    """Return employee name with database ID."""

    return (
        f"{employee_name(employee)} "
        f"(ID: {employee.id})"
    )


def clean_text(value):
    """Clean a text value."""

    if value is None:
        return ""

    return str(value).strip()


def normalize_text(value):
    """
    Normalize text for duplicate checks
    and searching.
    """

    return " ".join(
        clean_text(value)
        .lower()
        .split()
    )


def level_icon(level):
    """Return an icon for the skill level."""

    icons = {
        "Beginner": "🟢",
        "Intermediate": "🔵",
        "Advanced": "🟠",
        "Expert": "🔴",
    }

    return icons.get(
        level,
        "⚪",
    )


def skill_search_text(skill, employee):
    """Build searchable text for a skill."""

    values = [
        skill.skill,
        skill.category,
        skill.level,
        skill.qualification,
        skill.notes,
        employee.first_name if employee else "",
        employee.last_name if employee else "",
        employee.role if employee else "",
    ]

    return normalize_text(
        " ".join(
            clean_text(value)
            for value in values
            if value
        )
    )


def find_duplicate_skill(
    session,
    employee_id,
    skill_name,
    exclude_id=None,
):
    """
    Find an existing skill for the same employee.

    Comparison is case-insensitive and ignores
    repeated/leading/trailing spaces.
    """

    normalized_skill = normalize_text(
        skill_name
    )

    if not normalized_skill:
        return None

    existing_skills = (
        session.query(EmployeeSkill)
        .filter(
            EmployeeSkill.employee_id
            == employee_id
        )
        .all()
    )

    for existing_skill in existing_skills:

        if (
            exclude_id is not None
            and existing_skill.id == exclude_id
        ):
            continue

        existing_name = normalize_text(
            existing_skill.skill
        )

        if (
            existing_name
            == normalized_skill
        ):
            return existing_skill

    return None


def get_average_years(skills):
    """
    Calculate average years only across
    skill records with positive experience.
    """

    years = [
        float(skill.years_used or 0)
        for skill in skills
        if float(skill.years_used or 0) > 0
    ]

    if not years:
        return 0

    return sum(years) / len(years)


# ============================================================
# MAIN SCREEN
# ============================================================

def show_employee_skills():

    st.title("Employee Skills")

    st.caption(
        "Manage employee skills, experience, "
        "qualifications and professional capabilities."
    )

    session = get_session()

    try:

        # ========================================================
        # SESSION STATE
        # ========================================================

        if (
            "editing_skill_id"
            not in st.session_state
        ):

            st.session_state.editing_skill_id = None

        if (
            "confirm_delete_skill_id"
            not in st.session_state
        ):

            st.session_state.confirm_delete_skill_id = None

        # ========================================================
        # LOAD EMPLOYEES
        # ========================================================

        employees = (
            session.query(Employee)
            .order_by(
                Employee.first_name.asc(),
                Employee.last_name.asc(),
            )
            .all()
        )

        # ========================================================
        # LOAD SKILLS
        # ========================================================

        skills = (
            session.query(EmployeeSkill)
            .order_by(
                EmployeeSkill.skill.asc(),
                EmployeeSkill.id.asc(),
            )
            .all()
        )

        # ========================================================
        # EMPLOYEE LOOKUP
        # ========================================================

        employee_map = {
            employee.id: employee
            for employee in employees
        }

        # ========================================================
        # FIND EDITING SKILL
        # ========================================================

        editing_skill = None

        editing_skill_id = (
            st.session_state.editing_skill_id
        )

        if editing_skill_id is not None:

            editing_skill = session.get(
                EmployeeSkill,
                editing_skill_id,
            )

            if editing_skill is None:

                st.session_state.editing_skill_id = None

        # ========================================================
        # KPI CALCULATIONS
        # ========================================================

        total_skills = len(skills)

        employees_with_skills = len(
            {
                skill.employee_id
                for skill in skills
                if skill.employee_id is not None
            }
        )

        unique_skills = len(
            {
                normalize_text(skill.skill)
                for skill in skills
                if normalize_text(skill.skill)
            }
        )

        advanced_expert = sum(
            1
            for skill in skills
            if skill.level
            in [
                "Advanced",
                "Expert",
            ]
        )

        average_years = get_average_years(
            skills
        )

        employees_without_skills = max(
            len(employees)
            - employees_with_skills,
            0,
        )

        # ========================================================
        # KPI DISPLAY
        # ========================================================

        col1, col2, col3, col4, col5 = (
            st.columns(5)
        )

        with col1:

            st.metric(
                "Skill Records",
                total_skills,
            )

        with col2:

            st.metric(
                "Employees With Skills",
                employees_with_skills,
            )

        with col3:

            st.metric(
                "Unique Skills",
                unique_skills,
            )

        with col4:

            st.metric(
                "Advanced / Expert",
                advanced_expert,
            )

        with col5:

            st.metric(
                "Avg. Years",
                f"{average_years:.1f}",
            )

        st.divider()

        # ========================================================
        # EMPLOYEES WITHOUT SKILLS
        # ========================================================

        if employees_without_skills > 0:

            st.info(
                f"{employees_without_skills} employee(s) "
                "currently have no skill records."
            )

        # ========================================================
        # SKILL OVERVIEW
        # ========================================================

        if skills:

            with st.expander(
                "Skill Overview",
                expanded=False,
            ):

                category_counts = {}
                level_counts = {}

                for skill in skills:

                    category = (
                        clean_text(
                            skill.category
                        )
                        or "Other"
                    )

                    level = (
                        clean_text(
                            skill.level
                        )
                        or "Not specified"
                    )

                    category_counts[
                        category
                    ] = (
                        category_counts.get(
                            category,
                            0,
                        )
                        + 1
                    )

                    level_counts[
                        level
                    ] = (
                        level_counts.get(
                            level,
                            0,
                        )
                        + 1
                    )

                # ------------------------------------------------
                # CATEGORIES
                # ------------------------------------------------

                st.write(
                    "**Skills by Category**"
                )

                category_columns = (
                    st.columns(3)
                )

                sorted_categories = sorted(
                    category_counts.items(),
                    key=lambda item:
                    item[0].lower(),
                )

                for index, (
                    category,
                    count,
                ) in enumerate(
                    sorted_categories
                ):

                    with category_columns[
                        index % 3
                    ]:

                        st.write(
                            f"**{category}:** "
                            f"{count}"
                        )

                # ------------------------------------------------
                # LEVELS
                # ------------------------------------------------

                st.write(
                    "**Skills by Level**"
                )

                for level in SKILL_LEVELS:

                    count = (
                        level_counts.get(
                            level,
                            0,
                        )
                    )

                    st.write(
                        f"{level_icon(level)} "
                        f"**{level}:** {count}"
                    )

        # ========================================================
        # FORM
        # ========================================================

        if editing_skill:

            st.subheader(
                "Edit Employee Skill"
            )

        else:

            st.subheader(
                "Add Employee Skill"
            )

        # ========================================================
        # EMPLOYEE CHECK
        # ========================================================

        if not employees:

            st.warning(
                "You need to add employees "
                "before adding skills."
            )

            return

        # ========================================================
        # SKILL FORM
        # ========================================================

        with st.form(
            "employee_skill_form"
        ):

            # ====================================================
            # EMPLOYEE
            # ====================================================

            employee_options = [
                employee.id
                for employee in employees
            ]

            if (
                editing_skill
                and editing_skill.employee_id
                in employee_options
            ):

                employee_index = (
                    employee_options.index(
                        editing_skill.employee_id
                    )
                )

            else:

                employee_index = 0

            selected_employee_id = (
                st.selectbox(
                    "Employee",
                    employee_options,
                    index=employee_index,
                    format_func=(
                        lambda employee_id:
                        employee_label(
                            employee_map[
                                employee_id
                            ]
                        )
                    ),
                )
            )

            # ====================================================
            # SKILL
            # ====================================================

            skill_name = st.text_input(
                "Skill",
                value=(
                    editing_skill.skill
                    if editing_skill
                    else ""
                ),
                placeholder="Example: Excel",
            )

            # ====================================================
            # CATEGORY / LEVEL
            # ====================================================

            col1, col2 = st.columns(2)

            with col1:

                current_category = (
                    editing_skill.category
                    if (
                        editing_skill
                        and editing_skill.category
                        in SKILL_CATEGORIES
                    )
                    else "Other"
                )

                category = (
                    st.selectbox(
                        "Category",
                        SKILL_CATEGORIES,
                        index=(
                            SKILL_CATEGORIES.index(
                                current_category
                            )
                        ),
                    )
                )

            with col2:

                current_level = (
                    editing_skill.level
                    if (
                        editing_skill
                        and editing_skill.level
                        in SKILL_LEVELS
                    )
                    else "Beginner"
                )

                level = (
                    st.selectbox(
                        "Skill Level",
                        SKILL_LEVELS,
                        index=(
                            SKILL_LEVELS.index(
                                current_level
                            )
                        ),
                    )
                )

            # ====================================================
            # YEARS
            # ====================================================

            current_years = 0.0

            if editing_skill:

                current_years = float(
                    editing_skill.years_used
                    or 0
                )

            years_used = (
                st.number_input(
                    "Years Used",
                    min_value=0.0,
                    step=0.5,
                    format="%.1f",
                    value=current_years,
                )
            )

            # ====================================================
            # QUALIFICATION
            # ====================================================

            qualification = (
                st.text_input(
                    "Qualification / Certification",
                    value=(
                        editing_skill.qualification
                        if editing_skill
                        else ""
                    ),
                    placeholder=(
                        "Example: Microsoft "
                        "Excel Certification"
                    ),
                )
            )

            # ====================================================
            # NOTES
            # ====================================================

            notes = st.text_area(
                "Notes",
                value=(
                    editing_skill.notes
                    if editing_skill
                    else ""
                ),
                placeholder=(
                    "Additional information "
                    "about this skill..."
                ),
            )

            # ====================================================
            # SUBMIT
            # ====================================================

            submitted = (
                st.form_submit_button(
                    "Save Changes"
                    if editing_skill
                    else "Add Skill",
                    use_container_width=True,
                )
            )

            # ====================================================
            # SAVE
            # ====================================================

            if submitted:

                skill_clean = clean_text(
                    skill_name
                )

                qualification_clean = (
                    clean_text(
                        qualification
                    )
                )

                notes_clean = clean_text(
                    notes
                )

                # =================================================
                # VALIDATION
                # =================================================

                if not skill_clean:

                    st.error(
                        "Skill name is required."
                    )

                elif years_used < 0:

                    st.error(
                        "Years used cannot be negative."
                    )

                elif (
                    selected_employee_id
                    not in employee_map
                ):

                    st.error(
                        "The selected employee "
                        "could not be found."
                    )

                else:

                    # =============================================
                    # DUPLICATE CHECK
                    # =============================================

                    duplicate = (
                        find_duplicate_skill(
                            session,
                            selected_employee_id,
                            skill_clean,
                            exclude_id=(
                                editing_skill.id
                                if editing_skill
                                else None
                            ),
                        )
                    )

                    if duplicate:

                        employee = (
                            employee_map.get(
                                selected_employee_id
                            )
                        )

                        st.error(
                            f"{employee_name(employee)} "
                            f"already has the skill "
                            f"'{skill_clean}'."
                        )

                    else:

                        # =========================================
                        # DATABASE OPERATION
                        # =========================================

                        try:

                            if editing_skill:

                                # ---------------------------------
                                # UPDATE
                                # ---------------------------------

                                editing_skill.employee_id = (
                                    selected_employee_id
                                )

                                editing_skill.skill = (
                                    skill_clean
                                )

                                editing_skill.category = (
                                    category
                                )

                                editing_skill.level = (
                                    level
                                )

                                editing_skill.years_used = (
                                    years_used
                                )

                                editing_skill.qualification = (
                                    qualification_clean
                                )

                                editing_skill.notes = (
                                    notes_clean
                                )

                                session.commit()

                                st.session_state[
                                    "editing_skill_id"
                                ] = None

                                st.success(
                                    "Employee skill "
                                    "updated successfully."
                                )

                            else:

                                # ---------------------------------
                                # CREATE
                                # ---------------------------------

                                new_skill = (
                                    EmployeeSkill(
                                        employee_id=(
                                            selected_employee_id
                                        ),
                                        skill=(
                                            skill_clean
                                        ),
                                        category=(
                                            category
                                        ),
                                        level=(
                                            level
                                        ),
                                        years_used=(
                                            years_used
                                        ),
                                        qualification=(
                                            qualification_clean
                                        ),
                                        notes=(
                                            notes_clean
                                        ),
                                    )
                                )

                                session.add(
                                    new_skill
                                )

                                session.commit()

                                st.success(
                                    "Employee skill "
                                    "added successfully."
                                )

                            st.rerun()

                        except Exception as error:

                            session.rollback()

                            st.error(
                                "The employee skill "
                                "could not be saved."
                            )

                            st.exception(
                                error
                            )

        # ========================================================
        # SKILL REGISTER
        # ========================================================

        st.divider()

        st.subheader(
            "Employee Skill Register"
        )

        if not skills:

            st.info(
                "No employee skills have "
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
                "Search Skills",
                placeholder=(
                    "Skill, employee, "
                    "qualification..."
                ),
            )

        with col2:

            employee_filter_options = [
                (
                    "All",
                    None,
                )
            ]

            employee_filter_options.extend(
                [
                    (
                        employee_label(
                            employee
                        ),
                        employee.id,
                    )
                    for employee in employees
                ]
            )

            selected_employee_filter = (
                st.selectbox(
                    "Employee",
                    employee_filter_options,
                    format_func=(
                        lambda item:
                        item[0]
                    ),
                )
            )

        with col3:

            category_filter = (
                st.selectbox(
                    "Category",
                    ["All"]
                    + SKILL_CATEGORIES,
                )
            )

        with col4:

            level_filter = (
                st.selectbox(
                    "Level",
                    ["All"]
                    + SKILL_LEVELS,
                )
            )

        # ========================================================
        # FILTER DATA
        # ========================================================

        filtered_skills = list(
            skills
        )

        # ========================================================
        # SEARCH
        # ========================================================

        if search.strip():

            search_text = normalize_text(
                search
            )

            filtered_skills = [
                skill
                for skill
                in filtered_skills
                if search_text
                in skill_search_text(
                    skill,
                    employee_map.get(
                        skill.employee_id
                    ),
                )
            ]

        # ========================================================
        # EMPLOYEE FILTER
        # ========================================================

        selected_employee_filter_id = (
            selected_employee_filter[1]
        )

        if (
            selected_employee_filter_id
            is not None
        ):

            filtered_skills = [
                skill
                for skill
                in filtered_skills
                if skill.employee_id
                == selected_employee_filter_id
            ]

        # ========================================================
        # CATEGORY FILTER
        # ========================================================

        if category_filter != "All":

            filtered_skills = [
                skill
                for skill
                in filtered_skills
                if skill.category
                == category_filter
            ]

        # ========================================================
        # LEVEL FILTER
        # ========================================================

        if level_filter != "All":

            filtered_skills = [
                skill
                for skill
                in filtered_skills
                if skill.level
                == level_filter
            ]

        # ========================================================
        # RESULT COUNT
        # ========================================================

        st.caption(
            f"Showing "
            f"{len(filtered_skills)} "
            f"of "
            f"{len(skills)} "
            f"skill records"
        )

        # ========================================================
        # NO RESULTS
        # ========================================================

        if not filtered_skills:

            st.info(
                "No skills match the "
                "selected filters."
            )

        # ========================================================
        # DISPLAY SKILLS
        # ========================================================

        for skill in filtered_skills:

            employee = employee_map.get(
                skill.employee_id
            )

            skill_display_name = (
                clean_text(
                    skill.skill
                )
                or "Unnamed Skill"
            )

            category_display = (
                clean_text(
                    skill.category
                )
                or "Other"
            )

            level_display = (
                clean_text(
                    skill.level
                )
                or "Not specified"
            )

            qualification_display = (
                clean_text(
                    skill.qualification
                )
            )

            years_display = float(
                skill.years_used or 0
            )

            with st.container(
                border=True
            ):

                col1, col2, col3 = (
                    st.columns(
                        [3, 3, 1]
                    )
                )

                # =================================================
                # SKILL INFORMATION
                # =================================================

                with col1:

                    st.subheader(
                        skill_display_name
                    )

                    st.caption(
                        f"Employee: "
                        f"{employee_name(employee)}"
                    )

                    st.write(
                        f"**Category:** "
                        f"{category_display}"
                    )

                    st.write(
                        f"**Level:** "
                        f"{level_icon(level_display)} "
                        f"{level_display}"
                    )

                # =================================================
                # EXPERIENCE
                # =================================================

                with col2:

                    st.write(
                        f"**Years Used:** "
                        f"{years_display:g}"
                    )

                    if qualification_display:

                        st.write(
                            f"**Qualification:** "
                            f"{qualification_display}"
                        )

                    if skill.notes:

                        st.caption(
                            f"Notes: "
                            f"{clean_text(skill.notes)}"
                        )

                # =================================================
                # ACTIONS
                # =================================================

                with col3:

                    edit_button = st.button(
                        "Edit",
                        key=(
                            f"edit_skill_"
                            f"{skill.id}"
                        ),
                        use_container_width=True,
                    )

                    delete_button = st.button(
                        "Delete",
                        key=(
                            f"delete_skill_"
                            f"{skill.id}"
                        ),
                        use_container_width=True,
                    )

                # =================================================
                # EDIT
                # =================================================

                if edit_button:

                    st.session_state[
                        "editing_skill_id"
                    ] = skill.id

                    st.session_state[
                        "confirm_delete_skill_id"
                    ] = None

                    st.rerun()

                # =================================================
                # DELETE REQUEST
                # =================================================

                if delete_button:

                    st.session_state[
                        "confirm_delete_skill_id"
                    ] = skill.id

                    st.rerun()

                # =================================================
                # DELETE CONFIRMATION
                # =================================================

                if (
                    st.session_state[
                        "confirm_delete_skill_id"
                    ]
                    == skill.id
                ):

                    st.warning(
                        f"Are you sure you want to "
                        f"delete the skill "
                        f"**{skill_display_name}** "
                        f"from "
                        f"**{employee_name(employee)}**?"
                    )

                    confirm_col1, confirm_col2 = (
                        st.columns(2)
                    )

                    with confirm_col1:

                        confirm_delete = (
                            st.button(
                                "Yes, Delete Skill",
                                key=(
                                    f"confirm_delete_"
                                    f"skill_{skill.id}"
                                ),
                                type="primary",
                                use_container_width=True,
                            )
                        )

                    with confirm_col2:

                        cancel_delete = (
                            st.button(
                                "Cancel",
                                key=(
                                    f"cancel_delete_"
                                    f"skill_{skill.id}"
                                ),
                                use_container_width=True,
                            )
                        )

                    # =============================================
                    # CANCEL DELETE
                    # =============================================

                    if cancel_delete:

                        st.session_state[
                            "confirm_delete_skill_id"
                        ] = None

                        st.rerun()

                    # =============================================
                    # CONFIRM DELETE
                    # =============================================

                    if confirm_delete:

                        try:

                            session.delete(
                                skill
                            )

                            session.commit()

                            st.session_state[
                                "confirm_delete_skill_id"
                            ] = None

                            if (
                                st.session_state[
                                    "editing_skill_id"
                                ]
                                == skill.id
                            ):

                                st.session_state[
                                    "editing_skill_id"
                                ] = None

                            st.success(
                                "Employee skill "
                                "deleted successfully."
                            )

                            st.rerun()

                        except Exception as error:

                            session.rollback()

                            st.error(
                                "The skill could "
                                "not be deleted."
                            )

                            st.exception(
                                error
                            )

    except Exception as error:

        session.rollback()

        st.error(
            "An error occurred while loading "
            "the Employee Skills screen."
        )

        st.exception(
            error
        )

    finally:

        session.close()