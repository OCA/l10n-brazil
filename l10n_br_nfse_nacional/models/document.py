# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import gzip
import logging
import os
import re
import tempfile

import pytz
from nfelib import CommonMixin
from nfelib.nfse.bindings.v1_0.dps_v1_01 import Dps
from nfelib.nfse.bindings.v1_0.ped_reg_evento_v1_01 import PedRegEvento
from nfelib.nfse.bindings.v1_0.tipos_complexos_v1_01 import (
    TcrtcinfoTribIbscbs,
    TcrtcinfoValoresIbscbs,
)
from nfelib.nfse.bindings.v1_0.tipos_eventos_v1_01 import (
    TcinfPedReg,
    Te101101,
    Te101101XDesc,
)
from requests.exceptions import RequestException

from odoo import _, api, fields
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    MODELO_FISCAL_NFSE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_REJEITADA,
)
from odoo.addons.spec_driven_model.models import spec_models
from odoo.addons.spec_driven_model.models.spec_export import SpecMixinExport

from ..constants.nfse_nacional import (
    ADN_BASE_URL,
    DANFSE_NACIONAL_TEMPLATE,
    NFSE_NACIONAL_CANCEL_EVENT,
    NFSE_NACIONAL_CANCEL_OFICIO_EVENT,
    NFSE_NACIONAL_REPLACE_MOTIVES,
    PROVEDOR_NFSE_NACIONAL,
)
from ..transport.adn_rest import AdnRestClient

BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")

_logger = logging.getLogger(__name__)


def filter_nfse_nacional(record):
    return (
        record.processador_edoc == PROCESSADOR_OCA
        and record.document_type_id.code == MODELO_FISCAL_NFSE
        and record.company_id.provedor_nfse == PROVEDOR_NFSE_NACIONAL
    )


def _nfse10_amount(value):
    """Format an amount the way the NFS-e schema expects it (2 decimals).

    The export skips an empty element, so a zero amount stays False.
    """
    return f"{value:.2f}" if value else False


# Line amounts the single service of a DPS declares, summed over every fiscal
# line when the company declares all of them in that service.
NFSE_NACIONAL_SUMMED_FIELDS = (
    "price_gross",  # vServ
    "discount_value",  # vDescIncond
    "issqn_desc_cond_amount",  # vDescCond
    "inss_wh_value",  # vRetCP
    "irpj_wh_value",  # vRetIRRF
    "csll_wh_value",  # vRetCSLL
    "pis_value",  # vPis
    "cofins_value",  # vCofins
    "issqn_wh_value",  # tpRetISSQN (the withheld amount itself is not exported)
    "pis_wh_value",  # tpRetPisCofins
    "cofins_wh_value",  # tpRetPisCofins
)

# The rates of the same service. A rate is not additive: the consolidated
# percentage is the value weighted average of the line rates.
NFSE_NACIONAL_FEDERAL_RATE_FIELDS = (
    "pis_percent",
    "cofins_percent",
    "irpj_percent",
    "csll_percent",
    "inss_percent",
)
NFSE_NACIONAL_RATE_FIELDS = NFSE_NACIONAL_FEDERAL_RATE_FIELDS + ("issqn_percent",)

# The code the DPS cannot leave empty: two blank values there are a difference
# like any other, while an optional code a line simply does not inform is not.
NFSE_NACIONAL_REQUIRED_CODES = ("cTribNac",)


