# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 KMEE INFORMATICA LTDA - Luis Felipe Miléo
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from openerp.openupgrade import openupgrade


logger = logging.getLogger('OpenUpgrade.l10n_br_account_product')


#   account.fiscal.position.tax.template object
# - replace ncm_id to fiscal_classification_id in account.fiscal.position.tax
# - Drop table l10n_br_tax_definition_template
# - Drop table l10n_br_tax_definition

column_renames = {
    'l10n_br_tax_definition_sale_template': [
        ('tax_id', 'tax_template_id'),
        ('tax_code_id', 'tax_code_template_id'),
    ],
    'l10n_br_tax_definition_purchase_template': [
        ('tax_id', 'tax_template_id'),
        ('tax_code_id', 'tax_code_template_id'),
    ],
    'product_template': [
        ('ncm_id', 'fiscal_classification_id'),
    ],
}


@openupgrade.migrate()
def migrate(cr, version):
    openupgrade.rename_columns(cr, column_renames)

    cr.execute(
    "delete from ir_ui_view v "
    "using ir_model_data d where "
    "v.id=d.res_id and d.model='ir.ui.view' and "
    "d.name='l10n_br_account_product_fiscal_classification_template_form'")
