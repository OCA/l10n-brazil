# Copyright 2018 Akretion - www.akretion.com.br - Magno Costa <magno.costa@akretion.com
# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    CFOP_DESTINATION_EXTERNAL,
    CFOP_DESTINATION_INTERNAL,
    TAX_DOMAIN_ISSQN,
    TAX_FRAMEWORK_NORMAL,
    TAX_FRAMEWORK_SIMPLES,
    TAX_FRAMEWORK_SIMPLES_ALL,
)


class L10nBrRepairBaseTest:
    __test__ = False

    company_ref = None
    so_products_ref = None
    so_services_ref = None
    so_prod_srv_ref = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref(cls.company_ref)
        cls.so_products = cls.env.ref(cls.so_products_ref)
        cls.so_services = cls.env.ref(cls.so_services_ref)
        cls.so_prod_srv = cls.env.ref(cls.so_prod_srv_ref)
        cls.fsc_op_sale = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fsc_op_line_sale = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
        cls.fsc_op_line_serv = cls.env.ref("l10n_br_fiscal.fo_venda_servico")
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company

        taxes_normal = {
            "icms": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_icms_12"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_icms_00"),
            },
            "issqn": {"tax": cls.env.ref("l10n_br_fiscal.tax_issqn_5")},
            "ipi": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_ipi_3_25"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_ipi_50"),
            },
            "pis": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_pis_0_65"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_pis_01"),
            },
            "cofins": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_cofins_3"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_cofins_01"),
            },
        }
        taxes_simples = {
            "icms": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_icms_sn_com_credito"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_icmssn_101"),
            },
            "issqn": {"tax": cls.env.ref("l10n_br_fiscal.tax_issqn_5")},
            "ipi": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_ipi_outros"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_ipi_99"),
            },
            "pis": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_pis_outros"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_pis_49"),
            },
            "cofins": {
                "tax": cls.env.ref("l10n_br_fiscal.tax_cofins_outros"),
                "cst": cls.env.ref("l10n_br_fiscal.cst_cofins_49"),
            },
        }
        cls.TAXES = {
            TAX_FRAMEWORK_NORMAL: taxes_normal,
            TAX_FRAMEWORK_SIMPLES: taxes_simples,
        }
        cls.CFOPS = {
            CFOP_DESTINATION_INTERNAL: cls.env.ref("l10n_br_fiscal.cfop_5101"),
            CFOP_DESTINATION_EXTERNAL: cls.env.ref("l10n_br_fiscal.cfop_6101"),
        }

    def _taxes(self, line):
        framework = line.company_id.tax_framework
        if framework in TAX_FRAMEWORK_SIMPLES_ALL:
            framework = TAX_FRAMEWORK_SIMPLES
        return self.TAXES[framework]

    def _assert_pis_cofins(self, line, taxes):
        for tax_domain in ("pis", "cofins"):
            self.assertEqual(
                line[f"{tax_domain}_tax_id"],
                taxes[tax_domain]["tax"],
                f"{tax_domain} tax of {line.name}",
            )
            self.assertEqual(
                line[f"{tax_domain}_cst_id"],
                taxes[tax_domain]["cst"],
                f"{tax_domain} CST of {line.name}",
            )

    def _assert_product_line(self, line):
        """Fiscal operation line, CFOP and taxes of a repair part."""
        self.assertEqual(line.fiscal_operation_id, self.fsc_op_sale)
        self.assertEqual(line.fiscal_operation_line_id, self.fsc_op_line_sale)
        self.assertEqual(line.cfop_id, self.CFOPS[line.cfop_id.destination])
        taxes = self._taxes(line)
        if line.company_id.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
            icms_tax = line.icmssn_tax_id
        else:
            icms_tax = line.icms_tax_id
        self.assertEqual(icms_tax, taxes["icms"]["tax"])
        self.assertEqual(line.icms_cst_id, taxes["icms"]["cst"])
        self.assertFalse(line.icmsfcp_tax_id)
        self.assertEqual(line.ipi_tax_id, taxes["ipi"]["tax"])
        self.assertEqual(line.ipi_cst_id, taxes["ipi"]["cst"])
        self._assert_pis_cofins(line, taxes)
        self._assert_line_amounts(line)

    def _assert_service_line(self, line):
        """Fiscal operation line, ISSQN and taxes of a repair fee."""
        self.assertEqual(line.fiscal_operation_id, self.fsc_op_sale)
        self.assertEqual(line.fiscal_operation_line_id, self.fsc_op_line_serv)
        self.assertEqual(line.tax_icms_or_issqn, TAX_DOMAIN_ISSQN)
        self.assertFalse(line.cfop_id)
        taxes = self._taxes(line)
        self.assertEqual(line.issqn_tax_id, taxes["issqn"]["tax"])
        self.assertTrue(line.issqn_value)
        self._assert_pis_cofins(line, taxes)
        self._assert_line_amounts(line)

    def _assert_line_amounts(self, line):
        """The core amounts of the line must be the fiscal ones and the
        account taxes must follow the fiscal taxes."""
        self.assertAlmostEqual(line.price_subtotal, line.fiscal_amount_untaxed, 2)
        self.assertAlmostEqual(line.price_total, line.fiscal_amount_total, 2)
        self.assertAlmostEqual(
            line.price_gross, line.price_unit * line.product_uom_qty, 2
        )
        # the main company may get a non Brazilian chart of accounts (the CI
        # installs l10n_generic_coa first), then no account tax is mapped
        if self.env["account.tax"].search_count(
            [("company_id", "=", line.company_id.id), ("fiscal_tax_ids", "!=", False)]
        ):
            self.assertTrue(line.tax_id)
        self.assertEqual(
            line.tax_id,
            line.fiscal_tax_ids.account_taxes(
                user_type="sale",
                fiscal_operation=line.fiscal_operation_id,
                company=line.company_id,
            ),
        )

    def _repair_lines(self, repair):
        return list(repair.operations.filtered(lambda op: op.type == "add")) + list(
            repair.fees_lines
        )

    def _invoice_repair_order(self, repair):
        """Confirm the repair, create the invoices and check every link
        between the repair lines and the fiscal documents."""
        repair.action_repair_confirm()
        self.assertEqual(repair.state, "2binvoiced")
        repair.action_repair_invoice_create()
        self.assertEqual(repair.state, "ready")
        self.assertTrue(repair.invoiced)

        invoices = repair.invoice_ids
        lines = self._repair_lines(repair)
        expected_document_types = {
            line.fiscal_operation_line_id.get_document_type(repair.company_id)
            for line in lines
        }
        self.assertEqual(len(invoices), len(expected_document_types))
        self.assertEqual(set(invoices.document_type_id), expected_document_types)
        self.assertEqual(repair.invoice_count, len(invoices))
        # repair.invoice_id is a Many2one in the core, it keeps the last one
        self.assertIn(repair.invoice_id, invoices)
        self.assertEqual(invoices.repair_ids, repair)

        for invoice in invoices:
            self.assertEqual(invoice.state, "draft")
            self.assertEqual(invoice.move_type, "out_invoice")
            self.assertEqual(invoice.fiscal_operation_id, repair.fiscal_operation_id)
            self.assertEqual(invoice.partner_id, repair.partner_invoice_id)
            self.assertEqual(invoice.company_id, repair.company_id)
            self.assertEqual(invoice.invoice_origin, repair.name)
            self.assertTrue(invoice.document_serie_id)

        for line in lines:
            self.assertTrue(line.invoiced)
            aml = line.invoice_line_id
            self.assertTrue(aml, f"{line.name} not linked to an invoice line")
            self.assertIn(aml.move_id, invoices)
            self.assertEqual(
                aml.move_id.document_type_id,
                line.fiscal_operation_line_id.get_document_type(repair.company_id),
            )
            self.assertEqual(
                aml.fiscal_operation_line_id, line.fiscal_operation_line_id
            )
            self.assertEqual(aml.cfop_id, line.cfop_id)
            self.assertEqual(aml.fiscal_tax_ids, line.fiscal_tax_ids)
            self.assertEqual(aml.tax_ids, line.tax_id)
            self.assertAlmostEqual(aml.quantity, line.product_uom_qty, 2)
            self.assertAlmostEqual(aml.price_subtotal, line.price_subtotal, 2)
            self.assertAlmostEqual(aml.price_total, line.price_total, 2)

        self.assertAlmostEqual(
            sum(invoices.mapped("amount_untaxed")), repair.amount_untaxed, 2
        )
        self.assertAlmostEqual(
            sum(invoices.mapped("amount_total")), repair.amount_total, 2
        )
        return invoices

    def _assert_repair_totals(self, repair):
        lines = self._repair_lines(repair)
        self.assertTrue(lines)
        self.assertAlmostEqual(
            repair.amount_untaxed, sum(ln.price_subtotal for ln in lines), 2
        )
        self.assertAlmostEqual(
            repair.amount_total, sum(ln.price_total for ln in lines), 2
        )
        self.assertAlmostEqual(
            repair.amount_price_gross, sum(ln.price_gross for ln in lines), 2
        )
        self.assertAlmostEqual(
            repair.amount_total, repair.amount_untaxed + repair.amount_tax, 2
        )

    def test_l10n_br_repair_products(self):
        """Repair order with parts only: one NF-e."""
        repair = self.so_products
        self.assertEqual(repair.fiscal_operation_id, self.fsc_op_sale)
        for line in repair.operations:
            self._assert_product_line(line)
        self._assert_repair_totals(repair)
        invoices = self._invoice_repair_order(repair)
        self.assertEqual(len(invoices), 1)
        action = repair.action_created_invoice()
        self.assertEqual(action["res_id"], invoices.id)

    def test_l10n_br_repair_services(self):
        """Repair order with fees only: one service document."""
        repair = self.so_services
        for line in repair.fees_lines:
            self._assert_service_line(line)
        self._assert_repair_totals(repair)
        invoices = self._invoice_repair_order(repair)
        self.assertEqual(len(invoices), 1)

    def test_l10n_br_repair_products_services(self):
        """Parts and fees: the fiscal documents are split by document type
        and the repair shows all of them."""
        repair = self.so_prod_srv
        for line in repair.operations:
            self._assert_product_line(line)
        for line in repair.fees_lines:
            self._assert_service_line(line)
        self._assert_repair_totals(repair)
        invoices = self._invoice_repair_order(repair)
        self.assertEqual(len(invoices), 2)
        self.assertEqual(
            {
                ln.invoice_line_id.move_id for ln in repair.operations
            }.pop().document_type_id.code,
            "55",
        )
        action = repair.action_created_invoice()
        self.assertEqual(action["domain"], [("id", "in", invoices.ids)])

    def test_l10n_br_repair_full_cycle(self):
        """Invoice before repair, post the fiscal documents, repair and
        finish: the repair ends done with posted invoices."""
        repair = self.so_prod_srv
        invoices = self._invoice_repair_order(repair)
        invoices.action_post()
        self.assertEqual(set(invoices.mapped("state")), {"posted"})
        repair.action_repair_start()
        self.assertEqual(repair.state, "under_repair")
        repair.action_repair_end()
        self.assertEqual(repair.state, "done")
        self.assertTrue(repair.repaired)
        part_moves = repair.operations.move_id
        self.assertTrue(part_moves)
        self.assertEqual(set(part_moves.mapped("state")), {"done"})
        self.env.flush_all()
        self.env.cr.execute(
            "SELECT state FROM account_move WHERE id IN %s", (tuple(invoices.ids),)
        )
        self.assertEqual({row[0] for row in self.env.cr.fetchall()}, {"posted"})

    def test_l10n_br_repair_without_fiscal_operation(self):
        """Without fiscal operation the core invoicing is kept."""
        repair = self.so_products.copy()
        repair.fiscal_operation_id = False
        repair.operations.fiscal_operation_id = False
        repair.action_repair_confirm()
        repair.action_repair_invoice_create()
        self.assertEqual(len(repair.invoice_ids), 1)
        self.assertFalse(repair.invoice_id.fiscal_operation_id)
        self.assertFalse(repair.invoice_id.invoice_line_ids.fiscal_operation_line_id)


@tagged("post_install", "-at_install")
class TestL10nBrRepair(L10nBrRepairBaseTest, TransactionCase):
    __test__ = True

    company_ref = "base.main_company"
    so_products_ref = "l10n_br_repair.main_so_only_products"
    so_services_ref = "l10n_br_repair.main_so_only_services"
    so_prod_srv_ref = "l10n_br_repair.main_so_product_service"
