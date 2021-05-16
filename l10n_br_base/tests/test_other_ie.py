# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.tests import SavepointCase
from odoo.tools import mute_logger

_logger = logging.getLogger(__name__)


class OtherIETest(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_model = cls.env["res.company"]
        cls.company = cls.company_model.with_context(
            tracking_disable=True).create(
            {
                "name": "Akretion Sao Paulo",
                "legal_name": "Akretion Sao Paulo",
                "cnpj_cpf": "26.905.703/0001-52",
                "inscr_est": "932.446.119.086",
                "street": "Rua Paulo Dias",
                "street_number": "586",
                "district": "Alumínio",
                "state_id": cls.env.ref("base.state_br_sp"),
                "city_id": cls.env.ref("l10n_br_base.city_3501152"),
                "country_id": cls.env.ref("base.br"),
                "city": "Alumínio",
                "zip": "18125-000",
                "phone": "+55 (21) 3010 9965",
                "email": "contact@companytest.com.br",
                "website": "www.companytest.com.br",
            }
        )

    @mute_logger("odoo.sql_db")
    def test_included_valid_ie_in_company(cls):
        result = cls.company.write(
            {
                "state_tax_number_ids": [
                    (
                        0,
                        0,
                        {
                            "state_id": cls.env.ref("base.state_br_ba").id,
                            "inscr_est": 41902653,
                        },
                    )
                ]
            }
        )
        cls.assertTrue(result, "Error to included valid IE.")
        for line in cls.company.partner_id.state_tax_number_ids:
            result = False
            if line.inscr_est == "41902653":
                result = True
            cls.assertTrue(result, "Error in method to update other IE(s) on partner.")

        try:
            result = cls.company.write(
                {
                    "state_tax_number_ids": [
                        (
                            0,
                            0,
                            {
                                "state_id": cls.env.ref("base.state_br_ba").id,
                                "inscr_est": 67729139,
                            },
                        )
                    ]
                }
            )
        except Exception:
            result = False

        cls.assertFalse(
            result, "Error to check included other" " IE to State already informed."
        )

    def test_included_invalid_ie(cls):
        try:
            result = cls.company.write(
                {
                    "state_tax_number_ids": [
                        (
                            0,
                            0,
                            {
                                "state_id": cls.env.ref("base.state_br_am").id,
                                "inscr_est": "042933681",
                            },
                        )
                    ]
                }
            )
        except Exception:
            result = False
        cls.assertFalse(result, "Error to check included invalid IE.")

    def test_included_other_valid_ie_to_same_state_of_company(cls):
        try:
            result = cls.company.write(
                {
                    "state_tax_number_ids": [
                        (
                            0,
                            0,
                            {
                                "state_id": cls.env.ref("base.state_br_sp").id,
                                "inscr_est": 692015742119,
                            },
                        )
                    ]
                }
            )
        except Exception:
            result = False
        cls.assertFalse(
            result,
            "Error to check included other valid IE " " in to same state of Company.",
        )

    def test_included_valid_ie_on_partner(cls):
        result = cls.company.partner_id.write(
            {
                "state_tax_number_ids": [
                    (
                        0,
                        0,
                        {
                            "state_id": cls.env.ref("base.state_br_ba").id,
                            "inscr_est": 41902653,
                        },
                    )
                ]
            }
        )
        cls.assertTrue(result, "Error to included valid IE.")
        for line in cls.company.state_tax_number_ids:
            result = False
            if line.inscr_est == "41902653":
                result = True
            cls.assertTrue(result, "Error in method to update other IE(s) on Company.")
