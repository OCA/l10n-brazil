# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase


class TestSpedSigner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Contabilista da Empresa",
                "email": "contador@example.com",
                "phone": "(35) 3333-4444",
            }
        )

    def _criar(self, **kw):
        vals = {
            "company_id": self.company.id,
            "name": "Responsavel Legal",
            "cpf_cnpj": "541.400.700-93",
            "qualification": "203",
        }
        vals.update(kw)
        return self.env["l10n_br_sped.signer"].create(vals)

    def test_valores_do_0930(self):
        """O registro sai sem pontuacao no documento e no telefone."""
        signer = self._criar(phone="(35) 3333-4444", email="legal@example.com")
        self.assertEqual(
            signer._sped_values(),
            {
                "IDENT_NOM": "Responsavel Legal",
                "IDENT_CPF_CNPJ": "54140070093",
                "IDENT_QUALIF": "203",
                "IND_CRC": "",
                "EMAIL": "legal@example.com",
                "FONE": "3533334444",
            },
        )

    def test_contabilista_sem_crc_e_recusado(self):
        """O contador (900 na tabela do Sped) assina com o numero do CRC."""
        with self.assertRaises(ValidationError):
            self._criar(name="Contador", qualification="900")

    def test_contabilista_com_crc(self):
        signer = self._criar(name="Contador", qualification="900", crc="1SP123456/O-7")
        self.assertEqual(signer._sped_values()["IND_CRC"], "1SP123456/O-7")

    def test_qualificacao_sem_crc_nao_exige(self):
        """A exigencia do CRC e so das qualificacoes de contabilista."""
        signer = self._criar(qualification="203")
        self.assertFalse(signer.crc)

    def test_onchange_do_contato(self):
        """O contato preenche nome, documento, e-mail e telefone."""
        signer = self.env["l10n_br_sped.signer"].new(
            {"company_id": self.company.id, "partner_id": self.partner.id}
        )
        signer._onchange_partner_id()
        self.assertEqual(signer.name, "Contabilista da Empresa")
        self.assertEqual(signer.email, "contador@example.com")
        self.assertEqual(signer.phone, "(35) 3333-4444")

    def test_onchange_traz_o_crc_do_contato(self):
        """O CRC e a UF do CRC do contador vem do contato (J930 da ECD)."""
        sp = self.env.ref("base.state_br_sp")
        self.partner.write({"crc_code": "1SP123456O1", "crc_state_id": sp.id})
        signer = self.env["l10n_br_sped.signer"].new(
            {"company_id": self.company.id, "partner_id": self.partner.id}
        )
        signer._onchange_partner_id()
        self.assertEqual(signer.crc, "1SP123456O1")
        self.assertEqual(signer.crc_state_id, sp)

    def test_signatarios_da_empresa_e_ordem(self):
        """A escrituracao e assinada por mais de um, na ordem da sequencia."""
        contador = self._criar(
            name="Contador", qualification="900", crc="1SP123456/O-7", sequence=20
        )
        legal = self._criar(sequence=10)
        signers = self.company.l10n_br_sped_signer_ids
        self.assertIn(legal, signers)
        self.assertIn(contador, signers)
        ordenados = signers.sorted(lambda s: (s.sequence, s.id))
        self.assertEqual(ordenados[0], legal)

    def test_espaco_no_telefone_nao_vaza(self):
        """O separador do DDD nao pode sobrar no campo FONE.

        O punctuation_rm do erpbrasil tira a pontuacao mas preserva o
        espaco, e o telefone brasileiro costuma ter um depois do DDD.
        """
        signer = self._criar(phone="+55 (35) 3333-4444")
        self.assertEqual(signer._sped_values()["FONE"], "553533334444")

    def test_cadastro_pelo_formulario_da_empresa(self):
        """A aba SPED da empresa guarda o registro na junta e os signatarios."""
        sp = self.env.ref("base.state_br_sp")
        with Form(self.company, view="base.view_company_form") as form:
            form.l10n_br_articles_filing_date = date(2015, 3, 10)
            self.assertIn("l10n_br_sped_signer_ids", form._view["fields"])
        # o Form de teste da 18.0 trata a lista como many2many (a aba das
        # filiais reabre o formulario da empresa): a linha sai do formulario
        # que a lista abre
        signers = self.env["l10n_br_sped.signer"].with_context(
            default_company_id=self.company.id
        )
        with Form(signers) as line:
            line.name = "Contador da Empresa"
            line.cpf_cnpj = "746.851.750-93"
            line.qualification = "900"
            line.crc = "1SP123456O1"
            line.crc_state_id = sp
            line.crp_number = "SP/2023/000123"
            line.crp_validity = date(2023, 12, 31)
        signer = self.company.l10n_br_sped_signer_ids.filtered(
            lambda s: s.name == "Contador da Empresa"
        )
        self.assertEqual(signer.crc_state_id, sp)
        self.assertEqual(signer.crp_validity, date(2023, 12, 31))
        self.assertEqual(self.company.l10n_br_articles_filing_date, date(2015, 3, 10))

    def test_cadastro_pelo_menu(self):
        """O formulario do signatario, aberto pelo menu do SPED."""
        form = Form(self.env["l10n_br_sped.signer"])
        form.name = "Diretora"
        form.cpf_cnpj = "191.808.470-05"
        form.qualification = "203"
        form.legal_responsible = True
        signer = form.save()
        self.assertTrue(signer.legal_responsible)
        # sem multiempresa o campo nao aparece: a empresa e a do usuario
        self.assertEqual(signer.company_id, self.env.company)

    def _empresa(self, uf):
        return self.env["res.company"].create(
            {
                "name": f"Empresa {uf}",
                "state_id": self.env.ref(f"base.state_br_{uf}").id,
            }
        )

    def test_nire_conferido_como_no_pva(self):
        """O NIRE passa pelo digito e pela UF das regras do PVA da ECD."""
        company = self._empresa("sp")
        company.l10n_br_nire_code = "35200123458"
        with self.assertRaisesRegex(ValidationError, "Invalid NIRE"):
            company.l10n_br_nire_code = "35200123459"
        with self.assertRaisesRegex(ValidationError, "Invalid NIRE"):
            company.l10n_br_nire_code = "3520012345"
        with self.assertRaisesRegex(ValidationError, "state SP"):
            company.l10n_br_nire_code = "33200123456"
        company.state_id = self.env.ref("base.state_br_rj")
        company.l10n_br_nire_code = "33200123456"

    def test_nire_de_mato_grosso_do_sul(self):
        """No MS o NIRE comeca por 54, nao pelo codigo 50 do IBGE."""
        company = self._empresa("ms")
        company.l10n_br_nire_code = "54200123453"
        with self.assertRaisesRegex(ValidationError, "state MS"):
            company.l10n_br_nire_code = "50200123450"
