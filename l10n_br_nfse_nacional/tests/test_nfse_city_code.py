# Copyright 2026 Pop Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase

from ..models.document import _nfse10_city_code
from .common import set_provedor_nacional


class TestNfseCityCode(TransactionCase):
    """cTribMun is the 3 digit municipal complement of cTribNac.

    Cities such as Barueri publish their service list as cTribNac followed by
    the complement (140101 + 220), and their own webservices expect the 9
    digits, so the city taxation code may hold the whole code.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document = cls.env.ref("l10n_br_nfse_nacional.demo_nfse_lc")
        set_provedor_nacional(cls.document)
        cls.line = cls.document.fiscal_line_ids[0]
        cls.national_code = cls.env["l10n_br_fiscal.national.taxation.code"].create(
            {"code": "140101", "name": "Manutencao de equipamentos"}
        )

    def _city_code(self, code):
        return self.env["l10n_br_fiscal.city.taxation.code"].create(
            {"code": code, "name": f"Codigo municipal {code}"}
        )

    def test_a_three_digit_code_is_declared_as_is(self):
        self.assertEqual(_nfse10_city_code("220", "140101"), "220")

    def test_a_code_embedding_the_national_code_declares_the_complement(self):
        self.assertEqual(_nfse10_city_code("140101220", "140101"), "220")

    def test_a_code_that_is_not_a_complement_is_left_out(self):
        self.assertIsNone(_nfse10_city_code("1234", "140101"))
        self.assertIsNone(_nfse10_city_code("990101220", "140101"))
        self.assertIsNone(_nfse10_city_code("140101220", False))
        self.assertIsNone(_nfse10_city_code(False, "140101"))

    def test_the_dps_declares_the_complement_of_a_barueri_code(self):
        self.line.write(
            {
                "national_taxation_code_id": self.national_code.id,
                "city_taxation_code_id": self._city_code("140101220").id,
            }
        )
        self.document._prepare_nfse10_service()
        self.assertEqual(self.document.nfse10_cTribNac, "140101")
        self.assertEqual(self.document.nfse10_cTribMun, "220")
