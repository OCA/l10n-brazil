## 16.0.1.0.0

- The installments declared by an imported document are consumed here, from
  `_edi_get_installments`, and no longer by `l10n_br_account_nfe`. The rule that
  spreads the net amount payable over the installments by their weight is the
  one proposed in OCA/l10n-brazil\#5203 for the 18.0 series.
- `account.journal.create_document_from_attachment` of a Brazilian company
  opens the imported fiscal document, not the old import wizard. Customizations
  that depended on the wizard opened by the upload must be adapted.
- The installments and the payment of an issued NF-e are written in the tags
  `dup` and `detPag` when the invoice is posted. Until then the tags are empty
  and the invoice and the fiscal document show a preview.
