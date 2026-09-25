The customer selects *Credit Card (powered by PagBank)* on the payment page and
fills in the card number, the card holder, the expiration date and the security
code. The card is encrypted in the browser by the PagBank SDK: only the
encrypted card reaches the Odoo server, which forwards it to PagBank in an
order.

When the customer asks for the card to be saved, PagBank stores it and returns
a card id that is saved as a payment token; subsequent payments are made with
that token.

If the provider is configured with *Capture Amount Manually*, the charge is
only authorized. Use the *Capture* and *Void* buttons of the transaction to
confirm or release the amount.
