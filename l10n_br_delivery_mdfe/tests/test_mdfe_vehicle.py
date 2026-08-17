# Copyright (C) 2026 Madooit
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import TransactionCase


class TestMDFeDeliveryVehicle(TransactionCase):
    """Integration between the MDF-e vehicle data and l10n_br_delivery."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vehicle = cls.env["l10n_br_delivery.carrier.vehicle"].create(
            {
                "name": "Cavalo Truck",
                "plate": "AAA1234",
                "vehicle_code": "01",
                "renavam": "42423325472",
                "tara": "7500",
                "capacity_kg": "42500",
                "capacity_m3": "300",
                "wheel_type": "03",
                "body_type": "02",
                "active": True,
                "state_id": cls.env.ref("base.state_br_ac").id,
            }
        )

    def test_onchange_vehicle_id(self):
        mdfe = self.env.ref("l10n_br_mdfe.demo_mdfe_lc_modal_rodoviario")
        mdfe.vehicle_id = self.vehicle
        mdfe._onchange_vehicle_id()
        self.assertEqual(mdfe.mdfe30_cInt, "01")
        self.assertEqual(mdfe.mdfe30_placa, "AAA1234")
        self.assertEqual(mdfe.mdfe30_RENAVAM, "42423325472")
        self.assertEqual(mdfe.mdfe30_tara, "7500")
        self.assertEqual(mdfe.mdfe30_capKG, "42500")
        self.assertEqual(mdfe.mdfe30_capM3, "300")
        self.assertEqual(mdfe.mdfe30_tpRod, "03")
        self.assertEqual(mdfe.mdfe30_tpCar, "02")
        self.assertEqual(mdfe.rodo_vehicle_state_id, self.vehicle.state_id)

    def test_partner_vehicle_ids(self):
        partner = self.env.ref("l10n_br_base.res_partner_intel")
        vehicle = self.env["l10n_br_delivery.carrier.vehicle"].create(
            {
                "name": "Cavalo Truck 2",
                "plate": "BBB1234",
                "active": True,
                "owner_id": partner.id,
            }
        )
        self.assertIn(vehicle, partner.vehicle_ids)
