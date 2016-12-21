# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class NCM(models.Model):
    _name = 'sped.ncm'
    _inherit = 'sped.ncm'

    ibptax_ids = fields.One2many('sped.ibptax.ncm', 'ncm_id', 'Alíquotas IBPT')


class Servico(models.Model):
    _name = 'sped.servico'
    _inherit = 'sped.servico'

    ibptax_ids = fields.One2many('sped.ibptax.servico', 'servico_id', 'Alíquotas IBPT')


class NBS(models.Model):
    _name = 'sped.nbs'
    _inherit = 'sped.nbs'

    ibptax_ids = fields.One2many('sped.ibptax.nbs', 'nbs_id', 'Alíquotas IBPT')
