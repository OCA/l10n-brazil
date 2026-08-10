# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from io import StringIO

from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestBlocoE(common.TransactionCase):
    """O bloco E serializa a apuração, não recalcula.

    É o contrato que faz a escrituração, a contabilidade e a guia falarem o
    mesmo número. Estes testes conferem valor, não presença: um E110 gerado
    com zeros passaria num teste de presença e reprovaria no PVA.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.group = cls.env["account.tax.group"].create(
            {
                "name": "ICMS (bloco E)",
                "fiscal_tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_icms").id,
            }
        )
        cls.assessment = cls.env["l10n_br_tax.assessment"].create(
            {
                "company_id": cls.company.id,
                "tax_group_id": cls.group.id,
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
            }
        )
        Line = cls.env["l10n_br_tax.assessment.line"]
        # apurado das move lines: campos 02 e 06 do E110
        Line.create(
            {
                "assessment_id": cls.assessment.id,
                "kind": "debit",
                "tax_amount": 1000.0,
                "source": "computed",
            }
        )
        Line.create(
            {
                "assessment_id": cls.assessment.id,
                "kind": "credit",
                "tax_amount": 400.0,
                "source": "computed",
            }
        )
        # ajustes manuais: viram E111 e alimentam os campos 04, 05 e 12
        Line.create(
            {
                "assessment_id": cls.assessment.id,
                "kind": "debit",
                "tax_amount": 50.0,
                "source": "manual",
                "adjustment_code": "SP100001",
                "description": "outros débitos",
            }
        )
        Line.create(
            {
                "assessment_id": cls.assessment.id,
                "kind": "debit",
                "tax_amount": 20.0,
                "source": "manual",
                "adjustment_code": "SP110001",
                "description": "estorno de crédito",
            }
        )
        Line.create(
            {
                "assessment_id": cls.assessment.id,
                "kind": "deduction",
                "tax_amount": 70.0,
                "source": "manual",
                "adjustment_code": "SP140001",
                "description": "dedução",
            }
        )
        cls.assessment.state = "computed"

        cls.declaration = cls.env["l10n_br_sped.efd_icms_ipi.0000"].create(
            {
                "company_id": cls.company.id,
                "DT_INI": "2026-07-01",
                "DT_FIN": "2026-07-31",
            }
        )

    def _pull_bloco_e(self):
        # mesmo contexto que `button_populate_sped_from_odoo` monta: o
        # `default_declaration_id` e quem amarra cada registro criado a
        # declaracao, e sem ele o create esbarra no not-null.
        model = self.env["l10n_br_sped.efd_icms_ipi.e100"].with_context(
            company_id=self.company.id,
            declaration=self.declaration,
            default_declaration_id=self.declaration.id,
        )
        model._pull_records_from_odoo("efd_icms_ipi", 2, log_msg=StringIO())
        return self.env["l10n_br_sped.efd_icms_ipi.e100"].search(
            [("declaration_id", "=", self.declaration.id)]
        )

    def test_e110_serializes_the_assessment(self):
        e100 = self._pull_bloco_e()
        self.assertEqual(len(e100), 1)
        e110 = e100.reg_E110_ids
        self.assertEqual(len(e110), 1, "E110 é 1:1 dentro do E100")

        self.assertAlmostEqual(e110.VL_TOT_DEBITOS, 1000.0, places=2)
        self.assertAlmostEqual(e110.VL_TOT_CREDITOS, 400.0, places=2)
        self.assertAlmostEqual(e110.VL_TOT_AJ_DEBITOS, 50.0, places=2)
        self.assertAlmostEqual(e110.VL_ESTORNOS_CRED, 20.0, places=2)
        self.assertAlmostEqual(e110.VL_TOT_DED, 70.0, places=2)
        # 1000 + 50 + 20 - 400 = 670 de saldo devedor apurado
        self.assertAlmostEqual(e110.VL_SLD_APURADO, 670.0, places=2)
        # 670 - 70 de deducao
        self.assertAlmostEqual(e110.VL_ICMS_RECOLHER, 600.0, places=2)
        self.assertAlmostEqual(e110.VL_SLD_CREDOR_TRANSPORTAR, 0.0, places=2)

    def test_e110_matches_the_assessment_totals(self):
        """O E110 não pode divergir da apuração: ele é uma projeção dela."""
        e110 = self._pull_bloco_e().reg_E110_ids
        self.assertAlmostEqual(
            e110.VL_ICMS_RECOLHER, self.assessment.amount_payable, places=2
        )
        self.assertAlmostEqual(
            e110.VL_SLD_APURADO, self.assessment.assessed_balance, places=2
        )

    def test_e111_only_carries_manual_adjustments(self):
        """Linha apurada não vira E111: já está somada no campo 02 do E110."""
        e111 = self._pull_bloco_e().reg_E110_ids.reg_E111_ids
        self.assertEqual(len(e111), 3)
        self.assertEqual(
            sorted(e111.mapped("COD_AJ_APUR")),
            ["SP100001", "SP110001", "SP140001"],
        )
        estorno = e111.filtered(lambda r: r.COD_AJ_APUR == "SP110001")
        self.assertAlmostEqual(estorno.VL_AJ_APUR, 20.0, places=2)
        self.assertEqual(estorno.DESCR_COMPL_AJ, "estorno de crédito")

    def test_draft_assessment_is_not_serialized(self):
        """Escriturar apuração em rascunho seria escriturar número não conferido."""
        self.assessment.state = "draft"
        self.assertFalse(self._pull_bloco_e().reg_E110_ids)
