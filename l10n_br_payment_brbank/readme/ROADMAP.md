- **Only Sicoob (boleto and Pix) has been validated in a bank sandbox**, the
  public one of Sicoob, which checks the requests against the API contract but
  keeps no state; the production OAuth, mTLS and scopes are still unproven.
  All the other adapters have `validado_sandbox = False`: they were built
  from public documentation. The provider form and the payment mode warn about
  it. Test each bank with low amounts before production.
- The manifest names the `brbank` package without a version (a specifier there
  breaks the import check), so the minimum version is not enforced at install.
- The registration runs in the transaction that posts the invoice. If that
  transaction is rolled back after the bank answered, the bank keeps the
  title; the next attempt sends the same idempotency key (Pix answers
  `Duplicado` and the title is read back), but a boleto bank that does not
  deduplicate by our reference may keep an orphan title. The nosso numero is
  kept on the transaction, so a retry of the same transaction sends the same
  number; a transaction undone by the rollback takes a new number on the next
  attempt (the sequence never gives a number twice).
- Webhooks are only parsed for the banks whose adapter declares them (Inter,
  Sicredi, BTG Pactual, C6 Bank, Unicred and the Pix profiles); the others
  rely on the reconciliation cron.
- The digits of the nosso numero of each bank are a map in the module
  (`NOSSO_NUMERO_DIGITS`), checked by a test against the adapters that take
  `gerar_nosso_numero`; the library does not publish them in a uniform way.
- BTG Pactual: the authorization code flow (consent at the BTG Id) is done
  outside Odoo. Two calls renewing the same refresh token at the same time
  (two workers) may leave one of them with a token the bank already replaced.
- Caixa has no test environment: the provider cannot use the test mode.
- The webhook events are processed by `ir.cron` with an immediate trigger, not
  by `queue_job`, so the module adds no dependency; move to `queue_job` if a
  bank sends large volumes.
- The CNAB bridge is a hook (`_brbank_notify_cnab_occurrence`): no return file
  module calls it yet.
- The brbank providers are left out of the online checkout: the redirect and
  token flows of `payment` are not implemented for them.
- The credentials are stored in the database, restricted to the settings
  group; a vault (Vault, KMS) is not supported yet.
- The reconciliation cron queries each open title; banks with batch queries or
  movement statements could be read in one call per account.
- No alert yet for certificates close to expiry.
- The provider records use the module icon; the logos of the banks are not shipped.
