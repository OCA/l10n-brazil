# Copyright (C) 2011 - TODAY  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization CRM",
    "summary": "Brazilian Localization CRM",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["renatonlima", "rvalyi", "mbcosta"],
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "16.0.5.1.0",
    "depends": ["l10n_br_base", "crm"],
    "data": ["views/crm_lead_view.xml", "views/crm_quick_create_opportunity_form.xml"],
    "installable": True,
    "auto_install": True,
    "external_dependencies": {
        "python": [
            "erpbrasil.base>=2.3.0",
        ]
    },
}
