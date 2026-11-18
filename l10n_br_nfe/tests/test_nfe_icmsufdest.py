# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNFeICMSUFDest(TransactionCase):
    """ICMSTot DIFAL totals only add the items that carry ICMSUFDest."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.company.partner_id.write(
            {
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_sp").id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "DIFAL Product", "list_price": 100.0}
        )

    def _create_line(self, ind_ie_dest, profile_xmlid):
        partner = self.env["res.partner"].create(
            {
                "name": f"DIFAL MG {ind_ie_dest}",
                "is_company": True,
                "country_id": self.env.ref("base.br").id,
                "state_id": self.env.ref("base.state_br_mg").id,
                "fiscal_profile_id": self.env.ref(profile_xmlid).id,
                "ind_ie_dest": ind_ie_dest,
            }
        )
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "partner_id": partner.id,
                "fiscal_operation_type": "out",
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
            }
        )
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        # DIFAL values of a sale of 100.00 from SP to MG written directly,
        # as if they came from the tax engine or from an imported document
        line.write(
            {
                "icms_value": 12.0,
                "icms_destination_value": 7.5,
                "icms_origin_value": 0.0,
                "icmsfcp_value": 2.5,
            }
        )
        return line

    def test_non_taxpayer_totals_follow_items(self):
        """Non-taxpayer: the item carries ICMSUFDest and ICMSTot adds it."""
        line = self._create_line("9", "l10n_br_fiscal.partner_fiscal_profile_snn")
        document = line.document_id
        self.assertTrue(line._nfe40_has_ICMSUFDest())
        self.assertEqual(document.nfe40_vICMSUFDest, 7.5)
        self.assertEqual(document.nfe40_vFCPUFDest, 2.5)
        self.assertEqual(document.nfe40_vICMSUFRemet, 0.0)

    def test_taxpayer_totals_without_items(self):
        """Taxpayer: no ICMSUFDest in the item, so ICMSTot stays at zero."""
        line = self._create_line("1", "l10n_br_fiscal.partner_fiscal_profile_cnt")
        document = line.document_id
        self.assertFalse(line._nfe40_has_ICMSUFDest())
        self.assertEqual(document.nfe40_vICMSUFDest, 0.0)
        self.assertEqual(document.nfe40_vFCPUFDest, 0.0)
        self.assertEqual(document.nfe40_vICMSUFRemet, 0.0)
