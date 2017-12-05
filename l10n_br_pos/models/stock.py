# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _get_fiscal_document_access_keys_fields(self):
        su = super(StockPicking, self)
        return su._get_fiscal_document_access_keys_fields() + [
            'pos_order_ids.chave_cfe'
        ]
