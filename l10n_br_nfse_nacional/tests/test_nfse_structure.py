# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from io import StringIO

from odoo.tests import TransactionCase

from odoo.addons.spec_driven_model.models.spec_models import SpecModel

from ..models.document import L10nBrFiscalDocument


class NfseStructure(TransactionCase):
    """The DPS of the national NFS-e is a stacked spec model of infDPS."""

    @classmethod
    def get_stacked_tree(cls, klass):
        """# + means the content of the m2o is stacked in the parent,
        - means a standard m2o (eventually followed by the mapped model)
        and ≡ means an o2m (eventually followed by the mapped model).
        """
        spec_module = "odoo.addons.l10n_br_nfse_spec.models.v1_0.tipos_complexos_v1_01"
        spec_prefix = "nfse10"
        stacking_settings = {
            "odoo_module": getattr(klass, f"_{spec_prefix}_odoo_module"),
            "stacking_mixin": getattr(klass, f"_{spec_prefix}_stacking_mixin"),
            "stacking_points": getattr(klass, f"_{spec_prefix}_stacking_points"),
            "stacking_skip_paths": getattr(
                klass, f"_{spec_prefix}_stacking_skip_paths", []
            ),
            "stacking_force_paths": getattr(
                klass, f"_{spec_prefix}_stacking_force_paths", []
            ),
        }
        node = SpecModel._odoo_name_to_class(
            stacking_settings["stacking_mixin"], spec_module
        )
        tree = StringIO()
        visited = set()
        for kind, n, path, field_path, child_concrete in klass._visit_stack(
            cls.env, node, stacking_settings
        ):
            visited.add(n)
            path_items = path.split(".")
            indent = "    ".join(["" for i in range(0, len(path_items))])
            if kind == "stacked":
                line = "\n{}+ <{}>".format(indent, path.split(".")[-1])
            elif kind == "one2many":
                line = "\n{}    \u2261 <{}> {}".format(
                    indent, field_path, child_concrete or ""
                )
            else:
                line = "\n{}    - <{}> {}".format(
                    indent, field_path, child_concrete or ""
                )
            tree.write(line.rstrip())
        tree_txt = tree.getvalue()
        return tree_txt, visited

    def test_doc_tree(self):
        """The stacked tree is the documented one: the DPS is one service."""
        tree, visited = self.get_stacked_tree(self.env["l10n_br_fiscal.document"])
        self.assertEqual(tree, L10nBrFiscalDocument.NFSE_TREE)
        self.assertEqual(len(visited), 13)  # all the stacked classes

    def test_doc_stacking_points(self):
        doc_keys = [
            "nfse10_cServ",
            "nfse10_locPrest",
            "nfse10_pTotTrib",
            "nfse10_piscofins",
            "nfse10_serv",
            "nfse10_totTrib",
            "nfse10_trib",
            "nfse10_tribFed",
            "nfse10_tribMun",
            "nfse10_vDescCondIncond",
            "nfse10_vServPrest",
            "nfse10_valores",
        ]
        keys = [
            k
            for k in self.env["l10n_br_fiscal.document"]
            .with_context(spec_schema="nfse", spec_version="10")
            ._get_stacking_points()
            .keys()
        ]
        self.assertEqual(sorted(keys), doc_keys)

    def test_m2o_stacked_to_odoo(self):
        """The prestador and the tomador stay mapped business records."""
        document = self.env["l10n_br_fiscal.document"]
        self.assertEqual(document._fields["nfse10_prest"].comodel_name, "res.company")
        self.assertEqual(document._fields["nfse10_toma"].comodel_name, "res.partner")

    def test_m2o_not_stacked_when_optional(self):
        """An optional group stays a m2o: its values live in a spec table."""
        document = self.env["l10n_br_fiscal.document"]
        # subst is optional and is not a field of the NFS-e DPS emitted here
        self.assertEqual(
            document._fields["nfse10_subst"].comodel_name, "nfse.10.tcsubstituicao"
        )
        # the RTC group keeps its own CST, which would clash with PIS/COFINS
        self.assertEqual(
            document._fields["nfse10_IBSCBS"].comodel_name, "nfse.10.tcrtcinfoibscbs"
        )

    def test_stacked_fields_are_on_the_document(self):
        """A field of a stacked group is a column of the fiscal document."""
        document = self.env["l10n_br_fiscal.document"]
        for field_name in (
            "nfse10_cTribNac",
            "nfse10_xDescServ",
            "nfse10_vServ",
            "nfse10_vRetCP",
            "nfse10_pTotTribFed",
        ):
            self.assertIn(field_name, document._fields)
        # the groups themselves are stacking points, not relation fields
        for group in ("nfse10_serv", "nfse10_valores", "nfse10_trib"):
            self.assertNotIn(group, document._fields)

    def test_company_fields_are_kept(self):
        self.assertIn("nfse10_CNPJ", self.env["res.company"]._fields.keys())
        self.assertIn("nfse10_opSimpNac", self.env["res.company"]._fields.keys())
