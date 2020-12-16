# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class ContractLine(models.Model):

    _name = 'contract.line'
    _inherit = [_name, 'l10n_br_fiscal.document.line.mixin']

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.contract_id.company_id,
    )

    @api.multi
    def _prepare_invoice_line(self, invoice_id=False, invoice_values=False):
        invoice_line_vals = self._prepare_br_fiscal_dict()
        invoice_line_vals.update(
            super()._prepare_invoice_line(invoice_id, invoice_values)
        )
        invoice_line_vals['fiscal_operation_id'] =\
            self.contract_id.fiscal_operation_id.id
        invoice_line_vals['contract_line_id'] = self.id
        return invoice_line_vals
