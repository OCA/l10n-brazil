# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ultrapassa_limite_credito = fields.Boolean(
        string='Venda ultrapassa o limite de crédito?',
        compute='_compute_ultrapassa_limite_credito',
    )

    @api.depends('vr_nf')
    def _compute_ultrapassa_limite_credito(self):
        for sale in self:
            if sale.participante_id.limite_credito:
                sale.ultrapassa_limite_credito = sale.vr_nf > \
                    sale.participante_id.limite_credito_disponivel
            else:
                sale.ultrapassa_limite_credito = False