class L10nBrFiscalDocument(spec_models.StackedModel):
    """The DPS of a NFS-e Nacional, as a stacked spec model of the schema.

    A DPS declares a single service: infDPS has no list of items. The whole
    tree of the schema is therefore stacked on the fiscal document, and the
    service data is computed from the fiscal lines, which stay the place
    where the services are described (product, taxes, NBS and taxation
    codes). The prestador and the tomador are not stacked: they are the
    mapped res.company and res.partner records, like emit and dest in a NF-e.
    """

    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "nfse.10.tcinfdps"]

    _nfse10_odoo_module = (
        "odoo.addons.l10n_br_nfse_spec.models.v1_0.tipos_complexos_v1_01"
    )
    _nfse10_binding_module = "nfelib.nfse.bindings.v1_0.tipos_complexos_v1_01"
    _nfse10_binding_type = "TcinfDps"
    _nfse10_stacking_mixin = "nfse.10.tcinfdps"
    # Groups the schema declares as optional (so they are not stacked by
    # default) but the DPS always declares: leaving them out of the stack
    # would send their values to a side table, outside the fiscal document.
    _nfse10_stacking_force_paths = (
        "tcinfdps.valores.vDescCondIncond",
        "tcinfdps.valores.trib.tribFed",
        "tcinfdps.valores.trib.tribFed.piscofins",
        "tcinfdps.valores.trib.totTrib.pTotTrib",
    )
    # totTrib is an xs:choice: vTotTrib and pTotTrib are exclusive, so the
    # unused member must stay out of the stack or it would be exported empty
    # next to the other one.
    _nfse10_stacking_skip_paths = ("nfse10_vTotTrib",)

    # When dynamic stacking is applied the DPS structure is:
    # (+ content of the m2o is stacked in the parent / - standard m2o /
    # ≡ o2m; the mapped Odoo model may follow the tag)
    NFSE_TREE = """
+ <tcinfdps>
    - <subst>
    - <prest> res.company
    - <toma> res.partner
    - <interm> res.partner
    + <serv>
        + <locPrest>
        + <cServ>
        - <comExt>
        - <obra>
        - <atvEvento>
        - <infoCompl>
    + <valores>
        + <vServPrest>
        + <vDescCondIncond>
        - <vAjusteBC>
        + <trib>
            + <tribMun>
                - <exigSusp>
                - <BM>
            + <tribFed>
                + <piscofins>
            + <totTrib>
                + <pTotTrib>
    - <IBSCBS>"""

    nfse10_Id = fields.Char(compute="_compute_nfse10_id")
    nfse10_tpAmb = fields.Selection(related="nfse_environment")
    nfse10_dhEmi = fields.Char(compute="_compute_nfse10_dates")
    nfse10_verAplic = fields.Char(default="Odoo OCA")
    nfse10_serie = fields.Char(related="document_serie")
    nfse10_nDPS = fields.Char(related="document_number")
    nfse10_dCompet = fields.Char(compute="_compute_nfse10_dates")
    nfse10_tpEmit = fields.Selection(default="1")
    # Leiaute 1.04.01 (NT 009) moved finNFSe from the IBSCBS group to infDPS,
    # where it is mandatory. The schema only allows "0" (regular NFS-e): a
    # substitution is declared by its own subst group.
    nfse10_finNFSe = fields.Selection(default="0")
    nfse10_cLocEmi = fields.Char(related="company_id.partner_id.city_id.ibge_code")

    nfse10_prest = fields.Many2one("res.company", related="company_id")
    nfse10_toma = fields.Many2one("res.partner", compute="_compute_nfse10_toma")
    nfse10_interm = fields.Many2one("res.partner")

    nfse_nacional_concat_lines = fields.Boolean(
        related="company_id.nfse_nacional_concat_lines"
    )

    nfse_provedor = fields.Selection(related="company_id.provedor_nfse")
    nfse_replace_motive = fields.Selection(
        NFSE_NACIONAL_REPLACE_MOTIVES,
        string="Replacement Motive",
        default="99",
        copy=False,
        help="cMotivo of the subst group of the DPS, used when this NFS-e "
        "replaces another one.",
    )
    nfse_replace_reason = fields.Char(
        string="Replacement Description",
        size=255,
        copy=False,
        help="xMotivo of the subst group of the DPS (at least 15 characters).",
    )
    nfse_key = fields.Char(
        string="NFS-e Access Key", size=50, copy=False, readonly=True
    )
    nfse_number = fields.Char(string="NFS-e Number", copy=False, readonly=True)
    nfse_protocol = fields.Char(string="NFS-e Protocol", copy=False, readonly=True)
    edoc_error_message = fields.Text(readonly=True, copy=False)

    def _nfse10_service_line(self):
        """Return the fiscal line the codes of the single DPS service come from.

        Off the consolidation option that is the first line of the document,
        whatever it holds (legacy behaviour). On, a line that declares a
        service is preferred: cServ describes a service, and the amounts of
        that single service are then summed over the whole document.
        """
        self.ensure_one()
        if not self.nfse_nacional_concat_lines:
            return self.fiscal_line_ids[:1]
        product_lines = self.fiscal_line_ids.filtered("product_id")
        return product_lines[:1] or self.fiscal_line_ids[:1]

    def _nfse10_weighted_percent(self, field_name):
        """Consolidated rate of the single service: a rate is not additive.

        The line rates are averaged, weighted by the line value, so that the
        percentage declared for the whole service stays coherent with the
        amounts summed for it.
        """
        self.ensure_one()
        lines = self.fiscal_line_ids
        total = sum(lines.mapped("price_gross"))
        if not total:
            return 0.0
        return (
            sum((line.price_gross or 0.0) * (line[field_name] or 0.0) for line in lines)
            / total
        )

    def _nfse10_service_amounts(self):
        """Amounts and rates the single service of the DPS declares.

        Off the consolidation option the values of the line the service is
        built from are declared, as the DPS always did. On, the amounts are
        summed over every fiscal line of the document, so a document whose
        services are described line by line is not transmitted with the
        amounts of its first line only.
        """
        self.ensure_one()
        line = self._nfse10_service_line()
        amounts = {
            field_name: line[field_name] or 0.0
            for field_name in NFSE_NACIONAL_SUMMED_FIELDS + NFSE_NACIONAL_RATE_FIELDS
        }
        # the PIS/COFINS base of a line falls back to the other contribution
        amounts["pis_base"] = line.pis_base or line.cofins_base or 0.0
        if not self.nfse_nacional_concat_lines:
            return amounts
        lines = self.fiscal_line_ids
        for field_name in NFSE_NACIONAL_SUMMED_FIELDS:
            amounts[field_name] = sum(lines.mapped(field_name))
        amounts["pis_base"] = sum(
            doc_line.pis_base or doc_line.cofins_base or 0.0 for doc_line in lines
        )
        for field_name in NFSE_NACIONAL_RATE_FIELDS:
            amounts[field_name] = self._nfse10_weighted_percent(field_name)
        return amounts

    def _nfse10_service_description(self):
        """Describe the single service of the DPS.

        xDescServ is required by the schema (max 2000 characters, at least one
        non blank character), so the concatenation of the lines is truncated
        and trimmed, and the description of the service line is the last
        resort.
        """
        self.ensure_one()
        line = self._nfse10_service_line()
        if not self.nfse_nacional_concat_lines:
            return line.name
        names = [
            doc_line.name
            for doc_line in self.fiscal_line_ids
            if doc_line.product_id and doc_line.name
        ]
        return "\n".join(names)[:2000].rstrip() or line.name

    def _nfse10_trib_issqn_code(self, line):
        """tribISSQN of the single service: taxable, immune, exempt..."""
        issqn_nt = self.env.ref("l10n_br_fiscal.tax_issqn_nt", False)
        if line.issqn_eligibility == "4":
            return "3"
        if line.issqn_eligibility == "5":
            return "2"
        if issqn_nt and line.issqn_tax_id == issqn_nt:
            return "4"
        return "1"

    def _nfse10_pis_cst(self, line):
        """PIS/COFINS CST of the single service, in the group vocabulary."""
        valid_cst = dict(self._fields["nfse10_CST"].selection)
        cst = line.pis_cst_code
        return cst if cst in valid_cst else "00"

    def _nfse10_service_codes(self, line):
        """Codes the DPS declares once for its single service.

        They describe the service, not an amount: they can neither be summed
        nor averaged, so the lines must agree on them (see the consistency
        check below).
        """
        self.ensure_one()
        return {
            "cTribNac": line.national_taxation_code_id.code_unmasked or None,
            "cTribMun": line.city_taxation_code_id.code_unmasked or None,
            "cNBS": line.nbs_id.code_unmasked or None,
            "cLocPrestacao": line.issqn_fg_city_id.ibge_code or None,
            "tribISSQN": self._nfse10_trib_issqn_code(line),
            "PIS/COFINS CST": self._nfse10_pis_cst(line),
            "RTC cClassTrib": line.tax_classification_id.code or None,
            "RTC CST": (line.ibs_cst_id or line.cbs_cst_id).code or None,
            "RTC cIndOp": line.operation_indicator_id.code or None,
        }

    def _nfse10_service_mismatches(self):
        """Return the `label: line -> value` descriptions of a split needed.

        Blank values are left out of the comparison for the optional codes: a
        line that simply does not inform cTribMun or cNBS must not block a
        document whose other lines agree on it. The required code (cTribNac)
        is always compared, and so is an optional one as soon as a line
        carries it.
        """
        self.ensure_one()
        lines = self.fiscal_line_ids.filtered("product_id")
        if len(lines) < 2:
            return []
        collected = {}
        for line in lines:
            for label, value in self._nfse10_service_codes(line).items():
                if not value and label not in NFSE_NACIONAL_REQUIRED_CODES:
                    continue
                collected.setdefault(label, []).append((line.name, value))
        mismatches = []
        for label, declared in collected.items():
            if len({value for _name, value in declared}) < 2:
                continue
            details = ", ".join(
                f"{name or _('line without description')} -> {value or _('empty')}"
                for name, value in declared
            )
            mismatches.append(f"{label}: {details}")
        return mismatches

    def _check_nfse_service_consistency(self):
        """Refuse to declare one code for a document holding several services.

        The DPS has a single cServ element and a single RTC classification:
        picking one of them silently would transmit a document whose code does
        not describe the services it bills. With the consolidation option on
        the mismatch is an error; off, the legacy export is kept but the
        mismatch is logged so nobody transmits the wrong code by accident.
        """
        self.ensure_one()
        mismatches = self._nfse10_service_mismatches()
        if not mismatches:
            return
        if not self.nfse_nacional_concat_lines:
            _logger.warning(
                "NFS-e %s: the DPS declares a single service but its lines "
                "differ on %s. Only the first line is declared; enable "
                '"Declare all lines in the DPS" or split the document.',
                self.display_name,
                "; ".join(mismatches),
            )
            return
        raise UserError(
            _(
                "The DPS of %(document)s declares a single service, but its "
                "lines cannot be merged into one:\n\n%(details)s\n\n"
                "Split the document into one NFS-e per service, or turn off "
                '"%(option)s" to declare only the first line.'
            )
            % {
                "document": self.display_name,
                "details": "\n".join(mismatches),
                "option": _("Declare all lines in the DPS"),
            }
        )

    def _prepare_nfse10_service(self):
        """Declare the single service of the DPS from the fiscal lines.

        The serv, valores and trib groups of infDPS are stacked on the
        document as plain fields, like the NF-e totals: the schema holds one
        service per document, so the values of that service are prepared here
        from the fiscal lines, right before the export. A document imported
        from a received DPS has no fiscal line and keeps the values the DPS
        declared.
        """
        self.ensure_one()
        line = self._nfse10_service_line()
        if not line:
            return
        self._check_nfse_service_consistency()
        codes = self._nfse10_service_codes(line)
        amounts = self._nfse10_service_amounts()
        # serv/cServ and serv/locPrest
        self.nfse10_cTribNac = codes["cTribNac"]
        self.nfse10_cTribMun = codes["cTribMun"]
        self.nfse10_cNBS = codes["cNBS"]
        self.nfse10_cLocPrestacao = codes["cLocPrestacao"]
        self.nfse10_xDescServ = self._nfse10_service_description()
        # valores/vServPrest and valores/vDescCondIncond
        self.nfse10_vServ = _nfse10_amount(amounts["price_gross"])
        self.nfse10_vDescIncond = _nfse10_amount(amounts["discount_value"])
        self.nfse10_vDescCond = _nfse10_amount(amounts["issqn_desc_cond_amount"])
        # valores/trib/tribMun
        self._prepare_nfse10_trib_mun(codes, amounts)
        # valores/trib/tribFed
        self.nfse10_vRetCP = _nfse10_amount(amounts["inss_wh_value"])
        self.nfse10_vRetIRRF = _nfse10_amount(amounts["irpj_wh_value"])
        self.nfse10_vRetCSLL = _nfse10_amount(amounts["csll_wh_value"])
        self._prepare_nfse10_piscofins(codes, amounts)
        self._prepare_nfse10_tot_trib(amounts)

    def _prepare_nfse10_trib_mun(self, codes, amounts):
        # issqn_eligibility defaults to "2" (Não incidência) and is rarely set,
        # so only its explicit export and immunity values are taken from it.
        # Non-incidence (such as the rental of movable goods, STF SV 31) comes
        # from the ISSQN NT tax of the fiscal operation.
        self.nfse10_tribISSQN = codes["tribISSQN"]
        # pAliq is optional in the XSD and, for a municipality that joined the
        # national system, the ADN takes the ISSQN rate from its own municipal
        # parameters. Informing it anyway is refused by business rules such as
        # E0625 (rate informed without ISSQN withholding), so it is left out.
        self.nfse10_pAliq = False
        self.nfse10_tpRetISSQN = "2" if amounts["issqn_wh_value"] > 0 else "1"

    def _prepare_nfse10_piscofins(self, codes, amounts):
        self.nfse10_CST = codes["PIS/COFINS CST"]
        self.nfse10_vBCPisCofins = _nfse10_amount(amounts["pis_base"])
        self.nfse10_pAliqPis = _nfse10_amount(amounts["pis_percent"])
        self.nfse10_pAliqCofins = _nfse10_amount(amounts["cofins_percent"])
        self.nfse10_vPis = _nfse10_amount(amounts["pis_value"])
        self.nfse10_vCofins = _nfse10_amount(amounts["cofins_value"])
        self.nfse10_tpRetPisCofins = (
            "1" if (amounts["pis_wh_value"] or amounts["cofins_wh_value"]) else "2"
        )

    def _prepare_nfse10_tot_trib(self, amounts):
        # totTrib is a mandatory xs:choice among vTotTrib, pTotTrib, indTotTrib
        # and pTotTribSN. The national environment refuses indTotTrib and
        # pTotTribSN for a company outside the Simples Nacional (E0713), which
        # informs the approximate burden in pTotTrib instead.
        #
        # The regime comes from the burden of the service line, shared with the
        # other NFS-e layouts. The percentages are the ones of the single
        # service: the line rates, or their value weighted average when the
        # whole document is declared in the DPS (a rate is not additive).
        # Outside the Simples Nacional the federal one adds the withheld IRPJ,
        # CSLL and INSS to PIS and COFINS: leaving them out understates
        # pTotTribFed and the DANFSE approximate total.
        burden = self._nfse10_service_line()._nfse_approximate_tax_burden_from_taxes()
        federal = sum(amounts[field] for field in NFSE_NACIONAL_FEDERAL_RATE_FIELDS)
        if burden["simples"]:
            percent = burden["simples_percent"]
            self.nfse10_indTotTrib = False if percent else "0"
            self.nfse10_pTotTribSN = _nfse10_amount(percent)
            self.nfse10_pTotTribFed = False
            self.nfse10_pTotTribEst = False
            self.nfse10_pTotTribMun = False
            return
        self.nfse10_indTotTrib = False
        self.nfse10_pTotTribSN = False
        self.nfse10_pTotTribFed = f"{federal:.2f}"
        self.nfse10_pTotTribEst = f"{burden['state_percent']:.2f}"
        self.nfse10_pTotTribMun = f"{amounts['issqn_percent']:.2f}"

    @api.depends("partner_id.cnpj_cpf_stripped", "partner_id.nfse10_cNaoNIF")
    def _compute_nfse10_toma(self):
        for rec in self:
            partner = rec.partner_id
            identified = partner.cnpj_cpf_stripped or partner.nfse10_cNaoNIF
            rec.nfse10_toma = partner.id if identified else False

    @api.depends("document_key")
    def _compute_nfse10_id(self):
        for rec in self:
            rec.nfse10_Id = f"DPS{rec.document_key}" if rec.document_key else False

    @api.depends("document_date", "date_in_out")
    def _compute_nfse10_dates(self):
        for rec in self:
            if rec.document_date:
                local_dt = pytz.utc.localize(rec.document_date).astimezone(BRAZIL_TZ)
                rec.nfse10_dhEmi = local_dt.isoformat(timespec="seconds")
                rec.nfse10_dCompet = local_dt.strftime("%Y-%m-%d")
            else:
                rec.nfse10_dhEmi = False
                rec.nfse10_dCompet = False

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        """Export the DPS groups with the generic stacking algorithm.

        The other Brazilian DPS modules stack their own leiaute on the same
        l10n_br_fiscal.document model, so their _export_many2one overrides
        sit in the same MRO: l10n_br_nfe drops every non required stacked
        group whose denormalized fields are all empty. The DPS always
        declares vDescCondIncond and tribFed (piscofins included) even when
        they hold no value, so the nfse fields are exported here with the
        generic implementation instead of being pruned by a sibling module.

        The totTrib xs:choice is the only conditional member: the pTotTrib
        percentages (a company outside the Simples Nacional) must not appear
        next to pTotTribSN and vice versa.
        """
        if not field_name.startswith(f"{self._spec_prefix()}_"):
            return super()._export_many2one(field_name, xsd_required, class_obj)
        if field_name == "nfse10_pTotTrib" and not self.nfse10_pTotTribFed:
            return False
        return SpecMixinExport._export_many2one(
            self, field_name, xsd_required, class_obj
        )

    ##########################
    # NFS-e tag: IBSCBS
    # Inverse Methods
    ##########################

    def _nfse_ibscbs_line(self):
        """Return the line the DPS IBSCBS group is built from.

        A DPS declares a single servico, so the RTC data of the group comes
        from the same line already declaring the serv and valores groups. The
        method is shared with the other NFS-e layouts, which keep their own
        first line: only a document of this provider follows the consolidated
        service line.
        """
        self.ensure_one()
        if not filter_nfse_nacional(self):
            return super()._nfse_ibscbs_line()
        return self._nfse10_service_line()

    def _export_tag_nfse_10_ibscbs(self, xsd_fields, class_obj, export_dict):
        """Export the IBSCBS group declared in the DPS (leiaute 1.04.01, RTC).

        Dispatched by spec_driven_model through the per tag hooks while
        exporting the nfse10_IBSCBS field of the nfse.10.tcinfdps class: its
        comodel is the reusable nfse.10.tcrtcinfoibscbs type, so the class
        name dispatch would not match the IBSCBS tag name. The nested group is
        built here instead of relying on self stacking fields because the
        valores and trib tags of the DPS (nfse.10.tcinfovalores and
        nfse.10.tcinfotributacao) already hold those field names on the
        document.

        The classification (CST and cClassTrib) and the operation indicator
        (cIndOp) come from the line, exactly like the NF-e IBSCBS group; the
        amounts of the group are declared by the Sefin in the NFS-e, not in
        the DPS. Leiaute 1.04.01 (NT 009) keeps CST and cClassTrib directly
        under valores/trib: the gIBSCBS group below them only carries the
        credit presumption, regular taxation and deferred amounts.
        """
        if not self._nfse_export_ibscbs():
            return
        line = self._nfse_ibscbs_line()
        # indDest = "0" (the recipient is the tomador identified in the
        # NFS-e) comes with the dest group, which is not exported yet: it
        # stays a constant instead of a new document field holding a single
        # possible value for the documents this module emits.
        export_dict.update(
            cIndOp=line.operation_indicator_id.code,
            indDest="0",
            valores=TcrtcinfoValoresIbscbs(
                trib=TcrtcinfoTribIbscbs(
                    CST=line.ibs_cst_id.code or line.cbs_cst_id.code,
                    cClassTrib=line.tax_classification_id.code,
                )
            ),
        )

    def _export_tag_nfse_10_subst(self, xsd_fields, class_obj, export_dict):
        """Export the subst group of the DPS: the NFS-e this one replaces.

        The city hall (or the ADN) authorizes the new NFS-e and registers the
        replacement event on the old one, so there is no cancellation request.
        """
        old = self.nfse_replaced_document_id
        if not old:
            return
        if not old.nfse_key:
            raise UserError(
                _(
                    "The NFS-e %(document)s has no access key: it cannot be replaced.",
                    document=old.display_name,
                )
            )
        export_dict.update(
            chSubstda=old.nfse_key,
            cMotivo=self.nfse_replace_motive or "99",
            xMotivo=self.nfse_replace_reason or _("NFS-e replaced to correct its data"),
        )

    def _compute_nfse_replace_supported(self):
        result = super()._compute_nfse_replace_supported()
        self.filtered(filter_nfse_nacional).nfse_replace_supported = True
        return result

    def import_binding_nfse(self, binding, edoc_type="in", dry_run=False):
        """Build the fiscal document from the infDPS of a received DPS.

        The whole DPS is stacked on the fiscal document, so the import fills
        the document fields instead of scattering the groups of the schema
        into separate records.
        """
        if hasattr(binding, "DPS"):
            binding = binding.DPS
        document = self.with_context(
            tracking_disable=True, edoc_type=edoc_type
        ).build_from_binding("nfse", "10", binding.infDPS, dry_run=dry_run)
        return document

    @api.constrains("document_key")
    def _check_key(self):  # TODO required??
        """
        Bypass the 44-digit ChaveEdoc validation for NFS-e Nacional.
        DPS uses 42 digits and NFS-e uses 50 digits, which breaks the
        standard validation.
        """
        nfse_nacional_docs = self.filtered(
            lambda r: r.document_type_id
            and r.document_type_id.code == MODELO_FISCAL_NFSE
        )
        other_docs = self - nfse_nacional_docs

        # Only call the strict l10n_br_fiscal validation on NFe/CTe/MDFe
        if other_docs:
            return super(L10nBrFiscalDocument, other_docs)._check_key()

    def _processador_erpbrasil_nfse(self):
        # The ADN is not a municipal provider of erpbrasil.edoc.
        if self.filtered(filter_nfse_nacional):
            return None
        return super()._processador_erpbrasil_nfse()

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.filtered(filter_nfse_nacional):
            record._prepare_nfse10_service()
            inf_dps = record._build_binding("nfse", "10")
            # Leiaute 1.04.01 (NT 009): the ADN only accepts the IBSCBS
            # group from DPS version 1.01 on (E0854), so the version
            # follows the group instead of being a constant. A document
            # without RTC data keeps the legacy 1.00 shape.
            versao = "1.01" if record._nfse_export_ibscbs() else "1.00"
            nfse = Dps(infDPS=inf_dps, versao=versao, signature=None)
            edocs.append(nfse)
        return edocs

    def _document_export(self, pretty_print=True):
        result = super()._document_export()
        for record in self.filtered(filter_nfse_nacional):
            edoc = record.serialize()[0]
            xml_file = edoc.to_xml()
            if (
                record.authorization_event_id
                and record.authorization_event_id.state == "draft"
            ):
                record.sudo().authorization_event_id.unlink()
            event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=record._nfse_nacional_event_env(),
                event_type="0",
                xml_file=xml_file,
                document_id=record,
            )
            record.authorization_event_id = event_id
            certificate = record.company_id._get_br_certificate()
            signed_xml = edoc.sign_xml(
                xml_file,
                certificate.with_context(bin_size=False).content,
                certificate.pkcs12_password,
                edoc.infDPS.Id,
            )
            record._validate_xml(signed_xml)
        return result

    def _validate_xml(self, xml_file):
        self.ensure_one()
        if not self.filtered(filter_nfse_nacional):
            return super()._validate_xml(xml_file)
        erros = "\n".join(Dps.schema_validation(xml_file))
        self.write({"xml_error_message": erros or False})

    def _nfse_nacional_event_env(self):
        self.ensure_one()
        if self.nfse_environment == "1":
            return EVENT_ENV_PROD
        return EVENT_ENV_HML

    def _document_number(self):
        """Assign the DPS number and its access key.

        The shared implementation routes NFS-e numbering to ``rps_number``
        because municipal NFS-e is issued out of an RPS. NFS-e Nacional has
        no RPS: the number the issuer assigns is ``nDPS`` itself, and the
        DPS access key has 42 digits instead of the 44 of an NF-e.
        """
        result = super()._document_number()
        if not filter_nfse_nacional(self):
            return result
        if self.issuer != DOCUMENT_ISSUER_COMPANY:
            return result
        if not self.document_number and self.rps_number:
            self.document_number = self.rps_number
        if self.document_number and not self.document_key:
            self._nfse_nacional_generate_key()
        return result

    def _nfse_nacional_generate_key(self):
        """Build the 42 digit DPS key: city, issuer type, CNPJ/CPF,
        series and number."""
        self.ensure_one()
        partner = self.company_id.partner_id
        city_code = (partner.city_id.ibge_code or "").zfill(7)
        cnpj_cpf = partner.cnpj_cpf_stripped or ""
        issuer_type = "2" if len(cnpj_cpf) == 14 else "1"
        series = (self.document_serie or "").zfill(5)
        number = str(self.document_number or "").zfill(15)
        self.document_key = "".join(
            [city_code, issuer_type, cnpj_cpf.zfill(14), series, number]
        )

    def _eletronic_document_send(self):
        result = super()._eletronic_document_send()
        for record in self.filtered(filter_nfse_nacional):
            if record.xml_error_message:
                # Skipping in silence leaves the user pressing Send with nothing
                # happening: no state change, no message, no error.
                raise UserError(
                    _(
                        "The XML of %(document)s did not pass schema validation, "
                        "so nothing was sent:\n\n%(errors)s\n\nSet the document "
                        "back to draft and confirm it again to rebuild the XML."
                    )
                    % {
                        "document": record.display_name,
                        "errors": record.xml_error_message,
                    }
                )
            # l10n_br_fiscal_edi calls this hook from _after_document_send,
            # when the state machine already left "a_enviar" for "enviada",
            # so guarding on "a_enviar" would skip every transmission. Only
            # a document that already reached a final state is skipped.
            if record.state_edoc in (
                SITUACAO_EDOC_AUTORIZADA,
                SITUACAO_EDOC_CANCELADA,
            ):
                continue
            record._adn_send_for_authorization()
        return result

    def _adn_send_for_authorization(self):
        self.ensure_one()
        edoc = self.serialize()[0]
        certificate = self.company_id._get_br_certificate()
        signed_xml = edoc.sign_xml(
            edoc.to_xml(),
            certificate.with_context(bin_size=False).content,
            certificate.pkcs12_password,
            edoc.infDPS.Id,
        )
        if not signed_xml.lstrip().startswith("<?xml"):
            signed_xml = '<?xml version="1.0" encoding="UTF-8"?>' + signed_xml
        packed = AdnRestClient.pack_dps(signed_xml)
        response = self._adn_post(lambda client: client.post_dps(packed))
        self._adn_process_response(response, sent_xml=signed_xml)

    def _adn_post(self, call):
        """Run ``call(client)`` against the ADN over mTLS with a temp 0600 PEM."""
        self.ensure_one()
        base_url = ADN_BASE_URL[self.nfse_environment]
        pem = self._adn_mtls_pem()
        tmp = tempfile.NamedTemporaryFile("wb", suffix=".pem", delete=False)
        try:
            os.chmod(tmp.name, 0o600)
            tmp.write(pem)
            tmp.close()
            client = AdnRestClient(base_url, tmp.name)
            try:
                return call(client)
            except RequestException as exc:
                raise UserError(
                    _(
                        "Could not reach the NFS-e Nacional service (ADN) at "
                        "%(url)s: %(err)s"
                    )
                    % {"url": base_url, "err": exc}
                ) from exc
        finally:
            os.unlink(tmp.name)

    def _adn_mtls_pem(self):
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
            pkcs12,
        )

        certificate = self.company_id._get_br_certificate()
        pfx = base64.b64decode(certificate.with_context(bin_size=False).content)
        password = (certificate.pkcs12_password or "").encode() or None
        key, cert, _extra = pkcs12.load_key_and_certificates(pfx, password)
        pem = key.private_bytes(
            Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
        )
        pem += cert.public_bytes(Encoding.PEM)
        return pem

    def _adn_process_response(self, response, sent_xml):
        self.ensure_one()
        body = response.body or {}
        authorized = response.status_code in (200, 201) and bool(
            body.get("chaveAcesso")
        )
        if authorized:
            nfse_xml = self._adn_decode_nfse(body)
            self.write(
                {
                    "nfse_key": body.get("chaveAcesso"),
                    "nfse_number": body.get("nNFSe")
                    or body.get("numeroNfse")
                    or self._adn_xml_tag(nfse_xml, "nNFSe"),
                    "nfse_protocol": body.get("protocolo")
                    or body.get("nProt")
                    or self._adn_xml_tag(nfse_xml, "nDFSe"),
                    "status_code": str(body.get("status") or "100"),
                    "status_name": body.get("motivo") or _("Authorized"),
                    "edoc_error_message": False,
                }
            )
            self.authorization_event_id.set_done(
                status_code=self.status_code,
                response=self.status_name,
                protocol_date=fields.Datetime.now(),
                protocol_number=self.nfse_protocol,
                file_response_xml=nfse_xml,
            )
            self._change_state(SITUACAO_EDOC_AUTORIZADA)
            self._nfse_mark_replaced(sent_xml, nfse_xml)
        else:
            message = self._adn_format_errors(response)
            self.write(
                {
                    "edoc_error_message": message,
                    "status_code": str(response.status_code),
                    "status_name": _("Rejected"),
                }
            )
            self.authorization_event_id.set_done(
                status_code=str(response.status_code),
                response=message,
                protocol_date=fields.Datetime.now(),
                protocol_number=False,
                file_response_xml=False,
            )
            self.message_post(body=_("NFS-e rejected by the ADN:\n%s") % message)
            self._change_state(SITUACAO_EDOC_REJEITADA)

    @staticmethod
    def _adn_format_errors(response):
        body = response.body or {}
        erros = body.get("erros") or body.get("erro") or []
        lines = []
        for e in erros:
            code = e.get("Codigo") or e.get("codigo")
            desc = e.get("Descricao") or e.get("descricao")
            comp = e.get("complemento") or e.get("Complemento")
            lines.append(f"{code} - {desc}" + (f" ({comp})" if comp else ""))
        if lines:
            return "\n".join(lines)
        return body.get("mensagem") or response.content[:1000].decode(
            "utf-8", "replace"
        )

    @staticmethod
    def _adn_xml_tag(xml, tag):
        if not xml:
            return False
        match = re.search(rf"<{tag}>([^<]+)</{tag}>", xml)
        return match.group(1) if match else False

    @staticmethod
    def _adn_decode_nfse(body):
        raw = body.get("nfseXmlGZipB64")
        if raw:
            return gzip.decompress(base64.b64decode(raw)).decode("utf-8")
        return body.get("nfseXml") or ""

    def _document_cancel(self, justificative):
        for record in self.filtered(filter_nfse_nacional):
            if self.env.context.get("nfse_replaced_xml"):
                # replaced: the provider registered the event on the new NFS-e
                continue
            motive = self.env.context.get("nfse_cancel_motive", "1")
            record._adn_cancel(justificative, motive)
        return super()._document_cancel(justificative)

    def _adn_cancel(self, justificative, motive):
        self.ensure_one()
        ped = self._build_cancel_pedreg(justificative, motive)
        certificate = self.company_id._get_br_certificate()
        signed = CommonMixin.sign_xml(
            self._serialize_pedreg(ped),
            certificate.with_context(bin_size=False).content,
            certificate.pkcs12_password,
            ped.infPedReg.Id,
        )
        if not signed.lstrip().startswith("<?xml"):
            signed = '<?xml version="1.0" encoding="UTF-8"?>' + signed
        packed = AdnRestClient.pack_dps(signed)
        response = self._adn_post(
            lambda client: client.post_event(self.nfse_key, packed)
        )
        return self._adn_process_cancel_response(response, signed)

    def _cancel_event_id(self):
        self.ensure_one()
        return f"PRE{self.nfse_key}{NFSE_NACIONAL_CANCEL_EVENT}"

    def _build_cancel_pedreg(self, justificative, motive):
        self.ensure_one()
        cnpj = self.company_id.partner_id.cnpj_cpf_stripped or ""
        dt = (
            pytz.utc.localize(fields.Datetime.now())
            .astimezone(BRAZIL_TZ)
            .isoformat(timespec="seconds")
        )
        inf = TcinfPedReg(
            tpAmb=self.nfse_environment,
            verAplic="Odoo OCA",
            dhEvento=dt,
            CNPJAutor=cnpj,
            chNFSe=self.nfse_key,
            e101101=Te101101(
                xDesc=Te101101XDesc.CANCELAMENTO_DE_NFS_E,
                cMotivo=motive,
                xMotivo=justificative,
            ),
            Id=self._cancel_event_id(),
        )
        return PedRegEvento(infPedReg=inf, versao="1.00")

    @staticmethod
    def _serialize_pedreg(ped):
        from xsdata.formats.dataclass.serializers import XmlSerializer
        from xsdata.formats.dataclass.serializers.config import SerializerConfig

        serializer = XmlSerializer(config=SerializerConfig(pretty_print=False))
        return serializer.render(
            ped, ns_map={None: "http://www.sped.fazenda.gov.br/nfse"}
        )

    def _adn_process_cancel_response(self, response, signed_xml):
        self.ensure_one()
        if response.status_code not in (200, 201):
            raise UserError(
                _("NFS-e cancellation rejected by the ADN:\n%s")
                % self._adn_format_errors(response)
            )
        body = response.body or {}
        event = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=self._nfse_nacional_event_env(),
            event_type="2",
            xml_file=signed_xml,
            document_id=self,
        )
        self.cancel_event_id = event
        event.set_done(
            status_code=str(response.status_code),
            response=body.get("mensagem") or _("Cancelled"),
            protocol_date=fields.Datetime.now(),
            protocol_number=body.get("protocolo") or body.get("nProt") or False,
            file_response_xml=self._adn_decode_nfse(body) or signed_xml,
        )
        return True

    def action_adn_check_status(self):
        for record in self.filtered(filter_nfse_nacional):
            record._adn_check_cancellation_status()

    def _adn_check_cancellation_status(self):
        self.ensure_one()
        if self.state_edoc != SITUACAO_EDOC_AUTORIZADA:
            return
        for event_type in (
            NFSE_NACIONAL_CANCEL_EVENT,
            NFSE_NACIONAL_CANCEL_OFICIO_EVENT,
        ):
            response = self._adn_post(
                lambda client, et=event_type: client.get_event(self.nfse_key, et, "1")
            )
            if response.status_code in (200, 201):
                self._adn_register_external_cancellation(event_type, response)
                return

    def _adn_register_external_cancellation(self, event_type, response):
        self.ensure_one()
        body = response.body or {}
        raw = body.get("eventoXmlGZipB64")
        xml = gzip.decompress(base64.b64decode(raw)).decode("utf-8") if raw else ""
        event = self.event_ids.create_event_save_xml(
            company_id=self.company_id,
            environment=self._nfse_nacional_event_env(),
            event_type="2",
            xml_file=xml,
            document_id=self,
        )
        self.cancel_event_id = event
        event.set_done(
            status_code=event_type,
            response=_("Cancelled at the ADN by another means (event %s)") % event_type,
            protocol_date=fields.Datetime.now(),
            protocol_number=False,
            file_response_xml=xml,
        )
        self.message_post(
            body=_(
                "NFS-e was cancelled directly at the ADN (event %s), "
                "detected via status check."
            )
            % event_type
        )
        self._change_state(SITUACAO_EDOC_CANCELADA)

    def make_pdf(self):
        nacional_docs = self.filtered(filter_nfse_nacional)
        if not nacional_docs:
            return super().make_pdf()
        report = self.env["ir.actions.report"]
        for record in nacional_docs:
            pdf = report._render_qweb_pdf(DANFSE_NACIONAL_TEMPLATE, record.ids)[0]
            vals = {
                "name": f"DANFSe-{record.document_number or record.id}.pdf",
                "res_model": record._name,
                "res_id": record.id,
                "datas": base64.b64encode(pdf),
                "mimetype": "application/pdf",
                "type": "binary",
            }
            if record.file_report_id:
                record.file_report_id.write(vals)
            else:
                record.file_report_id = self.env["ir.attachment"].create(vals)
        remaining = self - nacional_docs
        if remaining:
            return super(L10nBrFiscalDocument, remaining).make_pdf()
