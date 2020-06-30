# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PaymentMixin(models.AbstractModel):
    _name = "l10n_br_fiscal.payment.mixin"
    _description = "Fiscal Payment Mixin"

    _payment_inverse_name = 'document_id'  # Modify on your class

    def _compute_payment_change_value(self):
        """
            @api.depends("amount_total", "fiscal_payment_ids")
            def _compute_payment_change_value(self):
                self.___compute_payment_change_value()

        :return:
        """
        raise NotImplementedError

    def _date_field(self):
        self.date

    def _get_amount_total(self):
        return self.amount_total

    def _abstract_compute_payment_change_value(self):
        for record in self:
            payment_value = 0
            for payment in record.fiscal_payment_ids:
                for line in payment.line_ids:
                    payment_value += line.amount

            record.amount_payment_value = payment_value

            change_value = payment_value - record._get_amount_total()
            record.amount_change_value = change_value if change_value >= 0 else 0

            missing_payment = record._get_amount_total() - payment_value
            record.amount_missing_payment_value = missing_payment \
                if missing_payment >= 0 else 0

    currency_id = fields.Many2one(
        comodel_name='res.currency',
    )
    amount_change_value = fields.Monetary(
        string="Change Value",
        default=0.00,
        compute="_compute_payment_change_value"
    )

    amount_payment_value = fields.Monetary(
        string="Payment Value",
        default=0.00,
        compute="_compute_payment_change_value"
    )

    amount_missing_payment_value = fields.Monetary(
        string="Missing Payment Value",
        default=0.00,
        compute="_compute_payment_change_value"
    )

    #
    # Duplicatas e pagamentos
    #

    payment_condition_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.payment.condition',
        string='Condição de pagamento',
        ondelete='restrict',
    )

    payment_term_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.payment.term',
        string='Forma de pagamento',
        ondelete='restrict',
    )

    payment_mode_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.payment.mode',
        string='Modo de pagamento',
        ondelete='restrict',
    )

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

    show_payment_condition = fields.Boolean(
        compute='_compute_show_payment_condition'
    )

    def _compute_show_payment_condition(self):
        for record in self:
            record.show_payment_condition = self.user_has_groups(
                'l10n_br_fiscal.group_payment_condition'
            )

    def check_financial(self):
        for record in self:
            if not record.env.context.get('action_document_confirm'):
                continue
            elif record.amount_missing_payment_value > 0:
                if not record.payment_term_id:
                    raise UserError(
                        _("O Valor dos lançamentos financeiros é "
                          "menor que o valor da nota."),
                    )
                else:
                    record.generate_financial()

    def generate_financial(self):
        for record in self:
            if record.payment_term_id and self.company_id and self.currency_id:
                record.financial_ids.unlink()
                record.fiscal_payment_ids.unlink()
                vals = {
                    'payment_term_id':
                        self.payment_term_id and self.payment_term_id.id,
                    'payment_mode_id':
                           self.payment_mode_id and self.payment_mode_id.id,
                    'payment_condition_id':
                        self.payment_condition_id and self.payment_condition_id.id,
                    'amount': self.amount_missing_payment_value,
                    'currency_id': self.currency_id.id,
                    'company_id': self.company_id.id,
                }
                vals.update(self.fiscal_payment_ids._compute_payment_vals(
                    payment_term_id=self.payment_term_id,
                    currency_id=self.currency_id,
                    company_id=self.company_id,
                    amount=self.amount_missing_payment_value, date=self._date_field())
                )
                vals[self._payment_inverse_name] = self.id
                self.fiscal_payment_ids = self.fiscal_payment_ids.new(vals)
                for line in self.fiscal_payment_ids.mapped('line_ids'):
                    setattr(line, self._payment_inverse_name, self)

            elif record.fiscal_payment_ids:
                record.financial_ids.unlink()
                record.fiscal_payment_ids.unlink()

    @api.onchange("fiscal_payment_ids", "payment_term_id")
    def _onchange_fiscal_payment_ids(self):
        financial_ids = []

        for payment in self.fiscal_payment_ids:
            for line in payment.line_ids:
                financial_ids.append(line.id)
        self.financial_ids = [(6, 0, financial_ids)]

    # @api.onchange("payment_term_id", "company_id", "currency_id",
    #               "amount_missing_payment_value", "date")
    # def _onchange_payment_term_id(self):
    #     if (self.payment_term_id and self.company_id and
    #             self.currency_id):
    #
    #         self.financial_ids.unlink()
    #
    #         vals = {
    #             'payment_term_id': self.payment_term_id.id,
    #             'amount': self.amount_missing_payment_value,
    #             'currency_id': self.currency_id.id,
    #             'company_id': self.company_id.id,
    #          }
    #         vals.update(self.fiscal_payment_ids._compute_payment_vals(
    #             payment_term_id=self.payment_term_id, currency_id=self.currency_id,
    #             company_id=self.company_id,
    #             amount=self.amount_missing_payment_value, date=self.date)
    #         )
    #         self.fiscal_payment_ids = self.fiscal_payment_ids.new(vals)
    #         for line in self.fiscal_payment_ids.mapped('line_ids'):
    #             line.document_id = self

    @api.onchange('payment_condition_id')
    def _onchange_payment_condition(self):
        for record in self:
            if record.payment_condition_id:
                record.payment_term_id = record.payment_condition_id.payment_term_id
                record.payment_mode_id = record.payment_condition_id.payment_mode_id
