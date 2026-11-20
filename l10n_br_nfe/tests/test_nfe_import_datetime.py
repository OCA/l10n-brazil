# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os

from odoo import fields
from odoo.tests import TransactionCase

from odoo.addons import l10n_br_nfe

SAMPLE = "NFe35200181583054000129550010000000052062777166.xml"
SAMPLE_DH = b"2020-01-01T12:00:00+01:00"


class TestNFeImportDatetime(TransactionCase):
    """The issue date of an imported NF-e keeps the instant it carries.

    The XML has the local time with an offset, the Datetime fields keep UTC.
    The key of the sample belongs to 2020-01, so the issue date has to be in
    January for the user, whatever the hour.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.env.user.tz = "America/Sao_Paulo"
        # the check of the key against the issue date only runs with the processor
        cls.env.company.processador_edoc = "oca"
        path = os.path.join(
            l10n_br_nfe.__path__[0], "tests", "nfe", "v4_00", "leiauteNFe", SAMPLE
        )
        with open(path, "rb") as f:
            cls.xml = f.read()

    def _import(self, dh_emi, dh_sai_ent=None):
        xml = self.xml.replace(SAMPLE_DH, dh_emi.encode(), 1)
        xml = xml.replace(SAMPLE_DH, (dh_sai_ent or dh_emi).encode(), 1)
        self.assertNotIn(SAMPLE_DH, xml)
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "file": base64.b64encode(xml),
            }
        )
        wizard._onchange_file()
        wizard._import_edoc()
        return wizard.document_id

    def _local(self, document, field="document_date"):
        return fields.Datetime.context_timestamp(document, document[field])

    def test_issue_at_the_start_of_the_month(self):
        """01:00 in Brasilia on the 1st is 04:00 UTC on the 1st."""
        document = self._import("2020-01-01T01:00:00-03:00")
        self.assertEqual(str(document.document_date), "2020-01-01 04:00:00")
        local = self._local(document)
        self.assertEqual(local.strftime("%Y-%m-%d %H:%M"), "2020-01-01 01:00")

    def test_issue_at_the_start_of_the_month_passes_the_key_check(self):
        """The key says 2020-01: confirming checks it against the issue date."""
        document = self._import("2020-01-01T01:00:00-03:00")
        document.action_document_confirm()
        self.assertEqual(document.state_edoc, "autorizada")

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
