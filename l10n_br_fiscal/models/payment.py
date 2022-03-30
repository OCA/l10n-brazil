# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class FiscalPayment(models.Model):
    _name = "l10n_br_fiscal.payment"
    _description = "Fiscal Payment"

    name = fields.Char(string="Name", required=True)

    indPag = fields.Selection(
        selection=[
            ("0", "Pagamento à Vista"),
            ("1", "Pagamento à Prazo"),
            ("2", "Outros"),
        ],
        string="Indicador de Pagamento",
        default="1",
    )

    payment_type = fields.Selection(
        selection=[
            ("01", "01 - Dinheiro"),
            ("02", "02 - Cheque"),
            ("03", "03 - Cartão de Crédito"),
            ("04", "04 - Cartão de Débito"),
            ("06", "05 - Crédito Loja"),
            ("10", "10 - Vale Alimentação"),
            ("11", "11 - Vale Refeição"),
            ("12", "12 - Vale Presente"),
            ("13", "13 - Vale Combustível"),
            ("14", "14 - Duplicata Mercantil"),
            ("15", "15 - Boleto Bancário"),
            ("90", "90 - Sem pagamento"),
            ("99", "99 - Outros"),
        ],
        string="Tipo de Pagamento da NF",
        required=True,
        default="99",
        help="Obrigatório o preenchimento do Grupo Informações de Pagamento"
        " para NF-e e NFC-e. Para as notas com finalidade de Ajuste"
        " ou Devolução o campo Forma de Pagamento deve ser preenchido"
        " com 90 - Sem Pagamento.",
    )
