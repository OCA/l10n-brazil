from odoo import _, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    iface_tef = fields.Boolean(
        string="TEF",
        help="A TEF terminal is available on the Proxy",
    )

    institution_selection = fields.Selection(
        selection=[
            ("Administradora", _("Administrator")),
            ("Estabelecimento", _("Institute")),
        ],
        string="Institution",
        help="Institution selection for installment payments",
        default="Estabelecimento",
    )

    environment_selection = fields.Selection(
        selection=[
            ("Producao", _("Production")),
            ("Homologacao", _("Homologation")),
        ],
        string="Environment",
        help="Environment Selection",
        default="Homologacao",
    )

    credit_server = fields.Char(
        string="Credit Approval Server",
        help="Which credit approval server should be used",
    )

    debit_server = fields.Char(
        string="Debit Approval Server",
        help="Which debit approval server should be used",
    )
