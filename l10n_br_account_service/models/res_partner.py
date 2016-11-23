# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    @api.v7
    def map_tax(self, cr, uid, fposition_id, taxes, context=None):
        result = []
        if not context:
            context = {}
        if fposition_id and fposition_id.company_id and \
                context.get('type_tax_use') in ('sale', 'all'):
            if context.get('fiscal_type', 'service') == 'service':
                company_tax_ids = self.pool.get('res.company').read(
                    cr, uid, fposition_id.company_id.id, ['service_tax_ids'],
                    context=context)['service_tax_ids']

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

    @api.multi
    def _map_tax(self, product_id, taxes):
        result = {}
        if self.company_id and\
                self.env.context.get('type_tax_use') in ('sale', 'all'):
            if self.env.context.get('fiscal_type', 'service') == 'service':
                company_taxes = self.company_id.service_tax_definition_line
                for tax_def in company_taxes:
                    if tax_def.tax_id:
                        taxes |= tax_def.tax_id
                        result[tax_def.tax_id.domain] = {
                            'tax': tax_def.tax_id,
                            'tax_code': tax_def.tax_code_id,
                        }

        map_taxes = self.env['account.fiscal.position.tax'].browse()
        for tax in taxes:
            for map in self.tax_ids:
                if map.tax_src_id == tax or \
                        map.tax_code_src_id == tax.tax_code_id:
                    if map.tax_dest_id or tax.tax_code_id:
                        map_taxes |= map
                else:
                    if result.get(tax.domain):
                        result[tax.domain].update({'tax': tax})
                    else:
                        result[tax.domain] = {'tax': tax}

        return result

    @api.v8
    def map_tax(self, taxes):
        result = self.env['account.tax'].browse()
        taxes_codes = self._map_tax(self.env.context.get('product_id'), taxes)
        for tax in taxes_codes:
            if taxes_codes[tax].get('tax'):
                result |= taxes_codes[tax].get('tax')
        return result
