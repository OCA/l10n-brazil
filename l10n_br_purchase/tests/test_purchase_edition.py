# Copyright 2026-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import Command
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchaseEdition(TransactionCase):
    """
    Test basic purchase order edition through the UI to ensure the fiscal
    "decoration" works as expected on purchase.order(.line).

    This is the l10n_br_purchase counterpart of l10n_br_account's
    test_move_edition.test_in_fiscal_invoice.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company

        cls.user = cls.env["res.users"].create(
            {
                "name": "Purchase Fiscal Editor",
                "login": "po_fiscal_editor",
                "password": "po_fiscal_editor",
                "groups_id": [
                    Command.set(cls.env.user.groups_id.ids),
                    Command.link(cls.env.ref("purchase.group_purchase_manager").id),
                    Command.link(cls.env.ref("l10n_br_fiscal.group_user").id),
                    Command.link(cls.env.ref("uom.group_uom").id),
                ],
            }
        )
        companies = cls.env["res.company"].search([])
        cls.user.write(
            {
                "company_ids": [Command.set(companies.ids)],
                "company_id": cls.company.id,
            }
        )
        cls.env = cls.env(
            user=cls.user, context=dict(cls.env.context, tracking_disable=True)
        )

        # Product with a non-zero cost so fiscal tax values can be computed.
        # (core purchase recomputes price_unit from standard_price when no
        # vendor pricelist exists; a zero cost would zero-out everything.)
        cls.product_id = cls.env.ref("product.product_product_7")
        cls.product_id.standard_price = 100.0

    def test_fiscal_purchase_order(self):
        """Ensure fiscal fields are computed on a purchase order line.

        Mirrors l10n_br_account's test_in_fiscal_invoice: create a PO for the
        Lucro Presumido company via Form, add a product, and verify that
        fiscal_operation_line_id, cfop_id, fiscal_tax_ids, and the computed
        tax values (icms_value, ipi_value, etc.) are populated — both while
        the line is a NewID and after the order is saved.
        """
        partner = self.env.ref("l10n_br_base.res_partner_amd")

        po_form = Form(
            self.env["purchase.order"].with_context(
                default_company_id=self.company.id,
            )
        )
        po_form.partner_id = partner

        with po_form.order_line.new() as line_form:
            line_form.product_id = self.product_id

            # --- NewID assertions: fiscal mapping should fire live ---
            self.assertTrue(
                line_form.fiscal_operation_id,
                "fiscal_operation_id should be set by default.",
            )
            self.assertTrue(
                line_form.fiscal_operation_line_id,
                "fiscal_operation_line_id should be computed on NewID.",
            )
            self.assertTrue(
                line_form.cfop_id,
                "cfop_id should be computed on NewID.",
            )
            self.assertTrue(
                line_form.fiscal_tax_ids,
                "fiscal_tax_ids should be computed on NewID.",
            )
            self.assertTrue(
                line_form.icms_tax_id,
                "icms_tax_id should be computed on NewID.",
            )

            # price_unit comes from standard_price (100) because the core
            # purchase compute runs for this product/partner combo.
            line_form.product_qty = 10

        po = po_form.save()

        # --- Post-save assertions ---
        line = po.order_line[0]
        self.assertEqual(line.product_id, self.product_id)
        self.assertEqual(line.product_qty, 10)

        self.assertTrue(line.fiscal_operation_id)
        self.assertTrue(
            line.fiscal_operation_line_id,
            "fiscal_operation_line_id must be set after save.",
        )
        self.assertTrue(
            line.cfop_id,
            "cfop_id must be set after save.",
        )
        self.assertTrue(
            line.fiscal_tax_ids,
            "fiscal_tax_ids must be set after save.",
        )

        # The fiscal operation default_price_unit for purchase is "cost_price",
        # so price_unit should equal standard_price (100). This must NOT be
        # zeroed out by the fiscal mixin's _compute_price_unit_fiscal.
        self.assertEqual(
            line.price_unit,
            100.0,
            "price_unit should be 100 (standard_price), not 0.",
        )

        # Tax values must be computed from the non-zero price_unit.
        self.assertGreater(
            line.icms_base,
            0,
            "icms_base must be > 0 when price_unit is non-zero.",
        )
        self.assertGreater(
            line.icms_value,
            0,
            "icms_value must be > 0 when price_unit is non-zero.",
        )
        self.assertGreater(
            line.ipi_value,
            0,
            "ipi_value must be > 0 when price_unit is non-zero.",
        )

        # Fiscal totals should reflect the price.
        self.assertAlmostEqual(line.fiscal_amount_untaxed, 1000.0, places=2)

        # --- PO-level tax totals: ICMS and IPI group amounts should
        #     match the line values. ---
        self.env.flush_all()
        self.assertTrue(po.tax_totals, "tax_totals must not be empty.")
        subtotals = po.tax_totals.get("subtotals", [])
        self.assertTrue(subtotals, "tax_totals must have subtotals.")

        tax_groups = {g["group_name"]: g for g in subtotals[0]["tax_groups"]}
        self.assertIn("ICMS", tax_groups, "ICMS group missing in tax_totals.")
        self.assertIn("IPI", tax_groups, "IPI group missing in tax_totals.")

        self.assertAlmostEqual(
            tax_groups["ICMS"]["tax_amount_currency"],
            line.icms_value,
            places=2,
            msg="ICMS total at PO level must match line icms_value.",
        )
        self.assertAlmostEqual(
            tax_groups["IPI"]["tax_amount_currency"],
            line.ipi_value,
            places=2,
            msg="IPI total at PO level must match line ipi_value.",
        )

        # Manually change price_unit and verify tax values recompute.
        line.price_unit = 200
        self.assertAlmostEqual(line.icms_base, 2000.0, places=2)
        self.assertGreater(line.icms_value, 0)
