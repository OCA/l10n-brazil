# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import fields, models, api


class SaleConfigSettings(models.TransientModel):
    _inherit = 'sale.config.settings'

    dias_vencimento_cotacao = fields.Float(
        string="Dias de vencimento das cotações",
        default=0.0
    )

    @api.multi
    def set_dias_vencimento_cotacao_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'sale.config.settings',
            'dias_vencimento_cotacao',
            self.dias_vencimento_cotacao
        )
