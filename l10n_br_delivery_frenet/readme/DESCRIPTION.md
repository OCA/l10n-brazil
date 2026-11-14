This module quotes shipping through [Frenet](https://www.frenet.com.br),
the Brazilian shipping gateway: the checkout offers one delivery option
per service enabled in the Frenet account (Correios PAC, Sedex, Jadlog
and so on), each with its real price and estimated delivery time, so the
customer picks the best one.

It also follows the shipment: the tracking events of
`/tracking/trackinginfo` feed the delivery states of the `delivery_state`
module, whose scheduled action keeps the pickings up to date and can
notify the customer on delivery.

The public Frenet API does not register shipments nor emit transport
labels: the label is printed at the Frenet panel and the tracking number
is then typed into the picking.
