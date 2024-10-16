# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from io import StringIO

from odoo.tests import SavepointCase

from odoo.addons.spec_driven_model.models.spec_models import SpecModel

from ..models.document import MDFe


class MDFeStructure(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["spec.mixin.mdfe"]._register_hook()

    @classmethod
    def get_stacked_tree(cls, klass):
        """
        # > means the content of the m2o is stacked in the parent
        # - means standard m2o. Eventually followd by the mapped Odoo model
        # ≡ means o2m. Eventually followd by the mapped Odoo model
        """
        spec_module = (
            "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_tipos_basico_v3_00"
        )
        spec_prefix = "mdfe30"
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
        assert "mdfe30_CNPJ" in self.env["res.company"]._fields.keys()

    def test_concrete_spec(self):
        # this ensure basic SQL is set up
        self.assertEqual(
            len(
                self.env["mdfe.30.infmuncarrega"].search(
                    [("mdfe30_cMunCarrega", "=", "NO_RECORD")]
                )
            ),
            0,
        )

    def test_m2o_concrete_to_concrete_spec(self):
        self.assertEqual(
            self.env["mdfe.30.infcte"]
            ._fields["mdfe30_infCTe_infMunDescarga_id"]
            .comodel_name,
            "mdfe.30.infmundescarga",
        )

    def test_o2m_concrete_to_concrete_spec(self):
        self.assertEqual(
            self.env["mdfe.30.ide"]._fields["mdfe30_infMunCarrega"].comodel_name,
            "mdfe.30.infmuncarrega",
        )

    def test_m2o_stacked_to_odoo(self):
        self.assertEqual(
            self.env["l10n_br_fiscal.document"]._fields["mdfe30_prodPred"].comodel_name,
            "product.product",
        )

    def test_o2m_to_odoo(self):
        self.assertEqual(
            self.env["l10n_br_fiscal.document"]
            ._fields["mdfe30_infEmbComb"]
            .comodel_name,
            "l10n_br_mdfe.modal.aquaviario.comboio",
        )
        self.assertEqual(
            len(
                self.env["l10n_br_mdfe.modal.aquaviario.comboio"].search(
                    [("mdfe30_cEmbComb", "=", "NO_RECORD")]
                )
            ),
            0,
        )

    def test_m2o_stacked_to_concrete(self):
        # not stacked because optional
        model = (
            self.env["l10n_br_fiscal.document"]
            ._fields["mdfe30_infSolicNFF"]
            .comodel_name
        )
        self.assertEqual(model, "mdfe.30.infsolicnff")

    # def test_m2o_stacked(self):
    #     # not stacked because optional
    #     mdfe_model = self.env["l10n_br_fiscal.document"]
    #     # mdfe30_cana is optional so its fields shoudn't be stacked
    #     assert "mdfe30_XXX" not in mdfe_model._fields.keys()

    def test_doc_stacking_points(self):
        doc_keys = [
            "mdfe30_ide",
            "mdfe30_infModal",
            "mdfe30_infDoc",
            "mdfe30_tot",
            "mdfe30_infAdic",
            "mdfe30_trem",
            "mdfe30_infANTT",
            "mdfe30_valePed",
            "mdfe30_veicTracao",
            "mdfe30_infBanc",
        ]
        keys = [
            k
            for k in self.env["l10n_br_fiscal.document"]
            .with_context(spec_schema="mdfe", spec_version="30")
            ._get_stacking_points()
            .keys()
        ]
        self.assertEqual(sorted(keys), sorted(doc_keys))

    def test_doc_tree(self):
        base_class = self.env["l10n_br_fiscal.document"]
        tree, visited = self.get_stacked_tree(base_class)
        self.assertEqual(tree, MDFe.INFMDFE_TREE)
        self.assertEqual(len(visited), 6)  # all stacked classes

    # def test_doc_line_stacking_points(self):
    #     line_keys = [
    #         "nfe40_COFINS",
    #         "nfe40_COFINSAliq",
    #         "nfe40_COFINSNT",
    #         "nfe40_COFINSOutr",
    #         "nfe40_COFINSQtde",
    #         "nfe40_COFINSST",
    #         "nfe40_ICMS",
    #         "nfe40_ICMSPart",
    #         "nfe40_ICMSST",
    #         "nfe40_ICMSUFDest",
    #         "nfe40_II",
    #         "nfe40_IPI",
    #         "nfe40_IPINT",
    #         "nfe40_IPITrib",
    #         "nfe40_ISSQN",
    #         "nfe40_PIS",
    #         "nfe40_PISAliq",
    #         "nfe40_PISNT",
    #         "nfe40_PISOutr",
    #         "nfe40_PISQtde",
    #         "nfe40_PISST",
    #         "nfe40_imposto",
    #         "nfe40_prod",
    #     ]
    #     keys = [
    #         k
    #         for k in self.env["l10n_br_fiscal.document.line"]
    #         .with_context(spec_schema="nfe", spec_version="40")
    #         ._get_stacking_points()
    #         .keys()
    #     ]
    #     self.assertEqual(sorted(keys), line_keys)

    # def test_doc_line_tree(self):
    #     base_class = self.env["l10n_br_fiscal.document.line"]
    #     tree, visited = self.get_stacked_tree(base_class)
    #     self.assertEqual(tree, NFeLine.DET_TREE)
    #     self.assertEqual(len(visited), 24)

    # def test_nfref_tree(self):
    #     base_class = self.env["l10n_br_fiscal.document.related"]
    #     tree, visited = self.get_stacked_tree(base_class)
    #     self.assertEqual(tree, NFeRelated.NFREF_TREE)
    #     self.assertEqual(len(visited), 4)

    # def test_m2o_force_stack(self):
    #     pass

    # def test_doc_visit_stack(self):
    #     pass

    # def test_doc_line_visit_stack(self):
    #     pass
