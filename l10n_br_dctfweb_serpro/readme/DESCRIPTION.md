This module transmits the MIT and the DCTFWeb through the Integra Contador,
the API platform the Serpro runs for the tax authority.

It plugs on top of `l10n_br_dctfweb`, which assesses the debits and builds the
declaration. Splitting the two is deliberate: a company that only wants the
JSON file to import in the e-CAC installs the base module alone and never
carries a transmission stack, a certificate requirement or a billing account
it does not use.

What it does:

- authenticates with the e-CNPJ certificate over mTLS plus OAuth2, and
  supports an accounting firm filing for its clients through the attorney
  token and the electronic power of attorney;
- closes the MIT assessment at the authority, optionally asking for the
  DCTFWeb to be transmitted in the same act, which is what spares signing the
  declaration XML;
- follows the asynchronous closing, and reads back the assessment, the
  receipt, the full declaration and the declaration XML;
- issues the numbered DARF, including for a declaration still in progress;
- warns before every billed request, because the platform charges per call,
  and keeps every call in an audit log: which service, what was sent, what
  came back, which receipt.

Credentials are never written to the log, and neither is the certificate, the
token or the CNPJ of a taxpayer. What the log carries is the service and the
record, which is what a support ticket actually needs.
