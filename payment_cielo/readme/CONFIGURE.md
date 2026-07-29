Using this module requires an eCommerce Cielo account
(<https://www.cielo.com.br/e-commerce/api/>). The MerchantId and MerchantKey
credentials are secret and are given by Cielo when the account is opened.

To configure the provider go to Invoicing -\> Configuration -\> Payment
Providers -\> Cielo and fill in:

- **Merchant Id**: the store identifier, in the GUID format;
- **Merchant Key**: the 40 characters long authentication key;
- **Soft Descriptor**: the name shown on the credit card statement of the
  customer. Cielo truncates it to 13 characters.

While the provider is in the *Test Mode* state, the sandbox of Cielo
(`apisandbox.cieloecommerce.cielo.com.br`) is used, with the very same
credentials. Set the provider to *Enabled* to reach production.

Cielo settles in BRL only: the provider is filtered out of the payment methods
offered to the customer for any other currency.

Full manual of the API:
<https://developercielo.github.io/manual/cielo-ecommerce>
