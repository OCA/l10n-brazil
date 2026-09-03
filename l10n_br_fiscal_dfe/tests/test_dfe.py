# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=line-too-long

import base64
import gzip
from datetime import timedelta
from io import BytesIO
from unittest import mock

from requests.exceptions import RequestException
from xsdata.formats.dataclass.transports import DefaultTransport

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.queue_job.tests.common import trap_jobs

from ..constants.dfe import (
    DFE_INTERVAL_ERROR,
    DFE_INTERVAL_NO_DOCS,
    DFE_INTERVAL_SUCCESS,
)
from ..tools import utils

response_sucesso_multiplos = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><nfeDistDFeInteresseResponse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"><nfeDistDFeInteresseResult><retDistDFeInt xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01"><tpAmb>1</tpAmb><verAplic>1.4.0</verAplic><cStat>138</cStat><xMotivo>Documento(s) localizado(s)</xMotivo><dhResp>2022-04-04T11:54:49-03:00</dhResp><ultNSU>000000000000201</ultNSU><maxNSU>000000000000201</maxNSU><loteDistDFeInt><docZip NSU="000000000000200" schema="resNFe_v1.00.xsd">H4sIAAAAAAAEAIVS22qDQBD9FfFdd9Z7ZLKQphosqQ3mQuibMZto8RJcifn8rjG9PZUdZg7DOWeGYbHlIg65cqvKWvg3cZyqedddfEL6vtd7U2/aMzEAKNm/LtdZzqtU/SYX/5O1ohZdWmdcVa68FWkzVakO8PD4o780bZeWp0JkaakX9Uk/tKQ+cZVhlssVmUkNoPLZnjcAGKBtDwVMzzIodak3AIO6HpJRg/N49cL+apDcm3iLm4qz99lKWSSzMJrPlEAJnqPNWyJRlATLCMnIwShgUkqpNLEAHBOJ7OAxD6qCGWCARkEDZwPg30MDU2YkIwG7SxwyiuRe8SqTN3H1iXQZMB6L8y4t2W73sXdtJ+6TUDhGveaLbc9DsXyyt1NpNZLkzIRnh675PZZOfMP2LfNn7IOD9aptOkaHy5meDS44FnWRjG3M1kU3HEmu9gWRjP+BfQI6BY33GAIAAA==</docZip><docZip NSU="000000000000201" schema="procNFe_v4.00.xsd">H4sIAAAAAAAAA51WzXKjRhC+5ykoX1MWMyAssTWeiozQhpSFKEu7dwxjmwQYLUJYldfJOS+QY/bF0t0DWF5nt7JRqejub3q6p3/mR9QPKml0ZnWqOaT6+mI6YezCOlVlfbi+eGrb/Tvbfn5+nux106blQ3HI0nJS1A+T+8aGuRdSxCv1Xfog4JTXDqP8+gJQ13MY457v+VOXewz5mQeUs/7HHXblzGYzfsXRVK6kyD6spOsJG6nI4pUcNAACSdRpu9nLj6rOU2EbQVQ6lx7MQSoOqimU5MI2jKhhFkhIRP4UVoV0mMMuGYf/jjvvGIP/j4zDV9hGAfS2aRHW7bdVex3R7o0LohDFUh1alHtOZOtjvXoPUTHOPQfiMDLMi6q9mYgMyOD8YADiRLb8iCISGF1U99LBQWTEQwEhUaA9B6XIV0WdluR74BFNGnWQjEBixR56BAMFbGAFVBBbR25yra2bJj0UpbUJFlbHp8IeBjEo8KSqAuIK4uQX+bq6wiZQnGJdKbkLt7vQurS2RbUv1cGK06zQsChhm3FxWqWQwG+o0biAYqsmJJ+n28dG3h1TK0mPpbaWRXoANQRF3WjpzaFPkKGkv045TMbvojxWn/+sCw3zCIVG2ybCxn4LwkTyOXcwGggFJJElKdaEeXOwQrw4ETEpAiMGfNC1kg53obl9/wqakQBhn609CiW0v+vOwT53XWEDIIK7HdYLCSiTXk5dQ4mc86nv+jMfszv3X2c3Xl2GVriOdtFyAdRarG+iMIZMLkPr5816c7t5vwgWG0wsjH5c3G7urFW0DRa3Y/5pcaZJx8Ru0+qoSmutm4M6Ty3HXUmpPQX7EnbG339ZKezCBhwEuv71WLfa4h7EQuPidJMWDajfNFr/VhY14D0y1MZjLpu/qs328x/aVPYrxWFTb3bFrv5XcTyPc3c6mzvQrK/LYzIAuyMKx707Cli26RWbOj6cQq47NWVTVVqUMisLVbeK/zQwk0xXcDZiJXEcTgkykavWqqNWVdcXeNDBnstx8UjCy2Cz5rjJE4OGi1hiwd7vohhQFCEoHAvS+6IGS89F+2QtNRQIA6RZcbCW/pS5LjUuSiJYbRLpcQbdT6w4BrqSH+JoKWxixSf88gmjOSSI7kNN4HTCxh/sfoOKjpzRIIAv6901xf0XayZIHIn0Pg30icjo1YDgwMBv/JpxqMZOD3VBjs4t8A4nhj600FJRsN6a7zbmjEuhm+IRzzeiIthutjE0Cu40YsU+aFQOjDOZka9BFh0yxpBkExc66xyB6r/4sHuvSYR5qD9J3/cxfOAQjHfoeCc9F73i/u5Bm2Yk0ZY+m2PbGMWp3yt2NwH4phQAJ/aoyvqUkQCl6CEsBAL2aMkmOdisonik/8FHP2F0MxjozgYwFz1snxu2R3QsCHQ+Xo26xTsI80Rl+8JpRwnsAZNMIrDxdH2OG0B0qyAZYGTRHsQyWqS4XgASQe8FMUIP3sEKz3GU/7XHu1WjWjXqkgB+1OPoCFjRwSKzASEegonGKCIUkxc56YGl6nR5hhr5bYG/UocOK6AH1AiiwwdJHwK+SeyxAHZfkbZJ64N5Opl4fHo+9bHZw/A+faTTK0GKz4f0cXhIIEI4biqj0OF3TB0i9jDX3hsLD4u8yHpmBc9JLZc6O1YKLw+8/YpcW/DYfGet0yazlqrS6G1U7oUiMxw9e2z6wnnQvnmIkiOoYUsv0iiHO8xx+NxxvKnD5t7F21dV9oTWvufhChue5ogaHckvXMCVSbDItm0Ko5gaw8KNp9ui03JxbOGQ+j2FyLV1PGgrTy242/Hy7TUoVmPG7uMErn/ryx/+AZs2W+n2CwAA</docZip></loteDistDFeInt></retDistDFeInt></nfeDistDFeInteresseResult></nfeDistDFeInteresseResponse></soap:Body></soap:Envelope>"""  # noqa: E501

response_sucesso_individual = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><nfeDistDFeInteresseResponse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"><nfeDistDFeInteresseResult><retDistDFeInt xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01"><tpAmb>1</tpAmb><verAplic>1.4.0</verAplic><cStat>138</cStat><xMotivo>Documento(s) localizado(s)</xMotivo><dhResp>2022-04-04T11:54:49-03:00</dhResp><ultNSU>000000000000201</ultNSU><maxNSU>000000000000201</maxNSU><loteDistDFeInt><docZip NSU="000000000000201" schema="procNFe_v4.00.xsd">H4sIAAAAAAAAA51WzXKjRhC+5ykoX1MWMyAssTWeiozQhpSFKEu7dwxjmwQYLUJYldfJOS+QY/bF0t0DWF5nt7JRqejub3q6p3/mR9QPKml0ZnWqOaT6+mI6YezCOlVlfbi+eGrb/Tvbfn5+nux106blQ3HI0nJS1A+T+8aGuRdSxCv1Xfog4JTXDqP8+gJQ13MY457v+VOXewz5mQeUs/7HHXblzGYzfsXRVK6kyD6spOsJG6nI4pUcNAACSdRpu9nLj6rOU2EbQVQ6lx7MQSoOqimU5MI2jKhhFkhIRP4UVoV0mMMuGYf/jjvvGIP/j4zDV9hGAfS2aRHW7bdVex3R7o0LohDFUh1alHtOZOtjvXoPUTHOPQfiMDLMi6q9mYgMyOD8YADiRLb8iCISGF1U99LBQWTEQwEhUaA9B6XIV0WdluR74BFNGnWQjEBixR56BAMFbGAFVBBbR25yra2bJj0UpbUJFlbHp8IeBjEo8KSqAuIK4uQX+bq6wiZQnGJdKbkLt7vQurS2RbUv1cGK06zQsChhm3FxWqWQwG+o0biAYqsmJJ+n28dG3h1TK0mPpbaWRXoANQRF3WjpzaFPkKGkv045TMbvojxWn/+sCw3zCIVG2ybCxn4LwkTyOXcwGggFJJElKdaEeXOwQrw4ETEpAiMGfNC1kg53obl9/wqakQBhn609CiW0v+vOwT53XWEDIIK7HdYLCSiTXk5dQ4mc86nv+jMfszv3X2c3Xl2GVriOdtFyAdRarG+iMIZMLkPr5816c7t5vwgWG0wsjH5c3G7urFW0DRa3Y/5pcaZJx8Ru0+qoSmutm4M6Ty3HXUmpPQX7EnbG339ZKezCBhwEuv71WLfa4h7EQuPidJMWDajfNFr/VhY14D0y1MZjLpu/qs328x/aVPYrxWFTb3bFrv5XcTyPc3c6mzvQrK/LYzIAuyMKx707Cli26RWbOj6cQq47NWVTVVqUMisLVbeK/zQwk0xXcDZiJXEcTgkykavWqqNWVdcXeNDBnstx8UjCy2Cz5rjJE4OGi1hiwd7vohhQFCEoHAvS+6IGS89F+2QtNRQIA6RZcbCW/pS5LjUuSiJYbRLpcQbdT6w4BrqSH+JoKWxixSf88gmjOSSI7kNN4HTCxh/sfoOKjpzRIIAv6901xf0XayZIHIn0Pg30icjo1YDgwMBv/JpxqMZOD3VBjs4t8A4nhj600FJRsN6a7zbmjEuhm+IRzzeiIthutjE0Cu40YsU+aFQOjDOZka9BFh0yxpBkExc66xyB6r/4sHuvSYR5qD9J3/cxfOAQjHfoeCc9F73i/u5Bm2Yk0ZY+m2PbGMWp3yt2NwH4phQAJ/aoyvqUkQCl6CEsBAL2aMkmOdisonik/8FHP2F0MxjozgYwFz1snxu2R3QsCHQ+Xo26xTsI80Rl+8JpRwnsAZNMIrDxdH2OG0B0qyAZYGTRHsQyWqS4XgASQe8FMUIP3sEKz3GU/7XHu1WjWjXqkgB+1OPoCFjRwSKzASEegonGKCIUkxc56YGl6nR5hhr5bYG/UocOK6AH1AiiwwdJHwK+SeyxAHZfkbZJ64N5Opl4fHo+9bHZw/A+faTTK0GKz4f0cXhIIEI4biqj0OF3TB0i9jDX3hsLD4u8yHpmBc9JLZc6O1YKLw+8/YpcW/DYfGet0yazlqrS6G1U7oUiMxw9e2z6wnnQvnmIkiOoYUsv0iiHO8xx+NxxvKnD5t7F21dV9oTWvufhChue5ogaHckvXMCVSbDItm0Ko5gaw8KNp9ui03JxbOGQ+j2FyLV1PGgrTy242/Hy7TUoVmPG7uMErn/ryx/+AZs2W+n2CwAA</docZip></loteDistDFeInt></retDistDFeInt></nfeDistDFeInteresseResult></nfeDistDFeInteresseResponse></soap:Body></soap:Envelope>"""  # noqa: E501

