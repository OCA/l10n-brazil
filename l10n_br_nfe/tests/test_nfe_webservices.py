# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import subprocess
from unittest import mock

from odoo.fields import Datetime

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
)
from odoo.addons.l10n_br_nfe.models.document import NFe

from .mock_utils import nfe_mock
from .test_nfe_serialize import TestNFeExport


def is_libreoffice_command_available():
    try:
        subprocess.run(["libreoffice", "--version"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


class TestNFeWebservices(TestNFeExport):
    def setUp(self):
        nfe_list = [
            {
                "record_ref": "l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11",
                "xml_file": "NFe35200159594315000157550010000000022062777169.xml",
            },
        ]
        super().setUp(nfe_list)

    @nfe_mock(
        {
            "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
            "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
            "nfeRecepcaoEvento": "retEnvEvento/nfe_cancelamento.xml",
        }
    )
    def test_enviar_e_cancelar(self):
        for nfe_data in self.nfe_list:
            nfe = nfe_data["nfe"]

            if not is_libreoffice_command_available():
                with mock.patch.object(NFe, "make_pdf"):
                    nfe.action_document_send()
            else:
                # testing with the original make_pdf requires you have
                # apt-get install locale
                # locale-gen pt_BR.UTF-8
                # dpkg-reconfigure locales
                # pip install "reportlab==3.5.54"
                # apt-get install libreoffice
                nfe.action_document_send()

            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)

            cancel_wizard = (
                self.env["l10n_br_fiscal.document.cancel.wizard"]
                .with_context(active_model="l10n_br_fiscal.document", active_id=nfe.id)
                .create(
                    {"document_id": nfe.id, "justification": "Era apenas um teste."}
                )
            )
            cancel_wizard.doit()

            self.assertEqual(nfe.state_edoc, SITUACAO_EDOC_CANCELADA)
            self.assertIsNotNone(nfe.cancel_event_id)
            self.assertEqual(nfe.cancel_event_id.state, "done")
            self.assertEqual(nfe.cancel_event_id.status_code, "135")
            self.assertEqual(
                nfe.cancel_event_id.response, "Evento registrado e vinculado a NF-e"
            )
            self.assertEqual(
                Datetime.to_string(nfe.cancel_event_id.protocol_date),
                "2023-07-05 16:52:52",
            )

    @nfe_mock({"nfeInutilizacaoNF": "retInutNFe/nfe_inutilizacao.xml"})
    def test_inutilizar(self):
        nfe = self.nfe_list[0]["nfe"]
        inutilizar_wizard = (
            self.env["l10n_br_fiscal.invalidate.number.wizard"]
            .with_context(active_model="l10n_br_fiscal.document", active_id=nfe.id)
            .create({"document_id": nfe.id, "justification": "Era apenas um teste."})
        )
        inutilizar_wizard.doit()
