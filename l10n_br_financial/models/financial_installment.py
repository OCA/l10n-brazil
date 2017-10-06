# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FinancialInstallment(models.Model):
    _inherit = 'financial.installment'

    ultrapassa_limite_credito = fields.Boolean(
        string=u'Venda ultrapassa o limite de crédito?',
        compute='_compute_ultrapassa_limite_credito',
    )

    @api.depends('amount_document',
                 'participante_id.available_credit_limit')
    def _compute_ultrapassa_limite_credito(self):
        if self.participante_id:
            if self.amount_document > \
                    self.participante_id.available_credit_limit:
                self.ultrapassa_limite_credito = True
