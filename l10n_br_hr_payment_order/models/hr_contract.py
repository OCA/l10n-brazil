# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    conta_bancaria_id = fields.Many2one(
        string="Conta bancaria",
        comodel_name='res.partner.bank',
        required=True,
    )
