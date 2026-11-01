# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The token store: persistence between processes and the renewal lock."""

import threading
from unittest.mock import patch

from odoo.tests import HttpCase, TransactionCase, tagged

from ..utils.token_store import OdooTokenStore, TokenPersistido
from .common import ConnectionCommon

KEY = ("odoo-connection-1", None)
PROCESS_LOCK = "odoo.addons.l10n_br_bank_connection.utils.token_store._process_lock"


def _run_in_thread(target):
    errors = []

    def wrapper():
        try:
            target()
        except BaseException as error:  # pylint: disable=broad-except
            errors.append(error)

    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()
    return thread, errors


@tagged("post_install", "-at_install")
class TestTokenStore(ConnectionCommon, HttpCase):
    """`HttpCase` runs in test mode: the cursors of the store are test cursors
    of the connection of the test, so what they commit is readable here."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_connection()

    def setUp(self):
        super().setUp()
        self.connection = self._create_connection()
        self.store = OdooTokenStore(self.registry, self.connection.id)

    def test_write_and_read_back(self):
        self.assertIsNone(self.store.ler(KEY))
        self.store.gravar(KEY, TokenPersistido("access-1", 2000.5))
        token = self.store.ler(KEY)
        self.assertEqual((token.valor, token.expira_em), ("access-1", 2000.5))
        self.assertNotIn("access-1", repr(token))

    def test_write_replaces_and_keys_are_independent(self):
        scoped = ("odoo-connection-1", "read")
        self.store.gravar(KEY, TokenPersistido("a", 1.0))
        self.store.gravar(scoped, TokenPersistido("b", 2.0))
        self.store.gravar(KEY, TokenPersistido("c", 3.0))
        self.assertEqual(self.store.ler(KEY).valor, "c")
        self.assertEqual(self.store.ler(scoped).valor, "b")
        rows = self.env["l10n_br_bank_connection.token"].search_count(
            [("connection_id", "=", self.connection.id)]
        )
        self.assertEqual(rows, 2)

    def test_connections_do_not_share_tokens(self):
        other = self._create_connection(name="Other")
        self.store.gravar(KEY, TokenPersistido("mine", 1.0))
        self.assertIsNone(OdooTokenStore(self.registry, other.id).ler(KEY))

    def test_a_connection_that_does_not_exist_only_costs_a_renewal(self):
        orphan = OdooTokenStore(self.registry, 999999999)
        with self.assertLogs(
            "odoo.addons.l10n_br_bank_connection.utils.token_store", "WARNING"
        ):
            orphan.gravar(KEY, TokenPersistido("x", 1.0))
        self.assertIsNone(orphan.ler(KEY))

    def test_lock_serializes_threads_and_the_second_reads_again(self):
        first_inside = threading.Event()
        release_first = threading.Event()
        second_inside = threading.Event()
        seen_by_second = []

        def first():
            with self.store.trava(KEY):
                first_inside.set()
                self.store.gravar(KEY, TokenPersistido("renewed-by-first", 9e9))
                release_first.wait(10)

        def second():
            first_inside.wait(10)
            with self.store.trava(KEY):
                second_inside.set()
                seen_by_second.append(self.store.ler(KEY))

        thread_1, errors_1 = _run_in_thread(first)
        thread_2, errors_2 = _run_in_thread(second)
        self.assertTrue(first_inside.wait(10))
        # The second thread is waiting for the lock, not inside it.
        self.assertFalse(second_inside.wait(0.5))
        release_first.set()
        thread_1.join(10)
        thread_2.join(10)
        self.assertFalse(errors_1 or errors_2, errors_1 + errors_2)
        self.assertTrue(second_inside.is_set())
        self.assertEqual(seen_by_second[0].valor, "renewed-by-first")

    def test_lock_may_be_left_by_another_thread(self):
        lock = self.store.trava(KEY)
        thread, errors = _run_in_thread(lock.__enter__)
        thread.join(10)
        thread, errors_exit = _run_in_thread(lambda: lock.__exit__(None, None, None))
        thread.join(10)
        self.assertFalse(errors or errors_exit, errors + errors_exit)
        with self.store.trava(KEY):
            pass

    def test_lock_is_per_key(self):
        other_key = ("odoo-connection-1", "other")
        finished = []

        def other():
            with self.store.trava(other_key):
                finished.append(True)

        with self.store.trava(KEY):
            thread, errors = _run_in_thread(other)
            thread.join(5)
            self.assertFalse(thread.is_alive())
            self.assertFalse(errors)
        self.assertEqual(finished, [True])


@tagged("post_install", "-at_install")
class TestAdvisoryLock(TransactionCase):
    """Real cursors: only the lock of the database can make the second thread wait."""

    def setUp(self):
        super().setUp()
        patcher = patch(PROCESS_LOCK, lambda *args: threading.Lock())
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_two_connections_do_not_renew_at_once(self):
        self.assertFalse(self.registry.in_test_mode())
        # Id with no row: the lock only uses the number.
        store = OdooTokenStore(self.registry, 2**30)
        first_inside = threading.Event()
        release_first = threading.Event()
        second_inside = threading.Event()

        def first():
            with store.trava(KEY):
                first_inside.set()
                release_first.wait(10)

        def second():
            first_inside.wait(10)
            with OdooTokenStore(self.registry, 2**30).trava(KEY):
                second_inside.set()

        thread_1, errors_1 = _run_in_thread(first)
        thread_2, errors_2 = _run_in_thread(second)
        self.assertTrue(first_inside.wait(10))
        self.assertFalse(second_inside.wait(0.5))
        release_first.set()
        thread_1.join(10)
        thread_2.join(10)
        self.assertFalse(errors_1 or errors_2, errors_1 + errors_2)
        self.assertTrue(second_inside.is_set())

    def test_the_lock_is_a_lock_of_the_database(self):
        store = OdooTokenStore(self.registry, 2**30 + 1)
        with store.trava(KEY):
            with self.registry.cursor() as cr:
                cr.execute(
                    "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' "
                    "AND classid = %s AND granted",
                    (2**30 + 1,),
                )
                self.assertEqual(cr.fetchone()[0], 1)
        with self.registry.cursor() as cr:
            cr.execute(
                "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' "
                "AND classid = %s",
                (2**30 + 1,),
            )
            self.assertEqual(cr.fetchone()[0], 0)
