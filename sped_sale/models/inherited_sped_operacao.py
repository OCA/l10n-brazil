# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class SpedOperacao(models.Model):
    _inherit = 'sped.operacao'

    enviar_pela_venda = fields.Boolean(
        string='Autorizar a partir da venda?',
    )
