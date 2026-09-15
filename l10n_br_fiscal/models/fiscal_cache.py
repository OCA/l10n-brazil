# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Transaction-scoped caches for the fiscal engine.

The Brazilian fiscal engine maps and computes taxes many times per document
line within a single save (the onchange/compute cascade re-runs the mapping
and the tax computation with the *same* inputs several times per line). These
helpers provide a cache whose lifetime is exactly one database transaction, so
those redundant re-executions collapse into a single one — without ever
leaking results between transactions or workers.

Anchoring
---------
The cache dict is stored as an attribute on the *cursor* (``env.cr``). A cursor
lives for exactly one transaction: every web request / job gets a fresh cursor
(hence a fresh, empty cache), and there is one cursor per worker at a time, so
nothing is shared between transactions or across workers. This is deliberately
NOT a module-level dict (which would leak across transactions and workers).

Invalidation
------------
Mapping/computation results are a pure function of the input record ids **and**
the fiscal *definition* tables (tax definitions, ICMS regulation, taxes, tax
classifications). The cache keys already encode every input record id plus the
scalar configuration fields that drive the mapping branches (tax framework,
``ind_ie_dest``, ICMS origin, states...), so a change to any *keyed* value
naturally produces a different key.

Two complementary mechanisms cover an in-place edit of a *definition* row (e.g.
changing a tax rate) that keeps the same id:

1. ``FiscalCacheMixin`` — any create/write/unlink on a definition model that
   inherits it wipes the whole transaction cache. This covers config-screen and
   test edits performed in an *ordinary* transaction.
2. ``write_date`` in the cache keys — the keys encode the ``write_date`` of the
   fiscal taxes (``compute_taxes`` key) and of the definition-anchor records
   (``map_fiscal_taxes`` key: the operation line, the company ICMS regulation
   and tax classification, the partner fiscal profile). Because an edit bumps
   ``write_date`` and a **savepoint rollback reverts it**, the key produced
   after a rollback matches the pre-edit key, not the edited one: a stale entry
   left in the (rollback-surviving) transaction cache becomes *unreachable*
   instead of being served. This makes the cache self-validating across
   savepoint rollbacks, which neither ``cr.clear()`` nor ``FiscalCacheMixin``
   observe (the per-cursor cache attribute is not part of the ORM/precommit
   state a rollback clears).

Known, documented residual limitation
-------------------------------------
The ``write_date`` guard versions the *anchor* records, not every child
definition row they aggregate (``tax_definition_ids`` of the company/CFOP/
operation line/partner profile, ICMS-regulation lines...). So the one case that
still leaks is narrow and self-inflicted: editing a *child* definition row
**inside a savepoint that is later rolled back**, and then recomputing with the
**same key on the same cursor** — the child edit bumps only the child's
``write_date`` (not the anchor's), ``FiscalCacheMixin`` cleared the cache on the
edit but the rollback does not re-clear it, so the entry stored between the edit
and the rollback survives and is served. This is an honest upgrade of the prior
behaviour (which leaked on *any* savepoint rollback that reverted a keyed edit)
and does not happen in the supported document flows: fiscal definitions are not
mutated in the middle of computing a line's taxes. The same holds for an
in-place edit of a *non-definition* config field that feeds the mapping but is
not keyed (e.g. ``ncm.tax_ipi_id``) within the transaction that already mapped
the line.
"""

from odoo import api, models

_TXN_CACHE_ATTR = "_l10n_br_fiscal_txn_cache"


def get_fiscal_txn_cache(env, name):
    """Return the (create-on-demand) transaction-scoped cache dict ``name``."""
    cr = env.cr
    store = getattr(cr, _TXN_CACHE_ATTR, None)
    if store is None:
        store = {}
        setattr(cr, _TXN_CACHE_ATTR, store)
    return store.setdefault(name, {})


def clear_fiscal_txn_cache(env):
    """Drop every transaction-scoped fiscal cache of the current cursor."""
    cr = env.cr
    if getattr(cr, _TXN_CACHE_ATTR, None):
        setattr(cr, _TXN_CACHE_ATTR, None)


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
