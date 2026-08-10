# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestTaxAssessment(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.Assessment = cls.env["l10n_br_tax.assessment"]

        cls.account_payable = cls.env["account.account"].create(
            {
                "name": "ICMS a recolher",
                "code": "TSTPAY",
                "account_type": "liability_current",
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.account_receivable = cls.env["account.account"].create(
            {
                "name": "ICMS a recuperar",
                "code": "TSTREC",
                "account_type": "asset_current",
                "company_id": cls.company_data["company"].id,
            }
        )

    def setUp(self):
        super().setUp()
        # Um grupo por teste: `property_tax_payable_account_id` e
        # company_dependent (ir.property) e o cache nao acompanha o rollback,
        # entao um grupo de classe faria o teste que configura as contas
        # contaminar o que espera encontra-las vazias.
        self.group = self.env["account.tax.group"].create({"name": "ICMS (teste)"})

    def _configure_group(self):
        self.group.with_company(self.company_data["company"]).write(
            {
                "property_tax_payable_account_id": self.account_payable.id,
                "property_tax_receivable_account_id": self.account_receivable.id,
            }
        )

    def _new_assessment(
        self, date_from="2026-07-01", date_to="2026-07-31", regime="not_applicable"
    ):
        return self.Assessment.create(
            {
                "company_id": self.company_data["company"].id,
                "tax_group_id": self.group.id,
                "date_from": date_from,
                "date_to": date_to,
                "regime": regime,
            }
        )

    def _add_line(self, assessment, kind, tax_amount, source="manual", code=None):
        vals = {
            "assessment_id": assessment.id,
            "kind": kind,
            "tax_amount": tax_amount,
            "source": source,
            "description": "ajuste de teste",
        }
        if code:
            vals["adjustment_code"] = code
        return self.env["l10n_br_tax.assessment.line"].create(vals)

    # ------------------------------------------------------------------
    # conta grafica
    # ------------------------------------------------------------------

    def test_balance_is_debit_minus_credit(self):
        """O saldo do período é débito menos crédito."""
        a = self._new_assessment()
        self._add_line(a, "debit", 1000.0)
        self._add_line(a, "credit", 300.0)
        self.assertEqual(a.balance, 700.0)
        self.assertEqual(a.amount_payable, 700.0)
        self.assertEqual(a.amount_carried_forward, 0.0)

    def test_credit_balance_is_carried_forward_not_payable(self):
        """Crédito maior que débito não vira imposto a recolher negativo.

        Vira saldo credor a transportar. Confundir os dois e o erro que faz a
        guia sair com valor negativo.
        """
        a = self._new_assessment()
        self._add_line(a, "debit", 200.0)
        self._add_line(a, "credit", 500.0)
        self.assertEqual(a.balance, -300.0)
        self.assertEqual(a.amount_payable, 0.0)
        self.assertEqual(a.amount_carried_forward, 300.0)

    def test_previous_credit_balance_is_deducted(self):
        """O saldo credor do período anterior entra na apuração seguinte."""
        jun = self._new_assessment("2026-06-01", "2026-06-30")
        self._add_line(jun, "credit", 400.0)
        jun.state = "computed"
        self.assertEqual(jun.amount_carried_forward, 400.0)

        jul = self._new_assessment()
        jul.action_compute()
        self.assertEqual(jul.previous_assessment_id, jun)
        self.assertEqual(jul.previous_balance, 400.0)

        self._add_line(jul, "debit", 1000.0)
        # 1000 de debito menos 400 de credito anterior
        self.assertEqual(jul.balance, 600.0)
        self.assertEqual(jul.amount_payable, 600.0)

    # ------------------------------------------------------------------
    # ajustes da tabela 5.1.1, que e o que o E110 e o E111 exigem
    # ------------------------------------------------------------------

    def test_adjustment_code_classifies_the_line(self):
        """O quarto dígito do COD_AJ_APUR decide o campo do E110.

        SP1 0 0001 é outros débitos, SP1 1 0001 é estorno de crédito: os dois
        somam do lado devedor, mas o fisco os quer em campos diferentes.
        """
        a = self._new_assessment()
        self._add_line(a, "debit", 100.0, code="SP100001")
        self._add_line(a, "debit", 40.0, code="SP110001")
        self._add_line(a, "credit", 30.0, code="SP120001")
        self._add_line(a, "credit", 25.0, code="SP130001")

        self.assertEqual(a.adjustment_debit_total, 100.0)
        self.assertEqual(a.credit_reversal_total, 40.0)
        self.assertEqual(a.adjustment_credit_total, 30.0)
        self.assertEqual(a.debit_reversal_total, 25.0)
        # apurado e ajuste nao se misturam: campos 02 e 06 ficam zerados
        self.assertEqual(a.debit_total, 0.0)
        self.assertEqual(a.credit_total, 0.0)
        # o confronto usa os quatro: 140 de debito contra 55 de credito
        self.assertEqual(a.balance, 85.0)

    def test_deduction_reduces_payable_but_not_the_balance(self):
        """Dedução abate o que já foi apurado, não entra no confronto.

        Somar dedução como crédito produziria saldo credor a transportar onde
        na verdade não há crédito nenhum.
        """
        a = self._new_assessment()
        self._add_line(a, "debit", 1000.0)
        self._add_line(a, "deduction", 300.0, code="SP140001")
        self.assertEqual(a.balance, 1000.0)
        self.assertEqual(a.assessed_balance, 1000.0)
        self.assertEqual(a.deduction_total, 300.0)
        self.assertEqual(a.amount_payable, 700.0)
        self.assertEqual(a.amount_carried_forward, 0.0)

    def test_deduction_never_makes_payable_negative(self):
        """Dedução maior que o devido não vira crédito nem valor negativo."""
        a = self._new_assessment()
        self._add_line(a, "debit", 100.0)
        self._add_line(a, "deduction", 250.0, code="SP140001")
        self.assertEqual(a.amount_payable, 0.0)
        self.assertEqual(a.amount_carried_forward, 0.0)

    def test_special_debit_does_not_touch_the_balance(self):
        """Débito especial é extra-apuração: informa, não apura."""
        a = self._new_assessment()
        self._add_line(a, "debit", 500.0)
        self._add_line(a, "special_debit", 80.0, code="SP150001")
        self.assertEqual(a.special_debit_total, 80.0)
        self.assertEqual(a.balance, 500.0)
        self.assertEqual(a.amount_payable, 500.0)

    def test_adjustment_code_inconsistent_with_kind_is_refused(self):
        """Estorno de crédito lançado como crédito inverteria o imposto."""
        a = self._new_assessment()
        with self.assertRaises(ValidationError):
            self._add_line(a, "credit", 40.0, code="SP110001")

    def test_malformed_adjustment_code_is_refused(self):
        a = self._new_assessment()
        with self.assertRaises(ValidationError):
            self._add_line(a, "debit", 10.0, code="SP1")
        with self.assertRaises(ValidationError):
            # nono digito de tipo de ajuste nao existe na tabela 5.1.1
            self._add_line(a, "debit", 10.0, code="SP190001")

    def test_manual_line_requires_description(self):
        """Ajuste sem justificativa não tem o que escrever no E111."""
        a = self._new_assessment()
        with self.assertRaises(ValidationError):
            self.env["l10n_br_tax.assessment.line"].create(
                {
                    "assessment_id": a.id,
                    "kind": "debit",
                    "tax_amount": 10.0,
                    "source": "manual",
                }
            )

    def test_withholding_reduces_payable_in_its_own_field(self):
        """Retenção na fonte abate o devido, mas não se confunde com dedução.

        O M200 da EFD Contribuições pede as duas em campos separados, e somar
        uma na outra tornaria impossível reconstruir o registro.
        """
        a = self._new_assessment()
        self._add_line(a, "debit", 1000.0)
        self._add_line(a, "deduction", 100.0, code="SP140001")
        self._add_line(a, "withholding", 250.0)
        self.assertEqual(a.deduction_total, 100.0)
        self.assertEqual(a.withholding_total, 250.0)
        self.assertEqual(a.balance, 1000.0)
        self.assertEqual(a.amount_payable, 650.0)

    def test_same_period_two_regimes_coexist(self):
        """PIS cumulativo e não cumulativo são apurações distintas.

        A EFD Contribuições exige os dois separados no M200; forçá-los numa
        apuração só perderia a informação que o registro pede.
        """
        nc = self._new_assessment(regime="non_cumulative")
        cum = self._new_assessment(regime="cumulative")
        self.assertNotEqual(nc, cum)
        self._add_line(nc, "debit", 300.0)
        self._add_line(cum, "debit", 120.0)
        self.assertEqual(nc.amount_payable, 300.0)
        self.assertEqual(cum.amount_payable, 120.0)

    def test_previous_balance_does_not_cross_regimes(self):
        """Saldo credor do cumulativo não abate o não cumulativo."""
        jun = self._new_assessment("2026-06-01", "2026-06-30", regime="cumulative")
        self._add_line(jun, "credit", 500.0)
        jun.state = "computed"

        jul = self._new_assessment(regime="non_cumulative")
        jul.action_compute()
        self.assertFalse(jul.previous_assessment_id)
        self.assertEqual(jul.previous_balance, 0.0)

    # ------------------------------------------------------------------
    # critica
    # ------------------------------------------------------------------

    def test_post_without_configured_accounts_raises(self):
        """Sem as contas do grupo de imposto não se encerra.

        O plano de contas instala `ir.property` GLOBAIS (res_id=False) para
        `property_tax_payable_account_id` e irmã, então todo grupo novo já
        nasce com conta. Para exercitar a crítica é preciso limpar
        explicitamente a propriedade da empresa, que é o cenário real que a
        guarda protege: base sem plano de contas, ou empresa cuja propriedade
        foi apagada.
        """
        self.group.with_company(self.company_data["company"]).write(
            {
                "property_tax_payable_account_id": False,
                "property_tax_receivable_account_id": False,
            }
        )
        a = self._new_assessment()
        a.action_compute()
        with self.assertRaises(UserError) as ctx:
            a.action_post()
        self.assertIn("grupo de imposto", str(ctx.exception))

    def test_post_requires_computed_state(self):
        a = self._new_assessment()
        with self.assertRaises(UserError):
            a.action_post()

    # ------------------------------------------------------------------
    # encerramento
    # ------------------------------------------------------------------

    def test_closing_move_is_balanced_and_uses_group_accounts(self):
        """O lançamento fecha e usa as contas que o core já modela no grupo."""
        self._configure_group()
        a = self._new_assessment()
        a.action_compute()
        self._add_line(a, "debit", 1000.0)
        self._add_line(a, "credit", 250.0)
        a.action_post()

        self.assertEqual(a.state, "posted")
        move = a.move_id
        self.assertTrue(move)
        self.assertAlmostEqual(
            sum(move.line_ids.mapped("debit")),
            sum(move.line_ids.mapped("credit")),
            places=2,
            msg="lançamento de encerramento tem que fechar",
        )
        contas = move.line_ids.mapped("account_id")
        self.assertIn(self.account_payable, contas)
        self.assertIn(self.account_receivable, contas)
        # devedor de 750: credita a recuperar, debita a pagar
        linha_pagar = move.line_ids.filtered(
            lambda line: line.account_id == self.account_payable
        )
        self.assertAlmostEqual(linha_pagar.debit, 750.0, places=2)

    def test_period_without_movement_closes_without_move(self):
        """Período sem movimento fecha sem lançamento, mas fecha.

        É o que mantém a cadeia de saldo credor sem buraco: pular o período
        faria a apuração seguinte procurar a anterior e não achar.
        """
        self._configure_group()
        a = self._new_assessment()
        a.action_compute()
        a.action_post()
        self.assertEqual(a.state, "posted")
        self.assertFalse(a.move_id)

    def test_recompute_keeps_manual_adjustments(self):
        """Reapurar refaz o que veio das move lines e preserva o ajuste manual.

        É o que permite corrigir a apuração sem perder o E111 digitado.
        """
        a = self._new_assessment()
        a.action_compute()
        self._add_line(a, "debit", 90.0, source="manual")
        a.action_compute()
        manuais = a.line_ids.filtered(lambda line: line.source == "manual")
        self.assertEqual(len(manuais), 1)
        self.assertAlmostEqual(manuais.tax_amount, 90.0, places=2)

    @mute_logger("odoo.sql_db")
    def test_same_period_and_group_cannot_be_duplicated(self):
        """Duas apurações do mesmo grupo, regime e período dobrariam o imposto.

        O regime entra na chave com valor obrigatório justamente para isto
        continuar valendo: com regime nulo o Postgres deixaria a duplicata
        passar, porque NULL nunca é igual a NULL.
        """
        self._new_assessment()
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self._new_assessment()

    def test_draft_again_removes_the_closing_move(self):
        self._configure_group()
        a = self._new_assessment()
        a.action_compute()
        self._add_line(a, "debit", 500.0)
        a.action_post()
        self.assertTrue(a.move_id)
        a.action_draft()
        self.assertEqual(a.state, "draft")
        self.assertFalse(a.move_id)


@tagged("post_install", "-at_install")
class TestTaxAssessmentDemo(AccountTestInvoicingCommon):
    """O dado de demonstração precisa apurar de verdade, não só existir.

    O período é calculado na instalação, então um demo que só fosse criado
    passaria neste teste enquanto mostrasse uma apuração de mês errado.
    """

    def test_demo_assessment_is_computed_for_the_current_month(self):
        assessment = self.env.ref(
            "l10n_br_tax_assessment.demo_assessment_icms", raise_if_not_found=False
        )
        if not assessment:
            self.skipTest("base sem dados de demonstração")
        # O dado demo vive na empresa brasileira da localização, que não é a
        # do usuário de teste, e a `ir.rule` multi-empresa barra a leitura.
        # Ler em sudo mantém este teste sobre o DADO, sem transformá-lo num
        # teste de multi-empresa.
        assessment = assessment.sudo()
        today = fields.Date.context_today(assessment)
        self.assertEqual(assessment.state, "computed")
        self.assertEqual(assessment.tax_domain, "icms")
        self.assertEqual(assessment.date_from, today.replace(day=1))
        self.assertEqual(assessment.date_to.month, today.month)
        self.assertEqual(assessment.date_to.year, today.year)
        # o grupo tem que ser o dos impostos da empresa, senao a apuracao le
        # de um grupo que nenhum lancamento usa
        self.assertTrue(assessment._get_taxes())

    def test_demo_adjustment_is_classified_by_its_code(self):
        line = self.env.ref(
            "l10n_br_tax_assessment.demo_assessment_icms_adjustment",
            raise_if_not_found=False,
        )
        if not line:
            self.skipTest("base sem dados de demonstração")
        line = line.sudo()
        self.assertEqual(line.adjustment_kind, "other_debit")
        self.assertEqual(line.kind, "debit")
