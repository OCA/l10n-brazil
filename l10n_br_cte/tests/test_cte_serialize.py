# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
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

        cte.fiscal_line_ids.name = "Frete"
        cte.fiscal_line_ids._onchange_fiscal_operation_line_id()
        cte.fiscal_line_ids.cfop_id = cte.env.ref("l10n_br_fiscal.cfop_5352")
        cte._compute_amount()

        cte.action_document_confirm()
        cte.document_date = datetime.strptime(
            "2020-01-01T11:00:00", "%Y-%m-%dT%H:%M:%S"
        )
        cte.cte40_cCT = "57000111"

        if cte.cte_modal == "01":
            self.prepare_modal_rodoviario_data(cte)
        elif cte.cte_modal == "02":
            self.prepare_modal_aereo_data(cte)
        elif cte.cte_modal == "03":
            self.prepare_modal_aquaviario_data(cte)
        elif cte.cte_modal == "04":
            self.prepare_modal_ferroviario_data(cte)

        cte._document_export()

    def prepare_modal_rodoviario_data(self, cte):
        cte.cte40_RNTRC = "12345678"
        cte.cte40_occ = [
            (
                0,
                0,
                {
                    "cte40_serie": "01",
                    "cte40_nOcc": "01",
                    "cte40_cInt": "XYZ",
                },
            ),
            (
                0,
                0,
                {
                    "cte40_serie": "02",
                    "cte40_nOcc": "02",
                    "cte40_cInt": "ABC",
                },
            ),
        ]

    def prepare_modal_aereo_data(self, cte):
        pass
        # cte.cte40_nac = "TEST"
        # cte.cte40_matr = "TEST"
        # cte.cte40_nVoo = "123456789"
        # cte.cte40_cAerEmb = "OACI"
        # cte.cte40_cAerDes = "OACI"
        # cte.cte40_dVoo = datetime.strptime("2020-01-01", "%Y-%m-%d")

    def prepare_modal_aquaviario_data(self, cte):
        pass
        # cte.cte40_irin = "1234567899"
        # cte.cte40_tpEmb = "01"
        # cte.cte40_cEmbar = "123456"
        # cte.cte40_xEmbar = "teste"
        # cte.cte40_nViag = "123456"
        # cte.cte40_cPrtEmb = "BRADR"
        # cte.cte40_cPrtDest = "BRAFU"
        # cte.cte40_infTermCarreg = [
        #     (0, 0, {"loading_harbor": "BRADR"}),
        #     (0, 0, {"loading_harbor": "BRANT"}),
        # ]
        # cte.cte40_infTermDescarreg = [
        #     (0, 0, {"unloading_harbor": "BRAFU"}),
        #     (0, 0, {"unloading_harbor": "BRBZC"}),
        # ]

    def prepare_modal_ferroviario_data(self, cte):
        pass
        # cte.cte40_dhTrem = datetime.strptime(
        #   "2020-01-01T11:00:00", "%Y-%m-%dT%H:%M:%S")
        # cte.cte40_xPref = "TES"
        # cte.cte40_xOri = "TES"
        # cte.cte40_xDest = "TES"
        # cte.cte40_qVag = 2
        # cte.cte40_vag = [
        #     (
        #         0,
        #         0,
        #         {
        #             "cte40_pesoBC": 500,
        #             "cte40_pesoR": 1,
        #             "cte40_tpVag": 123,
        #             "cte40_serie": 123,
        #             "cte40_nVag": 123,
        #             "cte40_nSeq": 123,
        #             "cte40_TU": 1,
        #         },
        #     ),
        #     (
        #         0,
        #         0,
        #         {
        #             "cte40_pesoBC": 500,
        #             "cte40_pesoR": 1,
        #             "cte40_tpVag": 321,
        #             "cte40_serie": 321,
        #             "cte40_nVag": 321,
        #             "cte40_nSeq": 321,
        #             "cte40_TU": 1,
        #         },
        #     ),
        # ]

    def serialize_xml(self, cte_data):
        cte = cte_data["cte"]
        xml_path = os.path.join(
            l10n_br_cte.__path__[0],
            "tests",
            "cte",
            "v4_00",
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
