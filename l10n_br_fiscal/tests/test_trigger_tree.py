# Copyright 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import TransactionCase

from ..trigger_tree import get_field_trigger_tree


def _dump(tree):
    return list(tree.root), [(label, _dump(sub)) for label, sub in tree.items()]


class TestTriggerTree(TransactionCase):
    def test_same_tree_as_core(self):
        registry = self.env.registry
        fields = [
            self.env["l10n_br_fiscal.document.line"]._fields[name]
            for name in ("fiscal_price", "icms_cst_id", "cfop_id", "document_id")
        ] + [self.env["res.partner"]._fields[name] for name in ("parent_id", "name")]
        for field in fields:
            registry._field_trigger_trees.pop(field, None)
            core_tree = get_field_trigger_tree._original_method(registry, field)
            registry._field_trigger_trees.pop(field, None)
            tree = registry.get_field_trigger_tree(field)
            self.assertEqual(_dump(tree), _dump(core_tree), field)
