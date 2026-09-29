From an assessment, _Request Debits_ or _Request Credits_ opens the request and stores
the returned ticket. The rest of the cycle is automatic: the callback marks the request
as ready to download, and the scheduled action downloads the file and applies it to the
periods it carries.

A refusal leaves the request in the _Error_ state with the code and the message that
came back, instead of raising a dialog: the reason has to survive on the record, and the
call is charged by the gateway even when refused, so it counts against the daily quota.

When the callback does not arrive, _Check Status_ polls the status endpoint. A request
whose processing exceeded the limit of 240 minutes comes back with an error and has to
be opened again.

The signed download URL is valid for **48 hours**. After that the addon refuses to
download and a new request is needed. The URL authorises the download on its own, so it
is stored as a secret, restricted to assessment managers and never written to the log.

Because each answer only carries what changed since the previous query, with a window of
at most 8 days, the assessment is only complete if the requests are opened regularly.
Enable the daily scheduled action, or open them by hand often enough, and never rely on
a single request at the end of the period.
