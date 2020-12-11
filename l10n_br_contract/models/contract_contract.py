# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ContractContract(models.Model):

    _name = 'contract.contract'
    _inherit = [_name, 'l10n_br_fiscal.document.mixin']

    document_count = fields.Integer(compute="_compute_document_count")

    fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Fiscal Operation',
        default=lambda self: self.env.user.company_id,
        required=False)

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
        invoice_vals = self._prepare_br_fiscal_dict()
        invoice_vals.update(super()._prepare_invoice(date_invoice, journal))
        # invoice_vals['fiscal_document_id'] = False
        # invoice_vals['company_id'] = self.company_id.id
        # invoice_vals['fiscal_operation_type'] = 'out'
        # invoice_vals['document_type_id'] = self.company_id.document_type_id.id
        # if invoice_vals['document_type_id'] == \
        #     self.env['l10n_br_fiscal.document.type'].search([
        #         ('code', '=', 'SE')], limit=1).id:
        #     invoice_vals['document_section'] = 'nfse_recibos'
        # invoice_vals['fiscal_operation_id'] = \
        #     self.env.ref('l10n_br_fiscal.fo_venda').id
        # invoice_vals['document_serie_id'] = \
        #     self.env['l10n_br_fiscal.document.serie'].search([
        #         ('document_type_id', '=', invoice_vals['document_type_id']),
        #         ('company_id', '=', self.company_id.id),
        #     ], limit=1).id
        return invoice_vals

    @api.model
    def _finalize_invoice_creation(self, invoices):
        super()._finalize_invoice_creation(invoices)

        # TODO: Verificar se é necessário
        # for invoice in invoices:
        #     invoice.fiscal_document_id._onchange_document_serie_id()
        #     invoice.fiscal_document_id._onchange_company_id()
        #     invoice.fiscal_document_id._onchange_fiscal_operation_id()

            # TODO: Verificar se o número da nfse está correto
            # if hasattr(invoice.fiscal_document_id, 'rps_number') and \
            #         invoice.fiscal_document_id.number:
            #     invoice.fiscal_document_id.rps_number = \
            #         invoice.fiscal_document_id.number
            #     invoice.fiscal_document_id.number = False

            # TODO: Verificar se todos os campos fiscais estão sendo
            #  corretamente calculados
            # for line in invoice.fiscal_document_id.line_ids:
            #     line._onchange_product_id_fiscal()
            #     line._onchange_fiscal_operation_id()
            #     line._onchange_ncm_id()
            #     line.price_unit = line.contract_line_id.price_unit
            #     line._onchange_commercial_quantity()
            #     line._onchange_fiscal_operation_line_id()
            #     line._onchange_fiscal_taxes()
