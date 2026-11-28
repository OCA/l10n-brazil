# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "EDI Mock (SEFAZ Virtual para emissao)",
    "summary": "Simula a autorizacao de NF-e, NFC-e, CT-e e MDF-e sem "
    "comunicacao com a SEFAZ, para demonstracao e desenvolvimento.",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_nfe", "l10n_br_cte", "l10n_br_mdfe"],
    "data": ["views/res_company_view.xml", "views/document_view.xml"],
    "development_status": "Alpha",
    "installable": True,
}
