# @author Cristiano Mafra Junior
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date
from unittest import mock

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.l10n_br_cnpj_search.tests.common import (
    MOCK_REQUESTS_GET,
    TestCnpjCommon,
)


@tagged("post_install", "-at_install")
class TestOpenCNPJ(TestCnpjCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_param("cnpj_provider", "opencnpj")

    def test_opencnpj_success(self):
        knowledge = self.model.create(
            {
                "name": "Open Knowledge Brasil",
                "vat": "19.131.243/0001-97",
            }
        )

        with (
            mock.patch(
                MOCK_REQUESTS_GET,
                return_value=mock.Mock(status_code=200),
            ),
            mock.patch(
                "odoo.addons.l10n_br_cnpj_search.models.cnpj_webservice."
                "CNPJWebservice.validate",
                return_value=self.mocked_response_opencnpj_1,
            ),
        ):
            action_wizard = knowledge.action_open_cnpj_search_wizard()
            wizard_context = action_wizard.get("context")
            wizard_context["active_model"] = "res.partner"
            wizard = (
                self.env["partner.search.wizard"]
                .with_context(**wizard_context)
                .create({})
            )
            wizard.action_update_partner()

        self.assertEqual(knowledge.company_type, "company")
        self.assertEqual(knowledge.legal_name, "Open Knowledge Brasil")
        self.assertEqual(knowledge.name, "Rede Pelo Conhecimento Livre")
        self.assertEqual(knowledge.street_name, "Paulista")
        self.assertEqual(knowledge.street2, "Andar 4")
        self.assertEqual(knowledge.street_number, "37")
        self.assertEqual(knowledge.zip, "01311902")
        self.assertEqual(knowledge.district, "Bela Vista")
        self.assertEqual(knowledge.phone, "(11) 2385-1939")
        self.assertFalse(knowledge.mobile)
        self.assertEqual(knowledge.state_id.code, "SP")
        self.assertEqual(knowledge.equity_capital, 0)
        self.assertEqual(knowledge.legal_nature_id.code, "399-9")
        self.assertEqual(knowledge.cnae_main_id.code, "9430-8/00")
        self.assertEqual(knowledge.cnae_secondary_ids.mapped("code"), ["6204-0/00"])
        self.assertEqual(knowledge.registration_status, "ativa")
        self.assertEqual(knowledge.registration_status_reason, "Sem Motivo")
        self.assertEqual(knowledge.registration_status_date, date(2013, 10, 3))
        self.assertEqual(knowledge.company_start_date, date(2013, 10, 3))
        self.assertEqual(knowledge.company_size, "demais")
        self.assertEqual(knowledge.matrix_branch, "matriz")
        self.assertEqual(knowledge.legal_representative_qualification, "Presidente")
        self.assertEqual(knowledge.child_ids.mapped("name"), ["Haydee Svab"])
        self.assertEqual(knowledge.child_ids.company_type, "person")
        self.assertFalse(knowledge.child_ids.vat)

    def test_opencnpj_not_found(self):
        with (
            mock.patch(
                MOCK_REQUESTS_GET,
                return_value=mock.Mock(
                    status_code=404,
                    **{"json.return_value": {"error": "not found"}},
                ),
            ),
            self.assertRaises(ValidationError),
        ):
            invalido = self.model.create({"name": "invalido", "vat": "00000000000000"})
            invalido._onchange_vat()
            action_wizard = invalido.action_open_cnpj_search_wizard()
            wizard_context = action_wizard.get("context")
            wizard_context["active_model"] = "res.partner"
            self.env["partner.search.wizard"].with_context(**wizard_context).create({})

    def test_opencnpj_multiple_phones_skips_fax(self):
        with (
            mock.patch(
                MOCK_REQUESTS_GET,
                return_value=mock.Mock(status_code=200),
            ),
            mock.patch(
                "odoo.addons.l10n_br_cnpj_search.models.cnpj_webservice."
                "CNPJWebservice.validate",
                return_value=self.mocked_response_opencnpj_2,
            ),
        ):
            isla = self.model.create({"name": "Isla", "vat": "92.666.056/0001-06"})
            isla._onchange_vat()

            action_wizard = isla.action_open_cnpj_search_wizard()
            wizard_context = action_wizard.get("context")
            wizard_context["active_model"] = "res.partner"
            wizard = (
                self.env["partner.search.wizard"]
                .with_context(**wizard_context)
                .create({})
            )
            wizard.action_update_partner()
        self.assertEqual(isla.name, "Isla Sementes Ltda.")
        self.assertEqual(isla.phone, "(51) 9852-9561")
        self.assertEqual(isla.mobile, "(51) 2136-6600")
        self.assertEqual(isla.registration_status, "baixada")
        self.assertEqual(
            isla.registration_status_reason,
            "Extincao Por Encerramento Liquidacao Voluntaria",
        )
        self.assertEqual(isla.company_size, "me")
        self.assertEqual(isla.matrix_branch, "filial")
        self.assertEqual(isla.legal_representative_qualification, "Socio-Administrador")
        self.assertEqual(isla.child_ids.mapped("name"), ["Isla Sementes Holding Ltda"])
        self.assertEqual(isla.child_ids.company_type, "company")
        self.assertEqual(isla.child_ids.vat, "11222333000181")
