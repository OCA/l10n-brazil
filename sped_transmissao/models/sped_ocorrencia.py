# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class SpedOcorrencia(models.Model):
    _name = 'sped.ocorrencia'
    _inherit = []
    _description = 'Ocorrências de de registros ou lotes SPED'

    transmissao_id = fields.Many2one(
        string='Transmissão',
        comodel_name='sped.registro',
    )
    lote_id = fields.Many2one(
        string='Lote',
        comodel_name='sped.transmissao.lote',
    )

    tipo = fields.Char(
        string='Tipo',
    )
    local = fields.Char(
        string='Local',
    )
    codigo = fields.Char(
        string='Código',
    )
    descricao = fields.Char(
        string='Descrição',
    )
