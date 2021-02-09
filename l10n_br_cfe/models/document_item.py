# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)


import logging
from decimal import Decimal as D

from odoo import models
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    TAX_FRAMEWORK_SIMPLES,
    MODELO_FISCAL_CFE,
)

_logger = logging.getLogger(__name__)

try:
    from satcfe.entidades import (
        ProdutoServico,
        Detalhamento,
        Imposto,
        COFINSOutr,
        COFINSQtde,
        COFINSNT,
        COFINSAliq,
        PISOutr,
        PISQtde,
        PISNT,
        PISAliq,
        ICMS40,
        ICMS00,
        COFINSSN,
        PISSN,
        ICMSSN900,
        ICMSSN102,
    )

except (ImportError, IOError) as err:
    _logger.debug(err)


class FiscalDocumentLine(models.Model):
    _inherit = 'l10n_br_fiscal.document.line'

    def _serialize_cfe(self):
        """
        FIXME: Impostos
        FIXME: Caso de saída
        :return:
        """
        self.ensure_one()

        kwargs = {}
        kwargs_detalhamento = {}

        # if self.documento_id.modelo != MODELO_FISCAL_CFE:
        #     return

        if self.name:
            descricao = self.name
        else:
            descricao = self.product_id.name

        descricao = descricao.replace('—', '-').replace('–', '-')
        descricao = descricao.replace('”', '"').replace('“', '"')
        descricao = descricao.replace('’', "'").replace('‘', "'")

        if self.product_id.ncm_id:
            ncm = self.product_id.ncm_id.code_unmasked
            # ncm_extipi = self.product_id.ncm_id.ex
        else:
            ncm = ''

        icms = pis = cofins = None

        if self.document_id.company_tax_framework == TAX_FRAMEWORK_SIMPLES:
            if self.icms_cst_code in ['102', '300', '500']:
                icms = ICMSSN102(
                    Orig=self.icms_origin,
                    CSOSN=self.icms_cst_code,
                )
            else:
                icms = ICMSSN900(
                    Orig=self.icms_origin,
                    CSOSN=self.icms_cst_code,
                    pICMS=D(self.icmssn_percent).quantize(D('0.01')),
                )

            pis = PISSN(CST=self.pis_cst_code)
            cofins = COFINSSN(CST=self.cofins_cst_code)
        else:
            if self.cst_icms in ['00', '20', '90']:
                icms = ICMS00(
                    Orig=self.icms_origin,
                    CST=self.cst_icms,
                    pICMS=D(self.al_efetiva_icms_proprio).quantize(D('0.01')),
                    # TODO: Implementar al_efetiva_icms_proprio
                )
            elif self.cst_icms in ['40', '41', '50', '60']:
                icms = ICMS40(
                    Orig=self.icms_origin,
                    CST=self.cst_icms
                )
            #
            # PIS
            # TODO: Implementar pis ST

            al_pis_proprio = D(self.al_pis_proprio / 100).quantize(D('0.0001'))

            if self.pis_cst_code in ['01', '02', '05']:
                pis = PISAliq(
                    CST=self.pis_cst_code,
                    vBC=D(self.bc_pis_proprio).quantize(D('0.01')),
                    pPIS=al_pis_proprio,
                )
            elif self.pis_cst_code in ['04', '06', '07', '08', '09']:
                pis = PISNT(
                    CST=self.pis_cst_code
                )
            elif self.pis_cst_code == '03':
                pis = PISQtde(
                    CST=self.pis_cst_code,
                    qBCProd=D(self.quantidade).quantize(D('0.01')),
                    vAliqProd=D(self.vr_pis_proprio).quantize(D('0.01'))
                )
            elif self.pis_cst_code == '99':
                pis = PISOutr(
                    CST=self.pis_cst_code,
                    vBC=D(self.bc_pis_proprio).quantize(D('0.01')),
                    pPIS=al_pis_proprio,
                )

            #
            # COFINS
            # TODO: Implementar cofins ST

            al_cofins_proprio = D(
                self.al_cofins_proprio / 100).quantize(D('0.0001'))

            if self.cofins_cst_code in ['01', '02', '05']:
                cofins = COFINSAliq(
                    CST=self.cofins_cst_code,
                    vBC=D(self.bc_cofins_proprio).quantize(D('0.01')),
                    pCOFINS=al_cofins_proprio,
                )
            elif self.cofins_cst_code in ['04', '06', '07', '08', '09']:
                cofins = COFINSNT(
                    CST=self.cofins_cst_code
                )
            elif self.cofins_cst_code == '03':
                cofins = COFINSQtde(
                    CST=self.cofins_cst_code,
                    qBCProd=D(self.quantidade).quantize(D('0.01')),
                    vAliqProd=D(self.vr_cofins_proprio).quantize(D('0.01'))
                )
            elif self.cofins_cst_code == '99':
                cofins = COFINSOutr(
                    CST=self.cofins_cst_code,
                    vBC=D(self.bc_cofins_proprio).quantize(D('0.01')),
                    pCOFINS=al_cofins_proprio,
                )

        imposto = Imposto(
            vItem12741=D(self.amount_estimate_tax).quantize(D('0.01')),
            icms=icms,
            pis=pis,
            cofins=cofins,
        )
        imposto.validar()

        # TODO: REFACTOR
        # if self.infcomplementar:
        #     kwargs_detalhamento['infAdProd'] = self._monta_informacoes_adicionais()

        if self.discount_value:
            kwargs['vDesc'] = D(self.discount_value).quantize(D('0.01'))

        detalhe = Detalhamento(
            produto=ProdutoServico(
                cProd=self.product_id.code or str(self.product_id.id),
                xProd=descricao.strip(),
                CFOP=self.cfop_id.code,
                uCom=self.uom_id.code,
                qCom=D(self.quantity).quantize(D('0.0001')),
                vUnCom=D(self.price_unit).quantize(D('0.01')),
                indRegra='A',
                NCM=ncm,
                **kwargs
            ),
            imposto=imposto,
            **kwargs_detalhamento
        )

        detalhe.validar()

        return detalhe

    def _monta_informacoes_adicionais(self):
        self.ensure_one()

        if self.documento_id.modelo != MODELO_FISCAL_CFE:
            return super()._monta_informacoes_adicionais()

        infcomplementar = self.infcomplementar

        dados_infcomplementar = {
            'nf': self.documento_id,
            'item': self,
        }

        return self._renderizar_informacoes_template(
            dados_infcomplementar, infcomplementar)
