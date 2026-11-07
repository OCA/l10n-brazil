Feeds the DDA inbox (`l10n_br_dda`) from the API of the bank, through the shared
bank connection (`l10n_br_bank_connection`) and the
[brbank](https://pypi.org/project/brbank/) library. Three paths bring the boletos
registered against the CNPJ of the company, and all of them end in the same
idempotent `_dda_upsert`:

- **Webhook**: the notification of the bank is validated, stored as an event
  (deduplicated by connection and event id) and answered at once; a cron
  triggered by the call does the work. A new or changed boleto comes with its
  data and needs no query to the bank. A boleto reported as paid is read back
  from the listing and becomes *paid elsewhere* in the inbox, with no
  accounting entry.
- **Incremental pull**, hourly: the boletos due since a week before the last
  pull, page by page, a commit per page, resumable after a failure.
- **Daily reconciliation**: the full listing, the bank being the truth.

The event queue works in blocks of 20 with a commit per block, retries with a
backoff that doubles up to one hour, puts an event in quarantine after eight
failures and is fair between connections. *DDA disabled at the bank* turns the
synchronization status to error and schedules an activity for an administrator.
