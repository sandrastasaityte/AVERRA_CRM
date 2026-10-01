import csv
import io
from datetime import date, datetime

# ============================================================

# GENERAL HELPERS

# ============================================================

def safe_value(value, default=""):
"""
Return a safe value for CSV/export purposes.
"""
if value is None:
return default
return value

def safe_text(value, default=""):
"""
Convert a value safely to text.
"""
if value is None:
return default

```
if isinstance(value, bool):
    return "Yes" if value else "No"

return str(value)
```

def safe_float(value, default=0.0):
"""
Safely convert a value to float.
"""
if value is None:
return default

```
try:
    return float(value)
except (TypeError, ValueError):
    return default
```

def format_date(value):
"""
Format date/datetime values consistently.
"""
if value is None:
return ""

```
if isinstance(value, datetime):
    return value.strftime("%Y-%m-%d")

if isinstance(value, date):
    return value.strftime("%Y-%m-%d")

return str(value)
```

def format_money(value):
"""
Format numeric values as two-decimal amounts.
"""
if value is None:
return ""

```
try:
    return f"{float(value):.2f}"
except (TypeError, ValueError):
    return str(value)
```

def get_attr(obj, name, default=None):
"""
Safely retrieve an attribute from an object or dictionary.
"""
if obj is None:
return default

```
if isinstance(obj, dict):
    return obj.get(name, default)

return getattr(obj, name, default)
```

# ============================================================

# RELATIONSHIP HELPERS

# ============================================================

def get_client_name(client):
"""
Return a readable client/company name.
"""
if client is None:
return ""

```
for field in (
    "company_name",
    "name",
    "client_name",
    "business_name",
):
    value = get_attr(client, field)

    if value:
        return str(value)

return ""
```

def get_employee_name(employee):
"""
Return a readable employee name.
"""
if employee is None:
return ""

```
first_name = get_attr(employee, "first_name", "")
last_name = get_attr(employee, "last_name", "")

full_name = f"{first_name} {last_name}".strip()

if full_name:
    return full_name

for field in (
    "name",
    "full_name",
    "employee_name",
):
    value = get_attr(employee, field)

    if value:
        return str(value)

return ""
```

def get_contact_name(contact):
"""
Return a readable contact name.
"""
if contact is None:
return ""

```
first_name = get_attr(contact, "first_name", "")
last_name = get_attr(contact, "last_name", "")

full_name = f"{first_name} {last_name}".strip()

if full_name:
    return full_name

for field in (
    "name",
    "full_name",
    "contact_name",
):
    value = get_attr(contact, field)

    if value:
        return str(value)

return ""
```

def get_job_title(job):
"""
Return a readable job title.
"""
if job is None:
return ""

```
for field in (
    "title",
    "job_title",
    "position",
    "role",
    "name",
):
    value = get_attr(job, field)

    if value:
        return str(value)

return ""
```

def get_placement_position(placement):
"""
Return the placement position/title.
"""
if placement is None:
return ""

```
for field in (
    "position",
    "job_title",
    "title",
    "role",
):
    value = get_attr(placement, field)

    if value:
        return str(value)

return ""
```

def get_contract_number(contract):
"""
Return contract number.
"""
if contract is None:
return ""

```
for field in (
    "contract_number",
    "number",
    "reference",
    "contract_ref",
):
    value = get_attr(contract, field)

    if value:
        return str(value)

return ""
```

def get_invoice_number(invoice):
"""
Return invoice number.
"""
if invoice is None:
return ""

```
for field in (
    "invoice_number",
    "number",
    "reference",
    "invoice_ref",
):
    value = get_attr(invoice, field)

    if value:
        return str(value)

return ""
```

# ============================================================

# CORE CSV ENGINE

# ============================================================

def records_to_csv(records, columns, filename="export.csv"):
"""
Convert records to CSV.

```
columns should be a list of tuples:

    [
        ("Company", lambda x: ...),
        ("Status", lambda x: ...),
    ]

The accessor can be:
    - callable
    - dictionary key
    - object attribute name
"""

output = io.StringIO(newline="")

writer = csv.writer(
    output,
    quoting=csv.QUOTE_MINIMAL,
)

headers = [column[0] for column in columns]

writer.writerow(headers)

