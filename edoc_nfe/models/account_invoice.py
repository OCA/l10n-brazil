# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime
from unicodedata import normalize
import logging
from pytz import UTC

_logger = logging.getLogger(__name__)

from nfelib.v4_00 import leiauteNFe
from erpbrasil.assinatura.certificado import Certificado
from requests import Session
from erpbrasil.transmissao import TransmissaoSOAP
from erpbrasil.edoc import NFe

from odoo import models, api, fields
from odoo.exceptions import UserError
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm

from odoo.addons.l10n_br_account_product.models.account_invoice_term import (
    FORMA_PAGAMENTO_CARTOES,
    FORMA_PAGAMENTO_SEM_PAGAMENTO
)
from odoo.addons.edoc_base.constantes import (
    AUTORIZADO,
    AUTORIZADO_OU_DENEGADO,
    DENEGADO,
    CANCELADO,
    LOTE_EM_PROCESSAMENTO,
    LOTE_RECEBIDO,
    LOTE_PROCESSADO,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFCE,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
    SITUACAO_FISCAL_REGULAR,
    SITUACAO_FISCAL_REGULAR_EXTEMPORANEO,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
    SITUACAO_FISCAL_DENEGADO,
    SITUACAO_FISCAL_INUTILIZADO,
    SITUACAO_FISCAL_COMPLEMENTAR,
    SITUACAO_FISCAL_COMPLEMENTAR_EXTEMPORANEO,
    SITUACAO_FISCAL_REGIME_ESPECIAL,
    SITUACAO_FISCAL_MERCADORIA_NAO_CIRCULOU,
    SITUACAO_FISCAL_MERCADORIA_NAO_RECEBIDA,
)
from .res_company import PROCESSADOR