response_rejeicao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><nfeDistDFeInteresseResponse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"><nfeDistDFeInteresseResult><retDistDFeInt xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01"><tpAmb>2</tpAmb><verAplic>1.4.0</verAplic><cStat>589</cStat><xMotivo>Rejeicao: Numero do NSU informado superior ao maior NSU da base de dados doAmbiente Nacional</xMotivo><dhResp>2022-04-04T11:54:49-03:00</dhResp><ultNSU>000000000000000</ultNSU><maxNSU>000000000000000</maxNSU></retDistDFeInt></nfeDistDFeInteresseResult></nfeDistDFeInteresseResponse></soap:Body></soap:Envelope>"""  # noqa: E501

response_137 = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><nfeDistDFeInteresseResponse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"><nfeDistDFeInteresseResult><retDistDFeInt xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01"><tpAmb>1</tpAmb><verAplic>1.4.0</verAplic><cStat>137</cStat><xMotivo>Nenhum documento localizado para o Contribuinte</xMotivo><dhResp>2022-04-04T11:54:49-03:00</dhResp><ultNSU>000000000000200</ultNSU><maxNSU>000000000000200</maxNSU></retDistDFeInt></nfeDistDFeInteresseResult></nfeDistDFeInteresseResponse></soap:Body></soap:Envelope>"""  # noqa: E501

