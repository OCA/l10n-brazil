# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
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
    state_nfe = fields.Selection(
        selection=SITUACAO_NFE,
        string='Situação NF-e',
        default=SITUACAO_NFE_EM_DIGITACAO,
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

    @api.depends('modelo', 'emissao', 'state_nfe')
    def _compute_permite_alteracao(self):
        for documento in self:
            if documento.modelo not in (MODELO_FISCAL_NFE,
                                        MODELO_FISCAL_NFCE):
                super(SpedDocumento, documento)._compute_permite_alteracao()
                continue

            if documento.emissao != TIPO_EMISSAO_PROPRIA:
                super(SpedDocumento, documento)._compute_permite_alteracao()
                continue

            #
            # É emissão própria de NF-e ou NFC-e, permite alteração
            # somente quando estiver em digitação ou rejeitada
            #
            documento.permite_alteracao = \
                documento.state_nfe in (SITUACAO_NFE_EM_DIGITACAO,
                                        SITUACAO_NFE_REJEITADA)

    def _check_permite_alteracao(self, operacao='create', dados={}):
        CAMPOS_PERMITIDOS = [
            'justificativa',
            'arquivo_xml_cancelamento_id',
            'arquivo_xml_autorizacao_cancelamento_id',
            'data_hora_cancelamento',
            'protocolo_cancelamento',
            'arquivo_pdf_id',
            'situacao_fiscal',
            'state_nfe',
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
            if documento.state_nfe == SITUACAO_NFE_AUTORIZADA:
                for campo in CAMPOS_PERMITIDOS:
                    if campo in dados:
                        permite_alteracao = True
                        break

            if permite_alteracao:
                continue

            super(SpedDocumento, documento)._check_permite_alteracao(
                operacao,
                dados,
            )

    @api.depends('data_hora_autorizacao', 'modelo', 'emissao', 'justificativa',
                 'state_nfe')
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
            if documento.modelo not in (MODELO_FISCAL_NFE,
                                        MODELO_FISCAL_NFCE):
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

                if documento.state_nfe == SITUACAO_NFE_AUTORIZADA and \
                    tempo_autorizado.days < 1:
                    documento.permite_cancelamento = True

    def processador_nfe(self):
        self.ensure_one()

        if self.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
            raise UserError('Tentando processar um documento que não é uma'
                            'NF-e nem uma NFC-e!')

        processador = self.empresa_id.processador_nfe()
        processador.ambiente = int(self.ambiente_nfe or
                                   AMBIENTE_NFE_HOMOLOGACAO)
        processador.modelo = self.modelo

        if self.modelo == MODELO_FISCAL_NFE:
            if self.empresa_id.logo_danfe:
                processador.danfe.logo = ''
            processador.danfe.nome_sistema = 'Odoo 10.0'
            processador.caminho = os.path.join(
                self.empresa_id.caminho_sped,
                'nfe',
            )

        elif self.modelo == MODELO_FISCAL_NFCE:
            if self.empresa_id.logo_danfce:
                processador.danfce.logo = ''
            processador.danfce.nome_sistema = 'Odoo 10.0'
            processador.caminho = os.path.join(
                self.empresa_id.caminho_sped,
                'nfce',
            )

        return processador

    def _grava_anexo(self, nome_arquivo='', conteudo='',
                     tipo='application/xml'):
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

    def grava_xml(self, nfe):
        nome_arquivo = nfe.chave + '-nfe.xml'
        conteudo = nfe.xml.encode('utf-8')
        self.arquivo_xml_id = False
        self.arquivo_xml_id = self._grava_anexo(nome_arquivo, conteudo).id

    def grava_pdf(self, nfe, danfe_pdf):
        nome_arquivo = nfe.chave + '.pdf'
        conteudo = danfe_pdf
        self.arquivo_pdf_id = False
        self.arquivo_pdf_id = self._grava_anexo(nome_arquivo, conteudo,
                                                tipo='application/pdf').id

    def grava_xml_autorizacao(self, procNFe):
        nome_arquivo = procNFe.NFe.chave + '-proc-nfe.xml'
        conteudo = procNFe.xml.encode('utf-8')
        self.arquivo_xml_autorizacao_id = False
        self.arquivo_xml_autorizacao_id = \
            self._grava_anexo(nome_arquivo, conteudo).id

    def grava_xml_cancelamento(self, chave, canc):
        nome_arquivo = chave + '-01-can.xml'
        conteudo = canc.xml.encode('utf-8')
        self.arquivo_xml_cancelamento_id = False
        self.arquivo_xml_cancelamento_id = \
            self._grava_anexo(nome_arquivo, conteudo).id

    def grava_xml_autorizacao_cancelamento(self, chave, canc):
        nome_arquivo = chave + '-01-proc-can.xml'
        conteudo = canc.xml.encode('utf-8')
        self.arquivo_xml_autorizacao_cancelamento_id = False
        self.arquivo_xml_autorizacao_cancelamento_id = \
            self._grava_anexo(nome_arquivo, conteudo).id

    def monta_nfe(self, processador=None):
        self.ensure_one()

        if self.modelo == MODELO_FISCAL_NFE:
            nfe = NFe_310()
        elif self.modelo == MODELO_FISCAL_NFCE:
            nfe = NFCe_310()
        else:
            return

        #
        # Identificação da NF-e
        #
        self._monta_nfe_identificacao(nfe.infNFe.ide)

        #
        # Notas referenciadas
        #
        for doc_ref in self.documento_referenciado_ids:
            nfe.infNFe.ide.NFref.append(docref.monta_nfe())

        #
        # Emitente
        #
        self._monta_nfe_emitente(nfe.infNFe.emit)

        #
        # Destinatário
        #
        self._monta_nfe_destinatario(nfe.infNFe.dest)

        #
        # Endereço de entrega e retirada
        #
        self._monta_nfe_endereco_retirada(nfe.infNFe.retirada)
        self._monta_nfe_endereco_entrega(nfe.infNFe.entrega)

        #
        # Itens
        #
        i = 1
        for item in self.item_ids:
            nfe.infNFe.det.append(item.monta_nfe(i, nfe))
            i += 1

        #
        # Transporte e frete
        #
        self._monta_nfe_transporte(nfe.infNFe.transp)

        #
        # Duplicatas e pagamentos
        #
        self._monta_nfe_cobranca(nfe.infNFe.cobr)
        self._monta_nfe_pagamentos(nfe.infNFe.pag)

        #
        # Totais
        #
        self._monta_nfe_total(nfe.infNFe.total)

        #
        # Informações adicionais
        #
        self._monta_nfe_informacao_complementar(nfe)
        self._monta_nfe_informacao_fisco(nfe)

        nfe.gera_nova_chave()
        nfe.monta_chave()

        if self.empresa_id.certificado_id:
            certificado = self.empresa_id.certificado_id.certificado_nfe()
            certificado.assina_xmlnfe(nfe)

        return nfe

    def _monta_nfe_identificacao(self, ide):
        empresa = self.empresa_id
        participante = self.participante_id

        ide.tpAmb.valor = int(self.ambiente_nfe)
        ide.tpNF.valor = int(self.entrada_saida)
        ide.cUF.valor = UF_CODIGO[empresa.estado]
        ide.natOp.valor = self.natureza_operacao_id.nome
        ide.indPag.valor = int(self.ind_forma_pagamento)
        ide.serie.valor = self.serie
        ide.nNF.valor = str(D(self.numero).quantize(D('1')))

        #
        # Tratamento das datas de UTC para o horário de brasília
        #
        ide.dhEmi.valor = data_hora_horario_brasilia(
            parse_datetime(self.data_hora_emissao + ' GMT')
        )
        ide.dEmi.valor = ide.dhEmi.valor

        if self.data_hora_entrada_saida:
            ide.dhSaiEnt.valor = data_hora_horario_brasilia(
                parse_datetime(self.data_hora_entrada_saida + ' GMT')
            )
        else:
            nfe.infNFe.ide.dhSaiEnt.valor = data_hora_horario_brasilia(
                parse_datetime(self.data_hora_emissao + ' GMT')
            )

        ide.dSaiEnt.valor = ide.dhSaiEnt.valor
        ide.hSaiEnt.valor = ide.dhSaiEnt.valor

        ide.cMunFG.valor = empresa.municipio_id.codigo_ibge[:7]
        # ide.tpImp.valor = 1  # DANFE em retrato
        ide.tpEmis.valor = self.tipo_emissao_nfe
        ide.finNFe.valor = self.finalidade_nfe
        ide.procEmi.valor = 0  # Emissão por aplicativo próprio
        ide.verProc.valor = 'Odoo 10.0'
        ide.indPres.valor = self.presenca_comprador

        #
        # NFC-e é sempre emissão para dentro do estado
        # e sempre para consumidor final
        #
        if self.modelo == MODELO_FISCAL_NFCE:
            ide.idDest.valor = IDENTIFICACAO_DESTINO_INTERNO
            ide.indFinal.valor = TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL

        else:
            if participante.estado == 'EX':
                ide.idDest.valor = IDENTIFICACAO_DESTINO_EXTERIOR
            elif participante.estado == empresa.estado:
                ide.idDest.valor = IDENTIFICACAO_DESTINO_INTERNO
            else:
                ide.idDest.valor = IDENTIFICACAO_DESTINO_INTERESTADUAL

            if (self.consumidor_final) or \
                (participante.contribuinte ==
                    INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE):
                ide.indFinal.valor = TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL

    def _le_nfe(self, ide):
        dados = {}
        dados['ambiente_nfe'] = str(ide.tpAmb.valor)
        dados['entrada_saida'] = ide.tpNF.valor
        dados['natureza_operacao_original'] = ide.natOp.valor
        dados['ind_forma_pagamento'] = str(ide.indPag.valor)
        dados['serie'] = ide.serie.valor
        dados['numero'] = ide.nNF.valor
        dados['data_hora_emissao'] = ide.dhEmi.valor
        dados['data_hora_entrada_saida'] = ide.dhSaiEnt.valor
        #
        # Código do município do fato gerador
        #
        municipio = self.env['sped.municipio'].search(
            [('codigo_ibge', '=', ide.cMunFG.valor + '0000')]
        )
        if municipio:
            dados['municipio_fato_gerador_id'] = municipio.id
        dados['tipo_emissao_nfe'] = ide.tpEmis.valor
        dados['finalidade_nfe'] = ide.finNFe.valor
        dados['presenca_comprador'] = ide.indPres.valor
        dados['consumidor_final'] = ide.indFinal.valor
        return dados

    def _monta_nfe_emitente(self, emit):
        empresa = self.empresa_id

        emit.CNPJ.valor = limpa_formatacao(empresa.cnpj_cpf)
        emit.xNome.valor = empresa.razao_social
        emit.xFant.valor = empresa.fantasia or ''
        emit.enderEmit.xLgr.valor = empresa.endereco
        emit.enderEmit.nro.valor = empresa.numero
        emit.enderEmit.xCpl.valor = empresa.complemento or ''
        emit.enderEmit.xBairro.valor = empresa.bairro
        emit.enderEmit.cMun.valor = empresa.municipio_id.codigo_ibge[:7]
        emit.enderEmit.xMun.valor = empresa.cidade
        emit.enderEmit.UF.valor = empresa.estado
        emit.enderEmit.CEP.valor = limpa_formatacao(empresa.cep)
        # emit.enderEmit.cPais.valor = '1058'
        # emit.enderEmit.xPais.valor = 'Brasil'
        emit.enderEmit.fone.valor = limpa_formatacao(empresa.fone or '')
        emit.IE.valor = limpa_formatacao(empresa.ie or '')
        #
        # Usa o regime tributário da NF e não da empresa, e trata o código
        # interno 3.1 para o lucro real, que na NF deve ir somente 3
        #
        emit.CRT.valor = self.regime_tributario[0]

        if self.modelo == MODELO_FISCAL_NFCE:
            emit.csc.id = empresa.csc_id or 1
            emit.csc.codigo = empresa.csc_codigo or ''
            # emit.csc.codigo = emit.csc.codigo.strip()

    def _monta_nfe_destinatario(self, dest):
        participante = self.participante_id

        #
        # Para a NFC-e, o destinatário é sempre não contribuinte
        #
        if self.modelo == MODELO_FISCAL_NFCE:
            dest.indIEDest.valor = INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE

        else:
            dest.indIEDest.valor = participante.contribuinte

            if participante.contribuinte == \
                    INDICADOR_IE_DESTINATARIO_CONTRIBUINTE:
                dest.IE.valor = limpa_formatacao(participante.ie or '')

        #
        # Trata a possibilidade de ausência do destinatário na NFC-e
        #
        if self.modelo == MODELO_FISCAL_NFCE and not participante.cnpj_cpf:
            return

        #
        # Participantes estrangeiros tem a ID de estrangeiro sempre começando
        # com EX
        #
        if participante.cnpj_cpf.startswith('EX'):
            dest.idEstrangeiro.valor = \
                limpa_formatacao(participante.cnpj_cpf or '')

        elif len(participante.cnpj_cpf or '') == 14:
            dest.CPF.valor = limpa_formatacao(participante.cnpj_cpf)

        elif len(participante.cnpj_cpf or '') == 18:
            dest.CNPJ.valor = limpa_formatacao(participante.cnpj_cpf)

        if self.ambiente_nfe == AMBIENTE_NFE_HOMOLOGACAO:
            dest.xNome.valor = 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - ' \
                               'SEM VALOR FISCAL'
        else:
            dest.xNome.valor = participante.razao_social or ''

        #
        # Para a NFC-e, o endereço do participante pode não ter sido
        # preenchido
        #
        dest.enderDest.xLgr.valor = participante.endereco or ''
        dest.enderDest.nro.valor = participante.numero or ''
        dest.enderDest.xCpl.valor = participante.complemento or ''
        dest.enderDest.xBairro.valor = participante.bairro or ''

        if not participante.cnpj_cpf.startswith('EX'):
            dest.enderDest.CEP.valor = limpa_formatacao(participante.cep)
        else:
            dest.enderDest.CEP.valor = '99999999'

        #
        # Pode haver cadastro de participante sem município para NFC-e
        #
        if participante.municipio_id:
            dest.enderDest.cMun.valor = \
                participante.municipio_id.codigo_ibge[:7]
            dest.enderDest.xMun.valor = participante.cidade
            dest.enderDest.UF.valor = participante.estado

            if participante.cnpj_cpf.startswith('EX'):
                dest.enderDest.cPais.valor = \
                    participante.municipio_id.pais_id.codigo_bacen
                dest.enderDest.xPais.valor = \
                    participante.municipio_id.pais_id.nome

        dest.enderDest.fone.valor = limpa_formatacao(participante.fone or '')
        email_dest = participante.email_nfe or ''
        dest.email.valor = email_dest[:60]

    def _monta_nfe_endereco_retirada(self, retirada):
        return
        if not self.endereco_retirada_id:
            return

        retirada.xLgr.valor = self.endereco_retirada_id.endereco or ''
        retirada.nro.valor = self.endereco_retirada_id.numero or ''
        retirada.xCpl.valor = self.endereco_retirada_id.complemento or ''
        retirada.xBairro.valor = self.endereco_retirada_id.bairro or ''
        retirada.cMun.valor = \
            self.endereco_retirada_id.municipio_id.codigo_ibge[:7]
        retirada.xMun.valor = self.endereco_retirada_id.municipio_id.nome
        retirada.UF.valor = self.endereco_retirada_id.municipio_id.estado_id.uf

        if self.endereco_retirada_id.cpf:
            if len(self.endereco_retirada_id.cpf) == 18:
                retirada.CNPJ.valor = \
                    limpa_formatacao(self.endereco_retirada_id.cpf)
            else:
                retirada.CPF.valor = \
                    limpa_formatacao(self.endereco_retirada_id.cpf)

    def _monta_nfe_endereco_entrega(self, entrega):
        return
        if not self.endereco_entrega_id:
            return

        entrega.xLgr.valor = self.endereco_entrega_id.endereco or ''
        entrega.nro.valor = self.endereco_entrega_id.numero or ''
        entrega.xCpl.valor = self.endereco_entrega_id.complemento or ''
        entrega.xBairro.valor = self.endereco_entrega_id.bairro or ''
        entrega.cMun.valor = \
            self.endereco_entrega_id.municipio_id.codigo_ibge[:7]
        entrega.xMun.valor = self.endereco_entrega_id.municipio_id.nome
        entrega.UF.valor = self.endereco_entrega_id.municipio_id.estado_id.uf

        if self.endereco_entrega_id.cnpj_cpf:
            if len(self.endereco_entrega_id.cnpj_cpf) == 18:
                entrega.CNPJ.valor = \
                    limpa_formatacao(self.endereco_entrega_id.cnpj_cpf)
            else:
                entrega.CPF.valor = \
                    limpa_formatacao(self.endereco_entrega_id.cnpj_cpf)

    def _monta_nfe_transporte(self, transp):
        if self.modelo != MODELO_FISCAL_NFE:
            return
        #
        # Temporário até o início da NF-e 4.00
        #
        if self.modalidade_frete == MODALIDADE_FRETE_REMETENTE_PROPRIO:
            transp.modFrete.valor = MODALIDADE_FRETE_REMETENTE_CIF
        elif self.modalidade_frete == MODALIDADE_FRETE_DESTINATARIO_PROPRIO:
            transp.modFrete.valor = MODALIDADE_FRETE_DESTINATARIO_FOB
        else:
            transp.modFrete.valor = \
                self.modalidade_frete or MODALIDADE_FRETE_SEM_FRETE

        if self.transportadora_id:
            if len(self.transportadora_id.cnpj_cpf) == 14:
                transp.transporta.CPF.valor = \
                    limpa_formatacao(self.transportadora_id.cnpj_cpf)
            else:
                transp.transporta.CNPJ.valor = \
                    limpa_formatacao(self.transportadora_id.cnpj_cpf)

            transp.transporta.xNome.valor = \
                self.transportadora_id.razao_social or ''
            transp.transporta.IE.valor = \
                limpa_formatacao(self.transportadora_id.ie or 'ISENTO')
            ender = self.transportadora_id.endereco or ''
            ender += ' '
            ender += self.transportadora_id.numero or ''
            ender += ' '
            ender += self.transportadora_id.complemento or ''
            transp.transporta.xEnder.valor = ender.strip()
            transp.transporta.xMun.valor = self.transportadora_id.cidade or ''
            transp.transporta.UF.valor = self.transportadora_id.estado or ''

        if self.veiculo_id:
            transp.veicTransp.placa.valor = self.veiculo_id.placa or ''
            transp.veicTransp.UF.valor = self.veiculo_id.estado_id.uf or ''
            transp.veicTransp.RNTC.valor = self.veiculo_id.rntrc or ''

        transp.reboque = []
        if self.reboque_1_id:
            reb = Reboque_310()
            reb.placa.valor = self.reboque_1_id.placa or ''
            reb.UF.valor = self.reboque_1_id.estado_id.uf or ''
            reb.RNTC.valor = self.reboque_1_id.rntrc or ''
            transp.reboque.append(reb)
        if self.reboque_2_id:
            reb = Reboque_310()
            reb.placa.valor = self.reboque_2_id.placa or ''
            reb.UF.valor = self.reboque_2_id.estado_id.uf or ''
            reb.RNTC.valor = self.reboque_2_id.rntrc or ''
            transp.reboque.append(reb)
        if self.reboque_3_id:
            reb = Reboque_310()
            reb.placa.valor = self.reboque_3_id.placa or ''
            reb.UF.valor = self.reboque_3_id.estado_id.uf or ''
            reb.RNTC.valor = self.reboque_3_id.rntrc or ''
            transp.reboque.append(reb)
        if self.reboque_4_id:
            reb = Reboque_310()
            reb.placa.valor = self.reboque_4_id.placa or ''
            reb.UF.valor = self.reboque_4_id.estado_id.uf or ''
            reb.RNTC.valor = self.reboque_4_id.rntrc or ''
            transp.reboque.append(reb)
        if self.reboque_5_id:
            reb = Reboque_310()
            reb.placa.valor = self.reboque_5_id.placa or ''
            reb.UF.valor = self.reboque_5_id.estado_id.uf or ''
            reb.RNTC.valor = self.reboque_5_id.rntrc or ''
            transp.reboque.append(reb)

        #
        # Volumes
        #
        transp.vol = []
        for volume in self.volume_ids:
            transp.vol.append(volume.monta_nfe())

    def _monta_nfe_cobranca(self, cobr):
        if self.modelo != MODELO_FISCAL_NFE:
            return

        if self.ind_forma_pagamento not in \
                (IND_FORMA_PAGAMENTO_A_VISTA, IND_FORMA_PAGAMENTO_A_PRAZO):
            return
        cobr.fat.nFat.valor = formata_valor(self.numero, casas_decimais=0)
        cobr.fat.vOrig.valor = str(D(self.vr_operacao))
        cobr.fat.vDesc.valor = str(D(self.vr_desconto))
        cobr.fat.vLiq.valor = str(D(self.vr_fatura))

        for duplicata in self.duplicata_ids:
            cobr.dup.append(duplicata.monta_nfe())

    def _monta_nfe_pagamentos(self, pag):
        if self.modelo != MODELO_FISCAL_NFCE:
            return

        for pagamento in self.pagamento_ids:
            pag.append(pagamento.monta_nfe())

    def _monta_nfe_total(self, total):
        total.ICMSTot.vBC.valor = str(D(self.bc_icms_proprio))
        total.ICMSTot.vICMS.valor = str(D(self.vr_icms_proprio))
        total.ICMSTot.vICMSDeson.valor = str(D('0'))
        total.ICMSTot.vFCPUFDest.valor = str(D(self.vr_fcp))
        total.ICMSTot.vICMSUFDest.valor = str(D(self.vr_icms_estado_destino))
        total.ICMSTot.vICMSUFRemet.valor = str(D(self.vr_icms_estado_origem))
        total.ICMSTot.vBCST.valor = str(D(self.bc_icms_st))
        total.ICMSTot.vST.valor = str(D(self.vr_icms_st))
        total.ICMSTot.vProd.valor = str(D(self.vr_produtos))
        total.ICMSTot.vFrete.valor = str(D(self.vr_frete))
        total.ICMSTot.vSeg.valor = str(D(self.vr_seguro))
        total.ICMSTot.vDesc.valor = str(D(self.vr_desconto))
        total.ICMSTot.vII.valor = str(D(self.vr_ii))
        total.ICMSTot.vIPI.valor = str(D(self.vr_ipi))
        total.ICMSTot.vPIS.valor = str(D(self.vr_pis_proprio))
        total.ICMSTot.vCOFINS.valor = str(D(self.vr_cofins_proprio))
        total.ICMSTot.vOutro.valor = str(D(self.vr_outras))
        total.ICMSTot.vNF.valor = str(D(self.vr_nf))
        total.ICMSTot.vTotTrib.valor = str(D(self.vr_ibpt or 0))

    def _monta_nfe_informacao_complementar(self, nfe):
        infcomplementar = self.infcomplementar or ''

        dados_infcomplementar = {
            'nf': self,
        }

        #
        # Crédito de ICMS do SIMPLES
        #
        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES and \
            self.vr_icms_sn:
            if len(infcomplementar) > 0:
                infcomplementar += '\n'

            infcomplementar += 'Permite o aproveitamento de crédito de ' + \
                'ICMS no valor de R$ ${formata_valor(nf.vr_icms_sn)},' + \
                ' nos termos do art. 23 da LC 123/2006;'

        #
        # Valor do IBPT
        #
        if self.vr_ibpt:
            if len(infcomplementar) > 0:
                infcomplementar += '\n'

            infcomplementar += 'Valor aproximado dos tributos: ' + \
                'R$ ${formata_valor(nf.vr_ibpt)} - fonte: IBPT;'

        #
        # ICMS para UF de destino
        #
        if nfe.infNFe.ide.idDest.valor == \
            IDENTIFICACAO_DESTINO_INTERESTADUAL and \
            nfe.infNFe.ide.indFinal.valor == \
            TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL and \
            nfe.infNFe.dest.indIEDest.valor == \
            INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE:

            if len(infcomplementar) > 0:
                infcomplementar += '\n'

            infcomplementar += \
                'Partilha do ICMS de R$ ' + \
                '${formata_valor(nf.vr_icms_proprio)}% recolhida ' + \
                'conf. EC 87/2015: ' + \
                'R$ ${formata_valor(nf.vr_icms_estado_destino)} para o ' + \
                'estado de ${nf.participante_id.estado} e ' + \
                'R$ ${formata_valor(nf.vr_icms_estado_origem)} para o ' + \
                'estado de ${nf.empresa_id.estado}; Valor do diferencial ' + \
                'de alíquota: ' + \
                'R$ ${formata_valor(nf.vr_difal)};'

            if self.vr_fcp:
                infcomplementar += ' Fundo de combate à pobreza: R$ ' + \
                    '${formata_valor(nf.vr_fcp)}'

        #
        # Aplica um template na observação
        #
        template = TemplateBrasil(infcomplementar.encode('utf-8'))
        infcomplementar = template.render(**dados_infcomplementar)
        nfe.infNFe.infAdic.infCpl.valor = infcomplementar.decode('utf-8')

    def _monta_nfe_informacao_fisco(self, nfe):
        infadfisco = self.infadfisco or ''

        dados_infadfisco = {
            'nf': self,
        }

        #
        # Aplica um template na observação
        #
        template = TemplateBrasil(infadfisco.encode('utf-8'))
        infadfisco = template.render(**dados_infadfisco)
        nfe.infNFe.infAdic.infAdFisco.valor = infadfisco.decode('utf-8')

    def envia_nfe(self):
        self.ensure_one()

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
            self.state_nfe = SITUACAO_NFE_EM_DIGITACAO
        #
        # Se o último processo foi a consulta da nota, significa que ela já
        # está emitida
        #
        elif processo.webservice == WS_NFE_CONSULTA:
            if processo.resposta.cStat.valor in ('100', '150'):
                self.chave = processo.resposta.chNFe.valor
                self.executa_antes_autorizar()
                self.state_nfe = SITUACAO_NFE_AUTORIZADA
                self.executa_depois_autorizar()
            elif processo.resposta.cStat.valor in ('110', '301', '302'):
                self.chave = processo.resposta.chNFe.valor
                self.executa_antes_denegar()
                self.situacao_fiscal = SITUACAO_FISCAL_DENEGADO
                self.state_nfe = SITUACAO_NFE_DENEGADA
                self.executa_depois_denegar()
            else:
                self.state_nfe = SITUACAO_NFE_EM_DIGITACAO

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
                self.state_nfe = SITUACAO_NFE_REJEITADA
        #
        # Se o último processo foi o retorno do recibo, a nota foi rejeitada,
        # denegada, autorizada, ou ainda não tem resposta
        #
        elif processo.webservice == WS_NFE_CONSULTA_RECIBO:
            #
            # Consulta ainda sem resposta, a nota ainda não foi processada
            #
            if processo.resposta.cStat.valor == '105':
                self.state_nfe = SITUACAO_NFE_ENVIADA
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
                        self.grava_pdf(nfe, procNFe.danfe_pdf)
                    elif self.modelo == MODELO_FISCAL_NFCE:
                        self.grava_pdf(nfe, procNFe.danfce_pdf)

                    data_autorizacao = protNFe.infProt.dhRecbto.valor
                    data_autorizacao = UTC.normalize(data_autorizacao)

                    self.data_hora_autorizacao = data_autorizacao
                    self.protocolo_autorizacao = protNFe.infProt.nProt.valor
                    self.chave = protNFe.infProt.chNFe.valor

                    if protNFe.infProt.cStat.valor in ('100', '150'):
                        self.executa_antes_autorizar()
                        self.state_nfe = SITUACAO_NFE_AUTORIZADA
                        self.executa_depois_autorizar()
                    else:
                        self.executa_antes_denegar()
                        self.situacao_fiscal = SITUACAO_FISCAL_DENEGADO
                        self.state_nfe = SITUACAO_NFE_DENEGADA
                        self.executa_depois_denegar()

                else:
                    mensagem = 'Código de retorno: ' + \
                               protNFe.infProt.cStat.valor
                    mensagem += '\nMensagem: ' + \
                                protNFe.infProt.xMotivo.valor
                    self.mensagem_nfe = mensagem
                    self.state_nfe = SITUACAO_NFE_REJEITADA
            else:
                #
                # Rejeitada por outros motivos, falha no schema etc. etc.
                #
                mensagem = 'Código de retorno: ' + \
                           processo.resposta.cStat.valor
                mensagem += '\nMensagem: ' + \
                            processo.resposta.xMotivo.valor
                self.mensagem_nfe = mensagem
                self.state_nfe = SITUACAO_NFE_REJEITADA

    def cancela_nfe(self):
        self.ensure_one()

        processador = self.processador_nfe()

        xml = self.arquivo_xml_autorizacao_id.datas.decode('base64')
        xml = xml.decode('utf-8')

        procNFe = ProcNFe_310()

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
                self.grava_pdf(procNFe.NFe, processador.danfe.conteudo_pdf)
                processador.danfe.NFe = NFe_310()
                processador.danfe.protNFe = None
                processador.danfe.procEventoCancNFe = None
            elif self.modelo == MODELO_FISCAL_NFCE:
                processador.danfce.NFe = procNFe.NFe
                processador.danfce.protNFe = procNFe.protNFe
                processador.danfce.procEventoCancNFe = procevento
                processador.danfce.salvar_arquivo = False
                processador.danfce.gerar_danfce()
                self.grava_pdf(procNFe.NFe, processador.danfce.conteudo_pdf)
                processador.danfce.NFe = NFCe_310()
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
                self.state_nfe = SITUACAO_NFE_CANCELADA
            elif procevento.retEvento.infEvento.cStat.valor == '135':
                self.situacao_fiscal = SITUACAO_FISCAL_CANCELADO
                self.state_nfe = SITUACAO_NFE_CANCELADA

            self.executa_depois_cancelar()

    def executa_antes_autorizar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de autorizar uma NF-e
        #
        pass

    def executa_depois_autorizar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de autorizar uma NF-e,
        # por exemplo, criar lançamentos financeiros, movimentações de
        # estoque etc.
        #
        for documento in self:
            if documento.modelo not in (MODELO_FISCAL_NFE,
                                        MODELO_FISCAL_NFCE):
                super(SpedDocumento, documento)._compute_permite_cancelamento()
                continue

            if documento.emissao != TIPO_EMISSAO_PROPRIA:
                super(SpedDocumento, documento)._compute_permite_cancelamento()
                continue

            #
            # Envia o email da nota para o cliente
            #
            mail_template = None
            if documento.operacao_id.mail_template_id:
                mail_template = documento.operacao_id.mail_template_id
            else:
                if documento.modelo == MODELO_FISCAL_NFE and \
                    documento.empresa_id.mail_template_nfe_autorizada_id:
                    mail_template = \
                        documento.empresa_id.mail_template_nfe_autorizada_id
                elif documento.modelo == MODELO_FISCAL_NFCE and \
                    documento.empresa_id.mail_template_nfce_autorizada_id:
                    mail_template = \
                        documento.empresa_id.mail_template_nfce_autorizada_id

            if mail_template is None:
                continue

            documento.envia_email(mail_template)

    def executa_antes_cancelar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de autorizar uma NF-e;
        # não confundir com o método _compute_permite_cancelamento, que indica
        # se o botão de cancelamento vai estar disponível para o usuário na
        # interface
        #
        pass

    def executa_depois_cancelar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de cancelar uma NF-e,
        # por exemplo, excluir lançamentos financeiros, movimentações de
        # estoque etc.
        #
        for documento in self:
            if documento.modelo not in (MODELO_FISCAL_NFE,
                                        MODELO_FISCAL_NFCE):
                super(SpedDocumento, documento)._compute_permite_cancelamento()
                continue

            if documento.emissao != TIPO_EMISSAO_PROPRIA:
                super(SpedDocumento, documento)._compute_permite_cancelamento()
                continue

            #
            # Envia o email da nota para o cliente
            #
            mail_template = None
            if documento.modelo == MODELO_FISCAL_NFE and \
                documento.empresa_id.mail_template_nfe_cancelada_id:
                mail_template = \
                    documento.empresa_id.mail_template_nfe_cancelada_id
            elif documento.modelo == MODELO_FISCAL_NFCE and \
                documento.empresa_id.mail_template_nfce_cancelada_id:
                mail_template = \
                    documento.empresa_id.mail_template_nfce_cancelada_id

            if mail_template is None:
                continue

            documento.envia_email(mail_template)

    def executa_antes_denegar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias antes de denegar uma NF-e
        #
        pass

    def executa_depois_denegar(self):
        #
        # Este método deve ser alterado por módulos integrados, para realizar
        # tarefas de integração necessárias depois de denegar uma NF-e,
        # por exemplo, invalidar pedidos de venda e movimentações de estoque
        # etc.
        #
        for documento in self:
            if documento.modelo not in (MODELO_FISCAL_NFE,
                                        MODELO_FISCAL_NFCE):
                super(SpedDocumento, documento)._compute_permite_cancelamento()
                continue

            if documento.emissao != TIPO_EMISSAO_PROPRIA:
                super(SpedDocumento, documento)._compute_permite_cancelamento()
                continue

            #
            # Envia o email da nota para o cliente
            #
            mail_template = None
            if documento.modelo == MODELO_FISCAL_NFE and \
                documento.empresa_id.mail_template_nfe_denegada_id:
                mail_template = \
                    documento.empresa_id.mail_template_nfe_denegada_id
            elif documento.modelo == MODELO_FISCAL_NFCE and \
                documento.empresa_id.mail_template_nfce_denegada_id:
                mail_template = \
                    documento.empresa_id.mail_template_nfce_denegada_id

            if mail_template is None:
                continue

            documento.envia_email(mail_template)

    def envia_email(self, mail_template):
        self.ensure_one()
        dados = mail_template.generate_email([documento.id])
	# TODO: FIX ME

    def gera_pdf(self):
        self.ensure_one()

        if self.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
            return

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return

        processador = self.processador_nfe()

        procNFe = ProcNFe_310()
        if self.arquivo_xml_autorizacao_id:
            procNFe.xml = \
                self.arquivo_xml_autorizacao_id.datas.decode('base64')
        else:
            procNFe.NFe = self.monta_nfe()
            procNFe.NFe.gera_nova_chave()

        procNFe.NFe.monta_chave()

        procevento = ProcEventoCancNFe_100()
        if self.arquivo_xml_autorizacao_cancelamento_id:
            procevento.xml = \
                self.arquivo_xml_autorizacao_cancelamento_id.datas.decode('base64')

        #
        # Gera o DANFE, com a tarja de cancelamento quando necessário
        #
        if self.modelo == MODELO_FISCAL_NFE:
            processador.danfe.NFe = procNFe.NFe

            if self.arquivo_xml_autorizacao_id:
                processador.danfe.protNFe = procNFe.protNFe

            if self.arquivo_xml_autorizacao_cancelamento_id:
                processador.danfe.procEventoCancNFe = procevento

            processador.danfe.salvar_arquivo = False
            processador.danfe.gerar_danfe()
            self.grava_pdf(procNFe.NFe, processador.danfe.conteudo_pdf)
            processador.danfe.NFe = NFe_310()
            processador.danfe.protNFe = None
            processador.danfe.procEventoCancNFe = None

        elif self.modelo == MODELO_FISCAL_NFCE:
            processador.danfce.NFe = procNFe.NFe

            if self.arquivo_xml_autorizacao_id:
                processador.danfce.protNFe = procNFe.protNFe

            if self.arquivo_xml_autorizacao_cancelamento_id:
                processador.danfce.procEventoCancNFe = procevento

            processador.danfce.salvar_arquivo = False
            processador.danfce.gerar_danfce()
            self.grava_pdf(procNFe.NFe, processador.danfce.conteudo_pdf)
            processador.danfce.NFe = NFCe_310()
            processador.danfce.protNFe = None
            processador.danfce.procEventoCancNFe = None
