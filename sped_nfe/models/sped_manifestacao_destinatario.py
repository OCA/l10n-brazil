# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from pysped.nfe.leiaute import *
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                               agora)
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedManifestacaoDestinatario(models.Model):
    _name = b'sped.manifestacao.destinatario'
    _description = 'Manifestação do Destinatário'

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        required=True,
    )
    chave = fields.Char(
        string='Chave',
        size=44,
        required=True,
    )
    serie = fields.Char(
        string='Série',
        size=3,
        index=True,
    )
    numero = fields.Float(
        string='Número',
        index=True,
        digits=(18, 0),
    )
    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento Fiscal',
    )
    emissor = fields.Char(
        string='Emissor',
        size=60,
    )
    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18,
    )
    ie = fields.Char(
        string='Inscrição estadual',
        size=18,
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Fornecedor',
    )
    data_hora_emissao = fields.Datetime(
        string='Data de emissão',
        index=True,
        default=fields.Datetime.now,
    )
    data_emissao = fields.Date(
        string='Data de emissão',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )
    hora_emissao = fields.Char(
        'Hora de emissão',
        size=8,
        compute='_compute_data_hora_separadas',
        store=True,
    )
    data_hora_autorizacao = fields.Datetime(
        string='Data de autorização',
        index=True,
    )
    data_autorizacao = fields.Date(
        string='Data de autorização',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )
    data_hora_cancelamento = fields.Datetime(
        string='Data de cancelamento',
        index=True,
    )
    data_cancelamento = fields.Date(
        string='Data de cancelamento',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )
    digest_value = fields.Char(
        string='Digest Value',
        size=28,
    )
    justificativa = fields.Char(
        string='Justificativa',
        size=255,
    )
    protocolo_autorizacao = fields.Char(
        string='Protocolo de autorização',
        size=60,
    )
    protocolo_cancelamento = fields.Char(
        string='Protocolo de cancelamento',
        size=60,
    )

    # 'nsu': fields.char(
    # u'NSU', size=25, select=True),
    # 'situacao_dfe': fields.selection(
    #   SITUACAO_DFE, u'Situacação DF-e', select=True),
    # 'situacao_manifestacao': fields.selection(
    #   SITUACAO_MANIFESTACAO, u'Situacação DF-e', select=True),
    # 'data_manifestacao': fields.datetime(
    #   u'Data da manifestação'),
    # 'justificativa': fields.char(
    #   u'Justificativa', size=255),
    # 'xml_autorizacao': fields.text(
    #   u'XML de autorização'),
    # 'xml_cancelamento': fields.text(
    #   u'XML de cancelamento'),
    # 'documento_original_id': fields.many2one(
    #   'sped.documento',
    #   u'Documento de remessa/transferência/venda original'),
