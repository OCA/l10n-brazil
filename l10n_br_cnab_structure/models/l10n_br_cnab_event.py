# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class CNABReturnEvent(models.Model):
    _inherit = "l10n_br_cnab.return.event"

    # BASE FIELDS #

    occurrence_code_1 = fields.Char()
    occurrence_code_2 = fields.Char()
    occurrence_code_3 = fields.Char()
    occurrence_code_4 = fields.Char()
    occurrence_code_5 = fields.Char()
    bank_code = fields.Char()
    batch_code = fields.Char()
    record_type = fields.Char()
    seq_number = fields.Char()
    move_type_code = fields.Char()
    partner_bank_code = fields.Char()
    # código da câmera centralizadora
    centralizing_chamber_code = fields.Char()
    partner_bank_branch = fields.Char()
    partner_name = fields.Char()
    partner_document = fields.Char(
        help="Partners's document number, it can be a CNPJ or CPF."
    )
    partner_bank_account = fields.Char()
    partner_bank_account_dac = fields.Char()
    partner_notification = fields.Char()
    expected_payment_date = fields.Date()
    additional_info = fields.Char()
    ted_purpose = fields.Char()
    doc_purpose = fields.Char()

    gen_liquidation_move = fields.Boolean(
        string="Generate Liquidation Move",
        help="If check, this CNAB Event will generate a liquidity move line.",
    )
    generated_move_id = fields.Many2one(comodel_name="account.move")

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        related="cnab_return_log_id.cnab_structure_id",
    )

    balance = fields.Float(
        compute="_compute_balance",
        help="Balance = Payment Value + Discount Value + Rebate Value - Fees",
    )

    move_line_ids = fields.Many2many(
        comodel_name="account.move.line", ondelete="restrict"
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal", related="cnab_return_log_id.journal_id"
    )
    state = fields.Selection(
        selection=[
            ("error", "Error"),
            ("ignored", "Ignored"),
            ("ready", "Ready to Genereta Move"),
            ("confirmed", "Confirmed"),
        ]
    )

    @api.depends(
        "gen_liquidation_move",
        "payment_value",
        "discount_value",
        "rebate_value",
        "interest_fee_value",
    )
    def _compute_balance(self):
        for record in self:
            if record.gen_liquidation_move:
                record.balance = (
                    record.payment_value
                    + record.discount_value
                    + record.rebate_value
                    - record.interest_fee_value
                )
            else:
                record.balance = 0

    @api.model
    def create(self, vals):
        """Override Create Method"""
        event = super().create(vals)
        if not event.cnab_return_log_id.cnab_structure_id:
            # if there is no cnab_structure_id it is because the return file is not
            # being processed by this module, so there is nothing to do here.
            return event
        event.load_description_occurrences()
        event.load_bank_payment_line()
        event.check_gen_liquidation_move()
        event.set_move_line_ids()
        event.set_occurrence_date()
        if event.state != "error":
            if event.gen_liquidation_move or event.tariff_charge > 0:
                event.state = "ready"
            else:
                event.state = "confirmed"
        return event

    def confirm_event(self):
        if self.state != "ignored":
            if self.state == "error":
                raise UserError(
                    _(
                        f"Event {self.seq_number}: You cannot comfirm an "
                        f"Return Log with events with state error."
                    )
                )
            if self.gen_liquidation_move:
                self.create_liq_move()
            elif self.tariff_charge > 0:
                self.create_tariff_move()
            self.state = "confirmed"

    def set_occurrence_date(self):
        if not self.occurrence_date:
            self.occurrence_date = self.cnab_return_log_id.cnab_date_file

    def set_move_line_ids(self):
        payment_lines = self.payment_line_ids
        for payment_line in payment_lines:
            self.move_line_ids = [Command.link(payment_line.move_line_id.id)]

    def check_gen_liquidation_move(self):
        codes = [
            self.occurrence_code_1,
            self.occurrence_code_2,
            self.occurrence_code_3,
            self.occurrence_code_4,
            self.occurrence_code_5,
        ]
        occurrence_obj = self.env["cnab.occurrence"]

        self.gen_liquidation_move = False
        for code in codes:
            occurrence_id = occurrence_obj.search(
                [
                    ("cnab_structure_id", "=", self.cnab_structure_id.id),
                    ("code", "=", code),
                ]
            )
            if occurrence_id.gen_liquidation_move:
                self.gen_liquidation_move = True

    def load_bank_payment_line(self):
        """
        When for cnab outbound payment processed by this module the
        bank_payment_line_id is filled based on your_number field
        """
        for event in self:
            if event.cnab_return_log_id.type == "outbound":
                payment_lines = self.env["account.payment.line"].search(
                    [("name", "=", event.your_number)]
                )
                if not payment_lines:
                    event.state = "error"
                    event.occurrences = "PAYMENT LINES NOT FOUND"
                event.payment_line_ids = payment_lines.ids

    def get_description_occurrence(self, event_code):
        """Get occurrence description by occurrence code"""
        occurrence_id = (
            self.cnab_return_log_id.cnab_structure_id.cnab_occurrence_ids.filtered(
                lambda a: a.code == event_code
            )
        )
        if occurrence_id:
            description = occurrence_id.name
        else:
            self.state = "error"
            description = event_code + "-" + "DESCRIPTION CODE NOT FOUND"
        return description

    def load_description_occurrences(self):
        """Generate occurrence description for all occurrences"""
        for event in self:
            occurrences = []
            event_codes = (
                event.occurrence_code_1,
                event.occurrence_code_2,
                event.occurrence_code_3,
                event.occurrence_code_4,
                event.occurrence_code_5,
            )
            for code in event_codes:
                if not code:
                    continue
                occurrences.append(event.get_description_occurrence(code))
            event.occurrences = "\n".join(occurrences)

    def _get_liq_move_vals(self):
        return {
            "name": f"CNAB Return {self.cnab_return_log_id.bank_id.short_name} - "
            f"{self.cnab_return_log_id.bank_account_id.acc_number} - "
            f"REF: {self.your_number}",
            "ref": self.your_number,
            "is_cnab": True,
            "journal_id": self.journal_id.id,
            "currency_id": self.journal_id.currency_id.id
            or self.cnab_return_log_id.company_id.currency_id.id,
            "date": self.real_payment_date,
            "cnab_return_log_id": self.cnab_return_log_id.id,
        }

    # TODO We aren't handling multi-currency.
    def _get_reconciliation_items(self, move_id):
        move_line_obj = self.env["account.move.line"]
        to_reconcile_amls = []
        balance = self.balance
        # If it is an outbound payment, the counterpart will be an debit.
        # If inbound will be a credit
        debit_or_credit = "debit" if self.move_line_ids[0].balance < 0 else "credit"
        move_lines = self.move_line_ids.sorted(key=lambda line: line.date_maturity)
        for index, move_line in enumerate(move_lines):
            line_balance = abs(move_line.balance)
            # the total value of counterpart move lines must be equal to balance
            # in return event
            if index != len(self.move_line_ids) - 1:
                if balance > line_balance:
                    value = line_balance
                    balance -= line_balance
                elif balance < 0:
                    value = 0
                else:
                    value = balance
            else:
                value = balance if balance >= 0 else 0

            # TODO ver a logica para fazer o tratamento do multicurrency
            if value > 0:
                name = move_line.move_id.name
                if self.company_title_identification:
                    name += f" - {self.company_title_identification}"
                vals = {
                    "name": name,
                    "account_id": move_line.account_id.id,
                    "partner_id": move_line.partner_id.id,
                    "move_id": move_id.id,
                    debit_or_credit: value,
                }

                liq_move_line = move_line_obj.with_context(
                    check_move_validity=False
                ).create(vals)
                to_reconcile_amls.append(liq_move_line + move_line)
        self._create_counterpart_move_line(move_id, move_lines[0].partner_id)
        return to_reconcile_amls

    def _create_counterpart_move_line(self, move_id, partner_id):
        if self.move_line_ids[0].balance < 0:
            debit_or_credit = "credit"
            account_id = (
                self.journal_id.company_id.account_journal_payment_credit_account_id
            )
        else:
            debit_or_credit = "debit"
            account_id = (
                self.journal_id.company_id.account_journal_payment_debit_account_id
            )
        move_line_obj = self.env["account.move.line"]
        counterpart_vals = {
            "move_id": move_id.id,
            "partner_id": partner_id.id,
            "account_id": account_id.id,
            debit_or_credit: self.balance,
        }
        aml = move_line_obj.with_context(check_move_validity=False).create(
            counterpart_vals
        )
        return aml

    def _create_tariff_move_lines(self, move_id):
        if self.tariff_charge > 0:
            move_line_obj = self.env["account.move.line"]
            move_vals_list = []
            move_vals_list.append(
                {
                    "name": "Bank Tariff: " + self.your_number,
                    "credit": self.tariff_charge,
                    "account_id": (
                        self.journal_id.company_id.account_journal_payment_credit_account_id.id
                    ),
                    "partner_id": self.move_line_ids[0].partner_id.id,
                    "move_id": move_id.id,
                }
            )

            move_vals_list.append(
                {
                    "name": "Bank Tariff: " + self.your_number,
                    "debit": self.tariff_charge,
                    "account_id": self.journal_id.tariff_charge_account_id.id,
                    "partner_id": self.move_line_ids[0].partner_id.id,
                    "move_id": move_id.id,
                }
            )
            move_line_obj.with_context(check_move_validity=False).create(move_vals_list)

    def _get_tariff_move_vals(self):
        return {
            "name": (
                f"CNAB Return {self.cnab_return_log_id.bank_id.short_name} - "
                f"{self.cnab_return_log_id.bank_account_id.acc_number} - "
                f"REF: {self.your_number} - TARIFF: {self.occurrences}"
            ),
            "ref": self.your_number,
            "is_cnab": True,
            "journal_id": self.journal_id.id,
            "currency_id": self.journal_id.currency_id.id
            or self.cnab_return_log_id.company_id.currency_id.id,
            "date": self.occurrence_date,
            "cnab_return_log_id": self.cnab_return_log_id.id,
        }

    def create_tariff_move(self):
        move_obj = self.env["account.move"]
        move_vals = self._get_tariff_move_vals()
        move_id = move_obj.create(move_vals)
        self._create_tariff_move_lines(move_id)
        move_id.post()
        self.generated_move_id = move_id

    def _create_rebate_move_lines(self, move_id):
        if self.rebate_value > 0:
            move_line_obj = self.env["account.move.line"]
            credit_move_line = {
                "name": "Rebate: " + self.your_number,
                "credit": self.rebate_value,
                "partner_id": self.move_line_ids[0].partner_id.id,
                "move_id": move_id.id,
            }
            debit_move_line = {
                "name": "Rebate: " + self.your_number,
                "debit": self.rebate_value,
                "partner_id": self.move_line_ids[0].partner_id.id,
                "move_id": move_id.id,
            }
            if self.cnab_return_log_id.type == "inbound":
                company_id = self.journal_id.company_id
                account_id = company_id.account_journal_payment_credit_account_id
                credit_move_line["account_id"] = account_id.id
                debit_move_line[
                    "account_id"
                ] = self.journal_id.inbound_rebate_account_id.id
            else:
                credit_move_line[
                    "account_id"
                ] = self.journal_id.outbound_rebate_account_id.id
                debit_move_line[
                    "account_id"
                ] = self.journal_id.company_id.account_journal_payment_debit_account_id

            move_line_obj.with_context(check_move_validity=False).create(
                [credit_move_line, debit_move_line]
            )

    def _create_discount_move_lines(self, move_id):
        if self.discount_value > 0:
            move_line_obj = self.env["account.move.line"]
            credit_move_line = {
                "name": "Discount: " + self.your_number,
                "credit": self.discount_value,
                "partner_id": self.move_line_ids[0].partner_id.id,
                "move_id": move_id.id,
            }
            debit_move_line = {
                "name": "Discount: " + self.your_number,
                "debit": self.discount_value,
                "partner_id": self.move_line_ids[0].partner_id.id,
                "move_id": move_id.id,
            }
            if self.cnab_return_log_id.type == "inbound":
                company_id = self.journal_id.company_id
                account_id = company_id.account_journal_payment_credit_account_id
                credit_move_line["account_id"] = account_id.id
                debit_move_line[
                    "account_id"
                ] = self.journal_id.inbound_discount_account_id.id
            else:
                credit_move_line[
                    "account_id"
                ] = self.journal_id.outbound_discount_account_id.id
                debit_move_line[
                    "account_id"
                ] = self.journal_id.company_id.account_journal_payment_debit_account_id

            move_line_obj.with_context(check_move_validity=False).create(
                [credit_move_line, debit_move_line]
            )

    def _create_fees_move_lines(self, move_id):
        if self.interest_fee_value <= 0:
            return  # skip

        move_line_obj = self.env["account.move.line"]
        credit_move_line = {
            "name": "Interest and Fees: " + self.your_number,
            "credit": self.interest_fee_value,
            "partner_id": self.move_line_ids[0].partner_id.id,
            "move_id": move_id.id,
        }
        debit_move_line = {
            "name": "Interest and Fees: " + self.your_number,
            "debit": self.interest_fee_value,
            "partner_id": self.move_line_ids[0].partner_id.id,
            "move_id": move_id.id,
        }
        if self.cnab_return_log_id.type == "inbound":
            credit_move_line[
                "account_id"
            ] = self.journal_id.inbound_interest_fee_account_id.id
            debit_move_line[
                "account_id"
            ] = self.journal_id.company_id.account_journal_payment_debit_account_id
        else:
            credit_move_line[
                "account_id"
            ] = self.journal_id.company_id.account_journal_payment_credit_account_id.id
            debit_move_line[
                "account_id"
            ] = self.journal_id.outbound_interest_fee_account_id.id

        move_line_obj.with_context(check_move_validity=False).create(
            [credit_move_line, debit_move_line]
        )

    def create_liq_move(self):
        move_obj = self.env["account.move"]
        move_vals = self._get_liq_move_vals()
        move_id = move_obj.create(move_vals)
        to_reconcile_items = self._get_reconciliation_items(move_id)
        self._create_rebate_move_lines(move_id)
        self._create_discount_move_lines(move_id)
        self._create_fees_move_lines(move_id)
        self._create_tariff_move_lines(move_id)
        move_id.action_post()
        self.generated_move_id = move_id
        for to_reconcile in to_reconcile_items:
            to_reconcile.reconcile()

    def action_ignore_event(self):
        self.write({"state": "ignored"})