def fiter_processador_edoc_nfe(record):
    if (record.processador_edoc == PROCESSADOR and
            record.fiscal_document_id.code in [
                MODELO_FISCAL_NFE,
                MODELO_FISCAL_NFCE,
            ]):
        return True
    return False


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _dest(self):
        partner_bc_code = ''
        partner_cep = ''
        if self.partner_id.country_id.bc_code:
            partner_bc_code = self.partner_id.country_id.bc_code[1:]
        if self.partner_id.country_id.id != self.company_id.country_id.id:
            address_invoice_state_code = 'EX'
            address_invoice_city = 'Exterior'
            address_invoice_city_code = '9999999'
        else:
            address_invoice_state_code = self.partner_id.state_id.code
            address_invoice_city = (normalize(
                'NFKD', unicode(
                    self.partner_id.l10n_br_city_id.name or '')).encode(
                'ASCII', 'ignore'))
            address_invoice_city_code = ('%s%s') % (
                self.partner_id.state_id.ibge_code,
                self.partner_id.l10n_br_city_id.ibge_code)
            partner_cep = punctuation_rm(self.partner_id.zip)
        if self.company_id.nfe_environment == '2':
            x_nome = \
                'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL'
            cnpj = '99999999000191'
        else:
            x_nome = normalize('NFKD', unicode(
                self.partner_id.legal_name[:60] or ''
            )).encode('ASCII', 'ignore')

        if self.partner_id.is_company:
            ie = punctuation_rm(
                self.partner_id.inscr_est)

        cnpj = None
        cpf = None
        if self.partner_id.country_id.id == self.company_id.country_id.id:
            if self.partner_id.is_company:
                cnpj = punctuation_rm(self.partner_id.cnpj_cpf)
            else:
                cpf = punctuation_rm(self.partner_id.cnpj_cpf)

        ind_ie_dest = self.partner_id.partner_fiscal_type_id.ind_ie_dest

        ender_dest = leiauteNFe.TEnderEmi(
            xLgr=normalize('NFKD', unicode(
                self.partner_id.street or '')).encode('ASCII', 'ignore'),
            nro=self.partner_id.number or '',
            # xCpl=normalize('NFKD', unicode(
            #     self.partner_id.street2 or '')).encode('ASCII', 'ignore'),
            xBairro=normalize('NFKD', unicode(
                self.partner_id.district or 'Sem Bairro')
                              ).encode('ASCII', 'ignore'),
            cMun=address_invoice_city_code,
            xMun=address_invoice_city,
            UF=address_invoice_state_code,
            CEP=partner_cep,
            cPais=partner_bc_code,
            xPais=self.partner_id.country_id.name or '',
            fone=punctuation_rm(self.partner_id.phone or ''
                                ).replace(' ', '') or None)

        if self.partner_id.country_id.id != self.company_id.country_id.id:
            id_estrangeiro = punctuation_rm(self.partner_id.cnpj_cpf)
        else:
            id_estrangeiro = None

        dest = leiauteNFe.destType(
            CNPJ=cnpj,
            CPF=cpf,
            idEstrangeiro=id_estrangeiro,
            xNome=x_nome,
            enderDest=ender_dest,
            indIEDest=ind_ie_dest,
            IE=ie,
            ISUF=None,
            IM=None,
            email=self.partner_id.email or None)
        return dest

    def _icms(self, invoice_line):
        icms_00 = None
        icms_10 = None
        icms_20 = None
        icms_30 = None
        icms_40 = None
        icms_51 = None
        icms_60 = None
        icms_70 = None
        icms_90 = None
        icms_part = None
        icms_st = None
        icms_sn_101 = None
        icms_sn_102 = None
        icms_sn_201 = None
        icms_sn_202 = None
        icms_sn_500 = None
        icms_sn_900 = None
        if invoice_line.icms_cst_id.code == '00':
            icms_00 = leiauteNFe.ICMS00Type(
                orig=invoice_line.icms_origin or '',
                CST=invoice_line.icms_cst_id.code,
                modBC=invoice_line.icms_base_type,
                vBC=str("%.2f" % invoice_line.icms_base),
                pICMS=str("%.2f" % invoice_line.icms_percent),
                vICMS=str("%.2f" % invoice_line.icms_value),
                pFCP=None,
                vFCP=None)
        elif invoice_line.icms_cst_id.code == '10':
            icms_10 = leiauteNFe.ICMS10Type(
                orig=invoice_line.icms_origin or '',
                CST=invoice_line.icms_cst_id.code,
                modBC=invoice_line.icms_base_type,
                vBC=str("%.2f" % invoice_line.icms_base),
                pICMS=str("%.2f" % invoice_line.icms_percent),
                vICMS=str("%.2f" % invoice_line.icms_value),
                vBCFCP=None,
                pFCP=None,
                vFCP=None,
                modBCST=invoice_line.icms_st_base_type,
                pMVAST=str("%.2f" % invoice_line.icms_st_mva),
                pRedBCST=str("%.2f" % invoice_line.icms_st_percent_reduction),
                vBCST=str("%.2f" % invoice_line.icms_st_base),
                pICMSST=str("%.2f" % invoice_line.icms_st_percent),
                vICMSST=str("%.2f" % invoice_line.icms_st_value),
                vBCFCPST=None,
                pFCPST=None,
                vFCPST=None)
        elif invoice_line.icms_cst_id.code == '20':
            icms_20 = leiauteNFe.ICMS20Type(
                orig=invoice_line.icms_origin or '',
                CST=invoice_line.icms_cst_id.code,
                modBC=invoice_line.icms_base_type,
                pRedBC=str("%.2f" % invoice_line.icms_percent_reduction),
                vBC=str("%.2f" % invoice_line.icms_base),
                pICMS=str("%.2f" % invoice_line.icms_percent),
                vICMS=str("%.2f" % invoice_line.icms_value),
                vBCFCP=None,
                pFCP=None,
                vFCP=None,
                vICMSDeson=None,
                motDesICMS=invoice_line.icms_relief_id.code or '')
        elif invoice_line.icms_cst_id.code == '30':
            icms_30 = leiauteNFe.ICMS30Type(
                orig=invoice_line.icms_origin or '',
                CST=invoice_line.icms_cst_id.code,
                modBCST=invoice_line.icms_st_base_type,
                pMVAST=str("%.2f" % invoice_line.icms_st_mva),
                pRedBCST=str("%.2f" % invoice_line.icms_st_percent_reduction),
                vBCST=str("%.2f" % invoice_line.icms_st_base),
                pICMSST=str("%.2f" % invoice_line.icms_st_percent),
                vICMSST=str("%.2f" % invoice_line.icms_st_value),
                vBCFCPST=None,
                pFCPST=None,
                vFCPST=None,
                vICMSDeson=None,
                motDesICMS=invoice_line.icms_relief_id.code or '')
        elif invoice_line.icms_cst_id.code in ('40', '41', '50'):
            icms_40 = leiauteNFe.ICMS40Type(
                orig=invoice_line.icms_origin or '',
                CST=invoice_line.icms_cst_id.code,
                vICMSDeson=None,
                motDesICMS=invoice_line.icms_relief_id.code or '')
        elif invoice_line.icms_cst_id.code == '51':
            icms_51 = leiauteNFe.ICMS51Type(
                orig=invoice_line.icms_origin or '',
                CST=invoice_line.icms_cst_id.code,
                modBC=invoice_line.icms_base_type,
                pRedBC=str("%.2f" % invoice_line.icms_percent_reduction),
                vBC=str("%.2f" % invoice_line.icms_base),
                pICMS=str("%.2f" % invoice_line.icms_percent),
                vICMSOp=None,
                pDif=None,
                vICMSDif=None,
                vICMS=str("%.2f" % invoice_line.icms_value),
                vBCFCP=None,
                pFCP=None,
                vFCP=None)
        elif invoice_line.icms_cst_id.code == '60':
            icms_60 = leiauteNFe.ICMS60Type(
                orig=invoice_line.icms_origin or '',
                CST=invoice_line.icms_cst_id.code,
                vBCSTRet=None,
                pST=None,
                vICMSSTRet=None,
                vBCFCPSTRet=None,
                pFCPSTRet=None,
                vFCPSTRet=None,
                pRedBCEfet=None,
                vBCEfet=None,
                pICMSEfet=None,
                vICMSEfet=None)
        elif invoice_line.icms_cst_id.code == '70':
            icms_70 = leiauteNFe.ICMS70Type(
                orig=invoice_line.icms_origin or '',
                CST=invoice_line.icms_cst_id.code,
                modBC=invoice_line.icms_base_type,
                pRedBC=str("%.2f" % invoice_line.icms_percent_reduction),
                vBC=str("%.2f" % invoice_line.icms_base),
                pICMS=str("%.2f" % invoice_line.icms_percent),
                vICMS=str("%.2f" % invoice_line.icms_value),
                vBCFCP=None,
                pFCP=None,
                vFCP=None,
                modBCST=invoice_line.icms_st_base_type,
                pMVAST=str("%.2f" % invoice_line.icms_st_mva),
                pRedBCST=str("%.2f" % invoice_line.icms_st_percent_reduction),
                vBCST=str("%.2f" % invoice_line.icms_st_base),
                pICMSST=str("%.2f" % invoice_line.icms_st_percent),
                vICMSST=str("%.2f" % invoice_line.icms_st_value),
                vBCFCPST=None,
                pFCPST=None,
                vFCPST=None,
                vICMSDeson=None,
                motDesICMS=invoice_line.icms_relief_id.code or '')
        elif invoice_line.icms_cst_id.code == '90':
            icms_90 = leiauteNFe.ICMS90Type(
                orig=invoice_line.icms_origin or '',
                CST=invoice_line.icms_cst_id.code,
                modBC=invoice_line.icms_base_type,
                vBC=str("%.2f" % invoice_line.icms_base),
                pRedBC=str("%.2f" % invoice_line.icms_percent_reduction),
                pICMS=str("%.2f" % invoice_line.icms_percent),
                vICMS=str("%.2f" % invoice_line.icms_value),
                vBCFCP=None,
                pFCP=None,
                vFCP=None,
                modBCST=invoice_line.icms_st_base_type,
                pMVAST=str("%.2f" % invoice_line.icms_st_mva),
                pRedBCST=str("%.2f" % invoice_line.icms_st_percent_reduction),
                vBCST=str("%.2f" % invoice_line.icms_st_base),
                pICMSST=str("%.2f" % invoice_line.icms_st_percent),
                vICMSST=str("%.2f" % invoice_line.icms_st_value),
                vBCFCPST=None,
                pFCPST=None,
                vFCPST=None,
                vICMSDeson=None,
                motDesICMS=invoice_line.icms_relief_id.code or '')
        elif invoice_line.icms_cst_id.code == '400':
            icms_sn_102 = leiauteNFe.ICMSSN102Type(
                orig=invoice_line.icms_origin or '',
                CSOSN=invoice_line.icms_cst_id.code)

        icms = leiauteNFe.ICMSType(
            ICMS00=icms_00,
            ICMS10=icms_10,
            ICMS20=icms_20,
            ICMS30=icms_30,
            ICMS40=icms_40,
            ICMS51=icms_51,
            ICMS60=icms_60,
            ICMS70=icms_70,
            ICMS90=icms_90,
            ICMSPart=icms_part,
            ICMSST=icms_st,
            ICMSSN101=icms_sn_101,
            ICMSSN102=icms_sn_102,
            ICMSSN201=icms_sn_201,
            ICMSSN202=icms_sn_202,
            ICMSSN500=icms_sn_500,
            ICMSSN900=icms_sn_900)
        return icms

    def _details(self, invoice_line, index):
        c_ean = None
        c_ean_trib = None
        if invoice_line.product_id:
            c_prod = invoice_line.product_id.code or ''
            c_ean = invoice_line.product_id.barcode or 'SEM GTIN'
            c_ean_trib = invoice_line.product_id.barcode or 'SEM GTIN'
            x_prod = normalize('NFKD', unicode(
                invoice_line.product_id.name[:120] or '')
                               ).encode('ASCII', 'ignore')
        else:
            c_prod = invoice_line.code or ''
            x_prod = normalize('NFKD', unicode(
                invoice_line.name[:120] or '')).encode('ASCII', 'ignore')

        di = []
        for inv_di in invoice_line.import_declaration_ids:
            adi = []
            for inv_di_line in inv_di.line_ids:
                adi.append(leiauteNFe.adiType(
                    nAdicao=inv_di_line.name,
                    nSeqAdic=inv_di_line.sequence,
                    cFabricante=inv_di_line.manufacturer_code,
                    vDescDI=str("%.2f" % inv_di_line.amount_discount),
                    nDraw=None))
            di.append(leiauteNFe.DIType(
                nDI=invoice_line.name,
                dDI=invoice_line.date_registration or '',
                xLocDesemb=invoice_line.location,
                UFDesemb=invoice_line.state_id.code or '',
                dDesemb=invoice_line.date_release or '',
                tpViaTransp=invoice_line.type_transportation or '',
                vAFRMM=str("%.2f" % invoice_line.afrmm_value),
                tpIntermedio=invoice_line.type_import or '',
                CNPJ=invoice_line.exporting_code or '',
                UFTerceiro=invoice_line.thirdparty_state_id.code or '',
                cExportador=invoice_line.exporting_code,
                adi=adi))

        prod = leiauteNFe.prodType(
            cProd=c_prod,
            cEAN=c_ean,
            xProd=x_prod,
            NCM=punctuation_rm(
                invoice_line.fiscal_classification_id.code or '')[:8],
            NVE=None,
            CEST=punctuation_rm(invoice_line.cest_id.code or '') or None,
            indEscala=None,
            CNPJFab=None,
            cBenef=None,
            EXTIPI=punctuation_rm(
                invoice_line.fiscal_classification_id.code or '')[8:] or None,
            CFOP=invoice_line.cfop_id.code,
            uCom=invoice_line.uom_id.name or '',
            qCom=str("%.4f" % invoice_line.quantity),
            vUnCom=str("%.7f" % invoice_line.price_unit),
            vProd=str("%.2f" % invoice_line.price_gross),
            cEANTrib=c_ean_trib,
            uTrib=invoice_line.uom_id.name or '',
            qTrib=str("%.4f" % invoice_line.quantity),
            vUnTrib=str("%.7f" % invoice_line.price_unit),
            vFrete=str("%.2f" % invoice_line.freight_value)
            if invoice_line.freight_value else None,
            vSeg=str("%.2f" % invoice_line.insurance_value)
            if invoice_line.insurance_value else None,
            vDesc=str("%.2f" % invoice_line.discount_value)
            if invoice_line.discount_value else None,
            vOutro=str("%.2f" % invoice_line.other_costs_value)
            if invoice_line.other_costs_value else None,
            indTot='1',
            DI=di,
            detExport=None,
            xPed=invoice_line.partner_order or None,
            nItemPed=invoice_line.partner_order_line or None,
            nFCI=invoice_line.fci or None,
            rastro=None,
            veicProd=None,
            med=None,
            arma=None,
            comb=None,
            nRECOPI=None)

        icms = None
        icms_uf_dest = None
        ipi = None
        issqn = None
        if invoice_line.product_type == 'product':
            icms = self._icms(invoice_line)
            if invoice_line.icms_dest_base:
                icms_uf_dest = leiauteNFe.ICMSUFDestType(
                    vBCUFDest=str("%.2f" % invoice_line.icms_dest_base),
                    vBCFCPUFDest=None,
                    pFCPUFDest=str("%.2f" % invoice_line.icms_fcp_percent),
                    pICMSUFDest=str("%.2f" % invoice_line.icms_dest_percent),
                    pICMSInter=str("%.2f" % invoice_line.icms_origin_percent),
                    pICMSInterPart=str("%.2f" % invoice_line.icms_part_percent),
                    vFCPUFDest=str("%.2f" % invoice_line.icms_fcp_value),
                    vICMSUFDest=str("%.2f" % invoice_line.icms_dest_value),
                    vICMSUFRemet=str("%.2f" % invoice_line.icms_origin_value))

            v_bc = None
            p_ipi = None
            q_unid = None
            v_unid = None
            if invoice_line.ipi_type == 'percent' or '':
                v_bc = str("%.2f" % invoice_line.ipi_base)
                p_ipi = str("%.2f" % invoice_line.ipi_percent)
            if invoice_line.ipi_type == 'quantity':
                if invoice_line.product_id:
                    pesol = invoice_line.product_id.weight_net
                    q_unid = str("%.2f" % invoice_line.quantity * pesol)
                    v_unid = str("%.2f" % invoice_line.ipi_percent)
            ipi_trib = leiauteNFe.IPITribType(
                CST=invoice_line.ipi_cst_id.code,
                vBC=v_bc,
                pIPI=p_ipi,
                qUnid=q_unid,
                vUnid=v_unid,
                vIPI=str("%.2f" % invoice_line.ipi_value))
            ipi = leiauteNFe.TIpi(
                CNPJProd=None,
                cSelo=None,
                qSelo=None,
                cEnq=str(invoice_line.ipi_guideline_id.code or '999').zfill(3),
                IPITrib=ipi_trib,
                IPINT=None)
        else:
            issqn = leiauteNFe.ISSQNType(
                vBC=str("%.2f" % invoice_line.issqn_base),
                vAliq=str("%.2f" % invoice_line.issqn_percent),
                vISSQN=str("%.2f" % invoice_line.issqn_value),
                cMunFG=('%s%s') % (
                    self.partner_id.state_id.ibge_code,
                    self.partner_id.l10n_br_city_id.ibge_code),
                cListServ=punctuation_rm(
                    invoice_line.service_type_id.code or ''),
                vDeducao=None,
                vOutro=None,
                vDescIncond=None,
                vDescCond=None,
                vISSRet=None,
                indISS=None,
                cServico=None,
                cMun=None,
                cPais=None,
                nProcesso=None,
                indIncentivo=None)

        pis_aliq = None
        pis_qtde = None
        pisnt = None
        pis_ourt = None
        if invoice_line.pis_cst_id.code in ('01', '02'):
            pis_aliq = leiauteNFe.PISAliqType(
                CST=invoice_line.pis_cst_id.code,
                vBC=str("%.2f" % invoice_line.pis_base),
                pPIS=str("%.2f" % invoice_line.pis_percent),
                vPIS=str("%.2f" % invoice_line.pis_value))
        elif invoice_line.pis_cst_id.code == '03':
            pis_qtde = leiauteNFe.PISQtdeType(
                CST=invoice_line.pis_cst_id.code,
                qBCProd=None,
                vAliqProd=None,
                vPIS=str("%.2f" % invoice_line.pis_value))
        elif invoice_line.pis_cst_id.code in ('04', '06', '07', '08', '09'):
            pisnt = leiauteNFe.PISNTType(
                CST=invoice_line.pis_cst_id.code)
        else:
            pis_ourt = leiauteNFe.PISOutrType(
                CST=invoice_line.pis_cst_id.code,
                vBC=str("%.2f" % invoice_line.pis_base),
                pPIS=str("%.2f" % invoice_line.pis_percent),
                qBCProd=None,
                vAliqProd=None,
                vPIS=str("%.2f" % invoice_line.pis_value))
        pis = leiauteNFe.PISType(
            PISAliq=pis_aliq,
            PISQtde=pis_qtde,
            PISNT=pisnt,
            PISOutr=pis_ourt)

        pisst = None
        if invoice_line.pis_st_base:
            pisst = leiauteNFe.PISSTType(
                vBC=str("%.2f" % invoice_line.pis_st_base),
                pPIS=str("%.2f" % invoice_line.pis_st_percent),
                qBCProd='',
                vAliqProd='',
                vPIS=str("%.2f" % invoice_line.pis_st_value))

        cofins_aliq = None
        cofins_qtde = None
        cofinsnt = None
        cofins_outr = None
        if invoice_line.cofins_cst_id.code in ('01', '02'):
            cofins_aliq = leiauteNFe.COFINSAliqType(
                CST=invoice_line.cofins_cst_id.code,
                vBC=str("%.2f" % invoice_line.cofins_base),
                pCOFINS=str("%.2f" % invoice_line.cofins_percent),
                vCOFINS=str("%.2f" % invoice_line.cofins_value))
        elif invoice_line.cofins_cst_id.code == '03':
            cofins_qtde = leiauteNFe.COFINSQtdeType(
                CST=invoice_line.cofins_cst_id.code,
                qBCProd=None,
                vAliqProd=None,
                vCOFINS=str("%.2f" % invoice_line.cofins_value))
        elif invoice_line.cofins_cst_id.code in (
                '04', '06', '07', '08', '09'):
            cofinsnt = leiauteNFe.COFINSNTType(
                CST=invoice_line.cofins_cst_id.code)
        else:
            cofins_outr = leiauteNFe.COFINSOutrType(
                CST=invoice_line.cofins_cst_id.code,
                vBC=str("%.2f" % invoice_line.cofins_base),
                pCOFINS=str("%.2f" % invoice_line.cofins_percent),
                qBCProd=None,
                vAliqProd=None,
                vCOFINS=str("%.2f" % invoice_line.cofins_value))
        cofins = leiauteNFe.COFINSType(
            COFINSAliq=cofins_aliq,
            COFINSQtde=cofins_qtde,
            COFINSNT=cofinsnt,
            COFINSOutr=cofins_outr)

        cofinsst = None
        if invoice_line.cofins_st_base:
            cofinsst = leiauteNFe.COFINSSTType(
                vBC=str("%.2f" % invoice_line.cofins_st_base),
                pCOFINS=str("%.2f" % invoice_line.cofins_st_percent),
                qBCProd='',
                vAliqProd='',
                vCOFINS=str("%.2f" % invoice_line.cofins_st_value))

        ii = None
        if invoice_line.ii_base:
            ii = leiauteNFe.IIType(
                vBC=str("%.2f" % invoice_line.ii_base),
                vDespAdu=str(
                    "%.2f" % invoice_line.ii_customhouse_charges),
                vII=str("%.2f" % invoice_line.ii_value),
                vIOF=str("%.2f" % invoice_line.ii_iof))

        imposto = leiauteNFe.impostoType(
            vTotTrib=str("%.2f" % invoice_line.total_taxes),
            ICMS=icms,
            II=ii,
            IPI=ipi,
            ISSQN=issqn,
            PIS=pis,
            PISST=pisst,
            COFINS=cofins,
            COFINSST=cofinsst,
            ICMSUFDest=icms_uf_dest)
        det = leiauteNFe.detType(
            nItem=index,
            prod=prod,
            imposto=imposto,
            impostoDevol=None,
            infAdProd=invoice_line.fiscal_comment or None)
        return det

    def serialize_nfe(self):
        company = self.company_id.partner_id

        if self.cfop_ids[0].type in ("input"):
            tpNF = '0'
        else:
            tpNF = '1'

        nf_ref = []
        for inv_related in self.fiscal_document_related_ids:
            ref_nf = None
            ref_nfp = None
            ref_nfe = None
            ref_cte = None
            ref_ecf = None
            if inv_related.document_type == 'nf':
                ref_nf = leiauteNFe.refNFType(
                    cUF=inv_related.state_id and
                        inv_related.state_id.ibge_code or '',
                    AAMM=datetime.strptime(
                        inv_related.date, '%Y-%m-%d').strftime('%y%m') or '',
                    CNPJ=punctuation_rm(inv_related.cnpj_cpf),
                    mod=inv_related.fiscal_document_id and
                        inv_related.fiscal_document_id.code or '',
                    serie=inv_related.serie or '',
                    nNF=inv_related.internal_number or '')
            elif inv_related.document_type == 'nfrural':
                cnpj = None
                cpf = None
                if inv_related.cpfcnpj_type == 'cnpj':
                    cnpj = punctuation_rm(inv_related.cnpj_cpf)
                else:
                    cpf = punctuation_rm(inv_related.cnpj_cpf)
                ref_nfp = leiauteNFe.refNFPType(
                    cUF=inv_related.state_id and
                        inv_related.state_id.ibge_code or '',
                    AAMM=datetime.strptime(
                        inv_related.date, '%Y-%m-%d').strftime('%y%m') or '',
                    CNPJ=cnpj,
                    CPF=cpf,
                    IE=punctuation_rm(inv_related.inscr_est),
                    mod=inv_related.fiscal_document_id and
                        inv_related.fiscal_document_id.code or '',
                    serie=inv_related.serie or '',
                    nNF=inv_related.internal_number or '')
            elif inv_related.document_type == 'nfe':
                ref_nfe = inv_related.access_key or ''
            elif inv_related.document_type == 'cte':
                ref_cte = inv_related.access_key or ''
            elif inv_related.document_type == 'cf':
                ref_ecf = leiauteNFe.refECFType(
                    mod=inv_related.fiscal_document_id and
                        inv_related.fiscal_document_id.code or '',
                    nECF=inv_related.internal_number or '',
                    nCOO=inv_related.serie or '')
            nf_ref.append(leiauteNFe.NFrefType(
                refNFe=ref_nfe,
                refNF=ref_nf,
                refNFP=ref_nfp,
                refCTe=ref_cte,
                refECF=ref_ecf)
            )

        if not self.edoc_access_key:
            self.gera_nova_chave()

        dh_emi = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date_hour_invoice)
        ).isoformat('T')

        dh_sai_ent = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(self.date_in_out)
        ).isoformat('T')

        ide = leiauteNFe.ideType(
            cUF=(company.state_id and company.state_id.ibge_code or ''),
            cNF=self.edoc_access_key[35:43],
            natOp=self.fiscal_category_id.name[:60] or '',
            mod=self.fiscal_document_id.code or '',
            serie=self.document_serie_id.code or '',
            nNF=self.fiscal_number or '',
            dhEmi=dh_emi,
            dhSaiEnt=dh_sai_ent,
            tpNF=tpNF,
            idDest=self.fiscal_position_id.cfop_id.id_dest or '',
            cMunFG=('%s%s') % (
                company.state_id.ibge_code,
                company.l10n_br_city_id.ibge_code),
            tpImp='1',
            tpEmis='1',
            cDV=self.edoc_access_key[-1],
            tpAmb=self.company_id.nfe_environment,
            finNFe=self.edoc_purpose,
            indFinal=self.ind_final or '',
            indPres=self.ind_pres or '',
            procEmi='0',
            verProc='Odoo Brasil v10.0',
            dhCont=None,
            xJust=None,
            NFref=nf_ref
        )

        if company.country_id.name.lower() == 'brazil':
            x_pais = 'Brasil'
        else:
            x_pais = company.country_id.name
        ender_emit = leiauteNFe.TEnderEmi(
            xLgr=normalize('NFKD', unicode(company.street or '')
                           ).encode('ASCII', 'ignore'),
            nro=company.number or '',
            # xCpl=normalize('NFKD', unicode(company.street2 or '')
            #                ).encode('ASCII', 'ignore'),
            xBairro=normalize('NFKD',
                              unicode(company.district or 'Sem Bairro')
                              ).encode('ASCII', 'ignore'),
            cMun='%s%s' % (company.state_id.ibge_code,
                           company.l10n_br_city_id.ibge_code),
            xMun=normalize('NFKD', unicode(company.l10n_br_city_id.name or '')
                           ).encode('ASCII', 'ignore'),
            UF=company.state_id.code or '',
            CEP=punctuation_rm(company.zip or ''),
            cPais=company.country_id.bc_code[1:],
            xPais=x_pais,
            fone=punctuation_rm(str(company.phone or '').replace(' ', '')))
        iest = None
        for inscr_est_line in \
                self.company_id.partner_id.other_inscr_est_lines:
            if inscr_est_line.state_id.id == self.partner_id.state_id.id:
                iest = punctuation_rm(inscr_est_line.inscr_est)
            else:
                iest = ''
        if company.inscr_mun:
            cnae = punctuation_rm(self.company_id.cnae_main_id.code or '')
        else:
            cnae = None
        emit = leiauteNFe.emitType(
            CNPJ=punctuation_rm(self.company_id.partner_id.cnpj_cpf),
            CPF=None,
            xNome=normalize('NFKD', unicode(
                self.company_id.partner_id.legal_name[:60])).encode(
                'ASCII', 'ignore'),
            xFant=company.name,
            enderEmit=ender_emit,
            IE=punctuation_rm(self.company_id.partner_id.inscr_est),
            IEST=iest,
            IM=punctuation_rm(self.company_id.partner_id.inscr_mun or ''
                              ) or None,
            CNAE=cnae,
            CRT=self.company_id.fiscal_type or '')

        dest = self._dest()

        retirada = None
        entrega = None
        if self.partner_shipping_id and \
                self.partner_id != self.partner_shipping_id:
            local = leiauteNFe.TLocal(
                CNPJ=punctuation_rm(self.partner_shipping_id.cnpj_cpf),
                CPF=None,
                xLgr=self.partner_shipping_id.street or '',
                nro=self.partner_shipping_id.number or '',
                # xCpl=self.partner_shipping_id.street2 or '',
                xBairro=self.partner_shipping_id.district or 'Sem Bairro',
                cMun='%s%s' % (
                    self.partner_shipping_id.state_id.ibge_code,
                    self.partner_shipping_id.l10n_br_city_id.ibge_code),
                xMun=self.partner_shipping_id.l10n_br_city_id.name or '',
                UF=self.partner_shipping_id.state_id.code or '')
            if tpNF == '0':
                retirada = local
            else:
                entrega = local

        det = []
        i = 0
        for inv_line in self.invoice_line_ids:
            i += 1
            det.append(self._details(inv_line, i))

        cobr = None
        if FORMA_PAGAMENTO_SEM_PAGAMENTO not in \
                self.account_payment_ids.mapped('forma_pagamento'):
            fat = leiauteNFe.fatType(
                nFat=self.number,
                vOrig=str("%.2f" % self.amount_payment_original),
                vDesc=str("%.2f" % self.amount_payment_discount),
                vLiq=str("%.2f" % self.amount_payment_net))

            dup = []
            for payment_line in self.account_payment_line_ids:
                dup.append(leiauteNFe.dupType(
                    nDup=payment_line.number,
                    dVenc=payment_line.date_due,
                    vDup=str("%.2f" % payment_line.amount_net)))

            cobr = leiauteNFe.cobrType(fat=fat, dup=dup)

        transporta = None
        if hasattr(self, 'carrier_id') and self.carrier_id:
            cnpj = None
            cpf = None
            if self.carrier_id.partner_id.is_company:
                cnpj = punctuation_rm(
                    self.carrier_id.partner_id.cnpj_cpf or '')
            else:
                cpf = punctuation_rm(
                    self.carrier_id.partner_id.cnpj_cpf or '')
            transporta = leiauteNFe.transportaType(
                CNPJ=cnpj,
                CPF=cpf,
                xNome=self.carrier_id.partner_id.legal_name[:60] or '',
                IE=punctuation_rm(self.carrier_id.partner_id.inscr_est),
                xEnder=((self.carrier_id.partner_id.street or '') + ', ' +
                        (self.carrier_id.partner_id.number or '') + ', ' +
                        (self.carrier_id.partner_id.district or ''))[:60],
                xMun=self.carrier_id.partner_id.l10n_br_city_id.name or '',
                UF=self.carrier_id.partner_id.state_id.code or '')

        veic_transp = None
        if hasattr(self, 'vehicle_id') and self.vehicle_id:
            veic_transp = leiauteNFe.TVeiculo(
                placa=self.vehicle_id.plate or '',
                UF=self.vehicle_id.plate.state_id.code or '',
                RNTC=self.vehicle_id.rntc_code or '')

        vol = []
        if self.number_of_packages:
            vol.append(leiauteNFe.volType(
                qVol=self.number_of_packages or '',
                esp=self.kind_of_packages or '',
                marca=self.brand_of_packages or '',
                nVol=self.notation_of_packages or '',
                pesoL=str("%.2f" % self.weight_net),
                pesoB=str("%.2f" % self.weight),
                lacres=None))

        transp = leiauteNFe.transpType(
            modFrete=(self.incoterm and self.incoterm.freight_responsibility
                      or '9') if hasattr(self, 'incoterm') else '0',
            transporta=transporta,
            retTransp=None,
            veicTransp=veic_transp,
            reboque=None,
            vagao=None,
            balsa=None,
            vol=vol)

        det_pag = []
        for pagamento in self.account_payment_ids:
            card = None
            if pagamento.forma_pagamento in FORMA_PAGAMENTO_CARTOES:
                card = leiauteNFe.cardType(
                    tpIntegra=pagamento.card_integration,
                    CNPJ=punctuation_rm(pagamento.cnpj_cpf or ''),
                    tBand=pagamento.card_brand,
                    cAut=pagamento.autorizacao)
            det_pag.append(leiauteNFe.detPagType(
                indPag=None,
                tPag=pagamento.forma_pagamento,
                vPag=str("%.2f" % pagamento.amount),
                card=card))

        pag = leiauteNFe.pagType(
            detPag=det_pag,
            vTroco=str("%.2f" % self.amount_change)
            if self.amount_change else None)

        inf_adic = None
        if self.fiscal_comment or self.comment:
            inf_adic = leiauteNFe.infAdicType(
                infAdFisco=self.fiscal_comment or '',
                infCpl=self.comment or '',
                obsCont=None,
                obsFisco=None,
                procRef=None)

        icms_tot = leiauteNFe.ICMSTotType(
            vBC=str("%.2f" % self.icms_base),
            vICMS=str("%.2f" % self.icms_value),
            vICMSDeson=str("%.2f" % 0.00),
            vFCPUFDest=str("%.2f" % self.icms_fcp_value)
            if self.icms_fcp_value else None,
            vICMSUFDest=str("%.2f" % self.icms_dest_value)
            if self.icms_dest_value else None,
            vICMSUFRemet=str("%.2f" % self.icms_origin_value)
            if self.icms_origin_value else None,
            vFCP=str("%.2f" % 0.00),
            vBCST=str("%.2f" % self.icms_st_base),
            vST=str("%.2f" % self.icms_st_value),
            vFCPST=str("%.2f" % 0.00),
            vFCPSTRet=str("%.2f" % 0.00),
            vProd=str("%.2f" % self.amount_gross),
            vFrete=str("%.2f" % self.amount_freight),
            vSeg=str("%.2f" % self.amount_insurance),
            vDesc=str("%.2f" % self.amount_discount),
            vII=str("%.2f" % self.ii_value),
            vIPI=str("%.2f" % self.ipi_value),
            vIPIDevol=str("%.2f" % 0.00),
            vPIS=str("%.2f" % self.pis_value),
            vCOFINS=str("%.2f" % self.cofins_value),
            vOutro=str("%.2f" % self.amount_costs),
            vNF=str("%.2f" % self.amount_total),
            vTotTrib=str("%.2f" % self.amount_total_taxes)
            if self.amount_total_taxes else None)

        total = leiauteNFe.totalType(
            ICMSTot=icms_tot,
            ISSQNtot=None,
            retTrib=None)

        exporta = None
        if False:
            exporta = leiauteNFe.exportaType(
                UFSaidaPais=None,
                xLocExporta=None,
                xLocDespacho=None)
        # UFEmbarq
        # xLocEmbarq

        if self.company_id.accountant_cnpj_cpf:
            aut_xml = [leiauteNFe.autXMLType(
                CNPJ=punctuation_rm(self.company_id.accountant_cnpj_cpf
                                    ) or None,
                CPF=None)]
        else:
            aut_xml = None

        inf_nfe = leiauteNFe.infNFeType(
            versao='4.00',
            Id='NFe' + self.edoc_access_key,
            ide=ide,
            emit=emit,
            avulsa=None,
            dest=dest,
            retirada=retirada,
            entrega=entrega,
            autXML=aut_xml,
            det=det,
            total=total,
            transp=transp,
            cobr=cobr,
            pag=pag,
            infAdic=inf_adic,
            exporta=exporta,
            compra=None,
            cana=None)

        tnfe = leiauteNFe.TNFe(
            infNFe=inf_nfe,
            infNFeSupl=None,
            Signature=None)
        tnfe.original_tagname_ = 'NFe'

        return tnfe

    def gera_nova_chave(self):
        company = self.company_id.partner_id
        chave = str(company.state_id and
                    company.state_id.ibge_code or '').zfill(2)

        chave += str(datetime.strptime(
            self.date_hour_invoice, '%Y-%m-%d %H:%M:%S').strftime('%y%m')
                     ).zfill(4)

        chave += str(punctuation_rm(
            self.company_id.partner_id.cnpj_cpf)).zfill(14)
        chave += str(self.fiscal_document_id.code or '').zfill(2)
        chave += str(self.document_serie_id.code or '').zfill(3)
        chave += str(self.fiscal_number or '').zfill(9)

        #
        # A inclusão do tipo de emissão na chave já torna a chave válida também
        # para a versão 2.00 da NF-e
        #
        chave += str(1).zfill(1)

        #
        # O código numério é um número aleatório
        #
        # chave += str(random.randint(0, 99999999)).strip().rjust(8, '0')

        #
        # Mas, por segurança, é preferível que esse número não seja
        # aleatório de todo
        #
        soma = 0
        for c in chave:
            soma += int(c) ** 3 ** 2

        codigo = str(soma)
        if len(codigo) > 8:
            codigo = codigo[-8:]
        else:
            codigo = codigo.rjust(8, '0')

        chave += codigo

        soma = 0
        m = 2
        for i in range(len(chave) - 1, -1, -1):
            c = chave[i]
            soma += int(c) * m
            m += 1
            if m > 9:
                m = 2

        digito = 11 - (soma % 11)
        if digito > 9:
            digito = 0

        chave += str(digito)
        self.edoc_access_key = chave

    def _serialize(self, edocs):
        edocs = super(AccountInvoice, self)._serialize(edocs)
        for record in self.filtered(fiter_processador_edoc_nfe):
            edocs.append(record.serialize_nfe())
        return edocs

    def _procesador(self):
        certificado = Certificado(
            arquivo=self.company_id.nfe_a1_file,
            senha=self.company_id.nfe_a1_password
        )
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(certificado, session)
        return NFe(transmissao)

    @api.multi
    def _edoc_export(self):
        super(AccountInvoice, self)._edoc_export()
        for record in self.filtered(fiter_processador_edoc_nfe):
            edoc = record.serialize()[0]
            procesador = record._procesador()
            xml_file = procesador._generateds_to_string_etree(edoc)[0]
            event_id = self._gerar_evento(xml_file, type="0")
            record.autorizacao_event_id = event_id
            record._change_state(SITUACAO_EDOC_A_ENVIAR)

    def atualiza_status_nfe(self, infProt):
        self.ensure_one()
        documento = self
        if not infProt.chNFe == self.edoc_access_key:
            documento = self.search([
                ('edoc_access_key', '=', infProt.chNFe)
            ])

        if infProt.cStat in AUTORIZADO:
            state = SITUACAO_EDOC_AUTORIZADA
        elif infProt.cStat in DENEGADO:
            state = SITUACAO_EDOC_DENEGADA
        else:
            state = SITUACAO_EDOC_REJEITADA

        self._change_state(state)

        documento.write({
            'edoc_access_key': infProt.chNFe,
            'edoc_status_code': infProt.cStat,
            'edoc_status_message': infProt.xMotivo,
            'edoc_date': infProt.dhRecbto,
            'edoc_protocol_number': infProt.nProt,
            # 'nfe_access_key': infProt.tpAmb,
            # 'nfe_access_key': infProt.digVal,
            # 'nfe_access_key': infProt.xMsg,
        })

    @api.multi
    def _edoc_send(self):
        super(AccountInvoice, self)._edoc_send()
        for record in self.filtered(fiter_processador_edoc_nfe):
            procesador = record._procesador()
            for edoc in record.serialize():
                processo = None
                for p in procesador.processar_documento(edoc):
                    processo = p

            if processo.resposta.cStat in LOTE_PROCESSADO:
                for protocolo in processo.resposta.protNFe:
                    record.atualiza_status_nfe(protocolo.infProt)
        return

    @api.multi
    def cancel_invoice_online(self, justificative):
        super(AccountInvoice, self).cancel_invoice_online(justificative)
        for record in self.filtered(fiter_processador_edoc_nfe):
            if record.state in ('open', 'paid'):
                processador = record._procesador()

                evento = processador.cancela_documento(
                    chave=record.edoc_access_key,
                    protocolo_autorizacao=record.edoc_protocol_number,
                    justificativa=justificative
                )
                processo = processador.enviar_lote_evento(
                    lista_eventos=[evento]
                )

                for retevento in processo.resposta.retEvento:
                    if not retevento.infEvento.chNFe == record.edoc_access_key:
                        continue

                    if retevento.infEvento.cStat not in CANCELADO:
                        mensagem = 'Erro no cancelamento'
                        mensagem += '\nCódigo: ' + \
                                    retevento.infEvento.cStat
                        mensagem += '\nMotivo: ' + \
                                    retevento.infEvento.xMotivo
                        raise UserError(mensagem)

                    if retevento.infEvento.cStat == '155':
                        record.state_fiscal = SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO
                        record.state_edoc = SITUACAO_EDOC_CANCELADA
                    elif retevento.infEvento.cStat == '135':
                        record.state_fiscal = SITUACAO_FISCAL_CANCELADO
                        record.state_edoc = SITUACAO_EDOC_CANCELADA

    def cce_invoice_online(self, justificative):
        super(AccountInvoice, self).cce_invoice_online(justificative)
        for record in self.filtered(fiter_processador_edoc_nfe):
            if record.state in ('open', 'paid'):
                processador = record._procesador()

                evento = processador.carta_correcao(
                    chave=record.edoc_access_key,
                    sequencia='1',
                    justificativa=justificative
                )
                processo = processador.enviar_lote_evento(
                    lista_eventos=[evento]
                )
                pass
