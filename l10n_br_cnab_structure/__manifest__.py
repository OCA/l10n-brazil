# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "CNAB Structure",
    "summary": """
        This module allows defining the structure for generating the CNAB file.""",
    "version": "14.0.0.0.0",
    "author": "Engenere,Odoo Community Association (OCA)",
    "maintainers": ["netosjb", "felipemotter"],
    "website": "https://engenere.one/",
    "license": "AGPL-3",
    "depends": [
        "l10n_br_account_payment_order",
        "l10n_br_coa_generic",
    ],
    "data": [
        "data/l10n_br_cnab.structure.csv",
        "data/l10n_br_cnab.batch.csv",
        "data/l10n_br_cnab.line.csv",
        "data/l10n_br_cnab.line.field.csv",
        "wizard/field_select_wizard.xml",
        "wizard/cnab_preview_wizard.xml",
        "wizard/cnab_import_wizard.xml",
        "views/cnab_structure.xml",
        "views/cnab_batch.xml",
        "views/cnab_line.xml",
        "views/cnab_line_field.xml",
        "views/account_payment_mode.xml",
        "views/l10n_br_cnab_return_log_view.xml",
        "views/journal_view.xml",
        "security/cnab_security.xml",
        "security/ir.model.access.csv",
        "views/cnab_menu.xml",
    ],
    "demo": [],
}
