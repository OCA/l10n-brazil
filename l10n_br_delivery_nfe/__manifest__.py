# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization Delivery NFe",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["mbcosta"],
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "15.0.1.0.0",
    "development_status": "Beta",
    "depends": ["l10n_br_nfe", "l10n_br_account", "l10n_br_delivery"],
    "data": [
        # Views
        "views/nfe_document_view.xml"
    ],
    "installable": True,
    "auto_install": True,
}
