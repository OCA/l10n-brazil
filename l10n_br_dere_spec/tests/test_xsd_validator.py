# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_dere_spec.models import xsd_validator


@tagged("post_install", "-at_install")
class TestDereXsdValidator(TransactionCase):
    def test_official_event_schemas_load(self):
        filenames = (*xsd_validator.EVENT_SCHEMA.values(), xsd_validator.LOTE_SCHEMA)
        for filename in filenames:
            schema = xsd_validator._schema(filename)
            self.assertTrue(schema)

    def test_invalid_d1199_is_reported(self):
        xml = (
            '<DeRE xmlns="http://www.dere.gov.br/schemas/evtFechMensal/v0_0_2">'
            '<evtFechMensal id="not-a-valid-id"/>'
            "</DeRE>"
        )
        errors = xsd_validator.validate(xml, "D-1199")
        self.assertTrue(errors)

    def test_unknown_event_type_raises(self):
        with self.assertRaises(ValueError):
            xsd_validator.validate("<DeRE/>", "D-9999")
