# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from io import StringIO

from odoo.tests import SavepointCase

from odoo.addons.spec_driven_model.models.spec_models import SpecModel


class CTeStructure(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def get_stacked_tree(cls, klass):
        """
        # > means the content of the m2o is stacked in the parent
        # - means standard m2o. Eventually followd by the mapped Odoo model
        # ≡ means o2m. Eventually followd by the mapped Odoo model
        """
        spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
        spec_prefix = "cte40"
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
                line = "\n%s> <%s>" % (indent, path.split(".")[-1])
            elif kind == "one2many":
                line = "\n%s    \u2261 <%s> %s" % (
                    indent,
                    field_path,
                    child_concrete or "",
                )
            elif kind == "many2one":
                line = "\n%s    - <%s> %s" % (indent, field_path, child_concrete or "")
            tree.write(line.rstrip())
        tree_txt = tree.getvalue()
        return tree_txt, visited

    def test_inherited_fields(self):
        assert "cte40_CNPJ" in self.env["res.company"]._fields.keys()

    def test_concrete_spec(self):
        # this ensure basic SQL is set up
        self.assertEqual(
            len(
                self.env["cte.40.tcte_infnfe"].search(
                    [("cte40_chave", "=", "NO_RECORD")]
                )
            ),
            0,
        )

    # TODO: Nao achei um exemplo de m2o concreto para concreto
    # def test_m2o_concrete_to_concrete_spec(self):
    #     self.assertEqual(
    #         self.env["cte.40.infnfe"]
    #         ._fields["cte40_infUnidCarga_infNFe_id"]
    #         .comodel_name,
    #         "cte.40.tunidcarga",
    #     )

    def test_o2m_concrete_to_concrete_spec(self):
        self.assertEqual(
            self.env["cte.40.tcte_infdoc"]._fields["cte40_infOutros"].comodel_name,
            "cte.40.infoutros",
        )

    def test_m2o_stacked_to_odoo(self):
        self.assertEqual(
            self.env["l10n_br_fiscal.document"]._fields["cte40_enderReme"].comodel_name,
            "res.partner",
        )

    def test_o2m_to_odoo(self):
        self.assertEqual(
            self.env["l10n_br_fiscal.document"]._fields["cte40_occ"].comodel_name,
            "l10n_br_cte.modal.rodo.occ",
        )
        self.assertEqual(
            len(
                self.env["l10n_br_cte.modal.rodo.occ"].search(
                    [("cte40_nOcc", "=", "NO_RECORD")]
                )
            ),
            0,
        )

    def test_m2o_stacked_to_concrete(self):
        # not stacked because optional
        model = (
            self.env["l10n_br_fiscal.document"]
            ._fields["cte40_infSolicNFF"]
            .comodel_name
        )
        self.assertEqual(model, "cte.40.tcte_infsolicnff")

    # TODO: Tratar
    # def test_m2o_stacked(self):
    #     # not stacked because optional
    #     cte_model = self.env["l10n_br_fiscal.document"]
    #     # cte40_cana is optional so its fields shoudn't be stacked
    #     assert "cte40_XXX" not in cte_model._fields.keys()

    def test_doc_stacking_points(self):
        doc_keys = [
            "cte40_ide",
            "cte40_toma3",
            "cte40_toma4",
            # "cte40_enderToma",
            "cte40_compl",
            "cte40_fluxo",
            "cte40_entrega",
            "cte40_comData",
            "cte40_semHora",
            "cte40_vPrest",
            "cte40_imp",
            "cte40_ICMS",
            "cte40_infCTeNorm",
            "cte40_infCarga",
            "cte40_infModal",
        ]
        keys = [
            k
            for k in self.env["l10n_br_fiscal.document"]
            .with_context(spec_schema="cte", spec_version="40")
            ._get_stacking_points()
            .keys()
        ]
        self.assertEqual(sorted(keys), sorted(doc_keys))

    # TODO: Tratar
    # def test_doc_tree(self):
    #     base_class = self.env["l10n_br_fiscal.document"]
    #     tree, visited = self.get_stacked_tree(base_class)
    #     self.assertEqual(tree, CTe.INFCTE_TREE)
    #     self.assertEqual(len(visited), 15)  # all stacked classes

    def test_m2o_force_stack(self):
        pass

    def test_doc_visit_stack(self):
        pass
