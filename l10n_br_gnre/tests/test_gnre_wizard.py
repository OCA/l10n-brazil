# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGnreWizard(TransactionCase):
    """Geração das guias do período e o ciclo de vida da obrigação."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.state_sp = cls.env.ref("base.state_br_sp")
        cls.state_rj = cls.env.ref("base.state_br_rj")
        cls.tax_group = cls.env.ref("l10n_br_fiscal.tax_group_icmsst")
        cls.document_type = cls.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", "55")], limit=1
        )
        cls.config_sp = cls.env["l10n_br_gnre.state.config"].create(
            {
                "company_id": cls.company.id,
                "fiscal_state_id": cls.state_sp.id,
                "tax_group_id": cls.tax_group.id,
                "revenue_code": "100099",
                "mode": "consolidated",
                "period": "0",
            }
        )
        cls.config_rj = cls.env["l10n_br_gnre.state.config"].create(
            {
                "company_id": cls.company.id,
                "fiscal_state_id": cls.state_rj.id,
                "tax_group_id": cls.tax_group.id,
                "revenue_code": "100099",
                "mode": "document",
            }
        )
        cls.Obligation = cls.env["l10n_br_gnre.obligation"]

    def _obligation(self, config, number, date_due="2026-08-10"):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.document_type.id,
                "document_serie": "1",
                "document_number": f"8800{number}",
                "document_date": "2026-07-15",
            }
        )
        return self.Obligation.create(
            {
                "company_id": self.company.id,
                "document_id": document.id,
                "config_id": config.id,
                "fiscal_state_id": config.fiscal_state_id.id,
                "tax_group_id": self.tax_group.id,
                "revenue_code": config.revenue_code,
                "amount_principal": 100.0,
                "period_ref": "072026",
                "date_due": date_due,
            }
        )

    def _wizard(self, **values):
        return self.env["l10n_br_gnre.generate.wizard"].create(
            dict(
                {
                    "company_id": self.company.id,
                    "date_from": "2026-08-01",
                    "date_to": "2026-08-31",
                },
                **values,
            )
        )

    def test_preview_counts_obligations_and_guides(self):
        """O assistente mostra quantas obrigações e guias vão sair."""
        self._obligation(self.config_sp, "1")
        self._obligation(self.config_sp, "2")
        self._obligation(self.config_rj, "3")
        self._obligation(self.config_rj, "4", date_due="2026-09-10")

        wizard = self._wizard()

        self.assertEqual(wizard.obligation_count, 3)
        self.assertEqual(wizard.guide_count, 2, "SP consolidada, uma guia de RJ")

    def test_generate_creates_the_guides(self):
        sp = self._obligation(self.config_sp, "1") | self._obligation(
            self.config_sp, "2"
        )
        rj = self._obligation(self.config_rj, "3")

        action = self._wizard().action_generate()

        guides = self.env["l10n_br_fiscal.document"].browse(action["domain"][0][2])
        self.assertEqual(len(guides), 2)
        self.assertEqual(sp.guide_id.gnre_obligation_count, 2)
        self.assertEqual(set((sp | rj).mapped("state")), {"grouped"})

    def test_state_filter_limits_the_guides(self):
        self._obligation(self.config_sp, "1")
        rj = self._obligation(self.config_rj, "2")

        wizard = self._wizard(fiscal_state_ids=[(6, 0, self.state_rj.ids)])
        wizard.action_generate()
        wizard.invalidate_recordset()

        self.assertEqual(wizard.obligation_count, 0, "nada pendente sobrou no RJ")
        self.assertEqual(rj.state, "grouped")

    def test_generate_without_obligations_is_refused(self):
        with self.assertRaises(UserError):
            self._wizard().action_generate()

    def test_cancel_pending_obligation(self):
        obligation = self._obligation(self.config_sp, "1")
        obligation.action_cancel()

        self.assertEqual(obligation.state, "cancelled")

    def test_transmitted_obligation_cannot_be_cancelled(self):
        obligation = self._obligation(self.config_sp, "1")
        obligation.state = "transmitted"

        with self.assertRaises(UserError):
            obligation.action_cancel()

    def test_consolidated_rule_requires_a_period(self):
        with self.assertRaises(ValidationError):
            self.config_sp.period = False

    def test_guide_actions(self):
        obligation = self._obligation(self.config_rj, "1")
        guide = self.env["l10n_br_fiscal.document"]._create_gnre_guide(obligation)

        action = guide.action_view_gnre_obligations()
        self.assertEqual(action["domain"], [("guide_id", "=", guide.id)])
        self.assertIn("TLote_GNRE", guide.action_gnre_render_xml())
