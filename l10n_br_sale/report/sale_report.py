# -*- coding: utf-8 -*-
# Copyright (C) 2011  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class SaleReport(models.Model):
    _inherit = "sale.report"
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        'Fiscal Category',
        readonly=True)
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position',
        'Fiscal Position',
        readonly=True)

    def _select(self):
        return super(SaleReport, self)._select() + \
            ", l.fiscal_category_id as fiscal_category_id, " \
            "l.fiscal_position_id as fiscal_position_id"

    def _group_by(self):
        return super(SaleReport, self)._group_by() + \
            ", l.fiscal_category_id, l.fiscal_position_id"
