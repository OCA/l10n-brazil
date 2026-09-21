- Regenerate the Wave 1 abstract models with `xsdata-odoo` only after the
  official XSD roots are namespaced per event. A raw generate today creates
  four models named `dere.12.dere`, skips anonymous `regTribSecund`, and
  treats `Signature` as required. `xmldsig-core-schema.xsd` is already next
  to the event schemas (`XSDATA_SCHEMA=dere`, `XSDATA_VERSION=12`,
  `xsdata generate schemas/v1_2_0 --output=odoo`).
- Return abstracts in `evt_retorno.py` were curated by hand (D-9001,
  D-9101, D-9106, D-9199). Keep them until the same namespaced generate
  can replace the outbound mixins.
- Add transactional event mixins (D-32xx / D-22xx) after CGIBS stabilizes
  those layouts and the user manual.
