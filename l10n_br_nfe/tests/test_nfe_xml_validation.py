import logging

from odoo.tests.common import TransactionCase

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
                "product_id": self.env.ref("product.product_product_4d").id,
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
