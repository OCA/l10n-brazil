# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Fiscal Queue",
    "summary": """
        Permite o envio assicrono de documentos fiscais""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["gabrielcardoso21", "mileo"],
    "development_status": "Beta",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "queue_job",
        "l10n_br_fiscal",
    ],
    "data": [
        "views/operation_view.xml",
        "views/subsequent_operation_view.xml",
        "data/queue_job.xml",
    ],
}
