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
        compute="_compute_service_type",
        store=True,
        readonly=False,
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

    def _get_cnab_payment_way_and_service_type(self):
        """Payment way and service type (G025) of the line.

        A matching payment rule wins; otherwise the first payment way of the
        payment mode for the CNAB structure is used with service type 20.
        """
        self.ensure_one()
        rule = self._get_matching_rule()
        if rule:
            return rule.payment_way_id, rule.service_type
        ways = self.order_id.payment_mode_id.cnab_payment_way_ids.filtered(
            lambda w, s=self.order_id.cnab_structure_id: w.cnab_structure_id == s
        )
        if ways:
            return ways[0], "20"
        return self.env["cnab.payment.way"], False

    @api.depends("payment_mode_id", "partner_id", "partner_bank_id")
    def _compute_cnab_payment_way_id(self):
        for line in self:
            payment_way = line._get_cnab_payment_way_and_service_type()[0]
            line.cnab_payment_way_id = payment_way
            mode = line.order_id.payment_mode_id
            if not payment_way and mode.cnab_structure_ok:
                raise UserError(
                    _(
                        "CNAB payment way not found.\n"
                        "Payment Mode: %(payment_mode)s\n"
                        "CNAB Structure: %(cnab_structure)s"
                    )
                    % {
                        "payment_mode": mode.name,
                        "cnab_structure": line.order_id.cnab_structure_id.name,
                    }
                )

    @api.depends("payment_mode_id", "partner_id", "partner_bank_id")
    def _compute_service_type(self):
        for line in self:
            line.service_type = line._get_cnab_payment_way_and_service_type()[1]

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
