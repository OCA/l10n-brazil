# -*- coding: utf-8 -*-
# Copyright 2018 ABGF.gov.br Luciano Veras
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    contract_ressarcimento_provisionado_id = fields.Many2one(
        comodel_name='contract.ressarcimento',
        string=u'Ressarcimento (provisao)',
    )

    contract_ressarcimento_id = fields.Many2one(
        comodel_name='contract.ressarcimento',
        string=u'Ressarcimento',
    )
