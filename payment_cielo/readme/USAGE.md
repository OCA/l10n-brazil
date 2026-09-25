Once the provider is enabled and published, the customer selects *Credit Card
(powered by Cielo)* on the payment page and fills in the card number, the card
holder, the expiration date and the security code. The card details are sent to
Cielo by the Odoo server and are never stored in the database.

When the customer asks for the card to be saved, Cielo returns a card token
that is saved as a payment token: subsequent payments are made with that token.

If the provider is configured with *Capture Amount Manually*, the payment is
only authorized. Use the *Capture* and *Void* buttons of the transaction to
confirm or release the amount, within the deadline of Cielo (5 days for most
brands).
