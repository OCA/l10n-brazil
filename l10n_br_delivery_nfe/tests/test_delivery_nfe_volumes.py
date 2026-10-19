# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command
from odoo.tests.common import TransactionCase


class TestDeliveryNFeVolumes(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document = cls.env.ref("l10n_br_nfe.demo_nfe_natural_icms_7_resale")
        if cls.document.state_edoc != "em_digitacao":
            cls.document.action_document_back2draft()
        cls.document._register_hook()

    def test_volume_list_columns(self):
        """The volume list shows quantity, kind, brand and weights."""
        view = self.env["nfe.40.vol"].get_view(view_type="list")
        arch = view["arch"]
        for name in (
            "nfe40_qVol",
            "nfe40_esp",
            "nfe40_marca",
            "nfe40_pesoL",
            "nfe40_pesoB",
        ):
            self.assertIn(f'name="{name}"', arch)

    def test_total_weight_sums_volumes(self):
        """Total weight follows the gross weight of the volumes."""
        self.document.nfe40_vol = [Command.clear()]
        self.document.nfe40_vol = [
            Command.create(
                {
                    "nfe40_qVol": "3",
                    "nfe40_esp": "Caixa",
                    "nfe40_pesoL": 90.0,
                    "nfe40_pesoB": 100.0,
                }
            ),
            Command.create(
                {
                    "nfe40_qVol": "2",
                    "nfe40_esp": "Caixa",
                    "nfe40_pesoL": 80.0,
                    "nfe40_pesoB": 89.0,
                }
            ),
        ]
        self.assertEqual(self.document.total_weight, 189.0)
        self.document.nfe40_vol[0].nfe40_pesoB = 111.0
        self.assertEqual(self.document.total_weight, 200.0)
