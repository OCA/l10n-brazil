# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import DUIMP_NUMBER, PRODUCT_CODE_1, DuimpCommon


@tagged("post_install", "-at_install")
class TestDuimpDeclaracao(DuimpCommon):
    def test_import_payload_creates_persistent_records(self):
        declaracao = self._create_declaracao()
        self.assertEqual(declaracao.numero, DUIMP_NUMBER)
        self.assertEqual(declaracao.versao, 1)
        self.assertEqual(declaracao.situacao, "REGISTRADA")
        self.assertEqual(len(declaracao.item_ids), 2)
        self.assertEqual(len(declaracao.pagamento_ids), 1)
        # header federal taxes
        self.assertAlmostEqual(declaracao.ii_total, 1541.00)
        self.assertAlmostEqual(declaracao.cofins_total, 970.00)

    def test_import_payload_maps_item_fields(self):
        declaracao = self._create_declaracao()
        item = declaracao.item_ids.filtered(lambda i: i.numero_item == "1")
        self.assertEqual(item.codigo_produto, PRODUCT_CODE_1)
        self.assertEqual(item.ncm_codigo, "84821010")
        self.assertAlmostEqual(item.quantidade, 100.0)
        self.assertAlmostEqual(item.valor_aduaneiro, 5300.00)
        self.assertAlmostEqual(item.price_unit, 50.00)  # 5000 / 100
        self.assertEqual(len(item.tributo_ids), 1)
        self.assertEqual(item.tributo_ids.tipo, "II")
        self.assertAlmostEqual(item.tributo_ids.valor_devido, 848.00)

    def test_auto_match_product_by_code(self):
        declaracao = self._create_declaracao()
        item1 = declaracao.item_ids.filtered(lambda i: i.numero_item == "1")
        item2 = declaracao.item_ids.filtered(lambda i: i.numero_item == "2")
        self.assertEqual(item1.product_id, self.product_1)
        self.assertEqual(item2.product_id, self.product_2)

    def test_total_customs_value(self):
        declaracao = self._create_declaracao()
        self.assertAlmostEqual(declaracao.total_valor_aduaneiro, 5300.00 + 4950.00)

    def test_cost_allocation_by_customs_value(self):
        # AFRMM 1000 + Siscomex 300 allocated proportionally to the
        # customs value of each item (5300 / 10250 and 4950 / 10250).
        declaracao = self._create_declaracao(afrmm=1000.0, siscomex=300.0)
        item1 = declaracao.item_ids.filtered(lambda i: i.numero_item == "1")
        item2 = declaracao.item_ids.filtered(lambda i: i.numero_item == "2")
        total = 5300.00 + 4950.00
        self.assertAlmostEqual(item1.amount_afrmm, 1000.0 * 5300.0 / total, places=2)
        self.assertAlmostEqual(item2.amount_afrmm, 1000.0 * 4950.0 / total, places=2)
        self.assertAlmostEqual(item1.amount_siscomex, 300.0 * 5300.0 / total, places=2)
        # amount_other = afrmm + siscomex + capatazia
        self.assertAlmostEqual(
            item1.amount_other, item1.amount_afrmm + item1.amount_siscomex, places=2
        )
        # total AFRMM allocated must equal the header value
        self.assertAlmostEqual(
            sum(declaracao.item_ids.mapped("amount_afrmm")), 1000.0, places=2
        )

    def test_addition_deduction_changes_final_price(self):
        declaracao = self._create_declaracao()
        item = declaracao.item_ids.filtered(lambda i: i.numero_item == "1")
        # without additions/deductions, final == price_unit
        self.assertAlmostEqual(item.final_price_unit, item.price_unit)
        self.env["l10n_br_duimp.acrescimo.deducao"].create(
            {"item_id": item.id, "denominacao": "Royalties", "valor": 500.00}
        )
        item.invalidate_recordset()
        # +500 over 100 units => +5.0/unit
        self.assertAlmostEqual(item.unit_addition_deduction, 5.0)
        self.assertAlmostEqual(item.final_price_unit, item.price_unit + 5.0)

    def test_prepare_document_line_uses_per_item_taxes(self):
        declaracao = self._create_declaracao(afrmm=1000.0, siscomex=300.0)
        item = declaracao.item_ids.filtered(lambda i: i.numero_item == "1")
        vals = declaracao._prepare_document_line_values(
            self.env["l10n_br_fiscal.document"], item
        )
        self.assertEqual(vals["duimp_item_id"], item.id)
        self.assertEqual(vals["product_id"], self.product_1.id)
        self.assertAlmostEqual(vals["ii_value"], 848.00)
        self.assertAlmostEqual(vals["ii_base"], 5300.00)
        self.assertAlmostEqual(vals["ii_percent"], 16.0)
        # AFRMM booked separately; other_value carries siscomex + capatazia
        self.assertAlmostEqual(vals["afrmm_value"], item.amount_afrmm, places=2)
        self.assertAlmostEqual(vals["other_value"], item.amount_siscomex, places=2)

    def test_generate_invoice_requires_products(self):
        declaracao = self._create_declaracao()
        declaracao.item_ids.write({"product_id": False})
        declaracao.fornecedor_partner_id = self.vendor
        with self.assertRaises(UserError):
            declaracao.action_generate_vendor_bill()

    def test_generate_invoice_requires_vendor(self):
        declaracao = self._create_declaracao()
        declaracao.item_ids.write({"cfop_id": False})
        with self.assertRaises(UserError):
            declaracao.action_generate_vendor_bill()

    def test_state_machine(self):
        declaracao = self._create_declaracao()
        self.assertEqual(declaracao.state, "draft")
        declaracao.action_open()
        self.assertEqual(declaracao.state, "open")
        declaracao.action_cancel()
        self.assertEqual(declaracao.state, "canceled")
        declaracao.action_draft()
        self.assertEqual(declaracao.state, "draft")

    def test_refresh_blocked_when_locked(self):
        declaracao = self._create_declaracao()
        declaracao.state = "locked"
        with self.assertRaises(UserError):
            declaracao.action_refresh_from_siscomex()
