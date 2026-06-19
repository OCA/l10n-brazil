# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from dataclasses import dataclass, field

from nfelib.nfse.bindings.v1_0.dps_v1_00 import Dps
from nfelib.nfse.bindings.v1_0.tipos_complexos_v1_00 import (
    Tccserv,
    Tcendereco,
    TcenderNac,
    TcinfDps,
    TcinfoPessoa,
    TcinfoPrestador,
    TcinfoTributacao,
    TcinfoValores,
    TclocPrest,
    TcregTrib,
    Tcserv,
    TctribMunicipal,
    TctribNacional,
    TctribOutrosPisCofins,
    TctribTotal,
    TcvservPrest,
)
from nfelib.nfse.bindings.v1_0.tipos_simples_v1_00 import (
    TsemitenteDps,
    TsopSimpNac,
    TsregEspTrib,
    TstipoAmbiente,
    TstipoCst,
    TstipoIndTotTrib,
    TstipoRetIssqn,
    TstribIssqn,
)
from xsdata.formats.dataclass.serializers import JsonSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from odoo import fields, models


@dataclass
class NfseResponse:
    """Type-safe wrapper for SEFIN NFS-e Nacional authorization responses.

    Normalises the two common field-name variants returned by SEFIN
    (``chave_nfse`` / ``chaveNFSe``, ``data_emissao`` / ``dhEmi``) into a
    single consistent structure so callers do not need to handle both forms.
    """

    status: str = ""
    numero: str = ""
    chave_nfse: str = ""
    data_emissao: str = ""
    erros: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "NfseResponse":
        """Construct an NfseResponse from a raw SEFIN API response dict.

        Args:
            data: Raw JSON dict from the SEFIN REST endpoint.

        Returns:
            NfseResponse populated from ``data``, with empty-string defaults
            for any missing keys.
        """
        return cls(
            status=data.get("status", ""),
            numero=str(data["numero"]) if data.get("numero") is not None else "",
            chave_nfse=data.get("chave_nfse") or data.get("chaveNFSe") or "",
            data_emissao=data.get("data_emissao") or data.get("dhEmi") or "",
            erros=data.get("erros", []),
        )


def _strip_nulls(obj):
    """Recursively remove None values from a dict/list structure.

    xsdata's JsonSerializer emits explicit ``null`` for absent optional fields.
    SEFIN rejects payloads that contain null values, so they must be stripped
    before the dict is sent to the API.
    """
    if isinstance(obj, dict):
        return {k: _strip_nulls(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_strip_nulls(i) for i in obj if i is not None]
    return obj


def _fmt(value) -> str | None:
    """Format a numeric value as a two-decimal string, or None when falsy.

    Args:
        value: Any numeric-compatible value (int, float, Decimal, or str).

    Returns:
        String like ``"100.00"``, or ``None`` when *value* is zero or absent.
    """
    if not value:
        return None
    return f"{float(value):.2f}"


class NfseSpecMixin(models.AbstractModel):
    """Base abstract model for all NFS-e Nacional v1.0 xsdata-odoo generated models.

    Exposes the module pointers used by ``spec_driven_model`` to resolve Odoo
    AbstractModels from nfelib binding class names, and whitelists the custom
    XSD field parameters that xsdata-odoo injects into field definitions
    (``xsd_type``, ``xsd_required``, ``choice``, ``xsd_implicit``,
    ``xsd_choice_required``).
    """

    _description = "NFS-e Nacional Abstract Model"
    _name = "spec.mixin.nfse"
    _nfse10_odoo_module = (
        "odoo.addons.l10n_br_nfse_spec.models.v1_0.tipos_complexos_v1_00"
    )
    _nfse10_binding_module = "nfelib.nfse.bindings.v1_0.tipos_complexos_v1_00"

    brl_currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.ref("base.BRL"),
    )

    def _valid_field_parameter(self, field, name):
        """Allow xsdata-odoo custom field parameters without Odoo framework warnings.

        xsdata-odoo injects non-standard keyword arguments into Odoo field
        definitions to carry XSD metadata. Odoo's base implementation raises
        a warning for unrecognised parameter names, so we whitelist them here.
        """
        if name in (
            "xsd_type",
            "xsd_required",
            "choice",
            "xsd_implicit",
            "xsd_choice_required",
        ):
            return True
        return super()._valid_field_parameter(field, name)


