import streamlit as st
import pandas as pd

from database import get_session
from models import (
    Client,
    Employee,
    Job,
    Candidate,
    Placement,
    Contract,
    Invoice,
    Payment,
    Activity
)


def show_reports():

    st.title("Reports")
    st.caption(
        "Management reporting across sales, recruitment, placements and finance."
    )

    session = get_session()

    # ==========================================================
    # DATA
    # ==========================================================

    clients = session.query(Client).all()
    employees = session.query(Employee).all()
    jobs = session.query(Job).all()
    candidates = session.query(Candidate).all()
    placements = session.query(Placement).all()
    contracts = session.query(Contract).all()
    invoices = session.query(Invoice).all()
    payments = session.query(Payment).all()
    activities = session.query(Activity).all()

    # ==========================================================
    # MANAGEMENT SUMMARY
    # ==========================================================

    st.subheader("Management Summary")

    active_placements = [
        p for p in placements
        if p.status == "Active"
    ]

    open_jobs = [
        j for j in jobs
        if j.status not in ["Closed", "Cancelled"]
    ]

    monthly_revenue = sum(
        p.client_monthly_fee or 0
        for p in active_placements
    )

    monthly_worker_cost = sum(
        p.worker_monthly_cost or 0
        for p in active_placements
    )

    monthly_gross_margin = (
        monthly_revenue - monthly_worker_cost
    )

    margin_percentage = (
        (monthly_gross_margin / monthly_revenue) * 100
        if monthly_revenue
        else 0
    )

    outstanding_invoices = sum(
        max((i.total_amount or 0) - (i.amount_paid or 0), 0)
        for i in invoices
        if i.status not in ["Cancelled", "Paid"]
    )

    total_paid = sum(
        p.amount or 0
        for p in payments
        if p.status == "Received"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Clients",
            len(clients)
        )

    with col2:
        st.metric(
            "Employees",
            len(employees)
        )

    with col3:
        st.metric(
            "Open Jobs",
            len(open_jobs)
        )

    with col4:
        st.metric(
            "Active Placements",
            len(active_placements)
        )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Monthly Revenue",
            f"£{monthly_revenue:,.2f}"
        )

    with col2:
        st.metric(
            "Worker Costs",
            f"£{monthly_worker_cost:,.2f}"
        )

    with col3:
        st.metric(
            "Gross Margin",
            f"£{monthly_gross_margin:,.2f}"
        )

    with col4:
        st.metric(
            "Margin %",
            f"{margin_percentage:.1f}%"
        )

    st.divider()

    # ==========================================================
    # SALES PIPELINE
    # ==========================================================

    st.subheader("Sales Pipeline")

    pipeline_statuses = [
        "Lead",
        "Contacted",
        "Replied",
        "Call",
        "Proposal",
        "Negotiation",
        "Contract",
        "Won",
        "Lost"
    ]

    pipeline_data = []

    for status in pipeline_statuses:

        count = sum(
            1
            for client in clients
            if client.status == status
        )

        pipeline_data.append(
            {
                "Stage": status,
                "Clients": count
            }
        )

    pipeline_df = pd.DataFrame(pipeline_data)

    col1, col2 = st.columns(2)

    with col1:

        st.dataframe(
            pipeline_df,
            use_container_width=True,
            hide_index=True
        )

    with col2:

        chart_data = pipeline_df.set_index("Stage")

        st.bar_chart(
            chart_data["Clients"]
        )

    # ==========================================================
    # RECRUITMENT PIPELINE
    # ==========================================================

    st.divider()

    st.subheader("Recruitment Pipeline")

    job_status_data = (
        pd.Series(
            [job.status for job in jobs]
        )
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Jobs")
    )

    candidate_status_data = (
        pd.Series(
            [candidate.status for candidate in candidates]
        )
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Candidates")
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write("**Jobs by Status**")

        if job_status_data.empty:

            st.info("No jobs available.")

        else:

            st.dataframe(
                job_status_data,
                use_container_width=True,
                hide_index=True
            )

    with col2:

        st.write("**Candidates by Status**")

        if candidate_status_data.empty:

            st.info("No candidates available.")

        else:

            st.dataframe(
                candidate_status_data,
                use_container_width=True,
                hide_index=True
            )

    # ==========================================================
    # PLACEMENT PROFITABILITY
    # ==========================================================

    st.divider()

    st.subheader("Placement Profitability")

    profitability_data = []

    for placement in active_placements:

        client_name = "Unknown"

        employee_name = "Unknown"

        job_title = "Unknown"

        if placement.client:

            client_name = placement.client.company_name

        if placement.employee:

            employee_name = (
                f"{placement.employee.first_name} "
                f"{placement.employee.last_name or ''}"
            ).strip()

        if placement.job:

            job_title = placement.job.title

        revenue = placement.client_monthly_fee or 0

        cost = placement.worker_monthly_cost or 0

        gross_margin = revenue - cost

        margin = (
            (gross_margin / revenue) * 100
            if revenue
            else 0
        )

        profitability_data.append(
            {
                "Client": client_name,
                "Employee": employee_name,
                "Position": job_title,
                "Monthly Fee": revenue,
                "Worker Cost": cost,
                "Gross Margin": gross_margin,
                "Margin %": margin
            }
        )

    if profitability_data:

        profitability_df = pd.DataFrame(
            profitability_data
        )

        st.dataframe(
            profitability_df.style.format(
                {
                    "Monthly Fee": "£{:,.2f}",
                    "Worker Cost": "£{:,.2f}",
                    "Gross Margin": "£{:,.2f}",
                    "Margin %": "{:.1f}%"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No active placements available."
        )

    # ==========================================================
    # INVOICE REPORT
    # ==========================================================

    st.divider()

    st.subheader("Invoice Report")

    invoice_statuses = [
        "Draft",
        "Sent",
        "Partially Paid",
        "Paid",
        "Overdue",
        "Cancelled"
    ]

    invoice_data = []

    for status in invoice_statuses:

        matching = [
            invoice
            for invoice in invoices
            if invoice.status == status
        ]

        total = sum(
            invoice.total_amount or 0
            for invoice in matching
        )

        paid = sum(
            invoice.amount_paid or 0
            for invoice in matching
        )

        balance = total - paid

        invoice_data.append(
            {
                "Status": status,
                "Invoices": len(matching),
                "Total": total,
                "Paid": paid,
                "Balance": balance
            }
        )

    invoice_df = pd.DataFrame(invoice_data)

    st.dataframe(
        invoice_df.style.format(
            {
                "Total": "£{:,.2f}",
                "Paid": "£{:,.2f}",
                "Balance": "£{:,.2f}"
            }
        ),
        use_container_width=True,
        hide_index=True
    )

    # ==========================================================
    # OUTSTANDING / OVERDUE INVOICES
    # ==========================================================

    st.subheader("Outstanding Invoices")

    outstanding_data = []

    for invoice in invoices:

        balance = (
            (invoice.total_amount or 0)
            - (invoice.amount_paid or 0)
        )

        if balance <= 0:
            continue

        client_name = "Unknown"

        if invoice.client:
            client_name = invoice.client.company_name

        outstanding_data.append(
            {
                "Invoice": invoice.invoice_number,
                "Client": client_name,
                "Invoice Date": invoice.invoice_date,
                "Due Date": invoice.due_date,
                "Status": invoice.status,
                "Total": invoice.total_amount or 0,
                "Paid": invoice.amount_paid or 0,
                "Balance": balance
            }
        )

    if outstanding_data:

        outstanding_df = pd.DataFrame(
            outstanding_data
        )

        st.dataframe(
            outstanding_df.style.format(
                {
                    "Total": "£{:,.2f}",
                    "Paid": "£{:,.2f}",
                    "Balance": "£{:,.2f}"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "There are no outstanding invoices."
        )

    # ==========================================================
    # PAYMENTS
    # ==========================================================

    st.divider()

    st.subheader("Payment Summary")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Payments Received",
            f"£{total_paid:,.2f}"
        )

    with col2:

        st.metric(
            "Outstanding Invoices",
            f"£{outstanding_invoices:,.2f}"
        )

    payment_status_data = (
        pd.Series(
            [payment.status for payment in payments]
        )
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Payments")
    )

    if not payment_status_data.empty:

        st.dataframe(
            payment_status_data,
            use_container_width=True,
            hide_index=True
        )

    # ==========================================================
    # ACTIVITY REPORT
    # ==========================================================

    st.divider()

    st.subheader("Activity Report")

    if activities:

        activity_data = (
            pd.Series(
                [activity.activity_type for activity in activities]
            )
            .value_counts()
            .rename_axis("Activity Type")
            .reset_index(name="Activities")
        )

        st.dataframe(
            activity_data,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No activities have been recorded."
        )

    # ==========================================================
    # CONTRACT REPORT
    # ==========================================================

    st.divider()

    st.subheader("Contract Report")

    contract_status_data = (
        pd.Series(
            [contract.status for contract in contracts]
        )
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Contracts")
    )

    if not contract_status_data.empty:

        st.dataframe(
            contract_status_data,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No contracts have been created."
        )

    session.close()