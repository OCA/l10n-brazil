# Copyright 2024 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestOperation(TransactionCase):
    def test_copy(self):
        """Test Operation copy()"""
        operation_venda = self.env.ref("l10n_br_fiscal.fo_venda")
        operation_venda_copy = operation_venda.copy()
        self.assertEqual(operation_venda_copy.name, "Venda")
        self.assertEqual(operation_venda_copy.code, "VD (Copy)")


class TestOperationLineRequiresST(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.operation_venda = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.line_revenda = cls.env.ref("l10n_br_fiscal.fo_venda_revenda")
        cls.line_revenda_st = cls.env.ref("l10n_br_fiscal.fo_venda_revenda_st")
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        cest = cls.env.ref("l10n_br_fiscal.cest_0100100")
        ncm = cest.ncm_ids[:1]
        cls.product_with_st = cls.env["product.product"].create(
            {
                "name": "Produto Teste com ST",
                "ncm_id": ncm.id,
                "cest_id": cest.id,
                "fiscal_type": cls.line_revenda.product_type,
            }
        )
        cls.product_without_st = cls.env["product.product"].create(
            {
                "name": "Produto Teste sem ST",
                "ncm_id": ncm.id,
                "fiscal_type": cls.line_revenda.product_type,
            }
        )

    def test_line_definition_without_st_returns_revenda(self):
        result = self.operation_venda.line_definition(
            company=self.company,
            partner=self.partner,
            product=self.product_without_st,
        )
        self.assertEqual(result, self.line_revenda)

    def test_line_definition_with_st_returns_revenda_st(self):
        result = self.operation_venda.line_definition(
            company=self.company,
            partner=self.partner,
            product=self.product_with_st,
        )
        self.assertEqual(result, self.line_revenda_st)

    def test_line_domain_excludes_st_line_when_product_has_no_cest(self):
        domain = self.operation_venda._line_domain(
            self.company, self.partner, self.product_without_st
        )
        candidates = self.env["l10n_br_fiscal.operation.line"].search(domain)
        self.assertIn(self.line_revenda, candidates)
        self.assertNotIn(self.line_revenda_st, candidates)
