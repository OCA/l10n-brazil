# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import models, api
from odoo.addons.l10n_br_base.constante_tributaria import *

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.produto import valida_ean

except (ImportError, IOError) as err:
    _logger.debug(err)

from .versao_nfe_padrao import ClasseDet


class SpedDocumentoItem(models.Model):
    _inherit = 'sped.documento.item'

    def _busca_cfop(self, codigo):
        cfop = self.env['sped.cfop'].search([('codigo', '=', codigo)])

        if len(cfop) == 0:
            return False

        return cfop[0].id

    def _busca_ncm(self, codigo, ex):
        ncm = self.env['sped.ncm'].search(
            [('codigo', '=', codigo), ('ex', '=', ex)])

        if len(ncm) == 0:
            return False

        return ncm[0].id

    def _busca_cest(self, codigo):
        cest = self.env['sped.cest'].search(
            [('codigo', '=', codigo)])

        if len(cest) == 0:
            return False

        return cest[0].id

    def _busca_unidade(self, codigo, pode_incluir=True):
        unidade = self.env['sped.unidade'].busca(codigo)

        #
        # Trata o caso de unidade UN9999 que tem em várias notas
        #
        if len(unidade) == 0 and codigo[:2] == 'UN':
            cod = codigo[2:]

            if cod.isdigit():
                unidade = self.env['sped.unidade'].busca('UN')

        if len(unidade) == 0:
            if not pode_incluir:
                return False

            dados = {
                'codigo': codigo,
                'nome': 'unidade ' + codigo,
            }
            unidade = self.env['sped.unidade'].create(dados)
            return unidade

        return unidade[0]

    def _busca_produto(self, dados):
        if dados['codigo_barras']:
            produto = self.env['sped.produto'].search(
                [('codigo_barras', '=', dados['codigo_barras'])])

            if len(produto) != 0:
                return produto[0]

        produto = self.env['sped.produto'].search(
            [('codigo', '=', dados['codigo'])])

        if len(produto) != 0:
            return produto[0]

        produto = self.env['sped.produto'].search(
            [('codigo_cliente', '=', dados['codigo'])])

        if len(produto) != 0:
            return produto[0]

        produto = self.env['sped.produto'].create(dados)

        return produto

    def _busca_produto_terceiros(self, dados):
        if dados['codigo_barras']:
            produto = self.env['sped.produto'].search(
                [('codigo_barras', '=', dados['codigo_barras'])])

            if len(produto) != 0:
                return produto[0]

        if dados['codigo_barras_tributacao']:
            produto = self.env['sped.produto'].search(
                [('codigo_barras_tributacao', '=',
                  dados['codigo_barras_tributacao'])])

            if len(produto) != 0:
                return produto[0]

        produto = self.env['sped.produto'].search(
            [('codigo_cliente', '=', dados['codigo'])])

        if len(produto) != 0:
            return produto[0]

        return False

    def le_nfe(self, det, dados_documento):
        dados = {
            'emissao': dados_documento['emissao'],
            'entrada_saida': dados_documento['entrada_saida'],
            'regime_tributario': dados_documento['regime_tributario'],

            'quantidade': det.prod.qCom.valor,
            'vr_unitario': det.prod.vUnCom.valor,
            'vr_produtos': det.prod.vProd.valor,

            'quantidade_tributacao': det.prod.qTrib.valor,
            'vr_unitario_tributacao': det.prod.vUnTrib.valor,
            'vr_produtos_tributacao': \
                det.prod.qTrib.valor * det.prod.vUnTrib.valor,
            'exibe_tributacao': False,
            'fator_conversao_unidade_tributacao': 1,

            'vr_frete': det.prod.vFrete.valor,
            'vr_seguro': det.prod.vSeg.valor,
            'vr_outras': det.prod.vOutro.valor,
            'vr_desconto': det.prod.vDesc.valor,
            'numero_pedido': det.prod.xPed.valor,
            'numero_item_pedido': det.prod.nItemPed.valor,
            'compoe_total': str(det.prod.indTot.valor) == '1',

            #
            # Impostos
            #

            #
            # ICMS comum
            #
            'org_icms': str(det.imposto.ICMS.orig.valor),
            'cst_icms': str(det.imposto.ICMS.CST.valor),

            #
            # ICMS SIMPLES
            #
            'cst_icms_sn': str(det.imposto.ICMS.CSOSN.valor),
            'al_icms_sn': det.imposto.ICMS.pCredSN.valor,
            'vr_icms_sn': det.imposto.ICMS.vCredICMSSN.valor,

            'md_icms_proprio': str(det.imposto.ICMS.modBC.valor),
            'rd_icms_proprio': det.imposto.ICMS.pRedBC.valor,
            'bc_icms_proprio': det.imposto.ICMS.vBC.valor,
            'al_icms_proprio': det.imposto.ICMS.pICMS.valor,
            'vr_icms_proprio': det.imposto.ICMS.vICMS.valor,
            'md_icms_st': str(det.imposto.ICMS.modBCST.valor),
            'pr_icms_st': det.imposto.ICMS.pMVAST.valor,
            'rd_icms_st': det.imposto.ICMS.pRedBCST.valor,
            'bc_icms_st': det.imposto.ICMS.vBCST.valor,
            'al_icms_st': det.imposto.ICMS.pICMSST.valor,
            'vr_icms_st': det.imposto.ICMS.vICMSST.valor,
            # det.imposto.ICMS.motDesICMS.valor =
            # det.imposto.ICMS.vBCSTRet.valor = str(D(self.bc_icms_st_retido))
            # det.imposto.ICMS.vICMSSTRet.valor = str(D(self.vr_icms_st_retido))
            # det.imposto.ICMS.vBCSTDest.valor =
            # det.imposto.ICMS.vICMSSTDest.valor =
            # det.imposto.ICMS.UFST.valor =
            # det.imposto.ICMS.pBCOp.valor =

            #
            # IPI
            #
            'cst_ipi': det.imposto.IPI.CST.valor,
            'enquadramento_ipi': det.imposto.IPI.cEnq.valor,
            'bc_ipi': det.imposto.IPI.vBC.valor,
            # det.imposto.IPI.qUnid.valor = str(D(self.quantidade_tributacao))
            # det.imposto.IPI.vUnid.valor = str(D(self.al_ipi))
            'al_ipi': det.imposto.IPI.pIPI.valor,
            'vr_ipi': det.imposto.IPI.vIPI.valor,

            #
            # PIS e COFINS
            #
            'cst_pis': det.imposto.PIS.CST.valor,
            'bc_pis_proprio': det.imposto.PIS.vBC.valor,
            'al_pis_proprio': det.imposto.PIS.pPIS.valor,
            'vr_pis_proprio': det.imposto.PIS.vPIS.valor,
            'cst_cofins': det.imposto.COFINS.CST.valor,
            'bc_cofins_proprio': det.imposto.COFINS.vBC.valor,
            'al_cofins_proprio': det.imposto.COFINS.pCOFINS.valor,
            'vr_cofins_proprio': det.imposto.COFINS.vCOFINS.valor,

            #
            # Imposto de importação
            #
            'bc_ii': det.imposto.II.vBC.valor,
            'vr_ii': det.imposto.II.vII.valor,
            'vr_despesas_aduaneiras': det.imposto.II.vDespAdu.valor,
            'vr_iof': det.imposto.II.vIOF.valor,

            #
            # Valor do IBPT
            #
            'vr_ibpt': det.imposto.vTotTrib.valor,

            #
            # ICMS para UF de destino
            #
            'al_fcp': det.imposto.ICMSUFDest.pFCPUFDest.valor,
            'al_interna_destino': det.imposto.ICMSUFDest.pICMSUFDest.valor,
            #'al_icms_proprio': det.imposto.ICMSUFDest.pICMSInter.valor,
            'al_partilha_estado_destino': det.imposto.ICMSUFDest.pICMSInterPart.valor,
            'vr_fcp':det.imposto.ICMSUFDest.vFCPUFDest.valor,
            'vr_icms_estado_destino': det.imposto.ICMSUFDest.vICMSUFDest.valor,
            'vr_icms_estado_origem': det.imposto.ICMSUFDest.vICMSUFRemet.valor,

            #
            # Informação complementar
            #
            'infcomplementar': det.infAdProd.valor,

            #
            # CFOP
            #
            'cfop_id': self._busca_cfop(str(det.prod.CFOP.valor)),
        }

        #
        # Calcula o fator de conversão da unidade de tributação
        #
        if dados['quantidade'] != dados['quantidade_tributacao']:
            dados['fator_conversao_unidade_tributacao'] = \
                D(dados['quantidade_tributacao']) / \
                D(dados['quantidade'])
            dados['exibe_tributacao'] = True

        #
        # Trata as CSTs de IPI e PIS-COFINS para entrada e saída
        #
        if dados_documento['entrada_saida'] == ENTRADA_SAIDA_ENTRADA:
            if dados['cst_ipi'] in ST_IPI_ENTRADA_DICT:
                dados['cst_ipi_entrada'] = dados['cst_ipi']

            if dados['cst_pis'] in ST_PIS_ENTRADA_DICT:
                dados['cst_pis_entrada'] = dados['cst_pis']

            if dados['cst_cofins'] in ST_COFINS_ENTRADA_DICT:
                dados['cst_cofins_entrada'] = dados['cst_cofins']

        else:
            if dados['cst_ipi'] in ST_IPI_SAIDA_DICT:
                dados['cst_ipi_saida'] = dados['cst_ipi']

            if dados['cst_pis'] in ST_PIS_SAIDA_DICT:
                dados['cst_pis_saida'] = dados['cst_pis']

            if dados['cst_cofins'] in ST_COFINS_SAIDA_DICT:
                dados['cst_cofins_saida'] = dados['cst_cofins']

        #
        # Caso a nota seja de emissão própria, podemos incluir os produtos
        # automaticamente
        #
        dados_produto = {
            'codigo': det.prod.cProd.valor,
            'nome': det.prod.xProd.valor,
            'ncm_id': self._busca_ncm(str(det.prod.NCM.valor),
                                      str(det.prod.EXTIPI.valor)),
            'cest_id': self._busca_cest(str(det.prod.CEST.valor)),
            'tipo': TIPO_PRODUTO_SERVICO_MERCADORIA_PARA_REVENDA,
            'org_icms': dados['org_icms']
        }

        if valida_ean(det.prod.cEAN.valor):
            dados_produto['codigo_barras'] = det.prod.cEAN.valor
        else:
            dados_produto['codigo_barras'] = False

        if valida_ean(det.prod.cEANTrib.valor):
            dados_produto['codigo_barras_tributacao'] = \
                det.prod.cEANTrib.valor
        else:
            dados_produto['codigo_barras_tributacao'] = False

        if dados_documento['emissao'] == TIPO_EMISSAO_TERCEIROS:
            produto = self._busca_produto_terceiros(dados_produto)
            if produto:
                dados['produto_id'] = produto.id

            unidade = self._busca_unidade(det.prod.uCom.valor, False)
            if unidade:
                dados['unidade_id'] = unidade.id
                dados['currency_unidade_id'] = unidade.currency_id.id

            unidade_tributacao = self._busca_unidade(det.prod.uTrib.valor,
                                                     False)
            if unidade_tributacao:
                dados['unidade_tributacao_id'] = unidade_tributacao.id
                dados['currency_unidade_tributacao_id'] = \
                    unidade_tributacao.currency_id.id

        else:
            unidade = self._busca_unidade(det.prod.uCom.valor)
            dados['unidade_id'] = unidade.id
            dados['currency_unidade_id'] = unidade.currency_id.id
            dados_produto['unidade_id'] = unidade.id
            dados_produto['currency_unidade_id'] = unidade.currency_id.id

            unidade_tributacao = self._busca_unidade(det.prod.uTrib.valor)
            dados['unidade_tributacao_id'] = unidade_tributacao.id
            dados['currency_unidade_tributacao_id'] = \
                unidade_tributacao.currency_id.id

            #
            # No cadastro do produto, só preenchemos a unidade de tributação
            # caso essa seja diferente da própria unidade do produto
            #
            if unidade.id != unidade_tributacao.id:
                dados_produto['unidade_tributacao_id'] = unidade_tributacao.id
                dados_produto['currency_unidade_tributacao_id'] = \
                    unidade_tributacao.currency_id.id
                dados_produto['fator_conversao_unidade_tributacao'] = \
                    dados['fator_conversao_unidade_tributacao']

            #
            # Trata o caso do código de barras de tributação vir no final
            # do nome do produto
            #
            partes = dados_produto['nome'].split('-')
            if len(partes) > 1:
                codigo = partes[-1].strip()

                if codigo.isdigit() and codigo == str(det.prod.cEAN.valor):
                    dados_produto['nome'] = '-'.join(partes[:-1]).strip()

                if codigo.isdigit() and codigo == str(det.prod.cEANTrib.valor):
                    dados_produto['nome'] = '-'.join(partes[:-1]).strip()

            dados['produto_id'] = self._busca_produto(dados_produto).id

        ##
        ## Declaração de Importação
        ##
        #for declaracao in self.declaracao_ids:
            #det.prod.DI.append(declaracao.monta_nfe())

        ##
        ## Rastreabilidade
        ##
        #for rastreabilidade in self.rastreabilidade_ids:
            #det.prod.rastro.append(rastreabilidade.monta_nfe())

        item = self.new()
        item.update(dados)
        item._onchange_calcula_valor_operacao()
        item._onchange_calcula_total()

        dados['vr_operacao'] = item.vr_operacao
        dados['vr_operacao_tributacao'] = item.vr_operacao_tributacao
        dados['vr_fatura'] = item.vr_fatura
        dados['vr_nf'] = item.vr_nf

        #
        # Cadastro do produto
        #
        dados.update({
            'produto_codigo': det.prod.cProd.valor,
            'produto_nome': det.prod.xProd.valor,
            'produto_codigo_barras': det.prod.cEAN.valor,
            'produto_codigo_barras_tributacao': det.prod.cEANTrib.valor,
            'produto_unidade': det.prod.uCom.valor,
            'produto_unidade_tributacao': det.prod.uTrib.valor,
            'produto_ncm': str(det.prod.NCM.valor),
            'produto_ncm_ex': str(det.prod.EXTIPI.valor),
            'produto_cest': str(det.prod.CEST.valor),
        })

        return dados
