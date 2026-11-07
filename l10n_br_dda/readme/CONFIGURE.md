1. In *Invoicing > Configuration > Settings*, block DDA, choose by company:
   - *DDA automatic link* (off by default).
   - *DDA bill creation*: whether a boleto without title recommends a draft
     vendor bill (off by default).
   - The tolerance of days (default 3) and of amount (default zero).
   - The payment mode (CNAB, outbound) of the order that receives the boletos and
     the accounts of the interest, fine and discount.
2. Give the users one of the groups *DDA / User*, *DDA / Approver* (releases a
   suspect boleto) or *DDA / Manager* (policies and technical data).
3. A vendor can list *DDA assignees* in the *Invoicing* tab: companies that issue
   boletos in its name.
4. To read a DDA return file, register the layout of the bank as a structure of
   *CNAB Structure* and tick *DDA return*. Each field of the detail maps a boleto
   field in *Content Destination Field*: `digitable_line`, `beneficiary_vat`,
   `beneficiary_name`, `payer_cnpj`, `date_due` (DDMMYYYY), `amount`,
   `document_number`, `guarantor_vat`, `guarantor_name` and `status_code`
   (1 open, 2 paid, 3 cancelled).