# Map legacy TAXATION_SPECIAL_REGIME codes (l10n_br_nfse) to DPS regEspTrib
# codes. The two sets of codes do not match. MEI ("5") and ME/EPP ("6") are
# expressed via opSimpNac and must not appear here.
# Legacy → DPS:
#   "1" Microempresa Municipal     → "3" Microempresa Municipal
#   "2" Estimativa                 → "2" Estimativa
#   "3" Sociedade de Profissionais → "6" Sociedade de Profissionais
#   "4" Cooperativa                → "1" Ato Cooperado (Cooperativa)
_LEGACY_REG_ESP_TO_DPS = {
    "1": "3",
    "2": "2",
    "3": "6",
    "4": "1",
}


class DpsBuilder:
    """Converts an Odoo fiscal document record into a DPS v1.0 JSON payload.

    Uses nfelib xsdata-generated binding classes and xsdata's JsonSerializer
    to produce the JSON body expected by the SEFIN REST API. Follows the same
    pattern used by ``l10n_br_nfe_spec`` (nfelib + xsdata + null-stripping).

    The *record* passed to the constructor must expose:

    - ``_prepare_lote_rps()``     → dict with RPS header fields
    - ``_prepare_dados_servico()`` → dict with service and tax fields
    - ``_prepare_dados_tomador()`` → dict with taker identity and address
    - ``company_id.cnpj_cpf``
    - ``company_id.partner_id.city_id.ibge_code``
    - ``nfse_environment``  (``"1"`` = production, ``"2"`` = homologation)
    """

    _SERIALIZER = JsonSerializer(config=SerializerConfig(pretty_print=False))

    def __init__(self, record):
        self._record = record

    def build(self) -> dict:
        """Build the complete DPS payload and return it as a Python dict.

        Calls the three record preparation helpers, assembles the full DPS
        dataclass hierarchy, serialises it to JSON via xsdata, strips null
        values, and returns the parsed dict ready to POST to SEFIN.

        Returns:
            Nested dict matching the DPS v1.0 schema with all null values
            removed.
        """
        rps = self._record._prepare_lote_rps()
        svc = self._record._prepare_dados_servico()
        taker = self._record._prepare_dados_tomador()
        dps = self._build_dps(rps, svc, taker)
        return _strip_nulls(json.loads(self._SERIALIZER.render(dps)))

    def _build_dps(self, rps: dict, svc: dict, taker: dict) -> Dps:
        """Assemble the top-level Dps dataclass from the three preparation dicts.

        Derives the environment enum from the record's ``nfse_environment``
        field, normalises the emission datetime to include a UTC offset, and
        delegates to the section-specific sub-builders.

        Args:
            rps:   RPS header data from ``_prepare_lote_rps()``.
            svc:   Service data from ``_prepare_dados_servico()``.
            taker: Taker data from ``_prepare_dados_tomador()``.

        Returns:
            Fully populated ``Dps`` nfelib dataclass instance.
        """
        record = self._record
        company = record.company_id
        env_code = int(record.nfse_environment or company.nfse_environment or "2")
        tp_amb = TstipoAmbiente.VALUE_1 if env_code == 1 else TstipoAmbiente.VALUE_2

        emission_dt = rps.get("data_emissao", "")
        if emission_dt and not emission_dt.endswith(("-0300", "-0200", "+0000", "Z")):
            emission_dt += "-0300"
        competence_date = emission_dt[:10] if emission_dt else ""
        ibge = str(company.partner_id.city_id.ibge_code or "0000000").zfill(7)

        return Dps(
            versao="1.00",
            infDPS=TcinfDps(
                tpAmb=tp_amb,
                dhEmi=emission_dt,
                verAplic="Odoo",
                serie=rps.get("serie"),
                nDPS=str(rps.get("numero", "")),
                dCompet=competence_date,
                tpEmit=TsemitenteDps.VALUE_1,
                cLocEmi=ibge,
                prest=self._build_prest(rps),
                toma=self._build_toma(taker),
                serv=self._build_serv(svc),
                valores=self._build_valores(svc, rps),
            ),
        )

    def _build_prest(self, rps: dict) -> TcinfoPrestador:
        """Build the service provider (prestador) section of the DPS.

        Strips punctuation from the company CNPJ/CPF and resolves both the
        Simples Nacional enrolment status (``opSimpNac``) and the special tax
        regime (``regEspTrib``) from the RPS dict.

        ``opSimpNac`` mapping:
        - enrolled (``optante_simples_nacional == "1"``) + MEI regime
          (``regime_especial_tributacao == "5"``) → ``VALUE_2`` (Optante MEI)
        - enrolled + any other regime               → ``VALUE_3`` (Optante ME/EPP)
        - not enrolled                              → ``VALUE_1`` (Não Optante)

        ``regEspTrib`` mapping uses ``_LEGACY_REG_ESP_TO_DPS`` to translate the
        legacy ``TAXATION_SPECIAL_REGIME`` codes to DPS codes. MEI and ME/EPP
        are expressed via ``opSimpNac`` and produce no ``regEspTrib`` value.

        Args:
            rps: RPS header dict from ``_prepare_lote_rps()``.

        Returns:
            Populated ``TcinfoPrestador`` instance.
        """
        company = self._record.company_id
        raw = (
            (company.cnpj_cpf or "").replace(".", "").replace("/", "").replace("-", "")
        )
        cnpj = raw if len(raw) == 14 else None
        cpf = raw if len(raw) == 11 else None

        optante = rps.get("optante_simples_nacional", "2")
        regime_leg = str(rps.get("regime_especial_tributacao") or "")

        if optante == "1":
            op_simp_nac = (
                TsopSimpNac.VALUE_2 if regime_leg == "5" else TsopSimpNac.VALUE_3
            )
        else:
            op_simp_nac = TsopSimpNac.VALUE_1

        dps_reg = _LEGACY_REG_ESP_TO_DPS.get(regime_leg)
        reg_esp_trib = TsregEspTrib(dps_reg) if dps_reg else None

        return TcinfoPrestador(
            CNPJ=cnpj,
            CPF=cpf,
            IM=rps.get("inscricao_municipal") or None,
            regTrib=TcregTrib(
                opSimpNac=op_simp_nac,
                regEspTrib=reg_esp_trib,
            ),
        )

    def _build_toma(self, taker: dict) -> TcinfoPessoa | None:
        """Build the service taker (tomador) section of the DPS.

        Constructs a domestic address block (``endNac``) when both the IBGE
        city code and CEP are present. Omits the address entirely when the
        taker dict has no ``endereco`` key. Uses ``NIF`` as the identifier
        when neither CNPJ nor CPF is provided.

        Args:
            taker: Taker identity and address dict from
                ``_prepare_dados_tomador()``.

        Returns:
            Populated ``TcinfoPessoa``, or ``None`` when the taker is absent.
        """
        cnpj = taker.get("cnpj") or ""
        cpf = taker.get("cpf") or ""
        nif = taker.get("nif") if not cnpj and not cpf else None

        end = None
        if taker.get("endereco"):
            cep = (taker.get("cep", "") or "").replace("-", "").replace(".", "")
            cep = cep.zfill(8) if cep else None
            cMun = str(taker.get("codigo_municipio") or "").zfill(7)
            end_nac = TcenderNac(cMun=cMun, CEP=cep) if cMun and cep else None
            end = Tcendereco(
                endNac=end_nac,
                xLgr=taker.get("endereco", ""),
                nro=taker.get("numero") or "SN",
                xBairro=taker.get("bairro") or "N/D",
                xCpl=taker.get("complemento") or None,
            )

        return TcinfoPessoa(
            CNPJ=cnpj if len(cnpj) == 14 else None,
            CPF=cpf if len(cpf) == 11 else None,
            NIF=nif,
            xNome=taker.get("razao_social"),
            end=end,
            email=taker.get("email") or None,
        )

    def _build_serv(self, svc: dict) -> Tcserv:
        """Build the service section (serv) of the DPS.

        Truncates the service description to 2 000 characters (XSD maximum)
        and zero-pads the IBGE municipality code to 7 digits.

        Args:
            svc: Service data dict from ``_prepare_dados_servico()``.

        Returns:
            Populated ``Tcserv`` instance.
        """
        desc = (svc.get("discriminacao") or "")[:2000]
        city_ibge = str(svc.get("municipio_prestacao_servico") or "").zfill(7)
        return Tcserv(
            locPrest=TclocPrest(cLocPrestacao=city_ibge),
            cServ=Tccserv(
                cTribNac=svc.get("codigo_tributacao_nacional") or "",
                cTribMun=svc.get("codigo_tributacao_municipio") or None,
                xDescServ=desc,
                cNBS=svc.get("codigo_nbs") or None,
            ),
        )

    def _build_valores(self, svc: dict, rps: dict) -> TcinfoValores:
        """Build the values section (valores) of the DPS.

        Handles ISSQN withholding flag and tax rate conversion:

        - ``iss_retido == "1"`` → ``tpRetISSQN`` VALUE_2 (withheld by taker)
        - any other value       → ``tpRetISSQN`` VALUE_1 (not withheld)
        - ``aliquota`` is a decimal fraction (e.g. ``0.02`` for 2%) and is
          multiplied by 100 before being stored as a percentage string.
        - ``totTrib`` is required by the XSD; ``indTotTrib=0`` signals
          "do not report estimated totals" per Decree 8.264/2014.

        Args:
            svc: Service data dict from ``_prepare_dados_servico()``.
            rps: RPS header dict (reserved for future substitution logic).

        Returns:
            Populated ``TcinfoValores`` instance.
        """
        svc_value = f"{float(svc.get('valor_servicos', 0)):.2f}"

        ret_issqn = (
            TstipoRetIssqn.VALUE_2
            if svc.get("iss_retido") == "1"
            else TstipoRetIssqn.VALUE_1
        )
        trib_mun = TctribMunicipal(
            tribISSQN=TstribIssqn.VALUE_1,
            tpRetISSQN=ret_issqn,
        )
        aliq = round(float(svc.get("aliquota", 0.0)) * 100, 2)
        if aliq:
            trib_mun.pAliq = f"{aliq:.2f}"

        trib_fed = self._build_trib_fed(svc)
        tot_trib = TctribTotal(indTotTrib=TstipoIndTotTrib.VALUE_0)

        return TcinfoValores(
            vServPrest=TcvservPrest(vServ=svc_value),
            trib=TcinfoTributacao(
                tribMun=trib_mun,
                tribFed=trib_fed,
                totTrib=tot_trib,
            ),
        )

    def _build_trib_fed(self, svc: dict) -> TctribNacional | None:
        """Build the federal withholding section (tribFed) or return None.

        Returns ``None`` when all federal withholding amounts are zero or
        absent, omitting the optional ``tribFed`` block from the payload.
        A ``TctribOutrosPisCofins`` sub-block is only created when PIS
        or COFINS withholding is present.

        Args:
            svc: Service data dict from ``_prepare_dados_servico()``.

        Returns:
            Populated ``TctribNacional``, or ``None`` when no withholding.
        """
        v_cp = float(svc.get("valor_inss_retido") or 0)
        v_irrf = float(svc.get("valor_ir_retido") or 0)
        v_csll = float(svc.get("valor_csll_retido") or 0)
        v_pis = float(svc.get("valor_pis_retido") or 0)
        v_cofins = float(svc.get("valor_cofins_retido") or 0)

        if not any([v_cp, v_irrf, v_csll, v_pis, v_cofins]):
            return None

        piscofins = None
        if v_pis or v_cofins:
            cst_str = (
                svc.get("situacao_tributaria_pis")
                or svc.get("situacao_tributaria_cofins")
                or "07"
            )
            piscofins = TctribOutrosPisCofins(
                CST=TstipoCst(cst_str),
                vPis=_fmt(v_pis),
                vCofins=_fmt(v_cofins),
                vBCPisCofins=_fmt(svc.get("base_calculo_pis")),
                pAliqPis=_fmt(svc.get("aliquota_pis")),
                pAliqCofins=_fmt(svc.get("aliquota_cofins")),
            )

        return TctribNacional(
            vRetCP=_fmt(v_cp),
            vRetIRRF=_fmt(v_irrf),
            vRetCSLL=_fmt(v_csll),
            piscofins=piscofins,
        )
