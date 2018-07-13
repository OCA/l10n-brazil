# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA, Grupo Zenir
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals
import tempfile

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
    SITUACAO_FISCAL_DENEGADO,
)

from pynfe.utils.flags import (
    WS_MDFE_CONSULTA,
    WS_MDFE_STATUS_SERVICO,
    WS_MDFE_CONSULTA_NAO_ENCERRADOS,
    WS_MDFE_RECEPCAO,
    WS_MDFE_RET_RECEPCAO,
)

from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                           agora)

from edoclib.edoc import DocumentoEletronico
from odoo.exceptions import UserError, Warning


class SpedDocumento(models.Model):

    _inherit = 'sped.documento'

    @api.depends('modelo', 'emissao', 'importado_xml', 'situacao_nfe')
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

        return result

    def _envia_documento(self):
        self.ensure_one()
        result = super(SpedDocumento, self)._envia_documento()
        if not self.modelo == MODELO_FISCAL_MDFE:
            return result

        # processador = self.processador_cfe()
        processador = False

        cert = self.empresa_id.certificado_id.arquivo.decode('base64')
        pw = self.empresa_id.certificado_id.senha
        uf = self.empresa_id.estado

        caminho = tempfile.gettempdir() + '/certificado.pfx'
        f = open(caminho, 'wb')
        f.write(cert)
        f.close()

        mdfe = self.monta_mdfe(processador)
        edoc = DocumentoEletronico(mdfe, certificado=caminho, senha=pw, uf=uf)

        processo = None
        for p in edoc.envia_documento():
            processo = p

        #
        # Se o último processo foi a consulta do status do serviço, significa
        # que ele não está online...
        #
        if processo.webservice == WS_MDFE_STATUS_SERVICO:
            self.situacao_nfe = SITUACAO_NFE_EM_DIGITACAO
        #
        # Se o último processo foi a consulta da nota, significa que ela já
        # está emitida
        #
        elif processo.webservice == WS_MDFE_CONSULTA:
            if processo.resposta.cStat == '100':
                # TODO Corrir o GenetateDS:
                # http://www.davekuhlman.org/generateDS.html#support-for-xs-any
                # implementar gds_build_any para infProt

                # self.chave = processo.resposta.protMDFe.infProt.chMDFe
                # self.executa_antes_autorizar()
                self.situacao_nfe = SITUACAO_NFE_AUTORIZADA
                # self.executa_depois_autorizar()

            else:
                self.situacao_nfe = SITUACAO_NFE_EM_DIGITACAO
        #
        # Se o último processo foi o envio do lote, significa que a consulta
        # falhou, mas o envio não
        #
        elif processo.webservice == WS_MDFE_RECEPCAO:
            #
            # Lote recebido, vamos guardar o recibo
            #
            if processo.resposta.cStat == '103':
                self.recibo = processo.resposta.infRec.nRec
            else:
                mensagem = 'Código de retorno: ' + \
                           processo.resposta.cStat
                mensagem += '\nMensagem: ' + \
                            processo.resposta.xMotivo
                self.mensagem_nfe = mensagem
                self.situacao_nfe = SITUACAO_NFE_REJEITADA
        #
        # Se o último processo foi o retorno do recibo, a nota foi rejeitada,
        # denegada, autorizada, ou ainda não tem resposta
        #
        elif processo.webservice == WS_MDFE_RET_RECEPCAO:
            #
            # Consulta ainda sem resposta, a nota ainda não foi processada
            #
            if processo.resposta.cStat == '105':
                self.situacao_nfe = SITUACAO_NFE_ENVIADA
            #
            # Lote processado
            #
            elif processo.resposta.cStat == '104':
                protMDFe = processo.resposta.protMDFe

                #
                # Autorizada ou denegada
                #
                if protMDFe.infProt.cStat == '100':
                    # procMDFe = processo.resposta.procMDFe
                    # self.grava_xml(procMDFe.MDFe)
                    # self.grava_xml_autorizacao(procMDFe)

                    # TODO: Gravar o xml
                    # TODO: Gravar o pdf
                    # TODO: Salbar a gora de autorizaçao

                    # data_autorizacao = protMDFe.infProt.dhRecbto
                    # data_autorizacao = UTC.normalize(data_autorizacao)

                    # self.data_hora_autorizacao = data_autorizacao
                    self.protocolo_autorizacao = protMDFe.infProt.nProt
                    self.chave = protMDFe.infProt.chMDFe

                    if protMDFe.infProt.cStat == '100':
                        self.executa_antes_autorizar()
                        self.situacao_nfe = SITUACAO_NFE_AUTORIZADA
                        self.executa_depois_autorizar()

                else:
                    mensagem = 'Código de retorno: ' + \
                               protMDFe.infProt.cStat
                    mensagem += '\nMensagem: ' + \
                                protMDFe.infProt.xMotivo
                    self.mensagem_nfe = mensagem
                    self.situacao_nfe = SITUACAO_NFE_REJEITADA
            else:
                #
                # Rejeitada por outros motivos, falha no schema etc. etc.
                #
                mensagem = 'Código de retorno: ' + \
                           processo.resposta.cStat
                mensagem += '\nMensagem: ' + \
                            processo.resposta.xMotivo
                self.mensagem_nfe = mensagem
                self.situacao_nfe = SITUACAO_NFE_REJEITADA

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
