# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp import models, fields, api
from openerp.addons.l10n_br_account_product.models.product import \
    PRODUCT_ORIGIN
from openerp.addons.l10n_br_account_product.models.l10n_br_account_product\
    import (GNRE_RESPONSE,
            GNRE_RESPONSE_DEFAULT)
from operator import attrgetter


class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'

    cfop_id = fields.Many2one('l10n_br_account_product.cfop', 'CFOP')
    ind_final = fields.Selection([
        ('0', u'Não'),
        ('1', u'Sim')
    ], u'Operação com Consumidor final', readonly=True,
        states={'draft': [('readonly', False)]}, required=False,
        help=u'Indica operação com Consumidor final.', default='0')
    icms_st_extract = fields.Boolean(
        string=u'Remover Substituição Tributária dos totais',
        states={'draft': [('readonly', False)]},
        default=False
    )
    tax_estimate = fields.Boolean(
        string=u'Calcular total dos tributos',
        states={'draft': [('readonly', False)]},
        default=True
    )

class AccountFiscalPositionTaxTemplate(models.Model):
    _inherit = 'account.fiscal.position.tax.template'

    fiscal_classification_id = fields.Many2one(
        'account.product.fiscal.classification.template', 'NCM')

    origin = fields.Selection(PRODUCT_ORIGIN, 'Origem',)
    tax_ipi_guideline_id = fields.Many2one(
        'l10n_br_account_product.ipi_guideline', string=u'Enquadramento IPI')
    tax_icms_relief_id = fields.Many2one(
        'l10n_br_account_product.icms_relief', string=u'Desoneração ICMS')


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    cfop_id = fields.Many2one('l10n_br_account_product.cfop', 'CFOP')
    ind_final = fields.Selection([
        ('0', u'Não'),
        ('1', u'Sim')
    ], u'Operação com Consumidor final', readonly=True,
        states={'draft': [('readonly', False)]}, required=False,
        help=u'Indica operação com Consumidor final.', default='0')
    icms_st_extract = fields.Boolean(
        string=u'Remover Substituição Tributária dos totais',
        states={'draft': [('readonly', False)]},
        default=False
    )
    tax_estimate = fields.Boolean(
        string=u'Calcular total dos tributos',
        states={'draft': [('readonly', False)]},
        default=True
    )

    @api.v7
    def map_tax(self, cr, uid, fposition_id, taxes, context=None):
        result = []
        if not context:
            context = {}
        if fposition_id and fposition_id.company_id and \
                context.get('type_tax_use') in ('sale', 'all'):
            if context.get('fiscal_type', 'product') == 'product':
                company_tax_ids = self.pool.get('res.company').read(
                    cr, uid, fposition_id.company_id.id, ['product_tax_ids'],
                    context=context)['product_tax_ids']

            company_taxes = self.pool.get('account.tax').browse(
                cr, uid, company_tax_ids, context=context)
            if taxes:
                all_taxes = taxes + company_taxes
            else:
                all_taxes = company_taxes
            taxes = all_taxes

        if not taxes:
            return []
        if not fposition_id:
            return map(lambda x: x.id, taxes)
        for t in taxes:
            ok = False
            tax_src = False
            for tax in fposition_id.tax_ids:
                tax_src = tax.tax_src_id and tax.tax_src_id.id == t.id
                tax_code_src = tax.tax_code_src_id and \
                    tax.tax_code_src_id.id == t.tax_code_id.id

                if tax_src or tax_code_src:
                    if tax.tax_dest_id:
                        result.append(tax.tax_dest_id.id)
                    ok = True
            if not ok:
                result.append(t.id)

        return list(set(result))

    def _map_tax_code(self, map_tax):
        result = {}
        for map in map_tax:
            result[map.tax_dest_id.domain] = {
                'tax': map.tax_dest_id,
                'tax_code': map.tax_code_dest_id,
                'icms_relief': map.tax_icms_relief_id,
                'ipi_guideline':  map.tax_ipi_guideline_id,
            }
        return result

    def _map_analysis(self, result, product, taxes):
        temp = result
        tax_match = self.env['account.fiscal.position.tax'].browse()
        for domain, value in temp.iteritems():
            tax_in_domain = self.tax_ids.filtered(
                lambda r: r.tax_src_domain == domain and r.tax_dest_id)

            tax_ncm_origin = tax_in_domain.filtered(lambda ncm_origin: (
                ncm_origin.fiscal_classification_id and
                ncm_origin.fiscal_classification_id.id ==
                product.fiscal_classification_id.id and
                ncm_origin.origin and ncm_origin.origin ==
                product.origin))
            if tax_ncm_origin:
                tax_match |= tax_ncm_origin
            else:
                tax_ncm = tax_in_domain.filtered(lambda ncm_origin: (
                    ncm_origin.fiscal_classification_id and
                    ncm_origin.fiscal_classification_id.id ==
                    product.fiscal_classification_id.id))
                if tax_ncm:
                    tax_match |= tax_ncm
                else:
                    tax_origin = tax_in_domain.filtered(lambda ncm_origin: (
                        ncm_origin.origin and ncm_origin.origin ==
                        product.origin))
                    if tax_origin:
                        tax_match |= tax_origin
                    else:
                        tax_only = tax_in_domain.filtered(lambda ncm_origin: (
                            not ncm_origin.fiscal_classification_id and
                            not ncm_origin.origin))
                        tax_match |= tax_only

        tax_to_remove = self.tax_ids - tax_match

        for remove in tax_to_remove:
            if result.has_key(remove.tax_src_domain):
                result.pop(remove.tax_src_domain)
        result.update(self._map_tax_code(tax_match))
        return result

    @api.multi
    def _map_tax(self, product_id, taxes):
        result = {}
        if not product_id:
            return result
        product = self.env['product.product'].browse(product_id)

        product_fc = product.fiscal_classification_id
        if self.company_id and \
                self.env.context.get('type_tax_use') in ('sale', 'all'):
            if self.env.context.get('fiscal_type', 'product') == 'product':
                company_taxes = self.company_id.product_tax_definition_line
                for tax_def in company_taxes:
                    if tax_def.tax_id:
                        taxes |= tax_def.tax_id
                        result[tax_def.tax_id.domain] = {
                            'tax': tax_def.tax_id,
                            'tax_code': tax_def.tax_code_id,
                            'icms_relief': tax_def.tax_icms_relief_id,
                            'ipi_guideline':  tax_def.tax_ipi_guideline_id,
                        }

            # FIXME se tiver com o admin pegar impostos de outras empresas
            product_ncm_tax_def = product_fc.sale_tax_definition_line

        else:
            # FIXME se tiver com o admin pegar impostos de outras empresas
            product_ncm_tax_def = product_fc.purchase_tax_definition_line

        for ncm_tax_def in product_ncm_tax_def:
            # Sobrescreve as taxas da empresa com as da ncm
            if ncm_tax_def.tax_id:
                result[ncm_tax_def.tax_id.domain] = {
                    'tax': ncm_tax_def.tax_id,
                    'tax_code': ncm_tax_def.tax_code_id,
                    'icms_relief': ncm_tax_def.tax_icms_relief_id,
                    'ipi_guideline':  ncm_tax_def.tax_ipi_guideline_id,
                }
        result = self._map_analysis(result, product, taxes)
        return result

    @api.v8
    def map_tax_code(self, product_id, taxes=None):
        result = {}
        taxes_codes = self._map_tax(product_id, taxes)
        for code in taxes_codes:
            if taxes_codes[code].get('tax_code'):
                result.update({code: taxes_codes[code].get('tax_code').id})
            if taxes_codes[code].get('ipi_guideline'):
                result.update({
                    'ipi_guideline': taxes_codes[code].get('ipi_guideline').id
                })
            if taxes_codes[code].get('icms_relief'):
                result.update({
                    'icms_relief': taxes_codes[code].get('icms_relief').id
                })
        return result

    @api.v8
    def map_tax(self, taxes):
        result = self.env['account.tax'].browse()
        taxes_codes = self._map_tax(self.env.context.get('product_id'), taxes)
        for tax in taxes_codes:
            if taxes_codes[tax].get('tax'):
                result |= taxes_codes[tax].get('tax')
        return result


class AccountFiscalPositionTax(models.Model):
    _inherit = 'account.fiscal.position.tax'

    fiscal_classification_id = fields.Many2one(
        'account.product.fiscal.classification', 'NCM')
    origin = fields.Selection(PRODUCT_ORIGIN, 'Origem',)
    tax_ipi_guideline_id = fields.Many2one(
        'l10n_br_account_product.ipi_guideline', string=u'Enquadramento IPI')
    tax_icms_relief_id = fields.Many2one(
        'l10n_br_account_product.icms_relief', string=u'Desoneração ICMS')


class ResPartner(models.Model):
    _inherit = "res.partner"

    has_gnre = fields.Boolean(
        string=u"Recolhe imposto antecipadamente atraves de GNRE")
    gnre_due_days = fields.Integer(
        string=u"Vencimento (em dias)")
    gnre_response= fields.Selection(
        selection=GNRE_RESPONSE,
        default=GNRE_RESPONSE_DEFAULT,
        string=u'Responsabilidade'
    )