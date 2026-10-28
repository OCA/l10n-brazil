# Copyright (C) 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

# Constants for the Portal Único Siscomex DUIMP REST API integration.

DUIMP_ENVIRONMENT_VALIDATION = "validation"
DUIMP_ENVIRONMENT_PRODUCTION = "production"

DUIMP_ENVIRONMENTS = {
    DUIMP_ENVIRONMENT_VALIDATION: "https://val.portalunico.siscomex.gov.br",
    DUIMP_ENVIRONMENT_PRODUCTION: "https://portalunico.siscomex.gov.br",
}

DUIMP_ENVIRONMENT_SELECTION = [
    (DUIMP_ENVIRONMENT_VALIDATION, "Company Validation"),
    (DUIMP_ENVIRONMENT_PRODUCTION, "Production"),
]

DUIMP_AUTH_PATH = "/portal/api/autenticar"
DUIMP_API_PATH_PREFIX = "/duimp-api/api/ext/duimp"
DUIMP_DEFAULT_VERSION = 1
DUIMP_ROLE_TYPE_DEFAULT = "IMPEXP"
DUIMP_DOCUMENT_TYPE_CODE = "55"
DUIMP_TAX_FIELD_PREFIX = {
    "II": "ii",
    "IPI": "ipi",
    "PIS": "pis",
    "COFINS": "cofins",
}
DUIMP_SEARCH_DEFAULT_DAYS = 60
DUIMP_TOKEN_CACHE_SECONDS = 300

DUIMP_STATE_SELECTION = [
    ("draft", "Draft"),
    ("open", "Open"),
    ("locked", "Locked"),
    ("canceled", "Canceled"),
]

# Order follows the sequence the taxes are assessed in, which is also the
# order they are listed in: the selection order drives the "sequence"
# stored on each tax line, so the item breakdown does not come out sorted
# alphabetically.
#
# The labels of the Brazilian federal taxes (II, IPI, PIS, COFINS, CBS,
# IBS, CIDE) are kept in Portuguese on purpose: they are the official
# names of the tax, not a description we chose, the same way CFOP/NCM
# labels stay in Portuguese elsewhere in l10n_br_fiscal.
DUIMP_TAX_TYPE_SELECTION = [
    ("II", "II - Imposto de Importação"),
    ("IPI", "IPI - Imposto sobre Produtos Industrializados"),
    ("PIS", "PIS/PASEP-Importação"),
    ("COFINS", "COFINS-Importação"),
    ("CBS", "CBS - Contribuição sobre Bens e Serviços"),
    ("IBS_ESTADUAL", "IBS Estadual"),
    ("IBS_MUNICIPAL", "IBS Municipal"),
    ("CIDE", "CIDE"),
    ("ANTIDUMPING", "Direito Antidumping"),
    ("TAXA_UTILIZACAO", "Taxa de Utilização do Siscomex"),
    ("OUTRO", "Other"),
]

DUIMP_TAX_SEQUENCE = {
    code: index for index, (code, _label) in enumerate(DUIMP_TAX_TYPE_SELECTION)
}

# Header fields read straight from the payload, as dotted paths tried in
# order. Only paths confirmed against a real "Consulta aos Dados da Duimp"
# response belong here: a guessed path that never resolves is worse than no
# mapping, because it makes an empty field look mapped.
#
# Keys are l10n_br_duimp.declaration field names.
DUIMP_HEADER_PAYLOAD_PATHS = {
    "clearance_office_code": ("carga.unidadeDeclarada.codigo",),
    "clearance_office_name": ("despacho.urfDespacho.nome",),
    "clearance_state": ("despacho.ufDesembaraco",),
    "clearance_date": ("despacho.dataDesembaraco",),
    "transport_mode_code": ("carga.viaTransporte.codigo",),
    "operation_type_code": ("carga.caracterizacaoOperacao.codigo",),
    "origin_country_code": ("carga.paisProcedencia.codigo",),
    "cargo_identification": ("carga.identificacao",),
}

# Fields the real payload does NOT carry in any structured node, left for
# manual entry (some only exist inside the free-text
# "identificacao.informacaoComplementar"):
#   incoterm_id                -> per item, and null on real responses
#   clearance_office_name      -> only the code is returned
#   clearance_state, clearance_date
#   transport_mode_code        -> "VIA DE TRANSPORTE : 04 - AEREA"
#   operation_type_code
# They are editable on the declaration form so the NF-e import-declaration
# group can still be completed by hand.


