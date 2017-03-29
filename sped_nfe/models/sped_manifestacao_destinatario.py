# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


import logging
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from ...sped.constante_tributaria import *

_logger = logging.getLogger(__name__)

try:
    from pysped.nfe.leiaute import *
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                               agora)
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class ManifestacaoDestinatario(models.Model):
    _description = u'Manifestação do Destinatário'
    _name = 'sped.manifestacao.destinatario'

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string=u'Empresa',
        required=True,
    )
    chave = fields.Char(
        string=u'Chave',
        size=44,
        required=True,
    )
    serie = fields.Char(
        string=u'Série',
        size=3,
        index=True,
    )
    numero = fields.Float(
        string=u'Número',
        index=True,
        digits=(18, 0),
    )
    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string=u'Documento Fiscal',
    )
    emissor = fields.Char(
        string=u'Emissor',
        size=60,
    )
    cnpj_cpf = fields.Char(
        string=u'CNPJ/CPF',
        size=18,
    )
    ie = fields.Char(
        string=u'Inscrição estadual',
        size=18,
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string=u'Fornecedor',
    )
    data_hora_emissao = fields.Datetime(
        string=u'Data de emissão',
        index=True,
        default=fields.Datetime.now,
    )
    data_emissao = fields.Date(
        string=u'Data de emissão',
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
        string=u'Data de autorização',
        index=True,
    )
    data_autorizacao = fields.Date(
        string=u'Data de autorização',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )
    data_hora_cancelamento = fields.Datetime(
        string=u'Data de cancelamento',
        index=True,
    )
    data_cancelamento = fields.Date(
        string=u'Data de cancelamento',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )
    digest_value = fields.Char(
        string=u'Digest Value',
        size=28,
    )
    justificativa = fields.Char(
        string=u'Justificativa',
        size=255,
    )
    protocolo_autorizacao = fields.Char(
        string=u'Protocolo de autorização',
        size=60,
    )
    protocolo_cancelamento = fields.Char(
        string=u'Protocolo de cancelamento',
        size=60,
    )



   #'nsu': fields.char(u'NSU', size=25, select=True),
   #'situacao_dfe': fields.selection(SITUACAO_DFE, u'Situacação DF-e', select=True),
   #'situacao_manifestacao': fields.selection(SITUACAO_MANIFESTACAO, u'Situacação DF-e', select=True),
   #'data_manifestacao': fields.datetime(u'Data da manifestação'),
   #'justificativa': fields.char(u'Justificativa', size=255),
   #'xml_autorizacao': fields.text(u'XML de autorização'),
   ##'xml_cancelamento': fields.text(u'XML de cancelamento'),
   #'documento_original_id': fields.many2one('sped.documento', u'Documento de remessa/transferência/venda original'),
