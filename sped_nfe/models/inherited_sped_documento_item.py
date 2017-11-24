# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import models
from odoo.addons.l10n_br_base.constante_tributaria import *

_logger = logging.getLogger(__name__)

try:
    from pysped.nfe.leiaute import Det_310
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.template import TemplateBrasil

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumentoItem(models.Model):
    _inherit = 'sped.documento.item'

    def monta_nfe(self, numero_item, nfe):
        self.ensure_one()

        if self.documento_id.modelo != MODELO_FISCAL_NFE and \
                self.documento_id.modelo != MODELO_FISCAL_NFCE:
            return

        det = Det_310()

        det.nItem.valor = numero_item
        det.prod.cProd.valor = \
            self.produto_id.codigo or str(self.produto_id.id)
        det.prod.cEAN.valor = self.produto_id.codigo_barras or ''

        #
        # O 1º item da NFC-e tem que ter uma descrição específica em
        # homologação
        #
        if self.documento_id.modelo == MODELO_FISCAL_NFCE and \
                self.documento_id.ambiente_nfe == AMBIENTE_NFE_HOMOLOGACAO:
            descricao = 'NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO - ' \
                        'SEM VALOR FISCAL'

        else:
            if self.produto_descricao:
                descricao = self.produto_descricao
            else:
                descricao = self.produto_id.nome

        descricao = descricao.replace('—', '-').replace('–', '-')
        descricao = descricao.replace('”', '"').replace('“', '"')
        descricao = descricao.replace('’', u"'").replace('‘', u"'")
        descricao = descricao.replace('—', '-').replace('–', '-')
        det.prod.xProd.valor = descricao.strip()

        if self.produto_id.ncm_id:
            det.prod.NCM.valor = self.produto_id.ncm_id.codigo
            det.prod.EXTIPI.valor = self.produto_id.ncm_id.ex
        else:
            det.prod.NCM.valor = ''

        det.prod.CFOP.valor = self.cfop_id.codigo
        det.prod.uCom.valor = self.unidade_id.codigo
        det.prod.qCom.valor = str(D(self.quantidade).quantize(D('0.0001')))
        det.prod.vUnCom.valor = \
            str(D(self.vr_unitario).quantize(D(10 * 10 ** -10)))
        det.prod.vProd.valor = str(D(self.vr_produtos))
        det.prod.cEANTrib.valor = ''
        det.prod.uTrib.valor = det.prod.uCom.valor
        det.prod.qTrib.valor = det.prod.qCom.valor
        det.prod.vUnTrib.valor = det.prod.vUnCom.valor
        det.prod.vFrete.valor = str(D(self.vr_frete))
        det.prod.vSeg.valor = str(D(self.vr_seguro))
        det.prod.vOutro.valor = str(D(self.vr_outras))
        det.prod.vDesc.valor = str(D(self.vr_desconto))
        det.prod.xPed.valor = self.numero_pedido or ''
        det.prod.nItemPed.valor = self.numero_item_pedido or ''

        if self.compoe_total:
            det.prod.indTot.valor = '1'
        else:
            det.prod.indTot.valor = '0'

        #
        # Declaração de Importação
        #
        for declaracao in self.declaracao_ids:
            det.prod.DI.append(declaracao.monta_nfe())

        #
        # Impostos
        #
        det.imposto.vTotTrib.valor = str(D(self.vr_ibpt))

        #
        # Usa o regime tributário da NF e não da empresa, e trata o código
        # interno 3.1 para o lucro real, que na NF deve ir somente 3
        #
        det.imposto.ICMS.regime_tributario = \
            self.documento_id.regime_tributario[0]

        #
        # ICMS comum
        #
        det.imposto.ICMS.orig.valor = self.org_icms
        det.imposto.ICMS.CST.valor = self.cst_icms

        #
        # ICMS SIMPLES
        #
        if self.documento_id.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            det.imposto.ICMS.CSOSN.valor = self.cst_icms_sn
            det.imposto.ICMS.pCredSN.valor = str(D(self.al_icms_sn))
            det.imposto.ICMS.vCredICMSSN.valor = str(D(self.vr_icms_sn))

        det.imposto.ICMS.modBC.valor = self.md_icms_proprio
        det.imposto.ICMS.pRedBC.valor = str(D(self.rd_icms_proprio))
        det.imposto.ICMS.vBC.valor = str(D(self.bc_icms_proprio))
        det.imposto.ICMS.pICMS.valor = str(D(self.al_icms_proprio))
        det.imposto.ICMS.vICMS.valor = str(D(self.vr_icms_proprio))
        det.imposto.ICMS.modBCST.valor = self.md_icms_st
        det.imposto.ICMS.pMVAST.valor = str(D(self.pr_icms_st))
        det.imposto.ICMS.pRedBCST.valor = str(D(self.rd_icms_st))
        det.imposto.ICMS.vBCST.valor = str(D(self.bc_icms_st))
        det.imposto.ICMS.pICMSST.valor = str(D(self.al_icms_st))
        det.imposto.ICMS.vICMSST.valor = str(D(self.vr_icms_st))
        # det.imposto.ICMS.motDesICMS.valor =
        # det.imposto.ICMS.vBCSTRet.valor = str(D(self.bc_icms_st_retido))
        # det.imposto.ICMS.vICMSSTRet.valor = str(D(self.vr_icms_st_retido))
        # det.imposto.ICMS.vBCSTDest.valor =
        # det.imposto.ICMS.vICMSSTDest.valor =
        # det.imposto.ICMS.UFST.valor =
        # det.imposto.ICMS.pBCOp.valor =

        if (self.cst_icms not in ST_ICMS_CALCULA_PROPRIO and
                self.cst_icms_sn not in ST_ICMS_SN_CALCULA_PROPRIO):
            det.imposto.ICMS.pICMS.valor = str(D(0))

        if self.documento_id.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if self.cst_icms_sn in ST_ICMS_CODIGO_CEST:
                if self.produto_id.cest_id:
                    det.prod.CEST.valor = self.produto_id.cest_id.codigo or ''

        else:
            if self.cst_icms in ST_ICMS_CODIGO_CEST:
                if self.produto_id.cest_id:
                    det.prod.CEST.valor = self.produto_id.cest_id.codigo or ''

        #
        # IPI
        #
        if ((self.documento_id.regime_tributario != REGIME_TRIBUTARIO_SIMPLES)
                and self.cst_ipi):
            det.imposto.IPI.cEnq.valor = self.enquadramento_ipi or '999'
            det.imposto.IPI.CST.valor = self.cst_ipi or ''
            det.imposto.IPI.vBC.valor = str(D(self.bc_ipi))
            # det.imposto.IPI.qUnid.valor = str(D(self.quantidade_tributacao))
            # det.imposto.IPI.vUnid.valor = str(D(self.al_ipi))
            det.imposto.IPI.pIPI.valor = str(D(self.al_ipi))
            det.imposto.IPI.vIPI.valor = str(D(self.vr_ipi))
        else:
            det.imposto.IPI.CST.valor = ''

        #
        # PIS e COFINS
        #
        det.imposto.PIS.CST.valor = self.cst_pis
        det.imposto.PIS.vBC.valor = str(D(self.bc_pis_proprio))
        det.imposto.PIS.pPIS.valor = str(D(self.al_pis_proprio))
        det.imposto.PIS.vPIS.valor = str(D(self.vr_pis_proprio))
        det.imposto.COFINS.CST.valor = self.cst_cofins
        det.imposto.COFINS.vBC.valor = str(D(self.bc_cofins_proprio))
        det.imposto.COFINS.pCOFINS.valor = str(D(self.al_cofins_proprio))
        det.imposto.COFINS.vCOFINS.valor = str(D(self.vr_cofins_proprio))

        #
        # Imposto de importação
        #
        det.imposto.II.vBC.valor = str(D(self.bc_ii))
        det.imposto.II.vII.valor = str(D(self.vr_ii))
        det.imposto.II.vDespAdu.valor = str(D(self.vr_despesas_aduaneiras))
        det.imposto.II.vIOF.valor = str(D(self.vr_iof))

        #
        # Prepara a observação do item
        #
        infcomplementar = self.infcomplementar or ''

        dados_infcomplementar = {
            'nf': self.documento_id,
            'item': self,
        }

        #
        # Crédito de ICMS do SIMPLES
        #
        if self.documento_id.regime_tributario == REGIME_TRIBUTARIO_SIMPLES \
            and self.cst_icms_sn in ST_ICMS_SN_CALCULA_CREDITO:
            if len(infcomplementar) > 0:
                infcomplementar += '\n'

            infcomplementar += 'Permite o aproveitamento de crédito de ' + \
                'ICMS no valor de R$ ${formata_valor(item.vr_icms_sn)},' + \
                ' correspondente à alíquota de ' + \
                '${formata_valor(item.al_icms_sn)}%, nos termos do art. 23'+ \
                ' da LC 123/2006;'

        #
        # Valor do IBPT
        #
        if self.vr_ibpt:
            if len(infcomplementar) > 0:
                infcomplementar += '\n'

            infcomplementar += 'Valor aproximado dos tributos: ' + \
                'R$ ${formata_valor(item.vr_ibpt)} (' + \
                '${formata_valor(item.al_ibpt)}%) - fonte: IBPT;'

        #
        # ICMS para UF de destino
        #
        if nfe.infNFe.ide.idDest.valor == \
            IDENTIFICACAO_DESTINO_INTERESTADUAL and \
            nfe.infNFe.ide.indFinal.valor == \
            TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL and \
            nfe.infNFe.dest.indIEDest.valor == \
            INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE:

            det.imposto.ICMSUFDest.vBCUFDest.valor = \
                det.imposto.ICMS.vBC.valor
            det.imposto.ICMSUFDest.pFCPUFDest.valor = \
                str(D(self.al_fcp))
            det.imposto.ICMSUFDest.pICMSUFDest.valor = \
                str(D(self.al_interna_destino))
            det.imposto.ICMSUFDest.pICMSInter.valor = \
                str(D(self.al_icms_proprio))
            det.imposto.ICMSUFDest.pICMSInterPart.valor = \
                str(D(self.al_partilha_estado_destino))
            det.imposto.ICMSUFDest.vFCPUFDest.valor = \
                str(D(self.vr_fcp))
            det.imposto.ICMSUFDest.vICMSUFDest.valor = \
                str(D(self.vr_icms_estado_destino))
            det.imposto.ICMSUFDest.vICMSUFRemet.valor = \
                str(D(self.vr_icms_estado_origem))

            if len(infcomplementar) > 0:
                infcomplementar += '\n'

            infcomplementar += \
                'Partilha do ICMS de ' + \
                '${formata_valor(item.al_interna_destino)}% recolhida ' + \
                'conf. EC 87/2015: ' + \
                'R$ ${formata_valor(item.vr_icms_estado_destino)} para o ' + \
                'estado de ${nf.participante_id.estado} e ' + \
                'R$ ${formata_valor(item.vr_icms_estado_origem)} para o ' + \
                'estado de ${nf.empresa_id.estado}; Valor do diferencial ' + \
                'de alíquota (${formata_valor(item.al_difal)}%): ' + \
                'R$ ${formata_valor(item.vr_difal)};'

            if self.vr_fcp:
                infcomplementar += ' Fundo de combate à pobreza: R$ ' + \
                    '${formata_valor(item.vr_fcp)}'

        #
        # Aplica um template na observação do item
        #
        template = TemplateBrasil(infcomplementar.encode('utf-8'))
        infcomplementar = template.render(**dados_infcomplementar)
        det.infAdProd.valor = infcomplementar.decode('utf-8')

        return det
