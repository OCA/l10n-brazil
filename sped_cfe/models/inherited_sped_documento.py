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
from odoo.exceptions import UserError

from odoo.addons.l10n_br_base.constante_tributaria import *

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
        conteudo = cfe.documento().encode('utf-8')
        self.arquivo_xml_id = False
        self.arquivo_xml_id = self._grava_anexo(nome_arquivo, conteudo).id

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
        cnpj_software_house, assinatura, numero_caixa = self._monta_cfe_identificacao()

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

        return cfe_venda

    def _monta_cfe_identificacao(self):
        # FIXME: Buscar dados do cadastro da empresa / cadastro do caixa
        cnpj_software_house = '16716114000172'
        assinatura = 'SGR-SAT SISTEMA DE GESTAO E RETAGUARDA DO SAT'
        numero_caixa = int(2),
        return cnpj_software_house, assinatura, numero_caixa

    def _monta_cfe_emitente(self):
        empresa = self.empresa_id

        emitente = Emitente(
                CNPJ=limpa_formatacao(empresa.cnpj_cpf),
                IE=limpa_formatacao(empresa.ie or ''),
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

    def envia_nfe(self):
        #FIXME: Este super deveria ser chamado mas retornar para manter a compatibilidade entre os módulos
        # super(SpedDocumento, self).envia_nfe()

        self.ensure_one()

        # TODO: Conectar corretamente no SAT
        # cliente = self.processador_cfe()

        # FIXME: Datas
        # # A NFC-e deve ter data de emissão no máx. 5 minutos antes
        # # da transmissão; por isso, definimos a hora de emissão aqui no
        # # envio
        # #
        # if self.modelo == MODELO_FISCAL_CFE:
        #     self.data_hora_emissao = fields.Datetime.now()
        #     self.data_hora_entrada_saida = self.data_hora_emissao

        cfe = self.monta_cfe()

        self.grava_cfe(cfe)
