# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        # The default service type of a vendor bill (20) must not override the
        # payment rule of the CNAB structure: a salary booked as a bill of the
        # employee goes out with the service type of the rule (30)
        if vals.get("service_type") and payment_order.cnab_structure_id:
            rule = self.env["l10n_br_cnab.payment.rule"]._find_matching_rule(
                payment_order.cnab_structure_id,
                self.partner_id,
                self.env["res.partner.bank"].browse(vals.get("partner_bank_id")),
                payment_order.journal_id,
            )
            if rule:
                vals["service_type"] = rule.service_type
        return vals
