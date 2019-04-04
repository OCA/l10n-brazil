# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime
from unicodedata import normalize

from odoo.exceptions import Warning as UserError
from odoo.tools.translate import _

from odoo.addons.l10n_br_account.sped.document import FiscalDocument
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm


class NFe200(FiscalDocument):
    def __init__(self):
        super(NFe200, self).__init__()
        self.nfe = None
        self.nfref = None
        self.det = None
        self.dup = None

    def _serializer(self, invoices, nfe_environment):

        nfes = []

        for invoice in invoices:
            company = invoice.company_id.partner_id

            self.nfe = self.get_NFe()

            self._nfe_identification(invoice, company, nfe_environment)

            self._in_out_adress(invoice)

            for inv_related in invoice.fiscal_document_related_ids:
                self.nfref = self._get_NFRef()
                self._nfe_references(inv_related)
                self.nfe.infNFe.ide.NFref.append(self.nfref)

            self._emmiter(invoice, company)
            self._receiver(invoice, company, nfe_environment)

            i = 0
            for inv_line in invoice.invoice_line_ids:
                i += 1
                self.det = self._get_Det()
                self._details(invoice, inv_line, i)

                for inv_di in inv_line.import_declaration_ids:

                    self.di = self._get_DI()
                    self._di(inv_di)

                    for inv_di_line in inv_di.line_ids:
                        self.di_line = self._get_Addition()
                        self._addition(inv_di_line)
                        self.di.adi.append(self.di_line)

                    self.det.prod.DI.append(self.di)

                self.nfe.infNFe.det.append(self.det)

            if invoice.journal_id.revenue_expense:
                numero_dup = 0
                for move_line in invoice.move_line_receivable_id:
                    numero_dup += 1
                    self.dup = self._get_Dup()
                    self._encashment_data(invoice, move_line, numero_dup)
                    self.nfe.infNFe.cobr.dup.append(self.dup)

            try:
                self._carrier_data(invoice)
            except AttributeError:
                pass

            self.pag = self._get_Pag()
            self._details_pag(invoice)

            self.detPag = self._get_DetPag()
            self._details_pag_data(invoice)
            self.nfe.infNFe.pag.detPag.append(self.detPag)

            self.vol = self._get_Vol()
            self._weight_data(invoice)
            self.nfe.infNFe.transp.vol.append(self.vol)

            self._additional_information(invoice)
            self._total(invoice)
            self._export(invoice)

            # Gera Chave da NFe
            self.nfe.gera_nova_chave()
            nfes.append(self.nfe)

        return nfes

    def _nfe_identification(self, invoice, company, nfe_environment):

        # Identificação da NF-e
        #
        self.nfe.infNFe.ide.cUF.valor = (company.state_id and
                                         company.state_id.ibge_code or '')
        self.nfe.infNFe.ide.cNF.valor = ''
        self.nfe.infNFe.ide.natOp.valor = (
            invoice.fiscal_category_id.name[:60] or '')
        self.nfe.infNFe.ide.indPag.valor = (
            invoice.payment_term_id and
            invoice.payment_term_id.indPag or '0')
        self.nfe.infNFe.ide.mod.valor = invoice.fiscal_document_id.code or ''
        self.nfe.infNFe.ide.serie.valor = invoice.document_serie_id.code or ''
        self.nfe.infNFe.ide.nNF.valor = invoice.fiscal_number or ''
        self.nfe.infNFe.ide.dEmi.valor = invoice.date_invoice or ''
        self.nfe.infNFe.ide.dSaiEnt.valor = datetime.strptime(
            invoice.date_in_out, '%Y-%m-%d %H:%M:%S').date() or ''
        self.nfe.infNFe.ide.cMunFG.valor = ('%s%s') % (
            company.state_id.ibge_code, company.l10n_br_city_id.ibge_code)
        self.nfe.infNFe.ide.tpImp.valor = 1  # (1 - Retrato; 2 - Paisagem)
        self.nfe.infNFe.ide.tpEmis.valor = 1
        self.nfe.infNFe.ide.tpAmb.valor = nfe_environment
        self.nfe.infNFe.ide.finNFe.valor = invoice.nfe_purpose
        self.nfe.infNFe.ide.procEmi.valor = 0
        self.nfe.infNFe.ide.verProc.valor = 'Odoo Brasil v12.0'
        self.nfe.infNFe.compra.xPed.valor = invoice.name or ''

        if invoice.cfop_ids[0].type in ("input"):
            self.nfe.infNFe.ide.tpNF.valor = 0
        else:
            self.nfe.infNFe.ide.tpNF.valor = 1

    def _in_out_adress(self, invoice):

        #
        # Endereço de Entrega ou Retirada
        #
        if invoice.partner_shipping_id:
            if invoice.partner_id.id != invoice.partner_shipping_id.id:
                if self.nfe.infNFe.ide.tpNF.valor == 0:
                    self.nfe.infNFe.retirada.CNPJ.valor = punctuation_rm(
                        invoice.partner_shipping_id.cnpj_cpf)
                    self.nfe.infNFe.retirada.xLgr.valor = (
                        invoice.partner_shipping_id.street or '')
                    self.nfe.infNFe.retirada.nro.valor = (
                        invoice.partner_shipping_id.number or '')
                    self.nfe.infNFe.retirada.xCpl.valor = (
                        invoice.partner_shipping_id.street2 or '')
                    self.nfe.infNFe.retirada.xBairro.valor = (
                        invoice.partner_shipping_id.district or 'Sem Bairro')
                    self.nfe.infNFe.retirada.cMun.valor = '%s%s' % (
                        invoice.partner_shipping_id.state_id.ibge_code,
                        invoice.partner_shipping_id.l10n_br_city_id.ibge_code)
                    self.nfe.infNFe.retirada.xMun.valor = (
                        invoice.partner_shipping_id.l10n_br_city_id.name or '')
                    self.nfe.infNFe.retirada.UF.valor = (
                        invoice.partner_shipping_id.state_id.code or '')
                else:
                    self.nfe.infNFe.entrega.CNPJ.valor = punctuation_rm(
                        invoice.partner_shipping_id.cnpj_cpf)
                    self.nfe.infNFe.entrega.xLgr.valor = (
                        invoice.partner_shipping_id.street or '')
                    self.nfe.infNFe.entrega.nro.valor = (
                        invoice.partner_shipping_id.number or '')
                    self.nfe.infNFe.entrega.xCpl.valor = (
                        invoice.partner_shipping_id.street2 or '')
                    self.nfe.infNFe.entrega.xBairro.valor = (
                        invoice.partner_shipping_id.district or 'Sem Bairro')
                    self.nfe.infNFe.entrega.cMun.valor = '%s%s' % (
                        invoice.partner_shipping_id.state_id.ibge_code,
                        invoice.partner_shipping_id.l10n_br_city_id.ibge_code)
                    self.nfe.infNFe.entrega.xMun.valor = (
                        invoice.partner_shipping_id.l10n_br_city_id.name or '')
                    self.nfe.infNFe.entrega.UF.valor = (
                        invoice.partner_shipping_id.state_id.code or '')

    def _nfe_references(self, inv_related):

        #
        # Documentos referenciadas
        #
        if inv_related.document_type == 'nf':
            self.nfref.refNF.cUF.valor = (
                inv_related.state_id and
                inv_related.state_id.ibge_code or '',)
            self.nfref.refNF.AAMM.valor = datetime.strptime(
                inv_related.date, '%Y-%m-%d').strftime('%y%m') or ''
            self.nfref.refNF.CNPJ.valor = punctuation_rm(inv_related.cnpj_cpf)
            self.nfref.refNF.mod.valor = (
                inv_related.fiscal_document_id and
                inv_related.fiscal_document_id.code or '')
            self.nfref.refNF.serie.valor = inv_related.serie or ''
            self.nfref.refNF.nNF.valor = inv_related.internal_number or ''

        elif inv_related.document_type == 'nfrural':
            self.nfref.refNFP.cUF.valor = (
                inv_related.state_id and
                inv_related.state_id.ibge_code or '',)
            self.nfref.refNFP.AAMM.valor = datetime.strptime(
                inv_related.date, '%Y-%m-%d').strftime('%y%m') or ''
            self.nfref.refNFP.IE.valor = punctuation_rm(inv_related.inscr_est)
            self.nfref.refNFP.mod.valor = (
                inv_related.fiscal_document_id and
                inv_related.fiscal_document_id.code or '')
            self.nfref.refNFP.serie.valor = inv_related.serie or ''
            self.nfref.refNFP.nNF.valor = inv_related.internal_number or ''

            if inv_related.cpfcnpj_type == 'cnpj':
                self.nfref.refNFP.CNPJ.valor = punctuation_rm(
                    inv_related.cnpj_cpf)
            else:
                self.nfref.refNFP.CPF.valor = punctuation_rm(
                    inv_related.cnpj_cpf)

        elif inv_related.document_type == 'nfe':
            self.nfref.refNFe.valor = inv_related.access_key or ''

        elif inv_related.document_type == 'cte':
            self.nfref.refCTe.valor = inv_related.access_key or ''

        elif inv_related.document_type == 'cf':
            self.nfref.refECF.mod.valor = (
                inv_related.fiscal_document_id and
                inv_related.fiscal_document_id.code or '')
            self.nfref.refECF.nECF.valor = inv_related.internal_number
            self.nfref.refECF.nCOO.valor = inv_related.serie

    def _emmiter(self, invoice, company):
        """Emitente"""

        self.nfe.infNFe.emit.CNPJ.valor = punctuation_rm(
            invoice.company_id.partner_id.cnpj_cpf)
        self.nfe.infNFe.emit.xNome.valor = (normalize(
            'NFKD', unicode(
                invoice.company_id.partner_id.legal_name[:60])).encode(
            'ASCII', 'ignore'))
        self.nfe.infNFe.emit.xFant.valor = invoice.company_id.partner_id.name
        self.nfe.infNFe.emit.enderEmit.xLgr.valor = (normalize(
            'NFKD', unicode(company.street or '')).encode('ASCII', 'ignore'))
        self.nfe.infNFe.emit.enderEmit.nro.valor = company.number or ''
        self.nfe.infNFe.emit.enderEmit.xCpl.valor = (normalize(
            'NFKD', unicode(company.street2 or '')).encode('ASCII', 'ignore'))
        self.nfe.infNFe.emit.enderEmit.xBairro.valor = (normalize(
            'NFKD', unicode(
                company.district or 'Sem Bairro')).encode('ASCII', 'ignore'))
        self.nfe.infNFe.emit.enderEmit.cMun.valor = '%s%s' % (
            company.state_id.ibge_code, company.l10n_br_city_id.ibge_code)
        self.nfe.infNFe.emit.enderEmit.xMun.valor = (normalize(
            'NFKD', unicode(
                company.l10n_br_city_id.name or '')).encode('ASCII', 'ignore'))
        self.nfe.infNFe.emit.enderEmit.UF.valor = company.state_id.code or ''
        self.nfe.infNFe.emit.enderEmit.CEP.valor = punctuation_rm(
            company.zip or '')
        self.nfe.infNFe.emit.enderEmit.cPais.valor = (
            company.country_id.bc_code[1:])
        self.nfe.infNFe.emit.enderEmit.xPais.valor = company.country_id.name
        self.nfe.infNFe.emit.enderEmit.fone.valor = punctuation_rm(
            str(company.phone or '').replace(' ', ''))
        self.nfe.infNFe.emit.IE.valor = punctuation_rm(
            invoice.company_id.partner_id.inscr_est)
        for inscr_est_line in\
                invoice.company_id.partner_id.other_inscr_est_lines:
            if inscr_est_line.state_id.id == invoice.partner_id.state_id.id:
                self.nfe.infNFe.emit.IEST.valor = punctuation_rm(
                    inscr_est_line.inscr_est)
            else:
                self.nfe.infNFe.emit.IEST.valor = ''
        self.nfe.infNFe.emit.IM.valor = punctuation_rm(
            invoice.company_id.partner_id.inscr_mun or '')
        self.nfe.infNFe.emit.CRT.valor = invoice.company_id.fiscal_type or ''

        if invoice.company_id.partner_id.inscr_mun:
            self.nfe.infNFe.emit.CNAE.valor = punctuation_rm(
                invoice.company_id.cnae_main_id.code or '')

    def _receiver(self, invoice, company, nfe_environment):
        """Destinatário"""

        partner_bc_code = ''
        address_invoice_state_code = ''
        address_invoice_city = ''
        partner_cep = ''

        if invoice.partner_id.country_id.bc_code:
            partner_bc_code = invoice.partner_id.country_id.bc_code[1:]

        if invoice.partner_id.country_id.id != \
                invoice.company_id.country_id.id:
            address_invoice_state_code = 'EX'
            address_invoice_city = 'Exterior'
            address_invoice_city_code = '9999999'
        else:
            address_invoice_state_code = invoice.partner_id.state_id.code
            address_invoice_city = (normalize(
                'NFKD', unicode(
                    invoice.partner_id.l10n_br_city_id.name or '')).encode(
                'ASCII', 'ignore'))
            address_invoice_city_code = ('%s%s') % (
                invoice.partner_id.state_id.ibge_code,
                invoice.partner_id.l10n_br_city_id.ibge_code)
            partner_cep = punctuation_rm(invoice.partner_id.zip)

        # Se o ambiente for de teste deve ser
        # escrito na razão do destinatário
        if nfe_environment == 2:
            self.nfe.infNFe.dest.xNome.valor = (
                'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL')
            self.nfe.infNFe.dest.CNPJ.valor = '99999999000191'
        else:
            self.nfe.infNFe.dest.xNome.valor = (normalize(
                'NFKD', unicode(
                    invoice.partner_id.legal_name[:60] or '')
            ).encode('ASCII', 'ignore'))

            if invoice.partner_id.is_company:
                self.nfe.infNFe.dest.IE.valor = punctuation_rm(
                    invoice.partner_id.inscr_est)

            if invoice.partner_id.country_id.id == \
                    invoice.company_id.country_id.id:
                if invoice.partner_id.is_company:
                    self.nfe.infNFe.dest.CNPJ.valor = punctuation_rm(
                        invoice.partner_id.cnpj_cpf)
                else:
                    self.nfe.infNFe.dest.CPF.valor = punctuation_rm(
                        invoice.partner_id.cnpj_cpf)

        self.nfe.infNFe.dest.indIEDest.valor = \
            invoice.partner_id.partner_fiscal_type_id.ind_ie_dest

        self.nfe.infNFe.dest.enderDest.xLgr.valor = (normalize(
            'NFKD', unicode(
                invoice.partner_id.street or '')).encode('ASCII', 'ignore'))
        self.nfe.infNFe.dest.enderDest.nro.valor = (
            invoice.partner_id.number or '')
        self.nfe.infNFe.dest.enderDest.xCpl.valor = (normalize(
            'NFKD', unicode(
                invoice.partner_id.street2 or '')).encode('ASCII', 'ignore'))
        self.nfe.infNFe.dest.enderDest.xBairro.valor = (normalize(
            'NFKD', unicode(
                invoice.partner_id.district or 'Sem Bairro')
        ).encode('ASCII', 'ignore'))
        self.nfe.infNFe.dest.enderDest.cMun.valor = address_invoice_city_code
        self.nfe.infNFe.dest.enderDest.xMun.valor = address_invoice_city
        self.nfe.infNFe.dest.enderDest.UF.valor = address_invoice_state_code
        self.nfe.infNFe.dest.enderDest.CEP.valor = partner_cep
        self.nfe.infNFe.dest.enderDest.cPais.valor = partner_bc_code
        self.nfe.infNFe.dest.enderDest.xPais.valor = (
            invoice.partner_id.country_id.name or '')
        self.nfe.infNFe.dest.enderDest.fone.valor = punctuation_rm(
            invoice.partner_id.phone or '').replace(' ', '')
        self.nfe.infNFe.dest.email.valor = invoice.partner_id.email or ''

    def _details(self, invoice, invoice_line, index):
        """Detalhe"""

        self.det.nItem.valor = index

        if invoice_line.product_id:
            self.det.prod.cProd.valor = invoice_line.product_id.code or ''
            self.det.prod.cEAN.valor =\
                invoice_line.product_id.barcode or 'SEM GTIN'
            self.det.prod.cEANTrib.valor =\
                invoice_line.product_id.barcode or ''
            self.det.prod.xProd.valor = (normalize(
                'NFKD', unicode(
                    invoice_line.product_id.name[:120] or '')
            ).encode('ASCII', 'ignore'))
        else:
            self.det.prod.cProd.valor = invoice_line.code or ''
            self.det.prod.xProd.valor = (normalize(
                'NFKD', unicode(
                    invoice_line.name[:120] or '')
            ).encode('ASCII', 'ignore'))

        self.det.prod.NCM.valor = punctuation_rm(
            invoice_line.fiscal_classification_id.code or '')[:8]
        self.det.prod.EXTIPI.valor = punctuation_rm(
            invoice_line.fiscal_classification_id.code or '')[8:]
        self.det.prod.CEST.valor = punctuation_rm(
            invoice_line.cest_id.code or '')
        self.det.prod.nFCI.valor = invoice_line.fci or ''
        self.det.prod.CFOP.valor = invoice_line.cfop_id.code
        self.det.prod.uCom.valor = invoice_line.uom_id.name or ''
        self.det.prod.qCom.valor = str("%.4f" % invoice_line.quantity)
        self.det.prod.vUnCom.valor = str("%.7f" % invoice_line.price_unit)
        self.det.prod.vProd.valor = str("%.2f" % invoice_line.price_gross)
        self.det.prod.uTrib.valor = self.det.prod.uCom.valor
        self.det.prod.qTrib.valor = self.det.prod.qCom.valor
        self.det.prod.vUnTrib.valor = self.det.prod.vUnCom.valor
        self.det.prod.vFrete.valor = str("%.2f" % invoice_line.freight_value)
        self.det.prod.vSeg.valor = str("%.2f" % invoice_line.insurance_value)
        self.det.prod.vDesc.valor = str("%.2f" % invoice_line.discount_value)
        self.det.prod.vOutro.valor = str(
            "%.2f" % invoice_line.other_costs_value)
        self.det.prod.xPed.valor = invoice_line.partner_order or ''
        self.det.prod.nItemPed.valor = invoice_line.partner_order_line or ''
        self.det.infAdProd.valor = invoice_line.fiscal_comment or ''

        #
        # Produto entra no total da NF-e
        #
        self.det.prod.indTot.valor = 1

        if invoice_line.product_type == 'product':
            # ICMS
            if invoice_line.icms_cst_id.code > 100:
                self.det.imposto.ICMS.CSOSN.valor = (
                    invoice_line.icms_cst_id.code)
                self.det.imposto.ICMS.pCredSN.valor = str(
                    "%.2f" % invoice_line.icms_percent)
                self.det.imposto.ICMS.vCredICMSSN.valor = str(
                    "%.2f" % invoice_line.icms_value)

            self.det.imposto.ICMS.orig.valor = invoice_line.icms_origin or ''
            self.det.imposto.ICMS.CST.valor = invoice_line.icms_cst_id.code
            self.det.imposto.ICMS.modBC.valor = invoice_line.icms_base_type
            self.det.imposto.ICMS.vBC.valor = str(
                "%.2f" % invoice_line.icms_base)
            self.det.imposto.ICMS.pRedBC.valor = str(
                "%.2f" % invoice_line.icms_percent_reduction)
            self.det.imposto.ICMS.pICMS.valor = str(
                "%.2f" % invoice_line.icms_percent)
            self.det.imposto.ICMS.vICMS.valor = str(
                "%.2f" % invoice_line.icms_value)
            self.det.imposto.ICMS.motDesICMS.valor = (
                invoice_line.icms_relief_id.code or '')

            # ICMS ST
            self.det.imposto.ICMS.modBCST.valor = (
                invoice_line.icms_st_base_type)
            self.det.imposto.ICMS.pMVAST.valor = str(
                "%.2f" % invoice_line.icms_st_mva)
            self.det.imposto.ICMS.pRedBCST.valor = str(
                "%.2f" % invoice_line.icms_st_percent_reduction)
            self.det.imposto.ICMS.vBCST.valor = str(
                "%.2f" % invoice_line.icms_st_base)
            self.det.imposto.ICMS.pICMSST.valor = str(
                "%.2f" % invoice_line.icms_st_percent)
            self.det.imposto.ICMS.vICMSST.valor = str(
                "%.2f" % invoice_line.icms_st_value)

            # Informação do ICMS Interestadual nas vendas para consumidor final
            self.det.imposto.ICMSUFDest.vBCUFDest.valor = str(
                "%.2f" % invoice_line.icms_dest_base)
            self.det.imposto.ICMSUFDest.pFCPUFDest.valor = str(
                "%.2f" % invoice_line.icms_fcp_percent)
            self.det.imposto.ICMSUFDest.pICMSUFDest.valor = str(
                "%.2f" % invoice_line.icms_dest_percent)
            self.det.imposto.ICMSUFDest.pICMSInter.valor = str(
                "%.2f" % invoice_line.icms_origin_percent)
            self.det.imposto.ICMSUFDest.pICMSInterPart.valor = str(
                "%.2f" % invoice_line.icms_part_percent)
            self.det.imposto.ICMSUFDest.vFCPUFDest.valor = str(
                "%.2f" % invoice_line.icms_fcp_value)
            self.det.imposto.ICMSUFDest.vICMSUFDest.valor = str(
                "%.2f" % invoice_line.icms_dest_value)
            self.det.imposto.ICMSUFDest.vICMSUFRemet.valor = str(
                "%.2f" % invoice_line.icms_origin_value)
            # IPI
            self.det.imposto.IPI.CST.valor = invoice_line.ipi_cst_id.code
            if invoice_line.ipi_type == 'percent' or '':
                self.det.imposto.IPI.vBC.valor = str(
                    "%.2f" % invoice_line.ipi_base)
                self.det.imposto.IPI.pIPI.valor = str(
                    "%.2f" % invoice_line.ipi_percent)
            if invoice_line.ipi_type == 'quantity':
                pesol = 0
                if invoice_line.product_id:
                    pesol = invoice_line.product_id.weight_net
                    self.det.imposto.IPI.qUnid.valor = str(
                        "%.2f" % invoice_line.quantity * pesol)
                    self.det.imposto.IPI.vUnid.valor = str(
                        "%.2f" % invoice_line.ipi_percent)
            self.det.imposto.IPI.vIPI.valor = str(
                "%.2f" % invoice_line.ipi_value)
            self.det.imposto.IPI.cEnq.valor = str(
                invoice_line.ipi_guideline_id.code or '999').zfill(3)

        else:
            # ISSQN
            self.det.imposto.ISSQN.vBC.valor = str(
                "%.2f" % invoice_line.issqn_base)
            self.det.imposto.ISSQN.vAliq.valor = str(
                "%.2f" % invoice_line.issqn_percent)
            self.det.imposto.ISSQN.vISSQN.valor = str(
                "%.2f" % invoice_line.issqn_value)
            self.det.imposto.ISSQN.cMunFG.valor = ('%s%s') % (
                invoice.partner_id.state_id.ibge_code,
                invoice.partner_id.l10n_br_city_id.ibge_code)
            self.det.imposto.ISSQN.cListServ.valor = punctuation_rm(
                invoice_line.service_type_id.code or '')
            self.det.imposto.ISSQN.cSitTrib.valor = invoice_line.issqn_type

        # PIS
        self.det.imposto.PIS.CST.valor = invoice_line.pis_cst_id.code
        self.det.imposto.PIS.vBC.valor = str("%.2f" % invoice_line.pis_base)
        self.det.imposto.PIS.pPIS.valor = str(
            "%.2f" % invoice_line.pis_percent)
        self.det.imposto.PIS.vPIS.valor = str("%.2f" % invoice_line.pis_value)

        # PISST
        self.det.imposto.PISST.vBC.valor = str(
            "%.2f" % invoice_line.pis_st_base)
        self.det.imposto.PISST.pPIS.valor = str(
            "%.2f" % invoice_line.pis_st_percent)
        self.det.imposto.PISST.qBCProd.valor = ''
        self.det.imposto.PISST.vAliqProd.valor = ''
        self.det.imposto.PISST.vPIS.valor = str(
            "%.2f" % invoice_line.pis_st_value)

        # COFINS
        self.det.imposto.COFINS.CST.valor = invoice_line.cofins_cst_id.code
        self.det.imposto.COFINS.vBC.valor = str(
            "%.2f" % invoice_line.cofins_base)
        self.det.imposto.COFINS.pCOFINS.valor = str(
            "%.2f" % invoice_line.cofins_percent)
        self.det.imposto.COFINS.vCOFINS.valor = str(
            "%.2f" % invoice_line.cofins_value)

        # COFINSST
        self.det.imposto.COFINSST.vBC.valor = str(
            "%.2f" % invoice_line.cofins_st_base)
        self.det.imposto.COFINSST.pCOFINS.valor = str(
            "%.2f" % invoice_line.cofins_st_percent)
        self.det.imposto.COFINSST.qBCProd.valor = ''
        self.det.imposto.COFINSST.vAliqProd.valor = ''
        self.det.imposto.COFINSST.vCOFINS.valor = str(
            "%.2f" % invoice_line.cofins_st_value)

        # II
        self.det.imposto.II.vBC.valor = str("%.2f" % invoice_line.ii_base)
        self.det.imposto.II.vDespAdu.valor = str(
            "%.2f" % invoice_line.ii_customhouse_charges)
        self.det.imposto.II.vII.valor = str("%.2f" % invoice_line.ii_value)
        self.det.imposto.II.vIOF.valor = str("%.2f" % invoice_line.ii_iof)

        self.det.imposto.vTotTrib.valor = str(
            "%.2f" % invoice_line.total_taxes)

    def _di(self, invoice_line_di):
        self.di.nDI.valor = invoice_line_di.name
        self.di.dDI.valor = invoice_line_di.date_registration or ''
        self.di.xLocDesemb.valor = invoice_line_di.location
        self.di.UFDesemb.valor = invoice_line_di.state_id.code or ''
        self.di.dDesemb.valor = invoice_line_di.date_release or ''
        self.di.cExportador.valor = invoice_line_di.exporting_code

    def _addition(self, invoice_line_di):
        self.di_line.nAdicao.valor = invoice_line_di.name
        self.di_line.nSeqAdic.valor = invoice_line_di.sequence
        self.di_line.cFabricante.valor = invoice_line_di.manufacturer_code
        self.di_line.vDescDI.valor = str(
            "%.2f" % invoice_line_di.amount_discount)

    def _encashment_data(self, invoice, move_line, numero_dup):
        """Dados de Cobrança"""

        if invoice.type in ('out_invoice', 'in_refund'):
            value = move_line.debit
        else:
            value = move_line.credit

        self.dup.nDup.valor = str(numero_dup).zfill(3)

        self.dup.dVenc.valor = (move_line.date_maturity or
                                invoice.date_due or
                                invoice.date_invoice)
        self.dup.vDup.valor = str("%.2f" % value)

    def _carrier_data(self, invoice):
        """Dados da Transportadora e veiculo"""

        self.nfe.infNFe.transp.modFrete.valor = (
            invoice.incoterm and
            invoice.incoterm.freight_responsibility or '9')

        if invoice.carrier_id:

            if invoice.carrier_id.partner_id.is_company:
                self.nfe.infNFe.transp.transporta.CNPJ.valor = \
                    punctuation_rm(
                        invoice.carrier_id.partner_id.cnpj_cpf or '')
            else:
                self.nfe.infNFe.transp.transporta.CPF.valor = \
                    punctuation_rm(
                        invoice.carrier_id.partner_id.cnpj_cpf or '')

            self.nfe.infNFe.transp.transporta.xNome.valor = (
                invoice.carrier_id.partner_id.legal_name[:60] or '')
            self.nfe.infNFe.transp.transporta.IE.valor = punctuation_rm(
                invoice.carrier_id.partner_id.inscr_est)
            self.nfe.infNFe.transp.transporta.xEnder.valor = (
                invoice.carrier_id.partner_id.street or '')
            self.nfe.infNFe.transp.transporta.xMun.valor = (
                invoice.carrier_id.partner_id.l10n_br_city_id.name or '')
            self.nfe.infNFe.transp.transporta.UF.valor = (
                invoice.carrier_id.partner_id.state_id.code or '')

        if invoice.vehicle_id:
            self.nfe.infNFe.transp.veicTransp.placa.valor = (
                invoice.vehicle_id.plate or '')
            self.nfe.infNFe.transp.veicTransp.UF.valor = (
                invoice.vehicle_id.plate.state_id.code or '')
            self.nfe.infNFe.transp.veicTransp.RNTC.valor = (
                invoice.vehicle_id.rntc_code or '')

    def _weight_data(self, invoice):
        """Campos do Transporte da NF-e Bloco 381"""

        self.vol.qVol.valor = invoice.number_of_packages
        self.vol.esp.valor = invoice.kind_of_packages or ''
        self.vol.marca.valor = invoice.brand_of_packages or ''
        self.vol.nVol.valor = invoice.notation_of_packages or ''
        self.vol.pesoL.valor = str("%.2f" % invoice.weight_net)
        self.vol.pesoB.valor = str("%.2f" % invoice.weight)

    def _additional_information(self, invoice):
        """Informações adicionais"""

        self.nfe.infNFe.infAdic.infAdFisco.valor = invoice.fiscal_comment or ''
        self.nfe.infNFe.infAdic.infCpl.valor = invoice.comment or ''

    def _total(self, invoice):
        """Totais"""

        self.nfe.infNFe.total.ICMSTot.vBC.valor = str(
            "%.2f" % invoice.icms_base)
        self.nfe.infNFe.total.ICMSTot.vICMS.valor = str(
            "%.2f" % invoice.icms_value)
        self.nfe.infNFe.total.ICMSTot.vFCPUFDest.valor = str(
            "%.2f" % invoice.icms_fcp_value)
        self.nfe.infNFe.total.ICMSTot.vICMSUFDest.valor = str(
            "%.2f" % invoice.icms_dest_value)
        self.nfe.infNFe.total.ICMSTot.vICMSUFRemet.valor = str(
            "%.2f" % invoice.icms_origin_value)
        self.nfe.infNFe.total.ICMSTot.vBCST.valor = str(
            "%.2f" % invoice.icms_st_base)
        self.nfe.infNFe.total.ICMSTot.vST.valor = str(
            "%.2f" % invoice.icms_st_value)
        self.nfe.infNFe.total.ICMSTot.vProd.valor = str(
            "%.2f" % invoice.amount_gross)
        self.nfe.infNFe.total.ICMSTot.vFrete.valor = str(
            "%.2f" % invoice.amount_freight)
        self.nfe.infNFe.total.ICMSTot.vSeg.valor = str(
            "%.2f" % invoice.amount_insurance)
        self.nfe.infNFe.total.ICMSTot.vDesc.valor = str(
            "%.2f" % invoice.amount_discount)
        self.nfe.infNFe.total.ICMSTot.vII.valor = str(
            "%.2f" % invoice.ii_value)
        self.nfe.infNFe.total.ICMSTot.vIPI.valor = str(
            "%.2f" % invoice.ipi_value)
        self.nfe.infNFe.total.ICMSTot.vPIS.valor = str(
            "%.2f" % invoice.pis_value)
        self.nfe.infNFe.total.ICMSTot.vCOFINS.valor = str(
            "%.2f" % invoice.cofins_value)
        self.nfe.infNFe.total.ICMSTot.vOutro.valor = str(
            "%.2f" % invoice.amount_costs)
        self.nfe.infNFe.total.ICMSTot.vNF.valor = str(
            "%.2f" % invoice.amount_total)
        self.nfe.infNFe.total.ICMSTot.vTotTrib.valor = str(
            "%.2f" % invoice.amount_total_taxes)

    def _export(self, invoice):
        "Informações de exportação"
        self.nfe.infNFe.exporta.UFEmbarq.valor = (
            invoice.shipping_state_id.code or '')
        self.nfe.infNFe.exporta.xLocEmbarq.valor = (
            invoice.shipping_location or '')

    def get_NFe(self):

        try:
            from pysped.nfe.leiaute import NFe_200
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))

        return NFe_200()

    def _get_NFRef(self):
        try:
            from pysped.nfe.leiaute import NFRef_200
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))

        return NFRef_200()

    def _get_Det(self):
        try:
            from pysped.nfe.leiaute import Det_200
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))

        return Det_200()

    def _get_DI(self):
        try:
            from pysped.nfe.leiaute import DI_200
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))
        return DI_200()

    def _get_Addition(self):
        try:
            from pysped.nfe.leiaute import Adi_200
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))
        return Adi_200()

    def _get_Vol(self):
        try:
            from pysped.nfe.leiaute import Vol_200
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))
        return Vol_200()

    def _get_Dup(self):

        try:
            from pysped.nfe.leiaute import Dup_200
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))

        return Dup_200()

    def get_xml(self, invoices, nfe_environment):
        """"""
        result = []
        for nfe in self._serializer(invoices, nfe_environment):
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

    def _nfe_identification(self, invoice, company, nfe_environment):

        super(NFe310, self)._nfe_identification(
            invoice, company, nfe_environment)

        self.nfe.infNFe.ide.idDest.valor = (
            invoice.fiscal_position_id.cfop_id.id_dest or '')
        self.nfe.infNFe.ide.indFinal.valor = invoice.ind_final or ''
        self.nfe.infNFe.ide.indPres.valor = invoice.ind_pres or ''
        self.nfe.infNFe.ide.dhEmi.valor = datetime.strptime(
            invoice.date_hour_invoice, '%Y-%m-%d %H:%M:%S')
        self.nfe.infNFe.ide.dhSaiEnt.valor = datetime.strptime(
            invoice.date_in_out, '%Y-%m-%d %H:%M:%S')
        self.aut_xml = self._get_AutXML()
        self.aut_xml.CNPJ.valor = punctuation_rm(
            invoice.company_id.accountant_cnpj_cpf)
        self.nfe.infNFe.autXML.append(self.aut_xml)

    def _receiver(self, invoice, company, nfe_environment):
        super(NFe310, self)._receiver(
            invoice, company, nfe_environment)

        if invoice.partner_id.country_id.id != \
                invoice.company_id.country_id.id:
            self.nfe.infNFe.dest.idEstrangeiro.valor = punctuation_rm(
                invoice.partner_id.cnpj_cpf)

    def _di(self, invoice_line_di):
        super(NFe310, self)._di(invoice_line_di)

        self.di.tpViaTransp.valor = invoice_line_di.type_transportation or ''
        self.di.vAFRMM.valor = str("%.2f" % invoice_line_di.afrmm_value)
        self.di.tpIntermedio.valor = invoice_line_di.type_import or ''
        self.di.CNPJ.valor = invoice_line_di.exporting_code or ''
        self.di.UFTerceiro.valor = (
            invoice_line_di.thirdparty_state_id.code or '')

    def _export(self, invoice):
        "Informações de exportação"
        self.nfe.infNFe.exporta.UFSaidaPais.valor = (
            invoice.shipping_state_id.code or '')
        self.nfe.infNFe.exporta.xLocExporta.valor = (
            invoice.shipping_location or '')
        self.nfe.infNFe.exporta.xLocDespacho.valor = (
            invoice.expedition_location or '')

    def get_NFe(self):
        try:
            from pysped.nfe.leiaute import NFe_310
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))

        return NFe_310()

    def _get_NFRef(self):
        try:
            from pysped.nfe.leiaute import NFRef_310
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))

        return NFRef_310()

    def _get_Det(self):
        try:
            from pysped.nfe.leiaute import Det_310
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))

        return Det_310()

    def _get_Dup(self):
        try:
            from pysped.nfe.leiaute import Dup_310
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))

        return Dup_310()

    def _get_DI(self):
        try:
            from pysped.nfe.leiaute import DI_310
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))
        return DI_310()

    def _get_AutXML(self):
        try:
            from pysped.nfe.leiaute import AutXML_310
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))
        return AutXML_310()


