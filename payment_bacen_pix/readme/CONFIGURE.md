To configure the provider go to Invoicing -\> Configuration -\> Payment
Providers -\> Pix and fill in:

- **Pix Provider**: the bank that holds the account;
- **Pix Key**: the key that receives the payments, as registered with the PSP;
- **Client ID** and **Client Secret**: the credentials of the application
  created in the developer portal of the bank;
- **Application Key**: only for the Banco do Brasil, the `gw-dev-app-key` of
  the application;
- **Certificate** and **Private Key**: the client certificate in the PEM
  format, required by the PSPs that demand mutual TLS, such as the Banco Inter;
- **Expiration**: how long a charge stays payable, in seconds.

While the provider is in the *Test Mode* state, the sandbox of the PSP is used.

The payment is confirmed either by the notification of the PSP, sent to
`/payment/bacenpix/webhook` and registered with `PUT /webhook/{chave}`, or by
the scheduled action *Pix: Poll the charges waiting for a payment*, which is
disabled by default. The page holding the QR code also polls the charge while
the payer keeps it open.

Pix settles in BRL only: the provider is filtered out of the payment methods
offered to the customer for any other currency.

API reference: <https://bacen.github.io/pix-api>
