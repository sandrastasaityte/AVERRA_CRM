from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
import csv
import io


# ============================================================
# EXPORT FOLDER
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

EXPORT_DIR = BASE_DIR / "data" / "exports"

EXPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    """
    Convert a value into a CSV-friendly format.

    Handles:
    - None
    - dates
    - datetimes
    - Decimal values
    - booleans
    - normal Python values
    """

    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    if isinstance(value, date):
        return value.strftime(
            "%Y-%m-%d"
        )

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, bool):
        return "Yes" if value else "No"

    return str(value)


def generate_filename(
    prefix,
    extension="csv",
):
    """
    Generate a timestamped export filename.
    """

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    extension = extension.lstrip(".")

    return (
        f"{prefix}_{timestamp}.{extension}"
    )


def get_export_path(
    filename,
):
    """
    Return the full path inside the exports folder.

    Prevents an absolute path from escaping the
    AVERRA CRM export directory.
    """

    filename = Path(filename).name

    return EXPORT_DIR / filename


def ensure_csv_extension(
    filename,
):
    """
    Ensure that a filename ends with .csv.
    """

    if not filename:
        filename = generate_filename(
            "averra_export"
        )

    if not filename.lower().endswith(".csv"):
        filename += ".csv"

    return filename


def get_model_fields(
    record,
):
    """
    Return SQLAlchemy column names from a model object.

    Returns an empty list if the object is not
    a SQLAlchemy model.
    """

    table = getattr(
        record,
        "__table__",
        None,
    )

    if table is None:
        return []

    return [
        column.name
        for column in table.columns
    ]


def infer_fieldnames(
    records,
):
    """
    Automatically determine CSV field names.

    Supports:
    - dictionaries
    - SQLAlchemy model objects
    """

    records = list(records or [])

    if not records:
        return []

    first = records[0]

    if isinstance(first, dict):
        return list(first.keys())

    return get_model_fields(first)


# ============================================================
# CSV EXPORT
# ============================================================

def export_to_csv(
    records,
    filename=None,
    fieldnames=None,
):
    """
    Export records to CSV.

    records can be:
    - dictionaries
    - SQLAlchemy model objects

    Returns:
        pathlib.Path
    """

    records = list(records or [])

    filename = ensure_csv_extension(
        filename
    )

    output_path = get_export_path(
        filename
    )

    if fieldnames is None:
        fieldnames = infer_fieldnames(
            records
        )

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()

        for record in records:

            if isinstance(record, dict):

                row = {
                    field: clean_value(
                        record.get(
                            field,
                            "",
                        )
                    )
                    for field in fieldnames
                }

            else:

                row = {
                    field: clean_value(
                        getattr(
                            record,
                            field,
                            "",
                        )
                    )
                    for field in fieldnames
                }

            writer.writerow(row)

    return output_path


# ============================================================
# CSV BY DICTIONARY DATA
# ============================================================

def export_dicts_to_csv(
    rows,
    filename=None,
    fieldnames=None,
):
    """
    Export a list of dictionaries to CSV.

    Returns:
        pathlib.Path
    """

    rows = list(rows or [])

    filename = ensure_csv_extension(
        filename
    )

    output_path = get_export_path(
        filename
    )

    if fieldnames is None:

        if rows:
            fieldnames = list(
                rows[0].keys()
            )

        else:
            fieldnames = []

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()

        for row in rows:

            cleaned_row = {
                field: clean_value(
                    row.get(
                        field,
                        "",
                    )
                )
                for field in fieldnames
            }

            writer.writerow(
                cleaned_row
            )

    return output_path


# ============================================================
# CSV BY SQLALCHEMY OBJECTS
# ============================================================

def export_models_to_csv(
    records,
    filename=None,
    fields=None,
):
    """
    Export SQLAlchemy model records to CSV.

    If fields are not supplied, all database columns
    from the first record are exported.

    Returns:
        pathlib.Path
    """

    records = list(records or [])

    filename = ensure_csv_extension(
        filename
    )

    output_path = get_export_path(
        filename
    )

    if fields is None:

        if records:
            fields = get_model_fields(
                records[0]
            )

        else:
            fields = []

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            extrasaction="ignore",
        )

        writer.writeheader()

        for record in records:

            row = {
                field: clean_value(
                    getattr(
                        record,
                        field,
                        "",
                    )
                )
                for field in fields
            }

            writer.writerow(row)

    return output_path


# ============================================================
# EXPORT TEXT / CSV DATA FOR STREAMLIT
# ============================================================

def csv_bytes(
    rows,
    fieldnames=None,
):
    """
    Return CSV content as UTF-8-SIG bytes.

    Useful with:

        st.download_button()

    Supports:
    - dictionaries
    - SQLAlchemy model objects
    """

    rows = list(rows or [])

    if fieldnames is None:
        fieldnames = infer_fieldnames(
            rows
        )

    buffer = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
        extrasaction="ignore",
    )

    writer.writeheader()

    for record in rows:

        if isinstance(record, dict):

            row = {
                field: clean_value(
                    record.get(
                        field,
                        "",
                    )
                )
                for field in fieldnames
            }

        else:

            row = {
                field: clean_value(
                    getattr(
                        record,
                        field,
                        "",
                    )
                )
                for field in fieldnames
            }

        writer.writerow(row)

    return buffer.getvalue().encode(
        "utf-8-sig"
    )


# ============================================================
# EXPORT SUMMARY
# ============================================================

def get_export_folder():
    """
    Return the AVERRA CRM export folder.
    """

    return EXPORT_DIR


def list_export_files():
    """
    Return all files currently in the export folder.

    Files are returned newest first.
    """

    if not EXPORT_DIR.exists():
        return []

    files = [
        path
        for path in EXPORT_DIR.iterdir()
        if path.is_file()
    ]

    return sorted(
        files,
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def delete_export_file(
    filename,
):
    """
    Delete an exported file from the
    AVERRA CRM export folder.

    Returns:
        True if deleted.
        False if the file did not exist.
    """

    path = get_export_path(
        filename
    )

    if not path.exists():
        return False

    if not path.is_file():
        return False

    path.unlink()

    return True