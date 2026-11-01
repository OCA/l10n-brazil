# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from unittest.mock import patch

from brbank.erros import Indisponivel, Validacao

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged

from ..utils.token_store import OdooTokenStore
from .common import ConnectionCommon
from .fake_bank import FAKE, FAKE_NO_SANDBOX, STATE, reset_state

SECRET_FIELDS = (
    "client_id",
    "client_secret",
    "username",
    "password",
    "certificate",
    "private_key",
    "pix_key",
    "refresh_token",
    "extra_config",
    "secret_config",
    "webhook_token",
    "webhook_url",
)


@tagged("post_install", "-at_install")
class TestConnection(ConnectionCommon, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_connection()

    def setUp(self):
        super().setUp()
        reset_state()
        self.connection = self._create_connection()

    def _ping_fails(self, error_type):
        """Not `assertRaises`: the Odoo one rolls back a savepoint, and with
        it the state the failed call just recorded."""
        try:
            self._ping()
        except error_type:
            return
        self.fail("the call should have failed")

    def _ping(self, connection=None):
        return (connection or self.connection)._l10n_br_bank_run(
            lambda adapter: adapter.ping()
        )

    # === configuration === #

    def test_cnpj_defaults_to_the_company(self):
        with patch.object(
            type(self.Connection),
            "_l10n_br_bank_company_cnpj",
            lambda self, company: "91300766000147",
        ):
            connection = self.Connection.create(
                {"name": "No CNPJ", "adapter": FAKE, "company_id": self.env.company.id}
            )
        self.assertEqual(connection.cnpj, "91300766000147")

    def test_config_built_from_the_connection(self):
        _adapter_class, config = self.connection._l10n_br_bank_prepare_adapter()
        self.assertEqual(config.conta, f"odoo-connection-{self.connection.id}")
        self.assertEqual(config.ambiente, "sandbox")
        self.assertEqual(config.cnpj_empresa, "91300766000147")
        self.assertNotIn("client-secret", repr(config))
        self.connection.environment = "prod"
        _adapter_class, config = self.connection._l10n_br_bank_prepare_adapter()
        self.assertEqual(config.ambiente, "producao")

    def test_url_overrides_reach_the_config(self):
        self.connection.api_base_url_override = "http://localhost:8899"
        _adapter_class, config = self.connection._l10n_br_bank_prepare_adapter()
        self.assertEqual(config.url_base_override, "http://localhost:8899")

    def test_token_store_and_callbacks_are_served(self):
        _adapter_class, config = self.connection._l10n_br_bank_prepare_adapter()
        self.assertIsInstance(config.armazem, OdooTokenStore)
        self.assertEqual(config.armazem.connection_id, self.connection.id)
        self.assertTrue(callable(config.ao_renovar_refresh_token))
        # Not committed: own cursors cannot see the row.
        self.connection.refresh_token = "rt-1"
        _adapter_class, config = self.connection._l10n_br_bank_prepare_adapter()
        self.assertEqual(config.ler_refresh_token(), "rt-1")
        self.assertEqual(config.refresh_token, "rt-1")

    def test_callable_keys_never_come_from_the_settings(self):
        self.connection.action_fill_settings_template()
        settings = json.loads(self.connection.extra_config)
        settings.update(json.loads(self.connection.secret_config))
        for name in ("armazem", "ler_refresh_token", "ao_renovar_refresh_token"):
            self.assertNotIn(name, settings)
        with self.assertRaisesRegex(ValidationError, "armazem"):
            self.connection.extra_config = json.dumps({"armazem": "x"})

    def test_secret_typed_in_public_settings_is_refused(self):
        with self.assertRaisesRegex(ValidationError, "unknown or invalid"):
            self.connection.extra_config = json.dumps({"nope": 1})

    def test_invalid_json_is_refused(self):
        with self.assertRaises(ValidationError):
            self.connection.extra_config = "{not json"
        with self.assertRaises(ValidationError):
            self.connection.secret_config = "[1, 2]"

    def test_draft_may_be_incomplete_connected_may_not(self):
        draft = self._create_connection(client_secret=False)
        self.assertEqual(draft.state, "draft")
        with self.assertRaisesRegex(ValidationError, "client_secret"):
            draft.state = "connected"

    def test_adapter_without_test_environment_refuses_test(self):
        connection = self._create_connection(
            adapter=FAKE_NO_SANDBOX, environment="prod", client_secret=False
        )
        with self.assertRaisesRegex(ValidationError, "no test environment"):
            connection.environment = "test"

    def test_rotate_webhook_token(self):
        old_url = self.connection.webhook_url
        self.assertIn(
            f"/l10n_br_bank_connection/webhook/{self.connection.id}/", old_url
        )
        self.connection.action_rotate_webhook_token()
        self.assertNotEqual(self.connection.webhook_url, old_url)

    # === calls to the bank === #

    def test_run_uses_the_adapter_and_marks_connected(self):
        self.assertEqual(self.connection.state, "draft")
        self.assertEqual(self._ping(), "ok")
        self.assertEqual(len(STATE["configs"]), 1)
        self.assertEqual(self.connection.state, "connected")
        self.assertFalse(self.connection.last_error)

    def test_run_success_clears_a_previous_error(self):
        self.connection.write({"state": "error", "last_error": "old"})
        self._ping()
        self.assertEqual(self.connection.state, "connected")
        self.assertFalse(self.connection.last_error)

    def test_token_refusal_marks_the_connection(self):
        STATE["error"] = Validacao("credenciais recusadas ao obter token")
        self._ping_fails(Validacao)
        self.assertEqual(self.connection.state, "error")
        self.assertIn("credenciais", self.connection.last_error)

    def test_token_refusal_asks_for_consent_where_oauth_applies(self):
        STATE["error"] = Validacao("credenciais recusadas ao obter token")
        self.connection.state = "connected"
        with patch.object(
            type(self.connection),
            "_l10n_br_bank_oauth_functions",
            lambda self: (None, None),
        ):
            self.connection.invalidate_recordset()
            self._ping_fails(Validacao)
        self.assertEqual(self.connection.state, "needs_reconsent")

    def test_refused_title_or_bank_down_keep_the_state(self):
        self.connection.state = "connected"
        for error in (Validacao("title refused"), Indisponivel("token down")):
            STATE["error"] = error
            self._ping_fails(type(error))
            self.assertEqual(self.connection.state, "connected")
            self.assertTrue(self.connection.last_error)

    def test_parsing_does_not_touch_the_state(self):
        self.connection._l10n_br_bank_run(
            lambda adapter: adapter.parse_webhook(b"[]"), record=False
        )
        self.assertEqual(self.connection.state, "draft")

    def test_archived_connection_does_not_call_the_bank(self):
        self.connection.active = False
        with self.assertRaisesRegex(UserError, "archived"):
            self._ping()
        self.assertFalse(STATE["configs"])

    def test_caller_callbacks_reach_the_config(self):
        def hook(titulo):
            return "x"

        self.connection._l10n_br_bank_run(
            lambda adapter: None, callbacks={"ler_refresh_token": hook, "nope": hook}
        )
        self.assertIs(STATE["configs"][0].ler_refresh_token, hook)

    # === hooks for the domains === #

    def test_sync_report_keeps_one_row_per_domain(self):
        self.connection._l10n_br_bank_sync_report("dda", True, "12 debits")
        self.connection._l10n_br_bank_sync_report("dda", "warning", "slow")
        self.connection._l10n_br_bank_sync_report("collection", False, "down")
        rows = {row.domain: row for row in self.connection.sync_status_ids}
        self.assertEqual(set(rows), {"dda", "collection"})
        self.assertEqual(rows["dda"].state, "warning")
        self.assertEqual(rows["dda"].message, "slow")
        self.assertEqual(rows["collection"].state, "error")
        self.assertTrue(rows["dda"].last_date)
        self.assertIn("DDA", rows["dda"].display_name)
        self.assertNotEqual(rows["dda"].color, rows["collection"].color)

    def test_action_test_connection_reports_the_failure(self):
        notification = self.connection.action_test_connection()
        self.assertEqual(notification["params"]["type"], "success")
        with patch.object(
            type(self.connection),
            "_l10n_br_bank_test_connection",
            side_effect=Validacao("refused"),
        ):
            notification = self.connection.action_test_connection()
        self.assertEqual(notification["params"]["type"], "danger")
        self.assertIn("refused", notification["params"]["message"])

    # === security === #

    def test_secrets_hidden_from_account_managers(self):
        manager = new_test_user(
            self.env,
            login="conn-manager",
            groups="base.group_user,account.group_account_manager",
        )
        connection = self.connection.with_user(manager)
        self.assertEqual(connection.read(["name"])[0]["name"], "Fake bank")
        with self.assertRaises(AccessError):
            connection.write({"name": "other"})
        fields_seen = connection.fields_get()
        for field_name in SECRET_FIELDS:
            self.assertNotIn(field_name, fields_seen)
            with self.assertRaises(AccessError):
                connection.read([field_name])

    def test_tokens_have_no_access_outside_the_system_group(self):
        user = new_test_user(
            self.env,
            login="conn-admin",
            groups="base.group_user,l10n_br_bank_connection.group_bank_connection_admin",
        )
        with self.assertRaises(AccessError):
            self.env["l10n_br_bank_connection.token"].with_user(user).search([])
        # The administrator group edits connections, secrets stay hidden.
        connection = self.connection.with_user(user)
        connection.write({"name": "Renamed"})
        self.assertNotIn("client_secret", connection.fields_get())
