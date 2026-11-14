Some cities adopted the national NFS-e layout (DPS 1.01) but receive the DPS
through the NotaControl/ISSNet municipal webservice instead of the national
data environment (ADN). Goiânia (GO) is the first one configured.

The payload is the one built by `l10n_br_nfse_nacional`; what changes is the
transport:

- SOAP 1.1 Document/Literal with `nfseCabecMsg` and `nfseDadosMsg`;
- the DPS goes inside a `LoteDps` (`RecepcionarLoteDpsSincrono`), and the
  batch is signed too: two signatures, the `infDPS` one and the batch one;
- the WSDL is only reachable with mutual TLS.

The module keeps the DPS serialization of `l10n_br_nfse_nacional` and only
replaces sending, response handling and cancellation, delegating the protocol
to the `NotaControl` provider of `erpbrasil.edoc`.

For NotaControl companies the DPS is also adjusted to what the Goiânia
webservice accepts: version 1.01, empty groups removed, `tpRetPisCofins` in the
1.01 domain, the 9-digit municipal taxation code (`cTribMun`) right after
`cTribNac`, the competence date in local time and a default IBSCBS group when
the line does not export one.
