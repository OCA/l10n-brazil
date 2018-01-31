# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    payment_mode_id = fields.Many2one(
        string="Forma de Pagamento padrão do holerite",
        comodel_name='payment.mode',
        domain="[('tipo_pagamento', '=', 'folha')]"
    )