# Copyright 2026 Engenere.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestNFeAutXMLComodel(TransactionCase):
    def test_invoice_autxml_field_points_to_the_concrete_model(self):
        """account.move inherits nfe40_autXML through _inherits.

        Its copy of the field must point to the concrete l10n_br_nfe.autxml
        whatever the module loading order, or creating an invoice fails
        with "Invalid field 'partner_id' on model 'nfe.40.autxml'".
        """
        field = self.env["account.move"]._fields["nfe40_autXML"]
        self.assertEqual(field.comodel_name, "l10n_br_nfe.autxml")
