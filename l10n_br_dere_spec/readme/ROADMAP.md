- Regenerate the Wave 1 abstract models with `xsdata-odoo` only after the
  official XSD roots are namespaced per event. A raw generate today creates
  four models named `dere.12.dere`, skips anonymous `regTribSecund`, and
  treats `Signature` as required. Ship `xmldsig-core-schema.xsd` next to the
  event schemas before retrying (`XSDATA_SCHEMA=dere`, `XSDATA_VERSION=12`,
  `xsdata generate schemas/v1_2_0 --output=odoo`).
- Add transactional event mixins (D-32xx / D-22xx) after CGIBS stabilizes
  those layouts and the user manual.
