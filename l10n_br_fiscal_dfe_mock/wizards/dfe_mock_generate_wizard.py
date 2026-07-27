# Copyright 2026 Engenere (<https://engenere.one>)
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import random
import re
from datetime import datetime, timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError

# Demo partner xmlids from l10n_br_base
_DEMO_PARTNER_XMLIDS = [
    "l10n_br_base.res_partner_intel",
    "l10n_br_base.res_partner_amd",
    "l10n_br_base.res_partner_dell",
    "l10n_br_base.res_partner_positivo",
    "l10n_br_base.res_partner_lg",
    "l10n_br_base.res_partner_samsungpe",
]

# UF codes (IBGE)
_UF_CODES = {
    "AC": "12",
    "AL": "27",
    "AM": "13",
    "AP": "16",
    "BA": "29",
    "CE": "23",
    "DF": "53",
    "ES": "32",
    "GO": "52",
    "MA": "21",
    "MG": "31",
    "MS": "50",
    "MT": "51",
    "PA": "15",
    "PB": "25",
    "PE": "26",
    "PI": "22",
    "PR": "41",
    "RJ": "33",
    "RN": "24",
    "RO": "11",
    "RR": "14",
    "RS": "43",
    "SC": "42",
    "SE": "28",
    "SP": "35",
    "TO": "17",
}


def _compute_access_key_check_digit(key_43):
    """Compute the check digit (mod 11) for a 43-char NF-e access key."""
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    total = 0
    for idx, digit in enumerate(reversed(key_43)):
        total += int(digit) * weights[idx % len(weights)]
    remainder = total % 11
    if remainder < 2:
        return "0"
    return str(11 - remainder)


def _generate_access_key(uf_code, year_month, cnpj_digits, serie, number, cnf=None):
    """Generate a valid 44-digit NF-e access key with correct check digit."""
    mod = "55"  # NF-e model
    tp_emis = "1"  # Normal emission
    if cnf is None:
        cnf = str(random.randint(10000000, 99999999))
    key_43 = (
        f"{uf_code}"
        f"{year_month}"
        f"{cnpj_digits}"
        f"{mod}"
        f"{str(serie).zfill(3)}"
        f"{str(number).zfill(9)}"
        f"{tp_emis}"
        f"{cnf}"
    )
    return key_43 + _compute_access_key_check_digit(key_43)


