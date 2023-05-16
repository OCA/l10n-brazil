Este módulo contem a estrutura de dados do Conhecimento de Transporte Eletrônico (CT-e).
Este módulo não faz nada sozinho, ele precisaria de um modulo `l10n_br_cte` que mapearia esses mixins
nos documentos fiscais Odoo de forma semlhante a forma como o módulo `l10n_br_nfe` faz como o módulo `l10n_br_nfe_spec`.

Este módulo inclue os principais leiautes persistantes de CT-e:

* CT-e (Conhecimento de Transporte Eletrônico)
* CT-e OS (Conhecimento de transporte eletrônico para outros serviço
* GVT-e (Guia de Transporte de Valores Eletrônica).



Geração
~~~~~~~

O código dos mixins Odoo desse módulo é 100% gerado a partir dos últimos esquemas xsd da Fazenda usando xsdata e essa extensão dele:

https://github.com/akretion/xsdata-odoo


O Comando usado foi:

export XSDATA_SCHEMA=cte; export XSDATA_VERSION=30; export XSDATA_SKIP="^ICMS\d+|^ICMSSN+|ICMSOutraUF|ICMSUFFim"; export XSDATA_LANG="portuguese"

xsdata generate nfelib/cte/schemas/v3_0 --package nfelib.cte.odoo.v3_0 --output=odoo
