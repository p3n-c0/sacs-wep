# SACS WEP Validation Report

## Tool Information

- Tool Name: SACS WEP (SecureAfrica WhatsApp Evidence Processor)
- Version: v0.7.0
- Validation Date: 2026-05-03
- Examiner: Ibrahim Sulaiman. A., CEO, SACS (Nig) Ltd.

---

## Objective

The purpose of this validation exercise was to assess the accuracy and reliability of SACS WEP in processing WhatsApp `ChatStorage.sqlite` databases and producing structured forensic outputs.

The validation focused on:

- database structure detection;
- message extraction completeness;
- timestamp conversion accuracy;
- direction (incoming/outgoing) interpretation;
- message text extraction;
- media reference detection;
- chat summary generation;
- selected chat extraction;
- hash integrity verification;
- reporting outputs.

---

## Test Dataset

### Case A

- Source: Extracted WhatsApp iOS database
- File: `ChatStorage.sqlite`
- WAL file: Not present
- SHM file: Not present
- Total database tables detected: 18
- Key table: `ZWAMESSAGE`

---

## Validation Methodology

The validation followed a comparative approach using:

- SACS WEP outputs
- :contentReference[oaicite:0]{index=0} manual inspection

The following steps were performed:

1. Database structure comparison
2. Message count comparison
3. Field-by-field validation
4. Timestamp conversion verification
5. Direction interpretation verification
6. Message text validation
7. Blank/empty message analysis
8. Media reference validation
9. Chat summary comparison
10. Selected chat extraction testing
11. HTML report review
12. Hash integrity verification
13. Processing log review

---

## Results

### 1. Database Structure

- `ZWAMESSAGE`: detected in both DB Browser and SACS WEP
- `ZWACHATSESSION`: detected in both
- `ZWAGROUPMEMBER`: detected in both
- `ZWAPROFILEPUSHNAME`: detected in both
- `ZWAMEDIAITEM`: present in database; detection confirmed via processing log

Conclusion:
Database structure detection is accurate.

---

### 2. Message Count

- DB Browser count: 44,834
- SACS WEP exported records: 44,834

Conclusion:
Message extraction is complete and consistent with source database.

---

### 3. Field Mapping Validation

The following mappings were confirmed:

- `Z_PK` → `message_id`
- `ZCHATSESSION` → `chat_reference`
- `ZISFROMME` → `direction_raw`
- `ZMESSAGEDATE` → `timestamp_raw`
- `ZMESSAGETYPE` → `message_type_raw`
- `ZTEXT` → `message_text`

Conclusion:
Core field extraction is correct.

---

### 4. Timestamp Conversion

Sample values:

- Raw timestamp: `423654623`
- Converted UTC: `2014-06-05 09:50:23`

Timezone offset used:

```text
+01:00 (West Africa Time)