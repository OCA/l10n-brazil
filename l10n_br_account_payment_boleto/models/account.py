# -*- coding: utf-8 -*-
# Copyright (C) 2017  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import Warning as UserError


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    discount_perc = fields.Float(
        string=u"Percentual de Desconto até a Data de Vencimento",
        digits=dp.get_precision('Account'))
    instrucao_discount_perc = fields.Text(
        u'Instrução de Desconto antes do Vencimento',
        help=u'Percentual de Desconto concedido antes da Data de Vencimento',
        default=u'CONCEDER ABATIMENTO PERCENTUAL DE '
    )

    @api.constrains('discount_perc')
    def _check_discount_perc(self):
        for record in self:
            if record.discount_perc > 100 or record.discount_perc < 0:
                raise UserError(
                    _('O percentual deve ser um valor entre 0 a 100.'))
