# -*- coding: utf-8 -*-
# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ContractContract(models.Model):

    _inherit = 'contract.contract'

    @api.multi
    def _prepare_invoice(self, date_invoice, journal=None):
        invoice_vals = super()._prepare_invoice(date_invoice, journal)
        invoice_vals['fiscal_document_id'] = False
        invoice_vals['company_id'] = self.company_id.id
        invoice_vals['operation_type'] = 'out'
        invoice_vals['document_type_id'] = self.company_id.document_type_id.id
        invoice_vals['fiscal_operation_id'] = \
            self.env.ref('l10n_br_fiscal.fo_venda').id
        invoice_vals['document_serie_id'] = \
            self.env['l10n_br_fiscal.document.serie'].search([
                ('document_type_id', '=', invoice_vals['document_type_id']),
                ('company_id', '=', self.company_id.id),
            ], limit=1).id
        return invoice_vals

    @api.model
    def _finalize_invoice_creation(self, invoices):
        super()._finalize_invoice_creation(invoices)
        for invoice in invoices:
            invoice.fiscal_document_id._onchange_document_serie_id()
            invoice.fiscal_document_id._onchange_company_id()
            invoice.fiscal_document_id._onchange_partner_id()
            invoice.fiscal_document_id._onchange_fiscal_operation_id()
            if hasattr(invoice.fiscal_document_id, 'rps_number'):
                invoice.fiscal_document_id.rps_number = \
                    invoice.fiscal_document_id.number
                invoice.fiscal_document_id.number = 'SN'
            for line in invoice.fiscal_document_id.line_ids:
                line._onchange_product_id_fiscal()
                line._onchange_commercial_quantity()
                line._onchange_ncm_id()
                line._onchange_fiscal_operation_id()
                line._onchange_fiscal_operation_line_id()
                line._onchange_fiscal_taxes()
