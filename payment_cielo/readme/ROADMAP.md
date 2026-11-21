- The card details transit through the Odoo server, which puts the merchant in
  the scope of the PCI-DSS SAQ D questionnaire. An implementation based on
  Cielo Checkout, where the card is entered on a page hosted by Cielo, would
  avoid it.
- Only a single installment is supported. Installments, debit cards, Pix and
  the anti-fraud analysis of Cielo are not implemented yet.
- Refunds are full only, although the API of Cielo supports partial refunds.
- Zero Auth (`/1/zeroauth`) is not used to validate a card: a payment of BRL
  1.00 is authorized and voided instead.
