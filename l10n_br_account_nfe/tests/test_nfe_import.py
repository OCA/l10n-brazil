import base64
import os

from odoo import Command
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
            user=cls.user, context=dict(cls.env.context, tracking_disable=True)
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

        wizard = self.env["l10n_br_nfe.import_xml"].create({})
        with Form(wizard) as import_form:
            import_form.file = base64.b64encode(file_content)
            import_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras")
            self.assertEqual(import_form.xml_partner_name, "FORNECEDER NFE DEMO LTDA")
            lines = import_form.imported_products_ids._records
        for line in lines:  # ensure testing consistency
            del line["id"]
            del line["product_id"]
            del line["ncm_internal"]
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

        self.assertTrue(abs(move.amount_price_gross - 11975.96) < 0.01)
        self.assertTrue(abs(move.amount_discount_value - 0) < 0.01)
        self.assertTrue(abs(move.amount_untaxed - 11975.96) < 0.01)
        self.assertTrue(abs(move.amount_freight_value - 0) < 0.01)
        self.assertTrue(abs(move.amount_insurance_value - 0) < 0.01)
        self.assertTrue(abs(move.amount_other_value - 0) < 0.01)
        self.assertTrue(abs(move.amount_tax - 132.14) < 0.01)
        self.assertTrue(abs(move.amount_total - 12108.10) < 0.01)

        self.assertEqual(len(move.invoice_line_ids), 4)

        self.assertEqual(
            move.invoice_line_ids[0].product_id.name,
            "PAPEL CELOFANE (CELULOSE) 35GSM 19x24CM",
        )
        self.assertEqual(move.invoice_line_ids[0].product_id.code, "1070147")
        self.assertEqual(move.invoice_line_ids[0].product_id.ncm_id.code, "48111090")
        self.assertEqual(move.invoice_line_ids[0].quantity, 70.1)
        self.assertTrue(abs(move.invoice_line_ids[0].fiscal_quantity - 70.1) < 0.01)
        self.assertTrue(abs(move.invoice_line_ids[0].price_unit - 58.0) < 0.01)
        self.assertTrue(abs(move.invoice_line_ids[0].fiscal_price - 58.0) < 0.01)
        self.assertTrue(abs(move.invoice_line_ids[0].price_subtotal - 4065.80) < 0.01)
        self.assertEqual(move.invoice_line_ids[0].nfe40_xPed, "OC00589")
        self.assertEqual(move.invoice_line_ids[0].product_uom_id.code, "KG")

        self.assertEqual(
            move.invoice_line_ids[0].icms_tax_id.id,
            self.ref("l10n_br_fiscal.tax_icms_12"),
        )
        self.assertTrue(abs(move.invoice_line_ids[0].icms_value - 487.90) < 0.01)
        self.assertEqual(
            move.invoice_line_ids[0].ipi_tax_id.id,
            self.ref("l10n_br_fiscal.tax_ipi_3_25"),
        )
        self.assertTrue(abs(move.invoice_line_ids[0].ipi_value - 132.14) < 0.01)
        self.assertEqual(
            move.invoice_line_ids[0].pis_tax_id.id,
            self.ref("l10n_br_fiscal.tax_pis_0_65"),
        )
        self.assertTrue(abs(move.invoice_line_ids[0].pis_value - 23.26) < 0.01)
        self.assertEqual(
            move.invoice_line_ids[0].cofins_tax_id.id,
            self.ref("l10n_br_fiscal.tax_cofins_3"),
        )
        self.assertTrue(abs(move.invoice_line_ids[0].ipi_value - 132.14) < 0.01)

        self.assertEqual(
            move.invoice_line_ids[1].product_id.name,
            "PAVIO P/VELA VOTIVA 50 X 150MM (C102018007170)",
        )
        self.assertEqual(move.invoice_line_ids[1].product_id.code, "B100618007170")
        self.assertEqual(move.invoice_line_ids[1].product_id.ncm_id.code, "34060000")
        self.assertEqual(move.invoice_line_ids[1].quantity, 60)
        self.assertTrue(abs(move.invoice_line_ids[1].fiscal_quantity - 60) < 0.01)
        self.assertEqual(move.invoice_line_ids[1].product_uom_id.code, "MILHEI")
        self.assertTrue(abs(move.invoice_line_ids[1].price_subtotal - 3439.20) < 0.01)

        self.assertEqual(len(move.due_line_ids), 3)
        self.assertEqual(move.due_line_ids[0].credit, 4035.63)
        self.assertEqual(move.due_line_ids[1].credit, 4035.63)
        self.assertEqual(move.due_line_ids[2].credit, 4036.84)
