# -*- coding: utf-8 -*-
# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ContractLine(models.Model):

    _inherit = 'contract.line'

    @api.multi
    def _prepare_invoice_line(self, invoice_id=False):
        invoice_line_vals = super()._prepare_invoice_line(invoice_id)
        invoice_line_vals['fiscal_operation_id'] = \
            self.env.ref('l10n_br_fiscal.fo_venda').id
        return invoice_line_vals
