# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Cenario de uma empresa do lucro presumido com escrituracao contabil.

E o mesmo cenario da ECF: uma empresa que revende mercadoria e presta servico,
com o resultado encerrado a cada trimestre. A ECD sai inteira dele, sem
registro digitado.
"""

import calendar
from datetime import date

ANO = 2022

# Grupos sinteticos: com a conta analitica, os quatro niveis que a Resolucao
# CFC 1299/2010 exige.
GRUPOS = [
    ("1", "ATIVO", None),
    ("1.01", "ATIVO CIRCULANTE", "1"),
    ("1.01.01", "DISPONIBILIDADES", "1.01"),
    ("1.01.02", "CREDITOS", "1.01"),
    ("1.01.03", "ESTOQUES", "1.01"),
    ("1.01.04", "TRIBUTOS A COMPENSAR", "1.01"),
    ("2", "PASSIVO", None),
    ("2.01", "PASSIVO CIRCULANTE", "2"),
    ("2.01.01", "FORNECEDORES", "2.01"),
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

# (codigo, nome, tipo do Odoo, conta referencial do lucro presumido)
PLANO = [
    ("1.01.01.01", "Bancos Conta Movimento", "asset_cash", "1.01.01.02.01"),
    ("1.01.02.01", "Duplicatas a Receber", "asset_receivable", "1.01.02.02.01"),
    ("1.01.03.01", "Mercadorias para Revenda", "asset_current", "1.01.03.01.01"),
    ("1.01.04.01", "IRRF a Compensar", "asset_current", "1.01.02.04.01"),
    ("1.01.04.02", "CSLL Retida a Compensar", "asset_current", "1.01.02.04.04"),
    ("2.01.01.01", "Fornecedores", "liability_payable", "2.01.01.03.01"),
    ("2.03.01.01", "Capital Social", "equity", "2.03.01.01.01"),
    ("2.03.02.01", "Lucros Acumulados", "equity", "2.03.04.01.01"),
    ("3.01.01.01", "Receita de Revenda", "income", "3.01.01.01.01.05"),
    ("3.01.01.02", "Receita de Servicos", "income", "3.01.01.01.01.06"),
    ("3.01.02.01", "Rendimentos de Aplicacoes", "income", "3.01.01.05.01.05"),
    ("4.01.01.01", "Custo das Mercadorias", "expense", "3.01.01.03.01.02"),
    ("4.01.02.01", "Despesas Operacionais", "expense", "3.01.01.09.01.99"),
]

# Revenda, servicos, rendimentos, custo da revenda e despesas, por trimestre.
MOVIMENTO = {
    1: (300000.00, 120000.00, 4000.00, 180000.00, 60000.00),
    2: (360000.00, 150000.00, 5000.00, 210000.00, 70000.00),
    3: (420000.00, 180000.00, 6000.00, 250000.00, 80000.00),
    4: (500000.00, 200000.00, 7000.00, 300000.00, 90000.00),
}

# IRRF de 1,5% e CSLL de 1% retidos pelo tomador do servico.
ALIQUOTA_IRRF = 0.015
ALIQUOTA_CSLL = 0.01

CAPITAL = 500000.00

EMPRESA = ("ECF Comercio e Servicos Ltda", "91.827.364/0001-03")


class CenarioPresumido:
    """Monta a empresa, o plano, os signatarios e o movimento do ano."""

    def __init__(self, env):
        self.env = env
        self.company = None
        self.contas = {}
        self.journal = None
        self.encerramentos = {}

    def montar(self):
        self._empresa()
        self._plano_de_contas()
        self._diario()
        self._signatarios()
        self._movimento()
        return self

    def _empresa(self):
        nome, cnpj = EMPRESA
        self.company = self.env["res.company"].create(
            {
                "name": nome,
                "legal_name": nome,
                "vat": cnpj,
                "profit_calculation": "presumed",
            }
        )
        self.env.user.company_ids |= self.company
        self.env = self.env(
            context=dict(self.env.context, allowed_company_ids=[self.company.id])
        )
        cidade = self.env["res.city"].search(
            [("ibge_code", "!=", False), ("state_id.code", "=", "SP")], limit=1
        )
        self.company.partner_id.write(
            {
                "street_name": "Rua das Escrituracoes",
                "street_number": "1000",
                "zip": "01310-100",
                "city_id": cidade.id,
                "state_id": cidade.state_id.id,
                "country_id": cidade.state_id.country_id.id,
            }
        )

    def _plano_de_contas(self):
        grupos = {}
        for codigo, nome, pai in GRUPOS:
            grupos[codigo] = self.env["account.group"].create(
                {
                    "name": nome,
                    "code_prefix_start": codigo,
                    "code_prefix_end": codigo,
                    "parent_id": grupos[pai].id if pai else False,
                    "company_id": self.company.id,
                }
            )
        for codigo, nome, tipo, referencial in PLANO:
            self.contas[codigo] = self.env["account.account"].create(
                {
                    "code": codigo,
                    "name": nome,
                    "account_type": tipo,
                    "company_id": self.company.id,
                    "l10n_br_sped_referential_code": referencial,
                }
            )

    def _diario(self):
        self.journal = self.env["account.journal"].create(
            {
                "name": "Diario Geral",
                "code": "DG",
                "type": "general",
                "company_id": self.company.id,
            }
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
                "legal_responsible": True,
            }
        )
        signer.create(
            {
                "company_id": self.company.id,
                "name": "Joao Pereira",
                "cpf_cnpj": "746.851.750-93",
                "qualification": "900",
                "crc": "1SP123456/O-1",
                "crc_state_id": self.env.ref("base.state_br_sp").id,
                "crp_number": "SP/2023/000123",
                "crp_validity": date(ANO + 1, 12, 31),
                "email": "contabilidade@exemplo.com.br",
                "phone": "11 3333-5555",
            }
        )

    def _lancar(self, data, linhas, referencia, encerramento=False):
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": data,
                "ref": referencia,
                "journal_id": self.journal.id,
                "company_id": self.company.id,
                "l10n_br_sped_result_closing": encerramento,
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
        move.action_post()
        return move

    def _movimento(self):
        self._lancar(
            date(ANO, 1, 1),
            [("1.01.01.01", CAPITAL, 0.0), ("2.03.01.01", 0.0, CAPITAL)],
            "Integralizacao de capital",
        )
        for trimestre, valores in MOVIMENTO.items():
            revenda, servicos, rendimentos, custo, despesas = valores
            mes = trimestre * 3
            data = date(ANO, mes, 20)
            irrf = round(servicos * ALIQUOTA_IRRF, 2)
            csll = round(servicos * ALIQUOTA_CSLL, 2)
            self._lancar(
                data,
                [
                    ("1.01.02.01", revenda + servicos - irrf - csll, 0.0),
                    ("1.01.04.01", irrf, 0.0),
                    ("1.01.04.02", csll, 0.0),
                    ("3.01.01.01", 0.0, revenda),
                    ("3.01.01.02", 0.0, servicos),
                ],
                f"Receitas do {trimestre}o trimestre",
            )
            self._lancar(
                data,
                [("1.01.01.01", rendimentos, 0.0), ("3.01.02.01", 0.0, rendimentos)],
                f"Rendimentos do {trimestre}o trimestre",
            )
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
            # encerramento do resultado do trimestre, no ultimo dia
            lucro = revenda + servicos + rendimentos - custo - despesas
            self.encerramentos[trimestre] = self._lancar(
                date(ANO, mes, calendar.monthrange(ANO, mes)[1]),
                [
                    ("3.01.01.01", revenda, 0.0),
                    ("3.01.01.02", servicos, 0.0),
                    ("3.01.02.01", rendimentos, 0.0),
                    ("4.01.01.01", 0.0, custo),
                    ("4.01.02.01", 0.0, despesas),
                    ("2.03.02.01", 0.0, lucro),
                ],
                f"Encerramento do resultado do {trimestre}o trimestre",
                encerramento=True,
            )

    def declaracao(self):
        """A declaracao do ano, so com o que o Odoo preenche."""
        modelo = self.env["l10n_br_sped.ecd.0000"].with_company(self.company)
        vals = modelo._map_from_odoo(self.company, None, None)
        vals.update(
            {
                "company_id": self.company.id,
                "DT_INI": date(ANO, 1, 1),
                "DT_FIN": date(ANO, 12, 31),
            }
        )
        return modelo.create(vals)