class NFe400(NFe310):
    def __init__(self):
        super(NFe400, self).__init__()

    def _details_pag(self, invoice):

        # TODO - implementar campo
        self.pag.vTroco.valor = ''

    def _details_pag_data(self, invoice):
        # TODO - existe a possibilidade de pagar uma parte
        # em uma forma de pagto e outra parte em outra
        # ex.: metade em dinheiro e metade boleto
        self.detPag.tPag.valor = invoice.type_nf_payment
        self.detPag.vPag.valor = invoice.amount_total

    def get_NFe(self):
        try:
            from pysped.nfe.leiaute import NFe_400
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))

        return NFe_400()

    def _get_NFRef(self):
        try:
            from pysped.nfe.leiaute import NFRef_400
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))

        return NFRef_400()

    def _get_Det(self):
        try:
            from pysped.nfe.leiaute import Det_400
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))
        return Det_400()

    def _get_Dup(self):
        try:
            from pysped.nfe.leiaute import Dup_400
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))
        return Dup_400()

    def _get_DI(self):
        try:
            from pysped.nfe.leiaute import DI_400
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))
        return DI_400()

    def _get_Pag(self):
        try:
            from pysped.nfe.leiaute import Pag_400
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))
        return Pag_400()

    def _get_DetPag(self):
        try:
            from pysped.nfe.leiaute import DetPag_400
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))
        return DetPag_400()

    def _get_AutXML(self):
        try:
            from pysped.nfe.leiaute import AutXML_400
        except ImportError:
            raise UserError(
                _(u"Biblioteca PySPED não instalada!"))
        return AutXML_400()
