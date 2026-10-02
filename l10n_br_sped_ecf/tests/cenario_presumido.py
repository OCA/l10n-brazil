# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
"""Cenario de uma empresa do lucro presumido com escrituracao contabil.

E o caso mais comum do regime: uma empresa que revende mercadoria e presta
servico, sem atividade incentivada e sem operacao com o exterior. O mesmo
cenario alimenta o teste da escrituracao e a geracao do arquivo de exemplo
(``demo/demo_ecf.txt``), para que o exemplo do modulo seja sempre um arquivo
que a propria escrituracao produz.

Os codigos do plano de contas referencial sao os do pacote oficial de tabelas
dinamicas do Sped (abas P100A e P150A).
"""

from datetime import date

# Ano-calendario coerente com o leiaute 9 implementado pelo spec do modulo.
ANO = 2022

# Grupos sinteticos do plano do contribuinte. A Resolucao CFC 1299/2010 exige
# no minimo quatro niveis, e o PVA critica a conta analitica de nivel menor:
# tres grupos mais a conta dao os quatro.
GRUPOS = [
    ("1", "ATIVO", None),
    ("1.01", "ATIVO CIRCULANTE", "1"),
    ("1.01.01", "DISPONIBILIDADES", "1.01"),
    ("1.01.02", "CREDITOS", "1.01"),
    ("1.01.03", "ESTOQUES", "1.01"),
    ("2", "PASSIVO", None),
    ("2.01", "PASSIVO CIRCULANTE", "2"),
    ("2.01.01", "FORNECEDORES", "2.01"),
    ("2.01.02", "OBRIGACOES FISCAIS", "2.01"),
    ("2.03", "PATRIMONIO LIQUIDO", "2"),
    ("2.03.01", "CAPITAL SOCIAL", "2.03"),
    ("2.03.02", "LUCROS ACUMULADOS", "2.03"),
    ("3", "RECEITAS", None),
    ("3.01", "RECEITA OPERACIONAL", "3"),
    ("3.01.01", "RECEITA BRUTA", "3.01"),
    ("3.01.02", "OUTRAS RECEITAS", "3.01"),
    ("4", "CUSTOS E DESPESAS", None),
    ("4.01", "CUSTOS E DESPESAS OPERACIONAIS", "4"),
    ("4.01.01", "CUSTO DAS MERCADORIAS", "4.01"),
    ("4.01.02", "DESPESAS OPERACIONAIS", "4.01"),
]

# (codigo, nome, tipo do Odoo, conta referencial da RFB, linha do P200,
#  linha da retencao no P300/P500)
PLANO = [
    (
        "1.01.01.01",
        "Bancos Conta Movimento",
        "asset_cash",
        "1.01.01.02.01",
        False,
        False,
    ),
    (
        "1.01.02.01",
        "Duplicatas a Receber",
        "asset_receivable",
        "1.01.02.02.01",
        False,
        False,
    ),
    (
        "1.01.03.01",
        "Mercadorias para Revenda",
        "asset_current",
        "1.01.03.01.01",
        False,
        False,
    ),
    ("2.01.01.01", "Fornecedores", "liability_payable", "2.01.01.03.01", False, False),
    (
        "2.01.02.01",
        "IRPJ a Recolher",
        "liability_current",
        "2.01.01.09.13",
        False,
        False,
    ),
    (
        "2.01.02.02",
        "CSLL a Recolher",
        "liability_current",
        "2.01.01.09.14",
        False,
        False,
    ),
    ("2.03.01.01", "Capital Social", "equity", "2.03.01.01.01", False, False),
    ("2.03.02.01", "Lucros Acumulados", "equity", "2.03.04.01.01", False, False),
    ("3.01.01.01", "Receita de Revenda", "income", "3.01.01.01.01.05", "4", False),
    ("3.01.01.02", "Receita de Servicos", "income", "3.01.01.01.01.06", "8", False),
    (
        "3.01.02.01",
        "Rendimentos de Aplicacoes",
        "income",
        "3.01.01.05.01.05",
        "11",
        False,
    ),
    (
        "4.01.01.01",
        "Custo das Mercadorias",
        "expense",
        "3.01.01.03.01.02",
        False,
        False,
    ),
    (
        "4.01.02.01",
        "Despesas Operacionais",
        "expense",
        "3.01.01.09.01.99",
        False,
        False,
    ),
    # o prestador de servico sofre IRRF de 1,5% e CSRF de 1% do tomador:
    # a retencao e um credito a compensar, e o de-para diz em que linha
    # do P300 e do P500 ela e deduzida do imposto devido
    (
        "1.01.04.01",
        "IRRF a Compensar",
        "asset_current",
        "1.01.02.04.01",
        False,
        "P300-10",
    ),
    (
        "1.01.04.02",
        "CSLL Retida a Compensar",
        "asset_current",
        "1.01.02.04.04",
        False,
        "P500-11",
    ),
]

