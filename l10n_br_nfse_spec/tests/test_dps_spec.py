# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import unittest
from unittest.mock import MagicMock

from ..models.spec_mixin import DpsBuilder, NfseResponse


class TestNfseResponse(unittest.TestCase):
    def test_from_dict_status(self):
        r = NfseResponse.from_dict({"status": "autorizado"})
        self.assertEqual(r.status, "autorizado")

    def test_from_dict_numero(self):
        r = NfseResponse.from_dict({"status": "autorizado", "numero": 42})
        self.assertEqual(r.numero, "42")

    def test_from_dict_chave_nfse(self):
        chave = "A" * 44
        r = NfseResponse.from_dict({"status": "autorizado", "chave_nfse": chave})
        self.assertEqual(r.chave_nfse, chave)

    def test_from_dict_chave_nfse_fallback_key(self):
        chave = "B" * 44
        r = NfseResponse.from_dict({"status": "autorizado", "chaveNFSe": chave})
        self.assertEqual(r.chave_nfse, chave)

    def test_from_dict_erros_default_empty(self):
        r = NfseResponse.from_dict({"status": "erro"})
        self.assertEqual(r.erros, [])

    def test_from_dict_erros_populated(self):
        r = NfseResponse.from_dict(
            {"status": "erro", "erros": [{"mensagem": "Invalid data"}]}
        )
        self.assertEqual(len(r.erros), 1)

    def test_from_dict_data_emissao_fallback(self):
        r = NfseResponse.from_dict(
            {"status": "autorizado", "dhEmi": "2024-01-15T10:30:00-03:00"}
        )
        self.assertEqual(r.data_emissao, "2024-01-15T10:30:00-03:00")