response_656_with_nsu = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><nfeDistDFeInteresseResponse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"><nfeDistDFeInteresseResult><retDistDFeInt xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01"><tpAmb>1</tpAmb><verAplic>1.4.0</verAplic><cStat>656</cStat><xMotivo>Consumo Indevido</xMotivo><dhResp>2022-04-04T11:54:49-03:00</dhResp><ultNSU>000000000000300</ultNSU><maxNSU>000000000000300</maxNSU></retDistDFeInt></nfeDistDFeInteresseResult></nfeDistDFeInteresseResponse></soap:Body></soap:Envelope>"""  # noqa: E501


def _gzip_base64(xml_str):
    """Gzip and base64-encode an XML string (like SEFAZ docZip)."""
    buf = BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        gz.write(xml_str.encode("utf-8"))
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _build_dfe_response(
    doczip_list,
    ult_nsu="000000000000300",
    max_nsu="000000000000300",
):
    """Build a SEFAZ cStat=138 response with custom docZip entries.

    doczip_list: list of (nsu_str, schema_str, xml_content) tuples.
    """
    parts = []
    for nsu, schema, xml_content in doczip_list:
        encoded = _gzip_base64(xml_content)
        parts.append(f'<docZip NSU="{nsu}" schema="{schema}">' f"{encoded}</docZip>")
    doczip_xml = "".join(parts)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soap:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        "<soap:Body><nfeDistDFeInteresseResponse"
        ' xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/'
        'NFeDistribuicaoDFe"><nfeDistDFeInteresseResult>'
        '<retDistDFeInt xmlns:xsd="http://www.w3.org/2001/XMLSchema"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01">'
        "<tpAmb>1</tpAmb><verAplic>1.4.0</verAplic>"
        "<cStat>138</cStat>"
        "<xMotivo>Documento(s) localizado(s)</xMotivo>"
        "<dhResp>2022-04-04T11:54:49-03:00</dhResp>"
        f"<ultNSU>{ult_nsu}</ultNSU>"
        f"<maxNSU>{max_nsu}</maxNSU>"
        f"<loteDistDFeInt>{doczip_xml}</loteDistDFeInt>"
        "</retDistDFeInt></nfeDistDFeInteresseResult>"
        "</nfeDistDFeInteresseResponse></soap:Body>"
        "</soap:Envelope>"
    )


_RESEVENTO_XML = (
    '<resEvento xmlns="http://www.portalfiscal.inf.br/nfe">'
    "<cOrgao>91</cOrgao>"
    "<CNPJ>59594315000157</CNPJ>"
    "<chNFe>35200159594315000157550010000000012062777161</chNFe>"
    "<dhEvento>2022-04-04T11:54:49-03:00</dhEvento>"
    "<tpEvento>210210</tpEvento>"
    "<nSeqEvento>1</nSeqEvento>"
    "<xEvento>Ciencia da Operacao</xEvento>"
    "<dhRecbto>2022-04-04T11:54:49-03:00</dhRecbto>"
    "</resEvento>"
)

_PROCEVENTONFE_XML = (
    '<procEventoNFe xmlns="http://www.portalfiscal.inf.br/nfe"'
    ' versao="1.00">'
    '<evento versao="1.00">'
    '<infEvento Id="ID210210352001">'
    "<cOrgao>91</cOrgao><tpAmb>1</tpAmb>"
    "<CNPJ>59594315000157</CNPJ>"
    "<chNFe>35200159594315000157550010000000012062777161</chNFe>"
    "<dhEvento>2022-04-04T11:54:49-03:00</dhEvento>"
    "<tpEvento>210210</tpEvento>"
    "<nSeqEvento>1</nSeqEvento>"
    "<verEvento>1.00</verEvento>"
    '<detEvento versao="1.00">'
    "<descEvento>Ciencia da Operacao</descEvento>"
    "</detEvento>"
    "</infEvento></evento>"
    '<retEvento versao="1.00"><infEvento>'
    "<tpAmb>1</tpAmb><verAplic>1.4.0</verAplic>"
    "<cOrgao>91</cOrgao><cStat>135</cStat>"
    "<xMotivo>Evento registrado</xMotivo>"
    "<chNFe>35200159594315000157550010000000012062777161</chNFe>"
    "<dhRegEvento>2022-04-04T11:54:49-03:00</dhRegEvento>"
    "<nProt>891220000000001</nProt>"
    "</infEvento></retEvento>"
    "</procEventoNFe>"
)


class TestDFe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")

    @mock.patch.object(DefaultTransport, "post")
    def test_search_dfe_success(self, mock_post):
        """Test a successful DFe search with multiple documents returned."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")

        self.company.dfe_search_documents()

        self.assertEqual(self.company.last_nsu, utils.format_nsu("201"))
        mock_post.assert_called_once()

        # The procNFe in the mock contains CFOP 5102
        dfe_record = self.env["l10n_br_fiscal_dfe.dfe"].search(
            [
                ("company_id", "=", self.company.id),
                ("dfe_nfe_document_type", "=", "dfe_nfe_complete"),
            ],
            limit=1,
        )
        self.assertTrue(dfe_record, "procNFe should create a dfe_nfe_complete record")
        cfop_codes = dfe_record.dfe_document_id.cfop_ids.mapped("code")
        self.assertIn("5102", cfop_codes, "CFOP 5102 should be extracted from procNFe")

    def test_search_dfe_error_conditions(self):
        """Test various error conditions during DFe search."""
        # 1. Test a 500-level HTTP error
        with mock.patch.object(
            DefaultTransport, "post", side_effect=RequestException("Mocked HTTP 500")
        ) as mock_post_http_error:
            self.company.dfe_search_documents()
            self.assertEqual(self.company.last_nsu, "0")
            mock_post_http_error.assert_called_once()

        # 2. Test a business-level rejection from SEFAZ
        with mock.patch.object(
            DefaultTransport, "post", return_value=response_rejeicao.encode("utf-8")
        ) as mock_post_rejection:
            self.company.last_nsu = "0"
            self.company.dfe_next_query = False
            self.company.dfe_search_documents()
            self.assertEqual(
                self.company.last_nsu,
                "0",
                "last_nsu must not be overwritten by error response zeros",
            )
            mock_post_rejection.assert_called_once()

        # 3. Test a generic exception during processing
        with mock.patch.object(
            DefaultTransport, "post", side_effect=Exception("Generic Mock Error")
        ) as mock_post_generic_error:
            self.company.last_nsu = "0"
            self.company.dfe_next_query = False
            self.company.dfe_search_documents()
            self.assertEqual(self.company.last_nsu, "0")
            mock_post_generic_error.assert_called_once()

    def test_cron_search_documents(self):
        """Test the automated cron job for searching documents."""
        self.company.auto_fetch = True

        # Test that cron succeeds (queue_job__no_delay makes with_delay run inline)
        with mock.patch.object(
            DefaultTransport,
            "post",
            return_value=response_sucesso_multiplos.encode("utf-8"),
        ):
            self.env["res.company"].with_context(
                queue_job__no_delay=True,
            )._cron_dfe_search_documents()
            self.assertEqual(self.company.last_nsu, "000000000000201")

    def test_utils(self):
        # format_nsu with valid values
        self.assertEqual(utils.format_nsu("100"), "000000000000100")
        self.assertEqual(utils.format_nsu("0"), "000000000000000")
        self.assertEqual(utils.format_nsu(200), "000000000000200")

        # format_nsu with invalid values should return False
        self.assertFalse(utils.format_nsu(None))
        self.assertFalse(utils.format_nsu(""))
        self.assertFalse(utils.format_nsu("abc"))

        # mask_cnpj tests
        cnpj_masked = utils.mask_cnpj(False)
        self.assertFalse(cnpj_masked)

        cnpj_masked = utils.mask_cnpj("1234")
        self.assertEqual(cnpj_masked, "1234")

        cnpj_masked = utils.mask_cnpj("31282204000196")
        self.assertEqual(cnpj_masked, "31.282.204/0001-96")

    @mock.patch.object(DefaultTransport, "post")
    def test_search_specific_zero_nsu(self, mock_post):
        """consChNFe with NSU=0 creates record with nsu=False and dedup works."""
        # Build response with zero NSU (typical for consChNFe in homologation)
        response_zero_nsu = response_sucesso_individual.replace(
            'NSU="000000000000201"', 'NSU="000000000000000"'
        )
        mock_post.return_value = response_zero_nsu.encode("utf-8")

        DfeRecord = self.env["l10n_br_fiscal_dfe.dfe"]
        access_key = "35200159594315000157550010000000012062777161"

        # First call: should create exactly 1 record
        self.company._dfe_search_specific_document(access_key=access_key)
        records = DfeRecord.search(
            [
                ("company_id", "=", self.company.id),
                ("schema_type", "=", "procNFe"),
            ]
        )
        self.assertEqual(len(records), 1)
        self.assertFalse(records.nsu, "NSU should be False for zero-NSU documents")

        # Second call: dedup by access_key should prevent duplicate
        self.company._dfe_search_specific_document(access_key=access_key)
        records = DfeRecord.search(
            [
                ("company_id", "=", self.company.id),
                ("schema_type", "=", "procNFe"),
            ]
        )
        self.assertEqual(
            len(records),
            1,
            "No duplicate should be created for same access_key with zero NSU",
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_zero_nsu_different_documents(self, mock_post):
        """Two documents with NSU=0 but different schemas should both be created."""
        response_zero_multi = response_sucesso_multiplos.replace(
            'NSU="000000000000200"', 'NSU="000000000000000"'
        ).replace('NSU="000000000000201"', 'NSU="000000000000000"')
        mock_post.return_value = response_zero_multi.encode("utf-8")

        DfeRecord = self.env["l10n_br_fiscal_dfe.dfe"]
        self.company._dfe_search_specific_document(access_key="any_key")

        records = DfeRecord.search([("company_id", "=", self.company.id)])
        self.assertGreaterEqual(
            len(records),
            2,
            "Documents with zero NSU but different schemas should both be created",
        )
        for record in records:
            self.assertFalse(record.nsu)

    @mock.patch.object(DefaultTransport, "post")
    def test_nsu_not_reset_on_error_589(self, mock_post):
        """NSU values must not be reset when SEFAZ returns a 589 rejection."""
        mock_post.return_value = response_rejeicao.encode("utf-8")

        self.company.last_nsu = "150"
        self.company.max_nsu = "200"
        self.company.dfe_search_documents()

        self.assertEqual(
            self.company.last_nsu,
            "150",
            "last_nsu must be preserved on 589 error",
        )
        self.assertEqual(
            self.company.max_nsu,
            "200",
            "max_nsu must be preserved on 589 error",
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_cooldown_after_137(self, mock_post):
        """Immediate retry after cStat=137 should return cooldown notification."""
        mock_post.return_value = response_137.encode("utf-8")

        # First call: sets dfe_next_query to ~1h in the future
        self.company.dfe_search_documents()
        self.assertEqual(self.company.dfe_last_status_code, "137")
        self.assertTrue(self.company.dfe_next_query)

        # Second call: should be blocked by dfe_next_query
        mock_post.reset_mock()
        result = self.company.action_document_distribution()
        self.assertTrue(result, "Should return a notification action")
        self.assertEqual(result.get("tag"), "display_notification")
        self.assertIn("137", result["params"]["title"])
        mock_post.assert_not_called()

    @mock.patch.object(DefaultTransport, "post")
    def test_cooldown_skipped_when_next_query_passed(self, mock_post):
        """Cooldown should be skipped when dfe_next_query is in the past."""
        mock_post.return_value = response_137.encode("utf-8")

        self.company.dfe_next_query = fields.Datetime.now() - timedelta(minutes=1)

        self.company._dfe_document_distribution()
        mock_post.assert_called_once()

    @mock.patch.object(DefaultTransport, "post")
    def test_656_nsu_recovery(self, mock_post):
        """656 response with non-zero ultNSU should update last_nsu."""
        mock_post.return_value = response_656_with_nsu.encode("utf-8")

        self.company.last_nsu = "100"
        self.company.dfe_search_documents()

        self.assertEqual(
            self.company.last_nsu,
            "000000000000300",
            "last_nsu should be recovered from 656 response ultNSU",
        )

    def test_max_nsu_not_written_as_false(self):
        """Exception on SEFAZ call must not overwrite max_nsu with False."""
        self.company.last_nsu = "100"
        self.company.max_nsu = "500"

        with mock.patch.object(
            DefaultTransport,
            "post",
            side_effect=Exception("Connection error"),
        ):
            self.company.dfe_search_documents()

        self.assertEqual(
            self.company.max_nsu,
            "500",
            "max_nsu must not be overwritten when no successful response",
        )

    # ── Dynamic scheduling tests ─────────────────────────────────────────

    @mock.patch.object(DefaultTransport, "post")
    def test_schedule_after_success(self, mock_post):
        """After cStat=138, dfe_next_query should be ~now + 10min."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")
        before = fields.Datetime.now()
        self.company.dfe_search_documents()
        after = fields.Datetime.now()

        self.assertTrue(self.company.dfe_next_query)
        self.assertGreaterEqual(
            self.company.dfe_next_query, before + DFE_INTERVAL_SUCCESS
        )
        self.assertLessEqual(self.company.dfe_next_query, after + DFE_INTERVAL_SUCCESS)

    @mock.patch.object(DefaultTransport, "post")
    def test_schedule_after_137(self, mock_post):
        """After cStat=137, dfe_next_query should be ~now + 1h."""
        mock_post.return_value = response_137.encode("utf-8")
        before = fields.Datetime.now()
        self.company.dfe_search_documents()
        after = fields.Datetime.now()

        self.assertTrue(self.company.dfe_next_query)
        self.assertGreaterEqual(
            self.company.dfe_next_query, before + DFE_INTERVAL_NO_DOCS
        )
        self.assertLessEqual(self.company.dfe_next_query, after + DFE_INTERVAL_NO_DOCS)

    def test_schedule_after_exception(self):
        """After a network exception, dfe_next_query should be ~now + 15min."""
        with mock.patch.object(
            DefaultTransport,
            "post",
            side_effect=Exception("Connection error"),
        ):
            before = fields.Datetime.now()
            self.company.dfe_search_documents()
            after = fields.Datetime.now()

        self.assertTrue(self.company.dfe_next_query)
        self.assertGreaterEqual(
            self.company.dfe_next_query, before + DFE_INTERVAL_ERROR
        )
        self.assertLessEqual(self.company.dfe_next_query, after + DFE_INTERVAL_ERROR)

    def test_cron_skips_company_not_ready(self):
        """Cron should skip companies whose dfe_next_query is in the future."""
        self.company.auto_fetch = True
        self.company.dfe_next_query = fields.Datetime.now() + timedelta(hours=2)

        with mock.patch.object(DefaultTransport, "post") as mock_post:
            self.env["res.company"]._cron_dfe_search_documents()
            mock_post.assert_not_called()

    @mock.patch.object(DefaultTransport, "post")
    def test_cron_runs_company_ready(self, mock_post):
        """Cron should run for companies whose dfe_next_query is in the past."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")
        self.company.auto_fetch = True
        self.company.dfe_next_query = fields.Datetime.now() - timedelta(minutes=1)

        self.env["res.company"].with_context(
            queue_job__no_delay=True,
        )._cron_dfe_search_documents()
        mock_post.assert_called_once()

    def test_ciencia_does_not_reschedule_during_656(self):
        """Ciência must not reschedule when company has active 656 status."""
        self.company.dfe_last_status_code = "656"
        self.company.dfe_next_query = fields.Datetime.now() + timedelta(hours=1)
        original_next_query = self.company.dfe_next_query

        mde = self.env["l10n_br_nfe.md_event"].create(
            {
                "access_key": "35200159594315000157550010000000012062777161",
                "event_type": "ciente",
                "company_id": self.company.id,
                "document_type": "nfe",
                "state": "draft",
            }
        )
        with mock.patch.object(type(mde), "_send_event"):
            mde.action_confirm()

        self.assertEqual(
            self.company.dfe_next_query,
            original_next_query,
            "dfe_next_query must not be changed during 656 cooldown",
        )

    def test_ciencia_reschedules_after_137(self):
        """Ciência should reschedule even when NSUs are synced (137)."""
        self.company.dfe_last_status_code = "137"
        self.company.last_nsu = "200"
        self.company.max_nsu = "200"
        self.company.dfe_next_query = fields.Datetime.now() + timedelta(hours=1)

        mde = self.env["l10n_br_nfe.md_event"].create(
            {
                "access_key": "35200159594315000157550010000000012062777161",
                "event_type": "ciente",
                "company_id": self.company.id,
                "document_type": "nfe",
                "state": "draft",
            }
        )
        before = fields.Datetime.now()
        with mock.patch.object(type(mde), "_send_event"):
            mde.action_confirm()
        after = fields.Datetime.now()

        self.assertGreaterEqual(
            self.company.dfe_next_query, before + DFE_INTERVAL_SUCCESS
        )
        self.assertLessEqual(self.company.dfe_next_query, after + DFE_INTERVAL_SUCCESS)

    # ── Auto-manifest tests ────────────────────────────────────────────

    @mock.patch.object(DefaultTransport, "post")
    def test_auto_manifest_enqueues_job(self, mock_post):
        """resNFe with auto_manifest_nfe=True should enqueue action_confirm job."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")
        self.company.auto_manifest_nfe = True

        with trap_jobs() as trap:
            self.company.dfe_search_documents()
            trap.assert_jobs_count(1)

        mde = self.env["l10n_br_nfe.md_event"].search(
            [("company_id", "=", self.company.id)]
        )
        self.assertEqual(len(mde), 1)
        self.assertEqual(mde.event_type, "ciente")
        self.assertEqual(mde.state, "draft")
        self.assertTrue(mde.dfe_document_id, "MDE should be linked to DFe document")

    @mock.patch.object(DefaultTransport, "post")
    def test_auto_manifest_not_triggered_when_disabled(self, mock_post):
        """resNFe with auto_manifest_nfe=False should NOT create MDE."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")
        self.company.auto_manifest_nfe = False

        self.company.dfe_search_documents()

        mde = self.env["l10n_br_nfe.md_event"].search(
            [("company_id", "=", self.company.id)]
        )
        self.assertFalse(mde, "No MDE should be created when auto_manifest is disabled")

    # ── MDE error 573 (duplicate event) tests ────────────────────────────

    def test_573_duplicate_event_treated_as_done(self):
        """Error 573 (duplicate event) should mark MDE as done, not raise."""
        mde = self.env["l10n_br_nfe.md_event"].create(
            {
                "access_key": "35200159594315000157550010000000012062777161",
                "event_type": "ciente",
                "company_id": self.company.id,
                "document_type": "nfe",
                "state": "draft",
            }
        )

        result = mock.MagicMock()
        result.retorno.status_code = 200
        result.retorno._content = b"<xml>573 response</xml>"
        inf_evento = result.resposta.retEvento.__getitem__.return_value.infEvento
        inf_evento.cStat = "573"
        inf_evento.xMotivo = "Duplicidade de Evento"

        mde.validate_event_response(result, ["135"])
        self.assertEqual(mde.state, "done")
        self.assertIn("573", mde.response_xml)

    def test_non_573_error_still_raises(self):
        """Non-573 SEFAZ error should still raise ValidationError."""
        mde = self.env["l10n_br_nfe.md_event"].create(
            {
                "access_key": "35200159594315000157550010000000012062777161",
                "event_type": "ciente",
                "company_id": self.company.id,
                "document_type": "nfe",
                "state": "draft",
            }
        )

        result = mock.MagicMock()
        result.retorno.status_code = 200
        result.retorno._content = b"<xml>response</xml>"
        inf_evento = result.resposta.retEvento.__getitem__.return_value.infEvento
        inf_evento.cStat = "999"
        inf_evento.xMotivo = "Outro erro qualquer"

        with self.assertRaises(ValidationError):
            mde.validate_event_response(result, ["135"])
        self.assertEqual(mde.state, "draft")

    # ── Access key validation tests ──────────────────────────────────────

    def _create_wizard(self, **kwargs):
        defaults = {
            "search_type": "access_key",
            "company_id": self.company.id,
        }
        defaults.update(kwargs)
        return self.env["dfe_specific_search_wizard"].create(defaults)

    def test_wizard_strips_non_digits_from_access_key(self):
        """Wizard should strip spaces and non-digit chars before searching."""
        key_with_spaces = "3520 0159 5943 1500 0157 5500 1000 0000 0120 6277 7161"
        wizard = self._create_wizard(access_key=key_with_spaces)
        with mock.patch.object(
            DefaultTransport,
            "post",
            return_value=response_sucesso_individual.encode("utf-8"),
        ):
            wizard.action_confirm_search()

    def test_wizard_rejects_short_access_key(self):
        """Wizard should raise UserError for keys shorter than 44 digits."""
        wizard = self._create_wizard(access_key="1234567890")
        with self.assertRaises(UserError):
            wizard.action_confirm_search()

    def test_wizard_rejects_empty_access_key(self):
        """Wizard should raise UserError when access key is empty."""
        wizard = self._create_wizard(access_key="")
        with self.assertRaises(UserError):
            wizard.action_confirm_search()

    def test_wizard_rejects_invalid_check_digit(self):
        """Wizard should raise UserError for wrong check digit."""
        # Valid key ends in 1; change last digit to 2
        invalid_key = "35200159594315000157550010000000012062777162"
        wizard = self._create_wizard(access_key=invalid_key)
        with self.assertRaises(UserError):
            wizard.action_confirm_search()

    def test_wizard_accepts_valid_access_key(self):
        """Wizard should accept a valid 44-digit key with correct check digit."""
        valid_key = "35200159594315000157550010000000012062777161"
        wizard = self._create_wizard(access_key=valid_key)
        with mock.patch.object(
            DefaultTransport,
            "post",
            return_value=response_sucesso_individual.encode("utf-8"),
        ):
            result = wizard.action_confirm_search()
        self.assertEqual(result["tag"], "display_notification")
        self.assertEqual(result["params"]["type"], "success")

    def test_wizard_nsu_search_skips_key_validation(self):
        """NSU search should not validate access_key."""
        wizard = self._create_wizard(
            search_type="nsu",
            nsu="200",
            access_key="invalid",
        )
        with mock.patch.object(
            DefaultTransport,
            "post",
            return_value=response_sucesso_individual.encode("utf-8"),
        ):
            result = wizard.action_confirm_search()
        self.assertEqual(result["tag"], "display_notification")

    # ── DF-e Inbox notification tests ────────────────────────────────────

    def _create_dfe_notification_user(self, login, dfe_notification=False):
        """Helper to create a user with the given dfe_notification preference."""
        return self.env["res.users"].create(
            {
                "name": f"DFe Test {login}",
                "login": login,
                "company_id": self.company.id,
                "company_ids": [(6, 0, [self.company.id])],
                "dfe_notification": dfe_notification,
            }
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_notification_enabled_receives(self, mock_post):
        """User with dfe_notification=True receives notification on third-party docs."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")
        user = self._create_dfe_notification_user("dfe_on", dfe_notification=True)

        # Mock response CNPJ (59594315000157) != company CNPJ (81583054000129)
        # so all documents are third-party
        self.company.dfe_search_documents()

        notifications = self.env["mail.message"].search(
            [
                ("message_type", "=", "user_notification"),
                ("partner_ids", "in", user.partner_id.id),
                ("body", "ilike", "%DF-e%"),
            ]
        )
        self.assertTrue(
            notifications,
            "User with dfe_notification=True should receive notification",
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_notification_disabled_skips(self, mock_post):
        """User with dfe_notification=False should NOT receive notification."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")
        user = self._create_dfe_notification_user("dfe_off", dfe_notification=False)

        self.company.dfe_search_documents()

        notifications = self.env["mail.message"].search(
            [
                ("message_type", "=", "user_notification"),
                ("partner_ids", "in", user.partner_id.id),
                ("body", "ilike", "%DF-e%"),
            ]
        )
        self.assertFalse(
            notifications,
            "User with dfe_notification=False should not receive notification",
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_notification_no_new_docs_137(self, mock_post):
        """Response 137 (no documents) should not trigger any notification."""
        mock_post.return_value = response_137.encode("utf-8")
        user = self._create_dfe_notification_user("dfe_137", dfe_notification=True)

        self.company.dfe_search_documents()

        notifications = self.env["mail.message"].search(
            [
                ("message_type", "=", "user_notification"),
                ("partner_ids", "in", user.partner_id.id),
                ("body", "ilike", "%DF-e%"),
            ]
        )
        self.assertFalse(
            notifications,
            "No notification should be sent when no new documents found (137)",
        )

    # ── Partner matching tests ───────────────────────────────────────────

    @mock.patch.object(DefaultTransport, "post")
    def test_partner_id_computed_on_dfe_search(self, mock_post):
        """partner_id should be set when a partner matches the access key CNPJ."""
        mock_post.return_value = response_sucesso_individual.encode("utf-8")

        # Access key CNPJ = 59594315000157 (positions 6-20)
        self.company.dfe_search_documents()

        dfe_doc = self.env["l10n_br_fiscal_dfe.document"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        self.assertTrue(
            dfe_doc.partner_id,
            "partner_id should be set when a partner with matching CNPJ exists",
        )
        self.assertEqual(
            dfe_doc.partner_id.cnpj_cpf_stripped,
            "59594315000157",
            "partner_id CNPJ should match the access key CNPJ",
        )

    def test_partner_id_false_when_no_match(self):
        """partner_id should be False when no partner matches the CNPJ."""
        # Use a CNPJ that doesn't exist in demo data (positions 6-20)
        fake_key = "35200199999999999999550010000000012062777161"
        dfe_doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": fake_key,
                "company_id": self.company.id,
            }
        )
        self.assertFalse(
            dfe_doc.partner_id,
            "partner_id should be False when no partner matches",
        )

    def test_action_match_partner_rematch(self):
        """action_match_partner should update partner_id for existing documents."""
        # Use a unique CNPJ that doesn't exist yet
        test_cnpj = "12345678000195"
        fake_key = "352001" + test_cnpj + "550010000000012062777161"
        dfe_doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": fake_key,
                "company_id": self.company.id,
            }
        )
        self.assertFalse(dfe_doc.partner_id)

        # Now create the partner and trigger re-match
        partner = self.env["res.partner"].create(
            {
                "name": "Late Partner DFe",
                "cnpj_cpf": "12.345.678/0001-95",
            }
        )
        dfe_doc.action_match_partner()

        self.assertEqual(
            dfe_doc.partner_id,
            partner,
            "action_match_partner should find the newly created partner",
        )

    # ── DFe record compute/display tests ──────────────────────────────────

    @mock.patch.object(DefaultTransport, "post")
    def test_event_type_dfe_label(self, mock_post):
        """event_type_dfe_label should resolve known codes and handle unknowns."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")
        self.company.dfe_search_documents()

        DfeRecord = self.env["l10n_br_fiscal_dfe.dfe"]
        dfe = DfeRecord.search([("company_id", "=", self.company.id)], limit=1)
        # Known event type
        dfe.event_type_dfe = "110111"
        self.assertTrue(dfe.event_type_dfe_label)

        # Unknown event type
        dfe.event_type_dfe = "999999"
        self.assertIn("999999", dfe.event_type_dfe_label)

        # Empty event type
        dfe.event_type_dfe = False
        self.assertFalse(dfe.event_type_dfe_label)

    @mock.patch.object(DefaultTransport, "post")
    def test_xml_pretty_computed(self, mock_post):
        """xml_pretty should format valid XML and handle missing/invalid data."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")
        self.company.dfe_search_documents()

        dfe = self.env["l10n_br_fiscal_dfe.dfe"].search(
            [
                ("company_id", "=", self.company.id),
                ("attachment_id", "!=", False),
            ],
            limit=1,
        )
        self.assertTrue(dfe.xml_pretty, "Valid XML should produce pretty output")

        # DFe without attachment should return False
        dfe_no_attach = self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
            }
        )
        self.assertFalse(dfe_no_attach.xml_pretty)

    def test_dfe_import_document_no_attachment(self):
        """import_document should raise UserError when no attachment exists."""
        dfe_doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200159594315000157550010000000012062777161",
                "company_id": self.company.id,
            }
        )
        self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": dfe_doc.access_key,
                "company_id": self.company.id,
                "dfe_document_id": dfe_doc.id,
                "dfe_nfe_document_type": "dfe_nfe_complete",
                "schema_type": "procNFe",
            }
        )
        with self.assertRaises(UserError):
            dfe_doc.import_document()

    # ── Distribution log tests ────────────────────────────────────────────

    def test_distribution_log_name_get(self):
        """Distribution log name_get should show [type] date format."""
        log = self.env["l10n_br_fiscal_dfe.distribution_log"].create(
            {
                "company_id": self.company.id,
                "log_type": "success",
                "message": "Test log",
            }
        )
        name = log.name_get()[0][1]
        self.assertIn("Success", name)

    # ── DFe document compute tests ────────────────────────────────────────

    def test_document_color_status(self):
        """color_status should reflect document state and DFe types."""
        dfe_doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
            }
        )
        # No DFe records → False
        self.assertFalse(dfe_doc.color_status)

        # Cancelled document
        dfe_doc.document_state = "2"
        dfe_doc._compute_color_status()
        self.assertEqual(dfe_doc.color_status, "muted")

    def test_document_manifestation_status(self):
        """manifestation_status should reflect latest MDE state."""
        dfe_doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
            }
        )
        # No manifestation → sem_manifestacao
        self.assertEqual(dfe_doc.manifestation_status, "sem_manifestacao")

    def test_document_manifestations_ids(self):
        """manifestations_ids should find MDE records for same access_key."""
        key = "35200159594315000157550010000000012062777161"
        dfe_doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": key,
                "company_id": self.company.id,
            }
        )
        mde = self.env["l10n_br_nfe.md_event"].create(
            {
                "access_key": key,
                "event_type": "ciente",
                "company_id": self.company.id,
                "document_type": "nfe",
                "state": "draft",
            }
        )
        self.assertIn(mde, dfe_doc.manifestations_ids)

    def test_document_create_nfe_md_action(self):
        """create_nfe_md_action should return wizard action."""
        dfe_doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
            }
        )
        action = dfe_doc.create_nfe_md_action()
        self.assertEqual(
            action["res_model"],
            "nfe_recipient_manifestation_event.wizard",
        )
        self.assertEqual(action["context"]["default_access_key"], dfe_doc.access_key)

    def test_document_import_no_complete(self):
        """import_document on document without complete DFe should raise."""
        dfe_doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
            }
        )
        with self.assertRaises(UserError):
            dfe_doc.import_document()

    # ── Wizard NSU validation tests ───────────────────────────────────────

    def test_wizard_nsu_empty_raises(self):
        """Empty NSU should raise UserError."""
        wizard = self._create_wizard(search_type="nsu", nsu="")
        with self.assertRaises(UserError):
            wizard.action_confirm_search()

    def test_wizard_nsu_non_numeric_raises(self):
        """Non-numeric NSU should raise UserError."""
        wizard = self._create_wizard(search_type="nsu", nsu="abc")
        with self.assertRaises(UserError):
            wizard.action_confirm_search()

    def test_wizard_nsu_zero_raises(self):
        """Zero NSU should raise UserError."""
        wizard = self._create_wizard(search_type="nsu", nsu="0")
        with self.assertRaises(UserError):
            wizard.action_confirm_search()

    @mock.patch.object(DefaultTransport, "post")
    def test_wizard_nsu_duplicate_raises(self, mock_post):
        """Already-existing NSU should raise UserError."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")
        self.company.dfe_search_documents()

        # NSU 201 was created by the search
        wizard = self._create_wizard(search_type="nsu", nsu="201")
        with self.assertRaises(UserError):
            wizard.action_confirm_search()

    def test_wizard_onchange_access_key_strips(self):
        """_onchange_access_key should strip non-digit characters."""
        wizard = self._create_wizard(
            access_key="3520 0159 5943",
        )
        wizard._onchange_access_key()
        self.assertEqual(wizard.access_key, "352001595943")

    # ── res_company coverage: event schemas ─────────────────────────────

    @mock.patch.object(DefaultTransport, "post")
    def test_create_from_resEvento(self, mock_post):
        """resEvento schema creates DFe record with event type."""
        response = _build_dfe_response(
            [("000000000000300", "resEvento_v1.00.xsd", _RESEVENTO_XML)],
            ult_nsu="000000000000300",
            max_nsu="000000000000300",
        )
        mock_post.return_value = response.encode("utf-8")
        self.company.dfe_search_documents()

        dfe_record = self.env["l10n_br_fiscal_dfe.dfe"].search(
            [
                ("company_id", "=", self.company.id),
                ("schema_type", "=", "resEvento"),
            ]
        )
        self.assertEqual(len(dfe_record), 1)
        self.assertEqual(dfe_record.dfe_nfe_document_type, "dfe_nfe_event")
        self.assertEqual(dfe_record.event_type_dfe, "210210")
        self.assertTrue(dfe_record.dfe_document_id)

    @mock.patch.object(DefaultTransport, "post")
    def test_create_from_procEventoNFe(self, mock_post):
        """procEventoNFe schema creates DFe record linked to document."""
        response = _build_dfe_response(
            [
                (
                    "000000000000301",
                    "procEventoNFe_v1.00.xsd",
                    _PROCEVENTONFE_XML,
                )
            ],
            ult_nsu="000000000000301",
            max_nsu="000000000000301",
        )
        mock_post.return_value = response.encode("utf-8")
        self.company.dfe_search_documents()

        dfe_record = self.env["l10n_br_fiscal_dfe.dfe"].search(
            [
                ("company_id", "=", self.company.id),
                ("schema_type", "=", "procEventoNFe"),
            ]
        )
        self.assertEqual(len(dfe_record), 1)
        self.assertEqual(dfe_record.dfe_nfe_document_type, "dfe_nfe_event")
        self.assertEqual(dfe_record.event_type_dfe, "210210")
        self.assertTrue(dfe_record.dfe_document_id)

    @mock.patch.object(DefaultTransport, "post")
    def test_create_from_unknown_schema(self, mock_post):
        """Unknown schema creates a minimal DFe record."""
        unknown_xml = (
            '<unknownDoc xmlns="http://example.com">' "<id>1</id></unknownDoc>"
        )
        response = _build_dfe_response(
            [("000000000000302", "unknownDoc_v1.00.xsd", unknown_xml)],
            ult_nsu="000000000000302",
            max_nsu="000000000000302",
        )
        mock_post.return_value = response.encode("utf-8")
        self.company.dfe_search_documents()

        dfe_record = self.env["l10n_br_fiscal_dfe.dfe"].search(
            [
                ("company_id", "=", self.company.id),
                ("schema_type", "=", "unknownDoc"),
            ]
        )
        self.assertEqual(len(dfe_record), 1)

    # ── res_company coverage: banner actions ────────────────────────────

    def test_action_banner_search_all(self):
        """action_banner_search_all delegates to current company."""
        self.company.dfe_next_query = False
        with mock.patch.object(
            type(self.company),
            "_dfe_document_distribution",
            return_value=None,
        ):
            ResCompany = self.env["res.company"].with_company(self.company)
            result = ResCompany.action_banner_search_all()
        self.assertEqual(result["tag"], "reload")

    def test_action_banner_specific_search(self):
        """action_banner_specific_search returns wizard action."""
        ResCompany = self.env["res.company"].with_company(self.company)
        result = ResCompany.action_banner_specific_search()
        self.assertEqual(result["res_model"], "dfe_specific_search_wizard")
        self.assertEqual(result["target"], "new")

    # ── res_company coverage: specific search paths ─────────────────────

    @mock.patch.object(DefaultTransport, "post")
    def test_specific_search_no_docs(self, mock_post):
        """Specific search with cStat=137 returns without error."""
        mock_post.return_value = response_137.encode("utf-8")
        key = "35200159594315000157550010000000012062777161"
        # Should not raise — 137 means "no documents found"
        self.company._dfe_search_specific_document(access_key=key)

    @mock.patch.object(DefaultTransport, "post")
    def test_specific_search_error_raises(self, mock_post):
        """Specific search with SEFAZ error raises ValidationError."""
        mock_post.return_value = response_rejeicao.encode("utf-8")
        key = "35200159594315000157550010000000012062777161"
        with self.assertRaises(ValidationError):
            self.company._dfe_search_specific_document(access_key=key)

    # ── res_company coverage: notification & cooldown ───────────────────

    def test_notify_own_documents_skipped(self):
        """_dfe_notify_users returns early when all docs are own company."""
        self._create_dfe_notification_user("dfe_own", dfe_notification=True)
        # Build access key with company's own CNPJ at positions 6-20
        cnpj = "".join(c for c in (self.company.vat or "") if c.isdigit())
        own_key = ("352001" + cnpj).ljust(44, "0")[:44]
        doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": own_key,
                "company_id": self.company.id,
            }
        )
        self.assertTrue(doc.is_own_document)
        self.company._dfe_notify_users(doc)

        notifications = self.env["mail.message"].search(
            [
                ("message_type", "=", "user_notification"),
                ("body", "ilike", "%DF-e%"),
            ]
        )
        self.assertFalse(notifications)

    def test_distribution_skips_during_cooldown(self):
        """_dfe_document_distribution returns early during cooldown."""
        self.company.dfe_next_query = fields.Datetime.now() + timedelta(hours=2)
        with mock.patch.object(DefaultTransport, "post") as mock_post:
            self.company._dfe_document_distribution()
            mock_post.assert_not_called()

    # ── dfe_document: short key, cfop, make_pdf, import ─────────────────

    def test_short_access_key_partner_and_own(self):
        """Short access key sets partner_id=False and is_own_document=False."""
        doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "123",
                "company_id": self.company.id,
            }
        )
        self.assertFalse(doc.partner_id)
        self.assertFalse(doc.is_own_document)

    def test_cfop_ids_without_complete_dfe(self):
        """cfop_ids is empty when document has no complete DFe."""
        doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
            }
        )
        self.assertFalse(doc.cfop_ids)

    def test_cfop_ids_with_invalid_xml(self):
        """cfop_ids handles corrupt XML in complete DFe gracefully."""
        doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
            }
        )
        dfe = self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": doc.access_key,
                "company_id": self.company.id,
                "dfe_document_id": doc.id,
                "dfe_nfe_document_type": "dfe_nfe_complete",
                "schema_type": "procNFe",
            }
        )
        # Attach invalid XML
        dfe.attachment_id = self.env["ir.attachment"].create(
            {
                "name": "bad.xml",
                "datas": base64.b64encode(b"not xml at all"),
                "res_model": "l10n_br_fiscal_dfe.dfe",
                "res_id": dfe.id,
            }
        )
        doc.invalidate_cache(["cfop_ids"])
        self.assertFalse(doc.cfop_ids)

    def test_cfop_ids_complete_dfe_without_attachment(self):
        """cfop_ids handles complete DFe without attachment data."""
        doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
            }
        )
        self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": doc.access_key,
                "company_id": self.company.id,
                "dfe_document_id": doc.id,
                "dfe_nfe_document_type": "dfe_nfe_complete",
                "schema_type": "procNFe",
            }
        )
        doc.invalidate_cache(["cfop_ids"])
        self.assertFalse(doc.cfop_ids)

    def test_make_pdf_without_complete_dfe(self):
        """make_pdf raises UserError when no complete DFe exists."""
        doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
            }
        )
        with self.assertRaises(UserError):
            doc.make_pdf()

    # ── dfe.py: xml_pretty with corrupt attachment ──────────────────────

    def test_xml_pretty_with_corrupt_attachment(self):
        """xml_pretty returns False when attachment has invalid XML."""
        dfe = self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
                "dfe_nfe_document_type": "dfe_nfe_complete",
                "schema_type": "procNFe",
            }
        )
        dfe.attachment_id = self.env["ir.attachment"].create(
            {
                "name": "corrupt.xml",
                "datas": base64.b64encode(b"<<<not valid xml>>>"),
                "res_model": "l10n_br_fiscal_dfe.dfe",
                "res_id": dfe.id,
            }
        )
        self.assertFalse(dfe.xml_pretty)

    # ── res_users: SELF_WRITEABLE_FIELDS ────────────────────────────────

    def test_user_can_write_dfe_notification(self):
        """User can write dfe_notification on their own record."""
        user = self._create_dfe_notification_user("dfe_write", dfe_notification=False)
        user_self = user.with_user(user)
        user_self.write({"dfe_notification": True})
        self.assertTrue(user.dfe_notification)

    # ── Coverage: _dfe_log branch paths ──────────────────────────────────

    def test_dfe_log_with_string_envio_xml(self):
        """_dfe_log handles envio_xml as a string (not bytes)."""
        result = mock.MagicMock()
        result.envio_xml = "<xml>request</xml>"  # string, not bytes
        result.retorno = None
        self.company._dfe_log("Test message", result=result)

        log = self.env["l10n_br_fiscal_dfe.distribution_log"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        self.assertEqual(log.request_xml, "<xml>request</xml>")

    def test_dfe_log_with_bytes_envio_xml(self):
        """_dfe_log handles envio_xml as bytes."""
        result = mock.MagicMock()
        result.envio_xml = b"<xml>request</xml>"
        result.retorno = None
        self.company._dfe_log("Test bytes", result=result)

        log = self.env["l10n_br_fiscal_dfe.distribution_log"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        self.assertEqual(log.request_xml, "<xml>request</xml>")

    def test_dfe_log_retorno_with_content_attr(self):
        """_dfe_log reads retorno.content when _content is missing."""
        result = mock.MagicMock(spec=["retorno"])
        del result.envio_xml  # no envio_xml attribute
        retorno = mock.MagicMock(spec=["content"])
        retorno.content = b"<xml>response via content</xml>"
        result.retorno = retorno
        self.company._dfe_log("Test content attr", result=result)

        log = self.env["l10n_br_fiscal_dfe.distribution_log"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        self.assertEqual(log.response_xml, "<xml>response via content</xml>")

    def test_dfe_log_retorno_content_as_string(self):
        """_dfe_log handles retorno content as string (not bytes)."""
        result = mock.MagicMock(spec=["retorno"])
        del result.envio_xml
        retorno = mock.MagicMock(spec=["_content"])
        retorno._content = "<xml>string response</xml>"
        result.retorno = retorno
        self.company._dfe_log("Test string content", result=result)

        log = self.env["l10n_br_fiscal_dfe.distribution_log"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        self.assertEqual(log.response_xml, "<xml>string response</xml>")

    def test_dfe_log_retorno_no_content(self):
        """_dfe_log handles retorno with no content attributes."""
        result = mock.MagicMock(spec=["retorno"])
        del result.envio_xml
        retorno = mock.MagicMock(spec=[])
        result.retorno = retorno
        self.company._dfe_log("Test no content", result=result)

        log = self.env["l10n_br_fiscal_dfe.distribution_log"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        self.assertFalse(log.response_xml)

    # ── Coverage: _dfe_process_distribution edge cases ───────────────────

    @mock.patch.object(DefaultTransport, "post")
    def test_zero_nsu_unknown_schema_no_dedup(self, mock_post):
        """Zero NSU with unknown schema (no extractor) creates record."""
        unknown_xml = '<myDoc xmlns="http://example.com"><data>1</data></myDoc>'
        response = _build_dfe_response(
            [("000000000000000", "myDoc_v1.00.xsd", unknown_xml)],
            ult_nsu="000000000000300",
            max_nsu="000000000000300",
        )
        mock_post.return_value = response.encode("utf-8")

        self.company._dfe_search_specific_document(access_key="any_key")

        dfe_record = self.env["l10n_br_fiscal_dfe.dfe"].search(
            [
                ("company_id", "=", self.company.id),
                ("schema_type", "=", "myDoc"),
            ]
        )
        self.assertEqual(len(dfe_record), 1)
        self.assertFalse(dfe_record.nsu, "NSU should be False for zero-NSU")

    # ── Coverage: _dfe_sync_cron_nextcall without cron ───────────────────

    def test_sync_cron_nextcall_no_cron(self):
        """_dfe_sync_cron_nextcall returns gracefully when cron ref is missing."""
        # Temporarily make the ref return False
        with mock.patch.object(
            type(self.env),
            "ref",
            return_value=False,
        ):
            # Should not raise
            self.company._dfe_sync_cron_nextcall()

    # ── Coverage: _update_metadata skip ──────────────────────────────────

    def test_update_metadata_skip_when_complete_exists(self):
        """_update_metadata with is_complete=False skips when complete DFe exists."""
        dfe_doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
                "emitter": "Original Emitter",
            }
        )
        self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": dfe_doc.access_key,
                "company_id": self.company.id,
                "dfe_document_id": dfe_doc.id,
                "dfe_nfe_document_type": "dfe_nfe_complete",
                "schema_type": "procNFe",
            }
        )
        # Try to update with is_complete=False — should be skipped
        dfe_doc._update_metadata({"emitter": "New Emitter"}, is_complete=False)
        self.assertEqual(
            dfe_doc.emitter,
            "Original Emitter",
            "Metadata should not be updated when complete DFe already exists",
        )

    # ── Coverage: DFe name_get without type ──────────────────────────────

    def test_dfe_name_get_without_type(self):
        """name_get handles DFe record without dfe_nfe_document_type."""
        dfe = self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": "35200199999999999999550010000000019999999991",
                "company_id": self.company.id,
            }
        )
        name = dfe.name_get()[0][1]
        self.assertIn("35200199999999999999550010000000019999999991", name)

    # ── Coverage: notify fallback URL ────────────────────────────────────

    def test_notify_users_fallback_url(self):
        """_dfe_notify_users uses fallback URL when action ref is missing."""
        user = self._create_dfe_notification_user("dfe_fb", dfe_notification=True)
        key = "35200159594315000157550010000000012062777161"
        doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": key,
                "company_id": self.company.id,
            }
        )
        with mock.patch.object(
            type(self.env),
            "ref",
            return_value=False,
        ):
            self.company._dfe_notify_users(doc)

        notifications = self.env["mail.message"].search(
            [
                ("message_type", "=", "user_notification"),
                ("partner_ids", "in", user.partner_id.id),
                ("body", "ilike", "%DF-e%"),
            ]
        )
        self.assertTrue(notifications)

    # ── Coverage: _dfe_get_or_create_document short key ──────────────────

    def test_get_or_create_document_short_key(self):
        """_dfe_get_or_create_document with short key skips metadata extraction."""
        doc = self.company._dfe_get_or_create_document("SHORT_KEY")
        self.assertTrue(doc)
        self.assertEqual(doc.access_key, "SHORT_KEY")
        self.assertFalse(doc.vat, "Short key should not extract CNPJ metadata")

    # ── Timezone: dhEmi and dhRegEvento must be converted to UTC ─────────

    @mock.patch.object(DefaultTransport, "post")
    def test_resnfe_dhemi_converted_to_utc(self, mock_post):
        """resNFe dhEmi with -03:00 offset must be stored as UTC."""
        resnfe_xml = (
            '<resNFe xmlns="http://www.portalfiscal.inf.br/nfe">'
            "<chNFe>35200159594315000157550010000000012062777161</chNFe>"
            "<CNPJ>59594315000157</CNPJ>"
            "<xNome>Test Emitter TZ</xNome>"
            "<dhEmi>2026-02-23T12:15:38-03:00</dhEmi>"
            "<tpNF>1</tpNF>"
            "<vNF>1000.00</vNF>"
            "<cSitNFe>1</cSitNFe>"
            "</resNFe>"
        )
        response = _build_dfe_response(
            [("000000000000400", "resNFe_v1.00.xsd", resnfe_xml)],
            ult_nsu="000000000000400",
            max_nsu="000000000000400",
        )
        mock_post.return_value = response.encode("utf-8")
        self.company.dfe_search_documents()

        dfe_doc = self.env["l10n_br_fiscal_dfe.document"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        self.assertTrue(dfe_doc.document_emission_date)
        # 12:15:38 BRT (-03:00) = 15:15:38 UTC
        self.assertEqual(dfe_doc.document_emission_date.hour, 15)
        self.assertEqual(dfe_doc.document_emission_date.minute, 15)
        self.assertEqual(dfe_doc.document_emission_date.second, 38)

    def test_mde_protocol_date_converted_to_utc(self):
        """validate_event_response dhRegEvento with offset must be stored as UTC."""
        mde = self.env["l10n_br_nfe.md_event"].create(
            {
                "access_key": "35200159594315000157550010000000012062777161",
                "event_type": "ciente",
                "company_id": self.company.id,
                "document_type": "nfe",
                "state": "draft",
            }
        )

        result = mock.MagicMock()
        result.retorno.status_code = 200
        result.retorno._content = b"<xml>response</xml>"
        inf_evento = result.resposta.retEvento.__getitem__.return_value.infEvento
        inf_evento.cStat = "135"
        inf_evento.xMotivo = "Evento registrado"
        inf_evento.nProt = "891220000000001"
        inf_evento.dhRegEvento = "2026-02-23T10:30:00-03:00"

        mde.validate_event_response(result, ["135"])

        self.assertEqual(mde.state, "done")
        # 10:30:00 BRT (-03:00) = 13:30:00 UTC
        self.assertEqual(mde.protocol_date.hour, 13)
        self.assertEqual(mde.protocol_date.minute, 30)
        self.assertEqual(mde.protocol_date.second, 0)