# Movimento de cada trimestre: revenda, servicos, rendimentos financeiros,
# custo da revenda e despesas operacionais.
MOVIMENTO = {
    1: (300000.00, 120000.00, 4000.00, 180000.00, 60000.00),
    2: (360000.00, 150000.00, 5000.00, 210000.00, 70000.00),
    3: (420000.00, 180000.00, 6000.00, 250000.00, 80000.00),
    4: (500000.00, 200000.00, 7000.00, 300000.00, 90000.00),
}

# Retencao na fonte que o tomador faz sobre o servico prestado:
# IRRF de 1,5% (Lei 7.450/1985, art. 52) e CSLL de 1% dentro da CSRF de
# 4,65% (Lei 10.833/2003, art. 30).
ALIQUOTA_IRRF_SERVICO = 0.015
ALIQUOTA_CSLL_RETIDA_SERVICO = 0.01

ULTIMO_MES_DO_TRIMESTRE = {1: 3, 2: 6, 3: 9, 4: 12}

CAPITAL_INTEGRALIZADO = 500000.00

# Cada combinacao de regime e apuracao monta sua propria empresa, para que as
# variantes possam conviver no mesmo banco.
EMPRESAS = {
    ("presumed", "T"): ("ECF Comercio e Servicos Ltda", "91.827.364/0001-03"),
    ("real", "T"): ("ECF Lucro Real Trimestral Ltda", "82.736.451/0001-56"),
    ("real", "A"): ("ECF Lucro Real Anual Ltda", "73.645.182/0001-21"),
}


