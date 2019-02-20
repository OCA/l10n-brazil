# -*- coding: utf-8 -*-

from openerp import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    contract_ressarcimento_ids = fields.One2many(
        comodel_name="contract.ressarcimento",
        inverse_name="contract_id",
        string="Ressarcimento",
    )
