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

CARD_ACQUIRERS = [
    # Código da credenciadora, CNPJ e Nome
    ("001", "03.106.213/0001-90 Administradora de Cartões Sicredi Ltda."),
    ("002", "03.106.213/0002-71 Administradora de Cartões Sicredi Ltda.(filial RS)"),
    ("003", "60.419.645/0001-95 Banco American Express S/A - AMEX"),
    ("004", "62.421.979/0001-29 BANCO GE - CAPITAL"),
    ("005", "58.160.789/0001-28 BANCO SAFRA S/A"),
    ("006", "07.679.404/0001-00 BANCO TOPÁZIO S/A"),
    ("007", "17.351.180/0001-59 BANCO TRIANGULO S/A"),
    ("008", "04.627.085/0001-93 BIGCARD Adm. de Convenios e Serv."),
    ("009", "01.418.852/0001-66 BOURBON Adm. de Cartões de Crédito"),
    ("010", "03.766.873/0001-06 CABAL Brasil Ltda."),
    ("011", "03.722.919/0001-87 CETELEM Brasil S/A - CFI"),
    ("012", "01.027.058/0001-91 CIELO S/A"),
    ("013", "03.529.067/0001-06 CREDI 21 Participações Ltda."),
    ("014", "71.225.700/0001-22 ECX CARD Adm. e Processadora de Cartões S/A"),
    ("015", "03.506.307/0001-57 Empresa Bras. Tec. Adm. Conv. Hom. Ltda. - EMBRATEC"),
    ("016", "04.432.048/0001-20 EMPÓRIO CARD LTDA"),
    ("017", "07.953.674/0001-50 FREEDDOM e Tecnologia e Serviços S/A"),
    ("018", "03.322.366/0001-75 FUNCIONAL CARD LTDA."),
    ("019", "03.012.230/0001-69 HIPERCARD Banco Multiplo S/A"),
    ("020", "03.966.317/0001-75 MAPA Admin. Conv. e Cartões Ltda."),
    (
        "021",
        "00.163.051/0001-34 Novo Pag Adm. e Proc. de Meios Eletrônicos de Pagto. Ltda.",
    ),
    (
        "022",
        "43.180.355/0001-12 PERNAMBUCANAS Financiadora S/A Crédito, Fin. e Invest.",
    ),
    ("023", "00.904.951/0001-95 POLICARD Systems e Serviços Ltda."),
    ("024", "33.098.658/0001-37 PROVAR Negócios de Varejo Ltda."),
    ("025", "01.425.787/0001-04 REDECARD S/A"),
    ("026", "90.055.609/0001-50 RENNER Adm. Cartões de Crédito Ltda."),
    ("027", "03.007.699/0001-00 RP Administração de Convênios Ltda."),
    ("028", "00.122.327/0001-36 SANTINVEST S/A Crédito, Financiamento e Investimentos"),
    ("029", "69.034.668/0001-56 SODEXHO Pass do Brasil Serviços e Comércio S/A"),
    ("030", "60.114.865/0001-00 SOROCRED Meios de Pagamentos Ltda."),
    ("031", "51.427.102/0004-71 Tecnologia Bancária S/A - TECBAN"),
    ("032", "47.866.934/0001-74 TICKET Serviços S/A"),
    ("033", "00.604.122/0001-97 TRIVALE Administração Ltda."),
    ("034", "61.071.387/0001-61 Unicard Banco Múltiplo S/A - TRICARD"),
    ("999", "0 Outros"),
]


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    sat_payment_mode = fields.Selection(WA03_CMP_MP, "SAT Payment Mode")
    sat_card_acquirer = fields.Selection(CARD_ACQUIRERS, "Card Acquirer")
