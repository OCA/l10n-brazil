# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import fields, models


class NCM(models.Model):
    _name = 'sped.ncm'
    _inherit = 'sped.ncm'

    ibptax_ids = fields.One2many(
        comodel_name='sped.ibptax.ncm',
        inverse_name='ncm_id',
        string=u'Alíquotas IBPT',
    )


class Servico(models.Model):
    _name = 'sped.servico'
    _inherit = 'sped.servico'

    ibptax_ids = fields.One2many(
        comodel_name='sped.ibptax.servico',
        inverse_name='servico_id',
        string=u'Alíquotas IBPT'
    )


class NBS(models.Model):
    _name = 'sped.nbs'
    _inherit = 'sped.nbs'

    ibptax_ids = fields.One2many(
        comodel_name='sped.ibptax.nbs',
        inverse_name='nbs_id',
        string=u'Alíquotas IBPT'
    )
