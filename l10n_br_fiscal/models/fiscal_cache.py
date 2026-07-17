# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Transaction-scoped caches for the fiscal engine.

The Brazilian fiscal engine maps and computes taxes many times per document
line within a single save (the onchange/compute cascade re-runs the mapping
and the tax computation with the *same* inputs several times per line). These
helpers provide a cache whose lifetime is one database transaction, so those
redundant re-executions collapse into a single one.

Anchoring
---------
The cache lives in ``cr.precommit.data``, the per-cursor dictionary that Odoo
itself empties whenever the transaction changes: ``cr.commit()``,
``cr.rollback()`` (so also the retry of a concurrency error and a cron that
commits per record) and the rollback of a ``cr.savepoint()``. A cache kept as
a plain attribute of the cursor survived all of those, because the Odoo 16
cursor is reused after a commit or a rollback. It is deliberately NOT a
module-level dict, which would leak across transactions and workers.

Invalidation
------------
Results are a pure function of the input record ids and of the fiscal
*definition* tables (tax definitions, ICMS regulation, taxes, tax
classifications). The cache keys encode every input record id plus the scalar
configuration fields that drive the mapping branches, so a change to a keyed
value produces a different key. ``FiscalCacheMixin`` covers the in-place edit
of a definition row that keeps the same id: any create/write/unlink on a model
that inherits it empties the cache of the transaction.

An in-place edit of a field that is read by the mapping but is not keyed, on
a record that does not inherit the mixin (e.g. ``ncm.tax_ipi_id``), within
the transaction that already mapped the line, is not observed.
"""

from odoo import api, models

_TXN_CACHE_KEY = "l10n_br_fiscal.txn_cache"


def get_fiscal_txn_cache(env, name):
    """Return the (create-on-demand) transaction-scoped cache dict ``name``."""
    store = env.cr.precommit.data.setdefault(_TXN_CACHE_KEY, {})
    return store.setdefault(name, {})


def clear_fiscal_txn_cache(env):
    """Drop every transaction-scoped fiscal cache of the current cursor."""
    store = env.cr.precommit.data.get(_TXN_CACHE_KEY)
    if store:
        store.clear()


class FiscalCacheMixin(models.AbstractModel):
    """Wipe the transaction fiscal caches on any change of a definition model.

    Inherited by the fiscal *definition* models whose rows feed the mapping and
    the tax computation. Kept intentionally tiny: it only clears the caches; the
    per-key correctness is handled by the cache keys themselves.
    """

    _name = "l10n_br_fiscal.cache.mixin"
    _description = "Fiscal transaction cache invalidation"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        clear_fiscal_txn_cache(self.env)
        return records

    def write(self, vals):
        res = super().write(vals)
        clear_fiscal_txn_cache(self.env)
        return res

    def unlink(self):
        res = super().unlink()
        clear_fiscal_txn_cache(self.env)
        return res
