# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Demonstrações contábeis completas: DFC, DMPL, DRA e DVA",
    "summary": """
        As demonstrações que a Lei 6.404/76 e os pronunciamentos do CPC exigem
        além do Balanço Patrimonial e da DRE""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "maintainers": ["mileo"],
    "development_status": "Alpha",
    "depends": [
        "l10n_br_mis_report",
    ],
    "data": [
        "data/mis_report_dfc.xml",
        "data/mis_report_dmpl.xml",
        "data/mis_report_dlpa.xml",
        "data/mis_report_instance.xml",
    ],
}
