# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountNatureza(models.Model):
    _name = 'account.natureza'

    name = fields.Char(
        string='Nome',
    )

    code = fields.Char(
        string='Código',
        size=8,
        unique=True,
    )
