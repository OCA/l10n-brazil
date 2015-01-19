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

import re
import string
from datetime import datetime

from openerp import pooler
from openerp.osv import orm
from openerp.tools.translate import _
from openerp.addons.l10n_br_account.sped.document import FiscalDocument


class NFe200(FiscalDocument):

    def __init__(self):
        super(NFe200, self).__init__()
        self.nfe = None
        self.nfref = None
        self.det = None
        self.dup = None

    def _serializer(self, cr, uid, ids, nfe_environment, context=None):

        pool = pooler.get_pool(cr.dbname)
        nfes = []

        if not context:
            context = {'lang': 'pt_BR'}

        for inv in pool.get('account.invoice').browse(cr, uid, ids, context):

            company = pool.get('res.partner').browse(
                cr, uid, inv.company_id.partner_id.id, context)

            self.nfe = self.get_NFe()

            self._nfe_identification(
                cr, uid, ids, inv, company, nfe_environment, context)

            self._in_out_adress(cr, uid, ids, inv, context)

            for inv_related in inv.fiscal_document_related_ids:
                self.nfref = self._get_NFRef()
                self._nfe_references(cr, uid, ids, inv_related)
                self.nfe.infNFe.ide.NFref.append(self.nfref)

            self._emmiter(cr, uid, ids, inv, company, context)
            self._receiver(cr, uid, ids, inv, company, nfe_environment, context)

            i = 0
            for inv_line in inv.invoice_line:
                i += 1
                self.det = self._get_Det()
                self._details(cr, uid, ids, inv, inv_line, i, context)

                for inv_di in inv_line.import_declaration_ids:

                    self.di = self._get_DI()
                    self._di(cr, uid, ids, inv, inv_line, inv_di, i, context)
                    self.det.prod.DI.append(self.di)
                    self.di = self._get_DI()

                    for inv_di_line in inv_di.line_ids:
                        self.di_line = self._get_Addition()
                        self._adiction(cr, uid, ids, inv, inv_line, inv_di, inv_di_line, i, context)
                        self.di.adi.append(self.di_line)

                self.nfe.infNFe.det.append(self.det)

            if inv.journal_id.revenue_expense:
                for line in inv.move_line_receivable_id:
                    self.dup = self._get_Dup()
                    self._encashment_data(cr, uid, ids, inv, line, context)
                    self.nfe.infNFe.cobr.dup.append(self.dup)

            try:
                self._carrier_data(cr, uid, ids, inv, context)
            except AttributeError:
                pass

            self.vol = self._get_Vol()
            self._weight_data(cr, uid, ids, inv, context=None)
            self.nfe.infNFe.transp.vol.append(self.vol)

            self._additional_information(cr, uid, ids, inv, context)
            self._total(cr, uid, ids, inv, context)

            # Gera Chave da NFe
            self.nfe.gera_nova_chave()
            nfes.append(self.nfe)

        return nfes


    def _nfe_identification(self, cr, uid, ids, inv, company, nfe_environment, context=None):

        # Identificação da NF-e
        #
        self.nfe.infNFe.ide.cUF.valor = company.state_id and company.state_id.ibge_code or ''
        self.nfe.infNFe.ide.cNF.valor = ''
        self.nfe.infNFe.ide.natOp.valor = inv.cfop_ids[0].small_name or ''
        self.nfe.infNFe.ide.indPag.valor = inv.payment_term and inv.payment_term.indPag or '0'
        self.nfe.infNFe.ide.mod.valor  = inv.fiscal_document_id.code or ''
        self.nfe.infNFe.ide.serie.valor = inv.document_serie_id.code or ''
        self.nfe.infNFe.ide.nNF.valor = inv.internal_number or ''
        self.nfe.infNFe.ide.dEmi.valor = inv.date_invoice or ''
        self.nfe.infNFe.ide.dSaiEnt.valor = datetime.strptime(inv.date_in_out, '%Y-%m-%d %H:%M:%S').date() or ''
        self.nfe.infNFe.ide.cMunFG.valor = ('%s%s') % (company.state_id.ibge_code, company.l10n_br_city_id.ibge_code)
        self.nfe.infNFe.ide.tpImp.valor = 1  # (1 - Retrato; 2 - Paisagem)
        self.nfe.infNFe.ide.tpEmis.valor = 1
        self.nfe.infNFe.ide.tpAmb.valor = nfe_environment
        self.nfe.infNFe.ide.finNFe.valor = inv.nfe_purpose
        self.nfe.infNFe.ide.procEmi.valor = 0
        self.nfe.infNFe.ide.verProc.valor = 'OpenERP Brasil v7'

        if inv.cfop_ids[0].type in ("input"):
            self.nfe.infNFe.ide.tpNF.valor = '0'
        else:
            self.nfe.infNFe.ide.tpNF.valor = '1'

    def _in_out_adress(self, cr, uid, ids, inv, context=None):

        #
        # Endereço de Entrega ou Retirada
        #
        if inv.partner_shipping_id:
            if inv.partner_id.id != inv.partner_shipping_id.id:
                if self.nfe.infNFe.ide.tpNF.valor == '0':
                    self.nfe.infNFe.retirada.CNPJ.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.partner_shipping_id.cnpj_cpf or '')
                    self.nfe.infNFe.retirada.xLgr.valor = inv.partner_shipping_id.street or ''
                    self.nfe.infNFe.retirada.nro.valor = inv.partner_shipping_id.number or ''
                    self.nfe.infNFe.retirada.xCpl.valor = inv.partner_shipping_id.street2 or ''
                    self.nfe.infNFe.retirada.xBairro.valor = inv.partner_shipping_id.district or 'Sem Bairro'
                    self.nfe.infNFe.retirada.cMun.valor = '%s%s' % (inv.partner_shipping_id.state_id.ibge_code, inv.partner_shipping_id.l10n_br_city_id.ibge_code)
                    self.nfe.infNFe.retirada.xMun.valor = inv.partner_shipping_id.l10n_br_city_id.name or ''
                    self.nfe.infNFe.retirada.UF.valor = inv.address_invoice_id.state_id.code or ''
                else:
                    self.nfe.infNFe.entrega.CNPJ.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.partner_shipping_id.cnpj_cpf or '')
                    self.nfe.infNFe.entrega.xLgr.valor = inv.partner_shipping_id.street or ''
                    self.nfe.infNFe.entrega.nro.valor = inv.partner_shipping_id.number or ''
                    self.nfe.infNFe.entrega.xCpl.valor = inv.partner_shipping_id.street2 or ''
                    self.nfe.infNFe.entrega.xBairro.valor = inv.partner_shipping_id.district or 'Sem Bairro'
                    self.nfe.infNFe.entrega.cMun.valor = '%s%s' % (inv.partner_shipping_id.state_id.ibge_code, inv.partner_shipping_id.l10n_br_city_id.ibge_code)
                    self.nfe.infNFe.entrega.xMun.valor = inv.partner_shipping_id.l10n_br_city_id.name or ''
                    self.nfe.infNFe.entrega.UF.valor = inv.address_invoice_id.state_id.code or ''


    def _nfe_references(self, cr, uid, ids, inv_related, context=None):

        #
        # Documentos referenciadas
        #

        if inv_related.document_type == 'nf':
            self.nfref.refNF.cUF.valor = inv_related.state_id and inv_related.state_id.ibge_code or '',
            self.nfref.refNF.AAMM.valor = datetime.strptime(inv_related.date, '%Y-%m-%d').strftime('%y%m') or ''
            self.nfref.refNF.CNPJ.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv_related.cnpj_cpf or '')
            self.nfref.refNF.mod.valor = inv_related.fiscal_document_id and inv_related.fiscal_document_id.code or ''
            self.nfref.refNF.serie.valor = inv_related.serie or ''
            self.nfref.refNF.nNF.valor = inv_related.internal_number or ''

        elif inv_related.document_type == 'nfrural':
            self.nfref.refNFP.cUF.valor = inv_related.state_id and inv_related.state_id.ibge_code or '',
            self.nfref.refNFP.AAMM.valor = datetime.strptime(inv_related.date, '%Y-%m-%d').strftime('%y%m') or ''
            self.nfref.refNFP.IE.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv_related.inscr_est or '')
            self.nfref.refNFP.mod.valor = inv_related.fiscal_document_id and inv_related.fiscal_document_id.code or ''
            self.nfref.refNFP.serie.valor = inv_related.serie or ''
            self.nfref.refNFP.nNF.valor = inv_related.internal_number or ''

            if inv_related.cpfcnpj_type == 'cnpj':
                self.nfref.refNFP.CNPJ.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv_related.cnpj_cpf or '')
            else:
                self.nfref.refNFP.CPF.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv_related.cnpj_cpf or '')

        elif inv_related.document_type == 'nfe':
            self.nfref.refNFe.valor = inv_related.access_key or ''

        elif inv_related.document_type == 'cte':
            self.nfref.refCTe.valor = inv_related.access_key or ''

        elif inv_related.document_type == 'cf':
            self.nfref.refECF.mod.valor = inv_related.fiscal_document_id and inv_related.fiscal_document_id.code or ''
            self.nfref.refECF.nECF.valor = inv_related.internal_number
            self.nfref.refECF.nCOO.valor = inv_related.serie


    def _emmiter(self, cr, uid, ids, inv, company, context=None):

        #
        # Emitente
        #
        self.nfe.infNFe.emit.CNPJ.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.partner_id.cnpj_cpf or '')
        self.nfe.infNFe.emit.xNome.valor = inv.company_id.partner_id.legal_name
        self.nfe.infNFe.emit.xFant.valor = inv.company_id.partner_id.name
        self.nfe.infNFe.emit.enderEmit.xLgr.valor = company.street or ''
        self.nfe.infNFe.emit.enderEmit.nro.valor = company.number or ''
        self.nfe.infNFe.emit.enderEmit.xCpl.valor = company.street2 or ''
        self.nfe.infNFe.emit.enderEmit.xBairro.valor = company.district or 'Sem Bairro'
        self.nfe.infNFe.emit.enderEmit.cMun.valor = '%s%s' % (company.state_id.ibge_code, company.l10n_br_city_id.ibge_code)
        self.nfe.infNFe.emit.enderEmit.xMun.valor = company.l10n_br_city_id.name or ''
        self.nfe.infNFe.emit.enderEmit.UF.valor = company.state_id.code or ''
        self.nfe.infNFe.emit.enderEmit.CEP.valor = re.sub('[%s]' % re.escape(string.punctuation), '', str(company.zip or '').replace(' ',''))
        self.nfe.infNFe.emit.enderEmit.cPais.valor = company.country_id.bc_code[1:]
        self.nfe.infNFe.emit.enderEmit.xPais.valor = company.country_id.name
        self.nfe.infNFe.emit.enderEmit.fone.valor = re.sub('[%s]' % re.escape(string.punctuation), '', str(company.phone or '').replace(' ',''))
        self.nfe.infNFe.emit.IE.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.partner_id.inscr_est or '')
        self.nfe.infNFe.emit.IEST.valor = ''
        self.nfe.infNFe.emit.IM.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.partner_id.inscr_mun or '')
        self.nfe.infNFe.emit.CRT.valor = inv.company_id.fiscal_type or ''

        if inv.company_id.partner_id.inscr_mun:
            self.nfe.infNFe.emit.CNAE.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.company_id.cnae_main_id.code or '')


    def _receiver(self, cr, uid, ids, inv, company, nfe_environment, context=None):

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
            partner_cep = re.sub('[%s]' % re.escape(string.punctuation), '', str(inv.partner_id.zip or '').replace(' ',''))

        # Se o ambiente for de teste deve ser
        # escrito na razão do destinatário
        if nfe_environment == '2':
            self.nfe.infNFe.dest.xNome.valor = 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL'
        else:
            self.nfe.infNFe.dest.xNome.valor = inv.partner_id.legal_name or ''

        if inv.partner_id.is_company:
            self.nfe.infNFe.dest.CNPJ.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.partner_id.cnpj_cpf or '')
            self.nfe.infNFe.dest.IE.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.partner_id.inscr_est or '')
        else:
            self.nfe.infNFe.dest.CPF.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv.partner_id.cnpj_cpf or '')

        self.nfe.infNFe.dest.enderDest.xLgr.valor = inv.partner_id.street or ''
        self.nfe.infNFe.dest.enderDest.nro.valor = inv.partner_id.number or ''
        self.nfe.infNFe.dest.enderDest.xCpl.valor = inv.partner_id.street2 or ''
        self.nfe.infNFe.dest.enderDest.xBairro.valor = inv.partner_id.district or 'Sem Bairro'
        self.nfe.infNFe.dest.enderDest.cMun.valor = '%s%s' % (inv.partner_id.state_id.ibge_code, inv.partner_id.l10n_br_city_id.ibge_code)
        self.nfe.infNFe.dest.enderDest.xMun.valor = address_invoice_city
        self.nfe.infNFe.dest.enderDest.UF.valor = address_invoice_state_code
        self.nfe.infNFe.dest.enderDest.CEP.valor = partner_cep
        self.nfe.infNFe.dest.enderDest.cPais.valor = partner_bc_code
        self.nfe.infNFe.dest.enderDest.xPais.valor = inv.partner_id.country_id.name or ''
        self.nfe.infNFe.dest.enderDest.fone.valor = re.sub('[%s]' % re.escape(string.punctuation), '', str(inv.partner_id.phone or '').replace(' ',''))
        self.nfe.infNFe.dest.email.valor = inv.partner_id.email or ''


    def _details(self, cr, uid, ids, inv, inv_line, i, context=None):

        #
        # Detalhe
        #

        self.det.nItem.valor = i
        self.det.prod.cProd.valor = inv_line.product_id.code or ''
        self.det.prod.cEAN.valor = inv_line.product_id.ean13 or ''
        self.det.prod.xProd.valor = inv_line.product_id.name or ''
        self.det.prod.NCM.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv_line.fiscal_classification_id.name or '')
        self.det.prod.EXTIPI.valor = ''
        self.det.prod.CFOP.valor = inv_line.cfop_id.code
        self.det.prod.uCom.valor = inv_line.uos_id.name or ''
        self.det.prod.qCom.valor = str("%.4f" % inv_line.quantity)
        self.det.prod.vUnCom.valor = str("%.7f" % (inv_line.price_unit))
        self.det.prod.vProd.valor = str("%.2f" % inv_line.price_gross)
        self.det.prod.cEANTrib.valor = inv_line.product_id.ean13 or ''
        self.det.prod.uTrib.valor = self.det.prod.uCom.valor
        self.det.prod.qTrib.valor = self.det.prod.qCom.valor
        self.det.prod.vUnTrib.valor = self.det.prod.vUnCom.valor
        self.det.prod.vFrete.valor = str("%.2f" % inv_line.freight_value)
        self.det.prod.vSeg.valor = str("%.2f" % inv_line.insurance_value)
        self.det.prod.vDesc.valor = str("%.2f" % inv_line.discount_value)
        self.det.prod.vOutro.valor = str("%.2f" % inv_line.other_costs_value)
        #
        # Produto entra no total da NF-e
        #
        self.det.prod.indTot.valor = 1

        if inv_line.product_type == 'product':
            #
            # Impostos
            #
            # ICMS
            if inv_line.icms_cst_id.code > 100:
                self.det.imposto.ICMS.CSOSN.valor = inv_line.icms_cst_id.code
                self.det.imposto.ICMS.pCredSN.valor = str("%.2f" % inv_line.icms_percent)
                self.det.imposto.ICMS.vCredICMSSN.valor = str("%.2f" % inv_line.icms_value)

            self.det.imposto.ICMS.CST.valor = inv_line.icms_cst_id.code
            self.det.imposto.ICMS.modBC.valor = inv_line.icms_base_type
            self.det.imposto.ICMS.vBC.valor = str("%.2f" % inv_line.icms_base)
            self.det.imposto.ICMS.pRedBC.valor = str("%.2f" % inv_line.icms_percent_reduction)
            self.det.imposto.ICMS.pICMS.valor = str("%.2f" % inv_line.icms_percent)
            self.det.imposto.ICMS.vICMS.valor = str("%.2f" % inv_line.icms_value)

            # ICMS ST
            self.det.imposto.ICMS.modBCST.valor = inv_line.icms_st_base_type
            self.det.imposto.ICMS.pMVAST.valor = str("%.2f" % inv_line.icms_st_mva)
            self.det.imposto.ICMS.pRedBCST.valor = str("%.2f" % inv_line.icms_st_percent_reduction)
            self.det.imposto.ICMS.vBCST.valor = str("%.2f" % inv_line.icms_st_base)
            self.det.imposto.ICMS.pICMSST.valor = str("%.2f" % inv_line.icms_st_percent)
            self.det.imposto.ICMS.vICMSST.valor = str("%.2f" % inv_line.icms_st_value)

            # IPI
            self.det.imposto.IPI.CST.valor = inv_line.ipi_cst_id.code
            if inv_line.ipi_type == 'percent' or '':
                self.det.imposto.IPI.vBC.valor = str("%.2f" % inv_line.ipi_base)
                self.det.imposto.IPI.pIPI.valor = str("%.2f" % inv_line.ipi_percent)
            if inv_line.ipi_type == 'quantity':
                pesol = 0
                if inv_line.product_id:
                    pesol = inv_line.product_id.weight_net
                    self.det.imposto.IPI.qUnid.valor = str("%.2f" % inv_line.quantity * pesol)
                    self.det.imposto.IPI.vUnid.valor = str("%.2f" % inv_line.ipi_percent)
            self.det.imposto.IPI.vIPI.valor = str("%.2f" % inv_line.ipi_value)

        else:
            #ISSQN
            self.det.imposto.ISSQN.vBC.valor = str("%.2f" % inv_line.issqn_base)
            self.det.imposto.ISSQN.vAliq.valor = str("%.2f" % inv_line.issqn_percent)
            self.det.imposto.ISSQN.vISSQN.valor = str("%.2f" % inv_line.issqn_value)
            self.det.imposto.ISSQN.cMunFG.valor = ('%s%s') % (inv.partner_id.state_id.ibge_code, inv.partner_id.l10n_br_city_id.ibge_code)
            self.det.imposto.ISSQN.cListServ.valor = re.sub('[%s]' % re.escape(string.punctuation), '', inv_line.service_type_id.code or '')
            self.det.imposto.ISSQN.cSitTrib.valor = inv_line.issqn_type


        # PIS
        self.det.imposto.PIS.CST.valor = inv_line.pis_cst_id.code
        self.det.imposto.PIS.vBC.valor = str("%.2f" % inv_line.pis_base)
        self.det.imposto.PIS.pPIS.valor = str("%.2f" % inv_line.pis_percent)
        self.det.imposto.PIS.vPIS.valor = str("%.2f" % inv_line.pis_value)

        # PISST
        self.det.imposto.PISST.vBC.valor = str("%.2f" % inv_line.pis_st_base)
        self.det.imposto.PISST.pPIS.valor = str("%.2f" % inv_line.pis_st_percent)
        self.det.imposto.PISST.qBCProd.valor = ''
        self.det.imposto.PISST.vAliqProd.valor = ''
        self.det.imposto.PISST.vPIS.valor = str("%.2f" % inv_line.pis_st_value)

        # COFINS
        self.det.imposto.COFINS.CST.valor = inv_line.cofins_cst_id.code
        self.det.imposto.COFINS.vBC.valor = str("%.2f" % inv_line.cofins_base)
        self.det.imposto.COFINS.pCOFINS.valor = str("%.2f" % inv_line.cofins_percent)
        self.det.imposto.COFINS.vCOFINS.valor = str("%.2f" % inv_line.cofins_value)

        # COFINSST
        self.det.imposto.COFINSST.vBC.valor = str("%.2f" % inv_line.cofins_st_base)
        self.det.imposto.COFINSST.pCOFINS.valor = str("%.2f" % inv_line.cofins_st_percent)
        self.det.imposto.COFINSST.qBCProd.valor = ''
        self.det.imposto.COFINSST.vAliqProd.valor = ''
        self.det.imposto.COFINSST.vCOFINS.valor = str("%.2f" % inv_line.cofins_st_value)


    def _di(self, cr, uid, ids, inv, inv_line, inv_di, i, context=None):
        self.di.nDI.valor = inv_di.name
        self.di.dDI.valor = inv_di.date_registration or ''
        self.di.xLocDesemb.valor = inv_di.location
        self.di.UFDesemb.valor = inv_di.state_id.code or ''
        self.di.dDesemb.valor = inv_di.date_release or ''
        self.di.cExportador.valor = inv_di.exporting_code

    def _addition(self, cr, uid, ids, inv, inv_line, inv_di, inv_di_line, i, context=None):
        self.di_line.nAdicao.valor = inv_di_line.name
        self.di_line.nSeqAdic.valor = inv_di_line.sequence
        self.di_line.cFabricante.valor = inv_di_line.manufacturer_code
        self.di_line.vDescDI.valor = str("%.2f" % inv_di_line.amount_discount)

    def _encashment_data(self, cr, uid, ids, inv, line, context=None):

        #
        # Dados de Cobrança
        #

        self.dup.nDup.valor = line.name
        self.dup.dVenc.valor = line.date_maturity or inv.date_due or inv.date_invoice
        self.dup.vDup.valor = str("%.2f" % line.debit)

    def _carrier_data(self, cr, uid, ids, inv, context=None):

        #
        # Dados da Transportadora e veiculo
        #
        if inv.carrier_id:

            self.nfe.infNFe.transp.modFrete.valor = inv.incoterm and inv.incoterm.freight_responsibility or '9'

            if inv.carrier_id.partner_id.is_company:
                self.nfe.infNFe.transp.transporta.CNPJ.valor = \
                    re.sub('[%s]' % re.escape(string.punctuation), '', inv.carrier_id.partner_id.cnpj_cpf or '')
            else:
                self.nfe.infNFe.transp.transporta.CPF.valor = \
                    re.sub('[%s]' % re.escape(string.punctuation), '', inv.carrier_id.partner_id.cnpj_cpf or '')

            self.nfe.infNFe.transp.transporta.xNome.valor = inv.carrier_id.partner_id.legal_name or ''
            self.nfe.infNFe.transp.transporta.IE.valor = inv.carrier_id.partner_id.inscr_est or ''
            self.nfe.infNFe.transp.transporta.xEnder.valor = inv.carrier_id.partner_id.street or ''
            self.nfe.infNFe.transp.transporta.xMun.valor = inv.carrier_id.partner_id.l10n_br_city_id.name or ''
            self.nfe.infNFe.transp.transporta.UF.valor = inv.carrier_id.partner_id.state_id.code or ''

        if inv.vehicle_id:
            self.nfe.infNFe.transp.veicTransp.placa.valor = inv.vehicle_id.plate or ''
            self.nfe.infNFe.transp.veicTransp.UF.valor = inv.vehicle_id.plate.state_id.code or ''
            self.nfe.infNFe.transp.veicTransp.RNTC.valor = inv.vehicle_id.rntc_code or ''

    def _weight_data(self, cr, uid, ids, inv, context=None):
        #
        # Campos do Transporte da NF-e Bloco 381
        #
        self.vol.qVol.valor = inv.number_of_packages
        self.vol.esp.valor = inv.kind_of_packages or ''
        self.vol.marca.valor = inv.brand_of_packages or ''
        self.vol.nVol.valor = inv.notation_of_packages or ''
        self.vol.pesoL.valor = str("%.2f" % inv.weight)
        self.vol.pesoB.valor = str("%.2f" % inv.weight_net)

    def _additional_information(self, cr, uid, ids, inv, context=None):

        #
        # Informações adicionais
        #
        self.nfe.infNFe.infAdic.infAdFisco.valor = inv.fiscal_comment or ''
        self.nfe.infNFe.infAdic.infCpl.valor = inv.comment or ''

    def _total(self, cr, uid, ids, inv, context=None):

        #
        # Totais
        #
        self.nfe.infNFe.total.ICMSTot.vBC.valor = str("%.2f" % inv.icms_base)
        self.nfe.infNFe.total.ICMSTot.vICMS.valor = str("%.2f" % inv.icms_value)
        self.nfe.infNFe.total.ICMSTot.vBCST.valor = str("%.2f" % inv.icms_st_base)
        self.nfe.infNFe.total.ICMSTot.vST.valor = str("%.2f" % inv.icms_st_value)
        self.nfe.infNFe.total.ICMSTot.vProd.valor = str("%.2f" % inv.amount_gross)
        self.nfe.infNFe.total.ICMSTot.vFrete.valor = str("%.2f" % inv.amount_freight)
        self.nfe.infNFe.total.ICMSTot.vSeg.valor = str("%.2f" % inv.amount_insurance)
        self.nfe.infNFe.total.ICMSTot.vDesc.valor = str("%.2f" % inv.amount_discount)
        self.nfe.infNFe.total.ICMSTot.vII.valor = str("%.2f" % inv.ii_value)
        self.nfe.infNFe.total.ICMSTot.vIPI.valor = str("%.2f" % inv.ipi_value)
        self.nfe.infNFe.total.ICMSTot.vPIS.valor = str("%.2f" % inv.pis_value)
        self.nfe.infNFe.total.ICMSTot.vCOFINS.valor = str("%.2f" % inv.cofins_value)
        self.nfe.infNFe.total.ICMSTot.vOutro.valor = str("%.2f" % inv.amount_costs)
        self.nfe.infNFe.total.ICMSTot.vNF.valor = str("%.2f" % inv.amount_total)

    def get_NFe(self):

        try:
            from pysped.nfe.leiaute import NFe_200
        except ImportError:
            raise orm.except_orm(_(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))

        return NFe_200()

    def _get_NFRef(self):

        try:
            from pysped.nfe.leiaute import NFRef_200
        except ImportError:
            raise orm.except_orm(_(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))

        return NFRef_200()

    def _get_Det(self):

        try:
            from pysped.nfe.leiaute import Det_200
        except ImportError:
            raise orm.except_orm(_(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))

        return Det_200()

    def _get_DI(self):
        try:
            from pysped.nfe.leiaute import DI_200
        except ImportError:
            raise orm.except_orm(_(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))
        return DI_200()

    def _get_Addition(self):
        try:
            from pysped.nfe.leiaute import Adi_200
        except ImportError:
            raise orm.except_orm(_(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))
        return Adi_200()


    def _get_Vol(self):
        try:
            from pysped.nfe.leiaute import Vol_200
        except ImportError:
            raise orm.except_orm(_(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))
        return Vol_200()

    def _get_Dup(self):

        try:
            from pysped.nfe.leiaute import Dup_200
        except ImportError:
            raise orm.except_orm(_(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))

        return Dup_200()

    def get_xml(self, cr, uid, ids, nfe_environment, context=None):
        """"""
        result = []
        for nfe in self._serializer(cr, uid, ids, nfe_environment, context):
            result.append({'key': nfe.infNFe.Id.valor, 'nfe': nfe.get_xml()})
        return result

    def set_xml(self, nfe_string, context=None):
        """"""
        nfe = self.get_NFe()
        nfe.set_xml(nfe_string)
        return nfe


