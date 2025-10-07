# Copyright 2025-TODAY  Akretion - Raphaël Valyi
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from odoo import Command
from odoo.tests import Form, TransactionCase


class TestDocumentEdition(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            {
                "name": "Fiscal User",
                "login": "fiscaluser",
                "password": "fiscaluser",
                "groups_id": [
                    Command.set(cls.env.user.groups_id.ids),
                    Command.link(cls.env.ref("l10n_br_fiscal.group_user").id),
                    Command.link(cls.env.ref("base.group_multi_company").id),
                ],
            }
        )
        cls.user.partner_id.email = "accountman@test.com"
        companies = cls.env["res.company"].search([])
        cls.user.write(
            {
                "company_ids": [Command.set(companies.ids)],
                "company_id": cls.env.ref("l10n_br_base.empresa_lucro_presumido"),
            }
        )

        cls.env = cls.env(
            user=cls.user, context=dict(cls.env.context, tracking_disable=True)
        )
        cls.user = cls.env.user
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.user.company_ids |= cls.company
        cls.user.company_id = cls.company.id

    def test_basic_doc_edition(self):
        doc_form = Form(
            self.env["l10n_br_fiscal.document"].with_context(
                default_fiscal_operation_type="out",
            )
        )
        doc_form.company_id = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        doc_form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        doc_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        doc_form.ind_final = "1"
        product_id = self.env.ref("product.product_product_6")
        product_id.list_price = 150  # we will later check we can set price_unit to 100
        with doc_form.fiscal_line_ids.new() as line_form:
            original_method = type(
                self.env["l10n_br_fiscal.operation.line"]
            ).map_fiscal_taxes

            def wrapped_method(self, *args, **kwargs):
                return original_method(self, *args, **kwargs)

            with mock.patch.object(
                type(self.env["l10n_br_fiscal.operation.line"]),
                "map_fiscal_taxes",
                side_effect=wrapped_method,
                autospec=True,
            ) as mocked:
                line_form.product_id = product_id

            # ensure the tax engine is called with the proper
            # parameters, especially ind_final
            # as it is related=document_id.ind_final
            # which is converted to move_id.ind_final to work live
            mocked.assert_called_with(
                self.env.ref("l10n_br_fiscal.fo_venda_revenda"),
                company=doc_form.company_id,
                partner=doc_form.partner_id,
                product=product_id,
                ncm=product_id.ncm_id,
                nbm=self.env["l10n_br_fiscal.nbm"],
                nbs=self.env["l10n_br_fiscal.nbs"],
                cest=self.env["l10n_br_fiscal.cest"],
                city_taxation_code=self.env["l10n_br_fiscal.city.taxation.code"],
                service_type=self.env["l10n_br_fiscal.service.type"],
                ind_final="1",
            )

            line_form.price_unit = 50
            line_form.quantity = 2
            self.assertEqual(len(line_form.fiscal_tax_ids), 4)
            self.assertEqual(
                line_form.icms_tax_id, self.env.ref("l10n_br_fiscal.tax_icms_12")
            )
            self.assertEqual(line_form.icms_value, 12.0)
            line_form.price_unit = 100
            self.assertEqual(
                line_form.icms_tax_id, self.env.ref("l10n_br_fiscal.tax_icms_12")
            )
            self.assertEqual(line_form.icms_value, 24.0)
            self.assertEqual(
                line_form.fiscal_operation_line_id,
                self.env.ref("l10n_br_fiscal.fo_venda_revenda"),
            )

            # line_form.fiscal_operation_line_id = False
            # self.assertEqual(len(line_form.fiscal_tax_ids), 0)

        doc = doc_form.save()
        self.assertEqual(doc.fiscal_line_ids[0].price_unit, 100)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_price, 100)
        self.assertEqual(doc.fiscal_line_ids[0].quantity, 2)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_quantity, 2)
        self.assertEqual(len(doc.fiscal_line_ids[0].fiscal_tax_ids), 4)
        self.assertEqual(
            doc.fiscal_line_ids[0].icms_tax_id.id,
            self.ref("l10n_br_fiscal.tax_icms_12"),
        )

    def test_product_fiscal_factor(self):
        doc_form = Form(
            self.env["l10n_br_fiscal.document"].with_context(
                default_fiscal_operation_type="out",
            )
        )
        doc_form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        doc_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        doc_form.ind_final = "1"
        product_id = self.env.ref("product.product_product_6")
        product_id.uot_factor = 2
        with doc_form.fiscal_line_ids.new() as line_form:
            line_form.product_id = product_id
            line_form.price_unit = 100
            line_form.quantity = 10

        doc = doc_form.save()
        self.assertEqual(doc.fiscal_line_ids[0].price_unit, 100)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_price, 50)
        self.assertEqual(doc.fiscal_line_ids[0].quantity, 10)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_quantity, 20)

    def test_product_fiscal_price_and_qty_edition(self):
        doc_form = Form(
            self.env["l10n_br_fiscal.document"].with_context(
                default_fiscal_operation_type="out",
            )
        )
        doc_form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        doc_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        doc_form.ind_final = "1"
        product_id = self.env.ref("product.product_product_6")
        product_id.list_price = 100
        with doc_form.fiscal_line_ids.new() as line_form:
            line_form.product_id = product_id
            line_form.price_unit = 110
            line_form.quantity = 10
            line_form.fiscal_price = 112
            line_form.fiscal_quantity = 5
            self.assertEqual(line_form.price_unit, 110)
            self.assertEqual(line_form.fiscal_price, 112)
            self.assertEqual(line_form.quantity, 10)
            self.assertEqual(line_form.fiscal_quantity, 5)

        doc = doc_form.save()
        self.assertEqual(doc.fiscal_line_ids[0].price_unit, 110)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_price, 112)
        self.assertEqual(doc.fiscal_line_ids[0].quantity, 10)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_quantity, 5)

    def test_landed_costs_by_line_and_by_total(self):
        """
        Tests both landed cost scenarios: 'by line' and 'by total'.
        1. By Line: Enters costs on lines and verifies the header totals.
        2. By Total: Enters costs on the header and verifies lines distribution.
        """
        self.env.user.groups_id |= self.env.ref("l10n_br_fiscal.group_user")
        product1 = self.env.ref("product.product_product_6")
        product2 = self.env.ref("product.product_product_7")

        # Part 1: Test with delivery_costs = 'line'
        # ----------------------------------------------------
        self.company.delivery_costs = "line"
        doc_form = Form(self.env["l10n_br_fiscal.document"])
        doc_form.company_id = self.company
        doc_form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        doc_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")

        with doc_form.fiscal_line_ids.new() as line1:
            line1.product_id = product1
            line1.fiscal_operation_line_id = self.env.ref(
                "l10n_br_fiscal.fo_venda_venda"
            )
            line1.price_unit = 1000.0
            line1.quantity = 2.0  # Gross: 2000
            line1.freight_value = 10.0
            line1.insurance_value = 20.0
            line1.other_value = 5.0

        with doc_form.fiscal_line_ids.new() as line2:
            line2.product_id = product2
            line2.fiscal_operation_line_id = self.env.ref(
                "l10n_br_fiscal.fo_venda_venda"
            )
            line2.price_unit = 500.0
            line2.quantity = 1.0  # Gross: 500
            line2.freight_value = 4.0
            line2.insurance_value = 6.0
            line2.other_value = 2.0

        doc = doc_form.save()

        self.assertEqual(doc.company_id.delivery_costs, "line")
        # Assert header totals are the SUM of line values
        self.assertAlmostEqual(doc.amount_freight_value, 14.0)  # 10.0 + 4.0
        self.assertAlmostEqual(doc.amount_insurance_value, 26.0)  # 20.0 + 6.0
        self.assertAlmostEqual(doc.amount_other_value, 7.0)  # 5.0 + 2.0

        # Assert final fiscal totals (bottom-up calculation)
        # price_gross = (1000*2) + (500*1) = 2500
        # landed_costs = 14 + 26 + 7 = 47
        # fiscal_amount_untaxed (IPI Base) = 2500 + 47 = 2547
        self.assertAlmostEqual(doc.fiscal_amount_untaxed, 2547.00)
        # fiscal_amount_tax (IPI) = (2035 * 3.25%) + (512 * 5%) = 66.14 + 25.60 = 91.74
        self.assertAlmostEqual(doc.fiscal_amount_tax, 91.74, places=2)
        # fiscal_amount_total = 2547.00 + 91.74 = 2638.74
        self.assertAlmostEqual(doc.fiscal_amount_total, 2638.74, places=2)

        # Part 2: Test with delivery_costs = 'total'
        # ----------------------------------------------------
        self.company.delivery_costs = "total"
        doc_form_edit = Form(doc)
        # Set new header totals, which should trigger inverse methods to distribute
        doc_form_edit.amount_freight_value = 30.0
        doc_form_edit.amount_insurance_value = 60.0
        doc_form_edit.amount_other_value = 90.0
        doc_after_total_update = doc_form_edit.save()

        line1 = doc_after_total_update.fiscal_line_ids[0]
        line2 = doc_after_total_update.fiscal_line_ids[1]

        # Assert values were distributed proportionally to price_gross
        # (2000 vs 500 -> 80% vs 20%)
        # Freight: 30.0 * 0.8 = 24.0 | 30.0 * 0.2 = 6.0
        self.assertAlmostEqual(line1.freight_value, 24.0)
        self.assertAlmostEqual(line2.freight_value, 6.0)
        # Insurance: 60.0 * 0.8 = 48.0 | 60.0 * 0.2 = 12.0
        self.assertAlmostEqual(line1.insurance_value, 48.0)
        self.assertAlmostEqual(line2.insurance_value, 12.0)
        # Other: 90.0 * 0.8 = 72.0 | 90.0 * 0.2 = 18.0
        self.assertAlmostEqual(line1.other_value, 72.0)
        self.assertAlmostEqual(line2.other_value, 18.0)

        # Assert final fiscal totals are recomputed correctly (top-down calculation)
        # price_gross = 2500
        # landed_costs = 30 + 60 + 90 = 180
        # fiscal_amount_untaxed (IPI Base) = 2500 + 180 = 2680
        self.assertAlmostEqual(doc_after_total_update.fiscal_amount_untaxed, 2680.00)
        # Line 1 IPI Base = 2000 (product) + 24 (freight) + 48 (insurance)
        # + 72 (other) = 2144
        # Line 1 IPI Value = 2144 * 3.25% = 69.68
        self.assertAlmostEqual(line1.ipi_base, 2144.00)
        self.assertAlmostEqual(line1.ipi_value, 69.68, places=2)

        # Line 2 IPI Base = 500 (product) + 6 (freight) + 12 (insurance)
        # + 18 (other) = 536
        # Line 2 IPI Value = 536 * 5% = 26.80
        self.assertAlmostEqual(line2.ipi_base, 536.00)
        self.assertAlmostEqual(line2.ipi_value, 26.80, places=2)

        # fiscal_amount_tax (IPI) = 69.68 + 26.80 = 96.48
        self.assertAlmostEqual(
            doc_after_total_update.fiscal_amount_tax, 96.48, places=2
        )
        # fiscal_amount_total = 2680.00 + 96.48 = 2776.48
        self.assertAlmostEqual(
            doc_after_total_update.fiscal_amount_total, 2776.48, places=2
        )

    def test_difal_calculation(self):
        partner = self.env.ref("l10n_br_base.res_partner_cliente5_pe")
        partner.ind_ie_dest = "9"
        doc_form = Form(
            self.env["l10n_br_fiscal.document"].with_context(
                default_fiscal_operation_type="out",
            )
        )
        doc_form.company_id = self.company
        doc_form.partner_id = partner
        doc_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")

        product = self.env.ref("product.product_product_6")
        with doc_form.fiscal_line_ids.new() as line_form:
            line_form.product_id = product
            line_form.price_unit = 100.0
            line_form.quantity = 1.0

        doc = doc_form.save()
        line = doc.fiscal_line_ids[0]
        self.assertEqual(line.icms_destination_base, 100.0)
        self.assertEqual(line.icms_origin_percent, 7.0)
        self.assertEqual(line.icms_destination_percent, 20.5)
        self.assertEqual(line.icms_destination_value, 13.5)
