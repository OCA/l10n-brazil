# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


def filter_processador_edoc_cte(record):
    if record.processador_edoc == "oca" and record.document_type_id.code in [
        "57",
        "67",
    ]:
        return True
    return False


class CTe(spec_models.StackedModel):

    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "cte.40.tcte_infcte", "cte.40.tcte_fat"]
    _stacked = "cte.40.tcte_infcte"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_v4_00"
    _cte_search_keys = ["cte40_Id"]

    INFCTE_TREE = """
    > infCte
        > <ide>
        - <toma> res.partner
        > <emit> res.company
        > <dest> res.partner
        > <vPrest>
        > <imp>
        - <ICMS>
        - <ICMSUFFim>
        > <infCTeNorm>
        - <infCarga>
        - <infModal>"""

    ##########################
    # CT-e spec related fields
    ##########################

    ##########################
    # CT-e tag: infCte
    ##########################

    cte40_versao = fields.Char(related="document_version")

    cte40_Id = fields.Char(
        compute="_compute_cte40_Id",
        inverse="_inverse_cte40_Id",
    )

    ##########################
    # CT-e tag: Id
    # Methods
    ##########################

    @api.depends("document_type_id", "document_key")
    def _compute_cte40_Id(self):
        for record in self.filtered(filter_processador_edoc_cte):
            if (
                record.document_type_id
                and record.document_type.prefix
                and record.document_key
            ):
                record.cte40_Id = "{}{}".format(
                    record.document_type.prefix, record.document_key
                )
            else:
                record.cte40_Id = False

    def _inverse_cte40_Id(self):
        for record in self:
            if record.cte40_Id:
                record.document_key = re.findall(r"\d+", str(record.cte40_Id))[0]

    ##########################
    # CT-e tag: ide
    ##########################

    cte40_cUF = fields.Char(
        related="company_id.partner_id.state_id.ibge_code", string="cte40_cUF"
    )

    cte40_cCT = fields.Char()  # TODO

    cte40_CFOP = fields.Char(compute="_compute_cte40_CFOP")

    cte40_natOp = fields.Char(related="operation_name")

    cte40_mod = fields.Char(related="document_type_id.code", string="cte40_mod")

    cte40_serie = fields.Char(related="document_serie")

    cte40_nCT = fields.Char(related="document_number")

    cte40_dhEmi = fields.Datetime(related="document_date")

    cte40_tpImp = fields.Selection(
        selection=[(1, "Retrato"), (2, "Paisagem")]
    )  # TODO constantes

    cte40_tpEmis = fields.Selection(related="cte_transmission")

    cte40_cDV = fields.Char()  # TODO

    cte40_tpAmb = fields.Selection(related="cte_environment")

    cte_environment = fields.Selection(
        selection=[(1, "Produção"), (2, "Homologação")],
        string="CTe Environment",
        copy=False,
    )

    cte40_tpCTe = fields.selection(
        selection=[(0, "CTe Normal"), (1, "CTe Complementar"), (3, "CTe Substituição")],
    )

    cte40_procEmi = fields.Selection(default="0")

    cte40_verProc = fields.Char(
        copy=False,
        default=lambda s: s.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_cte.version.name", default="Odoo Brasil OCA v14"),
    )

    cte40_cMunEnv = fields.Char(
        related="company_id.partner_id.city_id.ibge_code"
    )  # TODO compute pro exterior

    cte40_xMunEnv = fields.Char(
        related="company_id.partner_id.city_id.name"
    )  # TODO compute pro exterior

    cte40_UFEnv = fields.Char(
        related="company_id.partner_id.state_id.code",
        string="nfe40_UFEnv",
    )

    cte40_tpServ = fields.Selection(
        selection=[
            (6, "Transporte de Pessoas"),
            (7, "Transporte de Valores"),
            (8, "Excesso de Bagagem"),
        ],
    )

    cte40_indIEToma = fields.Char()  # TODO IE tomador

    cte40_cMunIni = fields.Char(
        related="company_id.partner_id.city_id.ibge_code"
    )  # TODO compute pro exterior

    cte40_xMunIni = fields.Char(
        related="company_id.partner_id.city_id.name"
    )  # TODO compute pro exterior

    cte40_UFIni = fields.Char(
        related="company_id.partner_id.state_id.ibge_code", string="cte40_cUF"
    )

    cMunFim = fields.Char(related="partner_id.city_id.code")

    xMunFim = fields.Char(related="partner_id.city_id.name")

    UFFim = fields.Char(related="partner_id.state_id.code", string="cte40_cUF")

    retira = fields.Selection(selection=[(0, "Sim"), (1, "Não")])  # TODO constantes

    ##########################
    # CT-e tag: ide
    # Compute Methods
    ##########################
