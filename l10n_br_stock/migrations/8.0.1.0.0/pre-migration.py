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


logger = logging.getLogger('OpenUpgrade.l10n_br_stock')

column_renames = {
    'stock_picking': [
        ('id_dest', None),
        ('fiscal_category_id', None),
    ],
    'stock_move': [
        ('fiscal_position', None),
        ('fiscal_category_id', None),
    ],
    # 'res_company': [
    #     ('stock_out_fiscal_category_id', None),
    #     ('stock_in_fiscal_category_id', None),
    #     ('stock_fiscal_category_id', None),
    # ],
}

xmlid_renames = [
    ('l10n_br_stock.l10n_br_view_move_picking_tree', 'l10n_br_stock_account.l10n_br_view_move_picking_tree'),
    ('l10n_br_stock.l10n_br_view_picking_form', 'l10n_br_stock_account.l10n_br_stock_move_form'),
    ('l10n_br_stock.l10n_br_view_picking_form1', 'l10n_br_stock_account.l10n_br_view_picking_form1'),
    ('l10n_br_stock.view_l10n_br_stock_company_form', 'l10n_br_stock_account.view_l10n_br_stock_company_form'),
    ('l10n_br_stock.view_l10n_br_stock_invoice_onshipping', 'l10n_br_stock_account.view_l10n_br_stock_invoice_onshipping'),
]


@openupgrade.migrate()
def migrate(cr, version):
    openupgrade.rename_columns(cr, column_renames)
    openupgrade.rename_xmlids(cr, xmlid_renames)
