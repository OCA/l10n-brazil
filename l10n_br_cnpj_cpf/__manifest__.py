# Copyright 2022 ATSTi Soluções
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization CNPJF/CPF Consulta",
    "summary": """
        Busca do Cadastro pelo CNPJ/CPF.
        Para UF São Paulo funciona normal,
        alguns UFs não possuem a busca.""",
    "version": "14.0.2.0.2",
    "license": "AGPL-3",
    "author": "ATSTi,Odoo Community Association (OCA)",
    "maintainers": ["carlos"],
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_base"],
    "data": [
        "views/res_partner_view.xml",
    ],
    "demo": [
    ],
}
