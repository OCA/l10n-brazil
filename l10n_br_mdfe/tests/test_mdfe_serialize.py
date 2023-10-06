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

        FiscalDocument = self.env["l10n_br_fiscal.document"]

        self.acre_state = self.env.ref("base.state_br_ac")
        self.acre_city = self.env.ref("l10n_br_base.city_1200013")
        self.mdfe_document_type_id = self.env.ref("l10n_br_fiscal.document_58")
        self.sn_company_id = self.env.ref("l10n_br_base.empresa_simples_nacional")
        self.serie_id = self.env.ref("l10n_br_fiscal.empresa_sn_document_58_serie_1")
        self.related_nfe_id = self.env.ref("l10n_br_mdfe.demo_mdfe_related_nfe")
        self.formatted_related_nfe_key = FiscalDocument._format_document_key(
            self.related_nfe_id.mdfe30_chNFe
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
        mdfe.mdfe30_codAgPorto = "12345678"

        # infANTT
        mdfe.mdfe30_RNTRC = "12345678"
        mdfe.mdfe30_categCombVeic = "02"
        mdfe.mdfe30_infCIOT = [
            (
                0,
                0,
                {
                    "is_company": False,
                    "mdfe30_CIOT": "123456789101",
                    "mdfe30_CPF": "99999999999",
                },
            ),
        ]
        mdfe.mdfe30_disp = [
            (
                0,
                0,
                {
                    "mdfe30_CNPJForn": "99999999999999",
                    "mdfe30_CNPJPg": "99999999999999",
                    "mdfe30_nCompra": "1234",
                    "mdfe30_vValePed": 5,
                    "mdfe30_tpValePed": "01",
                },
            ),
        ]
        mdfe.mdfe30_infPag = [
            (
                0,
                0,
                {
                    "partner_id": self.env.ref("l10n_br_base.res_partner_intel").id,
                    "mdfe30_vContrato": 5,
                    "mdfe30_indPag": "0",
                    "payment_type": "pix",
                    "mdfe30_PIX": "99999999999999",
                    "mdfe30_comp": [
                        (
                            0,
                            0,
                            {
                                "mdfe30_tpComp": "01",
                                "mdfe30_vComp": 5,
                            },
                        )
                    ],
                },
            ),
        ]

        # veicTracao
        mdfe.mdfe30_cInt = "1"
        mdfe.mdfe30_RENAVAM = "42423325472"
        mdfe.mdfe30_placa = "AAA1233"
        mdfe.mdfe30_tpTransp = False
        mdfe.mdfe30_tara = 7500
        mdfe.mdfe30_capKG = 42500
        mdfe.mdfe30_capM3 = 300
        mdfe.mdfe30_tpRod = "03"
        mdfe.mdfe30_tpCar = "00"
        mdfe.rodo_vehicle_state_id = self.env.ref("base.state_br_ac").id
        mdfe.mdfe30_condutor = [
            (
                0,
                0,
                {
                    "mdfe30_xNome": "Teste",
                    "mdfe30_CPF": "99999999999",
                },
            ),
            (
                0,
                0,
                {
                    "mdfe30_xNome": "Teste2",
                    "mdfe30_CPF": "99999999999",
                },
            ),
        ]

        # veicReboque
        mdfe.mdfe30_veicReboque = [
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
        mdfe.mdfe30_nac = "TEST"
        mdfe.mdfe30_matr = "TEST"
        mdfe.mdfe30_nVoo = "123456789"
        mdfe.mdfe30_cAerEmb = "OACI"
        mdfe.mdfe30_cAerDes = "OACI"
        mdfe.mdfe30_dVoo = datetime.strptime("2020-01-01", "%Y-%m-%d")

    def prepare_modal_aquaviario_data(self, mdfe):
        mdfe.mdfe30_irin = "1234567899"
        mdfe.mdfe30_tpEmb = "01"
        mdfe.mdfe30_cEmbar = "123456"
        mdfe.mdfe30_xEmbar = "teste"
        mdfe.mdfe30_nViag = "123456"
        mdfe.mdfe30_cPrtEmb = "BRADR"
        mdfe.mdfe30_cPrtDest = "BRAFU"
        mdfe.mdfe30_infTermCarreg = [
            (0, 0, {"loading_harbor": "BRADR"}),
            (0, 0, {"loading_harbor": "BRANT"}),
        ]
        mdfe.mdfe30_infTermDescarreg = [
            (0, 0, {"unloading_harbor": "BRAFU"}),
            (0, 0, {"unloading_harbor": "BRBZC"}),
        ]

    def prepare_modal_ferroviario_data(self, mdfe):
        mdfe.mdfe30_dhTrem = datetime.strptime(
            "2020-01-01T11:00:00", "%Y-%m-%dT%H:%M:%S"
        )
        mdfe.mdfe30_xPref = "TES"
        mdfe.mdfe30_xOri = "TES"
        mdfe.mdfe30_xDest = "TES"
        mdfe.mdfe30_qVag = 2
        mdfe.mdfe30_vag = [
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

    def _get_default_document_data(self):
        info_descarregamento = [
            (
                0,
                0,
                {
                    "state_id": self.acre_state.id,
                    "city_id": self.acre_city.id,
                    "document_type": "nfe",
                    "nfe_ids": [(6, 0, [self.related_nfe_id.id])],
                },
            )
        ]

        return {
            "document_type_id": self.mdfe_document_type_id.id,
            "company_id": self.sn_company_id.id,
            "document_serie_id": self.serie_id.id,
            "document_date": datetime.now(),
            "mdfe_initial_state_id": self.acre_state.id,
            "mdfe_final_state_id": self.acre_state.id,
            "mdfe_loading_city_ids": [(4, self.acre_city.id)],
            "mdfe30_infMunDescarga": info_descarregamento,
            "manual_fiscal_additional_data": "FISCAL ADDITIONAL DATA",
            "manual_customer_additional_data": "CUSTOMER ADDITIONAL DATA",
        }

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
