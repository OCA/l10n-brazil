# Copyright 2023 Tiago Amaral <https://kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models

BAIXAS = [
    ("acertos", "Acertos"),
    ("pagodiretoaocliente", "Pago direto ao cliente"),
    ("substituicao", "Substituição"),
    ("apedidodocliente", "A pedido do cliente"),
]


class BankApiInterBaixa(models.TransientModel):
    _name = "bank.api.inter.baixa"
    _description = "Wizard to choose the reason for the dismissal."

    write_off_choice = fields.Selection(
        selection=BAIXAS,
        string="Drop Bank Slip Options",
        default="apedidodocliente",
    )

    def baixar(self):
        boleto = self.env["account.move.line"].browse(self.env.context["active_id"])
        boleto.write({"write_off_choice": self.write_off_choice})
        boleto.drop_bank_slip()
