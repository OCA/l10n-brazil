# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _
from openerp.exceptions import Warning


class HrAgenteCausador(models.Model):
    _name = 'hr.agente.causador'

    acidente_trabalho_id = fields.Many2one(
        comodel_name='hr.comunicacao.acidente.trabalho',
    )
    cod_agente_causador_id = fields.Many2one(
        string=u'Agente Causador Acidente',
        comodel_name='sped.agente_causador',
    )
    cod_agente_causador_doenca_id = fields.Many2one(
        string=u'Agente Causador Doença',
        comodel_name='sped.situacao_geradora_doenca',
    )
