# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import TIPO_DE_FOLHA


class PaymentOrder(models.Model):

    _inherit = b'payment.order'

    payment_order_type = fields.Selection(
        selection_add=[
            ('cobranca', u'Cobrança'),
        ])

    tipo_de_folha = fields.Selection(
        selection=TIPO_DE_FOLHA,
        string=u'Tipo de folha',
        default='normal',
    )

    @api.multi
    def action_open(self):
        """
        Validacao ao confirmar ordem:
        """
        for record in self:
            if not record.line_ids:
                raise ValidationError(
                    _("Impossivel confirmar linha vazia!"))
        res = super(PaymentOrder, self).action_open()
        return res

    @api.multi
    def cancel(self):
        for line in self.line_ids:
            if line.payslip_id:
                line.write({'payslip_id': ''})
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def buscar_holerites_wizard(self):
        context = dict(self.env.context)
        context.update({
            'active_id': self.id,
        })
        form = self.env.ref(
            'l10n_br_financial_payment_order.'
            'payslip_payment_create_order_view',
            True
        )
        return {
            'view_type': 'form',
            'view_id': [form.id],
            'view_mode': 'form',
            'res_model': 'payslip.payment.order.created',
            'views': [(form.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
