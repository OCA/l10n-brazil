# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
"""Apuracao do IRPJ e da CSLL pelo lucro presumido (bloco P da ECF).

O calculo e Python puro, sem Odoo, para poder ser testado isoladamente: recebe
a receita bruta separada por percentual de presuncao mais as adicoes e
exclusoes do periodo, e devolve o valor de cada linha dos registros P200, P300,
P400 e P500.

Cada metodo de linha calculada traz no docstring a FORMULA oficial publicada
pela RFB na tabela dinamica do registro (ver ``tabelas_dinamicas.py``), copiada
literalmente, para que a conferencia contra o Guia seja direta.

As linhas da Lei Complementar 224/25 (P200 "25.100" em diante, P400 "20.100" em
diante e as linhas 18.x do P300/P500) valem a partir de 2026 e sao geradas
apenas quando o periodo alcanca a vigencia; o leiaute 9 desta escrituracao nao
as contempla.
"""

from . import tabelas_dinamicas

# Percentuais de presuncao do lucro para o IRPJ, por linha do P200.
PERCENTUAL_IRPJ = {
    "2": 0.016,
    "4": 0.08,
    "6": 0.16,
    "8": 0.32,
    "9": 0.384,
}

# Percentuais de presuncao do lucro para a CSLL, por linha do P400.
PERCENTUAL_CSLL = {
    "2": 0.12,
    "4": 0.32,
    "5": 0.384,
}

# Aliquotas da CSLL por 0020.IND_ALIQ_CSLL (P500 linha 2).
ALIQUOTA_CSLL = {
    "1": 0.09,
    "2": 0.15,
    "3": 0.20,
}

# Parcela mensal isenta do adicional de IRPJ (P300 linha 4).
LIMITE_MENSAL_ADICIONAL = 20000.0

ALIQUOTA_IRPJ = 0.15
ALIQUOTA_ADICIONAL_IRPJ = 0.10


def chave_ordem(codigo):
    """Ordem oficial de um codigo de linha: "2" < "20.01" < "25.110" < "26"."""
    partes = str(codigo).split(".")
    inteiro = int(partes[0]) if partes[0].isdigit() else 0
    decimal = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else 0
    return (inteiro, decimal)


def soma(valores, primeiro, ultimo):
    """SOMA(Pxxx(primeiro:ultimo)) da linguagem de formulas da RFB.

    Soma todas as linhas cujo codigo esta no intervalo, inclusive, seguindo a
    ordem oficial dos codigos e nao a ordem alfabetica. Limite superior sem
    parte decimal ("14") abrange as proprias sublinhas ("14.10"): a sublinha
    pertence a linha, e a RFB escreve o limite pela linha-mae. Limite com
    parte decimal ("25.99") e exato.
    """
    inicio = chave_ordem(primeiro)
    partes_fim = str(ultimo).split(".")
    if len(partes_fim) > 1:
        fim = chave_ordem(ultimo)
    else:
        fim = (int(partes_fim[0]), float("inf"))
    return sum(
        valor
        for codigo, valor in valores.items()
        if inicio <= chave_ordem(codigo) <= fim
    )


def arredonda(valor):
    """Arredondamento contabil de duas casas usado na escrituracao.

    O epsilon acompanha o sinal: sem isso o meio centavo negativo
    arredondaria em direcao ao zero (-0,125 viraria -0,12).
    """
    epsilon = 1e-9 if valor >= 0 else -1e-9
    return round(valor + epsilon, 2)


