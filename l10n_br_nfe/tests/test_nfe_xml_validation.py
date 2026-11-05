import logging

from odoo.exceptions import UserError
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
        document_line_model.create(
            {
                "document_id": document.id,
                "company_id": document.company_id.id,
                "partner_id": document.partner_id.id,
                "fiscal_operation_type": document.fiscal_operation_type,
                "fiscal_operation_id": document.fiscal_operation_id.id,
                "product_id": self.env.ref("product.product_product_4c").id,
            }
        )
        document.action_document_confirm()
        # The schema errors are recorded by the confirmation, and the send is
        # then refused by _before_document_send() so the document stays in
        # 'a_enviar', where it can be set back to draft and fixed.
        with self.assertRaises(UserError):
            document.action_document_send()
        _logger.info(
            f"(Test Result) XML Validation Message: {document.xml_error_message}"
        )
        self.assertTrue("CEP" in document.xml_error_message)
        self.assertEqual(document.state_edoc, SITUACAO_EDOC_A_ENVIAR)

    def test_xml_nfe_string_fields_cut_to_the_xsd_max_length(self):
        """The NF-e schema limits natOp and xNome to 60 characters (TString).

        The cut is generic: spec_driven_model reads the maxLength of the
        schema field from the binding metadata, so l10n_br_nfe hard codes no
        cut at all and the Odoo records keep their full value.
        """
        company = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        self.env.user.company_ids += company
        self.env.user.company_id = company
        partner = self.env.ref("l10n_br_base.res_partner_cliente7_rs")
        fiscal_operation = self.env.ref("l10n_br_fiscal.fo_venda")
        nat_op = "Retorno de mercadoria ou bem remetido para conserto ou reparo"
        legal_name = (
            "Comercio Importacao e Exportacao de Produtos Industriais "
            "e Agricolas Ltda"
        )
        fiscal_operation.name = nat_op
        partner.legal_name = legal_name
        company.partner_id.write({"legal_name": legal_name, "name": legal_name})

        document = self.env["l10n_br_fiscal.document"].create(
            {
                "partner_id": partner.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "fiscal_operation_id": fiscal_operation.id,
            }
        )

        # natOp is 61 characters long in the fiscal operation:
        self.assertEqual(document.nfe40_natOp, nat_op)
        ide = document._build_binding(
            spec_schema="nfe", spec_version="40", class_name="nfe.40.ide"
        )
        self.assertEqual(ide.natOp, nat_op[:60])
        self.assertEqual(len(ide.natOp), 60)

        # xNome is 73 characters long in the partner legal name:
        for class_name in ("nfe.40.dest", "nfe.40.tlocal", "nfe.40.transporta"):
            binding = partner._build_binding(
                spec_schema="nfe", spec_version="40", class_name=class_name
            )
            self.assertEqual(binding.xNome, legal_name[:60], class_name)

        emit = company._build_binding(
            spec_schema="nfe", spec_version="40", class_name="nfe.40.emit"
        )
        self.assertEqual(emit.xNome, legal_name[:60])
        self.assertEqual(emit.xFant, legal_name[:60])

        # xProd: the schema allows 120 characters, l10n_br_nfe does not cut it
        # anymore, only the line breaks are replaced:
        product = self.env.ref("product.product_product_4c")
        product_name = "Produto " + "x" * 130
        product.name = product_name
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "company_id": document.company_id.id,
                "partner_id": document.partner_id.id,
                "fiscal_operation_type": document.fiscal_operation_type,
                "fiscal_operation_id": document.fiscal_operation_id.id,
                "product_id": product.id,
            }
        )
        prod = line._build_binding(
            spec_schema="nfe", spec_version="40", class_name="nfe.40.prod"
        )
        self.assertEqual(prod.xProd, product_name[:120])

        # the Odoo records keep the full value:
        self.assertEqual(partner.legal_name, legal_name)
        self.assertEqual(company.partner_id.legal_name, legal_name)

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
        # Force taxes
        line.write(
            {
                "price_unit": 116.41,
                "fiscal_price": 116.41,
                "quantity": 22,
                "fiscal_quantity": 22,
            }
        )
        self.assertEqual(len(line.fiscal_tax_ids), 6)
        line.write(
            {
                "icms_tax_id": self.env.ref("l10n_br_fiscal.tax_icms_12_st").id,
                "icmsst_tax_id": self.env.ref("l10n_br_fiscal.tax_icmsst_p30_50").id,
                "icmsfcpst_tax_id": self.env.ref("l10n_br_fiscal.tax_icmsfcp_st_2").id,
                "ipi_tax_id": self.env.ref("l10n_br_fiscal.tax_ipi_30").id,
                "pis_tax_id": self.env.ref("l10n_br_fiscal.tax_pis_1_65").id,
                "cofins_tax_id": self.env.ref("l10n_br_fiscal.tax_cofins_7_6").id,
            }
        )
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
        # Force taxes
        line2.write(
            {
                "price_unit": 116.41,
                "fiscal_price": 116.41,
                "quantity": 22,
                "fiscal_quantity": 22,
            }
        )
        # update separado para não ser sobreescrito pelo compute.
        line2.write(
            {
                "icms_tax_id": self.env.ref("l10n_br_fiscal.tax_icms_12_st").id,
                "icmsst_tax_id": self.env.ref("l10n_br_fiscal.tax_icmsst_p30_50").id,
                "icmsfcpst_tax_id": self.env.ref("l10n_br_fiscal.tax_icmsfcp_st_2").id,
                "ipi_tax_id": self.env.ref("l10n_br_fiscal.tax_ipi_30").id,
                "pis_tax_id": self.env.ref("l10n_br_fiscal.tax_pis_1_65").id,
                "cofins_tax_id": self.env.ref("l10n_br_fiscal.tax_cofins_7_6").id,
            }
        )

        # This test only checks tax values, which are computed by the
        # confirmation. It does not transmit: the document carries no payment
        # details, so its XML does not validate against the schema and
        # _before_document_send() refuses the transmission.
        document.action_document_confirm()
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
