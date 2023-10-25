# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    used_to_import_cnab = fields.Boolean(string="Journal used for import CNAB")

    tariff_charge_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Tariff Account",
        help="Default account for bank tariff.",
        tracking=True,
        check_company=True,
    )

    inbound_interest_fee_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Inbound Interest and Fees Account",
        help="Interest and Fees Account for CNAB inbound payments.",
        tracking=True,
        check_company=True,
    )

    inbound_discount_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Inbound Discount Account",
        help="Discount Account for CNAB inbound payments.",
        tracking=True,
        check_company=True,
    )

    inbound_rebate_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Inbound Rebate Account",
        help="Rebate Account for CNAB inbound payments.",
        tracking=True,
        check_company=True,
    )

    outbound_interest_fee_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Outbound Interest and Fees Account",
        help="Interest and Fees Account for CNAB outbound payments.",
        tracking=True,
        check_company=True,
    )

    outbound_discount_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Outbound Discount Account",
        help="Discount Account for CNAB outbound payments.",
        tracking=True,
        check_company=True,
    )

    outbound_rebate_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Outbound Rebate Account",
        help="Rebate Account for CNAB outbound payments.",
        tracking=True,
        check_company=True,
    )

    default_outbound_cnab_processor = fields.Selection(
        selection=[("oca_processor", "OCA Processor")],
        string="CNAB Processor",
        help="CNAB Processor to be used in a payment order"
        " when it is not defined in the payment mode",
    )
    default_outbound_cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        string="CNAB Structure",
        help="CNAB Structure to be used in a payment order "
        "when it is not defined in the payment mode.",
    )
