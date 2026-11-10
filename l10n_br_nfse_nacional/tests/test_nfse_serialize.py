# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os

from nfelib.nfse.bindings.v1_0.tipos_complexos_v1_01 import TcinfDps
from xmldiff import main
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from odoo.tests.common import TransactionCase, tagged

from odoo.addons import l10n_br_nfse_nacional

from .common import set_provedor_nacional

_logger = logging.getLogger(__name__)

# The expected DPS of each fixture is the golden document of a demo document.
# Its data is declared here and applied right before the export instead of
# being inherited from the demo data: the demo companies and lines are shared
# with the other localisation modules of the repository, and several of the
# values the fixtures encode are computed fields (the national taxation code,
# the NBS code, the service city and the withheld INSS of the line, the
# document_serie of the document) that a recomputation silently resets.
DPS_FIXTURES = {
    "l10n_br_nfse_nacional.demo_nfse_lc": {
        # outside the Simples Nacional: totTrib is declared in pTotTrib
        "company": {"tax_framework": "3", "nfse_environment": "2"},
        # document_serie is a stored compute of the serie: its code is what
        # must be set, writing document_serie loses against a recomputation
        "serie_code": "00007",
        "document": {
            "document_key": "420240420000000000000000007000000000000002",
            "document_serie": "00007",
            "document_number": "2",
        },
        "line": {
            "national_taxation_code_id": ("l10n_br_nfse_nacional.nat_tax_code_010101"),
            "nbs_id": "l10n_br_nfse_nacional.nbs_111111111",
            "issqn_fg_city_id": "l10n_br_base.city_4202404",
            "price_unit": 20.0,
            "quantity": 1,
            "discount_value": 0.0,
            "issqn_desc_cond_amount": 0.0,
            "inss_wh_value": 0.4,
        },
    },
    "l10n_br_nfse_nacional.demo_nfse_sn": {
        # Simples Nacional: totTrib is declared in pTotTribSN
        "company": {"tax_framework": "1", "nfse_environment": "2"},
        "simplified_tax_range_percent": 11.2,
        "serie_code": "900",
        "document": {
            "document_key": "140015920176113500013200900000000000000006",
            "document_serie": "900",
            "document_number": "6",
        },
        "line": {
            "national_taxation_code_id": ("l10n_br_nfse_nacional.nat_tax_code_010101"),
            "issqn_fg_city_id": "l10n_br_base.city_1400159",
            "price_unit": 999999999.99,
            "quantity": 1,
            "discount_value": 9999999.99,
            "issqn_desc_cond_amount": 9.99,
        },
    },
}


# The export builds the remaining spec models on the fly, which must not happen
# inside an at_install test transaction: it would roll back their tables.
@tagged("post_install", "-at_install")
class TestNfseSerialize(TransactionCase):
    @classmethod
    def setUpClass(cls, nfse_list=None):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.nfse_list = []
        for nfse_data in nfse_list or []:
            # Only append if the demo data exists in the database
            nfse = cls.env.ref(nfse_data["record_ref"], raise_if_not_found=False)
            if nfse:
                nfse_data["nfse"] = nfse
                cls.nfse_list.append(nfse_data)
                set_provedor_nacional(nfse)

    def setUp(self):
        super().setUp()
        if not self.nfse_list:
            self.skipTest("l10n_br_nfse_nacional demo data is not installed")

    def _declare_fixture_data(self, nfse_data):
        """Declare the data the expected DPS of the fixture encodes."""
        expected = DPS_FIXTURES.get(nfse_data["record_ref"], {})
        nfse = nfse_data["nfse"]
        if expected.get("company"):
            nfse.company_id.write(expected["company"])
        percent = expected.get("simplified_tax_range_percent")
        if percent:
            tax_range = self.env["l10n_br_fiscal.simplified.tax.range"].search(
                [("total_tax_percent", "=", percent)], limit=1
            )
            if tax_range:
                nfse.company_id.simplified_tax_range_id = tax_range
        if expected.get("serie_code") and nfse.document_serie_id:
            nfse.document_serie_id.code = expected["serie_code"]
        if expected.get("document"):
            nfse.write(expected["document"])
        # the line comes last: writing on the company recomputes its taxes
        line_values = dict(expected.get("line") or {})
        for field_name in (
            "national_taxation_code_id",
            "nbs_id",
            "issqn_fg_city_id",
        ):
            xml_id = line_values.get(field_name)
            if not xml_id:
                continue
            record = self.env.ref(xml_id, raise_if_not_found=False)
            if record:
                line_values[field_name] = record.id
            else:
                line_values.pop(field_name)
        if line_values:
            nfse.fiscal_line_ids.write(line_values)

    def serialize_xml(self, nfse_data):
        nfse = nfse_data["nfse"]
        self._declare_fixture_data(nfse_data)

        # Set namespace on binding class to avoid ns1 prefixes in XML output
        # TODO should not be required...
        TcinfDps.Meta.namespace = "http://www.sped.fazenda.gov.br/nfse"

        binding = nfse._serialize([])[0]
        serializer = XmlSerializer(config=SerializerConfig(indent="  "))
        xml_output = serializer.render(
            obj=binding, ns_map={None: "http://www.sped.fazenda.gov.br/nfse"}
        )

        expected_path = os.path.join(
            l10n_br_nfse_nacional.__path__[0],
            "tests",
            "nfse",
            "v1_00",
            "DPS",
            nfse_data["xml_file"],
        )
        with open(expected_path, "rb") as expected:
            diff = main.diff_texts(xml_output.encode(), expected.read())
        if diff:
            # a bare assertion count in a CI log says nothing about what moved
            _logger.info("Diff with expected XML (if any): %s", diff)
        return diff
