# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models


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
        string="Interest and Fees Account",
        help="Interest and Fees Account for CNAB inbound payments.",
        tracking=True,
        check_company=True,
    )

    inbound_discount_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Discount Account",
        help="Discount Account for CNAB inbound payments.",
        tracking=True,
        check_company=True,
    )

    inbound_rebate_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Rebate Account",
        help="Rebate Account for CNAB inbound payments.",
        tracking=True,
        check_company=True,
    )

    outbound_interest_fee_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Interest and Fees Account",
        help="Interest and Fees Account for CNAB outbound payments.",
        tracking=True,
        check_company=True,
    )

    outbound_discount_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Discount Account",
        help="Discount Account for CNAB outbound payments.",
        tracking=True,
        check_company=True,
    )

    outbound_rebate_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Rebate Account",
        help="Rebate Account for CNAB outbound payments.",
        tracking=True,
        check_company=True,
    )
