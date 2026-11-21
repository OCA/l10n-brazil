# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNFeICMSReliefTotal(TransactionCase):
    """ICMSTot/vICMSDeson adds the items that carry the ICMS relief."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.product = cls.env["product.product"].create(
            {"name": "ICMS Relief Product", "list_price": 100.0}
        )
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                "fiscal_operation_type": "out",
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
            }
        )

    def _create_line(self, relief_xmlid, relief_value):
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
            }
        )
        # relief values written directly, as if they came from the tax engine
        # or from an imported document
        line.write(
            {
                "icms_relief_id": relief_xmlid and self.env.ref(relief_xmlid).id,
                "icms_relief_value": relief_value,
            }
        )
        return line

    def test_total_adds_the_relief_of_the_items(self):
        """The header total is the sum of vICMSDeson of the items."""
        self._create_line("l10n_br_fiscal.icms_relief_9", 12.0)
        self._create_line("l10n_br_fiscal.icms_relief_9", 3.5)
        self.assertEqual(self.document.nfe40_vICMSDeson, 15.5)

    def test_total_skips_items_without_relief_reason(self):
        """An item without the relief reason exports no vICMSDeson, so the
        header total must not add its value either."""
        self._create_line("l10n_br_fiscal.icms_relief_9", 12.0)
        self._create_line(False, 5.0)
        self.assertEqual(self.document.nfe40_vICMSDeson, 12.0)
