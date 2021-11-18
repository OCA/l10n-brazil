# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CFOP(models.Model):
    _inherit = "l10n_br_fiscal.cfop"

    is_pos = fields.Boolean(
        string="Permitida no POS",
        help="""Marque esta seleção para que a CFOP possa ser utililizada no
        Ponto de Venda""",
    )
