- Regenerar os modelos abstratos da Onda 1 com `xsdata-odoo` só depois
  que as raízes oficiais do XSD forem namespaced por evento. Um
  generate cru hoje cria quatro modelos chamados `dere.12.dere`,
  ignora o `regTribSecund` anônimo e trata `Signature` como
  obrigatório. O `xmldsig-core-schema.xsd` já está ao lado dos
  schemas de evento (`XSDATA_SCHEMA=dere`, `XSDATA_VERSION=12`,
  `xsdata generate schemas/v1_2_0 --output=odoo`).
- Os abstracts de retorno em `evt_retorno.py` foram curados à mão
  (D-9001, D-9101, D-9106, D-9199). Mantenha-os até o mesmo generate
  namespaced poder substituir os mixins de saída.
- Incluir mixins de eventos transacionais (D-32xx / D-22xx) depois que
  o CGIBS estabilizar esses leiautes e o manual do usuário.
