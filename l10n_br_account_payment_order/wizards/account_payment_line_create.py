# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class AccountPaymentLineCreate(models.TransientModel):
    _inherit = "account.payment.line.create"

    allow_error = fields.Boolean(
        string="Permitir linhas com erro na exportação, "
        "já incluidas em outras ordens",
    )

    allow_rejected = fields.Boolean(
        string="Permitir linhas com retorno rejeitado",
    )

    def _prepare_move_line_domain(self):
        """Nenhuma linha deve ser adicionada novamente a nao ser que o
        retorno do cnab informe que o registro falhou,

        entretanto o super tem um trecho:

        # Exclude lines that are already in a non-cancelled
        # and non-uploaded payment order; lines that are in a
        # uploaded payment order are proposed if they are not reconciled,
        paylines = self.env['account.payment.line'].search([
            ('state', 'in', ('draft', 'open', 'generated')),
            ('move_line_id', '!=', False)])
        if paylines:
            move_lines_ids = [payline.move_line_id.id for payline in paylines]
            domain += [('id', 'not in', move_lines_ids)]

        :return:
        """
        domain = super()._prepare_move_line_domain()

        # self.ensure_one()
        # domain = [
        #     ("reconciled", "=", False),
        #     ("company_id", "=", self.order_id.company_id.id),
        # ]
        # if self.journal_ids:
        #     domain += [("journal_id", "in", self.journal_ids.ids)]
        # if self.partner_ids:
        #     domain += [("partner_id", "in", self.partner_ids.ids)]
        # if self.target_move == "posted":
        #     domain += [("move_id.state", "=", "posted")]
        # if not self.allow_blocked:
        #     domain += [("blocked", "!=", True)]
        # if self.date_type == "due":
        #     domain += [
        #         "|",
        #         ("date_maturity", "<=", self.due_date),
        #         ("date_maturity", "=", False),
        #     ]
        # elif self.date_type == "move":
        #     domain.append(("date", "<=", self.move_date))
        # if self.invoice:
        #     domain.append(("invoice_id", "!=", False))
        # if self.payment_mode:
        #     if self.payment_mode == "same":
        #         domain.append(
        #             ("payment_mode_id", "=", self.order_id.payment_mode_id.id)
        #         )
        #     elif self.payment_mode == "same_or_null":
        #         domain += [
        #             "|",
        #             ("payment_mode_id", "=", False),
        #             ("payment_mode_id", "=", self.order_id.payment_mode_id.id),
        #         ]
        #
        # if self.order_id.payment_type == "outbound":
        #     # For payables, propose all unreconciled credit lines,
        #     # including partially reconciled ones.
        #     # If they are partially reconciled with a supplier refund,
        #     # the residual will be added to the payment order.
        #     #
        #     # For receivables, propose all unreconciled credit lines.
        #     # (ie customer refunds): they can be refunded with a payment.
        #     # Do not propose partially reconciled credit lines,
        #     # as they are deducted from a customer invoice, and
        #     # will not be refunded with a payment.
        #     domain += [
        #         ("credit", ">", 0),
        #         #  '|',
        #         ("account_id.internal_type", "=", "payable"),
        #         #  '&',
        #         #  ('account_id.internal_type', '=', 'receivable'),
        #         #  ('reconcile_partial_id', '=', False),  # TODO uncomment
        #     ]
        # elif self.order_id.payment_type == "inbound":
        #     domain += [
        #         ("debit", ">", 0),
        #         ("account_id.internal_type", "=", "receivable"),
        #     ]
        # # Exclude lines that are already in a non-cancelled
        # # and non-uploaded payment order; lines that are in a
        # # uploaded payment order are proposed if they are not reconciled,
        # # paylines = self.env["account.payment.line"].search(
        # #     [
        # #         ("state", "in", ("draft", "open", "generated", "uploaded")),
        # #         ("move_line_id", "!=", False),
        # #     ]
        # # )

        # move_line_domain = ["draft"]
        # if self.allow_error:
        #     move_line_domain.append("exporting_error")
        # if self.allow_rejected:
        #     move_line_domain.append("not_accepted")
        #
        # domain += [("bank_payment_line_id", "=", False)]
        #
        # domain += [("state_cnab", "in", move_line_domain)]

        # if paylines:
        #     move_lines_ids = [
        #         payline.move_line_id.id for payline in paylines
        #     ]
        #     domain += [('id', 'not in', move_lines_ids)]
        return domain
