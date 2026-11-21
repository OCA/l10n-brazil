# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""A ECD inteira a partir do Odoo, do cenario do lucro presumido ao arquivo."""

import base64
import os

from odoo.tests import common, tagged

from .cenario_presumido import CenarioPresumido


@tagged("post_install", "-at_install")
class TestEcdCenario(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cenario = CenarioPresumido(cls.env).montar()

    def _arquivo(self):
        """O anexo que o botao Gerar cria, como texto."""
        declaracao = self.cenario.declaracao()
        declaracao.button_create_sped_files()
        anexo = self.env["ir.attachment"].search(
            [("res_model", "=", declaracao._name), ("res_id", "=", declaracao.id)],
            order="id desc",
            limit=1,
        )
        conteudo = base64.b64decode(anexo.datas)
        destino = os.environ.get("ECD_GERAR_ARQUIVO")
        if destino:
            with open(destino, "wb") as arquivo:
                arquivo.write(conteudo)
        return declaracao, conteudo.decode("iso-8859-1").split("\r\n")[:-1]

    @staticmethod
    def _campos(linhas, registro):
        return [ln.split("|")[1:-1] for ln in linhas if ln[1:5] == registro]

    def test_termos_com_a_quantidade_de_linhas(self):
        """I030 e J900 saem do Odoo com o total de linhas do arquivo."""
        _declaracao, linhas = self._arquivo()
        i030 = self._campos(linhas, "I030")
        j900 = self._campos(linhas, "J900")
        self.assertEqual(len(i030), 1)
        self.assertEqual(i030[0][1], "TERMO DE ABERTURA")
        self.assertEqual(i030[0][4], str(len(linhas)))
        self.assertEqual(j900[0][1], "TERMO DE ENCERRAMENTO")
        self.assertEqual(j900[0][5], str(len(linhas)))

    def test_signatarios(self):
        """O J930 sai do cadastro de signatarios da empresa."""
        _declaracao, linhas = self._arquivo()
        j930 = self._campos(linhas, "J930")
        self.assertEqual(
            j930,
            [
                [
                    "J930",
                    "Maria de Souza",
                    "19180847005",
                    "Diretor",
                    "203",
                    "",
                    "diretoria@exemplo.com.br",
                    "1133334444",
                    "",
                    "",
                    "",
                    "S",
                ],
                [
                    "J930",
                    "Joao Pereira",
                    "74685175093",
                    "Contador",
                    "900",
                    "1SP123456O1",
                    "contabilidade@exemplo.com.br",
                    "1133335555",
                    "SP",
                    "SP/2023/000123",
                    "31122023",
                    "N",
                ],
            ],
        )

    def test_encerramento_e_saldos_antes_dele(self):
        """O encerramento de cada trimestre sai como lancamento E, com os saldos
        de resultado que ele zera no I350/I355."""
        _declaracao, linhas = self._arquivo()
        i200 = self._campos(linhas, "I200")
        self.assertEqual(sum(1 for campos in i200 if campos[4] == "E"), 4)
        i350 = self._campos(linhas, "I350")
        self.assertEqual(
            [campos[1] for campos in i350],
            ["31032022", "30062022", "30092022", "31122022"],
        )
        self.assertIn("|I355|3.01.01.01||300000,00|C|", linhas)
        self.assertIn("|I355|4.01.01.01||180000,00|D|", linhas)

    def test_balanco_e_resultado(self):
        """O balanco fecha depois do encerramento e o resultado e o do ano."""
        _declaracao, linhas = self._arquivo()
        j100 = {campos[1]: campos for campos in self._campos(linhas, "J100")}
        # ativo = passivo + patrimonio liquido, com o lucro do ano encerrado
        self.assertEqual(j100["1"][9], j100["2"][9])
        self.assertEqual(j100["2.03.02.01"][9:11], ["1012000,00", "C"])
        j150 = {campos[2]: campos for campos in self._campos(linhas, "J150")}
        self.assertEqual(j150["RES"][9:12], ["1012000,00", "C", "R"])
        self.assertEqual(j150["3.01.01.01"][9:12], ["1580000,00", "C", "R"])
        # cada conta dos demonstrativos tem a sua aglutinacao no I052
        i052 = {campos[2] for campos in self._campos(linhas, "I052")}
        self.assertIn("4.01.02.01", i052)
        self.assertIn("2.03.02.01", i052)

    def test_digitado_sob_registro_puxado_fica(self):
        """Puxar de novo nao apaga o que foi digitado sob um registro puxado."""
        declaracao = self.cenario.declaracao()
        declaracao.button_populate_sped_from_odoo()
        i010 = self.env["l10n_br_sped.ecd.i010"].search(
            [("declaration_id", "=", declaracao.id)]
        )
        self.env["l10n_br_sped.ecd.i075"].create(
            {
                "declaration_id": declaracao.id,
                "reg_I075_ids_RegistroI010_id": i010.id,
                "COD_HIST": "1",
                "DESCR_HIST": "Historico padrao digitado",
            }
        )
        declaracao.button_populate_sped_from_odoo()
        i075 = self.env["l10n_br_sped.ecd.i075"].search(
            [("declaration_id", "=", declaracao.id)]
        )
        novo_i010 = self.env["l10n_br_sped.ecd.i010"].search(
            [("declaration_id", "=", declaracao.id)]
        )
        self.assertEqual(len(novo_i010), 1)
        self.assertNotEqual(novo_i010, i010)
        self.assertEqual(i075.DESCR_HIST, "Historico padrao digitado")
        self.assertEqual(i075.reg_I075_ids_RegistroI010_id, novo_i010)
        self.assertFalse(i075.is_generated_from_odoo)
