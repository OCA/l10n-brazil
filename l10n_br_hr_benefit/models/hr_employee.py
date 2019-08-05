# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from openerp import api, fields, models


class HrEmployee(models.Model):

    _inherit = b'hr.employee'

    @api.multi
    def _compute_beneficios(self):
        for record in self:
            record.benefit_ids = self.env['hr.contract.benefit'].search(
                [('partner_id', '=', record.address_home_id.id)]
            )

    benefit_ids = fields.Many2many(
        comodel_name='hr.contract.benefit',
        string='Benefícios ativos',
        readonly=True,
        compute='_compute_beneficios',
    )
