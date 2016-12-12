# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    bc_code = fields.Char('Codigo BC', size=5)
    ibge_code = fields.Char('Codigo IBGE', size=5)
    siscomex_code = fields.Char('Codigo Siscomex', size=4)


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    ibge_code = fields.Char('Codigo IBGE', size=2)
