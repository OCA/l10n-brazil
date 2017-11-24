# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import _, api, fields, models
import base64


_logger = logging.getLogger(__name__)

try:
    from pysped.nfe.leiaute import *
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                               agora)
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)

SITUACAO_NFE = [
    ('1', 'Autorizada'),
    ('2', 'Cancelada'),
    ('3', 'Denegada'),
]

SITUACAO_MANIFESTACAO = [
         ('pendente', 'Pendente'),
         ('ciente', 'Ciente da operação'),
         ('confirmado', 'Confirmada operação'),
         ('desconhecido', 'Desconhecimento'),
         ('nao_realizado', 'Não realizado'),
]


class SpedManifestacaoDestinatario(models.Model):
    _name = b'sped.manifestacao.destinatario'
    _description = 'Manifestação do Destinatário'

    @api.multi
    def name_get(self):
        return [(rec.id,
                 u"NFº: {0} ({1}): {2}".format(
                     rec.numero, rec.cnpj_cpf, rec.empresa_id.razao_social)
                 ) for rec in self]

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Razão Social',
        required=True,
    )
    chave = fields.Char(
        string='Chave de Acesso',
        size=44,
        required=True,
    )
    serie = fields.Char(
        string='Série',
        size=3,
        index=True,
    )
    numero = fields.Float(
        string='Número da NF-e',
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

    nsu = fields.Char(
        string=u'Número Sequencial',
        size=25,
        select=True,
    )

    tipo_operacao = fields.Selection(
        [('0', 'Entrada'), ('1', 'Saída')],
        string="Tipo de Operação",
        readonly=True,
    )

    valor_documento = fields.Float(
        string="Valor Total da NF-e",
        readonly=True,
        digits=(18, 2),
    )

    ie = fields.Char(
        string='Inscrição estadual',
        size=18,
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Fornecedor',
        invisible=True,
    )

    fornecedor = fields.Char(
        string='Fornecedor',
        size=60,
        index=True,
    )

    data_hora_emissao = fields.Datetime(
        string='Data de Emissão',
        index=True,
        default=fields.Datetime.now,
    )
    data_emissao = fields.Date(
        string='Data de Emissão',
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
    data_hora_inclusao = fields.Datetime(
        string='Data de Inclusão',
        index=True,
        default=fields.Datetime.now,
    )
    data_inclusao = fields.Date(
        string='Data de inclusão',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )
    hora_inclusao = fields.Char(
        'Hora de inclusão',
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
    forma_inclusao = fields.Char(
        string='Forma de Inclusão',
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

    situacao_nfe = fields.Selection(
        string=u'Situacação da NF-e',
        selection=SITUACAO_NFE,
        select=True,
        readonly=True,
    )

    state = fields.Selection(
        string=u'Situacação da Manifestação',
        selection=SITUACAO_MANIFESTACAO,
        select=True,
        readonly=True,
    )
    sped_consulta_dfe_id = fields.Many2one(
        string=u'DF-E',
        comodel_name='sped.consulta.dfe',
        readonly=True,
    )

    @api.multi
    def action_ciencia_emissao(self):
        for record in self:

            record.sped_consulta_dfe_id.validate_nfe_configuration(
                record.empresa_id)

            nfe_result = record.sped_consulta_dfe_id.send_event(
                record.empresa_id,
                record.chave,
                'ciencia_operacao'
            )
            if nfe_result['code'] == '135':
                record.state = 'ciente'
            elif nfe_result['code'] == '573':
                record.state = 'ciente'
            else:
                raise models.ValidationError(
                    nfe_result['code'] + ' - ' + nfe_result['message'])
                return False

        return True

    @api.multi
    def action_confirmar_operacacao(self):
        for record in self:
            record.sped_consulta_dfe_id.validate_nfe_configuration(
                record.empresa_id)
            nfe_result = record.sped_consulta_dfe_id.send_event(
                record.empresa_id,
                record.chave,
                'confirma_operacao')

            if nfe_result['code'] == '135':
                record.state = 'confirmado'
            else:
                raise models.ValidationError(
                    nfe_result['code'] + ' - ' + nfe_result['message'])
                return False

        return True

    @api.multi
    def action_operacao_desconhecida(self):
        for record in self:
            record.sped_consulta_dfe_id.\
                validate_nfe_configuration(record.empresa_id)
            nfe_result = record.sped_consulta_dfe_id.send_event(
                record.empresa_id,
                record.chave,
                'desconhece_operacao')

            if nfe_result['code'] == '135':
                record.state = 'desconhecido'
            else:
                raise models.ValidationError(
                    nfe_result['code'] + ' - ' + nfe_result['message'])
                return False

        return True

    @api.multi
    def action_negar_operacao(self):
        for record in self:
            record.sped_consulta_dfe_id.\
                validate_nfe_configuration(record.empresa_id)
            nfe_result = record.sped_consulta_dfe_id.send_event(
                record.empresa_id,
                record.chave,
                'nao_realizar_operacao')

            if nfe_result['code'] == '135':
                record.state = 'nap_realizado'
            else:
                raise models.ValidationError(
                    nfe_result['code'] + ' - ' + nfe_result['message'])
                return False

        return True

    @api.multi
    def action_download_xml(self):
        result = True
        for record in self:
            record.sped_consulta_dfe_id.\
                validate_nfe_configuration(record.empresa_id)
            nfe_result = record.sped_consulta_dfe_id.\
                download_nfe(record.empresa_id, record.chave)

            if nfe_result['code'] == '138':

                file_name = 'NFe%s.xml' % record.chave
                record.env['ir.attachment'].create(
                    {
                        'name': file_name,
                        'datas': base64.b64encode(nfe_result['nfe']),
                        'datas_fname': file_name,
                        'description':
                            u'XML NFe - Download manifesto do destinatário',
                        'res_model': 'sped.manifestacao.destinatario',
                        'res_id': record.id
                    })
            else:
                result = False

                raise models.ValidationError(
                    nfe_result['code'] + ' - ' + nfe_result['message'])

        return result
