Using this module requires a PagBank account
(<https://pagseguro.uol.com.br/>). The API token is generated in the PagBank
account, under Vendas Online > Integrações > Token.

To configure the provider go to Invoicing -\> Configuration -\> Payment
Providers -\> PagSeguro and fill in:

- **API Token**: the token of the account;
- **Soft Descriptor**: the name shown on the credit card statement of the
  customer. PagBank truncates it to 17 characters.

While the provider is in the *Test Mode* state, the sandbox
(`sandbox.api.pagseguro.com`) is used, which requires a token of the sandbox
account. Set the provider to *Enabled* to reach production.

PagBank settles in BRL only: the provider is filtered out of the payment
methods offered to the customer for any other currency.

API reference: <https://developer.pagbank.com.br/reference/criar-pedido>
