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

EXPERIENCE_FILTERS = [
    "All",
    "No Experience Recorded",
    "1+ Years",
    "3+ Years",
    "5+ Years",
    "10+ Years",
]

SORT_OPTIONS = [
    "Employee A-Z",
    "Employee Z-A",
    "Skill A-Z",
    "Skill Z-A",
    "Highest Level",
    "Lowest Level",
    "Most Experience",
    "Least Experience",
    "Newest",
    "Oldest",
]


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    """Safely clean a text value."""

    if value is None:
        return ""

    return str(value).strip()


def normalize_text(value):
    """Normalize text for searching and duplicate detection."""

    return " ".join(
        clean_text(value).lower().split()
    )


def employee_name(employee):
    """Return an employee's full name safely."""

    if employee is None:
        return "Unknown Employee"

    first_name = clean_text(
        getattr(employee, "first_name", "")
    )

    last_name = clean_text(
        getattr(employee, "last_name", "")
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


def employee_label(employee):
    """Return employee name with ID."""

    employee_id = getattr(
        employee,
        "id",
        None,
    )

    if employee_id is None:
        return employee_name(employee)

    return (
        f"{employee_name(employee)} "
        f"(ID: {employee_id})"
    )


def employee_role(employee):
    """Return employee role safely."""

    if employee is None:
        return ""

    return clean_text(
        getattr(
            employee,
            "role",
            "",
        )
    )


def level_icon(level):
    """Return a visual indicator for skill level."""

    icons = {
        "Beginner": "🟢",
        "Intermediate": "🔵",
        "Advanced": "🟠",
        "Expert": "🔴",
    }

    return icons.get(
        clean_text(level),
        "⚪",
    )


def level_rank(level):
    """Return numeric ranking for skill level."""

    return {
        "Beginner": 1,
        "Intermediate": 2,
        "Advanced": 3,
        "Expert": 4,
    }.get(
        clean_text(level),
        0,
    )


def safe_years_used(skill):
    """Return years_used as a safe non-negative float."""

    if skill is None:
        return 0.0

    try:

        value = float(
            getattr(
                skill,
                "years_used",
                0,
            )
            or 0
        )

        if value < 0:
            return 0.0

        return value

    except (
        TypeError,
        ValueError,
    ):

        return 0.0


def skill_search_text(skill, employee):
    """Build searchable text for a skill."""

    if skill is None:
        return ""

    values = [
        getattr(skill, "skill", ""),
        getattr(skill, "category", ""),
        getattr(skill, "level", ""),
        getattr(skill, "qualification", ""),
        getattr(skill, "notes", ""),
    ]

    if employee is not None:

        values.extend(
            [
                getattr(employee, "first_name", ""),
                getattr(employee, "last_name", ""),
                getattr(employee, "role", ""),
            ]
        )

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

    Comparison is case-insensitive and
    whitespace-normalized.
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
            and existing_skill.id
            == exclude_id
        ):
            continue

        existing_name = normalize_text(
            getattr(
                existing_skill,
                "skill",
                "",
            )
        )

        if (
            existing_name
            == normalized_skill
        ):
            return existing_skill

    return None


def get_average_years(skills):
    """Calculate average recorded years."""

    years = [
        safe_years_used(skill)
        for skill in skills
        if safe_years_used(skill) > 0
    ]

    if not years:
        return 0.0

    return sum(years) / len(years)


def get_total_years(skills):
    """Calculate total recorded years."""

    return sum(
        safe_years_used(skill)
        for skill in skills
    )


def get_unique_skill_count(skills):
    """Return unique skill names."""

    return len(
        {
            normalize_text(
                getattr(skill, "skill", "")
            )
            for skill in skills
            if normalize_text(
                getattr(skill, "skill", "")
            )
        }
    )


def get_highest_level(skills):
    """Return highest represented skill level."""

    highest = None
    highest_rank = 0

    for skill in skills:

        current_level = clean_text(
            getattr(
                skill,
                "level",
                "",
            )
        )

        current_rank = level_rank(
            current_level
        )

        if current_rank > highest_rank:

            highest = current_level
            highest_rank = current_rank

    return highest


def get_level_counts(skills):
    """Return counts by skill level."""

    counts = {
        level: 0
        for level in SKILL_LEVELS
    }

    for skill in skills:

        level = clean_text(
            getattr(
                skill,
                "level",
                "",
            )
        )

        if level in counts:
            counts[level] += 1

    return counts


