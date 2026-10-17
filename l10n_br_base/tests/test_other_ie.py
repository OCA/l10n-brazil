# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase
from odoo.tools import mute_logger


class OtherIETest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_model = cls.env["res.company"]
        cls.company = cls.company_model.with_context(tracking_disable=True).create(
            {
                "name": "Akretion Sao Paulo",
                "legal_name": "Akretion Sao Paulo",
                "vat": "26.905.703/0001-52",
                "l10n_br_ie_code": "932.446.119.086",
                "street": "Rua Paulo Dias",
                "street_number": "586",
                "district": "Alumínio",
                "state_id": cls.env.ref("base.state_br_sp").id,
                "city_id": cls.env.ref("l10n_br_base.city_3501152").id,
                "country_id": cls.env.ref("base.br").id,
                "city": "Alumínio",
                "zip": "18125-000",
                "phone": "+55 (21) 3010 9965",
                "email": "contact@companytest.com.br",
                "website": "www.companytest.com.br",
            }
        )

    def _add_other_ie(self, record, state_xmlid, ie_code):
        return record.write(
            {
                "state_tax_number_ids": [
                    (
                        0,
                        0,
                        {
                            "state_id": self.env.ref(state_xmlid).id,
                            "l10n_br_ie_code": ie_code,
                        },
                    )
                ]
            }
        )

    def test_included_valid_ie_in_company(self):
        self._add_other_ie(self.company, "base.state_br_ba", 41902653)
        self.assertEqual(
            self.company.partner_id.state_tax_number_ids.mapped("l10n_br_ie_code"),
            ["41902653"],
            "Error in method to update other IE(s) on partner.",
        )
        # a second State Tax Number for the same state
        with (
            self.assertRaisesRegex(
                IntegrityError, "l10n_br_base_state_tax_numbers_id_uniq"
            ),
            mute_logger("odoo.sql_db"),
        ):
            self._add_other_ie(self.company, "base.state_br_ba", 67729139)

    def test_included_invalid_ie(self):
        with self.assertRaisesRegex(ValidationError, "Invalid for State"):
            self._add_other_ie(self.company, "base.state_br_am", "042933681")

    def test_included_other_valid_ie_to_same_state_of_company(self):
        with self.assertRaisesRegex(
            ValidationError, "only be one state tax number per state"
        ):
            self._add_other_ie(self.company, "base.state_br_sp", 692015742119)

    def test_included_valid_ie_on_partner(self):
        self._add_other_ie(self.company.partner_id, "base.state_br_ba", 41902653)
        self.assertEqual(
            self.company.state_tax_number_ids.mapped("l10n_br_ie_code"),
            ["41902653"],
            "Error in method to update other IE(s) on Company.",
        )
