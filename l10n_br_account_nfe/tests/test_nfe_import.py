# Copyright 2025 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os

from erpbrasil.base.misc import punctuation_rm

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase
from odoo.tests.common import Form

from odoo.addons import l10n_br_account_nfe


class NFeImportTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.user = cls.env["res.users"].create(
            {
                "name": "Because I am accountman!",
                "login": "accountman",
                "password": "accountman",
                "groups_id": [
                    # we purposely don't give Fiscal access rights now to ensure
                    # non fiscal operations are still allowed
                    Command.set(cls.env.user.groups_id.ids),
                    Command.link(cls.env.ref("account.group_account_manager").id),
                    Command.link(cls.env.ref("account.group_account_user").id),
                    Command.link(cls.env.ref("l10n_br_fiscal.group_user").id),
                    Command.link(cls.env.ref("l10n_br_nfe.group_manager").id),
                ],
            }
        )
        cls.user.partner_id.email = "accountman@test.com"
        companies = cls.env["res.company"].search([])
        cls.user.write(
            {
                "company_ids": [Command.set(companies.ids)],
                "company_id": cls.company.id,
            }
        )

        cls.env = cls.env(
            user=cls.user,
            context=dict(
                cls.env.context,
                tracking_disable=True,
                allowed_company_ids=[cls.company.id],
            ),
        )

    def test_import_in_nfe(self):
        file_path = os.path.join(
            l10n_br_account_nfe.__path__[0],
            "tests",
            "nfe",
            "35231149647316000169550010000661061151600085-nfe.xml",
        )
        with open(file_path, "rb") as file:
            file_content = file.read()

        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create({})
        with Form(wizard) as import_form:
            import_form.file = base64.b64encode(file_content)
            import_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras")
            lines = import_form.imported_products_ids._records
        for line in lines:  # ensure testing consistency
            del line["id"]
            del line["product_id"]
            del line["ncm_internal"]
            del line["cfop_warning"]
            # match source fields are provided by l10n_br_fiscal_edi and
            # depend on the installed purchase/stock modules and demo data
            del line["match_source_id"]
            del line["match_source_available"]
            del line["match_source_product_matched"]
            del line["company_id"]
            del line["issuer_partner_id"]
        self.assertEqual(len(lines), 4)
        self.assertDictEqual(
            lines[0],
            {
                "icms_value": "487.90",
                "uom_conversion_factor": 1.0,
                "total": 4065.8,
                "new_cfop_id": False,
                "product_name": "PAPEL CELOFANE (CELULOSE) 35GSM 19x24CM",
                "icms_percent": "12.0000",
                "ipi_value": "132.14",
                "uom_com": "KG",
                "ncm_xml": "48111090",
                "cfop_xml": "6101",
                "ipi_percent": "3.2500",
                "price_unit_com": 58.0,
                "product_code": "1070147",
                "quantity_com": 70.1,
                "uom_internal": 12,
            },
        )
        self.assertDictEqual(
            lines[1],
            {
                "icms_value": "412.70",
                "uom_conversion_factor": 1.0,
                "total": 3439.2,
                "new_cfop_id": False,
                "product_name": "PAVIO P/VELA VOTIVA 50 X 150MM (C102018007170)",
                "icms_percent": "12.0000",
                "ipi_value": "0.00",
                "uom_com": "MIL",
                "ncm_xml": "34060000",
                "cfop_xml": "6101",
                "ipi_percent": "0.0000",
                "price_unit_com": 57.32,
                "product_code": "B100618007170",
                "quantity_com": 60.0,
                "uom_internal": 61,
            },
        )
        self.assertDictEqual(
            lines[2],
            {
                "quantity_com": 48.0,
                "uom_conversion_factor": 1.0,
                "icms_value": "330.16",
                "ncm_xml": "34060000",
                "icms_percent": "12.0000",
                "uom_internal": 61,
                "cfop_xml": "6101",
                "product_code": "B101518007170",
                "ipi_value": "0.00",
                "product_name": "PAVIO P/VELA VOTIVA 57 X 150MM",
                "uom_com": "MIL",
                "price_unit_com": 57.32,
                "total": 2751.36,
                "new_cfop_id": False,
                "ipi_percent": "0.0000",
            },
        )
        self.assertDictEqual(
            lines[3],
            {
                "icms_value": "206.35",
                "uom_conversion_factor": 1.0,
                "total": 1719.6,
                "new_cfop_id": False,
                "product_name": "PAVIO P/VELA VOTIVA 50 X 140MM (C102018007160)",
                "icms_percent": "12.0000",
                "ipi_value": "0.00",
                "uom_com": "MIL",
                "ncm_xml": "34060000",
                "cfop_xml": "6101",
                "ipi_percent": "0.0000",
                "price_unit_com": 57.32,
                "product_code": "B100618007160",
                "quantity_com": 30.0,
                "uom_internal": 61,
            },
        )

        action = wizard.action_import_and_open_move()
        move = self.env["account.move"].browse(action["res_id"])

        self.assertEqual(move.partner_id.name, "FORNECEDER NFE DEMO LTDA")
        self.assertEqual(move.partner_id.vat, "04.712.500/0001-07")
        self.assertEqual(move.partner_id.l10n_br_ie_code, "078016350838")
        self.assertEqual(
            move.document_type_id, self.env.ref("l10n_br_fiscal.document_55")
        )
        self.assertEqual(
            move.fiscal_operation_id, self.env.ref("l10n_br_fiscal.fo_compras")
        )
        self.assertEqual(move.document_number, "66106")
        self.assertEqual(
            move.document_key, "35231149647316000169550010000661061151600085"
        )

        self.assertAlmostEqual(move.amount_price_gross, 11975.96, places=2)
        self.assertAlmostEqual(move.amount_discount_value, 0, places=2)
        self.assertAlmostEqual(move.amount_untaxed, 11975.96, places=2)
        self.assertAlmostEqual(move.amount_freight_value, 0, places=2)
        self.assertAlmostEqual(move.amount_insurance_value, 0, places=2)
        self.assertAlmostEqual(move.amount_other_value, 0, places=2)
        self.assertAlmostEqual(move.amount_tax, 132.14, places=2)
        self.assertAlmostEqual(move.amount_total, 12108.10, places=2)

        self.assertEqual(len(move.invoice_line_ids), 4)

        # The wizard stamps the effective incoming date (DT_E_S in the SPED
        # bookkeeping), defaulting to the import date.
        self.assertTrue(move.fiscal_document_id.date_in_out)

        # The supplier declared CFOP 6101 (interstate sale); the de-para
        # recomputes it to the company's inbound CFOP, but partner_cfop_id
        # preserves the declared value for bookkeeping / SPED (C197).
        doc_line = move.fiscal_document_id.fiscal_line_ids[0]
        self.assertEqual(doc_line.partner_cfop_id.code, "6101")
        self.assertNotEqual(doc_line.cfop_id.code, "6101")

        self.assertEqual(
            move.invoice_line_ids[0].product_id.name,
            "PAPEL CELOFANE (CELULOSE) 35GSM 19x24CM",
        )
        self.assertEqual(move.invoice_line_ids[0].product_id.code, "1070147")
        self.assertEqual(move.invoice_line_ids[0].product_id.ncm_id.code, "48111090")
        self.assertEqual(move.invoice_line_ids[0].quantity, 70.1)
        self.assertAlmostEqual(move.invoice_line_ids[0].fiscal_quantity, 70.1, places=2)
        self.assertAlmostEqual(move.invoice_line_ids[0].price_unit, 58.0, places=2)
        self.assertAlmostEqual(move.invoice_line_ids[0].fiscal_price, 58.0, places=2)
        self.assertAlmostEqual(
            move.invoice_line_ids[0].price_subtotal, 4065.80, places=2
        )
        self.assertEqual(move.invoice_line_ids[0].nfe40_xPed, "OC00589")
        self.assertEqual(move.invoice_line_ids[0].product_uom_id.code, "KG")

        self.assertEqual(
            move.invoice_line_ids[0].icms_tax_id.id,
            self.ref("l10n_br_fiscal.tax_icms_12"),
        )
        self.assertAlmostEqual(move.invoice_line_ids[0].icms_value, 487.90, places=2)
        self.assertEqual(
            move.invoice_line_ids[0].ipi_tax_id.id,
            self.ref("l10n_br_fiscal.tax_ipi_3_25"),
        )
        self.assertAlmostEqual(move.invoice_line_ids[0].ipi_value, 132.14, places=2)
        self.assertEqual(
            move.invoice_line_ids[0].pis_tax_id.id,
            self.ref("l10n_br_fiscal.tax_pis_0_65"),
        )
        self.assertAlmostEqual(move.invoice_line_ids[0].pis_value, 23.26, places=2)
        self.assertEqual(
            move.invoice_line_ids[0].cofins_tax_id.id,
            self.ref("l10n_br_fiscal.tax_cofins_3"),
        )
        self.assertEqual(
            move.invoice_line_ids[1].product_id.name,
            "PAVIO P/VELA VOTIVA 50 X 150MM (C102018007170)",
        )
        self.assertEqual(move.invoice_line_ids[1].product_id.code, "B100618007170")
        self.assertEqual(move.invoice_line_ids[1].product_id.ncm_id.code, "34060000")
        self.assertEqual(move.invoice_line_ids[1].quantity, 60)
        self.assertAlmostEqual(move.invoice_line_ids[1].fiscal_quantity, 60, places=2)
        self.assertEqual(move.invoice_line_ids[1].product_uom_id.code, "MILHEI")
        self.assertAlmostEqual(
            move.invoice_line_ids[1].price_subtotal, 3439.20, places=2
        )

        self.assertEqual(len(move.due_line_ids), 3)
        self.assertAlmostEqual(move.due_line_ids[0].credit, 4035.63, places=2)
        self.assertAlmostEqual(move.due_line_ids[1].credit, 4035.63, places=2)
        self.assertAlmostEqual(move.due_line_ids[2].credit, 4036.84, places=2)

    def test_import_switches_to_the_company_the_document_is_addressed_to(self):
        """The CNPJ of the destination identifies the company the document
        belongs to: the import runs in that company, not in the user's current
        one, so the fiscal operations, the taxes and the journal are resolved
        with the configuration of the right company."""
        other_company = self.env.ref("base.main_company")
        self.assertNotEqual(other_company, self.company)
        # the CNPJ the document is addressed to is the one of self.company
        self.assertEqual(punctuation_rm(self.company.cnpj_cpf or ""), "81583054000129")
        env = self.env(
            context=dict(
                self.env.context,
                allowed_company_ids=[other_company.id, self.company.id],
            )
        )
        self.assertEqual(env.company, other_company)

        file_path = os.path.join(
            l10n_br_account_nfe.__path__[0],
            "tests",
            "nfe",
            "35231149647316000169550010000661061151600085-nfe.xml",
        )
        with open(file_path, "rb") as file:
            file_content = file.read()

        wizard = env["l10n_br_fiscal.document.import.wizard"].create(
            {"company_id": other_company.id, "file": base64.b64encode(file_content)}
        )
        wizard._onchange_file()

        # the wizard switched to the company the document is addressed to
        self.assertEqual(wizard.destination_cnpj, self.company.cnpj_cpf)
        self.assertEqual(wizard.company_id, self.company)
        self.assertEqual(wizard.fiscal_operation_type, "in")

        wizard.fiscal_operation_id = env.ref("l10n_br_fiscal.fo_compras")
        action = wizard.action_import_and_open_move()
        move = env["account.move"].browse(action["res_id"])

        self.assertEqual(move.company_id, self.company)
        self.assertEqual(move.fiscal_document_id.company_id, self.company)
        # the taxes resolved with the configuration of that company: the bill
        # totals are the ones of the fixture (see test_import_in_nfe, imported
        # in the same company but started from the right current company)
        self.assertAlmostEqual(move.amount_total, 12108.10, places=2)

    def test_import_incomplete_document_is_blocked(self):
        """A document with a line missing its product/uom/qty/price must not
        be importable into an account move (SPED data integrity)."""
        file_path = os.path.join(
            l10n_br_account_nfe.__path__[0],
            "tests",
            "nfe",
            "35231149647316000169550010000661061151600085-nfe.xml",
        )
        with open(file_path, "rb") as file:
            file_content = file.read()

        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create({})
        with Form(wizard) as import_form:
            import_form.file = base64.b64encode(file_content)
            import_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras")

        _binding, document = wizard._import_edoc()
        # Break one line to simulate an unmatched product.
        document.fiscal_line_ids[0].product_id = False
        with self.assertRaises(UserError):
            document._check_document_import()

    def test_import_carries_the_order_reference_onto_the_bill(self):
        """End to end from the import wizard to the vendor bill: the order
        reference of the document (or the canonical one the operator
        synthesized by picking a match source) must reach the
        (partner_order, partner_order_line) fields of the bill lines, line by
        line — that pair is what the stock bill matching reconciles on, and
        this module neither requires nor imports stock."""
        if "purchase.order" not in self.env:
            self.skipTest("purchase module not installed")
        file_path = os.path.join(
            l10n_br_account_nfe.__path__[0],
            "tests",
            "nfe",
            "35231149647316000169550010000661061151600085-nfe.xml",
        )
        with open(file_path, "rb") as file:
            file_content = file.read()

        # The supplier as declared in the xml body: in this fixture the CNPJ of
        # the document key is that of another company, so the issuer the wizard
        # resolves from the key is not the supplier — the operator (and here
        # the test) sets it explicitly.
        supplier = self.env["res.partner"].search(
            [("cnpj_cpf_stripped", "=", "04712500000107")], limit=1
        )
        if not supplier:
            supplier = self.env["res.partner"].create(
                {
                    "name": "FORNECEDOR NFE DEMO LTDA",
                    "cnpj_cpf": "04.712.500/0001-07",
                }
            )
        product = self.env["product.product"].create(
            {
                "name": "Ordered Product (PO)",
                "default_code": "XML-PO-ORDERED",
                "purchase_ok": True,
            }
        )
        order = self.env["purchase.order"].create(
            {"partner_id": supplier.id, "company_id": self.company.id}
        )
        if (
            "fiscal_operation_id" in order._fields
            and self.company.purchase_fiscal_operation_id
        ):
            order.fiscal_operation_id = self.company.purchase_fiscal_operation_id
        self.env["purchase.order.line"].create(
            {
                "order_id": order.id,
                "product_id": product.id,
                "name": product.name,
                "product_qty": 100.0,
                "price_unit": 10.0,
            }
        )
        order.with_context(tracking_disable=True).button_confirm()

        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {"company_id": self.company.id, "file": base64.b64encode(file_content)}
        )
        wizard._onchange_file()
        wizard.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras")
        wizard.issuer_partner_id = supplier
        self.assertTrue(wizard.match_source_available)

        # the operator reconciles the first xml line (the paper) with the order;
        # no product is mapped yet on that line, so the reference is synthesized
        # from the xml product code
        line = wizard.imported_products_ids.filtered(
            lambda wline: wline.product_code == "1070147"
        )
        self.assertTrue(line)
        line.match_source_id = self.env[
            "l10n_br_fiscal.document.import.match.candidate"
        ].search([("po_line_id", "=", order.order_line.id)], limit=1)
        self.assertTrue(line.match_source_id)

        action = wizard.action_import_and_open_move()
        move = self.env["account.move"].browse(action["res_id"])
        self.assertEqual(move.move_type, "in_invoice")

        matched = move.invoice_line_ids.filtered(
            lambda aml: aml.product_id.code == "1070147"
        )
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched.partner_order, order.name)
        self.assertEqual(matched.partner_order_line, "1")
        # the canonical reference, i.e. the value the matching screen displays
        expr = self.env["account.move.line"]._get_bill_matching_reference_sql("aml")
        self.env.cr.execute(
            f"SELECT ({expr}) FROM account_move_line aml WHERE aml.id = %s",
            [matched.id],
        )
        self.assertEqual(self.env.cr.fetchone()[0], f"{order.name}-1")

        # the other lines keep the reference the document declared (xPed), they
        # are not stamped with the chosen source: the mapping is per line
        others = move.invoice_line_ids - matched
        self.assertEqual(others.mapped("partner_order"), ["OC00589"] * len(others))
        self.assertEqual(others.mapped("partner_order_line"), [False] * len(others))
