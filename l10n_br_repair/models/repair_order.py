# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RepairOrder(models.Model):
    _name = "repair.order"
    _inherit = [_name, "l10n_br_fiscal.document.mixin"]

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.repair_fiscal_operation_id

    @api.model
    def _default_copy_note(self):
        return self.env.company.copy_repair_quotation_notes

    @api.model
    def _fiscal_operation_domain(self):
        return [("state", "=", "approved")]

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    ind_pres = fields.Selection()

    copy_repair_quotation_notes = fields.Boolean(
        string="Copiar Observação no documentos fiscal",
        default=_default_copy_note,
    )

    cnpj_cpf = fields.Char(
        related="partner_id.cnpj_cpf_stripped",
    )

    legal_name = fields.Char(
        related="partner_id.legal_name",
    )

    ie = fields.Char(
        related="partner_id.l10n_br_ie_code",
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="repair_order_comment_rel",
        column1="repair_id",
        column2="comment_id",
        string="Comments",
    )

    client_order_ref = fields.Char(string="Customer Reference", copy=False)

    operation_name = fields.Char(
        copy=False,
    )

    @api.model
    def _get_fiscal_lines_field_name(self):
        return "move_ids"

    def _get_amount_lines(self):
        """Object lines used to compute fiscal amounts."""
        return self.mapped("move_ids").filtered("is_repair_line")

    def _get_product_amount_lines(self):
        return self._get_amount_lines()
