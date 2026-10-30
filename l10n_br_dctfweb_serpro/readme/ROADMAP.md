- The whole flow was written against the published service contract and is
  covered by tests with a mocked transport. It still has to be run against the
  trial environment end to end before anyone points it at production.
- Signing the declaration XML is not implemented: the module accepts an XML
  signed elsewhere. Closing the MIT with immediate transmission is the path
  that does not need it, and is the default for that reason.
- The attorney token is stored and sent, but the Authenticate Attorney service
  that issues it is not called yet: for now the token is filled in by hand.
- The billed calls are counted per assessment, but there is no consumption
  report per company and per period yet, which is what an accounting firm
  needs to bill its clients back.
- Only the general monthly category is built by the base module. The other
  categories exist on the field because the DARF and receipt services accept
  them, but nothing assesses them here.
