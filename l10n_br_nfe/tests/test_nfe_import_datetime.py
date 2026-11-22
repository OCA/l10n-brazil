# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os

from xsdata.formats.dataclass.parsers import XmlParser

from odoo import fields
from odoo.tests import TransactionCase

from odoo.addons import l10n_br_nfe

SAMPLE = "NFe35200181583054000129550010000000052062777166.xml"
SAMPLE_DH = b"2020-01-01T12:00:00+01:00"


class TestNFeImportDatetime(TransactionCase):
    """The issue date of an imported NF-e keeps the instant it carries.

    The XML has the local time with an offset, the Datetime fields keep UTC.
    The test goes through the import of the spec (``build_from_binding``), which every
    importer of the localization uses, so it holds whatever the path that reads the
    file: it does not depend on the wizard nor on the service of import.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.env.user.tz = "America/Sao_Paulo"
        path = os.path.join(
            l10n_br_nfe.__path__[0], "tests", "nfe", "v4_00", "leiauteNFe", SAMPLE
        )
        with open(path, "rb") as f:
            cls.xml = f.read()

    def _import(self, dh_emi, dh_sai_ent=None):
        """Build the document from the binding of the file, as every importer does:
        the conversion is a matter of the import of the spec, not of one importer."""
        xml = self.xml.replace(SAMPLE_DH, dh_emi.encode(), 1)
        xml = xml.replace(SAMPLE_DH, (dh_sai_ent or dh_emi).encode(), 1)
        self.assertNotIn(SAMPLE_DH, xml)
        binding = XmlParser().from_bytes(xml)
        binding = getattr(binding, "NFe", binding)
        return (
            self.env["nfe.40.infnfe"]
            .with_context(tracking_disable=True, edoc_type="in")
            .build_from_binding("nfe", "40", binding.infNFe)
        )

    def _local(self, document, field="document_date"):
        return fields.Datetime.context_timestamp(document, document[field])

    def test_issue_at_the_start_of_the_month(self):
        """01:00 in Brasilia on the 1st is 04:00 UTC on the 1st."""
        document = self._import("2020-01-01T01:00:00-03:00")
        self.assertEqual(str(document.document_date), "2020-01-01 04:00:00")
        local = self._local(document)
        self.assertEqual(local.strftime("%Y-%m-%d %H:%M"), "2020-01-01 01:00")

    def test_issue_at_night_changes_the_day_in_utc_only(self):
        """22:30 in Brasilia is 01:30 UTC of the next day, same day for the user."""
        document = self._import("2020-01-15T22:30:00-03:00")
        self.assertEqual(str(document.document_date), "2020-01-16 01:30:00")
        local = self._local(document)
        self.assertEqual(local.strftime("%Y-%m-%d %H:%M"), "2020-01-15 22:30")

    def test_departure_date_is_converted_too(self):
        document = self._import(
            "2020-01-10T08:00:00-03:00", dh_sai_ent="2020-01-11T23:15:00-03:00"
        )
        self.assertEqual(str(document.date_in_out), "2020-01-12 02:15:00")

    def test_issue_in_the_time_zone_of_the_amazon(self):
        """-04:00 (MT and AM) is not the same shift as Brasilia."""
        document = self._import("2020-01-01T01:00:00-04:00")
        self.assertEqual(str(document.document_date), "2020-01-01 05:00:00")

    def test_export_gives_back_the_imported_time(self):
        """What is imported with an offset is exported with the user offset."""
        document = self._import("2020-01-01T01:00:00-03:00")
        self.assertEqual(
            document._export_datetime("document_date"), "2020-01-01T01:00:00-03:00"
        )
