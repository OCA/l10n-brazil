# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models, _
from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
    SpedCalculoImposto
)


class SaleOrder(SpedCalculoImposto, models.Model):
    _inherit = 'sale.order'

    brazil_line_ids = fields.One2many(
        comodel_name='sale.order.line.brazil',
        inverse_name='order_id',
        string='Linhas',
    )

    @api.multi
    def _prepare_invoice(self):
        vals = super(SaleOrder, self)._prepare_invoice()

        vals['sped_empresa_id'] = self.sped_empresa_id.id or False
        vals['sped_participante_id'] = self.sped_participante_id.id or False
        vals['sped_operacao_produto_id'] = \
            self.sped_operacao_produto_id.id or False
        vals['sped_operacao_servico_id'] = \
            self.sped_operacao_servico_id.id or False
        vals['condicao_pagamento_id'] = \
            self.condicao_pagamento_id.id or False
        vals['date_invoice'] = fields.Date.context_today(self)

        return vals

    def _get_date(self):
        """ Return the document date Used in _amount_all_wrapper """
        return self.date_order

    @api.one
    @api.depends('order_line.price_total')
    def _amount_all(self):
        if not self.is_brazilian:
            return super(SaleOrder, self)._amount_all()
        return self._amount_all_brazil()

    # TODO: O campo empresa não é obrigatório
