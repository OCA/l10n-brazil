# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestAccountGnre(AccountMoveBRCommon):
    """Ciclo completo: nota com ICMS ST, obrigação, guia e conta a pagar."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Traz a serie de documento e as definicoes de imposto da empresa
        # normal, como fazem os demais testes de l10n_br_account.
        cls.configure_normal_company_taxes()
        cls.state_sp = cls.env.ref("base.state_br_sp")
        cls.state_rj = cls.env.ref("base.state_br_rj")
        # O calculo do DIFAL exige o regulamento de ICMS na empresa, senao o
        # map_tax_def_icms_difal estoura em operacao interestadual.
        cls.company_data["company"].write(
            {
                "icms_regulation_id": cls.env.ref(
                    "l10n_br_fiscal.tax_icms_regulation"
                ).id,
            }
        )
        cls.company_data["company"].partner_id.state_id = cls.state_sp

        cls.sefaz_rj = cls.env["res.partner"].create(
            {
                "name": "SEFAZ RJ",
                "state_id": cls.state_rj.id,
                "country_id": cls.env.ref("base.br").id,
                "wh_state_treasury": True,
            }
        )
        cls.customer_rj = cls.env["res.partner"].create(
            {
                "name": "Cliente RJ",
                "state_id": cls.state_rj.id,
                "country_id": cls.env.ref("base.br").id,
            }
        )

        cls.config_rj = cls.env["l10n_br_gnre.state.config"].create(
            {
                "company_id": cls.company_data["company"].id,
                "fiscal_state_id": cls.state_rj.id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_icmsst").id,
                "amount_source": "icmsst",
                "revenue_code": "100102",
                "mode": "document",
                "due_days": 0,
            }
        )

    def _create_invoice(self, icmsst=100.0, fcpst=0.0, partner=None):
        move = self.init_invoice(
            "out_invoice",
            products=[self.product_a],
            partner=partner or self.customer_rj,
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=self.empresa_lc_document_55_serie_1,
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[self.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )
        # O motor fiscal nao calcula ST nesta fixture, entao os valores sao
        # postos na linha fiscal diretamente: o que esta sob teste aqui e o
        # gatilho e o ciclo, nao o calculo do imposto.
        move.fiscal_document_id.fiscal_line_ids.write(
            {"icmsst_value": icmsst, "icmsfcpst_value": fcpst}
        )
        return move

    def test_posting_creates_the_obligation(self):
        """Postar a nota cria a obrigação, e só ela."""
        move = self._create_invoice(icmsst=100.0, fcpst=15.0)
        move.action_post()

        self.assertEqual(len(move.gnre_obligation_ids), 1)
        obligation = move.gnre_obligation_ids
        self.assertEqual(obligation.state, "pending")
        self.assertEqual(obligation.fiscal_state_id, self.state_rj)
        self.assertEqual(obligation.revenue_code, "100102")
        self.assertEqual(obligation.amount_principal, 100.0)
        self.assertEqual(obligation.amount_fcp, 15.0)
        self.assertEqual(obligation.amount_total, 115.0)
        self.assertFalse(obligation.guide_id, "a nota cria a obrigação, nunca a guia")

    def test_authority_comes_from_the_destination_state(self):
        """O credor é a SEFAZ da UF de destino, não um parceiro fixo."""
        move = self._create_invoice()
        move.action_post()

        self.assertEqual(move.gnre_obligation_ids.authority_partner_id, self.sefaz_rj)

    def test_internal_operation_creates_nothing(self):
        """Operação dentro do estado não gera GNRE."""
        customer_sp = self.env["res.partner"].create(
            {
                "name": "Cliente SP",
                "state_id": self.state_sp.id,
                "country_id": self.env.ref("base.br").id,
            }
        )
        move = self._create_invoice(partner=customer_sp)
        move.action_post()

        self.assertFalse(move.gnre_obligation_ids)

    def test_state_without_rule_creates_nothing(self):
        """UF sem regra cadastrada não gera obrigação."""
        customer_mg = self.env["res.partner"].create(
            {
                "name": "Cliente MG",
                "state_id": self.env.ref("base.state_br_mg").id,
                "country_id": self.env.ref("base.br").id,
            }
        )
        move = self._create_invoice(partner=customer_mg)
        move.action_post()

        self.assertFalse(move.gnre_obligation_ids)

    def test_invoice_without_tax_creates_nothing(self):
        """Nota sem ICMS ST não gera obrigação."""
        move = self._create_invoice(icmsst=0.0, fcpst=0.0)
        move.action_post()

        self.assertFalse(move.gnre_obligation_ids)

    def test_guide_creates_the_payable_invoice(self):
        """Emitir a guia cria a conta a pagar contra a SEFAZ."""
        move = self._create_invoice(icmsst=100.0, fcpst=15.0)
        move.action_post()
        obligation = move.gnre_obligation_ids

        guide = self.env["l10n_br_fiscal.document"]._create_gnre_guide(obligation)

        payable = obligation.payable_move_id
        self.assertTrue(payable, "a guia emitida gera o título a pagar")
        self.assertEqual(payable.move_type, "in_invoice")
        self.assertEqual(payable.partner_id, self.sefaz_rj)
        self.assertEqual(payable.amount_total, 115.0)
        self.assertEqual(payable.invoice_date_due, obligation.date_due)
        self.assertEqual(payable.invoice_origin, guide.display_name)

    def test_consolidated_guide_pays_once(self):
        """Guia consolidada gera um título só, com a soma das notas."""
        self.config_rj.write({"mode": "consolidated", "period": "0"})
        obligations = self.env["l10n_br_gnre.obligation"]
        for _index in range(3):
            move = self._create_invoice(icmsst=100.0)
            move.action_post()
            obligations |= move.gnre_obligation_ids

        batches = obligations.group_for_guides()
        self.assertEqual(len(batches), 1, "as três notas numa guia só")

        self.env["l10n_br_fiscal.document"]._create_gnre_guide(batches[0])

        payables = obligations.mapped("payable_move_id")
        self.assertEqual(len(payables), 1)
        self.assertEqual(payables.amount_total, 300.0)

    def test_reset_to_draft_drops_the_obligation(self):
        """Voltar a nota para rascunho apaga a obrigação pendente."""
        move = self._create_invoice()
        move.action_post()
        self.assertTrue(move.gnre_obligation_ids)

        move.button_draft()

        self.assertFalse(move.gnre_obligation_ids)

    def test_reset_to_draft_is_blocked_after_transmission(self):
        """Com guia transmitida, voltar para rascunho é erro explícito."""
        move = self._create_invoice()
        move.action_post()
        obligation = move.gnre_obligation_ids
        self.env["l10n_br_fiscal.document"]._create_gnre_guide(obligation)
        obligation.state = "transmitted"

        with self.assertRaises(UserError):
            move.button_draft()

    def test_vendor_bill_creates_nothing(self):
        """A GNRE de ST nasce na saída, não na entrada."""
        bill = self.init_invoice(
            "in_invoice",
            products=[self.product_a],
            partner=self.customer_rj,
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            document_serie="1",
            document_number="900",
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[
                self.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
            ],
        )
        bill.fiscal_document_id.fiscal_line_ids.write({"icmsst_value": 100.0})
        bill.action_post()

        self.assertFalse(bill.gnre_obligation_ids)

    def test_payable_uses_the_configured_account(self):
        """A conta a pagar da regra sobrepõe a conta padrão do parceiro."""
        account = self.env["account.account"].create(
            {
                "name": "GNRE a Recolher",
                "code": "GNRE210",
                "account_type": "liability_payable",
                "reconcile": True,
                "company_id": self.company_data["company"].id,
            }
        )
        self.config_rj.payable_account_id = account
        move = self._create_invoice()
        move.action_post()
        obligation = move.gnre_obligation_ids

        self.env["l10n_br_fiscal.document"]._create_gnre_guide(obligation)

        payable_lines = obligation.payable_move_id.line_ids.filtered(
            lambda line: line.account_id.account_type == "liability_payable"
        )
        self.assertTrue(payable_lines)
        self.assertEqual(payable_lines.account_id, account)

    def test_obligation_is_linked_both_ways(self):
        """Da nota se chega à obrigação e vice-versa."""
        move = self._create_invoice()
        move.action_post()
        obligation = move.gnre_obligation_ids

        self.assertEqual(obligation.move_id, move)
        self.assertEqual(move.gnre_obligation_count, 1)
        action = move.action_view_gnre_obligations()
        self.assertEqual(action["res_model"], "l10n_br_gnre.obligation")
        self.assertIn(("move_id", "=", move.id), action["domain"])
