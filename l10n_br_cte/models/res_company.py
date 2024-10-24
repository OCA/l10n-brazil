# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = ["res.company"]

    ##########################
    # CT-e models fields
    ##########################

    cte_default_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
        string="CT-e Default Serie",
    )

    cte_dacte_layout = fields.Selection(
        selection=[("1", "Paisagem"), ("2", "Retrato")],
        string="CT-e DACTE Layout",
        default="1",
    )

    cte_transmission = fields.Selection(
        selection=[
            ("1", "Normal"),
            ("2", "Regime Especial NFF"),
            ("4", "EPEC pela SVC"),
            ("5", "Contingência FSDA"),
            ("7", "Contingência SVC-RS"),
            ("8", "Contingência SVC-SP"),
        ],
        string="CT-e Transmission Type",
        default="1",
    )

    cte_type = fields.Selection(
        selection=[
            ("0", "CT-e Normal"),
            ("1", "CT-e de Complemento de Valores"),
            ("3", "CT-e de Substituição"),
        ],
        string="CT-e Type",
        default="0",
    )

    cte_environment = fields.Selection(
        selection=[("1", "Produção"), ("2", "Homologação")],
        string="CT-e Environment",
        default="2",
    )

    cte_version = fields.Selection(
        selection=[("3.00", "3.00"), ("4.00", "4.00")],
        string="CT-e Version",
        default="4.00",
    )

    processador_edoc = fields.Selection(
        selection_add=[("erpbrasil.edoc", "erpbrasil.edoc")],
    )

    cte_authorize_accountant_download_xml = fields.Boolean(
        string="Include Accountant Partner data in persons authorized to "
        "download CTe XML",
        default=False,
    )
