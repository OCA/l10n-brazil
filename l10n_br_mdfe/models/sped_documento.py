# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA, Grupo Zenir
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals
import tempfile
import time
import base64
from pynfe.utils import etree
import re

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_MDFE,
    TIPO_TRANSPORTADOR,
    TIPO_EMISSAO_PROPRIA,
    MODALIDADE_TRANSPORTE,
    MODALIDADE_TRANSPORTE_RODOVIARIO,
    TIPO_EMITENTE,
    TIPO_RODADO,
    TIPO_CARROCERIA,
    AMBIENTE_MDFE_PRODUCAO,
    TIPO_EMISSAO_MDFE_NORMAL,
    TIPO_EMISSAO_MDFE_CONTINGENCIA,
    SITUACAO_NFE_AUTORIZADA,
    SITUACAO_NFE_CANCELADA,
    SITUACAO_NFE_DENEGADA,
    SITUACAO_NFE_ENVIADA,
    SITUACAO_NFE_REJEITADA,
    SITUACAO_NFE_EM_DIGITACAO,
    SITUACAO_NFE_A_ENVIAR,
    SITUACAO_FISCAL_DENEGADO,
)
from odoo.exceptions import UserError

SITUACAO_MDFE_ENCERRADA = 'encerrada'


STATUS_MDFE = {
    '100':'autorizada',
    '101':'cancelada',
    '132':'encerrada',
}


