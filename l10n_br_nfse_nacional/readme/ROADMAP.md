Implemented:

- DPS document and field mapping (`SpecModel` over `nfse.10.tcdps`/`tcinfdps`),
  with `prest`/`toma`/`serv`/`valores` mapped by comodel (res.company /
  res.partner / document.line) and regime-aware `regTrib` (MEI / Simples
  Nacional / normal). Filtered by `document_type_id.code == "SE"`.
- REST/mTLS transport client (`transport/adn_rest.py`): `verify=True`, GET-only
  retry, gzip+base64 packing, no payload/key logging.
- Issuance following the NF-e pattern: `_serialize` (`_build_binding` → `Dps`),
  `_document_export` (build → save event → sign → XSD validate),
  `_eletronic_document_send` → `_adn_send_for_authorization` (`POST /nfse` over
  mTLS, A1 derived in memory to a 0600 temp PEM, explicit UTF-8 declaration) and
  `_adn_process_response` (authorized → store key/number/protocol + NFS-e XML +
  `set_done` + `SITUACAO_EDOC_AUTORIZADA`; rejected → readable reason on the
  chatter/event + `SITUACAO_EDOC_REJEITADA`).
- Cancellation event `e101101`: `_document_cancel` → `_adn_cancel` (build
  `PedRegEvento` → sign → `POST /nfse/{chave}/eventos`), with the cancel reason
  code (cMotivo) collected by the extended cancel wizard. Number invalidation is
  hidden for NFS-e (SE) documents (no national service for it).

Not yet implemented (next iteration):

- Lost-response reconciliation (`GET /nfse/{chave}` / `GET /dps/{id}` before any
  re-`POST`) and the DANFSe rendering (`make_pdf` via `nfelib.to_pdf`).
- Substitution events (e105xxx) and the remaining event types.

Out of scope here: IBS/CBS (RTC), inbound distribution, contingency,
async / queue_job — see the project specs. Number inutilização against a service
does not exist for the national NFS-e (free DPS numbering).