class DfeMockGenerateWizard(models.TransientModel):
    _name = "dfe.mock.generate.wizard"
    _description = "Generate Mock NSU Records"

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    quantity = fields.Integer(default=5)
    generate_res_nfe = fields.Boolean(default=True, string="Generate resNFe")
    generate_proc_nfe = fields.Boolean(default=True, string="Generate procNFe")
    generate_res_evento = fields.Boolean(default=False, string="Generate resEvento")
    generate_proc_evento_nfe = fields.Boolean(
        default=False, string="Generate procEventoNFe"
    )

    def _get_demo_partners(self):
        """Load demo partners from l10n_br_base, with fallback to search."""
        partners = self.env["res.partner"]
        for xmlid in _DEMO_PARTNER_XMLIDS:
            partner = self.env.ref(xmlid, raise_if_not_found=False)
            if partner:
                partners |= partner
        if not partners:
            partners = self.env["res.partner"].search(
                [
                    ("is_company", "=", True),
                    ("vat", "!=", False),
                    ("country_id.code", "=", "BR"),
                ],
                limit=6,
            )
        if not partners:
            raise UserError(
                _("No demo partners found. Install l10n_br_base demo data.")
            )
        return partners

    def _get_partner_data(self, partner):
        """Extract CNPJ digits, name, UF code, and IE from a partner."""
        cnpj_digits = re.sub(r"[^0-9]", "", partner.vat or "")
        uf_code = _UF_CODES.get(partner.state_id.code, "35")
        ie_raw = re.sub(r"[^0-9]", "", partner.l10n_br_ie_code or "")
        return {
            "cnpj": cnpj_digits,
            "name": partner.name or "Emitente Mock",
            "uf_code": uf_code,
            "ie": ie_raw or "ISENTO",
        }

    def _next_nsu(self, company):
        """Calculate the next NSU number for a company."""
        last = (
            self.env["dfe.mock.nsu"]
            .sudo()
            .search(
                [("company_id", "=", company.id)],
                order="nsu desc",
                limit=1,
            )
        )
        if last:
            return int(last.nsu) + 1
        return 1

    def _build_res_nfe_xml(self, access_key, partner_data, amount, emission_dt):
        """Build a resNFe XML string."""
        return (
            '<resNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">'
            f"<chNFe>{access_key}</chNFe>"
            f"<CNPJ>{partner_data['cnpj']}</CNPJ>"
            f"<xNome>{partner_data['name']}</xNome>"
            f"<IE>{partner_data['ie']}</IE>"
            f"<dhEmi>{emission_dt.strftime('%Y-%m-%dT%H:%M:%S')}-03:00</dhEmi>"
            "<tpNF>1</tpNF>"
            f"<vNF>{amount:.2f}</vNF>"
            "<digVal>mock+digest==</digVal>"
            "<dhRecbto>"
            f"{emission_dt.strftime('%Y-%m-%dT%H:%M:%S')}-03:00"
            "</dhRecbto>"
            "<cSitNFe>1</cSitNFe>"
            "</resNFe>"
        )

    def _build_proc_nfe_xml(self, access_key, partner_data, amount, emission_dt):
        """Build a procNFe XML string."""
        serie = access_key[22:25].lstrip("0") or "1"
        nnf = access_key[25:34].lstrip("0") or "1"
        company = self.company_id
        dest_cnpj = re.sub(r"[^0-9]", "", company.vat or "")
        dest_ie = re.sub(r"[^0-9]", "", getattr(company, "l10n_br_ie_code", "") or "")
        return (
            '<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
            '<NFe xmlns="http://www.portalfiscal.inf.br/nfe">'
            f'<infNFe Id="NFe{access_key}" versao="4.00">'
            "<ide>"
            f"<cUF>{partner_data['uf_code']}</cUF>"
            "<cNF>00000001</cNF>"
            "<natOp>VENDA DE MERCADORIA</natOp>"
            "<mod>55</mod>"
            f"<serie>{serie}</serie>"
            f"<nNF>{nnf}</nNF>"
            f"<dhEmi>{emission_dt.strftime('%Y-%m-%dT%H:%M:%S')}-03:00</dhEmi>"
            "<tpNF>1</tpNF>"
            "<idDest>1</idDest>"
            "<tpImp>1</tpImp>"
            "<tpEmis>1</tpEmis>"
            "<tpAmb>2</tpAmb>"
            "<finNFe>1</finNFe>"
            "<indFinal>1</indFinal>"
            "<indPres>1</indPres>"
            "<procEmi>0</procEmi>"
            "<verProc>1.0</verProc>"
            "</ide>"
            "<emit>"
            f"<CNPJ>{partner_data['cnpj']}</CNPJ>"
            f"<xNome>{partner_data['name']}</xNome>"
            "<enderEmit>"
            "<xLgr>Rua Mock</xLgr><nro>100</nro>"
            "<xBairro>Centro</xBairro>"
            f"<cMun>{partner_data['uf_code']}00308</cMun>"
            "<xMun>Cidade Mock</xMun>"
            f"<UF>SP</UF>"
            "<CEP>01000000</CEP>"
            "<cPais>1058</cPais><xPais>BRASIL</xPais>"
            "</enderEmit>"
            f"<IE>{partner_data['ie']}</IE>"
            "<CRT>3</CRT>"
            "</emit>"
            "<dest>"
            f"<CNPJ>{dest_cnpj}</CNPJ>"
            f"<xNome>{company.name}</xNome>"
            "<enderDest>"
            "<xLgr>Rua Empresa Mock</xLgr><nro>1</nro>"
            "<xBairro>Centro</xBairro>"
            f"<cMun>{partner_data['uf_code']}00308</cMun>"
            "<xMun>Cidade Mock</xMun>"
            "<UF>SP</UF>"
            "<CEP>01000000</CEP>"
            "<cPais>1058</cPais><xPais>BRASIL</xPais>"
            "</enderDest>"
            "<indIEDest>1</indIEDest>"
            f"<IE>{dest_ie or 'ISENTO'}</IE>"
            "</dest>"
            "<det nItem=\"1\">"
            '<prod><cProd>001</cProd><cEAN>SEM GTIN</cEAN>'
            "<xProd>PRODUTO MOCK</xProd>"
            "<NCM>84719012</NCM>"
            "<CFOP>5102</CFOP>"
            "<uCom>UN</uCom>"
            "<qCom>1.0000</qCom>"
            f"<vUnCom>{amount:.4f}</vUnCom>"
            f"<vProd>{amount:.2f}</vProd>"
            "<cEANTrib>SEM GTIN</cEANTrib>"
            "<uTrib>UN</uTrib>"
            "<qTrib>1.0000</qTrib>"
            f"<vUnTrib>{amount:.4f}</vUnTrib>"
            "<indTot>1</indTot>"
            "</prod>"
            "<imposto>"
            "<ICMS><ICMS00>"
            "<orig>0</orig><CST>00</CST>"
            "<modBC>0</modBC>"
            f"<vBC>{amount:.2f}</vBC>"
            "<pICMS>18.00</pICMS>"
            f"<vICMS>{amount * 0.18:.2f}</vICMS>"
            "</ICMS00></ICMS>"
            "</imposto>"
            "</det>"
            "<total><ICMSTot>"
            f"<vBC>{amount:.2f}</vBC>"
            f"<vICMS>{amount * 0.18:.2f}</vICMS>"
            "<vICMSDeson>0.00</vICMSDeson>"
            "<vFCPUFDest>0.00</vFCPUFDest>"
            "<vICMSUFDest>0.00</vICMSUFDest>"
            "<vICMSUFRemet>0.00</vICMSUFRemet>"
            "<vFCP>0.00</vFCP>"
            "<vBCST>0.00</vBCST>"
            "<vST>0.00</vST>"
            "<vFCPST>0.00</vFCPST>"
            "<vFCPSTRet>0.00</vFCPSTRet>"
            f"<vProd>{amount:.2f}</vProd>"
            "<vFrete>0.00</vFrete>"
            "<vSeg>0.00</vSeg>"
            "<vDesc>0.00</vDesc>"
            "<vII>0.00</vII>"
            "<vIPI>0.00</vIPI>"
            "<vIPIDevol>0.00</vIPIDevol>"
            "<vPIS>0.00</vPIS>"
            "<vCOFINS>0.00</vCOFINS>"
            "<vOutro>0.00</vOutro>"
            f"<vNF>{amount:.2f}</vNF>"
            "</ICMSTot></total>"
            "<transp><modFrete>9</modFrete></transp>"
            "</infNFe>"
            "</NFe>"
            '<protNFe versao="4.00">'
            "<infProt>"
            "<tpAmb>2</tpAmb>"
            "<verAplic>1.0</verAplic>"
            f"<chNFe>{access_key}</chNFe>"
            f"<dhRecbto>"
            f"{emission_dt.strftime('%Y-%m-%dT%H:%M:%S')}-03:00"
            f"</dhRecbto>"
            f"<nProt>{random.randint(100000000000000, 999999999999999)}</nProt>"
            "<digVal>mock+digest==</digVal>"
            "<cStat>100</cStat>"
            "<xMotivo>Autorizado o uso da NF-e</xMotivo>"
            "</infProt>"
            "</protNFe>"
            "</nfeProc>"
        )

    def _build_res_evento_xml(self, access_key, partner_data, emission_dt):
        """Build a resEvento XML string."""
        return (
            '<resEvento xmlns="http://www.portalfiscal.inf.br/nfe">'
            f"<cOrgao>91</cOrgao>"
            f"<CNPJ>{partner_data['cnpj']}</CNPJ>"
            f"<chNFe>{access_key}</chNFe>"
            f"<dhEvento>{emission_dt.strftime('%Y-%m-%dT%H:%M:%S')}-03:00"
            "</dhEvento>"
            "<tpEvento>210210</tpEvento>"
            "<nSeqEvento>1</nSeqEvento>"
            "<xEvento>Ciencia da Operacao</xEvento>"
            f"<dhRecbto>{emission_dt.strftime('%Y-%m-%dT%H:%M:%S')}-03:00"
            "</dhRecbto>"
            "</resEvento>"
        )

    def _build_proc_evento_nfe_xml(self, access_key, partner_data, emission_dt):
        """Build a procEventoNFe XML string."""
        return (
            '<procEventoNFe xmlns="http://www.portalfiscal.inf.br/nfe"'
            ' versao="1.00">'
            '<evento versao="1.00">'
            '<infEvento Id="ID210210352001">'
            "<cOrgao>91</cOrgao><tpAmb>2</tpAmb>"
            f"<CNPJ>{partner_data['cnpj']}</CNPJ>"
            f"<chNFe>{access_key}</chNFe>"
            f"<dhEvento>{emission_dt.strftime('%Y-%m-%dT%H:%M:%S')}-03:00"
            "</dhEvento>"
            "<tpEvento>210210</tpEvento>"
            "<nSeqEvento>1</nSeqEvento>"
            "<verEvento>1.00</verEvento>"
            '<detEvento versao="1.00">'
            "<descEvento>Ciencia da Operacao</descEvento>"
            "</detEvento>"
            "</infEvento></evento>"
            '<retEvento versao="1.00"><infEvento>'
            "<tpAmb>2</tpAmb><verAplic>1.0</verAplic>"
            "<cOrgao>91</cOrgao><cStat>135</cStat>"
            "<xMotivo>Evento registrado</xMotivo>"
            f"<chNFe>{access_key}</chNFe>"
            f"<dhRegEvento>"
            f"{emission_dt.strftime('%Y-%m-%dT%H:%M:%S')}-03:00"
            f"</dhRegEvento>"
            f"<nProt>{random.randint(100000000000000, 999999999999999)}</nProt>"
            "</infEvento></retEvento>"
            "</procEventoNFe>"
        )

    def action_generate(self):
        self.ensure_one()
        if self.quantity < 1:
            raise UserError(_("Quantity must be at least 1."))

        partners = self._get_demo_partners()
        partner_list = list(partners)
        starting_nsu = self._next_nsu(self.company_id)
        now = datetime.now()

        enabled_types = []
        if self.generate_res_nfe:
            enabled_types.append("resNFe")
        if self.generate_proc_nfe:
            enabled_types.append("procNFe")
        if (
            not enabled_types
            and not self.generate_res_evento
            and not self.generate_proc_evento_nfe
        ):
            raise UserError(_("Select at least one document type to generate."))

        created_ids = []
        nfe_keys = []  # Track keys for event generation
        current_nsu = starting_nsu

        # Generate NF-e types first (resNFe, procNFe)
        for _idx in range(self.quantity):
            partner = random.choice(partner_list)
            partner_data = self._get_partner_data(partner)
            emission_dt = now - timedelta(days=random.randint(1, 30))
            amount = round(random.uniform(100, 50000), 2)
            year_month = emission_dt.strftime("%y%m")
            number = random.randint(1, 999999999)
            access_key = _generate_access_key(
                partner_data["uf_code"],
                year_month,
                partner_data["cnpj"],
                1,
                number,
            )
            nfe_keys.append(access_key)

            for schema_type in enabled_types:
                nsu_str = str(current_nsu).zfill(15)
                if schema_type == "resNFe":
                    xml = self._build_res_nfe_xml(
                        access_key, partner_data, amount, emission_dt
                    )
                else:
                    xml = self._build_proc_nfe_xml(
                        access_key, partner_data, amount, emission_dt
                    )

                record = self.env["dfe.mock.nsu"].create(
                    {
                        "nsu": nsu_str,
                        "schema_type": schema_type,
                        "xml_content": xml,
                        "access_key": access_key,
                        "company_id": self.company_id.id,
                    }
                )
                created_ids.append(record.id)
                current_nsu += 1

        # Generate event types referencing previously generated keys
        if nfe_keys and (self.generate_res_evento or self.generate_proc_evento_nfe):
            event_types = []
            if self.generate_res_evento:
                event_types.append("resEvento")
            if self.generate_proc_evento_nfe:
                event_types.append("procEventoNFe")

            for _idx in range(min(self.quantity, len(nfe_keys))):
                ref_key = nfe_keys[_idx]
                partner = random.choice(partner_list)
                partner_data = self._get_partner_data(partner)
                emission_dt = now - timedelta(days=random.randint(0, 5))

                for schema_type in event_types:
                    nsu_str = str(current_nsu).zfill(15)
                    if schema_type == "resEvento":
                        xml = self._build_res_evento_xml(
                            ref_key, partner_data, emission_dt
                        )
                    else:
                        xml = self._build_proc_evento_nfe_xml(
                            ref_key, partner_data, emission_dt
                        )

                    record = self.env["dfe.mock.nsu"].create(
                        {
                            "nsu": nsu_str,
                            "schema_type": schema_type,
                            "xml_content": xml,
                            "access_key": ref_key,
                            "company_id": self.company_id.id,
                        }
                    )
                    created_ids.append(record.id)
                    current_nsu += 1

        return {
            "name": _("Generated Mock NSUs"),
            "type": "ir.actions.act_window",
            "res_model": "dfe.mock.nsu",
            "view_mode": "tree,form",
            "domain": [("id", "in", created_ids)],
            "target": "current",
        }
