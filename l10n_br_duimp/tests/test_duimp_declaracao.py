# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import DUIMP_NUMBER, PRODUCT_CODE_1, DuimpCommon


@tagged("post_install", "-at_install")
class TestDuimpDeclaracao(DuimpCommon):
    def test_import_payload_creates_persistent_records(self):
        declaracao = self._create_declaracao()
        self.assertEqual(declaracao.number, DUIMP_NUMBER)
        self.assertEqual(declaracao.version, 1)
        self.assertEqual(declaracao.status, "REGISTRADA")
        self.assertEqual(len(declaracao.item_ids), 2)
        self.assertEqual(len(declaracao.payment_ids), 1)
        # header federal taxes
        self.assertAlmostEqual(declaracao.ii_amount, 1541.00)
        self.assertAlmostEqual(declaracao.cofins_amount, 970.00)

    def test_import_payload_maps_item_fields(self):
        declaracao = self._create_declaracao()
        item = declaracao.item_ids.filtered(lambda i: i.item_number == "1")
        self.assertEqual(item.product_code, PRODUCT_CODE_1)
        self.assertEqual(item.ncm_code, "84821010")
        self.assertAlmostEqual(item.quantity, 100.0)
        self.assertAlmostEqual(item.customs_value, 5300.00)
        self.assertAlmostEqual(item.price_unit, 50.00)  # 5000 / 100
        self.assertEqual(len(item.tax_ids), 1)
        self.assertEqual(item.tax_ids.type, "II")
        self.assertAlmostEqual(item.tax_ids.amount_due, 848.00)

    def test_import_payload_maps_parties_and_clearance(self):
        """The parties/clearance/cargo header block must come out of the
        payload: l10n_br_duimp_nfe turns the clearance and transport
        fields into the NF-e import-declaration group, where the layout
        requires them.
        """
        declaracao = self._create_declaracao()
        self.assertEqual(declaracao.importer_name, "Test Importer SA")
        self.assertEqual(declaracao.importer_number, "12345678000195")
        self.assertEqual(declaracao.incoterm, "FOB")
        self.assertEqual(declaracao.clearance_office_name, "PORTO DE SANTOS")
        self.assertEqual(declaracao.clearance_state, "SP")
        self.assertEqual(str(declaracao.clearance_date), "2026-02-10")
        self.assertEqual(declaracao.transport_mode_code, "01")
        self.assertEqual(declaracao.operation_type_code, "1")
        self.assertAlmostEqual(declaracao.total_freight, 300.00)
        self.assertAlmostEqual(declaracao.total_insurance, 150.00)

    def test_payload_path_missing_steps(self):
        declaracao = self._create_declaracao()
        payload = {"despacho": {"urfDespacho": {"nome": "SANTOS"}}}
        self.assertEqual(
            declaracao._payload_path(payload, "despacho.urfDespacho.nome"), "SANTOS"
        )
        self.assertFalse(declaracao._payload_path(payload, "carga.frete.totalReais"))
        # a path that walks past a leaf must not raise
        self.assertFalse(
            declaracao._payload_path(payload, "despacho.urfDespacho.nome.extra")
        )

    def test_import_payload_maps_acrescimo_deducao(self):
        """Additions/deductions must come from the payload: they feed
        unit_addition_deduction and therefore the price_unit of the
        generated invoice line.
        """
        declaracao = self._create_declaracao()
        item = declaracao.item_ids.filtered(lambda i: i.item_number == "2")
        self.assertEqual(len(item.addition_deduction_ids), 2)

        acrescimo = item.addition_deduction_ids.filtered(lambda a: a.codigo == "16")
        self.assertAlmostEqual(acrescimo.valor, 300.00)
        self.assertEqual(acrescimo.description, "Frete internacional")
        self.assertAlmostEqual(acrescimo.moeda_taxa, 5.25)
        self.assertEqual(acrescimo.moeda_negociada_id, self.env.ref("base.USD"))
        self.assertEqual(acrescimo.declaration_id, declaracao)

        # a "DEDUCAO" is stored as a negative amount
        deducao = item.addition_deduction_ids.filtered(lambda a: a.codigo == "99")
        self.assertAlmostEqual(deducao.valor, -100.00)

        # net +200.00 over 40 units => +5.00 per unit
        self.assertAlmostEqual(item.addition_deduction, 200.00)
        self.assertAlmostEqual(item.unit_addition_deduction, 5.00)
        self.assertAlmostEqual(item.price_unit, 120.00)  # 4800 / 40
        self.assertAlmostEqual(item.final_price_unit, 125.00)

    def test_import_payload_maps_item_currency(self):
        declaracao = self._create_declaracao()
        item = declaracao.item_ids.filtered(lambda i: i.item_number == "1")
        self.assertEqual(item.trade_currency_id, self.env.ref("base.USD"))
        self.assertAlmostEqual(item.exchange_rate, 5.25)
        self.assertAlmostEqual(item.trade_unit_value, 9.52)

    def test_import_payload_maps_pagamento(self):
        declaracao = self._create_declaracao()
        pagamento = declaracao.payment_ids
        self.assertEqual(pagamento.revenue_code, "0086")
        self.assertEqual(str(pagamento.payment_date), "2026-02-11")
        self.assertEqual(pagamento.amendment_number, "0")

    def test_auto_match_product_by_code(self):
        declaracao = self._create_declaracao()
        item1 = declaracao.item_ids.filtered(lambda i: i.item_number == "1")
        item2 = declaracao.item_ids.filtered(lambda i: i.item_number == "2")
        self.assertEqual(item1.product_id, self.product_1)
        self.assertEqual(item2.product_id, self.product_2)

    def test_total_customs_value(self):
        declaracao = self._create_declaracao()
        self.assertAlmostEqual(declaracao.total_customs_value, 5300.00 + 4950.00)

    def test_cost_allocation_by_customs_value(self):
        # AFRMM 1000 + Siscomex 300 allocated proportionally to the
        # customs value of each item (5300 / 10250 and 4950 / 10250).
        declaracao = self._create_declaracao(afrmm=1000.0, siscomex=300.0)
        item1 = declaracao.item_ids.filtered(lambda i: i.item_number == "1")
        item2 = declaracao.item_ids.filtered(lambda i: i.item_number == "2")
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
        item = declaracao.item_ids.filtered(lambda i: i.item_number == "1")
        # without additions/deductions, final == price_unit
        self.assertAlmostEqual(item.final_price_unit, item.price_unit)
        self.env["l10n_br_duimp.addition.deduction"].create(
            {"item_id": item.id, "description": "Royalties", "valor": 500.00}
        )
        item.invalidate_recordset()
        # +500 over 100 units => +5.0/unit
        self.assertAlmostEqual(item.unit_addition_deduction, 5.0)
        self.assertAlmostEqual(item.final_price_unit, item.price_unit + 5.0)

    def test_prepare_document_line_uses_per_item_taxes(self):
        declaracao = self._create_declaracao(afrmm=1000.0, siscomex=300.0)
        item = declaracao.item_ids.filtered(lambda i: i.item_number == "1")
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
        declaracao.partner_id = self.vendor
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
