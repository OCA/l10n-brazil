# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
# pylint: disable=pointless-statement
{
    "name": "CNAB Structure",
    "summary": """
        This module allows defining the structure for generating the CNAB file.
        Used to exchange information with Brazilian banks.""",
    "version": "16.0.1.3.0",
    "author": "Engenere, Escodoo, Odoo Community Association (OCA)",
    "maintainers": ["antoniospneto", "felipemotter"],
    "website": "https://github.com/OCA/l10n-brazil",
    "license": "AGPL-3",
    "depends": [
        "l10n_br_account_payment_order",
        "l10n_br_coa_generic",
    ],
    "data": [
        "wizard/field_select_wizard.xml",
        "wizard/cnab_preview_wizard.xml",
        "wizard/cnab_import_wizard.xml",
        "views/cnab_structure.xml",
        "views/cnab_batch.xml",
        "views/cnab_line.xml",
        "views/cnab_line_field.xml",
        "views/account_payment_mode.xml",
        "views/l10n_br_cnab_return_log_view.xml",
        "views/l10n_br_cnab_return_event_view.xml",
        "views/cnab_line_field_group.xml",
        "views/cnab_line_field_group_condition.xml",
        "views/journal_view.xml",
        "security/cnab_security.xml",
        "security/ir.model.access.csv",
        "views/cnab_menu.xml",
    ],
    "demo": [],
    "post_init_hook": "post_init_hook",
    "external_dependencies": {"python": ["pyyaml", "unidecode"]},
}
