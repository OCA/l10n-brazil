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
5. Client certificate (mTLS), for the banks that ask for one: load the A1 of
   the company once, as a `.pfx` file with its password, in *Settings >
   Certificates and Keys > Certificates*, and choose it in the *Certificate*
   field of the connection (the certificate of the company is suggested when
   the bank asks for one). The PEM certificate and key fields remain for a
   certificate kept outside Odoo.
6. In the test environment, *Generate test certificate* creates a self-signed
   certificate (RSA 2048, SHA-256, one year, subject
   `CN=LEGAL NAME:CNPJ, C=BR, O=LEGAL NAME`, as the Bradesco asks), keeps it on
   the connection and downloads only its public part (`.pem`), to upload at the
   bank portal. The button does not show in production.
7. The connection remembers the certificate the bank credential was issued
   with. When it changes (a renewed A1), a warning asks to renew the credential
   at the bank portal (Bradesco: *Solicitar Credencial*, *Renovação
   certificado*) and to confirm with *Credential renewed at the bank*. Changing
   the environment starts a new credential, without warning.

Developers: call the bank with
`connection._l10n_br_bank_run(lambda adapter: adapter.method(...))`, and
extend `_l10n_br_bank_handle_webhook`, `_l10n_br_bank_test_connection` and
`_l10n_br_bank_sync_report` from the module of the domain.
