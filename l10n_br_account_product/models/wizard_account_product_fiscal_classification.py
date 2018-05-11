# -*- coding: utf-8 -*-
# Copyright (C) 2012  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api


class WizardAccountProductFiscalClassification(models.TransientModel):
    _inherit = 'wizard.account.product.fiscal.classification'

    @api.multi
    def action_create(self):
        obj_tax = self.env['account.tax']
        obj_tax_code = self.env['account.tax.code']
        obj_tax_code_template = self.env['account.tax.code.template']
        obj_tax_template = self.env['account.tax.template']
        obj_fc = self.env['account.product.fiscal.classification']
        obj_tax_purchase = self.env['l10n_br_tax.definition.purchase']
        obj_tax_sale = self.env['l10n_br_tax.definition.sale']

        obj_fc_template = self.env[
            'account.product.fiscal.classification.template']

        def map_taxes_codes(tax_definition, tax_type='sale'):
            for line in tax_definition:

                for company in companies:

                    if company_taxes[company].get(line.tax_template_id.id):

                        tax_def_domain = [
                            ('tax_id', '=', company_taxes[
                                company].get(line.tax_template_id.id)),
                            ('fiscal_classification_id', '=', fc_id.id),
                            ('company_id', '=', company)]

                        if tax_type == 'sale':
                            obj_tax_def = obj_tax_sale
                        else:
                            obj_tax_def = obj_tax_purchase

                        tax_def_result = obj_tax_def.search(tax_def_domain)

                        values = {
                            'tax_id': company_taxes[company].get(
                                line.tax_template_id.id),
                            'tax_code_id': company_codes[company].get(
                                line.tax_code_template_id.id),
                            'company_id': company,
                            'fiscal_classification_id': fc_id.id,
                        }

                        if tax_def_result:
                            tax_def_result.write(values)
                        else:
                            obj_tax_def.create(values)
            return True

        company_id = self.company_id.id
        companies = []

        if company_id:
            companies.append(company_id)
        else:
            companies = self.env['res.company'].sudo().search([]).ids

        company_taxes = {}
        company_codes = {}
        for company in companies:
            company_taxes[company] = {}
            company_codes[company] = {}
            for tax in obj_tax.sudo().search([('company_id', '=', company)]):
                tax_template = obj_tax_template.search(
                    [('name', '=', tax.name)])

                if tax_template:
                    company_taxes[company][tax_template[0].id] = tax.id

            for code in obj_tax_code.sudo().search(
                    [('company_id', '=', company)]):

                code_template = obj_tax_code_template.search(
                    [('name', '=', code.name)])

                if code_template:
                    company_codes[company][code_template[0].id] = code.id

        for fc_template in obj_fc_template.search([]):

            fc_id = obj_fc.search([('name', '=', fc_template.name)])

            if not fc_id:

                vals = {
                    'active': fc_template.active,
                    'code': fc_template.code,
                    'name': fc_template.name,
                    'description': fc_template.description,
                    'company_id': company_id,
                    'type': fc_template.type,
                    'note': fc_template.note,
                    'inv_copy_note': fc_template.inv_copy_note,
                }
                fc_id = obj_fc.sudo().create(vals)

            map_taxes_codes(fc_template.sale_tax_definition_line,
                            'sale')

            map_taxes_codes(fc_template.purchase_tax_definition_line,
                            'purchase')

        return True
