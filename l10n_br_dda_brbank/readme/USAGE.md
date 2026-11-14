1. In *Invoicing > Configuration > Bank Connections*, open (or create and
   connect) the connection of a bank that supports DDA, such as BTG. Its CNPJ is
   the one the boletos are registered against.
2. In the *DDA* tab, click *Enable DDA*. The bank is asked to turn DDA on and the
   first synchronization, a full one, starts at once. *Synchronize now* pulls
   again, *Disable DDA* turns it off at the bank (the boletos captured stay).
3. Register the webhook URL of the connection (*Webhook* tab) at the bank to
   receive the boletos in real time. Without it the hourly pull brings them.
4. The state of each connection shows on the panel of *DDA Boletos*, next to the
   CNAB file source. The *DDA* tab lists the last synchronization and the
   events. An event in *Quarantine* failed eight times: read its error, fix the
   cause and click *Process again*.
5. The events also have a technical menu (developer mode) under *Invoicing >
   Configuration > DDA Bank Events*. The periods of the crons (events, hourly
   pull, daily reconciliation) are in *Settings > Technical > Scheduled
   Actions*.
6. Processed events are purged by a daily cron after 30 days (system
   parameter `l10n_br_dda_brbank.event_retention_days`). Events in error or in
   quarantine are never purged.

For tests and demos, the demo data points the BTG connection at the bank
simulator of the library (`python -m brbank.simulador --semente demo`, port
8899) with DDA already on.
The boletos of that seed are registered against the fictitious CNPJ
91.300.766/0001-47, the one of the connection: to see them in the inbox, a
company needs this CNPJ.
