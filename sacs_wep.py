import argparse
import csv
import hashlib
import html
import re
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone


SCRIPT_NAME = "SACS WEP"
SCRIPT_VERSION = "0.7.0"


MESSAGE_TYPE_MAP = {
    "0": "Text / standard message",
    "1": "Image or media-related message",
    "2": "Audio or voice-related message",
    "3": "Video or media-related message",
    "4": "Contact card or shared contact",
    "5": "Location-related message",
    "6": "System/service message",
    "7": "Link/document/other supported type",
}


def safe_filename_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as file:
        for byte_block in iter(lambda: file.read(1024 * 1024), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def parse_timezone_offset(offset_text):
    if not offset_text:
        return timezone.utc

    pattern = r"^([+-])(\d{2}):(\d{2})$"
    match = re.match(pattern, offset_text.strip())

    if not match:
        raise ValueError("Timezone offset must look like +01:00, +00:00, or -05:00")

    sign, hours, minutes = match.groups()
    delta = timedelta(hours=int(hours), minutes=int(minutes))

    if sign == "-":
        delta = -delta

    return timezone(delta)


def convert_apple_timestamp(raw_value, target_timezone):
    if raw_value is None:
        return "", ""

    try:
        raw_float = float(raw_value)
        apple_epoch = datetime(2001, 1, 1, tzinfo=timezone.utc)
        utc_time = apple_epoch + timedelta(seconds=raw_float)
        local_time = utc_time.astimezone(target_timezone)

        return (
            utc_time.isoformat(sep=" ", timespec="seconds"),
            local_time.isoformat(sep=" ", timespec="seconds"),
        )
    except Exception:
        return "", ""


def create_case_folders(output_root, case_id):
    case_folder = output_root / case_id

    folders = {
        "case_folder": case_folder,
        "working_copy": case_folder / "Working_Copy",
        "exports": case_folder / "Exports",
        "hashes": case_folder / "Hashes",
        "logs": case_folder / "Logs",
        "reports": case_folder / "Reports",
        "case_info": case_folder / "Case_Info",
    }

    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)

    return folders


def write_log(log_path, lines):
    with open(log_path, "w", encoding="utf-8") as log_file:
        for line in lines:
            log_file.write(line + "\n")


def write_hash_manifest(hash_path, hash_records):
    with open(hash_path, "w", encoding="utf-8") as hash_file:
        hash_file.write("SACS WEP Hash Manifest\n")
        hash_file.write("=" * 70 + "\n")
        hash_file.write(f"Generated On: {datetime.now().isoformat(timespec='seconds')}\n")
        hash_file.write(f"Tool Version: {SCRIPT_VERSION}\n")
        hash_file.write("=" * 70 + "\n\n")

        for record in hash_records:
            hash_file.write(f"File Role: {record['role']}\n")
            hash_file.write(f"File Name: {record['file_name']}\n")
            hash_file.write(f"File Path: {record['file_path']}\n")
            hash_file.write(f"SHA-256: {record['sha256']}\n")
            hash_file.write("-" * 70 + "\n")


def inspect_sqlite_database(database_path):
    structure = {}

    connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    cursor = connection.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        cursor.execute(f"PRAGMA table_info('{table}');")
        columns = cursor.fetchall()

        structure[table] = [
            {
                "cid": column[0],
                "name": column[1],
                "type": column[2],
                "notnull": column[3],
                "default": column[4],
                "pk": column[5],
            }
            for column in columns
        ]

    connection.close()
    return structure


def write_database_structure(structure_path, structure):
    with open(structure_path, "w", encoding="utf-8") as file:
        file.write("SACS WEP Database Structure Report\n")
        file.write("=" * 70 + "\n")
        file.write(f"Generated On: {datetime.now().isoformat(timespec='seconds')}\n")
        file.write(f"Tool Version: {SCRIPT_VERSION}\n")
        file.write("=" * 70 + "\n\n")
        file.write(f"Total Tables Detected: {len(structure)}\n\n")

        for table_name, columns in structure.items():
            file.write(f"TABLE: {table_name}\n")
            file.write("-" * 70 + "\n")

            if not columns:
                file.write("No columns detected.\n\n")
                continue

            for column in columns:
                file.write(
                    f"Column: {column['name']} | "
                    f"Type: {column['type']} | "
                    f"Primary Key: {column['pk']}\n"
                )

            file.write("\n")


