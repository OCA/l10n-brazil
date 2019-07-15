# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class DocumentAbstract(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.abstract'
    _description = 'Fiscal Document Abstract'

    @api.one
    @api.depends('line_ids')
    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal
                                  for line in self.line_ids)
        self.amount_tax = sum(line.price_subtotal for line in self.line_ids)
        self.amount_total = sum(line.price_subtotal for line in self.line_ids)

    number = fields.Char(
        string='Number',
        required=True,
        index=True)

    key = fields.Char(
        string='key',
        required=True,
        index=True)

    document_type_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.type',
        required=True)

    document_serie_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.serie',
        domain="[('active', '=', True),"
               "('document_type_id', '=', document_type_id)]",
        required=True)

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner')

    operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Partner')

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'l10n_br_fiscal.tax.estimate'))

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        store=True,
        readonly=True)

    amount_total = fields.Monetary(
        string="Amount Total",
        compute='_compute_amount')

    amount_untaxed = fields.Monetary(
        string="Amount Untaxed",
        compute='_compute_amount')

    amount_tax = fields.Monetary(
        string="Amount Tax",
        compute='_compute_amount')