# Federal taxes the payload returns at header level but that have no
# counterpart field on l10n_br_fiscal.document.line: kept on the
# declaration for auditing/landed cost only, never pushed to the invoice.
# CBS/IBS come from the tax reform and the DUIMP already returns them.
#
# Values are l10n_br_duimp.declaration field names.
DUIMP_HEADER_EXTRA_TAX_FIELD = {
    "CBS": "cbs_total",
    "IBS_ESTADUAL": "ibs_estadual_total",
    "IBS_MUNICIPAL": "ibs_municipal_total",
    "TAXA_UTILIZACAO": "siscomex_usage_fee_amount",
}

# Siscomex commercial unit -> Odoo uom.uom xmlid. Only unambiguous
# equivalences are listed: the unit the DUIMP reports is always kept as
# text in l10n_br_duimp.item.trade_uom, and a unit that is not here simply
# leaves uom_id empty for the user to pick, rather than being forced into
# "Units" and silently changing what is invoiced.
# Units with no Odoo counterpart (PAR, MILHEIRO, GRAMA QUILATE, ...) are
# intentionally absent.
DUIMP_UOM_XMLID = {
    "UNIDADE": "uom.product_uom_unit",
    "PECA": "uom.product_uom_unit",
    "ROLO": "uom.product_uom_unit",
    "CAIXA": "uom.product_uom_unit",
    "JOGO": "uom.product_uom_unit",
    "DUZIA": "uom.product_uom_dozen",
    "QUILOGRAMA": "uom.product_uom_kgm",
    "QUILOGRAMA LIQUIDO": "uom.product_uom_kgm",
    "GRAMA": "uom.product_uom_gram",
    "TONELADA METRICA": "uom.product_uom_ton",
    "LITRO": "uom.product_uom_litre",
    "METRO": "uom.product_uom_meter",
    "METRO CUBICO": "uom.product_uom_cubic_meter",
    "QUILOMETRO": "uom.product_uom_km",
}

# Fields recovered from "identificacao.informacaoComplementar", the free
# text block of the DUIMP. Several of them exist nowhere else in the
# response - notably the ICMS, which this federal service never returns
# in a structured node, and the transport mode and clearance location,
# which the NF-e import-declaration group requires.
#
# The block is "LABEL <padding> : VALUE" per line, so each entry is a
# regex with a single capture group. Nothing here is authoritative: every
# target field stays editable, and a label that changes format simply
# leaves its field empty instead of breaking the import.
#
# Keys are l10n_br_duimp.declaration field names; the regexes match the
# Portuguese labels Siscomex itself prints in that block, which do not
# change with our own field naming.
DUIMP_FREE_TEXT_PATTERNS = {
    "transport_mode_code": r"^VIA DE TRANSPORTE\s*:\s*(\d+)",
    "bonded_warehouse": r"^RECINTO ALFANDEGADO\s*:\s*(.+?)\s*$",
    "gross_weight": r"^PESO BRUTO KG\s*:\s*([\d.,]+)",
    "net_weight": r"^PESO LIQUIDO KG\s*:\s*([\d.,]+)",
    "shipping_date": r"^DATA DE EMBARQUE\s*:\s*(\d{2}/\d{2}/\d{4})",
    "arrival_date": r"^DATA DE CHEGADA\s*:\s*(\d{2}/\d{2}/\d{4})",
    "icms_amount": r"^ICMS A RECOLHER - R\$\s*:\s*([\d.,]+)",
}

DUIMP_FREE_TEXT_DATE_FIELDS = ("shipping_date", "arrival_date")
DUIMP_FREE_TEXT_MONETARY_FIELDS = ("gross_weight", "net_weight", "icms_amount")

# "BASE DE CALCULO" appears only inside the ICMS block, but it is anchored
# to that heading so a future layout with other tax blocks cannot pick up
# the wrong one.
DUIMP_FREE_TEXT_ICMS_BASE = (
    r"TOTAL DOS IMPOSTOS - ICMS.*?^BASE DE CALCULO\s*:\s*([\d.,]+)"
)

# "caracterizacaoImportacao.indicador" (per item) is what the NF-e calls
# tpIntermedio in the import-declaration group: 1-por conta propria,
# 2-por conta e ordem, 3-encomenda. The DUIMP spells it out instead of
# numbering it, so it needs translating.
DUIMP_CARACTERIZACAO_TPINTERMEDIO = {
    "IMPORTACAO_DIRETA": "1",
    "IMPORTACAO_POR_CONTA_E_ORDEM": "2",
    "CONTA_E_ORDEM": "2",
    "IMPORTACAO_POR_ENCOMENDA": "3",
    "ENCOMENDA": "3",
}

# Tax reform taxes that DO have fields on l10n_br_fiscal.document.line.
# The DUIMP splits the IBS into its state and municipal shares, while the
# line carries a single IBS (the total), so the two are summed.
DUIMP_CBS_TYPE = "CBS"
DUIMP_IBS_TYPES = ("IBS_ESTADUAL", "IBS_MUNICIPAL")
