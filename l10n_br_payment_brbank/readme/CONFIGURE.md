1. Install the `brbank` Python library in the Odoo environment
   (`pip install "brbank>=0.0.12"`). It needs Python 3.10 or later. Version
   0.0.12 is the minimum: it brings the Santander, Itaú and Bradesco settings
   described below (the manifest only names the package, so the version is
   not checked at install). For Sicoob, the
   document kind (`codigo_especie_documento`) is the acronym, for instance
   `DM`, and no longer a number.
2. Go to *Invoicing > Configuration > Bank Connections* and create the
   connection of the bank account (see the module `l10n_br_bank_connection`):
   adapter, environment (test uses the bank sandbox), CNPJ, credentials, the
   JSON of *Extra Settings* and *Extra Secrets* (*Fill settings template* lists
   the keys), and the consent at the bank where the adapter needs one (BTG).
   The webhook URL to register at the bank is on the connection.
3. Go to *Invoicing > Configuration > Payment Providers* and open the provider
   of the bank (for instance *Sicoob (Boleto)* or *Pix Itaú*): the bank
   adapter (and the Pix profile) are already set by the data; choose the
   *Bank Connection*. One connection can serve several providers.
4. Set the provider to *Test Mode* or *Enabled* and choose its journal in the
   *Configuration* tab. The provider refuses to leave *Disabled* without a
   connection of the same adapter, or while a required key is missing. Test
   or production is decided by the *environment* of the connection.
5. In the payment mode (*Invoicing > Configuration > Payment Modes*), tick
   *Generate boletos on invoice?* and choose the provider. The payment mode
   shows what the bank supports.
6. To send rebates, choose the *Rebate Account* of the provider: the rebate is
   refused before reaching the bank while it is empty.

The webhook URL to register at the bank is the one of the connection; the
route `/payment/brbank/webhook/<provider>/<token>` is kept as an alias.
Keys typed as a function in the library (`gerar_nosso_numero`,
`ao_renovar_refresh_token`) never go in the JSON: the provider and the
connection serve them.

Notes per bank:

- **BTG Pactual**: the API only accepts tokens of the authorization code flow.
  Use *Connect* on the bank connection (or paste a refresh token in *Refresh
  Token*). The bank may return a new refresh token at each renewal and
  invalidate the old one: the connection saves it at once, in a database
  transaction of its own, so an error or a rollback of the operation never
  loses it, and the renewals of the workers are serialized by a lock of the
  database. A refresh token unused for more than 10 days expires and the
  consent must be done again. Use each BTG credential in one database only.
  Fill `dias_expiracao` (days after the due date until the title expires), or
  the bank refuses titles without an automatic write-off term.
- **Caixa**: there is no public test environment, so the connection refuses the
  test environment. Use production and validate with a title of low amount.
  `documento_beneficiario` is a secret key (*Extra Secrets*).
- **C6 Bank**: the Pix key must be a random key (EVP); the bank silently issues
  a boleto without Pix with any other kind.
- **Itaú**: `bolecode` (hybrid boleto) is on by default and needs the Pix key.
  When the bank delivers a separate credential for the Bolecode, fill
  `bolecode_client_id` and, in *Extra Secrets*, `bolecode_client_secret`,
  `bolecode_certificado_pem` and `bolecode_chave_pem`. A protest needs
  `dias_protesto`; without it the instruction is recorded as rejected.
- **Santander**: the Pix key needs `tipo_chave_pix` (EMAIL, CPF, CNPJ, CELULAR
  or EVP); `workspace_id` is the billing workspace created at the bank. Set
  `webhook_ativo` to true before registering the webhook URL in the workspace:
  without it the webhook is refused.
- **Bradesco**: `documento_beneficiario` is a secret key (*Extra Secrets*). With
  `hibrido` (boleto with QR code) the bank takes no protest by instruction.
- **Banrisul**: the provider sends the 8 free digits of the nosso numero and
  the library adds the check digits.
- **Unicred**: `api_key` and the two webhook keys go in *Extra Secrets*.
- **Safra**: the bank declares no capability (no write-off, instruction, PDF
  nor webhook): titles are followed by the reconciliation cron only.

Nosso numero: for the banks where the issuer chooses it (Banco do Brasil,
Bradesco, Itaú, Santander, Banrisul, Caixa and Safra) the provider creates its own
sequence (*Nosso Numero Sequence*) at the first title, starting after the
numbers already registered by it. The number is taken before the first call
to the bank and kept on the transaction (*Nosso Numero Sent*), so a retry
sends the same one, and a number is never given twice. When the sequence
passes the digits of the bank (Itaú 8, Banrisul 8, Safra 9, Banco do Brasil
10, Bradesco 11, Santander 12, Caixa 15), the registration stops with an error instead of
cutting the number: agree with the bank on a new wallet or agreement.

Only users of *Administration / Settings* see and edit the credentials (on the
connection). The webhook token travels in the URL: mask it in the logs of the
reverse proxy.

Crons:

- *Boleto brbank: reconcile titles with the banks*, every 30 minutes.
  Lengthen it only when the webhook of every bank in use is validated in
  production.
- *Boleto brbank: process bank webhook events*, triggered by every webhook call
  and every 10 minutes as a fallback.
