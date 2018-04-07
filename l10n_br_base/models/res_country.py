# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2018  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import division, print_function, unicode_literals


from odoo import models, fields, api
from odoo.addons.base.res.res_partner import _tz_get


class ResCountry(models.Model):
    _inherit = 'res.country'

    bc_code = fields.Char(
        string='Codigo Bacen',
        size=5
    )
    ibge_code = fields.Char(
        string='Codigo IBGE',
        size=5,
    )
    siscomex_code = fields.Char(
        string='Codigo Siscomex',
        size=4
    )
    iso_3166_alfa_2 = fields.Char(
        string='Código ISO 3166',
        size=2,
        index=True,
    )


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    ibge_code = fields.Char('Codigo IBGE', size=2)

    tz = fields.Selection(
        selection=_tz_get,
        string='Timezone',
    )

    _sql_constraints = [
        ('uf_unique', 'unique (code, country_id)',
            'A UF não pode se repetir!'),
        ('ibge_code_unique', 'unique (ibge_code, country_id)',
         'O código do IBGE não pode se repetir!'),
        ('nome_unique', 'unique (name, code, country_id)',
            'O nome não pode se repetir!'),
    ]
