# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)


import logging
import base64
from io import StringIO
import qrcode
from decimal import Decimal as D
from lxml import etree
from odoo import api, fields, models
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    MODELO_FISCAL_CFE,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_FISCAL_DENEGADO,
    SITUACAO_FISCAL_REGULAR,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
)
from odoo.addons.l10n_br_cfe.constants.fiscal import (
    AMBIENTE_CFE_HOMOLOGACAO,
)

from odoo.exceptions import UserError, Warning


_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.misc import punctuation_rm

    from satcomum.ersat import ChaveCFeSAT, dados_qrcode
    from satcfe.entidades import (
        CFeVenda,
        Emitente,
        Destinatario,
        LocalEntrega,
        InformacoesAdicionais,
        CFeCancelamento,
    )
    from satcfe.excecoes import ExcecaoRespostaSAT, ErroRespostaSATInvalida

except (ImportError, IOError) as err:
    _logger.debug(err)


def filter_processador_edoc_cfe(record):
    if record.document_type_id.code == MODELO_FISCAL_CFE:
        return True
    return False


class FiscalDocument(models.Model):
    _inherit = 'l10n_br_fiscal.document'

    def _compute_cfe_code128(self, key):
        report = self.env['report']
        return base64.b64encode(report.barcode(
            'Code128',
            key,
            width=600,
            height=40,
            humanreadable=False,
        ))

    def _compute_cfe_qrcode(self, atttachment):
        datas = atttachment.datas.decode('base64')
        root = etree.fromstring(datas)
        tree = etree.ElementTree(root)
        image = qrcode.make(dados_qrcode(tree))
        buffer = StringIO()
        image.save(buffer, format="png")
        return base64.b64encode(buffer.getvalue())

    @api.depends('company_id', 'user_id')
    def compute_pos_config(self):
        """ Localiza o POS correto para o usuário,
        pois vários usuários podem compartilhar
        o mesmo SAT ou impressora.
        :return:
        """
        for record in self.filtered(filter_processador_edoc_cfe):
            if record.user_id.l10n_br_pos_config_id:
                record.configuracao_pdv_id = record.user_id.l10n_br_pos_config_id
            else:
                configuracao_pdv_id = record.configuracao_pdv_id.search([
                    '|',
                    ('company_id', '=', record.company_id.id),
                    ('company_id', '=', False)
                ], limit=1, order='company_id')
                record.configuracao_pdv_id = configuracao_pdv_id

    @api.multi
    def _verificar_pagamentos_cfe(self):
        """ Função Específica do Ceará / MF-e onde é necessário
        validar os pagamentos no integrador
        :return:
        """
        for record in self.filtered(filter_processador_edoc_cfe):
            pagamentos_validados = True
            for pagamento in record.fiscal_payment_ids:
                if not pagamento.pagamento_valido:
                    pagamentos_validados = False
                    break
            if record.amount_missing_payment_value:
                pagamentos_validados = False
            record.pagamento_autorizado_cfe = pagamentos_validados

    @api.depends('key', 'autorizacao_event_id', 'state_edoc')
    def _compute_cfe_image(self):
        for record in self.filtered(filter_processador_edoc_cfe):
            if not record.state_edoc == SITUACAO_EDOC_AUTORIZADA:
                return
            if record.key:
                record.cfe_code128 = self._compute_cfe_code128(record.key)
            if record.arquivo_xml_autorizacao_id:
                record.cfe_qrcode = self._compute_cfe_qrcode(
                    record.autorizacao_event_id.xml_returned_id
                )

    @api.depends('chave_cancelamento', 'cancel_document_event_id', 'state_edoc')
    def _compute_cfe_cancel_image(self):
        for record in self.filtered(filter_processador_edoc_cfe):
            if not record.state_edoc == SITUACAO_EDOC_CANCELADA:
                return
            if record.chave_cancelamento:
                record.num_cfe_cancelamento = int(
                    record.chave_cancelamento[31:37])
                record.cfe_cancelamento_code128 = self._compute_cfe_code128(
                    record.chave_cancelamento
                )
            if record.arquivo_xml_autorizacao_cancelamento_id:
                record.cfe_cancelamento_qrcode = self._compute_cfe_qrcode(
                    record.arquivo_xml_autorizacao_cancelamento_id.xml_returned_id
                )

    configuracao_pdv_id = fields.Many2one(
        string="Configurações PDV",
        comodel_name="l10n_br_fiscal.pos_config",
        compute='compute_pos_config',
    )

    pagamento_autorizado_cfe = fields.Boolean(
        string="Pagamento Autorizado",
        readonly=True,
        default=False,
        compute=_verificar_pagamentos_cfe
    )

    chave_cancelamento = fields.Char(
        string='Chave Cancelamento',
        size=44,
        readonly=True,
    )
    codigo_rejeicao_cfe = fields.Char(
        string='Código Rejeição CFe'
    )

    id_fila_validador = fields.Char(string='ID Fila Validador')

    cfe_code128 = fields.Binary(
        string='Imagem cfe code 128',
        compute='_compute_cfe_image',
    )

    cfe_qrcode = fields.Binary(
        string='Imagem cfe QRCODE',
        compute='_compute_cfe_image',
    )

    cfe_cancelamento_code128 = fields.Binary(
        string='Cfe code 128 cancelamento',
        compute='_compute_cfe_cancel_image',
    )

    cfe_cancelamento_qrcode = fields.Binary(
        string='Cfe QRCODE cancelamento',
        compute='_compute_cfe_cancel_image',
    )

    num_cfe_cancelamento = fields.Integer(
        string='Número',
        index=True,
        copy=False,
        compute='_compute_cfe_cancel_image',
    )
    numero_identificador_sessao = fields.Char(
        string='Numero identificador sessao'
    )

    # def _monta_cfe_informacoes_adicionais(self):
    #
    #     dados_informacoes_venda = InformacoesAdicionais()
    #     dados_informacoes_venda.infCpl = self._monta_informacoes_adicionais()
    #     dados_informacoes_venda.validar()
    #
    #     return dados_informacoes_venda
    #
    # def _monta_informacoes_adicionais(self):
    #     infcomplementar = self.infcomplementar or ''
    #
    #     dados_infcomplementar = {
    #         'nf': self,
    #     }
    #
    #     return self._renderizar_informacoes_template(
    #         dados_infcomplementar, infcomplementar)
    #
    # def _monta_cfe_destinatario(self,):
    #
    #     participante = self.participante_id
    #
    #     #
    #     # Trata a possibilidade de ausência do destinatário na NFC-e
    #     #
    #     if self.modelo == MODELO_FISCAL_CFE and not participante.cnpj_cpf:
    #         return
    #
    #     #
    #     # Participantes estrangeiros tem a ID de estrangeiro sempre começando
    #     # com EX
    #     #
    #     if participante.cnpj_cpf.startswith('EX'):
    #         # TODO:
    #         pass
    #         # dest.idEstrangeiro.valor = \
    #         #     limpa_formatacao(participante.cnpj_cpf or '')
    #
    #     elif len(participante.cnpj_cpf or '') == 14:
    #         return Destinatario(
    #             CPF=limpa_formatacao(participante.cnpj_cpf),
    #             xNome=participante.nome
    #         )
    #
    #     elif len(participante.cnpj_cpf or '') == 18:
    #         return Destinatario(
    #             CNPJ=limpa_formatacao(participante.cnpj_cpf),
    #             xNome=participante.nome
    #         )
    #
    # def _monta_cfe_entrega(self,):
    #
    #     participante = self.participante_id
    #
    #     if self.modelo == MODELO_FISCAL_CFE and not participante.cnpj_cpf:
    #         return
    #
    #     entrega = LocalEntrega(
    #         xLgr=participante.endereco,
    #         nro=participante.numero,
    #         xBairro=participante.bairro,
    #         xMun=participante.municipio_id.nome,
    #         UF=participante.municipio_id.estado
    #     )
    #     entrega.validar()
    #
    #     return entrega

    def _monta_cfe_emitente(self):
        ambiente = self.company_id.ambiente_cfe or AMBIENTE_CFE_HOMOLOGACAO

        if ambiente == AMBIENTE_CFE_HOMOLOGACAO:
            cnpj = self.configuracao_pdv_id.sat_cnpj_empresa_dev
            ie = self.configuracao_pdv_id.sat_ie_empresa_dev
        else:
            cnpj = self.company_cnpj_cpf
            ie = self.company_inscr_est

        emitente = Emitente(
            CNPJ=punctuation_rm(cnpj),
            IE=punctuation_rm(ie),
            indRatISSQN='N'
        )
        emitente.validar()
        return emitente

    def _monta_cfe_pagamentos(self, pag):
        if not self.filtered(filter_processador_edoc_cfe):
            return
        for pagamento in self.fiscal_payment_ids:
            pag.append(pagamento._serialize_cfe())

    def _serialize_cfe(self):
        self.ensure_one()
        if not self.filtered(filter_processador_edoc_cfe):
            return
        kwargs = {}
        #
        # Identificação da CF-E
        #
        cnpj_software_house, assinatura, numero_caixa = \
            self.configuracao_pdv_id._monta_cfe_identificacao()

        #
        # Emitente
        #
        emitente = self._monta_cfe_emitente()

        #
        # Destinatário
        #
        # if self.participante_id and self.participante_id.cnpj_cpf:
        #     kwargs['destinatario'] = self._monta_cfe_destinatario()
        #     kwargs['entrega'] = self._monta_cfe_entrega()

        #
        # Itens
        #

        detalhamentos = []

        for item in self.line_ids:
            detalhamentos.append(item._serialize_cfe())

        #
        # Pagamentos
        #
        pagamentos = []

        self._monta_cfe_pagamentos(pagamentos)

        cfe_venda = CFeVenda(
            CNPJ=punctuation_rm(cnpj_software_house),
            signAC=assinatura,
            numeroCaixa=numero_caixa,
            emitente=emitente,
            detalhamentos=detalhamentos,
            pagamentos=pagamentos,
            vCFeLei12741=D(self.amount_estimate_tax).quantize(D('0.01')),
            # informacoes_adicionais=self._monta_cfe_informacoes_adicionais(),
            **kwargs
        )
        cfe_venda.validar()
        return cfe_venda

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_processador_edoc_cfe):
            edocs.append(record._serialize_cfe())
        return edocs

    @api.multi
    def _document_export(self):
        super()._document_export()
        for record in self.filtered(filter_processador_edoc_cfe):
            edoc = record.serialize()[0]
            xml_file = edoc.documento()
            event_id = self._gerar_evento(xml_file, event_type="0")
            _logger.debug(xml_file)
            record.autorizacao_event_id = event_id

    @api.multi
    def _eletronic_document_send(self):
        super()._eletronic_document_send()
        for record in self.filtered(filter_processador_edoc_cfe):

            # TODO: VPFE - Ceará
            # if not record.pagamento_autorizado_cfe:
            #     raise Warning('Pagamento(s) não autorizado(s)!')
            # TODO: VPFE - Ceará
            # impressao = record.configuracao_pdv_id.impressora

            cliente = record.configuracao_pdv_id.processador_cfe()
            cfe = record._serialize_cfe()
            #
            # Processa resposta
            #
            try:
                if self.configuracao_pdv_id.tipo_sat == 'local':
                    resposta = cliente.enviar_dados_venda(cfe)
                elif self.configuracao_pdv_id.tipo_sat == 'rede_interna':
                    resposta = cliente.enviar_dados_venda(
                        dados_venda=cfe,
                    )
                else:
                    resposta = None
                if resposta.EEEEE in '06000':
                    # self.executa_antes_autorizar() TODO: executa_antes_autorizar
                    # self.executa_depois_autorizar() TODO: executa_depois_autorizar
                    key = ChaveCFeSAT(resposta.chaveConsulta)
                    self.data_hora_autorizacao = fields.Datetime.now()
                    self.number = key.numero_cupom_fiscal
                    self.document_serie = key.numero_serie
                    self.key = resposta.chaveConsulta[3:]

                    self.state_fiscal = SITUACAO_FISCAL_REGULAR
                    self.state_edoc = SITUACAO_EDOC_AUTORIZADA
                    self.autorizacao_event_id.set_done(resposta.xml())
                    self.codigo_situacao = resposta.EEEEE
                    motivo_situacao = '{} {}'.format(
                        resposta.mensagem or '',
                        resposta.mensagemSEFAZ or ''
                    )
                    self.motivo_situacao = motivo_situacao
                    # self.id_fila_validador = resposta.id_fila # TODO: Ceará

                elif resposta.EEEEE in ('06001', '06002', '06003', '06004',
                                        '06005', '06006', '06007', '06008',
                                        '06009', '06010', '06098', '06099'):
                    self.codigo_rejeicao_cfe = resposta.EEEEE
                    # self.executa_antes_denegar()
                    self.situacao_fiscal = SITUACAO_FISCAL_DENEGADO
                    self.situacao_nfe = SITUACAO_EDOC_DENEGADA
                    # self.executa_depois_denegar()
            except (ErroRespostaSATInvalida, ExcecaoRespostaSAT) as resposta:
                self.codigo_rejeicao_cfe = resposta.EEEEE
                mensagem = 'Código de retorno: ' + \
                           resposta.EEEEE
                mensagem += '\nMensagem: ' + \
                            resposta.mensagem
                if resposta.resposta.mensagem == 'Erro interno' and \
                        resposta.resposta.mensagemSEFAZ == 'ERRO' and not \
                        self.numero_identificador_sessao:
                    self.numero_identificador_sessao = \
                        resposta.resposta.numeroSessao
                self.mensagem_nfe = mensagem
                self.situacao_nfe = SITUACAO_EDOC_REJEITADA
            except Exception as resposta:
                if hasattr(resposta, 'resposta'):
                    self.codigo_rejeicao_cfe = resposta.resposta.EEEEE
                if resposta.resposta.mensagem == 'Erro interno' and \
                        resposta.resposta.mensagemSEFAZ == 'ERRO' and not \
                        self.numero_identificador_sessao:
                    self.numero_identificador_sessao = \
                        resposta.resposta.numeroSessao
                self.mensagem_nfe = "Falha na conexão com a retaguarda"
                self.situacao_nfe = SITUACAO_EDOC_REJEITADA

    @api.multi
    def cancel_invoice_online(self, justificative):
        super().cancel_invoice_online(justificative)
        for record in self.filtered(filter_processador_edoc_cfe):
            pass

    # def executa_depois_autorizar(self):
    #     #
    #     # Este método deve ser alterado por módulos integrados, para realizar
    #     # tarefas de integração necessárias depois de autorizar uma NF-e,
    #     # por exemplo, criar lançamentos financeiros, movimentações de
    #     # estoque etc.
    #     #
    #     self.ensure_one()
    #     super().executa_depois_autorizar()
    #
    #     if self.modelo != MODELO_FISCAL_CFE:
    #         super()._compute_permite_cancelamento()
    #         return
    #
    #     if self.emissao != DOCUMENT_ISSUER_COMPANY:
    #         super()._compute_permite_cancelamento()
    #         return
    #
    #     #
    #     # Envia o email da nota para o cliente
    #     #
    #     mail_template = None
    #     if self.operacao_id.mail_template_id:
    #         mail_template = self.operacao_id.mail_template_id
    #     else:
    #         if self.modelo == MODELO_FISCAL_NFE and \
    #                 self.empresa_id.mail_template_nfe_autorizada_id:
    #             mail_template = \
    #                 self.empresa_id.mail_template_nfe_autorizada_id
    #         elif self.modelo == MODELO_FISCAL_NFCE and \
    #                 self.empresa_id.mail_template_nfce_autorizada_id:
    #             mail_template = \
    #                 self.empresa_id.mail_template_nfce_autorizada_id
    #
    #     if mail_template is None:
    #         return
    #
    #     self.envia_email(mail_template)

    # def grava_cfe(self, cfe):
    #     self.ensure_one()
    #     nome_arquivo = 'envio-cfe.xml'
    #     conteudo = cfe.documento().encode('utf-8')
    #     self.arquivo_xml_id = False
    #     self.arquivo_xml_id = self._grava_anexo(nome_arquivo, conteudo).id
    #
    # def grava_cfe_autorizacao(self, cfe):
    #     self.ensure_one()
    #     nome_arquivo = self.key + '-proc-nfe.xml'
    #     self.arquivo_xml_autorizacao_id = False
    #     self.arquivo_xml_autorizacao_id = \
    #         self._grava_anexo(nome_arquivo, cfe).id
    #
    # def grava_cfe_cancelamento(self, key, canc):
    #     self.ensure_one()
    #     nome_arquivo = self.key + '-01-can.xml'
    #     conteudo = canc.documento().encode('utf-8')
    #     self.arquivo_xml_cancelamento_id = False
    #     self.arquivo_xml_cancelamento_id = \
    #         self._grava_anexo(nome_arquivo, conteudo).id
    #
    # def grava_cfe_autorizacao_cancelamento(self, key, canc):
    #     self.ensure_one()
    #     nome_arquivo = key + '-01-proc-can.xml'
    #     conteudo = canc.encode('utf-8')
    #     self.arquivo_xml_autorizacao_cancelamento_id = False
    #     self.arquivo_xml_autorizacao_cancelamento_id = \
    #         self._grava_anexo(nome_arquivo, conteudo).id

    #
    #
    # def resposta_cfe(self, resposta):
    #     """
    #
    #     :param resposta:
    #
    #     u'123456|06001|Código de ativação inválido||'
    #     u'123456|06002|SAT ainda não ativado||'
    #     u'123456|06003|SAT não vinculado ao AC||'
    #     u'123456|06004|Vinculação do AC não confere||'
    #     u'123456|06005|Tamanho do CF-e-SAT superior a 1.500KB||'
    #     u'123456|06006|SAT bloqueado pelo contribuinte||'
    #     u'123456|06007|SAT bloqueado pela SEFAZ||'
    #     u'123456|06008|SAT bloqueado por falta de comunicação||'
    #     u'123456|06009|SAT bloqueado, código de ativação incorreto||'
    #     u'123456|06010|Erro de validação do conteúdo||'
    #     u'123456|06098|SAT em processamento. Tente novamente.||'
    #     u'123456|06099|Erro desconhecido na emissão||'
    #
    #     resposta.numeroSessao
    #     resposta.EEEEE
    #     resposta.CCCC
    #     resposta.arquivoCFeSAT
    #     resposta.timeStamp
    #     resposta.chaveConsulta
    #     resposta.valorTotalCFe
    #     resposta.assinaturaQRCODE
    #     resposta.xml()
    #     :return:
    #     """
    #     from mfecfe.resposta.enviardadosvenda import RespostaEnviarDadosVenda
    #     resposta_sefaz = RespostaEnviarDadosVenda.analisar(
    #         resposta.get('retorno'))
    #
    #     if resposta_sefaz.EEEEE in '06000':
    #         self.executa_antes_autorizar()
    #         self.situacao_nfe = SITUACAO_EDOC_AUTORIZADA
    #         self.executa_depois_autorizar()
    #         # self.data_hora_autorizacao = fields.Datetime.now()
    #     elif resposta_sefaz.EEEEE in ('06001', '06002', '06003', '06004',
    #                                   '06005', '06006', '06007', '06008',
    #                                   '06009', '06010', '06098', '06099'):
    #         self.executa_antes_denegar()
    #         self.situacao_fiscal = SITUACAO_FISCAL_DENEGADO
    #         self.situacao_nfe = SITUACAO_EDOC_DENEGADA
    #         self.executa_depois_denegar()
    #     self.grava_cfe(resposta_sefaz.xml())
    #
    # @api.model
    # def processar_venda_cfe(self, venda_id):
    #     venda = self.browse(venda_id)
    #     return venda.monta_cfe()
    #
    # @api.model
    # def processar_resposta_cfe(self, venda_id, resposta):
    #     venda = self.browse(venda_id)
    #     return venda.resposta_cfe(resposta)
    #
    # def _monta_cancelamento(self):
    #     cnpj_software_house, assinatura, numero_caixa = \
    #         self._monta_cfe_identificacao()
    #     return CFeCancelamento(
    #         chCanc='CFe' + self.key,
    #         CNPJ=limpa_formatacao(cnpj_software_house),
    #         signAC=assinatura,
    #         numeroCaixa=int(numero_caixa),
    #     )
    #
    # def cancela_nfe(self):
    #     self.ensure_one()
    #     result = super().cancela_nfe()
    #     if not self.modelo == MODELO_FISCAL_CFE:
    #         return result
    #     if not fields.Datetime.from_string(fields.Datetime.now()) < \
    #         fields.Datetime.from_string(
    #             self.data_hora_emissao) + relativedelta(minutes=29):
    #         raise UserError("Cupom Fiscal não pode ser cancelado após "
    #                         "passados 30 minutos.")
    #
    #     processador = self.processador_cfe()
    #
    #     try:
    #         cancelamento = self._monta_cancelamento()
    #
    #         if self.configuracao_pdv_id.tipo_sat == 'local':
    #             processo = processador.cancelar_ultima_venda(
    #                 cancelamento.chCanc,
    #                 cancelamento
    #             )
    #         elif self.configuracao_pdv_id.tipo_sat == 'rede_interna':
    #             processo = processador.cancelar_ultima_venda(
    #                 cancelamento.chCanc,
    #                 cancelamento,
    #                 self.configuracao_pdv_id.codigo_ativacao,
    #                 self.configuracao_pdv_id.path_integrador
    #             )
    #         else:
    #             processo = None
    #
    #         #
    #         # O cancelamento foi aceito e vinculado à CF-E
    #         #
    #         if processo.EEEEE in '07000':
    #             #
    #             # Grava o protocolo de cancelamento
    #             #
    #             self.grava_cfe_cancelamento(self.key, cancelamento)
    #             self.grava_cfe_autorizacao_cancelamento(
    #                 self.key, processo.xml())
    #             self.chave_cancelamento = processo.chaveConsulta[3:]
    #
    #  #           dh_cancelamento = UTC.normalize(processo.timeStamp)
    #  #           self.data_hora_cancelamento = dh_cancelamento
    #
    #             # if impressao:
    #             #     processador.imprimir_cupom_cancelamento(
    #             #         self.arquivo_xml_autorizacao_id.datas,
    #             #         processo.arquivoCFeBase64,
    #             #         impressao.modelo,
    #             #         impressao.conexao
    #             #     )
    #
    #             # data_cancelamento = retevento.infEvento.dhRegEvento.valor
    #             # data_cancelamento = UTC.normalize(data_cancelamento)
    #             # self.protocolo_cancelamento = \
    #             #     procevento.retEvento.infEvento.nProt.valor
    #
    #             #
    #             # Cancelamento extemporâneo
    #             #
    #             self.executa_antes_cancelar()
    #
    #             if processo.EEEEE != '07000':
    #                 # FIXME: Verificar se da para cancelar fora do prazo
    #                 self.situacao_fiscal = \
    #                     SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO
    #                 self.situacao_nfe = SITUACAO_EDOC_CANCELADA
    #             elif processo.EEEEE == '07000':
    #                 self.situacao_fiscal = SITUACAO_FISCAL_CANCELADO
    #                 self.situacao_nfe = SITUACAO_EDOC_CANCELADA
    #
    #             self.executa_depois_cancelar()
    #             return self.imprimir_documento()
    #
    #     except (ErroRespostaSATInvalida, ExcecaoRespostaSAT) as resposta:
    #         mensagem = 'Erro no cancelamento'
    #         mensagem += '\nCódigo: ' + resposta.EEEEE
    #         mensagem += '\nMotivo: ' + resposta.mensagem
    #         raise UserError(mensagem)
    #     except Exception as resposta:
    #
    #         if not hasattr(resposta, 'resposta'):
    #             mensagem = 'Erro no cancelamento'
    #             mensagem += '\nMotivo: ' + resposta.message
    #             raise UserError(mensagem)
    #
    #         mensagem = 'Erro no cancelamento'
    #         mensagem += '\nCódigo: ' + resposta.resposta.EEEEE
    #         mensagem += '\nMotivo: ' + resposta.resposta.mensagem
    #         raise UserError(mensagem)
    #
    # @api.multi
    # def imprimir_documento(self):
    #     """ Print the invoice and mark it as sent, so that we can see more
    #         easily the next step of the workflow
    #     """
    #     self.ensure_one()
    #     if not self.modelo == MODELO_FISCAL_CFE:
    #         return super().imprimir_documento()
    #     self.sudo().write({'documento_impresso': True})
    #     return self.env['report'].get_action(self, 'report_sped_documento_cfe')


    #
    #  Código antigo - v10 - apagar
    #

    # @api.multi
    # def _compute_total_a_pagar(self):
    #     for record in self:
    #         valor = record.amount_financial
    #         for pagamento in record.fiscal_payment_ids:
    #             valor -= pagamento.valor
    #         record.vr_total_residual = valor
    #
    # vr_total_residual = fields.Monetary(
    #     string='Total Residual',
    #     compute='_compute_total_a_pagar',
    # )
    #
    # # @api.depends('modelo', 'issuer', 'importado_xml', 'situacao_nfe')
    # def _compute_permite_alteracao(self):
    #     super()._compute_permite_alteracao()
    #
    #     for documento in self:
    #         if not documento.modelo == MODELO_FISCAL_CFE:
    #             super()._compute_permite_alteracao()
    #             continue
    #
    #         if documento.issuer != DOCUMENT_ISSUER_COMPANY:
    #             super()._compute_permite_alteracao()
    #             continue
    #
    #         #
    #         # É emissão própria de NF-e ou NFC-e, permite alteração
    #         # somente quando estiver em digitação ou rejeitada
    #         #
    #         documento.permite_alteracao = documento.permite_alteracao or \
    #             documento.situacao_nfe in (SITUACAO_EDOC_EM_DIGITACAO,
    #                                        SITUACAO_EDOC_REJEITADA)
    #
    # def _check_permite_alteracao(self, operacao='create', dados={},
    #                              campos_proibidos=[]):
    #
    #     CAMPOS_PERMITIDOS = [
    #         'message_follower_ids',
    #         'justificativa',
    #         'chave_cancelamento',
    #     ]
    #     for documento in self:
    #         if documento.modelo != MODELO_FISCAL_CFE:
    #             super()._check_permite_alteracao(
    #                 operacao,
    #                 dados,
    #             )
    #             continue
    #
    #         if documento.issuer != DOCUMENT_ISSUER_COMPANY:
    #             super()._check_permite_alteracao(
    #                 operacao,
    #                 dados,
    #             )
    #             continue
    #
    #         if documento.permite_alteracao:
    #             continue
    #
    #         permite_alteracao = False
    #
    #         if documento.situacao_nfe == SITUACAO_EDOC_AUTORIZADA:
    #             for campo in dados:
    #                 if campo in CAMPOS_PERMITIDOS:
    #                     permite_alteracao = True
    #                     break
    #                 elif campo not in campos_proibidos:
    #                     campos_proibidos.append(campo)
    #
    #         if permite_alteracao:
    #             continue
    #
    # @api.multi
    # def imprimir_documento(self):
    #     # TODO: Reimprimir cupom de cancelamento caso houver com o normal.
    #     if not self.modelo == MODELO_FISCAL_CFE:
    #         return super().imprimir_documento()
    #     self.ensure_one()
    #     impressao = self.configuracao_pdv_id.impressora
    #     if impressao:
    #         try:
    #             cliente = self.processador_cfe()
    #             resposta = self.arquivo_xml_autorizacao_id.datas
    #             cliente.imprimir_cupom_venda(
    #                 resposta,
    #                 impressao.modelo,
    #                 impressao.conexao,
    #                 self.configuracao_pdv_id.site_consulta_qrcode.encode("utf-8")
    #             )
    #         except Exception as e:
    #             _logger.error("Erro ao imprimir o cupom")
    #     else:
    #         raise Warning("Não existem configurações para impressão no PDV!")

    def gera_pdf(self):
        for record in self:
            if record.modelo not in (MODELO_FISCAL_CFE):
                return super().gera_pdf()

            if record.issuer != DOCUMENT_ISSUER_COMPANY:
                return

        context = self.env.context.copy()
        reportname = 'report_sped_documento_cfe'
        action_py3o_report = self.env.ref('l10n_br_cfe.action_report_sped_documento_cfe')

        if not action_py3o_report:
            raise UserError(
                'Py3o action report not found for report_name')

        context['report_name'] = reportname

        py3o_report = self.env['py3o.report'].create({
            'ir_actions_report_xml_id': action_py3o_report.id
        }).with_context(context)

        res, filetype = py3o_report.create_report(self.ids, {})
        return res

    @api.multi
    def _verificar_formas_pagamento(self):
        pagamentos_cartoes = []
        for pagamento in self.fiscal_payment_ids:
            if pagamento.condicao_pagamento_id.forma_pagamento in ["03", "04"]:
                pagamentos_cartoes.append(pagamento)

        return pagamentos_cartoes

    def envia_pagamento(self):
        self.ensure_one()
        pagamentos_cartoes = self._verificar_formas_pagamento()
        if not pagamentos_cartoes:
            self.pagamento_autorizado_cfe = True
        else:
            pagamentos_autorizados = True
            config = self.configuracao_pdv_id
            cliente = self.processador_vfpe()

            for duplicata in pagamentos_cartoes:
                if not duplicata.id_pagamento:
                    if self.configuracao_pdv_id.tipo_sat == 'local':
                        resposta = cliente.enviar_pagamento(
                            config.chave_requisicao, duplicata.estabecimento,
                            duplicata.serial_pos, config.cnpjsh,
                            self.bc_icms_proprio,
                            duplicata.valor,
                            config.multiplos_pag,
                            config.anti_fraude,
                            'BRL',
                            int(config.numero_caixa),
                        )
                    elif self.configuracao_pdv_id.tipo_sat == 'rede_interna':
                        resposta = cliente.enviar_pagamento(
                            config.chave_requisicao,
                            duplicata.estabecimento,
                            duplicata.serial_pos,
                            config.cnpjsh,
                            self.bc_icms_proprio,
                            duplicata.valor,
                            config.multiplos_pag,
                            config.anti_fraude,
                            'BRL',
                            int(config.numero_caixa),
                            config.chave_acesso_validador,
                            config.path_integrador,
                            self.numero_identificador_sessao
                        )
                    resposta_pagamento = resposta.split('|')
                    if len(resposta_pagamento[0]) >= 7:
                        duplicata.id_pagamento = resposta_pagamento[0]
                        duplicata.id_fila = resposta_pagamento[1]
                    else:
                        pagamentos_autorizados = False
                # FIXME status sempre vai ser negativo na homologacao
                # resposta_status_pagamento =
                        # cliente.verificar_status_validador(
                #     config.cnpjsh, duplicata.id_fila_status
                # )
                #
                # resposta_status_pagamento =
                        # cliente.verificar_status_validador(
                #     config.cnpjsh, '214452'
                # )
                # if resposta_status_pagamento.ValorPagamento
                        # == '0' and resposta_status_pagamento.IdFila == '0':
                #     pagamentos_autorizados = False
                #     break

            self.pagamento_autorizado_cfe = pagamentos_autorizados
