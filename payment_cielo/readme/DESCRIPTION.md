Payment Provider: Cielo implementation for the Odoo payment framework.

This module lets customers pay online with a credit card processed by
[Cielo](https://www.cielo.com.br/e-commerce/api/), through the Cielo
E-commerce API 3.0. It supports:

- payment in a single installment, captured immediately or manually;
- manual capture and void of an authorized payment;
- full refund of a captured payment;
- tokenization: the card is saved on the Cielo side and only the card token
  returned by Cielo is stored by Odoo.

The card details never reach the database, and every payload and every response
is redacted before being logged: a log file is not a place where a card number
may be kept, and a security code may not be stored at all.
