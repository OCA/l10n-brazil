# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_dere_spec.models import xsd_validator

BALAN_NS = "http://www.dere.gov.br/schemas/evtRetornoBalan/v1_0_0"
EVENT_ID = "DeRE1101" + "1" + "00000012345678" + "20261205120000" + "00001"


def _balan_return(info_rec_ev=None):
    info_rec_ev = info_rec_ev or (
        "<nrRecibo>1101-202611-ABCDEFGHIJ012345678</nrRecibo>"
        "<seqEvento>00</seqEvento>"
        "<dhRecepcao>2026-12-05T12:00:00.0000000-03:00</dhRecepcao>"
        "<dhProcess>2026-12-05T12:00:01.0000000-03:00</dhProcess>"
        "<tpEv>D-1101</tpEv>"
        "<hash>" + "A" * 43 + "=</hash>"
    )
    return (
        f'<DeRE xmlns="{BALAN_NS}">'
        f'<evtRetornoBalan id="{EVENT_ID}">'
        "<ideContrib><nrInsc>12345678</nrInsc></ideContrib>"
        "<ideStatus><cdRetorno>1</cdRetorno>"
        "<descRetorno>Sucesso</descRetorno></ideStatus>"
        f"<infoRecEv>{info_rec_ev}</infoRecEv>"
        "<infoEvento><idePeriodo><perApur>2026-11</perApur></idePeriodo>"
        "<infoAdic><nrReciboPGCC>1011-202611-ABCDEFGHIJ012345678</nrReciboPGCC>"
        "</infoAdic>"
        "<infoTotBalan><gTotalCodTrib><codTrib>110110001</codTrib>"
        "<indTribISS>0</indTribISS><vApurTot>150.00</vApurTot>"
        "</gTotalCodTrib></infoTotBalan>"
        "</infoEvento>"
        "</evtRetornoBalan>"
        "</DeRE>"
    )


@tagged("post_install", "-at_install")
class TestDereXsdValidator(TransactionCase):
    def test_official_event_schemas_load(self):
        filenames = (
            *xsd_validator.EVENT_SCHEMA.values(),
            *xsd_validator.RETURN_SCHEMA.values(),
            xsd_validator.LOTE_SCHEMA,
        )
        for filename in filenames:
            schema = xsd_validator._schema(filename)
            self.assertTrue(schema)

    def test_valid_return_passes(self):
        self.assertEqual(xsd_validator.validate_return(_balan_return()), [])

    def test_invalid_return_is_reported(self):
        xml = _balan_return(info_rec_ev="<tpEv>D-1101</tpEv>")
        self.assertTrue(xsd_validator.validate_return(xml))

    def test_unknown_return_is_skipped(self):
        self.assertIsNone(
            xsd_validator.validate_return(
                '<DeRE xmlns="http://www.dere.gov.br/schemas/evtRetornoX/v9_9_9"/>'
            )
        )
        self.assertIsNone(
            xsd_validator.validate_return(
                f'<evtRetornoBalan xmlns="{BALAN_NS}" id="{EVENT_ID}"/>'
            )
        )

    def test_invalid_d1199_is_reported(self):
        xml = (
            '<DeRE xmlns="http://www.dere.gov.br/schemas/evtFechMensal/v0_0_2">'
            '<evtFechMensal id="not-a-valid-id"/>'
            "</DeRE>"
        )
        errors = xsd_validator.validate(xml, "D-1199")
        self.assertTrue(errors)

    def test_unknown_event_type_raises(self):
        with self.assertRaises(ValueError):
            xsd_validator.validate("<DeRE/>", "D-9999")