for record in records or []:
    row = []

    for _, accessor in columns:

        try:
            if callable(accessor):
                value = accessor(record)

            elif isinstance(record, dict):
                value = record.get(accessor, "")

            else:
                value = getattr(
                    record,
                    accessor,
                    "",
                )

        except Exception:
            value = ""

        if isinstance(value, (date, datetime)):
            value = format_date(value)

        elif isinstance(value, float):
            value = format_money(value)

        elif value is None:
            value = ""

        else:
            value = str(value)

        row.append(value)

    writer.writerow(row)

return {
    "filename": filename,
    "content": output.getvalue(),
    "mime": "text/csv",
}
```

def csv_bytes(records, columns):
"""
Return CSV data as UTF-8 bytes.

```
UTF-8 BOM is included for better Excel compatibility.
"""
result = records_to_csv(
    records,
    columns,
    filename="export.csv",
)

return result["content"].encode(
    "utf-8-sig"
)
```

# ============================================================

# CLIENT EXPORT

# ============================================================

def export_clients(clients):
columns = [
("ID", lambda x: get_attr(x, "id")),
("Company Name", lambda x: get_client_name(x)),
("Status", lambda x: get_attr(x, "status")),
("Industry", lambda x: get_attr(x, "industry")),
("Country", lambda x: get_attr(x, "country")),
("City", lambda x: get_attr(x, "city")),
("Website", lambda x: get_attr(x, "website")),
("Email", lambda x: get_attr(x, "email")),
("Phone", lambda x: get_attr(x, "phone")),
("Lead Source", lambda x: get_attr(x, "lead_source")),
("Company Size", lambda x: get_attr(x, "company_size")),
("Account Owner", lambda x: get_attr(x, "account_owner")),
("Follow-up Date", lambda x: format_date(get_attr(x, "follow_up_date"))),
("Notes", lambda x: get_attr(x, "notes")),
("Created At", lambda x: format_date(get_attr(x, "created_at"))),
("Updated At", lambda x: format_date(get_attr(x, "updated_at"))),
]

```
return records_to_csv(
    clients,
    columns,
    "clients.csv",
)
```

# ============================================================

# CLIENT CONTACT EXPORT

# ============================================================

def export_client_contacts(contacts):
columns = [
("ID", lambda x: get_attr(x, "id")),
(
"Client",
lambda x: get_client_name(
get_attr(x, "client")
),
),
("First Name", lambda x: get_attr(x, "first_name")),
("Last Name", lambda x: get_attr(x, "last_name")),
("Full Name", lambda x: get_contact_name(x)),
("Job Title", lambda x: get_attr(x, "job_title")),
("Email", lambda x: get_attr(x, "email")),
("Phone", lambda x: get_attr(x, "phone")),
("Mobile", lambda x: get_attr(x, "mobile")),
("LinkedIn", lambda x: get_attr(x, "linkedin_url")),
("Primary Contact", lambda x: get_attr(x, "primary_contact")),
("Status", lambda x: get_attr(x, "status")),
("Notes", lambda x: get_attr(x, "notes")),
("Created At", lambda x: format_date(get_attr(x, "created_at"))),
]

```
return records_to_csv(
    contacts,
    columns,
    "client_contacts.csv",
)
```

# ============================================================

# ACTIVITIES EXPORT

# ============================================================

def export_activities(activities):
def candidate_name(activity):
candidate = get_attr(activity, "candidate")

```
    if candidate is None:
        return ""

    employee = get_attr(candidate, "employee")

    if employee:
        return get_employee_name(employee)

    return get_attr(candidate, "name", "")

columns = [
    ("ID", lambda x: get_attr(x, "id")),
    (
        "Client",
        lambda x: get_client_name(
            get_attr(x, "client")
        ),
    ),
    (
        "Contact",
        lambda x: get_contact_name(
            get_attr(x, "contact")
        ),
    ),
    (
        "Job",
        lambda x: get_job_title(
            get_attr(x, "job")
        ),
    ),
    (
        "Candidate",
        candidate_name,
    ),
    (
        "Placement",
        lambda x: get_placement_position(
            get_attr(x, "placement")
        ),
    ),
    (
        "Contract",
        lambda x: get_contract_number(
            get_attr(x, "contract")
        ),
    ),
    ("Activity Type", lambda x: get_attr(x, "activity_type")),
    ("Subject", lambda x: get_attr(x, "subject")),
    ("Description", lambda x: get_attr(x, "description")),
    ("Status", lambda x: get_attr(x, "status")),
    ("Priority", lambda x: get_attr(x, "priority")),
    ("Due Date", lambda x: format_date(get_attr(x, "due_date"))),
    ("Completed At", lambda x: format_date(get_attr(x, "completed_at"))),
    ("Created At", lambda x: format_date(get_attr(x, "created_at"))),
]

return records_to_csv(
    activities,
    columns,
    "activities.csv",
)
```

# ============================================================

# EMPLOYEE EXPORT

# ============================================================

def export_employees(employees):
columns = [
("ID", lambda x: get_attr(x, "id")),
("First Name", lambda x: get_attr(x, "first_name")),
("Last Name", lambda x: get_attr(x, "last_name")),
("Full Name", lambda x: get_employee_name(x)),
("Email", lambda x: get_attr(x, "email")),
("Phone", lambda x: get_attr(x, "phone")),
("Country", lambda x: get_attr(x, "country")),
("City", lambda x: get_attr(x, "city")),
("Role", lambda x: get_attr(x, "role")),
("Department", lambda x: get_attr(x, "department")),
("Status", lambda x: get_attr(x, "status")),
("English Level", lambda x: get_attr(x, "english_level")),
("Availability", lambda x: get_attr(x, "availability")),
("Currency", lambda x: get_attr(x, "currency")),
("Expected Salary", lambda x: format_money(get_attr(x, "expected_salary"))),
("CV Path", lambda x: get_attr(x, "cv_path")),
("CV Link", lambda x: get_attr(x, "cv_link")),
("Notes", lambda x: get_attr(x, "notes")),
("Created At", lambda x: format_date(get_attr(x, "created_at"))),
]

```
return records_to_csv(
    employees,
    columns,
    "employees.csv",
)
```

# ============================================================

# EMPLOYEE SKILLS EXPORT

# ============================================================

def export_employee_skills(skills):
def skill_name(skill):
for field in (
"skill_name",
"skill",
"name",
):
value = get_attr(skill, field)

```
        if value:
            return value

    return ""

columns = [
    ("ID", lambda x: get_attr(x, "id")),
    (
        "Employee",
        lambda x: get_employee_name(
            get_attr(x, "employee")
        ),
    ),
    ("Skill", skill_name),
    ("Category", lambda x: get_attr(x, "category")),
    ("Level", lambda x: get_attr(x, "level")),
    ("Years Experience", lambda x: get_attr(x, "years_experience")),
    ("Notes", lambda x: get_attr(x, "notes")),
    ("Created At", lambda x: format_date(get_attr(x, "created_at"))),
]

return records_to_csv(
    skills,
    columns,
    "employee_skills.csv",
)
```

# ============================================================

# JOB EXPORT

# ============================================================

def export_jobs(jobs):
columns = [
("ID", lambda x: get_attr(x, "id")),
(
"Client",
lambda x: get_client_name(
get_attr(x, "client")
),
),
("Job Title", lambda x: get_job_title(x)),
("Department", lambda x: get_attr(x, "department")),
("Location", lambda x: get_attr(x, "location")),
("Employment Type", lambda x: get_attr(x, "employment_type")),
("Status", lambda x: get_attr(x, "status")),
("Openings", lambda x: get_attr(x, "openings")),
("Salary Min", lambda x: format_money(get_attr(x, "salary_min"))),
("Salary Max", lambda x: format_money(get_attr(x, "salary_max"))),
("Currency", lambda x: get_attr(x, "currency")),
("Start Date", lambda x: format_date(get_attr(x, "start_date"))),
("Closing Date", lambda x: format_date(get_attr(x, "closing_date"))),
("Description", lambda x: get_attr(x, "description")),
("Requirements", lambda x: get_attr(x, "requirements")),
("Notes", lambda x: get_attr(x, "notes")),
("Created At", lambda x: format_date(get_attr(x, "created_at"))),
]

```
return records_to_csv(
    jobs,
    columns,
    "jobs.csv",
)
```

# ============================================================

# CANDIDATE EXPORT

# ============================================================

def export_candidates(candidates):
def candidate_employee(candidate):
employee = get_attr(candidate, "employee")

```
    if employee:
        return get_employee_name(employee)

    return get_attr(candidate, "employee_name", "")

columns = [
    ("ID", lambda x: get_attr(x, "id")),
    (
        "Employee",
        candidate_employee,
    ),
    (
        "Job",
        lambda x: get_job_title(
            get_attr(x, "job")
        ),
    ),
    (
        "Client",
        lambda x: get_client_name(
            get_attr(
                get_attr(x, "job"),
                "client",
            )
        ),
    ),
    ("Status", lambda x: get_attr(x, "status")),
    ("Submitted Date", lambda x: format_date(get_attr(x, "submitted_date"))),
    ("Interview Date", lambda x: format_date(get_attr(x, "interview_date"))),
    ("Offer Date", lambda x: format_date(get_attr(x, "offer_date"))),
    ("Placed Date", lambda x: format_date(get_attr(x, "placed_date"))),
    ("Client Feedback", lambda x: get_attr(x, "client_feedback")),
    ("Notes", lambda x: get_attr(x, "notes")),
    ("Created At", lambda x: format_date(get_attr(x, "created_at"))),
]

return records_to_csv(
    candidates,
    columns,
    "candidates.csv",
)
```

# ============================================================

# PLACEMENT EXPORT

# ============================================================

def export_placements(placements):
columns = [
("ID", lambda x: get_attr(x, "id")),
(
"Client",
lambda x: get_client_name(
get_attr(x, "client")
),
),
(
"Employee",
lambda x: get_employee_name(
get_attr(x, "employee")
),
),
(
"Job",
lambda x: get_job_title(
get_attr(x, "job")
),
),
("Position", lambda x: get_placement_position(x)),
("Status", lambda x: get_attr(x, "status")),
("Start Date", lambda x: format_date(get_attr(x, "start_date"))),
("End Date", lambda x: format_date(get_attr(x, "end_date"))),
("Billing Frequency", lambda x: get_attr(x, "billing_frequency")),
("Client Monthly Fee", lambda x: format_money(get_attr(x, "client_monthly_fee"))),
("Worker Monthly Cost", lambda x: format_money(get_attr(x, "worker_monthly_cost"))),
("Currency", lambda x: get_attr(x, "currency")),
("Notes", lambda x: get_attr(x, "notes")),
("Created At", lambda x: format_date(get_attr(x, "created_at"))),
]

```
return records_to_csv(
    placements,
    columns,
    "placements.csv",
)
```

# ============================================================

# CONTRACT EXPORT

# ============================================================

def export_contracts(contracts):
columns = [
("ID", lambda x: get_attr(x, "id")),
(
"Client",
lambda x: get_client_name(
get_attr(x, "client")
),
),
("Contract Number", lambda x: get_contract_number(x)),
("Contract Type", lambda x: get_attr(x, "contract_type")),
("Status", lambda x: get_attr(x, "status")),
("Currency", lambda x: get_attr(x, "currency")),
("Contract Value", lambda x: format_money(get_attr(x, "contract_value"))),
(
"Placement",
lambda x: get_placement_position(
get_attr(x, "placement")
),
),
("Start Date", lambda x: format_date(get_attr(x, "start_date"))),
("End Date", lambda x: format_date(get_attr(x, "end_date"))),
("Signed Date", lambda x: format_date(get_attr(x, "signed_date"))),
("Renewal Date", lambda x: format_date(get_attr(x, "renewal_date"))),
("Document Link", lambda x: get_attr(x, "document_link")),
("Notes", lambda x: get_attr(x, "notes")),
("Created At", lambda x: format_date(get_attr(x, "created_at"))),
]

```
return records_to_csv(
    contracts,
    columns,
    "contracts.csv",
)
```

# ============================================================

# INVOICE EXPORT

# ============================================================

def export_invoices(invoices):
columns = [
("ID", lambda x: get_attr(x, "id")),
("Invoice Number", lambda x: get_invoice_number(x)),
(
"Client",
lambda x: get_client_name(
get_attr(x, "client")
),
),
(
"Placement",
lambda x: get_placement_position(
get_attr(x, "placement")
),
),
("Invoice Date", lambda x: format_date(get_attr(x, "invoice_date"))),
("Due Date", lambda x: format_date(get_attr(x, "due_date"))),
("Description", lambda x: get_attr(x, "description")),
("Subtotal", lambda x: format_money(get_attr(x, "subtotal"))),
("Tax", lambda x: format_money(get_attr(x, "tax"))),
("Total", lambda x: format_money(get_attr(x, "total_amount"))),
("Amount Paid", lambda x: format_money(get_attr(x, "amount_paid"))),
(
"Balance",
lambda x: format_money(
safe_float(
get_attr(x, "total_amount")
)
- safe_float(
get_attr(x, "amount_paid")
)
),
),
("Currency", lambda x: get_attr(x, "currency")),
("Status", lambda x: get_attr(x, "status")),
("Document Link", lambda x: get_attr(x, "document_link")),
("Notes", lambda x: get_attr(x, "notes")),
("Created At", lambda x: format_date(get_attr(x, "created_at"))),
]

```
return records_to_csv(
    invoices,
    columns,
    "invoices.csv",
)
```

# ============================================================

# PAYMENT EXPORT

# ============================================================

def export_payments(payments):
columns = [
("ID", lambda x: get_attr(x, "id")),
(
"Invoice Number",
lambda x: get_invoice_number(
get_attr(x, "invoice")
),
),
(
"Client",
lambda x: get_client_name(
get_attr(
get_attr(x, "invoice"),
"client",
)
),
),
("Payment Date", lambda x: format_date(get_attr(x, "payment_date"))),
("Amount", lambda x: format_money(get_attr(x, "amount"))),
(
"Currency",
lambda x: get_attr(
get_attr(x, "invoice"),
"currency",
),
),
("Payment Method", lambda x: get_attr(x, "payment_method")),
("Status", lambda x: get_attr(x, "status")),
("Reference", lambda x: get_attr(x, "reference")),
("Notes", lambda x: get_attr(x, "notes")),
("Created At", lambda x: format_date(get_attr(x, "created_at"))),
]

```
return records_to_csv(
    payments,
    columns,
    "payments.csv",
)
```

# ============================================================

# GENERIC EXPORT

# ============================================================

def export_records(
records,
columns,
filename="export.csv",
):
"""
Generic export function for any CRM model.
"""
return records_to_csv(
records,
columns,
filename,
)

def get_csv_download_data(
records,
columns,
filename="export.csv",
):
"""
Return data suitable for Streamlit download_button().
"""
return {
"data": csv_bytes(records, columns),
"file_name": filename,
"mime": "text/csv",
}

# ============================================================

# EXPORT ALL CRM DATA

# ============================================================

def export_all_data(
clients=None,
client_contacts=None,
activities=None,
employees=None,
employee_skills=None,
jobs=None,
candidates=None,
placements=None,
contracts=None,
invoices=None,
payments=None,
):
"""
Export all CRM entities into a dictionary of CSV files.

