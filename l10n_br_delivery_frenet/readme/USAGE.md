At the checkout the customer sees one option per published Frenet
service, with the price and the estimated delivery time returned by
Frenet for their ZIP code.

After registering the shipment at the Frenet panel and printing the
label there, type the tracking number into the delivery order. The
*Update delivery states* scheduled action of the `delivery_state` module
then follows the tracking events, and the tracking link of the picking
points to the Frenet public tracking page.

For the fiscal label glued on the package handed to Correios or the
other delivery services, print the *DANFE Simplificado - Etiqueta* of
the NF-e (see the `l10n_br_nfe` module), made for the same 100 x 150 mm
thermal label paper.
