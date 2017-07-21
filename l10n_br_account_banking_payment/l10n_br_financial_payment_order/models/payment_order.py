# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class PaymentOrder(models.Model):

    _inherit = b'payment.order'

    payment_order_type = fields.Selection(
        selection_add=[
            ('cobranca', u'Cobrança'),
        ])

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
