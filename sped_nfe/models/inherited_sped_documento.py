# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import os
import logging
import base64
from StringIO import StringIO
from io import BytesIO
from pyPdf import PdfFileReader, PdfFileWriter

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_base.constante_tributaria import *

from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)

try:
    from pysped.nfe.webservices_flags import *
    from pysped.nfe.leiaute import *
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                               agora)
    from pybrasil.valor import formata_valor
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.template import TemplateBrasil

except (ImportError, IOError) as err:
    _logger.debug(err)

from .versao_nfe_padrao import *


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    #
    # Os campos de anexos abaixo servem para que os anexos não possam
    # ser excluídos pelo usuário, somente através do sistema ou pelo
    # suporte
    #
    arquivo_xml_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML',
        ondelete='restrict',
        copy=False,
    )
    arquivo_xml_autorizacao_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de autorização',
        ondelete='restrict',
        copy=False,
    )
    arquivo_xml_cancelamento_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de cancelamento',
        ondelete='restrict',
        copy=False,
    )
    arquivo_xml_autorizacao_cancelamento_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de autorização de cancelamento',
        ondelete='restrict',
        copy=False,
    )
    arquivo_xml_inutilizacao_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de inutilização',
        ondelete='restrict',
        copy=False,
    )
    arquivo_xml_autorizacao_inutilizacao_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de inutilização',
        ondelete='restrict',
        copy=False,
    )
    arquivo_pdf_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='PDF DANFE/DANFCE',
        ondelete='restrict',
        copy=False,
    )
    mensagem_nfe = fields.Text(
        string='Mensagem',
        copy=False,
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
    data_hora_inutilizacao = fields.Datetime(
        string='Data de inutilização',
        index=True,
    )
    data_inutilizacao = fields.Date(
        string='Data de inutilização',
        compute='_compute_data_hora_separadas',
        store=True,
        index=True,
    )
    justificativa = fields.Char(
        string='Justificativa',
        size=60,
    )
    recibo = fields.Char(
        string='Recibo de transmissão',
        size=60,
    )
    protocolo_autorizacao = fields.Char(
        string='Protocolo de autorização',
        size=60,
    )
    protocolo_cancelamento = fields.Char(
        string='Protocolo de cancelamento',
        size=60,
    )
    protocolo_inutilizacao = fields.Char(
        string='Protocolo de inutilização',
        size=60,
    )

    consulta_dfe_id = fields.Many2one(
        comodel_name='sped.consulta.dfe',
        string='Consulta-DFe',
        ondelete='cascade',
    )

    xmls_exportados = fields.Boolean(
        string='XMLs exportados para a pasta da contabilidade',
        default=False,
    )

    @api.multi
    def action_fluxo_compras(self):
        self.ensure_one()
        return {
            'name': "Associar Pedido de Compras",
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref(
                'sped_nfe.sped_documento_ajuste_recebimento_form').id,
            'res_id': self.id,
            'res_model': 'sped.documento',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'flags': {'form': {'action_buttons': True,
                               'options': {'mode': 'edit'}}},
        }

    @api.depends('data_hora_emissao', 'data_hora_entrada_saida',
                 'data_hora_autorizacao', 'data_hora_cancelamento')
    def _compute_data_hora_separadas(self):
        super(SpedDocumento, self)._compute_data_hora_separadas()

        for documento in self:
            if documento.data_hora_autorizacao:
                data_hora_autorizacao = data_hora_horario_brasilia(
                    parse_datetime(documento.data_hora_autorizacao))
                documento.data_autorizacao = str(data_hora_autorizacao)[:10]

            if documento.data_hora_cancelamento:
                data_hora_cancelamento = data_hora_horario_brasilia(
                    parse_datetime(documento.data_hora_cancelamento))
                documento.data_cancelamento = str(data_hora_cancelamento)[:10]

            if documento.data_hora_inutilizacao:
                data_hora_inutilizacao = data_hora_horario_brasilia(
                    parse_datetime(documento.data_hora_inutilizacao))
                documento.data_inutilizacao = str(data_hora_inutilizacao)[:10]

    @api.depends('modelo', 'emissao', 'importado_xml', 'situacao_nfe')
    def _compute_permite_alteracao(self):
        result = super(SpedDocumento, self)._compute_permite_alteracao()
        for documento in self:
            if documento.modelo not in (MODELO_FISCAL_NFE,
                                        MODELO_FISCAL_NFCE):
                continue
            if documento.emissao != TIPO_EMISSAO_PROPRIA:
                continue

            #
            # É emissão própria de NF-e ou NFC-e, permite alteração
            # somente quando estiver em digitação ou rejeitada
            #
            documento.permite_alteracao = documento.permite_alteracao or \
                                          documento.situacao_nfe in (SITUACAO_NFE_EM_DIGITACAO,
                                                                     SITUACAO_NFE_REJEITADA)
        return result

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
            'permite_cancelamento',
            'permite_alteracao',
            'xmls_exportados',
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
                 'situacao_nfe', 'importado_xml')
    def _compute_permite_cancelamento(self):
        super(SpedDocumento, self)._compute_permite_cancelamento()

        #
        # Este método deve ser alterado por módulos integrados, para verificar
        # regras de negócio que proíbam o cancelamento de um documento fiscal,
        # como por exemplo, a existência de boletos emitidos no financeiro,
        # que precisariam ser cancelados antes, caso tenham sido enviados
        # para o banco, a verificação de movimentações de estoque confirmadas,
        # a contabilização definitiva do documento etc.
        #
        for documento in self:
            if documento.modelo not in (MODELO_FISCAL_NFE,
                                        MODELO_FISCAL_NFCE):
                super(SpedDocumento, documento)._compute_permite_cancelamento()
                continue

            if documento.emissao != TIPO_EMISSAO_PROPRIA:
                super(SpedDocumento, documento)._compute_permite_cancelamento()
                continue

            if documento.data_hora_autorizacao:
                tempo_autorizado = UTC.normalize(agora())
                tempo_autorizado -= \
                    parse_datetime(documento.data_hora_autorizacao + ' GMT')

                if (documento.situacao_nfe == SITUACAO_NFE_AUTORIZADA and
                        tempo_autorizado.days < 1):
                    documento.permite_cancelamento = \
                        documento.permite_cancelamento and True

    @api.depends('modelo', 'emissao', 'justificativa', 'situacao_nfe', 'importado_xml')
    def _compute_permite_inutilizacao(self):
        #
        # Este método deve ser alterado por módulos integrados, para verificar
        # regras de negócio que proíbam a inutilização de um documento fiscal,
        # como por exemplo, a existência de boletos emitidos no financeiro,
        # que precisariam ser cancelados antes, caso tenham sido enviados
        # para o banco, a verificação de movimentações de estoque confirmadas,
        # a contabilização definitiva do documento etc.
        #
        for documento in self:
            if documento.modelo not in (MODELO_FISCAL_NFE,
                                        MODELO_FISCAL_NFCE):
                super(SpedDocumento, documento)._compute_permite_inutilizacao()
                continue

            if documento.emissao != TIPO_EMISSAO_PROPRIA:
                super(SpedDocumento, documento)._compute_permite_inutilizacao()
                continue

            documento.permite_inutilizacao = False

            if documento.situacao_nfe in (SITUACAO_NFE_EM_DIGITACAO,
                                          SITUACAO_NFE_REJEITADA):
                documento.permite_inutilizacao = True

    def processador_nfe(self):
        self.ensure_one()

        if self.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
            raise UserError('Tentando processar um documento que não é uma'
                            'NF-e nem uma NFC-e!')

        processador = self.empresa_id.processador_nfe()
        processador.ambiente = int(self.ambiente_nfe or
                                   AMBIENTE_NFE_HOMOLOGACAO)
        processador.modelo = self.modelo
        if not self.tipo_emissao_nfe == TIPO_EMISSAO_NFE_NORMAL:
            processador.contingencia = True

        if self.modelo == MODELO_FISCAL_NFE:
            if self.empresa_id.logo_danfe:
                data = self.empresa_id.logo_danfe
                logo = StringIO(data.decode('base64'))
                processador.danfe.logo = logo
            processador.danfe.nome_sistema = 'Odoo 10.0'
            processador.caminho = os.path.join(
                self.empresa_id.caminho_sped,
                'nfe',
            )

        elif self.modelo == MODELO_FISCAL_NFCE:
            if self.empresa_id.logo_danfce:
                processador.danfce.logo = self.empresa_id.logo_danfce
            processador.danfce.nome_sistema = 'Odoo 10.0'
            processador.caminho = os.path.join(
                self.empresa_id.caminho_sped,
                'nfce',
            )

        return processador

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
        nome_arquivo = nfe.chave + '-nfe.xml'
        conteudo = nfe.xml.encode('utf-8')
        self.arquivo_xml_id = False
        self.arquivo_xml_id = self._grava_anexo(nome_arquivo, conteudo)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{id}/{nome}'.format(
                id=self.arquivo_xml_id.id,
                nome=self.arquivo_xml_id.name),
            'target': 'new',
        }

    def grava_pdf(self, nfe, danfe_pdf):
        self.ensure_one()
        nome_arquivo = nfe.chave + '.pdf'
        conteudo = danfe_pdf
        self.arquivo_pdf_id = False
        self.arquivo_pdf_id = self._grava_anexo(nome_arquivo, conteudo,
                                                tipo='application/pdf')

        return {
            'name': 'Download PDF',
            'type': 'ir.actions.act_url',
            'url': '/web/content/{id}/{nome}'.format(
                id=self.arquivo_pdf_id.id,
                nome=self.arquivo_pdf_id.name),
            'target': 'new',
        }

    def grava_xml_autorizacao(self, procNFe):
        self.ensure_one()
        nome_arquivo = procNFe.NFe.chave + '-proc-nfe.xml'
        conteudo = procNFe.xml.encode('utf-8')
        self.arquivo_xml_autorizacao_id = False
        self.arquivo_xml_autorizacao_id = \
            self._grava_anexo(nome_arquivo, conteudo)
        self.xmls_exportados = False

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{id}/{nome}'.format(
                id=self.arquivo_xml_autorizacao_id.id,
                nome=self.arquivo_xml_autorizacao_id.name),
            'target': 'new',
        }

    def grava_xml_cancelamento(self, chave, canc):
        self.ensure_one()
        nome_arquivo = chave + '-01-can.xml'
        conteudo = canc.xml.encode('utf-8')
        self.arquivo_xml_cancelamento_id = False
        self.arquivo_xml_cancelamento_id = \
            self._grava_anexo(nome_arquivo, conteudo)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{id}/{nome}'.format(
                id=self.arquivo_xml_cancelamento_id.id,
                nome=self.arquivo_xml_cancelamento_id.name),
            'target': 'new',
        }

    def grava_xml_autorizacao_cancelamento(self, chave, canc):
        self.ensure_one()
        nome_arquivo = chave + '-01-proc-can.xml'
        conteudo = canc.xml.encode('utf-8')
        self.arquivo_xml_autorizacao_cancelamento_id = False
        self.arquivo_xml_autorizacao_cancelamento_id = \
            self._grava_anexo(nome_arquivo, conteudo)
        self.xmls_exportados = False

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{id}/{nome}'.format(
                id=self.arquivo_xml_autorizacao_cancelamento_id.id,
                nome=self.arquivo_xml_autorizacao_cancelamento_id.name),
            'target': 'new',
        }

    def grava_xml_inutilizacao(self, chave, inut):
        self.ensure_one()
        nome_arquivo = chave + '-inu.xml'
        conteudo = inut.xml.encode('utf-8')
        self.arquivo_xml_inutilizacao_id = False
        self.arquivo_xml_inutilizacao_id = \
            self._grava_anexo(nome_arquivo, conteudo).id

    def grava_xml_autorizacao_inutilizacao(self, chave, inut):
        self.ensure_one()
        nome_arquivo = chave + '-proc-inu.xml'
        conteudo = inut.xml.encode('utf-8')
        self.arquivo_xml_autorizacao_inutilizacao_id = False
        self.arquivo_xml_autorizacao_inutilizacao_id = \
            self._grava_anexo(nome_arquivo, conteudo).id
        self.xmls_exportados = False

    @api.multi
    def consultar_nfe(self):
        for record in self:
            record._consultar_nfe()

    def _consultar_nfe(self, processador=None, nfe=None):
        #
        # Se a nota já foi emitida: autorizada, rejeitada e denegada
        # E não temos todos os dados, tentamos consultar a nota.
        #

        if not processador:
            processador = self.processador_nfe()
        if not nfe:
            nfe = self.monta_nfe(processador)

        consulta = processador.consultar_nota(
            processador.ambiente,
            self.chave,
            nfe,
        )
        if nfe.procNFe:
            procNFe = nfe.procNFe
            self.grava_xml(procNFe.NFe)
            self.grava_xml_autorizacao(procNFe)

            if self.modelo == MODELO_FISCAL_NFE:
                res = self.grava_pdf(nfe, procNFe.danfe_pdf)
            elif self.modelo == MODELO_FISCAL_NFCE:
                res = self.grava_pdf(nfe, procNFe.danfce_pdf)

            data_autorizacao = \
                consulta.resposta.protNFe.infProt.dhRecbto.valor
            data_autorizacao = UTC.normalize(data_autorizacao)

            self.data_hora_autorizacao = data_autorizacao
            self.protocolo_autorizacao = \
                consulta.resposta.protNFe.infProt.nProt.valor
            self.chave = \
                consulta.resposta.protNFe.infProt.chNFe.valor

    def _envia_documento(self):
        self.ensure_one()
        result = super(SpedDocumento, self)._envia_documento()
        if self.modelo not in (MODELO_FISCAL_NFCE, MODELO_FISCAL_NFE):
            return result

        processador = self.processador_nfe()

        #
        # A NFC-e deve ter data de emissão no máx. 5 minutos antes
        # da transmissão; por isso, definimos a hora de emissão aqui no
        # envio
        #
        if self.modelo == MODELO_FISCAL_NFCE:
            self.data_hora_emissao = fields.Datetime.now()
            self.data_hora_entrada_saida = self.data_hora_emissao

        nfe = self.monta_nfe(processador)

        if not self.tipo_emissao_nfe == TIPO_EMISSAO_NFE_NORMAL:
            processador.contingencia = True

        if self.modelo == MODELO_FISCAL_NFE:
            processador.danfe.NFe = nfe
            processador.danfe.salvar_arquivo = False
            processador.danfe.gerar_danfe()

            self.grava_pdf(nfe, processador.danfe.conteudo_pdf)

        elif self.modelo == MODELO_FISCAL_NFCE:
            processador.danfce.NFe = nfe
            processador.danfce.salvar_arquivo = False
            processador.danfce.gerar_danfce()
            self.grava_pdf(nfe, processador.danfce.conteudo_pdf)

        #
        # Envia a nota
        #
        processo = None
        for p in processador.processar_notas([nfe]):
            processo = p

        #
        # Se o último processo foi a consulta do status do serviço, significa
        # que ele não está online...
        #
        if processo.webservice == WS_NFE_SITUACAO:
            self.situacao_nfe = SITUACAO_NFE_EM_DIGITACAO
        #
        # Se o último processo foi a consulta da nota, significa que ela já
        # está emitida
        #
        elif processo.webservice == WS_NFE_CONSULTA:

            if processo.resposta.cStat.valor in ('100', '150'):
                self.chave = processo.resposta.chNFe.valor
                self.executa_antes_autorizar()
                self.situacao_nfe = SITUACAO_NFE_AUTORIZADA
                self.executa_depois_autorizar()

            elif processo.resposta.cStat.valor in ('110', '301', '302'):
                self.chave = processo.resposta.chNFe.valor
                self.executa_antes_denegar()
                self.situacao_fiscal = SITUACAO_FISCAL_DENEGADO
                self.situacao_nfe = SITUACAO_NFE_DENEGADA
                self.executa_depois_denegar()
            else:
                self.situacao_nfe = SITUACAO_NFE_EM_DIGITACAO
        #
        # Se o último processo foi o envio do lote, significa que a consulta
        # falhou, mas o envio não
        #
        elif processo.webservice == WS_NFE_ENVIO_LOTE:
            #
            # Lote recebido, vamos guardar o recibo
            #
            if processo.resposta.cStat.valor == '103':
                self.recibo = processo.resposta.infRec.nRec.valor
            else:
                mensagem = 'Código de retorno: ' + \
                           processo.resposta.cStat.valor
                mensagem += '\nMensagem: ' + \
                            processo.resposta.xMotivo.valor
                self.mensagem_nfe = mensagem
                self.situacao_nfe = SITUACAO_NFE_REJEITADA
        #
        # Se o último processo foi o retorno do recibo, a nota foi rejeitada,
        # denegada, autorizada, ou ainda não tem resposta
        #
        elif processo.webservice == WS_NFE_CONSULTA_RECIBO:
            #
            # Consulta ainda sem resposta, a nota ainda não foi processada
            #
            if processo.resposta.cStat.valor == '105':
                self.situacao_nfe = SITUACAO_NFE_ENVIADA
            #
            # Lote processado
            #
            elif processo.resposta.cStat.valor == '104':
                protNFe = processo.resposta.protNFe[0]

                #
                # Autorizada ou denegada
                #
                if protNFe.infProt.cStat.valor in ('100', '150', '110', '301',
                                                   '302'):
                    procNFe = processo.resposta.dic_procNFe[nfe.chave]
                    self.grava_xml(procNFe.NFe)
                    self.grava_xml_autorizacao(procNFe)

                    if self.modelo == MODELO_FISCAL_NFE:
                        res = self.grava_pdf(nfe, procNFe.danfe_pdf)
                    elif self.modelo == MODELO_FISCAL_NFCE:
                        res = self.grava_pdf(nfe, procNFe.danfce_pdf)

                    data_autorizacao = protNFe.infProt.dhRecbto.valor
                    data_autorizacao = UTC.normalize(data_autorizacao)

                    self.data_hora_autorizacao = data_autorizacao
                    self.protocolo_autorizacao = protNFe.infProt.nProt.valor
                    self.chave = protNFe.infProt.chNFe.valor

                    if protNFe.infProt.cStat.valor in ('100', '150'):
                        self.executa_antes_autorizar()
                        self.situacao_nfe = SITUACAO_NFE_AUTORIZADA
                        self.executa_depois_autorizar()
                    else:
                        self.executa_antes_denegar()
                        self.situacao_fiscal = SITUACAO_FISCAL_DENEGADO
                        self.situacao_nfe = SITUACAO_NFE_DENEGADA
                        self.executa_depois_denegar()

                else:
                    mensagem = 'Código de retorno: ' + \
                               protNFe.infProt.cStat.valor
                    mensagem += '\nMensagem: ' + \
                                protNFe.infProt.xMotivo.valor
                    self.mensagem_nfe = mensagem
                    self.situacao_nfe = SITUACAO_NFE_REJEITADA
            else:
                #
                # Rejeitada por outros motivos, falha no schema etc. etc.
                #
                mensagem = 'Código de retorno: ' + \
                           processo.resposta.cStat.valor
                mensagem += '\nMensagem: ' + \
                            processo.resposta.xMotivo.valor
                self.mensagem_nfe = mensagem
                self.situacao_nfe = SITUACAO_NFE_REJEITADA

    def cancela_nfe(self):
        self.ensure_one()
        res = super(SpedDocumento, self).cancela_nfe()
        if self.modelo not in (MODELO_FISCAL_NFCE, MODELO_FISCAL_NFE):
            return res

        processador = self.processador_nfe()

        xml = base64.b64decode(self.arquivo_xml_autorizacao_id.datas)
        xml = xml.decode('utf-8')

        procNFe = ClasseProcNFe()

        procNFe.xml = xml
        procNFe.NFe.monta_chave()

        evento = EventoCancNFe_100()
        evento.infEvento.tpAmb.valor = procNFe.NFe.infNFe.ide.tpAmb.valor
        evento.infEvento.cOrgao.valor = procNFe.NFe.chave[:2]
        evento.infEvento.CNPJ.valor = procNFe.NFe.infNFe.emit.CNPJ.valor
        evento.infEvento.chNFe.valor = procNFe.NFe.chave
        evento.infEvento.dhEvento.valor = agora()
        evento.infEvento.detEvento.nProt.valor = \
            procNFe.protNFe.infProt.nProt.valor
        evento.infEvento.detEvento.xJust.valor = self.justificativa or ''

        if processador.certificado:
            processador.certificado.assina_xmlnfe(evento)

        processador.salvar_arquivo = True
        processo = processador.enviar_lote_cancelamento(lista_eventos=[evento])

        #
        # O cancelamento foi aceito e vinculado à NF-e
        #
        if self.chave in processo.resposta.dic_procEvento:
            procevento = processo.resposta.dic_procEvento[self.chave]
            retevento = procevento.retEvento

            if retevento.infEvento.cStat.valor not in ('155', '135'):
                mensagem = 'Erro no cancelamento'
                mensagem += '\nCódigo: ' + retevento.infEvento.cStat.valor
                mensagem += '\nMotivo: ' + \
                            retevento.infEvento.xMotivo.valor
                raise UserError(mensagem)

            #
            # Grava o protocolo de cancelamento
            #
            self.grava_xml_cancelamento(self.chave, evento)
            self.grava_xml_autorizacao_cancelamento(self.chave, procevento)

            #
            # Regera o DANFE com a tarja de cancelamento
            #
            if self.modelo == MODELO_FISCAL_NFE:
                processador.danfe.NFe = procNFe.NFe
                processador.danfe.protNFe = procNFe.protNFe
                processador.danfe.procEventoCancNFe = procevento
                processador.danfe.salvar_arquivo = False
                processador.danfe.gerar_danfe()
                res = self.grava_pdf(procNFe.NFe,
                                     processador.danfe.conteudo_pdf)
                processador.danfe.NFe = ClasseNFe()
                processador.danfe.protNFe = None
                processador.danfe.procEventoCancNFe = None
            elif self.modelo == MODELO_FISCAL_NFCE:
                processador.danfce.NFe = procNFe.NFe
                processador.danfce.protNFe = procNFe.protNFe
                processador.danfce.procEventoCancNFe = procevento
                processador.danfce.salvar_arquivo = False
                processador.danfce.gerar_danfce()
                res = self.grava_pdf(procNFe.NFe,
                                     processador.danfce.conteudo_pdf)
                processador.danfce.NFe = ClasseNFCe()
                processador.danfce.protNFe = None
                processador.danfce.procEventoCancNFe = None

            data_cancelamento = retevento.infEvento.dhRegEvento.valor
            data_cancelamento = UTC.normalize(data_cancelamento)

            self.data_hora_cancelamento = data_cancelamento
            self.protocolo_cancelamento = \
                procevento.retEvento.infEvento.nProt.valor

            #
            # Cancelamento extemporâneo
            #
            self.executa_antes_cancelar()

            if procevento.retEvento.infEvento.cStat.valor == '155':
                self.situacao_fiscal = SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO
                self.situacao_nfe = SITUACAO_NFE_CANCELADA
            elif procevento.retEvento.infEvento.cStat.valor == '135':
                self.situacao_fiscal = SITUACAO_FISCAL_CANCELADO
                self.situacao_nfe = SITUACAO_NFE_CANCELADA

            self.executa_depois_cancelar()

    def inutiliza_nfe(self):
        super(SpedDocumento, self).inutiliza_nfe()
        self.ensure_one()

        processador = self.processador_nfe()

        cnpj = limpa_formatacao(self.empresa_id.cnpj_cpf)
        serie = str(self.serie or '')
        numero = int(self.numero)
        motivo = self.justificativa or \
                 'AVANÇO ACIDENTAL NO CONTROLE DE NUMERAÇÃO NO SISTEMA'

        processo = processador.inutilizar_nota(cnpj=cnpj, serie=serie,
                                               numero_inicial=numero,
                                               justificativa=motivo)

        retInut = processo.resposta

        if retInut.infInut.cStat.valor != '102':
            #
            # Inutilização rejeitada, falha no schema etc. etc.
            #
            mensagem = 'Código de retorno: ' + retInut.infInut.cStat.valor
            mensagem += '\nMensagem: ' + retInut.infInut.xMotivo.valor
            self.mensagem_nfe = mensagem
            self.situacao_nfe = SITUACAO_NFE_REJEITADA

        else:
            procInut = processo.processo_inutilizacao_nfe

            self.chave = processo.envio.chave
            self.grava_xml_inutilizacao(self.chave, procInut.inutNFe)
            self.grava_xml_autorizacao_inutilizacao(self.chave, procInut)

            data_inutilizacao = retInut.infInut.dhRecbto.valor
            data_inutilizacao = UTC.normalize(data_inutilizacao)

            self.data_hora_inutilizacao = data_inutilizacao
            self.protocolo_inutilizacao = retInut.infInut.nProt.valor

            self.executa_antes_inutilizar()
            self.situacao_fiscal = SITUACAO_FISCAL_INUTILIZADO
            self.situacao_nfe = SITUACAO_NFE_INUTILIZADA
            self.executa_depois_inutilizar()

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

    def executa_antes_cancelar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de autorizar uma NF-e;
        # não confundir com o método _compute_permite_cancelamento, que indica
        # se o botão de cancelamento vai estar disponível para o usuário na
        # interface
        #
        super(SpedDocumento, self).executa_antes_cancelar()

    def executa_depois_cancelar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de cancelar uma NF-e,
        # por exemplo, excluir lançamentos financeiros, movimentações de
        # estoque etc.
        #
        super(SpedDocumento, self).executa_depois_cancelar()
        self.ensure_one()

        if self.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
            super(SpedDocumento, self)._compute_permite_cancelamento()
            return

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            super(SpedDocumento, self)._compute_permite_cancelamento()
            return
        #
        # Deletar operacao subsequente
        #
        if self.documento_subsequente_ids:
            documento_subsequente = self.env['sped.documento'] \
                .browse(self.documento_subsequente_ids \
                        .documento_subsequente_id.id)
            documento_subsequente.unlink()


        #
        # Envia o email da nota para o cliente
        #
        mail_template = None
        if self.modelo == MODELO_FISCAL_NFE and \
                self.empresa_id.mail_template_nfe_cancelada_id:
            mail_template = \
                self.empresa_id.mail_template_nfe_cancelada_id
        elif self.modelo == MODELO_FISCAL_NFCE and \
                self.empresa_id.mail_template_nfce_cancelada_id:
            mail_template = \
                self.empresa_id.mail_template_nfce_cancelada_id

        if mail_template is None:
            return

        self.envia_email(mail_template)

    def executa_antes_inutilizar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de inutilizar uma NF-e
        #
        super(SpedDocumento, self).executa_antes_inutilizar()

    def executa_depois_inutilizar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de inutilizar uma NF-e,
        # por exemplo, invalidar pedidos de venda e movimentações de estoque
        # etc.
        #
        super(SpedDocumento, self).executa_depois_inutilizar()
        self.ensure_one()

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

    @job
    def _envia_email(self, mail_template):
        mail_template.send_mail(self.id)

    def envia_email(self, mail_template):
        self.ensure_one()
        self._envia_email(mail_template)

    def envia_email_nfe(self):
        self.ensure_one()

        if self.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
            return

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return

        mail_template = None

        if self.situacao_nfe == SITUACAO_NFE_CANCELADA:
            if self.modelo == MODELO_FISCAL_NFE and \
                    self.empresa_id.mail_template_nfe_cancelada_id:
                mail_template = self.empresa_id.mail_template_nfe_cancelada_id
            elif self.modelo == MODELO_FISCAL_NFCE and \
                    self.empresa_id.mail_template_nfce_cancelada_id:
                mail_template = self.empresa_id.mail_template_nfce_cancelada_id

        elif self.situacao_nfe == SITUACAO_NFE_DENEGADA:
            if self.modelo == MODELO_FISCAL_NFE and \
                    self.empresa_id.mail_template_nfe_denegada_id:
                mail_template = self.empresa_id.mail_template_nfe_denegada_id
            elif self.modelo == MODELO_FISCAL_NFCE and \
                    self.empresa_id.mail_template_nfce_denegada_id:
                mail_template = self.empresa_id.mail_template_nfce_denegada_id
        else:
            if self.operacao_id.mail_template_id:
                mail_template_id = self.operacao_id.mail_template_id
            elif self.modelo == MODELO_FISCAL_NFE and \
                    self.empresa_id.mail_template_nfe_autorizada_id:
                mail_template = self.empresa_id.mail_template_nfe_autorizada_id
            elif self.modelo == MODELO_FISCAL_NFCE and \
                    self.empresa_id.mail_template_nfce_autorizada_id:
                mail_template = \
                    self.empresa_id.mail_template_nfce_autorizada_id

        if mail_template is None:
            raise UserError('Não foi possível determinar o modelo de email '
                            'para o envio!')

        self.envia_email(mail_template)

    def gera_pdf(self):
        output = PdfFileWriter()
        s = StringIO()
        path = ''

        for record in self:
            if record.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
                return super(SpedDocumento, self).gera_pdf()

            if record.emissao != TIPO_EMISSAO_PROPRIA:
                return

            processador = record.processador_nfe()

            procNFe = ClasseProcNFe()
            if record.arquivo_xml_autorizacao_id:
                xml = base64.b64decode(record.arquivo_xml_autorizacao_id.datas)
                procNFe.xml = xml.decode('utf-8')
                procNFe.NFe.chave = procNFe.NFe.infNFe.Id.valor[3:]
            else:
                procNFe.NFe = record.monta_nfe()
                procNFe.NFe.gera_nova_chave()
                procNFe.NFe.monta_chave()

            procevento = ProcEventoCancNFe_100()
            if record.arquivo_xml_autorizacao_cancelamento_id:
                xml = base64.b64decode(
                    record.arquivo_xml_autorizacao_cancelamento_id.datas)

                procevento.xml = xml.decode('utf-8')

            #
            # Gera o DANFE, com a tarja de cancelamento quando necessário
            #
            if record.modelo == MODELO_FISCAL_NFE:
                processador.danfe.NFe = procNFe.NFe

                if record.arquivo_xml_autorizacao_id:
                    processador.danfe.protNFe = procNFe.protNFe

                if record.arquivo_xml_autorizacao_cancelamento_id:
                    processador.danfe.procEventoCancNFe = procevento

                processador.danfe.salvar_arquivo = True
                processador.danfe.caminho = "/tmp/"
                processador.danfe.gerar_danfe()
                path = processador.danfe.caminho + \
                       processador.danfe.NFe.chave + '.pdf'

                processador.danfe.NFe = ClasseNFe()
                processador.danfe.protNFe = None
                processador.danfe.procEventoCancNFe = None

            elif record.modelo == MODELO_FISCAL_NFCE:
                processador.danfce.NFe = procNFe.NFe

                if record.arquivo_xml_autorizacao_id:
                    processador.danfce.protNFe = procNFe.protNFe

                if record.arquivo_xml_autorizacao_cancelamento_id:
                    processador.danfce.procEventoCancNFe = procevento

                processador.danfce.salvar_arquivo = True

                processador.danfce.salvar_arquivo = True
                processador.danfce.caminho = "/tmp/"
                processador.danfce.gerar_danfe()
                path = processador.danfce.caminho + \
                       processador.danfce.NFe.chave + '.pdf'

            pdf = PdfFileReader(file(path, "rb"))
            for i in range(pdf.getNumPages()):
                output.addPage(pdf.getPage(i))
            output.write(s)

        str_pdf = s.getvalue()
        s.close()
        return str_pdf

    def gera_xml(self):

        self.ensure_one()
        res = None

        if self.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
            return

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return

        if self.arquivo_xml_autorizacao_id:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/{id}/{nome}'.format(
                    id=self.arquivo_xml_autorizacao_id.id,
                    nome=self.arquivo_xml_autorizacao_id.name),
                'target': 'new',
            }

        procNFe = ClasseProcNFe()
        procNFe.NFe = self.monta_nfe()
        procNFe.NFe.gera_nova_chave()
        procNFe.NFe.monta_chave()
        return self.grava_xml(procNFe.NFe)

    @api.onchange('empresa_id', 'modelo', 'emissao', 'serie', 'ambiente_nfe')
    def _onchange_serie(self):
        res = super(SpedDocumento, self)._onchange_serie()
        _logger.info(res)

        if not res['value']:
            return res

        tipo_documento_inutilizado = self.env[
            'sped.inutilizacao.tipo.documento'
        ].search([('codigo', '=', self.modelo)])
        faixa_inutilizada = self.env['sped.inutilizacao.documento'].search([
            ('empresa_id', '=', self.empresa_id.id),
            ('tipo_documento_inutilizacao_id', '=', tipo_documento_inutilizado.id),
            ('serie_documento', '=', res['value']['serie']),
            ('inicio_numeracao', '<=', res['value']['numero']),
            ('fim_numeracao', '>=', res['value']['numero'])
        ], limit=1, order='fim_numeracao desc')

        if faixa_inutilizada:
            res['value']['numero'] = faixa_inutilizada.fim_numeracao + 1

        return res
