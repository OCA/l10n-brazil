# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestFiscalDocumentGeneric(TransactionCase):

    def setUp(self):
        super(TestFiscalDocumentGeneric, self).setUp()
        # Contribuinte
        self.nfe_same_state = self.env.ref(
            'l10n_br_fiscal.demo_nfe_same_state'
        )
        self.nfe_other_state = self.env.ref(
            'l10n_br_fiscal.demo_nfe_other_state'
        )
        self.nfe_not_taxpayer = self.env.ref(
            'l10n_br_fiscal.demo_nfe_nao_contribuinte'
        )
        self.nfe_export = self.env.ref(
            'l10n_br_fiscal.demo_nfe_export'
        )

        # Simples Nacional
        self.nfe_sn_same_state = self.env.ref(
            'l10n_br_fiscal.demo_nfe_sn_same_state'
        )
        self.nfe_sn_other_state = self.env.ref(
            'l10n_br_fiscal.demo_nfe_sn_other_state'
        )
        self.nfe_sn_not_taxpayer = self.env.ref(
            'l10n_br_fiscal.demo_nfe_sn_nao_contribuinte'
        )
        self.nfe_sn_export = self.env.ref(
            'l10n_br_fiscal.demo_nfe_sn_export'
        )

    def test_nfe_same_state(self):
        """ Test NFe same state. """

        self.nfe_same_state._onchange_document_serie_id()
        self.nfe_same_state._onchange_partner_id()
        self.nfe_same_state._onchange_operation_id()

        for line in self.nfe_same_state.line_ids:
            line._onchange_product_id()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_operation_id()
            line._onchange_operation_line_id()
            line._onchange_fiscal_taxes()

            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.cfop_id.code, '5102',
                    "Error to mappping CFOP 5102"
                    " for Revenda de Contribuinte Dentro do Estado.")
            else:
                self.assertEquals(
                    line.cfop_id.code, '5101',
                    "Error to mapping CFOP 5101"
                    " for Venda de Contribuinte Dentro do Estado.")

            # ICMS
            self.assertEquals(
                line.icms_tax_id.name, 'ICMS 18%',
                "Error to mapping ICMS 18%"
                " for Venda de Contribuinte Dentro do Estado.")
            self.assertEquals(
                line.icms_cst_id.code, '00',
                "Error to mapping CST 00 from ICMS 18%"
                " for Venda de Contribuinte Dentro do Estado.")

            # ICMS FCP
            self.assertEquals(
                line.icmsfcp_tax_id.name, 'FCP 2%',
                "Error to mapping ICMS FCP 2%"
                " for Venda de Contribuinte Dentro do Estado.")

            # IPI
            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.ipi_tax_id.name, 'IPI NT',
                    "Error to mapping IPI NT"
                    " for Revenda de Contribuinte Dentro do Estado.")
                self.assertEquals(
                    line.ipi_cst_id.code, '53',
                    "Error to mapping CST 53 from IPI NT"
                    " to Revenda de Contribuinte Dentro do Estado.")
            else:
                self.assertEquals(
                    line.ipi_tax_id.name, 'IPI 5%',
                    "Error to mapping IPI 5%"
                    " for Venda de Contribuinte Dentro do Estado.")
                self.assertEquals(
                    line.ipi_cst_id.code, '50',
                    "Error to mapping CST 50 from IPI 5%"
                    " to Venda de Contribuinte Dentro do Estado.")

            # PIS
            self.assertEquals(
                line.pis_tax_id.name, 'PIS 0,65%',
                "Error to mapping PIS 0,65%"
                " for Venda de Contribuinte Dentro do Estado.")
            self.assertEquals(
                line.pis_cst_id.code, '01',
                "Error to mapping CST 01 - Operação Tributável com Alíquota"
                " Básica from PIS 0,65% to Venda de Contribuinte Dentro do Estado.")

            # PIS
            self.assertEquals(
                line.cofins_tax_id.name, 'COFINS 3%',
                "Error to mapping COFINS 3%"
                " for Venda de Contribuinte Dentro do Estado.")
            self.assertEquals(
                line.cofins_cst_id.code, '01',
                "Error to mapping CST 01 - Operação Tributável com Alíquota Básica"
                " Básica to COFINS 3% de Venda de Contribuinte Dentro do Estado.")

        self.nfe_same_state.action_document_confirm()

    def test_nfe_other_state(self):
        """ Test NFe other state. """

        self.nfe_other_state._onchange_document_serie_id()
        self.nfe_other_state._onchange_partner_id()
        self.nfe_other_state._onchange_operation_id()

        for line in self.nfe_other_state.line_ids:
            line._onchange_product_id()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_operation_id()
            line._onchange_operation_line_id()
            line._onchange_fiscal_taxes()

            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.cfop_id.code, '6102',
                    "Error to mapping CFOP 6102"
                    " for Revenda de Contribuinte p/ Fora do Estado.")
            else:
                self.assertEquals(
                    line.cfop_id.code, '6101',
                    "Error to mapping CFOP 6101"
                    " for Venda de Contribuinte p/ Fora do Estado.")

            # ICMS
            self.assertEquals(
                line.icms_tax_id.name, 'ICMS 7%',
                "Error to mapping ICMS 7%"
                " for Venda de Contribuinte p/ Fora do Estado.")
            self.assertEquals(
                line.icms_cst_id.code, '00',
                "Error to mapping CST 00 from ICMS 7%"
                " for Venda de Contribuinte p/ Fora do Estado.")

            # ICMS FCP
            # self.assertEquals(
            #    line.icmsfcp_tax_id.name, 'FCP 2%',
            #    "Erro ao mapear ICMS FCP 2%"
            #    " para Venda de Contribuinte p/ Fora do Estado.")

            # IPI
            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.ipi_tax_id.name, 'IPI NT',
                    "Error to mapping IPI NT"
                    " for Revenda de Contribuinte Dentro do Estado.")
                self.assertEquals(
                    line.ipi_cst_id.code, '53',
                    "Error to mapping CST 53 from IPI NT"
                    " to Revenda de Contribuinte Dentro do Estado.")
            else:
                self.assertEquals(
                    line.ipi_tax_id.name, 'IPI 5%',
                    "Error to mapping IPI 5%"
                    " for Venda de Contribuinte Dentro do Estado.")
                self.assertEquals(
                    line.ipi_cst_id.code, '50',
                    "Error to mapping CST 50 from IPI 5%"
                    " to Venda de Contribuinte Dentro do Estado.")

            # PIS
            self.assertEquals(
                line.pis_tax_id.name, 'PIS 0,65%',
                "Error to mapping PIS 0,65%"
                " for Venda de Contribuinte p/ Fora do Estado.")
            self.assertEquals(
                line.pis_cst_id.code, '01',
                "Error to mapping CST 01 - Operação Tributável com Alíquota"
                " Básica from PIS 0,65% for"
                " Venda de Contribuinte p/ Fora do Estado.")

            # PIS
            self.assertEquals(
                line.cofins_tax_id.name, 'COFINS 3%',
                "Error to mapping COFINS 3%"
                " for Venda de Contribuinte p/ Fora do Estado.")
            self.assertEquals(
                line.cofins_cst_id.code, '01',
                "Error to mapping CST 01 -"
                " Operação Tributável com Alíquota Básica"
                "from COFINS 3% for Venda de Contribuinte p/ Fora do Estado.")

    def test_nfe_not_taxpayer(self):
        """ Test NFe not taxpayer. """

        self.nfe_not_taxpayer._onchange_document_serie_id()
        self.nfe_not_taxpayer._onchange_partner_id()
        self.nfe_not_taxpayer._onchange_operation_id()

        for line in self.nfe_not_taxpayer.line_ids:
            line._onchange_product_id()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_operation_id()
            line._onchange_operation_line_id()
            line._onchange_fiscal_taxes()

            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.cfop_id.code, '6102',
                    "Error to mapping CFOP 6102"
                    " for Revenda de Contribuinte p/ Não Contribuinte.")
            else:
                self.assertEquals(
                    line.cfop_id.code, '6101',
                    "Error to mapping CFOP 6101"
                    " for Venda de Contribuinte p/ Não Contribuinte.")

            # ICMS
            self.assertEquals(
                line.icms_tax_id.name, 'ICMS 12%',
                "Error to mapping ICMS 12%"
                " for Venda de Contribuinte p/ Não Contribuinte.")
            self.assertEquals(
                line.icms_cst_id.code, '00',
                "Error to mapping CST 00 from ICMS 7%"
                " for Venda de Contribuinte p/ Não Contribuinte.")

            # ICMS FCP
            # self.assertEquals(
            #    line.icmsfcp_tax_id.name, 'FCP 2%',
            #    "Erro ao mapear ICMS FCP 2%"
            #    " para Venda de Contribuinte p/ Não Contribuinte.")

            # IPI
            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.ipi_tax_id.name, 'IPI NT',
                    "Error to mapping IPI NT"
                    " for Revenda de Contribuinte Dentro do Estado.")
                self.assertEquals(
                    line.ipi_cst_id.code, '53',
                    "Error to mapping CST 53 from IPI NT"
                    " to Revenda de Contribuinte Dentro do Estado.")
            else:
                self.assertEquals(
                    line.ipi_tax_id.name, 'IPI 5%',
                    "Error to mapping IPI 5%"
                    " for Venda de Contribuinte Dentro do Estado.")
                self.assertEquals(
                    line.ipi_cst_id.code, '50',
                    "Error to mapping CST 50 from IPI 5%"
                    " to Venda de Contribuinte Dentro do Estado.")

            # PIS
            self.assertEquals(
                line.pis_tax_id.name, 'PIS 0,65%',
                "Error to mapping PIS 0,65%"
                " for Venda de Contribuinte p/ Não Contribuinte.")
            self.assertEquals(
                line.pis_cst_id.code, '01',
                "Error to mapping CST 01 - Operação Tributável com Alíquota"
                " Básica from PIS 0,65% for"
                " Venda de Contribuinte p/ Não Contribuinte.")

            # PIS
            self.assertEquals(
                line.cofins_tax_id.name, 'COFINS 3%',
                "Error to mapping COFINS 3%"
                " for Venda de Contribuinte p/ Não Contribuinte.")
            self.assertEquals(
                line.cofins_cst_id.code, '01',
                "Error to mapping CST 01 -"
                " Operação Tributável com Alíquota Básica"
                "from COFINS 3% for Venda de Contribuinte p/ Não Contribuinte.")

    def test_nfe_export(self):
        """ Test NFe export. """

        self.nfe_export._onchange_document_serie_id()
        self.nfe_export._onchange_partner_id()
        self.nfe_export._onchange_operation_id()

        for line in self.nfe_export.line_ids:
            line._onchange_product_id()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_operation_id()
            line._onchange_operation_line_id()
            line._onchange_fiscal_taxes()

            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.cfop_id.code, '7102',
                    "Error to mapping CFOP 7102"
                    " for Revenda de Contribuinte p/ o Exterior.")
            else:
                self.assertEquals(
                    line.cfop_id.code, '7101',
                    "Error to mapping CFOP 7101"
                    " for Venda de Contribuinte p/ o Exterior.")

            # ICMS - TODO field missing
            # self.assertEquals(
            #    line.icms_tax_id.name, 'ICMS 7%',
            #    "Error to mapping ICMS 7%"
            #    " for Venda de Contribuinte p/ o Exterior.")
            # self.assertEquals(
            #    line.icms_cst_id.code, '00',
            #    "Error to mapping CST 00 from ICMS 7%"
            #    " for Venda de Contribuinte p/ o Exterior.")

            # ICMS FCP
            # self.assertEquals(
            #    line.icmsfcp_tax_id.name, 'FCP 2%',
            #    "Erro ao mapear ICMS FCP 2%"
            #    " para Venda de Contribuinte p/ o Exterior.")

            # IPI
            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.ipi_tax_id.name, 'IPI NT',
                    "Error to mapping IPI NT"
                    " for Revenda de Contribuinte Dentro do Estado.")
                self.assertEquals(
                    line.ipi_cst_id.code, '53',
                    "Error to mapping CST 53 from IPI NT"
                    " to Revenda de Contribuinte Dentro do Estado.")
            else:
                self.assertEquals(
                    line.ipi_tax_id.name, 'IPI 5%',
                    "Error to mapping IPI 5%"
                    " for Venda de Contribuinte Dentro do Estado.")
                self.assertEquals(
                    line.ipi_cst_id.code, '50',
                    "Error to mapping CST 50 from IPI 5%"
                    " to Venda de Contribuinte Dentro do Estado.")

            # PIS
            self.assertEquals(
                line.pis_tax_id.name, 'PIS 0,65%',
                "Error to mapping PIS 0,65%"
                " for Venda de Contribuinte p/ o Exterior.")
            self.assertEquals(
                line.pis_cst_id.code, '01',
                "Error to mapping CST 01 - Operação Tributável com Alíquota"
                " Básica from PIS 0,65% for"
                " Venda de Contribuinte p/ o Exterior.")

            # PIS
            self.assertEquals(
                line.cofins_tax_id.name, 'COFINS 3%',
                "Error to mapping COFINS 3%"
                " for Venda de Contribuinte p/ o Exterior.")
            self.assertEquals(
                line.cofins_cst_id.code, '01',
                "Error to mapping CST 01 -"
                " Operação Tributável com Alíquota Básica"
                "from COFINS 3% for Venda de Contribuinte p/ o Exterior.")

    def test_nfe_sn_same_state(self):
        """ Test NFe Simples Nacional same state. """

        self.nfe_sn_same_state._onchange_document_serie_id()
        self.nfe_sn_same_state._onchange_partner_id()
        self.nfe_sn_same_state._onchange_operation_id()

        for line in self.nfe_sn_same_state.line_ids:
            line._onchange_product_id()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_operation_id()
            line._onchange_operation_line_id()
            line._onchange_fiscal_taxes()

            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.cfop_id.code, '5102',
                    "Error to mappping CFOP 5102"
                    " for Revenda de Simples Nacional Dentro do Estado.")
            else:
                self.assertEquals(
                    line.cfop_id.code, '5101',
                    "Error to mapping CFOP 5101"
                    " for Venda de Simples Nacional Dentro do Estado.")

            # ICMS
            self.assertEquals(
                line.icmssn_tax_id.name, 'ICMS SN Com Permissão de Crédito',
                "Error to mapping ICMS SN Com Permissão de Crédito"
                " for Venda de Simples Nacional Dentro do Estado.")
            self.assertEquals(
                line.icms_cst_id.code, '101',
                "Error to mapping CST 101 do ICMS SN Com Permissão de Crédito"
                " for Venda de Simples Nacional Dentro do Estado.")

            # ICMS FCP - TODO mapping failed
            # self.assertEquals(
            #    line.icmsfcp_tax_id.name, 'FCP 2%',
            #    "Erro ao mapear ICMS FCP 2%"
            #    " para Venda de Simples Nacional Dentro do Estado.")

            # IPI
            self.assertEquals(
                line.ipi_tax_id.name, 'IPI Simples Nacional',
                "Error to mapping IPI Simples Nacional"
                " for Venda de Simples Nacional Fora do Estado.")
            self.assertEquals(
                line.ipi_cst_id.code, '99',
                "Error to mapping CST 99 from IPI Simples Nacional"
                " for Venda de Simples Nacional Fora do Estado.")

            # PIS
            self.assertEquals(
                line.pis_tax_id.name, 'PIS Simples Nacional',
                "Error to mapping PIS Simples Nacional"
                " for Venda de Simples Nacional Dentro do Estado.")
            self.assertEquals(
                line.pis_cst_id.code, '49',
                "Error to mapping CST 49 Outras Operações de Saída"
                " from PIS Simples Nacional from Venda de"
                " Simples Nacional Dentro do Estado.")

            # COFINS
            self.assertEquals(
                line.cofins_tax_id.name, 'COFINS Simples Nacional',
                "Error to mapping COFINS Simples Nacional"
                " for Venda de Simples Nacional Dentro do Estado.")
            self.assertEquals(
                line.cofins_cst_id.code, '49',
                "Error to mapping CST 49 Outras Operações de Saída"
                " from COFINS Simples Nacional for Venda de"
                " Simples Nacional Fora do Estado.")

    def test_nfe_sn_other_state(self):
        """ Test NFe SN other state. """

        self.nfe_sn_other_state._onchange_document_serie_id()
        self.nfe_sn_other_state._onchange_partner_id()
        self.nfe_sn_other_state._onchange_operation_id()

        for line in self.nfe_sn_other_state.line_ids:
            line._onchange_product_id()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_operation_id()
            line._onchange_operation_line_id()
            line._onchange_fiscal_taxes()

            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.cfop_id.code, '6102',
                    "Error to mappping CFOP 6102"
                    " for Revenda de Simples Nacional Fora do Estado.")
            else:
                self.assertEquals(
                    line.cfop_id.code, '6101',
                    "Error to mapping CFOP 6101"
                    " for Venda de Simples Nacional Fora do Estado.")

            # ICMS
            self.assertEquals(
                line.icmssn_tax_id.name, 'ICMS SN Com Permissão de Crédito',
                "Error to mapping ICMS SN Com Permissão de Crédito"
                " for Venda de Simples Nacional Dentro do Estado.")
            self.assertEquals(
                line.icms_cst_id.code, '101',
                "Erro ao mapear a CST 101 do ICMS SN Com Permissão de Crédito"
                " para Venda de Simples Nacional Dentro do Estado.")

            # ICMS FCP - TODO mapping failed
            # self.assertEquals(
            #    line.icmsfcp_tax_id.name, 'FCP 2%',
            #    "Erro ao mapear ICMS FCP 2%"
            #    " para Venda de Simples Nacional Fora do Estado.")

            # IPI
            self.assertEquals(
                line.ipi_tax_id.name, 'IPI Simples Nacional',
                "Error to mapping IPI Simples Nacional"
                " for Venda de Simples Nacional Fora do Estado.")
            self.assertEquals(
                line.ipi_cst_id.code, '99',
                "Error to mapping CST 99 from IPI Simples Nacional"
                " for Venda de Simples Nacional Fora do Estado.")

            # PIS
            self.assertEquals(
                line.pis_tax_id.name, 'PIS Simples Nacional',
                "Erro ao mapear PIS Simples Nacional"
                " para Venda de Simples Nacional Fora do Estado.")
            self.assertEquals(
                line.pis_cst_id.code, '49',
                "Erro ao mapear a CST 49 Outras Operações de Saída"
                " com Alíquota Básica do PIS Simples Nacional de Venda de"
                " Simples Nacional Dentro do Estado.")

            # COFINS
            self.assertEquals(
                line.cofins_tax_id.name, 'COFINS Simples Nacional',
                "Error to mapping COFINS Simples Nacional"
                " for Venda de Simples Nacional Dentro do Estado.")
            self.assertEquals(
                line.cofins_cst_id.code, '49',
                "Error to mapping CST 49 Outras Operações de Saída"
                " from COFINS Simples Nacional for Venda de"
                " Simples Nacional Fora do Estado.")

    def test_nfe_sn_not_taxpayer(self):
        """ Test NFe SN not taxpayer. """

        self.nfe_sn_not_taxpayer._onchange_document_serie_id()
        self.nfe_sn_not_taxpayer._onchange_partner_id()
        self.nfe_sn_not_taxpayer._onchange_operation_id()

        for line in self.nfe_sn_not_taxpayer.line_ids:
            line._onchange_product_id()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_operation_id()
            line._onchange_operation_line_id()
            line._onchange_fiscal_taxes()

            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.cfop_id.code, '5102',
                    "Error to mappping CFOP 5102"
                    " for Revenda de Simples Nacional Fora do Estado.")
            else:
                self.assertEquals(
                    line.cfop_id.code, '5101',
                    "Error to mapping CFOP 5101"
                    " for Venda de Simples Nacional Fora do Estado.")

            # ICMS
            self.assertEquals(
                line.icms_tax_id.name, 'ICMS 18%',
                "Error to mapping ICMS 18%"
                " for Venda de Simples Nacional Fora do Estado.")
            self.assertEquals(
                line.icms_cst_id.code, '00',
                "Erro ao mapear a CST 00 do ICMS 18%"
                " para Venda de Simples Nacional Fora do Estado.")

            # ICMS FCP
            self.assertEquals(
                line.icmsfcp_tax_id.name, 'FCP 2%',
                "Erro ao mapear ICMS FCP 2%"
                " para Venda de Simples Nacional Fora do Estado.")

            # IPI
            self.assertEquals(
                line.ipi_tax_id.name, 'IPI 5%',
                "Erro ao mapear IPI 5%"
                " para Venda de Simples Nacional Fora do Estado.")
            self.assertEquals(
                line.ipi_cst_id.code, '50',
                "Erro ao mapear a CST 50 do IPI 5%"
                " de Venda de Simples Nacional Fora do Estado.")

            # PIS
            self.assertEquals(
                line.pis_tax_id.name, 'PIS 0,65%',
                "Erro ao mapear PIS 0,65%"
                " para Venda de Simples Nacional Fora do Estado.")
            self.assertEquals(
                line.pis_cst_id.code, '01',
                "Erro ao mapear a CST 01 - Operação Tributável"
                " com Alíquota Básica do PIS 0,65% de Venda de"
                " Simples Nacional Fora do Estado.")

            # PIS
            self.assertEquals(
                line.cofins_tax_id.name, 'COFINS 3%',
                "Erro ao mapear COFINS 3%"
                " para Venda de Simples Nacional Dentro do Estado.")
            self.assertEquals(
                line.cofins_cst_id.code, '01',
                "Erro ao mapear a CST 01 - Operação Tributável"
                " com Alíquota Básica do COFINS 3% de Venda de"
                " Simples Nacional Fora do Estado.")

    def test_nfe_sn_export(self):
        """ Test NFe SN export. """

        self.nfe_sn_export._onchange_document_serie_id()
        self.nfe_sn_export._onchange_partner_id()
        self.nfe_sn_export._onchange_operation_id()

        for line in self.nfe_sn_export.line_ids:
            line._onchange_product_id()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_operation_id()
            line._onchange_operation_line_id()
            line._onchange_fiscal_taxes()

            if line.operation_line_id.name == 'Revenda':
                self.assertEquals(
                    line.cfop_id.code, '7102',
                    "Error to mapping CFOP 7102"
                    " for Revenda de Contribuinte p/ o Exterior.")
            else:
                self.assertEquals(
                    line.cfop_id.code, '7101',
                    "Error to mapping CFOP 7101"
                    " for Venda de Contribuinte p/ o Exterior.")

            # ICMS
            self.assertEquals(
                line.icmssn_tax_id.name, 'ICMS SN Com Permissão de Crédito',
                "Error to mapping ICMS SN Com Permissão de Crédito"
                " for Venda de Simples Nacional Dentro do Estado.")
            self.assertEquals(
                line.icms_cst_id.code, '101',
                "Erro ao mapear a CST 101 do ICMS SN Com Permissão de Crédito"
                " para Venda de Simples Nacional Dentro do Estado.")

            # ICMS FCP
            # self.assertEquals(
            #    line.icmsfcp_tax_id.name, 'FCP 2%',
            #    "Erro ao mapear ICMS FCP 2%"
            #    " para Venda de Contribuinte p/ o Exterior.")

            # IPI
            self.assertEquals(
                line.ipi_tax_id.name, 'IPI Simples Nacional',
                "Error to mapping IPI Simples Nacional"
                " for Venda de Simples Nacional Fora do Estado.")
            self.assertEquals(
                line.ipi_cst_id.code, '99',
                "Error to mapping CST 99 from IPI Simples Nacional"
                " for Venda de Simples Nacional Fora do Estado.")

            # PIS
            self.assertEquals(
                line.pis_tax_id.name, 'PIS Simples Nacional',
                "Erro ao mapear PIS Simples Nacional"
                " para Venda de Simples Nacional Fora do Estado.")
            self.assertEquals(
                line.pis_cst_id.code, '49',
                "Erro ao mapear a CST 49 Outras Operações de Saída"
                " com Alíquota Básica do PIS Simples Nacional de Venda de"
                " Simples Nacional Dentro do Estado.")

            # COFINS
            self.assertEquals(
                line.cofins_tax_id.name, 'COFINS Simples Nacional',
                "Error to mapping COFINS Simples Nacional"
                " for Venda de Simples Nacional Dentro do Estado.")
            self.assertEquals(
                line.cofins_cst_id.code, '49',
                "Error to mapping CST 49 Outras Operações de Saída"
                " from COFINS Simples Nacional for Venda de"
                " Simples Nacional Fora do Estado.")

    def test_nfe_return(self):
        """ Test Fiscal Document Return """

        action = self.nfe_same_state.action_create_return()
        return_id = self.nfe_same_state.browse(
            [i[2] for i in action['domain'] if i[0] == 'id'])

        self.assertEquals(
            return_id.operation_id.id,
            self.nfe_same_state.operation_id.return_operation_id.id,
            "Error on creation return"
        )

    def test_event_to_fiscal_close(self):
        test_xml = '<?xml version="1.0" encoding="utf-8"?><nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><NFe xmlns="http://www.portalfiscal.inf.br/nfe"><infNFe versao="4.00" Id="NFe26180812984794000154550010000016871192213339"><ide><cUF>26</cUF><cNF>19221333</cNF><natOp>Venda</natOp><mod>55</mod><serie>1</serie><nNF>1687</nNF><dhEmi>2018-08-16T16:28:18-03:00</dhEmi><dhSaiEnt>2018-08-16T16:28:18-03:00</dhSaiEnt><tpNF>1</tpNF><idDest>2</idDest><cMunFG>2611606</cMunFG><tpImp>1</tpImp><tpEmis>1</tpEmis><cDV>9</cDV><tpAmb>1</tpAmb><finNFe>1</finNFe><indFinal>0</indFinal><indPres>0</indPres><procEmi>0</procEmi><verProc>Odoo Brasil v8</verProc></ide><emit><CNPJ>75335849000115</CNPJ><xNome>Teste Produtos Médicos Ltda - ME</xNome><xFant>Teste Produtos Médicos Ltda - ME</xFant><enderEmit><xLgr>Avenida Manoel</xLgr><nro>1</nro><xBairro>Boa Vista</xBairro><cMun>2611606</cMun><xMun>Recife</xMun><UF>PE</UF><CEP>50070123</CEP><cPais>1058</cPais><xPais>Brasil</xPais><fone>0123456789</fone></enderEmit><IE>306412330</IE><CRT>3</CRT></emit><dest><CNPJ>37148260000119</CNPJ><xNome>MEDICOS, HOSP, IMP. E EXP. LTDA</xNome><enderDest><xLgr>Av. Doutor Pedro</xLgr><nro>1</nro><xCpl>Sala 4</xCpl><xBairro>Ponta da Praia</xBairro><cMun>3548500</cMun><xMun>Santos</xMun><UF>SP</UF><CEP>11025012</CEP><cPais>1058</cPais><xPais>Brasil</xPais><fone>99999999</fone></enderDest><indIEDest>1</indIEDest><IE>803879214167</IE></dest><det nItem="1"><prod><cProd>880945</cProd><cEAN>SEM GTIN</cEAN><xProd>ESPAÇADOR TEMPORARIO DE ACRILICO PARA QUADRIL COM GENTAMICINA</xProd><NCM>90211010</NCM><CFOP>6102</CFOP><uCom>UN</uCom><qCom>1.0000</qCom><vUnCom>2490.0000000</vUnCom><vProd>2490.00</vProd><cEANTrib>SEM GTIN</cEANTrib><uTrib>UN</uTrib><qTrib>1.0000</qTrib><vUnTrib>2490.0000000</vUnTrib><indTot>1</indTot></prod><imposto><vTotTrib>0.00</vTotTrib><ICMS><ICMS40><orig>1</orig><CST>40</CST></ICMS40></ICMS><IPI><cEnq>999</cEnq><IPINT><CST>51</CST></IPINT></IPI><PIS><PISNT><CST>07</CST></PISNT></PIS><COFINS><COFINSNT><CST>07</CST></COFINSNT></COFINS></imposto></det><det nItem="2"><prod><cProd>880930</cProd><cEAN>SEM GTIN</cEAN><xProd>ESPAÇADOR TEMPORARIO DE ACRILICO PARA QUADRIL COM GENTAMICINA</xProd><NCM>90211010</NCM><CFOP>6102</CFOP><uCom>UN</uCom><qCom>1.0000</qCom><vUnCom>2490.0000000</vUnCom><vProd>2490.00</vProd><cEANTrib>SEM GTIN</cEANTrib><uTrib>UN</uTrib><qTrib>1.0000</qTrib><vUnTrib>2490.0000000</vUnTrib><indTot>1</indTot></prod><imposto><vTotTrib>0.00</vTotTrib><ICMS><ICMS40><orig>1</orig><CST>40</CST></ICMS40></ICMS><IPI><cEnq>999</cEnq><IPINT><CST>51</CST></IPINT></IPI><PIS><PISNT><CST>07</CST></PISNT></PIS><COFINS><COFINSNT><CST>07</CST></COFINSNT></COFINS></imposto></det><det nItem="3"><prod><cProd>880200</cProd><cEAN>SEM GTIN</cEAN><xProd>CIMENTO ACRÍLICO G 40G - APLICAÇÃO MANUAL COM GENTAMICINA</xProd><NCM>30064020</NCM><CFOP>6102</CFOP><uCom>UN</uCom><qCom>4.0000</qCom><vUnCom>200.0000000</vUnCom><vProd>800.00</vProd><cEANTrib>SEM GTIN</cEANTrib><uTrib>UN</uTrib><qTrib>4.0000</qTrib><vUnTrib>200.0000000</vUnTrib><indTot>1</indTot></prod><imposto><vTotTrib>0.00</vTotTrib><ICMS><ICMS40><orig>1</orig><CST>40</CST></ICMS40></ICMS><IPI><cEnq>999</cEnq><IPINT><CST>51</CST></IPINT></IPI><PIS><PISNT><CST>06</CST></PISNT></PIS><COFINS><COFINSNT><CST>06</CST></COFINSNT></COFINS></imposto></det><total><ICMSTot><vBC>0.00</vBC><vICMS>0.00</vICMS><vICMSDeson>0.00</vICMSDeson><vFCP>0.00</vFCP><vBCST>0.00</vBCST><vST>0.00</vST><vFCPST>0.00</vFCPST><vFCPSTRet>0.00</vFCPSTRet><vProd>5780.00</vProd><vFrete>0.00</vFrete><vSeg>0.00</vSeg><vDesc>0.00</vDesc><vII>0.00</vII><vIPI>0.00</vIPI><vIPIDevol>0.00</vIPIDevol><vPIS>0.00</vPIS><vCOFINS>0.00</vCOFINS><vOutro>0.00</vOutro><vNF>5780.00</vNF></ICMSTot></total><transp><modFrete>1</modFrete><transporta><CNPJ>02012862002707</CNPJ><xNome>LATAM LINHAS AEREAS S/A</xNome><IE>024673560</IE><xEnder>PRACA MINISTRO SALGADO FILHO, S/N, IMBIRIBEIRA</xEnder><xMun>Recife</xMun><UF>PE</UF></transporta><vol><qVol>1</qVol><esp>CAIXA DE PAPELÃO</esp><marca>S/ MARCA</marca></vol></transp><cobr><fat><nFat>1687</nFat><vOrig>5780.00</vOrig><vDesc>0.00</vDesc><vLiq>5780.00</vLiq></fat><dup><nDup>001</nDup><dVenc>2018-09-25</dVenc><vDup>2890.00</vDup></dup><dup><nDup>002</nDup><dVenc>2018-11-04</dVenc><vDup>2890.00</vDup></dup></cobr><pag><detPag><tPag>99</tPag><vPag>5780.00</vPag></detPag></pag><infAdic><infCpl>- NCM:9021.10.10 - Alíquotas da COFINS e do PIS Reduzidas a Zero pela Lei pela Lei 10.865/2004 ( Redação da Lei 12.058/2009 ) - Isento de ICMS pelo Convênio 126/2010.NCM:3006.40.20 - Isento de ICMS até 30/09/2019 pelos Convênios 01/99 e 049/2017 - Alíquotas da COFINS e do PIS Reduzidas a Zero pelo Decreto 6426/2008.</infCpl></infAdic></infNFe><Signature xmlns="http://www.w3.org/2000/09/xmldsig#"><SignedInfo><CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315" /><SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1" /><Reference URI="#NFe26180812984794000154550010000016871192213339"><Transforms><Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature" /><Transform Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315" /></Transforms><DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1" /><DigestValue>x7gyL3XnoxBJdNazenJGuNwqRIQ=</DigestValue></Reference></SignedInfo><SignatureValue>fwCykhp3tX/+E3uomHDLVmZB8qX7X6MBJsPluFn4SgDRXenw5Umxgb9NORDE9j/uhsYE7vwJT+T5mslK88jOCDp0loi5z89jmzK9T+/tdwOTHL5FF0oRWvm4MUP3wxFIClfPHzEYL308uVGC9RH1lVa0RjPUPhSj2ikSWHIJwZx5koIdW2b23iLa3ACSjWHLFUs3C6k0ZVRjz70smR/Dn8WuEZs2b1kW2KYmG81nrK+iIO6IQrETwSX+whX/TuL6Z9c0HwOArteAB5pMLL76MJlwwgyUdO/V7SlM1TErsILSHNUZjkOo+5RsWQfAbdsVi0UFDMgkIFm2uc+TxqcKrA==</SignatureValue><KeyInfo><X509Data><X509Certificate>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</X509Certificate></X509Data></KeyInfo></Signature></NFe><protNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><infProt Id="ID26180812984794000154550010000016871192213339"><tpAmb>1</tpAmb><verAplic>NFEPE_P_20.01.01.166</verAplic><chNFe>26180812984794000154550010000016871192213339</chNFe><dhRecbto>2018-08-16T16:45:05-03:00</dhRecbto><nProt>126180042806970</nProt><digVal>x7gyL3XnoxBJdNazenJGuNwqRIQ=</digVal><cStat>100</cStat><xMotivo>Autorizado o uso da NF-e</xMotivo></infProt></protNFe></nfeProc>'  # noqa
        event = self.nfe_export._gerar_evento(test_xml, '1')
