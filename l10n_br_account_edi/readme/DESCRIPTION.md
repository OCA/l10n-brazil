Connects the fiscal documents of `l10n_br_fiscal_edi` to the invoices of
`l10n_br_account`, in both senses.

**Received documents.** A fiscal document imported from a file stays a
draft document: nothing is payable yet. The button **Generate Invoice**
creates the vendor bill, and only then the payables are born. They follow
the installments declared by the document (NF-e duplicates, CT-e
collection). When the installments do not add up to the net amount payable
of the document, which already discounts the withholdings, each installment
takes its share of the total by its weight and the last one gets the
rounding residue. A document that declares no installment uses the payment
term of the invoice. Files uploaded to a Brazilian vendor bill are imported
as fiscal documents, to be reviewed before the invoice is generated.

**Issued documents.** The installments and the payment that the fiscal
document will declare in its tags (NF-e `dup` and `detPag`) are shown as a
preview on the invoice, while it is a draft, and on the fiscal document, so
they can be checked. They are written in the tags when the invoice is
posted, never before.
