# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models

STATES = [('draft', 'Rascunho'),
          ('done', 'Confirmado'),
          ('paid', 'Pago'),
          ('error', 'Erro'),
          ('cancel', 'Cancelado')]


class PaymentOrder(models.Model):

    _inherit = 'payment.order'

    def action_done(self):
        super(PaymentOrder, self).action_done()
        for line in self.line_ids:
            line.action_done()
        pass


class PaymentLine(models.Model):
    _inherit = 'payment.line'

    # order_id
    state = fields.Selection(
        selection=STATES,
        default='draft',
        string='Status'
    )
    payslip_id = fields.Many2one(
        string="Ref do Holerite",
        comodel_name="hr.payslip",
    )

    def action_done(self):
        self.state = 'done'

    # FIXME
    def action_paid(self):
        self.state = 'pid'

    # Caso de retorno
    def verify_error(self):
        pass