# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
#   Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from odoo.tests import Form, TransactionCase

from .test_l10n_br_sale import L10nBrSaleBaseTest


class TestL10nBrSaleSN(L10nBrSaleBaseTest, TransactionCase):
    __test__ = True

    company_ref = "l10n_br_base.empresa_simples_nacional"
    so_products_ref = "l10n_br_sale.sn_so_only_products"
    so_services_ref = "l10n_br_sale.sn_so_only_services"
    so_product_service_ref = "l10n_br_sale.sn_so_product_service"

    def test_create_service_invoice_with_withholding_taxes(self):
        self._change_user_company(self.company)
        self.fsc_op_sale.deductible_taxes = False
        self.company.write(
            {
                "tax_issqn_wh_id": False,
                "tax_cofins_wh_id": False,
                "tax_pis_wh_id": False,
                "tax_csll_wh_id": False,
                "tax_inss_wh_id": False,
            }
        )
        self.company.tax_definition_ids.filtered(
            lambda definition: definition.tax_group_id.tax_withholding
        ).unlink()

        tax_definition_model = self.env["l10n_br_fiscal.tax.definition"]
        withholding_taxes = (
            "l10n_br_fiscal.tax_issqn_wh_5",
            "l10n_br_fiscal.tax_cofins_wh_3",
            "l10n_br_fiscal.tax_pis_wh_0_65",
            "l10n_br_fiscal.tax_csll_wh_1",
            "l10n_br_fiscal.tax_inss_wh_11",
        )
        for tax_xmlid in withholding_taxes:
            tax = self.env.ref(tax_xmlid)
            tax_definition_model.create(
                {
                    "fiscal_operation_line_id": self.fsc_op_line_serv.id,
                    "tax_group_id": tax.tax_group_id.id,
                    "is_taxed": True,
                    "is_debit_credit": True,
                    "custom_tax": True,
                    "tax_id": tax.id,
                    "state": "approved",
                }
            )

        sale_order_form = Form(self.env["sale.order"])
        sale_order_form.partner_id = self.env.ref("l10n_br_base.res_partner_akretion")
        sale_order_form.fiscal_operation_id = self.fsc_op_sale
        sale_order_form.note = "Service invoice with withholding taxes"
        with sale_order_form.order_line.new() as line_form:
            line_form.product_id = self.env.ref(
                "l10n_br_fiscal.customized_development_sale"
            )
            line_form.product_uom_qty = 90
            line_form.price_unit = 100
        sale_order = sale_order_form.save()
        self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "display_type": "line_note",
                "name": "Invoice note",
            }
        )

        service_line = sale_order.order_line.filtered(
            lambda line: not line.display_type
        )
        expected_taxes = self.env["l10n_br_fiscal.tax"].browse(
            [self.env.ref(xmlid).id for xmlid in withholding_taxes]
        )
        self.assertEqual(
            service_line.fiscal_tax_ids & expected_taxes,
            expected_taxes,
        )
        self.assertGreater(service_line.amount_tax_withholding, 0.0)

        sale_order.action_confirm()
        self.env.flush_all()
        self.env.invalidate_all()
        sale_order = self.env["sale.order"].browse(sale_order.id)
        forced_recomputes = []
        account_move_model = type(self.env["account.move"])
        original_compute_amount = account_move_model._compute_amount

        def _compute_amount(moves):
            if moves.env.context.get("force_fiscal_amount_recompute"):
                forced_recomputes.append(moves)
            return original_compute_amount(moves)

        with patch.object(account_move_model, "_compute_amount", _compute_amount):
            invoices = sale_order._create_invoices(final=True)

        self.assertTrue(forced_recomputes)
        self.assertEqual(len(invoices), 1)
        invoice_line = invoices.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        for field_name in (
            "fiscal_amount_untaxed",
            "fiscal_amount_tax",
            "fiscal_amount_total",
            "amount_tax_withholding",
        ):
            self.assertAlmostEqual(
                service_line[field_name],
                invoice_line[field_name],
                2,
            )
        self.assertAlmostEqual(sum(invoices.line_ids.mapped("balance")), 0.0, 2)
