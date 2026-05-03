# SACS WEP Forensic Limitations

SACS WEP is a forensic support utility. It assists with processing, structuring, and reviewing extracted WhatsApp data, but it does not replace professional forensic examination.

## 1. Acquisition Limitation

SACS WEP does not acquire evidence from phones or cloud accounts. It only processes files already extracted by lawful and appropriate means.

## 2. Encryption Limitation

SACS WEP does not bypass WhatsApp encryption, phone locks, backup passwords, or account protections.

## 3. Deleted Message Limitation

SACS WEP may indicate blank or missing text fields, but this should not automatically be interpreted as a deleted message.

A blank text field may represent:

- media message;
- system message;
- unsupported message type;
- deleted or retracted message;
- schema difference;
- extraction limitation.

Further examination is required.

## 4. Authorship Limitation

SACS WEP cannot independently prove who physically typed or sent a message.

A message associated with a device/account does not automatically prove:

- physical possession at the time;
- intent;
- voluntariness;
- identity of the human operator;
- absence of compromise.

## 5. Schema Limitation

WhatsApp database schemas vary across iOS versions, WhatsApp versions, backup types, and extraction methods.

Some fields may be blank or unresolved because the database uses a schema not yet mapped by the tool.

## 6. Timestamp Limitation

SACS WEP converts Apple/Core Data timestamps using the 2001-01-01 UTC epoch. Timezone conversion depends on the examiner-supplied offset.

The examiner should verify:

- device timezone;
- relevant local timezone;
- daylight saving where applicable;
- acquisition context;
- consistency with other evidence.

## 7. Media Limitation

SACS WEP exports media references when detectable. It does not yet locate, verify, hash, or preview all associated media files.

Media references should be compared with the extracted media folder and independently hashed where necessary.

## 8. Reporting Limitation

The HTML timeline report is a review aid, not a final expert report.

Final reporting should include:

- acquisition method;
- tool version;
- hash values;
- source file details;
- chain-of-custody details;
- examiner interpretation;
- limitations;
- validation steps.