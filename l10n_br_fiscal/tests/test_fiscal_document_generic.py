# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from psycopg2 import IntegrityError

from odoo.exceptions import UserError
from odoo.tests import SavepointCase
from odoo.tools import mute_logger

from ..constants.icms import ICMS_ORIGIN_TAX_IMPORTED


class TestFiscalDocumentGeneric(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Contribuinte
        cls.nfe_same_state = cls.env.ref("l10n_br_fiscal.demo_nfe_same_state")
        cls.nfe_other_state = cls.env.ref("l10n_br_fiscal.demo_nfe_other_state")
        cls.nfe_not_taxpayer = cls.env.ref("l10n_br_fiscal.demo_nfe_nao_contribuinte")

        cls.nfe_not_taxpayer_pf = cls.env.ref(
            "l10n_br_fiscal.demo_nfe_nao_contribuinte_pf"
        )

        cls.nfe_export = cls.env.ref("l10n_br_fiscal.demo_nfe_export")

        # Simples Nacional
        cls.nfe_sn_same_state = cls.env.ref("l10n_br_fiscal.demo_nfe_sn_same_state")
        cls.nfe_sn_other_state = cls.env.ref("l10n_br_fiscal.demo_nfe_sn_other_state")
        cls.nfe_sn_not_taxpayer = cls.env.ref(
            "l10n_br_fiscal.demo_nfe_sn_nao_contribuinte"
        )
        cls.nfe_sn_export = cls.env.ref("l10n_br_fiscal.demo_nfe_sn_export")

    def test_nfe_same_state(self):
        """Test NFe same state."""

        self.nfe_same_state._onchange_document_serie_id()
        self.nfe_same_state._onchange_fiscal_operation_id()

        for line in self.nfe_same_state.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.cfop_id.code,
                    "5102",
                    "Error to mappping CFOP 5102"
                    " for Revenda de Contribuinte Dentro do Estado.",
                )
            else:
                self.assertEqual(
                    line.cfop_id.code,
                    "5101",
                    "Error to mapping CFOP 5101"
                    " for Venda de Contribuinte Dentro do Estado.",
                )

            icms_internal_sp = [
                self.env.ref("l10n_br_fiscal.tax_icms_4"),
                self.env.ref("l10n_br_fiscal.tax_icms_7"),
                self.env.ref("l10n_br_fiscal.tax_icms_12"),
                self.env.ref("l10n_br_fiscal.tax_icms_18"),
                self.env.ref("l10n_br_fiscal.tax_icms_25"),
            ]

            is_icms_internal = line.icms_tax_id in icms_internal_sp

            # ICMS
            self.assertTrue(
                is_icms_internal,
                "Error to mapping ICMS Inernal for {}"
                " for Venda de Contribuinte Dentro do "
                "Estado.".format(self.nfe_same_state.partner_id.state_id.name),
            )
            self.assertEqual(
                line.icms_cst_id.code,
                "00",
                "Error to mapping CST 00 from ICMS 12%"
                " for Venda de Contribuinte Dentro do Estado.",
            )

            # ICMS FCP
            self.assertFalse(
                line.icmsfcp_tax_id,
                "Error to mapping ICMS FCP 2%"
                " for Venda de Contribuinte Dentro do Estado.",
            )

            # IPI
            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI NT",
                    "Error to mapping IPI NT"
                    " for Revenda de Contribuinte Dentro do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "53",
                    "Error to mapping CST 53 from IPI NT"
                    " to Revenda de Contribuinte Dentro do Estado.",
                )
            else:
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI 5%",
                    "Error to mapping IPI 5%"
                    " for Venda de Contribuinte Dentro do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "50",
                    "Error to mapping CST 50 from IPI 5%"
                    " to Venda de Contribuinte Dentro do Estado.",
                )

            # PIS
            self.assertEqual(
                line.pis_tax_id.name,
                "PIS 0,65%",
                "Error to mapping PIS 0,65%"
                " for Venda de Contribuinte Dentro do Estado.",
            )
            self.assertEqual(
                line.pis_cst_id.code,
                "01",
                "Error to mapping CST 01 - Operação Tributável com Alíquota"
                " Básica from PIS 0,65% to Venda de Contribuinte Dentro do Estado.",
            )

            # PIS
            self.assertEqual(
                line.cofins_tax_id.name,
                "COFINS 3%",
                "Error to mapping COFINS 3%"
                " for Venda de Contribuinte Dentro do Estado.",
            )
            self.assertEqual(
                line.cofins_cst_id.code,
                "01",
                "Error to mapping CST 01 - Operação Tributável com Alíquota Básica"
                " Básica to COFINS 3% de Venda de Contribuinte Dentro do Estado.",
            )

        self.nfe_same_state.action_document_confirm()

    def test_nfe_other_state(self):
        """Test NFe other state."""

        self.nfe_other_state._onchange_document_serie_id()
        self.nfe_other_state._onchange_fiscal_operation_id()

        for line in self.nfe_other_state.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.cfop_id.code,
                    "6102",
                    "Error to mapping CFOP 6102"
                    " for Revenda de Contribuinte p/ Fora do Estado.",
                )
            else:
                self.assertEqual(
                    line.cfop_id.code,
                    "6101",
                    "Error to mapping CFOP 6101"
                    " for Venda de Contribuinte p/ Fora do Estado.",
                )

            # ICMS
            if line.product_id.icms_origin in ICMS_ORIGIN_TAX_IMPORTED:
                self.assertEqual(
                    line.icms_tax_id.name,
                    "ICMS 4%",
                    "Error to mapping ICMS 4%"
                    " for Venda de Contribuinte p/ Fora do Estado.",
                )
                self.assertEqual(
                    line.icms_cst_id.code,
                    "00",
                    "Error to mapping CST 00 from ICMS 4%"
                    " for Venda de Contribuinte p/ Fora do Estado.",
                )
            else:

                self.assertEqual(
                    line.icms_tax_id.name,
                    "ICMS 7%",
                    "Error to mapping ICMS 7%"
                    " for Venda de Contribuinte p/ Fora do Estado.",
                )
                self.assertEqual(
                    line.icms_cst_id.code,
                    "00",
                    "Error to mapping CST 00 from ICMS 7%"
                    " for Venda de Contribuinte p/ Fora do Estado.",
                )

            # ICMS FCP
            self.assertFalse(
                line.icmsfcp_tax_id,
                "Error to mapping ICMS FCP 2%"
                " for Venda de Contribuinte Dentro do Estado.",
            )

            # IPI
            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI NT",
                    "Error to mapping IPI NT"
                    " for Revenda de Contribuinte Dentro do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "53",
                    "Error to mapping CST 53 from IPI NT"
                    " to Revenda de Contribuinte Dentro do Estado.",
                )
            else:
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI 5%",
                    "Error to mapping IPI 5%"
                    " for Venda de Contribuinte Dentro do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "50",
                    "Error to mapping CST 50 from IPI 5%"
                    " to Venda de Contribuinte Dentro do Estado.",
                )

            # PIS
            self.assertEqual(
                line.pis_tax_id.name,
                "PIS 0,65%",
                "Error to mapping PIS 0,65%"
                " for Venda de Contribuinte p/ Fora do Estado.",
            )
            self.assertEqual(
                line.pis_cst_id.code,
                "01",
                "Error to mapping CST 01 - Operação Tributável com Alíquota"
                " Básica from PIS 0,65% for"
                " Venda de Contribuinte p/ Fora do Estado.",
            )

            # PIS
            self.assertEqual(
                line.cofins_tax_id.name,
                "COFINS 3%",
                "Error to mapping COFINS 3%"
                " for Venda de Contribuinte p/ Fora do Estado.",
            )
            self.assertEqual(
                line.cofins_cst_id.code,
                "01",
                "Error to mapping CST 01 -"
                " Operação Tributável com Alíquota Básica"
                "from COFINS 3% for Venda de Contribuinte p/ Fora do Estado.",
            )

    def test_nfe_not_taxpayer(self):
        """Test NFe not taxpayer."""

        self.nfe_not_taxpayer._onchange_document_serie_id()
        self.nfe_not_taxpayer._onchange_fiscal_operation_id()

        for line in self.nfe_not_taxpayer.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.cfop_id.code,
                    "6108",
                    "Error to mapping CFOP 6108"
                    " for Revenda de Contribuinte p/ Não Contribuinte.",
                )
            else:
                self.assertEqual(
                    line.cfop_id.code,
                    "6107",
                    "Error to mapping CFOP 6107"
                    " for Venda de Contribuinte p/ Não Contribuinte.",
                )

            # ICMS
            self.assertEqual(
                line.icms_tax_id.name,
                "ICMS 12%",
                "Error to mapping ICMS 12%"
                " for Venda de Contribuinte p/ Não Contribuinte.",
            )
            self.assertEqual(
                line.icms_cst_id.code,
                "00",
                "Error to mapping CST 00 from ICMS 12%"
                " for Venda de Contribuinte p/ Não Contribuinte.",
            )

            # ICMS FCP
            self.assertFalse(
                line.icmsfcp_tax_id,
                "Error to mapping ICMS FCP 2%"
                " for Venda de Contribuinte Dentro do Estado.",
            )

            # IPI
            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI NT",
                    "Error to mapping IPI NT"
                    " for Revenda de Contribuinte Dentro do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "53",
                    "Error to mapping CST 53 from IPI NT"
                    " to Revenda de Contribuinte Dentro do Estado.",
                )
            else:
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI 5%",
                    "Error to mapping IPI 5%"
                    " for Venda de Contribuinte Dentro do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "50",
                    "Error to mapping CST 50 from IPI 5%"
                    " to Venda de Contribuinte Dentro do Estado.",
                )

            # PIS
            self.assertEqual(
                line.pis_tax_id.name,
                "PIS 0,65%",
                "Error to mapping PIS 0,65%"
                " for Venda de Contribuinte p/ Não Contribuinte.",
            )
            self.assertEqual(
                line.pis_cst_id.code,
                "01",
                "Error to mapping CST 01 - Operação Tributável com Alíquota"
                " Básica from PIS 0,65% for"
                " Venda de Contribuinte p/ Não Contribuinte.",
            )

            # PIS
            self.assertEqual(
                line.cofins_tax_id.name,
                "COFINS 3%",
                "Error to mapping COFINS 3%"
                " for Venda de Contribuinte p/ Não Contribuinte.",
            )
            self.assertEqual(
                line.cofins_cst_id.code,
                "01",
                "Error to mapping CST 01 -"
                " Operação Tributável com Alíquota Básica"
                "from COFINS 3% for Venda de Contribuinte p/ Não Contribuinte.",
            )

    def test_nfe_not_taxpayer_not_company(self):
        """Test NFe not taxpayer not Company."""

        self.nfe_not_taxpayer_pf._onchange_document_serie_id()
        self.nfe_not_taxpayer_pf._onchange_fiscal_operation_id()

        for line in self.nfe_not_taxpayer_pf.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.cfop_id.code,
                    "6108",
                    "Error to mapping CFOP 6108"
                    " for Revenda de Contribuinte p/ Não Contribuinte.",
                )
            else:
                self.assertEqual(
                    line.cfop_id.code,
                    "6107",
                    "Error to mapping CFOP 6107"
                    " for Venda de Contribuinte p/ Não Contribuinte.",
                )

            # ICMS
            self.assertEqual(
                line.icms_tax_id.name,
                "ICMS 12%",
                "Error to mapping ICMS 12%"
                " for Venda de Contribuinte p/ Não Contribuinte.",
            )
            self.assertEqual(
                line.icms_cst_id.code,
                "00",
                "Error to mapping CST 00 from ICMS 12%"
                " for Venda de Contribuinte p/ Não Contribuinte.",
            )

            # ICMS FCP
            self.assertEqual(
                line.icmsfcp_tax_id.name,
                "FCP 2%",
                "Erro ao mapear ICMS FCP 2%"
                " para Venda de Contribuinte p/ Não Contribuinte.",
            )

            # IPI
            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI NT",
                    "Error to mapping IPI NT"
                    " for Revenda de Contribuinte Dentro do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "53",
                    "Error to mapping CST 53 from IPI NT"
                    " to Revenda de Contribuinte Dentro do Estado.",
                )
            else:
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI 5%",
                    "Error to mapping IPI 5%"
                    " for Venda de Contribuinte Dentro do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "50",
                    "Error to mapping CST 50 from IPI 5%"
                    " to Venda de Contribuinte Dentro do Estado.",
                )

            # PIS
            self.assertEqual(
                line.pis_tax_id.name,
                "PIS 0,65%",
                "Error to mapping PIS 0,65%"
                " for Venda de Contribuinte p/ Não Contribuinte.",
            )
            self.assertEqual(
                line.pis_cst_id.code,
                "01",
                "Error to mapping CST 01 - Operação Tributável com Alíquota"
                " Básica from PIS 0,65% for"
                " Venda de Contribuinte p/ Não Contribuinte.",
            )

            # PIS
            self.assertEqual(
                line.cofins_tax_id.name,
                "COFINS 3%",
                "Error to mapping COFINS 3%"
                " for Venda de Contribuinte p/ Não Contribuinte.",
            )
            self.assertEqual(
                line.cofins_cst_id.code,
                "01",
                "Error to mapping CST 01 -"
                " Operação Tributável com Alíquota Básica"
                "from COFINS 3% for Venda de Contribuinte p/ Não Contribuinte.",
            )

    def test_nfe_export(self):
        """Test NFe export."""

        self.nfe_export._onchange_document_serie_id()
        self.nfe_export._onchange_fiscal_operation_id()

        for line in self.nfe_export.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.cfop_id.code,
                    "7102",
                    "Error to mapping CFOP 7102"
                    " for Revenda de Contribuinte p/ o Exterior.",
                )
            else:
                self.assertEqual(
                    line.cfop_id.code,
                    "7101",
                    "Error to mapping CFOP 7101"
                    " for Venda de Contribuinte p/ o Exterior.",
                )

            # ICMS - TODO field missing
            # self.assertEqual(
            #    line.icms_tax_id.name, 'ICMS 7%',
            #    "Error to mapping ICMS 7%"
            #    " for Venda de Contribuinte p/ o Exterior.")
            # self.assertEqual(
            #    line.icms_cst_id.code, '00',
            #    "Error to mapping CST 00 from ICMS 7%"
            #    " for Venda de Contribuinte p/ o Exterior.")

            # ICMS FCP
            # self.assertEqual(
            #    line.icmsfcp_tax_id.name, 'FCP 2%',
            #    "Erro ao mapear ICMS FCP 2%"
            #    " para Venda de Contribuinte p/ o Exterior.")

            # IPI
            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI NT",
                    "Error to mapping IPI NT"
                    " for Revenda de Contribuinte Dentro do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "53",
                    "Error to mapping CST 53 from IPI NT"
                    " to Revenda de Contribuinte Dentro do Estado.",
                )
            else:
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI 5%",
                    "Error to mapping IPI 5%"
                    " for Venda de Contribuinte Dentro do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "50",
                    "Error to mapping CST 50 from IPI 5%"
                    " to Venda de Contribuinte Dentro do Estado.",
                )

            # PIS
            self.assertEqual(
                line.pis_tax_id.name,
                "PIS 0,65%",
                "Error to mapping PIS 0,65%"
                " for Venda de Contribuinte p/ o Exterior.",
            )
            self.assertEqual(
                line.pis_cst_id.code,
                "01",
                "Error to mapping CST 01 - Operação Tributável com Alíquota"
                " Básica from PIS 0,65% for"
                " Venda de Contribuinte p/ o Exterior.",
            )

            # PIS
            self.assertEqual(
                line.cofins_tax_id.name,
                "COFINS 3%",
                "Error to mapping COFINS 3%"
                " for Venda de Contribuinte p/ o Exterior.",
            )
            self.assertEqual(
                line.cofins_cst_id.code,
                "01",
                "Error to mapping CST 01 -"
                " Operação Tributável com Alíquota Básica"
                "from COFINS 3% for Venda de Contribuinte p/ o Exterior.",
            )

    def test_nfe_sn_same_state(self):
        """Test NFe Simples Nacional same state."""

        self.nfe_sn_same_state._onchange_document_serie_id()
        self.nfe_sn_same_state._onchange_fiscal_operation_id()

        for line in self.nfe_sn_same_state.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()

            # set fake estimate tax
            line.ncm_id.tax_estimate_ids.create(
                {
                    "ncm_id": line.ncm_id.id,
                    "state_id": line.company_id.state_id.id,
                    "key": "fake estimate tax",
                    "origin": "fake estimate tax",
                    "federal_taxes_national": 33.00,
                }
            )

            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.cfop_id.code,
                    "5102",
                    "Error to mappping CFOP 5102"
                    " for Revenda de Simples Nacional Dentro do Estado.",
                )
                # IPI
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI NT",
                    "Error to mapping IPI Simples Nacional"
                    " for Venda de Simples Nacional Fora do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "53",
                    "Error to mapping CST 53 from IPI Simples Nacional"
                    " for Venda de Simples Nacional Fora do Estado.",
                )
            else:
                self.assertEqual(
                    line.cfop_id.code,
                    "5101",
                    "Error to mapping CFOP 5101"
                    " for Venda de Simples Nacional Dentro do Estado.",
                )
                # IPI
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI Outros",
                    "Error to mapping IPI Simples Nacional"
                    " for Venda de Simples Nacional Fora do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "99",
                    "Error to mapping CST 99 from IPI Simples Nacional"
                    " for Venda de Simples Nacional Fora do Estado.",
                )

            # ICMS
            self.assertEqual(
                line.icmssn_tax_id.name,
                "ICMS SN Com Permissão de Crédito",
                "Error to mapping ICMS SN Com Permissão de Crédito"
                " for Venda de Simples Nacional Dentro do Estado.",
            )
            self.assertEqual(
                line.icms_cst_id.code,
                "101",
                "Error to mapping CST 101 do ICMS SN Com Permissão de Crédito"
                " for Venda de Simples Nacional Dentro do Estado.",
            )

            # ICMS FCP - TODO mapping failed
            # self.assertEqual(
            #    line.icmsfcp_tax_id.name, 'FCP 2%',
            #    "Erro ao mapear ICMS FCP 2%"
            #    " para Venda de Simples Nacional Dentro do Estado.")

            # PIS
            self.assertEqual(
                line.pis_tax_id.name,
                "PIS Outros",
                "Error to mapping PIS Simples Nacional"
                " for Venda de Simples Nacional Dentro do Estado.",
            )
            self.assertEqual(
                line.pis_cst_id.code,
                "49",
                "Error to mapping CST 49 Outras Operações de Saída"
                " from PIS Simples Nacional from Venda de"
                " Simples Nacional Dentro do Estado.",
            )

            # COFINS
            self.assertEqual(
                line.cofins_tax_id.name,
                "COFINS Outros",
                "Error to mapping COFINS Simples Nacional"
                " for Venda de Simples Nacional Dentro do Estado.",
            )
            self.assertEqual(
                line.cofins_cst_id.code,
                "49",
                "Error to mapping CST 49 Outras Operações de Saída"
                " from COFINS Simples Nacional for Venda de"
                " Simples Nacional Fora do Estado.",
            )

        # ESTIMATE TAXES
        self.assertEqual(self.nfe_sn_same_state.amount_estimate_tax, 1308.45)

    def test_nfe_sn_other_state(self):
        """Test NFe SN other state."""

        self.nfe_sn_other_state._onchange_document_serie_id()
        self.nfe_sn_other_state._onchange_fiscal_operation_id()

        for line in self.nfe_sn_other_state.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.cfop_id.code,
                    "6102",
                    "Error to mappping CFOP 6102"
                    " for Revenda de Simples Nacional Fora do Estado.",
                )
                # IPI
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI NT",
                    "Error to mapping IPI Simples Nacional"
                    " for Venda de Simples Nacional Fora do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "53",
                    "Error to mapping CST 53 from IPI Simples Nacional"
                    " for Venda de Simples Nacional Fora do Estado.",
                )
            else:
                self.assertEqual(
                    line.cfop_id.code,
                    "6101",
                    "Error to mapping CFOP 6101"
                    " for Venda de Simples Nacional Fora do Estado.",
                )
                # IPI
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI Outros",
                    "Error to mapping IPI Simples Nacional"
                    " for Venda de Simples Nacional Fora do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "99",
                    "Error to mapping CST 99 from IPI Simples Nacional"
                    " for Venda de Simples Nacional Fora do Estado.",
                )

            # ICMS
            self.assertEqual(
                line.icmssn_tax_id.name,
                "ICMS SN Com Permissão de Crédito",
                "Error to mapping ICMS SN Com Permissão de Crédito"
                " for Venda de Simples Nacional Dentro do Estado.",
            )
            self.assertEqual(
                line.icms_cst_id.code,
                "101",
                "Erro ao mapear a CST 101 do ICMS SN Com Permissão de Crédito"
                " para Venda de Simples Nacional Dentro do Estado.",
            )

            # ICMS FCP - TODO mapping failed
            # self.assertEqual(
            #    line.icmsfcp_tax_id.name, 'FCP 2%',
            #    "Erro ao mapear ICMS FCP 2%"
            #    " para Venda de Simples Nacional Fora do Estado.")

            # PIS
            self.assertEqual(
                line.pis_tax_id.name,
                "PIS Outros",
                "Erro ao mapear PIS Simples Nacional"
                " para Venda de Simples Nacional Fora do Estado.",
            )
            self.assertEqual(
                line.pis_cst_id.code,
                "49",
                "Erro ao mapear a CST 49 Outras Operações de Saída"
                " com Alíquota Básica do PIS Simples Nacional de Venda de"
                " Simples Nacional Dentro do Estado.",
            )

            # COFINS
            self.assertEqual(
                line.cofins_tax_id.name,
                "COFINS Outros",
                "Error to mapping COFINS Simples Nacional"
                " for Venda de Simples Nacional Dentro do Estado.",
            )
            self.assertEqual(
                line.cofins_cst_id.code,
                "49",
                "Error to mapping CST 49 Outras Operações de Saída"
                " from COFINS Simples Nacional for Venda de"
                " Simples Nacional Fora do Estado.",
            )

    def test_nfe_sn_not_taxpayer(self):
        """Test NFe SN not taxpayer."""

        self.nfe_sn_not_taxpayer._onchange_document_serie_id()
        self.nfe_sn_not_taxpayer._onchange_fiscal_operation_id()

        for line in self.nfe_sn_not_taxpayer.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.cfop_id.code,
                    "5102",
                    "Error to mappping CFOP 5102"
                    " for Revenda de Simples Nacional Fora do Estado.",
                )
            else:
                self.assertEqual(
                    line.cfop_id.code,
                    "5101",
                    "Error to mapping CFOP 5101"
                    " for Venda de Simples Nacional Fora do Estado.",
                )

            # ICMS
            self.assertEqual(
                line.icms_tax_id.name,
                "ICMS 18%",
                "Error to mapping ICMS 18%"
                " for Venda de Simples Nacional Fora do Estado.",
            )
            self.assertEqual(
                line.icms_cst_id.code,
                "00",
                "Erro ao mapear a CST 00 do ICMS 18%"
                " para Venda de Simples Nacional Fora do Estado.",
            )

            # ICMS FCP
            # self.assertEqual(
            #     line.icmsfcp_tax_id.name, 'FCP 2%',
            #     "Erro ao mapear ICMS FCP 2%"
            #     " para Venda de Simples Nacional Fora do Estado.")

            # IPI
            self.assertEqual(
                line.ipi_tax_id.name,
                "IPI 5%",
                "Erro ao mapear IPI 5%"
                " para Venda de Simples Nacional Fora do Estado.",
            )
            self.assertEqual(
                line.ipi_cst_id.code,
                "50",
                "Erro ao mapear a CST 50 do IPI 5%"
                " de Venda de Simples Nacional Fora do Estado.",
            )

            # PIS
            self.assertEqual(
                line.pis_tax_id.name,
                "PIS 0,65%",
                "Erro ao mapear PIS 0,65%"
                " para Venda de Simples Nacional Fora do Estado.",
            )
            self.assertEqual(
                line.pis_cst_id.code,
                "01",
                "Erro ao mapear a CST 01 - Operação Tributável"
                " com Alíquota Básica do PIS 0,65% de Venda de"
                " Simples Nacional Fora do Estado.",
            )

            # PIS
            self.assertEqual(
                line.cofins_tax_id.name,
                "COFINS 3%",
                "Erro ao mapear COFINS 3%"
                " para Venda de Simples Nacional Dentro do Estado.",
            )
            self.assertEqual(
                line.cofins_cst_id.code,
                "01",
                "Erro ao mapear a CST 01 - Operação Tributável"
                " com Alíquota Básica do COFINS 3% de Venda de"
                " Simples Nacional Fora do Estado.",
            )

    def test_nfe_sn_export(self):
        """Test NFe SN export."""

        self.nfe_sn_export._onchange_document_serie_id()
        self.nfe_sn_export._onchange_fiscal_operation_id()

        for line in self.nfe_sn_export.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

            if "Revenda" in line.fiscal_operation_line_id.name:
                self.assertEqual(
                    line.cfop_id.code,
                    "7102",
                    "Error to mapping CFOP 7102"
                    " for Revenda de Contribuinte p/ o Exterior.",
                )
                # IPI
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI NT",
                    "Error to mapping IPI Simples Nacional"
                    " for Venda de Simples Nacional Fora do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "53",
                    "Error to mapping CST 53 from IPI Simples Nacional"
                    " for Venda de Simples Nacional Fora do Estado.",
                )
            else:
                self.assertEqual(
                    line.cfop_id.code,
                    "7101",
                    "Error to mapping CFOP 7101"
                    " for Venda de Contribuinte p/ o Exterior.",
                )
                # IPI
                self.assertEqual(
                    line.ipi_tax_id.name,
                    "IPI Outros",
                    "Error to mapping IPI Simples Nacional"
                    " for Venda de Simples Nacional Fora do Estado.",
                )
                self.assertEqual(
                    line.ipi_cst_id.code,
                    "99",
                    "Error to mapping CST 99 from IPI Simples Nacional"
                    " for Venda de Simples Nacional Fora do Estado.",
                )

            # ICMS
            self.assertEqual(
                line.icmssn_tax_id.name,
                "ICMS SN Com Permissão de Crédito",
                "Error to mapping ICMS SN Com Permissão de Crédito"
                " for Venda de Simples Nacional Dentro do Estado.",
            )
            self.assertEqual(
                line.icms_cst_id.code,
                "101",
                "Erro ao mapear a CST 101 do ICMS SN Com Permissão de Crédito"
                " para Venda de Simples Nacional Dentro do Estado.",
            )

            # ICMS FCP
            # self.assertEqual(
            #    line.icmsfcp_tax_id.name, 'FCP 2%',
            #    "Erro ao mapear ICMS FCP 2%"
            #    " para Venda de Contribuinte p/ o Exterior.")

            # PIS
            self.assertEqual(
                line.pis_tax_id.name,
                "PIS Outros",
                "Erro ao mapear PIS Simples Nacional"
                " para Venda de Simples Nacional Fora do Estado.",
            )
            self.assertEqual(
                line.pis_cst_id.code,
                "49",
                "Erro ao mapear a CST 49 Outras Operações de Saída"
                " com Alíquota Básica do PIS Simples Nacional de Venda de"
                " Simples Nacional Dentro do Estado.",
            )

            # COFINS
            self.assertEqual(
                line.cofins_tax_id.name,
                "COFINS Outros",
                "Error to mapping COFINS Simples Nacional"
                " for Venda de Simples Nacional Dentro do Estado.",
            )
            self.assertEqual(
                line.cofins_cst_id.code,
                "49",
                "Error to mapping CST 49 Outras Operações de Saída"
                " from COFINS Simples Nacional for Venda de"
                " Simples Nacional Fora do Estado.",
            )

    def test_nfe_return(self):
        """Test Fiscal Document Return"""
        action = self.nfe_same_state.action_create_return()
        return_id = self.nfe_same_state.browse(
            [i[2][0] for i in action["domain"] if i[0] == "id"]
        )

        self.assertEqual(
            return_id.fiscal_operation_id.id,
            self.nfe_same_state.fiscal_operation_id.return_fiscal_operation_id.id,
            "Error on creation return",
        )

    def test_unlink_dummy_document(self):
        """Test Dummy Fiscal Document Unlink Restrictions"""
        dummy_document = self.env.user.company_id.fiscal_dummy_id
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            # as much as possible we ensure technical dummy fiscal documents
            # cannot be removed by mistake easily even from SQL
            dummy_document.unlink()

    def test_unlink_dummy_document_line(self):
        """Test Dummy Fiscal Document Line Unlink Restrictions"""
        dummy_line = self.env.user.company_id.fiscal_dummy_id.line_ids[0]
        with self.assertRaises(UserError):
            dummy_line.unlink()

    def test_nfe_comments(self):
        self.nfe_not_taxpayer._document_comment()
        additional_data = self.nfe_not_taxpayer.line_ids[0].additional_data
        self.assertEqual(
            additional_data, "manual comment test - Valor Aprox. dos Tributos: R$ 0.00"
        )
