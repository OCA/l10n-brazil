# @ 2024 KMEE INFORMATICA LTDA - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestMDFeDeliveryVehicle(TransactionCase):
    """Tests for the MDF-e vehicle integration with l10n_br_delivery."""

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

    def test_partner_rntrc_compute_and_inverse(self):
        partner = self.env.ref("l10n_br_base.res_partner_intel")
        partner.mdfe30_RNTRC = "12345678"
        self.assertEqual(partner.mdfe30_RNTRC, "12345678")
        self.assertEqual(partner.rntrc_code, "12345678")
        partner.rntrc_code = False
        self.assertFalse(partner.mdfe30_RNTRC)

    def test_partner_rntrc_inverse_invalid(self):
        partner = self.env.ref("l10n_br_base.res_partner_intel")
        with self.assertRaises(ValidationError):
            partner.mdfe30_RNTRC = "123"
        with self.assertRaises(ValidationError):
            partner.mdfe30_RNTRC = "abcdefgh"

    def test_onchange_partner_id(self):
        partner = self.env.ref("l10n_br_base.res_partner_intel")
        condutor = self.env["l10n_br_mdfe.modal.rodoviario.veiculo.condutor"].new(
            {"partner_id": partner.id}
        )
        condutor._onchange_partner_id()
        self.assertEqual(condutor.mdfe30_xNome, partner.legal_name or partner.name)
        self.assertEqual(condutor.mdfe30_CPF, partner.cnpj_cpf)

    def test_get_binding_class(self):
        partner = self.env.ref("l10n_br_base.res_partner_intel")
        prop_class = self.env["mdfe.30.veictracao_prop"]
        binding = partner._get_binding_class(prop_class)
        self.assertEqual(binding.__name__, "Prop")
        reb_class = self.env["mdfe.30.veicreboque_prop"]
        binding = partner._get_binding_class(reb_class)
        self.assertEqual(binding.__name__, "Prop")

    def test_get_binding_class_super_fallback(self):
        """Test that _get_binding_class falls back to super for other classes."""
        partner = self.env.ref("l10n_br_base.res_partner_intel")
        resptec_class = self.env["mdfe.30.tresptec"]
        binding = partner._get_binding_class(resptec_class)
        self.assertIsNotNone(binding)
