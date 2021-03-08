# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants.fiscal import (TAX_FRAMEWORK)


class DocumentLine(models.Model):
    _name = 'l10n_br_fiscal.document.line'
    _inherit = 'l10n_br_fiscal.document.line.mixin'
    _description = 'Fiscal Document Line'

    @api.model
    def _operation_domain(self):
        domain = [('state', '=', 'approved')]
        return domain

    fiscal_operation_id = fields.Many2one(
        domain=lambda self: self._operation_domain(),
    )

    document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        string='Document',
        ondelete='cascade',
    )

    # used mostly to enable _inherits of account.invoice on fiscal_document
    # when existing invoices have no fiscal document.
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    name = fields.Text(
        string='Name',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        related='document_id.company_id',
        store=True,
        string='Company',
    )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related='company_id.tax_framework',
        string='Tax Framework',
    )

    partner_id = fields.Many2one(
        related='document_id.partner_id',
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string='Currency',
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )

    # Amount Fields
    amount_untaxed = fields.Monetary(
        string='Amount Untaxed',
        compute='_compute_amounts',
        default=0.00,
    )

    amount_tax = fields.Monetary(
        string='Amount Tax',
        compute='_compute_amounts',
        default=0.00,
    )

    amount_fiscal = fields.Monetary(
        string='Amount Fiscal',
        compute='_compute_amounts',
        default=0.00,
    )

    amount_financial = fields.Monetary(
        string='Amount Financial',
        compute='_compute_amounts',
        default=0.00,
    )

    amount_total = fields.Monetary(
        string='Amount Total',
        compute='_compute_amounts',
        default=0.00,
    )

    @api.multi
    def unlink(self):
        if self.env.ref('l10n_br_fiscal.fiscal_document_line_dummy') in self:
            raise UserError(
                _("You cannot unlink Fiscal Document Line Dummy !"))
        return super().unlink()
