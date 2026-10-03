# Copyright 2018 Akretion - www.akretion.com.br - Magno Costa <magno.costa@akretion.com
# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    CFOP_DESTINATION_EXTERNAL,
    CFOP_DESTINATION_INTERNAL,
    TAX_DOMAIN_ISSQN,
    TAX_FRAMEWORK_SIMPLES_ALL,
)


class TestL10nBrRepair(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        cls.product_to_repair = cls.env.ref("product.product_product_6")
        cls.part = cls.env.ref("product.product_product_27")
        cls.service = cls.env.ref("l10n_br_fiscal.customized_development_sale")
        cls.fo_sale = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fo_line_sale = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
        cls.fo_line_service = cls.env.ref("l10n_br_fiscal.fo_venda_servico")
        cls.company.repair_fiscal_operation_id = cls.fo_sale
        # The quotation must take the operation from the repair, not from
        # the default sale operation of the company.
        cls.company.sale_fiscal_operation_id = False

    def _create_repair(self, **vals):
        values = {
            "partner_id": self.partner.id,
            "product_id": self.product_to_repair.id,
            "company_id": self.company.id,
            "move_ids": [
                Command.create(
                    {
                        "product_id": self.part.id,
                        "product_uom_qty": 2.0,
                        "repair_line_type": "add",
                    }
                )
            ],
        }
        values.update(vals)
        return self.env["repair.order"].create(values)

    def _add_service(self, sale_order):
        return self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.service.id,
                "product_uom_qty": 3.0,
                "price_unit": 120.0,
                "fiscal_operation_id": sale_order.fiscal_operation_id.id,
            }
        )

    def _assert_fiscal_line(self, so_line, operation_line):
        self.assertEqual(so_line.fiscal_operation_id, self.fo_sale)
        self.assertEqual(so_line.fiscal_operation_line_id, operation_line)
        self.assertTrue(so_line.fiscal_tax_ids)
        self.assertEqual(
            so_line.tax_id,
            so_line.fiscal_tax_ids.account_taxes(
                user_type="sale",
                fiscal_operation=so_line.fiscal_operation_id,
                company=so_line.company_id,
            ),
        )
        self.assertAlmostEqual(so_line.price_subtotal, so_line.fiscal_amount_untaxed, 2)
        self.assertAlmostEqual(so_line.price_total, so_line.fiscal_amount_total, 2)

    def test_default_fiscal_operation(self):
        """A new repair takes the default repair operation of the company."""
        repair = self._create_repair()
        self.assertEqual(repair.fiscal_operation_id, self.fo_sale)

    def test_quotation_from_repair(self):
        """The quotation created from the repair carries the fiscal
        operation, and the lines of the parts get CFOP and taxes."""
        repair = self._create_repair()
        repair.action_create_sale_order()
        sale_order = repair.sale_order_id
        self.assertTrue(sale_order)
        self.assertEqual(sale_order.fiscal_operation_id, self.fo_sale)
        part_line = sale_order.order_line.filtered(
            lambda ln: ln.product_id == self.part
        )
        self.assertEqual(len(part_line), 1)
        self.assertEqual(part_line.move_ids, repair.move_ids)
        self._assert_fiscal_line(part_line, self.fo_line_sale)
        # the demo data of other modules may move the company to another state
        if self.partner.state_id == self.company.state_id:
            destination, cfop_code = CFOP_DESTINATION_INTERNAL, "5101"
        else:
            destination, cfop_code = CFOP_DESTINATION_EXTERNAL, "6101"
        self.assertEqual(part_line.cfop_id.destination, destination)
        self.assertEqual(part_line.cfop_id.code, cfop_code)
        if self.company.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
            icms_tax = part_line.icmssn_tax_id
        else:
            icms_tax = part_line.icms_tax_id
        self.assertTrue(icms_tax)
        self.assertIn(icms_tax, part_line.fiscal_tax_ids)

        # a part added afterwards also gets the fiscal operation
        repair.write(
            {
                "move_ids": [
                    Command.create(
                        {
                            "product_id": self.env.ref("product.product_product_12").id,
                            "product_uom_qty": 1.0,
                            "repair_line_type": "add",
                        }
                    )
                ]
            }
        )
        new_line = sale_order.order_line.filtered(
            lambda ln: ln.product_id == self.env.ref("product.product_product_12")
        )
        # the mouse is a resale product
        self.assertEqual(new_line.fiscal_operation_id, self.fo_sale)
        self.assertEqual(
            new_line.fiscal_operation_line_id,
            self.env.ref("l10n_br_fiscal.fo_venda_revenda"),
        )

    def test_repair_full_cycle(self):
        """Quotation, repair done, one fiscal document per document type
        (NF-e for the parts, NFS-e for the service), posted."""
        repair = self._create_repair()
        repair.action_create_sale_order()
        sale_order = repair.sale_order_id
        service_line = self._add_service(sale_order)
        self._assert_fiscal_line(service_line, self.fo_line_service)
        self.assertEqual(service_line.tax_icms_or_issqn, TAX_DOMAIN_ISSQN)
        self.assertTrue(service_line.issqn_tax_id)

        sale_order.action_confirm()
        self.assertEqual(sale_order.state, "sale")
        self.assertEqual(repair.state, "draft")
        repair.action_repair_start()
        self.assertEqual(repair.state, "under_repair")
        repair.move_ids.write({"quantity": 2.0, "picked": True})
        repair.action_repair_end()
        self.assertEqual(repair.state, "done")
        self.assertEqual(set(repair.move_ids.mapped("state")), {"done"})
        part_line = sale_order.order_line - service_line
        self.assertEqual(part_line.qty_delivered, 2.0)

        invoices = sale_order._create_invoices(final=True)
        self.assertEqual(len(invoices), 2)
        self.assertEqual(set(invoices.mapped("document_type_id.code")), {"55", "SE"})
        for invoice in invoices:
            self.assertEqual(invoice.fiscal_operation_id, self.fo_sale)
            for aml in invoice.invoice_line_ids:
                so_line = aml.sale_line_ids
                self.assertEqual(
                    aml.fiscal_operation_line_id, so_line.fiscal_operation_line_id
                )
                self.assertEqual(aml.cfop_id, so_line.cfop_id)
                self.assertAlmostEqual(aml.price_total, so_line.price_total, 2)
        self.assertAlmostEqual(
            sum(invoices.mapped("amount_total")), sale_order.amount_total, 2
        )

        invoices.action_post()
        self.env.flush_all()
        self.env.cr.execute(
            "SELECT state FROM account_move WHERE id IN %s", (tuple(invoices.ids),)
        )
        self.assertEqual({row[0] for row in self.env.cr.fetchall()}, {"posted"})
        self.assertEqual(sale_order.invoice_status, "invoiced")

    def test_repair_cancel(self):
        """Cancelling the repair zeroes the quotation line of the parts and
        its fiscal amounts."""
        repair = self._create_repair()
        repair.action_create_sale_order()
        part_line = repair.sale_order_id.order_line
        self.assertTrue(part_line.fiscal_amount_total)
        repair.action_repair_cancel()
        self.assertEqual(repair.state, "cancel")
        self.assertEqual(part_line.product_uom_qty, 0.0)
        self.assertEqual(part_line.fiscal_amount_total, 0.0)
        self.assertEqual(part_line.price_subtotal, 0.0)

    def test_repair_from_sale_order(self):
        """A repair created by a confirmed sale order follows the fiscal
        operation of the order."""
        self.product_to_repair.product_tmpl_id.create_repair = True
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "fiscal_operation_id": self.fo_sale.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_to_repair.id,
                            "product_uom_qty": 1.0,
                            "fiscal_operation_id": self.fo_sale.id,
                        }
                    )
                ],
            }
        )
        sale_order.action_confirm()
        repair = sale_order.repair_order_ids
        self.assertEqual(len(repair), 1)
        self.assertEqual(repair.fiscal_operation_id, self.fo_sale)

    def test_repair_without_fiscal_operation(self):
        """Without fiscal operation the quotation keeps the core behavior."""
        repair = self._create_repair(fiscal_operation_id=False)
        self.assertFalse(repair.fiscal_operation_id)
        repair.action_create_sale_order()
        self.assertFalse(repair.sale_order_id.fiscal_operation_id)
        self.assertFalse(repair.sale_order_id.order_line.fiscal_operation_id)

    def test_demo_repair_invoiced(self):
        """The demo repair went through the whole cycle (checked in the
        database: a failing demo is dropped silently)."""
        repair = self.env.ref("l10n_br_repair.main_repair_invoiced")
        self.assertEqual(repair.state, "done")
        self.env.flush_all()
        self.env.cr.execute(
            """
            SELECT DISTINCT am.state, dt.code
            FROM account_move am
            JOIN l10n_br_fiscal_document fd ON fd.id = am.fiscal_document_id
            JOIN l10n_br_fiscal_document_type dt ON dt.id = fd.document_type_id
            JOIN account_move_line aml ON aml.move_id = am.id
            JOIN sale_order_line_invoice_rel rel ON rel.invoice_line_id = aml.id
            JOIN sale_order_line sol ON sol.id = rel.order_line_id
            WHERE sol.order_id = %s
            """,
            (repair.sale_order_id.id,),
        )
        rows = self.env.cr.fetchall()
        self.assertEqual({row[0] for row in rows}, {"posted"})
        self.assertEqual({row[1] for row in rows}, {"55", "SE"})
