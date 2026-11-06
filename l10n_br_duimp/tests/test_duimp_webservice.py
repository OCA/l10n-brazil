# Copyright (C) 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import time
from unittest.mock import patch

import requests as requests_lib
from erpbrasil.assinatura import misc

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_duimp.constants.duimp import (
    DUIMP_ENVIRONMENT_PRODUCTION,
    DUIMP_ENVIRONMENT_VALIDATION,
    DUIMP_ENVIRONMENTS,
    DUIMP_TOKEN_CACHE_SECONDS,
)
from odoo.addons.l10n_br_duimp.models.duimp_webservice import (
    DuimpInMemoryTokenStore,
    DuimpWebservice,
    DuimpWebserviceError,
)

MODULE_PATH = "odoo.addons.l10n_br_duimp.models.duimp_webservice"


class FakeCertificate:
    def cert_chave(self):
        return "FAKE CERT PEM", "FAKE KEY PEM"


class FakeResponse:
    def __init__(self, status_code=200, headers=None, json_data=None, text=""):
        self.status_code = status_code
        self.headers = headers or {}
        self._json_data = json_data
        self.text = text

    def json(self):
        return self._json_data


class FakeTokenStore:
    def __init__(self, cached=None):
        self.cached = cached
        self.saved = []

    def get(self):
        return self.cached

    def set(self, token, csrf_token):
        self.saved.append((token, csrf_token))
        self.cached = (token, csrf_token)


