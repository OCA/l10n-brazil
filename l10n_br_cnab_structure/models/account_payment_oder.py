from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        compute="_compute_cnab_structure_id",
    )

    @api.depends("journal_id", "payment_method_id")
    def _compute_cnab_structure_id(self):
        for order in self:
            structure_obj = self.env["l10n_br_cnab.structure"]
            structure_ids = structure_obj.search(
                [
                    ("bank_id", "=", order.journal_id.bank_id.id),
                    ("payment_method_id", "=", order.payment_method_id.id),
                    ("state", "=", "approved"),
                ]
            )
            if len(structure_ids) > 1:
                raise UserError(
                    _(
                        "More than one cnab with the state approved for bank "
                        f"{order.journal_id.bank_id.name} and payment method "
                        f"{order.payment_method_id.name}"
                    )
                )
            if not structure_ids:
                raise UserError(
                    _(
                        "Could not find a approved cnab structure for bank "
                        f"{order.journal_id.bank_id.name} and payment method "
                        f"{order.payment_method_id.name}"
                    )
                )
            order.cnab_structure_id = structure_ids[0]
