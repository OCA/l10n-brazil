# -*- coding: utf-8 -*-
# @ 2016 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp.openupgrade import openupgrade


column_renames = {
    'l10n_br_tax_definition_sale_template': [
        ('tax_id', 'tax_template_id'),
        ('tax_code_id', 'tax_code_template_id')
        ],
    'l10n_br_tax_definition_purchase_template': [
        ('tax_id', 'tax_template_id'),
        ('tax_code_id', 'tax_code_template_id')
        ],
    'account_fiscal_position_tax_template': [
        ('ncm_id', 'fiscal_classification_id')
        ],
    }


@openupgrade.migrate()
def migrate(cr, version):
    openupgrade.rename_columns(
        cr, column_renames)
    cr.execute(
        "DROP TABLE l10n_br_tax_definition_template")
    cr.execute(
        "DROP TABLE l10n_br_tax_definition")
