## 16.0.18.3.1

- The import wizard of this module (`l10n_br_fiscal.document.import.wizard`
  extended with "Import Account Move" and `first_imported_move_id`) is removed
  with the wizard of `l10n_br_fiscal`. The fiscal document is imported by the
  window of `l10n_br_fiscal_edi`, and the vendor bill is generated from it by
  `l10n_br_account_edi` ("Generate invoice"), which this update installs
  (post-migration) when `l10n_br_fiscal_edi` is installed. See the HISTORY of
  `l10n_br_fiscal` for what replaces each method and the list of what is
  removed.
