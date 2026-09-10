# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
"""Escrituracao completa de uma ECF de lucro presumido, do Odoo ao arquivo.

O cenario esta em ``cenario_presumido.py``, compartilhado com a geracao do
arquivo de exemplo do modulo. O teste vai ate o fim: gera a ECF e a submete ao
validador estrutural, que confere blocos, hierarquia, campos, contagens do
bloco 9 e a aritmetica das linhas calculadas do bloco P contra as formulas
oficiais da RFB.
"""

import os

from odoo.tests import common, tagged

from odoo.addons.l10n_br_sped_ecf.models.ecf_validator import EcfValidator

from .cenario_presumido import CenarioPresumido

# Modelos do modulo que nao sao registros da escrituracao.
NAO_REGISTROS = ("MIXIN", "VALORES")


@tagged("post_install", "-at_install")
class TestEcfPresumido(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cenario = CenarioPresumido(cls.env).montar()
        cls.company = cls.cenario.company

    # ------------------------------------------------------------------

    def _definicoes_de_registro(self):
        """``{codigo: [(campo, obrigatorio, tipo)]}`` a partir do spec."""
        definicoes = {}
        for modelo in self.env["ir.model"].search(
            [("model", "=like", "l10n_br_sped.ecf.%")]
        ):
            codigo = modelo.model.split(".")[-1].upper()
            if not codigo or codigo in NAO_REGISTROS:
                continue
            registro = self.env[modelo.model]
            if not hasattr(registro, "_ordered_fields"):
                continue
            campos = [
                (nome, bool(campo.required), campo.type)
                for nome, campo in registro._ordered_fields()
                if nome.isupper()
            ]
            if campos:
                definicoes[codigo] = campos
        return definicoes

    def test_arquivo_valido(self):
        """A ECF gerada passa no validador estrutural, sem nenhum apontamento."""
        texto = self.cenario.declaracao()._generate_sped_text()
        erros = EcfValidator(texto, self._definicoes_de_registro()).validate()
        self.assertEqual(
            erros,
            [],
            "a ECF gerada tem inconformidades:\n"
            + "\n".join(str(erro) for erro in erros),
        )

    def test_blocos_obrigatorios_preenchidos(self):
        """O arquivo carrega identificacao, plano, saldos e apuracao."""
        texto = self.cenario.declaracao()._generate_sped_text()
        obrigatorios = (
            "0000",
            "0010",
            "0020",
            "0030",
            "0930",
            "J050",
            "J051",
            "K030",
            "K155",
            "K156",
            "K355",
            "K356",
            "P030",
            "P100",
            "P150",
            "P200",
            "P300",
            "P400",
            "P500",
            "Y600",
        )
        for registro in obrigatorios:
            self.assertIn(f"|{registro}|", texto, f"falta o registro {registro}")
        self.assertTrue(texto.startswith("|0000|LECF|0009|"))
        # o bloco sem dados nao entra no arquivo, e o Y672 nao vale para quem
        # apresentou escrituracao contabil
        for ausente in ("E001", "L001", "M001", "N001", "T001", "U001", "Y672"):
            self.assertNotIn(f"|{ausente}|", texto, f"{ausente} nao deveria sair")

    def test_apuracao_do_primeiro_trimestre(self):
        """Os valores apurados batem com o calculo do lucro presumido.

        Primeiro trimestre: 300.000,00 de revenda (presuncao de 8%) e
        120.000,00 de servicos (presuncao de 32%), mais 4.000,00 de
        rendimentos de aplicacoes financeiras, que entram integralmente.
        """
        declaracao = self.cenario.declaracao()
        p030 = self.env["l10n_br_sped.ecf.p030"].search(
            [("declaration_id", "=", declaracao.id), ("PER_APUR", "=", "T01")]
        )
        self.assertTrue(p030, "o primeiro trimestre nao foi escriturado")

        p200 = {r.CODIGO: r.VALOR for r in p030.reg_P200_ids}
        self.assertEqual(p200["4"], "300000,00")
        self.assertEqual(p200["8"], "120000,00")
        # 300.000 x 8% + 120.000 x 32% = 24.000 + 38.400
        self.assertEqual(p200["10"], "62400,00")
        self.assertEqual(p200["11"], "4000,00")
        # base = 62.400 + 4.000
        self.assertEqual(p200["26"], "66400,00")

        p300 = {r.CODIGO: r.VALOR for r in p030.reg_P300_ids}
        self.assertEqual(p300["1"], "66400,00")
        # 66.400 x 15%
        self.assertEqual(p300["3"], "9960,00")
        # (66.400 - 3 x 20.000) x 10%
        self.assertEqual(p300["4"], "640,00")
        # IRRF de 1,5% sobre os 120.000 de servico, retido pelo tomador
        self.assertEqual(p300["10"], "1800,00")
        # 9.960 + 640 - 1.800
        self.assertEqual(p300["15"], "8800,00")

        p400 = {r.CODIGO: r.VALOR for r in p030.reg_P400_ids}
        # a revenda presume 12% para a CSLL e o servico 32%
        self.assertEqual(p400["2"], "300000,00")
        self.assertEqual(p400["4"], "120000,00")
        # 300.000 x 12% + 120.000 x 32% = 36.000 + 38.400
        self.assertEqual(p400["6"], "74400,00")
        self.assertEqual(p400["21"], "78400,00")

        p500 = {r.CODIGO: r.VALOR for r in p030.reg_P500_ids}
        self.assertEqual(p500["1"], "78400,00")
        # 78.400 x 9%
        self.assertEqual(p500["2"], "7056,00")
        # CSLL de 1% retida na fonte pelo tomador do servico
        self.assertEqual(p500["11"], "1200,00")
        # 7.056 - 1.200
        self.assertEqual(p500["13"], "5856,00")

    def test_validador_reprova_arquivo_adulterado(self):
        """O validador nao passa a mao: valor calculado errado e reprovado."""
        texto = self.cenario.declaracao()._generate_sped_text()
        adulterado = "\n".join(
            linha.replace("|9960,00|", "|1,00|")
            if linha.startswith("|P300|3|")
            else linha
            for linha in texto.split("\n")
        )
        self.assertNotEqual(adulterado, texto, "o arquivo nao foi adulterado")
        erros = EcfValidator(adulterado).validate()
        self.assertTrue(
            any("line 3 of period" in str(erro) for erro in erros),
            "o validador aceitou um IRPJ calculado errado: "
            + "; ".join(str(erro) for erro in erros),
        )

    def test_validador_reprova_contagem_errada(self):
        """Contagem do bloco 9 fora do que o arquivo tem e reprovada."""
        texto = self.cenario.declaracao()._generate_sped_text()
        adulterado = texto.replace("|9900|0930|2|", "|9900|0930|7|", 1)
        erros = EcfValidator(adulterado).validate()
        self.assertTrue(
            any("occurrence(s) of register 0930" in str(erro) for erro in erros),
            "o validador aceitou uma contagem do bloco 9 errada",
        )

    def test_gerar_arquivo_de_exemplo(self):
        """Escreve a ECF gerada no caminho de ``ECF_GERAR_DEMO``.

        O arquivo de exemplo do modulo (``demo/demo_ecf.txt``) deve ser a ECF
        que esta escrituracao produz, e nao um arquivo escrito a mao: e o que
        da valor ao teste de ida e volta ``test_import_ecf``. Roda sob demanda
        porque escreve em disco, e o destino vem da variavel porque o
        diretorio do modulo costuma estar montado somente para leitura.
        """
        destino = os.environ.get("ECF_GERAR_DEMO")
        if not destino:
            self.skipTest("defina ECF_GERAR_DEMO=<arquivo> para gerar o exemplo")
        regime = os.environ.get("ECF_REGIME", "presumed")
        apuracao = os.environ.get("ECF_APURACAO", "T")
        if regime != "presumed" or apuracao != "T":
            cenario = CenarioPresumido(self.env, regime, apuracao).montar()
            texto = cenario.declaracao()._generate_sped_text()
            with open(destino, "w") as arquivo:
                arquivo.write(texto.strip() + "\n")
            return
        texto = self.cenario.declaracao()._generate_sped_text()
        self.assertEqual(EcfValidator(texto).validate(), [])
        with open(destino, "w") as arquivo:
            arquivo.write(texto.strip() + "\n")

    def test_soma_e_arredondamento_do_motor(self):
        """Casos de borda da linguagem de formulas da RFB.

        O limite superior sem parte decimal abrange as sublinhas (a linha
        14.10 pertence a linha 14); o limite com parte decimal e exato. O
        arredondamento de meio centavo vai para longe do zero nos dois
        sinais.
        """
        from odoo.addons.l10n_br_sped_ecf.models.apuracao_presumido import (
            arredonda,
            soma,
        )

        valores = {"7": 100.0, "14": 50.0, "14.10": 30.0, "15": 1.0}
        self.assertEqual(soma(valores, "7", "14"), 180.0)
        exatos = {"25.02": 5.0, "25.100": 7.0}
        self.assertEqual(soma(exatos, "22", "25.99"), 5.0)
        self.assertEqual(arredonda(0.125), 0.13)
        self.assertEqual(arredonda(-0.125), -0.13)

    def test_csll_nao_deriva_da_linha_do_irpj(self):
        """Servico do art. 40 da Lei 9.250/1995: IRPJ a 16%, CSLL segue a 32%.

        A presuncao da CSLL nao deriva da do IRPJ: sem o campo proprio, o
        de-para usual mandaria o servico com IRPJ reduzido para a linha de
        12% da CSLL, recolhendo a menor.
        """
        declaracao = self.cenario.declaracao()
        p030 = self.env["l10n_br_sped.ecf.p030"].search(
            [("declaration_id", "=", declaracao.id), ("PER_APUR", "=", "T01")]
        )
        conta_servico = self.env["account.account"].search(
            [
                ("company_id", "=", self.company.id),
                ("l10n_br_ecf_revenue_line", "=", "8"),
            ],
            limit=1,
        )
        self.assertTrue(conta_servico, "o cenario nao tem conta de servico")
        # a empresa passa a se enquadrar no art. 40: IRPJ presume 16%...
        conta_servico.l10n_br_ecf_revenue_line = "6"
        valores = p030._apurar()
        # ...e SEM o campo proprio o de-para usual manda a CSLL para 12%
        # (que e o certo para transporte de passageiros, nao para servico):
        # a linha 2 do P400 soma a revenda (300.000) e o servico (120.000)
        self.assertEqual(valores["P400"].get("2", 0.0), 420000.0)
        # com a linha propria declarada, a CSLL do servico fica nos 32%
        conta_servico.l10n_br_ecf_csll_line = "4"
        valores = p030._apurar()
        self.assertEqual(valores["P400"].get("4", 0.0), 120000.0)
        self.assertEqual(valores["P400"].get("2", 0.0), 300000.0)

    def test_criterio_de_reconhecimento_e_competencia(self):
        """O 0010 declara competencia (2), que e o que a apuracao faz.

        Na tabela do leiaute o valor 1 e o regime de CAIXA e o 2 e o de
        COMPETENCIA. O modulo apura por competencia, entao declarar 1 seria
        afirmar a Receita uma opcao que a empresa nao exerceu (a inversao
        passou pelo PVA, que aceita os dois valores para o presumido).
        """
        texto = self.cenario.declaracao()._generate_sped_text()
        linha_0010 = next(
            linha for linha in texto.split("\n") if linha.startswith("|0010|")
        )
        campos = linha_0010.split("|")
        self.assertEqual(campos[-2], "2", linha_0010)

    def test_optante_pelo_caixa_nao_gera(self):
        """Quem optou pelo caixa nao pode sair com uma ECF de competencia.

        A opcao e exercida no primeiro DARF do ano e vale para IRPJ, CSLL,
        PIS e COFINS ao mesmo tempo (IN RFB 1700/2017, art. 224; MP
        2.158-35/2001, art. 20). O arquivo declarando competencia
        contradiria os recolhimentos, e o PVA nao cruza nada disso: o erro
        so apareceria na malha (art. 223, par. 4: juros e multa).
        """
        from odoo.exceptions import UserError

        declaracao = self.cenario.declaracao()
        self.company.l10n_br_ecf_revenue_recognition = "cash"
        self.addCleanup(
            setattr, self.company, "l10n_br_ecf_revenue_recognition", "accrual"
        )
        with self.assertRaisesRegex(UserError, "regime de caixa"):
            self.env["l10n_br_sped.ecf.0010"].with_context(
                declaration=declaracao
            )._map_from_odoo(None, None, declaracao)
