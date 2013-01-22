# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2012  Renato Lima - Akretion                                  #
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

from osv import osv
from tools.translate import _
import pooler


def validate(cr, uid, ids, context=None):
    strErro = u''
    pool = pooler.get_pool(cr.dbname)

    if context is None:
        context = {}

    for inv in pool.get('account.invoice').browse(cr, uid, ids):

        #Nota fiscal
        if not inv.own_invoice or inv.fiscal_type == 'service' or \
        not inv.fiscal_document_electronic:
            continue

        if not inv.document_serie_id:
            strErro = u'Nota Fiscal - Série da nota fiscal\n'

        if not inv.fiscal_document_id:
            strErro += u'Nota Fiscal - Tipo de documento fiscal\n'

        if not inv.document_serie_id.internal_sequence_id:
            strErro += u'Nota Fiscal - Número da nota fiscal, a série deve ter uma sequencia interna\n'

        #Emitente
        if not inv.company_id.partner_id.legal_name:
            strErro += u'Emitente - Razão Social\n'

        if not inv.company_id.partner_id.name:
            strErro += u'Emitente - Fantasia\n'

        if not inv.company_id.partner_id.cnpj_cpf:
            strErro += u'Emitente - CNPJ/CPF\n'

        if not inv.company_id.partner_id.street:
            strErro += u'Emitente / Endereço - Logradouro\n'

        if not inv.company_id.partner_id.number:
            strErro += u'Emitente / Endereço - Número\n'

        if not inv.company_id.partner_id.zip:
            strErro += u'Emitente / Endereço - CEP\n'

        if not inv.company_id.cnae_main_id:
            strErro += u'Emitente / CNAE Principal\n'

        if not inv.company_id.partner_id.inscr_est:
            strErro += u'Emitente / Inscrição Estadual\n'

        if not inv.company_id.partner_id.state_id:
            strErro += u'Emitente / Endereço - Estado\n'
        else:
            if not inv.company_id.partner_id.state_id.ibge_code:
                strErro += u'Emitente / Endereço - Código do IBGE do estado\n'
            if not inv.company_id.partner_id.state_id.name:
                strErro += u'Emitente / Endereço - Nome do estado\n'

        if not inv.company_id.partner_id.l10n_br_city_id:
            strErro += u'Emitente / Endereço - município\n'
        else:
            if not inv.company_id.partner_id.l10n_br_city_id.name:
                strErro += u'Emitente / Endereço - Nome do município\n'
            if not inv.company_id.partner_id.l10n_br_city_id.ibge_code:
                strErro += u'Emitente / Endereço - Código do IBGE do município\n'

        if not inv.company_id.partner_id.country_id:
            strErro += u'Emitente / Endereço - país\n'
        else:
            if not inv.company_id.partner_id.country_id.name:
                strErro += u'Emitente / Endereço - Nome do país\n'
            if not inv.company_id.partner_id.country_id.bc_code:
                strErro += u'Emitente / Endereço - Código do BC do país\n'

        #Destinatário
        if inv.partner_id.is_company and not inv.partner_id.legal_name:
            strErro += u'Destinatário - Razão Social\n'

        if not inv.partner_id.cnpj_cpf:
            strErro += u'Destinatário - CNPJ/CPF\n'

        if not inv.partner_id.street:
            strErro += u'Destinatário / Endereço - Logradouro\n'

        if not inv.partner_id.number:
            strErro += u'Destinatário / Endereço - Número\n'

        if inv.partner_id.country_id.id == inv.company_id.partner_id.country_id.id:
            if not inv.partner_id.zip:
                strErro += u'Destinatário / Endereço - CEP\n'

        if inv.partner_id.country_id.id == inv.company_id.partner_id.country_id.id:
            if not inv.partner_id.state_id:
                strErro += u'Destinatário / Endereço - Estado\n'
            else:
                if not inv.partner_id.state_id.ibge_code:
                    strErro += u'Destinatário / Endereço - Código do IBGE do estado\n'
                if not inv.partner_id.state_id.name:
                    strErro += u'Destinatário / Endereço - Nome do estado\n'

        if inv.partner_id.country_id.id == inv.company_id.partner_id.country_id.id:
            if not inv.partner_id.l10n_br_city_id:
                strErro += u'Destinatário / Endereço - Município\n'
            else:
                if not inv.partner_id.l10n_br_city_id.name:
                    strErro += u'Destinatário / Endereço - Nome do município\n'
                if not inv.partner_id.l10n_br_city_id.ibge_code:
                    strErro += u'Destinatário / Endereço - Código do IBGE do município\n'

        if not inv.partner_id.country_id:
            strErro += u'Destinatário / Endereço - País\n'
        else:
            if not inv.partner_id.country_id.name:
                strErro += u'Destinatário / Endereço - Nome do país\n'
            if not inv.partner_id.country_id.bc_code:
                strErro += u'Destinatário / Endereço - Código do BC do país\n'

        #endereco de entrega
        if inv.partner_shipping_id:

            if inv.partner_id.id != inv.partner_shipping_id.id:

                if not inv.partner_shipping_id.street:
                    strErro += u'Destinatário / Endereço de Entrega - Logradouro\n'

                if not inv.partner_shipping_id.number:
                    strErro += u'Destinatário / Endereço de Entrega - Número\n'

                if not inv.partner_shipping_id.zip:
                    strErro += u'Destinatário / Endereço de Entrega - CEP\n'

                if not inv.partner_shipping_id.state_id:
                    strErro += u'Destinatário / Endereço de Entrega - Estado\n'
                else:
                    if not inv.partner_shipping_id.state_id.ibge_code:
                        strErro += u'Destinatário / Endereço de Entrega - Código do IBGE do estado\n'
                    if not inv.partner_shipping_id.state_id.name:
                        strErro += u'Destinatário / Endereço de Entrega - Nome do estado\n'

                if not inv.partner_shipping_id.l10n_br_city_id:
                    strErro += u'Destinatário / Endereço - Município\n'
                else:
                    if not inv.partner_shipping_id.l10n_br_city_id.name:
                        strErro += u'Destinatário / Endereço de Entrega - Nome do município\n'
                    if not inv.partner_shipping_id.l10n_br_city_id.ibge_code:
                        strErro += u'Destinatário / Endereço de Entrega - Código do IBGE do município\n'

                if not inv.partner_shipping_id.country_id:
                    strErro += u'Destinatário / Endereço de Entrega - País\n'
                else:
                    if not inv.partner_shipping_id.country_id.name:
                        strErro += u'Destinatário / Endereço de Entrega - Nome do país\n'
                    if not inv.partner_shipping_id.country_id.bc_code:
                        strErro += u'Destinatário / Endereço de Entrega - Código do BC do país\n'

        #produtos
        for inv_line in inv.invoice_line:
            if inv_line.product_id:
                if not inv_line.product_id.default_code:
                    strErro += u'Produtos e Serviços: %s, Qtde: %s - Referência/Código do produto\n' % (inv_line.product_id.name, inv_line.quantity)
                if not inv_line.product_id.name:
                    strErro += u'Produtos e Serviços: %s, Qtde: %s - Nome do produto\n' % (inv_line.product_id.name, inv_line.quantity)

                if not inv_line.cfop_id:
                    strErro += u'Produtos e Serviços: %s, Qtde: %s - CFOP\n' % (inv_line.product_id.name, inv_line.quantity)
                else:
                    if not inv_line.cfop_id.code:
                        strErro += u'Produtos e Serviços: %s, Qtde: %s - Código do CFOP\n' % (inv_line.product_id.name, inv_line.quantity)

                if not inv_line.uos_id:
                    strErro += u'Produtos e Serviços: %s, Qtde: %s - Unidade de medida\n' % (inv_line.product_id.name, inv_line.quantity)

                if not inv_line.quantity:
                    strErro += u'Produtos e Serviços: %s, Qtde: %s - Quantidade\n' % (inv_line.product_id.name, inv_line.quantity)

                if not inv_line.price_unit:
                    strErro += u'Produtos e Serviços: %s, Qtde: %s - Preco unitario\n' % (inv_line.product_id.name, inv_line.quantity)

                if not inv_line.icms_cst:
                    strErro += u'Produtos e Serviços: %s, Qtde: %s - CST do ICMS\n' % (inv_line.product_id.name, inv_line.quantity)

                if not inv_line.ipi_cst:
                    strErro += u'Produtos e Serviços: %s, Qtde: %s - CST do IPI\n' % (inv_line.product_id.name, inv_line.quantity)

                if not inv_line.pis_cst:
                    strErro += u'Produtos e Serviços: %s, Qtde: %s - CST do PIS\n' % (inv_line.product_id.name, inv_line.quantity)

                if not inv_line.cofins_cst:
                    strErro += u'Produtos e Serviços: %s, Qtde: %s - CST do COFINS\n' % (inv_line.product_id.name, inv_line.quantity)

    if strErro:
        raise osv.except_osv(
            _('Error !'), ("Error Validating NFE:\n '%s'") % (strErro, ))

    return True
