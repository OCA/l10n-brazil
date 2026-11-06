Payment Provider: PagSeguro (PagBank) implementation for the Odoo payment
framework.

This module lets customers pay online with a credit card processed by
[PagBank](https://developer.pagbank.com.br/), through the Orders API. It
supports:

- payment in a single installment, captured immediately or manually;
- manual capture and cancellation of an authorized charge;
- full refund of a captured charge;
- tokenization: the card is saved on the PagBank side and only the card id
  returned by PagBank is stored by Odoo.

The card is encrypted in the browser, so the card number never reaches the Odoo
server, and every payload and every response is redacted before being logged:
the encrypted card is a payment credential, and the log has no need for the
holder nor for the personal data of the payer.
