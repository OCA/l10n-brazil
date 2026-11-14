# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    environment_sat = fields.Selection(
        selection=[
            ("homologation", "Homologation"),
            ("production", "Production"),
        ],
        string="SAT environment",
        default="homologation",
    )
    cnpj_software_house = fields.Char(string="CNPJ software house", size=18)
    sign_software_house = fields.Text(
        string="Software House Signature",
    )
    out_pos_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Pos Out Fiscal Operation",
    )
    refund_pos_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Pos Refund Fiscal Operation",
    )