class NFe310(NFe200):

    def __init__(self):
        super(NFe310, self).__init__()


    def _nfe_identification(self, cr, uid, ids, inv, company, nfe_environment, context=None):

        super(NFe310, self)._nfe_identification(
            cr, uid, ids, inv, company, nfe_environment, context)

        self.nfe.infNFe.ide.idDest.valor = inv.fiscal_position.id_dest or ''
        self.nfe.infNFe.ide.indFinal.valor = inv.ind_final or ''
        self.nfe.infNFe.ide.indPres.valor = inv.ind_pres or ''
        self.nfe.infNFe.ide.dhEmi.valor = datetime.strptime(inv.date_hour_invoice, '%Y-%m-%d %H:%M:%S')
        self.nfe.infNFe.ide.dhSaiEnt.valor = datetime.strptime(inv.date_in_out, '%Y-%m-%d %H:%M:%S')

    def get_NFe(self):

        try:
            from pysped.nfe.leiaute import NFe_310
        except ImportError:
            raise orm.except_orm(_(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))

        return NFe_310()

    def _get_NFRef(self):

        try:
            from pysped.nfe.leiaute import NFRef_310
        except ImportError:
            raise orm.except_orm(_(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))

        return NFRef_310()

    def _get_Det(self):

        try:
            from pysped.nfe.leiaute import Det_310
        except ImportError:
            raise orm.except_orm(_(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))

        return Det_310()

    def _get_Dup(self):

        try:
            from pysped.nfe.leiaute import Dup_310
        except ImportError:
            raise orm.except_orm(_(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))

        return Dup_310()
