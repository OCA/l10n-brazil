# Copyright 2021 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from io import StringIO

from odoo.tests import TransactionCase

from odoo.addons.spec_driven_model import hooks
from odoo.addons.spec_driven_model.models.spec_models import SpecModel

from ..models.document import NFe
from ..models.document_line import NFeLine
from ..models.document_related import NFeRelated


class NFeStructure(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        hooks.register_hook(
            cls.env,
            "l10n_br_nfe",
            "odoo.addons.l10n_br_nfe_spec.models.v4_0.leiaute_nfe_v4_00",
        )

    @classmethod
    def get_stacked_tree(cls, klass):
        """
        # > means the content of the m2o is stacked in the parent
        # - means standard m2o. Eventually followd by the mapped Odoo model
        # ≡ means o2m. Eventually followd by the mapped Odoo model
        """
        spec_module = "odoo.addons.l10n_br_nfe_spec.models.v4_0.leiaute_nfe_v4_00"
        node = SpecModel._odoo_name_to_class(klass._stacked, spec_module)
        tree = StringIO()
        visited = set()
        for kind, n, path, field_path, child_concrete in klass._visit_stack(
            cls.env, node
        ):
            visited.add(n)
            path_items = path.split(".")
            indent = "    ".join(["" for i in range(0, len(path_items))])
            if kind == "stacked":
                line = "\n{}> <{}>".format(indent, path.split(".")[-1])
            elif kind == "one2many":
                line = "\n{}    \u2261 <{}> {}".format(
                    indent,
                    field_path,
                    child_concrete or "",
                )
            elif kind == "many2one":
                line = "\n{}    - <{}> {}".format(
                    indent, field_path, child_concrete or ""
                )
            tree.write(line.rstrip())
        tree_txt = tree.getvalue()
        # print(tree_txt)
        return tree_txt, visited

    def test_inherited_fields(self):
        assert "nfe40_CNPJ" in self.env["res.company"]._fields.keys()

    def test_concrete_spec(self):
        # this ensure basic SQL is set up
        self.assertEqual(
            len(self.env["nfe.40.vol"].search([("nfe40_marca", "=", "NO_RECORD")])), 0
        )

    def test_m2o_concrete_to_concrete_spec(self):
        self.assertEqual(
            self.env["nfe.40.lacres"]._fields["nfe40_lacres_vol_id"].comodel_name,
            "nfe.40.vol",
        )

    def test_o2m_concrete_to_concrete_spec(self):
        self.assertEqual(
            self.env["nfe.40.vol"]._fields["nfe40_lacres"].comodel_name, "nfe.40.lacres"
        )
        self.assertEqual(
            len(self.env["nfe.40.lacres"].search([("nfe40_nLacre", "=", "NO_RECORD")])),
            0,
        )

    def test_m2o_stacked_to_odoo(self):
        self.assertEqual(
            self.env["l10n_br_fiscal.document"]._fields["nfe40_dest"].comodel_name,
            "res.partner",
        )
        self.assertEqual(
            self.env["l10n_br_fiscal.document"]
            ._fields["nfe40_infRespTec"]
            .comodel_name,
            "res.partner",
        )

    def test_o2m_to_odoo(self):
        pass  # any such example?

    def test_m2o_stacked_to_concrete(self):
        # not stacked because optional
        avulsa_model = (
            self.env["l10n_br_fiscal.document"]._fields["nfe40_avulsa"].comodel_name
        )
        self.assertEqual(avulsa_model, "nfe.40.avulsa")

    def test_m2o_stacked(self):
        # not stacked because optional
        nfe_model = self.env["l10n_br_fiscal.document"]
        # nfe40_cana is optional so its fields shoudn't be stacked
        assert "nfe40_safra" not in nfe_model._fields.keys()

    def test_doc_stacking_points(self):
        doc_keys = [
            "nfe40_ICMSTot",
            "nfe40_ISSQNtot",
            "nfe40_exporta",
            "nfe40_ide",
            "nfe40_infAdic",
            "nfe40_pag",
            "nfe40_refECF",
            "nfe40_refNF",
            "nfe40_refNFP",
            "nfe40_retTrib",
            "nfe40_total",
            "nfe40_transp",
            "nfe40_cobr",
            "nfe40_fat",
        ]
        keys = [k for k in self.env["l10n_br_fiscal.document"]._stacking_points.keys()]
        self.assertEqual(sorted(keys), sorted(doc_keys))

    def test_doc_tree(self):
        base_class = self.env["l10n_br_fiscal.document"]
        tree, visited = self.get_stacked_tree(base_class)
        self.assertEqual(tree, NFe.INFNFE_TREE)
        self.assertEqual(len(visited), 12)  # all stacked classes

    def test_doc_line_stacking_points(self):
        line_keys = [
            "nfe40_COFINS",
            "nfe40_COFINSAliq",
            "nfe40_COFINSNT",
            "nfe40_COFINSOutr",
            "nfe40_COFINSQtde",
            "nfe40_COFINSST",
            "nfe40_ICMS",
            "nfe40_ICMSPart",
            "nfe40_ICMSST",
            "nfe40_ICMSUFDest",
            "nfe40_II",
            "nfe40_IPI",
            "nfe40_IPINT",
            "nfe40_IPITrib",
            "nfe40_ISSQN",
            "nfe40_PIS",
            "nfe40_PISAliq",
            "nfe40_PISNT",
            "nfe40_PISOutr",
            "nfe40_PISQtde",
            "nfe40_PISST",
            "nfe40_imposto",
            "nfe40_prod",
        ]
        keys = [
            k for k in self.env["l10n_br_fiscal.document.line"]._stacking_points.keys()
        ]
        self.assertEqual(sorted(keys), line_keys)

    def test_doc_line_tree(self):
        base_class = self.env["l10n_br_fiscal.document.line"]
        tree, visited = self.get_stacked_tree(base_class)
        self.assertEqual(tree, NFeLine.DET_TREE)
        self.assertEqual(len(visited), 24)

    def test_nfref_tree(self):
        base_class = self.env["l10n_br_fiscal.document.related"]
        tree, visited = self.get_stacked_tree(base_class)
        self.assertEqual(tree, NFeRelated.NFREF_TREE)
        self.assertEqual(len(visited), 4)

    def test_m2o_force_stack(self):
        pass

    def test_doc_visit_stack(self):
        pass

    def test_doc_line_visit_stack(self):
        pass
