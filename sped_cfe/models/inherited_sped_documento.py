# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import os
import logging

from odoo import api, fields, models
from odoo.addons.l10n_br_base.constante_tributaria import *
from odoo.exceptions import UserError, Warning


_logger = logging.getLogger(__name__)

try:
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                               agora)
    from pybrasil.valor import formata_valor
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.template import TemplateBrasil

    from satcfe.entidades import *

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    @api.multi
    def _buscar_configuracoes_pdv(self):
        self.configuracoes_pdv = self.env.user.configuracoes_sat_cfe

    configuracoes_pdv = fields.Many2one(
        string=u"Configurações para a venda",
        comodel_name="pdv.config",
        compute=_buscar_configuracoes_pdv
    )

    pagamento_autorizado_cfe = fields.Boolean(
        string=u"Pagamento Autorizado",
        readonly=True,
        default=False
    )

    def _check_permite_alteracao(self, operacao='create', dados={},
                                 campos_proibidos=[]):
        CAMPOS_PERMITIDOS = [
            'justificativa',
            'arquivo_xml_cancelamento_id',
            'arquivo_xml_autorizacao_cancelamento_id',
            'data_hora_cancelamento',
            'protocolo_cancelamento',
            'arquivo_pdf_id',
            'situacao_fiscal',
            'situacao_nfe',
        ]
        for documento in self:
            if documento.modelo not in (MODELO_FISCAL_NFE,
                                        MODELO_FISCAL_NFCE):
                super(SpedDocumento, documento)._check_permite_alteracao(
                    operacao,
                    dados,
                )
                continue

            if documento.emissao != TIPO_EMISSAO_PROPRIA:
                super(SpedDocumento, documento)._check_permite_alteracao(
                    operacao,
                    dados,
                )
                continue

            if documento.permite_alteracao:
                continue

            permite_alteracao = False
            #
            # Trata alguns campos que é permitido alterar depois da nota
            # autorizada
            #
            if documento.situacao_nfe == SITUACAO_NFE_AUTORIZADA:
                for campo in dados:
                    if campo in CAMPOS_PERMITIDOS:
                        permite_alteracao = True
                        break
                    elif campo not in campos_proibidos:
                        campos_proibidos.append(campo)

            if permite_alteracao:
                continue

            super(SpedDocumento, documento)._check_permite_alteracao(
                operacao,
                dados,
                campos_proibidos
            )

    @api.depends('data_hora_autorizacao', 'modelo', 'emissao', 'justificativa',
                 'situacao_nfe')
    def _compute_permite_cancelamento(self):
        #
        # Este método deve ser alterado por módulos integrados, para verificar
        # regras de negócio que proíbam o cancelamento de um documento fiscal,
        # como por exemplo, a existência de boletos emitidos no financeiro,
        # que precisariam ser cancelados antes, caso tenham sido enviados
        # para o banco, a verificação de movimentações de estoque confirmadas,
        # a contabilização definitiva do documento etc.
        #
        for documento in self:
            if documento.modelo not in (MODELO_FISCAL_CFE):
                super(SpedDocumento, documento)._compute_permite_cancelamento()
                continue

            if documento.emissao != TIPO_EMISSAO_PROPRIA:
                super(SpedDocumento, documento)._compute_permite_cancelamento()
                continue

            documento.permite_cancelamento = False

            # FIXME retirar apost teste
            documento.permite_cancelamento = True

            if documento.data_hora_autorizacao:
                tempo_autorizado = UTC.normalize(agora())
                tempo_autorizado -= \
                    parse_datetime(documento.data_hora_autorizacao + ' GMT')

                if (documento.situacao_nfe == SITUACAO_NFE_AUTORIZADA and
                        tempo_autorizado.days < 1):
                    documento.permite_cancelamento = True

    def processador_cfe(self):
        self.ensure_one()

        if self.modelo not in (MODELO_FISCAL_CFE):
            raise UserError('Tentando processar um documento que não é uma'
                            'CF-E!')

        Processador, Cliente = self.empresa_id.processador_cfe()

        # TODO: Buscar caminho correto do caixa
        # TODO: Buscar código de ativação do caixa
        caminho_sat = '/opt/sefaz/drs/libmfe.so'
        codigo_ativacao = '12345678'

        return Cliente(
            Processador(caminho_sat),
            codigo_ativacao=codigo_ativacao
        )

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
            'datas': conteudo.encode('base64'),
            'mimetype': tipo,
        }

        anexo_id = self.env['ir.attachment'].create(dados)

        return anexo_id

    def grava_cfe(self, cfe):
        self.ensure_one()
        nome_arquivo = 'envio-cfe.xml'
        self.arquivo_xml_id = False
        self.arquivo_xml_id = self._grava_anexo(nome_arquivo, cfe).id

    def grava_cfe_autorizacao(self, procNFe):
        # TODO:
        self.ensure_one()
        nome_arquivo = procNFe.NFe.chave + '-proc-nfe.xml'
        conteudo = procNFe.xml.encode('utf-8')
        self.arquivo_xml_autorizacao_id = False
        self.arquivo_xml_autorizacao_id = \
            self._grava_anexo(nome_arquivo, conteudo).id

    def grava_cfe_cancelamento(self, chave, canc):
        self.ensure_one()
        nome_arquivo = chave + '-01-can.xml'
        conteudo = canc.xml.encode('utf-8')
        self.arquivo_xml_cancelamento_id = False
        self.arquivo_xml_cancelamento_id = \
            self._grava_anexo(nome_arquivo, conteudo).id

    def grava_cfe_autorizacao_cancelamento(self, chave, canc):
        self.ensure_one()
        nome_arquivo = chave + '-01-proc-can.xml'
        conteudo = canc.xml.encode('utf-8')
        self.arquivo_xml_autorizacao_cancelamento_id = False
        self.arquivo_xml_autorizacao_cancelamento_id = \
            self._grava_anexo(nome_arquivo, conteudo).id

    def monta_cfe(self, processador=None):
        self.ensure_one()

        kwargs = {}

        if not self.modelo == MODELO_FISCAL_CFE:
            return

        #
        # Identificação da CF-E
        #
        cnpj_software_house, assinatura, numero_caixa = \
            self._monta_cfe_identificacao()

        #
        # Emitente
        #
        emitente = self._monta_cfe_emitente()

        #
        # Destinatário
        #
        destinatario = self._monta_cfe_destinatario()

        #
        # Itens
        #

        detalhamentos = []

        for item in self.item_ids:
            detalhamentos.append(item.monta_cfe())

        #
        # Pagamentos
        #
        pagamentos = []

        self._monta_cfe_pagamentos(pagamentos)

        cfe_venda = CFeVenda(
            CNPJ=cnpj_software_house,
            signAC=assinatura,
            numeroCaixa=2,
            emitente=emitente,
            detalhamentos=detalhamentos,
            pagamentos=pagamentos,
            vCFeLei12741=D(self.vr_ibpt).quantize('0.01'),
            **kwargs
        )
        cfe_venda.validar()

        return cfe_venda.documento()

    def _monta_cfe_identificacao(self):
        # FIXME: Buscar dados do cadastro da empresa / cadastro do caixa
        cnpj_software_house = self.configuracoes_pdv.cnpj_software_house
        assinatura = self.configuracoes_pdv.assinatura
        numero_caixa = self.configuracoes_pdv.numero_caixa
        return cnpj_software_house, assinatura, numero_caixa

    def _monta_cfe_emitente(self):
        emitente = Emitente(
                # FIXME:
                CNPJ=self.configuracoes_pdv.cnpjsh,
                IE=self.configuracoes_pdv.ie,
                # CNPJ=limpa_formatacao(empresa.cnpj_cpf),
                # IE=limpa_formatacao(empresa.ie or ''),
                indRatISSQN='N')
        emitente.validar()

        return emitente

    def _monta_cfe_destinatario(self,):

        participante = self.participante_id

        #
        # Trata a possibilidade de ausência do destinatário na NFC-e
        #
        if self.modelo == MODELO_FISCAL_CFE and not participante.cnpj_cpf:
            return

        #
        # Participantes estrangeiros tem a ID de estrangeiro sempre começando
        # com EX
        #
        if participante.cnpj_cpf.startswith('EX'):
            # TODO:
            pass
            # dest.idEstrangeiro.valor = \
            #     limpa_formatacao(participante.cnpj_cpf or '')

        elif len(participante.cnpj_cpf or '') == 14:
            return Destinatario(CPF=limpa_formatacao(participante.cnpj_cpf))

        elif len(participante.cnpj_cpf or '') == 18:
            return Destinatario(CNPJ=limpa_formatacao(participante.cnpj_cpf))

    def _monta_cfe_pagamentos(self, pag):
        if self.modelo != MODELO_FISCAL_CFE:
            return

        for pagamento in self.pagamento_ids:
            pag.append(pagamento.monta_cfe())

    def executa_antes_autorizar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de autorizar uma NF-e
        #
        self.ensure_one()
        return super(SpedDocumento, self).executa_antes_autorizar()

    def executa_depois_autorizar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de autorizar uma NF-e,
        # por exemplo, criar lançamentos financeiros, movimentações de
        # estoque etc.
        #
        self.ensure_one()
        super(SpedDocumento, self).executa_depois_autorizar()

        if self.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
            super(SpedDocumento, self)._compute_permite_cancelamento()
            return

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            super(SpedDocumento, self)._compute_permite_cancelamento()
            return

        #
        # Envia o email da nota para o cliente
        #
        mail_template = None
        if self.operacao_id.mail_template_id:
            mail_template = self.operacao_id.mail_template_id
        else:
            if self.modelo == MODELO_FISCAL_NFE and \
                    self.empresa_id.mail_template_nfe_autorizada_id:
                mail_template = \
                    self.empresa_id.mail_template_nfe_autorizada_id
            elif self.modelo == MODELO_FISCAL_NFCE and \
                    self.empresa_id.mail_template_nfce_autorizada_id:
                mail_template = \
                    self.empresa_id.mail_template_nfce_autorizada_id

        if mail_template is None:
            return

        self.envia_email(mail_template)

    def executa_antes_denegar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de denegar uma NF-e
        #
        super(SpedDocumento, self).executa_antes_denegar()

    def executa_depois_denegar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de denegar uma NF-e,
        # por exemplo, invalidar pedidos de venda e movimentações de estoque
        # etc.
        #
        super(SpedDocumento, self).executa_depois_denegar()
        self.ensure_one()

        if self.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
            super(SpedDocumento, self)._compute_permite_cancelamento()
            return

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            super(SpedDocumento, self)._compute_permite_cancelamento()
            return

        #
        # Envia o email da nota para o cliente
        #
        mail_template = None
        if self.modelo == MODELO_FISCAL_NFE and \
                self.empresa_id.mail_template_nfe_denegada_id:
            mail_template = \
                self.empresa_id.mail_template_nfe_denegada_id
        elif self.modelo == MODELO_FISCAL_NFCE and \
                self.empresa_id.mail_template_nfce_denegada_id:
            mail_template = \
                self.empresa_id.mail_template_nfce_denegada_id

        if mail_template is None:
            return

        self.envia_email(mail_template)

    def envia_email(self, mail_template):
        self.ensure_one()

        # super(SpedDocumento, self).envia_email(mail_template)

        self.ensure_one()
        mail_template.send_mail(self.id)

    def resposta_cfe(self, resposta):
        from mfecfe.resposta.enviardadosvenda import RespostaEnviarDadosVenda
        resposta_sefaz = RespostaEnviarDadosVenda.analisar(resposta.get('retorno'))

        if resposta_sefaz.EEEEE in '06000':
            self.executa_antes_autorizar()
            self.situacao_nfe = SITUACAO_NFE_AUTORIZADA
            self.executa_depois_autorizar()
            # self.data_hora_autorizacao = fields.Datetime.now()
        elif resposta_sefaz.EEEEE in ('06001', '06002', '06003', '06004', '06005',
                                '06006', '06007', '06008', '06009', '06010',
                                '06098', '06099'):
            self.executa_antes_denegar()
            self.situacao_fiscal = SITUACAO_FISCAL_DENEGADO
            self.situacao_nfe = SITUACAO_NFE_DENEGADA
            self.executa_depois_denegar()

        # u'123456|06001|Código de ativação inválido||'
        # u'123456|06002|SAT ainda não ativado||'
        # u'123456|06003|SAT não vinculado ao AC||'
        # u'123456|06004|Vinculação do AC não confere||'
        # u'123456|06005|Tamanho do CF-e-SAT superior a 1.500KB||'
        # u'123456|06006|SAT bloqueado pelo contribuinte||'
        # u'123456|06007|SAT bloqueado pela SEFAZ||'
        # u'123456|06008|SAT bloqueado por falta de comunicação||'
        # u'123456|06009|SAT bloqueado, código de ativação incorreto||'
        # u'123456|06010|Erro de validação do conteúdo||'
        # u'123456|06098|SAT em processamento. Tente novamente.||'
        # u'123456|06099|Erro desconhecido na emissão||'
        #
        # Envia a nota
        #
        # print (resposta.numeroSessao)
        # print (resposta.EEEEE)
        # print (resposta.CCCC)
        # print (resposta.arquivoCFeSAT)
        # print (resposta.timeStamp)
        # print (resposta.chaveConsulta)
        # print (resposta.valorTotalCFe)
        # print (resposta.assinaturaQRCODE)
        # print (resposta.xml())
        self.grava_cfe(resposta_sefaz.xml())

    @api.model
    def processar_venda_cfe(self, venda_id):
        venda = self.browse(venda_id)
        return venda.monta_cfe()

    @api.model
    def processar_resposta_cfe(self, venda_id, resposta):
        venda = self.browse(venda_id)
        return venda.resposta_cfe(resposta)

    def envia_nfe(self):
        self.ensure_one()
        result = super(SpedDocumento, self).envia_nfe()
        if not self.modelo == MODELO_FISCAL_CFE:
            return result

        if not self.pagamento_autorizado_cfe:
            self.envia_pagamento()
            if not self.pagamento_autorizado_cfe:
                raise Warning('Pagamento(s) não autorizado(s)!')

        # TODO: Conectar corretamente no SAT
        # cliente = self.processador_cfe()
        from mfecfe import BibliotecaSAT
        from mfecfe import ClienteSATLocal
        cliente = ClienteSATLocal(
            BibliotecaSAT('/opt/Integrador'),  # Caminho do Integrador
            codigo_ativacao='123456789'
        )
        # FIXME: Datas
        # # A NFC-e deve ter data de emissão no máx. 5 minutos antes
        # # da transmissão; por isso, definimos a hora de emissão aqui no
        # # envio
        if self.modelo == MODELO_FISCAL_NFCE:
            self.data_hora_emissao = fields.Datetime.now()
            self.data_hora_entrada_saida = self.data_hora_emissao

        cfe = self.monta_cfe()
        #
        # Processa resposta
        #
        resposta = cliente.enviar_dados_venda(cfe)
        if resposta.EEEEE in '06000':
            self.executa_antes_autorizar()
            self.situacao_nfe = SITUACAO_NFE_AUTORIZADA
            self.executa_depois_autorizar()
            self.data_hora_autorizacao = fields.Datetime.now()
        elif resposta.EEEEE in ('06001', '06002', '06003', '06004', '06005',
                                '06006', '06007', '06008', '06009', '06010',
                                '06098', '06099'):
            self.executa_antes_denegar()
            self.situacao_fiscal = SITUACAO_FISCAL_DENEGADO
            self.situacao_nfe = SITUACAO_NFE_DENEGADA
            self.executa_depois_denegar()
        # nfe = self.monta_nfe(resposta)

    @api.multi
    def _verificar_formas_pagamento(self):
        pagamentos_cartoes = []
        for pagamento in self.pagamento_ids:
            if pagamento.condicao_pagamento_id.forma_pagamento in ["03", "04"]:
                for duplicata in pagamento.duplicata_ids:
                    pagamentos_cartoes.append(duplicata)

        return pagamentos_cartoes

    def envia_pagamento(self):
        self.ensure_one()
        pagamentos_cartoes = self._verificar_formas_pagamento()
        if not pagamentos_cartoes:
            self.pagamento_autorizado_cfe = True
        else:
            pagamentos_autorizados = True
            config = self.configuracoes_pdv
            from mfecfe import BibliotecaSAT
            from mfecfe import ClienteVfpeLocal
            cliente = ClienteVfpeLocal(
                BibliotecaSAT('/opt/Integrador'),
                chave_acesso_validador=config.chave_acesso_validador
            )

            for duplicata in pagamentos_cartoes:
                if not duplicata.id_fila_status:
                    resposta = cliente.enviar_pagamento(
                        config.chave_requisicao, config.estabelecimento,
                        config.serial_pos, config.cnpjsh, self.bc_icms_proprio,
                        duplicata.valor, config.id_fila_validador,config.multiplos_pag,
                        config.anti_fraude, 'BRL', config.numero_caixa
                    )
                    duplicata.id_fila_status = resposta
                # FIXME status sempre vai ser negativo na homologacao
                resposta_status_pagamento = cliente.verificar_status_validador(
                    config.cnpjsh, duplicata.id_fila_status
                )
                #
                # resposta_status_pagamento = cliente.verificar_status_validador(
                #     config.cnpjsh, '214452'
                # )
                if resposta_status_pagamento.ValorPagamento == '0' and resposta_status_pagamento.IdFila == '0':
                    pagamentos_autorizados = False
                    break

            self.pagamento_autorizado_cfe = pagamentos_autorizados
