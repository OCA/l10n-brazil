# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=line-too-long

from unittest import mock

from erpbrasil.edoc.resposta import analisar_retorno_raw
from nfelib.nfe.ws.edoc_legacy import DocumentoElectronicoAdapter
from nfelib.v4_00 import retDistDFeInt

from odoo.tests.common import TransactionCase

from ..tools import utils

response_sucesso_multiplos = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><nfeDistDFeInteresseResponse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"><nfeDistDFeInteresseResult><retDistDFeInt xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01"><tpAmb>1</tpAmb><verAplic>1.4.0</verAplic><cStat>138</cStat><xMotivo>Documento(s) localizado(s)</xMotivo><dhResp>2022-04-04T11:54:49-03:00</dhResp><ultNSU>000000000000201</ultNSU><maxNSU>000000000000201</maxNSU><loteDistDFeInt><docZip NSU="000000000000200" schema="resNFe_v1.00.xsd">H4sIAAAAAAAEAIVS22qDQBD9FfFdd9Z7ZLKQphosqQ3mQuibMZto8RJcifn8rjG9PZUdZg7DOWeGYbHlIg65cqvKWvg3cZyqedddfEL6vtd7U2/aMzEAKNm/LtdZzqtU/SYX/5O1ohZdWmdcVa68FWkzVakO8PD4o780bZeWp0JkaakX9Uk/tKQ+cZVhlssVmUkNoPLZnjcAGKBtDwVMzzIodak3AIO6HpJRg/N49cL+apDcm3iLm4qz99lKWSSzMJrPlEAJnqPNWyJRlATLCMnIwShgUkqpNLEAHBOJ7OAxD6qCGWCARkEDZwPg30MDU2YkIwG7SxwyiuRe8SqTN3H1iXQZMB6L8y4t2W73sXdtJ+6TUDhGveaLbc9DsXyyt1NpNZLkzIRnh675PZZOfMP2LfNn7IOD9aptOkaHy5meDS44FnWRjG3M1kU3HEmu9gWRjP+BfQI6BY33GAIAAA==</docZip><docZip NSU="000000000000201" schema="procNFe_v4.00.xsd">H4sIAAAAAAAAA51WzXKjRhC+5ykoX1MWMyAssTWeiozQhpSFKEu7dwxjmwQYLUJYldfJOS+QY/bF0t0DWF5nt7JRqejub3q6p3/mR9QPKml0ZnWqOaT6+mI6YezCOlVlfbi+eGrb/Tvbfn5+nux106blQ3HI0nJS1A+T+8aGuRdSxCv1Xfog4JTXDqP8+gJQ13MY457v+VOXewz5mQeUs/7HHXblzGYzfsXRVK6kyD6spOsJG6nI4pUcNAACSdRpu9nLj6rOU2EbQVQ6lx7MQSoOqimU5MI2jKhhFkhIRP4UVoV0mMMuGYf/jjvvGIP/j4zDV9hGAfS2aRHW7bdVex3R7o0LohDFUh1alHtOZOtjvXoPUTHOPQfiMDLMi6q9mYgMyOD8YADiRLb8iCISGF1U99LBQWTEQwEhUaA9B6XIV0WdluR74BFNGnWQjEBixR56BAMFbGAFVBBbR25yra2bJj0UpbUJFlbHp8IeBjEo8KSqAuIK4uQX+bq6wiZQnGJdKbkLt7vQurS2RbUv1cGK06zQsChhm3FxWqWQwG+o0biAYqsmJJ+n28dG3h1TK0mPpbaWRXoANQRF3WjpzaFPkKGkv045TMbvojxWn/+sCw3zCIVG2ybCxn4LwkTyOXcwGggFJJElKdaEeXOwQrw4ETEpAiMGfNC1kg53obl9/wqakQBhn609CiW0v+vOwT53XWEDIIK7HdYLCSiTXk5dQ4mc86nv+jMfszv3X2c3Xl2GVriOdtFyAdRarG+iMIZMLkPr5816c7t5vwgWG0wsjH5c3G7urFW0DRa3Y/5pcaZJx8Ru0+qoSmutm4M6Ty3HXUmpPQX7EnbG339ZKezCBhwEuv71WLfa4h7EQuPidJMWDajfNFr/VhY14D0y1MZjLpu/qs328x/aVPYrxWFTb3bFrv5XcTyPc3c6mzvQrK/LYzIAuyMKx707Cli26RWbOj6cQq47NWVTVVqUMisLVbeK/zQwk0xXcDZiJXEcTgkykavWqqNWVdcXeNDBnstx8UjCy2Cz5rjJE4OGi1hiwd7vohhQFCEoHAvS+6IGS89F+2QtNRQIA6RZcbCW/pS5LjUuSiJYbRLpcQbdT6w4BrqSH+JoKWxixSf88gmjOSSI7kNN4HTCxh/sfoOKjpzRIIAv6901xf0XayZIHIn0Pg30icjo1YDgwMBv/JpxqMZOD3VBjs4t8A4nhj600FJRsN6a7zbmjEuhm+IRzzeiIthutjE0Cu40YsU+aFQOjDOZka9BFh0yxpBkExc66xyB6r/4sHuvSYR5qD9J3/cxfOAQjHfoeCc9F73i/u5Bm2Yk0ZY+m2PbGMWp3yt2NwH4phQAJ/aoyvqUkQCl6CEsBAL2aMkmOdisonik/8FHP2F0MxjozgYwFz1snxu2R3QsCHQ+Xo26xTsI80Rl+8JpRwnsAZNMIrDxdH2OG0B0qyAZYGTRHsQyWqS4XgASQe8FMUIP3sEKz3GU/7XHu1WjWjXqkgB+1OPoCFjRwSKzASEegonGKCIUkxc56YGl6nR5hhr5bYG/UocOK6AH1AiiwwdJHwK+SeyxAHZfkbZJ64N5Opl4fHo+9bHZw/A+faTTK0GKz4f0cXhIIEI4biqj0OF3TB0i9jDX3hsLD4u8yHpmBc9JLZc6O1YKLw+8/YpcW/DYfGet0yazlqrS6G1U7oUiMxw9e2z6wnnQvnmIkiOoYUsv0iiHO8xx+NxxvKnD5t7F21dV9oTWvufhChue5ogaHckvXMCVSbDItm0Ko5gaw8KNp9ui03JxbOGQ+j2FyLV1PGgrTy242/Hy7TUoVmPG7uMErn/ryx/+AZs2W+n2CwAA</docZip></loteDistDFeInt></retDistDFeInt></nfeDistDFeInteresseResult></nfeDistDFeInteresseResponse></soap:Body></soap:Envelope>"""  # noqa: E501

response_sucesso_individual = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><nfeDistDFeInteresseResponse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"><nfeDistDFeInteresseResult><retDistDFeInt xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01"><tpAmb>1</tpAmb><verAplic>1.4.0</verAplic><cStat>138</cStat><xMotivo>Documento(s) localizado(s)</xMotivo><dhResp>2022-04-04T11:54:49-03:00</dhResp><ultNSU>000000000000201</ultNSU><maxNSU>000000000000201</maxNSU><loteDistDFeInt><docZip NSU="000000000000201" schema="procNFe_v4.00.xsd">H4sIAAAAAAAAA51WzXKjRhC+5ykoX1MWMyAssTWeiozQhpSFKEu7dwxjmwQYLUJYldfJOS+QY/bF0t0DWF5nt7JRqejub3q6p3/mR9QPKml0ZnWqOaT6+mI6YezCOlVlfbi+eGrb/Tvbfn5+nux106blQ3HI0nJS1A+T+8aGuRdSxCv1Xfog4JTXDqP8+gJQ13MY457v+VOXewz5mQeUs/7HHXblzGYzfsXRVK6kyD6spOsJG6nI4pUcNAACSdRpu9nLj6rOU2EbQVQ6lx7MQSoOqimU5MI2jKhhFkhIRP4UVoV0mMMuGYf/jjvvGIP/j4zDV9hGAfS2aRHW7bdVex3R7o0LohDFUh1alHtOZOtjvXoPUTHOPQfiMDLMi6q9mYgMyOD8YADiRLb8iCISGF1U99LBQWTEQwEhUaA9B6XIV0WdluR74BFNGnWQjEBixR56BAMFbGAFVBBbR25yra2bJj0UpbUJFlbHp8IeBjEo8KSqAuIK4uQX+bq6wiZQnGJdKbkLt7vQurS2RbUv1cGK06zQsChhm3FxWqWQwG+o0biAYqsmJJ+n28dG3h1TK0mPpbaWRXoANQRF3WjpzaFPkKGkv045TMbvojxWn/+sCw3zCIVG2ybCxn4LwkTyOXcwGggFJJElKdaEeXOwQrw4ETEpAiMGfNC1kg53obl9/wqakQBhn609CiW0v+vOwT53XWEDIIK7HdYLCSiTXk5dQ4mc86nv+jMfszv3X2c3Xl2GVriOdtFyAdRarG+iMIZMLkPr5816c7t5vwgWG0wsjH5c3G7urFW0DRa3Y/5pcaZJx8Ru0+qoSmutm4M6Ty3HXUmpPQX7EnbG339ZKezCBhwEuv71WLfa4h7EQuPidJMWDajfNFr/VhY14D0y1MZjLpu/qs328x/aVPYrxWFTb3bFrv5XcTyPc3c6mzvQrK/LYzIAuyMKx707Cli26RWbOj6cQq47NWVTVVqUMisLVbeK/zQwk0xXcDZiJXEcTgkykavWqqNWVdcXeNDBnstx8UjCy2Cz5rjJE4OGi1hiwd7vohhQFCEoHAvS+6IGS89F+2QtNRQIA6RZcbCW/pS5LjUuSiJYbRLpcQbdT6w4BrqSH+JoKWxixSf88gmjOSSI7kNN4HTCxh/sfoOKjpzRIIAv6901xf0XayZIHIn0Pg30icjo1YDgwMBv/JpxqMZOD3VBjs4t8A4nhj600FJRsN6a7zbmjEuhm+IRzzeiIthutjE0Cu40YsU+aFQOjDOZka9BFh0yxpBkExc66xyB6r/4sHuvSYR5qD9J3/cxfOAQjHfoeCc9F73i/u5Bm2Yk0ZY+m2PbGMWp3yt2NwH4phQAJ/aoyvqUkQCl6CEsBAL2aMkmOdisonik/8FHP2F0MxjozgYwFz1snxu2R3QsCHQ+Xo26xTsI80Rl+8JpRwnsAZNMIrDxdH2OG0B0qyAZYGTRHsQyWqS4XgASQe8FMUIP3sEKz3GU/7XHu1WjWjXqkgB+1OPoCFjRwSKzASEegonGKCIUkxc56YGl6nR5hhr5bYG/UocOK6AH1AiiwwdJHwK+SeyxAHZfkbZJ64N5Opl4fHo+9bHZw/A+faTTK0GKz4f0cXhIIEI4biqj0OF3TB0i9jDX3hsLD4u8yHpmBc9JLZc6O1YKLw+8/YpcW/DYfGet0yazlqrS6G1U7oUiMxw9e2z6wnnQvnmIkiOoYUsv0iiHO8xx+NxxvKnD5t7F21dV9oTWvufhChue5ogaHckvXMCVSbDItm0Ko5gaw8KNp9ui03JxbOGQ+j2FyLV1PGgrTy242/Hy7TUoVmPG7uMErn/ryx/+AZs2W+n2CwAA</docZip></loteDistDFeInt></retDistDFeInt></nfeDistDFeInteresseResult></nfeDistDFeInteresseResponse></soap:Body></soap:Envelope>"""  # noqa: E501

