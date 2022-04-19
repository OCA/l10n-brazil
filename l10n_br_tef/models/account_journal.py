from odoo import fields, models

WA03_CMP_MP = [
    ("01", "Cartão Crédito"),
    ("02", "Cartão Débito"),
]


class AccountJournal(models.Model):
    _inherit = "account.journal"

    tef_payment_mode = fields.Selection(WA03_CMP_MP, "Modo de Pagamento TEF")
