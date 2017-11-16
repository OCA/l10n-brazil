# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import _, api, fields, models
from odoo.osv import orm
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

    nsu = fields.Char(
        string=u'NSU',
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

    situacao_nfe= fields.Selection(
        string=u'Situacação NF-e',
        selection=SITUACAO_NFE,
        select=True,
        readonly=True,
    )

    situacao_manifestacao = fields.Selection(
        string=u'Situacação da Manifestação',
        selection=SITUACAO_MANIFESTACAO,
        select=True,
        readonly=True,
    )

    @api.multi
    def action_known_emission(self):
        for record in self:
            self.validate_nfe_configuration(record.company_id)
            nfe_result = self.send_event(
                record.company_id, record.chNFe, 'ciencia_operacao')
            env_events = record.env['l10n_br_account.document_event']
            event = record._create_event('Ciência da operação', nfe_result)
            if nfe_result['code'] == '135':
                record.state = 'ciente'
            elif nfe_result['code'] == '573':
                record.state = 'ciente'
                event['response'] = \
                    'Ciência da operação já previamente realizada'
            else:
                event['response'] = 'Ciência da operação sem êxito'
            event = env_events.create(event)
            record._create_attachment(event, nfe_result)
        return True

    @api.multi
    def action_confirm_operation(self):
        for record in self:
            self.validate_nfe_configuration(record.company_id)
            nfe_result = self.send_event(
                record.company_id,
                record.chNFe,
                'confirma_operacao')
            env_events = record.env['l10n_br_account.document_event']
            event = record._create_event('Confirmação da operação', nfe_result)
            if nfe_result['code'] == '135':
                record.state = 'confirmado'
            else:
                event['response'] = 'Confirmação da operação sem êxito'
            event = env_events.create(event)
            record._create_attachment(event, nfe_result)
        return True

    @api.multi
    def action_unknown_operation(self):
        for record in self:
            self.validate_nfe_configuration(record.company_id)
            nfe_result = self.send_event(
                record.company_id,
                record.chNFe,
                'desconhece_operacao')
            env_events = record.env['l10n_br_account.document_event']
            event = record._create_event(
                'Desconhecimento da operação', nfe_result)
            if nfe_result['code'] == '135':
                record.state = 'desconhecido'
            else:
                event['response'] = 'Desconhecimento da operação sem êxito'
            event = env_events.create(event)
            record._create_attachment(event, nfe_result)
        return True

    @api.multi
    def action_not_operation(self):
        for record in self:
            self.validate_nfe_configuration(record.empresa_id)
            nfe_result = self.send_event(
                record.company_id,
                record.chNFe,
                'nao_realizar_operacao')
            env_events = record.env['l10n_br_account.document_event']
            event = record._create_event('Operação não realizada', nfe_result)
            if nfe_result['code'] == '135':
                record.state = 'nap_realizado'
            else:
                event['response'] = \
                    'Tentativa de Operação não realizada sem êxito'
            event = env_events.create(event)
            record._create_attachment(event, nfe_result)
        return True

    @api.multi
    def action_download_xml(self):
        result = True
        for record in self:
            self.validate_nfe_configuration(record.company_id)
            nfe_result = self.download_nfe(record.company_id, record.chNFe)
            env_events = record.env['l10n_br_account.document_event']
            if nfe_result['code'] == '138':
                event = record._create_event(
                    'Download NFe concluido', nfe_result, type_event='10')
                env_events.create(event)
                file_name = 'NFe%s.xml' % record.chNFe
                record.env['ir.attachment'].create(
                    {
                        'name': file_name,
                        'datas': base64.b64encode(nfe_result['nfe']),
                        'datas_fname': file_name,
                        'description':
                            u'XML NFe - Download manifesto do destinatário',
                        'res_model': 'nfe.mde',
                        'res_id': record.id
                    })
            else:
                result = False
                event = record._create_event(
                    'Download NFe não efetuado', nfe_result, type_event='10')
                event = env_events.create(event)
                record._create_attachment(event, nfe_result)
        return result

    def validate_nfe_configuration(company):
        error = u'As seguintes configurações estão faltando:\n'
        if not company.nfe_version:
            error += u'Empresa - Versão NF-e\n'
        if not company.nfe_a1_file:
            error += u'Empresa - Arquivo NF-e A1\n'
        if not company.nfe_a1_password:
            error += u'Empresa - Senha NF-e A1\n'
        if error != u'As seguintes configurações estão faltando:\n':
            raise orm.except_orm(_(u'Validação !'), _(error))


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
