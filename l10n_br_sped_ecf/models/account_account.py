# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models

# Correspondencia USUAL entre a linha do P200 (presuncao do IRPJ) e a linha do
# P400 (presuncao da CSLL) para a mesma natureza de receita. Comercio,
# industria e transporte de carga presumem 8% para o IRPJ e 12% para a CSLL;
# servicos em geral presumem 32% nos dois; combustiveis, 1,6% e 12%. E um
# DEFAULT, nao uma regra: a presuncao da CSLL nao deriva da do IRPJ. O caso
# que separa as duas e o servico com IRPJ a 16% (art. 40 da Lei 9.250/1995,
# receita bruta anual ate 120 mil): a reducao e SO do IRPJ, e a CSLL segue a
# 32%; ja o transporte de passageiros (art. 15, par. 1, II da Lei 9.249/1995)
# tambem presume 16% no IRPJ, mas com CSLL a 12%. Por isso a conta tem o campo
# proprio l10n_br_ecf_csll_line, que prevalece sobre este de-para.
LINHA_CSLL_POR_LINHA_IRPJ = {
    "2": "2",
    "4": "2",
    "6": "2",
    "8": "4",
    "9": "5",
}


class AccountAccount(models.Model):
    _inherit = "account.account"

    l10n_br_ecf_revenue_line = fields.Selection(
        selection=[
            ("2", "Receita bruta sujeita ao percentual de 1,6%"),
            ("4", "Receita bruta sujeita ao percentual de 8%"),
            ("6", "Receita bruta sujeita ao percentual de 16%"),
            ("8", "Receita bruta sujeita ao percentual de 32%"),
            ("9", "Receita bruta sujeita ao percentual de 38,4%"),
            ("11", "Rendimentos e ganhos liquidos de aplicacoes financeiras"),
            ("12", "Juros sobre o capital proprio"),
            ("14", "Recuperacao de custos e despesas"),
            ("16", "Multas e vantagens por rescisao contratual"),
            ("20", "Demais receitas e ganhos de capital"),
        ],
        string="Natureza da receita na ECF",
        help="Linha do registro P200 da ECF em que a receita desta conta e "
        "apurada, no lucro presumido. As cinco primeiras opcoes sao a receita "
        "bruta, que entra na base pelo percentual de presuncao; as demais "
        "entram integralmente. Conta de receita sem classificacao entra em "
        "'Demais receitas e ganhos de capital', que e o tratamento mais "
        "oneroso, e a apuracao registra o aviso no chatter da declaracao.",
    )
    l10n_br_ecf_csll_line = fields.Selection(
        selection=[
            ("2", "Receita bruta sujeita ao percentual de 12%"),
            ("4", "Receita bruta sujeita ao percentual de 32%"),
            ("5", "Receita bruta sujeita ao percentual de 38,4%"),
        ],
        string="Presuncao da CSLL na ECF",
        help="Linha do registro P400 da ECF em que a receita desta conta "
        "entra na base da CSLL. Em branco, vale a correspondencia usual com a "
        "linha do IRPJ (8% -> 12%, 32% -> 32%). Preencha quando as presuncoes "
        "divergem: o servico com IRPJ reduzido a 16% (art. 40 da Lei "
        "9.250/1995, receita bruta anual ate 120 mil) mantem a CSLL a 32%, "
        "enquanto o transporte de passageiros, tambem a 16% no IRPJ, tem a "
        "CSLL a 12%.",
    )
    l10n_br_ecf_withholding_line = fields.Selection(
        selection=[
            ("P300-10", "IRPJ retido na fonte"),
            (
                "P300-12",
                "IRPJ retido por orgaos, autarquias e fundacoes federais",
            ),
            (
                "P300-13",
                "IRPJ retido pelas demais entidades da administracao federal",
            ),
            ("P300-14", "IRPJ pago sobre ganhos no mercado de renda variavel"),
            (
                "P500-11",
                "CSLL retida por pessoa juridica de direito privado",
            ),
            (
                "P500-9",
                "CSLL retida por orgaos, autarquias e fundacoes federais",
            ),
            (
                "P500-10",
                "CSLL retida pelas demais entidades da administracao federal",
            ),
            (
                "P500-12",
                "CSLL retida por orgaos de estados, DF e municipios",
            ),
        ],
        string="Retencao na fonte na ECF",
        help="Linha dos registros P300 (IRPJ) e P500 (CSLL) em que o saldo "
        "desta conta e deduzido do imposto devido. Classifique aqui as contas "
        "de imposto retido a compensar. A linha depende de QUEM reteve, e nao "
        "so do imposto: retencao por pessoa juridica de direito privado, por "
        "orgao federal e por orgao estadual ou municipal vao para linhas "
        "diferentes. Quem atende a administracao publica precisa das contas "
        "segregadas no plano para escriturar corretamente.",
    )
