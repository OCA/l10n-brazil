# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from unidecode import unidecode

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_account_payment_order.constants import TIPO_SERVICO


class AccountPaymentLine(models.Model):
    """
    Override Payment Line
    for add Help Functions for CNAB implementation.
    """

    _inherit = "account.payment.line"

    cnab_pix_type_id = fields.Many2one(
        comodel_name="cnab.pix.key.type",
        compute="_compute_cnab_pix_type_id",
        store=False,
    )

    cnab_beneficiary_name = fields.Char(
        compute="_compute_cnab_beneficiary_name",
        help="Name of the beneficiary (Nome do Favorecido) that will be informed"
        " in the CNAB.",
    )

    cnab_pix_transfer_type_id = fields.Many2one(
        comodel_name="cnab.pix.transfer.type",
        compute="_compute_cnab_pix_transfer_type_id",
        store=False,
    )

    cnab_payment_way_id = fields.Many2one(
        comodel_name="cnab.payment.way",
        compute="_compute_cnab_payment_way_id",
    )

    batch_template_id = fields.Many2one(
        comodel_name="l10n_br_cnab.batch",
        compute="_compute_batch_template_id",
    )

    service_type = fields.Selection(
        selection=TIPO_SERVICO,
        compute="_compute_cnab_payment_way_id",
        store=True,
    )

    @api.depends("partner_pix_id")
    def _compute_cnab_pix_type_id(self):
        for bline in self:
            cnab_pix_type_id = (
                bline.order_id.cnab_structure_id.cnab_pix_key_type_ids.filtered(
                    lambda t, b=bline: t.key_type == b.partner_pix_id.key_type
                )
            )
            self.cnab_pix_type_id = cnab_pix_type_id

    @api.depends("pix_transfer_type")
    def _compute_cnab_pix_transfer_type_id(self):
        for bline in self:
            if bline.payment_mode_domain == "pix_transfer":
                cnab_pix_transfer_type = self.env["cnab.pix.transfer.type"].search(
                    [
                        ("cnab_structure_id", "=", bline.order_id.cnab_structure_id.id),
                        ("type_domain", "=", bline.pix_transfer_type),
                    ],
                    limit=1,
                )
                bline.cnab_pix_transfer_type_id = cnab_pix_transfer_type
            else:
                bline.cnab_pix_transfer_type_id = False

    def _compute_cnab_beneficiary_name(self):
        for bline in self:
            if bline.partner_bank_id and bline.partner_bank_id.acc_holder_name:
                bline.cnab_beneficiary_name = unidecode(
                    bline.partner_bank_id.acc_holder_name
                ).strip()
            else:
                bline.cnab_beneficiary_name = unidecode(bline.partner_id.name).strip()

    def _compute_batch_template_id(self):
        for bline in self:
            if not bline.cnab_payment_way_id.batch_id:
                raise UserError(_("Mapping for batch template not found"))
            bline.batch_template_id = bline.cnab_payment_way_id.batch_id

    @api.depends("payment_mode_id", "partner_id", "partner_bank_id")
    def _compute_cnab_payment_way_id(self):
        for line in self:
            mode = line.order_id.payment_mode_id
            cnab_structure = line.order_id.cnab_structure_id
            rule = line._get_matching_rule()

            if rule:
                line.cnab_payment_way_id = rule.payment_way_id
                line.service_type = rule.service_type
            else:
                ways = mode.cnab_payment_way_ids.filtered(
                    lambda w, s=cnab_structure: w.cnab_structure_id == s
                )
                if ways:
                    line.cnab_payment_way_id = ways[0]
                    line.service_type = "20"
                else:
                    line.cnab_payment_way_id = False
                    line.service_type = False
                    if mode.cnab_structure_ok:
                        raise UserError(
                            _(
                                "CNAB payment way not found.\n"
                                "Payment Mode: %(payment_mode)s\n"
                                "CNAB Structure: %(cnab_structure)s"
                            )
                            % {
                                "payment_mode": mode.name,
                                "cnab_structure": cnab_structure.name,
                            }
                        )

    def _get_matching_rule(self):
        """Finds the best matching CNAB rule based on bank and partner attributes."""
        self.ensure_one()
        cnab_structure = self.order_id.cnab_structure_id
        if self.partner_bank_id.bank_id == self.order_id.journal_id.bank_id:
            bank_type = "same"
        else:
            bank_type = "other"
        is_employee = getattr(self.partner_id, "employee", False)
        if is_employee:
            partner_type = "employee"
        else:
            partner_type = "supplier"
        rules = self.env["l10n_br_cnab.payment.rule"].search(
            [
                ("cnab_structure_id", "=", cnab_structure.id),
            ]
        )
        for rule in rules:
            if rule.match_bank_type != "any" and rule.match_bank_type != bank_type:
                continue
            if (
                rule.match_partner_type != "any"
                and rule.match_partner_type != partner_type
            ):
                continue
            return rule
        return False

    def _compute_cnab_payment_way_id(self):
        for line in self:
            mode = line.order_id.payment_mode_id
            cnab_structure = line.order_id.cnab_structure_id

            rule = line._get_matching_rule()

            if rule:
                line.cnab_payment_way_id = rule.payment_way_id
                line.service_type = rule.service_type
            else:
                ways = mode.cnab_payment_way_ids.filtered(
                    lambda w, s=cnab_structure: w.cnab_structure_id == s
                )

                if ways:
                    line.cnab_payment_way_id = ways[0]
                else:
                    line.cnab_payment_way_id = False
                    raise UserError(
                        _(
                            "CNAB payment way not found.\n"
                            "Payment Mode: %(payment_mode)s\n"
                            "CNAB Structure: %(cnab_structure)s"
                        )
                        % {
                            "payment_mode": mode.name,
                            "cnab_structure": cnab_structure.name,
                        }
                    )
