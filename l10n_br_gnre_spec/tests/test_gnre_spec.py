# Copyright 2026 KMEE
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGnreSpec(TransactionCase):
    """The generated mixins load in the registry with their xsd metadata."""

    def test_lote_mixins_are_registered(self):
        for model in ("gnre.20.tlotegnre", "gnre.20.guias", "gnre.20.tdadosgnre"):
            self.assertIn(model, self.env)
            self.assertTrue(self.env[model]._abstract)

    def test_xsd_metadata(self):
        lote = self.env["gnre.20.tlotegnre"]
        self.assertTrue(lote._fields["gnre20_versao"].xsd_required)
        guias = self.env["gnre.20.guias"]._fields["gnre20_TDadosGNRE"]
        self.assertEqual(guias.comodel_name, "gnre.20.tdadosgnre")
        self.assertEqual(
            self.env["spec.mixin.gnre"]._gnre20_binding_module,
            "nfelib.gnre.bindings.v2_0.lote_gnre_v2_00",
        )