def get_category_counts(skills):
    """Return counts by category."""

    counts = {}

    for skill in skills:

        category = (
            clean_text(
                getattr(
                    skill,
                    "category",
                    "",
                )
            )
            or "Other"
        )

        counts[category] = (
            counts.get(
                category,
                0,
            )
            + 1
        )

    return counts


def get_employee_skill_count(
    skills,
    employee_id,
):
    """Return number of skills for employee."""

    return sum(
        1
        for skill in skills
        if skill.employee_id
        == employee_id
    )


def get_employee_skills(
    skills,
    employee_id,
):
    """Return skills belonging to employee."""

    return [
        skill
        for skill in skills
        if skill.employee_id
        == employee_id
    ]


def get_employee_level_summary(
    skills,
    employee_id,
):
    """Return level summary for employee."""

    employee_skills = get_employee_skills(
        skills,
        employee_id,
    )

    return get_level_counts(
        employee_skills
    )


def get_experience_label(years):
    """Return readable experience label."""

    if years <= 0:
        return "No experience recorded"

    if years == 1:
        return "1 year"

    return f"{years:g} years"


def sort_skills(
    skills,
    employee_map,
    sort_option,
):
    """Sort skill records for display."""

    skills = list(skills)

    if sort_option == "Employee A-Z":

        return sorted(
            skills,
            key=lambda skill: (
                employee_name(
                    employee_map.get(
                        skill.employee_id
                    )
                ).lower(),
                normalize_text(
                    getattr(
                        skill,
                        "skill",
                        "",
                    )
                ),
            ),
        )

    if sort_option == "Employee Z-A":

        return sorted(
            skills,
            key=lambda skill: (
                employee_name(
                    employee_map.get(
                        skill.employee_id
                    )
                ).lower(),
                normalize_text(
                    getattr(
                        skill,
                        "skill",
                        "",
                    )
                ),
            ),
            reverse=True,
        )

    if sort_option == "Skill A-Z":

        return sorted(
            skills,
            key=lambda skill: normalize_text(
                getattr(
                    skill,
                    "skill",
                    "",
                )
            ),
        )

    if sort_option == "Skill Z-A":

        return sorted(
            skills,
            key=lambda skill: normalize_text(
                getattr(
                    skill,
                    "skill",
                    "",
                )
            ),
            reverse=True,
        )

    if sort_option == "Highest Level":

        return sorted(
            skills,
            key=lambda skill: (
                level_rank(
                    getattr(
                        skill,
                        "level",
                        "",
                    )
                ),
                safe_years_used(skill),
            ),
            reverse=True,
        )

    if sort_option == "Lowest Level":

        return sorted(
            skills,
            key=lambda skill: (
                level_rank(
                    getattr(
                        skill,
                        "level",
                        "",
                    )
                ),
                safe_years_used(skill),
            ),
        )

    if sort_option == "Most Experience":

        return sorted(
            skills,
            key=lambda skill: (
                safe_years_used(skill),
                level_rank(
                    getattr(
                        skill,
                        "level",
                        "",
                    )
                ),
            ),
            reverse=True,
        )

    if sort_option == "Least Experience":

        return sorted(
            skills,
            key=lambda skill: (
                safe_years_used(skill),
                level_rank(
                    getattr(
                        skill,
                        "level",
                        "",
                    )
                ),
            ),
        )

    if sort_option == "Newest":

        return sorted(
            skills,
            key=lambda skill: getattr(
                skill,
                "id",
                0,
            ),
            reverse=True,
        )

    return sorted(
        skills,
        key=lambda skill: getattr(
            skill,
            "id",
            0,
        ),
    )


def validate_skill_name(skill_name):
    """Validate skill name."""

    skill_name = clean_text(
        skill_name
    )

    if not skill_name:
        return (
            False,
            "Skill name is required.",
        )

    if len(skill_name) > 150:
        return (
            False,
            "Skill name is too long. "
            "Please use 150 characters or fewer.",
        )

    return True, ""


def validate_years(years_used):
    """Validate years of experience."""

    try:

        value = float(
            years_used
        )

    except (
        TypeError,
        ValueError,
    ):

        return (
            False,
            "Years used must be a valid number.",
        )

    if value < 0:

        return (
            False,
            "Years used cannot be negative.",
        )

    if value > 100:

        return (
            False,
            "Years used cannot exceed 100 years.",
        )

    return True, ""


