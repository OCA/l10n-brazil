# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_base.tests.tools import load_fixture_files
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    PROCESSADOR_NENHUM,
    PROCESSADOR_OCA,
)
from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files

from ..models.document import filter_processador_edoc_nfse


class TestFiscalDocumentNFSeCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        load_fiscal_fixture_files(cls.env)
        load_fixture_files(
            cls.env, "l10n_br_fiscal", file_names=["fiscal_document_nfse_demo.xml"]
        )
        load_fixture_files(
            cls.env,
            "l10n_br_nfse",
            file_names=[
                "product_demo.xml",
                "fiscal_document_demo.xml",
            ],
        )

        cls.nfse_same_state = cls.env.ref("l10n_br_fiscal.demo_nfse_same_state")
        cls.company = cls.env.ref("l10n_br_base.empresa_simples_nacional")

        cls.company.processador_edoc = PROCESSADOR_OCA
        cls.company.partner_id.l10n_br_im_code = "35172"
        cls.company.partner_id.l10n_br_ie_code = ""
        cls.company.partner_id.state_id = cls.env.ref("base.state_br_mg")
        cls.company.partner_id.city_id = cls.env.ref("l10n_br_base.city_3132404")
        cls.company.icms_regulation_id = cls.env.ref(
            "l10n_br_fiscal.tax_icms_regulation"
        ).id
        cls.company.document_type_id = cls.env.ref("l10n_br_fiscal.document_SE")
        cls.nfse_same_state.company_id = cls.company.id
        cls.nbs_id = cls.env["l10n_br_fiscal.nbs"].create(
            {
                "code": "0101",
                "name": "Desenvolvimento de Software",
            }
        )
        cls.tax_estimate = cls.env["l10n_br_fiscal.tax.estimate"].create(
            {
                "nbs_id": cls.nbs_id.id,
                "state_id": cls.company.partner_id.state_id.id,
                "federal_taxes_national": 13.45,
                "federal_taxes_import": 18.20,
                "state_taxes": 0.0,
                "municipal_taxes": 2.90,
            }
        )

    def test_certified_nfse_same_state_(self):
        """Test Certified NFSe same state."""
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
            str(self.company._prepare_company_service().get("codigo_municipio")),
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

        self.assertEqual(
            str(
                self.nfse_same_state.partner_id._prepare_service_provider(
                    self.company.country_id.id
                ).get("codigo_municipio")
            ),
            "3550308",
            "Error to mappping IBGE Code 3550308"
            " for Venda de Serviço de Contribuinte Dentro do Estado.",
        )

        self.assertEqual(
            str(
                self.nfse_same_state.partner_id._prepare_service_provider(1).get(
                    "codigo_municipio"
                )
            ),
            "9999999",
            "Error to mappping IBGE Code 9999999"
            " for Venda de Serviço de Contribuinte Dentro do Estado.",
        )

        for line in self.nfse_same_state.fiscal_line_ids:
            self.assertEqual(
                line._prepare_line_service().get("codigo_tributacao_municipio"),
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
            self.assertEqual(
                line.fiscal_deductions_value,
                10.0,
                "Error to mappping Fiscal Deductions Value 10.0"
                " for Venda de Serviço de Contribuinte Dentro do Estado.",
            )

    def test_tax_estimate_by_nbs(self):
        """Test tax estimate tags for national and foreign partners based on NBS."""

        fiscal_document = self.nfse_same_state
        service_data = fiscal_document._prepare_dados_servico()

        self.assertFalse(
            service_data["percentual_total_tributos_federais"],
            "Should be False when no NBS is defined",
        )
        self.assertFalse(
            service_data["percentual_total_tributos_estaduais"],
            "Should be False when no NBS is defined",
        )
        self.assertFalse(
            service_data["percentual_total_tributos_municipais"],
            "Should be False when no NBS is defined",
        )

        fiscal_line = fiscal_document.fiscal_line_ids[0]
        fiscal_line.nbs_id = self.nbs_id
        fiscal_line.issqn_fg_city_id = self.company.partner_id.city_id
        service_data = fiscal_document._prepare_dados_servico()

        self.assertEqual(
            self.tax_estimate.federal_taxes_national,
            service_data["percentual_total_tributos_federais"],
            "Should be the same as tax_estimate.federal_taxes_national",
        )
        self.assertEqual(
            self.tax_estimate.state_taxes,
            service_data["percentual_total_tributos_estaduais"],
            "Should be the same as tax_estimate.state_taxes",
        )
        self.assertEqual(
            self.tax_estimate.municipal_taxes,
            service_data["percentual_total_tributos_municipais"],
            "Should be the same as tax_estimate.municipal_taxes",
        )

        fiscal_document.partner_id = self.env.ref("l10n_br_base.res_partner_exterior")
        fiscal_line.issqn_fg_city_id = False
        service_data = fiscal_document._prepare_dados_servico()

        self.assertEqual(
            self.tax_estimate.federal_taxes_import,
            service_data["percentual_total_tributos_federais"],
            "Should be the same as tax_estimate.federal_taxes_import",
        )
        self.assertEqual(
            self.tax_estimate.state_taxes,
            service_data["percentual_total_tributos_estaduais"],
            "Should be the same as tax_estimate.state_taxes",
        )
        self.assertEqual(
            self.tax_estimate.municipal_taxes,
            service_data["percentual_total_tributos_municipais"],
            "Should be the same as tax_estimate.municipal_taxes",
        )
