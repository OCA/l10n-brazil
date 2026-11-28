# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestNFeExportDetail(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=[cls.company.id])
        )
        cls.abroad = cls.env["res.partner"].create(
            {
                "name": "Cliente do exterior",
                "is_company": True,
                "country_id": cls.env.ref("base.es").id,
                "city": "Gijon",
                "street_name": "Poligono de Roces",
                "street_number": "36",
                "district": "Roces",
                "zip": "33211",
            }
        )
        cls.inland = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        cls.product = cls.env.ref("product.product_product_7")
        cls.document_type = cls.env.ref("l10n_br_fiscal.document_55")
        cls._define_tax("tax_group_icms", "tax_icms_nt", "cst_icms_41")
        cls._define_tax("tax_group_ipi", "tax_ipi_nt", "cst_ipi_53")

    @classmethod
    def _define_tax(cls, tax_group, tax, cst):
        cls.env["l10n_br_fiscal.tax.definition"].create(
            {
                "fiscal_operation_line_id": cls.env.ref(
                    "l10n_br_fiscal.fo_venda_venda"
                ).id,
                "tax_group_id": cls.env.ref(f"l10n_br_fiscal.{tax_group}").id,
                "custom_tax": True,
                "tax_id": cls.env.ref(f"l10n_br_fiscal.{tax}").id,
                "cst_id": cls.env.ref(f"l10n_br_fiscal.{cst}").id,
                "state": "approved",
            }
        )

    def _document(self, partner, cfop_ref, number, **values):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "partner_id": partner.id,
                "document_type_id": self.document_type.id,
                "document_serie": "1",
                "document_number": number,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "fiscal_operation_type": "out",
                **values,
            }
        )
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "name": "Mercadoria exportada",
                "product_id": self.product.id,
                "quantity": 2,
                "price_unit": 5000.0,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "fiscal_operation_line_id": self.env.ref(
                    "l10n_br_fiscal.fo_venda_venda"
                ).id,
                "cfop_id": self.env.ref(cfop_ref).id,
            }
        )
        return document, line

    def test_an_export_needs_the_place_of_shipment(self):
        document, _line = self._document(
            self.abroad, "l10n_br_fiscal.cfop_7101", "910001"
        )
        with self.assertRaises(UserError) as error:
            document._document_check()
        self.assertIn("place of shipment", str(error.exception))

        document.write({"nfe40_UFSaidaPais": "SP", "nfe40_xLocExporta": "Santos"})
        self.assertTrue(document._document_check())

    def test_the_place_of_shipment_is_only_for_an_export(self):
        document, _line = self._document(
            self.inland,
            "l10n_br_fiscal.cfop_5101",
            "910002",
            nfe40_UFSaidaPais="SP",
            nfe40_xLocExporta="Santos",
        )
        with self.assertRaises(UserError) as error:
            document._document_check()
        self.assertIn("356", str(error.exception))

    def test_the_export_detail_is_only_for_an_export_cfop(self):
        document, line = self._document(
            self.inland, "l10n_br_fiscal.cfop_5101", "910003"
        )
        line.nfe40_detExport = [Command.create({"nfe40_nDraw": "12345678901"})]
        with self.assertRaises(UserError) as error:
            document._document_check()
        self.assertIn("336", str(error.exception))

    def test_an_indirect_export_needs_the_export_registration(self):
        document, line = self._document(
            self.abroad,
            "l10n_br_fiscal.cfop_7501",
            "910004",
            nfe40_UFSaidaPais="SP",
            nfe40_xLocExporta="Santos",
        )
        with self.assertRaises(UserError) as error:
            document._document_check()
        self.assertIn("340", str(error.exception))

        line.nfe40_detExport = [
            Command.create(
                {
                    "nfe40_exportInd": self.env["nfe.40.exportind"]
                    .create(
                        {
                            "nfe40_nRE": "12345678901",
                            "nfe40_chNFe": "3" * 44,
                            "nfe40_qExport": 2,
                        }
                    )
                    .id
                }
            )
        ]
        self.assertTrue(document._document_check())

    def test_the_nfe_of_an_export_carries_the_shipping_place(self):
        document, line = self._document(
            self.abroad,
            "l10n_br_fiscal.cfop_7101",
            "910005",
            nfe40_UFSaidaPais="SP",
            nfe40_xLocExporta="Santos",
        )
        line.nfe40_detExport = [Command.create({"nfe40_nDraw": "12345678901"})]
        document.nfe40_detPag = [
            Command.create({"nfe40_tPag": "90", "nfe40_vPag": 0.0})
        ]

        document.action_document_confirm()
        document.with_context(force_product_lang="en_US")._document_export()

        self.assertFalse(document.xml_error_message)
        xml = base64.b64decode(document.send_file_id.datas).decode()
        self.assertEqual(line.cfop_id.code, "7101")
        self.assertIn("<UFSaidaPais>SP</UFSaidaPais>", xml)
        self.assertIn("<xLocExporta>Santos</xLocExporta>", xml)
        self.assertIn("<nDraw>12345678901</nDraw>", xml)
        self.assertIn("<idDest>3</idDest>", xml)
