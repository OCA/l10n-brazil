# Copyright 2026 Engenere.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""SOAP fixtures of the CTeDistribuicaoDFe web service (NT 2015.002)."""

import base64
import gzip
from io import BytesIO

from odoo.modules.module import get_module_resource

CTE_NS = "http://www.portalfiscal.inf.br/cte"

# Sample CT-e of l10n_br_cte, issued by "Empresa Simples Nacional"
# (59.594.315/0001-57) with the lucro presumido company as recipient.
CTE_ACCESS_KEY = "35240759594315000157570010000057311040445890"
CTE_OS_ACCESS_KEY = "35261059594315000157670010000000121000000017"
GTVE_ACCESS_KEY = "35261059594315000157640010000000051000000015"


def _prot_cte(access_key, model_tag="protCTe"):
    return (
        f'<{model_tag} versao="4.00"><infProt>'
        "<tpAmb>2</tpAmb><verAplic>SP_CTE_PL_4.00</verAplic>"
        f"<chCTe>{access_key}</chCTe>"
        "<dhRecbto>2024-07-10T10:00:00-03:00</dhRecbto>"
        "<nProt>135240000000002</nProt><digVal>YWJj</digVal>"
        "<cStat>100</cStat><xMotivo>Autorizado o uso do CT-e</xMotivo>"
        f"</infProt></{model_tag}>"
    )


def cte_proc_xml():
    """``cteProc`` built from the l10n_br_cte sample CT-e plus a protocol."""
    path = get_module_resource(
        "l10n_br_cte",
        "tests",
        "cte",
        "v4_00",
        "leiauteCTe",
        f"CTe{CTE_ACCESS_KEY}.xml",
    )
    with open(path, "rb") as sample:
        cte = sample.read().decode("utf-8")
    cte = cte.split("?>", 1)[1].strip()
    return (
        f'<cteProc xmlns="{CTE_NS}" versao="4.00">'
        f"{cte}{_prot_cte(CTE_ACCESS_KEY)}</cteProc>"
    )


def cte_os_proc_xml():
    """Minimal ``cteOSProc``: only what the monitor reads."""
    return (
        f'<cteOSProc xmlns="{CTE_NS}" versao="4.00">'
        '<CTeOS versao="4.00">'
        f'<infCte versao="4.00" Id="CTe{CTE_OS_ACCESS_KEY}">'
        "<ide><cUF>35</cUF><cCT>00000012</cCT><CFOP>6932</CFOP>"
        "<natOp>Transporte de pessoas</natOp><mod>67</mod><serie>1</serie>"
        "<nCT>12</nCT><dhEmi>2026-10-01T08:00:00-03:00</dhEmi>"
        "<tpImp>1</tpImp><tpEmis>1</tpEmis><cDV>7</cDV><tpAmb>2</tpAmb>"
        "<tpCTe>0</tpCTe><procEmi>0</procEmi><verProc>1.0</verProc>"
        "<cMunEnv>3550308</cMunEnv><xMunEnv>Sao Paulo</xMunEnv>"
        "<UFEnv>SP</UFEnv><modal>01</modal><tpServ>6</tpServ>"
        "<indIEToma>1</indIEToma></ide>"
        "<emit><CNPJ>59594315000157</CNPJ><IE>755338250133</IE>"
        "<xNome>Empresa Simples Nacional</xNome></emit>"
        "<vPrest><vTPrest>250.00</vTPrest><vRec>250.00</vRec></vPrest>"
        "<imp><ICMS><ICMSSN><CST>90</CST><indSN>1</indSN></ICMSSN></ICMS></imp>"
        "</infCte></CTeOS>"
        f"{_prot_cte(CTE_OS_ACCESS_KEY)}</cteOSProc>"
    )


def gtve_proc_xml():
    """Minimal ``GTVeProc``: the GTV-e has no service amount."""
    return (
        f'<GTVeProc xmlns="{CTE_NS}" versao="4.00">'
        '<GTVe versao="4.00">'
        f'<infCte versao="4.00" Id="CTe{GTVE_ACCESS_KEY}">'
        "<ide><cUF>35</cUF><cCT>00000005</cCT><CFOP>5932</CFOP>"
        "<natOp>Transporte de valores</natOp><mod>64</mod><serie>1</serie>"
        "<nCT>5</nCT><dhEmi>2026-10-02T09:30:00-03:00</dhEmi>"
        "<tpImp>1</tpImp><tpEmis>1</tpEmis><cDV>5</cDV><tpAmb>2</tpAmb>"
        "<tpCTe>4</tpCTe><procEmi>0</procEmi><verProc>1.0</verProc>"
        "<cMunEnv>3550308</cMunEnv><xMunEnv>Sao Paulo</xMunEnv>"
        "<UFEnv>SP</UFEnv><modal>01</modal><tpServ>9</tpServ></ide>"
        "<emit><CNPJ>59594315000157</CNPJ><IE>755338250133</IE>"
        "<xNome>Empresa Simples Nacional</xNome></emit>"
        "</infCte></GTVe>"
        f"{_prot_cte(GTVE_ACCESS_KEY)}</GTVeProc>"
    )


