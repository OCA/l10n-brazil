# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.tests import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestNFeWithholding(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.configure_normal_company_taxes()
        cls.env.user.groups_id |= cls.env.ref("l10n_br_nfe.group_manager")

        # Withholding of PIS and COFINS on the sale, replacing the regular ones
        cls.pis_tax_definition_empresa_lc.write(
            {
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_pis_wh_0_65").id,
                "cst_id": False,
            }
        )
        cls.cofins_tax_definition_empresa_lc.write(
            {
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_cofins_wh_3").id,
                "cst_id": False,
            }
        )

        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Cash",
                "company_id": cls.company_data["company"].id,
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "fiscal_payment_mode": "18",
                "bank_account_link": "variable",
            }
        )
        cls.move_out_venda = cls.init_invoice(
            move_type="out_invoice",
            products=[cls.product_b],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
            post=False,
        )
        cls.move_out_venda.payment_mode_id = cls.payment_mode
        cls.move_out_venda.action_post()

    def test_vnf_is_not_reduced_by_withholding(self):
        """vNF is the value of the operation: withholdings go in retTrib."""
        move = self.move_out_venda
        self.assertTrue(move.amount_tax_withholding)
        self.assertTrue(move.nfe40_vRetPIS)
        self.assertTrue(move.nfe40_vRetCOFINS)
        # Products + IPI, with no withholding deducted
        self.assertEqual(move.nfe40_vNF, move.nfe40_vProd + move.nfe40_vIPI)
        self.assertEqual(
            move.nfe40_vNF, move.fiscal_amount_total + move.amount_tax_withholding
        )
        # The payments add up to vNF, or SEFAZ rejects the NF-e (865). The tags
        # are only computed for the OCA processor, which would also sign the
        # document on posting, so the compute is called directly.
        document = move.fiscal_document_id
        with mock.patch.object(
            type(document), "_need_compute_nfe_tags", return_value=True
        ):
            document._compute_nfe40_detpag()
        self.assertEqual(
            sum(document.nfe40_detPag.mapped("nfe40_vPag")), document.nfe40_vNF
        )

    def test_receivable_stays_net_of_withholding(self):
        """The title to receive is still net of the withholdings."""
        move = self.move_out_venda
        self.assertEqual(
            move.amount_financial_total,
            move.nfe40_vNF - move.amount_tax_withholding,
        )
