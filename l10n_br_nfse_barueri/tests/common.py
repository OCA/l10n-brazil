# Copyright 2026 Pop Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import re
from unittest import mock

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_base.tests.tools import load_fixture_files
from odoo.addons.l10n_br_fiscal.constants.fiscal import PROCESSADOR_OCA
from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files

# Tamanho de cada registro do leiaute PMB004 (V4.4), sem o CRLF final.
RECORD_LENGTHS = {"1": 25, "2": 1970, "3": 18, "4": 531, "5": 697, "9": 38}


def ok_line(numero="0000123", verify="ABCD.1234.5678.9012345-X"):
    """Registro tipo 2 do arquivo de retorno de sucesso de Barueri."""
    line = (
        "2"
        + " " * 4  # serie da NFS-e
        + numero  # 6-12
        + "20261127"  # 13-20
        + "151128"  # 21-26
        + verify.ljust(24)  # 27-50
        + "001 "  # serie do RPS
        + "0000000004"  # numero do RPS
        + "1"  # tributacao
        + "N"  # ISS retido
        + "A"  # situacao 67
    )
    return line.ljust(1678)


class BarueriCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        load_fiscal_fixture_files(cls.env)
        load_fixture_files(
            cls.env, "l10n_br_fiscal", file_names=["fiscal_document_nfse_demo.xml"]
        )
        load_fixture_files(
            cls.env,
            "l10n_br_nfse",
            file_names=["product_demo.xml", "fiscal_document_demo.xml"],
        )
        cls.document = cls.env.ref("l10n_br_fiscal.demo_nfse_same_state")
        cls.company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.barueri = cls.env["res.city"].search(
            [("ibge_code", "=", "3505708")], limit=1
        )
        cls.company.write(
            {
                "processador_edoc": PROCESSADOR_OCA,
                "provedor_nfse": "barueri",
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_SE").id,
            }
        )
        cls.company.partner_id.write(
            {
                "l10n_br_im_code": "5.36678-0",
                "l10n_br_ie_code": "",
                "state_id": cls.barueri.state_id.id,
                "city_id": cls.barueri.id,
            }
        )
        cls.document.write(
            {
                "company_id": cls.company.id,
                "document_date": "2026-11-27 18:00:00",
                "date_in_out": "2026-11-27 18:00:00",
            }
        )
        cls.city_code = cls.env["l10n_br_fiscal.city.taxation.code"].create(
            {
                "code": "140101220",
                "name": "Manutencao de equipamentos - PJ",
                "city_id": cls.barueri.id,
                "state_id": cls.barueri.state_id.id,
            }
        )
        cls.document.fiscal_line_ids.write(
            {
                "city_taxation_code_id": cls.city_code.id,
                "issqn_fg_city_id": cls.barueri.id,
            }
        )

    def _rps_lines(self, document=None):
        message = (document or self.document).serialize_nfse_barueri()
        b64 = re.search(r"<ArquivoRPSBase64>(.*)</ArquivoRPSBase64>", message).group(1)
        content = base64.b64decode(b64).decode("latin-1")
        self.assertTrue(content.endswith("\r\n"))
        return content[:-2].split("\r\n")

    def _rps_lines_with(self, **values):
        """RPS lines with these values added to the service data."""
        Document = type(self.document)
        original = Document._serialize_barueri_dados_servico

        def dados_servico(document):
            return dict(original(document), **values)

        with mock.patch.object(
            Document, "_serialize_barueri_dados_servico", dados_servico
        ):
            return self._rps_lines()
