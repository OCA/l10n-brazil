# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class SpedTransmissaoLote(models.Model):
    _name = 'sped.transmissao.lote'
    _inherit = []
    _description = 'Lotes de transmissões de registros SPED'
    _rec_name = 'codigo'
    _order = "data_hora_transmissao DESC, situacao"

    codigo = fields.Char(
        string='Código',
        default=lambda self: self.env['ir.sequence'].next_by_code('sped.transmissao.lote'),
        readonly=True,
    )
    tipo = fields.Selection(
        string='Tipo',
        selection=[
            ('efdreinf', 'EFD-Reinf'),
            ('esocial', 'e-Social'),
        ],
    )
    ambiente = fields.Selection(
        string='Ambiente',
        selection=[
            ('1', 'Produção'),
            ('2', 'Produção Restrita'),
            ('3', 'Homologação'),
        ],
    )
    transmissao_ids = fields.Many2many(
        string='Registros',
        comodel_name='sped.transmissao',
    )
    data_hora_transmissao = fields.Datetime(
        string='Data/Hora da Transmissão',
    )
    xml_transmissao = fields.Binary(
        string='XML de Transmissão',
    )
    data_hora_retorno = fields.Datetime(
        string='Data/Hora do Retorno',
    )
    xml_retorno = fields.Binary(
        string='XML de Retorno',
    )
    situacao = fields.Selection(
        string='Situação',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ]
    )

    # Dados de retorno

