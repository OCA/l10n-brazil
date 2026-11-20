# Copyright 2026 Engenere.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import contextlib
from datetime import datetime, timedelta
from unittest import mock

from xsdata.formats.dataclass.transports import DefaultTransport

import odoo.http
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal_dfe.constants.dfe import (
    DFE_INTERVAL_NO_DOCS,
    DFE_INTERVAL_RATE_LIMITED,
    DFE_INTERVAL_SUCCESS,
)
from odoo.addons.l10n_br_fiscal_dfe.controllers.main import DfeDocumentBannerController

from .common import (
    CTE_ACCESS_KEY,
    CTE_OS_ACCESS_KEY,
    GTVE_ACCESS_KEY,
    build_cte_dfe_response,
    cte_os_proc_xml,
    gtve_proc_xml,
    response_cte_and_cancel,
    response_cte_only,
    response_no_docs,
    response_rate_limited,
)


@contextlib.contextmanager
def mock_request(env):
    """Push a mock request onto Odoo's request stack."""
    request = mock.Mock()
    request.env = env
    request.session.debug = ""
    odoo.http._request_stack.push(request)
    try:
        yield request
    finally:
        odoo.http._request_stack.pop()


class TestCteDfe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company.cte_dfe_next_query = False

    def _dfe_records(self):
        return self.env["l10n_br_fiscal_dfe.dfe"].search(
            [("company_id", "=", self.company.id), ("fiscal_type", "=", "cte")]
        )

    def _documents(self):
        return self.env["l10n_br_fiscal_dfe.document"].search(
            [("company_id", "=", self.company.id), ("fiscal_type", "=", "cte")]
        )

    def _assert_within(self, value, expected, seconds=120):
        self.assertTrue(
            abs((value - expected).total_seconds()) <= seconds,
            f"{value} is not within {seconds}s of {expected}",
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_search_cte_and_cancellation(self, mock_post):
        mock_post.return_value = response_cte_and_cancel()

        self.company.cte_dfe_search_documents()

        mock_post.assert_called_once()
        self.assertEqual(self.company.cte_last_nsu, "000000000000101")
        self.assertEqual(self.company.cte_max_nsu, "000000000000101")
        self.assertEqual(self.company.cte_dfe_last_status_code, "138")
        self._assert_within(
            self.company.cte_dfe_next_query,
            fields.Datetime.now() + DFE_INTERVAL_SUCCESS,
        )

        records = self._dfe_records().sorted("nsu")
        self.assertEqual(len(records), 2)
        complete, event = records
        self.assertEqual(complete.schema_type, "procCTe")
        self.assertEqual(complete.document_type_dfe, "complete")
        self.assertEqual(complete.access_key, CTE_ACCESS_KEY)
        self.assertTrue(complete.attachment_id)
        self.assertEqual(event.schema_type, "procEventoCTe")
        self.assertEqual(event.document_type_dfe, "event")
        self.assertEqual(event.event_type_dfe, "110111")
        self.assertEqual(event.event_type_dfe_label, "Cancelamento")

        document = self._documents()
        self.assertEqual(len(document), 1)
        self.assertEqual(document.dfe_ids, records)
        self.assertEqual(document.emitter, "Empresa Simples Nacional")
        self.assertEqual(document.vat, "59.594.315/0001-57")
        self.assertEqual(document.serie, "1")
        self.assertEqual(document.document_number, "573")
        self.assertEqual(document.document_amount, 100.0)
        self.assertEqual(
            document.document_emission_date, datetime(2020, 1, 1, 11, 0, 0)
        )
        self.assertFalse(document.is_own_document)
        # The cancellation event is the only source of the situation.
        self.assertEqual(document.document_state, "3")
        self.assertEqual(document.document_state_label, "Cancelada")
        self.assertEqual(document.color_status, "muted")

    @mock.patch.object(DefaultTransport, "post")
    def test_request_targets_the_cte_national_service(self, mock_post):
        mock_post.return_value = response_cte_only()
        self.company.cte_environment = "2"

        self.company.cte_dfe_search_documents()

        args, kwargs = mock_post.call_args
        url = args[0] if args else kwargs["url"]
        data = (kwargs.get("data") or args[1]).decode("utf-8")
        self.assertIn("hom1.cte.fazenda.gov.br/CTeDistribuicaoDFe", url)
        self.assertIn("cteDistDFeInteresse", data)
        self.assertIn("cteDadosMsg", data)
        self.assertIn('xmlns="http://www.portalfiscal.inf.br/cte"', data)
        self.assertIn("<ultNSU>000000000000000</ultNSU>", data)
        self.assertNotIn("consChNFe", data)

        document = self._documents()
        self.assertEqual(document.document_state, "1")
        self.assertEqual(document.document_state_label, "Autorizada")
        self.assertEqual(document.color_status, "green")

    @mock.patch.object(DefaultTransport, "post")
    def test_no_documents_137(self, mock_post):
        mock_post.return_value = response_no_docs()

        self.company.cte_dfe_search_documents()

        self.assertFalse(self._dfe_records())
        self.assertEqual(self.company.cte_dfe_last_status_code, "137")
        self._assert_within(
            self.company.cte_dfe_next_query,
            fields.Datetime.now() + DFE_INTERVAL_NO_DOCS,
        )
        log = self.env["l10n_br_fiscal_dfe.distribution_log"].search(
            [("company_id", "=", self.company.id)], order="id desc", limit=1
        )
        self.assertEqual(log.log_type, "info")
        self.assertIn("cteDistDFeInteresse", log.request_xml)

    @mock.patch.object(DefaultTransport, "post")
    def test_rate_limited_656(self, mock_post):
        mock_post.return_value = response_rate_limited()

        self.company.cte_dfe_search_documents()

        self.assertEqual(self.company.cte_dfe_last_status_code, "656")
        self.assertEqual(self.company.cte_last_nsu, "000000000000300")
        self._assert_within(
            self.company.cte_dfe_next_query,
            fields.Datetime.now() + DFE_INTERVAL_RATE_LIMITED,
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_same_nsu_is_not_duplicated(self, mock_post):
        mock_post.return_value = response_cte_and_cancel()

        self.company.cte_dfe_search_documents()
        self.company.cte_dfe_next_query = False
        self.company.cte_last_nsu = "0"
        self.company.cte_dfe_search_documents()

        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(len(self._dfe_records()), 2)
        self.assertEqual(len(self._documents()), 1)

    @mock.patch.object(DefaultTransport, "post")
    def test_cooldown_blocks_manual_search(self, mock_post):
        self.company.cte_dfe_next_query = fields.Datetime.now() + timedelta(hours=1)
        self.company.cte_dfe_last_status_code = "656"

        result = self.company.with_company(self.company).action_banner_search_all_cte()

        mock_post.assert_not_called()
        self.assertEqual(result["tag"], "display_notification")
        self.assertIn("656", result["params"]["title"])

    @mock.patch.object(DefaultTransport, "post")
    def test_specific_search_by_nsu(self, mock_post):
        mock_post.return_value = response_cte_only()
        action = self.company.action_search_specific("cte")
        wizard = (
            self.env["dfe.specific.search.wizard"]
            .with_context(**action["context"])
            .create({})
        )
        # No consChCTe in the CT-e service: the wizard defaults to NSU.
        self.assertEqual(wizard.fiscal_type, "cte")
        self.assertEqual(wizard.search_type, "nsu")

        wizard.nsu = "100"
        wizard.action_confirm_search()

        _, kwargs = mock_post.call_args
        self.assertIn(
            "<consNSU><NSU>000000000000100</NSU></consNSU>",
            kwargs["data"].decode("utf-8"),
        )
        record = self._dfe_records()
        self.assertEqual(record.nsu, "000000000000100")
        self.assertEqual(record.access_key, CTE_ACCESS_KEY)

    def test_specific_search_by_access_key_is_refused(self):
        wizard = self.env["dfe.specific.search.wizard"].create(
            {
                "company_id": self.company.id,
                "fiscal_type": "cte",
                "search_type": "access_key",
                "access_key": CTE_ACCESS_KEY,
            }
        )
        with self.assertRaisesRegex(UserError, "NSU"):
            wizard.action_confirm_search()

    @mock.patch.object(DefaultTransport, "post")
    def test_other_cte_family_documents(self, mock_post):
        mock_post.return_value = build_cte_dfe_response(
            [
                ("000000000000200", "procCTeOS_v4.00.xsd", cte_os_proc_xml()),
                ("000000000000201", "procGTVe_v4.00.xsd", gtve_proc_xml()),
            ],
            ult_nsu="000000000000201",
            max_nsu="000000000000201",
        )

        self.company.cte_dfe_search_documents()

        documents = self._documents()
        self.assertEqual(len(documents), 2)
        cte_os = documents.filtered(lambda d: d.access_key == CTE_OS_ACCESS_KEY)
        gtve = documents.filtered(lambda d: d.access_key == GTVE_ACCESS_KEY)
        self.assertEqual(cte_os.dfe_ids.schema_type, "procCTeOS")
        self.assertEqual(cte_os.document_number, "12")
        self.assertEqual(cte_os.document_amount, 250.0)
        self.assertEqual(cte_os.color_status, "green")
        self.assertEqual(gtve.dfe_ids.schema_type, "procGTVe")
        self.assertEqual(gtve.document_number, "5")
        self.assertEqual(gtve.document_amount, 0.0)
        # Only the CT-e model 57 is importable and has a DACTE.
        with self.assertRaisesRegex(UserError, "procCTeOS"):
            cte_os.import_document()
        with self.assertRaisesRegex(UserError, "procGTVe"):
            gtve.make_pdf()

    @mock.patch.object(DefaultTransport, "post")
    def test_cron_follows_next_query(self, mock_post):
        mock_post.return_value = response_no_docs()
        self.company.cte_auto_fetch = True
        cron = self.env.ref("l10n_br_cte_dfe.ir_cron_search_cte_dfe_documents")

        self.company.cte_dfe_search_documents()

        self.assertEqual(cron.nextcall, self.company.cte_dfe_next_query)

    @mock.patch.object(DefaultTransport, "post")
    def test_banner(self, mock_post):
        mock_post.return_value = response_cte_only()
        self.company.cte_environment = "2"
        self.company.cte_dfe_search_documents()

        env = self.env(context={"allowed_company_ids": [self.company.id]})
        with mock_request(env):
            html = DfeDocumentBannerController().document_banner("cte")["html"]

        self.assertIn("action_banner_search_all_cte", html)
        self.assertIn("Homologa", html)
        self.assertIn("Synced", html)
        # 1 procCTe not imported → pending count uses text-warning style
        self.assertIn("text-warning", html)
