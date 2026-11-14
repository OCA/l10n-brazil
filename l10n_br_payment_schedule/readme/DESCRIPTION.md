Brazilian instruments in the payment schedule of `account_payment_schedule`
(OCA/bank-payment). Each payable item gets the instrument its payment mode
needs, checked before it goes into a payment order:

- **Boleto** and **guia**: the barcode or the digitable line, with the check
  digits verified (modulo 10 and 11 of the boleto, modulo 10 or 11 of the guia
  by its value identifier). The item shows whether it is a boleto or a guia and
  its digitable line.
- **Pix**: a Pix key of the partner, or a transactional bank account. A Pix copy
  and paste code given by the supplier is read and its receiver checked: a CNPJ
  or CPF key must be the document of the partner, otherwise the item stays out
  of the payment orders; other key types and dynamic QR codes are marked to be
  checked at the bank.
- **TED** and **DOC**: a bank account of the partner.

The instrument goes to the payment line when the item enters a payment order.
The *Read Boleto or Pix* button of each item reads a code, warns when its amount
differs from the open amount and, for Pix, registers the key on the partner
when the user asks for it: keys are never created automatically.

Codes are checked by the [brbank](https://pypi.org/project/brbank/) library,
without network access.
