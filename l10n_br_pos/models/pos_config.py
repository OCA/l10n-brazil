# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

PRINTER = [
    ("epson-tm-t20", "Epson TM-T20"),
    ("bematech-mp4200th", "Bematech MP4200TH"),
    ("daruma-dr700", "Daruma DR700"),
    ("elgin-i9", "Elgin I9"),
]

SIMPLIFIED_INVOICE_TYPE = [
    ("nfce", "NFC-E"),
    ("sat", "SAT"),
    ("paf", "PAF-ECF"),
]


class PosConfig(models.Model):
    _inherit = "pos.config"

    @api.depends("out_pos_fiscal_operation_id")
    def _compute_allowed_tax(self):
        for record in self:
            record.cfop_ids = record.cfop_ids.search([("is_pos", "=", True)])
            if record.cfop_ids and record.out_pos_fiscal_operation_id:
                record.out_pos_fiscal_operation_line_ids = (
                    record.out_pos_fiscal_operation_id.line_ids.filtered(
                        lambda x, record=record: x.cfop_internal_id in record.cfop_ids
                    )
                )
            else:
                record.out_pos_fiscal_operation_line_ids = False

    out_pos_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Default Sales Operation",
        default=lambda self: self.env.company.out_pos_fiscal_operation_id,
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
    )
    # TODO: This can be a one2many

    cfop_ids = fields.One2many(
        string="Allowed CFOPs",
        comodel_name="l10n_br_fiscal.cfop",
        compute="_compute_allowed_tax",
        readonly=True,
    )

    out_pos_fiscal_operation_line_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Sales Operation Lines",
        compute="_compute_allowed_tax",
        readonly=True,
    )

    refund_pos_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Default Return Operation",
        default=lambda self: self.env.company.refund_pos_fiscal_operation_id,
    )

    anonymous_simplified_limit = fields.Float(
        digits="Account",
        help="Over this amount is not legally posible to create a Anonymous "
        "NFC-E / CF-e",
        default=10000,
    )

    simplified_invoice_limit = fields.Float(
        digits="Account",
        help="Over this amount is not legally posible to create a simplified invoice",
        default=200000,
    )

    simplified_document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
    )

    simplified_document_type = fields.Char(
        related="simplified_document_type_id.code",
        string="Simplified document type",
        store=True,
    )

    detailed_document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
    )

    detailed_document_type = fields.Char(
        related="detailed_document_type_id.code",
        string="Detailed document type",
        store=True,
    )

    iface_fiscal_via_proxy = fields.Boolean(
        string="Fiscal via IOT",
    )

    iface_nfce_via_proxy = fields.Boolean(
        string="NFC-e via IOT",
        help="""NFC-E can be issued by cloud or IoT, not requiring Odoo server
        to be turned on""",
    )

    certificate_nfe_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.certificate",
        string="Digital certificate",
    )

    # SAT OPTIONS
    # TODO: Rename field

    sat_environment = fields.Selection(
        string="SAT environment", related="company_id.environment_sat", store=True
    )

    cnpj_homologation = fields.Char(string="CNPJ homologation", size=18)

    ie_homologation = fields.Char(string="IE homologation", size=16)

    cnpj_software_house = fields.Char(string="CNPJ software house", size=18)

    sat_path = fields.Char(string="SAT path")

    # TODO: Can we use pos.config ID?
    cashier_number = fields.Integer(string="Cashier Number", copy=False)

    activation_code = fields.Char(
        string="Activation code",
    )

    signature_sat = fields.Char("Signature in CFe")

    # Printer settings, can we use just ESC-POS protocol??
    # These are SAT print parameters

    printer = fields.Selection(
        selection=PRINTER,
    )

    fiscal_printer_type = fields.Selection(
        selection=[
            ("BluetoothConnection", "Bluetooth"),
            ("DummyConnection", "Dummy"),
            ("FileConnection", "File"),
            ("NetworkConnection", "Network"),
            ("SerialConnection", "Serial"),
            ("USBConnection", "USB"),
            ("CupsConnection", "Cups"),
        ],
    )

    printer_params = fields.Char(string="Printer parameters")

    session_sat = fields.Integer(string="Last Session Value", default=1)

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
        for record in self:
            product_tmpl_ids = self.env["product.template"].search(
                [("available_in_pos", "=", True)]
            )

            pos_fiscal_map_ids = record.pos_fiscal_map_ids.search(
                [("pos_config_id", "=", record.id)]
            )
            pos_fiscal_map_ids.unlink()

            for product in product_tmpl_ids:
                product.update_pos_fiscal_map()

    @api.model
    def update_session_sat(self, config_id):
        config = self.browse(config_id)
        config.session_sat += 1
