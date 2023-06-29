# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from odoo.tests import SavepointCase

_module_ns = "odoo.addons.l10n_br_zip"
_provider_class = _module_ns + ".models.l10n_br_zip" + ".L10nBrZip"


class L10nBRZipTest(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.zip_obj = cls.env["l10n_br.zip"]
        cls.zip_1 = cls.zip_obj.create(
            dict(
                zip_code="01310923",
                city_id=cls.env.ref("l10n_br_base.city_3550308").id,
                state_id=cls.env.ref("base.state_br_sp").id,
                country_id=cls.env.ref("base.br").id,
                street_name="Avenida Paulista 1842",
                street_type="Avenida",
                district="Bela Vista",
            )
        )
        cls.res_partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        cls.res_partner_1 = cls.env["res.partner"].create(
            dict(
                name="teste",
                street_name="paulista",
                district="Bela Vista",
                country_id=cls.env.ref("base.br").id,
                state_id=cls.env.ref("base.state_br_sp").id,
                city_id=cls.env.ref("l10n_br_base.city_3550308").id,
            )
        )

    def test_without_all_required_fields(self):
        """Test object without all required fields in res.partner."""

        self.res_partner_1.street_name = False
        try:
            result = self.res_partner_1.zip_search()
        except Exception:
            result = False
        self.assertFalse(
            result, "Error to search by address without all required fields."
        )

    def test_search_zip_code_company(self):
        """Test search zip code in res_partner."""

        self.res_partner.zip = "01310923"
        self.res_partner.zip_search()
        self.assertEqual(
            self.res_partner.district,
            "Bela Vista",
            "Error in method zip_search to mapping field district.",
        )
        self.assertEqual(
            self.res_partner.street_name,
            "Avenida Avenida Paulista 1842",
            "Error in method zip_search to mapping field street_name.",
        )
        self.assertEqual(
            self.res_partner.city_id.name,
            "São Paulo",
            "Error in method zip_search to mapping field city.",
        )

    def test_search_zip_code_by_other_fields_company(self):
        """Test search by address in res_partner."""

        self.res_partner_1.street_name = False
        try:
            result = self.res_partner_1.zip_search()
        except Exception:
            result = False
        self.assertFalse(
            result, "Error to search by address without all required fields."
        )

        self.res_partner_1.street_name = "paulista"
        self.res_partner_1.zip_search()
        self.assertEqual(
            self.res_partner_1.zip,
            "01310-923",
            "Error in method zip_search to mapping zip code from fields"
            "country, state, city and street_name.",
        )

    def test_return_two_results_zip_search(self):
        """Test search by address return more the one result in res_partner."""

        self.zip_2 = self.zip_obj.create(
            dict(
                zip_code="01310940",
                city_id=self.env.ref("l10n_br_base.city_3550308").id,
                state_id=self.env.ref("base.state_br_sp").id,
                country_id=self.env.ref("base.br").id,
                street_name="Avenida Paulista 900",
                street_type="Avenida",
                district="Bela Vista",
            )
        )
        result = self.res_partner_1.zip_search()
        obj_zip_search = self.env["l10n_br.zip.search"].browse(result.get("res_id"))

        self.assertEqual(
            result["type"],
            "ir.actions.act_window",
            "It should return a action when there are more than one result",
        )
        self.assertEqual(
            result["res_model"],
            "l10n_br.zip.search",
            "It should return the model zip.search",
        )
        self.assertEqual(
            obj_zip_search.street_name,
            "paulista",
            "It should return the correct street_name",
        )
        self.assertEqual(
            obj_zip_search.state_id.id,
            self.env.ref("base.state_br_sp").id,
            "It should return the correct state",
        )
        self.assertEqual(
            len(obj_zip_search.zip_ids), 2, "It should return two Zip Codes."
        )

        # Test button/method 'New Search'
        obj_zip_search.zip_new_search()
        obj_zip_search.street_name = "900"
        result = obj_zip_search.zip_search()

        self.assertEqual(
            len(obj_zip_search.zip_ids), 1, "It should return one Zip Codes."
        )

        # Test button/method 'Zip Select'

        #  This code obj_zip_search.zip_ids.zip_select() doesn't work.
        #  In the tests context return empty, by this reason method
        #  zip_select don't receive fields address_id and object_name, what
        #  makes tests failed without with_context parameter. This problem
        #  only happening in the tests on screen doesn't.

        obj_zip_search.zip_ids.with_context(**result.get("context")).zip_select()

        self.assertEqual(
            self.res_partner_1.zip,
            "01310-940",
            "It should return the correct zip, failed method zip_select.",
        )
        self.assertEqual(
            self.res_partner_1.street_name,
            "Avenida Avenida Paulista 900",
            "It should return the correct street_name, failed method zip_select.",
        )

    def test_brazilcep_library(self):
        """Test with brazilcep library in partner."""

        self.res_partner.zip = "00000000"
        try:
            result = self.res_partner.zip_search()
        except Exception:
            result = False
        self.assertFalse(result, "Error to search by invalid ZIP on PyCEP-Correios.")

    def test_return_brazilcep_library(self):
        """Test search with brazilcep library in res_partner."""
        mocked_response = {
            "zip_code": "01310930",
            "street_name": "Avenida Paulista, 2100",
            "zip_complement": None,
            "district": "Bela Vista",
            "city_id": self.env.ref("l10n_br_base.city_3550308").id,
            "state_id": self.env.ref("base.state_br_sp").id,
            "country_id": self.env.ref("base.br").id,
        }

        self.res_partner.zip = "01310930"

        with mock.patch(
            _provider_class + "._consultar_cep",
            return_value=mocked_response,
        ):
            self.res_partner.zip_search()
        self.assertEqual(
            self.res_partner.district,
            "Bela Vista",
            "Error in method zip_search with PyCEP-Correios"
            "to mapping field district.",
        )
        self.assertEqual(
            self.res_partner.street_name,
            "Avenida Paulista",
            "Error in method zip_search with PyCEP-Correios"
            "to mapping field street_name.",
        )
        self.assertEqual(
            self.res_partner.city_id.name,
            "São Paulo",
            "Error in method zip_search with PyCEP-Correios" "to mapping field city.",
        )
