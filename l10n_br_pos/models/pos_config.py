# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    @api.depends("cfop_ids", "out_pos_fiscal_operation_id")
    def _compute_allowed_tax(self):
        self._compute_cfop_ids()
        self._compute_out_fiscal_operation_line_ids()

    def _compute_cfop_ids(self):
        self.cfop_ids = self.env["l10n_br_fiscal.cfop"].search([("is_pos", "=", True)])

    def _compute_out_fiscal_operation_line_ids(self):
        if self.cfop_ids and self.out_pos_fiscal_operation_id:
            self.out_pos_fiscal_operation_line_ids = (
                self.out_pos_fiscal_operation_id.line_ids.filtered(
                    lambda line: line.cfop_internal_id in self.cfop_ids
                )
            )
        else:
            self.out_pos_fiscal_operation_line_ids = False

    iface_brazilian_taxes = fields.Boolean(
        string="Brazilian Taxes",
        help="Activating will enable brazilian taxes calculation on POS",
        default=False,
    )

    partner_id = fields.Many2one(
        string="Default Partner",
        comodel_name="res.partner",
        help="Partner to be used in POS transactions as default.",
    )
    # TODO: This can be a one2many

    cfop_ids = fields.One2many(
        string="Allowed CFOP's",
        comodel_name="l10n_br_fiscal.cfop",
        compute="_compute_allowed_tax",
        readonly=True,
        help="CFOP's allowed to be used in this POS.",
    )

    out_pos_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Default Sales Operation",
        default=lambda self: self.env.company.pos_out_fiscal_operation_id,
        help="Default operation to be used in sales transactions in this POS.",
    )

    out_pos_fiscal_operation_line_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Sales Operation Lines",
        compute="_compute_allowed_tax",
        readonly=True,
        help="Default operation lines to be used in sales transactions in this POS.",
    )

    refund_pos_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Default Return Operation",
        default=lambda self: self.env.company.refund_pos_fiscal_operation_id,
        help="Default operation to be used in return transactions in this POS.",
    )

    simplified_invoice_amount_limit = fields.Float(
        digits="Account",
        help="""Over this amount is not legally possible to create a simplified
            invoice for CF-e or NFC-e operations.""",
    )

    simplified_document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
    )

    detailed_document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
    )

    iface_fiscal_via_proxy = fields.Boolean(
        string="Fiscal via IOT",
    )

    save_identity_automatic = fields.Boolean(
        string="Save new client",
        help="Activating will create a new identity customer to the partners data",
        default=False,
    )

    ask_identity = fields.Boolean(string="Ask Identity on Payment", default=False)

    additional_data = fields.Text(
        string="Aditional Information",
    )

    pos_fiscal_map_ids = fields.One2many(
        comodel_name="l10n_br_pos.product_fiscal_map",
        inverse_name="pos_config_id",
    )

    def update_pos_fiscal_map(self):
        product_tmpl_ids = self.env["product.template"].search(
            [("available_in_pos", "=", True)]
        )

        pos_fiscal_map_ids = self.pos_fiscal_map_ids.filtered(
            lambda map_id: map_id.pos_config_id.id == self.id
        )
        pos_fiscal_map_ids.unlink()

        self._update_product_pos_fiscal_map(product_tmpl_ids)

    def _update_product_pos_fiscal_map(self, product_tmpl_ids):
        for product in product_tmpl_ids:
            product.update_pos_fiscal_map()
