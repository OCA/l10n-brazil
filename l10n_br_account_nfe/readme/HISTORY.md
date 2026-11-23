## Unreleased

- The tags `dup` and `detPag` of an issued NF-e or NFC-e are no longer computed
  fields redeclared here. `l10n_br_nfe` writes them when the invoice is posted,
  from what `l10n_br_account_edi` reads of the invoice (`_edi_installments()`
  and `_edi_payments()`). Until the posting they are empty, and the invoice and
  the fiscal document show the installments and the payment as a preview. A
  customization that reads the tags of a draft invoice must read the preview.
- The module no longer depends on `l10n_br_account_due_list`: it reads the due
  lines of the invoice itself, and `due_line_ids` is only there when that module
  is installed by someone else.
- Removed, because their rules moved to `l10n_br_nfe` and
  `l10n_br_account_edi`: `_compute_nfe40_dup`, `_need_compute_nfe40_dup`,
  `_compute_nfe40_detpag`, `_is_installment`, `_is_without_payment`, the
  override of `_compute_imported_terms` and the constants `A_PRAZO`, `A_VISTA`,
  `SEM_PAGAMENTO`, `NFE_IN` and `NFE_OUT` (now in `l10n_br_nfe.constants.nfe`).
  What remains here is the means of payment of the payment mode, its check, the
  refund with a payment mode, the DANFE of the invoice and the offline
  contingency of the NFC-e.
- `models/leiauteNFe.py` is gone: the selection of `nfe40_indPag` is the one of
  the NF-e spec, and the stored values do not change.

## 12.0.1.0.0 (2022-03-30)

- \[NEW\] Primeira versão
