# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import os
from datetime import datetime

from xmldiff import main

from odoo.tests.common import TransactionCase
from odoo.tools import config

from odoo.addons import l10n_br_mdfe
from odoo.addons.spec_driven_model import hooks

_logger = logging.getLogger(__name__)


class TestMDFeSerialize(TransactionCase):
    def setUp(self, mdfe_list):
        super().setUp()

        hooks.register_hook(
            self.env,
            "l10n_br_mdfe",
            "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_tipos_basico_v3_00",
        )

        self.mdfe_list = mdfe_list
        for mdfe_data in self.mdfe_list:
            mdfe = self.env.ref(mdfe_data["record_ref"])
            mdfe_data["mdfe"] = mdfe
            self.prepare_test_mdfe(mdfe)

    def prepare_test_mdfe(self, mdfe):
        """
        Performs actions necessary to prepare an MDFe of the demo data to
        perform the tests
        """
        if mdfe.state != "em_digitacao":  # 2nd test run
            mdfe.action_document_back2draft()

        mdfe._compute_amount()
        mdfe.action_document_confirm()
        mdfe.document_date = datetime.strptime(
            "2020-01-01T11:00:00", "%Y-%m-%dT%H:%M:%S"
        )
        mdfe.mdfe30_cMDF = "20801844"

        if mdfe.mdfe_modal == "1":
            self.prepare_modal_rodoviario_data(mdfe)
        elif mdfe.mdfe_modal == "2":
            self.prepare_modal_aereo_data(mdfe)
        elif mdfe.mdfe_modal == "3":
            self.prepare_modal_aquaviario_data(mdfe)
        elif mdfe.mdfe_modal == "4":
            self.prepare_modal_ferroviario_data(mdfe)

        mdfe._document_export()

    def prepare_modal_rodoviario_data(self, mdfe):
        mdfe.rodo_scheduling_code = "12345678"

        # veicTracao
        mdfe.rodo_vehicle_code = "1"
        mdfe.rodo_vehicle_RENAVAM = "42423325472"
        mdfe.rodo_vehicle_plate = "AAA1233"
        mdfe.rodo_vehicle_tare_weight = 7500
        mdfe.rodo_vehicle_kg_capacity = 42500
        mdfe.rodo_vehicle_m3_capacity = 300
        mdfe.rodo_vehicle_tire_type = "03"
        mdfe.rodo_vehicle_type = "00"
        mdfe.rodo_vehicle_state_id = self.env.ref("base.state_br_ac").id
        mdfe.rodo_vehicle_conductor_ids = [
            (
                0,
                0,
                {
                    "mdfe30_xNome": "Teste",
                    "mdfe30_CPF": "78981282064",
                },
            ),
            (
                0,
                0,
                {
                    "mdfe30_xNome": "Teste2",
                    "mdfe30_CPF": "76706683000",
                },
            ),
        ]

        # veicReboque
        mdfe.rodo_tow_ids = [
            (
                0,
                0,
                {
                    "mdfe30_cInt": "2",
                    "mdfe30_placa": "AAA4321",
                    "mdfe30_RENAVAM": "11557770179",
                    "mdfe30_tara": 7200,
                    "mdfe30_capKG": 42500,
                    "mdfe30_capM3": 300,
                    "mdfe30_tpCar": "00",
                    "mdfe30_UF": "AC",
                },
            )
        ]

    def prepare_modal_aereo_data(self, mdfe):
        mdfe.airplane_nationality = "TEST"
        mdfe.airplane_registration = "TEST"
        mdfe.flight_number = "123456789"
        mdfe.boarding_airfield = "OACI"
        mdfe.landing_airfield = "OACI"
        mdfe.flight_date = datetime.strptime("2020-01-01", "%Y-%m-%d")

    def prepare_modal_aquaviario_data(self, mdfe):
        mdfe.ship_irin = "1234567899"
        mdfe.ship_type = "01"
        mdfe.ship_code = "123456"
        mdfe.ship_name = "teste"
        mdfe.ship_travel_number = "123456"
        mdfe.ship_boarding_point = "BRADR"
        mdfe.ship_landing_point = "BRAFU"
        mdfe.ship_loading_ids = [
            (0, 0, {"loading_harbor": "BRADR"}),
            (0, 0, {"loading_harbor": "BRANT"}),
        ]
        mdfe.ship_unloading_ids = [
            (0, 0, {"unloading_harbor": "BRAFU"}),
            (0, 0, {"unloading_harbor": "BRBZC"}),
        ]

    def prepare_modal_ferroviario_data(self, mdfe):
        mdfe.train_release_time = datetime.strptime(
            "2020-01-01T11:00:00", "%Y-%m-%dT%H:%M:%S"
        )
        mdfe.train_prefix = "TES"
        mdfe.train_origin = "TES"
        mdfe.train_destiny = "TES"
        mdfe.train_wagon_quantity = 2
        mdfe.train_wagon_ids = [
            (
                0,
                0,
                {
                    "mdfe30_pesoBC": 500,
                    "mdfe30_pesoR": 1,
                    "mdfe30_tpVag": 123,
                    "mdfe30_serie": 123,
                    "mdfe30_nVag": 123,
                    "mdfe30_nSeq": 123,
                    "mdfe30_TU": 1,
                },
            ),
            (
                0,
                0,
                {
                    "mdfe30_pesoBC": 500,
                    "mdfe30_pesoR": 1,
                    "mdfe30_tpVag": 321,
                    "mdfe30_serie": 321,
                    "mdfe30_nVag": 321,
                    "mdfe30_nSeq": 321,
                    "mdfe30_TU": 1,
                },
            ),
        ]

    def serialize_xml(self, mdfe_data):
        mdfe = mdfe_data["mdfe"]
        xml_path = os.path.join(
            l10n_br_mdfe.__path__[0],
            "tests",
            "mdfe",
            "v3_00",
            "leiauteMDFe",
            mdfe_data["xml_file"],
        )
        output = os.path.join(
            config["data_dir"],
            "filestore",
            self.cr.dbname,
            mdfe.send_file_id.store_fname,
        )

        _logger.info("XML file saved at %s" % (output,))
        return main.diff_files(output, xml_path)
