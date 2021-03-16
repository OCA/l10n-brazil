# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree

from odoo import api, fields, models
# from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_ISSUER_PARTNER


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = [_name, 'l10n_br_fiscal.document.mixin']

    @api.model
    def _default_fiscal_operation(self):
        return self.env.user.company_id.purchase_fiscal_operation_id

    @api.model
    def _fiscal_operation_domain(self):
        domain = [
            ('state', '=', 'approved'),
            ('fiscal_type', 'in', ('purchase', 'other', 'purchase_refund'))]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        related='partner_id.cnpj_cpf',
    )

    legal_name = fields.Char(
        string='Legal Name',
        related='partner_id.legal_name',
    )

    ie = fields.Char(
        string='State Tax Number/RG',
        related='partner_id.inscr_est',
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type="form",
                        toolbar=False, submenu=False):

        order_view = super().fields_view_get(
            view_id, view_type, toolbar, submenu
        )

        if view_type == 'form':
            sub_form_view = order_view.get(
                'fields', {}).get('order_line', {}).get(
                'views', {}).get('form', {}).get('arch', {})

            view = self.env['ir.ui.view']

            sub_form_node = etree.fromstring(
                self.env['purchase.order.line'].fiscal_form_view(
                    sub_form_view))

            sub_arch, sub_fields = view.postprocess_and_fields(
                'purchase.order.line', sub_form_node, None)

            order_view['fields']['order_line']['views']['form'][
                'fields'] = sub_fields

            order_view['fields']['order_line']['views']['form'][
                'arch'] = sub_arch

        return order_view

    # TODO open by default Invoice view with Fiscal Details Button
    # You can add a group to select default view Fiscal Invoice or
    # Account invoice.
    # @api.multi
    # def action_view_invoice(self):
    #     result = super().action_view_invoice()
    #     fiscal_dict = self._prepare_br_fiscal_dict(default=True)
    #
    #     document_type_id = self._context.get('document_type_id')
    #
    #     if document_type_id:
    #         document_type = self.env['l10n_br_fiscal.document.type'].browse(
    #             document_type_id)
    #     else:
    #         document_type = self.company_id.document_type_id
    #         document_type_id = self.company_id.document_type_id.id
    #
    #     fiscal_dict['default_document_type_id'] = document_type_id
    #     document_serie = document_type.get_document_serie(
    #         self.company_id, self.fiscal_operation_id)
    #
    #     if document_serie:
    #         fiscal_dict['default_document_serie_id'] = document_serie.id
    #
    #     fiscal_dict['default_issuer'] = DOCUMENT_ISSUER_PARTNER
    #
    #     if self.fiscal_operation_id and self.fiscal_operation_id.journal_id:
    #         fiscal_dict['default_journal_id'] = (
    #             self.fiscal_operation_id.journal_id.id)
    #
    #     result['context'].update(fiscal_dict)
    #     return result

    @api.onchange('fiscal_operation_id')
    def _onchange_fiscal_operation_id(self):
        self.fiscal_position_id = self.fiscal_operation_id.fiscal_position_id

    @api.multi
    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        return self.mapped('order_line')

    @api.depends('order_line')
    def _compute_amount(self):
        super()._compute_amount()

    @api.depends('order_line.price_total')
    def _amount_all(self):
        self._compute_amount()
