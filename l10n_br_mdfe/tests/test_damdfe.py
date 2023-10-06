# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from datetime import datetime

from odoo.exceptions import UserError

from .test_mdfe_serialize import TestMDFeSerialize


class MDFeDAMDFeTest(TestMDFeSerialize):
    def setUp(self):
        super().setUp(mdfe_list=[])

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

        self._create_documents()

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

    def _create_documents(self):
        FiscalDocument = self.env["l10n_br_fiscal.document"]
        default_document_data = self._get_default_document_data()

        self.mdfe_modal_rodoviario_id = FiscalDocument.create(
            {**default_document_data, "document_number": "70000", "mdfe_modal": "1"}
        )
        self.mdfe_modal_aereo_id = FiscalDocument.create(
            {**default_document_data, "document_number": "71000", "mdfe_modal": "2"}
        )
        self.mdfe_modal_aquaviario_id = FiscalDocument.create(
            {**default_document_data, "document_number": "72000", "mdfe_modal": "3"}
        )
        self.mdfe_modal_ferroviario_id = FiscalDocument.create(
            {**default_document_data, "document_number": "73000", "mdfe_modal": "4"}
        )

        self.prepare_test_mdfe(self.mdfe_modal_rodoviario_id)
        self.prepare_test_mdfe(self.mdfe_modal_aereo_id)
        self.prepare_test_mdfe(self.mdfe_modal_aquaviario_id)
        self.prepare_test_mdfe(self.mdfe_modal_ferroviario_id)

    def check_document_key(self, key):
        pattern = r"^\d{4}( \d{4}){10}$"
        match = re.match(pattern, key)
        self.assertTrue(match)

    def check_common_damdfe_data(self, data):
        self.assertEqual(data["company_id"], self.sn_company_id.id)
        self.assertEqual(data["company_has_logo"], bool(self.sn_company_id.logo))
        self.assertEqual(data["company_ie"], self.sn_company_id.inscr_est)
        self.assertEqual(data["company_cnpj"], self.sn_company_id.cnpj_cpf)
        self.assertEqual(data["company_legal_name"], self.sn_company_id.legal_name)
        self.assertEqual(data["company_street"], self.sn_company_id.street)
        self.assertEqual(data["company_city"], self.sn_company_id.city_id.display_name)
        self.assertEqual(data["company_state"], self.sn_company_id.state_id.code)
        self.assertEqual(data["company_zip"], self.sn_company_id.zip)
        self.assertEqual(data["uf_carreg"], "AC")
        self.assertEqual(data["uf_descarreg"], "AC")
        self.assertEqual(data["weight_measure"], "KG")
        self.assertEqual(data["document_model"], self.mdfe_document_type_id.code)
        self.assertEqual(data["document_serie"], "1")
        self.assertEqual(data["environment"], "2")
        self.assertEqual(data["fiscal_additional_data"], "FISCAL ADDITIONAL DATA")
        self.assertEqual(data["customer_additional_data"], "CUSTOMER ADDITIONAL DATA")
        self.assertEqual(
            data["total_weight"], self.related_nfe_id.document_total_weight
        )
        self.assertEqual(data["qt_nfe"], "1")
        self.assertEqual(
            data["document_info"]["documents"][0]["key"],
            "NFe - %s" % self.formatted_related_nfe_key,
        )

        self.assertFalse(data["contingency"])
        self.assertFalse(data["qt_cte"])
        self.assertFalse(data["qt_mdfe"])

    def test_damdfe_rodoviario(self):
        self.mdfe_modal_rodoviario_id.document_type_id = False
        with self.assertRaises(UserError):
            self.mdfe_modal_rodoviario_id.view_pdf()

        self.mdfe_modal_rodoviario_id.document_type_id = self.mdfe_document_type_id
        report = self.mdfe_modal_rodoviario_id.view_pdf()
        report_action = report["context"]["report_action"]
        self.assertEqual(report_action["report_name"], "l10n_br_mdfe.report_damdfe")

        report_data = report["context"]["report_action"]["data"]
        self.check_common_damdfe_data(report_data)

        self.assertEqual(report_data["modal_str"], "Rodoviário")
        self.check_document_key(report_data["document_key"])
        self.assertFalse(report_data["modal_aereo_data"])

        vehicles = report_data["modal_rodoviario_data"]["vehicles"]
        self.assertEqual(len(vehicles), 2)
        self.assertEqual(
            vehicles[0]["RNTRC"], self.mdfe_modal_rodoviario_id.mdfe30_RNTRC
        )
        self.assertEqual(
            vehicles[0]["plate"], self.mdfe_modal_rodoviario_id.mdfe30_placa
        )

        reboque = self.mdfe_modal_rodoviario_id.mdfe30_veicReboque
        self.assertEqual(len(reboque), 1)
        self.assertFalse(vehicles[1]["RNTRC"])
        self.assertEqual(vehicles[1]["plate"], reboque[0].mdfe30_placa)

        report_conductors = report_data["modal_rodoviario_data"]["conductors"]
        mdfe_conductors = self.mdfe_modal_rodoviario_id.mdfe30_condutor
        self.assertEqual(len(report_conductors), len(mdfe_conductors))
        self.assertEqual(report_conductors[0]["name"], mdfe_conductors[0].mdfe30_xNome)
        self.assertEqual(report_conductors[0]["cpf"], mdfe_conductors[0].mdfe30_CPF)

        report_toll = report_data["modal_rodoviario_data"]["toll"]
        mdfe_toll = self.mdfe_modal_rodoviario_id.mdfe30_disp
        self.assertEqual(len(report_toll), len(mdfe_toll))
        self.assertEqual(report_toll[0]["resp_cnpj"], mdfe_toll[0].mdfe30_CNPJPg)
        self.assertEqual(report_toll[0]["forn_cnpj"], mdfe_toll[0].mdfe30_CNPJForn)
        self.assertEqual(report_toll[0]["purchase_number"], mdfe_toll[0].mdfe30_nCompra)

        report_ciot = report_data["modal_rodoviario_data"]["ciot"]
        mdfe_ciot = self.mdfe_modal_rodoviario_id.mdfe30_infCIOT
        self.assertEqual(len(report_ciot), len(mdfe_ciot))
        self.assertEqual(report_ciot[0]["code"], mdfe_ciot[0].mdfe30_CIOT)

    def test_damdfe_aereo(self):
        report = self.mdfe_modal_aereo_id.view_pdf()
        report_data = report["context"]["report_action"]["data"]
        self.check_common_damdfe_data(report_data)

        self.assertEqual(report_data["modal_str"], "Aéreo")
        self.check_document_key(report_data["document_key"])
        self.assertFalse(report_data["modal_rodoviario_data"])

        modal_data = report_data["modal_aereo_data"]
        self.assertEqual(modal_data["mdfe30_nac"], self.mdfe_modal_aereo_id.mdfe30_nac)
        self.assertEqual(
            modal_data["mdfe30_matr"], self.mdfe_modal_aereo_id.mdfe30_matr
        )
        self.assertEqual(
            modal_data["mdfe30_nVoo"], self.mdfe_modal_aereo_id.mdfe30_nVoo
        )
        self.assertEqual(
            modal_data["mdfe30_dVoo"],
            self.mdfe_modal_aereo_id.mdfe30_dVoo.strftime("%d/%m/%y"),
        )
        self.assertEqual(
            modal_data["mdfe30_cAerEmb"], self.mdfe_modal_aereo_id.mdfe30_cAerEmb
        )
        self.assertEqual(
            modal_data["mdfe30_cAerDes"], self.mdfe_modal_aereo_id.mdfe30_cAerDes
        )

    def test_damdfe_aquaviario(self):
        report = self.mdfe_modal_aquaviario_id.view_pdf()
        report_data = report["context"]["report_action"]["data"]
        self.check_common_damdfe_data(report_data)

        self.assertEqual(report_data["modal_str"], "Aquaviário")
        self.check_document_key(report_data["document_key"])
        self.assertFalse(report_data["modal_aereo_data"])

        report_loading = report_data["modal_aquaviario_data"]["loading"]
        mdfe_loading = self.mdfe_modal_aquaviario_id.mdfe30_infTermCarreg
        self.assertEqual(len(report_loading), len(mdfe_loading))
        self.assertEqual(
            report_loading[0]["city_code"], mdfe_loading[0].mdfe30_cTermCarreg
        )
        self.assertEqual(
            report_loading[0]["city_name"], mdfe_loading[0].mdfe30_xTermCarreg
        )

        report_unloading = report_data["modal_aquaviario_data"]["unloading"]
        mdfe_unloading = self.mdfe_modal_aquaviario_id.mdfe30_infTermDescarreg
        self.assertEqual(len(report_unloading), len(mdfe_unloading))
        self.assertEqual(
            report_unloading[0]["city_code"], mdfe_unloading[0].mdfe30_cTermDescarreg
        )
        self.assertEqual(
            report_unloading[0]["city_name"], mdfe_unloading[0].mdfe30_xTermDescarreg
        )

    def test_damdfe_ferroviario(self):
        report = self.mdfe_modal_ferroviario_id.view_pdf()
        report_data = report["context"]["report_action"]["data"]
        self.check_common_damdfe_data(report_data)

        self.assertEqual(report_data["modal_str"], "Ferroviário")
        self.check_document_key(report_data["document_key"])
        self.assertFalse(report_data["modal_aereo_data"])

        modal_data = report_data["modal_ferroviario_data"]
        self.assertEqual(
            modal_data["prefix"], self.mdfe_modal_ferroviario_id.mdfe30_xPref
        )
        self.assertEqual(
            modal_data["release_time"],
            self.mdfe_modal_ferroviario_id.mdfe30_dhTrem.strftime("%d/%m/%y %H:%M:%S"),
        )
        self.assertEqual(
            modal_data["origin"], self.mdfe_modal_ferroviario_id.mdfe30_xOri
        )
        self.assertEqual(
            modal_data["destiny"], self.mdfe_modal_ferroviario_id.mdfe30_xDest
        )
        self.assertEqual(
            modal_data["wagon_qty"], self.mdfe_modal_ferroviario_id.mdfe30_qVag
        )

        report_wagons = modal_data["wagons"]
        mdfe_wagons = self.mdfe_modal_ferroviario_id.mdfe30_vag
        self.assertEqual(len(report_wagons), len(mdfe_wagons))
        self.assertEqual(report_wagons[0]["serie"], mdfe_wagons[0].mdfe30_serie)
        self.assertEqual(report_wagons[0]["number"], mdfe_wagons[0].mdfe30_nVag)
        self.assertEqual(report_wagons[0]["seq"], mdfe_wagons[0].mdfe30_nSeq)
        self.assertEqual(report_wagons[0]["ton"], mdfe_wagons[0].mdfe30_TU)
