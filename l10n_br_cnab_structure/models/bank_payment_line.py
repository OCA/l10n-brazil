from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BankPaymentLine(models.Model):
    """
    Override bank Payment Line
    for add Help Functions for CNAB implementation.
    """

    _inherit = "bank.payment.line"

    cnab_pix_type_id = fields.Many2one(
        comodel_name="cnab.pix.key.type",
        compute="_compute_cnab_pix_type_id",
        store=False,
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

    def _compute_cnab_payment_way_id(self):
        for bline in self:
            if not bline.payment_way_id:
                raise UserError(_("Bank Payment Line without Payment Way!"))
            cnab_payment_way_id = self.env["cnab.payment.way"].search(
                [
                    ("account_payment_way_id", "=", bline.payment_way_id.id),
                    ("cnab_structure_id", "=", bline.order_id.cnab_structure_id.id),
                ],
                limit=1,
            )
            if not cnab_payment_way_id:
                raise UserError(_("Mapping for cnab payment way not found"))
            bline.cnab_payment_way_id = cnab_payment_way_id

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
            if bline.payment_way_domain == "pix_transfer":
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

    def _compute_batch_template_id(self):
        for bline in self:
            if not bline.cnab_payment_way_id.batch_id:
                raise UserError(_("Mapping for batch template not found"))
            bline.batch_template_id = bline.cnab_payment_way_id.batch_id
