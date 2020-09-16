# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, _


class CNABReturnMoveCode(models.Model):
    """
        CNAB return code, each Bank can has a list of Codes
    """
    _name = 'cnab.return.move.code'
    _description = 'CNAB Return Move Code'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    bank_id = fields.Many2one(
        string='Bank', comodel_name='res.bank'
    )
    payment_method_id = fields.Many2one(
        'account.payment.method', string='Payment Method'
    )
    # Fields used to create domain
    bank_code_bc = fields.Char(
        related='bank_id.code_bc',
    )
    payment_method_code = fields.Char(related='payment_method_id.code')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((
                record.id,  '%s - %s' % (
                    record.code, record.name)
            ))
        return result
