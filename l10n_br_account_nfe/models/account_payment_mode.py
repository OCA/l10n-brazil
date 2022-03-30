# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# Copyright (C) 2022-Today - Akretion (<https://akretion.com/pt-BR>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    fiscal_payment_mode = fields.Selection(
        selection=[
            ("01", "01 - Dinheiro"),
            ("02", "02 - Cheque"),
            ("03", "03 - Cartão de Crédito"),
            ("04", "04 - Cartão de Débito"),
            ("05", "05 - Crédito de Loja"),
            ("10", "10 - Vale Alimentação"),
            ("11", "11 - Vale Refeição"),
            ("12", "12 - Vale Presente"),
            ("13", "13 - Vale Combustível"),
            ("14", "14 - Duplicata Mercanti"),
            ("15", "15 - Boleto Bancário"),
            ("16", "16 - Depósito Bancário"),
            ("17", "17 - Pagamento Instantâneo (PIX)"),
            ("18", "18 - Transferência bancária, Carteira Digital"),
            ("19", "19 - Programa de fidelidade, Cashback, Crédito Virtual"),
            ("90", "90 - Sem Pagamento"),
            ("99", "99 - Outros"),
        ],
        string="Meio de Pagamento da NF",
        help="Obrigatório o preenchimento do Grupo Informações de Pagamento"
        " para NF-e e NFC-e. Para as notas com finalidade de Ajuste"
        " ou Devolução o campo Forma de Pagamento deve ser preenchido"
        " com 90 - Sem Pagamento.",
    )
