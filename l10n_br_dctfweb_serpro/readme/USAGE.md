On a MIT assessment that is already assessed locally:

**Close at the authority.** Sends the assessment through the closing service.
With immediate transmission on, which is the default, the authority also
transmits the DCTFWeb, and the assessment lands transmitted and active in one
act. The closing protocol and the assessment id it answers are kept on the
record.

**Closing status.** The closing is asynchronous on the authority side. This
button asks whether it finished, and it is not billed.

**Transmit DCTFWeb.** Only needed when the MIT was closed without immediate
transmission. Fetch the declaration XML, sign it with the e-CNPJ certificate
and attach it in the Transmission tab: the authority requires the XML it
answered, signed and otherwise identical character by character.

**Issue DARF.** Issues the numbered collection document. Before the
declaration is transmitted it uses the in-progress service, which is what
allows paying before the DCTFWeb closes.

**Receipt and full declaration.** After transmission, both come back as
documents attached to the assessment.

Every call, billed or not, is listed in the Transmission tab with what was
sent and what came back.