def validate_qualification(
    qualification,
):
    """Validate qualification length."""

    qualification = clean_text(
        qualification
    )

    if len(qualification) > 255:

        return (
            False,
            "Qualification / certification "
            "is too long. Maximum 255 characters.",
        )

    return True, ""


def validate_notes(notes):
    """Validate notes length."""

    notes = clean_text(
        notes
    )

    if len(notes) > 5000:

        return (
            False,
            "Notes are too long. "
            "Maximum 5,000 characters.",
        )

    return True, ""


def clear_edit_state():
    """Clear current edit state."""

    st.session_state[
        "editing_skill_id"
    ] = None


def clear_delete_state():
    """Clear current delete state."""

    st.session_state[
        "confirm_delete_skill_id"
    ] = None


def reset_skill_states():
    """Clear edit and delete states."""

    clear_edit_state()
    clear_delete_state()


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

            st.session_state[
                "editing_skill_id"
            ] = None

        if (
            "confirm_delete_skill_id"
            not in st.session_state
        ):

            st.session_state[
                "confirm_delete_skill_id"
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
        # LOAD SKILLS
        # ========================================================

        skills = (
            session.query(EmployeeSkill)
            .order_by(
                EmployeeSkill.id.desc()
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
        # CURRENT EDITING SKILL
        # ========================================================

        editing_skill = None

        editing_skill_id = (
            st.session_state[
                "editing_skill_id"
            ]
        )

        if editing_skill_id is not None:

            editing_skill = session.get(
                EmployeeSkill,
                editing_skill_id,
            )

            if editing_skill is None:

                clear_edit_state()

        # ========================================================
        # CURRENT DELETE TARGET
        # ========================================================

        delete_skill_id = (
            st.session_state[
                "confirm_delete_skill_id"
            ]
        )

        if delete_skill_id is not None:

            delete_target = session.get(
                EmployeeSkill,
                delete_skill_id,
            )

            if delete_target is None:

                clear_delete_state()

        # ========================================================
        # GLOBAL KPIs
        # ========================================================

        total_skills = len(skills)

        employees_with_skills = len(
            {
                skill.employee_id
                for skill in skills
                if skill.employee_id is not None
                and skill.employee_id in employee_map
            }
        )

        employees_without_skills = max(
            len(employees)
            - employees_with_skills,
            0,
        )

        unique_skills = (
            get_unique_skill_count(
                skills
            )
        )

        advanced_expert = sum(
            1
            for skill in skills
            if clean_text(
                getattr(
                    skill,
                    "level",
                    "",
                )
            )
            in {
                "Advanced",
                "Expert",
            }
        )

        expert_skills = sum(
            1
            for skill in skills
            if clean_text(
                getattr(
                    skill,
                    "level",
                    "",
                )
            )
            == "Expert"
        )

        average_years = (
            get_average_years(
                skills
            )
        )

        total_years = (
            get_total_years(
                skills
            )
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

        # ========================================================
        # SECONDARY SUMMARY
        # ========================================================

        summary_col1, summary_col2, summary_col3, summary_col4 = (
            st.columns(4)
        )

        with summary_col1:

            st.caption(
                f"Expert skills: **{expert_skills}**"
            )

        with summary_col2:

            st.caption(
                f"Total experience: "
                f"**{total_years:.1f} years**"
            )

        with summary_col3:

            st.caption(
                f"Employees without skills: "
                f"**{employees_without_skills}**"
            )

        with summary_col4:

            coverage = (
                (
                    employees_with_skills
                    / len(employees)
                    * 100
                )
                if employees
                else 0
            )

            st.caption(
                f"Skill coverage: "
                f"**{coverage:.1f}%**"
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

                category_counts = (
                    get_category_counts(
                        skills
                    )
                )

                level_counts = (
                    get_level_counts(
                        skills
                    )
                )

                # ------------------------------------------------
                # CATEGORY SUMMARY
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
                    (
                        -item[1],
                        item[0].lower(),
                    ),
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

                st.divider()

                # ------------------------------------------------
                # LEVEL SUMMARY
                # ------------------------------------------------

                st.write(
                    "**Skills by Level**"
                )

                level_columns = (
                    st.columns(4)
                )

                for index, level in enumerate(
                    SKILL_LEVELS
                ):

                    with level_columns[
                        index % 4
                    ]:

                        st.metric(
                            f"{level_icon(level)} {level}",
                            level_counts.get(
                                level,
                                0,
                            ),
                        )

        # ========================================================
        # EMPLOYEE CHECK
        # ========================================================

        if not employees:

            st.subheader(
                "Add Employee Skill"
            )

            st.warning(
                "You need to add employees "
                "before adding skills."
            )

            return

        # ========================================================
        # FORM HEADING
        # ========================================================

        if editing_skill:

            st.subheader(
                "Edit Employee Skill"
            )

            st.caption(
                f"Editing skill ID "
                f"{editing_skill.id}"
            )

        else:

            st.subheader(
                "Add Employee Skill"
            )

        # ========================================================
        # SKILL FORM
        # ========================================================

        with st.form(
            "employee_skill_form",
            clear_on_submit=False,
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
                    clean_text(
                        getattr(
                            editing_skill,
                            "skill",
                            "",
                        )
                    )
                    if editing_skill
                    else ""
                ),
                placeholder=(
                    "Example: Excel, SQL, "
                    "Financial Analysis"
                ),
                max_chars=150,
            )

            # ====================================================
            # CATEGORY / LEVEL
            # ====================================================

            col1, col2 = st.columns(2)

            with col1:

                current_category = (
                    clean_text(
                        getattr(
                            editing_skill,
                            "category",
                            "",
                        )
                    )
                    if editing_skill
                    else ""
                )

                if (
                    current_category
                    not in SKILL_CATEGORIES
                ):

                    current_category = "Other"

                category = st.selectbox(
                    "Category",
                    SKILL_CATEGORIES,
                    index=(
                        SKILL_CATEGORIES.index(
                            current_category
                        )
                    ),
                )

            with col2:

                current_level = (
                    clean_text(
                        getattr(
                            editing_skill,
                            "level",
                            "",
                        )
                    )
                    if editing_skill
                    else ""
                )

                if (
                    current_level
                    not in SKILL_LEVELS
                ):

                    current_level = "Beginner"

                level = st.selectbox(
                    "Skill Level",
                    SKILL_LEVELS,
                    index=(
                        SKILL_LEVELS.index(
                            current_level
                        )
                    ),
                    format_func=(
                        lambda value:
                        f"{level_icon(value)} "
                        f"{value}"
                    ),
                )

            # ====================================================
            # YEARS
            # ====================================================

            current_years = (
                safe_years_used(
                    editing_skill
                )
                if editing_skill
                else 0.0
            )

            years_used = st.number_input(
                "Years Used",
                min_value=0.0,
                max_value=100.0,
                step=0.5,
                format="%.1f",
                value=current_years,
            )

            # ====================================================
            # QUALIFICATION
            # ====================================================

            qualification = st.text_input(
                "Qualification / Certification",
                value=(
                    clean_text(
                        getattr(
                            editing_skill,
                            "qualification",
                            "",
                        )
                    )
                    if editing_skill
                    else ""
                ),
                placeholder=(
                    "Example: Microsoft "
                    "Excel Certification"
                ),
                max_chars=255,
            )

            # ====================================================
            # NOTES
            # ====================================================

            notes = st.text_area(
                "Notes",
                value=(
                    clean_text(
                        getattr(
                            editing_skill,
                            "notes",
                            "",
                        )
                    )
                    if editing_skill
                    else ""
                ),
                placeholder=(
                    "Additional information "
                    "about this skill..."
                ),
                max_chars=5000,
            )

            # ====================================================
            # FORM BUTTONS
            # ====================================================

            col1, col2 = st.columns(2)

            with col1:

                submitted = (
                    st.form_submit_button(
                        "Save Changes"
                        if editing_skill
                        else "Add Skill",
                        type="primary",
                        use_container_width=True,
                    )
                )

            with col2:

                cancel_edit = False

                if editing_skill:

                    cancel_edit = (
                        st.form_submit_button(
                            "Cancel",
                            use_container_width=True,
                        )
                    )

            # ====================================================
            # CANCEL EDIT
            # ====================================================

            if cancel_edit:

                reset_skill_states()

                st.rerun()

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

                # ===============================================
                # VALIDATE SKILL
                # ===============================================

                skill_valid, skill_error = (
                    validate_skill_name(
                        skill_clean
                    )
                )

                if not skill_valid:

                    st.error(
                        skill_error
                    )

                else:

                    # =============================================
                    # VALIDATE YEARS
                    # =============================================

                    years_valid, years_error = (
                        validate_years(
                            years_used
                        )
                    )

                    if not years_valid:

                        st.error(
                            years_error
                        )

                    else:

                        # =========================================
                        # VALIDATE QUALIFICATION
                        # =========================================

                        qualification_valid, qualification_error = (
                            validate_qualification(
                                qualification_clean
                            )
                        )

                        if not qualification_valid:

                            st.error(
                                qualification_error
                            )

                        else:

                            # =====================================
                            # VALIDATE NOTES
                            # =====================================

                            notes_valid, notes_error = (
                                validate_notes(
                                    notes_clean
                                )
                            )

                            if not notes_valid:

                                st.error(
                                    notes_error
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

                                # =================================
                                # DUPLICATE CHECK
                                # =================================

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

                                    # =============================
                                    # DATABASE OPERATION
                                    # =============================

                                    try:

                                        if editing_skill:

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
                                                float(
                                                    years_used
                                                )
                                            )

                                            editing_skill.qualification = (
                                                qualification_clean
                                            )

                                            editing_skill.notes = (
                                                notes_clean
                                            )

                                            session.commit()

                                            reset_skill_states()

                                            st.success(
                                                "Employee skill "
                                                "updated successfully."
                                            )

                                        else:

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
                                                        float(
                                                            years_used
                                                        )
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

                                            clear_delete_state()

                                            st.success(
                                                "Employee skill "
                                                "added successfully."
                                            )

                                        st.rerun()

                                    except Exception:

                                        session.rollback()

                                        st.error(
                                            "The employee skill "
                                            "could not be saved. "
                                            "Please check the information "
                                            "and try again."
                                        )

        # ========================================================
        # REGISTER
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

        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:

            search = st.text_input(
                "Search",
                placeholder=(
                    "Skill, employee, role, "
                    "qualification..."
                ),
            )

        with col2:

            employee_filter_options = [
                (
                    "All Employees",
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

        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:

            level_filter = (
                st.selectbox(
                    "Level",
                    ["All"]
                    + SKILL_LEVELS,
                )
            )

        with col2:

            experience_filter = (
                st.selectbox(
                    "Experience",
                    EXPERIENCE_FILTERS,
                )
            )

        with col3:

            sort_option = (
                st.selectbox(
                    "Sort By",
                    SORT_OPTIONS,
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
                if (
                    clean_text(
                        getattr(
                            skill,
                            "category",
                            "",
                        )
                    )
                    or "Other"
                )
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
                if clean_text(
                    getattr(
                        skill,
                        "level",
                        "",
                    )
                )
                == level_filter
            ]

        # ========================================================
        # EXPERIENCE FILTER
        # ========================================================

        if (
            experience_filter
            != "All"
        ):

            if (
                experience_filter
                == "No Experience Recorded"
            ):

                filtered_skills = [
                    skill
                    for skill
                    in filtered_skills
                    if safe_years_used(
                        skill
                    )
                    == 0
                ]

            elif (
                experience_filter
                == "1+ Years"
            ):

                filtered_skills = [
                    skill
                    for skill
                    in filtered_skills
                    if safe_years_used(
                        skill
                    )
                    >= 1
                ]

            elif (
                experience_filter
                == "3+ Years"
            ):

                filtered_skills = [
                    skill
                    for skill
                    in filtered_skills
                    if safe_years_used(
                        skill
                    )
                    >= 3
                ]

            elif (
                experience_filter
                == "5+ Years"
            ):

                filtered_skills = [
                    skill
                    for skill
                    in filtered_skills
                    if safe_years_used(
                        skill
                    )
                    >= 5
                ]

            elif (
                experience_filter
                == "10+ Years"
            ):

                filtered_skills = [
                    skill
                    for skill
                    in filtered_skills
                    if safe_years_used(
                        skill
                    )
                    >= 10
                ]

        # ========================================================
        # SORT
        # ========================================================

        filtered_skills = sort_skills(
            filtered_skills,
            employee_map,
            sort_option,
        )

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
        # FILTERED SUMMARY
        # ========================================================

        if filtered_skills:

            filtered_years = (
                get_total_years(
                    filtered_skills
                )
            )

            filtered_average = (
                get_average_years(
                    filtered_skills
                )
            )

            filtered_unique = (
                get_unique_skill_count(
                    filtered_skills
                )
            )

            filtered_expert = sum(
                1
                for skill in filtered_skills
                if clean_text(
                    getattr(
                        skill,
                        "level",
                        "",
                    )
                )
                == "Expert"
            )

            summary_col1, summary_col2, summary_col3, summary_col4 = (
                st.columns(4)
            )

            with summary_col1:

                st.metric(
                    "Filtered Skills",
                    len(filtered_skills),
                )

            with summary_col2:

                st.metric(
                    "Unique Skills",
                    filtered_unique,
                )

            with summary_col3:

                st.metric(
                    "Experience",
                    f"{filtered_years:.1f} yrs",
                )

            with summary_col4:

                st.metric(
                    "Expert",
                    filtered_expert,
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
                    getattr(
                        skill,
                        "skill",
                        "",
                    )
                )
                or "Unnamed Skill"
            )

            category_display = (
                clean_text(
                    getattr(
                        skill,
                        "category",
                        "",
                    )
                )
                or "Other"
            )

            level_display = (
                clean_text(
                    getattr(
                        skill,
                        "level",
                        "",
                    )
                )
                or "Not specified"
            )

            qualification_display = (
                clean_text(
                    getattr(
                        skill,
                        "qualification",
                        "",
                    )
                )
            )

            notes_display = (
                clean_text(
                    getattr(
                        skill,
                        "notes",
                        "",
                    )
                )
            )

            years_display = (
                safe_years_used(
                    skill
                )
            )

            is_currently_editing = (
                st.session_state[
                    "editing_skill_id"
                ]
                == skill.id
            )

            is_delete_pending = (
                st.session_state[
                    "confirm_delete_skill_id"
                ]
                == skill.id
            )

            with st.container(
                border=True
            ):

                # =================================================
                # HEADER
                # =================================================

                header_col1, header_col2 = (
                    st.columns(
                        [5, 1]
                    )
                )

                with header_col1:

                    st.subheader(
                        skill_display_name
                    )

                    st.caption(
                        f"👤 {employee_name(employee)}"
                    )

                with header_col2:

                    st.markdown(
                        f"### {level_icon(level_display)}"
                    )

                    st.caption(
                        level_display
                    )

                # =================================================
                # MAIN INFORMATION
                # =================================================

                col1, col2, col3 = (
                    st.columns(
                        [2, 3, 1]
                    )
                )

                with col1:

                    st.write(
                        f"**Category**  \n"
                        f"{category_display}"
                    )

                    role = employee_role(
                        employee
                    )

                    if role:

                        st.write(
                            f"**Employee Role**  \n"
                            f"{role}"
                        )

                with col2:

                    st.write(
                        f"**Experience**  \n"
                        f"{get_experience_label(years_display)}"
                    )

                    if qualification_display:

                        st.write(
                            f"**Qualification**  \n"
                            f"{qualification_display}"
                        )

                    if notes_display:

                        st.caption(
                            f"**Notes:** "
                            f"{notes_display}"
                        )

                with col3:

                    edit_button = st.button(
                        "Edit",
                        key=(
                            f"edit_skill_"
                            f"{skill.id}"
                        ),
                        use_container_width=True,
                        disabled=(
                            is_currently_editing
                        ),
                    )

                    delete_button = st.button(
                        "Delete",
                        key=(
                            f"delete_skill_"
                            f"{skill.id}"
                        ),
                        use_container_width=True,
                        disabled=(
                            is_currently_editing
                        ),
                    )

                # =================================================
                # EDIT
                # =================================================

                if edit_button:

                    st.session_state[
                        "editing_skill_id"
                    ] = skill.id

                    clear_delete_state()

                    st.rerun()

                # =================================================
                # DELETE REQUEST
                # =================================================

                if delete_button:

                    clear_edit_state()

                    st.session_state[
                        "confirm_delete_skill_id"
                    ] = skill.id

                    st.rerun()

                # =================================================
                # DELETE CONFIRMATION
                # =================================================

                if is_delete_pending:

                    st.warning(
                        f"Are you sure you want to "
                        f"delete **{skill_display_name}** "
                        f"from **{employee_name(employee)}**?"
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

                        clear_delete_state()

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

                            clear_delete_state()

                            if (
                                st.session_state[
                                    "editing_skill_id"
                                ]
                                == skill.id
                            ):

                                clear_edit_state()

                            st.success(
                                "Employee skill "
                                "deleted successfully."
                            )

                            st.rerun()

                        except Exception:

                            session.rollback()

                            clear_delete_state()

                            st.error(
                                "The skill could not "
                                "be deleted. The record "
                                "may be used by another "
                                "database record."
                            )

    except Exception:

        session.rollback()

        st.error(
            "An error occurred while loading "
            "the Employee Skills screen."
        )

    finally:

        session.close()