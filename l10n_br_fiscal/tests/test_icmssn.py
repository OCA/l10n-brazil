# Copyright 2023 Engenere - Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestICMSSN(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company
        cls.partner = cls.env.ref("l10n_br_base.res_partner_address_ak3")
        cls.product = cls.env.ref("product.product_product_4c")
        cls.credit_comment = cls.env.ref(
            "l10n_br_fiscal.fiscal_comment_sn_permissao_credito"
        )
        # venda de industrialização própria e revenda no mesmo documento.
        cls.document = cls._create_document()
        cls.line_venda = cls._create_line(cls.document, "fo_venda_venda")
        cls.line_revenda = cls._create_line(cls.document, "fo_venda_revenda")
        # documentos com um único tipo de venda.
        cls.document_industry = cls._create_document()
        cls._create_line(cls.document_industry, "fo_venda_venda")
        cls.document_commerce = cls._create_document()
        cls._create_line(cls.document_commerce, "fo_venda_revenda")

    @classmethod
    def _create_document(cls):
        return cls.env["l10n_br_fiscal.document"].create(
            {
                "partner_id": cls.partner.id,
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
            }
        )

    @classmethod
    def _create_line(cls, document, operation_line_ref):
        line = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "company_id": document.company_id.id,
                "partner_id": document.partner_id.id,
                "fiscal_operation_type": document.fiscal_operation_type,
                "fiscal_operation_id": document.fiscal_operation_id.id,
                "product_id": cls.product.id,
            }
        )
        line.fiscal_operation_line_id = cls.env.ref(
            f"l10n_br_fiscal.{operation_line_ref}"
        )
        return line

    def test_icmssn_tax_rate(self):
        """Test to verify if the calculation of the icms credit
        for Simples Nacional companies is correct."""
        self.assertEqual(self.line_venda.icmssn_percent, 2.70)
        self.assertEqual(self.line_venda.icmssn_credit_value, 20.25)
        self.assertEqual(self.line_revenda.icmssn_percent, 2.66)
        self.assertEqual(self.line_revenda.icmssn_credit_value, 19.95)

    def test_icmssn_range(self):
        """Each line tells the range of the annex it was taxed by."""
        self.assertEqual(
            self.line_venda.icmssn_range_id,
            self.env.ref("l10n_br_fiscal.simplefied_tax_anexo2_range4"),
        )
        self.assertEqual(
            self.line_revenda.icmssn_range_id,
            self.env.ref("l10n_br_fiscal.simplefied_tax_anexo1_range4"),
        )
        # sem imposto do Simples Nacional na linha não há faixa
        self.line_venda.fiscal_tax_ids -= self.line_venda.icmssn_tax_id
        self.assertFalse(self.line_venda.icmssn_range_id)

    def test_icmssn_tax_rate_of_industrialization_for_third_party(self):
        """Industrialization ordered by a third party (CFOP 5124) is not a
        sale move but is taxed by the Annex II, whatever the company is."""
        self.company.is_industry = False
        self.line_revenda.cfop_id = self.env.ref("l10n_br_fiscal.cfop_5124")
        self.assertEqual(self.line_revenda.icmssn_percent, 2.70)
        self.assertEqual(self.line_revenda.icmssn_credit_value, 20.25)

    def test_icmssn_tax_rate_of_cfop_not_for_sale(self):
        """A CFOP telling neither a sale of own production nor a resale (5949)
        follows the main activity of the company."""
        self.line_venda.cfop_id = self.env.ref("l10n_br_fiscal.cfop_5949")
        self.assertEqual(self.line_venda.icmssn_percent, 2.70)
        self.company.is_industry = False
        self.line_revenda.cfop_id = self.env.ref("l10n_br_fiscal.cfop_5949")
        self.assertEqual(self.line_revenda.icmssn_percent, 2.66)

    def test_icmssn_tax_rate_without_cfop(self):
        """The account lines give None as CFOP when they have none."""
        result = self.env.ref("l10n_br_fiscal.tax_icms_sn_com_credito").compute_taxes(
            company=self.company,
            partner=self.partner,
            product=self.product,
            price_unit=100.0,
            quantity=1.0,
            uom_id=self.product.uom_id,
            fiscal_price=100.0,
            fiscal_quantity=1.0,
            uot_id=self.product.uom_id,
            ncm=self.product.ncm_id,
            operation_line=self.env.ref("l10n_br_fiscal.fo_venda_venda"),
            cfop=None,
        )
        self.assertEqual(result["taxes"]["icmssn"]["percent_amount"], 2.70)
        self.assertEqual(result["taxes"]["icmssn"]["tax_value"], 2.70)

    def _get_credit_comment(self, document):
        document.comment_ids = self.credit_comment
        document._document_comment()
        return document.fiscal_additional_data

    def test_icmssn_credit_comment(self):
        comment = self._get_credit_comment(self.document)
        self.assertTrue(
            comment.endswith(
                "Permite o aproveitamento do crédito de ICMS, no valor de "
                "R$\N{NO-BREAK SPACE}40,20, correspondente à alíquota de 2,70% para "
                "industrialização e de 2,66% para revenda, nos termos do artigo 23 "
                "da LC 123/2006."
            ),
            comment,
        )
        self.assertTrue(comment.startswith("SIMPLES NACIONAL - "), comment)

    def test_icmssn_credit_comment_single_rate(self):
        comment = self._get_credit_comment(self.document_industry)
        self.assertTrue(
            comment.endswith(
                "no valor de R$\N{NO-BREAK SPACE}20,25, correspondente à alíquota "
                "de 2,70%, nos termos do artigo 23 da LC 123/2006."
            ),
            comment,
        )
        comment = self._get_credit_comment(self.document_commerce)
        self.assertTrue(
            comment.endswith(
                "no valor de R$\N{NO-BREAK SPACE}19,95, correspondente à alíquota "
                "de 2,66%, nos termos do artigo 23 da LC 123/2006."
            ),
            comment,
        )

    def test_icmssn_credit_comment_states_the_rate_of_the_lines(self):
        """The comment must tell the rate the lines were computed with, even
        when the company falls into another range afterwards."""
        self.company.annual_revenue = 100000.0
        comment = self._get_credit_comment(self.document)
        self.assertIn(
            "correspondente à alíquota de 2,70% para industrialização e de 2,66% "
            "para revenda",
            comment,
        )

    def test_icmssn_tax_rate_without_effective_tax_lines(self):
        """The effective tax lines of the company are only its display: a
        company missing them must grant the same credit."""
        self.company.sn_effective_tax_ids.unlink()
        line = self._create_line(self.document, "fo_venda_venda")
        self.assertEqual(line.icmssn_percent, 2.70)
        self.assertEqual(line.icmssn_credit_value, 20.25)
