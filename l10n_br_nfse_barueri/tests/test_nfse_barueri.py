# Copyright 2026 Pop Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from nfselib.barueri.exportador import CampoPosicional, Registro
from nfselib.barueri.rps import RegistroTipo2

from odoo.exceptions import UserError

from ..models.document import _decode_retorno, _new_registro
from ..models.rps_pmb004 import RegistroTipo4
from .common import RECORD_LENGTHS, BarueriCommon, ok_line


class TestNFSeBarueri(BarueriCommon):
    def test_rps_records_have_the_pmb004_lengths(self):
        lines = self._rps_lines()
        self.assertEqual([line[0] for line in lines], ["1", "2", "4", "9"])
        for line in lines:
            self.assertEqual(len(line), RECORD_LENGTHS[line[0]], line[0])
        self.assertEqual(lines[0][8:14], "PMB004")
        self.assertEqual(lines[3][1:8], "0000004")

    def test_rps_without_withholding_has_no_record_3(self):
        lines = self._rps_lines()
        self.assertEqual(lines[1][483:498], "0" * 15)
        self.assertEqual(lines[3][23:38], "0" * 15)

    def test_rps_lists_each_federal_withholding_in_a_record_3(self):
        """Each federal withholding goes in its own record 3, the record 2
        carries their sum and the record 9 counts the lines and the values."""
        lines = self._rps_lines_with(
            valor_ir_retido=48.0,
            valor_pis_retido=6.5,
            valor_cofins_retido=30.0,
            valor_csll_retido=10.0,
            valor_inss_retido=110.0,
            valor_iss_retido=50.0,
        )
        self.assertEqual(
            [line[0] for line in lines], ["1", "2", "3", "3", "3", "3", "3", "4", "9"]
        )
        for line in lines:
            self.assertEqual(len(line), RECORD_LENGTHS[line[0]], line[0])
        self.assertEqual(
            [line[1:] for line in lines[2:7]],
            [
                "01000000000004800",
                "02000000000000650",
                "03000000000003000",
                "04000000000001000",
                "05000000000011000",
            ],
        )
        # The ISS withheld has no code in the layout and stays out.
        self.assertEqual(lines[1][483:498], "000000000020450")
        self.assertEqual(lines[8][1:8], "0000009")
        self.assertEqual(lines[8][23:38], "000000000020450")

    def test_rps_of_a_single_income_tax_withholding(self):
        lines = self._rps_lines_with(valor_ir_retido=48.0)
        self.assertEqual([line[0] for line in lines], ["1", "2", "3", "4", "9"])
        self.assertEqual(lines[2], "301000000000004800")
        self.assertEqual(lines[1][483:498], "000000000004800")
        self.assertEqual(lines[4][1:8], "0000005")

    def test_rps_to_a_public_entity_has_a_record_5(self):
        """A purchase by a public entity declares the entity type and the
        kind of operation in the record 5."""
        self.document.partner_id.write(
            {"is_public_entity": True, "public_entity_type": "4"}
        )
        lines = self._rps_lines_with(valor_ir_retido=48.0)
        self.assertEqual([line[0] for line in lines], ["1", "2", "3", "4", "5", "9"])
        record5 = lines[4]
        self.assertEqual(len(record5), RECORD_LENGTHS["5"])
        self.assertEqual(record5[3:5], "41")
        self.assertEqual(lines[5][1:8], "0000006")
        self.document.public_entity_type = "2"
        self.assertEqual(self._rps_lines()[3][3], "2")

    def test_rps_declares_the_place_of_service(self):
        """Barueri rejects the record 4 with error 804 when the place of the
        service and the public roads flag of the record 2 are blank."""
        record2 = self._rps_lines()[1]
        self.assertEqual(record2[242:251], "140101220")
        self.assertEqual(record2[251], "1")
        self.assertEqual(record2[252], "2")
        other_city = self.env["res.city"].search(
            [("ibge_code", "=", "3550308")], limit=1
        )
        self.document.fiscal_line_ids.issqn_fg_city_id = other_city
        self.assertEqual(self._rps_lines()[1][251], "2")

    def test_rps_identifies_a_taker_by_cpf(self):
        partner = self.document.partner_id
        partner.write({"is_company": False, "vat": "724.830.165-53"})
        record2 = self._rps_lines()[1]
        self.assertEqual(record2[503], "1")
        self.assertEqual(record2[504:518], "00072483016553")

    def test_each_serialization_has_its_own_remittance_id(self):
        """Resending a rejected RPS must not reuse the remittance id, or
        Barueri refuses it as already informed (error 102)."""
        with mock.patch.object(
            type(self.document), "_barueri_remessa_id", side_effect=["1", "2"]
        ):
            first = self._rps_lines()[0][14:25]
            second = self._rps_lines()[0][14:25]
        self.assertNotEqual(first, second)

    def test_records_do_not_share_fields_between_documents(self):
        """nfselib.barueri 1.0.0 keeps the fields on the class: a value set
        for one document leaked into the next one."""
        first = _new_registro(RegistroTipo2)
        first.ComplementoLogradouroTomador = "SALA 1"
        second = _new_registro(RegistroTipo2)
        self.assertNotEqual(second.ComplementoLogradouroTomador, "SALA 1")
        self.assertEqual(second.TipoRegistro, "2")

    def test_record4_is_filled_with_a_library_that_resets_the_fields(self):
        """nfselib.barueri 1.1.0 sets ``self.campos = []`` in Registro's
        ``__init__``: a record declared only with class fields was exported
        empty."""

        class ResettingRegistro(Registro):
            def __init__(self):
                self.campos = []

        class Tipo4(ResettingRegistro):
            campos = RegistroTipo4.campos

        record = _new_registro(Tipo4)
        self.assertEqual(len(record.campos), len(RegistroTipo4.campos))
        record.CodigoNBS = "120018200"
        self.assertNotEqual(RegistroTipo4.campos[7].valor, "120018200")
        self.assertIsInstance(record.campos[0], CampoPosicional)

    def test_error_return_is_summarized_by_record(self):
        retorno = (
            "15366780PMB00400000000004\r\n"
            + "2RPS  ".ljust(1970)
            + "\r\n"
            + "41000035057083505708".ljust(531)
            + "807;817;818;\r\n"
            + "90000004\r\n"
        )
        self.assertEqual(
            self.document._barueri_erros_retorno(retorno),
            ["Registro 4: 807, 817, 818"],
        )

    def test_success_return_gives_number_and_verification_code(self):
        retorno = "1" + "\r\n" + ok_line() + "\r\n" + "9" + "\r\n"
        nota = self.document._barueri_parse_retorno_ok(retorno)
        self.assertEqual(nota["numero"], "0000123")
        self.assertEqual(nota["verify_code"], "ABCD.1234.5678.9012345-X")
        self.assertEqual(nota["data"] + nota["hora"], "20261127151128")
        self.assertEqual(nota["situacao"], "A")
        self.assertEqual(self.document._barueri_parse_retorno_ok("9\r\n"), {})

    def test_return_file_is_read_as_utf8(self):
        self.assertEqual(_decode_retorno("Lubrificação".encode()), "Lubrificação")
        self.assertEqual(_decode_retorno("ação".encode("latin-1")), "ação")

    def test_authorized_return_updates_the_document(self):
        self.document.state_edoc = "enviada"
        self.document._barueri_apply_result(
            "ENV123", "", "ENV123.RET", "1\r\n" + ok_line() + "\r\n9\r\n"
        )
        self.assertEqual(self.document.state_edoc, "autorizada")
        self.assertEqual(self.document.document_number, "0000123")
        self.assertEqual(self.document.verify_code, "ABCD.1234.5678.9012345-X")

    def test_pending_return_keeps_the_document_sent(self):
        # The FSM already moved the document to "enviada" before calling the
        # transmission hook; entering that state again would resend it.
        self.document.state_edoc = "enviada"
        self.document._barueri_apply_result("ENV123", "OK200", None, None)
        self.assertEqual(self.document.state_edoc, "enviada")
        self.assertIn("ENV123", self.document.status_name)

    def test_send_only_handles_barueri_documents(self):
        """A document of another NFS-e provider is neither serialized nor
        sent by this module."""
        Document = type(self.document)
        with mock.patch.object(Document, "_barueri_process_send") as send:
            self.document._eletronic_document_send()
        send.assert_called_once()
        self.company.provedor_nfse = False
        self.assertFalse([e for e in self.document.serialize() if isinstance(e, str)])
        with mock.patch.object(Document, "_barueri_process_send") as send:
            self.document._eletronic_document_send()
        send.assert_not_called()

    def test_an_authorized_note_is_not_cancelled_only_in_odoo(self):
        """Cancelling is not transmitted to Barueri yet: marking the note as
        cancelled in Odoo alone would leave it valid at the city."""
        self.document.state_edoc = "autorizada"
        with self.assertRaises(UserError):
            self.document._document_cancel("Servico nao prestado ao cliente")
        self.assertEqual(self.document.state_edoc, "autorizada")
