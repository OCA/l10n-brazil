# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base import misc

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'l10n_br_fiscal.document.mixin']

    @api.multi
    def _amount_all(self):
        """
        This override is specific for Brazil. Idealy, starting from
        v12 we should just call super when the sale is not for Brazil.
        """
        for order in self:
            order.amount_untaxed = sum(line.price_subtotal for line in order.order_line)
            order.amount_tax = sum(line.price_tax for line in order.order_line)
            order.amount_total = sum(line.price_total for line in order.order_line)
            order.amount_extra = 0.0
            order.amount_discount = 0.0
            order.amount_gross = 0.0

            amount_tax = (
                amount_untaxed
            ) = amount_discount = amount_gross = amount_extra = 0.0
            for line in order.order_line:
                amount_tax = line.amount_tax_not_included
                amount_extra += (
                    line.insurance_value + line.freight_value + line.other_costs_value
                )
                amount_untaxed += line.price_subtotal
                amount_discount += line.discount_value
                amount_gross += line.price_gross

            order.amount_tax = order.pricelist_id.currency_id.round(amount_tax)
            order.amount_untaxed = order.pricelist_id.currency_id.round(amount_untaxed)
            order.amount_extra = order.pricelist_id.currency_id.round(amount_extra)
            order.amount_total = (
                order.amount_untaxed + order.amount_tax + order.amount_extra
            )
            order.amount_discount = order.pricelist_id.currency_id.round(
                amount_discount
            )
            order.amount_gross = order.pricelist_id.currency_id.round(amount_gross)

    @api.multi
    def _compute_costs_value(self):
        """Compute the l10n_br specific functional fields."""
        for record in self:
            record.amount_freight = sum(
                line.freight_value for line in self.order_line)
            record.amount_costs = sum(
                line.other_costs_value for line in self.order_line)
            record.amount_insurance = sum(
                line.insurance_value for line in self.order_line)

    @api.one
    def _inverse_amount_freight(self):
        for line in self.order_line:
            if not self.amount_gross:
                break
            line.write(
                {
                    'freight_value': misc.calc_price_ratio(
                        line.price_gross,
                        self.amount_freight,
                        line.order_id.amount_gross,
                    )
                }
            )
        return True

    @api.one
    def _inverse_amount_insurance(self):
        for line in self.order_line:
            if not self.amount_gross:
                break
            line.write(
                {
                    'insurance_value': misc.calc_price_ratio(
                        line.price_gross,
                        self.amount_insurance,
                        line.order_id.amount_gross,
                    )
                }
            )
        return True

    @api.one
    def _inverse_amount_costs(self):
        for line in self.order_line:
            if not self.amount_gross:
                break
            line.write(
                {
                    'other_costs_value': misc.calc_price_ratio(
                        line.price_gross, self.amount_costs, line.order_id.amount_gross
                    )
                }
            )
        return True

    @api.model
    def _default_operation(self):
        return self.env.user.company_id.sale_fiscal_operation_id

    @api.model
    def _operation_domain(self):
        domain = [('state', '=', 'approved')]
        return domain

    @api.model
    def _default_copy_note(self):
        return self.env.user.company_id.copy_note

    operation_id = fields.Many2one(
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_operation,
        domain=lambda self: self._operation_domain())

    ind_pres = fields.Selection(
        readonly=True,
        states={"draft": [("readonly", False)]})

    copy_note = fields.Boolean(
        string='Copiar Observação no documentos fiscal',
        default=_default_copy_note)

    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        related='partner_id.cnpj_cpf')

    legal_name = fields.Char(
        string='Legal Name',
        related='partner_id.legal_name')

    ie = fields.Char(
        string='State Tax Number/RG',
        related='partner_id.inscr_est')

    discount_rate = fields.Float(
        string='Discount',
        readonly=True,
        states={'draft': [('readonly', False)]})

    amount_gross = fields.Float(
        compute='_amount_all',
        string="Gross Price",
        digits=dp.get_precision("Account"),
        store=True,
        help="Amount without discount.")

    amount_discount = fields.Float(
        compute="_amount_all",
        string="Discount (-)",
        digits=dp.get_precision("Account"),
        store=True,
        help="The discount amount.")

    amount_untaxed = fields.Float(
        compute="_amount_all",
        string="Untaxed Amount",
        digits=dp.get_precision("Account"),
        store=True,
        help="The amount without tax.",
        track_visibility="always")

    amount_tax = fields.Float(
        compute="_amount_all",
        string="Taxes",
        store=True,
        digits=dp.get_precision("Account"),
        help="The tax amount.")

    amount_extra = fields.Float(
        compute="_amount_all",
        string="Extra",
        digits=dp.get_precision("Account"),
        store=True,
        help="The total amount.")

    amount_freight = fields.Float(
        compute="_compute_costs_value",
        inverse="_inverse_amount_freight",
        string="Freight",
        default=0.00,
        digits=dp.get_precision("Account"),
        readonly=True,
        states={"draft": [("readonly", False)]})

    amount_costs = fields.Float(
        compute="_compute_costs_value",
        inverse="_inverse_amount_costs",
        string="Other Costs",
        default=0.00,
        digits=dp.get_precision("Account"),
        readonly=True,
        states={"draft": [("readonly", False)]})

    amount_insurance = fields.Float(
        compute="_compute_costs_value",
        inverse="_inverse_amount_insurance",
        string="Insurance",
        default=0.00,
        digits=dp.get_precision("Account"),
        readonly=True,
        states={"draft": [("readonly", False)]})

    amount_total = fields.Float(
        compute="_amount_all",
        string="Total",
        store=True,
        digits=dp.get_precision("Account"),
        help="The total amount.")

    @api.onchange('discount_rate')
    def onchange_discount_rate(self):
        for sale_order in self:
            for sale_line in sale_order.order_line:
                sale_line.discount = sale_order.discount_rate

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        self.fiscal_position_id = self.operation_id.fiscal_position_id

    # TODO FIscal Comment
    # @api.model
    # def _fiscal_comment(self, order):
    #     fp_comment = []
    #     fp_ids = []
    #
    #     for line in order.order_line:
    #         if line.operation_line_id and \
    #                 line.operation_line_id.inv_copy_note and \
    #                 line.operation_line_id.note:
    #             if line.operation_line_id.id not in fp_ids:
    #                 fp_comment.append(line.operation_line_id.note)
    #                 fp_ids.append(line.operation_line_id.id)
    #
    #      return fp_comment

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        result = super(SaleOrder, self)._prepare_invoice()

        if self.operation_id:
            result['operation_id'] = self.operation_id.id
            result['fiscal_document_id'] = False
            result['operation_type'] = self.operation_id.operation_type
            result['partner_shipping_id'] = self.partner_shipping_id.id

            # TODO Defini document_type_id in other method in line
            result['document_type_id'] = self._context.get('document_type_id')

            if self.operation_id.journal_id:
                result['journal_id'] = self.operation_id.journal_id.id

        comment = []
        if self.note and self.copy_note:
            comment.append(self.note)

        # TODO FISCAL Commnet
        # result['fiscal_comment'] = " - ".join(fiscal_comment)
        # fiscal_comment = self._fiscal_comment(self)
        result['comment'] = " - ".join(comment)
        return result

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id.
         If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        invoices = {}
        references = {}
        invoices_origin = {}
        invoices_name = {}

        # Keep track of the sequences of the lines
        # To keep lines under their section
        inv_line_sequence = 0
        for order in self:

            # In brazilian localization we need to overwrite this method
            # to changing the code below, because when there is a sale
            # order has line with Fiscal Type service and another
            # product, the method should be create two invoices separated.

            # group_key = order.id if grouped else (
            # order.partner_invoice_id.id, order.currency_id.id)

            # We only want to create sections that have at least
            # one invoiceable line
            pending_section = None

            # Create lines in batch to avoid performance problems
            line_vals_list = []
            # sequence is the natural order of order_lines
            for line in order.order_line:

                # Here we made the change for brazilian localization
                group_key = (
                    order.id, line.operation_line_id.document_type_id.id
                ) if grouped else (
                    order.partner_invoice_id.id, order.currency_id.id,
                    line.operation_line_id.document_type_id.id)

                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order.with_context(
                        document_type_id=line.operation_line_id.get_document_type(
                            line.order_id.company_id).id)._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                    invoices_origin[group_key] = [invoice.origin]
                    invoices_name[group_key] = [invoice.name]
                elif group_key in invoices:
                    if order.name not in invoices_origin[group_key]:
                        invoices_origin[group_key].append(order.name)
                    if (order.client_order_ref and order.client_order_ref
                            not in invoices_name[group_key]):
                        invoices_name[group_key].append(order.client_order_ref)

                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    if pending_section:
                        section_invoice = pending_section.invoice_line_create_vals(
                            invoices[group_key].id,
                            pending_section.qty_to_invoice
                        )
                        inv_line_sequence += 1
                        section_invoice[0]['sequence'] = inv_line_sequence
                        line_vals_list.extend(section_invoice)
                        pending_section = None

                    inv_line_sequence += 1
                    inv_line = line.invoice_line_create_vals(
                        invoices[group_key].id, line.qty_to_invoice
                    )
                    inv_line[0]['sequence'] = inv_line_sequence
                    line_vals_list.extend(inv_line)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoices[group_key]] |= order

            self.env['account.invoice.line'].create(line_vals_list)

        for group_key in invoices:
            invoices[group_key].write({'name': ', '.join(invoices_name[group_key]),
                                       'origin': ', '.join(invoices_origin[group_key])})
            sale_orders = references[invoices[group_key]]
            if len(sale_orders) == 1:
                invoices[group_key].reference = sale_orders.reference

        if not invoices:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered'
                ' quantities invoicing policy, please make sure that'
                ' a quantity has been delivered.'))

        self._finalize_invoices(invoices, references)
        return [inv.id for inv in invoices.values()]
