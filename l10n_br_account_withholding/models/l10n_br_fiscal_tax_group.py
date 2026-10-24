# Copyright 2024 Marcel Savegnago - Escodoo (https://www.escodoo.com.br)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FiscalTaxGroup(models.Model):
    _inherit = "l10n_br_fiscal.tax.group"

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Account Journal",
        company_dependent=True,
        domain="[('type', '=', 'purchase')]",
    )

    generate_wh_invoice = fields.Boolean(
        string="Generate WH Invoice",
        default=False,
        company_dependent=True,
    )

    wh_payable_account_id = fields.Many2one(
        comodel_name="account.account",
        string="WH Payable Account",
        help="Special account payable for withholding invoices",
        domain="[('account_type', 'in', ('asset_receivable', 'liability_payable'))]",
        company_dependent=True,
    )

    def _get_tax_authority_partner(self, move):
        """Return the partner that collects this tax group for a given move.

        The lookup depends on ``tax_scope``: city taxes are collected by the
        city hall of the taxable event, state taxes by the treasury of the
        state where the goods are delivered. When no specific authority is
        registered, fall back to the partner set on the tax group itself.

        :param move: the account.move that originated the tax.
        :return: a res.partner recordset, possibly empty.
        """
        self.ensure_one()
        authority = self.env["res.partner"]
        if self.tax_scope == "city":
            city = move.invoice_line_ids[:1].issqn_fg_city_id or move.partner_id.city_id
            authority = authority.search(
                [("city_id", "=", city.id), ("wh_cityhall", "=", True)], limit=1
            )
        elif self.tax_scope == "state":
            state = move.partner_shipping_id.state_id or move.partner_id.state_id
            authority = authority.search(
                [("state_id", "=", state.id), ("wh_state_treasury", "=", True)],
                limit=1,
            )
        return authority or self.partner_id
