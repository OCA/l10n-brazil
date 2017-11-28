# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import models
from odoo.addons.l10n_br_base.constante_tributaria import *

_logger = logging.getLogger(__name__)

try:
    from satcfe.entidades import *
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.template import TemplateBrasil

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumentoItem(models.Model):
    _inherit = 'sped.documento.item'

    def monta_cfe(self):
        """
        FIXME: Impostos
        :return:
        """
        self.ensure_one()

        kwargs = {}

        if self.documento_id.modelo != MODELO_FISCAL_CFE:
            return

        if self.produto_descricao:
            descricao = self.produto_descricao
        else:
            descricao = self.produto_id.nome

        descricao = descricao.replace('—', '-').replace('–', '-')
        descricao = descricao.replace('”', '"').replace('“', '"')
        descricao = descricao.replace('’', u"'").replace('‘', u"'")
        descricao = descricao.replace('—', '-').replace('–', '-')

        if self.produto_id.ncm_id:
            ncm = self.produto_id.ncm_id.codigo
            ncm_extipi = self.produto_id.ncm_id.ex
        else:
            ncm = ''

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            if self.cst_icms_sn in ['102', '300', '500']:
                icms = ICMSSN102(
                    Orig=self.org_icms,
                    CSOSN=self.cst_icms_sn,
                )
            else:
                icms = ICMSSN900(
                    Orig=self.org_icms,
                    CSOSN=self.cst_icms_sn,
                    pICMS=Decimal('18.00')
                )

            # TODO: Fix me
            pis = PISSN(CST='49')
            cofins = COFINSSN(CST='49')
        else:
            if self.cst_icms in ['00', '20', '90']:
                icms = ICMS00(
                    Orig='0',
                    CST='00',
                    pICMS=Decimal('18.00')
                )
            elif self.cst_icms in ['40', '41', '50', '60']:
                icms = ICMS40(
                    Orig='0',
                    CST='60'
                )
            #
            # PIS
            # TODO: Implementar pis ST

            if self.cst_pis in ['01', '02', '05']:
                pis = PISAliq(
                    CST=self.cst_pis,
                    vBC=Decimal('1.00'),
                    pPIS=Decimal('0.0065')
                )
            elif self.cst_pis in ['04', '06', '07', '08', '09']:
                pis = PISNT(
                    CST=self.cst_pis
                )
            elif self.cst_pis == '03':
                pis = PISQtde(
                    CST=self.cst_pis,
                    qBCProd=Decimal('100.0000'),
                    vAliqProd=Decimal('0.6500')
                )
            elif self.cst_pis == '99':
                pis = PISOutr(
                    CST=self.cst_pis,
                    vBC=Decimal('1.00'),
                    pPIS=Decimal('0.0065')
                )

            #
            # COFINS
            # TODO: Implementar cofins ST

            if self.cst_cofins in ['01', '02', '05']:
                cofins = COFINSAliq(
                    CST=self.cst_cofins,
                    vBC=Decimal('1.00'),
                    pCOFINS=Decimal('0.0065')
                )
            elif self.cst_cofins in ['04', '06', '07', '08', '09']:
                cofins = COFINSNT(
                    CST=self.cst_cofins
                )
            elif self.cst_cofins == '03':
                cofins = COFINSQtde(
                    CST=self.cst_cofins,
                    qBCProd=Decimal('100.0000'),
                    vAliqProd=Decimal('0.6500')
                )
            elif self.cst_cofins == '99':
                cofins = COFINSOutr(
                    CST=self.cst_cofins,
                    vBC=Decimal('1.00'),
                    pCOFINS=Decimal('0.0065')
                )

        imposto = Imposto(
            vItem12741=D(self.vr_ibpt).quantize(D('0.01')),
            icms=icms,
            pis=pis,
            cofins=cofins,
        )
        imposto.validar()

        detalhe = Detalhamento(
            produto=ProdutoServico(
                cProd=self.produto_id.codigo or str(self.produto_id.id),
                xProd=descricao.strip(),
                CFOP=self.cfop_id.codigo,
                uCom=self.unidade_id.codigo,
                qCom=D(self.quantidade).quantize(D('0.0001')),
                vUnCom=D(self.vr_unitario).quantize(D(10 * 10 ** -3)),
                indRegra='A',
                NCM=ncm,
                **kwargs
            ),
            imposto=imposto
        )
        detalhe.validar()

        return detalhe
