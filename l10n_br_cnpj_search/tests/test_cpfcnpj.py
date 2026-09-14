# Copyright 2015-2026 CPF.CNPJ | ALAS Tecnologia LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import date
from unittest import mock

import requests
from erpbrasil.base.misc import punctuation_rm

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK_NORMAL

from .common import MOCK_REQUESTS_GET, TestCnpjCommon

_logger = logging.getLogger(__name__)

MOCK_VALIDATE = (
    "odoo.addons.l10n_br_cnpj_search.models.cnpj_webservice.CNPJWebservice.validate"
)


@tagged("post_install", "-at_install")
class TestCpfCnpj(TestCnpjCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_param("cnpj_provider", "cpfcnpj")
        cls.set_param("cpfcnpj_token", "dummy-token")
        cls.set_param("cpfcnpj_package", "6")

    def _run_wizard(self, partner):
        action_wizard = partner.action_open_cnpj_search_wizard()
        wizard_context = action_wizard.get("context")
        wizard_context["active_model"] = "res.partner"
        wizard = (
            self.env["partner.search.wizard"].with_context(**wizard_context).create({})
        )
        wizard.action_update_partner()

    def test_cpfcnpj_simples(self):
        """A Simples Nacional company must fill tax_framework as Simples."""
        with (
            mock.patch(MOCK_REQUESTS_GET, return_value=mock.Mock(status_code=200)),
            mock.patch(
                MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_simples
            ),
        ):
            partner = self.model.create(
                {"name": "Dummy Simples", "vat": "34.238.864/0001-68"}
            )
            partner._onchange_vat()
            self._run_wizard(partner)

        self.assertEqual(partner.company_type, "company")
        self.assertEqual(partner.legal_name, "Token Test Ltda")
        self.assertEqual(partner.name, "Token Test")
        self.assertEqual(partner.email, "contato@empresa.com")
        self.assertEqual(partner.street_name, "Rua A")
        self.assertEqual(partner.street_number, "1")
        self.assertEqual(partner.street2, "Sala 1")
        self.assertEqual(partner.district, "Centro")
        self.assertEqual(partner.phone, "(11) 22334454")
        self.assertEqual(partner.mobile, "(11) 22334455")
        self.assertEqual(partner.state_id.code, "MG")
        self.assertEqual(partner.equity_capital, 95000)
        self.assertEqual(partner.cnae_main_id.code, "6202-3/00")
        # Differential: no other provider fills tax_framework today.
        self.assertEqual(partner.tax_framework, "1")

    def test_cpfcnpj_mei(self):
        """An MEI company must fill tax_framework as MEI."""
        with (
            mock.patch(MOCK_REQUESTS_GET, return_value=mock.Mock(status_code=200)),
            mock.patch(MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_mei),
        ):
            partner = self.model.create(
                {"name": "Dummy MEI", "vat": "44.356.113/0001-08"}
            )
            partner._onchange_vat()
            self._run_wizard(partner)

        self.assertEqual(partner.company_type, "company")
        self.assertEqual(partner.legal_name, "Joao Da Silva 12345678900")
        # No fantasy name, so name falls back to the legal name.
        self.assertEqual(partner.name, "Joao Da Silva 12345678900")
        self.assertEqual(partner.state_id.code, "MG")
        self.assertEqual(partner.tax_framework, "4")

    def test_cpfcnpj_regime_normal(self):
        """A company that is neither Simples nor SIMEI must fill tax_framework
        as Regime Normal. This payload also has no IBGE code (city resolved by
        name) and no phone numbers.
        """
        with (
            mock.patch(MOCK_REQUESTS_GET, return_value=mock.Mock(status_code=200)),
            mock.patch(MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_normal),
        ):
            partner = self.model.create(
                {"name": "Dummy Normal", "vat": "34.238.864/0001-68"}
            )
            partner._onchange_vat()
            self._run_wizard(partner)

        self.assertEqual(partner.legal_name, "Regime Normal Ltda")
        self.assertEqual(partner.state_id.code, "MG")
        self.assertFalse(partner.phone)
        self.assertFalse(partner.mobile)
        self.assertEqual(partner.tax_framework, TAX_FRAMEWORK_NORMAL)

    def test_cpfcnpj_package_5(self):
        """A package 5 payload has no tax regime data, so tax_framework must be
        left untouched.
        """
        with (
            mock.patch(MOCK_REQUESTS_GET, return_value=mock.Mock(status_code=200)),
            mock.patch(
                MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_package5
            ),
        ):
            partner = self.model.create(
                {"name": "Dummy Package 5", "vat": "34.238.864/0001-68"}
            )
            tax_framework_before = partner.tax_framework
            partner._onchange_vat()
            self._run_wizard(partner)

        self.assertEqual(partner.legal_name, "Pacote Cinco Ltda")
        self.assertEqual(partner.tax_framework, tax_framework_before)

    @property
    def _webservice(self):
        return self.env["l10n_br_cnpj_search.webservice.abstract"]

    def test_cpfcnpj_api_url_default_package(self):
        """Without an explicit package the default (6) is used in the URL."""
        self.set_param("cpfcnpj_package", "")
        url = self._webservice.cpfcnpj_get_api_url("12345678000199")
        self.assertTrue(url.endswith("/6/12345678000199"))

    def test_cpfcnpj_state_city_without_uf(self):
        """With no UF and no IBGE code, state and city stay empty."""
        state_id, city_id = self._webservice._cpfcnpj_get_state_city({}, {})
        self.assertFalse(state_id)
        self.assertFalse(city_id)

    def test_cpfcnpj_state_city_without_city_name(self):
        """With a UF but no IBGE code and no city name, only the state resolves."""
        state_id, city_id = self._webservice._cpfcnpj_get_state_city({}, {"uf": "MG"})
        self.assertTrue(state_id)
        self.assertFalse(city_id)

    def test_cpfcnpj_phones_missing_fields(self):
        """Items missing ddd or numero are skipped instead of producing
        "(None) None"; the first complete item goes to phone.
        """
        phone, mobile = self._webservice._cpfcnpj_get_phones(
            {
                "telefones": [
                    {"ddd": None, "numero": "22334454"},
                    {"ddd": "11", "numero": None},
                    {"numero": "22334455"},
                    {"ddd": "11", "numero": "22334456"},
                ]
            }
        )
        self.assertEqual(phone, "(11) 22334456")
        self.assertFalse(mobile)

    def test_cpfcnpj_phones_all_incomplete(self):
        """When no item is complete, phone and mobile stay False."""
        phone, mobile = self._webservice._cpfcnpj_get_phones(
            {"telefones": [{"ddd": None, "numero": None}, {}, "invalid"]}
        )
        self.assertFalse(phone)
        self.assertFalse(mobile)

    def test_cpfcnpj_phones_without_list(self):
        """A payload without telefones (or with null) yields False for both."""
        self.assertEqual(self._webservice._cpfcnpj_get_phones({}), (False, False))
        self.assertEqual(
            self._webservice._cpfcnpj_get_phones({"telefones": None}), (False, False)
        )

    def test_cpfcnpj_secondary_cnae_unresolved(self):
        """A secondary CNAE that does not resolve is skipped."""
        result = self._webservice._cpfcnpj_get_secondary_cnae(
            {"cnae": {"secundarias": [{"id": "0000000"}]}}
        )
        self.assertEqual(result, [Command.set([])])

    def test_cpfcnpj_validate_error_without_message(self):
        """A status 0 without an error message still raises ValidationError."""
        response = mock.Mock(status_code=200)
        response.json.return_value = {"status": 0}
        with self.assertRaises(ValidationError):
            self._webservice.cpfcnpj_validate(response)

    def test_cpfcnpj_invalid(self):
        """An error payload (status 0) must raise a ValidationError."""
        with (
            mock.patch(
                MOCK_REQUESTS_GET,
                return_value=mock.Mock(
                    status_code=200,
                    **{
                        "json.return_value": {
                            "status": 0,
                            "erro": "CNPJ inválido!",
                            "erroCodigo": 100,
                        }
                    },
                ),
            ),
            self.assertRaises(ValidationError),
        ):
            invalid = self.model.create(
                {"name": "invalid", "vat": "00.000.000/0000-00"}
            )
            invalid._onchange_vat()
            action_wizard = invalid.action_open_cnpj_search_wizard()
            wizard_context = action_wizard.get("context")
            wizard_context["active_model"] = "res.partner"
            self.env["partner.search.wizard"].with_context(**wizard_context).create({})

    @mute_logger("odoo.addons.l10n_br_cnpj_search.wizard.partner_cnpj_search_wizard")
    def test_cpfcnpj_timeout(self):
        """A request timeout must raise a friendly UserError."""
        with (
            mock.patch(MOCK_REQUESTS_GET, side_effect=requests.exceptions.Timeout),
            self.assertRaises(UserError),
        ):
            partner = self.model.create(
                {"name": "Dummy Timeout", "vat": "34.238.864/0001-68"}
            )
            partner._onchange_vat()
            action_wizard = partner.action_open_cnpj_search_wizard()
            wizard_context = action_wizard.get("context")
            wizard_context["active_model"] = "res.partner"
            self.env["partner.search.wizard"].with_context(**wizard_context).create({})

    def _card_attachments(self, partner, cnpj_digits):
        return self.env["ir.attachment"].search(
            [
                ("res_model", "=", "res.partner"),
                ("res_id", "=", partner.id),
                ("name", "=", f"Cartao_CNPJ_{cnpj_digits}.pdf"),
            ]
        )

    def test_cpfcnpj_qsa_creates_children(self):
        """The QSA import creates one child partner per socio, with the right
        function and vat. A company partner identified only by its 8 digit CNPJ
        root gets no vat.
        """
        with (
            mock.patch(MOCK_REQUESTS_GET, return_value=mock.Mock(status_code=200)),
            mock.patch(MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_qsa),
        ):
            partner = self.model.create(
                {"name": "Dummy QSA", "vat": "13.347.016/0001-17"}
            )
            partner._onchange_vat()
            self._run_wizard(partner)

        children = partner.child_ids
        self.assertEqual(len(children), 3)

        maria = children.filtered(lambda c: c.name == "Maria Socia Exemplo")
        carlos = children.filtered(lambda c: c.name == "Carlos Socio Exemplo")
        holdings = children.filtered(lambda c: c.name == "Exemplo Holdings Llc")
        self.assertTrue(maria)
        self.assertTrue(carlos)
        self.assertTrue(holdings)

        self.assertEqual(maria.function, "Administrador")
        self.assertEqual(maria.company_type, "person")
        self.assertEqual(punctuation_rm(maria.vat or ""), "11144477735")
        self.assertEqual(punctuation_rm(carlos.vat or ""), "33366699957")

        # Company partner: only the 8 digit CNPJ root, so no vat, typed company.
        self.assertEqual(holdings.company_type, "company")
        self.assertFalse(holdings.vat)

    def test_cpfcnpj_qsa_rerun_reuses_partners(self):
        """Running the wizard again for the same company must not duplicate
        the QSA partners: the ones with a vat are found by vat and the one
        without a vat is found by name among the current children.
        """
        with (
            mock.patch(MOCK_REQUESTS_GET, return_value=mock.Mock(status_code=200)),
            mock.patch(MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_qsa),
        ):
            partner = self.model.create(
                {"name": "Dummy QSA Rerun", "vat": "13.347.016/0001-17"}
            )
            partner._onchange_vat()
            self._run_wizard(partner)
            first_ids = set(partner.child_ids.ids)
            self._run_wizard(partner)

        self.assertEqual(len(partner.child_ids), 3)
        self.assertEqual(set(partner.child_ids.ids), first_ids)
        self.assertEqual(
            self.model.search_count([("name", "=", "Maria Socia Exemplo")]), 1
        )
        self.assertEqual(
            self.model.search_count([("name", "=", "Exemplo Holdings Llc")]), 1
        )

    def test_cpfcnpj_qsa_skips_contact_of_other_company(self):
        """A QSA entry whose CPF already belongs to a contact of another
        company is skipped instead of being moved.
        """
        other = self.model.create({"name": "Outra Empresa", "company_type": "company"})
        self.model.create(
            {
                "name": "Maria Socia Exemplo",
                "vat": "11144477735",
                "company_type": "person",
                "parent_id": other.id,
            }
        )
        with (
            mock.patch(MOCK_REQUESTS_GET, return_value=mock.Mock(status_code=200)),
            mock.patch(MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_qsa),
        ):
            partner = self.model.create(
                {"name": "Dummy QSA Skip", "vat": "13.347.016/0001-17"}
            )
            partner._onchange_vat()
            self._run_wizard(partner)

        self.assertEqual(len(partner.child_ids), 2)
        self.assertNotIn("Maria Socia Exemplo", partner.child_ids.mapped("name"))
        self.assertEqual(other.child_ids.mapped("name"), ["Maria Socia Exemplo"])

    def test_cpfcnpj_qsa_disabled(self):
        """With cpfcnpj_skip_partners enabled, no child partner is created."""
        self.set_param("cpfcnpj_skip_partners", "True")
        with (
            mock.patch(MOCK_REQUESTS_GET, return_value=mock.Mock(status_code=200)),
            mock.patch(MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_qsa),
        ):
            partner = self.model.create(
                {"name": "Dummy QSA Off", "vat": "13.347.016/0001-17"}
            )
            partner._onchange_vat()
            self._run_wizard(partner)

        self.assertFalse(partner.child_ids)

    def test_cpfcnpj_card_attachment(self):
        """The CNPJ card PDF is stored as a pdf attachment on the partner and a
        second run replaces it instead of duplicating.
        """
        with (
            mock.patch(MOCK_REQUESTS_GET, return_value=mock.Mock(status_code=200)),
            mock.patch(MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_qsa),
        ):
            partner = self.model.create(
                {"name": "Dummy Card", "vat": "13.347.016/0001-17"}
            )
            partner._onchange_vat()
            self._run_wizard(partner)

        attachments = self._card_attachments(partner, "13347016000117")
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments.mimetype, "application/pdf")

        with (
            mock.patch(MOCK_REQUESTS_GET, return_value=mock.Mock(status_code=200)),
            mock.patch(MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_qsa),
        ):
            self._run_wizard(partner)

        self.assertEqual(len(self._card_attachments(partner, "13347016000117")), 1)

    def test_cpfcnpj_card_disabled(self):
        """With cpfcnpj_skip_card enabled, no card attachment is created."""
        self.set_param("cpfcnpj_skip_card", "True")
        with (
            mock.patch(MOCK_REQUESTS_GET, return_value=mock.Mock(status_code=200)),
            mock.patch(MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_qsa),
        ):
            partner = self.model.create(
                {"name": "Dummy Card Off", "vat": "13.347.016/0001-17"}
            )
            partner._onchange_vat()
            self._run_wizard(partner)

        self.assertFalse(self._card_attachments(partner, "13347016000117"))

    def test_cpfcnpj_status_baixada(self):
        """A closed company fills the registration status, date and reason."""
        with (
            mock.patch(MOCK_REQUESTS_GET, return_value=mock.Mock(status_code=200)),
            mock.patch(
                MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_baixada
            ),
        ):
            partner = self.model.create(
                {"name": "Dummy Baixada", "vat": "47.427.653/0073-90"}
            )
            partner._onchange_vat()
            self._run_wizard(partner)

        self.assertEqual(partner.cnpj_status, "Baixada")
        self.assertEqual(partner.cnpj_status_date, date(2021, 3, 1))
        self.assertEqual(
            partner.cnpj_status_reason,
            "Extincao Por Encerramento Liquidacao Voluntaria",
        )
        self.assertEqual(partner.opening_date, date(2006, 10, 25))
        self.assertEqual(partner.company_size, "Demais")
        self.assertEqual(partner.cnpj_branch_type, "head_office")

    def test_cpfcnpj_branch_filial(self):
        """A branch establishment fills cnpj_branch_type as branch."""
        with (
            mock.patch(MOCK_REQUESTS_GET, return_value=mock.Mock(status_code=200)),
            mock.patch(MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_filial),
        ):
            partner = self.model.create(
                {"name": "Dummy Filial", "vat": "48.412.392/0002-03"}
            )
            partner._onchange_vat()
            self._run_wizard(partner)

        self.assertEqual(partner.cnpj_branch_type, "branch")
        self.assertEqual(partner.company_size, "Micro Empresa")

    def test_cpfcnpj_ie_second_call(self):
        """With cpfcnpj_fetch_ie enabled a second request (package 16) fills
        l10n_br_ie_code with the active registration of the establishment UF.
        """
        self.set_param("cpfcnpj_fetch_ie", "1")
        # Isolate the feature under test from l10n_br_base IE format validation.
        self.env["ir.config_parameter"].sudo().set_param(
            "l10n_br_base.disable_ie_validation", "True"
        )
        main_response = mock.Mock(status_code=200)
        ie_response = mock.Mock(status_code=200)
        ie_response.json.return_value = self.mocked_response_cpfcnpj_ie
        with (
            mock.patch(MOCK_REQUESTS_GET, side_effect=[main_response, ie_response]),
            mock.patch(MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_qsa),
        ):
            partner = self.model.create(
                {"name": "Dummy IE", "vat": "13.347.016/0001-17"}
            )
            partner._onchange_vat()
            self._run_wizard(partner)

        self.assertEqual(punctuation_rm(partner.l10n_br_ie_code or ""), "123456789")

    @mute_logger("odoo.addons.l10n_br_cnpj_search.wizard.partner_cnpj_search_wizard")
    def test_cpfcnpj_ie_second_call_failure(self):
        """A failure on the state registration request must not break the main
        lookup; l10n_br_ie_code simply stays empty.
        """
        self.set_param("cpfcnpj_fetch_ie", "1")
        main_response = mock.Mock(status_code=200)
        with (
            mock.patch(
                MOCK_REQUESTS_GET,
                side_effect=[main_response, requests.exceptions.ConnectionError()],
            ),
            mock.patch(MOCK_VALIDATE, return_value=self.mocked_response_cpfcnpj_qsa),
        ):
            partner = self.model.create(
                {"name": "Dummy IE Fail", "vat": "13.347.016/0001-17"}
            )
            partner._onchange_vat()
            self._run_wizard(partner)

        self.assertFalse(partner.l10n_br_ie_code)

    def test_cpfcnpj_parse_date(self):
        """The date helper accepts both provider formats and rejects garbage."""
        parse = self._webservice._cpfcnpj_parse_date
        self.assertEqual(parse("2020-01-17"), date(2020, 1, 17))
        self.assertEqual(parse("17/01/2020"), date(2020, 1, 17))
        self.assertFalse(parse("not-a-date"))
        self.assertFalse(parse("31/02/2020"))
        self.assertFalse(parse(None))
        self.assertFalse(parse(""))
