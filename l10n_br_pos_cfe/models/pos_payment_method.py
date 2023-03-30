# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br) - Fernando Marcato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

WA03_CMP_MP = [
    ("01", "Dinheiro"),
    ("02", "Cheque"),
    ("03", "Cartão Crédito"),
    ("04", "Cartão Débito"),
    ("05", "Crédito Loja"),
    ("10", "Vale Alimentação"),
    ("11", "Vale Refeição"),
    ("12", "Vale Presente"),
    ("13", "Vale Combustível"),
    ("99", "Outros"),
]


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    sat_payment_mode = fields.Selection(WA03_CMP_MP, "SAT Payment Mode")
