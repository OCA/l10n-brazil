# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from ..constants.fiscal import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_SERVICE,
    NCM_FOR_SERVICE_REF)


class DocumentLineAbstract(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.line.abstract'
    _description = 'Fiscal Document Line Abstract'

    @api.one
    @api.depends(
        'price', 'discount', 'quantity',
        'product_id', 'document_id.partner_id', 'document_id.company_id')
    def _compute_amount(self):
        round_curr = self.document_id.currency_id.round
        self.amount_untaxed = round_curr(self.price * self.quantity)
        self.amount_tax = 0.00
        self.amount_total = self.amount_untaxed + self.amount_tax

    def _get_default_ncm_id(self):
        fiscal_type = self.env.context.get('default_fiscal_type')
        if fiscal_type == PRODUCT_FISCAL_TYPE_SERVICE:
            ncm_id = self.env.ref(NCM_FOR_SERVICE_REF)
            return ncm_id

    document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.abstract',
        string='Document')

    operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation.line',
        string='Operation')

    company_id = fields.Many2one(
        comodel_name='res.company',
        related='document_id.company_id',
        string='Company')

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string='Currency')

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')

    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='UOM')

    quantity = fields.Float(
        string='Quantity')

    price = fields.Monetary(
        string='Price Unit')

    fiscal_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Fiscal UOM')

    fiscal_quantity = fields.Float(
        string='Fiscal Quantity')

    fiscal_price = fields.Monetary(
        string='Fiscal Price')

    discount = fields.Monetary(
        string='Discount')

    fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE,
        string='Fiscal Type')

    fiscal_genre_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.product.genre',
        string='Fiscal Genre')

    ncm_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.ncm',
        index=True,
        default=_get_default_ncm_id,
        string='NCM')

    cest_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cest',
        index=True,
        string='CEST',
        domain="[('ncm_ids', '=', ncm_id)]")

    nbs_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.nbs',
        index=True,
        string='NBS')

    service_type_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.service.type',
        string='Service Type',
        domain="[('internal_type', '=', 'normal')]")

    amount_untaxed = fields.Monetary(
        string="Amount Untaxed",
        compute='_compute_amount')

    amount_tax = fields.Monetary(
        string="Amount Tax",
        compute='_compute_amount')

    amount_total = fields.Monetary(
        string="Amount Total",
        compute='_compute_amount')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            # Fiscal UOM self.fiscal_uom_id = self.ncm_id.uom_id
            self.ncm_id = self.product_id.ncm_id
            self.cest_id = self.product_id.cest_id
            self.nbs_id = self.product_id.nbs_id

    @api.onchange('uom_id', 'price', 'quantity')
    def _onchange_commercial_quantity(self):
        if self.uom_id:
            self.fiscal_uom_id = self.uom_id

        if self.price:
            self.fiscal_price = self.price

        if self.quantity:
            self.fiscal_quantity = self.quantity
