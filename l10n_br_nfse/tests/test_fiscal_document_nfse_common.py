# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    PROCESSADOR_NENHUM,
    PROCESSADOR_OCA,
)

from ..models.document import filter_processador_edoc_nfse


class TestFiscalDocumentNFSeCommon(TransactionCase):
    def setUp(self):
        super(TestFiscalDocumentNFSeCommon, self).setUp()

        self.nfse_same_state = self.env.ref("l10n_br_fiscal.demo_nfse_same_state")
        self.company = self.env.ref("l10n_br_base.empresa_simples_nacional")

        self.company.processador_edoc = PROCESSADOR_OCA
        self.company.partner_id.inscr_mun = "35172"
        self.company.partner_id.inscr_est = ""
        self.company.partner_id.state_id = self.env.ref("base.state_br_mg")
        self.company.partner_id.city_id = self.env.ref("l10n_br_base.city_3132404")
        self.company.icms_regulation_id = self.env.ref(
            "l10n_br_fiscal.tax_icms_regulation"
        ).id
        self.company.city_taxation_code_id = self.env.ref(
            "l10n_br_fiscal.city_taxation_code_itajuba"
        )
        self.company.document_type_id = self.env.ref("l10n_br_fiscal.document_SE")
        self.nfse_same_state.company_id = self.company.id

    def test_certified_nfse_same_state_(self):
        """Test Certified NFSe same state."""

        self.nfse_same_state._onchange_document_serie_id()
        self.nfse_same_state._onchange_fiscal_operation_id()

        # RPS Number
        self.assertEqual(
            self.nfse_same_state.rps_number,
            "50",
            "Error to mappping RPS Number 50"
            " for Venda de Serviço de Contribuinte Dentro do Estado.",
        )

        # RPS Type
        self.assertEqual(
            self.nfse_same_state.rps_type,
            "1",
            "Error to mappping RPS Type 1"
            " for Venda de Serviço de Contribuinte Dentro do Estado.",
        )

        # Operation Nature
        self.assertEqual(
            self.nfse_same_state.operation_nature,
            "1",
            "Error to mappping Operation Nature 1"
            " for Venda de Serviço de Contribuinte Dentro do Estado.",
        )

        # Taxation Special Regime
        self.assertEqual(
            self.nfse_same_state.taxation_special_regime,
            "1",
            "Error to mappping Taxation Special Regime 1"
            " for Venda de Serviço de Contribuinte Dentro do Estado.",
        )

        # IBGE Code
        self.assertEqual(
            str(self.company.prepare_company_servico().get("codigo_municipio")),
            "3132404",
            "Error to mappping IBGE Code 3132404"
            " for Venda de Serviço de Contribuinte Dentro do Estado.",
        )

        # test _prepare_dados_servico()
        self.assertEqual(
            str(self.nfse_same_state._prepare_dados_servico().get("codigo_municipio")),
            "3132404",
            "Error to mappping IBGE Code 3132404"
            " for Venda de Serviço de Contribuinte Dentro do Estado.",
        )

        # test _prepare_dados_tomador()
        self.assertEqual(
            str(self.nfse_same_state._prepare_dados_tomador().get("codigo_municipio")),
            "3550308",
            "Error to mappping IBGE Code 3550308"
            " for Venda de Serviço de Contribuinte Dentro do Estado.",
        )

        # Test with Processador OCA
        self.assertTrue(filter_processador_edoc_nfse(self.nfse_same_state))

        # test without Processador
        self.company.processador_edoc = PROCESSADOR_NENHUM
        self.assertFalse(filter_processador_edoc_nfse(self.nfse_same_state))

        # Test res.partner.prepare_partner_tomador
        self.assertEqual(
            str(
                self.nfse_same_state.partner_id.prepare_partner_tomador(
                    self.company.country_id.id
                ).get("codigo_municipio")
            ),
            "3550308",
            "Error to mappping IBGE Code 3550308"
            " for Venda de Serviço de Contribuinte Dentro do Estado.",
        )

        # Test res.partner.prepare_partner_tomador (Exterior)
        self.assertEqual(
            str(
                self.nfse_same_state.partner_id.prepare_partner_tomador(1).get(
                    "codigo_municipio"
                )
            ),
            "9999999",
            "Error to mappping IBGE Code 9999999"
            " for Venda de Serviço de Contribuinte Dentro do Estado.",
        )

        for line in self.nfse_same_state.fiscal_line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

            # prepare_line_servico()
            self.assertEqual(
                line.prepare_line_servico().get("codigo_tributacao_municipio"),
                "6311900",
                "Error to mappping City Taxation Code 6311900"
                " for Venda de Serviço de Contribuinte Dentro do Estado.",
            )

            # Fiscal Deductions Value
            self.assertEqual(
                line.fiscal_deductions_value,
                0.0,
                "Error to mappping Fiscal Deductions Value 0.0"
                " for Venda de Serviço de Contribuinte Dentro do Estado.",
            )

            # City Taxation Code
            self.assertEqual(
                line.city_taxation_code_id.code,
                "6311900",
                "Error to mappping City Taxation Code 6311900"
                " for Venda de Serviço de Contribuinte Dentro do Estado.",
            )

            # Fiscal Deductions Value
            line.product_id.fiscal_deductions_value = 10
            line._onchange_product_id_fiscal()
            self.assertEqual(
                line.fiscal_deductions_value,
                10.0,
                "Error to mappping Fiscal Deductions Value 10.0"
                " for Venda de Serviço de Contribuinte Dentro do Estado.",
            )
