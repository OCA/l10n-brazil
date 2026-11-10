# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from io import StringIO

from odoo.tests import TransactionCase

from odoo.addons.spec_driven_model.models.spec_models import SpecModel


class NfseStructure(TransactionCase):
    """The DPS of the national NFS-e is a stacked spec model of infDPS."""

    @classmethod
    def get_stacked_tree(cls, klass):
        """# + means the content of the m2o is stacked in the parent,
        - means a standard m2o (eventually followed by the mapped model)
        and = means an o2m (eventually followed by the mapped model).
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
        for kind, _node, path, field_path, child_concrete in klass._visit_stack(
            cls.env, node, stacking_settings
        ):
            path_items = path.split(".")
            indent = "    " * len(path_items)
            if kind == "stacked":
                tree.write(f"\n{indent}+ <{path_items[-1]}>")
            elif kind == "one2many":
                tree.write(f"\n{indent}= <{field_path}> {child_concrete or ''}")
            else:
                tree.write(f"\n{indent}- <{field_path}> {child_concrete or ''}")
        return tree.getvalue()

    def test_stacked_tree(self):
        """The groups of the DPS are stacked on the document, not on the line."""
        tree = self.get_stacked_tree(self.env["l10n_br_fiscal.document"])
        # one service per DPS: serv, valores and their groups are stacked
        for group in ("tcinfdps", "serv", "cServ", "valores", "trib", "totTrib"):
            self.assertIn(f"+ <{group}>", tree)
        # the prestador and the tomador stay mapped records
        self.assertIn("- <prest> res.company", tree)
        self.assertIn("- <toma> res.partner", tree)

    def test_stacked_fields_are_on_the_document(self):
        """A field of a stacked group is a column of the fiscal document."""
        document = self.env["l10n_br_fiscal.document"]
        line = self.env["l10n_br_fiscal.document.line"]
        for field_name in (
            "nfse10_cTribNac",
            "nfse10_xDescServ",
            "nfse10_vServ",
            "nfse10_vRetCP",
            "nfse10_pTotTribFed",
        ):
            self.assertIn(field_name, document._fields)
        # the fiscal line is not a spec model of the NFS-e schema anymore
        self.assertFalse([name for name in line._fields if name.startswith("nfse10_")])

    def test_stacked_groups_are_not_fields(self):
        """The groups of the schema are stacked, they are not relation fields."""
        document = self.env["l10n_br_fiscal.document"]
        stacking_points = document._get_stacking_points()
        for group in ("nfse10_serv", "nfse10_valores", "nfse10_trib"):
            self.assertIn(group, stacking_points)
            self.assertNotIn(group, document._fields)
        # the prestador and the tomador are still relation fields
        self.assertEqual(document._fields["nfse10_prest"].comodel_name, "res.company")
        self.assertEqual(document._fields["nfse10_toma"].comodel_name, "res.partner")

    def test_company_fields_are_kept(self):
        self.assertIn("nfse10_CNPJ", self.env["res.company"]._fields.keys())
        self.assertIn("nfse10_opSimpNac", self.env["res.company"]._fields.keys())
