# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    own_number_type = fields.Selection(
        selection=[
            ("0", "Sequêncial único por empresa"),
            ("1", "Numero sequêncial da Fatura"),
            ("2", "Sequêncial único por carteira"),
        ],
        string="Tipo de nosso número",
        default="1",
    )

    own_number_sequence_id = fields.Many2one(
        comodel_name="ir.sequence", string="Sequência do Nosso Número"
    )
