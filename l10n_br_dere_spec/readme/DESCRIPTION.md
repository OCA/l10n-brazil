Este módulo fornece modelos abstratos Odoo mapeados a partir do pacote
XSD oficial da DeRE (Declaração de Regimes Específicos) **1.2.0**,
publicado pelo CGIBS/RFB.

Ele não gera nem transmite declarações. O módulo de implementação
`l10n_br_dere` aplica esses mixins em registros concretos e conversa
com a Receita Integra.

Os schemas oficiais em `schemas/v1_2_0/` vêm de:

https://cgibs.gov.br/declaracao-de-regimes-especificos-dere

A Onda 1 cobre D-1001, D-1011, D-1101, D-1106, D-1121, D-1198, D-1199
e os eventos oficiais de retorno D-9001, D-9101, D-9106, D-9112,
D-9198 e D-9199. Os schemas D-9121 e D-9209 vêm no pacote para
eventos posteriores reutilizá-los. Eventos transacionais (D-3201 e
outros) ficam de fora desta primeira versão porque os leiautes ainda
são preliminares.
