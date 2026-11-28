# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDocumentEntryCst(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company_real = cls.env.ref("l10n_br_base.empresa_lucro_real")
        cls.company_presumed = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Supplier MG",
                "state_id": cls.env.ref("base.state_br_mg").id,
                "country_id": cls.env.ref("base.br").id,
            }
        )
        cls.ncm = cls.env.ref("l10n_br_fiscal.ncm_48191000")
        cls.ncm.tax_ipi_id = cls.env.ref("l10n_br_fiscal.tax_ipi_10")
        cls.product = cls.env["product.product"].create(
            {"name": "Entry product", "default_code": "ENTRY01", "ncm_id": cls.ncm.id}
        )
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.operation_line = cls.env.ref(
            "l10n_br_fiscal.fo_compras_compras_comercializacao"
        )
        cls.cfop_6102 = cls.env.ref("l10n_br_fiscal.cfop_6102")
        cls.cfop_2102 = cls.env.ref("l10n_br_fiscal.cfop_2102")
        cls.number = 4200

    def _document(
        self,
        company,
        imported=True,
        state_edoc="em_digitacao",
        operation=None,
        **line,
    ):
        operation = operation or self.operation
        self.number += 1
        line_values = {
            "name": "Entry line",
            "product_id": self.product.id,
            "uom_id": self.env.ref("uom.product_uom_unit").id,
            "quantity": 1.0,
            "price_unit": 100.0,
            "fiscal_operation_id": operation.id,
            "fiscal_operation_line_id": self.operation_line.id,
            "partner_cfop_id": self.cfop_6102.id,
            "pis_cst_id": self.env.ref("l10n_br_fiscal.cst_pis_01").id,
            "cofins_cst_id": self.env.ref("l10n_br_fiscal.cst_cofins_01").id,
        }
        line_values.update(line)
        return self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "document_serie": "1",
                "document_number": str(self.number),
                "issuer": "partner",
                "partner_id": self.partner.id,
                "fiscal_operation_id": operation.id,
                "fiscal_operation_type": operation.fiscal_operation_type,
                "imported_document": imported,
                "state_edoc": state_edoc,
                "fiscal_line_ids": [Command.create(line_values)],
            }
        )

    def _operation_line_without_cfop(self):
        return self.operation_line.copy(
            {
                "name": "Operation line without CFOP",
                "cfop_internal_id": False,
                "cfop_external_id": False,
                "cfop_export_id": False,
            }
        )

    def test_entry_cfop_is_the_inverse_of_the_supplier_one(self):
        line = self._document(
            self.company_real,
            fiscal_operation_line_id=self._operation_line_without_cfop().id,
        ).fiscal_line_ids
        self.assertEqual(line.cfop_id, self.cfop_2102)

    def test_entry_cfop_is_never_an_outgoing_one(self):
        no_cfop = self._operation_line_without_cfop()
        line = self._document(
            self.company_real, fiscal_operation_line_id=no_cfop.id
        ).fiscal_line_ids
        line.cfop_id = self.cfop_6102
        line.fiscal_operation_line_id = no_cfop.copy({"name": "Another, no CFOP"})
        self.assertEqual(line.cfop_id, self.cfop_2102)

    def test_entry_cfop_of_the_operation_is_kept(self):
        line = self._document(
            self.company_real,
            partner_cfop_id=self.env.ref("l10n_br_fiscal.cfop_6403").id,
        ).fiscal_line_ids
        self.assertEqual(line.cfop_id, self.operation_line.cfop_external_id)

    def test_entry_cfop_safeguard_skips_a_document_not_imported(self):
        line = self._document(
            self.company_real,
            imported=False,
            fiscal_operation_line_id=self._operation_line_without_cfop().id,
        ).fiscal_line_ids
        self.assertFalse(line.cfop_id)

    def test_entry_cst_non_cumulative_regime_takes_the_credit_cst(self):
        line = self._document(self.company_real).fiscal_line_ids
        self.assertEqual(
            line.entry_ipi_cst_id, self.env.ref("l10n_br_fiscal.cst_ipi_00")
        )
        self.assertEqual(line.entry_pis_cst_id.code, "50")
        self.assertEqual(line.entry_cofins_cst_id.code, "50")
        self.assertEqual(line.pis_cst_id.code, "01", "the CST of the file stays")
        self.assertEqual(line.cofins_cst_id.code, "01", "the CST of the file stays")
        self.assertFalse(line._entry_piscofins_without_credit("pis"))
        self.assertFalse(line._entry_piscofins_without_credit("cofins"))

    def test_creditability_map_reads_the_entry_cst_of_an_imported_line(self):
        self.company_real.is_industry = True
        line = self._document(
            self.company_real,
            ipi_cst_id=self.env.ref("l10n_br_fiscal.cst_ipi_50").id,
        ).fiscal_line_ids
        self.assertEqual(line.ipi_cst_id.code, "50", "the CST of the file stays")
        tax_map = line._get_tax_creditability_map()
        self.assertEqual(tax_map["ipi"], "credit")
        self.assertEqual(tax_map["pis"], "credit")
        self.assertEqual(tax_map["cofins"], "credit")

    def test_creditability_map_of_an_imported_use_and_consumption(self):
        self.company_real.is_industry = True
        line = self._document(
            self.company_real,
            fiscal_operation_line_id=self.env.ref(
                "l10n_br_fiscal.fo_compras_compras_uso_consumo"
            ).id,
            ipi_cst_id=self.env.ref("l10n_br_fiscal.cst_ipi_50").id,
        ).fiscal_line_ids
        tax_map = line._get_tax_creditability_map()
        self.assertEqual(tax_map["ipi"], "cost")
        self.assertEqual(tax_map["pis"], "cost")
        self.assertEqual(tax_map["cofins"], "cost")

    def _opt_in(self, company, value=True):
        if "stock_valuation_via_stock_price" not in company._fields:
            self.skipTest("l10n_br_stock_account is not installed")
        company.stock_valuation_via_stock_price = value

    def _assert_entry_without_piscofins_credit(self, operation_line, type_move):
        self._opt_in(self.company_real)
        line = self._document(
            self.company_real,
            fiscal_operation_line_id=self.env.ref(
                f"l10n_br_fiscal.{operation_line}"
            ).id,
        ).fiscal_line_ids
        self.assertEqual(line.cfop_id.type_move, type_move)
        self.assertEqual(line.entry_pis_cst_id.code, "70")
        self.assertEqual(line.entry_cofins_cst_id.code, "70")
        self.assertTrue(line._entry_piscofins_without_credit("pis"))
        self.assertTrue(line._entry_piscofins_without_credit("cofins"))

    def test_entry_cst_non_cumulative_use_and_consumption_books_70(self):
        self._assert_entry_without_piscofins_credit(
            "fo_compras_compras_uso_consumo", "purchase_ownuse"
        )

    def test_entry_cst_non_cumulative_fixed_asset_books_70(self):
        self._assert_entry_without_piscofins_credit(
            "fo_compras_compras_ativo", "purchase_asset"
        )

    def test_entry_cst_of_a_company_that_did_not_opt_in_keeps_the_credit(self):
        """Its ledger credits PIS and COFINS of use and consumption, so the
        entry keeps the credit CST and the books match the ledger."""
        self._opt_in(self.company_real, False)
        line = self._document(
            self.company_real,
            fiscal_operation_line_id=self.env.ref(
                "l10n_br_fiscal.fo_compras_compras_uso_consumo"
            ).id,
        ).fiscal_line_ids
        self.assertEqual(line.cfop_id.type_move, "purchase_ownuse")
        self.assertTrue(line.entry_pis_cst_id.default_creditable_tax)
        self.assertTrue(line.entry_cofins_cst_id.default_creditable_tax)
        self.assertFalse(line._entry_piscofins_without_credit("pis"))

    def test_entry_cst_cumulative_regime_books_70(self):
        line = self._document(self.company_presumed).fiscal_line_ids
        self.assertEqual(
            line.entry_pis_cst_id, self.env.ref("l10n_br_fiscal.cst_pis_70")
        )
        self.assertEqual(
            line.entry_cofins_cst_id, self.env.ref("l10n_br_fiscal.cst_cofins_70")
        )
        self.assertEqual(line.pis_cst_id.code, "01", "the CST of the file stays")
        self.assertTrue(line._entry_piscofins_without_credit("pis"))
        self.assertTrue(line._entry_piscofins_without_credit("cofins"))

    def test_entry_cst_follows_the_regime_of_the_company(self):
        line = self._document(self.company_real).fiscal_line_ids
        self.assertEqual(line.entry_pis_cst_id.code, "50")
        self.company_real.profit_calculation = "presumed"
        self.assertEqual(line.entry_pis_cst_id.code, "70")

    def test_entry_cst_empty_for_a_document_not_imported(self):
        line = self._document(self.company_presumed, imported=False).fiscal_line_ids
        self.assertFalse(line.entry_ipi_cst_id)
        self.assertFalse(line.entry_pis_cst_id)
        self.assertFalse(line.entry_cofins_cst_id)
        self.assertFalse(line._entry_piscofins_without_credit("pis"))

    def test_entry_cst_empty_for_an_outgoing_document(self):
        line = self._document(
            self.company_presumed,
            operation=self.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_line_id=self.env.ref("l10n_br_fiscal.fo_venda_venda").id,
            partner_cfop_id=False,
        ).fiscal_line_ids
        self.assertEqual(line.fiscal_operation_type, "out")
        self.assertFalse(line.entry_pis_cst_id)
        self.assertFalse(line.entry_cofins_cst_id)

    def test_partner_benefit_code_is_kept_as_declared(self):
        line = self._document(
            self.company_real, partner_icms_tax_benefit_code="SP12345678"
        ).fiscal_line_ids
        line._compute_fiscal_tax_ids()
        self.assertEqual(line.partner_icms_tax_benefit_code, "SP12345678")

    def _stale_entry(self, state_edoc="em_digitacao"):
        document = self._document(self.company_presumed, state_edoc=state_edoc)
        line = document.fiscal_line_ids
        self.assertEqual(line.entry_pis_cst_id.code, "70")
        line.write(
            {
                "entry_pis_cst_id": self.env.ref("l10n_br_fiscal.cst_pis_50").id,
                "entry_cofins_cst_id": self.env.ref("l10n_br_fiscal.cst_cofins_50").id,
            }
        )
        return document, line

    def test_recompute_entry_cst_logs_what_changed(self):
        document, line = self._stale_entry()
        document.action_recompute_entry_cst()
        self.assertEqual(line.entry_pis_cst_id.code, "70")
        self.assertEqual(line.entry_cofins_cst_id.code, "70")
        body = " ".join(document.message_ids.mapped("body"))
        self.assertIn("Item 1, CST of the PIS: 50 to 70", body)
        self.assertIn("Item 1, CST of the COFINS: 50 to 70", body)
        self.assertNotIn("CST of the IPI", body)

    def test_recompute_entry_cst_without_change_logs_nothing(self):
        document = self._document(self.company_presumed)
        messages = document.message_ids
        document.action_recompute_entry_cst()
        self.assertEqual(document.message_ids, messages)

    def test_recompute_entry_cst_refuses_a_confirmed_document(self):
        document, line = self._stale_entry(state_edoc="a_enviar")
        with self.assertRaises(UserError):
            document.action_recompute_entry_cst()
        self.assertEqual(line.entry_pis_cst_id.code, "50")

    def test_recompute_entry_cst_refuses_a_document_not_imported(self):
        document = self._document(self.company_presumed, imported=False)
        with self.assertRaises(UserError):
            document.action_recompute_entry_cst()

    def test_recompute_entry_cst_selection_skips_the_confirmed_ones(self):
        typing, typing_line = self._stale_entry()
        confirmed, confirmed_line = self._stale_entry(state_edoc="a_enviar")
        action = (typing | confirmed).action_recompute_entry_cst_selection()
        self.assertEqual(typing_line.entry_pis_cst_id.code, "70")
        self.assertEqual(confirmed_line.entry_pis_cst_id.code, "50")
        self.assertEqual(action["tag"], "display_notification")
        self.assertIn("1 document(s) recalculated, 1 left", action["params"]["message"])
