# SACS WEP

**SecureAfrica WhatsApp Evidence Processor**

SACS WEP is a lightweight forensic support tool for processing extracted iOS WhatsApp `ChatStorage.sqlite` databases into readable CSV and HTML timeline outputs.

It is designed for digital forensic examiners, cybercrime investigators, legal-support personnel, and students who need a structured way to review WhatsApp evidence after lawful extraction.

## Current Version

v0.7.0

## What SACS WEP Does

SACS WEP can:

- accept an extracted WhatsApp evidence folder;
- locate `ChatStorage.sqlite`;
- hash original evidence files;
- create working copies;
- inspect SQLite database tables and columns;
- extract basic WhatsApp message records;
- convert Apple/Core Data timestamps;
- export all messages to CSV;
- generate a chat summary;
- export selected chats using a filter;
- export media-related message references;
- generate an HTML timeline report;
- write processing logs and hash manifests.

## What SACS WEP Does Not Do

SACS WEP does not:

- acquire data from phones;
- bypass device locks;
- bypass WhatsApp encryption;
- recover overwritten deleted messages;
- prove authorship by itself;
- replace forensic suites such as Cellebrite, Magnet, Belkasoft, or Elcomsoft;
- produce legal conclusions;
- modify original evidence.

## Expected Input

Place your extracted WhatsApp files in a folder such as:

```text
test_evidence/
└── WhatsApp/
    ├── ChatStorage.sqlite
    ├── ChatStorage.sqlite-wal
    └── ChatStorage.sqlite-shm