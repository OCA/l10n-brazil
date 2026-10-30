Payment Provider: Pix, through the API standardized by the Brazilian Central
Bank.

The customer pays with a QR code (or with the copy and paste payload) generated
as an immediate charge (`cob`) on the account of the merchant. The API of the
charges is the same for every PSP: the bank is chosen in the configuration of
the provider, which only changes the base URL, the way the OAuth token is
obtained and whether a client certificate is required.

Supported PSPs: Banco do Brasil and Banco Inter.
