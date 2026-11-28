# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Access tokens shared between the Odoo workers, kept in the database."""

import logging
import threading

import psycopg2
from brbank.auth import TokenPersistido

_logger = logging.getLogger(__name__)

TOKEN_TABLE = "l10n_br_bank_connection_token"
CONNECTION_TABLE = "l10n_br_bank_connection_connection"

# Process locks by (database, connection, key); released from another thread.
_PROCESS_LOCKS = {}
_PROCESS_LOCKS_GUARD = threading.Lock()


def _process_lock(dbname, connection_id, key):
    with _PROCESS_LOCKS_GUARD:
        return _PROCESS_LOCKS.setdefault((dbname, connection_id, key), threading.Lock())


def token_key(chave):
    """Text of the key of the library, a tuple `(account, scope or None)`."""
    return "|".join("" if part is None else str(part) for part in chave)


class _Lock:
    """Renewal lock: process lock plus `pg_advisory_xact_lock`."""

    def __init__(self, store, key):
        self._store = store
        self._key = key
        self._local = _process_lock(store.dbname, store.connection_id, key)
        self._cr = None

    def __enter__(self):
        self._local.acquire()
        try:
            registry = self._store.registry
            # Test mode: every cursor is a view of one connection.
            if not registry.in_test_mode():
                self._cr = registry.cursor()
                self._cr.execute(
                    "SELECT pg_advisory_xact_lock(%s, hashtext(%s))",
                    (self._store.connection_id, self._key),
                )
        except BaseException:
            self._release()
            raise
        return None

    def __exit__(self, exc_type, exc, traceback):
        self._release()
        return False

    def _release(self):
        cr, self._cr = self._cr, None
        try:
            if cr is not None:
                try:
                    # Own cursor: the commit publishes the renewed token at once.
                    cr.commit()  # pylint: disable=invalid-commit
                finally:
                    cr.close()
        finally:
            self._local.release()


class OdooTokenStore:
    """`ArmazemToken` of the brbank library on top of the Odoo database."""

    def __init__(self, registry, connection_id):
        self.registry = registry
        self.dbname = registry.db_name
        self.connection_id = connection_id

    def ler(self, chave):
        """Token stored for `chave`, or None. Never raises: it is a cache."""
        try:
            with self.registry.cursor() as cr:
                cr.execute(
                    f"SELECT value, expires_at FROM {TOKEN_TABLE} "  # noqa: S608
                    "WHERE connection_id = %s AND key = %s",
                    (self.connection_id, token_key(chave)),
                    log_exceptions=False,
                )
                row = cr.fetchone()
        except psycopg2.Error as error:
            _logger.warning(
                "bank connection %s: could not read the token (%s)",
                self.connection_id,
                type(error).__name__,
            )
            return None
        if not row or not row[0]:
            return None
        return TokenPersistido(valor=row[0], expira_em=float(row[1]))

    def gravar(self, chave, token):
        """Upsert and commit the token. A failure only costs one more renewal."""
        try:
            with self.registry.cursor() as cr:
                cr.execute(
                    f"INSERT INTO {TOKEN_TABLE} "  # noqa: S608
                    "(connection_id, key, value, expires_at, create_date, write_date) "
                    "VALUES (%s, %s, %s, %s, now() AT TIME ZONE 'UTC', "
                    "now() AT TIME ZONE 'UTC') "
                    "ON CONFLICT (connection_id, key) DO UPDATE SET "
                    "value = EXCLUDED.value, expires_at = EXCLUDED.expires_at, "
                    "write_date = EXCLUDED.write_date",
                    (
                        self.connection_id,
                        token_key(chave),
                        token.valor,
                        float(token.expira_em),
                    ),
                    log_exceptions=False,
                )
        except psycopg2.Error as error:
            # Typically a connection not committed yet (foreign key).
            _logger.warning(
                "bank connection %s: could not save the token (%s)",
                self.connection_id,
                type(error).__name__,
            )

    def trava(self, chave):
        """Context manager serializing the renewal of `chave` between processes."""
        return _Lock(self, token_key(chave))


def read_refresh_token(registry, connection_id, fallback=None):
    """Current refresh token, read in a cursor of its own."""
    try:
        with registry.cursor() as cr:
            cr.execute(
                f"SELECT refresh_token FROM {CONNECTION_TABLE} "  # noqa: S608
                "WHERE id = %s",
                (connection_id,),
                log_exceptions=False,
            )
            row = cr.fetchone()
    except psycopg2.Error:
        return fallback
    return (row and row[0]) or fallback
