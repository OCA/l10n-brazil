# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import fields, models


class SpedNCM(models.Model):
    _name = b'sped.ncm'
    _inherit = 'sped.ncm'

    ibptax_ids = fields.One2many(
        comodel_name='sped.ibptax.ncm',
        inverse_name='ncm_id',
        string='Alíquotas IBPT',
    )


class SpedServico(models.Model):
    _name = b'sped.servico'
    _inherit = 'sped.servico'

    ibptax_ids = fields.One2many(
        comodel_name='sped.ibptax.servico',
        inverse_name='servico_id',
        string='Alíquotas IBPT'
    )


class SpedNBS(models.Model):
    _name = b'sped.nbs'
    _inherit = 'sped.nbs'

    ibptax_ids = fields.One2many(
        comodel_name='sped.ibptax.nbs',
        inverse_name='nbs_id',
        string='Alíquotas IBPT'
    )
