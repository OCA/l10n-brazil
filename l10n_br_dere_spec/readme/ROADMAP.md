- Quando a raiz oficial do XSD for distinta por evento, o sufixo
  `d1001` no `_name` deixa de ser necessário.
- `regTribSecund` e `ds:Signature` entram no mixin gerado só quando o
  `xsdata-odoo` os emitir. Até lá o XML segue montado em
  `l10n_br_dere`.
- `dere.12.detbc` e `dere.12.totaltributos` continuam achatados em
  `flattened.py`. O generate 1.2.2 separa os grupos repetidos do
  D-9199.
- Incluir mixins de eventos transacionais (D-32xx / D-22xx) depois que
  o CGIBS estabilizar esses leiautes e o manual do usuário.
