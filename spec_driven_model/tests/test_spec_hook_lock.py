# Copyright 2026 PoP Solutions - Marcos Mendez <m@pop.coop>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import logging

import psycopg2

from odoo.sql_db import db_connect
from odoo.tests import TransactionCase
from odoo.tools import mute_logger

from ..models.spec_mixin import (
    _SPEC_HOOK_LOCK_CLASSID,
    _SPEC_HOOK_LOCK_OBJID,
    SpecMixin,
)

_logger = logging.getLogger(__name__)

# pg_locks.objsubid is 1 for the single int8 advisory lock form
# and 2 for the two int4 keys form.
_TWO_KEYS_OBJSUBID = 2


class TestSpecHookAdvisoryLock(TransactionCase):
    """
    _register_remaining_schema_models_hook serializes the workers with a
    session level advisory lock. A session lock is NOT released by a
    rollback, so failing to release it explicitly leaves it held on a
    connection that goes back to the Odoo pool, and every later registry
    load blocks on pg_advisory_lock, which has no timeout.
    """

    def _spare_cursor(self):
        """A cursor on a connection of its own, closed at the end of the test.

        The hook runs on the registry loading connection, not on the test
        one, and a leaked lock has to be observed from the outside.
        """
        cr = db_connect(self.env.cr.dbname).cursor()
        # Make sure a leaking test never poisons the connection pool.
        self.addCleanup(cr.close)
        self.addCleanup(self._force_unlock, cr)
        return cr

    @staticmethod
    def _force_unlock(cr):
        try:
            cr.rollback()
            cr.execute("SELECT pg_advisory_unlock_all()")
        except psycopg2.Error:
            _logger.warning("Could not clean up the advisory locks of the test.")

    def _lock_holders(self):
        """Backend pids currently holding the spec hook advisory lock."""
        self.env.cr.execute(
            """
            SELECT pid FROM pg_locks
             WHERE locktype = 'advisory'
               AND classid = %s
               AND objid = %s
               AND objsubid = %s
               AND granted
            """,
            (_SPEC_HOOK_LOCK_CLASSID, _SPEC_HOOK_LOCK_OBJID, _TWO_KEYS_OBJSUBID),
        )
        return {row[0] for row in self.env.cr.fetchall()}

    def test_lock_is_released_after_a_successful_hook(self):
        cr = self._spare_cursor()
        pid = cr.connection.info.backend_pid

        cr.execute(
            "SELECT pg_advisory_lock(%s, %s)",
            [_SPEC_HOOK_LOCK_CLASSID, _SPEC_HOOK_LOCK_OBJID],
        )
        self.assertIn(pid, self._lock_holders())

        SpecMixin._release_spec_hook_advisory_lock(cr)

        self.assertNotIn(pid, self._lock_holders())

    def test_lock_is_released_when_the_hook_aborted_the_transaction(self):
        """Regression test for the leak that hangs every later registry load.

        Once the hook raises a database error the transaction is aborted and
        a plain ``pg_advisory_unlock`` raises InFailedSqlTransaction, which
        masks the original exception and keeps the lock held.
        """
        cr = self._spare_cursor()
        pid = cr.connection.info.backend_pid

        cr.execute(
            "SELECT pg_advisory_lock(%s, %s)",
            [_SPEC_HOOK_LOCK_CLASSID, _SPEC_HOOK_LOCK_OBJID],
        )
        # Both the deliberate failure and the first unlock attempt, which is
        # the one that has to fail for this test to mean anything, are logged
        # as errors by odoo.sql_db. The OCA checklog step fails the build on
        # any ERROR line, so the logger is muted around the whole sequence.
        with mute_logger("odoo.sql_db"):
            # Same state the cursor is left in when the hook blows up on
            # INSERT INTO ir_model_data ... ON CONFLICT ... DO UPDATE.
            with self.assertRaises(psycopg2.Error):
                cr.execute("SELECT 1 / 0")

            SpecMixin._release_spec_hook_advisory_lock(cr)

        self.assertNotIn(
            pid,
            self._lock_holders(),
            "the advisory lock leaked on an aborted transaction: the "
            "connection goes back to the pool still holding it and the next "
            "registry load waits on pg_advisory_lock forever",
        )

    def test_the_hook_lock_never_waits_on_an_int8_advisory_lock(self):
        """The two keys form has a lock space of its own.

        Addons such as queue_job take advisory locks with the single int8
        form. Even when the very same 64 bits are used, the two forms cannot
        block each other, which is why the two keys form is preferred here.
        """
        int8_key = (_SPEC_HOOK_LOCK_CLASSID << 32) | _SPEC_HOOK_LOCK_OBJID

        other_addon_cr = self._spare_cursor()
        other_addon_cr.execute("SELECT pg_advisory_lock(%s)", [int8_key])

        hook_cr = self._spare_cursor()
        hook_cr.execute(
            "SELECT pg_try_advisory_lock(%s, %s)",
            [_SPEC_HOOK_LOCK_CLASSID, _SPEC_HOOK_LOCK_OBJID],
        )

        self.assertTrue(
            hook_cr.fetchone()[0],
            "the spec hook lock collided with an int8 advisory lock holding "
            "the same 64 bits",
        )
