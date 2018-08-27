# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields

from .account_fiscal_position_abstract import (
    AccountFiscalPositionAbstract,
    AccountFiscalPositionTaxAbstract
)


class AccountFiscalPosition(AccountFiscalPositionAbstract,
                            models.Model):

    _inherit = 'account.fiscal.position'
# TODO l10n_br_account_product's PR
#    @api.model
#    def map_tax(self, taxes, product=None, partner=None):
#        result = self.env['account.tax'].browse()
#
#        if self.company_id and \
#                self.env.context.get('type_tax_use') in ('sale', 'all'):
#            if self.env.context.get('fiscal_type', 'product') == 'service':
#                company_taxes = self.company_id.service_tax_ids
#
#            if taxes:
#                taxes |= company_taxes
#
#        for tax in taxes:
#            tax_count = 0
#            for t in self.tax_ids:
#                if (t.tax_src_id == tax or
#                        t.tax_group_id == tax.tax_group_id):
#                    tax_count += 1
#                    if t.tax_dest_id:
#                        result |= t.tax_dest_id
#            if not tax_count:
#                result |= tax
#        return result


class AccountFiscalPositionTax(AccountFiscalPositionTaxAbstract,
                               models.Model):

    _inherit = 'account.fiscal.position.tax'

    tax_src_id = fields.Many2one(
        comodel_name='account.tax',
        string='Tax on Product',
        required=False
    )
