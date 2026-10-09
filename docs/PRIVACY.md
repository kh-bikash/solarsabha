# Privacy and data protection

This is what SolarSabha stores, why, and the controls built into the code. The in-app notice (Settings, and the consent
step when creating a project) says the same in plain language. Notice version: **2026-10**.

## What is stored, per project

| Data | Why | Where in the code |
|---|---|---|
| Society details (name, flats, address, DISCOM, application and consumer numbers) | Sizing, letters | `inputs.society` |
| Uploaded bills and quotations (original files) | So a person can check what was read | S3 / `.state/files` (`files.py`) |
| Numbers read from them | Plan and quote audit | `inputs.bills`, `inputs.quotes` |
| Committee member names and roles | Who may change or approve | `members` |
| Drafts, edits, approvals | The committee's paper trail | `draft_state`, `drafts` |
| Activity log (who did what, when) | Accountability | `audit` (last 500 entries) |
| Consent record (who, when, notice version) | DPDP Act, 2023 | `consent` |

Not stored: passwords, payment details, phone numbers or email addresses. The browser keeps only the list of projects
it has opened (local storage); there are no tracking cookies.

## Controls

- **Access**: each project has a random access key (192 bits). Only its SHA-256 hash is stored; the key travels in the
  share link's `#fragment`, which browsers never send to servers in the URL. Every project route checks it (`project.check_key`).
- **Roles**: secretary (everything), member (edit, upload, approve), viewer (read only), enforced on every route that changes
  data. Names are chosen within a project's members; for verified identities, put an identity provider (e.g. Amazon Cognito)
  in front of the API.
- **Consent**: a new project cannot be created without accepting the notice; the acceptance is recorded.
- **Retention**: every project has `expires_at` (default 365 days, `RETENTION_DAYS`). Expired projects read as missing;
  DynamoDB TTL deletes them and an S3 lifecycle rule expires their files.
- **Export**: `GET /projects/{id}/export` (Settings > Export) returns everything stored, as JSON.
- **Erasure**: `DELETE /projects/{id}` (Settings > Delete, secretary only, type the society name) removes the record and all files.
  Individual originals can be deleted from Documents; the numbers read from them stay.
- **Encryption**: DynamoDB and S3 encrypted at rest; the bucket denies non-TLS access and blocks public access.
- **Logs**: one JSON line per request (method, route, status, time, project id); no document content, no names. 30-day retention.
- **AI processing**: off by default (offline reader). When `READER_MODE=live`, documents go to Amazon Bedrock with an
  India-only inference profile (`in.*`); Bedrock does not use them to train models.
- **No outbound actions**: the code has no send, sign, pay or file function.

## Data principal rights (DPDP Act, 2023)

Access (export), correction (edit in Documents and Settings), erasure (delete), and grievance: set
`VITE_PRIVACY_CONTACT` to the operator's contact so the notice shows it.
