# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    name = fields.Char(
        required = 'False',
    )

    def _verifica_valores_debito_credito(self, debito, credito):
        if not debito and not credito:
            raise Warning(
                'Não é possível criar lançamentos com debito/crédito zerado!'
            )

        return True

    @api.model
    def create(self, vals):
        self._verifica_valores_debito_credito(
            vals.get('debit', 0), vals.get('credit', 0))

        return super(AccountMoveLine, self).create(vals)

    @api.multi
    def write(self, vals, check=False):
        res = super(AccountMoveLine, self).write(vals)
        self._verifica_valores_debito_credito(self.debit, self.credit)

        return res

    @api.onchange('account_id')
    def compute_name(self):
        """

        :return:
        """
        for record in self:
            if record.account_id:
                record.name = record.account_id.display_name
