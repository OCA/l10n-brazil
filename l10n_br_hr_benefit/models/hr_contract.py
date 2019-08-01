# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from openerp import fields, models


class HrContract(models.Model):

    _inherit = b'hr.contract'

    benefit_ids = fields.One2many(
        comodel_name='hr.contract.benefit',
        inverse_name='contract_id',
        string='Benefícios',
    )
