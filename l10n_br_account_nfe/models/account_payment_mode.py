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
