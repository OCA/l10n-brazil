# © 2012 KMEE INFORMATICA LTDA
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
#   @author  Hendrix Costa <hendrix.costa@kmee.com.br>
# Copyright (C) 2020 - KMEE (<http://kmee.com.br>).
#  author Daniel Sadamo <daniel.sadamo@kmee.com.br>
# Copyright (C) 2020 - Akretion (<http://akretion.com.br>).
#  author Magno Costa <magno.costa@akretion.com.br>
#  author Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants import (
    BR_CODES_PAYMENT_ORDER,
    CODE_MANUAL_TEST,
    FORMA_LANCAMENTO,
    INDICATIVO_FORMA_PAGAMENTO,
    TIPO_SERVICO,
)

_logger = logging.getLogger(__name__)


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    file_number = fields.Integer(
        string="Número sequencial do arquivo",
    )

    cnab_file = fields.Binary(
        string="CNAB File",
        readonly=True,
    )

    cnab_filename = fields.Char(
        string="CNAB Filename",
    )

    service_type = fields.Selection(
        selection=TIPO_SERVICO,
        string="Tipo de Serviço",
        help="Campo G025 do CNAB",
        default="30",
    )

    release_form = fields.Selection(
        selection=FORMA_LANCAMENTO,
        string="Forma Lançamento",
        help="Campo G029 do CNAB",
    )

    cnab_company_bank_code = fields.Char(
        related="payment_mode_id.cnab_company_bank_code",
    )

    convention_code = fields.Char(related="payment_mode_id.convention_code")

    indicative_form_payment = fields.Selection(
        selection=INDICATIVO_FORMA_PAGAMENTO,
        string="Indicativo de Forma de Pagamento",
        help="Campo P014 do CNAB",
        default="01",
    )

    # Usados para deixar invisiveis/somente leitura
    # os campos relacionados ao CNAB
    payment_method_code = fields.Char(
        related="payment_method_id.code",
        readonly=True,
        store=True,
        string="Payment Method Code",
    )

    def draft2open(self):
        """
        Called when you click on the 'Confirm' button
        Set the 'date' on payment line depending on the 'date_prefered'
        setting of the payment.order
        Re-generate the account payments.
        """
        today = fields.Date.context_today(self)
        for order in self:
            # TODO - Por enquanto no caso do CNAB esse metodo está sendo
            #  sobreescrito para não criar o account.payment(abaixo no fim
            #  do metodo), dessa forma será possível atualizar os modulos da
            #  localização com account_payment_order mantendo o mesmo
            #  funcionamento, e depois em outro PR especifico tratar essa
            #  questão, um ROADMAP da implementação do CNAB
            if order.payment_method_code not in BR_CODES_PAYMENT_ORDER:
                return super().draft2open()

            if not order.journal_id:
                raise UserError(
                    _("Missing Bank Journal on payment order %s.") % order.name
                )
            if (
                order.payment_method_id.bank_account_required
                and not order.journal_id.bank_account_id
            ):
                raise UserError(
                    _("Missing bank account on bank journal '%s'.")
                    % order.journal_id.display_name
                )
            if not order.payment_line_ids:
                raise UserError(
                    _("There are no transactions on payment order %s.") % order.name
                )
            # Unreconcile, cancel and delete existing account payments
            order.payment_ids.action_draft()
            order.payment_ids.action_cancel()
            order.payment_ids.unlink()
            # Prepare account payments from the payment lines
            group_paylines = {}  # key = hashcode
            for payline in order.payment_line_ids:
                payline.draft2open_payment_line_check()
                # Compute requested payment date
                if order.date_prefered == "due":
                    requested_date = payline.ml_maturity_date or payline.date or today
                elif order.date_prefered == "fixed":
                    requested_date = order.date_scheduled or today
                else:
                    requested_date = today
                # No payment date in the past
                if requested_date < today:
                    requested_date = today
                # inbound: check option no_debit_before_maturity
                if (
                    order.payment_type == "inbound"
                    and order.payment_mode_id.no_debit_before_maturity
                    and payline.ml_maturity_date
                    and requested_date < payline.ml_maturity_date
                ):
                    raise UserError(
                        _(
                            "The payment mode '%(payment_mode)s' has the option "
                            "'Disallow Debit Before Maturity Date'. The payment line "
                            "'%(payline)s' has a maturity date %(maturity_date)s which "
                            "is after the computed payment date %(requested_date)s.",
                            payment_mode=order.payment_mode_id.name,
                            payline=payline.name,
                            maturity_date=payline.ml_maturity_date,
                            requested_date=requested_date,
                        )
                    )
                # Write requested_date on 'date' field of payment line
                # norecompute is for avoiding a chained recomputation
                # payment_line_ids.date
                # > payment_line_ids.amount_company_currency
                # > total_company_currency
                with self.env.norecompute():
                    payline.date = requested_date
                # Group options
                if order.payment_mode_id.group_lines:
                    hashcode = payline.payment_line_hashcode()
                else:
                    # Use line ID as hascode, which actually means no grouping
                    hashcode = payline.id
                if hashcode in group_paylines:
                    group_paylines[hashcode]["paylines"] += payline
                    group_paylines[hashcode]["total"] += payline.amount_currency
                else:
                    group_paylines[hashcode] = {
                        "paylines": payline,
                        "total": payline.amount_currency,
                    }
            order.env.flush_all()
            # Create account payments
            payment_vals = []
            for paydict in list(group_paylines.values()):
                # Block if a bank payment line is <= 0
                if paydict["total"] <= 0:
                    raise UserError(
                        _(
                            "The amount for Partner '%(name)s' "
                            "is negative "
                            "or null (%(total).2f) !",
                            name=paydict["paylines"][0].partner_id.name,
                            total=paydict["total"],
                        )
                    )
                payment_vals.append(paydict["paylines"]._prepare_account_payment_vals())
            # TODO: Por enquanto evitando a criação do account.payment no caso CNAB
            # self.env["account.payment"].create(payment_vals)
        self.write({"state": "open"})
        return True

    @api.ondelete(at_uninstall=False)
    def _unlink_except_cnab_order(self):
        for order in self:
            if (
                order.payment_method_code in BR_CODES_PAYMENT_ORDER
                and order.payment_mode_id.payment_method_id.payment_type == "inbound"
            ):
                raise UserError(_("You cannot delete CNAB order."))

    def action_done_cancel(self):
        for order in self:
            # TODO: Existe o caso de se Cancelar uma Ordem de Pagto
            #  no caso CNAB ? O que deveria ser feito nesse caso ?
            if (
                order.payment_method_code in BR_CODES_PAYMENT_ORDER
                and order.payment_mode_id.payment_method_id.payment_type == "inbound"
            ):
                raise UserError(_("You cannot Cancel CNAB order."))
        return super().unlink()

    def generate_payment_file(self):
        """Esse modo deve ser usado somente para testes,
        com ele é possível passarmos por todos os fluxos de
        funcionamento das ordens de pagamento.

        Permitindo que através de testes via interface e testes
        automatizados sejam geradas ordens de pagamento de inclusão,
        alteração, baixa e etc."""

        self.ensure_one()
        if self.payment_method_id.code == CODE_MANUAL_TEST:
            return (False, False)
        else:
            return super().generate_payment_file()

    def get_file_name(self, cnab_type):
        context_today = fields.Date.context_today(self)
        date = context_today.strftime("%d%m")
        file_number = self.file_number
        if cnab_type == "240":
            return f"CB{date}{file_number}.REM"
        elif cnab_type == "400":
            return f"CB{date}{file_number:02d}.REM"
        elif cnab_type == "500":
            return f"PG{date}{file_number}.REM"
