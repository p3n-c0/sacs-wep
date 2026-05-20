# SACS WEP (SecureAfrica WhatsApp Evidence Processor)

SACS WEP is a forensic-oriented WhatsApp database processing utility developed by SecureAfrica Cyber Solutions (SACS). It is designed to assist investigators, analysts, researchers, and DFIR practitioners in transforming raw WhatsApp SQLite evidence into structured, readable, and reviewable outputs.
The tool currently focuses on iOS WhatsApp databases (`ChatStorage.sqlite`) and emphasizes:
- evidence-safe workflow
- working-copy handling
- message extraction
- timeline generation
- entity resolution
- output hashing
- structured exports

SACS WEP is not intended to replace commercial forensic suites. Instead, it serves as a lightweight forensic utility for evidence review, validation, timeline reconstruction, and investigative support.

---

# Current Version
v0.9.0

# Key Features
- WhatsApp Database Processing
- Processes ChatStorage.sqlite
- Supports associated -wal and -shm files
- Uses read-only SQLite access during analysis
- Creates forensic working copies before processing

# Message Extraction
Extracts WhatsApp message records from: ZWAMESSAGE
including:
- timestamps
- message text
- message types
- sender/recipient information
- media references
- group event data

# Message Categorization
Messages are categorized into:
| Category | Message Types       |
| -------- | ------------------- |
| text     | 0                   |
| media    | 1, 2, 3             |
| system   | 6, 10               |
| other    | all remaining types |

This classification model was developed through empirical validation on real datasets and may vary across WhatsApp versions.

# Entity Resolution (v0.9.0)
v0.9.0 introduces entity resolution using:
- ZWACHATSESSION
- ZWAGROUPMEMBER
- ZWAPROFILEPUSHNAME
This improves timeline readability by resolving:
- chat JIDs
- chat names
- sender JIDs
- sender names
- pushnames
- group member information
Group event attribution now prioritizes actual group members, where available, rather than incorrectly attributing actions to the group container itself.

# Timeline Reporting
Generates:
- CSV exports
- selected chat exports
- HTML timeline reports
- chat summaries

The HTML report includes:
- timestamps
- message categories
- sender information
- chat information
- media references
- direction interpretation

# Hashing and Integrity
SACS WEP generates SHA-256 hashes for:
- original evidence files
- working copies
- generated outputs

This assists with:
- integrity verification
- repeatability
- examiner documentation

# Folder Structure
Example output structure:

<img width="462" height="142" alt="image" src="https://github.com/user-attachments/assets/466fb8b2-be60-426a-ba91-cc99fa27eb9b" />


# Example Outputs
## Exports
<img width="451" height="125" alt="image" src="https://github.com/user-attachments/assets/6cf86097-d4b1-4aa1-9161-f7df4c8f9678" />


## Reports
- timeline_report.html

## Integrity
- hash_manifest.txt

## Logging
- processing_log.txt
- run_summary.txt
- database_structure.txt

# Installation
## Requirements
- Python 3.10+
- Windows/Linux/macOS
- No external dependencies currently required

## Clone Repository
git clone https://github.com/p3n-c0/sacs-wep.git

## Move into Project Folder
cd sacs-wep

## Quick Start
Place your WhatsApp evidence files inside a folder.
Example:
<img width="446" height="93" alt="image" src="https://github.com/user-attachments/assets/a0bbdacf-3b53-4c4c-b75c-940262d0202c" />


Run
python sacs_wep.py --input "path_to_whatsapp" --case-id "SACS-CASE-001"

Example
python sacs_wep.py --input "C:\Evidence\WhatsApp" --case-id "CASE-A"

# Common Usage Examples
## Standard Processing
python sacs_wep.py --input "C:\Evidence\WhatsApp" --case-id "CASE-A"

## Set Local Timezone
python sacs_wep.py --input "C:\Evidence\WhatsApp" --case-id "CASE-A" --timezone-offset "+01:00"

## Export Selected Chat
python sacs_wep.py --input "C:\Evidence\WhatsApp" --case-id "CASE-A" --chat-filter "2348160119708-1407054136@g.us"
You can filter using:
- phone number
- JID
- chat name
- sender name
- message text

## Generate Full HTML Report
python sacs_wep.py --input "C:\Evidence\WhatsApp" --case-id "CASE-A" --report-limit 0

# Validation
SACS WEP v0.9.0 was validated against a real WhatsApp dataset containing:
  44,834 records

Validated capabilities:
- message extraction
- category classification
- entity resolution
- selected chat export
- HTML reporting
- output hashing
- chat summarization

Validation results included:
  Resolved Chat Records: 44799
  Resolved Sender Records: 44833

# Important Notes
This is not a full forensic suite. Rather, SACS WEP is a forensic support utility intended for:
- review
- validation
- timeline reconstruction
- evidence organization

It does not independently establish:
- authorship
- intent
- legal attribution
- device ownership

Examiner interpretation remains essential.

# Media Extraction
Media extraction and reconstruction are not yet implemented.
Current versions primarily process:
- metadata
- message structure
- timeline information

# WhatsApp Version Differences
WhatsApp database structures change over time. Some fields, message types, and relationships may differ depending on:
- iOS version
- WhatsApp version
- backup method
- acquisition method

# Future Development
Planned areas of improvement include:
- participant summary analytics
- media awareness improvements
- Android WhatsApp support
- improved timeline intelligence
- enhanced group event interpretation
- richer reporting formats

# License
This project is currently released for research, educational, and investigative utility purposes. Formal licensing may be updated in future releases.

# Author
SecureAfrica Cyber Solutions (SACS)

## Developed by:
Ibrahim Sulaiman. A.
CEO, SACS (Nig) Ltd.

# Disclaimer
This tool should be used responsibly and lawfully. Users are responsible for ensuring:
- lawful acquisition
- proper authorization
- chain-of-custody compliance
- jurisdictional compliance
- ethical handling of digital evidence
The author and organization are not responsible for the misuse of this software.
