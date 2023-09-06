# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from erpbrasil.assinatura import certificado as cert
from erpbrasil.transmissao import TransmissaoSOAP
from nfelib.nfe.ws.edoc_legacy import MDFeAdapter as edoc_mdfe
from requests import Session

from odoo import _, api, fields
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_MDFE
from odoo.addons.spec_driven_model.models import spec_models

from ..constants.mdfe import (
    MDFE_EMISSION_PROCESS_DEFAULT,
    MDFE_EMISSION_PROCESSES,
    MDFE_EMIT_TYPES,
    MDFE_MODAL_DEFAULT,
    MDFE_MODALS,
    MDFE_TRANSMISSIONS,
    MDFE_TRANSP_TYPE,
    MDFE_VERSIONS,
)


def filtered_processador_edoc_mdfe(record):
    return (
        record.processador_edoc == "oca"
        and record.document_type_id.code == MODELO_FISCAL_MDFE
    )


class MDFe(spec_models.StackedModel):

    _name = "l10n_br_fiscal.document"
    _inherit = ["l10n_br_fiscal.document", "mdfe.30.tmdfe_infmdfe"]
    _stacked = "mdfe.30.tmdfe_infmdfe"
    _field_prefix = "mdfe30_"
    _schame_name = "mdfe"
    _schema_version = "3.0.0"
    _odoo_module = "l10n_br_mdfe"
    _spec_module = "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_tipos_basico_v3_00"
    _spec_tab_name = "MDFe"
    _mdfe_search_keys = ["mdfe30_Id"]

    INFMDFE_TREE = """
    > <infMDFe>
        > <ide>
        - <emit> res.company
        - <infModal>
        - <infDoc> l10n_br_fiscal.document.related
        > <tot>
    """

    ##########################
    # MDF-e spec related fields
    ##########################

    ##########################
    # MDF-e tag: infMDFe
    ##########################

    mdfe30_versao = fields.Char(related="document_version")

    mdfe30_Id = fields.Char(
        compute="_compute_mdfe30_id_tag",
        inverse="_inverse_mdfe30_id_tag",
    )

    ##########################
    # MDF-e tag: infMDFe
    # Methods
    ##########################

    @api.depends("document_type_id", "document_key")
    def _compute_mdfe30_id_tag(self):
        """Set schema data which are not just related fields"""

        for record in self.filtered(filtered_processador_edoc_mdfe):
            if (
                record.document_type_id
                and record.document_type.prefix
                and record.document_key
            ):
                record.mdfe30_Id = "{}{}".format(
                    record.document_type.prefix, record.document_key
                )
            else:
                record.mdfe30_Id = False

    def _inverse_mdfe30_id_tag(self):
        for record in self:
            if record.mdfe30_Id:
                record.document_key = re.findall(r"\d+", str(record.mdfe30_Id))[0]

    ##########################
    # MDF-e tag: ide
    ##########################

    mdfe30_cUF = fields.Char(
        related="company_id.partner_id.state_id.ibge_code",
    )

    mdfe30_tpAmb = fields.Selection(related="mdfe_environment")

    mdfe_environment = fields.Selection(
        selection=MDFE_VERSIONS,
        string="MDFe Environment",
        copy=False,
        default=lambda self: self.env.company.mdfe_environment,
    )

    mdfe30_tpEmit = fields.Selection(related="mdfe_emit_type")

    mdfe_emit_type = fields.Selection(
        selection=MDFE_EMIT_TYPES,
        string="MDFe Emit Type",
        copy=False,
        default=lambda self: self.env.company.mdfe_emit_type,
    )

    mdfe30_tpTransp = fields.Selection(related="mdfe_transp_type")

    mdfe_transp_type = fields.Selection(
        selection=MDFE_TRANSP_TYPE,
        string="MDFe Transp Type",
        copy=False,
        default=lambda self: self.env.company.mdfe_transp_type,
    )

    mdfe30_mod = fields.Char(related="document_type_id.code")

    mdfe30_serie = fields.Char(related="document_serie")

    mdfe30_nMDF = fields.Char(related="document_number")

    mdfe30_dhEmi = fields.Datetime(related="document_date")

    mdfe30_modal = fields.Selection(
        selection=MDFE_MODALS, string="Transport Modal", default=MDFE_MODAL_DEFAULT
    )

    mdfe30_tpEmis = fields.Selection(related="nfe_transmission")

    mdfe_transmission = fields.Selection(
        selection=MDFE_TRANSMISSIONS,
        string="MDFe Transmission",
        copy=False,
        default=lambda self: self.env.company.mdfe_transmission,
    )

    mdfe30_procEmi = fields.Selection(
        selection=MDFE_EMISSION_PROCESSES,
        string="MDFe Emission Process",
        default=MDFE_EMISSION_PROCESS_DEFAULT,
    )

    mdfe30_verProc = fields.Char(
        copy=False,
        default=lambda s: s.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_br_mdfe.version.name", default="Odoo Brasil OCA v14"),
    )

    mdfe30_UFIni = fields.Selection(related="mdfe_initial_state_id.ibge_code")

    mdfe30_UFFim = fields.Selection(related="mdfe_final_state_id.ibge_code")

    mdfe_initial_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="MDFe Initial State",
        domain=[("country_id.code", "=", "BR")],
    )

    mdfe_final_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="MDFe Final State",
        domain=[("country_id.code", "=", "BR")],
    )

    ##########################
    # MDF-e tag: infMunCarrega
    ##########################

    # TODO: compute?
    mdfe30_infMunCarrega = fields.One2many(related="mdfe_loading_city_ids")

    mdfe_loading_city_ids = fields.One2many(
        comodel_name="res.city", string="MDFe Loading Cities"
    )

    ##########################
    # MDF-e tag: infPercurso
    ##########################

    # TODO: compute?
    mdfe30_infPercurso = fields.One2many(related="mdfe_route_state_ids")

    mdfe_route_state_ids = fields.One2many(
        comodel_name="res.country.state",
        string="MDFe Route States",
        domain=[("country_id.code", "=", "BR")],
    )

    ##########################
    # MDF-e tag: emit
    ##########################

    nfe40_emit = fields.Many2one(comodel_name="res.company", related="company_id")

    ##########################
    # MDF-e tag: infRespTec
    ##########################

    mdfe30_infRespTec = fields.Many2one(
        comodel_name="res.partner",
        related="company_id.technical_support_id",
    )

    def _processador(self):
        certificate = False
        if self.company_id.sudo().certificate_nfe_id:
            certificate = self.company_id.sudo().certificate_nfe_id
        elif self.company_id.sudo().certificate_ecnpj_id:
            certificate = self.company_id.sudo().certificate_ecnpj_id

        if not certificate:
            raise UserError(_("Certificado não encontrado"))

        certificado = cert.Certificado(
            arquivo=certificate.file,
            senha=certificate.password,
        )
        session = Session()
        session.verify = False
        params = {
            "transmissao": TransmissaoSOAP(certificado, session),
            "uf": self.company_id.state_id.ibge_code,
            "versao": self.nfe_version,
            "ambiente": self.nfe_environment,
        }

        return edoc_mdfe(**params)