def proc_evento_cte_xml(access_key=CTE_ACCESS_KEY, tp_evento="110111"):
    """``procEventoCTe`` registered against ``access_key``."""
    return (
        f'<procEventoCTe xmlns="{CTE_NS}" versao="4.00">'
        '<eventoCTe versao="4.00">'
        f'<infEvento Id="ID{tp_evento}{access_key}01">'
        "<cOrgao>35</cOrgao><tpAmb>2</tpAmb><CNPJ>59594315000157</CNPJ>"
        f"<chCTe>{access_key}</chCTe>"
        "<dhEvento>2024-07-11T10:00:00-03:00</dhEvento>"
        f"<tpEvento>{tp_evento}</tpEvento><nSeqEvento>1</nSeqEvento>"
        '<detEvento versaoEvento="4.00"><evCancCTe>'
        "<descEvento>Cancelamento</descEvento>"
        "<nProt>135240000000002</nProt><xJust>Teste de cancelamento</xJust>"
        "</evCancCTe></detEvento></infEvento></eventoCTe>"
        '<retEventoCTe versao="4.00"><infEvento>'
        "<tpAmb>2</tpAmb><verAplic>SP_CTE_PL_4.00</verAplic>"
        "<cOrgao>35</cOrgao><cStat>135</cStat>"
        "<xMotivo>Evento registrado e vinculado ao CT-e</xMotivo>"
        f"<chCTe>{access_key}</chCTe><tpEvento>{tp_evento}</tpEvento>"
        "<xEvento>Cancelamento</xEvento><nSeqEvento>1</nSeqEvento>"
        "<dhRegEvento>2024-07-11T10:00:01-03:00</dhRegEvento>"
        "<nProt>135240000000003</nProt>"
        "</infEvento></retEventoCTe></procEventoCTe>"
    )


def gzip_base64(xml_str):
    """Gzip and base64-encode an XML string (like SEFAZ docZip)."""
    buf = BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        gz.write(xml_str.encode("utf-8"))
    return base64.b64encode(buf.getvalue()).decode("ascii")


def build_cte_dfe_response(
    doczip_list=(),
    cstat="138",
    motivo="Documento(s) localizado(s)",
    ult_nsu="000000000000101",
    max_nsu="000000000000101",
):
    """SOAP 1.2 envelope of a ``cteDistDFeInteresse`` response.

    doczip_list: iterable of (nsu_str, schema_str, xml_content) tuples.
    """
    parts = []
    for nsu, schema, xml_content in doczip_list:
        parts.append(
            f'<docZip NSU="{nsu}" schema="{schema}">'
            f"{gzip_base64(xml_content)}</docZip>"
        )
    lote = f"<loteDistDFeInt>{''.join(parts)}</loteDistDFeInt>" if parts else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
        "<soap:Body><cteDistDFeInteresseResponse"
        ' xmlns="http://www.portalfiscal.inf.br/cte/wsdl/CTeDistribuicaoDFe">'
        "<cteDistDFeInteresseResult>"
        f'<retDistDFeInt xmlns="{CTE_NS}" versao="1.00">'
        "<tpAmb>2</tpAmb><verAplic>1.5.0</verAplic>"
        f"<cStat>{cstat}</cStat><xMotivo>{motivo}</xMotivo>"
        "<dhResp>2026-11-02T10:00:00-03:00</dhResp>"
        f"<ultNSU>{ult_nsu}</ultNSU><maxNSU>{max_nsu}</maxNSU>"
        f"{lote}</retDistDFeInt></cteDistDFeInteresseResult>"
        "</cteDistDFeInteresseResponse></soap:Body></soap:Envelope>"
    ).encode()


def response_cte_and_cancel():
    """cStat 138 with a complete CT-e (NSU 100) and its cancellation (NSU 101)."""
    return build_cte_dfe_response(
        [
            ("000000000000100", "procCTe_v4.00.xsd", cte_proc_xml()),
            ("000000000000101", "procEventoCTe_v4.00.xsd", proc_evento_cte_xml()),
        ]
    )


def response_cte_only():
    return build_cte_dfe_response(
        [("000000000000100", "procCTe_v4.00.xsd", cte_proc_xml())],
        ult_nsu="000000000000100",
        max_nsu="000000000000100",
    )


def response_no_docs():
    return build_cte_dfe_response(
        cstat="137",
        motivo="Nenhum documento localizado para o Contribuinte",
        ult_nsu="000000000000100",
        max_nsu="000000000000100",
    )


def response_rate_limited():
    return build_cte_dfe_response(
        cstat="656",
        motivo="Consumo Indevido",
        ult_nsu="000000000000300",
        max_nsu="000000000000300",
    )
