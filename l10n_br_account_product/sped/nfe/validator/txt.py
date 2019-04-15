# -*- coding: utf-8 -*-
# Copyright (C) 2012  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import Warning as UserError
from odoo.tools.translate import _

# TODO migrate


def validate(invoices, context=None):
    strErro = u''

    for inv in invoices:

        partner = inv.partner_id
        company = inv.company_id

        # Nota fiscal
        if (inv.issuer == '1' or inv.fiscal_type == 'service' or
                not inv.fiscal_document_electronic):
            continue

        if not inv.document_serie_id:
            strErro = u'Nota Fiscal - Série da nota fiscal\n'

        if not inv.fiscal_document_id:
            strErro += u'Nota Fiscal - Tipo de documento fiscal\n'

        if not inv.document_serie_id.internal_sequence_id:
            strErro += (u'Nota Fiscal - Número da nota fiscal, '
                        u'a série deve ter uma sequencia interna\n')

        # Emitente
        if not company.partner_id.legal_name:
            strErro += u'Emitente - Razão Social\n'

        if not company.partner_id.name:
            strErro += u'Emitente - Fantasia\n'

        if not company.partner_id.cnpj_cpf:
            strErro += u'Emitente - CNPJ/CPF\n'

        if not company.partner_id.street:
            strErro += u'Emitente / Endereço - Logradouro\n'

        if not company.partner_id.number:
            strErro += u'Emitente / Endereço - Número\n'

        if not company.partner_id.zip:
            strErro += u'Emitente / Endereço - CEP\n'

        if not company.cnae_main_id:
            strErro += u'Emitente / CNAE Principal\n'

        if not company.partner_id.inscr_est:
            strErro += u'Emitente / Inscrição Estadual\n'

        if not company.partner_id.state_id:
            strErro += u'Emitente / Endereço - Estado\n'
        else:
            if not company.partner_id.state_id.ibge_code:
                strErro += u'Emitente / Endereço - Código do IBGE do estado\n'
            if not company.partner_id.state_id.name:
                strErro += u'Emitente / Endereço - Nome do estado\n'

        if not company.partner_id.l10n_br_city_id:
            strErro += u'Emitente / Endereço - município\n'
        else:
            if not company.partner_id.l10n_br_city_id.name:
                strErro += u'Emitente / Endereço - Nome do município\n'
            if not company.partner_id.l10n_br_city_id.ibge_code:
                strErro += (u'Emitente / Endereço - '
                            u'Código do IBGE do município\n')

        if not company.partner_id.country_id:
            strErro += u'Emitente / Endereço - país\n'
        else:
            if not company.partner_id.country_id.name:
                strErro += u'Emitente / Endereço - Nome do país\n'
            if not company.partner_id.country_id.bc_code:
                strErro += u'Emitente / Endereço - Código do BC do país\n'

        # Destinatário
        if partner.is_company and not partner.legal_name:
            strErro += u'Destinatário - Razão Social\n'

        if partner.country_id.id == company.partner_id.country_id.id:
            if not partner.cnpj_cpf:
                strErro += u'Destinatário - CNPJ/CPF\n'

        if not partner.street:
            strErro += u'Destinatário / Endereço - Logradouro\n'

        if not partner.number:
            strErro += u'Destinatário / Endereço - Número\n'

        if partner.country_id.id == company.partner_id.country_id.id:
            if not partner.zip:
                strErro += u'Destinatário / Endereço - CEP\n'

        if partner.country_id.id == company.partner_id.country_id.id:
            if not partner.state_id:
                strErro += u'Destinatário / Endereço - Estado\n'
            else:
                if not partner.state_id.ibge_code:
                    strErro += (u'Destinatário / Endereço - '
                                u'Código do IBGE do estado\n')
                if not partner.state_id.name:
                    strErro += u'Destinatário / Endereço - Nome do estado\n'

        if partner.country_id.id == company.partner_id.country_id.id:
            if not partner.l10n_br_city_id:
                strErro += u'Destinatário / Endereço - Município\n'
            else:
                if not partner.l10n_br_city_id.name:
                    strErro += u'Destinatário / Endereço - Nome do município\n'
                if not partner.l10n_br_city_id.ibge_code:
                    strErro += (u'Destinatário / Endereço - '
                                u'Código do IBGE do município\n')

        if not partner.country_id:
            strErro += u'Destinatário / Endereço - País\n'
        else:
            if not partner.country_id.name:
                strErro += u'Destinatário / Endereço - Nome do país\n'
            if not partner.country_id.bc_code:
                strErro += u'Destinatário / Endereço - Código do BC do país\n'

        # endereco de entrega
        if inv.partner_shipping_id:

            if partner.id != inv.partner_shipping_id.id:

                if not inv.partner_shipping_id.street:
                    strErro += (u'Destinatário / Endereço de Entrega'
                                u' - Logradouro\n')

                if not inv.partner_shipping_id.number:
                    strErro += u'Destinatário / Endereço de Entrega - Número\n'

                if not inv.partner_shipping_id.zip:
                    strErro += u'Destinatário / Endereço de Entrega - CEP\n'

                if not inv.partner_shipping_id.state_id:
                    strErro += u'Destinatário / Endereço de Entrega - Estado\n'
                else:
                    if not inv.partner_shipping_id.state_id.ibge_code:
                        strErro += (u'Destinatário / Endereço de Entrega - '
                                    u'Código do IBGE do estado\n')
                    if not inv.partner_shipping_id.state_id.name:
                        strErro += (u'Destinatário / Endereço de Entrega - '
                                    u'Nome do estado\n')

                if not inv.partner_shipping_id.l10n_br_city_id:
                    strErro += u'Destinatário / Endereço - Município\n'
                else:
                    if not inv.partner_shipping_id.l10n_br_city_id.name:
                        strErro += (u'Destinatário / Endereço de Entrega - '
                                    u'Nome do município\n')
                    if not inv.partner_shipping_id.l10n_br_city_id.ibge_code:
                        strErro += (u'Destinatário / Endereço de Entrega - '
                                    u'Código do IBGE do município\n')

                if not inv.partner_shipping_id.country_id:
                    strErro += u'Destinatário / Endereço de Entrega - País\n'
                else:
                    if not inv.partner_shipping_id.country_id.name:
                        strErro += (u'Destinatário / Endereço de Entrega - '
                                    u'Nome do país\n')
                    if not inv.partner_shipping_id.country_id.bc_code:
                        strErro += (u'Destinatário / Endereço de Entrega - '
                                    u'Código do BC do país\n')

        # produtos
        for inv_line in inv.invoice_line_ids:
            if inv_line.product_id:
                if not inv_line.product_id.default_code:
                    strErro += (u'Produtos e Serviços: %s, '
                                u'Qtde: %s - '
                                u'Referência/Código do produto\n') % (
                        inv_line.product_id.name, inv_line.quantity)
                if not inv_line.product_id.name:
                    strErro += (u'Produtos e Serviços: %s, '
                                u'Qtde: %s - '
                                u'Referência/Código do produto\n') % (
                        inv_line.product_id.default_code,
                        inv_line.product_id.name,
                        inv_line.quantity)

                if not inv_line.cfop_id:
                    strErro += (u'Produtos e Serviços: %s - '
                                u'%s, Qtde: %s - CFOP\n') % (
                        inv_line.product_id.default_code,
                        inv_line.product_id.name,
                        inv_line.quantity)
                else:
                    if not inv_line.cfop_id.code:
                        strErro += (u'Produtos e Serviços: %s -'
                                    u' %s, Qtde: %s - Código do CFOP\n') % (
                            inv_line.product_id.default_code,
                            inv_line.product_id.name,
                            inv_line.quantity)
                if not inv_line.uom_id:
                    strErro += (u'Produtos e Serviços: %s -'
                                u' %s, Qtde: %s - Unidade de medida\n') % (
                        inv_line.product_id.default_code,
                        inv_line.product_id.name,
                        inv_line.quantity)

                if not inv_line.quantity:
                    strErro += (u'Produtos e Serviços: %s '
                                u'- %s, Qtde: %s - Quantidade\n') % (
                        inv_line.product_id.default_code,
                        inv_line.product_id.name,
                        inv_line.quantity)

                # Se for Documento Fiscal de Produto
                if inv.fiscal_type == 'product':
                    if not inv_line.fiscal_classification_id:
                        strErro += (u'Produtos e Serviços: %s - %s,'
                                    u' Qtde: %s - '
                                    u'Classificação Fiscal(NCM)\n') % (
                            inv_line.product_id.default_code,
                            inv_line.product_id.name,
                            inv_line.quantity)

                if not inv_line.price_unit:
                    strErro += (u'Produtos e Serviços: %s'
                                u' - %s, Qtde: %s - '
                                u'Preco unitario\n') % (
                        inv_line.product_id.default_code,
                        inv_line.product_id.name,
                        inv_line.quantity)

                if inv_line.product_type == 'product':
                    if not inv_line.icms_cst_id:
                        strErro += (u'Produtos e Serviços: %s - %s,'
                                    u' Qtde: %s - CST do ICMS\n') % (
                            inv_line.product_id.default_code,
                            inv_line.product_id.name,
                            inv_line.quantity)

                    if not inv_line.ipi_cst_id:
                        strErro += (u'Produtos e Serviços: %s - %s,'
                                    u' Qtde: %s - CST do IPI\n') % (
                            inv_line.product_id.default_code,
                            inv_line.product_id.name,
                            inv_line.quantity)

                if inv_line.product_type == 'service':
                    if not inv_line.issqn_type:
                        strErro += (u'Produtos e Serviços: %s - %s,'
                                    u' Qtde: %s - Tipo do ISSQN\n') % (
                            inv_line.product_id.default_code,
                            inv_line.product_id.name,
                            inv_line.quantity)

                    if not inv_line.service_type_id:
                        strErro += (u'Produtos e Serviços: %s - %s,'
                                    u' Qtde: %s - Tipo do Serviço\n') % (
                            inv_line.product_id.default_code,
                            inv_line.product_id.name,
                            inv_line.quantity)

                if not inv_line.pis_cst_id:
                    strErro += (u'Produtos e Serviços: %s - %s,'
                                u' Qtde: %s - CST do PIS\n') % (
                        inv_line.product_id.default_code,
                        inv_line.product_id.name,
                        inv_line.quantity)

                if not inv_line.cofins_cst_id:
                    strErro += (u'Produtos e Serviços: %s - %s,'
                                u' Qtde: %s - CST do COFINS\n') % (
                        inv_line.product_id.default_code,
                        inv_line.product_id.name,
                        inv_line.quantity)
    if strErro:
        raise UserError(
            _("Error ! Error Validating NFE:\n '%s'") % (strErro,))

    return True
