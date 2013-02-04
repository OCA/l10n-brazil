# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from lxml import etree
from lxml.etree import ElementTree
from lxml.etree import Element, SubElement, Comment, tostring
import time
from datetime import datetime
import netsvc
import string
from unicodedata import normalize

from osv import fields, osv
from tools.translate import _
import pooler


def nfe_dv(key):
        #Testing
        return '0'


def nfe_export(cr, uid, ids, nfe_environment='1', context=False):
    pool = pooler.get_pool(cr.dbname)
    nfeProc = Element('nfeProc', {'versao': '2.00', 'xmlns': 'http://www.portalfiscal.inf.br/nfe' })

    for inv in pool.get('account.invoice').browse(cr, uid, ids, context={'lang': 'pt_BR'}):

        #Endereço do company
        company_addr = pool.get('res.partner').address_get(cr, uid, [inv.company_id.partner_id.id], ['default'])
        company_addr_default = pool.get('res.partner.address').browse(cr, uid, [company_addr['default']], context={'lang': 'pt_BR'})[0]

        #MontaChave da Nota Fiscal Eletronica
        nfe_key = unicode(company_addr_default.state_id.ibge_code).strip().rjust(2, u'0')
        nfe_key += unicode(datetime.strptime(inv.date_invoice, '%Y-%m-%d').strftime(u'%y%m')).strip().rjust(4, u'0')
        nfe_key +=  '08478495000170' # unicode(inv.company_id.partner_id.cnpj_cpf).strip().rjust(14, u'0')
        nfe_key += inv.fiscal_document_id.code
        nfe_key += unicode(inv.document_serie_id.code).strip().rjust(3, u'0')
        nfe_key += unicode(inv.internal_number).strip().rjust(9, u'0')
        nfe_key += unicode('1').strip().rjust(1, u'0') # Homologação
        nfe_key += unicode(inv.internal_number).strip().rjust(8, u'0')
        nfe_key += unicode(nfe_dv(nfe_key)).strip().rjust(1, u'0')

        NFe = SubElement(nfeProc, 'NFe', { 'xmlns': 'http://www.portalfiscal.inf.br/nfe' })

        infNFe = SubElement(NFe, 'infNFe', {'versao': '2.00', 'Id': nfe_key })

        # Dados da identificação da nota fiscal
        ide = SubElement(infNFe, 'ide')

        ide_cUF = SubElement(ide, 'cUF')
        ide_cUF.text = company_addr_default.state_id.ibge_code

        ide_cNF = SubElement(ide, 'cNF')
        ide_cNF.text = unicode(inv.internal_number).strip().rjust(8, u'0')

        ide_natOp = SubElement(ide, 'natOp')
        ide_natOp.text = inv.cfop_ids[0].name

        ide_indPag = SubElement(ide, 'indPag')
        ide_indPag.text = "2"

        ide_mod = SubElement(ide, 'mod')
        ide_mod.text = inv.fiscal_document_id.code

        ide_serie = SubElement(ide, 'serie')
        ide_serie.text = inv.document_serie_id.code

        ide_nNF = SubElement(ide, 'nNF')
        ide_nNF.text = inv.internal_number

        ide_dEmi = SubElement(ide, 'dEmi')
        ide_dEmi.text = inv.date_invoice

        ide_dSaiEnt = SubElement(ide, 'dSaiEnt')
        ide_dSaiEnt.text = inv.date_invoice

        ide_tpNF = SubElement(ide, 'tpNF')
        if inv.type in ("out_invoice", "in_refuld"):
            ide_tpNF.text = '0'
        else:
            ide_tpNF.text = '1'

        ide_cMunFG = SubElement(ide, 'cMunFG')
        ide_cMunFG.text = ('%s%s') % (company_addr_default.state_id.ibge_code, company_addr_default.l10n_br_city_id.ibge_code)

        ide_tpImp = SubElement(ide, 'tpImp')
        ide_tpImp.text = "1"

        ide_tpEmis = SubElement(ide, 'tpEmis')
        ide_tpEmis.text = "1"

        ide_cDV = SubElement(ide, 'cDV')
        ide_cDV.text = nfe_dv(nfe_key)

        #Tipo de ambiente: 1 - Produção; 2 - Homologação
        ide_tpAmb = SubElement(ide, 'tpAmb')
        ide_tpAmb.text = "2"

        #Finalidade da emissão da NF-e: 1 - NFe normal 2 - NFe complementar 3 - NFe de ajuste
        ide_finNFe = SubElement(ide, 'finNFe')
        ide_finNFe.text = "1"

        ide_procEmi = SubElement(ide, 'procEmi')
        ide_procEmi.text = "0"

        ide_verProc = SubElement(ide, 'verProc')
        ide_verProc.text = "2.0.4"

        emit = SubElement(infNFe, 'emit')

        emit_CNPJ = SubElement(emit, 'CNPJ')
        emit_CNPJ.text = inv.company_id.partner_id.cnpj_cpf

        emit_xNome = SubElement(emit, 'xNome')
        emit_xNome.text = inv.company_id.partner_id.legal_name

        emit_xFant = SubElement(emit, 'xFant')
        emit_xFant.text = inv.company_id.partner_id.name

        enderEmit = SubElement(emit, 'enderEmit')

        enderEmit_xLgr = SubElement(enderEmit, 'xLgr')
        enderEmit_xLgr.text = company_addr_default.street

        enderEmit_nro = SubElement(enderEmit, 'nro')
        enderEmit_nro.text = company_addr_default.number

        enderEmit_xBairro = SubElement(enderEmit, 'xBairro')
        enderEmit_xBairro.text = company_addr_default.district

        enderEmit_cMun = SubElement(enderEmit, 'cMun')
        enderEmit_cMun.text = ('%s%s') % (company_addr_default.state_id.ibge_code, company_addr_default.l10n_br_city_id.ibge_code)

        enderEmit_xMun = SubElement(enderEmit, 'xMun')
        enderEmit_xMun.text = company_addr_default.l10n_br_city_id.name

        enderEmit_UF = SubElement(enderEmit, 'UF')
        enderEmit_UF.text = company_addr_default.state_id.code

        enderEmit_CEP = SubElement(enderEmit, 'CEP')
        enderEmit_CEP.text = company_addr_default.zip

        enderEmit_cPais = SubElement(enderEmit, 'cPais')
        enderEmit_cPais.text = company_addr_default.country_id.bc_code

        enderEmit_xPais = SubElement(enderEmit, 'xPais')
        enderEmit_xPais.text = company_addr_default.country_id.name

        enderEmit_fone = SubElement(enderEmit, 'fone')
        enderEmit_fone.text = company_addr_default.phone or ''

        emit_IE = SubElement(emit, 'IE')
        emit_IE.text = inv.company_id.partner_id.inscr_est

        emit_IEST = SubElement(emit, 'IEST')
        emit_IEST.text = '0000000000' #FIXME

        emit_IM = SubElement(emit, 'IM')
        emit_IM.text = '0000000000' #FIXME

        emit_CNAE = SubElement(emit, 'CNAE')
        emit_CNAE.text = '0111301'  #FIXME

        emit_CRT = SubElement(emit, 'CRT')
        emit_CRT.text = '3'  #FIXME

        dest = SubElement(infNFe, 'dest')

        dest_CNPJ = SubElement(dest, 'CNPJ')
        dest_CNPJ.text = inv.partner_id.cnpj_cpf

        dest_xNome = SubElement(dest, 'xNome')
        dest_xNome.text = inv.partner_id.legal_name

        enderDest = SubElement(dest, 'enderDest')

        enderDest_xLgr = SubElement(enderDest, 'xLgr')
        enderDest_xLgr.text = inv.address_invoice_id.street

        enderDest_nro = SubElement(enderDest, 'nro')
        enderDest_nro.text = inv.address_invoice_id.number

        enderDest_xBairro = SubElement(enderDest, 'xBairro')
        enderDest_xBairro.text = inv.address_invoice_id.district

        enderDest_cMun = SubElement(enderDest, 'cMun')
        enderDest_cMun.text = ('%s%s') % (inv.address_invoice_id.state_id.ibge_code, inv.address_invoice_id.l10n_br_city_id.ibge_code)

        enderDest_xMun = SubElement(enderDest, 'xMun')
        enderDest_xMun.text = inv.address_invoice_id.l10n_br_city_id.name

        enderDest_UF = SubElement(enderDest, 'UF')
        enderDest_UF.text = inv.address_invoice_id.state_id.code

        enderDest_CEP = SubElement(enderDest, 'CEP')
        enderDest_CEP.text = inv.address_invoice_id.zip

        enderDest_cPais = SubElement(enderDest, 'cPais')
        enderDest_cPais.text = inv.address_invoice_id.country_id.bc_code

        enderDest_xPais = SubElement(enderDest, 'xPais')
        enderDest_xPais.text = inv.address_invoice_id.country_id.name

        enderDest_fone = SubElement(enderDest, 'fone')
        enderDest_fone.text = inv.address_invoice_id.phone

        dest_IE = SubElement(dest, 'IE')
        dest_IE.text = inv.partner_id.inscr_est

        i = 0
        for inv_line in inv.invoice_line:
            i += 1
            det = SubElement(infNFe, 'det', {'nItem': str(i)})

            det_prod = SubElement(det, 'prod')

            prod_cProd = SubElement(det_prod, 'cProd')
            if inv_line.product_id.code:
                prod_cProd.text = inv_line.product_id.code
            else:
                prod_cProd.text = unicode(i).strip().rjust(4, u'0')

            prod_cEAN = SubElement(det_prod, 'cEAN')
            prod_cEAN.text = inv_line.product_id.ean13 or ''

            prod_xProd = SubElement(det_prod, 'xProd')
            prod_xProd.text = inv_line.product_id.name

            prod_NCM = SubElement(det_prod, 'NCM')
            prod_NCM.text = inv_line.product_id.property_fiscal_classification.name

            prod_CFOP = SubElement(det_prod, 'CFOP')
            prod_CFOP.text = inv_line.cfop_id.code

            prod_uCom = SubElement(det_prod, 'uCom')
            prod_uCom.text = inv_line.uos_id.name

            prod_qCom = SubElement(det_prod, 'qCom')
            prod_qCom.text = str("%.4f" % inv_line.quantity)

            prod_vUnCom = SubElement(det_prod, 'vUnCom')
            prod_vUnCom.text = str("%.4f" % inv_line.price_unit)

            prod_vProd = SubElement(det_prod, 'vProd')
            prod_vProd.text = str("%.2f" % inv_line.price_subtotal)

            prod_cEANTrib = SubElement(det_prod, 'cEANTrib')
            #prod_vProd.text(inv_line.total)

            prod_uTrib = SubElement(det_prod, 'uTrib')
            prod_uTrib.text = inv_line.uos_id.name

            prod_qTrib = SubElement(det_prod, 'qTrib')
            prod_qTrib.text = '0.0000'  #TODO

            prod_vUnTrib = SubElement(det_prod, 'vUnTrib')
            prod_vUnTrib.text = '0.00'  #TODO

            prod_vFrete = SubElement(det_prod, 'vFrete')
            prod_vFrete.text = '0.00'  #TODO - Valor do Frete

            prod_vSeg = SubElement(det_prod, 'vSeg')
            prod_vSeg.text = '0.00'  #TODO - Valor do seguro

            prod_vDesc = SubElement(det_prod, 'vDesc')
            prod_vDesc.text = str("%.2f" % inv_line.discount)  #TODO

            prod_vOutro = SubElement(det_prod, 'vOutro')
            prod_vOutro.text = '0.0000'  #TODO

            prod_indTot = SubElement(det_prod, 'indTot')
            prod_indTot.text = '1'  #TODO

            prod_imposto = SubElement(det, 'imposto')

            imposto_icms = SubElement(prod_imposto, 'ICMS' ) # + inv_line.icms_cst)

            imposto_icms_cst = SubElement(imposto_icms, 'ICMS%s' % (inv_line.icms_cst))

            icms_orig = SubElement(imposto_icms_cst, 'orig')
            icms_orig.text = inv_line.product_id.origin

            icms_CST = SubElement(imposto_icms_cst, 'CST')
            icms_CST.text = inv_line.icms_cst

            icms_modBC = SubElement(imposto_icms_cst, 'modBC')
            icms_modBC.text = '0' # TODO

            icms_vBC = SubElement(imposto_icms_cst, 'vBC')
            icms_vBC.text = str("%.2f" % inv_line.icms_base)

            icms_pICMS = SubElement(imposto_icms_cst, 'pICMS')
            icms_pICMS.text = str("%.2f" % inv_line.icms_percent)

            icms_vICMS = SubElement(imposto_icms_cst, 'vICMS')
            icms_vICMS.text = str("%.2f" % inv_line.icms_value)

            imposto_ipi = SubElement(prod_imposto, 'IPI')

            icms_cEnq = SubElement(imposto_ipi, 'cEnq')
            icms_cEnq.text = '999'

            #Imposto Não Tributado
            ipi_IPINT = SubElement(imposto_ipi, 'IPINT')

            ipi_CST = SubElement(ipi_IPINT, 'CST')
            ipi_CST.text = inv_line.ipi_cst

            imposto_pis = SubElement(prod_imposto, 'PIS')

            pis_PISAliq = SubElement(imposto_pis, 'PISAliq')

            pis_CST = SubElement(pis_PISAliq, 'CST')
            pis_CST.text = inv_line.pis_cst

            pis_vBC = SubElement(pis_PISAliq, 'vBC')
            pis_vBC.text = str("%.2f" % inv_line.pis_base)

            pis_pPIS = SubElement(pis_PISAliq, 'pPIS')
            pis_pPIS.text = str("%.2f" % inv_line.pis_percent)

            pis_vPIS = SubElement(pis_PISAliq, 'vPIS')
            pis_vPIS.text = str("%.2f" % inv_line.pis_value)

            imposto_cofins = SubElement(prod_imposto, 'COFINS')

            cofins_COFINSAliq = SubElement(imposto_cofins, 'COFINSAliq')

            cofins_CST = SubElement(cofins_COFINSAliq, 'CST')
            cofins_CST.text = inv_line.pis_cst

            cofins_vBC = SubElement(cofins_COFINSAliq, 'vBC')
            cofins_vBC.text = str("%.2f" % inv_line.cofins_base)

            cofins_pCOFINS = SubElement(cofins_COFINSAliq, 'pCOFINS')
            cofins_pCOFINS.text = str("%.2f" % inv_line.cofins_percent)

            cofins_vCOFINS = SubElement(cofins_COFINSAliq, 'vCOFINS')
            cofins_vCOFINS.text = str("%.2f" % inv_line.cofins_value)

        total = SubElement(infNFe, 'total')
        total_ICMSTot = SubElement(total, 'ICMSTot')

        ICMSTot_vBC = SubElement(total_ICMSTot, 'vBC')
        ICMSTot_vBC.text = str("%.2f" % inv.icms_base)

        ICMSTot_vICMS = SubElement(total_ICMSTot, 'vICMS')
        ICMSTot_vICMS.text = str("%.2f" % inv.icms_value)

        ICMSTot_vBCST = SubElement(total_ICMSTot, 'vBCST')
        ICMSTot_vBCST.text = '0.00' # TODO

        ICMSTot_vST = SubElement(total_ICMSTot, 'vST')
        ICMSTot_vST.text = '0.00' # TODO

        ICMSTot_vProd = SubElement(total_ICMSTot, 'vProd')
        ICMSTot_vProd.text = str("%.2f" % inv.amount_untaxed)

        ICMSTot_vFrete = SubElement(total_ICMSTot, 'vFrete')
        ICMSTot_vFrete.text = '0.00' # TODO

        ICMSTot_vSeg = SubElement(total_ICMSTot, 'vSeg')
        ICMSTot_vSeg.text = str("%.2f" % inv.amount_insurance)

        ICMSTot_vDesc = SubElement(total_ICMSTot, 'vDesc')
        ICMSTot_vDesc.text = '0.00' # TODO

        ICMSTot_II = SubElement(total_ICMSTot, 'vII')
        ICMSTot_II.text = '0.00' # TODO

        ICMSTot_vIPI = SubElement(total_ICMSTot, 'vIPI')
        ICMSTot_vIPI.text = str("%.2f" % inv.ipi_value)

        ICMSTot_vPIS = SubElement(total_ICMSTot, 'vPIS')
        ICMSTot_vPIS.text = str("%.2f" % inv.pis_value)

        ICMSTot_vCOFINS = SubElement(total_ICMSTot, 'vCOFINS')
        ICMSTot_vCOFINS.text = str("%.2f" % inv.cofins_value)

        ICMSTot_vOutro = SubElement(total_ICMSTot, 'vOutro')
        ICMSTot_vOutro.text = str("%.2f" % inv.amount_costs)

        ICMSTot_vNF = SubElement(total_ICMSTot, 'vNF')
        ICMSTot_vNF.text = str("%.2f" % inv.amount_total)


        transp = SubElement(infNFe, 'transp')

        # Modo do Frete: 0- Por conta do emitente; 1- Por conta do destinatário/remetente; 2- Por conta de terceiros; 9- Sem frete (v2.0)
        transp_modFrete = SubElement(transp, 'modFrete')
        transp_modFrete.text = '0' #TODO

        if inv.carrier_id:

            #Endereço do company
            carrier_addr = pool.get('res.partner').address_get(cr, uid, [inv.carrier_id.partner_id.id], ['default'])
            carrier_addr_default = pool.get('res.partner.address').browse(cr, uid, [carrier_addr['default']])[0]

            transp_transporta = SubElement(transp, 'transporta')

            if inv.carrier_id.partner_id.tipo_pessoa == 'J':
                transporta_CNPJ = SubElement(transp_transporta, 'CNPJ')
                transporta_CNPJ.text = inv.carrier_id.partner_id.cnpj_cpf
            else:
                transporta_CPF = SubElement(transp_transporta, 'CPF')
                transporta_CPF.text = inv.carrier_id.partner_id.cnpj_cpf

            transporta_xNome = SubElement(transp_transporta, 'xNome')
            if inv.carrier_id.partner_id.legal_name:
                transporta_xNome.text = inv.carrier_id.partner_id.legal_name
            else:
                transporta_xNome.text = inv.carrier_id.partner_id.name

            transporta_IE = SubElement(transp_transporta, 'IE')
            transporta_IE.text = inv.carrier_id.partner_id.inscr_est

            transporta_xEnder = SubElement(transp_transporta, 'xEnder')
            transporta_xEnder.text = carrier_addr_default.street

            transporta_xMun = SubElement(transp_transporta, 'xMun')
            transporta_xMun.text = ('%s%s') % (carrier_addr_default.state_id.ibge_code, carrier_addr_default.l10n_br_city_id.ibge_code)

            transporta_UF = SubElement(transp_transporta, 'UF')
            transporta_UF.text = carrier_addr_default.state_id.code


        if inv.number_of_packages:
            transp_vol = SubElement(transp, 'vol')

            vol_qVol = SubElement(transp_vol, 'qVol')
            vol_qVol.text = inv.number_of_packages

            vol_esp = SubElement(transp_vol, 'esp')
            vol_esp.text = 'volume' #TODO

            vol_pesoL = SubElement(transp_vol, 'pesoL')
            vol_pesoL.text = inv.weight_net

            vol_pesoB = SubElement(transp_vol, 'pesoB')
            vol_pesoB.text = inv.weight

    xml_string = ElementTree.tostring(nfeProc, 'utf-8')
    return xml_string


def nfe_import(ids, nfe_environment='1', context=False):
    return 'TESTE Import'
