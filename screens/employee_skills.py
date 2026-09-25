import streamlit as st

from database import get_session
from models import Employee, EmployeeSkill


def show_employee_skills():

    st.title("Employee Skills")
    st.caption("Manage skills, qualifications and experience for remote workers.")

    session = get_session()

    employees = session.query(Employee).order_by(
        Employee.first_name,
        Employee.last_name
    ).all()

    if not employees:
        st.warning("Please add an employee first.")
        session.close()
        return

    # ============================================================
    # ADD SKILL
    # ============================================================

    st.subheader("Add Employee Skill")

    with st.form("add_employee_skill_form"):

        employee_options = {
            f"{employee.first_name} "
            f"{employee.last_name or ''} "
            f"(ID: {employee.id})": employee.id
            for employee in employees
        }

        selected_employee = st.selectbox(
            "Employee",
            list(employee_options.keys())
        )

        skill = st.text_input(
            "Skill",
            placeholder="Example: Excel"
        )

        category = st.selectbox(
            "Category",
            [
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
        )

        level = st.selectbox(
            "Skill Level",
            [
                "Beginner",
                "Intermediate",
                "Advanced",
                "Expert"
            ]
        )

        years_used = st.number_input(
            "Years Used",
            min_value=0.0,
            step=0.5,
            format="%.1f"
        )

        qualification = st.text_input(
            "Qualification",
            placeholder="Example: Microsoft Excel certification"
        )

        notes = st.text_area(
            "Notes"
        )

        submitted = st.form_submit_button(
            "Add Skill",
            use_container_width=True
        )

        if submitted:

            if not skill.strip():

                st.error("Skill is required.")

            else:

                employee_id = employee_options[selected_employee]

                employee_skill = EmployeeSkill(
                    employee_id=employee_id,
                    skill=skill.strip(),
                    category=category,
                    level=level,
                    years_used=years_used,
                    qualification=qualification.strip(),
                    notes=notes.strip()
                )

                session.add(employee_skill)
                session.commit()

                st.success(
                    "Employee skill added successfully."
                )

                st.rerun()

    # ============================================================
    # SKILL REGISTER
    # ============================================================

    st.divider()

    st.subheader("Skill Register")

    skills = session.query(EmployeeSkill).order_by(
        EmployeeSkill.skill
    ).all()

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
            [
                "All",
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
        )

    with col3:

        level_filter = st.selectbox(
            "Level",
            [
                "All",
                "Beginner",
                "Intermediate",
                "Advanced",
                "Expert"
            ]
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
    # DISPLAY
    # ============================================================

    if not filtered_skills:

        st.info(
            "No skills match your filters."
        )

    else:

        for item in filtered_skills:

            employee_name = "Unknown Employee"

            if item.employee:

                employee_name = (
                    f"{item.employee.first_name} "
                    f"{item.employee.last_name or ''}"
                ).strip()

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(
                    [2, 3, 2, 2]
                )

                with col1:

                    st.write(
                        f"**{employee_name}**"
                    )

                with col2:

                    st.write(
                        f"**{item.skill}**"
                    )

                    st.caption(
                        item.category or ""
                    )

                with col3:

                    st.write(
                        f"Level: **{item.level}**"
                    )

                    st.caption(
                        f"Experience: "
                        f"{item.years_used or 0:g} years"
                    )

                with col4:

                    if item.qualification:

                        st.write(
                            f"**{item.qualification}**"
                        )

                if item.notes:

                    st.caption(
                        f"Notes: {item.notes}"
                    )

    session.close()