class TestDpsBuilder(unittest.TestCase):
    def _make_record(self):
        record = MagicMock()
        record.company_id.cnpj_cpf = "12.345.678/0001-95"
        record.company_id.partner_id.city_id.ibge_code = "3550308"
        record.nfse_environment = "2"
        record.company_id.nfse_environment = "2"

        record._prepare_lote_rps.return_value = {
            "data_emissao": "2024-01-15T10:30:00-03:00",
            "serie": "RPS",
            "numero": "1234",
            "inscricao_municipal": "12345",
            "optante_simples_nacional": "1",
            "regime_especial_tributacao": "0",
        }
        record._prepare_dados_servico.return_value = {
            "codigo_tributacao_nacional": "010101",
            "discriminacao": "Desenvolvimento de sistema web",
            "municipio_prestacao_servico": "3550308",
            "valor_servicos": 5000.00,
            "base_calculo": 5000.00,
            "iss_retido": "2",
            "aliquota": 0.02,
        }
        record._prepare_dados_tomador.return_value = {
            "cnpj": "98765432000100",
            "cpf": "",
            "razao_social": "Test Company LTDA",
            "endereco": "Rua das Flores",
            "numero": "100",
            "bairro": "Centro",
            "codigo_municipio": 3550308,
            "cep": "01310100",
        }
        return record

    def test_build_returns_dict_with_inf_dps(self):
        result = DpsBuilder(self._make_record()).build()
        self.assertIsInstance(result, dict)
        self.assertIn("infDPS", result)

    def test_build_versao(self):
        result = DpsBuilder(self._make_record()).build()
        self.assertEqual(result["versao"], "1.00")

    def test_build_tpAmb_homologation(self):
        result = DpsBuilder(self._make_record()).build()
        # xsdata serializes enum as string value
        self.assertEqual(result["infDPS"]["tpAmb"], "2")

    def test_build_prest_cnpj(self):
        result = DpsBuilder(self._make_record()).build()
        # nfelib TcinfoPrestador: CNPJ is a direct field (no "ident" wrapper)
        self.assertEqual(result["infDPS"]["prest"]["CNPJ"], "12345678000195")

    def test_build_prest_op_simp_nac_me_epp(self):
        result = DpsBuilder(self._make_record()).build()
        # optante="1" + regime != "5" → TsopSimpNac.VALUE_3="3" (ME/EPP)
        self.assertEqual(result["infDPS"]["prest"]["regTrib"]["opSimpNac"], "3")

    def test_build_prest_op_simp_nac_mei(self):
        record = self._make_record()
        record._prepare_lote_rps.return_value.update(
            {"optante_simples_nacional": "1", "regime_especial_tributacao": "5"}
        )
        result = DpsBuilder(record).build()
        # MEI: optante="1" + regime="5" → TsopSimpNac.VALUE_2="2"
        self.assertEqual(result["infDPS"]["prest"]["regTrib"]["opSimpNac"], "2")

    def test_build_prest_mei_has_no_reg_esp_trib(self):
        record = self._make_record()
        record._prepare_lote_rps.return_value.update(
            {"optante_simples_nacional": "1", "regime_especial_tributacao": "5"}
        )
        result = DpsBuilder(record).build()
        # MEI is expressed via opSimpNac, not regEspTrib
        reg_trib = result["infDPS"]["prest"]["regTrib"]
        self.assertNotIn("regEspTrib", reg_trib)

    def test_build_prest_op_simp_nac_nao_optante(self):
        record = self._make_record()
        record._prepare_lote_rps.return_value.update({"optante_simples_nacional": "2"})
        result = DpsBuilder(record).build()
        # não-optante → TsopSimpNac.VALUE_1="1"
        self.assertEqual(result["infDPS"]["prest"]["regTrib"]["opSimpNac"], "1")

    def test_build_prest_reg_esp_trib_cooperativa(self):
        record = self._make_record()
        record._prepare_lote_rps.return_value.update(
            {"optante_simples_nacional": "1", "regime_especial_tributacao": "4"}
        )
        result = DpsBuilder(record).build()
        # legacy "4" (Cooperativa) → DPS "1" (Ato Cooperado)
        self.assertEqual(result["infDPS"]["prest"]["regTrib"]["regEspTrib"], "1")

    def test_build_prest_reg_esp_trib_sociedade_profissionais(self):
        record = self._make_record()
        record._prepare_lote_rps.return_value.update(
            {"optante_simples_nacional": "2", "regime_especial_tributacao": "3"}
        )
        result = DpsBuilder(record).build()
        # legacy "3" (Sociedade de Profissionais) → DPS "6"
        self.assertEqual(result["infDPS"]["prest"]["regTrib"]["regEspTrib"], "6")

    def test_build_toma_cnpj(self):
        result = DpsBuilder(self._make_record()).build()
        # nfelib TcinfoPessoa: CNPJ is a direct field
        self.assertEqual(result["infDPS"]["toma"]["CNPJ"], "98765432000100")

    def test_build_serv_loc_prestacao(self):
        result = DpsBuilder(self._make_record()).build()
        # service city is in serv.locPrest.cLocPrestacao (not serv.cLocPrestacao)
        self.assertEqual(
            result["infDPS"]["serv"]["locPrest"]["cLocPrestacao"], "3550308"
        )

    def test_build_serv_descricao(self):
        result = DpsBuilder(self._make_record()).build()
        self.assertEqual(
            result["infDPS"]["serv"]["cServ"]["xDescServ"],
            "Desenvolvimento de sistema web",
        )

    def test_build_valores_vserv(self):
        result = DpsBuilder(self._make_record()).build()
        # service value is in valores.vServPrest.vServ (string, not float)
        self.assertEqual(result["infDPS"]["valores"]["vServPrest"]["vServ"], "5000.00")

    def test_build_trib_mun_paliq(self):
        result = DpsBuilder(self._make_record()).build()
        # aliquota 0.02 × 100 = 2.0%
        trib_mun = result["infDPS"]["valores"]["trib"]["tribMun"]
        self.assertEqual(trib_mun["pAliq"], "2.00")

    def test_build_trib_mun_tp_ret_nao_retido(self):
        result = DpsBuilder(self._make_record()).build()
        trib_mun = result["infDPS"]["valores"]["trib"]["tribMun"]
        # iss_retido="2" → tpRetISSQN="1" (não retido)
        self.assertEqual(trib_mun["tpRetISSQN"], "1")

    def test_build_trib_mun_tp_ret_retido(self):
        record = self._make_record()
        record._prepare_dados_servico.return_value.update({"iss_retido": "1"})
        result = DpsBuilder(record).build()
        trib_mun = result["infDPS"]["valores"]["trib"]["tribMun"]
        self.assertEqual(trib_mun["tpRetISSQN"], "2")

    def test_build_tot_trib_ind_zero(self):
        result = DpsBuilder(self._make_record()).build()
        tot_trib = result["infDPS"]["valores"]["trib"]["totTrib"]
        self.assertEqual(tot_trib["indTotTrib"], "0")

    def test_build_no_trib_fed_when_no_withholding(self):
        result = DpsBuilder(self._make_record()).build()
        trib = result["infDPS"]["valores"]["trib"]
        self.assertNotIn("tribFed", trib)

    def test_build_trib_fed_with_withholding(self):
        record = self._make_record()
        record._prepare_dados_servico.return_value.update(
            {
                "valor_inss_retido": 100.00,
                "valor_ir_retido": 50.00,
                "valor_csll_retido": 25.00,
            }
        )
        result = DpsBuilder(record).build()
        trib_fed = result["infDPS"]["valores"]["trib"]["tribFed"]
        self.assertEqual(trib_fed["vRetCP"], "100.00")
        self.assertEqual(trib_fed["vRetIRRF"], "50.00")
        self.assertEqual(trib_fed["vRetCSLL"], "25.00")

    def test_build_cpf_provider(self):
        record = self._make_record()
        record.company_id.cnpj_cpf = "123.456.789-01"
        result = DpsBuilder(record).build()
        prest = result["infDPS"]["prest"]
        self.assertIn("CPF", prest)
        self.assertNotIn("CNPJ", prest)

    def test_build_nulls_stripped(self):
        result = DpsBuilder(self._make_record()).build()
        # Optional fields with None should be stripped
        prest = result["infDPS"]["prest"]
        self.assertNotIn("NIF", prest)
        self.assertNotIn("xNome", prest)

    def test_build_dhemi_timezone_appended(self):
        record = self._make_record()
        record._prepare_lote_rps.return_value["data_emissao"] = "2024-01-15T10:30:00"
        result = DpsBuilder(record).build()
        self.assertTrue(result["infDPS"]["dhEmi"].endswith("-0300"))
