# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests import TransactionCase

ALL_CREDIT = dict.fromkeys(("icms", "ipi", "pis", "cofins"), "credit")
ALL_COST = dict.fromkeys(("icms", "ipi", "pis", "cofins"), "cost")


class TestDocumentLineTaxCreditability(TransactionCase):
    """The fiscal document line answers which taxes of an entry are a
    credit and which a cost, with the same gates the net cost uses and
    without storing anything."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company_real = cls.env.ref("l10n_br_base.empresa_lucro_real")
        cls.company_presumido = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company_simples = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        (cls.company_real + cls.company_presumido).write({"is_industry": True})
        cls.product = cls.env.ref("product.product_product_6")
        cls.supplier = cls.env.ref("l10n_br_base.res_partner_intel")
        cls.supplier.tax_framework = "3"  # Normal
        cls.customer = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        cls.document_type = cls.env.ref("l10n_br_fiscal.document_55")
        cls.purchase = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.resale = cls.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
        cls.own_use = cls.env.ref("l10n_br_fiscal.fo_compras_compras_uso_consumo")
        cls.asset = cls.env.ref("l10n_br_fiscal.fo_compras_compras_ativo")
        cls.sale = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.sale_line = cls.env.ref("l10n_br_fiscal.fo_venda_venda")

    def _make_line(self, company, operation_line, operation=None, partner=None):
        operation = operation or self.purchase
        partner = partner or self.supplier
        line_values = {
            "name": "Creditability",
            "product_id": self.product.id,
            "uom_id": self.product.uom_id.id,
            "quantity": 1.0,
            "price_unit": 800.0,
            "fiscal_operation_id": operation.id,
            "fiscal_operation_line_id": operation_line.id,
        }
        issuer = "partner" if operation.fiscal_operation_type == "in" else "company"
        model = self.env["l10n_br_fiscal.document"].with_company(company)
        document = model.create(
            {
                "company_id": company.id,
                "document_type_id": self.document_type.id,
                "issuer": issuer,
                "partner_id": partner.id,
                "fiscal_operation_id": operation.id,
                "fiscal_operation_type": operation.fiscal_operation_type,
                "fiscal_line_ids": [Command.create(line_values)],
            }
        )
        return document.fiscal_line_ids

    def test_resale_entry_in_lucro_real_credits_everything(self):
        line = self._make_line(self.company_real, self.resale)
        self.assertEqual(line.cfop_id.type_move, "purchase_commerce")
        self.assertEqual(line._get_tax_creditability_map(), ALL_CREDIT)

    def test_lucro_presumido_keeps_piscofins_in_the_cost(self):
        line = self._make_line(self.company_presumido, self.resale)
        self.assertEqual(
            line._get_tax_creditability_map(),
            {"icms": "credit", "ipi": "credit", "pis": "cost", "cofins": "cost"},
        )

    def test_own_use_cfop_vetoes_every_credit(self):
        line = self._make_line(self.company_real, self.own_use)
        self.assertEqual(line.cfop_id.type_move, "purchase_ownuse")
        self.assertEqual(line._get_tax_creditability_map(), ALL_COST)

    def test_fixed_asset_cfop_vetoes_every_credit(self):
        line = self._make_line(self.company_real, self.asset)
        self.assertEqual(line.cfop_id.type_move, "purchase_asset")
        self.assertEqual(line._get_tax_creditability_map(), ALL_COST)

    def test_simples_supplier_without_transferred_credit_vetoes_icms(self):
        self.supplier.tax_framework = "1"
        line = self._make_line(self.company_real, self.resale)
        self.assertFalse(line.icmssn_credit_value)
        tax_map = line._get_tax_creditability_map()
        self.assertEqual(tax_map["icms"], "cost")
        self.assertEqual(tax_map["pis"], "credit")
        self.assertEqual(tax_map["cofins"], "credit")

    def test_simples_buyer_vetoes_everything(self):
        line = self._make_line(self.company_simples, self.resale)
        self.assertEqual(line._get_tax_creditability_map(), ALL_COST)

    def test_outgoing_line_reports_credit(self):
        line = self._make_line(
            self.company_real,
            self.sale_line,
            operation=self.sale,
            partner=self.customer,
        )
        self.assertEqual(line.cfop_id.type_in_out, "out")
        self.assertEqual(line._get_tax_creditability_map(), ALL_CREDIT)

    def test_line_without_cfop_reports_credit(self):
        line = self._make_line(self.company_simples, self.resale)
        self.assertEqual(line._get_tax_creditability_map(), ALL_COST)

        line.cfop_id = False

        self.assertEqual(line._get_tax_creditability_map(), ALL_CREDIT)

    def test_the_map_follows_the_line_without_storing(self):
        line = self._make_line(self.company_real, self.resale)
        self.assertEqual(line._get_tax_creditability_map()["pis"], "credit")

        self.company_real.piscofins_id = self.env.ref(
            "l10n_br_fiscal.tax_pis_cofins_columativo"
        )

        self.assertEqual(line._get_tax_creditability_map()["pis"], "cost")
        self.assertNotIn("pis_tax_is_creditable", line._fields)