class TestDuimpWebservice(TransactionCase):
    def setUp(self):
        super().setUp()
        self.certificate = FakeCertificate()

    def test_environment_selection(self):
        cases = [
            (
                DUIMP_ENVIRONMENT_VALIDATION,
                DUIMP_ENVIRONMENTS[DUIMP_ENVIRONMENT_VALIDATION],
            ),
            (
                DUIMP_ENVIRONMENT_PRODUCTION,
                DUIMP_ENVIRONMENTS[DUIMP_ENVIRONMENT_PRODUCTION],
            ),
            ("unknown", DUIMP_ENVIRONMENTS[DUIMP_ENVIRONMENT_VALIDATION]),
        ]
        for environment, expected_url in cases:
            with self.subTest(environment=environment):
                webservice = DuimpWebservice(
                    certificate=self.certificate, environment=environment
                )
                self.assertEqual(webservice.base_url, expected_url)

    def test_authenticate_success(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        response = FakeResponse(
            status_code=200, headers={"Set-Token": "tok", "X-CSRF-Token": "csrf"}
        )
        cert_contents = []

        def fake_request(method, url, **kwargs):
            # ArquivoCertificado (erpbrasil.assinatura) removes the temp
            # PEM files as soon as its "with" block exits, so they must
            # be read here, while the request is still "in flight".
            cert_path, key_path = kwargs["cert"]
            with open(cert_path) as fp:
                cert_contents.append(fp.read())
            with open(key_path) as fp:
                cert_contents.append(fp.read())
            return response

        with patch(f"{MODULE_PATH}.requests.request", side_effect=fake_request):
            webservice._authenticate()

        self.assertEqual(webservice._token, "tok")
        self.assertEqual(webservice._csrf_token, "csrf")
        self.assertEqual(cert_contents, ["FAKE CERT PEM", "FAKE KEY PEM"])

    def test_authenticate_bad_status(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        response = FakeResponse(status_code=401, text="denied")
        with patch(f"{MODULE_PATH}.requests.request", return_value=response):
            with self.assertRaises(DuimpWebserviceError):
                webservice._authenticate()

    def test_authenticate_cooldown_gives_friendly_message(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        response = FakeResponse(
            status_code=422, text='{"code":"PLAT-ER2033","message":"..."}'
        )
        with patch(f"{MODULE_PATH}.requests.request", return_value=response):
            with self.assertRaises(DuimpWebserviceError) as capture:
                webservice._authenticate()
        self.assertIn("60 seconds", str(capture.exception))

    def test_authenticate_missing_headers(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        response = FakeResponse(status_code=200, headers={})
        with patch(f"{MODULE_PATH}.requests.request", return_value=response):
            with self.assertRaises(DuimpWebserviceError):
                webservice._authenticate()

    def test_auth_headers_reuses_existing_token(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        webservice._token = "tok"
        webservice._csrf_token = "csrf"
        with patch(f"{MODULE_PATH}.requests.request") as request_mock:
            headers = webservice._auth_headers()
        request_mock.assert_not_called()
        self.assertEqual(headers, {"Authorization": "tok", "X-CSRF-Token": "csrf"})

    def test_auth_headers_authenticates_when_missing_token(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        response = FakeResponse(
            status_code=200, headers={"Set-Token": "tok", "X-CSRF-Token": "csrf"}
        )
        with patch(f"{MODULE_PATH}.requests.request", return_value=response):
            headers = webservice._auth_headers()
        self.assertEqual(headers, {"Authorization": "tok", "X-CSRF-Token": "csrf"})

    def test_token_store_preloads_token_on_init(self):
        token_store = FakeTokenStore(cached=("cached-tok", "cached-csrf"))
        webservice = DuimpWebservice(
            certificate=self.certificate, token_store=token_store
        )
        with patch(f"{MODULE_PATH}.requests.request") as request_mock:
            headers = webservice._auth_headers()
        request_mock.assert_not_called()
        self.assertEqual(
            headers, {"Authorization": "cached-tok", "X-CSRF-Token": "cached-csrf"}
        )

    def test_authenticate_persists_to_token_store(self):
        token_store = FakeTokenStore()
        webservice = DuimpWebservice(
            certificate=self.certificate, token_store=token_store
        )
        response = FakeResponse(
            status_code=200, headers={"Set-Token": "tok", "X-CSRF-Token": "csrf"}
        )
        with patch(f"{MODULE_PATH}.requests.request", return_value=response):
            webservice._authenticate()
        self.assertEqual(token_store.saved, [("tok", "csrf")])

    def test_get_401_retries_once_then_succeeds(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        webservice._token = "stale-tok"
        webservice._csrf_token = "stale-csrf"
        responses = [
            FakeResponse(status_code=401, text="stale"),
            FakeResponse(
                status_code=200, headers={"Set-Token": "new", "X-CSRF-Token": "new"}
            ),
            FakeResponse(status_code=200, json_data={"ok": True}),
        ]
        with patch(
            f"{MODULE_PATH}.requests.request", side_effect=responses
        ) as request_mock:
            result = webservice._get("/x")
        self.assertEqual(result, {"ok": True})
        self.assertEqual(request_mock.call_count, 3)

    def test_get_401_twice_raises(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        webservice._token = "tok"
        webservice._csrf_token = "csrf"
        response = FakeResponse(status_code=401, text="denied")
        with patch(f"{MODULE_PATH}.requests.request", return_value=response):
            with self.assertRaises(DuimpWebserviceError):
                webservice._get("/x")

    def test_request_network_error(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        with patch(
            f"{MODULE_PATH}.requests.request",
            side_effect=requests_lib.exceptions.ConnectionError("boom"),
        ):
            with self.assertRaises(DuimpWebserviceError):
                webservice._request("GET", "/x")

    def test_get_error_statuses(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        webservice._token = "tok"
        webservice._csrf_token = "csrf"
        for status_code in (404, 500):
            with self.subTest(status_code=status_code):
                response = FakeResponse(status_code=status_code, text="error")
                with patch(f"{MODULE_PATH}.requests.request", return_value=response):
                    with self.assertRaises(DuimpWebserviceError):
                        webservice._get("/duimp/123")

    def test_get_not_found_returns_empty_when_requested(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        webservice._token = "tok"
        webservice._csrf_token = "csrf"
        response = FakeResponse(status_code=404, text="not found")
        with patch(f"{MODULE_PATH}.requests.request", return_value=response):
            result = webservice._get("/x", not_found_returns_empty=True)
        self.assertEqual(result, [])

    def test_get_success_status_codes(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        webservice._token = "tok"
        webservice._csrf_token = "csrf"
        for status_code in (200, 206):
            with self.subTest(status_code=status_code):
                response = FakeResponse(status_code=status_code, json_data={"ok": True})
                with patch(f"{MODULE_PATH}.requests.request", return_value=response):
                    result = webservice._get("/duimp/123")
                self.assertEqual(result, {"ok": True})

    def test_get_general_data_with_and_without_version(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        webservice._token = "tok"
        webservice._csrf_token = "csrf"
        response = FakeResponse(status_code=200, json_data={"identificacao": {}})
        cases = [
            (None, "/duimp-api/api/ext/duimp/26BR000/1"),
            (3, "/duimp-api/api/ext/duimp/26BR000/3"),
        ]
        for duimp_version, expected_suffix in cases:
            with self.subTest(duimp_version=duimp_version):
                with patch(
                    f"{MODULE_PATH}.requests.request", return_value=response
                ) as request_mock:
                    result = webservice.get_general_data("26BR000", duimp_version)
                self.assertEqual(result, {"identificacao": {}})
                called_url = request_mock.call_args.args[1]
                self.assertTrue(called_url.endswith(expected_suffix))

    def test_get_items_response_shapes(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        webservice._token = "tok"
        webservice._csrf_token = "csrf"
        cases = [
            ([{"a": 1}], [{"a": 1}]),
            ({"itens": [{"a": 1}]}, [{"a": 1}]),
            ({"content": [{"a": 1}]}, [{"a": 1}]),
            ({}, []),
        ]
        for json_data, expected in cases:
            with self.subTest(json_data=json_data):
                response = FakeResponse(status_code=200, json_data=json_data)
                with patch(f"{MODULE_PATH}.requests.request", return_value=response):
                    result = webservice.get_items("26BR000")
                self.assertEqual(result, expected)

    def test_get_items_with_version(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        webservice._token = "tok"
        webservice._csrf_token = "csrf"
        response = FakeResponse(status_code=200, json_data=[{"a": 1}])
        with patch(
            f"{MODULE_PATH}.requests.request", return_value=response
        ) as request_mock:
            result = webservice.get_items("26BR000", duimp_version=3)
        self.assertEqual(result, [{"a": 1}])
        called_url = request_mock.call_args.args[1]
        self.assertTrue(called_url.endswith("/duimp-api/api/ext/duimp/26BR000/3/itens"))

    def test_search_access_keys_by_importer_response_shapes(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        webservice._token = "tok"
        webservice._csrf_token = "csrf"
        cases = [
            ([{"numero": "1"}], [{"numero": "1"}]),
            ({"content": [{"numero": "1"}]}, [{"numero": "1"}]),
            ({}, []),
        ]
        for json_data, expected in cases:
            with self.subTest(json_data=json_data):
                response = FakeResponse(status_code=200, json_data=json_data)
                with patch(f"{MODULE_PATH}.requests.request", return_value=response):
                    result = webservice.search_access_keys_by_importer(
                        "12345678000190", "2026-01-01", "2026-03-01"
                    )
                self.assertEqual(result, expected)

    def test_search_access_keys_by_importer_404_returns_empty(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        webservice._token = "tok"
        webservice._csrf_token = "csrf"
        response = FakeResponse(status_code=404, text="not found")
        with patch(f"{MODULE_PATH}.requests.request", return_value=response):
            result = webservice.search_access_keys_by_importer(
                "12345678000190", "2026-01-01", "2026-03-01"
            )
        self.assertEqual(result, [])

    def test_search_access_keys_by_importer_builds_url_and_params(self):
        webservice = DuimpWebservice(certificate=self.certificate)
        webservice._token = "tok"
        webservice._csrf_token = "csrf"
        response = FakeResponse(status_code=200, json_data=[])
        with patch(
            f"{MODULE_PATH}.requests.request", return_value=response
        ) as request_mock:
            webservice.search_access_keys_by_importer(
                "12345678000190", "2026-01-01", "2026-03-01"
            )
        called_url = request_mock.call_args.args[1]
        self.assertTrue(
            called_url.endswith("/ext/duimp/chaves-acesso/importadores/12345678000190")
        )
        self.assertEqual(
            request_mock.call_args.kwargs["params"],
            {
                "data-inicio": "2026-01-01",
                "data-termino": "2026-03-01",
                "offset": 0,
                "limit": 100,
            },
        )


class TestResCompanyDuimpWebservice(TransactionCase):
    """Exercises the real (non-mocked) res.company._get_duimp_webservice()
    code path, using a locally-generated fake e-CPF certificate.

    The Portal Único Siscomex "Plataforma" auth module authenticates the
    natural person representing the company (e-CPF), not the company
    itself (e-CNPJ) - it rejects e-CNPJ for the IMPEXP profile used to
    query a DUIMP with HTTP 422, code PLAT-ER2008.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Company Test DUIMP Webservice",
                "cnpj_cpf": "42.245.642/0001-09",
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_sp").id,
            }
        )
        cert_file = misc.create_fake_certificate_file(
            valid=True,
            passwd="123456",
            issuer="EMISSOR TESTE",
            country="BR",
            subject="TITULAR TESTE",
        )
        certificate = cls.env["l10n_br_fiscal.certificate"].create(
            {
                "type": "e-cpf",
                "subtype": "a1",
                "password": "123456",
                "file": cert_file,
            }
        )
        cls.company.certificate_ecpf_id = certificate

    def test_get_duimp_webservice_default_environment(self):
        webservice = self.company._get_duimp_webservice()
        self.assertIsInstance(webservice, DuimpWebservice)
        self.assertEqual(
            webservice.base_url, DUIMP_ENVIRONMENTS[DUIMP_ENVIRONMENT_VALIDATION]
        )

    def test_get_duimp_webservice_production_environment(self):
        self.company.duimp_environment = DUIMP_ENVIRONMENT_PRODUCTION
        webservice = self.company._get_duimp_webservice()
        self.assertEqual(
            webservice.base_url, DUIMP_ENVIRONMENTS[DUIMP_ENVIRONMENT_PRODUCTION]
        )

    def test_get_duimp_webservice_sets_token_store(self):
        webservice = self.company._get_duimp_webservice()
        self.assertIsInstance(webservice.token_store, DuimpInMemoryTokenStore)
        self.assertEqual(
            webservice.token_store.key,
            f"{self.company.id}.{DUIMP_ENVIRONMENT_VALIDATION}",
        )


class TestDuimpInMemoryTokenStore(TransactionCase):
    def setUp(self):
        super().setUp()
        self.token_store = DuimpInMemoryTokenStore("test-key")
        self.addCleanup(DuimpInMemoryTokenStore._cache.pop, "test-key", None)

    def test_get_returns_none_when_not_set(self):
        self.assertIsNone(self.token_store.get())

    def test_set_then_get_round_trip(self):
        self.token_store.set("tok", "csrf")
        self.assertEqual(self.token_store.get(), ("tok", "csrf"))

    def test_get_returns_none_when_expired(self):
        stale_at = time.time() - (DUIMP_TOKEN_CACHE_SECONDS + 1)
        DuimpInMemoryTokenStore._cache["test-key"] = ("tok", "csrf", stale_at)
        self.assertIsNone(self.token_store.get())

    def test_cache_is_shared_across_instances_with_the_same_key(self):
        self.token_store.set("tok", "csrf")
        other_instance = DuimpInMemoryTokenStore("test-key")
        self.assertEqual(other_instance.get(), ("tok", "csrf"))

    def test_cache_is_isolated_per_key(self):
        self.token_store.set("tok", "csrf")
        other_key_store = DuimpInMemoryTokenStore("other-key")
        self.assertIsNone(other_key_store.get())
