# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest import mock

from lxml import etree

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestFiscalViewPruneClosure(TransactionCase):
    """C4: the reduced line tree must keep every field referenced in a kept
    node's modifier, even when a downstream ``_fiscal_view_pruned_fields()``
    override also prunes it, otherwise the view crashes at load."""

    def test_pruned_modifier_referenced_field_survives_in_tree(self):
        company = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        fiscal_line = self.env["l10n_br_fiscal.document.line"]
        mixin = self.env["l10n_br_fiscal.document.line.mixin"]

        fiscal_view = self.env.ref(
            "l10n_br_fiscal.document_fiscal_line_mixin_form"
        ).sudo()
        fsc_doc = etree.fromstring(
            fiscal_view.with_context(inherit_branding=True).get_combined_arch()
        )
        field_names = set(mixin._fields) | set(fiscal_line._fields)
        modifier_refs = fiscal_line._fiscal_line_modifier_refs(fsc_doc, field_names)
        taxes_names = {
            node.attrib["name"]
            for node in fsc_doc.xpath("//page[@name='fiscal_taxes']//field")
        }
        # A fiscal_taxes tree field kept ONLY by the modifier closure: droppable
        # on its own, so pruning it must not remove it from the tree.
        candidates = sorted(
            (modifier_refs & taxes_names) - fiscal_line._fiscal_line_view_fields()
        )
        self.assertTrue(
            candidates,
            "no modifier-referenced prunable fiscal tree field to exercise C4",
        )
        victim = candidates[0]

        base_pruned = fiscal_line._fiscal_view_pruned_fields()

        def _patched_pruned(self):
            return base_pruned | {victim}

        move = self.env["account.move"].with_company(company)
        with mock.patch.object(
            type(fiscal_line), "_fiscal_view_pruned_fields", _patched_pruned
        ):
            # Must not raise "Unknown field ... in modifier" at view load.
            view = move.with_context(force_line_fiscal_detail=True).get_view(
                view_type="form"
            )
        arch = etree.fromstring(view["arch"])
        self.assertTrue(
            arch.xpath(f"//tree//field[@name='{victim}']"),
            f"{victim} is referenced in a modifier but was dropped from the line "
            "tree despite the modifier closure (C4 regression).",
        )