class SpedDocumento(models.Model):

    _inherit = 'sped.documento'

    @api.depends('modelo', 'emissao', 'importado_xml', 'situacao_mdfe')
    def _compute_permite_alteracao(self):
        super(SpedDocumento, self)._compute_permite_alteracao()

        for documento in self:
            if not documento.modelo == MODELO_FISCAL_MDFE:
                super(SpedDocumento, documento)._compute_permite_alteracao()
                continue

            documento.permite_alteracao = True

    def _check_permite_alteracao(self, operacao='create', dados={},
                                 campos_proibidos=[]):

        CAMPOS_PERMITIDOS = [
            'message_follower_ids',
            'justificativa',
            'chave_cancelamento',
        ]
        for documento in self:
            if not documento.modelo == MODELO_FISCAL_MDFE:
                super(SpedDocumento, documento)._check_permite_alteracao(
                    operacao,
                    dados,
                )
                continue

            if documento.permite_alteracao:
                continue


    tipo_emitente = fields.Selection(
        selection=TIPO_EMITENTE,
        string='Tipo de emitente',
    )
    tipo_transportador = fields.Selection(
        selection=TIPO_TRANSPORTADOR,
        string='Tipo do transportador'
    )
    modalidade_transporte = fields.Selection(
        selection=MODALIDADE_TRANSPORTE,
        string='Modalidade',
    )
    veiculo_id = fields.Many2one(
        string='Veiculo',
        comodel_name='sped.veiculo',
    )
    veiculo_rntrc = fields.Char(
        string='RNTRC',
        size=20,
        related='veiculo_id.rntrc',
        store=True,
    )
    veiculo_placa = fields.Char(
        string='Placa',
        size=8,
        related='veiculo_id.placa',
        store=True,
    )
    veiculo_estado_id = fields.Many2one(
        comodel_name='sped.estado',
        string='Estado',
        related='veiculo_id.estado_id',
        store=True,
    )
    veiculo_ciot = fields.Char(
        string='Tipo CIOT',
        help='Também Conhecido como conta frete',
        related='veiculo_id.ciot',
        store=True,
    )
    veiculo_tipo_rodado = fields.Selection(
        selection=TIPO_RODADO,
        string='Rodado',
        related='veiculo_id.tipo_rodado',
        store=True,
    )
    veiculo_tipo_carroceria = fields.Selection(
        selection=TIPO_CARROCERIA,
        string='Tipo de carroceria',
        related='veiculo_id.tipo_carroceria',
        store=True,
    )
    veiculo_tara_kg = fields.Float(
        string='Tara (kg)',
        related = 'veiculo_id.tara_kg',
        store = True,
    )
    veiculo_capacidade_kg = fields.Float(
        string='Capacidade (kg)',
        related='veiculo_id.capacidade_kg',
        store=True,
    )
    veiculo_capacidade_m3 = fields.Float(
        string='Capacidade (m³)',
        related='veiculo_id.capacidade_m3',
        store=True,
    )
    carregamento_municipio_ids = fields.Many2many(
        comodel_name='sped.municipio',
        string='Municípios carregamento',
        help='Máximo 50',

    )
    percurso_estado_ids = fields.Many2many(
        comodel_name='sped.estado',
        string='UFs de percurso',
        help='Máximo 25',
    )
    descarregamento_estado_id = fields.Many2one(
        comodel_name='sped.estado',
        string='Estado descarregamento'
    )
    condutor_ids = fields.One2many(
        comodel_name='l10n_br.mdfe.condutor',
        inverse_name='documento_id',
    )
    lacre_ids = fields.One2many(
        comodel_name='l10n_br.mdfe.lacre',
        inverse_name='documento_id',
    )
    seguro_ids = fields.One2many(
        comodel_name='l10n_br.mdfe.seguro',
        inverse_name='documento_id',
    )
    item_mdfe_ids = fields.One2many(
        comodel_name='l10n_br.mdfe.item',
        inverse_name='mdfe_id',
        inverse='_inverse_item_mdfe_ids',
    )

    item_referenciado_ids = fields.One2many(
        comodel_name = 'l10n_br.mdfe.item',
        inverse_name = 'documento_id',
    )

    situacao_mdfe = fields.Selection(
        string=u'Situacação da NF-e',
        selection=[
            ('em_digitacao', 'Em digitação'),
            ('a_enviar', 'Aguardando envio'),
            ('enviada', 'Aguardando processamento'),
            ('rejeitada', 'Rejeitada'),
            ('autorizada', 'Autorizada'),
            ('cancelada', 'Cancelada'),
            ('denegada', 'Denegada'),
            ('inutilizada', 'Inutilizada'),
            ('encerrada', 'Encerrada'),
        ],
        select=True,
        readonly=True,)

    @api.multi
    @api.depends('item_mdfe_ids.documento_id')
    def _inverse_item_mdfe_ids(self):
        for record in self:
            if record.item_mdfe_ids.mapped('documento_id'):
                for campo in self._fields.keys():
                    if campo.startswith('vr_'):
                        record[campo] = \
                            sum(record.item_mdfe_ids.mapped(
                                'documento_id').mapped(campo))

    def _serie_padrao_mdfe(self, empresa, ambiente_mdfe, tipo_emissao_mdfe):
        serie = False
        if tipo_emissao_mdfe == TIPO_EMISSAO_MDFE_NORMAL:
            if ambiente_mdfe == AMBIENTE_MDFE_PRODUCAO:
                serie = empresa.serie_mdfe_producao
            else:
                serie = empresa.serie_mdfe_homologacao

        elif tipo_emissao_mdfe == TIPO_EMISSAO_MDFE_CONTINGENCIA:
            if ambiente_mdfe == AMBIENTE_MDFE_PRODUCAO:
                serie = empresa.serie_mdfe_contingencia_producao
            else:
                serie = empresa.serie_mdfe_contingencia_homologacao

        return serie

    @api.onchange('empresa_id', 'modelo', 'emissao')
    def _onchange_empresa_id(self):
        result = super(SpedDocumento, self)._onchange_empresa_id()

        if self.modelo == MODELO_FISCAL_MDFE:
            result['value']['ambiente_nfe'] = self.empresa_id.ambiente_nfe
            result['value']['tipo_emissao_nfe'] = self.empresa_id.tipo_emissao_nfe
            result['value']['serie'] = self._serie_padrao_mdfe(
                self.empresa_id,
                self.empresa_id.ambiente_nfe,
                self.empresa_id.tipo_emissao_nfe
            )
        return result

    @api.onchange('operacao_id', 'emissao', 'natureza_operacao_id')
    def _onchange_operacao_id(self):
        result = super(SpedDocumento, self)._onchange_operacao_id()

        if self.operacao_id.modelo == MODELO_FISCAL_MDFE:
            result['value']['tipo_emitente'] = self.operacao_id.tipo_emitente
            result['value']['tipo_transportador'] = \
                self.operacao_id.tipo_transportador
            result['value']['modalidade_transporte'] = \
                self.operacao_id.modalidade_transporte
            self.situacao_mdfe = SITUACAO_NFE_EM_DIGITACAO

        return result

    @api.onchange('empresa_id', 'modelo', 'emissao', 'serie', 'ambiente_nfe')
    def _onchange_serie(self):
        result = super(SpedDocumento, self)._onchange_serie()

        if not self.modelo == MODELO_FISCAL_MDFE:
            return result

        serie = self.serie and self.serie.strip()

        ultimo_numero = self.search([
            ('empresa_id.cnpj_cpf', '=', self.empresa_id.cnpj_cpf),
            ('ambiente_nfe', '=', self.ambiente_nfe),
            ('emissao', '=', self.emissao),
            ('modelo', '=', self.modelo),
            ('serie', '=', serie),
            ('numero', '!=', False),
        ], limit=1, order='numero desc')

        result['value']['serie'] = serie

        if not ultimo_numero:
            result['value']['numero'] = 1
        else:
            result['value']['numero'] = ultimo_numero[0].numero + 1

        return result

    def _confirma_documento(self):
        """
        TODO: Calcular informações do MDF-E:
            - Cidades/Estado do percurso;
            - Realizar validações;
            - Solicitar envio de NF-E em estado a_enviar;
            - Providenciar o envio do MDF-E caso todas as notas estejam
            autorizadas;
            - etc.

        :return:
        """

        result = super(SpedDocumento, self)._confirma_documento()
        for record in self:
            percurso_estado_ids = \
                record.item_mdfe_ids.mapped('destinatario_cidade_id').mapped('estado_id')
            record.percurso_estado_ids = \
                percurso_estado_ids - record.empresa_id.municipio_id.estado_id
            if (record.modalidade_transporte ==
                    MODALIDADE_TRANSPORTE_RODOVIARIO and not record.condutor_ids):
                raise UserError(_('Informar no mínimo um condutor!'))

        self.situacao_mdfe = SITUACAO_NFE_A_ENVIAR

        return result

    def _envia_documento(self):
        self.ensure_one()
        result = super(SpedDocumento, self)._envia_documento()
        if not self.modelo == MODELO_FISCAL_MDFE:
            return result

        mdfe = self.gera_mdfe()
        envio = self.monta_envio()


        if not mdfe.status_servico().resposta.cStat == '107':
            return {}

        consulta = mdfe.consulta(self.chave).resposta
        if consulta.cStat in ('100', '101', '132'):
            if consulta.cStat == '100':
                # TODO Corrir o GenetateDS:
                # http://www.davekuhlman.org/generateDS.html#support-for-xs-any
                # implementar gds_build_any para infProt

                self.situacao_mdfe = SITUACAO_NFE_AUTORIZADA
            elif consulta.cStat == '132':
                self.situacao_mdfe = SITUACAO_MDFE_ENCERRADA
            return {}

        processo = mdfe.autorizacao(envio).resposta
        xml_str = processo.retorno.request.body
        resposta = processo.resposta
        if resposta.cStat != '103':
            self.mensagem_nfe = 'Código de retorno: ' + resposta.cStat + \
                                '\nMensagem: ' + resposta.xMotivo
            self.situacao_mdfe = SITUACAO_NFE_REJEITADA
            return {}

        recibo = None
        for i in range(5):
            time.sleep(resposta.infRec.tMed * (1.5 if i else 1.3))
            recibo = mdfe.consulta_recibo(resposta.infRec.nRec).resposta
            if recibo and recibo.cStat == '105':
                continue
            else:
                #
                # Lote recebido, vamos guardar o recibo
                #
                self.recibo = resposta.infRec.nRec
                break

        if recibo.cStat == '105':
            self.situacao_mdfe = SITUACAO_NFE_ENVIADA

        elif recibo.cStat == '104' and recibo.protMDFe.infProt.cStat == '100':

            # TODO: Gravar o xml
            # TODO: Gravar o pdf
            # TODO: Salvar a hora de autorizaçao

            self.protocolo_autorizacao = recibo.protMDFe.infProt.nProt

            # Autorizada
            if recibo.protMDFe.infProt.cStat == '100':
                self.protocolo_autorizacao = recibo.protMDFe.infProt.nProt
                self.situacao_mdfe = SITUACAO_NFE_AUTORIZADA

            # xml_str += self._retorno(recibo)
            arquivo = {}
            arquivo['xml'] = xml_str
            arquivo['chave'] = self.chave
            self.grava_xml(arquivo)
        else:
            #
            # Rejeitada por outros motivos, falha no schema etc. etc.
            #
            self.mensagem_nfe = 'Código de retorno: ' + \
                                recibo.protMDFe.infProt.cStat + \
                                '\nMensagem: ' + \
                                recibo.protMDFe.infProt.xMotivo
            self.situacao_mdfe = SITUACAO_NFE_REJEITADA

    def gera_pdf(self):
        for record in self:
            if record.modelo not in (MODELO_FISCAL_MDFE):
                return super(SpedDocumento, self).gera_pdf()

            if record.emissao != TIPO_EMISSAO_PROPRIA:
                return

        context = self.env.context.copy()
        reportname = 'report_sped_documento_mdfe'
        action_py3o_report = self.env.ref('l10n_br_mdfe.action_report_sped_documento_mdfe')

        if not action_py3o_report:
            raise UserError(
                'Py3o action report not found for report_name')

        context['report_name'] = reportname

        py3o_report = self.env['py3o.report'].create({
            'ir_actions_report_xml_id': action_py3o_report.id
        }).with_context(context)

        res, filetype = py3o_report.create_report(self.ids, {})
        return res

    def encerra_documento(self):

        encerramento = self.monta_encerramento()
        mdfe = self.gera_mdfe()
        processo = mdfe.encerramento(encerramento)
        if processo.resposta.infEvento.cStat == '135':
            self.situacao_mdfe = SITUACAO_MDFE_ENCERRADA
        mensagem = 'Código de retorno: ' + \
                   processo.resposta.infEvento.cStat
        mensagem += '\nMensagem: ' + \
                    processo.resposta.infEvento.xMotivo
        self.mensagem_nfe = mensagem


    def consultar_documento(self):

        mdfe = self.gera_mdfe()
        consulta = mdfe.consulta(self.chave)

        if consulta.resposta.cStat in ('100', '101', '132'):
           self.situacao_mdfe = STATUS_MDFE[consulta.resposta.cStat]
           self.protocolo_autorizacao = consulta.resposta.protMDFe.anytypeobjs_.nProt
        mensagem = 'Código de retorno: ' + \
                   consulta.resposta.cStat
        mensagem += '\nMensagem: ' + \
                    consulta.resposta.xMotivo

        self.mensagem_nfe = mensagem


    def cancelar_documento(self):

        cancelamento = self.monta_cancelamento()
        #Cria objeto para assinar e comunicar
        mdfe = self.gera_mdfe()
        processo = mdfe.cancelamento(cancelamento)
        if processo.resposta.infEvento.cStat == '101' or processo.resposta.infEvento.cStat == '135':
            self.situacao_mdfe = SITUACAO_NFE_CANCELADA
        mensagem = 'Código de retorno: ' + \
                   processo.resposta.infEvento.cStat
        mensagem += '\nMensagem: ' + \
                    processo.resposta.infEvento.xMotivo
        self.mensagem_nfe = mensagem

    def _grava_anexo(self, nome_arquivo='', conteudo='',
                     tipo='application/xml', model='sped.documento'):
        self.ensure_one()

        attachment = self.env['ir.attachment']

        busca = [
            ('res_model', '=', 'sped.documento'),
            ('res_id', '=', self.id),
            ('name', '=', nome_arquivo),
        ]
        attachment_ids = attachment.search(busca)
        attachment_ids.unlink()

        dados = {
            'name': nome_arquivo,
            'datas_fname': nome_arquivo,
            'res_model': 'sped.documento',
            'res_id': self.id,
            'datas': base64.b64encode(conteudo),
            'mimetype': tipo,
        }

        anexo_id = self.env['ir.attachment'].create(dados)

        return anexo_id

    def grava_xml(self, nfe):
        self.ensure_one()
        nome_arquivo = nfe['chave'] + '-mdfe.xml'
        conteudo = nfe['xml'].encode('utf-8')
        self.arquivo_xml_id = False
        self.arquivo_xml_id = self._grava_anexo(nome_arquivo, conteudo)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{id}/{nome}'.format(
                id=self.arquivo_xml_id.id,
                nome=self.arquivo_xml_id.name),
            'target': 'new',
        }

    def _retorno(self, retorno):

        match = re.search('<soap:Body>(.*?)</soap:Body>', retorno)

        if match:
            resultado = etree.tostring(etree.fromstring(match.group(1))[0])
            resposta = resultado.encode('utf-8')

            return resposta