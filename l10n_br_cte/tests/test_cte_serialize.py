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
        elif cte.cte_modal == "05":
            self.prepare_modal_dutoviario_data(cte)

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
        # Dados gerais do modal aéreo
        cte.cte40_nMinu = "TEST123"  # Número do Minuta
        cte.cte40_nOCA = "OCA56789"  # Número do OCA
        cte.cte40_dPrevAereo = datetime.strptime(
            "2024-11-22", "%Y-%m-%d"
        ).date()  # Data prevista de entrega
        cte.cte40_CL = "TEST_CL"  # Código de Localidade
        cte.cte40_cTar = "TAR123"  # Código da Tarifa
        cte.cte40_vTar = 2500.00  # Valor da Tarifa
        cte.cte40_xDime = "Dimensão Padrão"  # Dimensões do volume

        # Lista de produtos perigosos
        cte.cte40_peri = [
            (
                0,
                0,
                {
                    "cte40_nONU": "1234",  # Número ONU do produto perigoso
                    "cte40_qTotEmb": "15",  # Quantidade total de volumes embarcados
                    "cte40_qTotProd": 300.0,  # Quantidade total do produto perigoso
                    "cte40_uniAP": "1",  # Unidade de Medida do Produto
                },
            ),
            (
                0,
                0,
                {
                    "cte40_nONU": "5678",
                    "cte40_qTotEmb": "20",
                    "cte40_qTotProd": 500.0,
                    "cte40_uniAP": "3",
                },
            ),
        ]

    def prepare_modal_aquaviario_data(self, cte):
        # Dados gerais do modal aquaviário
        cte.cte40_vAFRMM = (
            1200.00  # Valor do Adicional de Frete para Renovação da Marinha Mercante
        )
        # cte.cte40_vPrest = 3500.00  # Valor total do frete aquaviário
        cte.cte40_xNavio = "Navio Mercante 123"  # Nome do navio
        cte.cte40_nViag = "Viagem001"  # Número da viagem
        cte.cte40_direc = "S"  # Direção de navegação: 1 = Cabotagem, 2 = Longo curso
        cte.cte40_irin = "IRIN12345"  # Inscrição do Registro Internacional de Navios
        cte.cte40_tpNav = "0"  # Tipo de navegação: 01 = Interior, 02 = Cabotagem, etc.

        # Informações das balsas transportadas
        cte.cte40_balsa = [
            (
                0,
                0,
                {
                    "cte40_xBalsa": "Balsa A",  # Identificador da primeira balsa
                },
            ),
            (
                0,
                0,
                {
                    "cte40_xBalsa": "Balsa B",  # Identificador da segunda balsa
                },
            ),
        ]

    def prepare_modal_dutoviario_data(self, cte):
        # Dados gerais do modal dutoviário
        cte.cte40_dIni = "2024-01-01"  # Data de início da operação dutoviária
        cte.cte40_dFim = "2024-12-31"  # Data de término da operação dutoviária
        cte.cte40_vTar = 1500.00  # Valor da tarifa aplicada no transporte

    def prepare_modal_ferroviario_data(self, cte):
        # Dados gerais do modal ferroviário
        cte.cte40_tpTraf = "1"  # Tipo de Tráfego: 1 = Nacional, 2 = Internacional
        cte.cte40_fluxo = "Fluxo Norte-Sul"  # Fluxo de transporte
        cte.cte40_vFrete = 5000.00  # Valor do frete ferroviário
        cte.cte40_chCTeFerroOrigem = (
            "CTE123456789"  # Chave do CTe Ferroviário de origem
        )
        cte.cte40_respFat = (
            "1"  # Responsável pelo Faturamento: 1 = Emitente, 2 = Receptor
        )
        cte.cte40_ferrEmi = (
            "1"  # Emissor do documento: 1 = Ferrovia Emitente, 2 = Outro
        )
        # cte.cte40_ferroEnv = [
        #     (
        #         0,
        #         0,
        #         {
        #             "cte40_CNPJ": "12345678000199",  # CNPJ da ferrovia envolvida
        #             "cte40_cInt": "FERRO001",  # Código interno da ferrovia
        #             "cte40_IE": "ISENTO",  # Inscrição Estadual
        #             "cte40_xNome": "Ferrovia Teste LTDA",  # Nome ou razão social
        #             "cte40_enderFerro": (
        #                 0,
        #                 0,
        #                 {
        #                     "cte40_xLgr": "Rua da Ferrovia",
        #                     "cte40_nro": "123",
        #                     "cte40_xCpl": "Prédio 2",
        #                     "cte40_xBairro": "Centro",
        #                     "cte40_cMun": "1234567",  # Código do município IBGE
        #                     "cte40_xMun": "Cidade Ferrovia",
        #                     "cte40_CEP": "12345000",
        #                     "cte40_UF": "SP",  # Unidade Federativa
        #                 },
        #             ),
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
