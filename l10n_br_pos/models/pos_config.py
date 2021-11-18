# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

from odoo.addons import decimal_precision as dp

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

    @api.model
    def _default_out_pos_fiscal_operation_id(self):
        return self.company_id.out_pos_fiscal_operation_id

    @api.model
    def _default_refund_pos_fiscal_operation_id(self):
        return self.company_id.refund_pos_fiscal_operation_id

    @api.depends("out_pos_fiscal_operation_id")
    def _compute_allowed_tax(self):
        for record in self:
            record.cfop_ids = record.cfop_ids.search([("is_pos", "=", True)])
            if record.cfop_ids and record.out_pos_fiscal_operation_id:
                record.out_pos_fiscal_operation_line_ids = (
                    record.out_pos_fiscal_operation_id.line_ids.filtered(
                        lambda x: x.cfop_internal_id in record.cfop_ids
                    )
                )

    out_pos_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Operação Padrão de Venda",
        # domain="[('journal_type','=','sale'), ('state', '=', 'approved'),"
        # " ('fiscal_type','=','product'), ('type','=','output')]",
        default=_default_out_pos_fiscal_operation_id,
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
    )
    # TODO: Isso pode ser uma one2many

    cfop_ids = fields.One2many(
        string="CFOPs permitidas",
        comodel_name="l10n_br_fiscal.cfop",
        compute="_compute_allowed_tax",
        readonly=True,
    )

    out_pos_fiscal_operation_line_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Linhas de Operação de Venda",
        compute="_compute_allowed_tax",
        readonly=True,
    )

    refund_pos_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Operação Padrão de Devolução",
        # domain="[('journal_type','=','sale_refund'),"
        # "('state', '=', 'approved'), ('fiscal_type','=','product'),"
        # " ('type','=','input')]",
        default=_default_refund_pos_fiscal_operation_id,
    )

    anonymous_simplified_limit = fields.Float(
        string="Anonymous simplified limit",
        digits=dp.get_precision("Account"),
        help="Over this amount is not legally posible to create a Anonymous NFC-E / CF-e",
        default=10000,
    )

    simplified_invoice_limit = fields.Float(
        string="Simplified invoice limit",
        digits=dp.get_precision("Account"),
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
        help="""A NFC-E pode ser emitida pela nuvem ou pelo IOT,
             não exigindo que o servidor Odoo esteja ligado""",
    )

    certificate_nfe_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.certificate",
        string="Certificado Digital",
    )

    # SAT OPTIONS
    # TODO: Rename field

    sat_ambiente = fields.Selection(
        string="Ambiente SAT", related="company_id.ambiente_sat", store=True
    )

    cnpj_homologacao = fields.Char(string="CNPJ homologação", size=18)

    ie_homologacao = fields.Char(string="IE homologação", size=16)

    cnpj_software_house = fields.Char(string="CNPJ software house", size=18)

    sat_path = fields.Char(string="SAT path")

    # TODO: Podemos usar o ID do pos.config?
    numero_caixa = fields.Integer(string="Número do Caixa", copy=False)

    cod_ativacao = fields.Char(
        string="Código de ativação",
    )

    assinatura_sat = fields.Char("Assinatura no CFe")

    # Printer settings, será que podemos usar somente o protocolo ESC-POS?
    # Esses são parametros da impressão SAT

    impressora = fields.Selection(
        selection=PRINTER,
        string="Impressora",
    )

    fiscal_printer_type = fields.Selection(
        selection=[
            ("BluetoothConnection", "Bluetooth"),
            ("DummyConnection", "Dummy"),
            ("FileConnection", "File"),
            ("NetworkConnection", "Network"),
            ("SerialConnection", "Serial"),
            ("USBConnection", "USB"),
        ],
    )

    printer_params = fields.Char(string="Printer parameters")

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
            record.pos_fiscal_map_ids.unlink()
            for product in product_tmpl_ids:
                product.with_delay().update_pos_fiscal_map()

    # lim_data_alteracao = fields.Integer(
    #     string="Atualizar dados (meses)",
    #     default=3,
    # )
    #
    # crm_ativo = fields.Boolean(
    #     string='CRM ativo?',
    #     default=False,
    # )
    #

    # @api.multi
    # def retornar_dados(self):
    #     if self.ambiente_sat == 'homologacao':
    #         return (self.cnpj_fabricante,
    #                 self.ie_fabricante,
    #                 self.cnpj_software_house)
    #     else:
    #         return (self.company_id.cnpj_cpf,
    #                 self.company_id.inscr_est,
    #                 self.cnpj_software_house or
    #                 self.company_id.cnpj_software_house)
