import streamlit as st
from datetime import date

from database import get_session
from models import Activity, Client


def show_activities():

    st.title("Activities & Follow-Ups")
    st.caption("Manage client calls, emails, meetings, proposals and follow-ups.")

    session = get_session()

    # ============================================================
    # CHECK CLIENTS
    # ============================================================

    clients = session.query(Client).order_by(
        Client.company_name
    ).all()

    if not clients:
        st.warning("Please add a client first.")
        session.close()
        return

    # ============================================================
    # ADD ACTIVITY
    # ============================================================

    st.subheader("Add Activity")

    with st.form("add_activity_form"):

        client_options = {
            f"{client.company_name} (ID: {client.id})": client.id
            for client in clients
        }

        selected_client = st.selectbox(
            "Client",
            list(client_options.keys())
        )

        activity_type = st.selectbox(
            "Activity Type",
            [
                "Call",
                "Email",
                "Meeting",
                "LinkedIn",
                "Proposal",
                "Follow-Up",
                "Negotiation",
                "Contract",
                "Other"
            ]
        )

        subject = st.text_input(
            "Subject",
            placeholder="Example: Follow up regarding finance outsourcing proposal"
        )

        col1, col2 = st.columns(2)

        with col1:
            activity_date = st.date_input(
                "Activity Date",
                value=date.today()
            )

        with col2:
            due_date = st.date_input(
                "Follow-Up / Due Date",
                value=date.today()
            )

        col3, col4 = st.columns(2)

        with col3:
            status = st.selectbox(
                "Status",
                [
                    "Open",
                    "Completed",
                    "Waiting",
                    "Cancelled"
                ]
            )

        with col4:
            priority = st.selectbox(
                "Priority",
                [
                    "Low",
                    "Medium",
                    "High",
                    "Urgent"
                ]
            )

        assigned_to = st.text_input(
            "Assigned To",
            placeholder="Example: Sandra"
        )

        notes = st.text_area(
            "Notes",
            placeholder="Enter details about the activity..."
        )

        submitted = st.form_submit_button(
            "Add Activity",
            use_container_width=True
        )

        if submitted:

            if not subject.strip():
                st.error("Subject is required.")

            else:

                activity = Activity(
                    client_id=client_options[selected_client],
                    activity_type=activity_type,
                    subject=subject.strip(),
                    activity_date=activity_date,
                    due_date=due_date,
                    status=status,
                    priority=priority,
                    assigned_to=assigned_to.strip(),
                    notes=notes.strip()
                )

                session.add(activity)
                session.commit()

                st.success("Activity added successfully.")
                st.rerun()

    # ============================================================
    # ACTIVITY LIST
    # ============================================================

    st.divider()

    st.subheader("Activity History")

    activities = session.query(Activity).order_by(
        Activity.activity_date.desc(),
        Activity.id.desc()
    ).all()

    if not activities:
        st.info("No activities have been added yet.")
        session.close()
        return

    # ============================================================
    # FILTERS
    # ============================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        search = st.text_input(
            "Search",
            placeholder="Search subject or notes..."
        )

    with col2:

        type_filter = st.selectbox(
            "Activity Type",
            [
                "All",
                "Call",
                "Email",
                "Meeting",
                "LinkedIn",
                "Proposal",
                "Follow-Up",
                "Negotiation",
                "Contract",
                "Other"
            ]
        )

    with col3:

        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Open",
                "Completed",
                "Waiting",
                "Cancelled"
            ]
        )

    # ============================================================
    # APPLY FILTERS
    # ============================================================

    filtered_activities = activities

    if search:

        search_lower = search.lower()

        filtered_activities = [
            activity
            for activity in filtered_activities
            if (
                search_lower in (activity.subject or "").lower()
                or search_lower in (activity.notes or "").lower()
            )
        ]

    if type_filter != "All":

        filtered_activities = [
            activity
            for activity in filtered_activities
            if activity.activity_type == type_filter
        ]

    if status_filter != "All":

        filtered_activities = [
            activity
            for activity in filtered_activities
            if activity.status == status_filter
        ]

    # ============================================================
    # DISPLAY
    # ============================================================

    if not filtered_activities:

        st.info("No activities match your filters.")

    else:

        for activity in filtered_activities:

            client_name = (
                activity.client.company_name
                if activity.client
                else "Unknown Client"
            )

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(
                    [2, 3, 2, 2]
                )

                with col1:

                    st.write(
                        f"**{activity.activity_type}**"
                    )

                    st.caption(
                        activity.activity_date.strftime("%d %b %Y")
                        if activity.activity_date
                        else ""
                    )

                with col2:

                    st.write(
                        f"**{activity.subject}**"
                    )

                    st.caption(client_name)

                with col3:

                    st.write(
                        f"Status: **{activity.status}**"
                    )

                    st.write(
                        f"Priority: **{activity.priority}**"
                    )

                with col4:

                    if activity.due_date:

                        st.write(
                            f"Due: **{activity.due_date.strftime('%d %b %Y')}**"
                        )

                    if activity.assigned_to:

                        st.caption(
                            f"Assigned: {activity.assigned_to}"
                        )

                if activity.notes:

                    st.caption(
                        f"Notes: {activity.notes}"
                    )

    session.close()