import logging

from odoo.tests.common import TransactionCase
from odoo.tools import float_compare

from odoo.addons.l10n_br_fiscal.constants.fiscal import SITUACAO_EDOC_A_ENVIAR

_logger = logging.getLogger(__name__)


class TestXMLValidation(TransactionCase):
    def test_xml_nfe_validation(self):
        """In this test case, the CEP is deleted from the partner's record on purpose,
        when confirming the NF-e an XML validation error must be presented."""
        document_model = self.env["l10n_br_fiscal.document"]
        document_line_model = self.env["l10n_br_fiscal.document.line"]
        akretion_partner = self.env.ref("l10n_br_base.res_partner_address_ak3")
        wrong_cep = "XoQC@33278"
        akretion_partner.write({"zip": wrong_cep})
        company_id = self.env.ref("l10n_br_base.empresa_lucro_presumido")
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
        line._onchange_fiscal_operation_line_id()
        document.action_document_confirm()
        document.action_document_send()
        _logger.info(
            "(Test Result) XML Validation Message: %s" % (document.xml_error_message)
        )
        self.assertTrue("CEP" in document.xml_error_message)
        self.assertEqual(document.state_edoc, SITUACAO_EDOC_A_ENVIAR)

    def test_xml_nfe_taxes(self):
        """This method tests multiple tax fields for NFe lines and NFe totals.
        warning: failures in this method could indicate errors in fiscal or account
        """
        document_model = self.env["l10n_br_fiscal.document"]
        document_line_model = self.env["l10n_br_fiscal.document.line"]
        akretion_partner = self.env.ref("l10n_br_base.res_partner_cliente7_rs")
        company_id = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        self.env.user.company_ids += company_id
        self.env.user.company_id = company_id
        document = document_model.create(
            {
                "partner_id": akretion_partner.id,
                "ind_final": "0",
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
            }
        )
        document._onchange_fiscal_operation_id()
        document._onchange_document_type_id()
        document._onchange_document_serie_id()

        # Line 1
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
        line._onchange_fiscal_operation_line_id()

        # Force taxes
        line.update(
            {
                "price_unit": 116.41,
                "fiscal_price": 116.41,
                "quantity": 22,
                "fiscal_quantity": 22,
                "icms_tax_id": self.env.ref("l10n_br_fiscal.tax_icms_12_st").id,
                "icmsst_tax_id": self.env.ref("l10n_br_fiscal.tax_icmsst_p30_50").id,
                "icmsfcpst_tax_id": self.env.ref("l10n_br_fiscal.tax_icmsfcp_st_2").id,
                "ipi_tax_id": self.env.ref("l10n_br_fiscal.tax_ipi_30").id,
                "pis_tax_id": self.env.ref("l10n_br_fiscal.tax_pis_1_65").id,
                "cofins_tax_id": self.env.ref("l10n_br_fiscal.tax_cofins_7_6").id,
            }
        )
        line._onchange_fiscal_taxes()

        # Line 2 - using two lines to test the XML totals
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
        line2._onchange_fiscal_operation_line_id()

        # Force taxes
        line2.update(
            {
                "price_unit": 116.41,
                "fiscal_price": 116.41,
                "quantity": 22,
                "fiscal_quantity": 22,
                "icms_tax_id": self.env.ref("l10n_br_fiscal.tax_icms_12_st").id,
                "icmsst_tax_id": self.env.ref("l10n_br_fiscal.tax_icmsst_p30_50").id,
                "icmsfcpst_tax_id": self.env.ref("l10n_br_fiscal.tax_icmsfcp_st_2").id,
                "ipi_tax_id": self.env.ref("l10n_br_fiscal.tax_ipi_30").id,
                "pis_tax_id": self.env.ref("l10n_br_fiscal.tax_pis_1_65").id,
                "cofins_tax_id": self.env.ref("l10n_br_fiscal.tax_cofins_7_6").id,
            }
        )
        line2._onchange_fiscal_taxes()

        document.action_document_confirm()
        document.action_document_send()
        # This section probably indicates an error in eiter
        #   l10n_br_account or l10n_br_fiscal
        self.assertEqual(line.icms_value, 307.32)
        self.assertEqual(line.icmsst_value, 1190.88)
        self.assertEqual(line.icmsfcpst_value, 99.88)
        self.assertEqual(float_compare(line.ipi_value, 768.31, precision_digits=2), 0)
        self.assertEqual(line.pis_value, 42.26)
        self.assertEqual(
            float_compare(line.cofins_value, 194.64, precision_digits=2), 0
        )

        # This section actually tests NFe fields and values
        self.assertEqual(document.nfe40_vICMS, 614.64)
        self.assertEqual(document.nfe40_vST, 2381.76)
        self.assertEqual(document.nfe40_vFCPST, 199.76)
        self.assertEqual(
            float_compare(document.nfe40_vIPI, 1536.62, precision_digits=2), 0
        )
        self.assertEqual(document.nfe40_vPIS, 84.52)
        self.assertEqual(
            float_compare(document.nfe40_vCOFINS, 389.28, precision_digits=2), 0
        )
