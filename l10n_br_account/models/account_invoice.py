# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_OUT

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
    'partner_id',
    'company_id',
    'date',
    'currency_id',
    'partner_shipping_id',
]


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = [_name, 'l10n_br_fiscal.document.mixin.methods']
    _inherits = {'l10n_br_fiscal.document': 'fiscal_document_id'}
    _order = 'date_invoice DESC, number DESC'

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

    financial_move_line_ids = fields.Many2many(
        comodel_name='account.move.line',
        string='Financial Move Lines',
        store=True,
        compute='_compute_financial',
    )

    fiscal_number = fields.Char(
        string='Fiscal Number',
        related='fiscal_document_id.number',
        store=True,
    )

    # this default should be overwritten to False in a module pretending to
    # create fiscal documents from the invoices. But this default here
    # allows to install the l10n_br_account module without creating issues
    # with the existing Odoo invoice (demo or not).
    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        string='Fiscal Document',
        required=True,
        copy=False,
        ondelete='cascade',
    )

    @api.multi
    @api.depends('move_id.line_ids')
    def _compute_financial(self):
        for invoice in self:
            lines = invoice.move_id.line_ids.filtered(
                lambda l: l.account_id == invoice.account_id and
                l.account_id.internal_type in ('receivable', 'payable'))
            invoice.financial_move_line_ids = lines.sorted()

    @api.model
    def _shadowed_fields(self):
        """Returns the list of shadowed fields that are synced
        from the parent."""
        return SHADOWED_FIELDS

    @api.multi
    def _prepare_shadowed_fields_dict(self, default=False):
        self.ensure_one()
        vals = self._convert_to_write(self.read(self._shadowed_fields())[0])
        if default:  # in case you want to use new rather than write later
            return {'default_%s' % (k,): vals[k] for k in vals.keys()}
        return vals

    @api.model
    def fields_view_get(self, view_id=None, view_type="form",
                        toolbar=False, submenu=False):

        order_view = super().fields_view_get(
            view_id, view_type, toolbar, submenu
        )

        if view_type == 'form':
            view = self.env['ir.ui.view']

            sub_form_view = self.env['account.invoice.line'].fields_view_get(
                view_id=self.env.ref('l10n_br_account.invoice_line_form').id,
                view_type='form')['arch']

            sub_form_node = etree.fromstring(
                self.env['account.invoice.line'].fiscal_form_view(
                    sub_form_view))

            sub_arch, sub_fields = view.postprocess_and_fields(
                'account.invoice.line', sub_form_node, None)

            order_view['fields']['invoice_line_ids']['views']['form'] = {}

            order_view['fields']['invoice_line_ids']['views']['form'][
                'fields'] = sub_fields
            order_view['fields']['invoice_line_ids']['views']['form'][
                'arch'] = sub_arch

        return order_view

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        invoice_type = self.env.context.get('type', 'out_invoice')
        defaults['fiscal_operation_type'] = INVOICE_TO_OPERATION[invoice_type]
        if defaults['fiscal_operation_type'] == FISCAL_OUT:
            defaults['issuer'] = 'company'
        else:
            defaults['issuer'] = 'partner'
        return defaults

    @api.model
    def create(self, values):
        dummy_doc = self.env.ref('l10n_br_fiscal.fiscal_document_dummy')
        if not values.get('document_type_id'):
            values.update({'fiscal_document_id': dummy_doc.id})
        invoice = super().create(values)
        if invoice.fiscal_document_id != dummy_doc:
            shadowed_fiscal_vals = invoice._prepare_shadowed_fields_dict()
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

    @api.multi
    def unlink(self):
        """Allows delete a draft or cancelled invoices"""
        self.filtered(lambda i: i.state in ('draft', 'cancel')).write(
            {'move_name': False}
        )
        return super().unlink()

    @api.one
    @api.depends(
        'invoice_line_ids.price_total',
        'tax_line_ids.amount',
        'tax_line_ids.amount_rounding',
        'currency_id',
        'company_id',
        'date_invoice',
        'type')
    def _compute_amount(self):
        self.fiscal_document_id._compute_amount()
        for inv_line in self.invoice_line_ids:
            if inv_line.cfop_id:
                if inv_line.cfop_id.finance_move:
                    self.amount_untaxed += inv_line.price_subtotal
                    self.amount_tax += inv_line.price_tax
            else:
                self.amount_untaxed += inv_line.price_subtotal
                self.amount_tax += inv_line.price_tax

        self.amount_total = (
            self.amount_untaxed + self.amount_tax -
            self.amount_tax_withholding)

        self.amount_total = self.amount_untaxed + self.amount_tax
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if (self.currency_id and self.company_id and
                self.currency_id != self.company_id.currency_id):
            currency_id = self.currency_id
            amount_total_company_signed = currency_id._convert(
                self.amount_total, self.company_id.currency_id,
                self.company_id, self.date_invoice or fields.Date.today())
            amount_untaxed_signed = currency_id._convert(
                self.amount_untaxed, self.company_id.currency_id,
                self.company_id, self.date_invoice or fields.Date.today())
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

    @api.model
    def invoice_line_move_line_get(self):
        move_lines_dict = super().invoice_line_move_line_get()
        new_mv_lines_dict = []
        for line in move_lines_dict:
            invoice_line = self.invoice_line_ids.browse(line.get('invl_id'))
            line['price'] = invoice_line.price_total
            if invoice_line.cfop_id:
                if invoice_line.cfop_id.finance_move:
                    new_mv_lines_dict.append(line)
            else:
                new_mv_lines_dict.append(line)

        return new_mv_lines_dict

    @api.model
    def tax_line_move_line_get(self):
        tax_lines_dict = super().tax_line_move_line_get()
        # new_tax_lines_dict = []
        # for tax in tax_lines_dict:
        #     new_tax_lines_dict.append(tax)
        #
        #     new_tax = tax.copy()
        #     new_tax['type'] = 'src'
        #
        #     new_tax_lines_dict.append(new_tax)
        return tax_lines_dict

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        lines = super().finalize_invoice_move_lines(move_lines)
        financial_lines = [
            l for l in lines if l[2]['account_id'] == self.account_id.id]

        count = 1
        for l in financial_lines:
            if l[2]['debit'] or l[2]['credit']:
                l[2]['name'] = '{}/{}-{}'.format(
                    self.fiscal_number, count, len(financial_lines))
                count += 1
        return lines

    @api.multi
    def get_taxes_values(self):
        # uncomment these lines
        # dummy_doc = self.env.ref('l10n_br_fiscal.fiscal_document_dummy')
        # if self.fiscal_document_id == dummy_doc:
        #     return super().get_taxes_values()

        tax_grouped = {}
        round_curr = self.currency_id.round
        for line in self.invoice_line_ids:
            if not line.account_id or line.display_type:
                continue

            taxes = line.invoice_line_tax_ids.compute_all(
                price_unit=line.price_unit,
                currency=line.invoice_id.currency_id,
                quantity=line.quantity,
                product=line.product_id,
                partner=line.invoice_id.partner_id,
                fiscal_taxes=line.fiscal_tax_ids,
                operation_line=line.fiscal_operation_line_id,
                ncm=line.ncm_id,
                nbs=line.nbs_id,
                nbm=line.nbm_id,
                cest=line.cest_id,
                discount_value=line.discount_value,
                insurance_value=line.insurance_value,
                other_costs_value=line.other_costs_value,
                freight_value=line.freight_value,
                fiscal_price=line.fiscal_price,
                fiscal_quantity=line.fiscal_quantity,
                uot=line.uot_id,
                icmssn_range=line.icmssn_range_id)['taxes']

            for tax in taxes:
                if tax.get('amount', 0.0) != 0.0:
                    val = self._prepare_tax_line_vals(line, tax)
                    key = self.env['account.tax'].browse(
                        tax['id']).get_grouping_key(val)

                    if key not in tax_grouped:
                        tax_grouped[key] = val
                        tax_grouped[key]['base'] = round_curr(val['base'])
                    else:
                        tax_grouped[key]['amount'] += val['amount']
                        tax_grouped[key]['base'] += round_curr(val['base'])
        return tax_grouped

    @api.multi
    def action_move_create(self):
        for inv in self.filtred(lambda i: i.fiscal._document_id !=
                self.env.ref('l10n_br_fiscal.fiscal_document_dummy')):
            inv.fiscal_document_id.action_button_confirm()
        return super().action_move_create()

    @api.onchange('fiscal_operation_id')
    def _onchange_fiscal_operation_id(self):
        super()._onchange_fiscal_operation_id()
        if self.fiscal_operation_id and self.fiscal_operation_id.journal_id:
            self.journal_id = self.fiscal_operation_id.journal_id

    @api.multi
    def open_fiscal_document(self):
        # TODO
        pass
