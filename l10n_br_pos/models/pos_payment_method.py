# © 2024 KMEE INFORMATICA LTDA (https://kmee.com.br) - Fernando Marcato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    edoc_payment_method = fields.Selection(
        string="eDoc Payment Method",
        selection=[
            ("01", "01 - Dinheiro"),
            ("02", "02 - Cheque"),
            ("03", "03 - Cartão de Crédito"),
            ("04", "04 - Cartão de Débito"),
            ("05", "05 - Crédito Loja"),
            ("10", "10 - Vale Alimentação"),
            ("11", "11 - Vale Refeição"),
            ("12", "12 - Vale Presente"),
            ("13", "13 - Vale Combustível"),
            ("90", "90 - Sem Pagamento"),
            ("99", "99 - Others"),
        ],
        required=True,
        default="90",
        delete="oncascade",
    )
