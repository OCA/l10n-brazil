# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ultrapassa_limite_credito = fields.Boolean(
        string=u'Venda ultrapassa o limite de crédito?',
        compute='_compute_ultrapassa_limite_credito',
    )

    @api.depends('sale_order_line_produto_ids.vr_nf',
                 'sale_order_line_servico_ids.vr_nf',
                 'participante_id.available_credit_limit')
    def _compute_ultrapassa_limite_credito(self):
        if self.participante_id:
            total = 0.00
            for produto in self.sale_order_line_produto_ids:
                total += produto.vr_nf
            for servico in self.sale_order_line_servico_ids:
                total += servico.vr_nf
            if total > self.participante_id.available_credit_limit:
                self.ultrapassa_limite_credito = True

