# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#   Hugo Borges <hugo.borges@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import _, api, fields, models
import base64
from lxml import objectify

_logger = logging.getLogger(__name__)

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
    data_hora_inclusao = fields.Datetime(
        string='Data de Inclusão',
        index=True,
        default=fields.Datetime.now,
    )
    data_hora_autorizacao = fields.Datetime(
        string='Data de autorização',
        index=True,
    )
    data_hora_cancelamento = fields.Datetime(
        string='Data de cancelamento',
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

    confirma_acao_id = fields.Many2one(
        string=u'Confirma Ação',
        comodel_name='wizard.confirma.acao',
        readonly=True,
    )

    @api.multi
    def cria_wizard_gerenciamento(self, state=''):

        dados = {
            'manifestacao_ids': [(6, 0, self.ids)],
            'state': state,
        }

        return self.env['wizard.confirma.acao'].create(dados)

    @api.multi
    def action_baixa_documento(self):

        documento = self.sped_consulta_dfe_id.baixa_documentos(manifestos=self)

        return {
            'name': _(documento[0].chave),
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('sped_nfe.sped_documento'
                                    '_ajuste_recebimento_form').id,
            'res_id': documento[0].id,
            'res_model': 'sped.documento',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


    @api.multi
    def action_salva_xml(self):

        return self.baixa_attachment(
            self.action_baixa_documento()
        )

    @api.multi
    def baixa_attachment(self, attachment=None):

        return {
            'type': 'ir.actions.report.xml',
            'report_type': 'controller',
            'report_file':
                '/web/content/ir.attachment/' + str(attachment.id) +
                '/datas/' + attachment.display_name + '?download=true',
        }

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
                raise models.ValidationError(_(
                        nfe_result['code'] + ' - ' + nfe_result['message'])
                )
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
                raise models.ValidationError(_(
                    nfe_result['code'] + ' - ' + nfe_result['message']))
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
                raise models.ValidationError(_(
                    nfe_result['code'] + ' - ' + nfe_result['message']))
                return False

        return True

    @api.multi
    def action_download_xmls(self):

        if len(self) == 1:
            if self.state == 'pendente':
                self.action_ciencia_emissao()

            return self.baixa_attachment(self.action_download_xml())

        attachments = []

        for record in self:
            attachment = record.action_download_xml()
            attachments.append(attachment)

        monta_anexo = self.env['sped.monta.anexo'].create([])

        attachment_id = monta_anexo.monta_anexo_compactado(attachments)

        return self.baixa_attachment(attachment_id)

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
                return record.env['ir.attachment'].create(
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
                raise models.ValidationError(_(
                    nfe_result['code'] + ' - ' + nfe_result['message'])
                )

    @api.multi
    def action_importa_xmls(self):
        self[0].sped_consulta_dfe_id.baixa_documentos(manifestos=self)

    @api.multi
    def action_importa_xml(self):
        result = []
        for record in self:
            record.sped_consulta_dfe_id.\
                validate_nfe_configuration(record.empresa_id)
            nfe_result = record.sped_consulta_dfe_id.\
                download_nfe(record.empresa_id, record.chave)

            if nfe_result['code'] == '138':
                nfe = objectify.fromstring(nfe_result['nfe'])
                documento = self.env['sped.documento'].new()
                documento.modelo = nfe.NFe.infNFe.ide.mod.text
                dados = documento.le_nfe(xml=nfe_result['nfe'])
                record.documento_id = dados
                return {
                    'name': _("Associar Pedido de Compras"),
                    'view_mode': 'form',
                    'view_type': 'form',
                    'view_id': self.env.ref('sped_nfe.sped_documento_ajuste_recebimento_form').id,
                    'res_id': dados.id,
                    'res_model': 'sped.documento',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},
                }
            else:
                raise models.ValidationError(_(
                    nfe_result['code'] + ' - ' + nfe_result['message'])
                )
