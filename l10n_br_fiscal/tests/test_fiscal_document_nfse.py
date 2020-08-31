# @ 2020 KMEE - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestFiscalDocumentNFSe(TransactionCase):

    def setUp(self):
        super(TestFiscalDocumentNFSe, self).setUp()

        self.nfse_same_state = self.env.ref(
            'l10n_br_fiscal.demo_nfse_same_state'
        )

    def test_nfse_same_state(self):
        """ Test NFSe same state. """

        self.nfse_same_state._onchange_document_serie_id()
        self.nfse_same_state._onchange_fiscal_operation_id()

        for line in self.nfse_same_state.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

            self.assertEquals(
                line.fiscal_operation_line_id.name, 'Venda de Serviço',
                "Error to mappping Venda de Serviço"
                " for Venda de Serviço de Contribuinte Dentro do Estado.")

            # Service Type
            self.assertEquals(
                line.service_type_id.code, '1.05',
                "Error to mapping Service Type Code 1.05"
                " for Venda de Serviço de Contribuinte Dentro do Estado.")

            # IPI
            self.assertEquals(
                line.ipi_tax_id.name, 'IPI Simples Nacional',
                "Error to mapping IPI Simples Nacional"
                " for Venda de Serviço de Contribuinte Dentro do Estado.")
            self.assertEquals(
                line.ipi_cst_id.code, '99',
                "Error to mapping CST 99 from IPI Simples Nacional"
                " to Venda de Serviço de Contribuinte Dentro do Estado.")

            # ICMS CST
            self.assertEquals(
                line.icms_cst_id.name, 'Tributada com permissão de crédito',
                "Error to mapping ICMS CST Tributada com permissão de crédito"
                " for Venda de Serviço de Contribuinte Dentro do Estado.")
            self.assertEquals(
                line.icms_cst_id.code, '101',
                "Error to mapping ICMS CST 101 for "
                "Tributada com permissão de crédito"
                " to Venda de Serviço de Contribuinte Dentro do Estado.")

        self.nfse_same_state.action_document_confirm()
