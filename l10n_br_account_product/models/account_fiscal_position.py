# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from .product_template import PRODUCT_ORIGIN


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    cfop_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cfop',
        domain="[('internal_type', '=', 'normal')]",
        string=u'CFOP')

    ind_final = fields.Selection(
        selection=[('0', u'Não'),
                   ('1', u'Sim')],
        string=u'Operação com Consumidor final',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=False,
        default='0',
        help=u'Indica operação com Consumidor final.')

    def _fill_fiscal_data(self, defitions):
        result = {}
        for d in defitions:
            result[d.tax_id.domain] = {
                'tax': d.tax_id,
                'cst': d.cst_id,
                'icms_relief': d.tax_icms_relief_id,
                'ipi_guideline':  d.tax_ipi_guideline_id,
            }
        return result

    def _fill_fiscal_map(self, map_tax):
        result = {}
        for m in map_tax:
            domain = m.tax_dest_id.domain or m.tax_group_id.domain
            result[domain] = {
                'tax': m.tax_dest_id,
                'cst': m.cst_id,
                'icms_relief': m.tax_icms_relief_id,
                'ipi_guideline':  m.tax_ipi_guideline_id,
            }
        return result

    def _map_tax(self, taxes, product=None, partner=None):
        result = {}
        company_tax_def = state_tax_def = ncm_tax_def = []
        context = self.env.context
        product_fc = product and product.fiscal_classification_id or False

        if self.company_id and \
                context.get('type_tax_use') in ('sale', 'all'):
            if context.get('fiscal_type', 'product') == 'product':
                # Get taxes from company
                company_tax_def = self.company_id.product_tax_definition_line
                for tax_def in company_tax_def:
                    if tax_def.tax_id:
                        taxes |= tax_def.tax_id

                # Get taxes from state
                state_tax_def = partner.state_id.product_tax_definition_line
                for tax_def in state_tax_def:
                    if tax_def.tax_id:
                        fc = tax_def.fiscal_classification_id
                        if (not fc and not tax_def.cest_id) or \
                                (fc == product_fc or
                                 tax_def.cest_id == product.cest_id):
                            taxes |= tax_def.tax_id

            # FIXME se tiver com o admin pegar impostos de outras empresas
            if product_fc:
                ncm_tax_def = product_fc.sale_tax_definition_line

        else:
            # FIXME se tiver com o admin pegar impostos de outras empresas
            if product_fc:
                ncm_tax_def = product_fc.purchase_tax_definition_line

        result.update(self._fill_fiscal_data(company_tax_def))
        result.update(self._fill_fiscal_data(state_tax_def))
        result.update(self._fill_fiscal_data(ncm_tax_def))

        map_taxes = self.env['account.fiscal.position.tax'].browse()
        map_taxes_ncm = self.env['account.fiscal.position.tax'].browse()
        map_taxes_cest = self.env['account.fiscal.position.tax'].browse()
        map_taxes_origin = self.env['account.fiscal.position.tax'].browse()
        map_taxes_origin_ncm = self.env['account.fiscal.position.tax'].browse()

        for tax in taxes:
            for mapping in self.tax_ids:
                if (mapping.tax_src_id.id == tax.id or
                        mapping.tax_dest_id == tax or
                        mapping.tax_group_id.id == tax.tax_group_id.id):
                    if mapping.tax_dest_id.id or tax.tax_code_id.id:
                        if mapping.fiscal_classification_id.id == \
                                product.fiscal_classification_id.id:
                            map_taxes_ncm |= mapping
                        if product.cest_id:
                            if mapping.cest_id == product.cest_id:
                                map_taxes_cest |= mapping
                        if mapping.origin == product.origin:
                            map_taxes_origin |= mapping
                        if (mapping.fiscal_classification_id.id ==
                                product.fiscal_classification_id.id and
                                mapping.origin == product.origin):
                            map_taxes_origin_ncm |= mapping
                        if (not mapping.origin and
                                not mapping.fiscal_classification_id and
                                not mapping.cest_id):
                            map_taxes |= mapping
            else:
                if result.get(tax.domain):
                    result[tax.domain].update({'tax': tax})
                else:
                    result[tax.domain] = {'tax': tax}

        result.update(self._fill_fiscal_map(map_taxes))
        result.update(self._fill_fiscal_map(map_taxes_origin))
        result.update(self._fill_fiscal_map(map_taxes_ncm))
        result.update(self._fill_fiscal_map(map_taxes_origin_ncm))
        result.update(self._fill_fiscal_map(map_taxes_cest))

        return result

    @api.model
    def map_tax(self, taxes, product=None, partner=None):
        result = self.env['account.tax'].browse()
        mapping = self._map_tax(taxes, product, partner)
        for tax in mapping:
            if mapping[tax].get('tax'):
                result |= mapping[tax].get('tax')
        return result

    @api.model
    def map_tax_code(self, taxes, product=None, partner=None):
        return self._map_tax(taxes, product, partner)


class AccountFiscalPositionTax(models.Model):
    _inherit = 'account.fiscal.position.tax'

    fiscal_classification_id = fields.Many2one(
        comodel_name='account.product.fiscal.classification',
        string='NCM')

    origin = fields.Selection(
        selection=PRODUCT_ORIGIN,
        string=u'Origem')

    cest_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cest',
        string=u'CEST')

    tax_ipi_guideline_id = fields.Many2one(
        comodel_name='l10n_br_account_product.ipi_guideline',
        string=u'Enquadramento IPI')

    tax_icms_relief_id = fields.Many2one(
        comodel_name='l10n_br_account_product.icms_relief',
        string=u'Desoneração ICMS')

    cst_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        string=u'CST',
        required=False)

    @api.onchange('tax_dest_id',
                  'tax_group_id',
                  'position_id')
    def _onchange_tax_group(self):
        onchange = super(
            AccountFiscalPositionTax,
            self)._onchange_tax_group()

        if onchange:
            onchange['domain'].update(
                {'cst_id': onchange['domain']['tax_dest_id']})
        return onchange.update(
            {'readonly': {
                'tax_icms_relief_id': [('tax_dest_id.domain', '=', 'icms')]}})