def detect_relevant_tables(structure):
    keywords = [
        "message", "chat", "media", "group", "contact",
        "profile", "receipt", "status", "wamessage",
        "wachat", "wamedia", "wa"
    ]

    relevant = []

    for table_name in structure.keys():
        table_lower = table_name.lower()
        if any(keyword in table_lower for keyword in keywords):
            relevant.append(table_name)

    return relevant


def get_column_names(structure, table_name):
    if table_name not in structure:
        return []
    return [column["name"] for column in structure[table_name]]


def choose_first_existing_column(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def fetch_lookup_table(database_path, structure, table_name, key_candidates, value_candidates):
    if table_name not in structure:
        return {}

    columns = get_column_names(structure, table_name)
    key_col = choose_first_existing_column(columns, key_candidates)
    value_col = choose_first_existing_column(columns, value_candidates)

    if not key_col or not value_col:
        return {}

    lookup = {}

    connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    try:
        cursor.execute(f"SELECT {key_col}, {value_col} FROM {table_name};")
        rows = cursor.fetchall()

        for row in rows:
            key = row[key_col]
            value = row[value_col]
            if key is not None and value is not None:
                lookup[str(key)] = str(value)

    except sqlite3.DatabaseError:
        pass
    finally:
        connection.close()

    return lookup


def build_resolution_lookups(database_path, structure, log_lines):
    log_lines.append("Resolution Lookup Building")
    log_lines.append("-" * 70)

    chat_lookup = {}

    possible_chat_tables = [
        "ZWACHATSESSION",
        "ZWACHAT",
        "ZWACONVERSATION"
    ]

    for table in possible_chat_tables:
        partial_lookup = fetch_lookup_table(
            database_path=database_path,
            structure=structure,
            table_name=table,
            key_candidates=["Z_PK"],
            value_candidates=[
                "ZCONTACTJID",
                "ZGROUPJID",
                "ZPARTNERNAME",
                "ZTITLE",
                "ZNAME",
                "ZCHATIDENTIFIER"
            ]
        )

        if partial_lookup:
            chat_lookup.update(partial_lookup)
            log_lines.append(f"[OK] Chat lookup built from {table}: {len(partial_lookup)} entries")

    if not chat_lookup:
        log_lines.append("[INFO] No chat lookup could be built from known chat tables.")

    contact_lookup = {}

    possible_contact_tables = [
        "ZWAADDRESSBOOKCONTACT",
        "ZWAPROFILEPUSHNAME",
        "ZWAGROUPMEMBER"
    ]

    for table in possible_contact_tables:
        partial_lookup = fetch_lookup_table(
            database_path=database_path,
            structure=structure,
            table_name=table,
            key_candidates=["Z_PK"],
            value_candidates=[
                "ZFULLNAME",
                "ZFIRSTNAME",
                "ZPUSHNAME",
                "ZMEMBERJID",
                "ZCONTACTJID",
                "ZPHONE",
                "ZWHATSAPPID"
            ]
        )

        if partial_lookup:
            contact_lookup.update(partial_lookup)
            log_lines.append(f"[OK] Contact lookup built from {table}: {len(partial_lookup)} entries")

    if not contact_lookup:
        log_lines.append("[INFO] No contact lookup could be built from known contact/profile tables.")

    return {
        "chat_lookup": chat_lookup,
        "contact_lookup": contact_lookup,
    }


def interpret_direction(direction_raw):
    if str(direction_raw) == "1":
        return "Outgoing / From Device Owner"
    if str(direction_raw) == "0":
        return "Incoming / To Device Owner"
    return "Unknown"


def interpret_message_type(message_type_raw):
    raw = str(message_type_raw).strip()
    if raw in MESSAGE_TYPE_MAP:
        return MESSAGE_TYPE_MAP[raw]
    if raw == "":
        return "Unknown / not exported"
    return f"Unmapped message type ({raw})"


def extract_messages_basic(database_path, structure, export_path, log_lines, lookups, target_timezone):
    table_name = "ZWAMESSAGE"

    if table_name not in structure:
        log_lines.append("[WARNING] ZWAMESSAGE table not found. Message extraction skipped.")
        return 0

    columns = get_column_names(structure, table_name)

    id_col = choose_first_existing_column(columns, ["Z_PK", "Z_ENT", "Z_OPT"])
    text_col = choose_first_existing_column(columns, ["ZTEXT", "ZMESSAGETEXT", "ZBODY"])
    timestamp_col = choose_first_existing_column(columns, ["ZMESSAGEDATE", "ZDATE", "ZSENTDATE"])
    from_me_col = choose_first_existing_column(columns, ["ZISFROMME", "ZFROMME"])
    message_type_col = choose_first_existing_column(columns, ["ZMESSAGETYPE", "ZTYPE"])
    media_col = choose_first_existing_column(columns, ["ZMEDIAITEM", "ZMEDIASECTIONID"])
    chat_col = choose_first_existing_column(columns, ["ZCHATSESSION", "ZCHAT", "ZCONVERSATION"])
    sender_col = choose_first_existing_column(columns, ["ZFROMJID", "ZSENDERJID", "ZGROUPMEMBER", "ZCONTACT"])

    selected_columns = []

    for col in [
        id_col,
        chat_col,
        sender_col,
        from_me_col,
        timestamp_col,
        message_type_col,
        text_col,
        media_col
    ]:
        if col and col not in selected_columns:
            selected_columns.append(col)

    if not selected_columns:
        log_lines.append("[WARNING] No usable columns found in ZWAMESSAGE.")
        return 0

    order_col = timestamp_col if timestamp_col else id_col

    sql = f"""
        SELECT {", ".join(selected_columns)}
        FROM {table_name}
        ORDER BY {order_col};
    """

    connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
    except sqlite3.DatabaseError as error:
        log_lines.append(f"[ERROR] Message extraction failed: {error}")
        connection.close()
        return 0

    chat_lookup = lookups.get("chat_lookup", {})
    contact_lookup = lookups.get("contact_lookup", {})

    output_fields = [
        "source_table",
        "message_id",
        "chat_reference",
        "chat_resolved",
        "sender_reference",
        "sender_resolved",
        "direction_raw",
        "direction_interpreted",
        "timestamp_raw",
        "timestamp_utc",
        "timestamp_local",
        "message_type_raw",
        "message_type_interpreted",
        "message_text",
        "media_reference",
        "blank_or_deleted_indicator"
    ]

    try:
        with open(export_path, "w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=output_fields)
            writer.writeheader()

            for row in rows:
                message_id = row[id_col] if id_col else ""
                chat_reference = row[chat_col] if chat_col else ""
                sender_reference = row[sender_col] if sender_col else ""
                direction_raw = row[from_me_col] if from_me_col else ""
                timestamp_raw = row[timestamp_col] if timestamp_col else ""
                message_type_raw = row[message_type_col] if message_type_col else ""
                message_text = row[text_col] if text_col else ""
                media_reference = row[media_col] if media_col else ""

                timestamp_utc, timestamp_local = convert_apple_timestamp(
                    timestamp_raw,
                    target_timezone
                )

                chat_resolved = chat_lookup.get(str(chat_reference), "")
                sender_resolved = contact_lookup.get(str(sender_reference), "")

                if message_text is None or str(message_text).strip() == "":
                    blank_or_deleted_indicator = (
                        "Blank text field; may be media, system, deleted, "
                        "or unsupported message type. Review context before interpretation."
                    )
                else:
                    blank_or_deleted_indicator = ""

                writer.writerow({
                    "source_table": table_name,
                    "message_id": message_id,
                    "chat_reference": chat_reference,
                    "chat_resolved": chat_resolved,
                    "sender_reference": sender_reference,
                    "sender_resolved": sender_resolved,
                    "direction_raw": direction_raw,
                    "direction_interpreted": interpret_direction(direction_raw),
                    "timestamp_raw": timestamp_raw,
                    "timestamp_utc": timestamp_utc,
                    "timestamp_local": timestamp_local,
                    "message_type_raw": message_type_raw,
                    "message_type_interpreted": interpret_message_type(message_type_raw),
                    "message_text": message_text,
                    "media_reference": media_reference,
                    "blank_or_deleted_indicator": blank_or_deleted_indicator
                })

    except PermissionError:
        log_lines.append(f"[ERROR] Permission denied while writing: {export_path}")
        log_lines.append("[HINT] Close the CSV file if it is open in Excel or another program.")
        print("[ERROR] Permission denied while writing the message export.")
        print("Close all output CSV files and run the command again.")
        connection.close()
        return 0

    connection.close()

    log_lines.append("[OK] Basic message extraction completed.")
    log_lines.append(f"[OK] Records exported: {len(rows)}")
    log_lines.append(f"[OK] Message export path: {export_path.resolve()}")

    return len(rows)


def export_chat_summary(message_csv_path, summary_csv_path, log_lines):
    if not message_csv_path.exists():
        log_lines.append("[WARNING] Chat summary skipped because message CSV does not exist.")
        return

    summary = {}

    with open(message_csv_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            chat_key = row.get("chat_resolved") or row.get("chat_reference") or "UNKNOWN_CHAT"
            timestamp = row.get("timestamp_local", "") or row.get("timestamp_utc", "")

            if chat_key not in summary:
                summary[chat_key] = {
                    "chat_identifier": chat_key,
                    "message_count": 0,
                    "first_timestamp": timestamp,
                    "last_timestamp": timestamp,
                }

            summary[chat_key]["message_count"] += 1

            if timestamp:
                if not summary[chat_key]["first_timestamp"] or timestamp < summary[chat_key]["first_timestamp"]:
                    summary[chat_key]["first_timestamp"] = timestamp

                if not summary[chat_key]["last_timestamp"] or timestamp > summary[chat_key]["last_timestamp"]:
                    summary[chat_key]["last_timestamp"] = timestamp

    try:
        with open(summary_csv_path, "w", encoding="utf-8-sig", newline="") as csv_file:
            fieldnames = [
                "chat_identifier",
                "message_count",
                "first_timestamp",
                "last_timestamp"
            ]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for item in summary.values():
                writer.writerow(item)

        log_lines.append(f"[OK] Chat summary exported: {summary_csv_path.resolve()}")
        log_lines.append(f"[OK] Chats summarized: {len(summary)}")

    except PermissionError:
        log_lines.append(f"[ERROR] Permission denied while writing: {summary_csv_path}")
        log_lines.append("[HINT] Close the chat summary CSV if it is open.")


def export_selected_chat(message_csv_path, selected_csv_path, chat_filter, log_lines):
    if not chat_filter:
        log_lines.append("[INFO] Selected chat export skipped because no chat filter was provided.")
        return 0

    if not message_csv_path.exists():
        log_lines.append("[WARNING] Selected chat export skipped because message CSV does not exist.")
        return 0

    filter_text = chat_filter.lower().strip()
    matched_rows = []

    searchable_fields = [
        "chat_reference",
        "chat_resolved",
        "sender_reference",
        "sender_resolved",
        "message_text"
    ]

    with open(message_csv_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames

        for row in reader:
            combined_values = []

            for field in searchable_fields:
                value = row.get(field, "")
                combined_values.append(str(value).lower())

            if filter_text in " ".join(combined_values):
                matched_rows.append(row)

    if not matched_rows:
        log_lines.append(f"[INFO] No selected chat records matched filter: {chat_filter}")
        return 0

    try:
        with open(selected_csv_path, "w", encoding="utf-8-sig", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for row in matched_rows:
                writer.writerow(row)

        log_lines.append("[OK] Selected chat export completed.")
        log_lines.append(f"[OK] Chat filter: {chat_filter}")
        log_lines.append(f"[OK] Selected records exported: {len(matched_rows)}")
        log_lines.append(f"[OK] Selected chat export path: {selected_csv_path.resolve()}")

    except PermissionError:
        log_lines.append(f"[ERROR] Permission denied while writing: {selected_csv_path}")
        log_lines.append("[HINT] Close the selected chat CSV if it is open.")
        return 0

    return len(matched_rows)


def export_media_references(message_csv_path, media_csv_path, log_lines):
    if not message_csv_path.exists():
        log_lines.append("[WARNING] Media reference export skipped because message CSV does not exist.")
        return 0

    media_rows = []

    with open(message_csv_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            media_reference = row.get("media_reference", "")
            message_type = row.get("message_type_interpreted", "")

            if str(media_reference).strip() or "media" in str(message_type).lower():
                media_rows.append({
                    "message_id": row.get("message_id", ""),
                    "chat_reference": row.get("chat_reference", ""),
                    "chat_resolved": row.get("chat_resolved", ""),
                    "sender_reference": row.get("sender_reference", ""),
                    "sender_resolved": row.get("sender_resolved", ""),
                    "timestamp_utc": row.get("timestamp_utc", ""),
                    "timestamp_local": row.get("timestamp_local", ""),
                    "message_type_raw": row.get("message_type_raw", ""),
                    "message_type_interpreted": row.get("message_type_interpreted", ""),
                    "media_reference": media_reference,
                    "message_text": row.get("message_text", ""),
                })

    try:
        with open(media_csv_path, "w", encoding="utf-8-sig", newline="") as csv_file:
            fieldnames = [
                "message_id",
                "chat_reference",
                "chat_resolved",
                "sender_reference",
                "sender_resolved",
                "timestamp_utc",
                "timestamp_local",
                "message_type_raw",
                "message_type_interpreted",
                "media_reference",
                "message_text",
            ]

            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for row in media_rows:
                writer.writerow(row)

        log_lines.append(f"[OK] Media references exported: {media_csv_path.resolve()}")
        log_lines.append(f"[OK] Media-related records exported: {len(media_rows)}")

    except PermissionError:
        log_lines.append(f"[ERROR] Permission denied while writing: {media_csv_path}")
        log_lines.append("[HINT] Close the media references CSV if it is open.")
        return 0

    return len(media_rows)


def generate_html_timeline_report(
    csv_source_path,
    html_report_path,
    case_id,
    report_title,
    chat_filter,
    record_limit,
    timezone_offset,
    log_lines
):
    if not csv_source_path.exists():
        log_lines.append("[WARNING] HTML report skipped because source CSV does not exist.")
        return 0

    rows = []

    with open(csv_source_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            rows.append(row)

            if record_limit and len(rows) >= record_limit:
                break

    generated_on = datetime.now().isoformat(timespec="seconds")

    html_parts = []

    html_parts.append("<!DOCTYPE html>")
    html_parts.append("<html lang='en'>")
    html_parts.append("<head>")
    html_parts.append("<meta charset='UTF-8'>")
    html_parts.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    html_parts.append(f"<title>{html.escape(report_title)}</title>")

    html_parts.append("""
<style>
body {
    font-family: Arial, Helvetica, sans-serif;
    background: #f5f7fa;
    color: #1f2933;
    margin: 0;
    padding: 0;
}
header {
    background: #111827;
    color: white;
    padding: 24px 36px;
}
header h1 {
    margin: 0 0 8px 0;
    font-size: 24px;
}
header p {
    margin: 4px 0;
    color: #d1d5db;
}
main {
    padding: 28px 36px;
}
.notice {
    background: #fff7ed;
    border-left: 5px solid #f97316;
    padding: 14px 16px;
    margin-bottom: 24px;
    line-height: 1.5;
}
.metadata {
    background: #ffffff;
    padding: 18px;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    margin-bottom: 24px;
}
.metadata table {
    width: 100%;
    border-collapse: collapse;
}
.metadata td {
    padding: 8px;
    border-bottom: 1px solid #e5e7eb;
}
.message-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 14px;
}
.message-meta {
    font-size: 13px;
    color: #4b5563;
    margin-bottom: 10px;
}
.direction {
    font-weight: bold;
}
.message-text {
    white-space: pre-wrap;
    line-height: 1.55;
    font-size: 15px;
}
.badge {
    display: inline-block;
    background: #e5e7eb;
    color: #111827;
    padding: 3px 7px;
    border-radius: 5px;
    font-size: 12px;
    margin-right: 4px;
}
.warning {
    color: #b45309;
    font-size: 13px;
    margin-top: 8px;
}
footer {
    margin-top: 32px;
    padding-top: 18px;
    border-top: 1px solid #d1d5db;
    color: #6b7280;
    font-size: 13px;
}
</style>
""")

    html_parts.append("</head>")
    html_parts.append("<body>")

    html_parts.append("<header>")
    html_parts.append(f"<h1>{html.escape(report_title)}</h1>")
    html_parts.append(f"<p>Case ID: {html.escape(case_id)}</p>")
    html_parts.append(f"<p>Generated On: {html.escape(generated_on)}</p>")
    html_parts.append(f"<p>Tool: {html.escape(SCRIPT_NAME)} v{html.escape(SCRIPT_VERSION)}</p>")
    html_parts.append("</header>")

    html_parts.append("<main>")

    html_parts.append("""
<div class="notice">
<strong>Forensic Note:</strong> This report is an examiner-support output generated from an extracted WhatsApp database working copy.
It should be reviewed alongside the original acquisition records, hash manifest, processing log, and examiner notes.
It does not independently prove authorship, device control, intent, or legal liability.
</div>
""")

    html_parts.append("<section class='metadata'>")
    html_parts.append("<table>")
    html_parts.append(f"<tr><td><strong>CSV Source</strong></td><td>{html.escape(str(csv_source_path))}</td></tr>")
    html_parts.append(f"<tr><td><strong>Chat Filter</strong></td><td>{html.escape(str(chat_filter or 'None'))}</td></tr>")
    html_parts.append(f"<tr><td><strong>Timezone Offset</strong></td><td>{html.escape(str(timezone_offset))}</td></tr>")
    html_parts.append(f"<tr><td><strong>Records Included</strong></td><td>{len(rows)}</td></tr>")

    if record_limit:
        html_parts.append(f"<tr><td><strong>Record Limit</strong></td><td>{record_limit}</td></tr>")
    else:
        html_parts.append("<tr><td><strong>Record Limit</strong></td><td>No limit</td></tr>")

    html_parts.append("</table>")
    html_parts.append("</section>")

    html_parts.append("<section>")

    if not rows:
        html_parts.append("<p>No message records available for this report.</p>")

    for row in rows:
        timestamp_local = row.get("timestamp_local", "")
        timestamp_utc = row.get("timestamp_utc", "")
        direction = row.get("direction_interpreted", "")
        chat = row.get("chat_resolved") or row.get("chat_reference", "")
        sender = row.get("sender_resolved") or row.get("sender_reference", "")
        message_text = row.get("message_text", "")
        message_id = row.get("message_id", "")
        message_type_raw = row.get("message_type_raw", "")
        message_type_label = row.get("message_type_interpreted", "")
        media_reference = row.get("media_reference", "")
        warning = row.get("blank_or_deleted_indicator", "")

        if not message_text:
            message_text = "[No text content exported]"

        html_parts.append("<div class='message-card'>")
        html_parts.append("<div class='message-meta'>")
        html_parts.append(f"<span class='badge'>Message ID: {html.escape(str(message_id))}</span>")
        html_parts.append(f"<span class='badge'>Type: {html.escape(str(message_type_raw))}</span>")
        html_parts.append(f"<span class='badge'>{html.escape(str(message_type_label))}</span>")
        html_parts.append("<br><br>")
        html_parts.append(f"<strong>Local Time:</strong> {html.escape(str(timestamp_local))}<br>")
        html_parts.append(f"<strong>UTC Time:</strong> {html.escape(str(timestamp_utc))}<br>")
        html_parts.append(f"<strong>Chat:</strong> {html.escape(str(chat))}<br>")
        html_parts.append(f"<strong>Sender:</strong> {html.escape(str(sender))}<br>")
        html_parts.append(f"<strong>Direction:</strong> <span class='direction'>{html.escape(str(direction))}</span><br>")

        if media_reference:
            html_parts.append(f"<strong>Media Reference:</strong> {html.escape(str(media_reference))}<br>")

        html_parts.append("</div>")
        html_parts.append(f"<div class='message-text'>{html.escape(str(message_text))}</div>")

        if warning:
            html_parts.append(f"<div class='warning'>{html.escape(str(warning))}</div>")

        html_parts.append("</div>")

    html_parts.append("</section>")

    html_parts.append("<footer>")
    html_parts.append("Generated by SACS WEP. Review with hash manifest, processing log, and source evidence documentation.")
    html_parts.append("</footer>")

    html_parts.append("</main>")
    html_parts.append("</body>")
    html_parts.append("</html>")

    try:
        with open(html_report_path, "w", encoding="utf-8") as report_file:
            report_file.write("\n".join(html_parts))

        log_lines.append(f"[OK] HTML timeline report generated: {html_report_path.resolve()}")
        log_lines.append(f"[OK] HTML report records included: {len(rows)}")

    except PermissionError:
        log_lines.append(f"[ERROR] Permission denied while writing HTML report: {html_report_path}")
        log_lines.append("[HINT] Close the HTML report if it is open in a browser or editor.")
        return 0

    return len(rows)


def main():
    parser = argparse.ArgumentParser(
        description="SACS WEP - SecureAfrica WhatsApp Evidence Processor"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to WhatsApp evidence folder containing ChatStorage.sqlite"
    )

    parser.add_argument(
        "--case-id",
        required=True,
        help="Case identifier, for example SACS-CASE-001"
    )

    parser.add_argument(
        "--output",
        default="outputs",
        help="Output folder. Default is outputs"
    )

    parser.add_argument(
        "--chat-filter",
        default=None,
        help="Optional filter for exporting a selected chat by phone number, JID, name, reference, or message text"
    )

    parser.add_argument(
        "--report-limit",
        type=int,
        default=500,
        help="Maximum number of message records to include in HTML report. Default is 500. Use 0 for no limit."
    )

    parser.add_argument(
        "--timezone-offset",
        default="+00:00",
        help="Timezone offset for local timestamp display, e.g. +01:00 for Nigeria/WAT. Default is +00:00"
    )

    args = parser.parse_args()

    try:
        target_timezone = parse_timezone_offset(args.timezone_offset)
    except ValueError as error:
        print(f"[ERROR] {error}")
        return

    run_stamp = safe_filename_timestamp()

    input_folder = Path(args.input)
    output_root = Path(args.output)
    case_id = args.case_id

    started_at = datetime.now().isoformat(timespec="seconds")

    log_lines = []
    hash_records = []

    log_lines.append(f"{SCRIPT_NAME} Processing Log")
    log_lines.append("=" * 70)
    log_lines.append(f"Tool Version: {SCRIPT_VERSION}")
    log_lines.append(f"Started At: {started_at}")
    log_lines.append(f"Case ID: {case_id}")
    log_lines.append(f"Input Folder: {input_folder.resolve()}")
    log_lines.append(f"Timezone Offset: {args.timezone_offset}")
    log_lines.append(f"Run Stamp: {run_stamp}")
    log_lines.append("")

    if not input_folder.exists():
        print("[ERROR] Input folder does not exist.")
        return

    chat_db = input_folder / "ChatStorage.sqlite"

    if not chat_db.exists():
        print("[ERROR] ChatStorage.sqlite was not found in the input folder.")
        print(f"Checked here: {chat_db.resolve()}")
        return

    folders = create_case_folders(output_root, case_id)

    log_path = folders["logs"] / f"processing_log_{run_stamp}.txt"
    hash_path = folders["hashes"] / f"hash_manifest_{run_stamp}.txt"
    structure_path = folders["case_info"] / f"database_structure_{run_stamp}.txt"

    message_export_path = folders["exports"] / f"all_messages_raw_{run_stamp}.csv"
    chat_summary_path = folders["exports"] / f"chat_summary_{run_stamp}.csv"
    selected_chat_path = folders["exports"] / f"selected_chat_timeline_{run_stamp}.csv"
    media_export_path = folders["exports"] / f"media_references_{run_stamp}.csv"
    html_report_path = folders["reports"] / f"timeline_report_{run_stamp}.html"

    expected_files = [
        "ChatStorage.sqlite",
        "ChatStorage.sqlite-wal",
        "ChatStorage.sqlite-shm"
    ]

    working_database_path = None

    log_lines.append("Evidence File Check")
    log_lines.append("-" * 70)

    for file_name in expected_files:
        source_file = input_folder / file_name

        if source_file.exists():
            log_lines.append(f"[FOUND] {file_name}")

            original_hash = calculate_sha256(source_file)

            hash_records.append({
                "role": "Original Evidence File",
                "file_name": file_name,
                "file_path": str(source_file.resolve()),
                "sha256": original_hash
            })

            destination_file = folders["working_copy"] / f"{run_stamp}_{file_name}"
            shutil.copy2(source_file, destination_file)

            if file_name == "ChatStorage.sqlite":
                working_database_path = destination_file

            copied_hash = calculate_sha256(destination_file)

            hash_records.append({
                "role": "Working Copy",
                "file_name": destination_file.name,
                "file_path": str(destination_file.resolve()),
                "sha256": copied_hash
            })

            if original_hash == copied_hash:
                log_lines.append(f"[HASH MATCH] Original and working copy match for {file_name}")
            else:
                log_lines.append(f"[WARNING] Hash mismatch for {file_name}")

        else:
            log_lines.append(f"[NOT FOUND] {file_name}")

    log_lines.append("")

    if working_database_path is None:
        print("[ERROR] Working database copy was not created.")
        return

    log_lines.append("SQLite Database Inspection")
    log_lines.append("-" * 70)

    structure = {}

    try:
        structure = inspect_sqlite_database(working_database_path)
        write_database_structure(structure_path, structure)

        relevant_tables = detect_relevant_tables(structure)

        log_lines.append("[OK] SQLite database opened in read-only mode.")
        log_lines.append(f"[OK] Total tables detected: {len(structure)}")
        log_lines.append(f"[OK] Database structure written to: {structure_path.resolve()}")

        log_lines.append("")
        log_lines.append("Potential WhatsApp-Relevant Tables")
        log_lines.append("-" * 70)

        if relevant_tables:
            for table in relevant_tables:
                log_lines.append(f"[TABLE] {table}")
        else:
            log_lines.append("[INFO] No obviously relevant WhatsApp tables detected by keyword scan.")

    except sqlite3.DatabaseError as error:
        log_lines.append(f"[ERROR] SQLite database inspection failed: {error}")
        print("[ERROR] SQLite database inspection failed.")
        print(error)

    log_lines.append("")

    lookups = {"chat_lookup": {}, "contact_lookup": {}}

    if structure:
        lookups = build_resolution_lookups(
            working_database_path,
            structure,
            log_lines
        )

    log_lines.append("")
    log_lines.append("Basic Message Extraction")
    log_lines.append("-" * 70)

    selected_records_exported = 0
    html_source_csv = message_export_path
    report_title = "SACS WEP WhatsApp Timeline Report"

    if structure:
        records_exported = extract_messages_basic(
            working_database_path,
            structure,
            message_export_path,
            log_lines,
            lookups,
            target_timezone
        )

        if records_exported > 0:
            export_chat_summary(
                message_csv_path=message_export_path,
                summary_csv_path=chat_summary_path,
                log_lines=log_lines
            )

            export_media_references(
                message_csv_path=message_export_path,
                media_csv_path=media_export_path,
                log_lines=log_lines
            )

            selected_records_exported = export_selected_chat(
                message_csv_path=message_export_path,
                selected_csv_path=selected_chat_path,
                chat_filter=args.chat_filter,
                log_lines=log_lines
            )

            if args.chat_filter and selected_records_exported > 0:
                html_source_csv = selected_chat_path
                report_title = "SACS WEP Selected Chat Timeline Report"
            else:
                html_source_csv = message_export_path
                report_title = "SACS WEP Full WhatsApp Timeline Report"

            log_lines.append("")
            log_lines.append("HTML Timeline Report")
            log_lines.append("-" * 70)

            report_limit = None if args.report_limit == 0 else args.report_limit

            generate_html_timeline_report(
                csv_source_path=html_source_csv,
                html_report_path=html_report_path,
                case_id=case_id,
                report_title=report_title,
                chat_filter=args.chat_filter,
                record_limit=report_limit,
                timezone_offset=args.timezone_offset,
                log_lines=log_lines
            )

    else:
        log_lines.append("[WARNING] Message extraction skipped because database structure was not available.")

    completed_at = datetime.now().isoformat(timespec="seconds")

    log_lines.append("")
    log_lines.append("Output Folders")
    log_lines.append("-" * 70)

    for key, folder in folders.items():
        log_lines.append(f"{key}: {folder.resolve()}")

    log_lines.append("")
    log_lines.append(f"Completed At: {completed_at}")
    log_lines.append("=" * 70)

    write_hash_manifest(hash_path, hash_records)
    write_log(log_path, log_lines)

    print("[SUCCESS] SACS WEP v0.7.0 completed.")
    print(f"Case Output Folder: {folders['case_folder'].resolve()}")
    print(f"Hash Manifest: {hash_path.resolve()}")
    print(f"Processing Log: {log_path.resolve()}")
    print(f"Database Structure: {structure_path.resolve()}")
    print(f"Message Export: {message_export_path.resolve()}")
    print(f"Chat Summary: {chat_summary_path.resolve()}")
    print(f"Media References: {media_export_path.resolve()}")
    print(f"HTML Report: {html_report_path.resolve()}")

    if args.chat_filter:
        print(f"Selected Chat Export: {selected_chat_path.resolve()}")


if __name__ == "__main__":
    main()