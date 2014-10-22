# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
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

from datetime import datetime

from openerp import pooler
from openerp.osv import orm
from openerp.tools.translate import _
from openerp.addons.l10n_br_account.sped.document import FiscalDocument
from openerp.addons.l10n_br_base.tools.misc import punctuation_rm


class NFe200(FiscalDocument):

    def _serializer(self, cr, uid, ids, nfe_environment, context=None):
        """"""
        try:
            from pysped.nfe.leiaute import (
                NFe_200, Det_200, NFRef_200,
                Dup_200, Vol_200, DI_200, Adi_200)
        except ImportError:
            raise orm.except_orm(
                _(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))

        pool = pooler.get_pool(cr.dbname)
        nfes = []

        if not context:
            context = {'lang': 'pt_BR'}

        for inv in pool.get('account.invoice').browse(cr, uid, ids, context):

            company = pool.get('res.partner').browse(
                cr, uid, inv.company_id.partner_id.id, context)

            nfe = NFe_200()

            #
            # Identificação da NF-e
            #
            nfe.infNFe.ide.cUF.valor = company.state_id and company.state_id.ibge_code or ''
            nfe.infNFe.ide.cNF.valor = ''
            nfe.infNFe.ide.natOp.valor = inv.cfop_ids[0].small_name or ''
            nfe.infNFe.ide.indPag.valor = inv.payment_term and inv.payment_term.indPag or '0'
            nfe.infNFe.ide.mod.valor  = inv.fiscal_document_id.code or ''
            nfe.infNFe.ide.serie.valor = inv.document_serie_id.code or ''
            nfe.infNFe.ide.nNF.valor = inv.internal_number or ''
            nfe.infNFe.ide.dEmi.valor = inv.date_invoice or ''
            nfe.infNFe.ide.dSaiEnt.valor = inv.date_in_out or ''
            nfe.infNFe.ide.cMunFG.valor = ('%s%s') % (company.state_id.ibge_code, company.l10n_br_city_id.ibge_code)
            nfe.infNFe.ide.tpImp.valor = 1  # (1 - Retrato; 2 - Paisagem)
            nfe.infNFe.ide.tpEmis.valor = 1
            nfe.infNFe.ide.tpAmb.valor = nfe_environment
            nfe.infNFe.ide.finNFe.valor = inv.nfe_purpose
            nfe.infNFe.ide.procEmi.valor = 0
            nfe.infNFe.ide.verProc.valor = 'OpenERP Brasil v7'

            if inv.cfop_ids[0].type in ("input"):
                nfe.infNFe.ide.tpNF.valor = '0'
            else:
                nfe.infNFe.ide.tpNF.valor = '1'

            #
            # Endereço de Entrega ou Retirada
            #
            if inv.partner_shipping_id:
                if inv.partner_id.id != inv.partner_shipping_id.id:
                    if nfe.infNFe.ide.tpNF.valor == '0':
                        nfe.infNFe.retirada.CNPJ.valor = punctuation_rm(inv.partner_shipping_id.cnpj_cpf)
                        nfe.infNFe.retirada.xLgr.valor = inv.partner_shipping_id.street or ''
                        nfe.infNFe.retirada.nro.valor = inv.partner_shipping_id.number or ''
                        nfe.infNFe.retirada.xCpl.valor = inv.partner_shipping_id.street2 or ''
                        nfe.infNFe.retirada.xBairro.valor = inv.partner_shipping_id.district or 'Sem Bairro'
                        nfe.infNFe.retirada.cMun.valor = '%s%s' % (inv.partner_shipping_id.state_id.ibge_code, inv.partner_shipping_id.l10n_br_city_id.ibge_code)
                        nfe.infNFe.retirada.xMun.valor = inv.partner_shipping_id.l10n_br_city_id.name or ''
                        nfe.infNFe.retirada.UF.valor = inv.address_invoice_id.state_id.code or ''
                    else:
                        nfe.infNFe.entrega.CNPJ.valor = punctuation_rm(inv.partner_shipping_id.cnpj_cpf)
                        nfe.infNFe.entrega.xLgr.valor = inv.partner_shipping_id.street or ''
                        nfe.infNFe.entrega.nro.valor = inv.partner_shipping_id.number or ''
                        nfe.infNFe.entrega.xCpl.valor = inv.partner_shipping_id.street2 or ''
                        nfe.infNFe.entrega.xBairro.valor = inv.partner_shipping_id.district or 'Sem Bairro'
                        nfe.infNFe.entrega.cMun.valor = '%s%s' % (inv.partner_shipping_id.state_id.ibge_code, inv.partner_shipping_id.l10n_br_city_id.ibge_code)
                        nfe.infNFe.entrega.xMun.valor = inv.partner_shipping_id.l10n_br_city_id.name or ''
                        nfe.infNFe.entrega.UF.valor = inv.address_invoice_id.state_id.code or ''

            #
            # Documentos referenciadas
            #
            for inv_related in inv.fiscal_document_related_ids:

                nfref = NFRef_200()

                if inv_related.document_type == 'nf':
                    nfref.refNF.cUF.valor = inv_related.state_id and inv_related.state_id.ibge_code or '',
                    nfref.refNF.AAMM.valor = datetime.strptime(inv_related.date, '%Y-%m-%d').strftime('%y%m') or ''
                    nfref.refNF.CNPJ.valor = punctuation_rm(inv_related.cnpj_cpf)
                    nfref.refNF.mod.valor = inv_related.fiscal_document_id and inv_related.fiscal_document_id.code or ''
                    nfref.refNF.serie.valor = inv_related.serie or ''
                    nfref.refNF.nNF.valor = inv_related.internal_number or ''
                elif inv_related.document_type == 'nfrural':
                    nfref.refNFP.cUF.valor = inv_related.state_id and inv_related.state_id.ibge_code or '',
                    nfref.refNFP.AAMM.valor = datetime.strptime(inv_related.date, '%Y-%m-%d').strftime('%y%m') or ''
                    nfref.refNFP.IE.valor = punctuation_rm(inv_related.inscr_est)
                    nfref.refNFP.mod.valor = inv_related.fiscal_document_id and inv_related.fiscal_document_id.code or ''
                    nfref.refNFP.serie.valor = inv_related.serie or ''
                    nfref.refNFP.nNF.valor = inv_related.internal_number or ''
                    if inv_related.cpfcnpj_type == 'cnpj':
                        nfref.refNFP.CNPJ.valor = punctuation_rm(inv_related.cnpj_cpf)
                    else:
                        nfref.refNFP.CPF.valor = punctuation_rm(inv_related.cnpj_cpf)
                elif inv_related.document_type == 'nfe':
                    nfref.refNFe.valor = inv_related.access_key or ''
                elif inv_related.document_type == 'cte':
                    nfref.refCTe.valor = inv_related.access_key or ''
                elif inv_related.document_type == 'cf':
                    nfref.refECF.mod.valor = inv_related.fiscal_document_id and inv_related.fiscal_document_id.code or ''
                    nfref.refECF.nECF.valor = inv_related.internal_number
                    nfref.refECF.nCOO.valor = inv_related.serie

                nfe.infNFe.ide.NFref.append(nfref)

            #
            # Emitente
            #
            nfe.infNFe.emit.CNPJ.valor  = punctuation_rm(inv.company_id.partner_id.cnpj_cpf)
            nfe.infNFe.emit.xNome.valor = inv.company_id.partner_id.legal_name
            nfe.infNFe.emit.xFant.valor = inv.company_id.partner_id.name
            nfe.infNFe.emit.enderEmit.xLgr.valor = company.street or ''
            nfe.infNFe.emit.enderEmit.nro.valor = company.number or ''
            nfe.infNFe.emit.enderEmit.xCpl.valor = company.street2 or ''
            nfe.infNFe.emit.enderEmit.xBairro.valor = company.district or 'Sem Bairro'
            nfe.infNFe.emit.enderEmit.cMun.valor = '%s%s' % (company.state_id.ibge_code, company.l10n_br_city_id.ibge_code)
            nfe.infNFe.emit.enderEmit.xMun.valor = company.l10n_br_city_id.name or ''
            nfe.infNFe.emit.enderEmit.UF.valor = company.state_id.code or ''
            nfe.infNFe.emit.enderEmit.CEP.valor = punctuation_rm(company.zip)
            nfe.infNFe.emit.enderEmit.cPais.valor = company.country_id.bc_code[1:]
            nfe.infNFe.emit.enderEmit.xPais.valor = company.country_id.name
            nfe.infNFe.emit.enderEmit.fone.valor = punctuation_rm(company.phone or '').replace(' ', '')
            nfe.infNFe.emit.IE.valor = punctuation_rm(inv.company_id.partner_id.inscr_est)
            nfe.infNFe.emit.IEST.valor = ''
            nfe.infNFe.emit.IM.valor = punctuation_rm(inv.company_id.partner_id.inscr_mun)
            nfe.infNFe.emit.CRT.valor = inv.company_id.fiscal_type or ''
            if inv.company_id.partner_id.inscr_mun:
                nfe.infNFe.emit.CNAE.valor = punctuation_rm(inv.company_id.cnae_main_id.code)

            #
            # Destinatário
            #
            partner_bc_code = ''
            address_invoice_state_code = ''
            address_invoice_city = ''
            partner_cep = ''
            if inv.partner_id.country_id.bc_code:
                partner_bc_code = inv.partner_id.country_id.bc_code[1:]

            if inv.partner_id.country_id.id != company.country_id.id:
                address_invoice_state_code = 'EX'
                address_invoice_city = 'Exterior'
                partner_cep = ''
            else:
                address_invoice_state_code = inv.partner_id.state_id.code
                address_invoice_city = inv.partner_id.l10n_br_city_id.name or ''
                partner_cep = punctuation_rm(inv.partner_id.zip)

            # Se o ambiente for de teste deve ser
            # escrito na razão do destinatário
            if nfe_environment == '2':
                nfe.infNFe.dest.xNome.valor = 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL'
            else:
                nfe.infNFe.dest.xNome.valor = inv.partner_id.legal_name or ''

            if inv.partner_id.is_company:
                nfe.infNFe.dest.CNPJ.valor = punctuation_rm(inv.partner_id.cnpj_cpf)
                nfe.infNFe.dest.IE.valor = punctuation_rm(inv.partner_id.inscr_est)
            else:
                nfe.infNFe.dest.CPF.valor = punctuation_rm(inv.partner_id.cnpj_cpf)

            nfe.infNFe.dest.enderDest.xLgr.valor = inv.partner_id.street or ''
            nfe.infNFe.dest.enderDest.nro.valor = inv.partner_id.number or ''
            nfe.infNFe.dest.enderDest.xCpl.valor = inv.partner_id.street2 or ''
            nfe.infNFe.dest.enderDest.xBairro.valor = inv.partner_id.district or 'Sem Bairro'
            nfe.infNFe.dest.enderDest.cMun.valor = '%s%s' % (inv.partner_id.state_id.ibge_code, inv.partner_id.l10n_br_city_id.ibge_code)
            nfe.infNFe.dest.enderDest.xMun.valor = address_invoice_city
            nfe.infNFe.dest.enderDest.UF.valor = address_invoice_state_code
            nfe.infNFe.dest.enderDest.CEP.valor = partner_cep
            nfe.infNFe.dest.enderDest.cPais.valor = partner_bc_code
            nfe.infNFe.dest.enderDest.xPais.valor = inv.partner_id.country_id.name or ''
            nfe.infNFe.dest.enderDest.fone.valor = punctuation_rm(inv.partner_id.phone or '').replace(' ', '')
            nfe.infNFe.dest.email.valor = inv.partner_id.email or ''

            #
            # Detalhe
            #
            i = 0
            for inv_line in inv.invoice_line:
                i += 1
                det = Det_200()

                det.nItem.valor = i
                det.prod.cProd.valor = inv_line.product_id.code or ''
                det.prod.cEAN.valor = inv_line.product_id.ean13 or ''
                det.prod.xProd.valor = inv_line.product_id.name or ''
                det.prod.NCM.valor = punctuation_rm(inv_line.fiscal_classification_id.name)
                det.prod.EXTIPI.valor = ''
                det.prod.CFOP.valor = inv_line.cfop_id.code
                det.prod.uCom.valor = inv_line.uos_id.name or ''
                det.prod.qCom.valor = str("%.4f" % inv_line.quantity)
                det.prod.vUnCom.valor = str("%.7f" % (inv_line.price_unit))
                det.prod.vProd.valor = str("%.2f" % inv_line.price_gross)
                det.prod.cEANTrib.valor = inv_line.product_id.ean13 or ''
                det.prod.uTrib.valor = det.prod.uCom.valor
                det.prod.qTrib.valor = det.prod.qCom.valor
                det.prod.vUnTrib.valor = det.prod.vUnCom.valor
                det.prod.vFrete.valor = str("%.2f" % inv_line.freight_value)
                det.prod.vSeg.valor = str("%.2f" % inv_line.insurance_value)
                det.prod.vDesc.valor = str("%.2f" % inv_line.discount_value)
                det.prod.vOutro.valor = str("%.2f" % inv_line.other_costs_value)
                det.prod.xPed.valor = inv.name or ''
                #
                # Produto entra no total da NF-e
                #
                det.prod.indTot.valor = 1

                if inv_line.product_type == 'product':
                    #
                    # Impostos
                    #
                    # ICMS
                    if inv_line.icms_cst_id.code > 100:
                        det.imposto.ICMS.CSOSN.valor = inv_line.icms_cst_id.code
                        det.imposto.ICMS.pCredSN.valor = str("%.2f" % inv_line.icms_percent)
                        det.imposto.ICMS.vCredICMSSN.valor = str("%.2f" % inv_line.icms_value)
                    det.imposto.ICMS.CST.valor = inv_line.icms_cst_id.code
                    det.imposto.ICMS.modBC.valor = inv_line.icms_base_type
                    det.imposto.ICMS.vBC.valor = str("%.2f" % inv_line.icms_base)
                    det.imposto.ICMS.pRedBC.valor = str("%.2f" % inv_line.icms_percent_reduction)
                    det.imposto.ICMS.pICMS.valor = str("%.2f" % inv_line.icms_percent)
                    det.imposto.ICMS.vICMS.valor = str("%.2f" % inv_line.icms_value)

                    # ICMS ST
                    det.imposto.ICMS.modBCST.valor = inv_line.icms_st_base_type
                    det.imposto.ICMS.pMVAST.valor = str("%.2f" % inv_line.icms_st_mva)
                    det.imposto.ICMS.pRedBCST.valor = str("%.2f" % inv_line.icms_st_percent_reduction)
                    det.imposto.ICMS.vBCST.valor = str("%.2f" % inv_line.icms_st_base)
                    det.imposto.ICMS.pICMSST.valor = str("%.2f" % inv_line.icms_st_percent)
                    det.imposto.ICMS.vICMSST.valor = str("%.2f" % inv_line.icms_st_value)

                    # IPI
                    det.imposto.IPI.CST.valor = inv_line.ipi_cst_id.code
                    det.imposto.IPI.vBC.valor = str("%.2f" % inv_line.ipi_base)
                    det.imposto.IPI.pIPI.valor = str("%.2f" % inv_line.ipi_percent)
                    det.imposto.IPI.vIPI.valor = str("%.2f" % inv_line.ipi_value)
                else:
                    #ISSQN
                    det.imposto.ISSQN.vBC.valor = str("%.2f" % inv_line.issqn_base)
                    det.imposto.ISSQN.vAliq.valor = str("%.2f" % inv_line.issqn_percent)
                    det.imposto.ISSQN.vISSQN.valor = str("%.2f" % inv_line.issqn_value)
                    det.imposto.ISSQN.cMunFG.valor = ('%s%s') % (inv.partner_id.state_id.ibge_code, inv.partner_id.l10n_br_city_id.ibge_code)
                    det.imposto.ISSQN.cListServ.valor = punctuation_rm(inv_line.service_type_id.code)
                    det.imposto.ISSQN.cSitTrib.valor = inv_line.issqn_type

                # PIS
                det.imposto.PIS.CST.valor = inv_line.pis_cst_id.code
                det.imposto.PIS.vBC.valor = str("%.2f" % inv_line.pis_base)
                det.imposto.PIS.pPIS.valor = str("%.2f" % inv_line.pis_percent)
                det.imposto.PIS.vPIS.valor = str("%.2f" % inv_line.pis_value)

                # PISST
                det.imposto.PISST.vBC.valor = str("%.2f" % inv_line.pis_st_base)
                det.imposto.PISST.pPIS.valor = str("%.2f" % inv_line.pis_st_percent)
                det.imposto.PISST.qBCProd.valor = ''
                det.imposto.PISST.vAliqProd.valor = ''
                det.imposto.PISST.vPIS.valor = str("%.2f" % inv_line.pis_st_value)

                # COFINS
                det.imposto.COFINS.CST.valor = inv_line.cofins_cst_id.code
                det.imposto.COFINS.vBC.valor = str("%.2f" % inv_line.cofins_base)
                det.imposto.COFINS.pCOFINS.valor = str("%.2f" % inv_line.cofins_percent)
                det.imposto.COFINS.vCOFINS.valor = str("%.2f" % inv_line.cofins_value)

                # COFINSST
                det.imposto.COFINSST.vBC.valor = str("%.2f" % inv_line.cofins_st_base)
                det.imposto.COFINSST.pCOFINS.valor = str("%.2f" % inv_line.cofins_st_percent)
                det.imposto.COFINSST.qBCProd.valor = ''
                det.imposto.COFINSST.vAliqProd.valor = ''
                det.imposto.COFINSST.vCOFINS.valor = str("%.2f" % inv_line.cofins_st_value)

                # Declaração de importação
                for inv_di in inv_line.import_declaration_ids:
                    di = DI_200()

                    di.nDI.valor = inv_di.name
                    di.dDI.valor = inv_di.date_registration or ''
                    di.xLocDesemb.valor = inv_di.location
                    di.UFDesemb.valor = inv_di.state_id.code or ''
                    di.dDesemb.valor = inv_di.date_release or ''
                    di.cExportador.valor = inv_di.exporting_code

                    for inv_di_line in inv_di.line_ids:

                        di_line = Adi_200()

                        di_line.nAdicao.valor = inv_di_line.name
                        di_line.nSeqAdic.valor = inv_di_line.sequence
                        di_line.cFabricante.valor = inv_di_line.manufacturer_code
                        di_line.vDescDI.valor = str("%.2f" % inv_di_line.amount_discount)

                        di.adi.append(di_line)

                    det.prod.DI.append(di)

                nfe.infNFe.det.append(det)

            #
            # Dados de Cobrança
            #
            if inv.journal_id.revenue_expense:

                for line in inv.move_line_receivable_id:

                    dup = Dup_200()
                    dup.nDup.valor = line.name
                    dup.dVenc.valor = line.date_maturity or inv.date_due or inv.date_invoice
                    dup.vDup.valor = str("%.2f" % line.debit)
                    nfe.infNFe.cobr.dup.append(dup)

            #
            # Dados da Transportadora e veiculo
            #
            try:
                if inv.carrier_id:

                    nfe.infNFe.transp.modFrete.valor = inv.incoterm and inv.incoterm.freight_responsibility or '9'

                    if inv.carrier_id.partner_id.is_company:
                        nfe.infNFe.transp.transporta.CNPJ.valor = punctuation_rm(inv.carrier_id.partner_id.cnpj_cpf)
                    else:
                        nfe.infNFe.transp.transporta.CPF.valor = punctuation_rm(inv.carrier_id.partner_id.cnpj_cpf)
                    nfe.infNFe.transp.transporta.xNome.valor = inv.carrier_id.partner_id.legal_name or ''
                    nfe.infNFe.transp.transporta.IE.valor = inv.carrier_id.partner_id.inscr_est or ''
                    nfe.infNFe.transp.transporta.xEnder.valor = inv.carrier_id.partner_id.street or ''
                    nfe.infNFe.transp.transporta.xMun.valor = inv.carrier_id.partner_id.l10n_br_city_id.name or ''
                    nfe.infNFe.transp.transporta.UF.valor = inv.carrier_id.partner_id.state_id.code or ''

                if inv.vehicle_id:
                    nfe.infNFe.transp.veicTransp.placa.valor = inv.vehicle_id.plate or ''
                    nfe.infNFe.transp.veicTransp.UF.valor = inv.vehicle_id.state_id.code or ''
                    nfe.infNFe.transp.veicTransp.RNTC.valor = inv.vehicle_id.rntc_code or ''

            except AttributeError:
                pass
            
            #
            # Campos do Transporte da NF-e Bloco 381
            #
            
            vol = Vol_200()
            vol.qVol.valor = inv.number_of_packages
            vol.esp.valor = inv.kind_of_packages or ''
            vol.marca.valor = inv.brand_of_packages or ''
            vol.nVol.valor = inv.notation_of_packages or ''
            vol.pesoL.valor = str("%.2f" % inv.weight)
            vol.pesoB.valor = str("%.2f" % inv.weight_net)
            nfe.infNFe.transp.vol.append(vol)

            #
            # Informações adicionais
            #
            nfe.infNFe.infAdic.infAdFisco.valor = inv.fiscal_comment or ''
            nfe.infNFe.infAdic.infCpl.valor = inv.comment or ''

            #
            # Totais
            #
            nfe.infNFe.total.ICMSTot.vBC.valor     = str("%.2f" % inv.icms_base)
            nfe.infNFe.total.ICMSTot.vICMS.valor   = str("%.2f" % inv.icms_value)
            nfe.infNFe.total.ICMSTot.vBCST.valor   = str("%.2f" % inv.icms_st_base)
            nfe.infNFe.total.ICMSTot.vST.valor     = str("%.2f" % inv.icms_st_value)
            nfe.infNFe.total.ICMSTot.vProd.valor   = str("%.2f" % inv.amount_gross)
            nfe.infNFe.total.ICMSTot.vFrete.valor  = str("%.2f" % inv.amount_freight)
            nfe.infNFe.total.ICMSTot.vSeg.valor    = str("%.2f" % inv.amount_insurance)
            nfe.infNFe.total.ICMSTot.vDesc.valor   = str("%.2f" % inv.amount_discount)
            nfe.infNFe.total.ICMSTot.vII.valor     = str("%.2f" % inv.ii_value)
            nfe.infNFe.total.ICMSTot.vIPI.valor    = str("%.2f" % inv.ipi_value)
            nfe.infNFe.total.ICMSTot.vPIS.valor    = str("%.2f" % inv.pis_value)
            nfe.infNFe.total.ICMSTot.vCOFINS.valor = str("%.2f" % inv.cofins_value)
            nfe.infNFe.total.ICMSTot.vOutro.valor  = str("%.2f" % inv.amount_costs)
            nfe.infNFe.total.ICMSTot.vNF.valor     = str("%.2f" % inv.amount_total)

            # Gera Chave da NFe
            nfe.gera_nova_chave()
            nfes.append(nfe)

        return nfes

    def get_xml(self, cr, uid, ids, nfe_environment, context=None):
        """"""
        result = []
        for nfe in self._serializer(cr, uid, ids, nfe_environment, context):
            result.append({'key': nfe.infNFe.Id.valor, 'nfe': nfe.get_xml()})
        return result

    def set_xml(self, nfe_string, context=None):
        """"""
        try:
            from pysped.nfe.leiaute import NFe_200
        except ImportError:
            raise orm.except_orm(
                _(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))
        nfe = NFe_200()
        nfe.set_xml(nfe_string)
        return nfe