class CenarioPresumido:
    """Monta a empresa, o plano de contas, os cadastros e o movimento do ano."""

    def __init__(self, env, regime="presumed", apuracao="T"):
        """:param regime: ``presumed`` ou ``real``.
        :param apuracao: ``T`` trimestral ou ``A`` anual (so vale no real).
        """
        self.env = env
        self.regime = regime
        self.apuracao = apuracao
        self.company = None
        self.contas = {}
        self.journal = None

    def montar(self):
        self._empresa()
        self._endereco()
        self._plano_de_contas()
        self._diario()
        self._signatarios()
        self._socios()
        self._movimento()
        return self

    # ------------------------------------------------------------------

    def _empresa(self):
        nome, cnpj = EMPRESAS[(self.regime, self.apuracao)]
        self.company = self.env["res.company"].create(
            {
                "name": nome,
                "legal_name": nome,
                "vat": cnpj,
                "profit_calculation": self.regime,
                "l10n_br_ecf_profit_period": self.apuracao,
            }
        )
        self.env.user.company_ids |= self.company
        self.env = self.env(
            context=dict(self.env.context, allowed_company_ids=[self.company.id])
        )
        self.company.legal_nature_id = self.env["l10n_br_fiscal.legal.nature"].search(
            [], limit=1
        )
        # o registro 0030 escritura o CNAE sem pontuacao, com sete digitos
        self.company.cnae_main_id = self.env["l10n_br_fiscal.cnae"].search(
            [("internal_type", "=", "normal")], limit=1
        )

    def _endereco(self):
        """O registro 0030 exige endereco, municipio e CEP da matriz."""
        cidade = self.env["res.city"].search(
            [("ibge_code", "!=", False), ("state_id.code", "=", "SP")], limit=1
        )
        self.company.partner_id.write(
            {
                "street_name": "Rua das Escrituracoes",
                "street_number": "1000",
                "district": "Centro",
                "zip": "01310-100",
                "city_id": cidade.id,
                "state_id": cidade.state_id.id,
                "country_id": cidade.state_id.country_id.id,
                "phone": "11 3333-4444",
                "email": "contato@exemplo.com.br",
            }
        )

    def _plano_de_contas(self):
        grupos = {}
        for codigo, nome, pai in GRUPOS:
            grupos[codigo] = (
                self.env["account.group"]
                .with_company(self.company)
                .create(
                    {
                        "name": nome,
                        "code_prefix_start": codigo,
                        "code_prefix_end": codigo,
                        "parent_id": grupos[pai].id if pai else False,
                        "company_id": self.company.id,
                    }
                )
            )
        for codigo, nome, tipo, referencial, linha_p200, linha_wh in PLANO:
            self.contas[codigo] = (
                self.env["account.account"]
                .with_company(self.company)
                .create(
                    {
                        "code": codigo,
                        "name": nome,
                        "account_type": tipo,
                        "company_id": self.company.id,
                        "l10n_br_sped_referential_code": referencial,
                        "l10n_br_ecf_revenue_line": linha_p200,
                        "l10n_br_ecf_withholding_line": linha_wh,
                    }
                )
            )

    def _diario(self):
        self.journal = (
            self.env["account.journal"]
            .with_company(self.company)
            .create(
                {
                    "name": "Diario ECF",
                    "code": "ECF",
                    "type": "general",
                    "company_id": self.company.id,
                }
            )
        )

    def _signatarios(self):
        signer = self.env["l10n_br_sped.signer"]
        signer.create(
            {
                "company_id": self.company.id,
                "name": "Maria de Souza",
                "cpf_cnpj": "191.808.470-05",
                "qualification": "203",
                "email": "diretoria@exemplo.com.br",
                "phone": "11 3333-4444",
            }
        )
        signer.create(
            {
                "company_id": self.company.id,
                "name": "Joao Pereira",
                "cpf_cnpj": "746.851.750-93",
                "qualification": "309",
                "crc": "1SP123456/O-1",
                "email": "contabilidade@exemplo.com.br",
                "phone": "11 3333-5555",
            }
        )

    def _socios(self):
        socio = self.env["l10n_br_ecf.shareholder"]
        socio.create(
            {
                "company_id": self.company.id,
                "name": "Maria de Souza",
                "cpf_cnpj": "191.808.470-05",
                "qualification": "01",
                "capital_share": 60.0,
                "voting_share": 60.0,
                "work_income": 120000.00,
            }
        )
        socio.create(
            {
                "company_id": self.company.id,
                "name": "Carlos Lima",
                "cpf_cnpj": "528.994.310-21",
                "qualification": "01",
                "capital_share": 40.0,
                "voting_share": 40.0,
                "work_income": 90000.00,
            }
        )

    def _lancar(self, data, linhas, referencia):
        move = (
            self.env["account.move"]
            .with_company(self.company)
            .create(
                {
                    "move_type": "entry",
                    "date": data,
                    "ref": referencia,
                    "journal_id": self.journal.id,
                    "company_id": self.company.id,
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "account_id": self.contas[codigo].id,
                                "debit": debito,
                                "credit": credito,
                                "name": referencia,
                            },
                        )
                        for codigo, debito, credito in linhas
                    ],
                }
            )
        )
        move.action_post()
        return move

    def _movimento(self):
        self._lancar(
            date(ANO, 1, 1),
            [
                ("1.01.01.01", CAPITAL_INTEGRALIZADO, 0.0),
                ("2.03.01.01", 0.0, CAPITAL_INTEGRALIZADO),
            ],
            "Integralizacao de capital",
        )
        for trimestre, valores in MOVIMENTO.items():
            revenda, servicos, rendimentos, custo, despesas = valores
            data = date(ANO, ULTIMO_MES_DO_TRIMESTRE[trimestre], 20)
            irrf = round(servicos * ALIQUOTA_IRRF_SERVICO, 2)
            csll_retida = round(servicos * ALIQUOTA_CSLL_RETIDA_SERVICO, 2)
            self._lancar(
                data,
                [
                    # o tomador retem na fonte, entao o valor a receber e
                    # liquido e a retencao vira credito a compensar
                    ("1.01.02.01", revenda + servicos - irrf - csll_retida, 0.0),
                    ("1.01.04.01", irrf, 0.0),
                    ("1.01.04.02", csll_retida, 0.0),
                    ("3.01.01.01", 0.0, revenda),
                    ("3.01.01.02", 0.0, servicos),
                ],
                f"Receitas do {trimestre}o trimestre",
            )
            self._lancar(
                data,
                [("1.01.01.01", rendimentos, 0.0), ("3.01.02.01", 0.0, rendimentos)],
                f"Rendimentos financeiros do {trimestre}o trimestre",
            )
            # a mercadoria entra antes de sair: sem a compra o estoque fecha
            # negativo e o registro Y672 sai com saldo invertido
            self._lancar(
                data,
                [("1.01.03.01", custo, 0.0), ("2.01.01.01", 0.0, custo)],
                f"Compra de mercadorias do {trimestre}o trimestre",
            )
            self._lancar(
                data,
                [("4.01.01.01", custo, 0.0), ("1.01.03.01", 0.0, custo)],
                f"Custo das mercadorias do {trimestre}o trimestre",
            )
            self._lancar(
                data,
                [("4.01.02.01", despesas, 0.0), ("2.01.01.01", 0.0, despesas)],
                f"Despesas do {trimestre}o trimestre",
            )

    # ------------------------------------------------------------------

    def declaracao(self):
        """Cria a declaracao do ano-calendario e a preenche a partir do Odoo."""
        modelo = self.env["l10n_br_sped.ecf.0000"].with_company(self.company)
        vals = modelo._map_from_odoo(self.company, None, None)
        vals.update(
            {
                "company_id": self.company.id,
                "DT_INI": date(ANO, 1, 1),
                "DT_FIN": date(ANO, 12, 31),
            }
        )
        declaracao = modelo.create(vals)
        declaracao.button_populate_sped_from_odoo()
        return declaracao
