# SACS WEP (SecureAfrica WhatsApp Evidence Processor)

SACS WEP is a lightweight forensic support tool for processing extracted iOS WhatsApp `ChatStorage.sqlite` databases into structured CSV outputs and readable HTML timelines.

It is designed for digital forensic examiners, cybercrime investigators, legal support teams, and students working with WhatsApp evidence.

---

## Why This Exists

Working directly with WhatsApp SQLite databases can be slow and error-prone. After extraction, investigators are often left with raw tables (`ZWAMESSAGE`, `ZWACHATSESSION`, etc.), unfamiliar field names, and timestamps that are not immediately interpretable.
SACS WEP provides a structured way to move from raw database records to:
- readable timelines  
- organized message exports  
- quick chat-level summaries  

without modifying the original evidence.

---

## Features

- Processes iOS WhatsApp `ChatStorage.sqlite`
- Creates working copies with hash verification
- Extracts full message records from `ZWAMESSAGE`
- Converts Apple/Core Data timestamps (2001 epoch)
- Supports timezone offset (e.g., +01:00 for WAT)
- Exports:
  - full message dataset (CSV)
  - chat summary (CSV)
  - selected chat timeline (CSV)
  - media-related records (CSV)
- Generates HTML timeline report
- Produces:
  - processing logs
  - hash manifest
  - database structure report

---

## Quick Start

### 1. Prepare your evidence folder
Place your extracted WhatsApp files in a folder. For example, C:\Users\YourName\Desktop\WhatsApp\ChatStorage.sqlite
  * (optional) ChatStorage.sqlite-wal
  * (optional) ChatStorage.sqlite-shm

### 2. Run the tool
python sacs_wep.py --input "C:\Users\YourName\Desktop\WhatsApp" --case-id "CASE-001"

Important: The --input argument must point to the folder, not the .sqlite file itself.

### 3. Optional: Set local timezone (Nigeria/WAT)
python sacs_wep.py --input "C:\Users\YourName\Desktop\WhatsApp" --case-id "CASE-001" --timezone-offset "+01:00"

### 4. Optional: Export a specific chat
python sacs_wep.py --input "C:\Users\YourName\Desktop\WhatsApp" --case-id "CASE-002" --chat-filter "2348012345678" --timezone-offset "+01:00"

### 5. Optional: Generate full HTML report (no record limit)
python sacs_wep.py --input "C:\Users\YourName\Desktop\WhatsApp" --case-id "CASE-003" --report-limit 0

OPTIONAL STRUCTURE

outputs/
└── CASE-001/
    ├── Working_Copy/
    ├── Exports/
    │   ├── all_messages_raw_[timestamp].csv
    │   ├── chat_summary_[timestamp].csv
    │   ├── selected_chat_timeline_[timestamp].csv
    │   └── media_references_[timestamp].csv
    ├── Reports/
    │   └── timeline_report_[timestamp].html
    ├── Hashes/
    │   └── hash_manifest_[timestamp].txt
    ├── Logs/
    │   └── processing_log_[timestamp].txt
    └── Case_Info/
        └── database_structure_[timestamp].txt

Example Output

<img width="1046" height="633" alt="image" src="https://github.com/user-attachments/assets/52da060f-8793-4482-8c28-65bdbdb35b12" />


## Validation
SACS WEP has been tested against real WhatsApp database data. Validation included:
    message count verification against direct SQL queries
    timestamp conversion checks (Apple epoch → UTC → local time)
    direction field validation (ZISFROMME)
    message text comparison
    chat summary verification
    selected chat extraction testing
    hash integrity checks
See: VALIDATION_REPORT.md

## Limitations
SACS WEP is a forensic support tool, not a full forensic suite. Current limitations include:
    media reference detection is broad and may include system/service records
    chat/contact resolution depends on available database fields
    schema variations across WhatsApp versions may affect field mapping
    media file extraction and hashing are not yet implemented
    Android WhatsApp databases are not currently supported

## Forensic Disclaimer
SACS WEP:
does not acquire evidence
does not bypass encryption or device locks
does not recover overwritten deleted data
does not prove authorship or intent

All outputs must be reviewed alongside:
original evidence
acquisition records
hash verification
examiner analysis

This tool assists analysis but does not replace professional forensic judgment.

## Requirements
Python 3.9+
No external libraries required (standard library only)

## Future Improvements (v0.8.0)
refined media detection logic
improved chat and contact resolution
output file hashing
schema adaptability enhancements
media file linkage and hashing

## Author
Ibrahim Sulaiman. A.
CEO, SACS (Nig) Ltd.
Digital Forensics & Cybercrime Investigations
