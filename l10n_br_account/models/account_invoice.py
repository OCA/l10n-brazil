# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# Copyright 2020 KMEE - Luis Felipe Miléo
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

INVOICE_TO_OPERATION = {
    'out_invoice': 'out',
    'in_invoice': 'in',
    'out_refund': 'in',
    'in_refund': 'out',
}

REFUND_TO_OPERATION = {
    'out_invoice': 'in',
    'in_invoice': 'out',
    'out_refund': 'out',
    'in_refund': 'in',
}

FISCAL_TYPE_REFUND = {
    'out': ['purchase_return', 'in_return'],
    'in': ['sale_return', 'out_return'],
}

SHADOWED_FIELDS = [
    'partner_id', 'company_id', 'date', 'currency_id',
    'payment_term_id', 'financial_ids', 'fiscal_payment_ids',
    'journal_id', 'account_id', 'move_id',
]


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'l10n_br_fiscal.payment.mixin']
    _inherits = {'l10n_br_fiscal.document': 'fiscal_document_id'}
    _order = 'date_invoice DESC, number DESC'
    _payment_inverse_name = 'invoice_id'

    @api.depends("amount_total", "fiscal_payment_ids")
    def _compute_payment_change_value(self):
        self._abstract_compute_payment_change_value()

    # initial account.invoice inherits on fiscal.document that are
    # disable with active=False in their fiscal_document table.
    # To make these invoices still visible, we set active=True
    # in the invoice table.
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        related='partner_id.cnpj_cpf',
    )

    legal_name = fields.Char(
        string='Adapted Legal Name',
        related='partner_id.legal_name',
    )

    ie = fields.Char(
        string='Adapted State Tax Number',
        related='partner_id.inscr_est',
    )

    # this default should be overwritten to False in a module pretending to
    # create fiscal documents from the invoices. But this default here
    # allows to install the l10n_br_account module without creating issues
    # with the existing Odoo invoice (demo or not).
    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        string='Fiscal Document',
        required=True,
        ondelete='cascade',
        default=lambda self: self.env.ref(
            'l10n_br_fiscal.fiscal_document_dummy'),
    )

    @api.model
    def _shadowed_fields(self):
        """Returns the list of shadowed fields that are synced
        from the parent."""
        return SHADOWED_FIELDS

    financial_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.payment.line',
        inverse_name=_payment_inverse_name,
        string='Duplicatas',
        copy=True,
    )

    fiscal_payment_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.payment',
        inverse_name=_payment_inverse_name,
        string='Pagamentos',
        copy=True,
    )

    @api.multi
    def _prepare_shadowed_fields_dict(self, default=False):
        self.ensure_one()
        vals = self._convert_to_write(self.read(self._shadowed_fields())[0])
        if default:  # in case you want to use new rather than write later
            return {'default_%s' % (k,): vals[k] for k in vals.keys()}
        return vals

    @api.model
    def create(self, values):
        dummy_doc = self.env.ref('l10n_br_fiscal.fiscal_document_dummy')
        invoice = super().create(values)
        if invoice.fiscal_document_id != dummy_doc:
            shadowed_fiscal_vals = invoice._prepare_shadowed_fields_dict()
            shadowed_fiscal_vals['invoice_id'] = invoice.id
            invoice.fiscal_document_id.write(shadowed_fiscal_vals)
        return invoice

    @api.multi
    def write(self, values):
        dummy_doc = self.env.ref('l10n_br_fiscal.fiscal_document_dummy')
        result = super().write(values)
        for invoice in self:
            if invoice.fiscal_document_id != dummy_doc:
                shadowed_fiscal_vals = invoice._prepare_shadowed_fields_dict()
                invoice.fiscal_document_id.write(shadowed_fiscal_vals)
        return result

    def action_invoice_open(self):
        for record in self:
            record.fiscal_document_id.action_document_confirm()
            record.fiscal_document_id.action_document_send()
            if record.fiscal_document_id.move_id:
                record.move_id = record.fiscal_document_id.move_id
        return super().action_invoice_open()

    def invoice_validate(self):
        """ Só podemos validar uma invoice que tem account.move
        :return:
        """
        to_open_invoices = self.filtered(
            lambda inv:
                inv.state != 'open' and
                inv.move_id
        )
        return super(AccountInvoice, to_open_invoices).invoice_validate()

    def _move_create_with_templates(self):
        if not self.move_id:
            # TODO: Gerar com os dados da invoice
            # TODO: Verificar se os dados são suficientes
            self.fiscal_document_id.action_move_create()

    def action_move_create(self):
        for record in self:
            if record.journal_id.generate_move_with_templates:
                ctx = record.env.context
                if not record.journal_id.auto_generate_moves:
                    return
                record._move_create_with_templates()
            else:
                #
                # This context must be keep it unit account.payment.term.compute() call
                #
                ctx = record.env.context.copy()
                ctx['fiscal_payment_ids'] = record.fiscal_payment_ids
                ctx['financial_ids'] = record.financial_ids
            return super(
                AccountInvoice, record.with_context(ctx)
            ).action_move_create()

    @api.multi
    def _get_computed_reference(self):
        res = super()._get_computed_reference()
        if self.company_id.invoice_reference_type == 'fiscal_document':
            return self.fiscal_document_id.number  # FIXME: Name!
        return res

    def _onchange_payment_term_date_invoice(self):
        ctx = self.env.context.copy()
        ctx['fiscal_payment_ids'] = self.fiscal_payment_ids
        ctx['financial_ids'] = self.financial_ids
        return super(
            AccountInvoice, self.with_context(ctx)
        )._onchange_payment_term_date_invoice()
