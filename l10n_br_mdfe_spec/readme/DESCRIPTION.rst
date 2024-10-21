Este módulo contem a estrutura de dados do ​Manifesto Eletrônico de Documentos Fiscais (MDF-e).
Este módulo não faz nada sozinho, ele precisaria de um modulo `l10n_br_mdfe` que mapearia esses mixins
nos documentos fiscais Odoo de forma semlhante a forma como o módulo `l10n_br_nfe` faz como o módulo `l10n_br_nfe_spec`.

Este módulo inclui os leiautes persistantes dos modos de transporte do MDF-e:

* modo aéreo
* modo aquaviário
* modo ferroviário
* modo rodoviário



Geração
~~~~~~~

O código dos mixins Odoo desse módulo é 100% gerado a partir dos últimos esquemas xsd da Fazenda usando xsdata e essa extensão dele:

https://github.com/akretion/xsdata-odoo


O comando usado foi:

export XSDATA_SCHEMA=mdfe; export XSDATA_VERSION=30; export XSDATA_LANG="portuguese"

xsdata generate nfelib/mdfe/schemas/v3_0 --package nfelib.mdfe.odoo.v3_0 --output=odoo
