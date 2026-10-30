# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGnreObligation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.state_sp = cls.env.ref("base.state_br_sp")
        cls.state_rj = cls.env.ref("base.state_br_rj")
        cls.tax_group_icmsst = cls.env.ref("l10n_br_fiscal.tax_group_icmsst")
        cls.document_type = cls.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", "55")], limit=1
        )

        cls.config_sp_consolidated = cls.env["l10n_br_gnre.state.config"].create(
            {
                "company_id": cls.company.id,
                "fiscal_state_id": cls.state_sp.id,
                "tax_group_id": cls.tax_group_icmsst.id,
                "revenue_code": "100099",
                "mode": "consolidated",
                "period": "0",
                "due_days": 10,
            }
        )
        cls.config_rj_document = cls.env["l10n_br_gnre.state.config"].create(
            {
                "company_id": cls.company.id,
                "fiscal_state_id": cls.state_rj.id,
                "tax_group_id": cls.tax_group_icmsst.id,
                "revenue_code": "100102",
                "mode": "document",
                "due_days": 0,
            }
        )

    @classmethod
    def _create_document(cls, number):
        return cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "document_type_id": cls.document_type.id,
                "document_serie": "1",
                "document_number": number,
                "document_date": "2026-07-15",
            }
        )

    def _create_obligation(self, config, document, amount=100.0, **kwargs):
        values = {
            "company_id": self.company.id,
            "document_id": document.id,
            "config_id": config.id,
            "fiscal_state_id": config.fiscal_state_id.id,
            "tax_group_id": config.tax_group_id.id,
            "revenue_code": config.revenue_code,
            "amount_principal": amount,
            "period_ref": "072026",
            "date_due": "2026-08-10",
        }
        values.update(kwargs)
        return self.env["l10n_br_gnre.obligation"].create(values)

    def test_amount_total_sums_components(self):
        """O total é a soma dos componentes, incluindo o FCP."""
        obligation = self._create_obligation(
            self.config_sp_consolidated,
            self._create_document("1001"),
            amount=100.0,
            amount_fcp=20.0,
            amount_fine=5.0,
            amount_interest=2.0,
        )
        self.assertEqual(obligation.amount_total, 127.0)

    def test_consolidated_groups_documents_into_one_guide(self):
        """Três notas da mesma UF e receita viram uma guia só."""
        obligations = self.env["l10n_br_gnre.obligation"]
        for number in ("2001", "2002", "2003"):
            obligations |= self._create_obligation(
                self.config_sp_consolidated, self._create_document(number)
            )

        batches = obligations.group_for_guides()

        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0]), 3)

    def test_per_document_mode_keeps_one_guide_each(self):
        """Sem inscrição no destino, cada nota gera a sua guia."""
        obligations = self.env["l10n_br_gnre.obligation"]
        for number in ("3001", "3002", "3003"):
            obligations |= self._create_obligation(
                self.config_rj_document, self._create_document(number)
            )

        batches = obligations.group_for_guides()

        self.assertEqual(len(batches), 3)
        self.assertTrue(all(len(batch) == 1 for batch in batches))

    def test_different_states_never_share_a_guide(self):
        """UFs diferentes nunca caem na mesma guia."""
        obligations = self._create_obligation(
            self.config_sp_consolidated, self._create_document("4001")
        )
        obligations |= self._create_obligation(
            self.config_rj_document, self._create_document("4002")
        )

        batches = obligations.group_for_guides()

        self.assertEqual(len(batches), 2)
        states = [batch.mapped("fiscal_state_id") for batch in batches]
        self.assertEqual(len({state.id for state in states[0]}), 1)
        self.assertEqual(len({state.id for state in states[1]}), 1)

    def test_batch_respects_the_hundred_item_limit(self):
        """Mais de 100 itens no mesmo grupo viram mais de uma guia."""
        document = self._create_document("5001")
        obligations = self.env["l10n_br_gnre.obligation"]
        for _index in range(101):
            obligations |= self._create_obligation(
                self.config_sp_consolidated, document
            )

        batches = obligations.group_for_guides()

        self.assertEqual(len(batches), 2)
        self.assertEqual(len(batches[0]), 100)
        self.assertEqual(len(batches[1]), 1)
        self.assertEqual(
            sum(len(batch) for batch in batches),
            101,
            "nenhuma obrigação pode ficar de fora do lote",
        )

    def test_guide_consumes_obligations_and_references_origin(self):
        """A guia nasce tipo 23, referencia as notas e marca as obrigações."""
        obligations = self.env["l10n_br_gnre.obligation"]
        documents = self.env["l10n_br_fiscal.document"]
        for number in ("6001", "6002"):
            document = self._create_document(number)
            documents |= document
            obligations |= self._create_obligation(
                self.config_sp_consolidated, document
            )

        guide = self.env["l10n_br_fiscal.document"]._create_gnre_guide(obligations)

        self.assertEqual(guide.document_type_id.code, "23")
        self.assertEqual(guide.gnre_fiscal_state_id, self.state_sp)
        self.assertEqual(guide.gnre_type, "1", "duas notas de origem")
        self.assertEqual(len(guide.gnre_obligation_ids), 2)
        self.assertEqual(
            set(guide.document_related_ids.mapped("document_related_id").ids),
            set(documents.ids),
        )
        self.assertTrue(all(o.state == "grouped" for o in obligations))

    def test_guide_refuses_mixed_states(self):
        """Montar guia com duas UFs é erro, não silêncio."""
        obligations = self._create_obligation(
            self.config_sp_consolidated, self._create_document("7001")
        )
        obligations |= self._create_obligation(
            self.config_rj_document, self._create_document("7002")
        )

        with self.assertRaises(UserError):
            self.env["l10n_br_fiscal.document"]._create_gnre_guide(obligations)

    def test_grouped_obligation_cannot_be_grouped_again(self):
        """Obrigação já consumida não entra noutra guia."""
        obligations = self._create_obligation(
            self.config_sp_consolidated, self._create_document("8001")
        )
        self.env["l10n_br_fiscal.document"]._create_gnre_guide(obligations)

        with self.assertRaises(UserError):
            obligations.group_for_guides()

    def test_single_revenue_single_document_is_simple_guide(self):
        """Uma nota e uma receita geram GNRE simples."""
        obligations = self._create_obligation(
            self.config_rj_document, self._create_document("9001")
        )
        guide = self.env["l10n_br_fiscal.document"]._create_gnre_guide(obligations)
        self.assertEqual(guide.gnre_type, "0")
