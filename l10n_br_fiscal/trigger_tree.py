# Copyright 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.modules.registry import Registry, TriggerTree
from odoo.tools import OrderedSet


def _field_trigger_cycles(triggers):
    """Map each field of a dependency cycle to an identifier of its cycle
    (Tarjan's strongly connected components, iterative)."""

    def targets_of(field):
        paths = triggers[field].values() if field in triggers else ()
        return iter([target for targets in paths for target in targets])

    cycles, index, lowest, component, pending = {}, {}, {}, [], set()
    for start in list(triggers):
        if start in index:
            continue
        index[start] = lowest[start] = len(index)
        component.append(start)
        pending.add(start)
        stack = [(start, targets_of(start))]
        while stack:
            field, targets = stack[-1]
            for target in targets:
                if target not in index:
                    index[target] = lowest[target] = len(index)
                    component.append(target)
                    pending.add(target)
                    stack.append((target, targets_of(target)))
                    break
                if target in pending:
                    lowest[field] = min(lowest[field], index[target])
            else:
                stack.pop()
                if stack:
                    parent = stack[-1][0]
                    lowest[parent] = min(lowest[parent], lowest[field])
                if lowest[field] == index[field]:
                    members = [component.pop()]
                    while members[-1] is not field:
                        members.append(component.pop())
                    pending.difference_update(members)
                    if len(members) > 1:
                        cycles.update(dict.fromkeys(members, index[field] + 1))
    return cycles


def get_field_trigger_tree(self, field):
    """Same tree as the core method, without exploring twice the same
    (field, path, fields seen in the same dependency cycle): the core
    enumerates every path of the dependency graph, which is exponential
    with the 140+ tax fields of the fiscal line."""
    if field in self._field_trigger_trees:
        return self._field_trigger_trees[field]

    triggers = self._field_triggers
    if field not in triggers:
        return TriggerTree()

    cache = self.__dict__.get("_l10n_br_fiscal_trigger_cycles")
    if not cache or cache[0] is not triggers:
        cache = (triggers, _field_trigger_cycles(triggers))
        self.__dict__["_l10n_br_fiscal_trigger_cycles"] = cache
    cycles = cache[1]
    explored = set()

    def transitive_triggers(field, prefix=(), seen=()):
        if field in seen or field not in triggers:
            return
        cycle = cycles.get(field)
        key = (
            field,
            prefix,
            cycle and frozenset(f for f in seen if cycles.get(f) == cycle),
        )
        if key in explored:
            return
        explored.add(key)
        for path, targets in triggers[field].items():
            full_path = concat(prefix, path)
            yield full_path, targets
            for target in targets:
                yield from transitive_triggers(target, full_path, seen + (field,))

    def concat(seq1, seq2):
        if seq1 and seq2:
            f1, f2 = seq1[-1], seq2[0]
            if (
                f1.type == "many2one"
                and f2.type == "one2many"
                and f1.name == f2.inverse_name
                and f1.model_name == f2.comodel_name
                and f1.comodel_name == f2.model_name
            ):
                return concat(seq1[:-1], seq2[1:])
        return seq1 + seq2

    tree = TriggerTree()
    for path, targets in transitive_triggers(field):
        current = tree
        for label in path:
            current = current.increase(label)
        if current.root:
            current.root.update(targets)
        else:
            current.root = OrderedSet(targets)

    self._field_trigger_trees[field] = tree
    return tree


get_field_trigger_tree._original_method = Registry.get_field_trigger_tree
Registry.get_field_trigger_tree = get_field_trigger_tree