```
Example:

    files = export_all_data(
        clients=clients,
        employees=employees,
        jobs=jobs,
    )

Result:

    {
        "clients.csv": b"...",
        "employees.csv": b"...",
        "jobs.csv": b"...",
    }
"""

exports = {}

if clients is not None:
    result = export_clients(clients)
    exports[result["filename"]] = result["content"].encode("utf-8-sig")

if client_contacts is not None:
    result = export_client_contacts(client_contacts)
    exports[result["filename"]] = result["content"].encode("utf-8-sig")

if activities is not None:
    result = export_activities(activities)
    exports[result["filename"]] = result["content"].encode("utf-8-sig")

if employees is not None:
    result = export_employees(employees)
    exports[result["filename"]] = result["content"].encode("utf-8-sig")

if employee_skills is not None:
    result = export_employee_skills(employee_skills)
    exports[result["filename"]] = result["content"].encode("utf-8-sig")

if jobs is not None:
    result = export_jobs(jobs)
    exports[result["filename"]] = result["content"].encode("utf-8-sig")

if candidates is not None:
    result = export_candidates(candidates)
    exports[result["filename"]] = result["content"].encode("utf-8-sig")

if placements is not None:
    result = export_placements(placements)
    exports[result["filename"]] = result["content"].encode("utf-8-sig")

if contracts is not None:
    result = export_contracts(contracts)
    exports[result["filename"]] = result["content"].encode("utf-8-sig")

if invoices is not None:
    result = export_invoices(invoices)
    exports[result["filename"]] = result["content"].encode("utf-8-sig")

if payments is not None:
    result = export_payments(payments)
    exports[result["filename"]] = result["content"].encode("utf-8-sig")

return exports
```
