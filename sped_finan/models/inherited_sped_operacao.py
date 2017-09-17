# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class SpedOperacao(models.Model):
    _inherit = 'sped.operacao'

    finan_documento_id = fields.Many2one(
        comodel_name='finan.documento',
        string='Tipo de documento',
        ondelete='restrict',
    )
    finan_conta_id = fields.Many2one(
        comodel_name='finan.conta',
        string='Conta financeira',
        ondelete='restrict',
        domain=[('tipo', '=', 'A')],
    )
