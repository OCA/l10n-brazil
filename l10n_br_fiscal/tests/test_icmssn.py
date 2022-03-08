# Copyright 2023 Engenere - Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestNFE(TransactionCase):
    def test_icmssn_tax_rate(self):
        """Test to verify if the calculation of the icms credit
        for Simples Nacional companies is correct."""
        document_model = self.env["l10n_br_fiscal.document"]
        document_line_model = self.env["l10n_br_fiscal.document.line"]
        akretion_partner = self.env.ref("l10n_br_base.res_partner_address_ak3")
        company_id = self.env.ref("l10n_br_base.empresa_simples_nacional")
        self.env.user.company_ids += company_id
        self.env.user.company_id = company_id
        document = document_model.create(
            {
                "partner_id": akretion_partner.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
            }
        )
        document._onchange_fiscal_operation_id()
        document._onchange_document_type_id()
        document._onchange_document_serie_id()
        # venda de industrialização própria.
        line = document_line_model.create(
            {
                "document_id": document.id,
                "company_id": document.company_id.id,
                "partner_id": document.partner_id.id,
                "fiscal_operation_type": document.fiscal_operation_type,
                "fiscal_operation_id": document.fiscal_operation_id.id,
                "product_id": self.env.ref("product.product_product_4c").id,
            }
        )
        line._onchange_product_id_fiscal()
        line.fiscal_operation_line_id = self.env.ref("l10n_br_fiscal.fo_venda_venda")
        line._onchange_fiscal_operation_line_id()
        # Revenda
        line2 = document_line_model.create(
            {
                "document_id": document.id,
                "company_id": document.company_id.id,
                "partner_id": document.partner_id.id,
                "fiscal_operation_type": document.fiscal_operation_type,
                "fiscal_operation_id": document.fiscal_operation_id.id,
                "product_id": self.env.ref("product.product_product_4c").id,
            }
        )
        line2._onchange_product_id_fiscal()
        line2.fiscal_operation_line_id = self.env.ref("l10n_br_fiscal.fo_venda_revenda")
        line2._onchange_fiscal_operation_line_id()
        document.comment_ids = [
            (4, self.env.ref("l10n_br_fiscal.fiscal_comment_sn_permissao_credito").id)
        ]
        document._compute_amount()
        document.action_document_confirm()
        icmss_credit_info = (
            "Permite o aproveitamento do crédito de ICMS, no valor de "
            "R$\N{NO-BREAK SPACE}40,20, correspondente à alíquota de 2,70% para "
            "industrialização e de 2,66% para revenda"
        )
        self.assertIn(icmss_credit_info, document.fiscal_additional_data)
