# -*- coding: utf-8 -*-
# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ContractContract(models.Model):

    _inherit = 'contract.contract'
    document_count = fields.Integer(compute="_compute_document_count")

    @api.multi
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec._get_related_invoices().mapped(
                'fiscal_document_id'))

    @api.multi
    def action_show_documents(self):
        self.ensure_one()
        tree_view_ref = (
            'l10n_br_fiscal.document_tree'
        )
        form_view_ref = (
            'l10n_br_fiscal.document_form'
        )
        tree_view = self.env.ref(tree_view_ref, raise_if_not_found=False)
        form_view = self.env.ref(form_view_ref, raise_if_not_found=False)
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'res_model': 'l10n_br_fiscal.document',
            'view_type': 'form',
            'view_mode': 'tree,kanban,form,calendar,pivot,graph,activity',
            'domain': [('id', 'in', self._get_related_invoices().mapped(
                'fiscal_document_id').ids)],
        }
        if tree_view and form_view:
            action['views'] = [(tree_view.id, 'tree'), (form_view.id, 'form')]
        return action

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
