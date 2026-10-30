# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestPurchaseReturnTaxes(AccountMoveBRCommon):
    """The return of a purchase repeats the taxes of the purchase invoice."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()

        cls.env.ref("l10n_br_fiscal.fo_compras").deductible_taxes = True
        cls.purchase = cls.init_invoice(
            "in_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[
                cls.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
            ],
            document_serie="1",
            document_number="4242",
        )
        # Lucro Presumido buying from a supplier that charges no IPI and
        # no PIS/COFINS credit (CST 98)
        cls.purchase.invoice_line_ids.write(
            {
                "ipi_tax_id": cls.env.ref("l10n_br_fiscal.tax_ipi_nt").id,
                "pis_tax_id": cls.env.ref("l10n_br_fiscal.tax_pis_outros").id,
                "cofins_tax_id": cls.env.ref("l10n_br_fiscal.tax_cofins_outros").id,
            }
        )

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):
        if company_name == "company_1_data":
            company_name = "empresa 1 Lucro Presumido"
            cnpj = "62.128.834/0001-34"
        else:
            company_name = "empresa 2 Lucro Presumido"
            cnpj = "87.396.251/0001-15"
        chart_template = cls.env.ref("l10n_br_coa_generic.l10n_br_coa_generic_template")
        res = super().setup_company_data(
            company_name,
            chart_template,
            tax_framework="3",
            is_industry=True,
            industry_type="00",
            profit_calculation="presumed",
            ripi=True,
            piscofins_id=cls.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo").id,
            icms_regulation_id=cls.env.ref("l10n_br_fiscal.tax_icms_regulation").id,
            cnae_main_id=cls.env.ref("l10n_br_fiscal.cnae_3101200").id,
            document_type_id=cls.env.ref("l10n_br_fiscal.document_55").id,
            **kwargs,
        )
        res["company"].partner_id.state_id = cls.env.ref("base.state_br_sp").id
        res["company"].partner_id.cnpj_cpf = cnpj
        chart_template.load_fiscal_taxes()
        return res

    def _reverse(self, move):
        reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=move.ids)
            .create(
                {
                    "date": fields.Date.from_string("2019-02-01"),
                    "reason": "return to supplier",
                    "refund_method": "refund",
                    "force_fiscal_operation_id": self.env.ref(
                        "l10n_br_fiscal.fo_devolucao_compras"
                    ).id,
                }
            )
        )
        return self.env["account.move"].browse(reversal.reverse_moves()["res_id"])

    def test_purchase_return_repeats_origin_taxes(self):
        line = self.purchase.invoice_line_ids
        self.purchase.action_post()

        refund = self._reverse(self.purchase)
        refund_line = refund.invoice_line_ids

        self.assertEqual(refund.operation_name, "Devolução de Compras")
        for tax_field in ("ipi_tax_id", "pis_tax_id", "cofins_tax_id", "icms_tax_id"):
            self.assertEqual(
                refund_line[tax_field], line[tax_field], f"{tax_field} differs"
            )
        self.assertEqual(refund_line.ipi_value, 0.0)
        self.assertEqual(refund_line.pis_value, 0.0)
        self.assertEqual(refund_line.cofins_value, 0.0)
        self.assertEqual(refund_line.icms_value, line.icms_value)
        self.assertEqual(refund.amount_total, self.purchase.amount_total)
