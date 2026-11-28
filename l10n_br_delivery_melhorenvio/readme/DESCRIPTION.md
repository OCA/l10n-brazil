This module connects the delivery methods to [Melhor Envio](https://melhorenvio.com.br),
the Brazilian shipping platform that sells labels of Correios, Jadlog, Loggi and
other carriers.

- Quotation: one delivery method per Melhor Envio service, each with its own price
  and estimated delivery time on the sale order and in the shop.
- Label: the delivery buys the label (cart, checkout paid with the wallet balance,
  generation and print link). When the sale order has an authorized NF-e, its access
  key goes with the shipment; otherwise it ships with a content declaration.
- Tracking: the shipment status feeds the delivery states of the `delivery_state`
  module, and the tracking code is filled as soon as Melhor Envio gives it.
- Cancellation of the label from the delivery.

The Melhor Envio account (OAuth2 application, token and its renewal) is kept in a
single record shared by all the delivery methods of its services, and only
administrators can read its secrets.
