# Copyright 2024 KMEE,Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization CRM CNPJ Search",
    "summary": """
        CNPJ search in CRM Lead""",
    "version": "16.0.5.1.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "maintainers": ["corredato", "mileo"],
    "depends": [
        "l10n_br_cnpj_search",
        "l10n_br_crm",
    ],
    "data": [
        "views/crm_lead_form.xml",
    ],
}
