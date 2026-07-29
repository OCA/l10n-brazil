# Copyright 2024 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from .tools import load_fiscal_fixture_files


class TestOperation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_fiscal_fixture_files(cls.env)

    def test_copy(self):
        """Test Operation copy()"""
        operation_venda = self.env.ref("l10n_br_fiscal.fo_venda")
        operation_venda_copy = operation_venda.copy()
        self.assertEqual(operation_venda_copy.name, "Venda")
        self.assertEqual(operation_venda_copy.code, "VD (Copy)")

    def test_operation_line_is_icmsst_computed_field(self):
        """Operation Line ``is_icmsst`` should follow its CFOPs."""
        line_revenda = self.env.ref("l10n_br_fiscal.fo_venda_revenda")
        self.assertFalse(line_revenda.is_icmsst)

        line_revenda.cfop_internal_id = self.env.ref("l10n_br_fiscal.cfop_5403")
        self.assertTrue(line_revenda.is_icmsst)

    def test_venda_dedicated_icmsst_lines_are_flagged(self):
        """Sanity check on the dedicated ICMS ST demo Operation Lines: the
        "...ST" lines must be flagged ``is_icmsst`` and their regular
        counterparts must not."""
        self.assertFalse(self.env.ref("l10n_br_fiscal.fo_venda_venda").is_icmsst)
        self.assertTrue(self.env.ref("l10n_br_fiscal.fo_venda_vendast").is_icmsst)
        self.assertFalse(self.env.ref("l10n_br_fiscal.fo_venda_revenda").is_icmsst)
        self.assertTrue(self.env.ref("l10n_br_fiscal.fo_venda_revendast").is_icmsst)

    def test_line_definition_selects_icmsst_line(self):
        """``line_definition`` must prefer the dedicated "Revenda ST"
        Operation Line when the product/partner/company combination is
        subject to ICMS ST, and keep the regular "Revenda" line otherwise.
        """
        operation_venda = self.env.ref("l10n_br_fiscal.fo_venda")
        line_revenda = self.env.ref("l10n_br_fiscal.fo_venda_revenda")
        line_revenda_st = self.env.ref("l10n_br_fiscal.fo_venda_revendast")

        company = self.env.ref("base.main_company")
        partner = self.env.ref("l10n_br_base.res_partner_akretion")
        product = self.env.ref("product.product_product_1")

        company.icms_regulation_id = self.env.ref("l10n_br_fiscal.tax_icms_regulation")
        company.state_id = self.env.ref("base.state_br_sp")
        partner.state_id = self.env.ref("base.state_br_sp")
        partner.ind_ie_dest = "1"
        product.fiscal_type = "00"
        product.ncm_id = self.env.ref("l10n_br_fiscal.ncm_48191000")
        product.cest_id = self.env.ref("l10n_br_fiscal.cest_2112300")

        # Product/partner/company combination subject to ICMS ST: the
        # dedicated "Revenda ST" line must be selected.
        line = operation_venda.line_definition(company, partner, product)
        self.assertEqual(line, line_revenda_st)

        # A product not subject to ICMS ST must still get the regular line.
        product.cest_id = False
        line = operation_venda.line_definition(company, partner, product)
        self.assertEqual(line, line_revenda)

    def test_line_definition_selects_icmsst_line_for_purchase(self):
        """Same behavior on the purchase side, where the regular and ICMS
        ST lines ("Compra para industrialização" / "... com ST") are
        otherwise equally specific (no ``product_type`` set on either),
        so ``is_icmsst`` is what breaks the tie. Uses ``fiscal_type="04"``
        because it isn't claimed by any of the other, more specific
        "Compras" lines (resale="00", fixed asset="08", consumption="07",
        service="09"), so it doesn't introduce an unrelated tie-breaker."""
        operation_compras = self.env.ref("l10n_br_fiscal.fo_compras")
        line_compras = self.env.ref("l10n_br_fiscal.fo_compras_compras")
        line_compras_st = self.env.ref("l10n_br_fiscal.fo_compras_compras_st")

        company = self.env.ref("base.main_company")
        partner = self.env.ref("l10n_br_base.res_partner_akretion")
        product = self.env.ref("product.product_product_1")

        company.icms_regulation_id = self.env.ref("l10n_br_fiscal.tax_icms_regulation")
        company.state_id = self.env.ref("base.state_br_sp")
        partner.state_id = self.env.ref("base.state_br_sp")
        product.tax_icms_or_issqn = "icms"
        product.fiscal_type = "04"
        product.ncm_id = self.env.ref("l10n_br_fiscal.ncm_48191000")
        product.cest_id = self.env.ref("l10n_br_fiscal.cest_2112300")

        line = operation_compras.line_definition(company, partner, product)
        self.assertEqual(line, line_compras_st)

        product.cest_id = False
        line = operation_compras.line_definition(company, partner, product)
        self.assertEqual(line, line_compras)

    def test_line_definition_without_dedicated_icmsst_line_is_unaffected(self):
        """When a Fiscal Operation has no dedicated ICMS ST line at all,
        ``line_definition`` must keep its historical behavior and not
        filter by ``is_icmsst``, so existing setups that don't use this
        feature are unaffected."""
        operation = self.env["l10n_br_fiscal.operation"].create(
            {
                "code": "TESTOP",
                "name": "Test Operation",
                "fiscal_operation_type": "out",
                "fiscal_type": "sale",
                "state": "approved",
            }
        )
        line = self.env["l10n_br_fiscal.operation.line"].create(
            {
                "fiscal_operation_id": operation.id,
                "name": "Test Line",
                "cfop_internal_id": self.env.ref("l10n_br_fiscal.cfop_5102").id,
                "state": "approved",
            }
        )
        self.assertFalse(line.is_icmsst)

        company = self.env.ref("base.main_company")
        partner = self.env.ref("l10n_br_base.res_partner_akretion")
        product = self.env.ref("product.product_product_1")

        company.icms_regulation_id = self.env.ref("l10n_br_fiscal.tax_icms_regulation")
        company.state_id = self.env.ref("base.state_br_sp")
        partner.state_id = self.env.ref("base.state_br_sp")
        product.ncm_id = self.env.ref("l10n_br_fiscal.ncm_48191000")
        product.cest_id = self.env.ref("l10n_br_fiscal.cest_2112300")

        self.assertEqual(operation.line_definition(company, partner, product), line)
