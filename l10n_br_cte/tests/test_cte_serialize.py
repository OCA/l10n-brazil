# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import os
from datetime import datetime

from xmldiff import main

from odoo.tests.common import TransactionCase
from odoo.tools import config

from odoo.addons import l10n_br_cte

_logger = logging.getLogger(__name__)


class TestCTeSerialize(TransactionCase):
    def setUp(self, cte_list):
        super().setUp()
        self.cte_list = cte_list
        for cte_data in self.cte_list:
            cte = self.env.ref(cte_data["record_ref"])
            cte_data["cte"] = cte
            self.prepare_test_cte(cte)

    def prepare_test_cte(self, cte):
        """
        Performs actions necessary to prepare an CTe of the demo data to
        perform the tests
        """
        if cte.state != "em_digitacao":  # 2nd test run
            cte.action_document_back2draft()

        cte._compute_amount()
        cte.action_document_confirm()
        cte.document_date = datetime.strptime(
            "2020-01-01T11:00:00", "%Y-%m-%dT%H:%M:%S"
        )
        cte.cte40_cMDF = "20801844"

        if cte.cte_modal == "1":
            self.prepare_modal_rodoviario_data(cte)
        elif cte.cte_modal == "2":
            self.prepare_modal_aereo_data(cte)
        elif cte.cte_modal == "3":
            self.prepare_modal_aquaviario_data(cte)
        elif cte.cte_modal == "4":
            self.prepare_modal_ferroviario_data(cte)

        cte._document_export()

    def prepare_modal_rodoviario_data(self, cte):
        cte.cte40_codAgPorto = "12345678"

        # infANTT
        cte.cte40_RNTRC = "12345678"
        cte.cte40_categCombVeic = "02"
        cte.cte40_infCIOT = [
            (
                0,
                0,
                {
                    "is_company": False,
                    "cte40_CIOT": "123456789101",
                    "cte40_CPF": "99999999999",
                },
            ),
        ]
        cte.cte40_disp = [
            (
                0,
                0,
                {
                    "cte40_CNPJForn": "99999999999999",
                    "cte40_CNPJPg": "99999999999999",
                    "cte40_nCompra": "1234",
                    "cte40_vValePed": 5,
                    "cte40_tpValePed": "01",
                },
            ),
        ]
        cte.cte40_infPag = [
            (
                0,
                0,
                {
                    "partner_id": self.env.ref("l10n_br_base.res_partner_intel").id,
                    "cte40_vContrato": 5,
                    "cte40_indPag": "0",
                    "payment_type": "pix",
                    "cte40_PIX": "99999999999999",
                    "cte40_comp": [
                        (
                            0,
                            0,
                            {
                                "cte40_tpComp": "01",
                                "cte40_vComp": 5,
                            },
                        )
                    ],
                },
            ),
        ]

        # veicTracao
        cte.cte40_cInt = "1"
        cte.cte40_RENAVAM = "42423325472"
        cte.cte40_placa = "AAA1233"
        cte.cte40_tpTransp = False
        cte.cte40_tara = 7500
        cte.cte40_capKG = 42500
        cte.cte40_capM3 = 300
        cte.cte40_tpRod = "03"
        cte.cte40_tpCar = "00"
        cte.rodo_vehicle_state_id = self.env.ref("base.state_br_ac").id
        cte.cte40_condutor = [
            (
                0,
                0,
                {
                    "cte40_xNome": "Teste",
                    "cte40_CPF": "99999999999",
                },
            ),
            (
                0,
                0,
                {
                    "cte40_xNome": "Teste2",
                    "cte40_CPF": "99999999999",
                },
            ),
        ]

        # veicReboque
        cte.cte40_veicReboque = [
            (
                0,
                0,
                {
                    "cte40_cInt": "2",
                    "cte40_placa": "AAA4321",
                    "cte40_RENAVAM": "11557770179",
                    "cte40_tara": 7200,
                    "cte40_capKG": 42500,
                    "cte40_capM3": 300,
                    "cte40_tpCar": "00",
                    "cte40_UF": "AC",
                },
            )
        ]

    def prepare_modal_aereo_data(self, cte):
        cte.cte40_nac = "TEST"
        cte.cte40_matr = "TEST"
        cte.cte40_nVoo = "123456789"
        cte.cte40_cAerEmb = "OACI"
        cte.cte40_cAerDes = "OACI"
        cte.cte40_dVoo = datetime.strptime("2020-01-01", "%Y-%m-%d")

    def prepare_modal_aquaviario_data(self, cte):
        cte.cte40_irin = "1234567899"
        cte.cte40_tpEmb = "01"
        cte.cte40_cEmbar = "123456"
        cte.cte40_xEmbar = "teste"
        cte.cte40_nViag = "123456"
        cte.cte40_cPrtEmb = "BRADR"
        cte.cte40_cPrtDest = "BRAFU"
        cte.cte40_infTermCarreg = [
            (0, 0, {"loading_harbor": "BRADR"}),
            (0, 0, {"loading_harbor": "BRANT"}),
        ]
        cte.cte40_infTermDescarreg = [
            (0, 0, {"unloading_harbor": "BRAFU"}),
            (0, 0, {"unloading_harbor": "BRBZC"}),
        ]

    def prepare_modal_ferroviario_data(self, cte):
        cte.cte40_dhTrem = datetime.strptime("2020-01-01T11:00:00", "%Y-%m-%dT%H:%M:%S")
        cte.cte40_xPref = "TES"
        cte.cte40_xOri = "TES"
        cte.cte40_xDest = "TES"
        cte.cte40_qVag = 2
        cte.cte40_vag = [
            (
                0,
                0,
                {
                    "cte40_pesoBC": 500,
                    "cte40_pesoR": 1,
                    "cte40_tpVag": 123,
                    "cte40_serie": 123,
                    "cte40_nVag": 123,
                    "cte40_nSeq": 123,
                    "cte40_TU": 1,
                },
            ),
            (
                0,
                0,
                {
                    "cte40_pesoBC": 500,
                    "cte40_pesoR": 1,
                    "cte40_tpVag": 321,
                    "cte40_serie": 321,
                    "cte40_nVag": 321,
                    "cte40_nSeq": 321,
                    "cte40_TU": 1,
                },
            ),
        ]

    def serialize_xml(self, cte_data):
        cte = cte_data["cte"]
        xml_path = os.path.join(
            l10n_br_cte.__path__[0],
            "tests",
            "cte",
            "V4_00",
            "leiauteCTe",
            cte_data["xml_file"],
        )
        output = os.path.join(
            config["data_dir"],
            "filestore",
            self.cr.dbname,
            cte.send_file_id.store_fname,
        )
        _logger.info(f"XML file saved at {output}")
        diff = main.diff_files(output, xml_path)
        return diff
