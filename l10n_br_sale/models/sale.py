# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base import misc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'l10n_br_fiscal.document.mixin']

    @api.multi
    @api.depends('order_line.price_unit', 'order_line.tax_id',
                 'order_line.discount', 'order_line.product_uom_qty')
    def _amount_all_wrapper(self):
        """ Wrapper because of direct method passing
        as parameter for function fields """
        return self._amount_all()

    @api.multi
    def _amount_all(self):
        """
        This override is specific for Brazil. Idealy, starting from
        v12 we should just call super when the sale is not for Brazil.
        """
        for order in self:
            order.amount_untaxed = 0.0
            order.amount_tax = 0.0
            order.amount_total = 0.0
            order.amount_extra = 0.0
            order.amount_discount = 0.0
            order.amount_gross = 0.0

            amount_tax = (
                amount_untaxed
            ) = amount_discount = amount_gross = amount_extra = 0.0
            for line in order.order_line:
                amount_tax += self._amount_line_tax(line)
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

    @api.model
    def _amount_line_tax(self, line):
        value = 0.0
        price = line._calc_line_base_price()
        qty = line._calc_line_quantity()

        for computed in line.tax_id.compute_all(
            price_unit=price,
            quantity=qty,
            partner=line.order_id.partner_invoice_id,
            product=line.product_id,
            # line.order_id.partner_id,
            # operation_id=line.operation_id,
            insurance_value=line.insurance_value,
            freight_value=line.freight_value,
            other_costs_value=line.other_costs_value,
        )["taxes"]:
            tax = self.env["account.tax"].browse(computed["id"])
            if not tax.tax_group_id.tax_discount:
                value += computed.get("amount", 0.0)
        return value

    @api.model
    def _default_ind_pres(self):
        company = self.env["res.company"].browse(self.env.user.company_id.id)
        return company.default_ind_pres

    @api.one
    def _get_costs_value(self):
        """ Read the l10n_br specific functional fields. """
        freight = costs = insurance = 0.0
        for line in self.order_line:
            freight += line.freight_value
            insurance += line.insurance_value
            costs += line.other_costs_value
        self.amount_freight = freight
        self.amount_costs = costs
        self.amount_insurance = insurance

    @api.one
    def _set_amount_freight(self):
        for line in self.order_line:
            if not self.amount_gross:
                break
            line.write(
                {
                    "freight_value": misc.calc_price_ratio(
                        line.price_gross,
                        self.amount_freight,
                        line.order_id.amount_gross,
                    )
                }
            )
        return True

    @api.one
    def _set_amount_insurance(self):
        for line in self.order_line:
            if not self.amount_gross:
                break
            line.write(
                {
                    "insurance_value": misc.calc_price_ratio(
                        line.price_gross,
                        self.amount_insurance,
                        line.order_id.amount_gross,
                    )
                }
            )
        return True

    @api.one
    def _set_amount_costs(self):
        for line in self.order_line:
            if not self.amount_gross:
                break
            line.write(
                {
                    "other_costs_value": misc.calc_price_ratio(
                        line.price_gross, self.amount_costs, line.order_id.amount_gross
                    )
                }
            )
        return True

    copy_note = fields.Boolean(
        string='Copiar Observação no documentos fiscal')

    amount_discount = fields.Float(
        compute='_amount_all_wrapper',
        string='Desconto (-)',
        digits=dp.get_precision('Account'),
        store=True,
        help="The discount amount.")

    amount_gross = fields.Float(
        compute='_amount_all_wrapper',
        string='Vlr. Bruto',
        digits=dp.get_precision('Account'),
        store=True, help="The discount amount.")

    discount_rate = fields.Float(
        string='Desconto',
        readonly=True,
        states={'draft': [('readonly', False)]})

    cnpj_cpf = fields.Char(
        string=u'CNPJ/CPF',
        related='partner_id.cnpj_cpf')

    legal_name = fields.Char(
        string=u'Razão Social',
        related='partner_id.legal_name')

    ie = fields.Char(
        string=u'Inscrição Estadual',
        related='partner_id.inscr_est')

    ind_pres = fields.Selection(
        selection=[
            (
                "0",
                u"Não se aplica (por exemplo,"
                u" Nota Fiscal complementar ou de ajuste)",
            ),
            ("1", u"Operação presencial"),
            ("2", u"Operação não presencial, pela Internet"),
            ("3", u"Operação não presencial, Teleatendimento"),
            ("4", u"NFC-e em operação com entrega em domicílio"),
            ("5", u"Operação presencial, fora do estabelecimento"),
            ("9", u"Operação não presencial, outros"),
        ],
        string=u"Tipo de operação",
        readonly=True,
        states={"draft": [("readonly", False)]},
        required=False,
        help=u"Indicador de presença do comprador no estabelecimento \
             comercial no momento da operação.",
        default=_default_ind_pres,
    )

    amount_untaxed = fields.Float(
        compute="_amount_all",
        string="Untaxed Amount",
        digits=dp.get_precision("Account"),
        store=True,
        help="The amount without tax.",
        track_visibility="always",
    )

    amount_tax = fields.Float(
        compute="_amount_all",
        string="Taxes",
        store=True,
        digits=dp.get_precision("Account"),
        help="The tax amount.",
    )

    amount_total = fields.Float(
        compute="_amount_all",
        string="Total",
        store=True,
        digits=dp.get_precision("Account"),
        help="The total amount.",
    )

    amount_extra = fields.Float(
        compute="_amount_all",
        string="Extra",
        digits=dp.get_precision("Account"),
        store=True,
        help="The total amount.",
    )

    amount_discount = fields.Float(
        compute="_amount_all",
        string="Desconto (-)",
        digits=dp.get_precision("Account"),
        store=True,
        help="The discount amount.",
    )

    amount_gross = fields.Float(
        compute="_amount_all",
        string="Vlr. Bruto",
        digits=dp.get_precision("Account"),
        store=True,
        help="The discount amount.",
    )

    amount_freight = fields.Float(
        compute="_get_costs_value",
        inverse="_set_amount_freight",
        string="Frete",
        default=0.00,
        digits=dp.get_precision("Account"),
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    amount_costs = fields.Float(
        compute="_get_costs_value",
        inverse="_set_amount_costs",
        string="Outros Custos",
        default=0.00,
        digits=dp.get_precision("Account"),
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    amount_insurance = fields.Float(
        compute="_get_costs_value",
        inverse="_set_amount_insurance",
        string="Seguro",
        default=0.00,
        digits=dp.get_precision("Account"),
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.onchange('discount_rate')
    def onchange_discount_rate(self):
        for sale_order in self:
            for sale_line in sale_order.order_line:
                sale_line.discount = sale_order.discount_rate

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
        context = self.env.context

        if (context.get('fiscal_type') == 'service' and
                self.order_line and self.order_line[0].operation_id):
            operation_id = self.order_line[0].operation_id.id
            result['operation_id'] = self.order_line.operation_id.id
        else:
            operation_id = self.operation_id
            result['operation_id'] = self.operation_id.id

        # TODO check journal
        # if operation_id:
        #    result['journal_id'] = operation_id.property_journal.id

        result['partner_shipping_id'] = self.partner_shipping_id.id

        comment = []
        if self.note and self.copy_note:
            comment.append(self.note)

        # TODO FISCAL Commnet
        # fiscal_comment = self._fiscal_comment(self)
        result['comment'] = " - ".join(comment)
        # result['fiscal_comment'] = " - ".join(fiscal_comment)
        result['operation_id'] = operation_id.id

        return result
