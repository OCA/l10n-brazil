Modelos abstratos (mixins) da GNRE (Guia Nacional de Recolhimento de Tributos
Estaduais), gerados por [xsdata-odoo](https://github.com/akretion/xsdata-odoo) a
partir dos XSD oficiais.

Os schemas vêm do pacote do Manual de Integração do Contribuinte v2.15,
distribuído pelo portal GNRE. Como em `l10n_br_nfe_spec`, `l10n_br_cte_spec` e
`l10n_br_mdfe_spec`, só entram aqui os mixins do que será persistido no Odoo: o
lote de envio (`lote_gnre_v2.00.xsd`, com a guia `TDadosGNRE`) e os tipos que
ele referencia (`dados_gnre_v1.00.xsd`, `dados_gnre_v2.00.xsd`,
`tiposBasicoGNRE_v1.00.xsd` e `tiposBasicoGNRE_v2.00.xsd`).

As mensagens do webservice (cabeçalho, recibo, resultado do lote, consultas,
retorno e configuração por UF) ficam de fora: elas são lidas e escritas pelos
bindings da nfelib e não viram registro no Odoo. Ao regerar, o xsdata-odoo
produz os mixins de todos os XSD do pacote, e só os arquivos acima são
versionados.

Este módulo é 100% gerado e não tem regra de negócio. A implementação fica no
módulo `l10n_br_gnre`.
