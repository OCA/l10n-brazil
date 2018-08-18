# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields

from .account_fiscal_position_abstract import (
    AccountFiscalPositionAbstract,
    AccountFiscalPositionTaxAbstract
)


class AccountFiscalPositionTemplate(AccountFiscalPositionAbstract,
                                    models.Model):
    _inherit = 'account.fiscal.position.template'

    cfop_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cfop',
        string='CFOP'
    )

    def generate_fiscal_position(self, chart_temp_id,
                                 tax_template_ref, acc_template_ref,
                                 company_id):
        """
        This method generate Fiscal Position, Fiscal Position Accounts and
        Fiscal Position Taxes from templates.

        :param chart_temp_id: Chart Template Id.
        :param taxes_ids: Taxes templates reference for generating
        account.fiscal.position.tax.
        :param acc_template_ref: Account templates reference for generating
        account.fiscal.position.account.
        :param company_id: selected from wizard.multi.charts.accounts.
        :returns: True
        """
        obj_tax_fp = self.env['account.fiscal.position.tax']
        obj_ac_fp = self.env['account.fiscal.position.account']
        obj_fiscal_position = self.env['account.fiscal.position']
        obj_tax_code = self.env['account.tax.code']
        obj_tax_code_template = self.env['account.tax.code.template']
        tax_code_template_ref = {}
        tax_code_ids = obj_tax_code.search([('company_id', '=', company_id)])

        for tax_code in tax_code_ids:
            tax_code_template = obj_tax_code_template.search(
                [('name', '=', tax_code.name)])
            if tax_code_template:
                tax_code_template_ref[tax_code_template[0].id] = tax_code.id

        fp_ids = self.search([('chart_template_id', '=', chart_temp_id)])
        for position in fp_ids:
            new_fp = obj_fiscal_position.create({
                'company_id': company_id,
                'name': position.name,
                'note': position.note,
                'type': position.type,
                'state': position.state,
                'type_tax_use': position.type_tax_use,
                'cfop_id':
                    position.cfop_id and position.cfop_id.id or False,
                'inv_copy_note': position.inv_copy_note,
                'asset_operation': position.asset_operation,
                'fiscal_category_id': (position.fiscal_category_id and
                                       position.fiscal_category_id.id or
                                       False)})

            for tax in position.tax_ids:
                obj_tax_fp.create({
                    'tax_src_id':
                    tax.tax_src_id and
                    tax_template_ref.get(tax.tax_src_id.id, False),
                    'tax_code_src_id':
                    tax.tax_code_src_id,
                    'type': position.type,
                    'state': position.state,
                    'type_tax_use': position.type_tax_use,
                    'cfop_id': (position.cfop_id and
                                position.cfop_id.id or False),
                    'inv_copy_note': position.inv_copy_note,
                    'asset_operation': position.asset_operation,
                    'fiscal_category_id': (position.fiscal_category_id and
                                           position.fiscal_category_id.id or
                                           False)})

            for tax in position.tax_ids:
                obj_tax_fp.create({
                    'tax_src_id':
                    tax.tax_src_id and
                    tax_template_ref.get(tax.tax_src_id.id, False),
                    'tax_code_src_id':
                    tax.tax_code_src_id and
                    tax_code_template_ref.get(tax.tax_code_src_id.id, False),
                    'tax_src_domain': tax.tax_src_domain,
                    'tax_dest_id': tax.tax_dest_id and
                    tax_template_ref.get(tax.tax_dest_id.id, False),
                    'tax_code_dest_id': tax.tax_code_dest_id and
                    tax_code_template_ref.get(tax.tax_code_dest_id.id, False),
                    'position_id': new_fp})

            for acc in position.account_ids:
                obj_ac_fp.create({
                    'account_src_id': acc_template_ref[acc.account_src_id.id],
                    'account_dest_id':
                    acc_template_ref[acc.account_dest_id.id],
                    'position_id': new_fp})

        return True


class AccountFiscalPositionTaxTemplate(AccountFiscalPositionTaxAbstract,
                                       models.Model):

    _inherit = 'account.fiscal.position.tax.template'

    tax_src_id = fields.Many2one(
        comodel_name='account.tax.template',
        string=u'Tax on Product',
        required=False)
