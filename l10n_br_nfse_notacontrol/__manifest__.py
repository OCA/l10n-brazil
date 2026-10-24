# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e Nacional via NotaControl",
    "summary": "NFS-e padrão nacional (DPS) pelo webservice municipal NotaControl",
    "version": "16.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "maintainers": ["mileo"],
    "external_dependencies": {"python": ["erpbrasil.edoc"]},
    "depends": ["l10n_br_nfse_nacional"],
    "data": ["views/res_company_view.xml"],
    "installable": True,
}