response_rejeicao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><nfeDistDFeInteresseResponse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe"><nfeDistDFeInteresseResult><retDistDFeInt xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.01"><tpAmb>2</tpAmb><verAplic>1.4.0</verAplic><cStat>589</cStat><xMotivo>Rejeicao: Numero do NSU informado superior ao maior NSU da base de dados doAmbiente Nacional</xMotivo><dhResp>2022-04-04T11:54:49-03:00</dhResp><ultNSU>000000000000000</ultNSU><maxNSU>000000000000000</maxNSU></retDistDFeInt></nfeDistDFeInteresseResult></nfeDistDFeInteresseResponse></soap:Body></soap:Envelope>"""  # noqa: E501


class FakeRetorno:
    def __init__(self, text, status_code=200):
        self.text = text
        self.content = text.encode("utf-8")
        self.status_code = status_code

    def raise_for_status(self):
        pass


def mocked_post_success_multiple(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeDistDFeInteresse",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_sucesso_multiplos),
        retDistDFeInt,
    )


def mocked_post_success_single(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeDistDFeInteresse",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_sucesso_individual),
        retDistDFeInt,
    )


def mocked_post_error_rejection(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeDistDFeInteresse",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_rejeicao),
        retDistDFeInt,
    )


def mocked_post_error_status_code(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeDistDFeInteresse",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_rejeicao, status_code=500),
        retDistDFeInt,
    )


class TestDFe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.dfe_id = cls.env["l10n_br_fiscal.dfe"].create(
            {"company_id": cls.env.ref("l10n_br_base.empresa_lucro_presumido").id}
        )

    @mock.patch.object(
        DocumentoElectronicoAdapter, "_post", side_effect=mocked_post_success_multiple
    )
    def test_search_dfe_success(self, _mock_post):
        self.assertEqual(self.dfe_id.display_name, "Empresa Lucro Presumido - NSU: 0")

        self.dfe_id.search_documents()
        self.assertEqual(self.dfe_id.last_nsu, utils.format_nsu("201"))

    def test_search_dfe_error(self):
        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_error_status_code,
        ):
            self.dfe_id.search_documents()
            self.assertEqual(self.dfe_id.last_nsu, "000000000000000")

        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_error_rejection,
        ):
            self.dfe_id.search_documents()
            self.assertEqual(self.dfe_id.last_nsu, "000000000000000")

        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=KeyError("foo"),
        ):
            self.dfe_id.search_documents()

    def test_cron_search_documents(self):
        self.dfe_id.use_cron = True

        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_error_status_code,
        ):
            self.dfe_id._cron_search_documents()
            self.assertEqual(self.dfe_id.last_nsu, "000000000000000")

        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_success_multiple,
        ):
            self.dfe_id._cron_search_documents()
            self.assertEqual(self.dfe_id.last_nsu, "000000000000201")

    def test_utils(self):
        nsu_formatted = utils.format_nsu("100")
        self.assertEqual(nsu_formatted, "000000000000100")

        cnpj_masked = utils.mask_cnpj(False)
        self.assertFalse(cnpj_masked)

        cnpj_masked = utils.mask_cnpj("1234")
        self.assertEqual(cnpj_masked, "1234")

        cnpj_masked = utils.mask_cnpj("31282204000196")
        self.assertEqual(cnpj_masked, "31.282.204/0001-96")
