# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


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
        """Contador e tecnico contabil assinam com o numero do CRC."""
        with self.assertRaises(ValidationError):
            self._criar(name="Contador", qualification="309")

    def test_contabilista_com_crc(self):
        signer = self._criar(name="Contador", qualification="309", crc="1SP123456/O-7")
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

    def test_signatarios_da_empresa_e_ordem(self):
        """A escrituracao e assinada por mais de um, na ordem da sequencia."""
        contador = self._criar(
            name="Contador", qualification="309", crc="1SP123456/O-7", sequence=20
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
