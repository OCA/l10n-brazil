# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from unittest import mock

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import EVENT_ENV_HML


class CTeDocumentTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        FiscalDocument = cls.env["l10n_br_fiscal.document"]

        cls.acre_state = cls.env.ref("base.state_br_ac")
        cls.cte_document_type_id = cls.env.ref("l10n_br_fiscal.document_57")
        cls.sn_company_id = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.sn_company_id.processador_edoc = "oca"
        cls.cte_id = FiscalDocument.create(
            {
                "document_type_id": cls.cte_document_type_id.id,
                "company_id": cls.sn_company_id.id,
                "document_number": "70000",
                "document_serie": "30",
                "document_date": datetime.now(),
            }
        )

    # TODO: Tratar
    # def test_cte_compute_fields(self):
    #     self.cte_id.fiscal_additional_data = "TEST FISCAL ADDITIONAL DATA"
    #     self.cte_id.customer_additional_data = "TEST CUSTOMER ADDITIONAL DATA"

    #     self.assertTrue(self.cte_id.cte40_infAdFisco)
    #     self.assertTrue(self.cte_id.cte40_infCpl)

    # TODO: Tratar
    # def test_cte_inverse_fields(self):
    #     self.cte_id.cte40_UFIni = self.acre_state.code
    #     self.cte_id.cte40_UFFim = self.acre_state.code
    #     self.assertEqual(self.cte_id.cte_initial_state_id, self.acre_state)
    #     self.assertEqual(self.cte_id.cte_final_state_id, self.acre_state)

    #     self.cte_id.cte40_UF = self.acre_state.ibge_code
    #     self.assertEqual(self.cte_id.company_id.partner_id.state_id, self.acre_state)

    #     self.cte_id.cte40_infMunCarrega = [
    #         (
    #             0,
    #             0,
    #             {
    #                 "cte40_cMunCarrega": "1200013",
    #                 "cte40_xMunCarrega": "Acrelândia",
    #             },
    #         )
    #     ]
    #     self.assertIn(
    #         self.env.ref("l10n_br_base.city_1200013"),
    #         self.cte_id.cte_loading_city_ids,
    #     )

    # def test_cte_processor(self):
    #     processor = self.cte_id._edoc_processor()
    #     self.assertTrue(isinstance(processor, CTeAdapter))

    #     self.cte_id.document_type_id = False
    #     processor = self.cte_id._edoc_processor()
    #     self.assertFalse(isinstance(processor, CTeAdapter))

    #     self.cte_id.document_type_id = self.cte_document_type_id

    #     self.cte_id.company_id.certificate_nfe_id = False
    #     with self.assertRaises(UserError):
    #         processor = self.cte_id._edoc_processor()

    def test_generate_key(self):
        self.cte_id._generate_key()
        self.assertTrue(self.cte_id.document_key)
        self.assertTrue(self.cte_id.key_random_code)
        self.assertTrue(self.cte_id.key_check_digit)

    def _mock_processor(self):
        processor = mock.MagicMock()
        processor.enviar_lote_evento.return_value.envio_xml = "<envio/>"
        processor.enviar_lote_evento.return_value.retorno.content = b"<retorno/>"
        answer = processor.enviar_lote_evento.return_value.resposta.infEvento
        answer.cStat = "135"
        answer.chCTe = self.cte_id.document_key
        answer.xMotivo = "Evento registrado"
        answer.dhRegEvento = "2026-10-02T10:00:00-03:00"
        answer.nProt = "1"
        return processor

    def test_correction_sequence_after_ten_letters(self):
        """The sequence is text: as text the maximum of "1".."10" is "9"."""
        for number in range(1, 11):
            event = self.cte_id.event_ids.create_event_save_xml(
                company_id=self.sn_company_id,
                environment=EVENT_ENV_HML,
                event_type="14",
                xml_file="<evento/>",
                document_id=self.cte_id,
                sequence=str(number),
                justification="Correction text for the test",
            )
            event.set_done("135", "mocked", False, str(number), False)
        processor = self._mock_processor()
        with mock.patch.object(type(self.cte_id), "_edoc_processor") as get:
            get.return_value = processor
            self.cte_id._cte_correction("Correction text for the test")
        self.assertEqual(processor.carta_correcao.call_args.kwargs["sequencia"], "11")

    def test_correction_keeps_one_field_per_line(self):
        """The CT-e letter is `group;field;value`, one correction per line."""
        processor = self._mock_processor()
        wizard = self.env["l10n_br_fiscal.document.correction.wizard"].create(
            {
                "document_id": self.cte_id.id,
                "justification": "compl;xObs;New remark text\nide;cfop;6353",
            }
        )
        with mock.patch.object(type(self.cte_id), "_edoc_processor") as get:
            get.return_value = processor
            wizard.doit()
        self.assertEqual(
            processor.carta_correcao.call_args.kwargs["justificativa"],
            "compl;xObs;New remark text\\nide;cfop;6353",
        )
