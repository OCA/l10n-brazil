# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Relatórios contábeis brasileiros: DRA e DVA",
    "summary": """
        Demonstração do Resultado Abrangente e Demonstração do Valor
        Adicionado""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "maintainers": ["mileo"],
    "development_status": "Alpha",
    "depends": [
        "l10n_br_mis_report",
    ],
    "data": [
        "data/mis_report_dra.xml",
        "data/mis_report_dva.xml",
        "data/mis_report_instance.xml",
    ],
}
