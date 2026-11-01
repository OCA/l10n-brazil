1. Go to *Invoicing > Configuration > Bank Connections* and create a
   connection: choose the bank adapter (and the Pix profile), the environment
   (test uses the bank sandbox) and the CNPJ of the account holder.
2. In *Credentials*, fill what the adapter asks for (only those fields are
   shown). *Fill settings template* in *Bank Settings* lists the other keys of
   the adapter (agreement, wallet, client number, developer key and so on).
3. For BTG, click *Connect*: Odoo sends you to the bank, you grant the consent
   and come back connected, with the refresh token saved. A refresh token
   unused for more than 10 days expires; the connection then asks to
   *Reconnect*.
4. *Test connection* gets a token from the bank. The webhook URL, to register
   at the bank, is in the *Webhook* tab; *Rotate webhook token* stops the old
   one at once. The URL carries a secret: mask it in the logs of the proxy.

Developers: call the bank with
`connection._l10n_br_bank_run(lambda adapter: adapter.method(...))`, and
extend `_l10n_br_bank_handle_webhook`, `_l10n_br_bank_test_connection` and
`_l10n_br_bank_sync_report` from the module of the domain.
