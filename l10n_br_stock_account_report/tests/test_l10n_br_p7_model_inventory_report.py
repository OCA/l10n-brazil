# @ 2021 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import SavepointCase


class L10nBRP7ModelInventoryReportTest(SavepointCase):
    """Test Brazilian P7 Model Inventory Report"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.p7_report_wizard = cls.env["l10n_br.p7.model.inventory.report.wizard"]

    def test_l10n_br_p7_model_inventory_report(self):
        """Test Brazilian P7 Model Inventory Report."""

        wizard_obj = self.p7_report_wizard.with_context(
            default_compute_at_date=0,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.print_report()
