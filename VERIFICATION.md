# Verification of the replacement package

Created on 3 November 2026 after reviewing the complete original conversation.

The earlier attachment's binary file was unavailable: the conversation exposed an unresolved attachment reference, not downloadable project bytes. Its original type cannot be confirmed. This package was recreated from the agreed requirements; it is not claimed to be a recovered copy of the original.

Checks performed:

- All 16 behaviour tests passed.
- Live retrieval and generation succeeded for all seven cinemas.
- Live build at 2026-11-03T23:34:21Z generated 405 special-screening entries and 692 grouped film entries. Counts will change with future listings.
- An independent iCalendar parser read both generated calendars successfully. Event IDs were unique within each feed, required event fields were present, end dates followed start dates, and UTF-8 physical lines respected the 75-octet limit.
- The workflow YAML parsed successfully; the scheduled trigger, output path and build-to-deploy dependency were checked.
- The final ZIP's file signature, full member integrity, required paths (including the hidden workflow), extraction and tests from the extracted copy were checked.

No GitHub repository was changed. The GitHub-hosted workflow, Pages deployment and Apple Calendar subscriptions have not been activated or tested in your account. Local verification does not claim otherwise.

## Live build counts

| Cinema | Special screenings | Film entries |
|---|---:|---:|
| Prince Charles Cinema | 231 | 290 |
| BFI Southbank | 96 | 153 |
| The Nickel | 12 | 59 |
| The Garden Cinema | 38 | 78 |
| Rio Cinema | 11 | 40 |
| Genesis Cinema | 7 | 41 |
| The Castle Cinema | 10 | 31 |
