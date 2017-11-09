# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
    SpedCalculoImposto
)


class PurchaseOrder(SpedCalculoImposto, models.Model):
    _inherit = 'purchase.order'

    item_ids = fields.One2many(
        comodel_name='purchase.order.line',
        inverse_name='order_id',
        related='order_line',
    )

    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        related='operacao_produto_id',
    )

    operacao_produto_id = fields.Many2one(
        comodel_name='sped.operacao'
    )

    operacao_servico_id = fields.Many2one(
        comodel_name='sped.operacao'
    )

    @api.model
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res['operacao_id'] = self.operacao_produto_id.id
        return res

    def _get_date(self):
        """
        Return the document date
        Used in _amount_all_wrapper
        """
        return self.date_order

    @api.one
    @api.depends(
        'order_line.price_total',
        #
        # Campos Brasileiros
        #
        'order_line.vr_nf',
        'order_line.vr_fatura',
    )
    def _amount_all(self):
        if not self.is_brazilian:
            return super(PurchaseOrder, self)._amount_all()
        dados = {
            'amount_untaxed': self.vr_operacao,
            'amount_tax': self.vr_nf - self.vr_operacao,
            'amount_total': self.vr_fatura,
        }
        self.update(dados)

    @api.depends('company_id', 'partner_id')
    def _compute_is_brazilian(self):
        for documento in self:
            if not documento.company_id:
                documento.is_brazilian = True
            else:
                super(PurchaseOrder, self)._compute_is_brazilian()