class ApuracaoPresumido:
    """Apuracao trimestral do lucro presumido de um periodo do registro P030.

    :param receita_irpj: receita bruta por linha do P200 ("2", "4", "6", "8",
        "9"), ja separada pelo percentual de presuncao aplicavel.
    :param receita_csll: receita bruta por linha do P400 ("2", "4", "5").
    :param adicoes: demais receitas e ganhos do P200 (linhas 11 a 21), por
        codigo de linha.
    :param exclusoes: exclusoes do P200 (linhas 22 a "25.02"), por codigo de
        linha, informadas em valor positivo.
    :param meses_periodo: meses do periodo de apuracao, usado no limite do
        adicional de IRPJ.
    :param ind_aliquota_csll: 0020.IND_ALIQ_CSLL da declaracao.
    :param retencoes_irpj: retencoes na fonte deduziveis do IRPJ, por linha do
        P300 (10, 12, 13, 14).
    :param retencoes_csll: retencoes na fonte deduziveis da CSLL, por linha do
        P500 (9, 10, 11, 12).
    """

    def __init__(
        self,
        receita_irpj=None,
        receita_csll=None,
        adicoes=None,
        exclusoes=None,
        meses_periodo=3,
        ind_aliquota_csll="1",
        retencoes_irpj=None,
        retencoes_csll=None,
    ):
        self.receita_irpj = dict(receita_irpj or {})
        self.receita_csll = dict(receita_csll or {})
        self.adicoes = dict(adicoes or {})
        self.exclusoes = dict(exclusoes or {})
        self.meses_periodo = meses_periodo
        self.ind_aliquota_csll = ind_aliquota_csll
        self.retencoes_irpj = dict(retencoes_irpj or {})
        self.retencoes_csll = dict(retencoes_csll or {})

    # ------------------------------------------------------------------
    # P200 - Apuracao da Base de Calculo do Lucro Presumido
    # ------------------------------------------------------------------

    def p200(self):
        """Valores das linhas do P200."""
        valores = {}
        for codigo in PERCENTUAL_IRPJ:
            valores[codigo] = arredonda(self.receita_irpj.get(codigo, 0.0))
        valores["10"] = self._p200_10(valores)
        for codigo, valor in self.adicoes.items():
            valores[codigo] = arredonda(valor)
        for codigo, valor in self.exclusoes.items():
            valores[codigo] = arredonda(valor)
        valores["26"] = self._p200_26(valores)
        return valores

    def _p200_10(self, valores):
        """RESULTADO DA APLICACAO DOS PERCENTUAIS SOBRE A RECEITA BRUTA.

        SE (((P200(2)*0,016) + (P200(4)*0,08) + (P200(6)*0,16) +
        (P200(8)*0,32) + (P200(9)*0,384)) > 0) ENTAO ((P200(2)*0,016) +
        (P200(4)*0,08) + (P200(6)*0,16) + (P200(8)*0,32) + (P200(9)*0,384))
        SENAO 0 FIM_SE
        """
        resultado = sum(
            valores.get(codigo, 0.0) * percentual
            for codigo, percentual in PERCENTUAL_IRPJ.items()
        )
        return arredonda(resultado) if resultado > 0 else 0.0

    def _p200_26(self, valores):
        """BASE DE CALCULO DO IMPOSTO SOBRE O LUCRO PRESUMIDO.

        SE (SOMA(P200(10:21)) - SOMA(P200(22:"25.99")) > 0) ENTAO
        (SOMA(P200(10:21)) - SOMA(P200(22:"25.99"))) SENAO 0 FIM_SE
        """
        base = soma(valores, "10", "21") - soma(valores, "22", "25.99")
        return arredonda(base) if base > 0 else 0.0

    # ------------------------------------------------------------------
    # P300 - Calculo do IRPJ com Base no Lucro Presumido
    # ------------------------------------------------------------------

    def p300(self, valores_p200):
        """Valores das linhas do P300."""
        valores = {"1": valores_p200.get("26", 0.0)}
        valores["3"] = self._p300_3(valores)
        valores["4"] = self._p300_4(valores)
        for codigo, valor in self.retencoes_irpj.items():
            valores[codigo] = arredonda(valor)
        valores["15"] = self._p300_15(valores)
        return valores

    def _p300_3(self, valores):
        """A Aliquota de 15%.

        SE (P300(1) > 0) ENTAO P300(1) * 0,15 SENAO 0 FIM_SE
        """
        base = valores.get("1", 0.0)
        return arredonda(base * ALIQUOTA_IRPJ) if base > 0 else 0.0

    def _p300_4(self, valores):
        """Adicional.

        SE (P300(1) <= (20000 * MESES_PERIODO())) ENTAO 0 SENAO
        (P300(1) - (20000 * MESES_PERIODO())) * 0,10 FIM_SE
        """
        base = valores.get("1", 0.0)
        limite = LIMITE_MENSAL_ADICIONAL * self.meses_periodo
        if base <= limite:
            return 0.0
        return arredonda((base - limite) * ALIQUOTA_ADICIONAL_IRPJ)

    def _p300_15(self, valores):
        """IMPOSTO DE RENDA A PAGAR.

        SOMA(P300(3:5)) - SOMA(P300(7:14))
        """
        return arredonda(soma(valores, "3", "5") - soma(valores, "7", "14"))

    # ------------------------------------------------------------------
    # P400 - Apuracao da Base de Calculo da CSLL
    # ------------------------------------------------------------------

    # Linhas do P400 que sao transporte de uma linha do P200 (tipo CA).
    TRANSPORTE_P200 = {
        "7": "11",
        "8": "12",
        "10": "14",
        "12": "16",
        "13": "17",
        "14": "18",
        "15": "19",
        "16": "20",
        "16.01": "20.01",
        "18": "22",
        "19": "23",
        "19.01": "25.01",
        "19.02": "25.02",
    }

    def p400(self, valores_p200):
        """Valores das linhas do P400."""
        valores = {}
        for codigo in PERCENTUAL_CSLL:
            valores[codigo] = arredonda(self.receita_csll.get(codigo, 0.0))
        valores["6"] = self._p400_6(valores)
        for destino, origem in self.TRANSPORTE_P200.items():
            if origem in valores_p200:
                valores[destino] = valores_p200[origem]
        valores["21"] = self._p400_21(valores)
        return valores

    def _p400_6(self, valores):
        """RESULTADO DA APLICACAO DOS PERCENTUAIS SOBRE A RECEITA BRUTA.

        SE ((P400(2) * 0,12) + (P400(4) * 0,32) + (P400(5) * 0,384) > 0) ENTAO
        (P400(2) * 0,12) + (P400(4) * 0,32) + (P400(5) * 0,384) SENAO 0 FIM_SE
        """
        resultado = sum(
            valores.get(codigo, 0.0) * percentual
            for codigo, percentual in PERCENTUAL_CSLL.items()
        )
        return arredonda(resultado) if resultado > 0 else 0.0

    def _p400_21(self, valores):
        """BASE DE CALCULO DA CSLL.

        SOMA(P400(6:17)) - SOMA(P400(18:20))
        """
        return arredonda(soma(valores, "6", "17") - soma(valores, "18", "20"))

    # ------------------------------------------------------------------
    # P500 - Calculo da CSLL
    # ------------------------------------------------------------------

    def p500(self, valores_p400):
        """Valores das linhas do P500."""
        valores = {"1": valores_p400.get("21", 0.0)}
        valores["2"] = self._p500_2(valores)
        valores["4"] = self._p500_4(valores)
        for codigo, valor in self.retencoes_csll.items():
            valores[codigo] = arredonda(valor)
        valores["13"] = self._p500_13(valores)
        return valores

    def _p500_2(self, valores):
        """CSLL Apurada.

        SE (P500(1) < 0) ENTAO 0 SENAO SE (0000.DT_INI()>="2022-01-01") ENTAO
        SE(0020.IND_ALIQ_CSLL()="1") ENTAO P500(1)*0,09 SENAO
        SE(0020.IND_ALIQ_CSLL()="3") ENTAO P500(1)*0,20 SENAO P500(1)*0,15
        FIM_SE FIM_SE FIM_SE FIM_SE
        """
        base = valores.get("1", 0.0)
        if base < 0:
            return 0.0
        # a condicao 0000.DT_INI >= 2022-01-01 da formula nao e testada aqui
        # de proposito: o leiaute 9 desta escrituracao e do ano-calendario
        # 2022 em diante, entao ela e sempre verdadeira
        aliquota = ALIQUOTA_CSLL.get(self.ind_aliquota_csll, ALIQUOTA_CSLL["2"])
        return arredonda(base * aliquota)

    def _p500_4(self, valores):
        """TOTAL DA CONTRIBUICAO SOCIAL SOBRE O LUCRO LIQUIDO.

        SOMA(P500(2:3))
        """
        return arredonda(soma(valores, "2", "3"))

    def _p500_13(self, valores):
        """CSLL A PAGAR.

        P500(4) - SOMA(P500(6:12))
        """
        return arredonda(valores.get("4", 0.0) - soma(valores, "6", "12"))

    # ------------------------------------------------------------------

    def apurar(self):
        """Todos os registros do bloco P, por codigo de linha."""
        valores_p200 = self.p200()
        valores_p400 = self.p400(valores_p200)
        return {
            "P200": valores_p200,
            "P300": self.p300(valores_p200),
            "P400": valores_p400,
            "P500": self.p500(valores_p400),
        }

    def linhas(self, registro, data_inicio, data_fim, valores):
        """Linhas do registro a escriturar, na ordem e com a descricao oficiais.

        Devolve ``(codigo, descricao, valor)`` para cada linha vigente no
        periodo; o valor e ``None`` nas linhas de rotulo, que a RFB escritura
        sem valor.
        """
        escrituradas = []
        for codigo, descricao, tipo in tabelas_dinamicas.linhas_vigentes(
            registro, data_inicio, data_fim
        ):
            valor = None if tipo == "R" else valores.get(codigo, 0.0)
            escrituradas.append((codigo, descricao, valor))
        return escrituradas
