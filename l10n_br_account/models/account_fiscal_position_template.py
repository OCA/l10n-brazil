# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from .account_fiscal_position_abstract import AccountFiscalPositionTaxAbstract


class AccountFiscalPositionTaxTemplate(AccountFiscalPositionTaxAbstract, models.Model):

    _inherit = "account.fiscal.position.tax.template"

    tax_src_id = fields.Many2one(
        comodel_name="account.tax.template", string=u"Tax on Product", required=False
    )
