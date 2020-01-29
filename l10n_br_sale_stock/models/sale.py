# -*- coding: utf-8 -*-
# Copyright (C) 2013  Raphaël Valyi - Akretion                                #
# Copyright (C) 2014  Renato Lima - Akretion                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        vals = super(SaleOrder, self)._prepare_invoice()
        if self.incoterm:
            vals['incoterms_id'] = self.incoterm.id

        return vals
